"""
Integration service to connect channel administration with gamification system.
"""
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
try:
    from ..point_service import PointService
    from ..user_service import UserService
    from ..config_service import ConfigService
except ImportError:
    # Fallback to absolute imports for standalone usage
    from services.point_service import PointService
    from services.user_service import UserService
    from services.config_service import ConfigService

logger = logging.getLogger(__name__)

class ChannelEngagementService:
    """
    Service to handle awarding points for engagement with channel content.
    Integrates the administration system with the gamification system.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.point_service = PointService(session)
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
        
        # Award points for the reaction
        try:
            await self.point_service.award_reaction(user, message_id, bot)
            logger.info(f"Awarded reaction points to user {user_id} for message {message_id} in channel {channel_id}")
            return True
        except Exception as e:
            logger.exception(f"Error awarding reaction points to user {user_id}: {e}")
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
            success, progress = await self.point_service.daily_checkin(user_id, bot)
            if success:
                logger.info(f"Awarded daily checkin bonus to user {user_id}, streak: {progress.checkin_streak}")
                
                # Extra bonus for consistent engagement
                if progress.checkin_streak % 7 == 0:  # Weekly bonus
                    await self.point_service.add_points(user_id, 25, bot=bot)
                    logger.info(f"Awarded weekly streak bonus to user {user_id}, streak: {progress.checkin_streak}")
                    
                    if bot:
                        await bot.send_message(
                            user_id,
                            f"🎉 ¡Felicidades! Has completado {progress.checkin_streak} días de participación. Bonus semanal: +25 puntos"
                        )
                
                return True
            return False
        except Exception as e:
            logger.exception(f"Error checking daily engagement for user {user_id}: {e}")
            return False
