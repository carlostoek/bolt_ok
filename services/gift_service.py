"""
Gift Service - Sistema de regalos estratégicos

Maneja el envío de regalos por:
- Eventos específicos (ganó subasta, compró en tienda, alcanzó nivel)
- Sorpresas espontáneas del admin
- Logros especiales

Integrado con ContentService para enviar contenido multimedia.
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from aiogram import Bot

from database.models import User, GiftRecord, ContentSet
from services.content_service import ContentService

logger = logging.getLogger(__name__)


from utils.localization import L

# Templates de mensajes según evento
GIFT_MESSAGES = {
    "auction_won": {
        "title": L("gift.user.auction_won_title"),
        "message": L("gift.user.auction_won_message")
    },
    "shop_purchase": {
        "title": L("gift.user.shop_purchase_title"),
        "message": L("gift.user.shop_purchase_message")
    },
    "level_reached": {
        "title": L("gift.user.level_reached_title"),
        "message": L("gift.user.level_reached_message")
    },
    "milestone": {
        "title": L("gift.user.milestone_title"),
        "message": L("gift.user.milestone_message")
    },
    "surprise": {
        "title": L("gift.user.surprise_title"),
        "message": L("gift.user.surprise_message")
    },
    "loyalty": {
        "title": L("gift.user.loyalty_title"),
        "message": L("gift.user.loyalty_message")
    },
    "birthday": {
        "title": L("gift.user.birthday_title"),
        "message": L("gift.user.birthday_message")
    },
    "custom": {
        "title": L("gift.user.custom_title"),
        "message": L("gift.user.custom_message")
    }
}


class GiftService:
    """Servicio para gestionar el envío de regalos estratégicos"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.content_service = ContentService(session)

    async def send_gift(
        self,
        user_id: int,
        content_set_id: str,
        event_type: str,
        bot: Bot,
        context_data: Optional[Dict] = None,
        custom_message: Optional[str] = None,
        sent_by_admin: bool = False
    ) -> bool:
        """
        Envía un regalo a un usuario por un evento específico

        Args:
            user_id: ID del usuario
            content_set_id: ID del content set a enviar
            event_type: Tipo de evento (auction_won, shop_purchase, etc)
            bot: Instancia del bot
            context_data: Datos adicionales del contexto (item_name, level, etc)
            custom_message: Mensaje personalizado (sobrescribe el template)
            sent_by_admin: Si fue enviado manualmente por admin

        Returns:
            True si se envió correctamente
        """
        try:
            # Obtener usuario
            user = await self.session.get(User, user_id)
            if not user:
                logger.error(L("gift.user.user_not_found").format(user_id=user_id))
                return False

            # Verificar que el content set existe
            content_set = await self.content_service.get_content_set(content_set_id)
            if not content_set:
                logger.error(L("gift.user.content_set_not_found").format(content_set_id=content_set_id))
                return False

            # Generar mensaje de contexto
            if custom_message:
                context_message = custom_message
            else:
                context_message = self._build_context_message(
                    event_type=event_type,
                    username=user.username or "bella alma",
                    context_data=context_data or {}
                )

            # Enviar el regalo
            success = await self.content_service.send_content_set(
                user_id=user_id,
                set_id=content_set_id,
                context_message=context_message,
                bot=bot,
                trigger_type=event_type,
                sent_by_admin=sent_by_admin
            )

            if success:
                logger.info(f"Regalo {content_set_id} enviado a usuario {user_id} por evento {event_type}")
                return True
            else:
                logger.error(L("gift.user.send_error").format(content_set_id=content_set_id, user_id=user_id))
                return False

        except Exception as e:
            logger.error(L("gift.user.generic_error").format(user_id=user_id, error=e))
            return False

    def _build_context_message(
        self,
        event_type: str,
        username: str,
        context_data: Dict
    ) -> str:
        """
        Construye el mensaje de contexto según el tipo de evento

        Args:
            event_type: Tipo de evento
            username: Nombre del usuario
            context_data: Datos adicionales para el template

        Returns:
            Mensaje formateado
        """
        template = GIFT_MESSAGES.get(event_type, GIFT_MESSAGES["surprise"])

        # Preparar datos para el formato
        format_data = {
            "username": username,
            **context_data
        }

        try:
            message = template["message"].format(**format_data)
            return message
        except KeyError as e:
            logger.warning(f"Falta clave en context_data para {event_type}: {e}")
            # Fallback a mensaje de sorpresa
            return GIFT_MESSAGES["surprise"]["message"].format(username=username)

    async def send_auction_won_gift(
        self,
        user_id: int,
        auction_name: str,
        bot: Bot,
        content_set_id: str = "auction_winner_gift"
    ) -> bool:
        """
        Envía regalo por ganar una subasta

        Args:
            user_id: ID del usuario que ganó
            auction_name: Nombre de la subasta
            bot: Instancia del bot
            content_set_id: ID del content set (por defecto: auction_winner_gift)

        Returns:
            True si se envió
        """
        return await self.send_gift(
            user_id=user_id,
            content_set_id=content_set_id,
            event_type="auction_won",
            bot=bot,
            context_data={"item_name": auction_name}
        )

    async def send_shop_purchase_gift(
        self,
        user_id: int,
        item_name: str,
        bot: Bot,
        content_set_id: str = "shop_thank_you_gift"
    ) -> bool:
        """
        Envía regalo por compra en la tienda

        Args:
            user_id: ID del usuario
            item_name: Nombre del item comprado
            bot: Instancia del bot
            content_set_id: ID del content set

        Returns:
            True si se envió
        """
        return await self.send_gift(
            user_id=user_id,
            content_set_id=content_set_id,
            event_type="shop_purchase",
            bot=bot,
            context_data={"item_name": item_name}
        )

    async def send_level_reached_gift(
        self,
        user_id: int,
        level: int,
        bot: Bot,
        content_set_id: str = "level_milestone_gift"
    ) -> bool:
        """
        Envía regalo por alcanzar un nivel

        Args:
            user_id: ID del usuario
            level: Nivel alcanzado
            bot: Instancia del bot
            content_set_id: ID del content set

        Returns:
            True si se envió
        """
        return await self.send_gift(
            user_id=user_id,
            content_set_id=content_set_id,
            event_type="level_reached",
            bot=bot,
            context_data={"level": level}
        )

    async def send_surprise_gift(
        self,
        user_id: int,
        content_set_id: str,
        bot: Bot,
        custom_message: Optional[str] = None,
        sent_by_admin: bool = True
    ) -> bool:
        """
        Envía un regalo sorpresa sin evento específico

        Args:
            user_id: ID del usuario
            content_set_id: ID del content set
            bot: Instancia del bot
            custom_message: Mensaje personalizado (opcional)
            sent_by_admin: Marca como enviado por admin

        Returns:
            True si se envió
        """
        return await self.send_gift(
            user_id=user_id,
            content_set_id=content_set_id,
            event_type="surprise",
            bot=bot,
            custom_message=custom_message,
            sent_by_admin=sent_by_admin
        )

    async def send_loyalty_gift(
        self,
        user_id: int,
        days_active: int,
        bot: Bot,
        content_set_id: str = "loyalty_reward_gift"
    ) -> bool:
        """
        Envía regalo por lealtad (días activos)

        Args:
            user_id: ID del usuario
            days_active: Días desde que se registró
            bot: Instancia del bot
            content_set_id: ID del content set

        Returns:
            True si se envió
        """
        return await self.send_gift(
            user_id=user_id,
            content_set_id=content_set_id,
            event_type="loyalty",
            bot=bot,
            context_data={"days": days_active}
        )

    async def has_received_gift_for_event(
        self,
        user_id: int,
        event_type: str,
        content_set_id: Optional[str] = None
    ) -> bool:
        """
        Verifica si un usuario ya recibió un regalo por un evento específico

        Args:
            user_id: ID del usuario
            event_type: Tipo de evento
            content_set_id: ID del content set (opcional)

        Returns:
            True si ya recibió un regalo por este evento
        """
        conditions = [
            GiftRecord.user_id == user_id,
            GiftRecord.trigger_type == event_type
        ]

        if content_set_id:
            conditions.append(GiftRecord.content_set_id == content_set_id)

        stmt = select(func.count()).select_from(GiftRecord).where(and_(*conditions))
        result = await self.session.execute(stmt)
        count = result.scalar()

        return count > 0

    async def get_user_gifts_by_event(
        self,
        user_id: int,
        event_type: Optional[str] = None
    ) -> List[GiftRecord]:
        """
        Obtiene todos los regalos recibidos por un usuario

        Args:
            user_id: ID del usuario
            event_type: Filtrar por tipo de evento (opcional)

        Returns:
            Lista de GiftRecords
        """
        conditions = [GiftRecord.user_id == user_id]

        if event_type:
            conditions.append(GiftRecord.trigger_type == event_type)

        stmt = (
            select(GiftRecord)
            .where(and_(*conditions))
            .order_by(GiftRecord.sent_at.desc())
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_gift_stats(self) -> Dict:
        """
        Obtiene estadísticas generales de regalos enviados

        Returns:
            Diccionario con estadísticas
        """
        # Total de regalos enviados
        stmt = select(func.count(GiftRecord.id))
        result = await self.session.execute(stmt)
        total_gifts = result.scalar()

        # Regalos por tipo de evento
        stmt = (
            select(
                GiftRecord.trigger_type,
                func.count(GiftRecord.id).label("count")
            )
            .group_by(GiftRecord.trigger_type)
        )
        result = await self.session.execute(stmt)
        gifts_by_type = {row[0]: row[1] for row in result.all()}

        # Usuarios únicos que recibieron regalos
        stmt = select(func.count(func.distinct(GiftRecord.user_id)))
        result = await self.session.execute(stmt)
        unique_users = result.scalar()

        # Regalos enviados por admin vs automáticos
        stmt = select(func.count(GiftRecord.id)).where(GiftRecord.sent_by_admin == True)
        result = await self.session.execute(stmt)
        admin_gifts = result.scalar()

        return {
            "total_gifts": total_gifts,
            "gifts_by_type": gifts_by_type,
            "unique_users": unique_users,
            "admin_gifts": admin_gifts,
            "automatic_gifts": total_gifts - admin_gifts
        }

    async def list_available_gift_sets(self, tier: Optional[str] = None) -> List[ContentSet]:
        """
        Lista content sets disponibles para usar como regalos

        Args:
            tier: Filtrar por tier (opcional)

        Returns:
            Lista de ContentSets
        """
        return await self.content_service.list_content_sets(
            tier=tier or "gift",
            active_only=True
        )
