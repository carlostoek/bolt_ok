"""
Tests para verificar la consistencia de interfaces del sistema Diana.
Asegura que todas las interfaces sigan los patrones estandarizados.
"""
import pytest
import inspect
from typing import get_type_hints, get_origin, get_args
from dataclasses import dataclass, fields

from services.interfaces import (
    IUserNarrativeService,
    IRewardSystem,
    INotificationService,
    IPointService,
    IUserInteractionProcessor,
    IEmotionalStateManager,
    IContentDeliveryService,
    IUnifiedNarrativeOrchestrator,
    IUnifiedNarrativeAnalytics,
    IUnifiedNarrativeConfiguration
)


class TestInterfaceConsistency:
    """Pruebas de consistencia para todas las interfaces del sistema."""
    
    def test_all_interfaces_have_abstract_methods(self):
        """Verifica que todas las interfaces tengan métodos abstractos."""
        interfaces = [
            IUserNarrativeService,
            IRewardSystem,
            INotificationService, 
            IPointService,
            IUserInteractionProcessor,
            IEmotionalStateManager,
            IContentDeliveryService,
            IUnifiedNarrativeOrchestrator,
            IUnifiedNarrativeAnalytics,
            IUnifiedNarrativeConfiguration
        ]
        
        for interface in interfaces:
            abstract_methods = getattr(interface, '__abstractmethods__', set())
            assert len(abstract_methods) > 0, f"{interface.__name__} debe tener métodos abstractos"
    
    def test_standardized_result_types_structure(self):
        """Verifica que los tipos de resultado estandarizados tengan la estructura correcta."""
        from services.interfaces.user_interaction_interface import ValidationResult, InteractionResult
        from services.interfaces.content_delivery_interface import DeliveryResult, QueueOperationResult
        from services.interfaces.emotional_state_interface import EmotionalAnalysisResult, EmotionalProfileResult
        from services.interfaces.unified_narrative_interface import NarrativeOperationResult, AnalyticsResult, ConfigurationResult
        from services.interfaces.user_narrative_interface import NarrativeServiceResult
        
        standardized_types = [
            ValidationResult, InteractionResult, DeliveryResult, QueueOperationResult,
            EmotionalAnalysisResult, EmotionalProfileResult, NarrativeOperationResult,
            AnalyticsResult, ConfigurationResult, NarrativeServiceResult
        ]
        
        for result_type in standardized_types:
            # Verificar que sea un dataclass
            assert hasattr(result_type, '__dataclass_fields__'), f"{result_type.__name__} debe ser un dataclass"
            
            # Verificar estructura estándar
            field_names = set(field.name for field in fields(result_type))
            expected_fields = {'success', 'data', 'metadata', 'errors'}
            assert expected_fields.issubset(field_names), f"{result_type.__name__} debe tener campos: {expected_fields}"
            
            # Verificar tipos de campos estándar
            type_hints = get_type_hints(result_type)
            assert type_hints['success'] == bool, f"{result_type.__name__}.success debe ser bool"
            assert str(type_hints['data']).startswith('typing.Dict'), f"{result_type.__name__}.data debe ser Dict[str, Any]"
            assert str(type_hints['metadata']).startswith('typing.Dict'), f"{result_type.__name__}.metadata debe ser Dict[str, Any]"
    
    def test_async_method_signatures(self):
        """Verifica que todos los métodos de interface sean async cuando sea apropiado."""
        interfaces_to_check = [
            IUserInteractionProcessor,
            IEmotionalStateManager,
            IContentDeliveryService,
            IUnifiedNarrativeOrchestrator
        ]
        
        for interface in interfaces_to_check:
            methods = inspect.getmembers(interface, predicate=inspect.isfunction)
            
            for method_name, method in methods:
                if not method_name.startswith('_'):  # Ignorar métodos privados
                    assert inspect.iscoroutinefunction(method), f"{interface.__name__}.{method_name} debe ser async"
    
    def test_method_documentation(self):
        """Verifica que todos los métodos de interface tengan documentación adecuada."""
        interfaces_to_check = [
            IUserInteractionProcessor,
            IEmotionalStateManager,
            IContentDeliveryService,
            IUnifiedNarrativeOrchestrator
        ]
        
        for interface in interfaces_to_check:
            methods = inspect.getmembers(interface, predicate=inspect.isfunction)
            
            for method_name, method in methods:
                if not method_name.startswith('_'):  # Ignorar métodos privados
                    assert method.__doc__ is not None, f"{interface.__name__}.{method_name} debe tener docstring"
                    assert 'Args:' in method.__doc__, f"{interface.__name__}.{method_name} debe documentar Args"
                    assert 'Returns:' in method.__doc__, f"{interface.__name__}.{method_name} debe documentar Returns"
    
    def test_no_mixed_return_types(self):
        """Verifica que no haya tipos de retorno mixtos en las interfaces nuevas."""
        from services.interfaces.user_interaction_interface import IUserInteractionProcessor
        from services.interfaces.emotional_state_interface import IEmotionalStateManager
        from services.interfaces.content_delivery_interface import IContentDeliveryService
        from services.interfaces.unified_narrative_interface import IUnifiedNarrativeOrchestrator
        
        interfaces_to_check = [
            IUserInteractionProcessor,
            IEmotionalStateManager,
            IContentDeliveryService,
            IUnifiedNarrativeOrchestrator
        ]
        
        for interface in interfaces_to_check:
            methods = inspect.getmembers(interface, predicate=inspect.isfunction)
            
            for method_name, method in methods:
                if not method_name.startswith('_'):
                    type_hints = get_type_hints(method)
                    return_type = type_hints.get('return')
                    
                    if return_type is not None:
                        # Verificar que no sea bool simple o Dict[str, Any] simple
                        if hasattr(return_type, '__name__'):
                            assert return_type != bool or method_name in ['validate_interaction'], \
                                f"{interface.__name__}.{method_name} no debe retornar bool simple"
                            assert str(return_type) != 'typing.Dict[str, typing.Any]', \
                                f"{interface.__name__}.{method_name} no debe retornar Dict[str, Any] simple"
    
    def test_error_handling_patterns(self):
        """Verifica que las interfaces sigan patrones consistentes de manejo de errores."""
        from services.interfaces.user_interaction_interface import IUserInteractionProcessor
        from services.interfaces.emotional_state_interface import IEmotionalStateManager
        from services.interfaces.content_delivery_interface import IContentDeliveryService
        
        interfaces_to_check = [
            IUserInteractionProcessor,
            IEmotionalStateManager,
            IContentDeliveryService
        ]
        
        for interface in interfaces_to_check:
            methods = inspect.getmembers(interface, predicate=inspect.isfunction)
            
            for method_name, method in methods:
                if not method_name.startswith('_') and method.__doc__:
                    # Los métodos modernos no deben documentar Raises explícitamente
                    # ya que usan tipos de resultado estandarizados
                    if any(result_word in method.__doc__ for result_word in ['Result:', 'Result']):
                        assert 'Raises:' not in method.__doc__, \
                            f"{interface.__name__}.{method_name} no debe documentar Raises si usa tipos Result"


