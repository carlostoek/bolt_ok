"""
Admin service for centralized admin operations.
Replaces tenant-specific functionality with direct admin management.
"""
import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import User
from services.config_service import ConfigService
from services.channel_service import ChannelService

logger = logging.getLogger(__name__)

class AdminService:
    """
    Service for admin-specific operations and dashboard data.
    Provides admin functionality without pseudo-multitenant complexity.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.config_service = ConfigService(session)
        self.channel_service = ChannelService(session)
    
    async def ensure_admin_user(self, user_id: int) -> Dict[str, Any]:
        """
        Ensure user exists and has admin role.
        
        Returns:
            Dict with user information and status
        """
        try:
            user = await self.session.get(User, user_id)
            if not user:
                user = User(id=user_id, role="admin")
                self.session.add(user)
            else:
                user.role = "admin"
            
            await self.session.commit()
            
            logger.info(f"Admin user ensured: {user_id}")
            return {
                "success": True,
                "user_id": user_id,
                "role": "admin"
            }
            
        except Exception as e:
            logger.error(f"Error ensuring admin user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_setup_status(self) -> Dict[str, bool]:
        """
        Get global setup status for the bot.
        
        Returns:
            Dict with boolean flags for setup completion
        """
        try:
            vip_channel = await self.config_service.get_vip_channel_id()
            free_channel = await self.config_service.get_free_channel_id()
            
            # Check gamification setup (basic missions, levels, etc.)
            from services.mission_service import MissionService
            from services.level_service import LevelService
            
            mission_service = MissionService(self.session)
            level_service = LevelService(self.session)
            
            missions = await mission_service.get_active_missions()
            levels = await level_service.list_levels()
            
            return {
                "channels_configured": bool(vip_channel or free_channel),
                "vip_channel_configured": bool(vip_channel),
                "free_channel_configured": bool(free_channel),
                "gamification_configured": len(missions) > 0 and len(levels) > 0,
                "basic_setup_complete": bool(vip_channel or free_channel)
            }
            
        except Exception as e:
            logger.error(f"Error getting setup status: {e}")
            return {
                "channels_configured": False,
                "vip_channel_configured": False,
                "free_channel_configured": False,
                "gamification_configured": False,
                "basic_setup_complete": False
            }
    
    async def get_dashboard_data(self, admin_user_id: int) -> Dict[str, Any]:
        """
        Get dashboard data for admin view.
        
        Returns:
            Dict with admin dashboard information
        """
        try:
            setup_status = await self.get_setup_status()
            
            # Get channel information
            vip_channel_id = await self.config_service.get_vip_channel_id()
            free_channel_id = await self.config_service.get_free_channel_id()
            
            # Get user count
            user_count_stmt = select(func.count()).select_from(User)
            user_count_result = await self.session.execute(user_count_stmt)
            total_users = user_count_result.scalar() or 0
            
            return {
                "admin_user_id": admin_user_id,
                "configuration_status": setup_status,
                "channels": {
                    "vip_channel_id": vip_channel_id,
                    "free_channel_id": free_channel_id
                },
                "total_users": total_users,
                "setup_complete": setup_status["basic_setup_complete"]
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {
                "admin_user_id": admin_user_id,
                "error": str(e)
            }

    async def configure_channels(
        self, 
        admin_user_id: int, 
        vip_channel_id: int = None,
        free_channel_id: int = None,
        channel_titles: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Configure channels for the bot.
        
        Args:
            admin_user_id: The admin user configuring the channels
            vip_channel_id: Optional VIP channel ID
            free_channel_id: Optional free channel ID
            channel_titles: Optional dict with channel titles
        
        Returns:
            Dict with configuration result
        """
        try:
            results = {}
            
            if vip_channel_id:
                await self.config_service.set_vip_channel_id(vip_channel_id)
                title = channel_titles.get("vip") if channel_titles else None
                await self.channel_service.add_channel(vip_channel_id, title)
                results["vip_configured"] = True
                logger.info(f"VIP channel {vip_channel_id} configured by admin {admin_user_id}")
            
            if free_channel_id:
                await self.config_service.set_free_channel_id(free_channel_id)
                title = channel_titles.get("free") if channel_titles else None
                await self.channel_service.add_channel(free_channel_id, title)
                results["free_configured"] = True
                logger.info(f"Free channel {free_channel_id} configured by admin {admin_user_id}")
            
            return {
                "success": True,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error configuring channels for admin {admin_user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def setup_default_gamification(self, admin_user_id: int) -> Dict[str, Any]:
        """
        Set up default gamification elements.
        
        Returns:
            Dict with setup results
        """
        try:
            from services.mission_service import MissionService
            from services.level_service import LevelService
            from services.achievement_service import AchievementService
            
            mission_service = MissionService(self.session)
            level_service = LevelService(self.session)
            achievement_service = AchievementService(self.session)
            
            # Initialize default levels
            await level_service._init_levels()
            
            # Initialize default achievements
            await achievement_service.ensure_achievements_exist()
            
            # Create default missions
            default_missions = [
                {
                    "name": "Primer Mensaje",
                    "description": "Envía tu primer mensaje en el chat",
                    "mission_type": "messages",
                    "target_value": 1,
                    "reward_points": 10,
                    "duration_days": 0
                },
                {
                    "name": "Check-in Diario",
                    "description": "Realiza tu check-in diario con /checkin",
                    "mission_type": "daily",
                    "target_value": 1,
                    "reward_points": 5,
                    "duration_days": 1
                },
                {
                    "name": "Conversador Activo",
                    "description": "Envía 10 mensajes en el chat",
                    "mission_type": "messages",
                    "target_value": 10,
                    "reward_points": 25,
                    "duration_days": 0
                }
            ]
            
            created_missions = []
            for mission_data in default_missions:
                mission = await mission_service.create_mission(
                    mission_data["name"],
                    mission_data["description"],
                    mission_data["mission_type"],
                    mission_data["target_value"],
                    mission_data["reward_points"],
                    mission_data["duration_days"]
                )
                created_missions.append(mission.name)
            
            logger.info(f"Default gamification setup completed by admin {admin_user_id}")
            return {
                "success": True,
                "missions_created": created_missions,
                "levels_initialized": True,
                "achievements_initialized": True
            }
            
        except Exception as e:
            logger.error(f"Error setting up gamification for admin {admin_user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }