"""
Integration service to connect channel administration with gamification system.
"""
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from services.point_service import PointService
from services.user_service import UserService
from services.config_service import ConfigService
from services.level_service import LevelService
from services.achievement_service import AchievementService

logger = logging.getLogger(__name__)

class ChannelEngagementService:
    """
    Service to handle awarding points for engagement with channel content.
    Integrates the administration system with the gamification system.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        level_service = LevelService(session)
        achievement_service = AchievementService(session)
        self.point_service = PointService(session, level_service, achievement_service)
        self.user_service = UserService(session)
        self.config_service = ConfigService(session)
    
    async def award_channel_reaction(self, user_id: int, message_id: int, channel_id: int, bot=None):
        """
        Awards points to a user for reacting to a message in a channel.
        
        Args:
            user_id: The Telegram user ID
            message_id: The ID of the message that was reacted to
            channel_id: The ID of the channel where the reaction occurred
            bot: Optional bot instance for sending notifications
            
        Returns:
            bool: True if points were awarded, False otherwise
        """
        # Get user
        user = await self.user_service.get_user(user_id)
        if not user:
            logger.warning(f"User {user_id} not found when awarding channel reaction points")
            return False
        
        # Check if this is a managed channel
        managed_channels = await self.config_service.get_managed_channels()
        if str(channel_id) not in managed_channels:
            logger.debug(f"Channel {channel_id} is not managed, not awarding points")
            return False
        
        # Award points for the reaction - Omitir notificación para usar sistema unificado
        try:
            # Las notificaciones se manejan en el CoordinadorCentral con el servicio unificado
            await self.point_service.award_reaction(user, message_id, bot)
            logger.info(f"Awarded reaction points to user {user_id} for message {message_id} in channel {channel_id}")
            return True
        except Exception as e:
            logger.exception(f"Error awarding reaction points to user {user_id}: {e}")
            return False
    
    async def award_channel_participation(self, user_id: int, channel_id: int, action_type: str, bot=None):
        """
        Awards points to a user for participating in a channel (posting, commenting, etc.).
        
        Args:
            user_id: The Telegram user ID
            channel_id: The ID of the channel where the participation occurred
            action_type: The type of participation (post, comment, poll_vote, etc.)
            bot: Optional bot instance for sending notifications
            
        Returns:
            bool: True if points were awarded, False otherwise
        """
        # Check if this is a managed channel
        managed_channels = await self.config_service.get_managed_channels()
        if str(channel_id) not in managed_channels:
            logger.debug(f"Channel {channel_id} is not managed, not awarding points")
            return False
        
        # Award points based on action type
        try:
            points = 0
            if action_type == "post":
                points = 5
            elif action_type == "comment":
                points = 2
            elif action_type == "poll_vote":
                # Las notificaciones se manejan en el CoordinadorCentral con el servicio unificado
                await self.point_service.award_poll(user_id, bot)
                return True
            elif action_type == "message":
                # Las notificaciones se manejan en el CoordinadorCentral con el servicio unificado
                await self.point_service.award_message(user_id, bot)
                return True
            else:
                points = 1
            
            if points > 0:
                # Omitir notificación ya que se manejará a través del sistema unificado
                await self.point_service.add_points(user_id, points, bot=bot, skip_notification=True)
                logger.info(f"Awarded {points} points to user {user_id} for {action_type} in channel {channel_id}")
                return True
            
            return False
        except Exception as e:
            logger.exception(f"Error awarding participation points to user {user_id}: {e}")
            return False
    
    async def check_daily_engagement(self, user_id: int, bot=None):
        """
        Checks if a user has engaged with channels today and awards daily bonus if needed.
        
        Args:
            user_id: The Telegram user ID
            bot: Optional bot instance for sending notifications
            
        Returns:
            bool: True if daily bonus was awarded, False otherwise
        """
        try:
            # Usar sistema unificado para las notificaciones de daily_checkin
            success, progress = await self.point_service.daily_checkin(user_id, bot)
            if success:
                logger.info(f"Awarded daily checkin bonus to user {user_id}, streak: {progress.checkin_streak}")
                
                # Extra bonus for consistent engagement
                if progress.checkin_streak % 7 == 0:  # Weekly bonus
                    # Evitar notificaciones duplicadas usando el sistema unificado
                    await self.point_service.add_points(user_id, 25, bot=bot, skip_notification=True)
                    logger.info(f"Awarded weekly streak bonus to user {user_id}, streak: {progress.checkin_streak}")
                    
                    # Usar el sistema de notificaciones unificadas si está disponible
                    if bot:
                        try:
                            from services.notification_service import NotificationService, NotificationPriority
                            notification_service = NotificationService(self.session, bot)
                            
                            await notification_service.add_notification(
                                user_id,
                                "streak",
                                {
                                    "streak": progress.checkin_streak,
                                    "points": 25,
                                    "weekly": True
                                },
                                priority=NotificationPriority.MEDIUM
                            )
                            
                            logger.info(f"Sent unified streak notification to user {user_id}")
                        except ImportError:
                            # Fallback al método anterior si no está disponible el servicio unificado
                            await bot.send_message(
                                user_id,
                                f"🎉 ¡Felicidades! Has completado {progress.checkin_streak} días de participación. Bonus semanal: +25 puntos"
                            )
                
                return True
            return False
        except Exception as e:
            logger.exception(f"Error checking daily engagement for user {user_id}: {e}")
            return False
