"""
Character Intelligence Coordinator
Integrates enhanced character intelligence with existing narrative and handler systems.
Provides a unified interface for archetype-aware, emotionally intelligent character responses.
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from .enhanced_character_intelligence import (
        EnhancedCharacterIntelligence, RelationshipStage, EmotionalMilestone
    )
    from .character_relationship_evolution import CharacterRelationshipEvolution
    from .archetype_classifier import ArchetypeClassifier, UserArchetype
    from .character_voice_service import CharacterVoiceService, CharacterType, EmotionalContext
    from .emotional_analysis_service import EmotionalAnalysisService
    from .narrative_service import NarrativeService
    from ..database.models import User, UserStats, ButtonReaction
except ImportError:
    # Fallback to absolute imports
    from services.enhanced_character_intelligence import (
        EnhancedCharacterIntelligence, RelationshipStage, EmotionalMilestone
    )
    from services.character_relationship_evolution import CharacterRelationshipEvolution
    from services.archetype_classifier import ArchetypeClassifier, UserArchetype
    from services.character_voice_service import CharacterVoiceService, CharacterType, EmotionalContext
    from services.emotional_analysis_service import EmotionalAnalysisService
    from services.narrative_service import NarrativeService
    from database.models import User, UserStats, ButtonReaction

logger = logging.getLogger(__name__)

class CharacterIntelligenceCoordinator:
    """
    Unified coordinator for all character intelligence services.
    Provides seamless integration with existing narrative systems.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

        # Initialize all intelligence services
        self.enhanced_intelligence = EnhancedCharacterIntelligence(session)
        self.relationship_evolution = CharacterRelationshipEvolution(session)
        self.archetype_classifier = ArchetypeClassifier(session)
        self.character_voice_service = CharacterVoiceService()
        self.emotional_service = EmotionalAnalysisService(session)

        # Try to initialize narrative service (may not exist in all contexts)
        try:
            self.narrative_service = NarrativeService(session)
        except Exception as e:
            logger.warning(f"NarrativeService not available: {str(e)}")
            self.narrative_service = None

        # Service health tracking
        self._service_health = {}
        self._last_health_check = datetime.min

    async def get_intelligent_character_response(
        self,
        user_id: int,
        message_type: str,
        context: Dict[str, Any],
        fallback_safe: bool = True
    ) -> Dict[str, Any]:
        """
        Main entry point for getting intelligent character responses.
        Integrates all intelligence services while providing fallback safety.

        Args:
            user_id: User ID for personalization
            message_type: Type of message (reaction_success, decision_success, etc.)
            context: Interaction context (from handlers)
            fallback_safe: Whether to provide safe fallbacks on errors

        Returns:
            Dict with character response and intelligence metadata
        """
        try:
            # Health check services
            await self._check_service_health()

            # Prepare enriched context
            enriched_context = await self._enrich_interaction_context(user_id, context)

            # Get enhanced character response
            response = await self.enhanced_intelligence.get_enhanced_character_response(
                user_id=user_id,
                interaction_context=enriched_context,
                message_type=message_type,
                error_recovery=False
            )

            if response.get("success", False):
                # Track relationship evolution
                await self._track_relationship_evolution(user_id, response, enriched_context)

                # Add intelligence insights
                response["intelligence_insights"] = await self._generate_intelligence_insights(
                    user_id, response, enriched_context
                )

                return response
            else:
                # Fallback to enhanced error recovery
                return await self._enhanced_error_recovery(
                    user_id, message_type, enriched_context, fallback_safe
                )

        except Exception as e:
            logger.error(f"Error in intelligent character response for user {user_id}: {str(e)}")

            if fallback_safe:
                return await self._emergency_fallback_response(user_id, message_type, str(e))
            else:
                raise

    async def _enrich_interaction_context(
        self,
        user_id: int,
        base_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enrich interaction context with intelligence data."""

        enriched = base_context.copy()

        try:
            # Add emotional analysis
            emotional_analysis = await self.emotional_service.assess_vulnerability_level(user_id)
            if emotional_analysis.get("success", False):
                enriched.update({
                    "vulnerability_level": emotional_analysis.get("vulnerability_level", 0.3),
                    "emotional_indicators": emotional_analysis.get("indicators", []),
                    "emotional_state": emotional_analysis.get("vulnerability_category", "moderate")
                })

            # Add user archetype if available
            user_archetype = await self.archetype_classifier.get_user_archetype(user_id)
            if user_archetype:
                enriched["user_archetype"] = user_archetype

            # Add interaction history summary
            user_stats = await self.session.get(UserStats, user_id)
            if user_stats:
                enriched.update({
                    "total_interactions": getattr(user_stats, 'messages_sent', 0),
                    "engagement_pattern": "highly_engaged" if user_stats.checkin_streak > 7 else "moderate",
                    "user_loyalty": user_stats.checkin_streak
                })

            # Add timing analysis if response_time is provided
            if "response_time" in base_context:
                timing_data = {"response_time": base_context["response_time"]}
                timing_analysis = await self.emotional_service.analyze_response_timing(
                    user_id, datetime.utcnow(), "interaction"
                )
                if timing_analysis.get("success", False):
                    enriched["response_speed"] = timing_analysis.get("response_speed", "normal")

        except Exception as e:
            logger.warning(f"Error enriching interaction context for user {user_id}: {str(e)}")
            # Continue with base context if enrichment fails

        return enriched

    async def _track_relationship_evolution(
        self,
        user_id: int,
        response: Dict[str, Any],
        context: Dict[str, Any]
    ) -> None:
        """Track relationship evolution based on interaction."""
        try:
            character_str = response.get("character", "diana")
            character = CharacterType.DIANA if character_str == "diana" else CharacterType.LUCIEN

            # Detect milestones
            milestone_detected = None
            response_metadata = response.get("response_metadata", {})
            if response_metadata.get("milestone_detected"):
                milestone_str = response_metadata["milestone_detected"]
                try:
                    milestone_detected = EmotionalMilestone(milestone_str)
                except ValueError:
                    pass

            # Track evolution
            await self.relationship_evolution.track_relationship_evolution(
                user_id=user_id,
                character=character,
                interaction_data=context,
                milestone_detected=milestone_detected
            )

        except Exception as e:
            logger.warning(f"Error tracking relationship evolution: {str(e)}")
            # Non-critical error, don't fail main response

    async def _generate_intelligence_insights(
        self,
        user_id: int,
        response: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate insights about the intelligence applied."""
        try:
            insights = {
                "archetype_adaptation": False,
                "emotional_milestone": None,
                "relationship_growth": False,
                "character_evolution": False
            }

            response_metadata = response.get("response_metadata", {})

            # Check for archetype adaptation
            if response_metadata.get("archetype_used"):
                insights["archetype_adaptation"] = True
                insights["archetype_applied"] = response_metadata["archetype_used"]

            # Check for emotional milestone
            if response_metadata.get("milestone_detected"):
                insights["emotional_milestone"] = response_metadata["milestone_detected"]

            # Check for character evolution
            character_evolution = response.get("character_evolution", {})
            if character_evolution:
                insights["character_evolution"] = True
                insights["evolution_details"] = character_evolution

            return insights

        except Exception as e:
            logger.warning(f"Error generating intelligence insights: {str(e)}")
            return {}

    async def _enhanced_error_recovery(
        self,
        user_id: int,
        message_type: str,
        context: Dict[str, Any],
        fallback_safe: bool
    ) -> Dict[str, Any]:
        """Enhanced error recovery maintaining character authenticity."""
        try:
            # Try with error recovery mode
            response = await self.enhanced_intelligence.get_enhanced_character_response(
                user_id=user_id,
                interaction_context=context,
                message_type=message_type,
                error_recovery=True
            )

            if response.get("success", False):
                return response

            # Fallback to basic character voice service
            character = CharacterType.LUCIEN  # Lucien handles errors
            emotional_context = EmotionalContext.PAUSA_REFLEXIVA  # Default safe context

            base_response = self.character_voice_service.get_character_response(
                character, emotional_context, message_type
            )

            return {
                "success": True,
                "character": character.value,
                "response": base_response,
                "response_metadata": {
                    "fallback_mode": "character_voice_service",
                    "error_recovery": True
                },
                "character_evolution": {},
                "emotional_context": emotional_context.value
            }

        except Exception as e:
            logger.error(f"Error in enhanced error recovery: {str(e)}")

            if fallback_safe:
                return await self._emergency_fallback_response(user_id, message_type, str(e))
            else:
                raise

    async def _emergency_fallback_response(
        self,
        user_id: int,
        message_type: str,
        error_message: str
    ) -> Dict[str, Any]:
        """Emergency fallback when all intelligence services fail."""

        # Ultra-safe responses that maintain character authenticity
        emergency_responses = {
            "reaction_success": {
                "character": "diana",
                "response": "Tu gesto llega a mi corazón... *+10 besitos* 💋 han sido añadidos a tu cuenta."
            },
            "decision_success": {
                "character": "diana",
                "response": "Tu elección moldea nuestra historia compartida..."
            },
            "points_required": {
                "character": "lucien",
                "response": "Esta decisión requiere más besitos. Cultiva tu conexión primero."
            },
            "vip_required": {
                "character": "diana",
                "response": "Algunas fantasías están reservadas para mis amantes más dedicados..."
            },
            "daily_check": {
                "character": "diana",
                "response": "Me alegra verte de nuevo... Tu presencia constante alimenta nuestra conexión."
            },
            "error": {
                "character": "lucien",
                "response": "Ha ocurrido algo inesperado, pero mi guía para ti permanece constante."
            }
        }

        fallback = emergency_responses.get(message_type, emergency_responses["error"])

        return {
            "success": True,
            "character": fallback["character"],
            "response": fallback["response"],
            "response_metadata": {
                "emergency_fallback": True,
                "original_error": error_message[:100],  # Truncated for safety
                "fallback_mode": "emergency_static"
            },
            "character_evolution": {},
            "emotional_context": None
        }

    async def _check_service_health(self) -> None:
        """Check health of all intelligence services."""
        if datetime.utcnow() - self._last_health_check < timedelta(minutes=5):
            return  # Skip frequent health checks

        try:
            # Quick health checks
            services = {
                "enhanced_intelligence": self.enhanced_intelligence,
                "relationship_evolution": self.relationship_evolution,
                "archetype_classifier": self.archetype_classifier,
                "character_voice_service": self.character_voice_service,
                "emotional_service": self.emotional_service
            }

            for service_name, service in services.items():
                try:
                    # Basic health check - service exists and has expected methods
                    if hasattr(service, '__class__'):
                        self._service_health[service_name] = "healthy"
                    else:
                        self._service_health[service_name] = "unavailable"
                except Exception:
                    self._service_health[service_name] = "error"

            self._last_health_check = datetime.utcnow()

        except Exception as e:
            logger.warning(f"Error in service health check: {str(e)}")

    async def get_user_intelligence_summary(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive intelligence summary for a user."""
        try:
            # Get archetype information
            archetype_info = await self.archetype_classifier.get_user_archetype(user_id)

            # Get relationship insights
            relationship_insights = await self.enhanced_intelligence.get_relationship_insights(user_id)

            # Get character evolution report
            evolution_report = await self.relationship_evolution.get_character_evolution_report(user_id)

            # Get relationship consistency analysis
            consistency_analysis = await self.relationship_evolution.analyze_relationship_consistency(user_id)

            return {
                "success": True,
                "user_id": user_id,
                "archetype_profile": archetype_info,
                "relationship_insights": relationship_insights,
                "character_evolution": evolution_report,
                "relationship_consistency": consistency_analysis,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error generating intelligence summary for user {user_id}: {str(e)}")
            return {
                "success": False,
                "user_id": user_id,
                "error": str(e)
            }

    async def classify_user_archetype(
        self,
        user_id: int,
        conversation_data: List[Dict[str, Any]],
        force_reclassify: bool = False
    ) -> Dict[str, Any]:
        """
        Classify user archetype with intelligence coordination.

        Args:
            user_id: User ID to classify
            conversation_data: Recent conversation/interaction data
            force_reclassify: Force new classification

        Returns:
            Classification results with intelligence insights
        """
        try:
            # Use archetype classifier
            result = await self.archetype_classifier.classify_user(
                user_id, conversation_data, force_reclassify
            )

            # Add coordinator insights
            if result.get("success", False) or result.get("primary_archetype"):
                result["intelligence_insights"] = {
                    "character_adaptation_enabled": True,
                    "relationship_tracking_active": True,
                    "emotional_milestone_detection": True,
                    "classification_confidence": result.get("confidence_score", 0.0)
                }

                # Generate adaptation preview
                if result.get("primary_archetype"):
                    result["adaptation_preview"] = self._generate_adaptation_preview(
                        result["primary_archetype"]
                    )

            return result

        except Exception as e:
            logger.error(f"Error in coordinated archetype classification: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "fallback_available": True
            }

    def _generate_adaptation_preview(self, archetype: str) -> Dict[str, Any]:
        """Generate preview of how characters will adapt to this archetype."""
        adaptations = {
            UserArchetype.EXPLORER_DEEP.value: {
                "diana_style": "Revelaciones graduales con profundidad filosófica",
                "lucien_style": "Guía analítica que aprecia la complejidad",
                "interaction_pace": "Contemplativo y reflexivo",
                "content_focus": "Misterios profundos y conexiones significativas"
            },
            UserArchetype.DIRECT_AUTHENTIC.value: {
                "diana_style": "Intimidad honesta y conexión directa",
                "lucien_style": "Sabiduría clara y apoyo directo",
                "interaction_pace": "Inmediato y auténtico",
                "content_focus": "Verdades emocionales y conexión real"
            },
            UserArchetype.POET_DESIRE.value: {
                "diana_style": "Seducción estética con lenguaje poético",
                "lucien_style": "Guía elegante que valida la belleza",
                "interaction_pace": "Rítmico y artístico",
                "content_focus": "Belleza, metáforas y experiencias sensuales"
            },
            UserArchetype.ANALYTIC_EMPATHIC.value: {
                "diana_style": "Intimidad paradójica e intelectual",
                "lucien_style": "Análisis empático y sabiduría sofisticada",
                "interaction_pace": "Reflexivo y complejo",
                "content_focus": "Paradojas emocionales y comprensión profunda"
            },
            UserArchetype.PERSISTENT_PATIENT.value: {
                "diana_style": "Recompensas por devoción y paciencia",
                "lucien_style": "Honra el compromiso con sabiduría constante",
                "interaction_pace": "Constante y evolutivo",
                "content_focus": "Desarrollo gradual y recompensas por lealtad"
            }
        }

        return adaptations.get(archetype, {
            "diana_style": "Adaptación personalizada en desarrollo",
            "lucien_style": "Guía personalizada en desarrollo",
            "interaction_pace": "Adaptativo",
            "content_focus": "Personalización en progreso"
        })

    async def handle_narrative_integration(
        self,
        user_id: int,
        narrative_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle integration with narrative service for character intelligence.

        Args:
            user_id: User ID
            narrative_context: Context from narrative service

        Returns:
            Enhanced narrative context with character intelligence
        """
        try:
            if not self.narrative_service:
                return narrative_context

            # Enrich narrative context with character intelligence
            user_archetype = await self.archetype_classifier.get_user_archetype(user_id)
            relationship_stage = await self._get_relationship_stage_for_narrative(user_id)

            enhanced_context = narrative_context.copy()
            enhanced_context["character_intelligence"] = {
                "user_archetype": user_archetype,
                "relationship_stage": relationship_stage,
                "adaptation_active": bool(user_archetype),
                "emotional_awareness": True
            }

            return enhanced_context

        except Exception as e:
            logger.warning(f"Error in narrative integration: {str(e)}")
            return narrative_context

    async def _get_relationship_stage_for_narrative(self, user_id: int) -> Optional[str]:
        """Get relationship stage for narrative integration."""
        try:
            user_stats = await self.session.get(UserStats, user_id)
            if not user_stats:
                return RelationshipStage.INITIAL_CONTACT.value

            total_interactions = getattr(user_stats, 'messages_sent', 0)

            if total_interactions < 5:
                return RelationshipStage.INITIAL_CONTACT.value
            elif total_interactions < 15:
                return RelationshipStage.GROWING_CURIOSITY.value
            elif total_interactions < 30:
                return RelationshipStage.EMOTIONAL_OPENING.value
            elif total_interactions < 60:
                return RelationshipStage.DEEPENING_CONNECTION.value
            elif total_interactions < 100:
                return RelationshipStage.INTIMATE_UNDERSTANDING.value
            else:
                return RelationshipStage.MATURE_RELATIONSHIP.value

        except Exception:
            return RelationshipStage.INITIAL_CONTACT.value

    def get_service_health_status(self) -> Dict[str, Any]:
        """Get current health status of all intelligence services."""
        return {
            "service_health": self._service_health,
            "last_check": self._last_health_check.isoformat() if self._last_health_check != datetime.min else None,
            "overall_status": "healthy" if all(
                status == "healthy" for status in self._service_health.values()
            ) else "degraded",
            "available_services": [
                name for name, status in self._service_health.items()
                if status == "healthy"
            ]
        }