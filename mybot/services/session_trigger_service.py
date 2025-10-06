"""
Session Trigger Service - Detecta momentos óptimos para ofrecer sesiones individuales

Triggers automáticos:
1. Usuario completa fragmento narrativo con alta intensidad emocional
2. Usuario gana subasta importante (>300 besitos)
3. Usuario alcanza 60 días como VIP (lealtad)
4. Usuario ha tenido alta actividad (5+ reacciones en 24h)

Cada trigger respeta cooldown de 7 días para no saturar.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import User
from aiogram import Bot
from utils.messages import BOT_MESSAGES
from keyboards.besitos_kb import get_session_interest_kb

logger = logging.getLogger(__name__)


class SessionTriggerService:
    """Servicio para detectar y activar ofertas de sesión individual en momentos óptimos"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_and_trigger(
        self,
        user_id: int,
        trigger_type: str,
        bot: Bot,
        context_data: Optional[Dict] = None
    ) -> bool:
        """
        Evalúa si es momento de ofrecer sesión individual

        Args:
            user_id: ID del usuario
            trigger_type: Tipo de trigger ("emotional_narrative", "high_auction", "loyalty_60days", "high_activity")
            bot: Instancia del bot
            context_data: Datos adicionales del contexto (fragment_title, auction_value, etc.)

        Returns:
            True si se envió la oferta, False si no
        """
        try:
            user = await self.session.get(User, user_id)
            if not user:
                return False

            # Solo para VIPs
            if user.role != "vip":
                logger.debug(f"User {user_id} is not VIP, skipping session trigger")
                return False

            # Verificar cooldown (7 días desde última oferta)
            if not await self._check_cooldown(user):
                logger.debug(f"User {user_id} is in cooldown period, skipping session trigger")
                return False

            # Verificar antigüedad VIP mínima (30 días)
            days_vip = self._get_days_as_vip(user)
            if days_vip < 30:
                logger.debug(f"User {user_id} has been VIP for {days_vip} days, minimum is 30")
                return False

            # Determinar tipo de oferta según trigger
            offer = self._get_offer_for_trigger(trigger_type, user, context_data or {})
            if not offer:
                logger.warning(f"No offer defined for trigger type: {trigger_type}")
                return False

            # Enviar oferta
            await self._send_session_offer(user_id, bot, offer)

            # Actualizar timestamp de última oferta
            user.last_session_offer_at = datetime.utcnow()
            await self.session.commit()

            logger.info(f"Session offer sent to user {user_id} via trigger {trigger_type}")
            return True

        except Exception as e:
            logger.error(f"Error checking session trigger for user {user_id}: {e}", exc_info=True)
            return False

    async def _check_cooldown(self, user: User) -> bool:
        """Verifica si pasaron al menos 7 días desde última oferta"""
        if not hasattr(user, 'last_session_offer_at') or not user.last_session_offer_at:
            return True  # Nunca se le ofreció, ok

        days_since_last = (datetime.utcnow() - user.last_session_offer_at).days
        return days_since_last >= 7

    def _get_days_as_vip(self, user: User) -> int:
        """Calcula días que el usuario ha sido VIP"""
        if not user.vip_since:
            return 0
        return (datetime.utcnow() - user.vip_since).days

    def _get_offer_for_trigger(self, trigger_type: str, user: User, context: Dict) -> Optional[Dict]:
        """Determina qué oferta mostrar según el tipo de trigger"""

        if trigger_type == "emotional_narrative":
            # Usuario completó fragmento emocional intenso
            fragment_title = context.get("fragment_title", "ese fragmento")
            return {
                "message_key": "session_emotional_narrative",
                "message_data": {},
                "session_type": "emotional_narrative",
                "title": "💫 Diana te sintió..."
            }

        elif trigger_type == "high_auction":
            # Usuario ganó subasta con puja alta
            auction_value = context.get("auction_value", 0)
            return {
                "message_key": "session_high_auction_offer",
                "message_data": {"auction_value": auction_value},
                "session_type": "vip_special",
                "title": "🏆 ¡Ganaste! Y Diana lo notó."
            }

        elif trigger_type == "loyalty_60days":
            # Usuario cumplió 60 días VIP
            days_vip = self._get_days_as_vip(user)
            return {
                "message_key": "session_loyalty_discount",
                "message_data": {},
                "session_type": "loyalty_discount",
                "title": "🎁 Regalo de Lealtad - 60 Días"
            }

        elif trigger_type == "high_activity":
            # Usuario muy activo (5+ reacciones en 24h)
            return {
                "message_key": "session_standard_offer",
                "message_data": {},
                "session_type": "vip_special",
                "title": "💋 Diana notó tu actividad"
            }

        return None

    async def _send_session_offer(self, user_id: int, bot: Bot, offer: Dict):
        """Envía oferta de sesión individual al usuario"""
        try:
            # Obtener mensaje
            message_key = offer.get("message_key")
            message = BOT_MESSAGES.get(message_key, "")

            # Formatear con datos si existen
            message_data = offer.get("message_data", {})
            if message_data:
                try:
                    message = message.format(**message_data)
                except KeyError:
                    pass  # Si falta algún dato, usar sin formatear

            # Obtener keyboard
            session_type = offer.get("session_type", "standard")
            keyboard = get_session_interest_kb(session_type)

            # Enviar mensaje
            await bot.send_message(
                user_id,
                message,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error sending session offer to user {user_id}: {e}", exc_info=True)
            raise

    async def trigger_on_narrative_completion(
        self,
        user_id: int,
        fragment_key: str,
        bot: Bot
    ) -> bool:
        """
        Trigger cuando usuario completa fragmento narrativo

        Solo activa si el fragmento tiene alta intensidad emocional
        """
        # Fragmentos que califican como "intensos emocionalmente"
        # (puedes expandir esta lista según tu narrativa)
        emotional_fragments = [
            "L1F10",  # Final del nivel 1
            "L2F8",   # Momento dramático nivel 2
            "L3F5",   # Revelación importante
            "L3F10",  # Final del nivel 3
        ]

        # Verificar si el fragmento califica
        if fragment_key not in emotional_fragments:
            return False

        return await self.check_and_trigger(
            user_id=user_id,
            trigger_type="emotional_narrative",
            bot=bot,
            context_data={"fragment_key": fragment_key}
        )

    async def trigger_on_auction_win(
        self,
        user_id: int,
        auction_value: int,
        bot: Bot
    ) -> bool:
        """
        Trigger cuando usuario gana subasta

        Solo activa si pujó fuerte (>300 besitos)
        """
        # Umbral para considerar "puja alta"
        HIGH_BID_THRESHOLD = 300

        if auction_value < HIGH_BID_THRESHOLD:
            logger.debug(f"Auction value {auction_value} below threshold {HIGH_BID_THRESHOLD}")
            return False

        return await self.check_and_trigger(
            user_id=user_id,
            trigger_type="high_auction",
            bot=bot,
            context_data={"auction_value": auction_value}
        )

    async def trigger_on_loyalty_milestone(
        self,
        user_id: int,
        bot: Bot
    ) -> bool:
        """
        Trigger cuando usuario alcanza 60 días VIP

        Se ejecuta automáticamente por el scheduler de milestones
        """
        user = await self.session.get(User, user_id)
        if not user:
            return False

        days_vip = self._get_days_as_vip(user)

        # Solo activar exactamente en día 60 (no antes ni después)
        if days_vip != 60:
            return False

        return await self.check_and_trigger(
            user_id=user_id,
            trigger_type="loyalty_60days",
            bot=bot,
            context_data={"days_vip": days_vip}
        )

    async def check_all_loyalty_milestones(self, bot: Bot) -> int:
        """
        Revisa todos los usuarios VIP y activa trigger de 60 días si aplica

        Se ejecuta diariamente por el scheduler

        Returns:
            Número de ofertas de sesión enviadas
        """
        stats = {
            "checked": 0,
            "offers_sent": 0,
            "errors": 0
        }

        try:
            # Obtener todos los VIPs con 60 días exactos desde created_at
            today = datetime.utcnow().date()
            target_date = today - timedelta(days=60)

            from sqlalchemy import cast, Date
            from database.models import VipSubscription

            # Buscar suscripciones VIP creadas hace exactamente 60 días
            stmt = select(VipSubscription).join(
                User, VipSubscription.user_id == User.id
            ).where(
                User.role == "vip",
                cast(VipSubscription.created_at, Date) == target_date
            )

            result = await self.session.execute(stmt)
            subscriptions = result.scalars().all()

            stats["checked"] = len(subscriptions)

            for sub in subscriptions:
                try:
                    success = await self.trigger_on_loyalty_milestone(sub.user_id, bot)
                    if success:
                        stats["offers_sent"] += 1
                except Exception as e:
                    logger.error(f"Error processing loyalty milestone for user {sub.user_id}: {e}")
                    stats["errors"] += 1

            logger.info(f"Loyalty milestone check complete: {stats}")
            return stats["offers_sent"]  # Retornar solo el count de ofertas enviadas

        except Exception as e:
            logger.error(f"Error in check_all_loyalty_milestones: {e}", exc_info=True)
            return 0  # Retornar 0 en caso de error
