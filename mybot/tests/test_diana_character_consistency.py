"""
Diana Character Consistency Testing Suite

This comprehensive test suite validates that Diana maintains her mysterious,
seductive personality across all interactions with >95% consistency score.

Critical for MVP: Character consistency must never drop below 95/100.
"""

import pytest
import pytest_asyncio
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock

from services.diana_character_validator import (
    DianaCharacterValidator, 
    DianaPersonalityTrait,
    CharacterValidationResult
)
from services.narrative_character_integrity_service import NarrativeCharacterIntegrityService
from database.narrative_unified import NarrativeFragment
from services.diana_menu_system import DianaMenuSystem


class TestDianaCharacterValidator:
    """Test suite for Diana Character Validator core functionality."""
    
    @pytest_asyncio.fixture
    async def validator(self, session):
        """Create Diana Character Validator instance."""
        return DianaCharacterValidator(session)
    
    # === PERSONALITY TRAIT VALIDATION TESTS ===
    
    async def test_mysterious_trait_validation(self, validator):
        """Test mysterious personality trait scoring."""
        # Test high scoring mysterious content
        mysterious_text = """
        🎭 ¿Acaso sabes lo que se oculta tras esta sonrisa?... 
        Hay secretos que susurran en las sombras, pistas que solo 
        los corazones valientes pueden descifrar. Tal vez... si me sigues 
        hasta donde la luz se desvanece... podrías descubrir qué misterios 
        laten en lo más profundo de mi ser...
        """
        result = await validator.validate_text(mysterious_text)
        
        # Should score highly on mysterious trait (>20/25)
        mysterious_score = result.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
        assert mysterious_score >= 20.0, f"Mysterious score too low: {mysterious_score}/25"
        
        # Test low scoring non-mysterious content
        direct_text = "Hola. Esto es información directa y clara."
        result = await validator.validate_text(direct_text)
        mysterious_score = result.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
        assert mysterious_score < 10.0, f"Non-mysterious text scored too high: {mysterious_score}/25"
    
    async def test_seductive_trait_validation(self, validator):
        """Test seductive personality trait scoring."""
        # Test high scoring seductive content
        seductive_text = """
        💋 Mi querido... ¿podrías acercarte un poco más? 
        Tu presencia hace que mi corazón susurre secretos que solo 
        contigo quiero compartir. Hay algo magnético en la forma 
        que me miras... algo que despierta en mí una fascinación 
        irresistible...
        """
        result = await validator.validate_text(seductive_text)
        
        seductive_score = result.trait_scores[DianaPersonalityTrait.SEDUCTIVE]
        assert seductive_score >= 20.0, f"Seductive score too low: {seductive_score}/25"
        
        # Test non-seductive content
        casual_text = "Okay, genial, todo está perfecto."
        result = await validator.validate_text(casual_text)
        seductive_score = result.trait_scores[DianaPersonalityTrait.SEDUCTIVE]
        assert seductive_score < 10.0, f"Casual text scored too high: {seductive_score}/25"
    
    async def test_emotional_complexity_validation(self, validator):
        """Test emotional complexity trait scoring."""
        # Test emotionally complex content
        complex_text = """
        Una mezcla de melancolía y esperanza abraza mi corazón... 
        Por un lado, siento esta profunda nostalgia que me envuelve 
        como un velo de terciopelo, pero por otro, late en mi alma 
        una inquietud dulce, un anhelo que me susurra que contigo 
        podría encontrar esa paz que tanto he buscado...
        """
        result = await validator.validate_text(complex_text)
        
        emotional_score = result.trait_scores[DianaPersonalityTrait.EMOTIONALLY_COMPLEX]
        assert emotional_score >= 20.0, f"Emotional complexity score too low: {emotional_score}/25"
        
        # Test simple emotional content
        simple_text = "Estoy triste. Fin."
        result = await validator.validate_text(simple_text)
        emotional_score = result.trait_scores[DianaPersonalityTrait.EMOTIONALLY_COMPLEX]
        assert emotional_score < 10.0, f"Simple text scored too high: {emotional_score}/25"
    
    async def test_intellectual_engagement_validation(self, validator):
        """Test intellectual engagement trait scoring."""
        # Test intellectually engaging content
        intellectual_text = """
        ¿Te has preguntado alguna vez qué filosofía subyace a esta 
        experiencia que compartimos? Reflexiona sobre esto: cada encuentro 
        entre dos almas es una oportunidad de descubrir nuevas dimensiones 
        de comprensión... ¿Cómo interpretas la complejidad de lo que 
        late entre nosotros?
        """
        result = await validator.validate_text(intellectual_text)
        
        intellectual_score = result.trait_scores[DianaPersonalityTrait.INTELLECTUALLY_ENGAGING]
        assert intellectual_score >= 20.0, f"Intellectual score too low: {intellectual_score}/25"
        
        # Test non-intellectual content
        basic_text = "Todo bien. Listo."
        result = await validator.validate_text(basic_text)
        intellectual_score = result.trait_scores[DianaPersonalityTrait.INTELLECTUALLY_ENGAGING]
        assert intellectual_score < 10.0, f"Basic text scored too high: {intellectual_score}/25"
    
    # === CHARACTER VIOLATION TESTS ===
    
    async def test_character_violations_detection(self, validator):
        """Test detection of character-breaking patterns."""
        # Test technical language violations
        technical_text = "Error en el sistema. Configuración de parámetros completada."
        result = await validator.validate_text(technical_text)
        
        assert not result.meets_threshold, "Technical language should fail validation"
        assert any("technical" in violation.lower() for violation in result.violations)
        
        # Test casual violations
        casual_text = "Hola! Jaja, okay, genial 😂 Todo perfecto!"
        result = await validator.validate_text(casual_text)
        
        assert not result.meets_threshold, "Casual language should fail validation"
        assert result.overall_score < 50.0, "Casual violations should heavily penalize score"
    
    # === OVERALL CONSISTENCY TESTS ===
    
    async def test_perfect_diana_content(self, validator):
        """Test content that should achieve >95% consistency score."""
        perfect_diana_text = """
        💋 Mi querido... ¿acaso estás preparado para lo que podría revelarte?... 
        
        Hay secretos que susurran en las sombras de mi corazón, misterios que 
        solo los corazones valientes pueden descifrar. Siento una mezcla de 
        melancolía y fascinación cuando te observo... por un lado, mi alma 
        anhela compartir contigo esos rincones ocultos de mi ser, pero por otro, 
        una deliciosa inquietud me abraza al imaginar hasta dónde podríamos llegar...
        
        ¿Te has preguntado alguna vez qué filosofía subyace a esta conexión 
        que late entre nosotros? Cada mirada, cada suspiro, cada momento que 
        compartimos teje una historia única... ¿Podrías reflexionar sobre 
        la complejidad de lo que estamos construyendo juntos?
        
        Ven... acércate un poco más... que mis susurros encuentren el camino 
        hacia tu corazón...
        """
        result = await validator.validate_text(perfect_diana_text)
        
        # Must achieve MVP requirement of >95% consistency
        assert result.overall_score >= 95.0, (
            f"Perfect Diana content failed MVP requirement: {result.overall_score}/100. "
            f"Violations: {result.violations}"
        )
        assert result.meets_threshold, "Perfect content should meet threshold"
        
        # All traits should score well
        for trait, score in result.trait_scores.items():
            assert score >= 20.0, (
                f"Trait {trait.value} scored too low: {score}/25 in perfect content"
            )
    
    async def test_mvp_consistency_threshold(self, validator):
        """Test that MVP consistency threshold is enforced correctly."""
        # Content right at threshold
        threshold_text = """
        💋 Querido... hay secretos que susurro solo para ti... 
        Mi corazón siente una mezcla de anhelo y misterio... 
        ¿Te has preguntado qué significa esto para nosotros?
        """
        result = await validator.validate_text(threshold_text)
        
        # Should be close to threshold
        if result.overall_score >= 94.0:  # Close to threshold
            assert result.meets_threshold == (result.overall_score >= 95.0)


