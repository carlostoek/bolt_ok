"""
Middleware para gamificación de micro-interacciones
STRATEGIC: Sistema que premia engagement orgánico
"""
import logging
from typing import Any, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from datetime import datetime, timedelta
from sqlalchemy import select

logger = logging.getLogger(__name__)


class GamificationMiddleware(BaseMiddleware):
    """
    Middleware que detecta y premia micro-interacciones del usuario
    Transforma acciones simples en progreso gamificado
    """
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Any],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        # Ejecutar el handler primero
        result = await handler(event, data)
        
        # Procesar gamificación después (no bloqueante)
        try:
            await self._process_gamification(event, data)
        except Exception as e:
            logger.error(f"Error en gamification middleware: {e}")
        
        return result

    async def _process_gamification(self, event: Message | CallbackQuery, data: Dict[str, Any]):
        """Procesa la gamificación para la interacción actual"""
        session = data.get("session")
        user = data.get("user")
        bot = data.get("bot")
        
        if not all([session, user, bot]):
            return

        try:
            from services.user_journey_service import UserJourneyService
            from services.point_service import PointService
            from utils.messages import get_badge_unlock_message
            
            journey_service = UserJourneyService(session)
            point_service = PointService(session)
            
            # STRATEGIC: Logging de métricas
            interaction_type = "message" if isinstance(event, Message) else "callback"
            logger.info(f"🎮 Gamification processing: user={user.id}, type={interaction_type}")
            
            # Verificar y actualizar racha diaria
            streak_updated = await self._update_daily_streak(user, session, point_service, bot)
            if streak_updated:
                logger.info(f"🔥 Daily streak updated: user={user.id}")
            
            # Procesar badges por tipo de interacción
            badges_unlocked = 0
            if isinstance(event, Message):
                badges_unlocked = await self._process_message_interaction(event, user, journey_service, point_service, bot)
            elif isinstance(event, CallbackQuery):
                badges_unlocked = await self._process_callback_interaction(event, user, journey_service, point_service, bot)
            
            # STRATEGIC: Enviar sugerencias inteligentes periódicamente (10% de las veces)
            import random
            if random.random() < 0.1:  # 10% de probabilidad
                try:
                    suggestion_sent = await journey_service.send_intelligent_suggestions(user, bot, "automatic")
                    if suggestion_sent:
                        logger.info(f"💡 Intelligent suggestion sent: user={user.id}")
                except Exception as e:
                    logger.debug(f"No se pudo enviar sugerencia automática: {e}")
            
            # Log resumen de la gamificación
            if streak_updated or badges_unlocked > 0:
                logger.info(f"🎯 Gamification summary: user={user.id}, streaks={streak_updated}, badges={badges_unlocked}")
                
        except Exception as e:
            logger.error(f"Error procesando gamificación para usuario {user.id}: {e}")

    async def _update_daily_streak(self, user, session, point_service, bot):
        """Actualiza y premia la racha diaria del usuario"""
        from database.models import UserMilestone
        
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        # Obtener milestone de racha
        stmt = select(UserMilestone).where(
            UserMilestone.user_id == user.id,
            UserMilestone.milestone_type == "daily_streak"
        )
        result = await session.execute(stmt)
        streak_milestone = result.scalar_one_or_none()
        
        if not streak_milestone:
            # Primera interacción del día
            streak_milestone = UserMilestone(
                user_id=user.id,
                milestone_type="daily_streak",
                completed=False,
                data={"current_streak": 1, "last_interaction": today.isoformat()}
            )
            session.add(streak_milestone)
            
            # Premio por primer día
            await point_service.add_points(user.id, 10, "daily_streak_day_1")
            
        else:
            last_interaction = datetime.fromisoformat(streak_milestone.data.get("last_interaction")).date()
            current_streak = streak_milestone.data.get("current_streak", 0)
            
            if last_interaction == yesterday:
                # Racha continua
                current_streak += 1
                streak_milestone.data["current_streak"] = current_streak
                streak_milestone.data["last_interaction"] = today.isoformat()
                
                # Premios por racha
                if current_streak in [3, 7, 30]:
                    bonus_points = {3: 50, 7: 100, 30: 500}[current_streak]
                    await point_service.add_points(user.id, bonus_points, f"daily_streak_bonus_{current_streak}")
                    
                    # Enviar mensaje de racha
                    try:
                        from utils.messages import get_daily_streak_message
                        streak_message = get_daily_streak_message(current_streak)
                        await bot.send_message(user.id, streak_message, parse_mode="Markdown")
                    except Exception as e:
                        logger.debug(f"No se pudo enviar mensaje de racha: {e}")
                        
            elif last_interaction < yesterday:
                # Racha rota, reiniciar
                streak_milestone.data["current_streak"] = 1
                streak_milestone.data["last_interaction"] = today.isoformat()
        
        await session.commit()

    async def _process_message_interaction(self, event, user, journey_service, point_service, bot) -> int:
        """Procesa gamificación para mensajes - retorna número de badges desbloqueados"""
        badges_unlocked = 0
        
        try:
            # STRATEGIC: Detectar diferentes tipos de interacciones por mensaje
            if event.text and event.text.startswith('/'):
                command = event.text.split()[0]
                if command in ['/start', '/missions', '/shop', '/profile']:
                    command_name = command[1:]  # Remove the leading '/'
                    await journey_service.send_contextual_onboarding_message(
                        user, bot, f"first_{command_name}_visit"
                    )
            
            # STRATEGIC: Detectar interacciones específicas para badges
            message_text = event.text or ""
            message_text_lower = message_text.lower()
            
            # Badge por primera interacción extensa
            if len(message_text) > 20 and "diana" in message_text_lower:
                # Usuario mencionó a Diana en mensaje largo
                try:
                    from database.models import UserBadge
                    
                    # Verificar si ya tiene el badge
                    stmt = select(UserBadge).where(
                        UserBadge.user_id == user.id,
                        UserBadge.badge_type == "diana_mention"
                    )
                    result = await journey_service.session.execute(stmt)
                    existing_badge = result.scalar_one_or_none()
                    
                    if not existing_badge:
                        # Otorgar badge
                        new_badge = UserBadge(
                            user_id=user.id,
                            badge_type="diana_mention",
                            earned_at=datetime.utcnow()
                        )
                        journey_service.session.add(new_badge)
                        
                        # Otorgar puntos
                        await point_service.add_points(user.id, 25, "badge_diana_mention")
                        
                        # Enviar notificación
                        badge_message = (
                            "🏅 **¡Badge Desbloqueado!**\n\n"
                            "💬 **Mencionador de Diana**\n"
                            "Mencionaste a Diana en un mensaje significativo\n\n"
                            "💰 **Recompensa:** +25 besitos\n"
                            "✨ ¡Sigue conectando con la historia!"
                        )
                        
                        await bot.send_message(user.id, badge_message, parse_mode="Markdown")
                        badges_unlocked += 1
                        logger.info(f"🎖️ Badge unlocked: diana_mention for user={user.id}")
                        
                except Exception as badge_error:
                    logger.debug(f"No se pudo otorgar badge de mención: {badge_error}")
            
        except Exception as e:
            logger.error(f"Error en procesamiento de mensaje para gamificación: {e}")
        
        return badges_unlocked

    async def _process_callback_interaction(self, event, user, journey_service, point_service, bot):
        """Procesa gamificación para callback queries"""
        badges_unlocked = 0
        
        try:
            # Detectar interacciones específicas por callback data
            callback_data = event.data
            
            if callback_data and "mission" in callback_data:
                # El usuario está interactuando con misiones
                await journey_service.complete_onboarding_step(user.id, "first_interaction")
                
            # También detectar interacciones con la tienda
            if callback_data and "shop" in callback_data:
                await journey_service.send_contextual_onboarding_message(
                    user, bot, "first_shop_visit"
                )
            
            # Otorgar puntos por interacción básica de callback - usando keyword arguments
            await point_service.add_points(user.id, 1, reason="callback_interaction")
            
        except Exception as e:
            logger.error(f"Error en procesamiento de callback para gamificación: {e}")
        
        return badges_unlocked
