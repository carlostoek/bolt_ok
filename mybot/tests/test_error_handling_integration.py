"""
Tests para verificar el manejo integrado de errores entre interfaces.
Asegura que los errores se propaguen correctamente entre servicios.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, List

from services.interfaces.user_interaction_interface import (
    IUserInteractionProcessor,
    InteractionContext,
    InteractionType,
    InteractionResult,
    ValidationResult
)
from services.interfaces.emotional_state_interface import (
    IEmotionalStateManager,
    EmotionalAnalysisResult,
    EmotionalProfileResult
)
from services.interfaces.content_delivery_interface import (
    IContentDeliveryService,
    DeliveryResult,
    QueueOperationResult,
    ContentPackage,
    ContentType,
    DeliveryPriority
)
from services.interfaces.unified_narrative_interface import (
    IUnifiedNarrativeOrchestrator,
    NarrativeOperationResult
)


class MockUserInteractionProcessor(IUserInteractionProcessor):
    """Mock implementation para pruebas de manejo de errores."""
    
    def __init__(self, should_fail: bool = False, error_message: str = ""):
        self.should_fail = should_fail
        self.error_message = error_message
    
    async def process_interaction(self, context: InteractionContext) -> InteractionResult:
        if self.should_fail:
            return InteractionResult(
                success=False,
                data={},
                metadata={"error_context": "interaction_processing"},
                errors=[self.error_message]
            )
        
        return InteractionResult(
            success=True,
            data={"processed": True, "user_id": context.user_id},
            metadata={"processing_time": "0.1s"}
        )
    
    async def validate_interaction(self, context: InteractionContext) -> ValidationResult:
        if self.should_fail:
            return ValidationResult(
                success=False,
                data={},
                metadata={"validation_context": "interaction_validation"},
                errors=[f"Validation failed: {self.error_message}"]
            )
        
        return ValidationResult(
            success=True,
            data={"valid": True},
            metadata={"validation_rules_checked": 5}
        )
    
    async def log_interaction(self, context: InteractionContext, result: InteractionResult) -> None:
        if self.should_fail:
            raise RuntimeError(f"Logging failed: {self.error_message}")
    
    async def get_interaction_history(self, user_id: int, limit: int = 50) -> List[InteractionContext]:
        if self.should_fail:
            return []
        return []


class MockEmotionalStateManager(IEmotionalStateManager):
    """Mock implementation para pruebas de análisis emocional."""
    
    def __init__(self, should_fail: bool = False, error_message: str = ""):
        self.should_fail = should_fail
        self.error_message = error_message
    
    async def analyze_interaction_emotion(self, user_id: int, interaction_data: Dict[str, Any]):
        # Retorna el objeto EmotionalState real, no un Result
        from services.interfaces.emotional_state_interface import EmotionalState, EmotionalTone, EmotionalIntensity
        from datetime import datetime
        
        if self.should_fail:
            raise ValueError(f"Emotional analysis failed: {self.error_message}")
        
        return EmotionalState(
            user_id=user_id,
            primary_tone=EmotionalTone.POSITIVE,
            intensity=EmotionalIntensity.MEDIUM,
            confidence=0.8,
            context_factors={},
            timestamp=datetime.now()
        )
    
    async def update_user_emotional_profile(self, user_id: int, emotional_state) -> EmotionalProfileResult:
        if self.should_fail:
            return EmotionalProfileResult(
                success=False,
                data={},
                metadata={"user_id": user_id},
                errors=[f"Profile update failed: {self.error_message}"]
            )
        
        return EmotionalProfileResult(
            success=True,
            data={"profile_updated": True, "user_id": user_id},
            metadata={"update_timestamp": "2023-01-01T00:00:00Z"}
        )
    
    async def get_user_emotional_profile(self, user_id: int) -> EmotionalProfileResult:
        if self.should_fail:
            return EmotionalProfileResult(
                success=False,
                data={},
                metadata={"user_id": user_id},
                errors=[f"Profile retrieval failed: {self.error_message}"]
            )
        
        return EmotionalProfileResult(
            success=True,
            data={"profile_exists": True, "dominant_tone": "positive"},
            metadata={"user_id": user_id}
        )
    
    async def suggest_content_adaptation(self, user_id: int, base_content: Dict[str, Any]) -> EmotionalAnalysisResult:
        if self.should_fail:
            return EmotionalAnalysisResult(
                success=False,
                data={},
                metadata={"user_id": user_id},
                errors=[f"Content adaptation failed: {self.error_message}"]
            )
        
        return EmotionalAnalysisResult(
            success=True,
            data={"adapted_content": base_content, "adaptations_applied": ["tone_adjustment"]},
            metadata={"adaptation_confidence": 0.9}
        )
    
    async def detect_emotional_triggers(self, user_id: int, content_history: List[Dict[str, Any]]) -> EmotionalAnalysisResult:
        if self.should_fail:
            return EmotionalAnalysisResult(
                success=False,
                data={},
                metadata={"user_id": user_id},
                errors=[f"Trigger detection failed: {self.error_message}"]
            )
        
        return EmotionalAnalysisResult(
            success=True,
            data={"triggers": ["positive_feedback", "achievement_unlock"]},
            metadata={"analysis_depth": "comprehensive"}
        )
    
    async def get_engagement_recommendations(self, user_id: int) -> EmotionalAnalysisResult:
        if self.should_fail:
            return EmotionalAnalysisResult(
                success=False,
                data={},
                metadata={"user_id": user_id},
                errors=[f"Engagement recommendations failed: {self.error_message}"]
            )
        
        return EmotionalAnalysisResult(
            success=True,
            data={"recommendations": ["increase_positive_reinforcement", "add_variety"]},
            metadata={"confidence": 0.85}
        )


class TestErrorPropagation:
    """Pruebas para verificar la propagación correcta de errores."""
    
    @pytest.mark.asyncio
    async def test_interaction_processing_error_handling(self):
        """Verifica que los errores en procesamiento de interacción se manejen correctamente."""
        processor = MockUserInteractionProcessor(should_fail=True, error_message="Database connection lost")
        
        context = InteractionContext(
            user_id=123,
            interaction_type=InteractionType.MESSAGE,
            raw_data={"text": "hello"},
            timestamp=None,  # Sería datetime en uso real
            session_data={}
        )
        
        result = await processor.process_interaction(context)
        
        assert result.success is False
        assert len(result.errors) > 0
        assert "Database connection lost" in result.errors[0]
        assert result.metadata["error_context"] == "interaction_processing"
    
    @pytest.mark.asyncio
    async def test_validation_error_structure(self):
        """Verifica la estructura correcta de errores de validación."""
        processor = MockUserInteractionProcessor(should_fail=True, error_message="Invalid user session")
        
        context = InteractionContext(
            user_id=123,
            interaction_type=InteractionType.CALLBACK,
            raw_data={"callback_data": "invalid"},
            timestamp=None,
            session_data={}
        )
        
        result = await processor.validate_interaction(context)
        
        assert result.success is False
        assert len(result.errors) == 1
        assert "Validation failed: Invalid user session" in result.errors[0]
        assert "validation_context" in result.metadata
    
    @pytest.mark.asyncio
    async def test_emotional_analysis_error_recovery(self):
        """Verifica la recuperación de errores en análisis emocional."""
        emotion_manager = MockEmotionalStateManager(should_fail=True, error_message="Model not loaded")
        
        with pytest.raises(ValueError, match="Emotional analysis failed: Model not loaded"):
            await emotion_manager.analyze_interaction_emotion(123, {"text": "hello"})
    
    @pytest.mark.asyncio
    async def test_emotional_profile_error_handling(self):
        """Verifica el manejo de errores en operaciones de perfil emocional."""
        emotion_manager = MockEmotionalStateManager(should_fail=True, error_message="Profile corrupted")
        
        result = await emotion_manager.get_user_emotional_profile(123)
        
        assert result.success is False
        assert "Profile retrieval failed: Profile corrupted" in result.errors[0]
        assert result.metadata["user_id"] == 123
    
    @pytest.mark.asyncio
    async def test_content_adaptation_graceful_degradation(self):
        """Verifica la degradación elegante en adaptación de contenido."""
        emotion_manager = MockEmotionalStateManager(should_fail=True, error_message="Analysis service unavailable")
        
        base_content = {"type": "narrative", "content": "Hello world"}
        result = await emotion_manager.suggest_content_adaptation(123, base_content)
        
        assert result.success is False
        assert "Content adaptation failed" in result.errors[0]
        assert result.metadata["user_id"] == 123


class TestErrorRecoveryPatterns:
    """Pruebas para patrones de recuperación de errores."""
    
    @pytest.mark.asyncio
    async def test_retry_on_transient_failure(self):
        """Verifica el comportamiento de reintentos en fallos transitorios."""
        # Simulamos un servicio que falla las primeras 2 veces
        attempt_count = 0
        
        class RetryableProcessor(MockUserInteractionProcessor):
            async def process_interaction(self, context):
                nonlocal attempt_count
                attempt_count += 1
                
                if attempt_count <= 2:
                    return InteractionResult(
                        success=False,
                        data={},
                        metadata={"attempt": attempt_count},
                        errors=["Transient failure"]
                    )
                
                return InteractionResult(
                    success=True,
                    data={"processed": True, "attempts": attempt_count},
                    metadata={"final_attempt": attempt_count}
                )
        
        processor = RetryableProcessor()
        context = InteractionContext(
            user_id=123,
            interaction_type=InteractionType.MESSAGE,
            raw_data={},
            timestamp=None,
            session_data={}
        )
        
        # Simulamos lógica de reintentos
        max_retries = 3
        for attempt in range(max_retries):
            result = await processor.process_interaction(context)
            if result.success:
                break
        
        assert result.success is True
        assert result.data["attempts"] == 3
    
    @pytest.mark.asyncio
    async def test_fallback_mechanisms(self):
        """Verifica los mecanismos de fallback cuando servicios fallan."""
        primary_manager = MockEmotionalStateManager(should_fail=True, error_message="Primary service down")
        fallback_manager = MockEmotionalStateManager(should_fail=False)
        
        # Simular lógica de fallback
        try:
            result = await primary_manager.get_user_emotional_profile(123)
            if not result.success:
                raise Exception("Primary failed")
        except:
            result = await fallback_manager.get_user_emotional_profile(123)
        
        assert result.success is True
        assert result.data["profile_exists"] is True
    
    @pytest.mark.asyncio
    async def test_error_aggregation_across_services(self):
        """Verifica la agregación de errores a través de múltiples servicios."""
        interaction_processor = MockUserInteractionProcessor(
            should_fail=True, 
            error_message="Interaction validation failed"
        )
        emotion_manager = MockEmotionalStateManager(
            should_fail=True, 
            error_message="Emotional analysis failed"
        )
        
        # Simular orquestador que agrega errores
        errors = []
        
        # Procesar interacción
        context = InteractionContext(
            user_id=123,
            interaction_type=InteractionType.MESSAGE,
            raw_data={},
            timestamp=None,
            session_data={}
        )
        
        interaction_result = await interaction_processor.process_interaction(context)
        if not interaction_result.success:
            errors.extend(interaction_result.errors)
        
        # Análisis emocional
        profile_result = await emotion_manager.get_user_emotional_profile(123)
        if not profile_result.success:
            errors.extend(profile_result.errors)
        
        # Resultado agregado
        aggregated_result = NarrativeOperationResult(
            success=False,
            data={},
            metadata={"services_checked": ["interaction", "emotion"]},
            errors=errors
        )
        
        assert aggregated_result.success is False
        assert len(aggregated_result.errors) == 2
        assert "Interaction validation failed" in aggregated_result.errors[0]
        assert "Profile retrieval failed" in aggregated_result.errors[1]


class TestErrorContextInformation:
    """Pruebas para verificar información contextual en errores."""
    
    @pytest.mark.asyncio
    async def test_error_context_preservation(self):
        """Verifica que el contexto del error se preserve correctamente."""
        processor = MockUserInteractionProcessor(should_fail=True, error_message="Context test error")
        
        context = InteractionContext(
            user_id=456,
            interaction_type=InteractionType.COMMAND,
            raw_data={"command": "/test"},
            timestamp=None,
            session_data={"session_id": "abc123"}
        )
        
        result = await processor.process_interaction(context)
        
        assert result.success is False
        assert result.metadata["error_context"] == "interaction_processing"
        # En una implementación real, incluiríamos más contexto
    
    @pytest.mark.asyncio
    async def test_error_metadata_enrichment(self):
        """Verifica que los metadatos de error se enriquezcan apropiadamente."""
        emotion_manager = MockEmotionalStateManager(should_fail=True, error_message="Analysis timeout")
        
        result = await emotion_manager.update_user_emotional_profile(789, None)
        
        assert result.success is False
        assert result.metadata["user_id"] == 789
        assert len(result.errors) > 0
        # En una implementación real, incluiríamos timestamp, service_version, etc.


if __name__ == "__main__":
    pytest.main([__file__])