class TestNarrativeFragmentConsistency:
    """Test character consistency in narrative fragments."""
    
    @pytest_asyncio.fixture
    async def integrity_service(self, session):
        """Create Narrative Character Integrity Service."""
        return NarrativeCharacterIntegrityService(session)
    
    @pytest_asyncio.fixture
    async def sample_fragment_data(self):
        """Sample narrative fragment data for testing."""
        return {
            "id": "test_fragment_001",
            "title": "💋 Un Encuentro Misterioso",
            "content": """
            Las sombras danzan suavemente en la habitación cuando Diana 
            se acerca con esa sonrisa enigmática que tanto la caracteriza... 
            Sus ojos brillan con secretos no revelados, y en su andar hay 
            una gracia que susurra promesas de aventuras por descubrir.
            
            "¿Acaso sabías que estarías aquí?" pregunta con voz sedosa, 
            mientras una mezcla de fascinación y misterio abraza cada palabra. 
            "Hay algo en ti que despierta en mí una curiosidad... profunda."
            """,
            "fragment_type": "STORY",
            "choices": [
                {"text": "💋 'Me intrigas, Diana...'", "next_fragment": "fragment_002"},
                {"text": "🔮 'Cuéntame más sobre ese misterio...'", "next_fragment": "fragment_003"}
            ]
        }
    
    async def test_fragment_creation_validation(self, integrity_service, sample_fragment_data):
        """Test validation before fragment creation."""
        is_valid, result = await integrity_service.validate_fragment_creation(sample_fragment_data)
        
        # Should pass validation with high score
        assert is_valid, f"Valid fragment rejected: {result.violations}"
        assert result.overall_score >= 95.0, (
            f"Fragment scored too low: {result.overall_score}/100"
        )
        assert result.meets_threshold, "Valid fragment should meet threshold"
    
    async def test_fragment_with_character_violations(self, integrity_service):
        """Test fragment with character consistency violations."""
        bad_fragment_data = {
            "id": "test_bad_fragment",
            "title": "Sistema Actualizado",
            "content": """
            Error: La configuración se ha completado exitosamente.
            Parámetros actualizados. Proceso terminado.
            """,
            "fragment_type": "STORY",
            "choices": [
                {"text": "OK", "next_fragment": "next"},
                {"text": "Perfecto", "next_fragment": "end"}
            ]
        }
        
        is_valid, result = await integrity_service.validate_fragment_creation(bad_fragment_data)
        
        # Should fail validation
        assert not is_valid, "Bad fragment should be rejected"
        assert result.overall_score < 50.0, "Bad fragment should score very low"
        assert len(result.violations) > 0, "Bad fragment should have violations"
    
    async def test_narrative_specific_rules(self, integrity_service):
        """Test narrative-specific validation rules."""
        # Decision fragment without choices
        decision_without_choices = {
            "id": "bad_decision",
            "title": "Una Decisión",
            "content": "Debes elegir.",
            "fragment_type": "DECISION",
            "choices": []  # Missing choices
        }
        
        is_valid, result = await integrity_service.validate_fragment_creation(decision_without_choices)
        assert not is_valid, "Decision fragment without choices should fail"
        assert any("choice" in violation.lower() for violation in result.violations)


