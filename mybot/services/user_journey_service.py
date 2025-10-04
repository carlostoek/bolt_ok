"""
User Journey Service - Gestión del viaje del usuario

Maneja la progresión automática del usuario a través de los milestones:
- Day 1: Bienvenida con primera mirada
- Day 7: Oferta VIP con cupón
- Day 30: Celebración mensual / última oferta
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
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

        # STRATEGIC: Sistema de onboarding progresivo mejorado
        onboarding_milestone = UserMilestone(
            user_id=user_id,
            milestone_type="onboarding_complete",
            completed=False,
            data={
                "current_step": 0, 
                "total_steps": 5,
                "steps_completed": [],
                "last_interaction": datetime.utcnow().isoformat(),
                "personalized_tips": []
            }
        )
        self.session.add(onboarding_milestone)
        
        # Crear steps individuales de onboarding para tracking granular
        onboarding_steps = [
            {"step_type": "welcome", "completed": False, "data": {}},
            {"step_type": "narrative_intro", "completed": False, "data": {}},
            {"step_type": "missions_intro", "completed": False, "data": {}},
            {"step_type": "points_explained", "completed": False, "data": {}},
            {"step_type": "first_interaction", "completed": False, "data": {}},
        ]
        
        for step_data in onboarding_steps:
            step = UserMilestone(
                user_id=user_id,
                milestone_type=f"onboarding_{step_data['step_type']}",
                completed=step_data["completed"],
                data=step_data["data"]
            )
            self.session.add(step)

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
        # MODO TESTING: Calcular MINUTOS desde registro según milestone
        minutes_map = {
            "day_1": 7,   # 7 minutos en lugar de 1 día
            "day_7": 15,  # 15 minutos en lugar de 7 días
            "day_30": 30  # 30 minutos en lugar de 30 días
        }

        minutes_required = minutes_map.get(milestone_type, 7)
        cutoff_date = datetime.utcnow() - timedelta(minutes=minutes_required)

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

    async def get_next_onboarding_step(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene el siguiente paso de onboarding para el usuario
        STRATEGIC: Sistema de onboarding progresivo inteligente
        """
        stmt = select(UserMilestone).where(
            and_(
                UserMilestone.user_id == user_id,
                UserMilestone.milestone_type.like("onboarding_%"),
                UserMilestone.completed == False
            )
        ).order_by(UserMilestone.id)
        
        result = await self.session.execute(stmt)
        next_step = result.scalars().first()
        
        if next_step:
            return {
                "step_type": next_step.milestone_type.replace("onboarding_", ""),
                "milestone": next_step
            }
        return None

    async def complete_onboarding_step(self, user_id: int, step_type: str, data: Dict = None) -> bool:
        """
        Marca un paso de onboarding como completado
        """
        stmt = select(UserMilestone).where(
            and_(
                UserMilestone.user_id == user_id,
                UserMilestone.milestone_type == f"onboarding_{step_type}"
            )
        )
        
        result = await self.session.execute(stmt)
        step = result.scalar_one_or_none()
        
        if step:
            step.completed = True
            step.completed_at = datetime.utcnow()
            if data:
                step.data = data
            await self.session.commit()
            
            # Actualizar milestone principal de onboarding
            main_stmt = select(UserMilestone).where(
                and_(
                    UserMilestone.user_id == user_id,
                    UserMilestone.milestone_type == "onboarding_complete"
                )
            )
            main_result = await self.session.execute(main_stmt)
            main_milestone = main_result.scalar_one_or_none()
            
            if main_milestone:
                current_data = main_milestone.data or {}
                completed_steps = current_data.get("steps_completed", [])
                completed_steps.append(step_type)
                current_data["steps_completed"] = completed_steps
                current_data["current_step"] = len(completed_steps)
                main_milestone.data = current_data
                
                # Marcar como completado si todos los steps están hechos
                if len(completed_steps) >= current_data.get("total_steps", 5):
                    main_milestone.completed = True
                    main_milestone.completed_at = datetime.utcnow()
                
                await self.session.commit()
            
            return True
        return False

    async def send_contextual_onboarding_message(self, user: User, bot: Bot, context: str) -> bool:
        """
        Envía mensajes de onboarding contextuales basados en la interacción del usuario
        STRATEGIC: Anticipación inteligente en onboarding
        """
        try:
            onboarding_messages = {
                "first_narrative_interaction": {
                    "message": (
                        "💫 **¡Excelente elección!**\n\n"
                        "Acabas de descubrir tu primer fragmento narrativo. "
                        "Cada elección que hagas revela más sobre tu historia personal.\n\n"
                        "✨ **Tip:** Completa misiones para desbloquear más fragmentos rápidamente."
                    ),
                    "step_to_complete": "narrative_intro"
                },
                "first_mission_complete": {
                    "message": (
                        "🎯 **¡Primera misión completada!**\n\n"
                        "Has ganado tus primeros besitos. "
                        "Estos te permitirán acceder a contenido exclusivo y recompensas especiales.\n\n"
                        "💰 **Tip:** Acumula besitos para desbloquear sets fotográficos y experiencias únicas."
                    ),
                    "step_to_complete": "missions_intro"
                },
                "first_points_earned": {
                    "message": (
                        "💰 **¡Besitos ganados!**\n\n"
                        "Los besitos son tu moneda en este mundo. "
                        "Úsalos para:\n"
                        "• Desbloquear contenido exclusivo\n"
                        "• Participar en subastas\n"
                        "• Comprar en la tienda\n\n"
                        "🛍️ **Tip:** Visita /shop para ver las recompensas disponibles."
                    ),
                    "step_to_complete": "points_explained"
                },
                "first_shop_visit": {
                    "message": (
                        "🛍️ **Bienvenido a la tienda**\n\n"
                        "Aquí puedes canjear tus besitos por recompensas exclusivas.\n\n"
                        "💎 **Recomendación:** Comienza con los sets básicos "
                        "y ve subiendo según acumules más besitos.\n\n"
                        "✨ **Próximo paso:** ¡Sigue explorando la narrativa!"
                    ),
                    "step_to_complete": None  # No specific step, just guidance
                }
            }
            
            if context in onboarding_messages:
                message_data = onboarding_messages[context]
                
                await bot.send_message(
                    user.id,
                    message_data["message"],
                    parse_mode="Markdown"
                )
                
                # Completar step si corresponde
                if message_data["step_to_complete"]:
                    await self.complete_onboarding_step(user.id, message_data["step_to_complete"])
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error enviando onboarding contextual para usuario {user.id}: {e}")
            return False

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

    async def get_intelligent_suggestions(self, user_id: int) -> List[Dict[str, str]]:
        """
        Genera sugerencias inteligentes basadas en el comportamiento del usuario
        STRATEGIC: Sistema de anticipación inteligente mejorado
        """
        suggestions = []
        
        try:
            # Obtener datos del usuario
            user_stmt = select(User).where(User.id == user_id)
            user_result = await self.session.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if not user:
                return suggestions
            
            # STRATEGIC: Sistema de scoring para priorizar sugerencias
            suggestion_scores = {}
            
            # 1. Sugerencia basada en puntos acumulados (score: 80)
            if user.points >= 1000 and user.points < 5000:
                suggestion_scores["shop_reminder"] = {
                    "type": "shop_reminder",
                    "title": "🎁 Tienes besitos para gastar",
                    "message": f"Tienes {user.points} besitos acumulados. ¡Visita la tienda para reclamar recompensas!",
                    "action": "/shop",
                    "score": 80
                }
            
            # 2. Sugerencia basada en tiempo desde última interacción (score: 60-90)
            from datetime import datetime
            if user.last_interaction:
                time_diff = datetime.utcnow() - user.last_interaction
                if time_diff.days >= 2:
                    score = min(90, 60 + (time_diff.days * 10))  # Más días = mayor prioridad
                    suggestion_scores["re_engagement"] = {
                        "type": "re_engagement",
                        "title": "💫 Te extrañamos",
                        "message": "Tu historia te espera. ¿Quieres continuar donde lo dejaste?",
                        "action": "/start",
                        "score": score
                    }
            
            # 3. Sugerencia basada en progreso de misiones (score: 70)
            try:
                from services.mission_service import MissionService
                mission_service = MissionService(self.session)
                active_missions = await mission_service.get_active_missions(user_id)
                
                if len(active_missions) == 0:
                    suggestion_scores["mission_suggestion"] = {
                        "type": "mission_suggestion", 
                        "title": "🎯 Nuevos desafíos disponibles",
                        "message": "Hay nuevas misiones esperándote. ¡Complétalas para ganar más besitos!",
                        "action": "/missions",
                        "score": 70
                    }
            except Exception as e:
                logger.debug(f"No se pudieron obtener misiones para sugerencias: {e}")
            
            # 4. Sugerencia basada en onboarding incompleto (score: 100 - máxima prioridad)
            next_step = await self.get_next_onboarding_step(user_id)
            if next_step:
                step_type = next_step["step_type"]
                onboarding_suggestions = {
                    "narrative_intro": {
                        "title": "📖 Comienza tu historia",
                        "message": "Aún no has explorado la narrativa principal. ¡Descubre tu primer fragmento!",
                        "action": "/start",
                        "score": 100
                    },
                    "missions_intro": {
                        "title": "🎯 Tus primeras misiones",
                        "message": "Completa tu primera misión para ganar besitos y recompensas.",
                        "action": "/missions", 
                        "score": 95
                    },
                    "points_explained": {
                        "title": "💰 Aprende sobre besitos",
                        "message": "Descubre cómo ganar y usar tus besitos en el sistema.",
                        "action": "/profile",
                        "score": 85
                    }
                }
                
                if step_type in onboarding_suggestions:
                    suggestion_scores[f"onboarding_{step_type}"] = onboarding_suggestions[step_type]
            
            # Ordenar sugerencias por score (mayor a menor) y tomar las top 3
            sorted_suggestions = sorted(
                suggestion_scores.values(), 
                key=lambda x: x["score"], 
                reverse=True
            )[:3]
            
            # Remover el campo score del resultado final
            for suggestion in sorted_suggestions:
                suggestion.pop("score", None)
                suggestions.append(suggestion)
                
        except Exception as e:
            logger.error(f"Error generando sugerencias inteligentes para usuario {user_id}: {e}")
        
        return suggestions

    async def send_intelligent_suggestions(self, user: User, bot: Bot, trigger: str = "automatic") -> bool:
        """
        Envía sugerencias inteligentes al usuario basadas en su comportamiento
        """
        try:
            suggestions = await self.get_intelligent_suggestions(user.id)
            
            if suggestions:
                # Seleccionar la sugerencia más relevante (por ahora la primera)
                suggestion = suggestions[0]
                
                message = f"**{suggestion['title']}**\n\n{suggestion['message']}"
                
                if trigger == "automatic":
                    # En automático, ser más discreto
                    message += f"\n\n💡 *Sugerencia: Usa* `{suggestion['action']}` *para continuar*"
                else:
                    # En respuesta a interacción, ser más directo
                    message += f"\n\n✨ *¿Te gustaría probar* `{suggestion['action']}` *ahora?*"
                
                await bot.send_message(
                    user.id,
                    message,
                    parse_mode="Markdown"
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error enviando sugerencias inteligentes para usuario {user.id}: {e}")
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
