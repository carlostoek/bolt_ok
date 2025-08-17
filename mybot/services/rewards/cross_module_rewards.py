"""
Cross-Module Reward Flow Coordinator for Bolt OK Telegram Bot

This service orchestrates reward flows between the three main systems:
- Narrative system (interactive storytelling)
- Gamification system (points, missions, achievements)
- Channel engagement system (social interactions)

Provides real-time cross-module rewards, unlocks, and notifications.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..coordinador_central import CoordinadorCentral, AccionUsuario
from ..event_bus import get_event_bus, EventType, Event
from ..point_service import PointService
from ..mission_service import MissionService
from ..narrative_service import NarrativeService
from ..achievement_service import AchievementService
from ..user_service import UserService
from ..diana_menu_system import get_diana_menu_system
from utils.handler_decorators import safe_handler
from utils.message_safety import safe_send_message

logger = logging.getLogger(__name__)

@dataclass
class RewardResult:
    """Result of a cross-module reward operation."""
    success: bool
    reward_type: str
    message: str
    points_awarded: int = 0
    items_unlocked: List[str] = None
    achievements_gained: List[str] = None
    missions_unlocked: List[str] = None
    narrative_unlocked: List[str] = None
    
    def __post_init__(self):
        if self.items_unlocked is None:
            self.items_unlocked = []
        if self.achievements_gained is None:
            self.achievements_gained = []
        if self.missions_unlocked is None:
            self.missions_unlocked = []
        if self.narrative_unlocked is None:
            self.narrative_unlocked = []

class CrossModuleRewards:
    """
    Main coordinator for cross-module reward flows.
    
    Manages complex reward relationships between narrative progress,
    gamification achievements, and channel engagement activities.
    Integrates with Diana Menu System for real-time notifications.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize cross-module rewards coordinator.
        
        Args:
            session: Database session for all service operations
        """
        self.session = session
        
        # Core services
        self.coordinador = CoordinadorCentral(session)
        self.point_service = PointService(session)
        self.mission_service = MissionService(session)
        self.narrative_service = NarrativeService(session)
        self.achievement_service = AchievementService(session)
        self.user_service = UserService(session)
        
        # Event system integration
        self.event_bus = get_event_bus()
        
        # Cross-module reward tracking
        self.reward_multipliers = {
            "narrative_milestone": 2.0,
            "achievement_unlock": 1.5,
            "channel_engagement": 1.0,
            "cross_module_bonus": 3.0
        }
        
        # Unlock thresholds and conditions
        self.unlock_conditions = {
            "narrative_missions": {
                "level1_complete": ["daily_interaction", "narrative_explorer"],
                "level2_complete": ["vip_content_seeker", "story_completion"],
                "level3_complete": ["romance_master", "decision_expert"]
            },
            "achievement_narratives": {
                "first_reaction": "hint_basic_romance",
                "daily_streak_7": "hint_advanced_pleasure",
                "points_milestone_100": "fragment_secret_garden",
                "mission_master": "fragment_diana_backstory"
            },
            "engagement_bonuses": {
                "weekly_active": {"points": 50, "narrative_access": True},
                "monthly_champion": {"points": 200, "mission_unlock": "exclusive_content"}
            }
        }
        
        # Diana character integration for personalized messages
        self.diana_messages = {
            "narrative_unlock": "Diana te guía hacia un nuevo capítulo de vuestra historia...",
            "mission_unlock": "Diana te desafía con una nueva aventura...",
            "achievement_unlock": "Diana celebra tu progreso con una sonrisa seductora...",
            "cross_module_bonus": "Diana está especialmente impresionada por tu dedicación..."
        }
        
        # Initialize event subscribers
        self._setup_event_subscriptions()
    
    async def initialize_reward_system(self) -> Dict[str, Any]:
        """
        Initialize the cross-module reward system.
        Sets up event subscriptions and validates system components.
        
        Returns:
            Dict containing initialization results
        """
        try:
            logger.info("Initializing cross-module reward system...")
            
            # Validate core services
            services_status = await self._validate_services()
            if not services_status["all_active"]:
                logger.warning(f"Some services not available: {services_status}")
            
            # Set up event subscriptions
            subscriptions_setup = await self._setup_event_subscriptions()
            
            # Initialize reward tracking
            tracking_initialized = await self._initialize_reward_tracking()
            
            logger.info("Cross-module reward system initialized successfully")
            return {
                "success": True,
                "services_status": services_status,
                "subscriptions_setup": subscriptions_setup,
                "tracking_initialized": tracking_initialized,
                "message": "Sistema de recompensas cross-módulo operativo"
            }
            
        except Exception as e:
            logger.exception(f"Error initializing cross-module reward system: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error inicializando sistema de recompensas"
            }
    
    async def process_narrative_milestone(self, user_id: int, fragment_key: str, 
                                        bot=None) -> RewardResult:
        """
        Process narrative milestone completion and trigger cross-module rewards.
        
        Args:
            user_id: User ID
            fragment_key: Completed narrative fragment key
            bot: Telegram bot instance for notifications
            
        Returns:
            RewardResult with all unlocked rewards and bonuses
        """
        try:
            logger.info(f"Processing narrative milestone: user {user_id}, fragment {fragment_key}")
            
            result = RewardResult(
                success=True,
                reward_type="narrative_milestone",
                message="",
                points_awarded=0
            )
            
            # Calculate narrative progress level
            progress_level = await self._calculate_narrative_progress_level(user_id, fragment_key)
            
            # Award base narrative progression points
            base_points = self._get_narrative_milestone_points(fragment_key)
            multiplier = self.reward_multipliers["narrative_milestone"]
            total_points = int(base_points * multiplier)
            
            if total_points > 0:
                await self.point_service.add_points(user_id, total_points, bot=bot)
                result.points_awarded = total_points
            
            # Check for mission unlocks
            unlocked_missions = await self._check_narrative_mission_unlocks(user_id, fragment_key)
            result.missions_unlocked = unlocked_missions
            
            # Check for achievement triggers
            achievements = await self._check_narrative_achievement_triggers(user_id, progress_level)
            result.achievements_gained = achievements
            
            # Cross-module bonus check
            cross_bonus = await self._check_cross_module_bonus(user_id, "narrative_milestone")
            if cross_bonus["eligible"]:
                bonus_points = cross_bonus["points"]
                await self.point_service.add_points(user_id, bonus_points, bot=bot)
                result.points_awarded += bonus_points
                result.items_unlocked.append(f"Bonus cross-módulo: +{bonus_points} besitos")
            
            # Generate comprehensive Diana message
            result.message = await self._generate_narrative_milestone_message(
                fragment_key, result.points_awarded, result.missions_unlocked, 
                result.achievements_gained
            )
            
            # Emit events for real-time updates
            await self._emit_narrative_milestone_events(user_id, fragment_key, result)
            
            # Update Diana Menu System
            await self._update_diana_menu_notifications(user_id, "narrative_milestone", result)
            
            logger.info(f"Narrative milestone processed: {total_points} points, "
                       f"{len(unlocked_missions)} missions, {len(achievements)} achievements")
            
            return result
            
        except Exception as e:
            logger.exception(f"Error processing narrative milestone for user {user_id}: {e}")
            return RewardResult(
                success=False,
                reward_type="narrative_milestone",
                message="Error procesando progreso narrativo. Intenta de nuevo."
            )
    
    async def process_achievement_unlock(self, user_id: int, achievement_id: str, 
                                       bot=None) -> RewardResult:
        """
        Process achievement unlock and trigger narrative content access.
        
        Args:
            user_id: User ID
            achievement_id: Unlocked achievement ID
            bot: Telegram bot instance for notifications
            
        Returns:
            RewardResult with narrative unlocks and bonuses
        """
        try:
            logger.info(f"Processing achievement unlock: user {user_id}, achievement {achievement_id}")
            
            result = RewardResult(
                success=True,
                reward_type="achievement_unlock",
                message="",
                points_awarded=0
            )
            
            # Get achievement details
            achievement = await self.achievement_service.get_achievement_by_id(achievement_id)
            if not achievement:
                logger.warning(f"Achievement {achievement_id} not found")
                result.success = False
                result.message = "Logro no encontrado"
                return result
            
            # Award achievement bonus points
            bonus_points = self._get_achievement_bonus_points(achievement_id)
            multiplier = self.reward_multipliers["achievement_unlock"]
            total_points = int(bonus_points * multiplier)
            
            if total_points > 0:
                await self.point_service.add_points(user_id, total_points, bot=bot)
                result.points_awarded = total_points
            
            # Check for narrative content unlocks
            narrative_unlocks = await self._check_achievement_narrative_unlocks(user_id, achievement_id)
            result.narrative_unlocked = narrative_unlocks
            
            # Check for special mission unlocks
            mission_unlocks = await self._check_achievement_mission_unlocks(user_id, achievement_id)
            result.missions_unlocked = mission_unlocks
            
            # Cross-module bonus check
            cross_bonus = await self._check_cross_module_bonus(user_id, "achievement_unlock")
            if cross_bonus["eligible"]:
                bonus_points = cross_bonus["points"]
                await self.point_service.add_points(user_id, bonus_points, bot=bot)
                result.points_awarded += bonus_points
                result.items_unlocked.append(f"Bonus cross-módulo: +{bonus_points} besitos")
            
            # Generate Diana message
            result.message = await self._generate_achievement_unlock_message(
                achievement_id, result.points_awarded, result.narrative_unlocked,
                result.missions_unlocked
            )
            
            # Emit events
            await self._emit_achievement_unlock_events(user_id, achievement_id, result)
            
            # Update Diana Menu System
            await self._update_diana_menu_notifications(user_id, "achievement_unlock", result)
            
            logger.info(f"Achievement unlock processed: {total_points} points, "
                       f"{len(narrative_unlocks)} narrative unlocks, {len(mission_unlocks)} missions")
            
            return result
            
        except Exception as e:
            logger.exception(f"Error processing achievement unlock for user {user_id}: {e}")
            return RewardResult(
                success=False,
                reward_type="achievement_unlock",
                message="Error procesando logro. Intenta de nuevo."
            )
    
    async def process_engagement_milestone(self, user_id: int, engagement_type: str,
                                         engagement_data: Dict[str, Any], bot=None) -> RewardResult:
        """
        Process channel engagement milestone and award dual system rewards.
        
        Args:
            user_id: User ID
            engagement_type: Type of engagement (daily, weekly, reaction, etc.)
            engagement_data: Additional engagement data
            bot: Telegram bot instance for notifications
            
        Returns:
            RewardResult with points and narrative access rewards
        """
        try:
            logger.info(f"Processing engagement milestone: user {user_id}, type {engagement_type}")
            
            result = RewardResult(
                success=True,
                reward_type="engagement_milestone",
                message="",
                points_awarded=0
            )
            
            # Award engagement points
            base_points = self._get_engagement_milestone_points(engagement_type, engagement_data)
            multiplier = self.reward_multipliers["channel_engagement"]
            total_points = int(base_points * multiplier)
            
            if total_points > 0:
                await self.point_service.add_points(user_id, total_points, bot=bot)
                result.points_awarded = total_points
            
            # Check for narrative access unlocks
            narrative_unlocks = await self._check_engagement_narrative_unlocks(
                user_id, engagement_type, engagement_data
            )
            result.narrative_unlocked = narrative_unlocks
            
            # Check for special engagement missions
            mission_unlocks = await self._check_engagement_mission_unlocks(
                user_id, engagement_type, engagement_data
            )
            result.missions_unlocked = mission_unlocks
            
            # Cross-module bonus for multi-system engagement
            cross_bonus = await self._check_cross_module_bonus(user_id, "engagement_milestone")
            if cross_bonus["eligible"]:
                bonus_points = cross_bonus["points"]
                await self.point_service.add_points(user_id, bonus_points, bot=bot)
                result.points_awarded += bonus_points
                result.items_unlocked.append(f"Bonus cross-módulo: +{bonus_points} besitos")
            
            # Generate Diana message
            result.message = await self._generate_engagement_milestone_message(
                engagement_type, result.points_awarded, result.narrative_unlocked,
                result.missions_unlocked
            )
            
            # Emit events
            await self._emit_engagement_milestone_events(user_id, engagement_type, result)
            
            # Update Diana Menu System
            await self._update_diana_menu_notifications(user_id, "engagement_milestone", result)
            
            logger.info(f"Engagement milestone processed: {total_points} points, "
                       f"{len(narrative_unlocks)} narrative unlocks, {len(mission_unlocks)} missions")
            
            return result
            
        except Exception as e:
            logger.exception(f"Error processing engagement milestone for user {user_id}: {e}")
            return RewardResult(
                success=False,
                reward_type="engagement_milestone",
                message="Error procesando progreso de participación. Intenta de nuevo."
            )
    
    # ==================== EVENT SYSTEM INTEGRATION ====================
    
    async def _setup_event_subscriptions(self) -> Dict[str, int]:
        """Set up event subscriptions for cross-module communication."""
        try:
            subscriptions_count = 0
            
            # Narrative events
            self.event_bus.subscribe(EventType.NARRATIVE_PROGRESS, self._handle_narrative_progress_event)
            self.event_bus.subscribe(EventType.NARRATIVE_DECISION, self._handle_narrative_decision_event)
            subscriptions_count += 2
            
            # Gamification events  
            self.event_bus.subscribe(EventType.ACHIEVEMENT_UNLOCKED, self._handle_achievement_unlock_event)
            self.event_bus.subscribe(EventType.LEVEL_UP, self._handle_level_up_event)
            self.event_bus.subscribe(EventType.POINTS_AWARDED, self._handle_points_awarded_event)
            subscriptions_count += 3
            
            # Channel engagement events
            self.event_bus.subscribe(EventType.CHANNEL_ENGAGEMENT, self._handle_channel_engagement_event)
            self.event_bus.subscribe(EventType.USER_REACTION, self._handle_user_reaction_event)
            self.event_bus.subscribe(EventType.USER_DAILY_CHECKIN, self._handle_daily_checkin_event)
            subscriptions_count += 3
            
            logger.info(f"Set up {subscriptions_count} event subscriptions for cross-module rewards")
            return {"total_subscriptions": subscriptions_count}
            
        except Exception as e:
            logger.exception(f"Error setting up event subscriptions: {e}")
            return {"total_subscriptions": 0, "error": str(e)}
    
    async def _handle_narrative_progress_event(self, event: Event) -> None:
        """Handle narrative progress events for cross-module rewards."""
        try:
            user_id = event.user_id
            fragment_key = event.data.get("fragment_key")
            
            if fragment_key:
                # Process narrative milestone in background
                asyncio.create_task(
                    self.process_narrative_milestone(user_id, fragment_key)
                )
            
        except Exception as e:
            logger.exception(f"Error handling narrative progress event: {e}")
    
    async def _handle_achievement_unlock_event(self, event: Event) -> None:
        """Handle achievement unlock events for narrative content access."""
        try:
            user_id = event.user_id
            achievement_id = event.data.get("achievement_id")
            
            if achievement_id:
                # Process achievement unlock in background
                asyncio.create_task(
                    self.process_achievement_unlock(user_id, achievement_id)
                )
            
        except Exception as e:
            logger.exception(f"Error handling achievement unlock event: {e}")
    
    async def _handle_channel_engagement_event(self, event: Event) -> None:
        """Handle channel engagement events for dual system rewards."""
        try:
            user_id = event.user_id
            engagement_type = event.data.get("action_type", "general")
            engagement_data = event.data
            
            # Process engagement milestone in background
            asyncio.create_task(
                self.process_engagement_milestone(user_id, engagement_type, engagement_data)
            )
            
        except Exception as e:
            logger.exception(f"Error handling channel engagement event: {e}")
    
    # Additional event handlers for comprehensive integration...
    async def _handle_level_up_event(self, event: Event) -> None:
        """Handle level up events for special cross-module bonuses."""
        try:
            user_id = event.user_id
            new_level = event.data.get("new_level", 1)
            
            # Award cross-module bonus for level milestones
            if new_level % 5 == 0:  # Every 5 levels
                bonus_result = await self._award_level_milestone_bonus(user_id, new_level)
                if bonus_result["success"]:
                    await self._update_diana_menu_notifications(user_id, "level_milestone", bonus_result)
            
        except Exception as e:
            logger.exception(f"Error handling level up event: {e}")
    
    async def _handle_points_awarded_event(self, event: Event) -> None:
        """Handle points awarded events for threshold-based unlocks."""
        try:
            user_id = event.user_id
            points_awarded = event.data.get("points", 0)
            total_points = event.data.get("total_points", 0)
            
            # Check for points milestone unlocks
            milestone_unlocks = await self._check_points_milestone_unlocks(user_id, total_points)
            if milestone_unlocks["has_unlocks"]:
                await self._update_diana_menu_notifications(user_id, "points_milestone", milestone_unlocks)
            
        except Exception as e:
            logger.exception(f"Error handling points awarded event: {e}")
    
    async def _handle_user_reaction_event(self, event: Event) -> None:
        """Handle user reaction events for engagement tracking."""
        try:
            user_id = event.user_id
            reaction_data = event.data
            
            # Check for reaction-based narrative unlocks
            reaction_unlocks = await self._check_reaction_based_unlocks(user_id, reaction_data)
            if reaction_unlocks["has_unlocks"]:
                await self._update_diana_menu_notifications(user_id, "reaction_unlock", reaction_unlocks)
            
        except Exception as e:
            logger.exception(f"Error handling user reaction event: {e}")
    
    async def _handle_daily_checkin_event(self, event: Event) -> None:
        """Handle daily check-in events for streak bonuses."""
        try:
            user_id = event.user_id
            streak = event.data.get("streak", 1)
            
            # Award streak milestone bonuses
            if streak % 7 == 0:  # Weekly milestones
                streak_bonus = await self._award_streak_milestone_bonus(user_id, streak)
                if streak_bonus["success"]:
                    await self._update_diana_menu_notifications(user_id, "streak_milestone", streak_bonus)
            
        except Exception as e:
            logger.exception(f"Error handling daily checkin event: {e}")
    
    # ==================== HELPER METHODS ====================
    
    async def _validate_services(self) -> Dict[str, Any]:
        """Validate that all required services are available."""
        services = {
            "point_service": self.point_service is not None,
            "mission_service": self.mission_service is not None,
            "narrative_service": self.narrative_service is not None,
            "achievement_service": self.achievement_service is not None,
            "user_service": self.user_service is not None,
            "coordinador": self.coordinador is not None,
            "event_bus": self.event_bus is not None
        }
        
        all_active = all(services.values())
        return {"services": services, "all_active": all_active}
    
    async def _initialize_reward_tracking(self) -> Dict[str, Any]:
        """Initialize reward tracking systems."""
        try:
            # Initialize any required reward tracking data structures
            # This could include creating database tables, setting up caches, etc.
            
            return {
                "tracking_initialized": True,
                "reward_multipliers_loaded": len(self.reward_multipliers),
                "unlock_conditions_loaded": len(self.unlock_conditions)
            }
        except Exception as e:
            logger.exception(f"Error initializing reward tracking: {e}")
            return {"tracking_initialized": False, "error": str(e)}
    
    # Placeholder methods for specific reward calculations and unlocks
    # These would be implemented based on specific game mechanics
    
    async def _calculate_narrative_progress_level(self, user_id: int, fragment_key: str) -> int:
        """Calculate user's narrative progress level."""
        # Implementation would analyze fragment_key and user's narrative history
        return 1  # Placeholder
    
    def _get_narrative_milestone_points(self, fragment_key: str) -> int:
        """Get points for narrative milestone."""
        milestone_points = {
            "level1_": 10,
            "level2_": 15,
            "level3_": 20,
            "level4_": 25,
            "level5_": 30
        }
        
        for prefix, points in milestone_points.items():
            if fragment_key.startswith(prefix):
                return points
        return 5  # Default points
    
    def _get_achievement_bonus_points(self, achievement_id: str) -> int:
        """Get bonus points for achievement unlock."""
        bonus_points = {
            "first_reaction": 20,
            "daily_streak_7": 50,
            "points_milestone_100": 25,
            "mission_master": 100
        }
        return bonus_points.get(achievement_id, 10)
    
    def _get_engagement_milestone_points(self, engagement_type: str, data: Dict[str, Any]) -> int:
        """Get points for engagement milestone."""
        points_map = {
            "daily": 15,
            "weekly": 75,
            "reaction": 5,
            "post": 20,
            "comment": 10
        }
        return points_map.get(engagement_type, 5)
    
    # Additional helper methods would be implemented here...
    # These are placeholder implementations for the core architecture
    
    async def _check_narrative_mission_unlocks(self, user_id: int, fragment_key: str) -> List[str]:
        """Check for missions unlocked by narrative progress."""
        return []  # Placeholder
    
    async def _check_narrative_achievement_triggers(self, user_id: int, progress_level: int) -> List[str]:
        """Check for achievements triggered by narrative progress."""
        return []  # Placeholder
    
    async def _check_cross_module_bonus(self, user_id: int, trigger_type: str) -> Dict[str, Any]:
        """Check if user is eligible for cross-module bonus."""
        return {"eligible": False, "points": 0}  # Placeholder
    
    async def _generate_narrative_milestone_message(self, fragment_key: str, points: int, 
                                                  missions: List[str], achievements: List[str]) -> str:
        """Generate personalized Diana message for narrative milestone."""
        base_message = self.diana_messages["narrative_unlock"]
        
        rewards_text = f"\n\n*+{points} besitos* 💋"
        if missions:
            rewards_text += f"\n🎯 {len(missions)} nueva(s) misión(es) desbloqueada(s)"
        if achievements:
            rewards_text += f"\n🏆 {len(achievements)} logro(s) obtenido(s)"
        
        return base_message + rewards_text
    
    async def _generate_achievement_unlock_message(self, achievement_id: str, points: int,
                                                 narrative: List[str], missions: List[str]) -> str:
        """Generate personalized Diana message for achievement unlock."""
        base_message = self.diana_messages["achievement_unlock"]
        
        rewards_text = f"\n\n*+{points} besitos* 💋"
        if narrative:
            rewards_text += f"\n📖 {len(narrative)} contenido(s) narrativo(s) desbloqueado(s)"
        if missions:
            rewards_text += f"\n🎯 {len(missions)} nueva(s) misión(es) desbloqueada(s)"
        
        return base_message + rewards_text
    
    async def _generate_engagement_milestone_message(self, engagement_type: str, points: int,
                                                   narrative: List[str], missions: List[str]) -> str:
        """Generate personalized Diana message for engagement milestone."""
        base_message = "Diana nota tu participación activa y sonríe con complicidad..."
        
        rewards_text = f"\n\n*+{points} besitos* 💋"
        if narrative:
            rewards_text += f"\n📖 {len(narrative)} contenido(s) narrativo(s) desbloqueado(s)"
        if missions:
            rewards_text += f"\n🎯 {len(missions)} nueva(s) misión(es) desbloqueada(s)"
        
        return base_message + rewards_text
    
    async def _emit_narrative_milestone_events(self, user_id: int, fragment_key: str, result: RewardResult) -> None:
        """Emit events for narrative milestone completion."""
        await self.event_bus.publish(
            EventType.WORKFLOW_COMPLETED,
            user_id,
            {
                "workflow": "narrative_milestone",
                "fragment_key": fragment_key,
                "result": result.__dict__
            },
            source="cross_module_rewards"
        )
    
    async def _emit_achievement_unlock_events(self, user_id: int, achievement_id: str, result: RewardResult) -> None:
        """Emit events for achievement unlock completion."""
        await self.event_bus.publish(
            EventType.WORKFLOW_COMPLETED,
            user_id,
            {
                "workflow": "achievement_unlock",
                "achievement_id": achievement_id,
                "result": result.__dict__
            },
            source="cross_module_rewards"
        )
    
    async def _emit_engagement_milestone_events(self, user_id: int, engagement_type: str, result: RewardResult) -> None:
        """Emit events for engagement milestone completion."""
        await self.event_bus.publish(
            EventType.WORKFLOW_COMPLETED,
            user_id,
            {
                "workflow": "engagement_milestone",
                "engagement_type": engagement_type,
                "result": result.__dict__
            },
            source="cross_module_rewards"
        )
    
    async def _update_diana_menu_notifications(self, user_id: int, notification_type: str, data: Any) -> None:
        """Update Diana Menu System with new notifications."""
        try:
            diana_system = get_diana_menu_system(self.session)
            # This would integrate with the Diana Menu System for real-time updates
            # Implementation would depend on Diana Menu System's notification interface
            logger.debug(f"Updated Diana menu notifications for user {user_id}: {notification_type}")
        except Exception as e:
            logger.exception(f"Error updating Diana menu notifications: {e}")
    
    # Additional placeholder methods for specific unlock checks...
    async def _check_achievement_narrative_unlocks(self, user_id: int, achievement_id: str) -> List[str]:
        """Check narrative unlocks from achievement."""
        return []
    
    async def _check_achievement_mission_unlocks(self, user_id: int, achievement_id: str) -> List[str]:
        """Check mission unlocks from achievement."""
        return []
    
    async def _check_engagement_narrative_unlocks(self, user_id: int, engagement_type: str, data: Dict[str, Any]) -> List[str]:
        """Check narrative unlocks from engagement."""
        return []
    
    async def _check_engagement_mission_unlocks(self, user_id: int, engagement_type: str, data: Dict[str, Any]) -> List[str]:
        """Check mission unlocks from engagement."""
        return []
    
    async def _award_level_milestone_bonus(self, user_id: int, level: int) -> Dict[str, Any]:
        """Award bonus for level milestones."""
        return {"success": False}
    
    async def _check_points_milestone_unlocks(self, user_id: int, total_points: int) -> Dict[str, Any]:
        """Check unlocks based on total points."""
        return {"has_unlocks": False}
    
    async def _check_reaction_based_unlocks(self, user_id: int, reaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check unlocks based on reactions."""
        return {"has_unlocks": False}
    
    async def _award_streak_milestone_bonus(self, user_id: int, streak: int) -> Dict[str, Any]:
        """Award bonus for streak milestones."""
        return {"success": False}

# ==================== GLOBAL INSTANCE MANAGEMENT ====================

# Global cross-module rewards instance
_cross_module_rewards_instance = None

def get_cross_module_rewards(session: AsyncSession) -> CrossModuleRewards:
    """
    Get or create CrossModuleRewards instance.
    
    Args:
        session: Database session
        
    Returns:
        CrossModuleRewards: The global instance
    """
    global _cross_module_rewards_instance
    if _cross_module_rewards_instance is None or _cross_module_rewards_instance.session != session:
        _cross_module_rewards_instance = CrossModuleRewards(session)
    return _cross_module_rewards_instance

async def initialize_cross_module_rewards(session: AsyncSession) -> Dict[str, Any]:
    """
    Initialize cross-module rewards system.
    
    Args:
        session: Database session
        
    Returns:
        Dict containing initialization results
    """
    try:
        rewards_system = get_cross_module_rewards(session)
        result = await rewards_system.initialize_reward_system()
        
        logger.info("Cross-module rewards system initialized successfully")
        return result
        
    except Exception as e:
        logger.exception(f"Error initializing cross-module rewards system: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error inicializando sistema de recompensas cross-módulo"
        }