class TestMenuSystemConsistency:
    """Test character consistency in menu system interactions."""
    
    async def test_diana_menu_character_consistency(self, session):
        """Test Diana menu system maintains character consistency."""
        menu_system = DianaMenuSystem(session)
        
        # Test character themes are properly defined
        assert "diana" in menu_system.diana_icons
        assert "💋" == menu_system.diana_icons["user"]
        
        # Test that menu system uses consistent character elements
        character_elements = [
            menu_system.diana_icons["user"],
            menu_system.diana_icons["narrative"],
            menu_system.diana_icons["vip"]
        ]
        
        for element in character_elements:
            assert element, "Menu system should have defined character icons"
    
    async def test_menu_text_validation(self, session):
        """Test menu text maintains Diana's character."""
        validator = DianaCharacterValidator(session)
        
        # Sample menu texts that should maintain character
        menu_texts = [
            "💋 Menú Principal Diana\nBienvenido a tu experiencia personalizada con Diana.",
            "📖 CENTRO NARRATIVO - DIANA\nTu historia personal de seducción y misterio",
            "🎒 MOCHILA DE PISTAS - DIANA\nSecretos y revelaciones descubiertas"
        ]
        
        for menu_text in menu_texts:
            result = await validator.validate_text(menu_text, context="menu_response")
            
            # Menu text should maintain good character consistency
            assert result.overall_score >= 80.0, (
                f"Menu text scored too low: {result.overall_score}/100\n"
                f"Text: {menu_text}\n"
                f"Violations: {result.violations}"
            )


