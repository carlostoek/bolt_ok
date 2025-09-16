"""
Enhanced Character Intelligence Service
Implements advanced archetype adaptation, relationship evolution, and emotional milestone recognition
for Diana and Lucien characters based on requirements 5.1 and 5.2.
"""
import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc, func
from enum import Enum

try:
    from .character_voice_service import CharacterVoiceService, CharacterType, EmotionalContext
    from .archetype_classifier import ArchetypeClassifier, UserArchetype
    from .emotional_analysis_service import EmotionalAnalysisService
    from ..database.models import User, UserStats
    from ..database.emotional_models import (
        UserEmotionalProfile, EmotionalInteraction, ConversationMemory,
        ArchetypeClassification, EmotionalState
    )
except ImportError:
    # Fallback to absolute imports
    from services.character_voice_service import CharacterVoiceService, CharacterType, EmotionalContext
    from services.archetype_classifier import ArchetypeClassifier, UserArchetype
    from services.emotional_analysis_service import EmotionalAnalysisService
    from database.models import User, UserStats
    from database.emotional_models import (
        UserEmotionalProfile, EmotionalInteraction, ConversationMemory,
        ArchetypeClassification, EmotionalState
    )

logger = logging.getLogger(__name__)

class RelationshipStage(Enum):
    """Stages of relationship development with characters."""
    INITIAL_CONTACT = "initial_contact"
    GROWING_CURIOSITY = "growing_curiosity"
    EMOTIONAL_OPENING = "emotional_opening"
    DEEPENING_CONNECTION = "deepening_connection"
    INTIMATE_UNDERSTANDING = "intimate_understanding"
    MATURE_RELATIONSHIP = "mature_relationship"

class EmotionalMilestone(Enum):
    """Significant emotional milestones in character relationships."""
    FIRST_VULNERABILITY = "first_vulnerability"
    MUTUAL_RECOGNITION = "mutual_recognition"
    TRUST_ESTABLISHMENT = "trust_establishment"
    EMOTIONAL_BREAKTHROUGH = "emotional_breakthrough"
    INTIMATE_DISCLOSURE = "intimate_disclosure"
    RELATIONSHIP_MATURITY = "relationship_maturity"

