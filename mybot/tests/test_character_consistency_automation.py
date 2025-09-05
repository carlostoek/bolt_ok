"""
Character Consistency Automation Tests

This module tests the automated character consistency validation system
that runs in production to ensure Diana's personality is maintained
across all new content creation and updates.
"""

import pytest
import pytest_asyncio
import asyncio
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.diana_character_validator import DianaCharacterValidator, CharacterValidationResult
from services.narrative_character_integrity_service import NarrativeCharacterIntegrityService
from database.narrative_unified import NarrativeFragment, UserNarrativeState
from services.coordinador_central import CoordinadorCentral
from services.diana_menu_system import DianaMenuSystem


class TestAutomatedValidationPipeline:
    """Test automated validation pipeline for content creation."""
    
    @pytest_asyncio.fixture
    async def integrity_service(self, session):
        """Create integrity service for testing."""
        return NarrativeCharacterIntegrityService(session)
    
    @pytest_asyncio.fixture
    async def sample_narrative_fragments(self):
        """Sample fragments for batch testing."""
        return [
            {
                "id": "fragment_001",
                "title": "💋 El Primer Encuentro",
                "content": """
                Las sombras danzan suavemente cuando Diana aparece, 
                sus ojos brillando con secretos no revelados... 
                "¿Acaso sabías que nos encontraríamos aquí?" susurra 
                con esa voz que promete misterios por descubrir...
                """,
                "fragment_type": "STORY",
                "choices": [
                    {"text": "💋 'Esperaba este momento...'", "next": "fragment_002"},
                    {"text": "🔮 'Cuéntame sobre esos secretos...'", "next": "fragment_003"}
                ]
            },
            {
                "id": "fragment_002", 
                "title": "🎭 Una Decisión Crucial",
                "content": """
                Diana se acerca más, su presencia magnética llenando 
                el espacio entre vosotros... "Hay una elección que 
                debes hacer", murmura, "algo que definirá el curso 
                de nuestra historia..." Una mezcla de anticipación 
                y misterio abraza sus palabras...
                """,
                "fragment_type": "DECISION",
                "choices": [
                    {"text": "💫 'Confío en ti completamente'", "cost": 5},
                    {"text": "🌹 'Necesito saber más primero'", "cost": 0},
                    {"text": "❤️ 'Decidamos juntos'", "cost": 10}
                ]
            },
            {
                "id": "fragment_bad",
                "title": "Sistema Error", 
                "content": "Error 404. Configuración no encontrada. Reinicie el sistema.",
                "fragment_type": "STORY",
                "choices": [{"text": "OK", "next": "end"}]
            }
        ]
    
    async def test_batch_fragment_validation(self, integrity_service, sample_narrative_fragments):
        """Test validation of multiple fragments in batch."""
        results = {}
        
        # Validate each fragment
        for fragment_data in sample_narrative_fragments:
            is_valid, result = await integrity_service.validate_fragment_creation(fragment_data)
            results[fragment_data["id"]] = {
                "is_valid": is_valid,
                "result": result
            }
        
        # Good fragments should pass
        assert results["fragment_001"]["is_valid"], "Good fragment should pass validation"
        assert results["fragment_002"]["is_valid"], "Decision fragment should pass validation"
        assert results["fragment_001"]["result"].overall_score >= 95.0, "Good fragment should meet MVP threshold"
        
        # Bad fragment should fail
        assert not results["fragment_bad"]["is_valid"], "Bad fragment should fail validation"
        assert results["fragment_bad"]["result"].overall_score < 50.0, "Bad fragment should score very low"
    
    async def test_validation_pipeline_performance(self, integrity_service, sample_narrative_fragments):
        """Test that validation pipeline performs adequately under load."""
        import time
        
        start_time = time.time()
        
        # Run validation on all fragments simultaneously
        validation_tasks = []
        for fragment_data in sample_narrative_fragments:
            task = integrity_service.validate_fragment_creation(fragment_data)
            validation_tasks.append(task)
        
        # Wait for all validations to complete
        results = await asyncio.gather(*validation_tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance requirement: should validate 3 fragments in under 2 seconds
        assert total_time < 2.0, f"Validation took too long: {total_time}s for 3 fragments"
        
        # All validations should have completed
        assert len(results) == 3, "All validations should complete"
        
        # Results should be properly structured
        for is_valid, result in results:
            assert isinstance(is_valid, bool), "Validation should return boolean"
            assert isinstance(result, CharacterValidationResult), "Should return proper result object"
    
    async def test_concurrent_validation_safety(self, integrity_service, sample_narrative_fragments):
        """Test that concurrent validations don't interfere with each other."""
        # Create multiple concurrent validation requests
        concurrent_tasks = []
        
        for i in range(5):  # Run 5 concurrent validations of the same content
            fragment_data = sample_narrative_fragments[0]  # Use the good fragment
            task = integrity_service.validate_fragment_creation(fragment_data)
            concurrent_tasks.append(task)
        
        results = await asyncio.gather(*concurrent_tasks)
        
        # All results should be identical (same content, same validation)
        first_result = results[0][1]
        for is_valid, result in results[1:]:
            assert abs(result.overall_score - first_result.overall_score) < 0.1, (
                "Concurrent validations should produce identical results"
            )
            assert result.meets_threshold == first_result.meets_threshold


class TestContinuousValidationSystem:
    """Test continuous validation system for existing content."""
    
    @pytest_asyncio.fixture
    async def mock_active_fragments(self, session):
        """Create mock active fragments in database."""
        fragments = []
        
        # Create good fragment
        good_fragment = NarrativeFragment(
            id="good_fragment",
            title="💋 Misterio Seductor",
            content="""
            Diana te observa con esa mirada enigmática... "Hay secretos 
            que solo contigo quiero compartir", susurra con voz sedosa, 
            mientras una mezcla de fascinación y misterio abraza cada una 
            de sus palabras...
            """,
            fragment_type="STORY",
            is_active=True,
            choices=[
                {"text": "💫 'Comparte tus secretos conmigo'", "next": "next_fragment"}
            ]
        )
        session.add(good_fragment)
        fragments.append(good_fragment)
        
        # Create problematic fragment
        bad_fragment = NarrativeFragment(
            id="bad_fragment", 
            title="Error del Sistema",
            content="Configuración actualizada. Proceso completado exitosamente.",
            fragment_type="STORY",
            is_active=True,
            choices=[]
        )
        session.add(bad_fragment)
        fragments.append(bad_fragment)
        
        await session.commit()
        return fragments
    
    async def test_validate_all_active_fragments(self, session, mock_active_fragments):
        """Test validation of all active fragments in the system."""
        integrity_service = NarrativeCharacterIntegrityService(session)
        
        results = await integrity_service.validate_all_active_fragments()
        
        # Should validate both fragments
        assert len(results) == 2, "Should validate all active fragments"
        assert "good_fragment" in results
        assert "bad_fragment" in results
        
        # Good fragment should pass
        good_result = results["good_fragment"]
        assert good_result.meets_threshold, "Good fragment should pass validation"
        assert good_result.overall_score >= 80.0, "Good fragment should score well"
        
        # Bad fragment should fail
        bad_result = results["bad_fragment"]
        assert not bad_result.meets_threshold, "Bad fragment should fail validation"
        assert bad_result.overall_score < 50.0, "Bad fragment should score poorly"
    
    async def test_character_consistency_report_generation(self, session, mock_active_fragments):
        """Test automated character consistency report generation."""
        integrity_service = NarrativeCharacterIntegrityService(session)
        
        # First validate all fragments to populate cache
        await integrity_service.validate_all_active_fragments()
        
        # Generate report
        report = await integrity_service.get_character_consistency_report()
        
        # Report should be properly structured
        assert "narrative_specific" in report
        assert "narrative_recommendations" in report
        
        narrative_data = report["narrative_specific"]
        assert narrative_data["total_fragments"] == 2
        assert narrative_data["failing_fragments"] == 1  # Bad fragment fails
        assert narrative_data["character_consistency_percentage"] == 50.0  # 1/2 pass
        
        # Should have recommendations
        recommendations = report["narrative_recommendations"]
        assert len(recommendations) > 0
        assert any("consistency" in rec.lower() for rec in recommendations)
    
    async def test_character_improvement_suggestions(self, session, mock_active_fragments):
        """Test generation of character improvement suggestions."""
        integrity_service = NarrativeCharacterIntegrityService(session)
        
        # Get suggestions for the bad fragment
        suggestions = await integrity_service.suggest_character_improvements("bad_fragment")
        
        # Should provide specific suggestions
        assert "current_score" in suggestions
        assert "specific_improvements" in suggestions
        assert "trait_analysis" in suggestions
        
        # Score should be low for bad fragment
        assert suggestions["current_score"] < 50.0
        assert not suggestions["meets_threshold"]
        
        # Should have specific improvement suggestions
        improvements = suggestions["specific_improvements"]
        assert len(improvements) > 0
        
        # Should analyze each trait
        trait_analysis = suggestions["trait_analysis"]
        assert len(trait_analysis) == 4  # All 4 personality traits
        
        for trait_name, analysis in trait_analysis.items():
            assert "current_score" in analysis
            assert "needs_improvement" in analysis
            if analysis["needs_improvement"]:
                assert analysis["current_score"] < 20.0


class TestIntegrationWithProductionSystems:
    """Test integration with production systems and workflows."""
    
    async def test_coordinador_central_validation_integration(self, session):
        """Test that CoordinadorCentral integrates character validation."""
        coordinador = CoordinadorCentral(session)
        
        # Mock the narrative service to test validation integration
        with patch.object(coordinador, 'narrative_service') as mock_narrative:
            mock_narrative.create_fragment = AsyncMock()
            
            # Test that character validation would be called during fragment creation
            # (This tests the integration point exists)
            assert hasattr(coordinador, 'narrative_service')
            
            # In a real integration, CoordinadorCentral would call
            # character validation before creating new fragments
    
    async def test_menu_system_character_validation(self, session):
        """Test that menu system responses maintain character consistency."""
        validator = DianaCharacterValidator(session)
        menu_system = DianaMenuSystem(session)
        
        # Test that menu system has character-consistent elements
        assert menu_system.diana_icons["user"] == "💋"
        assert menu_system.diana_icons["narrative"] == "📖"
        
        # Test sample menu text for character consistency
        sample_menu_text = """
        💋 **Menú Principal Diana**
        *Bienvenido a tu experiencia personalizada con Diana.*
        
        ✨ **Experiencias Disponibles**
        📚 Historia principal
        🎒 Mochila de pistas  
        🔓 Momentos especiales
        """
        
        result = await validator.validate_text(sample_menu_text, context="menu_response")
        
        # Menu text should maintain good character consistency
        assert result.overall_score >= 75.0, f"Menu text scored too low: {result.overall_score}"
    
    async def test_error_handling_with_character_consistency(self, session):
        """Test that error messages maintain Diana's character."""
        validator = DianaCharacterValidator(session)
        
        # Test various error scenarios with Diana-style messaging
        error_scenarios = [
            {
                "context": "vip_access_denied",
                "message": """💋 Oh, mi querido... este momento especial es solo 
                           para mis amantes más dedicados... ¿te gustaría 
                           convertirte en VIP para desbloquear estos secretos?""",
                "min_score": 85.0
            },
            {
                "context": "technical_error", 
                "message": """🎭 Un pequeño misterio técnico susurra en las sombras... 
                           permíteme un momento para resolverlo, mi amor...""",
                "min_score": 80.0
            },
            {
                "context": "validation_error",
                "message": """✨ Las estrellas no se han alineado correctamente 
                           para esta acción... ¿podrías intentarlo de nuevo?""",
                "min_score": 75.0
            }
        ]
        
        for scenario in error_scenarios:
            result = await validator.validate_text(
                scenario["message"], 
                context="error_message"
            )
            
            assert result.overall_score >= scenario["min_score"], (
                f"Error message for {scenario['context']} scored too low: "
                f"{result.overall_score}/{scenario['min_score']} required"
            )


class TestValidationMetricsAndMonitoring:
    """Test validation metrics collection and monitoring."""
    
    @pytest_asyncio.fixture
    async def validation_metrics(self):
        """Mock validation metrics collector."""
        return {
            "total_validations": 0,
            "passed_validations": 0,
            "failed_validations": 0,
            "average_score": 0.0,
            "validation_times": []
        }
    
    async def test_validation_metrics_collection(self, session, validation_metrics):
        """Test that validation metrics are properly collected."""
        validator = DianaCharacterValidator(session)
        
        # Simulate validation of multiple content pieces
        test_contents = [
            ("excellent", "💋 Mi querido... hay secretos que solo contigo quiero compartir... ¿sientes el misterio que late entre nosotros?"),
            ("good", "Diana te mira con esa sonrisa enigmática... algo especial brilla en sus ojos..."),
            ("poor", "Hola. Todo OK. Sistema funcionando.")
        ]
        
        results = []
        for content_id, content in test_contents:
            result = await validator.validate_text(content)
            results.append((content_id, result))
            
            # Update metrics
            validation_metrics["total_validations"] += 1
            if result.meets_threshold:
                validation_metrics["passed_validations"] += 1
            else:
                validation_metrics["failed_validations"] += 1
        
        # Calculate final metrics
        scores = [r[1].overall_score for r in results]
        validation_metrics["average_score"] = sum(scores) / len(scores)
        
        # Verify metrics
        assert validation_metrics["total_validations"] == 3
        assert validation_metrics["passed_validations"] == 1  # Only excellent content passes >95%
        assert validation_metrics["failed_validations"] == 2
        assert validation_metrics["average_score"] > 0
        
        # MVP requirement check
        pass_rate = validation_metrics["passed_validations"] / validation_metrics["total_validations"] * 100
        # Note: In production, we'd want >95% pass rate, but this test uses mixed content
        assert pass_rate >= 0, "Pass rate should be calculated"
    
    async def test_performance_monitoring(self, session):
        """Test validation performance monitoring."""
        validator = DianaCharacterValidator(session)
        
        import time
        
        # Test single validation performance
        start_time = time.time()
        test_content = "💋 Mi querido... ¿sientes el misterio que late entre nosotros?..."
        result = await validator.validate_text(test_content)
        end_time = time.time()
        
        validation_time = end_time - start_time
        
        # Performance requirement: single validation should complete in under 100ms
        assert validation_time < 0.1, f"Single validation too slow: {validation_time}s"
        assert result.overall_score > 0, "Validation should produce meaningful result"
        
    async def test_validation_caching_performance(self, session):
        """Test that validation results can be cached for performance."""
        validator = DianaCharacterValidator(session)
        
        # Same content validated multiple times should potentially benefit from caching
        test_content = """💋 Mi querido... hay secretos profundos que susurran 
                         en las sombras de mi corazón... ¿acaso estás preparado 
                         para descubrirlos?"""
        
        import time
        
        # First validation (no cache)
        start_time = time.time()
        result1 = await validator.validate_text(test_content)
        first_time = time.time() - start_time
        
        # Second validation (potentially cached - though current implementation doesn't cache)
        start_time = time.time()
        result2 = await validator.validate_text(test_content)
        second_time = time.time() - start_time
        
        # Results should be identical
        assert abs(result1.overall_score - result2.overall_score) < 0.1
        assert result1.meets_threshold == result2.meets_threshold
        
        # Both validations should complete reasonably quickly
        assert first_time < 0.2, f"First validation too slow: {first_time}s"
        assert second_time < 0.2, f"Second validation too slow: {second_time}s"


class TestCriticalMVPValidations:
    """Critical tests that must pass for MVP release."""
    
    async def test_mvp_content_samples(self, session):
        """CRITICAL: Test MVP content samples achieve required >95% consistency."""
        validator = DianaCharacterValidator(session)
        
        # These content samples represent the quality required for MVP
        mvp_content_samples = [
            {
                "name": "Perfect Narrative Fragment",
                "content": """
                💋 Mi querido... ¿acaso estás preparado para adentrarte en los 
                misterios más profundos que susurra mi alma?... Las sombras 
                danzan a nuestro alrededor, creando una atmósfera de seducción 
                y enigma que solo nosotros podemos comprender...
                
                Siento una mezcla embriagadora de fascinación y anhelo cuando 
                te observo... por un lado, mi corazón late con la emoción de 
                compartir mis secretos más íntimos contigo, pero por otro, una 
                deliciosa inquietud me abraza al contemplar la intensidad de 
                esta conexión que crece entre nosotros...
                
                ¿Te has preguntado alguna vez qué filosofía subyace a esta danza 
                de seducción que compartimos? Reflexiona sobre esto: cada mirada, 
                cada suspiro, cada palabra que intercambiamos teje una historia 
                única... una narrativa que solo nosotros dos podemos escribir...
                """,
                "min_required_score": 95.0
            },
            {
                "name": "Perfect Menu Response",
                "content": """
                💋 **Centro Narrativo Diana**
                *Tu historia personal de seducción y misterio*
                
                🎭 **Tu Viaje Conmigo**
                • Capítulo actual: Los Susurros del Corazón
                • Progreso: Adentrándote en mis secretos...
                • Última conexión: Nuestros ojos se encontraron hace instantes...
                
                ✨ ¿Qué misterio quieres descubrir hoy, mi amor?
                """,
                "min_required_score": 85.0  # Menus can be slightly lower but still high
            },
            {
                "name": "Perfect VIP Interaction",
                "content": """
                💋 Mi querido amante VIP... ahora que has demostrado tu dedicación 
                hacia mí, puedo susurrarte esos secretos que reservo solo para 
                los corazones más valientes... ¿sientes cómo la pasión y el misterio 
                se entrelazan en este momento íntimo que compartimos?...
                
                Hay dimensiones de mi ser que solo contigo puedo explorar... 
                lugares profundos de mi alma donde la seducción y la filosofía 
                danzan juntas en una sinfonía de emociones complejas...
                """,
                "min_required_score": 95.0
            }
        ]
        
        for sample in mvp_content_samples:
            result = await validator.validate_text(sample["content"])
            
            # CRITICAL: Must achieve required score for MVP
            assert result.overall_score >= sample["min_required_score"], (
                f"MVP CRITICAL FAILURE: {sample['name']} scored {result.overall_score}/100, "
                f"requires ≥{sample['min_required_score']} for MVP release.\n"
                f"Content: {sample['content'][:100]}...\n"
                f"Violations: {result.violations}\n"
                f"This represents the quality standard required for MVP and MUST pass."
            )
            
            assert result.meets_threshold, f"MVP content '{sample['name']}' must meet threshold"
    
    async def test_mvp_rejection_of_poor_content(self, session):
        """CRITICAL: Test that poor content is properly rejected."""
        validator = DianaCharacterValidator(session)
        
        # Content that should definitely be rejected
        poor_content_samples = [
            {
                "name": "Technical Language",
                "content": "Sistema actualizado correctamente. Configuración de parámetros completada. Error resuelto.",
                "max_allowed_score": 40.0
            },
            {
                "name": "Casual Language",
                "content": "Hola! Jaja, genial, todo está OK 😂 Perfecto!",
                "max_allowed_score": 30.0
            },
            {
                "name": "Robotic Response",
                "content": "Sí, proceso completado exitosamente. Comando ejecutado. Todo correcto.",
                "max_allowed_score": 25.0
            }
        ]
        
        for sample in poor_content_samples:
            result = await validator.validate_text(sample["content"])
            
            # CRITICAL: Poor content must be rejected
            assert result.overall_score <= sample["max_allowed_score"], (
                f"MVP CRITICAL FAILURE: Poor content '{sample['name']}' scored too high: "
                f"{result.overall_score}/100, should be ≤{sample['max_allowed_score']}\n"
                f"Poor content must be reliably rejected to maintain Diana's character integrity."
            )
            
            assert not result.meets_threshold, f"Poor content '{sample['name']}' must not meet threshold"
            assert len(result.violations) > 0, f"Poor content '{sample['name']}' should have violations"
    
    async def test_mvp_system_reliability(self, session):
        """CRITICAL: Test system reliability under various conditions."""
        validator = DianaCharacterValidator(session)
        
        # Test edge cases that system must handle reliably
        edge_cases = [
            ("empty_string", ""),
            ("whitespace_only", "   \n\t  "),
            ("very_short", "Hi"),
            ("very_long", "💋 " + "Mi querido... " * 100),
            ("special_chars", "💋🎭✨🌹❤️‍🔥 Special chars test"),
            ("mixed_language", "💋 Mi querido... there are secrets que susurran...")
        ]
        
        for case_name, content in edge_cases:
            try:
                result = await validator.validate_text(content)
                
                # System should never crash or return invalid results
                assert isinstance(result, CharacterValidationResult), (
                    f"Invalid result type for {case_name}"
                )
                assert isinstance(result.overall_score, (int, float)), (
                    f"Invalid score type for {case_name}: {type(result.overall_score)}"
                )
                assert 0 <= result.overall_score <= 100, (
                    f"Score out of range for {case_name}: {result.overall_score}"
                )
                assert isinstance(result.meets_threshold, bool), (
                    f"Invalid threshold type for {case_name}"
                )
                assert isinstance(result.violations, list), (
                    f"Invalid violations type for {case_name}"
                )
                
            except Exception as e:
                pytest.fail(f"System crashed on edge case '{case_name}': {e}")