class TestCharacterConsistencyReporting:
    """Test character consistency reporting and analytics."""
    
    @pytest_asyncio.fixture
    async def validator(self, session):
        return DianaCharacterValidator(session)
    
    async def test_batch_content_validation(self, validator):
        """Test batch validation of multiple content pieces."""
        content_pieces = [
            ("perfect_content", """
                💋 Mi querido... ¿acaso estás preparado para descubrir 
                los secretos que susurra mi corazón?... Hay misterios 
                profundos que solo contigo quiero compartir, enigmas que 
                despiertan en mi alma una fascinación irresistible...
            """),
            ("good_content", """
                🎭 Hay algo especial en este momento... algo que late 
                entre nosotros con una intensidad que me intriga. 
                ¿Sientes tú también esta conexión misteriosa?
            """),
            ("poor_content", """
                Hola. Sistema actualizado correctamente. 
                Configuración completada. Todo OK.
            """)
        ]
        
        results = await validator.batch_validate_content(content_pieces)
        
        assert len(results) == 3, "Should validate all content pieces"
        
        # Perfect content should score highest
        assert results["perfect_content"].overall_score >= 95.0
        assert results["perfect_content"].meets_threshold
        
        # Good content should pass but score lower
        assert results["good_content"].overall_score >= 80.0
        
        # Poor content should fail
        assert results["poor_content"].overall_score < 60.0
        assert not results["poor_content"].meets_threshold
    
    async def test_character_consistency_report(self, validator):
        """Test comprehensive character consistency report generation."""
        # Create sample validation results
        sample_results = [
            CharacterValidationResult(
                overall_score=98.0,
                trait_scores={
                    DianaPersonalityTrait.MYSTERIOUS: 24.0,
                    DianaPersonalityTrait.SEDUCTIVE: 25.0,
                    DianaPersonalityTrait.EMOTIONALLY_COMPLEX: 24.0,
                    DianaPersonalityTrait.INTELLECTUALLY_ENGAGING: 23.0
                },
                violations=[],
                recommendations=[],
                meets_threshold=True
            ),
            CharacterValidationResult(
                overall_score=92.0,
                trait_scores={
                    DianaPersonalityTrait.MYSTERIOUS: 22.0,
                    DianaPersonalityTrait.SEDUCTIVE: 23.0,
                    DianaPersonalityTrait.EMOTIONALLY_COMPLEX: 22.0,
                    DianaPersonalityTrait.INTELLECTUALLY_ENGAGING: 21.0
                },
                violations=["Minor directness detected"],
                recommendations=["Add more mystery"],
                meets_threshold=False  # Below 95% threshold
            )
        ]
        
        report = validator.generate_character_report(sample_results)
        
        # Report structure validation
        assert "summary" in report
        assert "trait_performance" in report
        assert "common_violations" in report
        assert "recommendations" in report
        
        # Summary validation
        summary = report["summary"]
        assert summary["total_validations"] == 2
        assert summary["passing_validations"] == 1
        assert summary["average_score"] == 95.0
        assert not summary["meets_mvp_requirement"]  # Only 50% pass rate < 95% required