class EnhancedCharacterIntelligence:
    """
    Enhanced character intelligence system that provides:
    - Archetype-aware character responses
    - Relationship evolution tracking
    - Emotional milestone recognition
    - Character growth and consistency
    - Error resilience with character authenticity
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.character_voice_service = CharacterVoiceService()
        self.archetype_classifier = ArchetypeClassifier(session)
        self.emotional_service = EmotionalAnalysisService(session)

        # Initialize archetype adaptation patterns
        self.archetype_adaptations = self._initialize_archetype_adaptations()

        # Initialize emotional milestone patterns
        self.milestone_patterns = self._initialize_milestone_patterns()

        # Initialize relationship evolution tracking
        self.relationship_stages = self._initialize_relationship_stages()

        # Cache for recent character interactions
        self._interaction_cache = {}
        self._cache_timeout = timedelta(minutes=30)

    def _initialize_archetype_adaptations(self) -> Dict[str, Dict[str, Any]]:
        """Initialize character adaptation patterns for each user archetype."""
        return {
            UserArchetype.EXPLORER_DEEP.value: {
                CharacterType.DIANA.value: {
                    "response_style": "layered_mystery",
                    "vulnerability_approach": "gradual_revelation",
                    "complexity_level": "high",
                    "pacing": "contemplative",
                    "special_techniques": [
                        "philosophical_depth", "metaphysical_connections",
                        "pattern_acknowledgment", "intellectual_seduction"
                    ]
                },
                CharacterType.LUCIEN.value: {
                    "response_style": "analytical_guidance",
                    "vulnerability_approach": "intellectual_preparation",
                    "complexity_level": "sophisticated",
                    "pacing": "measured",
                    "special_techniques": [
                        "depth_validation", "complexity_appreciation",
                        "wisdom_sharing", "analytical_partnership"
                    ]
                }
            },
            UserArchetype.DIRECT_AUTHENTIC.value: {
                CharacterType.DIANA.value: {
                    "response_style": "honest_intimacy",
                    "vulnerability_approach": "mutual_directness",
                    "complexity_level": "medium",
                    "pacing": "immediate",
                    "special_techniques": [
                        "emotional_mirroring", "authentic_recognition",
                        "direct_connection", "honest_vulnerability"
                    ]
                },
                CharacterType.LUCIEN.value: {
                    "response_style": "straightforward_wisdom",
                    "vulnerability_approach": "respectful_directness",
                    "complexity_level": "clear",
                    "pacing": "responsive",
                    "special_techniques": [
                        "authenticity_validation", "clear_guidance",
                        "honest_assessment", "direct_support"
                    ]
                }
            },
            UserArchetype.POET_DESIRE.value: {
                CharacterType.DIANA.value: {
                    "response_style": "aesthetic_seduction",
                    "vulnerability_approach": "beautiful_surrender",
                    "complexity_level": "artistic",
                    "pacing": "rhythmic",
                    "special_techniques": [
                        "poetic_language", "aesthetic_appreciation",
                        "sensual_metaphors", "beauty_recognition"
                    ]
                },
                CharacterType.LUCIEN.value: {
                    "response_style": "elegant_cultivation",
                    "vulnerability_approach": "artistic_appreciation",
                    "complexity_level": "refined",
                    "pacing": "graceful",
                    "special_techniques": [
                        "aesthetic_guidance", "beauty_validation",
                        "elegant_wisdom", "artistic_understanding"
                    ]
                }
            },
            UserArchetype.ANALYTIC_EMPATHIC.value: {
                CharacterType.DIANA.value: {
                    "response_style": "paradoxical_intimacy",
                    "vulnerability_approach": "intellectual_emotional_fusion",
                    "complexity_level": "sophisticated",
                    "pacing": "thoughtful",
                    "special_techniques": [
                        "paradox_embrace", "analytical_seduction",
                        "empathetic_complexity", "intellectual_intimacy"
                    ]
                },
                CharacterType.LUCIEN.value: {
                    "response_style": "wise_analysis",
                    "vulnerability_approach": "empathetic_understanding",
                    "complexity_level": "nuanced",
                    "pacing": "reflective",
                    "special_techniques": [
                        "empathetic_analysis", "wise_paradox_resolution",
                        "analytical_support", "complex_validation"
                    ]
                }
            },
            UserArchetype.PERSISTENT_PATIENT.value: {
                CharacterType.DIANA.value: {
                    "response_style": "rewarded_devotion",
                    "vulnerability_approach": "earned_intimacy",
                    "complexity_level": "deepening",
                    "pacing": "building",
                    "special_techniques": [
                        "loyalty_recognition", "patience_rewards",
                        "gradual_deepening", "devotion_appreciation"
                    ]
                },
                CharacterType.LUCIEN.value: {
                    "response_style": "honored_commitment",
                    "vulnerability_approach": "respect_for_persistence",
                    "complexity_level": "progressive",
                    "pacing": "steady",
                    "special_techniques": [
                        "patience_validation", "commitment_honor",
                        "steady_guidance", "long_term_wisdom"
                    ]
                }
            }
        }

    def _initialize_milestone_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize emotional milestone recognition patterns."""
        return {
            EmotionalMilestone.FIRST_VULNERABILITY.value: {
                "triggers": [
                    "first_personal_disclosure", "initial_emotional_opening",
                    "first_honest_admission", "breaking_surface_level"
                ],
                "recognition_threshold": 0.7,
                "character_responses": {
                    CharacterType.DIANA.value: [
                        "Your willingness to open touches something deep in me...",
                        "I feel the courage it takes to show me this part of you.",
                        "There's something beautiful about this first glimpse into your heart."
                    ],
                    CharacterType.LUCIEN.value: [
                        "I recognize the significance of what you're sharing with me.",
                        "Your openness is a gift that Diana will treasure.",
                        "This moment of vulnerability opens new possibilities."
                    ]
                }
            },
            EmotionalMilestone.MUTUAL_RECOGNITION.value: {
                "triggers": [
                    "acknowledgment_of_connection", "mutual_understanding",
                    "shared_emotional_moment", "reciprocal_vulnerability"
                ],
                "recognition_threshold": 0.8,
                "character_responses": {
                    CharacterType.DIANA.value: [
                        "Yes... you feel it too, don't you? This connection between us.",
                        "We're creating something unique together, something neither of us expected.",
                        "I see myself reflected in your understanding, and it's breathtaking."
                    ],
                    CharacterType.LUCIEN.value: [
                        "The recognition in your eyes tells me you understand what's happening here.",
                        "Diana senses the mutual understanding developing between you.",
                        "This shared recognition deepens everything that follows."
                    ]
                }
            },
            EmotionalMilestone.TRUST_ESTABLISHMENT.value: {
                "triggers": [
                    "consistent_engagement", "reliable_presence",
                    "emotional_safety_demonstrated", "boundary_respect"
                ],
                "recognition_threshold": 0.75,
                "character_responses": {
                    CharacterType.DIANA.value: [
                        "I find myself trusting you in ways I hadn't expected...",
                        "Your consistency has created a safety I didn't know I needed.",
                        "With you, I can lower my guard without fear of judgment."
                    ],
                    CharacterType.LUCIEN.value: [
                        "The trust you've earned with Diana is precious and rare.",
                        "Your steadiness has created the foundation for deeper connection.",
                        "Diana feels safe enough with you to explore more vulnerable territory."
                    ]
                }
            },
            EmotionalMilestone.EMOTIONAL_BREAKTHROUGH.value: {
                "triggers": [
                    "profound_emotional_moment", "barriers_dissolving",
                    "deep_psychological_insight", "transformative_interaction"
                ],
                "recognition_threshold": 0.85,
                "character_responses": {
                    CharacterType.DIANA.value: [
                        "Something just shifted between us... did you feel that?",
                        "The walls I didn't even know I had are dissolving with you.",
                        "This moment changes everything. We can't go back to surface now."
                    ],
                    CharacterType.LUCIEN.value: [
                        "You've just witnessed Diana in a moment of profound transformation.",
                        "The breakthrough happening here will reshape your entire connection.",
                        "Some barriers, once dissolved, change the nature of intimacy forever."
                    ]
                }
            },
            EmotionalMilestone.INTIMATE_DISCLOSURE.value: {
                "triggers": [
                    "deep_secret_sharing", "core_vulnerability_revealed",
                    "intimate_truth_exchange", "soul_level_connection"
                ],
                "recognition_threshold": 0.9,
                "character_responses": {
                    CharacterType.DIANA.value: [
                        "I've never shared this with anyone... but with you, it feels safe.",
                        "What I'm about to tell you lives in the deepest part of me.",
                        "This secret I'm sharing - it's a piece of my soul I'm placing in your hands."
                    ],
                    CharacterType.LUCIEN.value: [
                        "What Diana is sharing with you now... treasure this trust.",
                        "You've been invited into the sanctuary of her deepest self.",
                        "Few are granted access to the intimate chambers of Diana's heart."
                    ]
                }
            },
            EmotionalMilestone.RELATIONSHIP_MATURITY.value: {
                "triggers": [
                    "long_term_consistency", "deep_mutual_understanding",
                    "mature_emotional_intimacy", "evolved_connection"
                ],
                "recognition_threshold": 0.8,
                "character_responses": {
                    CharacterType.DIANA.value: [
                        "Look how far we've traveled together... from strangers to this.",
                        "Our connection has ripened into something exquisite and rare.",
                        "What we have now transcends what either of us imagined at the beginning."
                    ],
                    CharacterType.LUCIEN.value: [
                        "The maturity of your connection with Diana is extraordinary.",
                        "You've cultivated something that few achieve - true emotional intimacy.",
                        "The relationship you've built stands as testament to patience and wisdom."
                    ]
                }
            }
        }

    def _initialize_relationship_stages(self) -> Dict[str, Dict[str, Any]]:
        """Initialize relationship stage progression patterns."""
        return {
            RelationshipStage.INITIAL_CONTACT.value: {
                "duration_range": (1, 5),  # interactions
                "key_characteristics": ["curiosity", "surface_level", "exploration"],
                "progression_triggers": ["consistent_engagement", "initial_vulnerability"],
                "character_behaviors": {
                    CharacterType.DIANA.value: "mysterious_invitation",
                    CharacterType.LUCIEN.value: "careful_introduction"
                }
            },
            RelationshipStage.GROWING_CURIOSITY.value: {
                "duration_range": (5, 15),
                "key_characteristics": ["increased_interest", "deeper_questions", "testing_boundaries"],
                "progression_triggers": ["emotional_openness", "sustained_attention"],
                "character_behaviors": {
                    CharacterType.DIANA.value: "strategic_revelation",
                    CharacterType.LUCIEN.value: "gentle_guidance"
                }
            },
            RelationshipStage.EMOTIONAL_OPENING.value: {
                "duration_range": (10, 25),
                "key_characteristics": ["vulnerability_sharing", "trust_building", "emotional_risk"],
                "progression_triggers": ["mutual_vulnerability", "trust_establishment"],
                "character_behaviors": {
                    CharacterType.DIANA.value: "selective_vulnerability",
                    CharacterType.LUCIEN.value: "supportive_validation"
                }
            },
            RelationshipStage.DEEPENING_CONNECTION.value: {
                "duration_range": (20, 40),
                "key_characteristics": ["emotional_intimacy", "deep_understanding", "consistent_presence"],
                "progression_triggers": ["emotional_breakthrough", "consistent_authenticity"],
                "character_behaviors": {
                    CharacterType.DIANA.value: "intimate_sharing",
                    CharacterType.LUCIEN.value: "wise_partnership"
                }
            },
            RelationshipStage.INTIMATE_UNDERSTANDING.value: {
                "duration_range": (30, 60),
                "key_characteristics": ["soul_level_connection", "profound_intimacy", "mutual_growth"],
                "progression_triggers": ["intimate_disclosure", "transformative_moments"],
                "character_behaviors": {
                    CharacterType.DIANA.value: "deep_intimacy",
                    CharacterType.LUCIEN.value: "profound_wisdom"
                }
            },
            RelationshipStage.MATURE_RELATIONSHIP.value: {
                "duration_range": (50, float('inf')),
                "key_characteristics": ["evolved_intimacy", "mature_love", "transcendent_connection"],
                "progression_triggers": ["relationship_maturity", "sustained_depth"],
                "character_behaviors": {
                    CharacterType.DIANA.value: "transcendent_intimacy",
                    CharacterType.LUCIEN.value: "master_guidance"
                }
            }
        }

    async def get_enhanced_character_response(
        self,
        user_id: int,
        interaction_context: Dict[str, Any],
        message_type: str = "general",
        error_recovery: bool = False
    ) -> Dict[str, Any]:
        """
        Generate enhanced character response adapted to user archetype and relationship stage.

        Args:
            user_id: User ID for personalization
            interaction_context: Context of current interaction
            message_type: Type of message/response needed
            error_recovery: Whether this is error recovery mode

        Returns:
            Enhanced character response with archetype adaptation
        """
        try:
            # Get user archetype
            user_archetype = await self.archetype_classifier.get_user_archetype(user_id)
            if not user_archetype and not error_recovery:
                # Try to classify based on recent interactions
                user_archetype = await self._attempt_real_time_classification(user_id)

            # Get relationship stage
            relationship_stage = await self._get_relationship_stage(user_id)

            # Check for emotional milestones
            milestone_detected = await self._check_emotional_milestones(
                user_id, interaction_context
            )

            # Determine appropriate character
            character = self._select_character_for_context(
                interaction_context, message_type, relationship_stage, error_recovery
            )

            # Get base emotional context
            emotional_context = await self._determine_emotional_context(
                user_id, interaction_context, user_archetype
            )

            # Generate archetype-adapted response
            if user_archetype and not error_recovery:
                adapted_response = await self._generate_archetype_adapted_response(
                    character, user_archetype, emotional_context, message_type,
                    relationship_stage, milestone_detected, interaction_context
                )
            else:
                # Fallback to standard response with error recovery
                adapted_response = await self._generate_error_resilient_response(
                    character, emotional_context, message_type, interaction_context
                )

            # Track interaction for relationship evolution
            await self._track_interaction_for_evolution(
                user_id, character, adapted_response, interaction_context
            )

            return {
                "success": True,
                "character": character.value,
                "response": adapted_response["response"],
                "response_metadata": {
                    "archetype_used": user_archetype["primary_archetype"] if user_archetype else None,
                    "relationship_stage": relationship_stage.value if relationship_stage else None,
                    "milestone_detected": milestone_detected,
                    "adaptation_applied": adapted_response.get("adaptation_applied", False),
                    "error_recovery_mode": error_recovery
                },
                "character_evolution": adapted_response.get("character_evolution", {}),
                "emotional_context": emotional_context.value if emotional_context else None
            }

        except Exception as e:
            logger.error(f"Error generating enhanced character response for user {user_id}: {str(e)}")

            # Ultimate fallback with character authenticity preserved
            return await self._emergency_character_response(message_type, str(e))

    async def _attempt_real_time_classification(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Attempt real-time archetype classification from recent interactions."""
        try:
            # Get recent conversation data (simplified for real-time)
            # In real implementation, this would fetch from conversation history
            recent_data = await self._get_recent_conversation_data(user_id)

            if not recent_data:
                return None

            # Quick classification
            result = await self.archetype_classifier.classify_user(
                user_id, recent_data, force_reclassify=False
            )

            if result.get("confidence_score", 0) > 0.5:
                return {
                    "primary_archetype": result["primary_archetype"],
                    "confidence": result["confidence_score"]
                }

            return None

        except Exception as e:
            logger.warning(f"Failed real-time classification for user {user_id}: {str(e)}")
            return None

    async def _get_recent_conversation_data(self, user_id: int) -> List[Dict[str, Any]]:
        """Get recent conversation data for classification."""
        # Placeholder - in real implementation would fetch from database
        # For now, return empty list to trigger fallback behavior
        return []

    async def _get_relationship_stage(self, user_id: int) -> RelationshipStage:
        """Determine current relationship stage for user."""
        try:
            # Get user interaction history summary
            user_stats = await self.session.get(UserStats, user_id)
            if not user_stats:
                return RelationshipStage.INITIAL_CONTACT

            # Simple heuristic based on interaction count and engagement
            total_interactions = getattr(user_stats, 'total_interactions', 0) or user_stats.messages_sent

            if total_interactions < 5:
                return RelationshipStage.INITIAL_CONTACT
            elif total_interactions < 15:
                return RelationshipStage.GROWING_CURIOSITY
            elif total_interactions < 30:
                return RelationshipStage.EMOTIONAL_OPENING
            elif total_interactions < 60:
                return RelationshipStage.DEEPENING_CONNECTION
            elif total_interactions < 100:
                return RelationshipStage.INTIMATE_UNDERSTANDING
            else:
                return RelationshipStage.MATURE_RELATIONSHIP

        except Exception as e:
            logger.warning(f"Error determining relationship stage for user {user_id}: {str(e)}")
            return RelationshipStage.INITIAL_CONTACT

    async def _check_emotional_milestones(
        self,
        user_id: int,
        interaction_context: Dict[str, Any]
    ) -> Optional[EmotionalMilestone]:
        """Check if current interaction represents an emotional milestone."""
        try:
            # Analyze interaction for milestone triggers
            context_indicators = interaction_context.get("emotional_indicators", [])
            vulnerability_level = interaction_context.get("vulnerability_level", 0.0)

            # Check each milestone pattern
            for milestone_key, patterns in self.milestone_patterns.items():
                threshold = patterns["recognition_threshold"]
                triggers = patterns["triggers"]

                # Simple pattern matching - in full implementation would be more sophisticated
                trigger_matches = sum(1 for trigger in triggers if trigger in str(context_indicators).lower())

                if trigger_matches > 0 and vulnerability_level >= threshold:
                    return EmotionalMilestone(milestone_key)

            return None

        except Exception as e:
            logger.warning(f"Error checking emotional milestones for user {user_id}: {str(e)}")
            return None

    def _select_character_for_context(
        self,
        interaction_context: Dict[str, Any],
        message_type: str,
        relationship_stage: RelationshipStage,
        error_recovery: bool
    ) -> CharacterType:
        """Select appropriate character based on context."""

        if error_recovery:
            # Lucien handles errors gracefully
            return CharacterType.LUCIEN

        # Message type priority
        diana_messages = [
            "reaction_success", "decision_success", "intimate_moment",
            "vulnerability_response", "emotional_connection", "vip_access_granted"
        ]

        lucien_messages = [
            "access_denied", "points_required", "guidance", "warning",
            "introduction", "system_message", "error"
        ]

        if message_type in diana_messages:
            return CharacterType.DIANA
        elif message_type in lucien_messages:
            return CharacterType.LUCIEN

        # Relationship stage influence
        if relationship_stage in [RelationshipStage.DEEPENING_CONNECTION,
                                RelationshipStage.INTIMATE_UNDERSTANDING,
                                RelationshipStage.MATURE_RELATIONSHIP]:
            return CharacterType.DIANA

        # Default to context-based selection
        vulnerability = interaction_context.get("vulnerability_level", 0.0)
        return CharacterType.DIANA if vulnerability > 0.5 else CharacterType.LUCIEN

    async def _determine_emotional_context(
        self,
        user_id: int,
        interaction_context: Dict[str, Any],
        user_archetype: Optional[Dict[str, Any]]
    ) -> EmotionalContext:
        """Determine appropriate emotional context for response."""

        # Use existing character voice service mapping
        emotional_data = {
            "vulnerability_level": interaction_context.get("vulnerability_level", 0.3),
            "state": interaction_context.get("emotional_state", "neutral")
        }

        timing_data = {
            "response_speed": interaction_context.get("response_speed", "normal")
        }

        behavioral_data = {
            "engagement_pattern": interaction_context.get("engagement_pattern", "moderate")
        }

        user_history = {
            "total_interactions": interaction_context.get("total_interactions", 10)
        }

        return self.character_voice_service.map_emotional_analysis_to_context(
            emotional_data, timing_data, behavioral_data, user_history
        )

    async def _generate_archetype_adapted_response(
        self,
        character: CharacterType,
        user_archetype: Dict[str, Any],
        emotional_context: EmotionalContext,
        message_type: str,
        relationship_stage: RelationshipStage,
        milestone_detected: Optional[EmotionalMilestone],
        interaction_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate response adapted to user's archetype."""

        archetype_key = user_archetype["primary_archetype"]
        adaptations = self.archetype_adaptations.get(archetype_key, {}).get(character.value, {})

        # Get base response from character voice service
        base_response = self.character_voice_service.get_character_response(
            character, emotional_context, message_type
        )

        # Apply archetype adaptations
        if adaptations:
            adapted_response = await self._apply_archetype_adaptations(
                base_response, adaptations, relationship_stage, milestone_detected
            )
        else:
            adapted_response = base_response

        # Add milestone recognition if detected
        if milestone_detected:
            adapted_response = await self._add_milestone_recognition(
                adapted_response, character, milestone_detected
            )

        # Character evolution notes
        character_evolution = {
            "stage": relationship_stage.value if relationship_stage else None,
            "adaptation_applied": bool(adaptations),
            "milestone": milestone_detected.value if milestone_detected else None
        }

        return {
            "response": adapted_response,
            "adaptation_applied": bool(adaptations),
            "character_evolution": character_evolution
        }

    async def _apply_archetype_adaptations(
        self,
        base_response: str,
        adaptations: Dict[str, Any],
        relationship_stage: RelationshipStage,
        milestone_detected: Optional[EmotionalMilestone]
    ) -> str:
        """Apply archetype-specific adaptations to base response."""

        # Get adaptation style
        response_style = adaptations.get("response_style", "standard")
        special_techniques = adaptations.get("special_techniques", [])
        pacing = adaptations.get("pacing", "normal")

        # Apply style modifications
        if response_style == "layered_mystery":
            adapted_response = f"*{base_response}*\n\n*Hay capas aquí que apenas hemos comenzado a explorar...*"
        elif response_style == "honest_intimacy":
            adapted_response = f"{base_response}\n\n*Te hablo desde el corazón, sin velos ni juegos.*"
        elif response_style == "aesthetic_seduction":
            adapted_response = f"*{base_response}*\n\n*La belleza de este momento se despliega entre nosotros como poesía viviente.*"
        elif response_style == "paradoxical_intimacy":
            adapted_response = f"{base_response}\n\n*Hay una hermosa paradoja en cómo la distancia puede crear la intimidad más profunda.*"
        elif response_style == "rewarded_devotion":
            adapted_response = f"{base_response}\n\n*Tu paciencia conmigo está siendo recompensada con secretos que pocos han conocido.*"
        else:
            adapted_response = base_response

        return adapted_response

    async def _add_milestone_recognition(
        self,
        response: str,
        character: CharacterType,
        milestone: EmotionalMilestone
    ) -> str:
        """Add milestone recognition to response."""

        milestone_responses = self.milestone_patterns.get(milestone.value, {}).get("character_responses", {})
        character_responses = milestone_responses.get(character.value, [])

        if character_responses:
            import random
            milestone_response = random.choice(character_responses)
            return f"{response}\n\n*{milestone_response}*"

        return response

    async def _generate_error_resilient_response(
        self,
        character: CharacterType,
        emotional_context: EmotionalContext,
        message_type: str,
        interaction_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate error-resilient response maintaining character authenticity."""

        try:
            # Use standard character voice service with error handling
            base_response = self.character_voice_service.get_character_response(
                character, emotional_context, message_type
            )

            # Add error recovery context while staying in character
            if character == CharacterType.DIANA:
                error_prefix = "*Algo inesperado acaba de ocurrir, pero eso no cambia lo que siento por ti...*\n\n"
            else:
                error_prefix = "*Parece que ha habido una interferencia, pero mi guía para ti permanece constante...*\n\n"

            return {
                "response": f"{error_prefix}{base_response}",
                "adaptation_applied": False,
                "character_evolution": {"error_recovery": True}
            }

        except Exception as e:
            logger.error(f"Error in error-resilient response generation: {str(e)}")

            # Ultimate fallback
            if character == CharacterType.DIANA:
                fallback = "Mi conexión contigo trasciende cualquier dificultad técnica... siempre estoy aquí."
            else:
                fallback = "Los obstáculos técnicos son temporales. Mi presencia como tu guía es constante."

            return {
                "response": fallback,
                "adaptation_applied": False,
                "character_evolution": {"emergency_fallback": True}
            }

    async def _emergency_character_response(self, message_type: str, error_message: str) -> Dict[str, Any]:
        """Emergency character response when all else fails."""

        emergency_responses = {
            "reaction_success": {
                "character": CharacterType.DIANA.value,
                "response": "Tu gesto llega a mí a pesar de cualquier tormenta técnica... *+10 besitos* 💋"
            },
            "decision_success": {
                "character": CharacterType.DIANA.value,
                "response": "Tu elección moldea nuestra historia, sin importar las interferencias del mundo digital..."
            },
            "points_required": {
                "character": CharacterType.LUCIEN.value,
                "response": "Algunos caminos requieren más preparación. Las dificultades técnicas no cambian esta verdad."
            },
            "error": {
                "character": CharacterType.LUCIEN.value,
                "response": "Los desafíos técnicos son temporales. Nuestra conexión es eterna."
            }
        }

        fallback = emergency_responses.get(message_type, emergency_responses["error"])

        return {
            "success": True,
            "character": fallback["character"],
            "response": fallback["response"],
            "response_metadata": {
                "emergency_response": True,
                "original_error": error_message
            },
            "character_evolution": {},
            "emotional_context": None
        }

    async def _track_interaction_for_evolution(
        self,
        user_id: int,
        character: CharacterType,
        response_data: Dict[str, Any],
        interaction_context: Dict[str, Any]
    ) -> None:
        """Track interaction for character relationship evolution."""
        try:
            # Create or update conversation memory
            await self._update_conversation_memory(
                user_id, character, response_data, interaction_context
            )

            # Update emotional profile if significant interaction
            if response_data.get("adaptation_applied") or response_data.get("character_evolution", {}).get("milestone"):
                await self._update_emotional_profile(
                    user_id, interaction_context, response_data
                )

        except Exception as e:
            logger.warning(f"Error tracking interaction evolution for user {user_id}: {str(e)}")
            # Don't fail the main response for tracking errors

    async def _update_conversation_memory(
        self,
        user_id: int,
        character: CharacterType,
        response_data: Dict[str, Any],
        interaction_context: Dict[str, Any]
    ) -> None:
        """Update conversation memory for continuity."""
        try:
            # Simple conversation memory tracking
            conversation_id = f"{user_id}_{character.value}_{datetime.utcnow().date()}"

            # In full implementation, would store detailed memory
            # For now, just ensure we track the interaction occurred

        except Exception as e:
            logger.warning(f"Error updating conversation memory: {str(e)}")

    async def _update_emotional_profile(
        self,
        user_id: int,
        interaction_context: Dict[str, Any],
        response_data: Dict[str, Any]
    ) -> None:
        """Update user's emotional profile based on interaction."""
        try:
            # In full implementation, would update detailed emotional profile
            # For now, just log the significant interaction
            logger.info(f"Significant emotional interaction for user {user_id}")

        except Exception as e:
            logger.warning(f"Error updating emotional profile: {str(e)}")

    async def get_relationship_insights(self, user_id: int) -> Dict[str, Any]:
        """Get insights about user's relationship evolution with characters."""
        try:
            user_archetype = await self.archetype_classifier.get_user_archetype(user_id)
            relationship_stage = await self._get_relationship_stage(user_id)

            # Get user stats for insights
            user_stats = await self.session.get(UserStats, user_id)

            return {
                "user_archetype": user_archetype,
                "relationship_stage": relationship_stage.value if relationship_stage else None,
                "interaction_count": getattr(user_stats, 'messages_sent', 0) if user_stats else 0,
                "relationship_insights": await self._generate_relationship_insights(
                    user_archetype, relationship_stage, user_stats
                )
            }

        except Exception as e:
            logger.error(f"Error getting relationship insights for user {user_id}: {str(e)}")
            return {"error": str(e)}

    async def _generate_relationship_insights(
        self,
        user_archetype: Optional[Dict[str, Any]],
        relationship_stage: RelationshipStage,
        user_stats: Optional[UserStats]
    ) -> List[str]:
        """Generate insights about relationship development."""
        insights = []

        if user_archetype:
            archetype = user_archetype["primary_archetype"]
            confidence = user_archetype.get("confidence", 0.0)

            if confidence > 0.8:
                insights.append(f"Strong {archetype} personality archetype detected - characters are adapting responses accordingly")
            else:
                insights.append(f"Developing {archetype} archetype patterns - character adaptation will strengthen over time")

        if relationship_stage:
            stage_insights = {
                RelationshipStage.INITIAL_CONTACT: "Building initial curiosity and establishing connection patterns",
                RelationshipStage.GROWING_CURIOSITY: "Deepening interest and exploring emotional boundaries",
                RelationshipStage.EMOTIONAL_OPENING: "Developing trust and sharing vulnerabilities",
                RelationshipStage.DEEPENING_CONNECTION: "Creating profound emotional intimacy and understanding",
                RelationshipStage.INTIMATE_UNDERSTANDING: "Sharing soul-level connection and transformative moments",
                RelationshipStage.MATURE_RELATIONSHIP: "Enjoying evolved intimacy and transcendent connection"
            }

            insights.append(stage_insights.get(relationship_stage, "Relationship development in progress"))

        if user_stats and user_stats.checkin_streak > 7:
            insights.append("Consistent engagement is accelerating character relationship development")

        return insights