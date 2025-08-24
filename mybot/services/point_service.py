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
import datetime
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


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
        now = datetime.datetime.utcnow()
        if progress.last_activity_at and (now - progress.last_activity_at).total_seconds() < 30:
            return None
        
        # Omitir notificación ya que la información se enviará a través del sistema unificado
        progress = await self.add_points(user_id, 1, bot=bot, skip_notification=True)
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
        now = datetime.datetime.utcnow()
        if progress.last_reaction_at and (now - progress.last_reaction_at).total_seconds() < 5:
            return None  # Skip if same reaction within 5 seconds
            
        progress.last_reaction_at = now
        
        # Solo hacer commit si no estamos en una transacción externa
        if not self.session.in_transaction():
            await self.session.commit()
        
        # Only then award points - Omitir notificación para usar sistema unificado
        progress = await self.add_points(user.id, 0.5, bot=bot, skip_notification=True)
        
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
        # Omitir notificación ya que la información se enviará a través del sistema unificado
        progress = await self.add_points(user_id, 2, bot=bot, skip_notification=True)
        
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