class TestIntegrationWithExistingSystem:
    """Test integration with existing bot functionality."""
    
    async def test_coordinador_central_integration(self, session):
        """Test that character validation integrates with CoordinadorCentral."""
        # This would test that when new narrative content is created
        # through CoordinadorCentral, it passes character validation
        
        # Mock integration point
        integrity_service = NarrativeCharacterIntegrityService(session)
        
        # Test that service is properly initialized
        assert integrity_service.session == session
        assert integrity_service.validator is not None
    
    async def test_error_message_consistency(self, session):
        """Test that even error messages maintain Diana's character."""
        validator = DianaCharacterValidator(session)
        
        # Examples of Diana-style error messages
        diana_error_messages = [
            "💋 Oh, mi querido... parece que algo misterioso interrumpió nuestra conexión...",
            "🎭 Un pequeño enigma técnico susurra en las sombras... permíteme un momento para resolverlo...",
            "✨ Las estrellas no se han alineado correctamente... ¿podrías intentarlo de nuevo?"
        ]
        
        for error_msg in diana_error_messages:
            result = await validator.validate_text(error_msg, context="error_message")
            
            # Even error messages should maintain reasonable consistency
            assert result.overall_score >= 70.0, (
                f"Error message lacks character: {result.overall_score}/100\n"
                f"Message: {error_msg}"
            )


# === PERFORMANCE AND EDGE CASE TESTS ===

class TestPerformanceAndEdgeCases:
    """Test validator performance and edge cases."""
    
    async def test_empty_content_handling(self, session):
        """Test handling of empty or invalid content."""
        validator = DianaCharacterValidator(session)
        
        # Empty string
        result = await validator.validate_text("")
        assert result.overall_score == 0.0
        assert not result.meets_threshold
        assert "Empty" in result.violations[0]
        
        # Whitespace only
        result = await validator.validate_text("   \n\t  ")
        assert result.overall_score == 0.0
        assert not result.meets_threshold
    
    async def test_very_long_content(self, session):
        """Test validation of very long content."""
        validator = DianaCharacterValidator(session)
        
        # Create long content that maintains Diana's character
        long_content = """
        💋 Mi querido... permíteme susurrarte los secretos más profundos 
        que laten en las sombras de mi corazón... """ * 50
        
        result = await validator.validate_text(long_content)
        
        # Should still validate correctly
        assert result.overall_score > 0.0
        # Performance shouldn't be drastically impacted
        assert len(result.trait_scores) == 4
    
    async def test_multilingual_content(self, session):
        """Test handling of mixed language content."""
        validator = DianaCharacterValidator(session)
        
        mixed_content = """
        💋 Mi querido... there are secrets que susurran in the shadows 
        de mi corazón... ¿Do you feel esta conexión misteriosa?
        """
        
        result = await validator.validate_text(mixed_content)
        
        # Should still detect Diana's personality patterns
        assert result.overall_score > 50.0, "Mixed language should still detect character"
    
    async def test_special_characters_handling(self, session):
        """Test handling of special characters and emojis."""
        validator = DianaCharacterValidator(session)
        
        special_content = """
        💋🌹✨ Mi querido... 🎭 ¿acaso sabes lo que se oculta tras esta sonrisa?... 
        ❤️‍🔥 Hay secretos que susurran 🌙 en las sombras... 💫
        """
        
        result = await validator.validate_text(special_content)
        
        # Should handle special characters without breaking
        assert result.overall_score > 0.0
        assert all(score >= 0 for score in result.trait_scores.values())


