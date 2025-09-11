"""
Fallback Handler for Emotional System
Provides graceful degradation when emotional features fail
"""
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from services.coordinador_central import AccionUsuario

logger = logging.getLogger(__name__)


@dataclass
class FallbackConfig:
    """Configuration for fallback behavior"""
    enable_logging: bool = True
    use_neutral_responses: bool = True
    preserve_core_functionality: bool = True
    fallback_message_style: str = "standard"


class EmotionalFallbackHandler:
    """
    Handles graceful degradation when emotional system components fail.
    
    Ensures that core functionality continues working even when
    emotional enhancements are unavailable.
    """
    
    def __init__(self, config: Optional[FallbackConfig] = None):
        self.config = config or FallbackConfig()

    def get_fallback_response(self, user_id: int, accion: AccionUsuario, **kwargs) -> Dict[str, Any]:
        """
        Get fallback response when emotional system is unavailable.
        
        Returns neutral, functional responses that maintain core functionality.
        """
        fallback_responses = {
            AccionUsuario.REACCIONAR_PUBLICACION: self._get_reaction_fallback,
            AccionUsuario.TOMAR_DECISION: self._get_decision_fallback,
            AccionUsuario.ACCEDER_NARRATIVA_VIP: self._get_vip_access_fallback,
            AccionUsuario.PARTICIPAR_CANAL: self._get_participation_fallback,
            AccionUsuario.VERIFICAR_ENGAGEMENT: self._get_engagement_fallback
        }
        
        handler = fallback_responses.get(accion)
        if handler:
            return handler(user_id, **kwargs)
        
        return self._get_default_fallback(user_id, accion, **kwargs)

    def get_default_emotional_context(self) -> Dict[str, Any]:
        """Get default emotional context when analysis fails"""
        return {
            "emotional_state": "neutral",
            "archetype": "standard",
            "personalization_level": "none",
            "recommended_tone": "neutral",
            "adaptation_confidence": 0.0,
            "fallback_mode": True
        }

    def get_neutral_message_adaptation(self, original_message: str) -> str:
        """Return original message when adaptation fails"""
        if self.config.enable_logging:
            logger.debug(f"Using neutral message adaptation for: {original_message[:50]}...")
        return original_message

    def should_log_failure(self, error: Exception) -> bool:
        """Determine if failure should be logged"""
        return self.config.enable_logging

    def _get_reaction_fallback(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Fallback for reaction responses"""
        return {
            "emotional_tone": "neutral",
            "personalization_level": "standard",
            "message_adaptation": None,
            "fallback_mode": True
        }

    def _get_decision_fallback(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Fallback for narrative decisions"""
        return {
            "narrative_adaptation": None,
            "personalization_level": "standard",
            "emotional_context": self.get_default_emotional_context(),
            "fallback_mode": True
        }

    def _get_vip_access_fallback(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Fallback for VIP access"""
        return {
            "message_adaptation": None,
            "emotional_tone": "neutral",
            "fallback_mode": True
        }

    def _get_participation_fallback(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Fallback for channel participation"""
        return {
            "emotional_tone": "neutral",
            "engagement_boost": False,
            "fallback_mode": True
        }

    def _get_engagement_fallback(self, user_id: int, **kwargs) -> Dict[str, Any]:
        """Fallback for daily engagement"""
        return {
            "personalization_level": "standard",
            "streak_celebration": "standard",
            "fallback_mode": True
        }

    def _get_default_fallback(self, user_id: int, accion: AccionUsuario, **kwargs) -> Dict[str, Any]:
        """Default fallback for unknown actions"""
        return {
            "emotional_context": self.get_default_emotional_context(),
            "fallback_mode": True
        }


# Global instance
_global_fallback_handler = None


def get_emotional_fallback_handler() -> EmotionalFallbackHandler:
    """Get global fallback handler instance"""
    global _global_fallback_handler
    
    if _global_fallback_handler is None:
        _global_fallback_handler = EmotionalFallbackHandler()
    
    return _global_fallback_handler