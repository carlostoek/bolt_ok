from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User, UserStats
from database.transaction_models import PointTransaction
from utils.user_roles import get_points_multiplier
from aiogram import Bot
from services.level_service import LevelService
from services.achievement_service import AchievementService
from services.event_service import EventService
import datetime
import logging

logger = logging.getLogger(__name__)

class PointService:
    """
    Servicio ÚNICO para TODAS las operaciones de puntos.
    Internamente usa PointTransaction para auditoría completa.
    La interface pública NO CAMBIA.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_or_create_progress(self, user_id: int) -> UserStats:
        progress = await self.session.get(UserStats, user_id)
        if not progress:
            progress = UserStats(user_id=user_id)
            self.session.add(progress)
            await self.session.commit()
            await self.session.refresh(progress)
        return progress

    async def award_message(self, user_id: int, bot: Bot) -> UserStats | None:
        progress = await self._get_or_create_progress(user_id)
        now = datetime.datetime.utcnow()
        if progress.last_activity_at and (now - progress.last_activity_at).total_seconds() < 30:
            return None
        # Omitir notificación ya que la información se enviará a través del sistema unificado
        progress = await self.add_points(user_id, 1, bot=bot, skip_notification=True)
        progress.messages_sent += 1
        await self.session.commit()
        
        ach_service = AchievementService(self.session)
        await ach_service.check_message_achievements(user_id, progress.messages_sent, bot=bot)
        new_badges = await ach_service.check_user_badges(user_id)
        
        # Usar el sistema unificado de notificaciones para las insignias si está disponible
        for badge in new_badges:
            await ach_service.award_badge(user_id, badge.id)
            if bot:
                try:
                    from services.notification_service import NotificationService, NotificationPriority
                    notification_service = NotificationService(self.session, bot)
                    
                    await notification_service.add_notification(
                        user_id,
                        "badge",
                        {
                            "name": badge.name,
                            "icon": badge.icon or "🏅",
                            "description": getattr(badge, 'description', '')
                        },
                        priority=NotificationPriority.MEDIUM
                    )
                    
                    logger.debug(f"Sent unified badge notification to user {user_id}")
                except ImportError:
                    # Fallback al método anterior
                    await bot.send_message(
                        user_id,
                        f"🏅 Has obtenido la insignia {badge.icon or ''} {badge.name}!",
                    )
        return progress

    async def award_reaction(
        self, user: User, message_id: int, bot: Bot
    ) -> UserStats | None:
        # First check if we already processed this reaction
        progress = await self._get_or_create_progress(user.id)
        now = datetime.datetime.utcnow()
        if progress.last_reaction_at and (now - progress.last_reaction_at).total_seconds() < 5:
            return None  # Skip if same reaction within 5 seconds
            
        progress.last_reaction_at = now
        await self.session.commit()
        
        # Only then award points - Omitir notificación para usar sistema unificado
        progress = await self.add_points(user.id, 0.5, bot=bot, skip_notification=True)
        
        ach_service = AchievementService(self.session)
        new_badges = await ach_service.check_user_badges(user.id)
        
        # Usar el sistema unificado de notificaciones para las insignias si está disponible
        for badge in new_badges:
            await ach_service.award_badge(user.id, badge.id)
            if bot:
                try:
                    from services.notification_service import NotificationService, NotificationPriority
                    notification_service = NotificationService(self.session, bot)
                    
                    await notification_service.add_notification(
                        user_id,
                        "badge",
                        {
                            "name": badge.name,
                            "icon": badge.icon or "🏅",
                            "description": getattr(badge, 'description', '')
                        },
                        priority=NotificationPriority.MEDIUM
                    )
                    
                    logger.debug(f"Sent unified badge notification to user {user.id}")
                except ImportError:
                    # Fallback al método anterior
                    await bot.send_message(
                        user.id,
                        f"🏅 Has obtenido la insignia {badge.icon or ''} {badge.name}!",
                    )
        return progress

    async def award_poll(self, user_id: int, bot: Bot) -> UserStats:
        # Omitir notificación ya que la información se enviará a través del sistema unificado
        progress = await self.add_points(user_id, 2, bot=bot, skip_notification=True)
        
        ach_service = AchievementService(self.session)
        new_badges = await ach_service.check_user_badges(user_id)
        
        # Usar el sistema unificado de notificaciones para las insignias si está disponible
        for badge in new_badges:
            await ach_service.award_badge(user_id, badge.id)
            if bot:
                try:
                    from services.notification_service import NotificationService, NotificationPriority
                    notification_service = NotificationService(self.session, bot)
                    
                    await notification_service.add_notification(
                        user_id,
                        "badge",
                        {
                            "name": badge.name,
                            "icon": badge.icon or "🏅",
                            "description": getattr(badge, 'description', '')
                        },
                        priority=NotificationPriority.MEDIUM
                    )
                    
                    logger.debug(f"Sent unified badge notification to user {user_id}")
                except ImportError:
                    # Fallback al método anterior
                    await bot.send_message(
                        user_id,
                        f"🏅 Has obtenido la insignia {badge.icon or ''} {badge.name}!",
                    )
        return progress

    async def daily_checkin(self, user_id: int, bot: Bot) -> tuple[bool, UserStats]:
        progress = await self._get_or_create_progress(user_id)
        now = datetime.datetime.utcnow()
        if progress.last_checkin_at and (now - progress.last_checkin_at).total_seconds() < 86400:
            return False, progress
            
        # Omitir notificación ya que la información se enviará a través del sistema unificado
        progress = await self.add_points(user_id, 10, bot=bot, skip_notification=True)
        
        if progress.last_checkin_at and (now.date() - progress.last_checkin_at.date()).days == 1:
            progress.checkin_streak += 1
        else:
            progress.checkin_streak = 1
        progress.last_checkin_at = now
        await self.session.commit()
        
        # Usar el sistema unificado para las notificaciones de daily_checkin
        try:
            if bot:
                from services.notification_service import NotificationService, NotificationPriority
                notification_service = NotificationService(self.session, bot)
                
                await notification_service.add_notification(
                    user_id,
                    "checkin",
                    {
                        "streak": progress.checkin_streak,
                        "points": 10
                    },
                    priority=NotificationPriority.MEDIUM
                )
                
                logger.debug(f"Sent unified checkin notification to user {user_id}")
        except ImportError:
            pass  # Sin fallback, ya que se maneja en el channel_engagement_service
        
        ach_service = AchievementService(self.session)
        await ach_service.check_checkin_achievements(user_id, progress.checkin_streak, bot=bot)
        new_badges = await ach_service.check_user_badges(user_id)
        
        # Usar el sistema unificado de notificaciones para las insignias
        for badge in new_badges:
            await ach_service.award_badge(user_id, badge.id)
            if bot:
                try:
                    from services.notification_service import NotificationService, NotificationPriority
                    notification_service = NotificationService(self.session, bot)
                    
                    await notification_service.add_notification(
                        user_id,
                        "badge",
                        {
                            "name": badge.name,
                            "icon": badge.icon or "🏅",
                            "description": getattr(badge, 'description', '')
                        },
                        priority=NotificationPriority.MEDIUM
                    )
                    
                    logger.debug(f"Sent unified badge notification to user {user_id}")
                except ImportError:
                    # Fallback al método anterior
                    await bot.send_message(
                        user_id,
                        f"🏅 Has obtenido la insignia {badge.icon or ''} {badge.name}!",
                    )
        return True, progress

    async def add_points(self, user_id: int, points: float, *, bot: Bot | None = None, skip_notification: bool = False, source="unknown") -> UserStats:
        """Interface IDÉNTICA - ningún servicio necesita cambiar"""
        # NUEVO: Crear transacción
        async with self.session.begin():
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
            progress.last_activity_at = datetime.datetime.utcnow()
            
            await self.session.commit()
            await self.session.refresh(progress)
            await self.session.refresh(user)
            
        # Fuera de la transacción para evitar deadlock
        level_service = LevelService(self.session)
        await level_service.check_for_level_up(user, bot=bot)

        ach_service = AchievementService(self.session)
        new_badges = await ach_service.check_user_badges(user_id)
        for badge in new_badges:
            await ach_service.award_badge(user_id, badge.id)
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
        # 3. El incremento desde la última notificación es significativo (>=5)
        if not skip_notification and bot and user.points - progress.last_notified_points >= 5:
            try:
                # Intentar usar el sistema de notificaciones unificadas
                from services.notification_service import NotificationService, NotificationPriority
                notification_service = NotificationService(self.session, bot)
                
                await notification_service.add_notification(
                    user_id,
                    "points",
                    {
                        "points": points,
                        "total": user.points
                    },
                    priority=NotificationPriority.LOW  # Prioridad baja para notificaciones de puntos
                )
                
                logger.debug(f"Sent unified points notification to user {user_id}")
            except ImportError:
                # Fallback al método anterior
                await bot.send_message(
                    user_id,
                    f"Has acumulado {user.points:.1f} puntos en total",
                )
            
            progress.last_notified_points = user.points
            await self.session.commit()
        return progress

    async def deduct_points(self, user_id: int, points: int) -> User | None:
        """Interface IDÉNTICA - ningún servicio necesita cambiar"""
        # NUEVO: Crear transacción
        async with self.session.begin():
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
                
                await self.session.commit()
                await self.session.refresh(user)
                logger.info(f"User {user_id} lost {points} points. Total: {user.points}")
                return user
        logger.warning(f"Failed to deduct {points} points from user {user_id}. Not enough points or user not found.")
        return None

    async def get_balance(self, user_id: int) -> float:
        """Interface IDÉNTICA"""
        # Opción 1: Desde User.points (rápido)
        # Opción 2: Desde último PointTransaction (auditable)
        user = await self.session.get(User, user_id)
        return user.points if user else 0

    async def get_transaction_history(self, user_id: int):
        """NUEVA funcionalidad - historial completo"""
        stmt = select(PointTransaction).where(
            PointTransaction.user_id == user_id
        ).order_by(PointTransaction.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_user_points(self, user_id: int) -> int:
        user = await self.session.get(User, user_id)
        return user.points if user else 0

    async def get_top_users(self, limit: int = 10) -> list[User]:
        """Return the top users ordered by points."""
        stmt = select(User).order_by(User.points.desc()).limit(limit)
        result = await self.session.execute(stmt)
        top_users = result.scalars().all()
        return top_users