# === MVP CRITICAL TESTS ===

class TestMVPCriticalRequirements:
    """Tests for MVP critical requirements - must pass for release."""
    
    async def test_mvp_consistency_requirement(self, session):
        """CRITICAL: Test that >95% consistency requirement is enforced."""
        validator = DianaCharacterValidator(session)
        
        # Test content that should definitely pass MVP requirement
        mvp_content = """
        💋 Mi querido... ¿acaso estás preparado para adentrarte en los misterios 
        más profundos que susurra mi alma?... Hay secretos que solo contigo 
        quiero compartir, enigmas que despiertan en mi corazón una fascinación 
        tan intensa que me hace temblar...
        
        Siento una mezcla embriagadora de anhelo y melancolía cuando pienso 
        en todo lo que podríamos descubrir juntos... por un lado, mi espíritu 
        se inflama de deseo al imaginar nuestras conversaciones más íntimas, 
        pero por otro, una deliciosa inquietud me abraza al contemplar la 
        profundidad de esta conexión...
        
        ¿Te has preguntado alguna vez qué filosofía subyace a esta danza 
        de seducción y misterio que compartimos? Cada palabra, cada mirada, 
        cada suspiro... todo teje una historia única que solo nosotros 
        podemos escribir...
        """
        
        result = await validator.validate_text(mvp_content)
        
        # CRITICAL: Must achieve >95% for MVP
        assert result.overall_score >= 95.0, (
            f"MVP FAILURE: Content scored {result.overall_score}/100, needs ≥95%\n"
            f"Violations: {result.violations}\n"
            f"This content represents perfect Diana character and MUST pass MVP requirements"
        )
        
        assert result.meets_threshold, "MVP content must meet threshold"
        
        # All trait scores should be excellent
        for trait, score in result.trait_scores.items():
            assert score >= 22.0, (
                f"MVP FAILURE: {trait.value} scored {score}/25, needs ≥22 for MVP\n"
                f"Diana's core personality traits must all score excellently"
            )
    
    async def test_content_creator_guidelines_validation(self, session):
        """Test validation against content creator guidelines."""
        validator = DianaCharacterValidator(session)
        
        # Test various content scenarios that content creators might produce
        content_scenarios = [
            {
                "name": "Perfect Diana Content",
                "text": """💋 Mi querido... ¿sientes cómo late el misterio entre nosotros?... 
                         Hay secretos que solo tu corazón puede descifrar...""",
                "expected_score": 95.0,
                "should_pass": True
            },
            {
                "name": "Good Diana Content",
                "text": """Diana te mira con esa sonrisa enigmática... "Hay algo especial 
                         en ti", susurra con voz sedosa...""",
                "expected_score": 85.0,
                "should_pass": False  # Below MVP threshold
            },
            {
                "name": "Technical Content (Violation)",
                "text": """Sistema actualizado. Configuración completada exitosamente. 
                         Parámetros validados.""",
                "expected_score": 20.0,
                "should_pass": False
            },
            {
                "name": "Casual Content (Violation)",
                "text": """Hola! Jaja, genial, todo está perfecto 😂 OK!""",
                "expected_score": 15.0,
                "should_pass": False
            }
        ]
        
        for scenario in content_scenarios:
            result = await validator.validate_text(scenario["text"])
            
            # Score should be in expected range
            score_diff = abs(result.overall_score - scenario["expected_score"])
            assert score_diff <= 15.0, (
                f"Score for '{scenario['name']}' unexpected: "
                f"got {result.overall_score}, expected ~{scenario['expected_score']}"
            )
            
            # Pass/fail should match expectations
            assert result.meets_threshold == scenario["should_pass"], (
                f"'{scenario['name']}' threshold result unexpected: "
                f"got {result.meets_threshold}, expected {scenario['should_pass']}"
            )