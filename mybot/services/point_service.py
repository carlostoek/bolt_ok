from typing import List, Optional, Tuple, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User, UserStats
from database.transaction_models import PointTransaction
from utils.user_roles import get_points_multiplier
from aiogram import Bot
from services.interfaces import IPointService, INotificationService
from services.level_service import LevelService
from services.achievement_service import AchievementService
from services.event_service import EventService
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# MVP Economic Rules Configuration
POINTS_CONFIG = {
    'story_fragment_completion': 10,
    'decision_made': 5,
    'daily_login': 15,
    'mission_completed': 25,
    'achievement_unlocked': 50,
    'channel_reaction': 2,
    'vip_bonus_multiplier': 1.5,
    'message_sent': 1,
    'poll_participation': 2,
    'checkin_daily': 10,
    'reaction_processed': 0.5
}

# Diana's character-consistent reward messages in Spanish
DIANA_REWARD_MESSAGES = {
    'besitos_earned': [
        "Mmm... has ganado {points} besitos más, cariño. Ya tienes {total} en total. ¿Te gusta coleccionarlos para mí? 💋",
        "Qué dulce... {points} besitos nuevos han llegado a ti. Con {total} besitos, te acercas más a mis secretos... 😘",
        "Has conseguido {points} besitos, mi querido. {total} besitos en total... cada uno es como un susurro mío. 💫"
    ],
    'level_up': [
        "¡Oh, mi amor! Has alcanzado el nivel {level}... Me impresionas cada día más. ¿Qué harás con este nuevo poder? 💎",
        "Nivel {level}... Interesante. Cada nivel que subes me permite mostrarte algo más de quien soy realmente... 🌹",
        "Has llegado al nivel {level}, cariño. Mis secretos se revelan solo a quienes demuestran tal dedicación... 🔮"
    ],
    'mission_completed': [
        "Excelente trabajo en esa misión, amor. {points} besitos como recompensa... y quizás algo más especial después. 🎯",
        "Has completado la misión perfectamente. {points} besitos son tuyos, y mi admiración también. ¿Qué viene después? ✨",
        "Misión cumplida... {points} besitos te esperan. Me gusta cuando demuestras tanta determinación por mí. 💋"
    ],
    'achievement_unlocked': [
        "¡Un logro desbloqueado! {points} besitos especiales... Cada logro tuyo es un paso más cerca de mi corazón. 🏆",
        "Has desbloqueado algo muy especial... {points} besitos y mi sonrisa. ¿Sientes cómo nos conectamos más? 💫",
        "Logro conseguido, mi querido. {points} besitos... y una pequeña parte de mis misterios se revelan. 🗝️"
    ]
}


