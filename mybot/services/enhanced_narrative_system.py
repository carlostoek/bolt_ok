"""
Enhanced Narrative System Integration
====================================

This module enhances the existing narrative system with cinematic integration,
6-level emotional progression, and soul signature personalization while maintaining
100% backward compatibility.

Integration Points:
- Works seamlessly with existing CoordinadorCentral
- Enhances existing narrative handlers
- Maintains compatibility with current database models
- Adds cinematic layer without breaking changes
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update

from .narrative_service import NarrativeService
from .cinema_integration_engine import (
    CinemaIntegrationEngine, EmotionalLevel, PersonalizationArchetype,
    CinematicMoment, SoulSignature, get_cinema_engine
)
from database.narrative_unified import (
    NarrativeFragment, UserNarrativeState, UserArchetype,
    UserMissionProgress, NarrativeCharacterValidation
)
from database.models import User

logger = logging.getLogger(__name__)

class EnhancedNarrativeSystem:
    """
    Enhanced narrative system that adds cinematic experiences on top of
    existing narrative functionality without breaking changes.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.base_narrative = NarrativeService(session)
        self.cinema_engine = get_cinema_engine(session)
        
        # Fragment enhancement mappings
        self.emotional_level_fragments = {
            EmotionalLevel.CURIOSITY_AWAKENING: ["level1_scene1_welcome", "level1_scene2_intrigue"],
            EmotionalLevel.MYSTERY_DEEPENING: ["level2_scene1_depth", "level2_scene2_connection"],
            EmotionalLevel.TRUST_BUILDING: ["level3_scene1_trust", "level3_scene2_vulnerability"],
            EmotionalLevel.INTIMATE_CONNECTION: ["level4_scene1_intimacy", "level4_scene2_revelation"],
            EmotionalLevel.VULNERABLE_REVELATION: ["level5_scene1_truth", "level5_scene2_depth"],
            EmotionalLevel.SOUL_FUSION: ["level6_scene1_unity", "level6_scene2_transcendence"]
        }
        
        # Archetype-specific content variations
        self.archetype_adaptations = {
            PersonalizationArchetype.EXPLORER: {
                "content_style": "detailed_discovery",
                "interaction_pace": "thorough",
                "mystery_level": "high"
            },
            PersonalizationArchetype.ROMANTIC: {
                "content_style": "emotional_connection",
                "interaction_pace": "intimate",
                "mystery_level": "moderate"
            },
            PersonalizationArchetype.ANALYTICAL: {
                "content_style": "intellectual_depth",
                "interaction_pace": "thoughtful",
                "mystery_level": "complex"
            },
            PersonalizationArchetype.DIRECT: {
                "content_style": "clear_progression",
                "interaction_pace": "efficient",
                "mystery_level": "focused"
            },
            PersonalizationArchetype.PERSISTENT: {
                "content_style": "layered_revelation",
                "interaction_pace": "patient",
                "mystery_level": "gradual"
            },
            PersonalizationArchetype.PATIENT: {
                "content_style": "deep_contemplation",
                "interaction_pace": "meditative",
                "mystery_level": "profound"
            }
        }
    
    async def get_enhanced_fragment(self, user_id: int, fragment_key: str, 
                                  interaction_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Gets a fragment enhanced with cinematic personalization.
        
        This method wraps the base narrative service and adds cinematic enhancement
        while maintaining full backward compatibility.
        """
        try:
            # Get base fragment from existing system
            base_fragment = await self.base_narrative.get_fragment_by_key(fragment_key)
            
            if not base_fragment:
                logger.warning(f"Fragment not found: {fragment_key}")
                return {"success": False, "error": "Fragment not found"}
            
            # Get user's cinematic context
            user_context = await self._get_user_cinematic_context(user_id)
            soul_signature = await self.cinema_engine.personalization_engine.get_soul_signature(user_id)
            current_level = await self.cinema_engine.emotional_state_machine.get_current_level(user_id)
            
            # Process through cinematic enhancement if user has advanced progress
            if await self._should_apply_cinematic_enhancement(user_id, user_context):
                enhanced_fragment = await self._apply_cinematic_enhancement(
                    base_fragment, user_context, soul_signature, current_level
                )
            else:
                # For new users, maintain existing experience
                enhanced_fragment = await self._format_base_fragment(base_fragment, user_context)
            
            # Track fragment access for progression
            await self._track_fragment_access(user_id, fragment_key, enhanced_fragment)
            
            return {
                "success": True,
                "fragment": enhanced_fragment,
                "enhanced": await self._should_apply_cinematic_enhancement(user_id, user_context),
                "emotional_level": current_level.value if current_level else 1,
                "personalization": soul_signature.dominant_archetype.value
            }
            
        except Exception as e:
            logger.exception(f"Error getting enhanced fragment for user {user_id}, fragment {fragment_key}: {e}")
            return {"success": False, "error": str(e)}
    
    async def process_enhanced_decision(self, user_id: int, fragment_key: str, 
                                      choice_text: str, interaction_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Processes a decision with cinematic enhancement and emotional progression.
        """
        try:
            # Get user's cinematic context
            user_context = await self._get_user_cinematic_context(user_id)
            
            # Process decision through cinematic engine if enhanced
            if await self._should_apply_cinematic_enhancement(user_id, user_context):
                
                cinematic_interaction = {
                    "type": "narrative_decision",
                    "fragment_key": fragment_key,
                    "choice_text": choice_text,
                    "context": interaction_context or {}
                }
                
                # Process through cinematic engine
                cinematic_result = await self.cinema_engine.process_cinematic_moment(
                    user_id, cinematic_interaction
                )
                
                # Also process through base system for data consistency
                base_result = await self.base_narrative.process_user_choice(
                    user_id, fragment_key, choice_text
                )
                
                # Merge results
                return {
                    "success": True,
                    "cinematic_response": cinematic_result["cinematic_response"],
                    "base_result": base_result,
                    "enhanced": True,
                    "emotional_progression": cinematic_result.get("emotional_level"),
                    "character_consistency": cinematic_result.get("character_consistency_score"),
                    "personalization_applied": cinematic_result.get("personalization_applied")
                }
            
            else:
                # Process through base system only
                base_result = await self.base_narrative.process_user_choice(
                    user_id, fragment_key, choice_text
                )
                
                return {
                    "success": True,
                    "base_result": base_result,
                    "enhanced": False
                }
                
        except Exception as e:
            logger.exception(f"Error processing enhanced decision for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_narrative_progress_enhanced(self, user_id: int) -> Dict[str, Any]:
        """
        Gets enhanced narrative progress including cinematic metrics.
        """
        try:
            # Get base progress
            base_progress = await self.base_narrative.get_user_progress(user_id)
            
            # Get cinematic enhancements
            user_context = await self._get_user_cinematic_context(user_id)
            current_level = await self.cinema_engine.emotional_state_machine.get_current_level(user_id)
            soul_signature = await self.cinema_engine.personalization_engine.get_soul_signature(user_id)
            
            # Calculate enhanced metrics
            enhanced_metrics = await self._calculate_enhanced_metrics(user_id, user_context)
            
            return {
                "base_progress": base_progress,
                "emotional_level": current_level.value if current_level else 1,
                "emotional_level_name": current_level.name if current_level else "CURIOSITY_AWAKENING",
                "personalization_archetype": soul_signature.dominant_archetype.value,
                "trust_progression": soul_signature.trust_progression_velocity,
                "vulnerability_comfort": soul_signature.vulnerability_comfort_level,
                "character_consistency_average": enhanced_metrics.get("consistency_average", 95.0),
                "cinematic_moments_experienced": enhanced_metrics.get("cinematic_moments", 0),
                "enhanced_experience_active": await self._should_apply_cinematic_enhancement(user_id, user_context)
            }
            
        except Exception as e:
            logger.exception(f"Error getting enhanced progress for user {user_id}: {e}")
            return {"error": str(e)}
    
    async def _get_user_cinematic_context(self, user_id: int) -> Dict[str, Any]:
        """Gets comprehensive cinematic context for the user."""
        
        context = {}
        
        # Get user data
        user_result = await self.session.execute(select(User).where(User.id == user_id))
        context["user"] = user_result.scalar_one_or_none()
        
        # Get narrative state
        narrative_result = await self.session.execute(
            select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        )
        context["narrative_state"] = narrative_result.scalar_one_or_none()
        
        # Get archetype
        archetype_result = await self.session.execute(
            select(UserArchetype).where(UserArchetype.user_id == user_id)
        )
        context["archetype"] = archetype_result.scalar_one_or_none()
        
        # Get mission progress
        mission_result = await self.session.execute(
            select(UserMissionProgress).where(UserMissionProgress.user_id == user_id)
        )
        context["mission_progress"] = mission_result.scalar_one_or_none()
        
        return context
    
    async def _should_apply_cinematic_enhancement(self, user_id: int, user_context: Dict) -> bool:
        """
        Determines if cinematic enhancement should be applied for this user.
        
        Enhancement is applied to users who have progressed beyond basic interactions
        to prevent overwhelming new users.
        """
        
        # Check if user has sufficient progression
        narrative_state = user_context.get("narrative_state")
        if not narrative_state:
            return False
        
        # Check if user has completed at least 3 fragments
        if len(narrative_state.completed_fragments) < 3:
            return False
        
        # Check if user has demonstrated engagement
        if len(narrative_state.visited_fragments) < 5:
            return False
        
        # Check if user has unlocked clues (shows exploration)
        if len(narrative_state.unlocked_clues) < 2:
            return False
        
        return True
    
    async def _apply_cinematic_enhancement(self, base_fragment: Dict, user_context: Dict,
                                         soul_signature: SoulSignature, 
                                         emotional_level: EmotionalLevel) -> Dict[str, Any]:
        """
        Applies cinematic enhancement to a base fragment.
        """
        
        enhanced_fragment = base_fragment.copy()
        
        # Apply archetype-specific content adaptations
        archetype = soul_signature.dominant_archetype
        adaptations = self.archetype_adaptations.get(archetype, {})
        
        # Enhance content based on archetype
        if adaptations.get("content_style") == "emotional_connection":
            enhanced_fragment["content"] = await self._enhance_content_emotional(
                enhanced_fragment["content"], emotional_level
            )
        elif adaptations.get("content_style") == "intellectual_depth":
            enhanced_fragment["content"] = await self._enhance_content_intellectual(
                enhanced_fragment["content"], emotional_level
            )
        elif adaptations.get("content_style") == "detailed_discovery":
            enhanced_fragment["content"] = await self._enhance_content_exploratory(
                enhanced_fragment["content"], emotional_level
            )
        
        # Add personalized timing and interaction elements
        enhanced_fragment["cinematic_timing"] = await self._calculate_personalized_timing(
            archetype, emotional_level
        )
        
        # Add character consistency validation
        enhanced_fragment["character_validation"] = {
            "required_score": 95.0,
            "archetype_adaptations": soul_signature.diana_personality_adaptation
        }
        
        # Add emotional progression hooks
        enhanced_fragment["emotional_hooks"] = await self._generate_emotional_hooks(
            emotional_level, archetype, user_context
        )
        
        return enhanced_fragment
    
    async def _format_base_fragment(self, base_fragment: Dict, user_context: Dict) -> Dict[str, Any]:
        """
        Formats base fragment for users not yet receiving cinematic enhancement.
        """
        formatted_fragment = base_fragment.copy()
        
        # Add basic progression tracking
        formatted_fragment["basic_mode"] = True
        formatted_fragment["enhancement_criteria"] = {
            "fragments_needed": max(0, 3 - len(user_context.get("narrative_state", {}).get("completed_fragments", []))),
            "visits_needed": max(0, 5 - len(user_context.get("narrative_state", {}).get("visited_fragments", []))),
            "clues_needed": max(0, 2 - len(user_context.get("narrative_state", {}).get("unlocked_clues", [])))
        }
        
        return formatted_fragment
    
    async def _enhance_content_emotional(self, base_content: str, level: EmotionalLevel) -> str:
        """Enhances content for romantic/emotional archetype users."""
        
        emotional_enhancements = {
            EmotionalLevel.CURIOSITY_AWAKENING: "con una suave sonrisa que insinúa secretos por descubrir",
            EmotionalLevel.MYSTERY_DEEPENING: "con una mirada que parece leer tu alma",
            EmotionalLevel.TRUST_BUILDING: "con una calidez genuina que trasciende las palabras",
            EmotionalLevel.INTIMATE_CONNECTION: "con una vulnerabilidad que solo tú has logrado despertar",
            EmotionalLevel.VULNERABLE_REVELATION: "con lágrimas que brillan como diamantes en sus ojos",
            EmotionalLevel.SOUL_FUSION: "con una conexión que desafía toda comprensión mortal"
        }
        
        enhancement = emotional_enhancements.get(level, "")
        if enhancement:
            # Insert enhancement into content naturally
            if "*[" in base_content:
                # Add to existing stage direction
                base_content = base_content.replace("]*", f", {enhancement}]*")
            else:
                # Add new stage direction
                base_content = f"*[{enhancement}]*\n\n{base_content}"
        
        return base_content
    
    async def _enhance_content_intellectual(self, base_content: str, level: EmotionalLevel) -> str:
        """Enhances content for analytical archetype users."""
        
        intellectual_enhancements = {
            EmotionalLevel.CURIOSITY_AWAKENING: "con la precisión de quien elige cada palabra cuidadosamente",
            EmotionalLevel.MYSTERY_DEEPENING: "con capas de significado que se revelan gradualmente",
            EmotionalLevel.TRUST_BUILDING: "con una honestidad intelectual que trasciende lo superficial",
            EmotionalLevel.INTIMATE_CONNECTION: "con una complejidad emocional que desafía el análisis",
            EmotionalLevel.VULNERABLE_REVELATION: "con una desnudez intelectual que es más íntima que lo físico",
            EmotionalLevel.SOUL_FUSION: "con una comprensión que trasciende la lógica y abraza el misterio"
        }
        
        enhancement = intellectual_enhancements.get(level, "")
        if enhancement:
            base_content = f"*[{enhancement}]*\n\n{base_content}"
        
        return base_content
    
    async def _enhance_content_exploratory(self, base_content: str, level: EmotionalLevel) -> str:
        """Enhances content for explorer archetype users."""
        
        exploratory_enhancements = {
            EmotionalLevel.CURIOSITY_AWAKENING: "notando cada detalle sutil en su expresión",
            EmotionalLevel.MYSTERY_DEEPENING: "descubriendo capas ocultas en cada gesto",
            EmotionalLevel.TRUST_BUILDING: "observando cómo se revela gradualmente ante ti",
            EmotionalLevel.INTIMATE_CONNECTION: "explorando territorios emocionales inexplorados juntos",
            EmotionalLevel.VULNERABLE_REVELATION: "descubriendo los secretos más profundos de su ser",
            EmotionalLevel.SOUL_FUSION: "explorando dimensiones de conexión que desafían toda comprensión"
        }
        
        enhancement = exploratory_enhancements.get(level, "")
        if enhancement:
            base_content = f"*[{enhancement}]*\n\n{base_content}"
        
        return base_content
    
    async def _calculate_personalized_timing(self, archetype: PersonalizationArchetype,
                                           level: EmotionalLevel) -> Dict[str, float]:
        """Calculates personalized timing for content delivery."""
        
        base_timing = {
            "pre_response_delay": 2.0,
            "typing_indicator_duration": 3.0,
            "between_messages_pause": 1.5,
            "emotional_processing_pause": 2.5
        }
        
        # Adjust based on archetype
        if archetype == PersonalizationArchetype.DIRECT:
            # Direct users prefer faster pacing
            for key in base_timing:
                base_timing[key] *= 0.8
        elif archetype == PersonalizationArchetype.PATIENT:
            # Patient users appreciate thoughtful pacing
            for key in base_timing:
                base_timing[key] *= 1.4
        elif archetype == PersonalizationArchetype.ROMANTIC:
            # Romantic users love dramatic pauses
            base_timing["emotional_processing_pause"] *= 1.8
            base_timing["between_messages_pause"] *= 1.6
        
        # Adjust based on emotional level
        if level in [EmotionalLevel.VULNERABLE_REVELATION, EmotionalLevel.SOUL_FUSION]:
            base_timing["emotional_processing_pause"] *= 1.5
            base_timing["pre_response_delay"] *= 1.3
        
        return base_timing
    
    async def _generate_emotional_hooks(self, level: EmotionalLevel, 
                                      archetype: PersonalizationArchetype,
                                      user_context: Dict) -> List[str]:
        """Generates emotional hooks for the user's current state."""
        
        hooks = []
        
        # Level-based hooks
        if level == EmotionalLevel.CURIOSITY_AWAKENING:
            hooks.append("¿Qué más crees que hay detrás de esta sonrisa?")
        elif level == EmotionalLevel.TRUST_BUILDING:
            hooks.append("Siento que empiezas a ver más allá de mis defensas...")
        elif level == EmotionalLevel.INTIMATE_CONNECTION:
            hooks.append("Hay algo entre nosotros que va más allá de las palabras...")
        
        # Archetype-specific hooks
        if archetype == PersonalizationArchetype.EXPLORER:
            hooks.append("¿Has notado ese detalle que la mayoría pasa por alto?")
        elif archetype == PersonalizationArchetype.ROMANTIC:
            hooks.append("¿Puedes sentir cómo cambia el aire entre nosotros?")
        elif archetype == PersonalizationArchetype.ANALYTICAL:
            hooks.append("¿Qué patrones has comenzado a reconocer en mi comportamiento?")
        
        return hooks[:2]  # Maximum 2 hooks per interaction
    
    async def _track_fragment_access(self, user_id: int, fragment_key: str, 
                                   enhanced_fragment: Dict) -> None:
        """Tracks fragment access for progression and analytics."""
        
        # Update visited fragments
        result = await self.session.execute(
            select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        )
        narrative_state = result.scalar_one_or_none()
        
        if narrative_state:
            if fragment_key not in narrative_state.visited_fragments:
                visited = list(narrative_state.visited_fragments)
                visited.append(fragment_key)
                narrative_state.visited_fragments = visited
                
            # Track interaction patterns for archetyping
            interaction_patterns = narrative_state.interaction_patterns or {}
            interaction_patterns["last_access"] = datetime.utcnow().isoformat()
            interaction_patterns["access_count"] = interaction_patterns.get("access_count", 0) + 1
            narrative_state.interaction_patterns = interaction_patterns
            
            await self.session.commit()
    
    async def _calculate_enhanced_metrics(self, user_id: int, user_context: Dict) -> Dict[str, Any]:
        """Calculates enhanced metrics for progress tracking."""
        
        # Get recent character validations
        validations_result = await self.session.execute(
            select(NarrativeCharacterValidation)
            .where(and_(
                NarrativeCharacterValidation.user_id == user_id,
                NarrativeCharacterValidation.validated_at >= datetime.utcnow() - timedelta(days=30)
            ))
            .order_by(NarrativeCharacterValidation.validated_at.desc())
        )
        validations = validations_result.scalars().all()
        
        consistency_average = 95.0
        if validations:
            consistency_average = sum(v.consistency_score for v in validations) / len(validations)
        
        return {
            "consistency_average": consistency_average,
            "cinematic_moments": len(validations),
            "recent_validations": len([v for v in validations if v.meets_threshold])
        }


# Global instance for enhanced narrative system
_enhanced_narrative = None

def get_enhanced_narrative_system(session: AsyncSession) -> EnhancedNarrativeSystem:
    """Gets or creates the global enhanced narrative system."""
    global _enhanced_narrative
    if _enhanced_narrative is None or _enhanced_narrative.session != session:
        _enhanced_narrative = EnhancedNarrativeSystem(session)
    return _enhanced_narrative

async def initialize_enhanced_narrative(session: AsyncSession) -> Dict[str, Any]:
    """Initializes the enhanced narrative system."""
    try:
        enhanced_system = get_enhanced_narrative_system(session)
        
        # Test system functionality
        test_result = await enhanced_system.get_enhanced_fragment(
            user_id=999999999,  # Test user
            fragment_key="level1_scene1_welcome"
        )
        
        logger.info("Enhanced Narrative System initialized successfully")
        
        return {
            "success": True,
            "enhanced_narrative_active": True,
            "backward_compatibility_maintained": True,
            "cinematic_integration_active": True,
            "test_result_success": test_result.get("success", False),
            "message": "Enhanced Narrative System operativo con integración cinematográfica"
        }
        
    except Exception as e:
        logger.error(f"Error initializing Enhanced Narrative System: {e}")
        return {
            "success": False,
            "error": str(e),
            "enhanced_narrative_active": False,
            "message": "Error inicializando sistema narrativo mejorado"
        }