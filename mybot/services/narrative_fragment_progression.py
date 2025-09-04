"""
Narrative Fragment Progression Service for Diana Bot

Handles the progression logic through the 15+ narrative fragments,
managing user state, decision consequences, and besitos reward integration
following the 6-level master storyline structure.

Integrates with Diana's character validation and maintains consistency.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from database.narrative_unified import (
    NarrativeFragment, UserNarrativeState, UserDecisionLog, 
    UserMissionProgress, UserArchetype
)
from database.models import User
from services.diana_character_validator import DianaCharacterValidator
from services.rewards.engagement_rewards_flow import EngagementRewardsFlow
from services.point_service import PointService
from services.level_service import LevelService
from services.achievement_service import AchievementService
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class ProgressionResult(Enum):
    """Results of fragment progression attempts."""
    SUCCESS = "success"
    BLOCKED_MISSING_CLUES = "blocked_missing_clues"
    BLOCKED_INSUFFICIENT_LEVEL = "blocked_insufficient_level"
    BLOCKED_VIP_REQUIRED = "blocked_vip_required"
    BLOCKED_SEQUENCE_VIOLATION = "blocked_sequence_violation"
    ERROR = "error"

@dataclass
class FragmentAccessResult:
    """Result of fragment access attempt."""
    can_access: bool
    result_type: ProgressionResult
    fragment: Optional[NarrativeFragment]
    missing_requirements: List[str]
    unlock_message: Optional[str]
    points_awarded: int
    clues_unlocked: List[str]
    next_fragment_suggestions: List[str]

@dataclass
class DecisionConsequence:
    """Consequences of user decisions in fragments."""
    points_awarded: int
    clues_unlocked: List[str]
    narrative_flags: List[str]
    archetyping_adjustments: Dict[str, int]
    next_fragment_id: Optional[str]
    achievement_triggers: List[str]
    special_access_granted: List[str]

class NarrativeFragmentProgression:
    """
    Manages progression through Diana Bot's narrative fragments.
    
    Handles:
    - Fragment access validation
    - Decision processing and consequences
    - User archetyping based on choices
    - Besitos reward integration
    - Character consistency maintenance
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Core services
        self.level_service = LevelService(session)
        self.achievement_service = AchievementService(session)
        self.point_service = PointService(session, self.level_service, self.achievement_service)
        self.notification_service = NotificationService(session, None)  # Bot set later
        self.character_validator = DianaCharacterValidator(session)
        self.engagement_flow = EngagementRewardsFlow(session)
        
        # Fragment progression rules
        self.progression_rules = self._initialize_progression_rules()
        
        # User archetyping weights
        self.archetype_weights = {
            "explorer": {"curiosity_bonus": 1.2, "detail_focus": 1.3, "patience_penalty": 0.9},
            "direct": {"speed_bonus": 1.3, "complexity_penalty": 0.8, "action_bonus": 1.4},
            "romantic": {"emotion_bonus": 1.5, "intimacy_bonus": 1.3, "intellectual_balance": 1.1},
            "analytical": {"depth_bonus": 1.4, "patience_bonus": 1.2, "spontaneity_penalty": 0.9},
            "persistent": {"challenge_bonus": 1.3, "completion_bonus": 1.2, "variety_tolerance": 0.95},
            "patient": {"reflection_bonus": 1.4, "timing_bonus": 1.2, "urgency_penalty": 0.8}
        }

    def _initialize_progression_rules(self) -> Dict[str, Any]:
        """Initialize fragment progression and validation rules."""
        return {
            "level_unlocks": {
                1: {"min_fragments_completed": 0, "required_clues": []},
                2: {"min_fragments_completed": 2, "required_clues": ["clue_diana_first_impression"]},
                3: {"min_fragments_completed": 4, "required_clues": ["clue_diana_deeper_mystery"]},
                4: {"min_fragments_completed": 6, "required_clues": ["clue_diana_observation_skills"], "vip_required": True},
                5: {"min_fragments_completed": 8, "required_clues": ["clue_diana_intimacy_philosophy"], "vip_required": True},
                6: {"min_fragments_completed": 10, "required_clues": ["diana_soul_understanding"], "vip_required": True, "vip_tier": 2}
            },
            "tier_requirements": {
                "los_kinkys": {"vip_required": False, "min_level": 1},
                "el_divan": {"vip_required": True, "min_level": 4, "vip_tier": 1},
                "elite": {"vip_required": True, "min_level": 6, "vip_tier": 2}
            },
            "sequence_validation": {
                "enforce_order": True,
                "allow_backtrack": True,
                "max_level_skip": 1
            }
        }

    async def get_fragment_for_user(self, user_id: int, fragment_id: Optional[str] = None) -> FragmentAccessResult:
        """
        Get appropriate fragment for user based on their progress.
        
        Args:
            user_id: User ID
            fragment_id: Specific fragment ID to access (optional)
            
        Returns:
            FragmentAccessResult with access status and fragment data
        """
        try:
            # Get user and their narrative state
            user = await self._get_user_with_narrative_state(user_id)
            if not user:
                return FragmentAccessResult(
                    can_access=False,
                    result_type=ProgressionResult.ERROR,
                    fragment=None,
                    missing_requirements=["Usuario no encontrado"],
                    unlock_message=None,
                    points_awarded=0,
                    clues_unlocked=[],
                    next_fragment_suggestions=[]
                )
            
            # Determine target fragment
            if fragment_id:
                # Validate access to specific fragment
                return await self._validate_specific_fragment_access(user, fragment_id)
            else:
                # Get next appropriate fragment in progression
                return await self._get_next_progression_fragment(user)
                
        except Exception as e:
            logger.exception(f"Error getting fragment for user {user_id}: {e}")
            return FragmentAccessResult(
                can_access=False,
                result_type=ProgressionResult.ERROR,
                fragment=None,
                missing_requirements=[f"Error del sistema: {str(e)}"],
                unlock_message=None,
                points_awarded=0,
                clues_unlocked=[],
                next_fragment_suggestions=[]
            )

    async def process_user_decision(self, user_id: int, fragment_id: str, choice_id: str, 
                                  additional_data: Optional[Dict[str, Any]] = None) -> DecisionConsequence:
        """
        Process user decision in a narrative fragment.
        
        Args:
            user_id: User ID
            fragment_id: Fragment ID where decision was made
            choice_id: ID of chosen option
            additional_data: Additional context data
            
        Returns:
            DecisionConsequence with all effects of the decision
        """
        try:
            # Get fragment and validate choice
            fragment = await self._get_fragment_by_id(fragment_id)
            if not fragment:
                raise ValueError(f"Fragment {fragment_id} not found")
            
            # Find the chosen option
            chosen_option = None
            for choice in fragment.choices:
                if choice.get("id") == choice_id:
                    chosen_option = choice
                    break
            
            if not chosen_option:
                raise ValueError(f"Choice {choice_id} not found in fragment {fragment_id}")
            
            # Calculate consequences
            consequence = await self._calculate_decision_consequences(
                user_id, fragment, chosen_option, additional_data
            )
            
            # Apply consequences
            await self._apply_decision_consequences(user_id, fragment_id, chosen_option, consequence)
            
            # Log decision
            await self._log_user_decision(user_id, fragment_id, chosen_option, consequence)
            
            # Update user archetyping
            await self._update_user_archetyping(user_id, chosen_option, consequence)
            
            logger.info(f"Processed decision for user {user_id}: {consequence.points_awarded} points, "
                       f"{len(consequence.clues_unlocked)} clues unlocked")
            
            return consequence
            
        except Exception as e:
            logger.exception(f"Error processing decision for user {user_id}: {e}")
            return DecisionConsequence(
                points_awarded=0,
                clues_unlocked=[],
                narrative_flags=["decision_error"],
                archetyping_adjustments={},
                next_fragment_id=None,
                achievement_triggers=[],
                special_access_granted=[]
            )

    async def _validate_specific_fragment_access(self, user: User, fragment_id: str) -> FragmentAccessResult:
        """Validate user access to a specific fragment."""
        
        fragment = await self._get_fragment_by_id(fragment_id)
        if not fragment:
            return FragmentAccessResult(
                can_access=False,
                result_type=ProgressionResult.ERROR,
                fragment=None,
                missing_requirements=["Fragmento no encontrado"],
                unlock_message=None,
                points_awarded=0,
                clues_unlocked=[],
                next_fragment_suggestions=[]
            )
        
        # Check VIP requirements
        if fragment.requires_vip and not self._user_has_vip(user, fragment.vip_tier_required):
            return FragmentAccessResult(
                can_access=False,
                result_type=ProgressionResult.BLOCKED_VIP_REQUIRED,
                fragment=fragment,
                missing_requirements=[f"VIP Tier {fragment.vip_tier_required} requerido"],
                unlock_message="Diana te susurra: 'Algunos secretos requieren... un compromiso más profundo.'",
                points_awarded=0,
                clues_unlocked=[],
                next_fragment_suggestions=[]
            )
        
        # Check level requirements
        narrative_state = getattr(user, 'narrative_state_unified', None)
        if narrative_state and narrative_state.current_level < fragment.storyline_level:
            return FragmentAccessResult(
                can_access=False,
                result_type=ProgressionResult.BLOCKED_INSUFFICIENT_LEVEL,
                fragment=fragment,
                missing_requirements=[f"Nivel {fragment.storyline_level} requerido (actual: {narrative_state.current_level})"],
                unlock_message="Diana sonríe misteriosamente: 'Paciencia, mi querido. Cada secreto tiene su momento.'",
                points_awarded=0,
                clues_unlocked=[],
                next_fragment_suggestions=[]
            )
        
        # Check required clues
        missing_clues = []
        if fragment.required_clues and narrative_state:
            for clue in fragment.required_clues:
                if not narrative_state.has_unlocked_clue(clue):
                    missing_clues.append(clue)
        
        if missing_clues:
            return FragmentAccessResult(
                can_access=False,
                result_type=ProgressionResult.BLOCKED_MISSING_CLUES,
                fragment=fragment,
                missing_requirements=missing_clues,
                unlock_message="Diana te mira con curiosidad: 'Aún hay cosas que debes descubrir antes...'",
                points_awarded=0,
                clues_unlocked=[],
                next_fragment_suggestions=await self._get_suggestion_fragments(user)
            )
        
        # Access granted
        return FragmentAccessResult(
            can_access=True,
            result_type=ProgressionResult.SUCCESS,
            fragment=fragment,
            missing_requirements=[],
            unlock_message=None,
            points_awarded=0,
            clues_unlocked=[],
            next_fragment_suggestions=[]
        )

    async def _get_next_progression_fragment(self, user: User) -> FragmentAccessResult:
        """Get the next appropriate fragment in user's progression."""
        
        narrative_state = getattr(user, 'narrative_state_unified', None)
        if not narrative_state:
            # First time user - get welcome fragment
            welcome_fragment = await self._get_fragment_by_id("fragment_diana_welcome")
            if welcome_fragment:
                return FragmentAccessResult(
                    can_access=True,
                    result_type=ProgressionResult.SUCCESS,
                    fragment=welcome_fragment,
                    missing_requirements=[],
                    unlock_message="Diana te da la bienvenida con una sonrisa enigmática...",
                    points_awarded=0,
                    clues_unlocked=[],
                    next_fragment_suggestions=[]
                )
        
        # Get available fragments for user's current level and tier
        available_fragments = await self._get_available_fragments_for_user(user)
        
        if not available_fragments:
            return FragmentAccessResult(
                can_access=False,
                result_type=ProgressionResult.BLOCKED_SEQUENCE_VIOLATION,
                fragment=None,
                missing_requirements=["No hay fragmentos disponibles en tu nivel actual"],
                unlock_message="Diana reflexiona: 'Has llegado a un punto de pausa en nuestro viaje...'",
                points_awarded=0,
                clues_unlocked=[],
                next_fragment_suggestions=[]
            )
        
        # Select best fragment based on user's archetype and progress
        best_fragment = await self._select_optimal_fragment(user, available_fragments)
        
        return FragmentAccessResult(
            can_access=True,
            result_type=ProgressionResult.SUCCESS,
            fragment=best_fragment,
            missing_requirements=[],
            unlock_message=await self._generate_progression_unlock_message(user, best_fragment),
            points_awarded=0,
            clues_unlocked=[],
            next_fragment_suggestions=[]
        )

    async def _calculate_decision_consequences(self, user_id: int, fragment: NarrativeFragment, 
                                            chosen_option: Dict[str, Any], 
                                            additional_data: Optional[Dict[str, Any]]) -> DecisionConsequence:
        """Calculate all consequences of a user's decision."""
        
        # Base points from choice
        base_points = chosen_option.get("points_reward", 0)
        
        # Additional points from fragment triggers
        trigger_points = 0
        if "points" in fragment.triggers:
            points_data = fragment.triggers["points"]
            if isinstance(points_data, dict):
                trigger_points = points_data.get("base", 0)
            else:
                trigger_points = points_data
        
        # User archetype bonus
        user_archetype = await self._get_user_archetype(user_id)
        archetype_multiplier = await self._calculate_archetype_multiplier(user_archetype, chosen_option)
        
        total_points = int((base_points + trigger_points) * archetype_multiplier)
        
        # Unlocked clues
        clues_unlocked = []
        if "unlocks" in fragment.triggers:
            clues_unlocked.extend(fragment.triggers["unlocks"])
        
        # Narrative flags
        narrative_flags = []
        if "narrative_flags" in fragment.triggers:
            narrative_flags.extend(fragment.triggers["narrative_flags"])
        
        # Archetyping adjustments from choice
        archetyping_adjustments = chosen_option.get("archetyping_data", {})
        
        # Next fragment determination
        next_fragment_id = chosen_option.get("leads_to")
        
        # Achievement triggers
        achievement_triggers = []
        if "achievements" in fragment.triggers:
            achievement_triggers.extend(fragment.triggers["achievements"])
        
        # Special access
        special_access = []
        if "special_access" in fragment.triggers:
            special_access.extend(fragment.triggers["special_access"])
        
        return DecisionConsequence(
            points_awarded=total_points,
            clues_unlocked=clues_unlocked,
            narrative_flags=narrative_flags,
            archetyping_adjustments=archetyping_adjustments,
            next_fragment_id=next_fragment_id,
            achievement_triggers=achievement_triggers,
            special_access_granted=special_access
        )

    async def _apply_decision_consequences(self, user_id: int, fragment_id: str, 
                                         chosen_option: Dict[str, Any], 
                                         consequence: DecisionConsequence) -> None:
        """Apply all decision consequences to user's state."""
        
        # Award points
        if consequence.points_awarded > 0:
            await self.point_service.add_points(user_id, consequence.points_awarded)
        
        # Unlock clues
        if consequence.clues_unlocked:
            narrative_state = await self._get_or_create_narrative_state(user_id)
            for clue in consequence.clues_unlocked:
                if clue not in narrative_state.unlocked_clues:
                    narrative_state.unlocked_clues.append(clue)
            
            await self.session.commit()
        
        # Update narrative flags
        if consequence.narrative_flags:
            # In a real implementation, these would update user's narrative state
            pass
        
        # Trigger achievements
        for achievement in consequence.achievement_triggers:
            await self.achievement_service.unlock_achievement(user_id, achievement)

    async def _log_user_decision(self, user_id: int, fragment_id: str, chosen_option: Dict[str, Any],
                               consequence: DecisionConsequence) -> None:
        """Log user decision for analysis and progression tracking."""
        
        decision_log = UserDecisionLog(
            user_id=user_id,
            fragment_id=fragment_id,
            decision_choice=chosen_option.get("text", ""),
            points_awarded=consequence.points_awarded,
            clues_unlocked=consequence.clues_unlocked,
            made_at=datetime.utcnow()
        )
        
        self.session.add(decision_log)
        await self.session.commit()

    async def _update_user_archetyping(self, user_id: int, chosen_option: Dict[str, Any],
                                     consequence: DecisionConsequence) -> None:
        """Update user's archetype scores based on their decision."""
        
        if not consequence.archetyping_adjustments:
            return
        
        # Get or create user archetype
        result = await self.session.execute(
            select(UserArchetype).where(UserArchetype.user_id == user_id)
        )
        user_archetype = result.scalar_one_or_none()
        
        if not user_archetype:
            user_archetype = UserArchetype(user_id=user_id)
            self.session.add(user_archetype)
        
        # Apply adjustments
        for archetype_name, adjustment in consequence.archetyping_adjustments.items():
            current_score = getattr(user_archetype, f"{archetype_name}_score", 0)
            new_score = max(0, current_score + adjustment)
            setattr(user_archetype, f"{archetype_name}_score", new_score)
        
        # Recalculate dominant archetype
        user_archetype.calculate_dominant_archetype()
        
        await self.session.commit()

    # Helper methods
    
    async def _get_user_with_narrative_state(self, user_id: int) -> Optional[User]:
        """Get user with their narrative state loaded."""
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.narrative_state_unified))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def _get_fragment_by_id(self, fragment_id: str) -> Optional[NarrativeFragment]:
        """Get fragment by ID."""
        result = await self.session.execute(
            select(NarrativeFragment)
            .where(NarrativeFragment.id == fragment_id)
            .where(NarrativeFragment.is_active == True)
        )
        return result.scalar_one_or_none()

    async def _get_available_fragments_for_user(self, user: User) -> List[NarrativeFragment]:
        """Get fragments available for user's current progression state."""
        narrative_state = getattr(user, 'narrative_state_unified', None)
        
        if not narrative_state:
            # Return welcome fragment for new users
            result = await self.session.execute(
                select(NarrativeFragment)
                .where(NarrativeFragment.storyline_level == 1)
                .where(NarrativeFragment.fragment_sequence == 1)
                .where(NarrativeFragment.is_active == True)
            )
            return [f for f in result.scalars().all() if f]
        
        # Get fragments for current level that haven't been completed
        current_level = narrative_state.current_level
        completed_fragments = narrative_state.completed_fragments
        
        result = await self.session.execute(
            select(NarrativeFragment)
            .where(NarrativeFragment.storyline_level <= current_level)
            .where(NarrativeFragment.is_active == True)
        )
        
        available = []
        for fragment in result.scalars().all():
            if fragment.id not in completed_fragments:
                # Check if user meets fragment requirements
                access_result = await self._validate_specific_fragment_access(user, fragment.id)
                if access_result.can_access:
                    available.append(fragment)
        
        return available

    async def _select_optimal_fragment(self, user: User, available_fragments: List[NarrativeFragment]) -> NarrativeFragment:
        """Select the optimal fragment for user based on their archetype and progress."""
        if len(available_fragments) == 1:
            return available_fragments[0]
        
        # Get user's dominant archetype
        user_archetype = await self._get_user_archetype(user.id)
        
        # Score fragments based on user preferences
        fragment_scores = []
        for fragment in available_fragments:
            score = await self._score_fragment_for_user(user, fragment, user_archetype)
            fragment_scores.append((fragment, score))
        
        # Sort by score and return best match
        fragment_scores.sort(key=lambda x: x[1], reverse=True)
        return fragment_scores[0][0]

    async def _score_fragment_for_user(self, user: User, fragment: NarrativeFragment, 
                                     archetype: Optional[str]) -> float:
        """Score a fragment's suitability for a specific user."""
        base_score = 50.0
        
        # Archetype-based scoring
        if archetype and archetype in self.archetype_weights:
            weights = self.archetype_weights[archetype]
            
            # Explorer preference for detailed, mysterious content
            if archetype == "explorer" and fragment.mission_type == "observation":
                base_score += 20.0
            
            # Direct preference for decision points
            if archetype == "direct" and fragment.fragment_type == "DECISION":
                base_score += 15.0
            
            # Romantic preference for emotional content
            if archetype == "romantic" and "emotional" in fragment.content.lower():
                base_score += 18.0
            
            # Analytical preference for complex content
            if archetype == "analytical" and fragment.mission_type == "comprehension":
                base_score += 17.0
        
        # Progression logic - prefer next in sequence
        narrative_state = getattr(user, 'narrative_state_unified', None)
        if narrative_state:
            if fragment.storyline_level == narrative_state.current_level:
                base_score += 10.0
            elif fragment.storyline_level == narrative_state.current_level + 1:
                base_score += 5.0
        
        return base_score

    async def _get_user_archetype(self, user_id: int) -> Optional[str]:
        """Get user's dominant archetype."""
        result = await self.session.execute(
            select(UserArchetype).where(UserArchetype.user_id == user_id)
        )
        archetype = result.scalar_one_or_none()
        return archetype.dominant_archetype if archetype else None

    async def _calculate_archetype_multiplier(self, archetype: Optional[str], chosen_option: Dict[str, Any]) -> float:
        """Calculate point multiplier based on user's archetype and choice."""
        if not archetype or archetype not in self.archetype_weights:
            return 1.0
        
        multiplier = 1.0
        weights = self.archetype_weights[archetype]
        
        # Apply bonuses based on choice characteristics
        option_text = chosen_option.get("text", "").lower()
        
        if "rápido" in option_text or "inmediato" in option_text:
            multiplier *= weights.get("speed_bonus", 1.0)
        
        if "reflexion" in option_text or "pensar" in option_text:
            multiplier *= weights.get("patience_bonus", 1.0)
        
        if "emoción" in option_text or "corazón" in option_text:
            multiplier *= weights.get("emotion_bonus", 1.0)
        
        return multiplier

    async def _get_or_create_narrative_state(self, user_id: int) -> UserNarrativeState:
        """Get or create user's narrative state."""
        result = await self.session.execute(
            select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        )
        state = result.scalar_one_or_none()
        
        if not state:
            state = UserNarrativeState(user_id=user_id)
            self.session.add(state)
            await self.session.commit()
        
        return state

    def _user_has_vip(self, user: User, required_tier: int) -> bool:
        """Check if user has required VIP tier."""
        # In real implementation, this would check user's subscription status
        return getattr(user, 'role', '') == 'vip'

    async def _get_suggestion_fragments(self, user: User) -> List[str]:
        """Get fragment suggestions for blocked users."""
        # Return fragments that might help unlock blocked content
        return ["fragment_diana_welcome", "fragment_lucien_first_challenge"]

    async def _generate_progression_unlock_message(self, user: User, fragment: NarrativeFragment) -> str:
        """Generate Diana's personalized unlock message."""
        messages = [
            f"Diana te sonríe misteriosamente: 'Ah, {fragment.title}... sabía que llegarías aquí.'",
            f"Diana susurra: 'Este fragmento... está esperándote desde hace tiempo.'",
            f"Diana aparece con elegancia: 'Perfecto timing para {fragment.title}, mi querido.'",
        ]
        
        # Select message based on user's archetype or random
        return messages[0]  # Simplified for MVP

# Global instance management
_progression_service_instance = None

def get_narrative_progression_service(session: AsyncSession) -> NarrativeFragmentProgression:
    """Get or create NarrativeFragmentProgression service instance."""
    global _progression_service_instance
    if _progression_service_instance is None or _progression_service_instance.session != session:
        _progression_service_instance = NarrativeFragmentProgression(session)
    return _progression_service_instance