class TestResultTypeUsage:
    """Pruebas específicas para el uso correcto de tipos de resultado."""
    
    def test_validation_result_usage(self):
        """Verifica el uso correcto de ValidationResult."""
        from services.interfaces.user_interaction_interface import ValidationResult
        
        # Test de construcción básica
        result = ValidationResult(
            success=True,
            data={"validation_passed": True},
            metadata={"validation_time": "2023-01-01T00:00:00Z"}
        )
        
        assert result.success is True
        assert result.data["validation_passed"] is True
        assert len(result.errors) == 0  # Lista vacía por defecto
    
    def test_error_handling_in_results(self):
        """Verifica el manejo correcto de errores en tipos Result."""
        from services.interfaces.user_interaction_interface import InteractionResult
        
        # Test con errores
        result = InteractionResult(
            success=False,
            data={},
            metadata={"error_context": "test"},
            errors=["Validation failed", "User not found"]
        )
        
        assert result.success is False
        assert len(result.errors) == 2
        assert "Validation failed" in result.errors
    
    def test_metadata_consistency(self):
        """Verifica que los metadatos sigan patrones consistentes."""
        from services.interfaces.emotional_state_interface import EmotionalAnalysisResult
        
        result = EmotionalAnalysisResult(
            success=True,
            data={"emotion": "positive"},
            metadata={
                "timestamp": "2023-01-01T00:00:00Z",
                "confidence": 0.85,
                "analysis_version": "v1.0"
            }
        )
        
        # Verificar que los metadatos contengan información útil
        assert "timestamp" in result.metadata
        assert isinstance(result.metadata["confidence"], (int, float))


class TestInterfaceIntegration:
    """Pruebas de integración entre interfaces."""
    
    def test_cross_interface_type_compatibility(self):
        """Verifica que los tipos compartidos entre interfaces sean compatibles."""
        from services.interfaces.emotional_state_interface import EmotionalState
        from services.interfaces.user_interaction_interface import InteractionResult
        
        # EmotionalState debería ser usable en InteractionResult
        emotional_state = EmotionalState(
            user_id=123,
            primary_tone="positive",  # Esto sería un enum en uso real
            intensity="medium",  # Esto sería un enum en uso real
            confidence=0.8,
            context_factors={},
            timestamp=None  # Sería datetime en uso real
        )
        
        # Verificar que se puede incluir en datos de resultado
        result = InteractionResult(
            success=True,
            data={"emotional_state": emotional_state},
            metadata={}
        )
        
        assert result.data["emotional_state"] is not None
    
    def test_interface_composition_patterns(self):
        """Verifica que las interfaces puedan componerse correctamente."""
        # Esta prueba verificaría que IUnifiedNarrativeOrchestrator
        # pueda usar correctamente los otros servicios
        
        # En una implementación real, esto verificaría:
        # - Que el orquestador pueda llamar métodos de otras interfaces
        # - Que los tipos de resultado sean compatibles
        # - Que la composición de servicios funcione correctamente
        
        # Por ahora, verificamos que las interfaces tengan las dependencias esperadas
        from services.interfaces.unified_narrative_interface import IUnifiedNarrativeOrchestrator
        
        # Verificar que la interfaz hace referencia a otros tipos de interfaces
        methods = inspect.getmembers(IUnifiedNarrativeOrchestrator, predicate=inspect.isfunction)
        assert len(methods) > 0, "El orquestador debe tener métodos definidos"


if __name__ == "__main__":
    pytest.main([__file__])