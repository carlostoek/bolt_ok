"""
VIP Grant Service - Sistema para otorgar accesos VIP gratuitos

Permite otorgar accesos VIP temporales desde diferentes fuentes:
- Narrativa (post_actions en fragmentos)
- Recompensas (canje en tienda)
- Achievements (logros especiales)
- Admin (manual)
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram import Bot
import logging

from database.models import User, VipGrant
from services.subscription_service import SubscriptionService
from services.config_service import ConfigService
from utils.user_roles import clear_role_cache
from utils.messages import BOT_MESSAGES

logger = logging.getLogger(__name__)


class VipGrantService:
    """Servicio para otorgar accesos VIP gratuitos de forma centralizada."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.subscription_service = SubscriptionService(session)
        self.config_service = ConfigService(session)

    async def grant_vip_access(
        self,
        user_id: int,
        days: int,
        source: str,
        source_id: Optional[int] = None,
        bot: Optional[Bot] = None
    ) -> Tuple[bool, str]:
        """
        Otorga acceso VIP temporal a un usuario.

        Args:
            user_id: ID del usuario
            days: Días de acceso VIP (generalmente 1)
            source: Fuente del grant ("narrative", "reward", "achievement", "admin")
            source_id: ID de la fuente (fragment_id, reward_id, etc.)
            bot: Instancia del bot para generar invite link

        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        try:
            logger.info(f"Granting {days} day(s) VIP access to user {user_id} from source {source}")

            # 1. Extender/crear suscripción VIP
            await self.subscription_service.extend_subscription(user_id, days)

            # 2. Calcular fecha de expiración
            user = await self.session.get(User, user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False, BOT_MESSAGES.get("vip_grant_error", "Error al otorgar VIP")

            expires_at = user.vip_expires_at

            # 3. Generar invite link al canal VIP (si bot disponible)
            invite_link = None
            if bot:
                invite_link = await self._generate_vip_invite_link(bot, user_id)

            # 4. Registrar grant en tabla de auditoría
            grant = VipGrant(
                user_id=user_id,
                days_granted=days,
                source=source,
                source_id=source_id,
                expires_at=expires_at,
                invite_link=invite_link
            )
            self.session.add(grant)
            await self.session.commit()
            await self.session.refresh(grant)

            # 5. Limpiar cache de roles
            clear_role_cache(user_id)

            # 6. Enviar mensajes de bienvenida (si bot disponible)
            if bot:
                await self._send_welcome_messages(
                    bot=bot,
                    user_id=user_id,
                    days=days,
                    expires_at=expires_at,
                    invite_link=invite_link,
                    source=source
                )

            logger.info(f"VIP access granted successfully to user {user_id}, expires at {expires_at}")

            # 7. Retornar mensaje de éxito
            success_msg = BOT_MESSAGES.get("vip_grant_success", "¡Acceso VIP otorgado!").format(
                days=days,
                expires_at=expires_at.strftime("%d/%m/%Y %H:%M") if expires_at else "indefinido"
            )

            return True, success_msg

        except Exception as e:
            logger.error(f"Error granting VIP access to user {user_id}: {e}", exc_info=True)
            return False, BOT_MESSAGES.get("vip_grant_error", "Error al otorgar VIP")

    async def _generate_vip_invite_link(self, bot: Bot, user_id: int) -> Optional[str]:
        """
        Genera un invite link de 24h al canal VIP.

        Args:
            bot: Instancia del bot
            user_id: ID del usuario (para logging)

        Returns:
            str | None: Link de invitación o None si falla
        """
        try:
            vip_channel_id = await self.config_service.get_vip_channel_id()
            if not vip_channel_id:
                logger.warning("VIP channel ID not configured")
                return None

            # Crear invite link de 24h, single-use, sin aprobación
            link = await bot.create_chat_invite_link(
                vip_channel_id,
                member_limit=1,
                expire_date=datetime.utcnow() + timedelta(hours=24),
                creates_join_request=False
            )

            logger.info(f"Generated VIP invite link for user {user_id}: {link.invite_link}")
            return link.invite_link

        except Exception as e:
            logger.error(f"Failed to generate VIP invite link for user {user_id}: {e}")
            return None

    async def _send_welcome_messages(
        self,
        bot: Bot,
        user_id: int,
        days: int,
        expires_at: datetime,
        invite_link: Optional[str],
        source: str
    ):
        """
        Envía mensajes de bienvenida VIP al usuario.

        Args:
            bot: Instancia del bot
            user_id: ID del usuario
            days: Días otorgados
            expires_at: Fecha de expiración
            invite_link: Link de invitación al canal
            source: Fuente del grant
        """
        try:
            # Mensaje 1: Bienvenida de Señorita Kinky
            await bot.send_message(
                user_id,
                BOT_MESSAGES.get("vip_welcome_special", "¡Bienvenido al mundo VIP!")
            )

            # Mensaje 2: Detalles según la fuente
            if source == "narrative":
                detail_msg = BOT_MESSAGES.get("vip_grant_narrative", "Regalo narrativo").format(days=days)
            elif source == "reward":
                detail_msg = BOT_MESSAGES.get("vip_grant_reward", "Recompensa canjeada").format(
                    days=days,
                    expires_at=expires_at.strftime("%d/%m/%Y %H:%M") if expires_at else "indefinido"
                )
            elif source == "achievement":
                detail_msg = BOT_MESSAGES.get("vip_grant_achievement", "¡Logro desbloqueado!").format(days=days)
            else:
                detail_msg = BOT_MESSAGES.get("vip_grant_success", "Acceso VIP otorgado").format(
                    days=days,
                    expires_at=expires_at.strftime("%d/%m/%Y %H:%M") if expires_at else "indefinido"
                )

            await bot.send_message(user_id, detail_msg)

            # Mensaje 3: Link al canal VIP (si disponible)
            if invite_link:
                link_msg = BOT_MESSAGES.get("vip_grant_channel_link", "Link al canal").format(
                    invite_link=invite_link
                )
                await bot.send_message(user_id, link_msg, parse_mode=None)
            else:
                # Si no hay link, enviar mensaje sin link
                await bot.send_message(
                    user_id,
                    BOT_MESSAGES.get(
                        "vip_activation_no_link",
                        "Acceso VIP activado. Contacta soporte para el link al canal."
                    ).format(
                        duration=days,
                        expires_at=expires_at.strftime("%d/%m/%Y %H:%M") if expires_at else "indefinido"
                    )
                )

            logger.info(f"Welcome messages sent to user {user_id}")

        except Exception as e:
            logger.error(f"Error sending welcome messages to user {user_id}: {e}", exc_info=True)

    async def check_duplicate_grant(
        self,
        user_id: int,
        source: str,
        source_id: Optional[int] = None
    ) -> bool:
        """
        Verifica si el usuario ya recibió un grant de esta fuente específica.

        Útil para evitar farming de VIP gratuito desde el mismo fragmento narrativo.

        Args:
            user_id: ID del usuario
            source: Fuente del grant
            source_id: ID de la fuente

        Returns:
            bool: True si ya existe, False si es nuevo
        """
        if not source_id:
            return False  # No verificar si no hay source_id

        stmt = select(VipGrant).where(
            VipGrant.user_id == user_id,
            VipGrant.source == source,
            VipGrant.source_id == source_id
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        return existing is not None

    async def get_user_grants(self, user_id: int) -> list[VipGrant]:
        """
        Obtiene todos los grants VIP de un usuario.

        Args:
            user_id: ID del usuario

        Returns:
            list[VipGrant]: Lista de grants
        """
        stmt = select(VipGrant).where(VipGrant.user_id == user_id).order_by(VipGrant.granted_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_grants_by_source(self, source: str, limit: int = 100) -> list[VipGrant]:
        """
        Obtiene grants por fuente (para analytics).

        Args:
            source: Fuente del grant
            limit: Límite de resultados

        Returns:
            list[VipGrant]: Lista de grants
        """
        stmt = (
            select(VipGrant)
            .where(VipGrant.source == source)
            .order_by(VipGrant.granted_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
