"""
User Journey Service - Gestión del viaje del usuario

Maneja la progresión automática del usuario a través de los milestones:
- Day 1: Bienvenida con primera mirada
- Day 7: Oferta VIP con cupón
- Day 30: Celebración mensual / última oferta
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from aiogram import Bot

from database.models import User, UserMilestone, ContentSet
from services.content_service import ContentService

logger = logging.getLogger(__name__)


class UserJourneyService:
    """Servicio para gestionar el journey del usuario"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.content_service = ContentService(session)

    async def initialize_user_milestones(self, user_id: int) -> None:
        """
        Inicializa los milestones para un nuevo usuario

        Se llama cuando un usuario se registra por primera vez.
        Crea registros de milestone para day_1, day_7, day_30

        Args:
            user_id: ID del usuario
        """
        milestone_types = ["day_1", "day_7", "day_30"]

        for milestone_type in milestone_types:
            # Verificar si ya existe
            stmt = select(UserMilestone).where(
                and_(
                    UserMilestone.user_id == user_id,
                    UserMilestone.milestone_type == milestone_type
                )
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                milestone = UserMilestone(
                    user_id=user_id,
                    milestone_type=milestone_type,
                    completed=False,
                    data={}
                )
                self.session.add(milestone)

        await self.session.commit()
        logger.info(f"Milestones inicializados para usuario {user_id}")

    async def get_users_for_milestone(self, milestone_type: str) -> List[User]:
        """
        Obtiene usuarios que alcanzaron un milestone específico pero no lo han completado

        Args:
            milestone_type: "day_1", "day_7", "day_30"

        Returns:
            Lista de usuarios que alcanzaron el milestone
        """
        # Calcular días desde registro según milestone
        days_map = {
            "day_1": 1,
            "day_7": 7,
            "day_30": 30
        }

        days_required = days_map.get(milestone_type, 1)
        cutoff_date = datetime.utcnow() - timedelta(days=days_required)

        # Query: usuarios registrados hace X días que no completaron el milestone
        stmt = (
            select(User)
            .join(UserMilestone, User.id == UserMilestone.user_id)
            .where(
                and_(
                    User.created_at <= cutoff_date,
                    UserMilestone.milestone_type == milestone_type,
                    UserMilestone.completed == False
                )
            )
        )

        result = await self.session.execute(stmt)
        users = result.scalars().all()

        logger.info(f"Encontrados {len(users)} usuarios para milestone {milestone_type}")
        return users

    async def mark_milestone_completed(
        self,
        user_id: int,
        milestone_type: str,
        data: Optional[Dict] = None
    ) -> bool:
        """
        Marca un milestone como completado

        Args:
            user_id: ID del usuario
            milestone_type: Tipo de milestone
            data: Metadata adicional (opcional)

        Returns:
            True si se marcó correctamente
        """
        stmt = select(UserMilestone).where(
            and_(
                UserMilestone.user_id == user_id,
                UserMilestone.milestone_type == milestone_type
            )
        )

        result = await self.session.execute(stmt)
        milestone = result.scalar_one_or_none()

        if not milestone:
            logger.warning(f"Milestone {milestone_type} no encontrado para usuario {user_id}")
            return False

        milestone.completed = True
        milestone.completed_at = datetime.utcnow()

        if data:
            milestone.data = data

        await self.session.commit()
        logger.info(f"Milestone {milestone_type} completado para usuario {user_id}")
        return True

    async def is_milestone_completed(self, user_id: int, milestone_type: str) -> bool:
        """
        Verifica si un usuario ya completó un milestone

        Args:
            user_id: ID del usuario
            milestone_type: Tipo de milestone

        Returns:
            True si está completado
        """
        stmt = select(UserMilestone).where(
            and_(
                UserMilestone.user_id == user_id,
                UserMilestone.milestone_type == milestone_type
            )
        )

        result = await self.session.execute(stmt)
        milestone = result.scalar_one_or_none()

        return milestone.completed if milestone else False

    async def process_day_1_milestone(self, user: User, bot: Bot) -> bool:
        """
        Procesa el milestone del día 1

        Envía contenido de bienvenida "Primera Mirada"

        Args:
            user: Usuario que alcanzó el milestone
            bot: Instancia del bot

        Returns:
            True si se procesó correctamente
        """
        try:
            # Mensaje de bienvenida de Lucien
            welcome_message = (
                f"Hola {user.username or 'bella alma'} 💫\n\n"
                "Soy Lucien, el guardián de este espacio mágico.\n\n"
                "Diana me pidió que te diera la bienvenida y te mostrara "
                "un pequeño adelanto de lo que encontrarás aquí...\n\n"
                "Prepárate para tu primera mirada. ✨"
            )

            # Verificar si el content set existe
            content_set = await self.content_service.get_content_set("day_1_welcome")

            if content_set and content_set.file_ids:
                # Enviar set de bienvenida
                success = await self.content_service.send_content_set(
                    user_id=user.id,
                    set_id="day_1_welcome",
                    context_message=welcome_message,
                    bot=bot,
                    trigger_type="automatic",
                    sent_by_admin=False
                )

                if not success:
                    logger.warning(f"Error enviando content set day_1 a usuario {user.id}, enviando solo mensaje")
                    await bot.send_message(user.id, welcome_message)
            else:
                # Content set no existe o no tiene archivos, enviar solo mensaje
                logger.warning(f"Content set day_1_welcome no disponible, enviando solo mensaje a usuario {user.id}")
                await bot.send_message(user.id, welcome_message)

            # Marcar milestone como completado (incluso si no se envió contenido)
            await self.mark_milestone_completed(
                user_id=user.id,
                milestone_type="day_1",
                data={
                    "sent_at": datetime.utcnow().isoformat(),
                    "content_sent": bool(content_set and content_set.file_ids)
                }
            )
            logger.info(f"Day 1 milestone procesado para usuario {user.id}")
            return True

        except Exception as e:
            logger.error(f"Error procesando day_1 milestone para usuario {user.id}: {e}")
            return False

    async def process_day_7_milestone(self, user: User, bot: Bot) -> bool:
        """
        Procesa el milestone del día 7

        Envía oferta VIP con cupón de descuento

        Args:
            user: Usuario que alcanzó el milestone
            bot: Instancia del bot

        Returns:
            True si se procesó correctamente
        """
        try:
            # Verificar si ya es VIP
            if user.role == "vip":
                logger.info(f"Usuario {user.id} ya es VIP, saltando day_7 milestone")
                await self.mark_milestone_completed(user.id, "day_7", {"skipped": "already_vip"})
                return True

            # Mensaje de Lucien con oferta
            offer_message = (
                f"{user.username or 'Querida alma'} 💎\n\n"
                "Ha pasado una semana desde que nos conocimos, y Diana "
                "ha notado tu interés por este mundo...\n\n"
                "Quiere ofrecerte algo especial: acceso exclusivo VIP "
                "con un descuento único para ti.\n\n"
                "🎁 **Código de descuento:** `PRIMERA_VEZ`\n"
                "💫 **15% de descuento** en tu primera suscripción VIP\n\n"
                "Este código es solo para ti y expira en 48 horas.\n\n"
                "¿Lista para desbloquear todo el contenido exclusivo? 🔥"
            )

            # Enviar mensaje con oferta
            await bot.send_message(user.id, offer_message)

            # Opcional: Enviar set teaser VIP (si existe y tiene archivos)
            teaser_set = await self.content_service.get_content_set("day_7_vip_teaser")
            if teaser_set and teaser_set.file_ids:
                try:
                    await self.content_service.send_content_set(
                        user_id=user.id,
                        set_id="day_7_vip_teaser",
                        context_message="",
                        bot=bot,
                        trigger_type="automatic",
                        sent_by_admin=False
                    )
                    logger.info(f"Teaser VIP enviado a usuario {user.id}")
                except Exception as e:
                    logger.warning(f"Error enviando teaser VIP a usuario {user.id}: {e}")
            else:
                logger.debug(f"Teaser VIP day_7 no disponible para usuario {user.id}")

            # Marcar milestone como completado
            await self.mark_milestone_completed(
                user_id=user.id,
                milestone_type="day_7",
                data={
                    "sent_at": datetime.utcnow().isoformat(),
                    "discount_code": "PRIMERA_VEZ",
                    "expires_at": (datetime.utcnow() + timedelta(hours=48)).isoformat()
                }
            )

            logger.info(f"Day 7 milestone procesado para usuario {user.id}")
            return True

        except Exception as e:
            logger.error(f"Error procesando day_7 milestone para usuario {user.id}: {e}")
            return False

    async def process_day_30_milestone(self, user: User, bot: Bot) -> bool:
        """
        Procesa el milestone del día 30

        Envía celebración mensual o última oferta si no es VIP

        Args:
            user: Usuario que alcanzó el milestone
            bot: Instancia del bot

        Returns:
            True si se procesó correctamente
        """
        try:
            if user.role == "vip":
                # Mensaje de celebración para VIP
                celebration_message = (
                    f"¡{user.username or 'Bella alma'}! 🎉\n\n"
                    "¡Ha pasado un mes desde que te uniste a nosotros!\n\n"
                    "Diana quiere agradecerte por ser parte de nuestra "
                    "comunidad VIP. Tu apoyo hace posible todo esto. 💖\n\n"
                    "Como agradecimiento, te envío algo especial..."
                )

                # Enviar regalo especial para VIP (si existe y tiene archivos)
                gift_set = await self.content_service.get_content_set("day_30_vip_gift")
                if gift_set and gift_set.file_ids:
                    try:
                        await self.content_service.send_content_set(
                            user_id=user.id,
                            set_id="day_30_vip_gift",
                            context_message=celebration_message,
                            bot=bot,
                            trigger_type="automatic",
                            sent_by_admin=False
                        )
                        logger.info(f"Regalo VIP day_30 enviado a usuario {user.id}")
                    except Exception as e:
                        logger.warning(f"Error enviando regalo VIP day_30 a usuario {user.id}: {e}")
                        await bot.send_message(user.id, celebration_message)
                else:
                    # No hay regalo, solo enviar mensaje
                    logger.debug(f"Regalo VIP day_30 no disponible, solo mensaje a usuario {user.id}")
                    await bot.send_message(user.id, celebration_message)

            else:
                # Última oferta para no-VIP
                final_offer_message = (
                    f"{user.username or 'Querida alma'} ✨\n\n"
                    "Ha pasado un mes desde que nos conociste, y aunque "
                    "te hemos visto por aquí, aún no has dado el paso...\n\n"
                    "Diana quiere darte una última oportunidad especial:\n\n"
                    "🎁 **Código exclusivo:** `MESUNO`\n"
                    "💎 **20% de descuento** en cualquier suscripción VIP\n\n"
                    "Este es nuestro mejor descuento y expira en 72 horas.\n\n"
                    "Si decides quedarte con el contenido gratuito, está bien, "
                    "seguiremos compartiendo sorpresas contigo de vez en cuando. 💫\n\n"
                    "Pero si quieres ver TODO lo que Diana tiene para ofrecerte, "
                    "esta es tu oportunidad. 🔥"
                )

                await bot.send_message(user.id, final_offer_message)

            # Marcar milestone como completado
            await self.mark_milestone_completed(
                user_id=user.id,
                milestone_type="day_30",
                data={
                    "sent_at": datetime.utcnow().isoformat(),
                    "is_vip": (user.role == "vip"),
                    "discount_code": None if (user.role == "vip") else "MESUNO"
                }
            )

            logger.info(f"Day 30 milestone procesado para usuario {user.id}")
            return True

        except Exception as e:
            logger.error(f"Error procesando day_30 milestone para usuario {user.id}: {e}")
            return False

    async def process_all_milestones(self, bot: Bot) -> Dict[str, int]:
        """
        Procesa todos los milestones pendientes para todos los usuarios

        Se ejecuta diariamente por el scheduler

        Args:
            bot: Instancia del bot

        Returns:
            Diccionario con contadores de procesamiento
        """
        stats = {
            "day_1_processed": 0,
            "day_7_processed": 0,
            "day_30_processed": 0,
            "errors": 0
        }

        # Procesar Day 1
        day_1_users = await self.get_users_for_milestone("day_1")
        for user in day_1_users:
            try:
                success = await self.process_day_1_milestone(user, bot)
                if success:
                    stats["day_1_processed"] += 1
                else:
                    stats["errors"] += 1
            except Exception as e:
                logger.error(f"Error procesando day_1 para usuario {user.id}: {e}")
                stats["errors"] += 1

        # Procesar Day 7
        day_7_users = await self.get_users_for_milestone("day_7")
        for user in day_7_users:
            try:
                success = await self.process_day_7_milestone(user, bot)
                if success:
                    stats["day_7_processed"] += 1
                else:
                    stats["errors"] += 1
            except Exception as e:
                logger.error(f"Error procesando day_7 para usuario {user.id}: {e}")
                stats["errors"] += 1

        # Procesar Day 30
        day_30_users = await self.get_users_for_milestone("day_30")
        for user in day_30_users:
            try:
                success = await self.process_day_30_milestone(user, bot)
                if success:
                    stats["day_30_processed"] += 1
                else:
                    stats["errors"] += 1
            except Exception as e:
                logger.error(f"Error procesando day_30 para usuario {user.id}: {e}")
                stats["errors"] += 1

        logger.info(f"Procesamiento de milestones completado: {stats}")
        return stats
