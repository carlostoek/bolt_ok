"""
Narrative Progress → Mission Unlocking Flow

This service handles the specific flow where narrative progress unlocks new missions
and provides dynamic notifications through the Diana Menu System.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dataclasses import dataclass
from datetime import datetime

from ..mission_service import MissionService
from ..narrative_service import NarrativeService
from ..user_service import UserService
from ..event_bus import get_event_bus, EventType
from ..diana_menu_system import get_diana_menu_system
from database.models import Mission, User
from database.narrative_models import NarrativeFragment, UserNarrativeState
from utils.handler_decorators import safe_handler
from utils.message_safety import safe_send_message

logger = logging.getLogger(__name__)

@dataclass
class MissionUnlockRule:
    """Defines rules for mission unlocking based on narrative progress."""
    fragment_key: str
    mission_ids: List[str]
    unlock_condition: str  # "exact", "prefix", "milestone"
    threshold: Optional[int] = None
    description: str = ""

@dataclass 
class UnlockResult:
    """Result of mission unlock operation."""
    success: bool
    unlocked_missions: List[str]
    notification_message: str
    user_level_required: Optional[int] = None
    points_threshold: Optional[int] = None

class NarrativeMissionFlow:
    """
    Service managing narrative progress → mission unlocking flow.
    
    Provides dynamic mission unlocking based on story progression,
    with real-time notifications and Diana Menu System integration.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize narrative mission flow service.
        
        Args:
            session: Database session for all operations
        """
        self.session = session
        
        # Core services
        self.mission_service = MissionService(session)
        self.narrative_service = NarrativeService(session)
        self.user_service = UserService(session)
        
        # Event system integration
        self.event_bus = get_event_bus()
        
        # Mission unlock rules configuration
        self.unlock_rules = self._initialize_unlock_rules()
        
        # Notification templates
        self.notification_templates = {
            "single_mission": "Diana te observa con una sonrisa misteriosa...\n\n*\"Has demostrado tu dedicación a nuestra historia, mi amor. Te he preparado una nueva aventura...\"*\n\n🎯 **Misión desbloqueada:** {mission_name}",
            "multiple_missions": "Diana aplaude suavemente, sus ojos brillando de emoción...\n\n*\"Tu progreso en nuestra historia me impresiona profundamente. Te he preparado varias sorpresas...\"*\n\n🎯 **{count} misiones desbloqueadas:**\n{mission_list}",
            "milestone_unlock": "Diana te toma de las manos, su mirada llena de orgullo...\n\n*\"Has alcanzado un momento especial en nuestra historia, mi amor. Es hora de revelar secretos más profundos...\"*\n\n🌟 **Misiones especiales desbloqueadas:**\n{mission_list}",
            "level_locked": "Diana suspira suavemente, acariciando tu mejilla...\n\n*\"Estas aventuras requieren más experiencia, mi amor. Continúa nuestro viaje y pronto estarás preparado...\"*\n\n🔒 **Misión disponible en nivel {required_level}**",
            "points_locked": "Diana te besa la frente con ternura...\n\n*\"Esta aventura especial requiere más besitos para desbloquear, mi amor. Participa más en nuestros canales...\"*\n\n💋 **Requiere {required_points} besitos**"
        }
        
        # Diana character responses
        self.diana_responses = {
            "level1": "Diana te guía suavemente hacia los jardines secretos...",
            "level2": "Diana susurra secretos al oído mientras exploran juntos...",
            "level3": "Diana revela pasiones ocultas con una sonrisa seductora...",
            "level4": "Diana comparte intimidades reservadas para amantes especiales...",
            "level5": "Diana abre su corazón completamente en momentos de éxtasis..."
        }
    
    def _initialize_unlock_rules(self) -> List[MissionUnlockRule]:
        """
        Initialize mission unlock rules based on narrative progression.
        
        Returns:
            List of unlock rules for different narrative milestones
        """
        return [
            # Level 1 - Introduction to Diana's world
            MissionUnlockRule(
                fragment_key="level1_garden_discovery",
                mission_ids=["daily_interaction", "first_choice"],
                unlock_condition="exact",
                description="First garden exploration unlocks basic interaction missions"
            ),
            MissionUnlockRule(
                fragment_key="level1_",
                mission_ids=["narrative_explorer"],
                unlock_condition="prefix",
                threshold=3,  # After 3 level1 fragments
                description="Multiple level1 fragments unlock exploration missions"
            ),
            
            # Level 2 - Deepening relationship
            MissionUnlockRule(
                fragment_key="level2_first_kiss",
                mission_ids=["romantic_gestures", "intimacy_building"],
                unlock_condition="exact",
                description="First kiss unlocks romantic missions"
            ),
            MissionUnlockRule(
                fragment_key="level2_",
                mission_ids=["vip_content_seeker"],
                unlock_condition="prefix",
                threshold=5,  # After 5 level2 fragments
                description="Advanced level2 progress unlocks VIP missions"
            ),
            
            # Level 3 - Passionate encounters
            MissionUnlockRule(
                fragment_key="level3_passionate_night",
                mission_ids=["passion_master", "secret_desires"],
                unlock_condition="exact",
                description="Passionate night unlocks advanced intimacy missions"
            ),
            MissionUnlockRule(
                fragment_key="level3_",
                mission_ids=["romance_master"],
                unlock_condition="prefix",
                threshold=4,  # After 4 level3 fragments
                description="Level3 mastery unlocks romance expert missions"
            ),
            
            # Level 4 - Deep intimacy
            MissionUnlockRule(
                fragment_key="level4_complete_trust",
                mission_ids=["trust_builder", "emotional_depth"],
                unlock_condition="exact",
                description="Complete trust unlocks emotional missions"
            ),
            MissionUnlockRule(
                fragment_key="level4_",
                mission_ids=["decision_expert"],
                unlock_condition="prefix",
                threshold=6,  # After 6 level4 fragments
                description="Level4 expertise unlocks decision mastery missions"
            ),
            
            # Level 5 - Ultimate connection
            MissionUnlockRule(
                fragment_key="level5_ultimate_union",
                mission_ids=["ultimate_lover", "diana_secrets"],
                unlock_condition="exact",
                description="Ultimate union unlocks final missions"
            ),
            MissionUnlockRule(
                fragment_key="level5_",
                mission_ids=["story_completion", "eternal_bond"],
                unlock_condition="prefix",
                threshold=3,  # After 3 level5 fragments
                description="Level5 completion unlocks finale missions"
            ),
            
            # Special milestone unlocks
            MissionUnlockRule(
                fragment_key="milestone_10_fragments",
                mission_ids=["consistency_reward", "dedication_bonus"],
                unlock_condition="milestone",
                threshold=10,  # After 10 total fragments
                description="10 fragments milestone unlocks dedication missions"
            ),
            MissionUnlockRule(
                fragment_key="milestone_25_fragments",
                mission_ids=["master_storyteller", "diana_favorite"],
                unlock_condition="milestone",
                threshold=25,  # After 25 total fragments
                description="25 fragments milestone unlocks master missions"
            )
        ]
    
    async def process_narrative_progress(self, user_id: int, completed_fragment_key: str, 
                                       bot=None) -> UnlockResult:
        """
        Process narrative progress and check for mission unlocks.
        
        Args:
            user_id: User ID who completed the fragment
            completed_fragment_key: Key of the completed narrative fragment
            bot: Telegram bot instance for notifications
            
        Returns:
            UnlockResult with unlocked missions and notification message
        """
        try:
            logger.info(f"Processing narrative progress: user {user_id}, fragment {completed_fragment_key}")
            
            # Get user's narrative progress
            user_progress = await self._get_user_narrative_progress(user_id)
            
            # Check unlock rules against completed fragment
            unlocked_missions = await self._check_unlock_rules(
                user_id, completed_fragment_key, user_progress
            )
            
            if not unlocked_missions:
                logger.debug(f"No missions unlocked for fragment {completed_fragment_key}")
                return UnlockResult(
                    success=True,
                    unlocked_missions=[],
                    notification_message=""
                )
            
            # Verify user meets requirements for unlocked missions
            validated_missions = await self._validate_mission_requirements(user_id, unlocked_missions)
            
            # Create the missions if they don't exist
            created_missions = await self._ensure_missions_exist(validated_missions["eligible"])
            
            # Update user's available missions
            await self._unlock_missions_for_user(user_id, created_missions)
            
            # Generate notification message
            notification_message = await self._generate_unlock_notification(
                completed_fragment_key, created_missions, validated_missions
            )
            
            # Emit unlock events
            await self._emit_mission_unlock_events(user_id, completed_fragment_key, created_missions)
            
            # Update Diana Menu System
            await self._update_diana_menu_with_unlocks(user_id, created_missions, notification_message)
            
            # Send notification to user
            if bot and notification_message:
                await safe_send_message(bot, user_id, notification_message)
            
            logger.info(f"Narrative mission unlock processed: {len(created_missions)} missions unlocked")
            
            return UnlockResult(
                success=True,
                unlocked_missions=[m.id for m in created_missions],
                notification_message=notification_message,
                user_level_required=validated_missions.get("min_level_required"),
                points_threshold=validated_missions.get("min_points_required")
            )
            
        except Exception as e:
            logger.exception(f"Error processing narrative progress for user {user_id}: {e}")
            return UnlockResult(
                success=False,
                unlocked_missions=[],
                notification_message="Error procesando progreso narrativo. Intenta de nuevo."
            )
    
    async def _get_user_narrative_progress(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive user narrative progress data.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict containing narrative progress information
        """
        try:
            # Get user's current narrative state
            user_state = await self.session.execute(
                select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            )
            user_state = user_state.scalar_one_or_none()
            
            # Get user's completed fragments count by level
            completed_fragments = await self._count_completed_fragments_by_level(user_id)
            
            # Get total fragments completed
            total_fragments = sum(completed_fragments.values())
            
            # Get user level and points
            user = await self.user_service.get_user(user_id)
            user_level = getattr(user, 'level', 1) if user else 1
            user_points = getattr(user, 'points', 0) if user else 0
            
            return {
                "current_fragment": user_state.current_fragment_key if user_state else "start",
                "completed_fragments_by_level": completed_fragments,
                "total_fragments_completed": total_fragments,
                "user_level": user_level,
                "user_points": user_points,
                "narrative_milestones": await self._calculate_narrative_milestones(total_fragments)
            }
            
        except Exception as e:
            logger.exception(f"Error getting user narrative progress: {e}")
            return {
                "current_fragment": "start",
                "completed_fragments_by_level": {},
                "total_fragments_completed": 0,
                "user_level": 1,
                "user_points": 0,
                "narrative_milestones": []
            }
    
    async def _check_unlock_rules(self, user_id: int, fragment_key: str, 
                                progress: Dict[str, Any]) -> List[str]:
        """
        Check unlock rules against completed fragment and user progress.
        
        Args:
            user_id: User ID
            fragment_key: Completed fragment key
            progress: User's narrative progress data
            
        Returns:
            List of mission IDs that should be unlocked
        """
        unlocked_missions = []
        
        for rule in self.unlock_rules:
            should_unlock = False
            
            if rule.unlock_condition == "exact":
                # Exact fragment key match
                should_unlock = fragment_key == rule.fragment_key
                
            elif rule.unlock_condition == "prefix":
                # Fragment key prefix match with threshold
                if fragment_key.startswith(rule.fragment_key):
                    level_prefix = rule.fragment_key.rstrip("_")
                    completed_count = progress["completed_fragments_by_level"].get(level_prefix, 0)
                    should_unlock = completed_count >= (rule.threshold or 1)
                    
            elif rule.unlock_condition == "milestone":
                # Total fragments milestone
                total_completed = progress["total_fragments_completed"]
                should_unlock = total_completed >= (rule.threshold or 1)
            
            if should_unlock:
                # Check if missions are already unlocked for this user
                new_missions = await self._filter_already_unlocked_missions(user_id, rule.mission_ids)
                unlocked_missions.extend(new_missions)
                
                logger.debug(f"Rule matched for {fragment_key}: {rule.description}, "
                           f"unlocking {len(new_missions)} new missions")
        
        # Remove duplicates
        return list(set(unlocked_missions))
    
    async def _validate_mission_requirements(self, user_id: int, mission_ids: List[str]) -> Dict[str, Any]:
        """
        Validate user meets requirements for mission unlocks.
        
        Args:
            user_id: User ID
            mission_ids: List of mission IDs to validate
            
        Returns:
            Dict containing eligible missions and requirement info
        """
        user = await self.user_service.get_user(user_id)
        user_level = getattr(user, 'level', 1) if user else 1
        user_points = getattr(user, 'points', 0) if user else 0
        
        eligible_missions = []
        locked_missions = []
        min_level_required = None
        min_points_required = None
        
        # Mission requirements (would be configurable in a real system)
        mission_requirements = {
            "vip_content_seeker": {"min_level": 5, "min_points": 100},
            "romance_master": {"min_level": 8, "min_points": 250},
            "decision_expert": {"min_level": 10, "min_points": 500},
            "ultimate_lover": {"min_level": 15, "min_points": 1000},
            "master_storyteller": {"min_level": 20, "min_points": 2000}
        }
        
        for mission_id in mission_ids:
            requirements = mission_requirements.get(mission_id, {})
            
            required_level = requirements.get("min_level", 1)
            required_points = requirements.get("min_points", 0)
            
            if user_level >= required_level and user_points >= required_points:
                eligible_missions.append(mission_id)
            else:
                locked_missions.append({
                    "mission_id": mission_id,
                    "required_level": required_level,
                    "required_points": required_points
                })
                
                if min_level_required is None or required_level < min_level_required:
                    min_level_required = required_level
                if min_points_required is None or required_points < min_points_required:
                    min_points_required = required_points
        
        return {
            "eligible": eligible_missions,
            "locked": locked_missions,
            "min_level_required": min_level_required,
            "min_points_required": min_points_required
        }
    
    async def _ensure_missions_exist(self, mission_ids: List[str]) -> List[Mission]:
        """
        Ensure missions exist in database, create if necessary.
        
        Args:
            mission_ids: List of mission IDs to check/create
            
        Returns:
            List of Mission objects
        """
        existing_missions = []
        
        for mission_id in mission_ids:
            mission = await self.mission_service.get_mission_by_id(mission_id)
            
            if mission:
                existing_missions.append(mission)
            else:
                # Create mission with default parameters
                new_mission = await self._create_default_mission(mission_id)
                if new_mission:
                    existing_missions.append(new_mission)
        
        return existing_missions
    
    async def _create_default_mission(self, mission_id: str) -> Optional[Mission]:
        """
        Create a default mission configuration.
        
        Args:
            mission_id: Mission ID to create
            
        Returns:
            Created Mission object or None
        """
        # Mission templates (would be configurable in a real system)
        mission_templates = {
            "daily_interaction": {
                "name": "Encuentro Diario con Diana",
                "description": "Visita a Diana todos los días para mantener vuestra conexión",
                "type": "daily",
                "target_value": 1,
                "reward_points": 15
            },
            "first_choice": {
                "name": "Primera Decisión Importante",
                "description": "Toma tu primera decisión narrativa significativa",
                "type": "one_time",
                "target_value": 1,
                "reward_points": 25
            },
            "narrative_explorer": {
                "name": "Explorador de Historias",
                "description": "Explora múltiples fragmentos narrativos",
                "type": "weekly",
                "target_value": 5,
                "reward_points": 50
            },
            "romantic_gestures": {
                "name": "Gestos Románticos",
                "description": "Realiza gestos románticos en los canales",
                "type": "daily",
                "target_value": 3,
                "reward_points": 20
            },
            "vip_content_seeker": {
                "name": "Buscador de Contenido VIP",
                "description": "Accede a contenido exclusivo VIP",
                "type": "weekly",
                "target_value": 3,
                "reward_points": 100
            },
            "romance_master": {
                "name": "Maestro del Romance",
                "description": "Domina las artes del romance con Diana",
                "type": "one_time",
                "target_value": 1,
                "reward_points": 200
            }
        }
        
        template = mission_templates.get(mission_id)
        if not template:
            logger.warning(f"No template found for mission {mission_id}")
            return None
        
        try:
            mission = await self.mission_service.create_mission(
                name=template["name"],
                description=template["description"],
                mission_type=template["type"],
                target_value=template["target_value"],
                reward_points=template["reward_points"],
                requires_action=True,
                action_data={"unlocked_by_narrative": True}
            )
            
            logger.info(f"Created mission from template: {mission_id}")
            return mission
            
        except Exception as e:
            logger.exception(f"Error creating mission {mission_id}: {e}")
            return None
    
    async def _unlock_missions_for_user(self, user_id: int, missions: List[Mission]) -> None:
        """
        Mark missions as available for the user.
        
        Args:
            user_id: User ID
            missions: List of Mission objects to unlock
        """
        # In this implementation, missions are globally available
        # In a more complex system, you might track per-user mission availability
        
        user = await self.user_service.get_user(user_id)
        if user:
            # Update user's mission tracking if needed
            for mission in missions:
                logger.debug(f"Mission {mission.id} unlocked for user {user_id}")
        
        # Additional tracking logic could be implemented here
    
    async def _generate_unlock_notification(self, fragment_key: str, missions: List[Mission],
                                          validation_result: Dict[str, Any]) -> str:
        """
        Generate personalized unlock notification message.
        
        Args:
            fragment_key: Completed fragment key
            missions: List of unlocked Mission objects
            validation_result: Mission validation results
            
        Returns:
            Formatted notification message
        """
        if not missions and not validation_result.get("locked"):
            return ""
        
        # Generate message for unlocked missions
        message_parts = []
        
        if missions:
            if len(missions) == 1:
                message = self.notification_templates["single_mission"].format(
                    mission_name=missions[0].name
                )
            else:
                mission_list = "\n".join([f"• {m.name}" for m in missions])
                message = self.notification_templates["multiple_missions"].format(
                    count=len(missions),
                    mission_list=mission_list
                )
            
            message_parts.append(message)
        
        # Add locked mission information
        locked_missions = validation_result.get("locked", [])
        if locked_missions:
            for locked in locked_missions:
                if locked.get("required_level", 0) > 1:
                    locked_msg = self.notification_templates["level_locked"].format(
                        required_level=locked["required_level"]
                    )
                elif locked.get("required_points", 0) > 0:
                    locked_msg = self.notification_templates["points_locked"].format(
                        required_points=locked["required_points"]
                    )
                else:
                    continue
                
                message_parts.append(locked_msg)
        
        # Add Diana character response based on progress
        fragment_level = self._extract_level_from_fragment(fragment_key)
        diana_response = self.diana_responses.get(fragment_level, "")
        if diana_response:
            message_parts.insert(0, diana_response)
        
        return "\n\n".join(message_parts)
    
    # Helper methods...
    
    async def _count_completed_fragments_by_level(self, user_id: int) -> Dict[str, int]:
        """Count completed fragments grouped by level."""
        # This would analyze user's narrative history
        # Placeholder implementation
        return {"level1": 3, "level2": 2, "level3": 1}
    
    async def _calculate_narrative_milestones(self, total_fragments: int) -> List[str]:
        """Calculate achieved narrative milestones."""
        milestones = []
        if total_fragments >= 10:
            milestones.append("milestone_10_fragments")
        if total_fragments >= 25:
            milestones.append("milestone_25_fragments")
        return milestones
    
    async def _filter_already_unlocked_missions(self, user_id: int, mission_ids: List[str]) -> List[str]:
        """Filter out missions already unlocked for user."""
        # Placeholder - would check user's mission history
        return mission_ids
    
    def _extract_level_from_fragment(self, fragment_key: str) -> str:
        """Extract level identifier from fragment key."""
        for level in ["level1", "level2", "level3", "level4", "level5"]:
            if fragment_key.startswith(level):
                return level
        return "level1"
    
    async def _emit_mission_unlock_events(self, user_id: int, fragment_key: str, 
                                        missions: List[Mission]) -> None:
        """Emit events for mission unlocks."""
        await self.event_bus.publish(
            EventType.WORKFLOW_COMPLETED,
            user_id,
            {
                "workflow": "narrative_mission_unlock",
                "fragment_key": fragment_key,
                "unlocked_missions": [m.id for m in missions],
                "mission_count": len(missions)
            },
            source="narrative_mission_flow"
        )
    
    async def _update_diana_menu_with_unlocks(self, user_id: int, missions: List[Mission],
                                            notification_message: str) -> None:
        """Update Diana Menu System with mission unlocks."""
        try:
            diana_system = get_diana_menu_system(self.session)
            # Integration with Diana Menu System would be implemented here
            logger.debug(f"Updated Diana menu with {len(missions)} mission unlocks for user {user_id}")
        except Exception as e:
            logger.exception(f"Error updating Diana menu with mission unlocks: {e}")

# ==================== GLOBAL INSTANCE MANAGEMENT ====================

_narrative_mission_flow_instance = None

def get_narrative_mission_flow(session: AsyncSession) -> NarrativeMissionFlow:
    """
    Get or create NarrativeMissionFlow instance.
    
    Args:
        session: Database session
        
    Returns:
        NarrativeMissionFlow: The global instance
    """
    global _narrative_mission_flow_instance
    if _narrative_mission_flow_instance is None or _narrative_mission_flow_instance.session != session:
        _narrative_mission_flow_instance = NarrativeMissionFlow(session)
    return _narrative_mission_flow_instance