"""
Emotional Coordinator - Surgical integration point for emotional evaluation system.
Extends existing CoordinadorCentral without modifying it.
"""
import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from services.coordinador_central import CoordinadorCentral, AccionUsuario
from services.emotional.emotional_analysis_service import EmotionalAnalysisService
from services.emotional.user_archetype_service import UserArchetypeService
from services.emotional.narrative_adaptation_engine import NarrativeAdaptationEngine
from services.emotional.feature_flags import EmotionalFeatureFlags
from services.emotional.circuit_breaker import EmotionalSystemCircuitBreaker
from utils.emotional.fallback_handler import EmotionalFallbackHandler

logger = logging.getLogger(__name__)


class EmotionalCoordinator:
    """
    Surgical integration coordinator that enhances CoordinadorCentral with emotional intelligence.
    
    Design Principles:
    - Preserve 100% existing functionality
    - Add emotional enhancements only when enabled and working
    - Graceful degradation when emotional system fails
    - Zero impact on performance when disabled
    """
    
    def __init__(self, coordinador_central: CoordinadorCentral):
        """Initialize emotional coordinator with existing coordinator"""
        self.core_coordinator = coordinador_central
        self.session = coordinador_central.session
        
        # Emotional services - lazy initialization for performance
        self._emotional_analysis = None
        self._archetype_service = None
        self._narrative_adaptation = None
        
        # Circuit breaker for fault tolerance
        self.circuit_breaker = EmotionalSystemCircuitBreaker()
        
        # Fallback handler for graceful degradation
        self.fallback_handler = EmotionalFallbackHandler()

    @property
    def emotional_analysis(self) -> EmotionalAnalysisService:
        """Lazy initialization of emotional analysis service"""
        if self._emotional_analysis is None:
            self._emotional_analysis = EmotionalAnalysisService(self.session)
        return self._emotional_analysis

    @property
    def archetype_service(self) -> UserArchetypeService:
        """Lazy initialization of archetype service"""
        if self._archetype_service is None:
            self._archetype_service = UserArchetypeService(self.session)
        return self._archetype_service

    @property
    def narrative_adaptation(self) -> NarrativeAdaptationEngine:
        """Lazy initialization of narrative adaptation engine"""
        if self._narrative_adaptation is None:
            self._narrative_adaptation = NarrativeAdaptationEngine(self.session)
        return self._narrative_adaptation

    async def execute_emotional_flow(self, user_id: int, accion: AccionUsuario, **kwargs) -> Dict[str, Any]:
        """
        Execute flow with emotional enhancements while preserving core functionality.
        
        This method implements the surgical integration pattern:
        1. Always execute core functionality first
        2. Apply emotional enhancements only if enabled and working
        3. Return enhanced result or fall back to core result
        
        Args:
            user_id: User ID
            accion: Action to execute
            **kwargs: Additional action parameters
            
        Returns:
            Enhanced result or core result if enhancement fails
        """
        # STEP 1: Always execute core functionality first (preserves existing behavior)
        core_result = await self.core_coordinator.ejecutar_flujo(user_id, accion, **kwargs)
        
        # STEP 2: Apply emotional enhancement only if enabled and core succeeded
        if not await self._should_apply_emotional_enhancement(user_id, accion):
            return core_result
        
        if not core_result.get("success", False):
            # Don't enhance failed operations
            return core_result
        
        # STEP 3: Attempt emotional enhancement with circuit breaker protection
        try:
            enhanced_result = await self.circuit_breaker.call(
                lambda: self._apply_emotional_enhancement(user_id, accion, core_result, **kwargs)
            )
            return enhanced_result
            
        except Exception as e:
            # STEP 4: Graceful degradation - return core result if enhancement fails
            logger.warning(f"Emotional enhancement failed for user {user_id}, action {accion}: {e}")
            await self._log_enhancement_failure(user_id, accion, e)
            return core_result

    async def _should_apply_emotional_enhancement(self, user_id: int, accion: AccionUsuario) -> bool:
        """
        Determine if emotional enhancement should be applied.
        
        Checks:
        1. Global feature flags
        2. User-specific rollout
        3. Action-specific enablement
        4. System health status
        """
        try:
            # Check if emotional features are globally enabled
            if not await EmotionalFeatureFlags.is_enabled("emotional_system_enabled"):
                return False
            
            # Check user-specific rollout
            if not await EmotionalFeatureFlags.is_user_in_rollout("emotional_system", user_id):
                return False
            
            # Check action-specific enablement
            action_flag_map = {
                AccionUsuario.REACCIONAR_PUBLICACION: "emotional_reactions_enabled",
                AccionUsuario.TOMAR_DECISION: "emotional_narrative_enabled",
                AccionUsuario.ACCEDER_NARRATIVA_VIP: "emotional_narrative_enabled",
                AccionUsuario.PARTICIPAR_CANAL: "emotional_engagement_enabled",
                AccionUsuario.VERIFICAR_ENGAGEMENT: "emotional_daily_enabled"
            }
            
            action_flag = action_flag_map.get(accion)
            if action_flag and not await EmotionalFeatureFlags.is_enabled(action_flag):
                return False
            
            # Check system health
            if not self.circuit_breaker.is_healthy():
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error checking emotional enhancement eligibility: {e}")
            return False

    async def _apply_emotional_enhancement(
        self, 
        user_id: int, 
        accion: AccionUsuario, 
        core_result: Dict[str, Any], 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Apply emotional enhancements to core result.
        
        This method adds emotional intelligence while preserving all core data.
        """
        # Create enhanced result as copy of core result
        enhanced_result = core_result.copy()
        
        # Get or create user emotional profile
        emotional_profile = await self.archetype_service.get_or_create_profile(user_id)
        
        # Analyze interaction for emotional context
        emotional_context = await self.emotional_analysis.analyze_interaction(
            user_id, accion, core_result, **kwargs
        )
        
        # Apply action-specific enhancements
        if accion == AccionUsuario.REACCIONAR_PUBLICACION:
            enhanced_result = await self._enhance_reaction_response(
                enhanced_result, emotional_profile, emotional_context
            )
        
        elif accion == AccionUsuario.TOMAR_DECISION:
            enhanced_result = await self._enhance_narrative_decision(
                enhanced_result, emotional_profile, emotional_context
            )
        
        elif accion == AccionUsuario.ACCEDER_NARRATIVA_VIP:
            enhanced_result = await self._enhance_vip_access(
                enhanced_result, emotional_profile, emotional_context
            )
        
        elif accion == AccionUsuario.PARTICIPAR_CANAL:
            enhanced_result = await self._enhance_channel_participation(
                enhanced_result, emotional_profile, emotional_context
            )
        
        elif accion == AccionUsuario.VERIFICAR_ENGAGEMENT:
            enhanced_result = await self._enhance_daily_engagement(
                enhanced_result, emotional_profile, emotional_context
            )
        
        # Update user emotional profile based on interaction
        await self.archetype_service.update_profile_from_interaction(
            user_id, accion, emotional_context, enhanced_result
        )
        
        # Add emotional metadata (preserves core data)
        enhanced_result["emotional_context"] = emotional_context
        enhanced_result["user_archetype"] = emotional_profile.archetype_primary
        enhanced_result["enhancement_applied"] = True
        
        return enhanced_result

    async def _enhance_reaction_response(
        self, 
        core_result: Dict[str, Any], 
        emotional_profile, 
        emotional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance reaction responses with emotional personalization"""
        if not core_result.get("success"):
            return core_result
        
        # Adapt message tone based on user archetype
        original_message = core_result.get("message", "")
        adapted_message = await self.narrative_adaptation.adapt_message(
            original_message, emotional_profile, emotional_context
        )
        
        # Preserve core message structure while enhancing tone
        core_result["message"] = adapted_message
        core_result["emotional_tone"] = emotional_context.get("recommended_tone", "neutral")
        
        return core_result

    async def _enhance_narrative_decision(
        self, 
        core_result: Dict[str, Any], 
        emotional_profile, 
        emotional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance narrative decisions with personalized content"""
        if not core_result.get("success") or not core_result.get("fragment"):
            return core_result
        
        # Adapt narrative fragment based on emotional profile
        fragment = core_result["fragment"]
        adapted_fragment = await self.narrative_adaptation.adapt_fragment(
            fragment, emotional_profile, emotional_context
        )
        
        # Preserve fragment structure while personalizing content
        core_result["fragment"] = adapted_fragment
        core_result["personalization_level"] = emotional_context.get("personalization_intensity", "medium")
        
        return core_result

    async def _enhance_vip_access(
        self, 
        core_result: Dict[str, Any], 
        emotional_profile, 
        emotional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance VIP access responses with emotional context"""
        # Adapt access denial/grant messages
        if core_result.get("message"):
            adapted_message = await self.narrative_adaptation.adapt_message(
                core_result["message"], emotional_profile, emotional_context
            )
            core_result["message"] = adapted_message
        
        return core_result

    async def _enhance_channel_participation(
        self, 
        core_result: Dict[str, Any], 
        emotional_profile, 
        emotional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance channel participation responses"""
        if core_result.get("message"):
            adapted_message = await self.narrative_adaptation.adapt_message(
                core_result["message"], emotional_profile, emotional_context
            )
            core_result["message"] = adapted_message
        
        return core_result

    async def _enhance_daily_engagement(
        self, 
        core_result: Dict[str, Any], 
        emotional_profile, 
        emotional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhance daily engagement responses with personalization"""
        if core_result.get("message"):
            adapted_message = await self.narrative_adaptation.adapt_message(
                core_result["message"], emotional_profile, emotional_context
            )
            core_result["message"] = adapted_message
        
        return core_result

    async def _log_enhancement_failure(self, user_id: int, accion: AccionUsuario, error: Exception):
        """Log emotional enhancement failures for monitoring"""
        logger.error(
            f"Emotional enhancement failure - User: {user_id}, Action: {accion}, Error: {error}",
            extra={
                "user_id": user_id,
                "action": accion.value,
                "error_type": type(error).__name__,
                "error_message": str(error)
            }
        )

    # Delegation methods for backward compatibility and easy access
    async def ejecutar_flujo(self, user_id: int, accion: AccionUsuario, **kwargs) -> Dict[str, Any]:
        """Delegate to execute_emotional_flow for backward compatibility"""
        return await self.execute_emotional_flow(user_id, accion, **kwargs)

    def __getattr__(self, name):
        """Delegate any other method calls to the core coordinator"""
        return getattr(self.core_coordinator, name)