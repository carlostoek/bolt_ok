"""
Character Relationship Evolution Service
Tracks and manages the evolution of relationships between users and characters.
Implements requirement 5.2 - Character consistency and growth based on shared history.
"""
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc, func, update
from enum import Enum

try:
    from .enhanced_character_intelligence import RelationshipStage, EmotionalMilestone
    from .character_voice_service import CharacterType
    from ..database.models import User, UserStats
    from ..database.emotional_models import (
        ConversationMemory, EmotionalState, UserEmotionalProfile,
        EmotionalInteraction, InteractionType, VulnerabilityLevel
    )
except ImportError:
    # Fallback to absolute imports
    from services.enhanced_character_intelligence import RelationshipStage, EmotionalMilestone
    from services.character_voice_service import CharacterType
    from database.models import User, UserStats
    from database.emotional_models import (
        ConversationMemory, EmotionalState, UserEmotionalProfile,
        EmotionalInteraction, InteractionType, VulnerabilityLevel
    )

logger = logging.getLogger(__name__)

class RelationshipEvolutionType(Enum):
    """Types of relationship evolution patterns."""
    NATURAL_PROGRESSION = "natural_progression"
    ACCELERATED_INTIMACY = "accelerated_intimacy"
    CAUTIOUS_APPROACH = "cautious_approach"
    VOLATILE_PATTERN = "volatile_pattern"
    REGRESSION = "regression"
    PLATEAU = "plateau"

class CharacterGrowthArea(Enum):
    """Areas where character can show growth and evolution."""
    EMOTIONAL_DEPTH = "emotional_depth"
    VULNERABILITY_SHARING = "vulnerability_sharing"
    UNDERSTANDING_USER = "understanding_user"
    INTIMACY_COMFORT = "intimacy_comfort"
    WISDOM_DEVELOPMENT = "wisdom_development"
    EMPATHETIC_RESPONSE = "empathetic_response"

