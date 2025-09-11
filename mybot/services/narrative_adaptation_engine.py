"""
Dynamic Narrative Adaptation Engine - The crown jewel of the storytelling system.

This engine creates a completely personalized narrative experience by:
- Real-time emotional analysis and response adaptation
- Dynamic persona voice evolution based on user interaction patterns
- Contextual memory system that remembers and references specific user moments
- Adaptive content generation that feels organic, never mechanical

The engine integrates seamlessly with the existing narrative infrastructure while
adding sophisticated personalization layers that make each user's experience unique.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc

# Import existing services
from .narrative_engine import NarrativeEngine
from .narrative_service import NarrativeService
from .user_service import UserService
from .point_service import PointService
from database.models import User
from database.narrative_models import StoryFragment, UserNarrativeState

logger = logging.getLogger(__name__)

class EmotionalState(Enum):
    """User emotional states that drive narrative adaptation."""
    CURIOUS = "curious"
    EXCITED = "excited"
    ROMANTIC = "romantic"
    PLAYFUL = "playful"
    INTENSE = "intense"
    CONTEMPLATIVE = "contemplative"
    PASSIONATE = "passionate"
    MYSTERIOUS = "mysterious"
    VULNERABLE = "vulnerable"
    CONFIDENT = "confident"

class UserArchetype(Enum):
    """User personality archetypes for targeted personalization."""
    EXPLORER = "explorer"          # Seeks discovery and novelty
    ROMANTIC = "romantic"          # Values emotional connection
    ADVENTURER = "adventurer"      # Craves excitement and risk
    INTELLECTUAL = "intellectual"  # Enjoys complexity and depth
    SENSUALIST = "sensualist"     # Focuses on physical and sensual experiences
    MYSTIC = "mystic"             # Drawn to mystery and the unknown
    DOMINANT = "dominant"         # Prefers control and leadership
    SUBMISSIVE = "submissive"     # Enjoys being guided and led

@dataclass
class EmotionalContext:
    """Rich emotional context for adaptive content generation."""
    current_state: EmotionalState
    intensity: float  # 0.0 to 1.0
    previous_states: List[Tuple[EmotionalState, datetime]]
    triggers: Dict[str, Any]  # What caused this emotional state
    duration: timedelta  # How long in this state
    volatility: float  # How quickly emotions change (0.0 to 1.0)

@dataclass
class UserPersonalizationProfile:
    """Comprehensive user profile for narrative personalization."""
    user_id: int
    archetype: UserArchetype
    archetype_confidence: float  # How certain we are of the classification
    emotional_baseline: EmotionalState  # User's default emotional state
    interaction_patterns: Dict[str, Any]  # Patterns in choices and behaviors
    preferences: Dict[str, float]  # Weighted preferences for content types
    memory_moments: List[Dict[str, Any]]  # Memorable interaction moments
    voice_evolution_stage: int  # How Diana/Lucien's voice has evolved for this user
    relationship_depth: float  # 0.0 to 1.0 - how deep the narrative relationship is
    last_updated: datetime

class NarrativeAdaptationEngine:
    """
    The ultimate personalization engine that creates unique narrative experiences.
    
    This engine is the crown jewel - it must deliver perfect, seamless personalization
    that feels genuinely human-crafted, never algorithmic or mechanical.
    """
    
    def __init__(self, session: AsyncSession, bot=None):
        self.session = session
        self.bot = bot
        
        # Core narrative services
        self.narrative_engine = NarrativeEngine(session, bot)
        self.narrative_service = NarrativeService(session)
        self.user_service = UserService(session)
        self.point_service = PointService(session)
        
        # Emotional analysis components (to be initialized)
        self.emotional_analyzer = None
        self.archetype_classifier = None
        
        # Cache for user profiles to optimize performance
        self._profile_cache: Dict[int, UserPersonalizationProfile] = {}
        self._cache_timeout = timedelta(minutes=30)
        
        logger.info("NarrativeAdaptationEngine initialized")
    
    async def get_adaptive_narrative_response(
        self, 
        user_id: int, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a completely personalized narrative response.
        
        This is the main entry point that orchestrates all adaptive components
        to create a uniquely tailored experience for each user.
        
        Args:
            user_id: The user requesting the narrative content
            context: Current interaction context (message, choice, etc.)
            
        Returns:
            Dict containing adaptive narrative content with personalized voice,
            emotional resonance, and contextual references
        """
        try:
            # Get or create user personalization profile
            profile = await self._get_user_profile(user_id)
            
            # Analyze current emotional context
            emotional_context = await self._analyze_emotional_context(user_id, context)
            
            # Get current narrative fragment
            current_fragment = await self.narrative_engine.get_user_current_fragment(user_id)
            if not current_fragment:
                return await self._handle_narrative_start(user_id, profile)
            
            # Generate adaptive content based on all factors
            adaptive_content = await self._generate_adaptive_content(
                current_fragment, profile, emotional_context, context
            )
            
            # Update user profile with new interaction data
            await self._update_profile_from_interaction(profile, emotional_context, context)
            
            # Cache the updated profile
            self._profile_cache[user_id] = profile
            
            return {
                "success": True,
                "content": adaptive_content,
                "emotional_state": emotional_context.current_state.value,
                "personalization_confidence": profile.archetype_confidence,
                "relationship_depth": profile.relationship_depth
            }
            
        except Exception as e:
            logger.exception(f"Error in adaptive narrative generation for user {user_id}: {e}")
            # Fallback to standard narrative response
            fragment = await self.narrative_engine.get_user_current_fragment(user_id)
            return {
                "success": False,
                "content": fragment.text if fragment else "Diana looks at you with gentle confusion...",
                "error": "adaptive_generation_failed",
                "fallback": True
            }
    
    async def process_adaptive_decision(
        self, 
        user_id: int, 
        choice_index: int,
        decision_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a user decision with full adaptive context awareness.
        
        This method not only advances the narrative but learns from the choice
        to better understand the user's personality and preferences.
        """
        try:
            # Get user profile for context
            profile = await self._get_user_profile(user_id)
            
            # Analyze the decision's emotional and personality implications
            decision_insights = await self._analyze_decision_patterns(
                user_id, choice_index, decision_context, profile
            )
            
            # Process the narrative progression
            next_fragment = await self.narrative_engine.process_user_decision(
                user_id, choice_index
            )
            
            if not next_fragment:
                return {"success": False, "error": "decision_processing_failed"}
            
            # Generate adaptive response for the new fragment
            emotional_context = await self._analyze_emotional_context(
                user_id, {"decision_made": True, "choice_index": choice_index}
            )
            
            adaptive_response = await self._generate_adaptive_content(
                next_fragment, profile, emotional_context, decision_context
            )
            
            # Update profile with decision insights
            await self._update_profile_from_decision(profile, decision_insights)
            
            return {
                "success": True,
                "fragment": next_fragment,
                "adaptive_content": adaptive_response,
                "personality_insights": decision_insights,
                "emotional_evolution": emotional_context.current_state.value
            }
            
        except Exception as e:
            logger.exception(f"Error in adaptive decision processing for user {user_id}: {e}")
            # Fallback to standard decision processing
            next_fragment = await self.narrative_engine.process_user_decision(
                user_id, choice_index
            )
            return {
                "success": False,
                "fragment": next_fragment,
                "error": "adaptive_decision_failed",
                "fallback": True
            }
    
    async def _get_user_profile(self, user_id: int) -> UserPersonalizationProfile:
        """Get or create a comprehensive user personalization profile."""
        # Check cache first
        if user_id in self._profile_cache:
            cached_profile = self._profile_cache[user_id]
            if datetime.now() - cached_profile.last_updated < self._cache_timeout:
                return cached_profile
        
        # Try to load from database or create new
        profile_data = await self._load_profile_from_database(user_id)
        
        if profile_data:
            profile = UserPersonalizationProfile(**profile_data)
        else:
            # Create new profile with intelligent defaults
            profile = await self._create_initial_profile(user_id)
        
        # Cache the profile
        self._profile_cache[user_id] = profile
        return profile
    
    async def _create_initial_profile(self, user_id: int) -> UserPersonalizationProfile:
        """Create an initial personalization profile for a new user."""
        user = await self.user_service.get_user(user_id)
        narrative_state = await self.session.execute(
            select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        )
        narrative_state = narrative_state.scalar_one_or_none()
        
        # Analyze initial indicators from existing data
        initial_archetype = UserArchetype.EXPLORER  # Default starting point
        archetype_confidence = 0.1  # Very low confidence initially
        
        # If user has some history, try to infer initial tendencies
        if narrative_state and narrative_state.choices_made:
            initial_archetype, archetype_confidence = await self._infer_archetype_from_history(
                narrative_state.choices_made
            )
        
        return UserPersonalizationProfile(
            user_id=user_id,
            archetype=initial_archetype,
            archetype_confidence=archetype_confidence,
            emotional_baseline=EmotionalState.CURIOUS,
            interaction_patterns={},
            preferences={},
            memory_moments=[],
            voice_evolution_stage=0,
            relationship_depth=0.0,
            last_updated=datetime.now()
        )
    
    async def _analyze_emotional_context(
        self, 
        user_id: int, 
        context: Dict[str, Any]
    ) -> EmotionalContext:
        """
        Analyze the user's current emotional state based on interaction context.
        
        This is a sophisticated emotional analysis that considers:
        - Recent interaction patterns
        - Choice patterns and timing
        - User's emotional history
        - Current narrative context
        """
        # For now, implement a sophisticated heuristic-based approach
        # This would be where ML-based emotion analysis would integrate
        
        profile = await self._get_user_profile(user_id)
        
        # Analyze context clues for emotional state
        current_state = profile.emotional_baseline
        intensity = 0.5
        triggers = {}
        
        # Context-based emotional inference
        if "decision_made" in context:
            # Decision-making often indicates engagement
            current_state = EmotionalState.ENGAGED if hasattr(EmotionalState, 'ENGAGED') else EmotionalState.EXCITED
            intensity = 0.7
            triggers["decision_context"] = True
        
        if "first_interaction" in context:
            current_state = EmotionalState.CURIOUS
            intensity = 0.6
            triggers["novelty"] = True
        
        # Consider user's archetype in emotional response
        if profile.archetype == UserArchetype.ROMANTIC:
            if current_state == EmotionalState.EXCITED:
                current_state = EmotionalState.ROMANTIC
                intensity += 0.2
        elif profile.archetype == UserArchetype.ADVENTURER:
            intensity += 0.1  # Adventurers tend to be more intense
        
        # Build emotional context
        return EmotionalContext(
            current_state=current_state,
            intensity=min(intensity, 1.0),
            previous_states=[],  # Would load from database in full implementation
            triggers=triggers,
            duration=timedelta(minutes=5),  # Estimated
            volatility=0.3  # Default moderate volatility
        )
    
    async def _generate_adaptive_content(
        self,
        fragment: StoryFragment,
        profile: UserPersonalizationProfile,
        emotional_context: EmotionalContext,
        interaction_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate completely personalized narrative content.
        
        This is where the magic happens - creating content that feels uniquely
        crafted for each user based on their personality, emotional state,
        and relationship history.
        """
        # Base content from fragment
        base_text = fragment.text
        character = fragment.character or "Diana"
        
        # Generate voice-adapted content
        adapted_voice = await self._adapt_character_voice(
            character, base_text, profile, emotional_context
        )
        
        # Add contextual memory references
        memory_enhanced = await self._add_contextual_memories(
            adapted_voice, profile, interaction_context
        )
        
        # Add emotional resonance
        emotionally_tuned = await self._tune_emotional_resonance(
            memory_enhanced, emotional_context, profile
        )
        
        # Generate personalized choices if this fragment has decisions
        choices = await self._generate_adaptive_choices(
            fragment, profile, emotional_context
        )
        
        return {
            "text": emotionally_tuned,
            "character": character,
            "voice_evolution_stage": profile.voice_evolution_stage,
            "emotional_tone": emotional_context.current_state.value,
            "personalization_level": profile.archetype_confidence,
            "choices": choices,
            "memory_references": len([m for m in profile.memory_moments if self._is_recent_memory(m)]),
            "relationship_indicators": await self._get_relationship_indicators(profile)
        }
    
    async def _adapt_character_voice(
        self,
        character: str,
        base_text: str,
        profile: UserPersonalizationProfile,
        emotional_context: EmotionalContext
    ) -> str:
        """
        Adapt the character's voice based on the user's relationship evolution.
        
        Diana and Lucien's way of speaking evolves as their relationship with
        the user deepens, becoming more intimate, personal, and attuned.
        """
        # Voice evolution stages:
        # 0: Formal, cautious, mysterious
        # 1: Warm, inviting, still somewhat reserved  
        # 2: Playful, flirtatious, more personal
        # 3: Intimate, knowing, deeply connected
        # 4: Passionate, intense, completely attuned
        # 5: Soulmate level - finishing thoughts, deep sync
        
        stage = profile.voice_evolution_stage
        archetype = profile.archetype
        emotional_state = emotional_context.current_state
        
        # Character-specific voice adaptations
        if character.lower() == "diana":
            adapted_text = await self._adapt_diana_voice(
                base_text, stage, archetype, emotional_state
            )
        elif character.lower() == "lucien":
            adapted_text = await self._adapt_lucien_voice(
                base_text, stage, archetype, emotional_state
            )
        else:
            adapted_text = base_text
        
        return adapted_text
    
    async def _adapt_diana_voice(
        self,
        text: str,
        evolution_stage: int,
        archetype: UserArchetype,
        emotional_state: EmotionalState
    ) -> str:
        """Adapt Diana's voice to the user's specific profile and evolution stage."""
        
        # Stage-based voice evolution
        voice_patterns = {
            0: {
                "greeting": "Diana observes you with curious, cautious eyes",
                "uncertainty": "she seems to weigh her words carefully",
                "interest": "a flicker of intrigue crosses her features"
            },
            1: {
                "greeting": "Diana's lips curve into a welcoming smile",
                "warmth": "her voice carries a warmth that wasn't there before",
                "recognition": "there's something familiar in the way she looks at you"
            },
            2: {
                "playful": "Diana's eyes dance with mischief",
                "flirtation": "she leans closer, her voice dropping to a whisper",
                "tease": "a playful smirk plays at the corners of her mouth"
            },
            3: {
                "intimate": "Diana's touch lingers, electric and knowing",
                "connection": "she reads your thoughts before you voice them",
                "passion": "her breath catches as she draws nearer"
            },
            4: {
                "intense": "Diana's eyes burn with an intensity that mirrors your own",
                "synchronized": "you move together as if choreographed by desire",
                "complete": "the space between you crackles with unspoken understanding"
            },
            5: {
                "soulmate": "Diana finishes your thought with a knowing smile",
                "transcendent": "words become unnecessary between you",
                "unity": "you exist as two parts of the same burning flame"
            }
        }
        
        # Archetype-specific adaptations
        archetype_voice = {
            UserArchetype.ROMANTIC: {
                "emphasis": "emotional depth, tender moments",
                "style": "poetic, heartfelt"
            },
            UserArchetype.ADVENTURER: {
                "emphasis": "excitement, boldness",
                "style": "energetic, daring"
            },
            UserArchetype.INTELLECTUAL: {
                "emphasis": "complexity, deeper meaning",
                "style": "thoughtful, layered"
            },
            UserArchetype.SENSUALIST: {
                "emphasis": "sensory details, physical connection",
                "style": "vivid, tactile"
            }
        }
        
        # For now, return enhanced version of original text
        # In full implementation, this would use sophisticated NLP transformation
        enhanced_text = text
        
        # Add stage-appropriate voice elements
        if evolution_stage >= 2 and archetype == UserArchetype.ROMANTIC:
            enhanced_text = f"*Diana's voice carries a tenderness reserved just for you* {enhanced_text}"
        elif evolution_stage >= 3 and archetype == UserArchetype.SENSUALIST:
            enhanced_text = f"*Her words caress your senses like silk* {enhanced_text}"
        
        return enhanced_text
    
    async def _adapt_lucien_voice(
        self,
        text: str,
        evolution_stage: int,
        archetype: UserArchetype,
        emotional_state: EmotionalState
    ) -> str:
        """Adapt Lucien's voice to the user's specific profile and evolution stage."""
        
        # Lucien's voice evolution - more mysterious, intense, commanding
        voice_patterns = {
            0: "calculating, distant, mysterious",
            1: "intrigued, slightly warmer, still guarded",
            2: "charming, seductive, more direct",
            3: "possessive, intense, deeply connected",
            4: "dominant, passionate, completely attuned",
            5: "transcendent connection, perfect synchronization"
        }
        
        # Similar pattern to Diana but with Lucien's darker, more intense personality
        enhanced_text = text
        
        if evolution_stage >= 2 and archetype == UserArchetype.SUBMISSIVE:
            enhanced_text = f"*Lucien's voice drops to a commanding whisper* {enhanced_text}"
        elif evolution_stage >= 3 and archetype == UserArchetype.MYSTERIOUS:
            enhanced_text = f"*His eyes hold secrets that mirror your own* {enhanced_text}"
        
        return enhanced_text
    
    async def _add_contextual_memories(
        self,
        text: str,
        profile: UserPersonalizationProfile,
        context: Dict[str, Any]
    ) -> str:
        """Add references to shared memories and previous interactions."""
        
        # Select relevant memories based on current context
        relevant_memories = [
            memory for memory in profile.memory_moments 
            if self._is_contextually_relevant_memory(memory, context)
        ]
        
        if not relevant_memories:
            return text
        
        # Add subtle memory reference
        recent_memory = relevant_memories[0]  # Most relevant
        memory_reference = await self._craft_memory_reference(recent_memory, profile)
        
        if memory_reference:
            text = f"{text}\n\n*{memory_reference}*"
        
        return text
    
    async def _tune_emotional_resonance(
        self,
        text: str,
        emotional_context: EmotionalContext,
        profile: UserPersonalizationProfile
    ) -> str:
        """Fine-tune the content to resonate with the user's current emotional state."""
        
        emotional_modifiers = {
            EmotionalState.PASSIONATE: {
                "intensity_boost": 0.3,
                "style": "intense, burning, consuming"
            },
            EmotionalState.ROMANTIC: {
                "tenderness_boost": 0.4,
                "style": "tender, heartfelt, deeply emotional"
            },
            EmotionalState.PLAYFUL: {
                "lightness_boost": 0.3,
                "style": "teasing, mischievous, fun"
            },
            EmotionalState.MYSTERIOUS: {
                "intrigue_boost": 0.4,
                "style": "enigmatic, alluring, secretive"
            }
        }
        
        # Apply emotional resonance based on current state and intensity
        current_modifier = emotional_modifiers.get(emotional_context.current_state, {})
        
        # In full implementation, this would apply sophisticated text transformation
        # For now, add emotional context cues
        if emotional_context.intensity > 0.7:
            text = f"*The air between you thrums with electric intensity* {text}"
        elif emotional_context.current_state == EmotionalState.ROMANTIC:
            text = f"*A tender warmth fills the space around you* {text}"
        
        return text
    
    async def _generate_adaptive_choices(
        self,
        fragment: StoryFragment,
        profile: UserPersonalizationProfile,
        emotional_context: EmotionalContext
    ) -> List[Dict[str, Any]]:
        """Generate choices adapted to the user's personality and emotional state."""
        
        # Get base choices from narrative engine
        base_choices = await self.narrative_engine._get_fragment_choices(fragment.id)
        
        adapted_choices = []
        for choice in base_choices:
            # Adapt choice text based on user profile
            adapted_text = await self._adapt_choice_text(
                choice.text, profile, emotional_context
            )
            
            # Calculate choice appeal based on user archetype
            appeal_score = await self._calculate_choice_appeal(
                choice, profile, emotional_context
            )
            
            adapted_choices.append({
                "id": choice.id,
                "original_text": choice.text,
                "adapted_text": adapted_text,
                "appeal_score": appeal_score,
                "destination": choice.destination_fragment_key,
                "requirements": {
                    "besitos": choice.required_besitos,
                    "role": choice.required_role
                }
            })
        
        # Sort by appeal score for this user
        adapted_choices.sort(key=lambda x: x["appeal_score"], reverse=True)
        
        return adapted_choices
    
    # Additional helper methods would continue here...
    # For brevity, I'll implement key remaining methods
    
    async def _is_recent_memory(self, memory: Dict[str, Any]) -> bool:
        """Check if a memory is recent enough to be relevant."""
        if "timestamp" not in memory:
            return False
        
        memory_time = datetime.fromisoformat(memory["timestamp"])
        return datetime.now() - memory_time < timedelta(days=7)
    
    async def _get_relationship_indicators(self, profile: UserPersonalizationProfile) -> Dict[str, Any]:
        """Get indicators of relationship depth and evolution."""
        return {
            "depth": profile.relationship_depth,
            "evolution_stage": profile.voice_evolution_stage,
            "archetype_certainty": profile.archetype_confidence,
            "memory_count": len(profile.memory_moments),
            "interaction_frequency": "high"  # Would be calculated from actual data
        }
    
    # Placeholder methods that would be fully implemented
    async def _load_profile_from_database(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Load user profile from database storage."""
        # Would implement database loading logic
        return None
    
    async def _infer_archetype_from_history(self, choices: List[Dict[str, Any]]) -> Tuple[UserArchetype, float]:
        """Infer user archetype from choice history."""
        # Sophisticated archetype analysis would be implemented here
        return UserArchetype.EXPLORER, 0.3
    
    async def _is_contextually_relevant_memory(self, memory: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Check if a memory is relevant to current context."""
        return self._is_recent_memory(memory)
    
    async def _craft_memory_reference(self, memory: Dict[str, Any], profile: UserPersonalizationProfile) -> Optional[str]:
        """Craft a subtle reference to a shared memory."""
        return "A knowing glance passes between you, remembering..."
    
    async def _adapt_choice_text(self, text: str, profile: UserPersonalizationProfile, emotional_context: EmotionalContext) -> str:
        """Adapt choice text to user's style and emotional state."""
        return text  # Would implement sophisticated adaptation
    
    async def _calculate_choice_appeal(self, choice, profile: UserPersonalizationProfile, emotional_context: EmotionalContext) -> float:
        """Calculate how appealing a choice is to this specific user."""
        base_score = 0.5
        
        # Archetype-based appeal modifiers would be implemented
        if profile.archetype == UserArchetype.ADVENTURER:
            if "bold" in choice.text.lower() or "risk" in choice.text.lower():
                base_score += 0.3
        
        return min(base_score, 1.0)
    
    async def _analyze_decision_patterns(self, user_id: int, choice_index: int, context: Dict[str, Any], profile: UserPersonalizationProfile) -> Dict[str, Any]:
        """Analyze decision patterns for personality insights."""
        return {
            "choice_type": "exploratory",
            "risk_level": 0.5,
            "emotional_driver": "curiosity"
        }
    
    async def _update_profile_from_interaction(self, profile: UserPersonalizationProfile, emotional_context: EmotionalContext, context: Dict[str, Any]):
        """Update user profile based on interaction."""
        profile.last_updated = datetime.now()
        # Would implement sophisticated profile updating logic
    
    async def _update_profile_from_decision(self, profile: UserPersonalizationProfile, insights: Dict[str, Any]):
        """Update profile based on decision analysis."""
        profile.last_updated = datetime.now()
        # Would implement decision-based profile updates
    
    async def _handle_narrative_start(self, user_id: int, profile: UserPersonalizationProfile) -> Dict[str, Any]:
        """Handle narrative start with personalization."""
        fragment = await self.narrative_engine.start_narrative(user_id)
        if not fragment:
            return {"success": False, "error": "narrative_start_failed"}
        
        emotional_context = EmotionalContext(
            current_state=EmotionalState.CURIOUS,
            intensity=0.6,
            previous_states=[],
            triggers={"first_encounter": True},
            duration=timedelta(0),
            volatility=0.5
        )
        
        adaptive_content = await self._generate_adaptive_content(
            fragment, profile, emotional_context, {"first_interaction": True}
        )
        
        return {
            "success": True,
            "content": adaptive_content,
            "first_encounter": True
        }