"""
Channel Engagement → Dual System Rewards Flow

This service handles the flow where channel engagement activities reward users
with both points and narrative content access, creating an integrated experience.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..point_service import PointService
from ..narrative_service import NarrativeService
from ..user_service import UserService
from ..mission_service import MissionService
from ..integration.channel_engagement_service import ChannelEngagementService
from ..event_bus import get_event_bus, EventType
from ..diana_menu_system import get_diana_menu_system
from database.models import User
from database.narrative_models import UserNarrativeState
from utils.handler_decorators import safe_handler
from utils.message_safety import safe_send_message

logger = logging.getLogger(__name__)

@dataclass
class EngagementRewardRule:
    """Defines reward rules for channel engagement activities."""
    engagement_type: str
    reward_points: int
    narrative_unlock_chance: float  # 0.0 to 1.0
    required_streak: Optional[int] = None
    required_engagement_count: Optional[int] = None
    narrative_rewards: List[str] = None
    special_conditions: Dict[str, Any] = None
    description: str = ""

@dataclass
class EngagementSession:
    """Tracks user engagement within a session or time period."""
    user_id: int
    session_start: datetime
    total_reactions: int
    total_posts: int
    total_comments: int
    channels_engaged: Set[int]
    points_earned: int
    narrative_unlocks: List[str]

@dataclass
class DualReward:
    """Represents combined points and narrative rewards."""
    base_points: int
    bonus_points: int
    total_points: int
    narrative_unlocks: List[str]
    special_access: List[str]
    bonus_multiplier: float
    engagement_streak: int
    reward_message: str

@dataclass
class RewardResult:
    """Result of engagement reward processing."""
    success: bool
    dual_reward: DualReward
    notification_message: str
    menu_updates: List[str]
    achievements_triggered: List[str]

class EngagementRewardsFlow:
    """
    Service managing channel engagement → dual system rewards flow.
    
    Provides dynamic reward allocation combining points and narrative access
    based on engagement patterns, with Diana Menu System integration.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize engagement rewards flow service.
        
        Args:
            session: Database session for all operations
        """
        self.session = session
        
        # Core services
        self.point_service = PointService(session)
        self.narrative_service = NarrativeService(session)
        self.user_service = UserService(session)
        self.mission_service = MissionService(session)
        self.channel_engagement_service = ChannelEngagementService(session)
        
        # Event system integration
        self.event_bus = get_event_bus()
        
        # Engagement reward rules configuration
        self.reward_rules = self._initialize_reward_rules()
        
        # Engagement session tracking
        self.active_sessions: Dict[int, EngagementSession] = {}
        
        # Session timeout (30 minutes)
        self.session_timeout = timedelta(minutes=30)
        
        # Diana notification templates
        self.notification_templates = {
            "reaction_reward": "Diana sonríe al ver tu reacción...\n\n*\"Cada gesto tuyo es como una caricia en mi alma, mi amor...\"*\n\n💋 **+{points} besitos**{narrative_bonus}",
            "comment_reward": "Diana lee tu comentario con interés...\n\n*\"Tus palabras me cautivan, mi querido amante...\"*\n\n💋 **+{points} besitos**{narrative_bonus}",
            "post_reward": "Diana aplaude tu participación...\n\n*\"Tu voz en nuestra comunidad me llena de alegría...\"*\n\n💋 **+{points} besitos**{narrative_bonus}",
            "engagement_streak": "Diana te abraza con emoción...\n\n*\"Tu constante participación demuestra tu devoción. Te mereces algo especial...\"*\n\n🔥 **Racha de {streak} días**\n💋 **+{points} besitos**\n{special_rewards}",
            "session_bonus": "Diana nota tu sesión de participación intensa...\n\n*\"Tu dedicación en esta sesión me tiene fascinada, mi amor...\"*\n\n✨ **Bonus de sesión:**\n💋 **+{bonus_points} besitos adicionales**\n{narrative_unlocks}",
            "cross_channel": "Diana admira tu presencia en múltiples espacios...\n\n*\"Dominas todos nuestros rincones como un verdadero amante experto...\"*\n\n🌟 **Bonus multi-canal:**\n💋 **+{points} besitos**\n{special_access}",
            "milestone_celebration": "Diana celebra tu progreso extraordinario...\n\n*\"Has alcanzado un hito increíble en nuestra relación, mi querido...\"*\n\n🏆 **Hito de participación:**\n{milestone_rewards}"
        }
        
        # Diana expressions for different engagement patterns
        self.diana_expressions = {
            "high_frequency": "Diana está claramente emocionada por tu actividad constante...",
            "quality_engagement": "Diana aprecia la calidad de tus contribuciones...",
            "diverse_participation": "Diana admira tu participación variada...",
            "loyal_community_member": "Diana reconoce tu lealtad a la comunidad...",
            "engagement_champion": "Diana te corona como campeón de participación..."
        }
        
        # Narrative unlock thresholds
        self.narrative_thresholds = {
            "daily_engagement": {"reactions": 5, "unlock": "hint_daily_devotion"},
            "weekly_champion": {"total_points": 100, "unlock": "fragment_diana_appreciation"},
            "social_butterfly": {"channels": 3, "unlock": "clue_community_secrets"},
            "conversation_master": {"comments": 10, "unlock": "backstory_diana_social_side"},
            "reaction_expert": {"reactions": 50, "unlock": "special_access_reaction_gallery"}
        }
    
    def _initialize_reward_rules(self) -> List[EngagementRewardRule]:
        """
        Initialize engagement reward rules for different activity types.
        
        Returns:
            List of reward rules for various engagement activities
        """
        return [
            # Basic engagement rewards
            EngagementRewardRule(
                engagement_type="reaction",
                reward_points=5,
                narrative_unlock_chance=0.1,
                narrative_rewards=["hint_garden_secrets", "clue_diana_mood"],
                description="Basic reaction rewards with chance for hints"
            ),
            EngagementRewardRule(
                engagement_type="comment",
                reward_points=10,
                narrative_unlock_chance=0.2,
                narrative_rewards=["hint_conversation_secrets", "clue_diana_interests"],
                description="Comment rewards with higher narrative chance"
            ),
            EngagementRewardRule(
                engagement_type="post",
                reward_points=20,
                narrative_unlock_chance=0.3,
                narrative_rewards=["fragment_community_story", "backstory_diana_public_side"],
                description="Post rewards with significant narrative unlocks"
            ),
            
            # Streak-based rewards
            EngagementRewardRule(
                engagement_type="daily_streak",
                reward_points=25,
                narrative_unlock_chance=0.8,
                required_streak=7,
                narrative_rewards=["backstory_diana_daily_routine", "special_access_morning_messages"],
                description="Weekly streak rewards with major narrative unlocks"
            ),
            EngagementRewardRule(
                engagement_type="engagement_burst",
                reward_points=15,
                narrative_unlock_chance=0.5,
                required_engagement_count=10,
                special_conditions={"time_window": 60},  # 60 minutes
                narrative_rewards=["fragment_diana_excitement", "clue_intense_moments"],
                description="High-intensity engagement session rewards"
            ),
            
            # Cross-channel engagement
            EngagementRewardRule(
                engagement_type="multi_channel",
                reward_points=40,
                narrative_unlock_chance=0.9,
                special_conditions={"min_channels": 3, "min_activities": 5},
                narrative_rewards=["special_access_all_channels", "backstory_diana_versatility"],
                description="Multi-channel engagement rewards"
            ),
            
            # Quality engagement
            EngagementRewardRule(
                engagement_type="quality_interaction",
                reward_points=35,
                narrative_unlock_chance=0.7,
                special_conditions={"min_comment_length": 50, "engagement_score": 8},
                narrative_rewards=["fragment_deep_conversation", "backstory_diana_intellectual_side"],
                description="High-quality interaction rewards"
            ),
            
            # Milestone rewards
            EngagementRewardRule(
                engagement_type="engagement_milestone",
                reward_points=100,
                narrative_unlock_chance=1.0,
                special_conditions={"total_engagements": [50, 100, 250, 500]},
                narrative_rewards=["special_access_milestone_content", "fragment_diana_gratitude"],
                description="Major engagement milestone rewards"
            )
        ]
    
    async def process_engagement_activity(self, user_id: int, activity_type: str,
                                        activity_data: Dict[str, Any], bot=None) -> RewardResult:
        """
        Process channel engagement activity and award dual rewards.
        
        Args:
            user_id: User ID who performed the activity
            activity_type: Type of activity (reaction, comment, post, etc.)
            activity_data: Additional activity data (channel_id, message_id, etc.)
            bot: Telegram bot instance for notifications
            
        Returns:
            RewardResult with points and narrative rewards
        """
        try:
            logger.info(f"Processing engagement activity: user {user_id}, type {activity_type}")
            
            # Get or create engagement session
            session = await self._get_or_create_engagement_session(user_id)
            
            # Update session with new activity
            await self._update_engagement_session(session, activity_type, activity_data)
            
            # Calculate dual rewards
            dual_reward = await self._calculate_dual_rewards(user_id, activity_type, activity_data, session)
            
            # Award points
            if dual_reward.total_points > 0:
                await self.point_service.add_points(user_id, dual_reward.total_points, bot=bot)
            
            # Process narrative unlocks
            await self._process_narrative_unlocks(user_id, dual_reward.narrative_unlocks)
            
            # Grant special access
            await self._grant_special_access(user_id, dual_reward.special_access)
            
            # Check for triggered achievements
            achievements = await self._check_engagement_achievements(user_id, session)
            
            # Generate notification message
            notification_message = await self._generate_engagement_notification(
                activity_type, dual_reward, session, achievements
            )
            
            # Update Diana Menu System
            menu_updates = await self._update_diana_menu_with_rewards(user_id, dual_reward, notification_message)
            
            # Emit engagement events
            await self._emit_engagement_reward_events(user_id, activity_type, dual_reward, session)
            
            # Send notification to user
            if bot and notification_message:
                await safe_send_message(bot, user_id, notification_message)
            
            logger.info(f"Engagement reward processed: {dual_reward.total_points} points, "
                       f"{len(dual_reward.narrative_unlocks)} narrative unlocks")
            
            return RewardResult(
                success=True,
                dual_reward=dual_reward,
                notification_message=notification_message,
                menu_updates=menu_updates,
                achievements_triggered=achievements
            )
            
        except Exception as e:
            logger.exception(f"Error processing engagement activity for user {user_id}: {e}")
            return RewardResult(
                success=False,
                dual_reward=DualReward(0, 0, 0, [], [], 1.0, 0, ""),
                notification_message="Error procesando actividad. Intenta de nuevo.",
                menu_updates=[],
                achievements_triggered=[]
            )
    
    async def _get_or_create_engagement_session(self, user_id: int) -> EngagementSession:
        """
        Get existing engagement session or create new one.
        
        Args:
            user_id: User ID
            
        Returns:
            EngagementSession for the user
        """
        now = datetime.utcnow()
        
        # Check if user has active session
        if user_id in self.active_sessions:
            session = self.active_sessions[user_id]
            
            # Check if session is still valid
            if now - session.session_start <= self.session_timeout:
                return session
            else:
                # Session expired, archive and create new
                await self._archive_engagement_session(session)
                del self.active_sessions[user_id]
        
        # Create new session
        session = EngagementSession(
            user_id=user_id,
            session_start=now,
            total_reactions=0,
            total_posts=0,
            total_comments=0,
            channels_engaged=set(),
            points_earned=0,
            narrative_unlocks=[]
        )
        
        self.active_sessions[user_id] = session
        logger.debug(f"Created new engagement session for user {user_id}")
        
        return session
    
    async def _update_engagement_session(self, session: EngagementSession, 
                                       activity_type: str, activity_data: Dict[str, Any]) -> None:
        """
        Update engagement session with new activity.
        
        Args:
            session: User's engagement session
            activity_type: Type of activity
            activity_data: Activity details
        """
        # Update activity counters
        if activity_type == "reaction":
            session.total_reactions += 1
        elif activity_type == "comment":
            session.total_comments += 1
        elif activity_type == "post":
            session.total_posts += 1
        
        # Track channel engagement
        channel_id = activity_data.get("channel_id")
        if channel_id:
            session.channels_engaged.add(channel_id)
        
        logger.debug(f"Updated session for user {session.user_id}: "
                    f"{session.total_reactions}R, {session.total_comments}C, {session.total_posts}P")
    
    async def _calculate_dual_rewards(self, user_id: int, activity_type: str,
                                    activity_data: Dict[str, Any], session: EngagementSession) -> DualReward:
        """
        Calculate combined points and narrative rewards.
        
        Args:
            user_id: User ID
            activity_type: Type of activity
            activity_data: Activity details
            session: User's engagement session
            
        Returns:
            DualReward with calculated rewards
        """
        # Get base reward rule
        base_rule = self._get_base_reward_rule(activity_type)
        base_points = base_rule.reward_points if base_rule else 5
        
        # Calculate multipliers
        multiplier = await self._calculate_reward_multiplier(user_id, session, activity_type)
        
        # Calculate bonus points
        bonus_points = await self._calculate_bonus_points(user_id, session, activity_type)
        
        # Total points
        total_points = int((base_points * multiplier) + bonus_points)
        
        # Calculate narrative unlocks
        narrative_unlocks = await self._calculate_narrative_unlocks(
            user_id, activity_type, session, base_rule
        )
        
        # Calculate special access
        special_access = await self._calculate_special_access(user_id, session)
        
        # Get engagement streak
        engagement_streak = await self._get_user_engagement_streak(user_id)
        
        # Generate reward message
        reward_message = await self._generate_reward_message(
            activity_type, total_points, narrative_unlocks, special_access
        )
        
        return DualReward(
            base_points=base_points,
            bonus_points=bonus_points,
            total_points=total_points,
            narrative_unlocks=narrative_unlocks,
            special_access=special_access,
            bonus_multiplier=multiplier,
            engagement_streak=engagement_streak,
            reward_message=reward_message
        )
    
    async def _calculate_reward_multiplier(self, user_id: int, session: EngagementSession,
                                         activity_type: str) -> float:
        """
        Calculate reward multiplier based on various factors.
        
        Args:
            user_id: User ID
            session: User's engagement session
            activity_type: Type of activity
            
        Returns:
            Multiplier value (1.0 or higher)
        """
        multiplier = 1.0
        
        # Session intensity multiplier
        total_activities = session.total_reactions + session.total_comments + session.total_posts
        if total_activities >= 20:
            multiplier += 0.5  # High intensity bonus
        elif total_activities >= 10:
            multiplier += 0.25  # Medium intensity bonus
        
        # Multi-channel bonus
        if len(session.channels_engaged) >= 3:
            multiplier += 0.3
        elif len(session.channels_engaged) >= 2:
            multiplier += 0.15
        
        # Engagement streak bonus
        streak = await self._get_user_engagement_streak(user_id)
        if streak >= 30:
            multiplier += 0.4
        elif streak >= 14:
            multiplier += 0.25
        elif streak >= 7:
            multiplier += 0.15
        
        # Activity type bonus
        if activity_type == "post":
            multiplier += 0.2  # Posts are more valuable
        elif activity_type == "comment":
            multiplier += 0.1  # Comments are moderately valuable
        
        # VIP user bonus
        user = await self.user_service.get_user(user_id)
        if user and getattr(user, 'role', '') == 'vip':
            multiplier += 0.25
        
        return round(multiplier, 2)
    
    async def _calculate_bonus_points(self, user_id: int, session: EngagementSession,
                                    activity_type: str) -> int:
        """
        Calculate bonus points from special conditions.
        
        Args:
            user_id: User ID
            session: User's engagement session
            activity_type: Type of activity
            
        Returns:
            Bonus points amount
        """
        bonus = 0
        
        # Session milestone bonuses
        total_activities = session.total_reactions + session.total_comments + session.total_posts
        if total_activities == 25:
            bonus += 50  # Session champion
        elif total_activities == 10:
            bonus += 20  # Session milestone
        elif total_activities == 5:
            bonus += 10  # Session starter
        
        # First activity in new channel bonus
        channel_id = session.channels_engaged
        if len(channel_id) == 1 and total_activities == 1:
            bonus += 15  # New channel exploration
        
        # Quality engagement bonus (placeholder logic)
        if activity_type == "comment":
            # In real implementation, this would analyze comment quality
            bonus += 5  # Quality comment bonus
        
        return bonus
    
    async def _calculate_narrative_unlocks(self, user_id: int, activity_type: str,
                                         session: EngagementSession, rule: Optional[EngagementRewardRule]) -> List[str]:
        """
        Calculate narrative content unlocks from engagement.
        
        Args:
            user_id: User ID
            activity_type: Type of activity
            session: User's engagement session
            rule: Applicable reward rule
            
        Returns:
            List of narrative content keys to unlock
        """
        unlocks = []
        
        if not rule or not rule.narrative_rewards:
            return unlocks
        
        # Calculate unlock probability
        base_chance = rule.narrative_unlock_chance
        
        # Increase chance based on session intensity
        total_activities = session.total_reactions + session.total_comments + session.total_posts
        intensity_bonus = min(0.3, total_activities * 0.02)  # Max 30% bonus
        
        # Increase chance based on engagement streak
        streak = await self._get_user_engagement_streak(user_id)
        streak_bonus = min(0.2, streak * 0.005)  # Max 20% bonus
        
        final_chance = min(1.0, base_chance + intensity_bonus + streak_bonus)
        
        # Determine if unlock triggers (simplified random logic)
        import random
        if random.random() < final_chance:
            # Select unlock based on activity type and user progress
            available_unlocks = rule.narrative_rewards.copy()
            
            # Filter already unlocked content
            already_unlocked = await self._get_user_unlocked_content(user_id)
            available_unlocks = [u for u in available_unlocks if u not in already_unlocked]
            
            if available_unlocks:
                # Select one unlock (could be randomized or based on progression)
                unlocks.append(available_unlocks[0])
        
        # Special milestone unlocks
        milestone_unlocks = await self._check_engagement_milestones(user_id, session)
        unlocks.extend(milestone_unlocks)
        
        return list(set(unlocks))  # Remove duplicates
    
    async def _calculate_special_access(self, user_id: int, session: EngagementSession) -> List[str]:
        """
        Calculate special access permissions from engagement.
        
        Args:
            user_id: User ID
            session: User's engagement session
            
        Returns:
            List of special access permissions
        """
        special_access = []
        
        # Multi-channel master access
        if len(session.channels_engaged) >= 4:
            special_access.append("multi_channel_master")
        
        # Session champion access
        total_activities = session.total_reactions + session.total_comments + session.total_posts
        if total_activities >= 30:
            special_access.append("session_champion")
        
        # Community contributor access
        if session.total_posts >= 5:
            special_access.append("community_contributor")
        
        return special_access
    
    # Helper methods for data retrieval and processing...
    
    def _get_base_reward_rule(self, activity_type: str) -> Optional[EngagementRewardRule]:
        """Get base reward rule for activity type."""
        for rule in self.reward_rules:
            if rule.engagement_type == activity_type:
                return rule
        return None
    
    async def _get_user_engagement_streak(self, user_id: int) -> int:
        """Get user's current engagement streak."""
        # Placeholder implementation
        return 5
    
    async def _get_user_unlocked_content(self, user_id: int) -> List[str]:
        """Get list of already unlocked narrative content."""
        # Placeholder implementation
        return []
    
    async def _check_engagement_milestones(self, user_id: int, session: EngagementSession) -> List[str]:
        """Check for engagement milestone unlocks."""
        milestones = []
        
        # Check session milestones
        total_activities = session.total_reactions + session.total_comments + session.total_posts
        
        if total_activities == 10:
            milestones.append("milestone_session_active")
        elif total_activities == 25:
            milestones.append("milestone_session_champion")
        
        # Check multi-channel milestones
        if len(session.channels_engaged) == 3:
            milestones.append("milestone_multi_channel")
        
        return milestones
    
    async def _process_narrative_unlocks(self, user_id: int, unlocks: List[str]) -> None:
        """Process narrative content unlocks for user."""
        for unlock_key in unlocks:
            # In real implementation, this would update user's narrative backpack
            logger.debug(f"Processed narrative unlock for user {user_id}: {unlock_key}")
    
    async def _grant_special_access(self, user_id: int, access_list: List[str]) -> None:
        """Grant special access permissions to user."""
        for access in access_list:
            # In real implementation, this would update user permissions
            logger.debug(f"Granted special access to user {user_id}: {access}")
    
    async def _check_engagement_achievements(self, user_id: int, session: EngagementSession) -> List[str]:
        """Check for achievements triggered by engagement."""
        achievements = []
        
        # Session achievements
        total_activities = session.total_reactions + session.total_comments + session.total_posts
        if total_activities >= 20:
            achievements.append("engagement_burst")
        
        # Multi-channel achievements
        if len(session.channels_engaged) >= 3:
            achievements.append("channel_explorer")
        
        return achievements
    
    async def _generate_engagement_notification(self, activity_type: str, dual_reward: DualReward,
                                              session: EngagementSession, achievements: List[str]) -> str:
        """Generate comprehensive engagement notification."""
        # Base activity message
        narrative_bonus = ""
        if dual_reward.narrative_unlocks:
            unlock_list = "\n".join([f"• {unlock}" for unlock in dual_reward.narrative_unlocks])
            narrative_bonus = f"\n\n📖 **Contenido desbloqueado:**\n{unlock_list}"
        
        if activity_type in self.notification_templates:
            base_message = self.notification_templates[activity_type].format(
                points=dual_reward.total_points,
                narrative_bonus=narrative_bonus
            )
        else:
            base_message = f"Diana aprecia tu participación...\n\n💋 **+{dual_reward.total_points} besitos**{narrative_bonus}"
        
        message_parts = [base_message]
        
        # Add session bonus if applicable
        if dual_reward.bonus_points > dual_reward.base_points * 0.5:  # Significant bonus
            bonus_msg = self.notification_templates["session_bonus"].format(
                bonus_points=dual_reward.bonus_points,
                narrative_unlocks="\n".join([f"• {unlock}" for unlock in dual_reward.narrative_unlocks])
            )
            message_parts.append(bonus_msg)
        
        # Add achievement notifications
        if achievements:
            achievement_list = "\n".join([f"🏆 {ach}" for ach in achievements])
            message_parts.append(f"\n**Logros obtenidos:**\n{achievement_list}")
        
        # Add Diana expression based on engagement pattern
        pattern = self._analyze_engagement_pattern(session)
        if pattern in self.diana_expressions:
            message_parts.insert(0, self.diana_expressions[pattern])
        
        return "\n\n".join(message_parts)
    
    def _analyze_engagement_pattern(self, session: EngagementSession) -> str:
        """Analyze engagement pattern for Diana expression."""
        total_activities = session.total_reactions + session.total_comments + session.total_posts
        
        if total_activities >= 25:
            return "engagement_champion"
        elif len(session.channels_engaged) >= 3:
            return "diverse_participation"
        elif session.total_posts >= 3:
            return "quality_engagement"
        elif total_activities >= 10:
            return "high_frequency"
        else:
            return "loyal_community_member"
    
    async def _generate_reward_message(self, activity_type: str, points: int,
                                     narrative_unlocks: List[str], special_access: List[str]) -> str:
        """Generate reward message summary."""
        parts = [f"{points} besitos"]
        
        if narrative_unlocks:
            parts.append(f"{len(narrative_unlocks)} contenido narrativo")
        
        if special_access:
            parts.append(f"{len(special_access)} acceso especial")
        
        return " + ".join(parts)
    
    async def _update_diana_menu_with_rewards(self, user_id: int, dual_reward: DualReward,
                                            notification_message: str) -> List[str]:
        """Update Diana Menu System with engagement rewards."""
        try:
            diana_system = get_diana_menu_system(self.session)
            # Integration with Diana Menu System would be implemented here
            menu_updates = ["points_updated", "narrative_content_available"]
            
            if dual_reward.special_access:
                menu_updates.append("special_access_granted")
            
            logger.debug(f"Updated Diana menu with engagement rewards for user {user_id}")
            return menu_updates
        except Exception as e:
            logger.exception(f"Error updating Diana menu with engagement rewards: {e}")
            return []
    
    async def _emit_engagement_reward_events(self, user_id: int, activity_type: str,
                                           dual_reward: DualReward, session: EngagementSession) -> None:
        """Emit events for engagement reward processing."""
        await self.event_bus.publish(
            EventType.WORKFLOW_COMPLETED,
            user_id,
            {
                "workflow": "engagement_dual_rewards",
                "activity_type": activity_type,
                "points_awarded": dual_reward.total_points,
                "narrative_unlocks": dual_reward.narrative_unlocks,
                "special_access": dual_reward.special_access,
                "session_activities": session.total_reactions + session.total_comments + session.total_posts,
                "channels_engaged": len(session.channels_engaged)
            },
            source="engagement_rewards_flow"
        )
    
    async def _archive_engagement_session(self, session: EngagementSession) -> None:
        """Archive completed engagement session."""
        # In real implementation, this would save session data to database
        logger.debug(f"Archived engagement session for user {session.user_id}: "
                    f"{session.total_reactions + session.total_comments + session.total_posts} activities")

# ==================== GLOBAL INSTANCE MANAGEMENT ====================

_engagement_rewards_flow_instance = None

def get_engagement_rewards_flow(session: AsyncSession) -> EngagementRewardsFlow:
    """
    Get or create EngagementRewardsFlow instance.
    
    Args:
        session: Database session
        
    Returns:
        EngagementRewardsFlow: The global instance
    """
    global _engagement_rewards_flow_instance
    if _engagement_rewards_flow_instance is None or _engagement_rewards_flow_instance.session != session:
        _engagement_rewards_flow_instance = EngagementRewardsFlow(session)
    return _engagement_rewards_flow_instance