class PointService(IPointService):
    """
    Servicio ÚNICO para TODAS las operaciones de puntos.
    Internamente usa PointTransaction para auditoría completa.
    """
    
    def __init__(self, 
                 session: AsyncSession,
                 level_service: LevelService,
                 achievement_service: AchievementService,
                 notification_service: Optional[INotificationService] = None):
        """
        Constructor con inyección de dependencias.
        
        Args:
            session (AsyncSession): Sesión de base de datos
            level_service (LevelService): Servicio de niveles
            achievement_service (AchievementService): Servicio de logros
            notification_service (Optional[INotificationService]): Servicio de notificaciones
        """
        self.session = session
        self.level_service = level_service
        self.achievement_service = achievement_service
        self.notification_service = notification_service

    async def _get_or_create_progress(self, user_id: int) -> UserStats:
        """
        Obtiene o crea el progreso de un usuario.
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            UserStats: Progreso del usuario
        """
        progress = await self.session.get(UserStats, user_id)
        if not progress:
            progress = UserStats(user_id=user_id)
            self.session.add(progress)
            # Solo hacer commit si no estamos en una transacción externa
            if not self.session.in_transaction():
                await self.session.commit()
                await self.session.refresh(progress)
        return progress

    async def award_message(self, user_id: int, bot: Bot) -> Optional[UserStats]:
        """
        Otorga puntos por envío de mensaje.
        
        Args:
            user_id (int): ID del usuario
            bot (Bot): Instancia del bot
            
        Returns:
            Optional[UserStats]: Progreso actualizado o None si no se otorgaron puntos
        """
        progress = await self._get_or_create_progress(user_id)
        now = datetime.utcnow()
        if progress.last_activity_at and (now - progress.last_activity_at).total_seconds() < 30:
            return None
        
        # Use MVP economic rules
        base_points = POINTS_CONFIG['message_sent']
        points = await self._apply_vip_multiplier(user_id, base_points)
        
        # Omitir notificación ya que la información se enviará a través del sistema unificado
        progress = await self.add_points(user_id, points, bot=bot, skip_notification=True, source="message_sent")
        progress.messages_sent += 1
        
        # Solo hacer commit si no estamos en una transacción externa
        if not self.session.in_transaction():
            await self.session.commit()
        
        new_badges = await self.achievement_service.check_message_achievements(user_id, progress.messages_sent, bot=bot)
        new_badges.extend(await self.achievement_service.check_user_badges(user_id))
        
        # Usar el sistema unificado de notificaciones para las insignias si está disponible
        for badge in new_badges:
            await self.achievement_service.award_badge(user_id, badge.id)
            if bot and self.notification_service:
                try:
                    await self.notification_service.add_notification(
                        user_id,
                        "badge",
                        {
                            "name": badge.name,
                            "icon": badge.icon or "🏅",
                            "description": getattr(badge, 'description', '')
                        },
                        priority=2  # MEDIUM
                    )
                    
                    logger.debug(f"Sent unified badge notification to user {user_id}")
                except Exception as e:
                    # Fallback al método anterior
                    logger.error(f"Error sending badge notification: {e}")
                    await bot.send_message(
                        user_id,
                        f"🏅 Has obtenido la insignia {badge.icon or ''} {badge.name}!",
                    )
                    
        return progress

    async def award_reaction(self, user: User, message_id: int, bot: Bot) -> Optional[UserStats]:
        """
        Otorga puntos por reacción a un mensaje.
        
        Args:
            user (User): Instancia del usuario
            message_id (int): ID del mensaje
            bot (Bot): Instancia del bot
            
        Returns:
            Optional[UserStats]: Progreso actualizado o None si no se otorgaron puntos
        """
        # First check if we already processed this reaction
        progress = await self._get_or_create_progress(user.id)
        now = datetime.utcnow()
        
        if progress.last_reaction_at and (now - progress.last_reaction_at).total_seconds() < 5:
            return None  # Skip if same reaction within 5 seconds
            
        progress.last_reaction_at = now
        
        # Solo hacer commit si no estamos en una transacción externa
        if not self.session.in_transaction():
            await self.session.commit()
        
        # Use MVP economic rules with VIP multiplier
        base_points = POINTS_CONFIG['channel_reaction']
        points = await self._apply_vip_multiplier(user.id, base_points)
        
        # Only then award points - Omitir notificación para usar sistema unificado
        progress = await self.add_points(user.id, points, bot=bot, skip_notification=True, source="channel_reaction")
        
        new_badges = await self.achievement_service.check_user_badges(user.id)
        
        # Usar el sistema unificado de notificaciones para las insignias si está disponible
        for badge in new_badges:
            await self.achievement_service.award_badge(user.id, badge.id)
            if bot and self.notification_service:
                try:
                    await self.notification_service.add_notification(
                        user.id,
                        "badge",
                        {
                            "name": badge.name,
                            "icon": badge.icon or "🏅",
                            "description": getattr(badge, 'description', '')
                        },
                        priority=2  # MEDIUM
                    )
                    
                    logger.debug(f"Sent unified badge notification to user {user.id}")
                except Exception as e:
                    # Fallback al método anterior
                    logger.error(f"Error sending badge notification: {e}")
                    await bot.send_message(
                        user.id,
                        f"🏅 Has obtenido la insignia {badge.icon or ''} {badge.name}!",
                    )
        return progress

    async def award_poll(self, user_id: int, bot: Bot) -> UserStats:
        """
        Otorga puntos por participación en encuesta.
        
        Args:
            user_id (int): ID del usuario
            bot (Bot): Instancia del bot
            
        Returns:
            UserStats: Progreso actualizado
        """
        # Use MVP economic rules with VIP multiplier
        base_points = POINTS_CONFIG['poll_participation']
        points = await self._apply_vip_multiplier(user_id, base_points)
        
        # Omitir notificación ya que la información se enviará a través del sistema unificado
        progress = await self.add_points(user_id, points, bot=bot, skip_notification=True, source="poll_participation")
        
        new_badges = await self.achievement_service.check_user_badges(user_id)
        
        # Usar el sistema unificado de notificaciones para las insignias si está disponible
        for badge in new_badges:
            await self.achievement_service.award_badge(user_id, badge.id)
            if bot and self.notification_service:
                try:
                    await self.notification_service.add_notification(
                        user_id,
                        "badge",
                        {
                            "name": badge.name,
                            "icon": badge.icon or "🏅",
                            "description": getattr(badge, 'description', '')
                        },
                        priority=2  # MEDIUM
                    )
                    
                    logger.debug(f"Sent unified badge notification to user {user_id}")
                except Exception as e:
                    # Fallback al método anterior
                    logger.error(f"Error sending badge notification: {e}")
                    await bot.send_message(
                        user_id,
                        f"🏅 Has obtenido la insignia {badge.icon or ''} {badge.name}!",
                    )
        return progress

    async def daily_checkin(self, user_id: int, bot: Bot) -> Tuple[bool, UserStats]:
        """
        Otorga puntos por check-in diario.
        
        Args:
            user_id (int): ID del usuario
            bot (Bot): Instancia del bot
            
        Returns:
            Tuple[bool, UserStats]: (Éxito, Progreso actualizado)
        """
        progress = await self._get_or_create_progress(user_id)
        now = datetime.utcnow()
        if progress.last_checkin_at and (now - progress.last_checkin_at).total_seconds() < 86400:
            return False, progress
            
        # Use MVP economic rules with VIP multiplier
        base_points = POINTS_CONFIG['daily_login']
        points = await self._apply_vip_multiplier(user_id, base_points)
        
        # Omitir notificación ya que la información se enviará a través del sistema unificado
        progress = await self.add_points(user_id, points, bot=bot, skip_notification=True, source="daily_checkin")
        
        if progress.last_checkin_at and (now.date() - progress.last_checkin_at.date()).days == 1:
            progress.checkin_streak += 1
        else:
            progress.checkin_streak = 1
        progress.last_checkin_at = now
        
        # Solo hacer commit si no estamos en una transacción externa
        if not self.session.in_transaction():
            await self.session.commit()
        
        # Usar el sistema unificado para las notificaciones de daily_checkin
        if bot and self.notification_service:
            try:
                await self.notification_service.add_notification(
                    user_id,
                    "checkin",
                    {
                        "streak": progress.checkin_streak,
                        "points": 10
                    },
                    priority=2  # MEDIUM
                )
                
                logger.debug(f"Sent unified checkin notification to user {user_id}")
            except Exception as e:
                logger.error(f"Error sending checkin notification: {e}")
        
        await self.achievement_service.check_checkin_achievements(user_id, progress.checkin_streak, bot=bot)
        new_badges = await self.achievement_service.check_user_badges(user_id)
        
        # Usar el sistema unificado de notificaciones para las insignias
        for badge in new_badges:
            await self.achievement_service.award_badge(user_id, badge.id)
            if bot and self.notification_service:
                try:
                    await self.notification_service.add_notification(
                        user_id,
                        "badge",
                        {
                            "name": badge.name,
                            "icon": badge.icon or "🏅",
                            "description": getattr(badge, 'description', '')
                        },
                        priority=2  # MEDIUM
                    )
                    
                    logger.debug(f"Sent unified badge notification to user {user_id}")
                except Exception as e:
                    # Fallback al método anterior
                    logger.error(f"Error sending badge notification: {e}")
                    await bot.send_message(
                        user_id,
                        f"🏅 Has obtenido la insignia {badge.icon or ''} {badge.name}!",
                    )
        return True, progress
    
    async def _apply_vip_multiplier(self, user_id: int, base_points: float) -> float:
        """
        Apply VIP multiplier to base points if user has VIP status.
        
        Args:
            user_id (int): ID del usuario
            base_points (float): Puntos base
            
        Returns:
            float: Puntos con multiplicador VIP aplicado
        """
        try:
            user = await self.session.get(User, user_id)
            if user and user.role == "vip" and user.vip_expires_at and user.vip_expires_at > datetime.utcnow():
                return base_points * POINTS_CONFIG['vip_bonus_multiplier']
        except Exception as e:
            logger.error(f"Error checking VIP status for user {user_id}: {e}")
        
        return base_points
    
    async def award_story_fragment_completion(self, user_id: int, bot: Optional[Bot] = None) -> UserStats:
        """
        Awards points for completing a story fragment with Diana's personality.
        
        Args:
            user_id (int): ID del usuario
            bot (Optional[Bot]): Instancia del bot
            
        Returns:
            UserStats: Progreso actualizado
        """
        base_points = POINTS_CONFIG['story_fragment_completion']
        points = await self._apply_vip_multiplier(user_id, base_points)
        
        progress = await self.add_points(user_id, points, bot=bot, skip_notification=True, source="story_fragment_completion")
        
        # Send Diana's character-consistent notification
        if bot and self.notification_service:
            try:
                import random
                message = random.choice(DIANA_REWARD_MESSAGES['besitos_earned'])
                total_points = await self.get_balance(user_id)
                await self.notification_service.add_notification(
                    user_id,
                    "story_progress",
                    {
                        "message": message.format(points=int(points), total=int(total_points)),
                        "points": points,
                        "source": "story_fragment"
                    },
                    priority=2  # MEDIUM
                )
                logger.debug(f"Sent Diana story completion notification to user {user_id}")
            except Exception as e:
                logger.error(f"Error sending story completion notification: {e}")
        
        return progress
    
    async def award_decision_made(self, user_id: int, bot: Optional[Bot] = None) -> UserStats:
        """
        Awards points for making a narrative decision with Diana's personality.
        
        Args:
            user_id (int): ID del usuario
            bot (Optional[Bot]): Instancia del bot
            
        Returns:
            UserStats: Progreso actualizado
        """
        base_points = POINTS_CONFIG['decision_made']
        points = await self._apply_vip_multiplier(user_id, base_points)
        
        return await self.add_points(user_id, points, bot=bot, skip_notification=True, source="decision_made")
    
    async def award_mission_completion(self, user_id: int, mission_name: str, bot: Optional[Bot] = None) -> UserStats:
        """
        Awards points for mission completion with Diana's personality.
        
        Args:
            user_id (int): ID del usuario
            mission_name (str): Nombre de la misión
            bot (Optional[Bot]): Instancia del bot
            
        Returns:
            UserStats: Progreso actualizado
        """
        base_points = POINTS_CONFIG['mission_completed']
        points = await self._apply_vip_multiplier(user_id, base_points)
        
        progress = await self.add_points(user_id, points, bot=bot, skip_notification=True, source="mission_completed")
        
        # Send Diana's character-consistent notification
        if bot and self.notification_service:
            try:
                import random
                message = random.choice(DIANA_REWARD_MESSAGES['mission_completed'])
                await self.notification_service.add_notification(
                    user_id,
                    "mission_complete",
                    {
                        "message": message.format(points=int(points)),
                        "mission_name": mission_name,
                        "points": points
                    },
                    priority=2  # MEDIUM
                )
                logger.debug(f"Sent Diana mission completion notification to user {user_id}")
            except Exception as e:
                logger.error(f"Error sending mission completion notification: {e}")
        
        return progress
    
    async def award_achievement_unlock(self, user_id: int, achievement_name: str, bot: Optional[Bot] = None) -> UserStats:
        """
        Awards points for achievement unlock with Diana's personality.
        
        Args:
            user_id (int): ID del usuario
            achievement_name (str): Nombre del logro
            bot (Optional[Bot]): Instancia del bot
            
        Returns:
            UserStats: Progreso actualizado
        """
        base_points = POINTS_CONFIG['achievement_unlocked']
        points = await self._apply_vip_multiplier(user_id, base_points)
        
        progress = await self.add_points(user_id, points, bot=bot, skip_notification=True, source="achievement_unlocked")
        
        # Send Diana's character-consistent notification
        if bot and self.notification_service:
            try:
                import random
                message = random.choice(DIANA_REWARD_MESSAGES['achievement_unlocked'])
                await self.notification_service.add_notification(
                    user_id,
                    "achievement_unlocked",
                    {
                        "message": message.format(points=int(points)),
                        "achievement_name": achievement_name,
                        "points": points
                    },
                    priority=1  # HIGH
                )
                logger.debug(f"Sent Diana achievement notification to user {user_id}")
            except Exception as e:
                logger.error(f"Error sending achievement notification: {e}")
        
        return progress

    async def add_points(self, user_id: int, points: float, *, bot: Optional[Bot] = None, 
                         skip_notification: bool = False, source: str = "unknown") -> UserStats:
        """
        Añade puntos a un usuario.
        
        Args:
            user_id (int): ID del usuario
            points (float): Cantidad de puntos a añadir
            bot (Optional[Bot]): Instancia del bot
            skip_notification (bool): Si se debe omitir la notificación
            source (str): Origen de los puntos
            
        Returns:
            UserStats: Progreso actualizado
        """
        # Verificar si ya hay una transacción activa en la sesión
        in_transaction = self.session.in_transaction()
        
        # Solo iniciar una nueva transacción si no hay una activa
        if not in_transaction:
            async with self.session.begin():
                return await self._add_points_internal(user_id, points, bot, skip_notification, source)
        else:
            # Si ya hay una transacción activa, ejecutar sin iniciar una nueva
            return await self._add_points_internal(user_id, points, bot, skip_notification, source)
    
    async def _add_points_internal(self, user_id: int, points: float, bot: Optional[Bot], 
                               skip_notification: bool, source: str) -> UserStats:
        """Implementación interna de add_points sin manejo de transacciones"""
        user = await self.session.get(User, user_id)
        if not user:
            logger.warning(
                f"Attempted to add points to non-existent user {user_id}. Creating new user."
            )
            user = User(id=user_id, points=0)
            self.session.add(user)
        
        # Calcular nuevo balance
        old_balance = user.points
        new_balance = old_balance + points
        
        # Crear registro de transacción
        transaction = PointTransaction(
            user_id=user_id,
            amount=points,
            balance_after=new_balance,
            source=source,
            description=f"Added {points} points from {source}"
        )
        self.session.add(transaction)
        
        # Actualizar usuario
        user.points = new_balance
        
        # Actualizar progreso
        progress = await self._get_or_create_progress(user_id)
        progress.last_activity_at = datetime.utcnow()
        
        # Commit solo si no estamos dentro de una transacción externa
        is_transaction_owner = not self.session.in_transaction()
        if is_transaction_owner:
            await self.session.commit()
            # Solo hacemos refresh si somos dueños de la transacción y acabamos de hacer commit
            await self.session.refresh(progress)
            await self.session.refresh(user)
            
        # Fuera de la transacción para evitar deadlock
        await self.level_service.check_for_level_up(user, bot=bot)

        new_badges = await self.achievement_service.check_user_badges(user_id)
        for badge in new_badges:
            await self.achievement_service.award_badge(user_id, badge.id)
            if bot:
                await bot.send_message(
                    user_id,
                    f"🏅 Has obtenido la insignia {badge.icon or ''} {badge.name}!",
                )
        logger.info(
            f"User {user_id} gained {points} points. Total: {user.points}"
        )
        
        # Solo enviar notificaciones de puntos cuando:
        # 1. No se ha solicitado omitir notificaciones
        # 2. Hay bot disponible
        # 3. El incremento desde la última notificación es significativo (>=5) o no hay registro previo
        
        # Añadir el atributo last_notified_points si no existe
        last_notified = getattr(progress, "last_notified_points", None)
        
        # Si no existe o la diferencia es significativa
        notification_needed = False
        if last_notified is None:
            notification_needed = True
        elif user.points - last_notified >= 5:
            notification_needed = True
            
        if not skip_notification and bot and notification_needed:
            if self.notification_service:
                try:
                    await self.notification_service.add_notification(
                        user_id,
                        "points",
                        {
                            "points": points,
                            "total": user.points
                        },
                        priority=3  # LOW
                    )
                    
                    logger.debug(f"Sent unified points notification to user {user_id}")
                except Exception as e:
                    # Fallback al método anterior
                    logger.error(f"Error sending points notification: {e}")
                    await bot.send_message(
                        user_id,
                        f"Has acumulado {user.points:.1f} puntos en total",
                    )
            else:
                # Fallback sin sistema de notificaciones
                await bot.send_message(
                    user_id,
                    f"Has acumulado {user.points:.1f} puntos en total",
                )
            
            # Añadir dinámicamente el atributo si no existe
            if not hasattr(progress, "last_notified_points"):
                progress.last_notified_points = user.points
            else:
                progress.last_notified_points = user.points
            
            # Solo hacer commit si no estamos en una transacción externa
            if not self.session.in_transaction():
                await self.session.commit()
        return progress

    async def deduct_points(self, user_id: int, points: int) -> Optional[User]:
        """
        Resta puntos a un usuario.
        
        Args:
            user_id (int): ID del usuario
            points (int): Cantidad de puntos a restar
            
        Returns:
            Optional[User]: Usuario actualizado o None si no se pudieron restar los puntos
        """
        # Verificar si ya hay una transacción activa en la sesión
        in_transaction = self.session.in_transaction()
        
        # Solo iniciar una nueva transacción si no hay una activa
        if not in_transaction:
            async with self.session.begin():
                return await self._deduct_points_internal(user_id, points)
        else:
            # Si ya hay una transacción activa, ejecutar sin iniciar una nueva
            return await self._deduct_points_internal(user_id, points)
    
    async def _deduct_points_internal(self, user_id: int, points: int) -> Optional[User]:
        """Implementación interna de deduct_points sin manejo de transacciones"""
        user = await self.session.get(User, user_id)
        if user and user.points >= points:
            # Calcular nuevo balance
            old_balance = user.points
            new_balance = old_balance - points
            
            # Crear registro de transacción
            transaction = PointTransaction(
                user_id=user_id,
                amount=-points,  # Negative for deductions
                balance_after=new_balance,
                source="deduction",
                description=f"Deducted {points} points"
            )
            self.session.add(transaction)
            
            # Actualizar usuario
            user.points = new_balance
            
            # Commit solo si no estamos dentro de una transacción externa
            is_transaction_owner = not self.session.in_transaction()
            if is_transaction_owner:
                await self.session.commit()
                # Solo hacemos refresh si somos dueños de la transacción y acabamos de hacer commit
                await self.session.refresh(user)
                
            logger.info(f"User {user_id} lost {points} points. Total: {user.points}")
            return user
            
        logger.warning(f"Failed to deduct {points} points from user {user_id}. Not enough points or user not found.")
        return None

    async def get_balance(self, user_id: int) -> float:
        """
        Obtiene el balance de puntos de un usuario.
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            float: Balance de puntos
        """
        # Opción 1: Desde User.points (rápido)
        # Opción 2: Desde último PointTransaction (auditable)
        user = await self.session.get(User, user_id)
        return user.points if user else 0

    async def get_transaction_history(self, user_id: int) -> List[PointTransaction]:
        """
        Obtiene el historial de transacciones de un usuario.
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            List[PointTransaction]: Lista de transacciones
        """
        stmt = select(PointTransaction).where(
            PointTransaction.user_id == user_id
        ).order_by(PointTransaction.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_user_points(self, user_id: int) -> int:
        """
        Obtiene los puntos de un usuario.
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            int: Puntos del usuario
        """
        user = await self.session.get(User, user_id)
        return user.points if user else 0

    async def get_top_users(self, limit: int = 10) -> List[User]:
        """
        Obtiene los usuarios con más puntos.
        
        Args:
            limit (int): Límite de usuarios a retornar
            
        Returns:
            List[User]: Lista de usuarios
        """
        stmt = select(User).order_by(User.points.desc()).limit(limit)
        result = await self.session.execute(stmt)
        top_users = result.scalars().all()
        return top_users