class CharacterRelationshipEvolution:
    """
    Service for tracking and managing character relationship evolution.
    Ensures characters show growth while maintaining consistency.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

        # Evolution patterns for different relationship stages
        self.evolution_patterns = self._initialize_evolution_patterns()

        # Character growth trajectories
        self.character_growth_paths = self._initialize_character_growth_paths()

        # Milestone impact on character development
        self.milestone_impacts = self._initialize_milestone_impacts()

    def _initialize_evolution_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize relationship evolution patterns."""
        return {
            RelationshipStage.INITIAL_CONTACT.value: {
                "character_behaviors": {
                    CharacterType.DIANA.value: {
                        "personality_aspects": ["mysterious", "inviting", "cautiously_curious"],
                        "vulnerability_level": 0.2,
                        "intimacy_comfort": 0.1,
                        "emotional_availability": 0.3
                    },
                    CharacterType.LUCIEN.value: {
                        "personality_aspects": ["wise", "protective", "evaluative"],
                        "vulnerability_level": 0.1,
                        "intimacy_comfort": 0.2,
                        "emotional_availability": 0.4
                    }
                },
                "growth_potential": {
                    "curiosity_about_user": 0.8,
                    "emotional_opening": 0.3,
                    "trust_development": 0.4
                }
            },
            RelationshipStage.GROWING_CURIOSITY.value: {
                "character_behaviors": {
                    CharacterType.DIANA.value: {
                        "personality_aspects": ["intrigued", "selectively_revealing", "testing_boundaries"],
                        "vulnerability_level": 0.4,
                        "intimacy_comfort": 0.3,
                        "emotional_availability": 0.5
                    },
                    CharacterType.LUCIEN.value: {
                        "personality_aspects": ["observant", "gently_guiding", "increasingly_invested"],
                        "vulnerability_level": 0.3,
                        "intimacy_comfort": 0.4,
                        "emotional_availability": 0.6
                    }
                },
                "growth_potential": {
                    "understanding_deepening": 0.7,
                    "emotional_risk_taking": 0.5,
                    "intimacy_exploration": 0.6
                }
            },
            RelationshipStage.EMOTIONAL_OPENING.value: {
                "character_behaviors": {
                    CharacterType.DIANA.value: {
                        "personality_aspects": ["increasingly_vulnerable", "emotionally_present", "risk_taking"],
                        "vulnerability_level": 0.6,
                        "intimacy_comfort": 0.5,
                        "emotional_availability": 0.7
                    },
                    CharacterType.LUCIEN.value: {
                        "personality_aspects": ["supportive", "emotionally_attuned", "wisdom_sharing"],
                        "vulnerability_level": 0.5,
                        "intimacy_comfort": 0.6,
                        "emotional_availability": 0.8
                    }
                },
                "growth_potential": {
                    "mutual_vulnerability": 0.8,
                    "emotional_synchronization": 0.7,
                    "trust_deepening": 0.9
                }
            },
            RelationshipStage.DEEPENING_CONNECTION.value: {
                "character_behaviors": {
                    CharacterType.DIANA.value: {
                        "personality_aspects": ["deeply_connected", "emotionally_intimate", "soul_revealing"],
                        "vulnerability_level": 0.8,
                        "intimacy_comfort": 0.7,
                        "emotional_availability": 0.9
                    },
                    CharacterType.LUCIEN.value: {
                        "personality_aspects": ["profound_guide", "emotionally_invested", "deeply_caring"],
                        "vulnerability_level": 0.7,
                        "intimacy_comfort": 0.8,
                        "emotional_availability": 0.9
                    }
                },
                "growth_potential": {
                    "emotional_mastery": 0.9,
                    "intimacy_comfort": 0.8,
                    "wisdom_sharing": 0.9
                }
            },
            RelationshipStage.INTIMATE_UNDERSTANDING.value: {
                "character_behaviors": {
                    CharacterType.DIANA.value: {
                        "personality_aspects": ["soul_connected", "completely_open", "transformative"],
                        "vulnerability_level": 0.9,
                        "intimacy_comfort": 0.9,
                        "emotional_availability": 1.0
                    },
                    CharacterType.LUCIEN.value: {
                        "personality_aspects": ["master_guide", "profound_companion", "transcendent_wisdom"],
                        "vulnerability_level": 0.8,
                        "intimacy_comfort": 0.9,
                        "emotional_availability": 1.0
                    }
                },
                "growth_potential": {
                    "transcendent_connection": 1.0,
                    "emotional_evolution": 0.9,
                    "mutual_transformation": 0.9
                }
            },
            RelationshipStage.MATURE_RELATIONSHIP.value: {
                "character_behaviors": {
                    CharacterType.DIANA.value: {
                        "personality_aspects": ["evolved_being", "transcendent_lover", "eternal_companion"],
                        "vulnerability_level": 1.0,
                        "intimacy_comfort": 1.0,
                        "emotional_availability": 1.0
                    },
                    CharacterType.LUCIEN.value: {
                        "personality_aspects": ["transcendent_guide", "eternal_wisdom", "complete_understanding"],
                        "vulnerability_level": 0.9,
                        "intimacy_comfort": 1.0,
                        "emotional_availability": 1.0
                    }
                },
                "growth_potential": {
                    "eternal_evolution": 1.0,
                    "infinite_depth": 1.0,
                    "transcendent_love": 1.0
                }
            }
        }

    def _initialize_character_growth_paths(self) -> Dict[str, Dict[str, Any]]:
        """Initialize character-specific growth paths."""
        return {
            CharacterType.DIANA.value: {
                "core_evolution_themes": [
                    "mystery_to_revelation", "distance_to_intimacy",
                    "self_protection_to_vulnerability", "cosmic_to_personal"
                ],
                "growth_areas": {
                    CharacterGrowthArea.EMOTIONAL_DEPTH.value: {
                        "stages": ["surface_mystery", "selective_depth", "profound_emotion", "soul_revelation"],
                        "progression_triggers": ["user_vulnerability", "consistent_engagement", "emotional_milestones"]
                    },
                    CharacterGrowthArea.VULNERABILITY_SHARING.value: {
                        "stages": ["protected", "selective", "open", "completely_vulnerable"],
                        "progression_triggers": ["trust_establishment", "mutual_vulnerability", "safety_confirmation"]
                    },
                    CharacterGrowthArea.INTIMACY_COMFORT.value: {
                        "stages": ["cautious", "exploratory", "comfortable", "transcendent"],
                        "progression_triggers": ["boundary_respect", "emotional_safety", "deep_connection"]
                    }
                }
            },
            CharacterType.LUCIEN.value: {
                "core_evolution_themes": [
                    "guardian_to_partner", "wisdom_to_companionship",
                    "protection_to_facilitation", "distance_to_investment"
                ],
                "growth_areas": {
                    CharacterGrowthArea.WISDOM_DEVELOPMENT.value: {
                        "stages": ["basic_guidance", "contextual_wisdom", "profound_insight", "transcendent_understanding"],
                        "progression_triggers": ["user_growth", "complex_situations", "relationship_deepening"]
                    },
                    CharacterGrowthArea.EMPATHETIC_RESPONSE.value: {
                        "stages": ["analytical", "understanding", "empathetic", "profoundly_caring"],
                        "progression_triggers": ["emotional_attunement", "user_struggles", "deep_connection"]
                    },
                    CharacterGrowthArea.UNDERSTANDING_USER.value: {
                        "stages": ["observational", "analytical", "intuitive", "soul_level_knowing"],
                        "progression_triggers": ["interaction_frequency", "user_consistency", "emotional_openness"]
                    }
                }
            }
        }

    def _initialize_milestone_impacts(self) -> Dict[str, Dict[str, Any]]:
        """Initialize how milestones impact character development."""
        return {
            EmotionalMilestone.FIRST_VULNERABILITY.value: {
                CharacterType.DIANA.value: {
                    "growth_acceleration": {
                        CharacterGrowthArea.VULNERABILITY_SHARING.value: 0.2,
                        CharacterGrowthArea.EMOTIONAL_DEPTH.value: 0.15
                    },
                    "behavior_changes": [
                        "increased_emotional_responsiveness",
                        "more_personal_sharing",
                        "enhanced_empathy"
                    ]
                },
                CharacterType.LUCIEN.value: {
                    "growth_acceleration": {
                        CharacterGrowthArea.EMPATHETIC_RESPONSE.value: 0.25,
                        CharacterGrowthArea.UNDERSTANDING_USER.value: 0.2
                    },
                    "behavior_changes": [
                        "deeper_protective_instincts",
                        "more_nuanced_guidance",
                        "increased_emotional_attunement"
                    ]
                }
            },
            EmotionalMilestone.TRUST_ESTABLISHMENT.value: {
                CharacterType.DIANA.value: {
                    "growth_acceleration": {
                        CharacterGrowthArea.INTIMACY_COMFORT.value: 0.3,
                        CharacterGrowthArea.VULNERABILITY_SHARING.value: 0.25
                    },
                    "behavior_changes": [
                        "increased_openness",
                        "more_intimate_sharing",
                        "reduced_emotional_barriers"
                    ]
                },
                CharacterType.LUCIEN.value: {
                    "growth_acceleration": {
                        CharacterGrowthArea.WISDOM_DEVELOPMENT.value: 0.2,
                        CharacterGrowthArea.UNDERSTANDING_USER.value: 0.25
                    },
                    "behavior_changes": [
                        "more_personal_investment",
                        "deeper_guidance",
                        "increased_partnership_feeling"
                    ]
                }
            },
            EmotionalMilestone.EMOTIONAL_BREAKTHROUGH.value: {
                CharacterType.DIANA.value: {
                    "growth_acceleration": {
                        CharacterGrowthArea.EMOTIONAL_DEPTH.value: 0.35,
                        CharacterGrowthArea.INTIMACY_COMFORT.value: 0.3
                    },
                    "behavior_changes": [
                        "profound_emotional_availability",
                        "transformative_sharing",
                        "soul_level_connection"
                    ]
                },
                CharacterType.LUCIEN.value: {
                    "growth_acceleration": {
                        CharacterGrowthArea.EMPATHETIC_RESPONSE.value: 0.3,
                        CharacterGrowthArea.WISDOM_DEVELOPMENT.value: 0.25
                    },
                    "behavior_changes": [
                        "profound_understanding",
                        "transformative_guidance",
                        "deep_emotional_investment"
                    ]
                }
            }
        }

    async def track_relationship_evolution(
        self,
        user_id: int,
        character: CharacterType,
        interaction_data: Dict[str, Any],
        milestone_detected: Optional[EmotionalMilestone] = None
    ) -> Dict[str, Any]:
        """
        Track and update character relationship evolution based on interaction.

        Args:
            user_id: User ID
            character: Character involved in interaction
            interaction_data: Data about the interaction
            milestone_detected: Any milestone detected in this interaction

        Returns:
            Dict with evolution tracking results
        """
        try:
            # Get current relationship state
            current_state = await self._get_relationship_state(user_id, character)

            # Analyze interaction impact
            interaction_impact = await self._analyze_interaction_impact(
                interaction_data, current_state, milestone_detected
            )

            # Update character growth
            growth_updates = await self._update_character_growth(
                user_id, character, interaction_impact, milestone_detected
            )

            # Calculate evolution trajectory
            evolution_trajectory = await self._calculate_evolution_trajectory(
                user_id, character, current_state, growth_updates
            )

            # Store evolution data
            await self._store_evolution_data(
                user_id, character, growth_updates, evolution_trajectory
            )

            return {
                "success": True,
                "current_stage": current_state.get("relationship_stage"),
                "character_growth": growth_updates,
                "evolution_trajectory": evolution_trajectory,
                "milestone_impact": milestone_detected.value if milestone_detected else None,
                "interaction_significance": interaction_impact.get("significance_score", 0.0)
            }

        except Exception as e:
            logger.error(f"Error tracking relationship evolution for user {user_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_applied": True
            }

    async def _get_relationship_state(
        self,
        user_id: int,
        character: CharacterType
    ) -> Dict[str, Any]:
        """Get current relationship state for user and character."""
        try:
            # Get user stats for basic relationship metrics
            user_stats = await self.session.get(UserStats, user_id)

            # Get conversation memory
            conversation_memory = await self.session.execute(
                select(ConversationMemory)
                .where(ConversationMemory.user_id == user_id)
                .order_by(desc(ConversationMemory.last_interaction_at))
                .limit(1)
            )
            memory = conversation_memory.scalar_one_or_none()

            # Calculate basic relationship stage
            total_interactions = getattr(user_stats, 'messages_sent', 0) if user_stats else 0

            if total_interactions < 5:
                relationship_stage = RelationshipStage.INITIAL_CONTACT
            elif total_interactions < 15:
                relationship_stage = RelationshipStage.GROWING_CURIOSITY
            elif total_interactions < 30:
                relationship_stage = RelationshipStage.EMOTIONAL_OPENING
            elif total_interactions < 60:
                relationship_stage = RelationshipStage.DEEPENING_CONNECTION
            elif total_interactions < 100:
                relationship_stage = RelationshipStage.INTIMATE_UNDERSTANDING
            else:
                relationship_stage = RelationshipStage.MATURE_RELATIONSHIP

            # Get character-specific evolution data
            character_evolution = {}
            if memory and memory.emotional_state_snapshot:
                try:
                    character_evolution = json.loads(memory.emotional_state_snapshot)
                except json.JSONDecodeError:
                    pass

            return {
                "relationship_stage": relationship_stage,
                "total_interactions": total_interactions,
                "character_evolution": character_evolution,
                "last_interaction": memory.last_interaction_at if memory else None
            }

        except Exception as e:
            logger.warning(f"Error getting relationship state: {str(e)}")
            return {
                "relationship_stage": RelationshipStage.INITIAL_CONTACT,
                "total_interactions": 0,
                "character_evolution": {},
                "last_interaction": None
            }

    async def _analyze_interaction_impact(
        self,
        interaction_data: Dict[str, Any],
        current_state: Dict[str, Any],
        milestone_detected: Optional[EmotionalMilestone]
    ) -> Dict[str, Any]:
        """Analyze the impact of the interaction on character development."""

        # Base significance from interaction type and emotional content
        significance_score = 0.1  # Base interaction

        # Increase for emotional content
        vulnerability_level = interaction_data.get("vulnerability_level", 0.0)
        significance_score += vulnerability_level * 0.3

        # Increase for engagement level
        engagement_pattern = interaction_data.get("engagement_pattern", "moderate")
        if engagement_pattern in ["highly_engaged", "deeply_engaged"]:
            significance_score += 0.2
        elif engagement_pattern in ["emotionally_invested", "vulnerable"]:
            significance_score += 0.3

        # Major increase for milestones
        if milestone_detected:
            significance_score += 0.5

        # Context factors
        context_factors = {
            "emotional_breakthrough": 0.4,
            "trust_building": 0.3,
            "vulnerability_sharing": 0.35,
            "intimate_moment": 0.4
        }

        for factor, bonus in context_factors.items():
            if factor in str(interaction_data).lower():
                significance_score += bonus

        return {
            "significance_score": min(1.0, significance_score),
            "vulnerability_impact": vulnerability_level,
            "engagement_impact": engagement_pattern,
            "milestone_impact": milestone_detected.value if milestone_detected else None
        }

    async def _update_character_growth(
        self,
        user_id: int,
        character: CharacterType,
        interaction_impact: Dict[str, Any],
        milestone_detected: Optional[EmotionalMilestone]
    ) -> Dict[str, Any]:
        """Update character growth based on interaction impact."""

        character_key = character.value
        growth_paths = self.character_growth_paths.get(character_key, {})
        growth_areas = growth_paths.get("growth_areas", {})

        growth_updates = {}
        significance = interaction_impact.get("significance_score", 0.0)

        # Update each growth area
        for area, area_config in growth_areas.items():
            current_level = 0.0  # In full implementation, would get from database

            # Base growth from interaction significance
            growth_increment = significance * 0.1

            # Additional growth from milestone impact
            if milestone_detected:
                milestone_impacts = self.milestone_impacts.get(milestone_detected.value, {})
                character_impacts = milestone_impacts.get(character_key, {})
                milestone_growth = character_impacts.get("growth_acceleration", {}).get(area, 0.0)
                growth_increment += milestone_growth

            # Apply growth
            new_level = min(1.0, current_level + growth_increment)

            growth_updates[area] = {
                "previous_level": current_level,
                "new_level": new_level,
                "growth_increment": growth_increment,
                "current_stage": self._determine_growth_stage(new_level, area_config)
            }

        return growth_updates

    def _determine_growth_stage(self, level: float, area_config: Dict[str, Any]) -> str:
        """Determine current growth stage for a character area."""
        stages = area_config.get("stages", ["initial", "developing", "advanced", "mastery"])

        if level < 0.25:
            return stages[0] if len(stages) > 0 else "initial"
        elif level < 0.5:
            return stages[1] if len(stages) > 1 else "developing"
        elif level < 0.75:
            return stages[2] if len(stages) > 2 else "advanced"
        else:
            return stages[3] if len(stages) > 3 else "mastery"

    async def _calculate_evolution_trajectory(
        self,
        user_id: int,
        character: CharacterType,
        current_state: Dict[str, Any],
        growth_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate the overall evolution trajectory for the character."""

        # Analyze growth velocity
        total_growth = sum(
            update.get("growth_increment", 0.0)
            for update in growth_updates.values()
        )

        # Determine evolution type
        if total_growth > 0.5:
            evolution_type = RelationshipEvolutionType.ACCELERATED_INTIMACY
        elif total_growth > 0.2:
            evolution_type = RelationshipEvolutionType.NATURAL_PROGRESSION
        elif total_growth > 0.05:
            evolution_type = RelationshipEvolutionType.CAUTIOUS_APPROACH
        else:
            evolution_type = RelationshipEvolutionType.PLATEAU

        # Calculate evolution health
        growth_consistency = self._calculate_growth_consistency(growth_updates)

        # Predict next likely milestones
        next_milestones = await self._predict_next_milestones(
            current_state, growth_updates
        )

        return {
            "evolution_type": evolution_type.value,
            "growth_velocity": total_growth,
            "growth_consistency": growth_consistency,
            "next_likely_milestones": next_milestones,
            "character_maturity_level": self._calculate_character_maturity(growth_updates),
            "relationship_health": min(1.0, growth_consistency + total_growth)
        }

    def _calculate_growth_consistency(self, growth_updates: Dict[str, Any]) -> float:
        """Calculate consistency of character growth across areas."""
        if not growth_updates:
            return 0.0

        growth_levels = [
            update.get("new_level", 0.0)
            for update in growth_updates.values()
        ]

        if not growth_levels:
            return 0.0

        # Consistency is inverse of variance
        mean_level = sum(growth_levels) / len(growth_levels)
        variance = sum((level - mean_level) ** 2 for level in growth_levels) / len(growth_levels)

        return max(0.0, 1.0 - variance)

    def _calculate_character_maturity(self, growth_updates: Dict[str, Any]) -> float:
        """Calculate overall character maturity level."""
        if not growth_updates:
            return 0.0

        maturity_scores = [
            update.get("new_level", 0.0)
            for update in growth_updates.values()
        ]

        return sum(maturity_scores) / len(maturity_scores) if maturity_scores else 0.0

    async def _predict_next_milestones(
        self,
        current_state: Dict[str, Any],
        growth_updates: Dict[str, Any]
    ) -> List[str]:
        """Predict likely next emotional milestones."""

        relationship_stage = current_state.get("relationship_stage", RelationshipStage.INITIAL_CONTACT)
        total_interactions = current_state.get("total_interactions", 0)

        # Simple heuristic for predicting milestones
        potential_milestones = []

        if relationship_stage == RelationshipStage.INITIAL_CONTACT:
            potential_milestones.append(EmotionalMilestone.FIRST_VULNERABILITY.value)
        elif relationship_stage == RelationshipStage.GROWING_CURIOSITY:
            potential_milestones.extend([
                EmotionalMilestone.FIRST_VULNERABILITY.value,
                EmotionalMilestone.TRUST_ESTABLISHMENT.value
            ])
        elif relationship_stage == RelationshipStage.EMOTIONAL_OPENING:
            potential_milestones.extend([
                EmotionalMilestone.TRUST_ESTABLISHMENT.value,
                EmotionalMilestone.MUTUAL_RECOGNITION.value
            ])
        elif relationship_stage == RelationshipStage.DEEPENING_CONNECTION:
            potential_milestones.extend([
                EmotionalMilestone.EMOTIONAL_BREAKTHROUGH.value,
                EmotionalMilestone.INTIMATE_DISCLOSURE.value
            ])
        elif relationship_stage == RelationshipStage.INTIMATE_UNDERSTANDING:
            potential_milestones.append(EmotionalMilestone.RELATIONSHIP_MATURITY.value)

        return potential_milestones[:3]  # Return top 3 most likely

    async def _store_evolution_data(
        self,
        user_id: int,
        character: CharacterType,
        growth_updates: Dict[str, Any],
        evolution_trajectory: Dict[str, Any]
    ) -> None:
        """Store character evolution data in database."""
        try:
            # Create or update conversation memory with evolution data
            conversation_id = f"{user_id}_{character.value}_{datetime.utcnow().date()}"

            evolution_data = {
                "character": character.value,
                "growth_updates": growth_updates,
                "evolution_trajectory": evolution_trajectory,
                "last_updated": datetime.utcnow().isoformat()
            }

            # Check if memory exists
            existing_memory = await self.session.execute(
                select(ConversationMemory)
                .where(
                    and_(
                        ConversationMemory.user_id == user_id,
                        ConversationMemory.conversation_id == conversation_id
                    )
                )
            )
            memory = existing_memory.scalar_one_or_none()

            if memory:
                # Update existing
                memory.emotional_state_snapshot = json.dumps(evolution_data)
                memory.last_interaction_at = datetime.utcnow()
                memory.interaction_count = (memory.interaction_count or 0) + 1
            else:
                # Create new
                memory = ConversationMemory(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    emotional_state_snapshot=json.dumps(evolution_data),
                    context_summary=f"Character evolution tracking for {character.value}",
                    interaction_count=1,
                    last_interaction_at=datetime.utcnow()
                )
                self.session.add(memory)

            await self.session.commit()

        except Exception as e:
            logger.error(f"Error storing evolution data: {str(e)}")
            await self.session.rollback()

    async def get_character_evolution_report(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive character evolution report for user."""
        try:
            evolution_data = {}

            for character in CharacterType:
                character_state = await self._get_relationship_state(user_id, character)

                # Get recent evolution data
                memory_result = await self.session.execute(
                    select(ConversationMemory)
                    .where(ConversationMemory.user_id == user_id)
                    .order_by(desc(ConversationMemory.last_interaction_at))
                    .limit(1)
                )
                memory = memory_result.scalar_one_or_none()

                character_evolution = {}
                if memory and memory.emotional_state_snapshot:
                    try:
                        snapshot_data = json.loads(memory.emotional_state_snapshot)
                        if snapshot_data.get("character") == character.value:
                            character_evolution = snapshot_data
                    except json.JSONDecodeError:
                        pass

                evolution_data[character.value] = {
                    "relationship_stage": character_state["relationship_stage"].value,
                    "total_interactions": character_state["total_interactions"],
                    "character_growth": character_evolution.get("growth_updates", {}),
                    "evolution_trajectory": character_evolution.get("evolution_trajectory", {}),
                    "last_interaction": character_state["last_interaction"].isoformat() if character_state["last_interaction"] else None
                }

            return {
                "success": True,
                "user_id": user_id,
                "characters": evolution_data,
                "overall_relationship_health": self._calculate_overall_relationship_health(evolution_data),
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating character evolution report for user {user_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }

    def _calculate_overall_relationship_health(self, evolution_data: Dict[str, Any]) -> float:
        """Calculate overall relationship health score."""
        if not evolution_data:
            return 0.0

        health_scores = []

        for character_data in evolution_data.values():
            trajectory = character_data.get("evolution_trajectory", {})
            relationship_health = trajectory.get("relationship_health", 0.0)
            health_scores.append(relationship_health)

        return sum(health_scores) / len(health_scores) if health_scores else 0.0

    async def analyze_relationship_consistency(self, user_id: int) -> Dict[str, Any]:
        """Analyze consistency of character relationships over time."""
        try:
            # Get conversation memories for analysis
            memories_result = await self.session.execute(
                select(ConversationMemory)
                .where(ConversationMemory.user_id == user_id)
                .order_by(ConversationMemory.last_interaction_at)
            )
            memories = memories_result.scalars().all()

            if not memories:
                return {
                    "consistency_score": 0.0,
                    "analysis": "insufficient_data",
                    "recommendations": ["engage_more_frequently"]
                }

            # Analyze consistency patterns
            character_progressions = {}

            for memory in memories:
                if memory.emotional_state_snapshot:
                    try:
                        snapshot = json.loads(memory.emotional_state_snapshot)
                        character = snapshot.get("character")
                        if character:
                            if character not in character_progressions:
                                character_progressions[character] = []

                            trajectory = snapshot.get("evolution_trajectory", {})
                            character_progressions[character].append({
                                "timestamp": memory.last_interaction_at,
                                "maturity_level": trajectory.get("character_maturity_level", 0.0),
                                "growth_velocity": trajectory.get("growth_velocity", 0.0)
                            })
                    except json.JSONDecodeError:
                        continue

            # Calculate consistency scores
            character_consistency = {}
            for character, progression in character_progressions.items():
                if len(progression) > 1:
                    # Check for logical progression (generally upward trend)
                    maturity_levels = [p["maturity_level"] for p in progression]
                    growth_trend = self._analyze_growth_trend(maturity_levels)
                    character_consistency[character] = growth_trend

            overall_consistency = (
                sum(character_consistency.values()) / len(character_consistency)
                if character_consistency else 0.0
            )

            return {
                "consistency_score": overall_consistency,
                "character_consistency": character_consistency,
                "analysis": self._interpret_consistency_score(overall_consistency),
                "recommendations": self._generate_consistency_recommendations(overall_consistency)
            }

        except Exception as e:
            logger.error(f"Error analyzing relationship consistency for user {user_id}: {str(e)}")
            return {
                "consistency_score": 0.0,
                "error": str(e),
                "analysis": "analysis_error"
            }

    def _analyze_growth_trend(self, maturity_levels: List[float]) -> float:
        """Analyze growth trend in maturity levels."""
        if len(maturity_levels) < 2:
            return 0.5

        # Simple linear trend analysis
        positive_changes = 0
        total_changes = 0

        for i in range(1, len(maturity_levels)):
            change = maturity_levels[i] - maturity_levels[i-1]
            if change > 0:
                positive_changes += 1
            total_changes += 1

        return positive_changes / total_changes if total_changes > 0 else 0.5

    def _interpret_consistency_score(self, score: float) -> str:
        """Interpret consistency score into readable analysis."""
        if score > 0.8:
            return "excellent_consistency"
        elif score > 0.6:
            return "good_consistency"
        elif score > 0.4:
            return "moderate_consistency"
        elif score > 0.2:
            return "low_consistency"
        else:
            return "inconsistent_relationship"

    def _generate_consistency_recommendations(self, score: float) -> List[str]:
        """Generate recommendations based on consistency score."""
        if score > 0.8:
            return ["maintain_current_engagement_patterns", "continue_emotional_growth"]
        elif score > 0.6:
            return ["increase_interaction_frequency", "focus_on_emotional_openness"]
        elif score > 0.4:
            return ["establish_regular_engagement", "work_on_vulnerability_sharing"]
        else:
            return [
                "establish_consistent_engagement_patterns",
                "focus_on_building_trust",
                "be_more_emotionally_present"
            ]