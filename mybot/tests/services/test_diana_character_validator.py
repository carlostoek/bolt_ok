"""
Comprehensive tests for Diana Character Consistency Validation Framework.

These tests ensure the character validation system correctly identifies
Diana's personality traits and maintains >95% consistency scoring.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from services.diana_character_validator import (
    DianaCharacterValidator,
    DianaPersonalityTrait,
    CharacterValidationResult,
    validate_diana_character
)

class TestDianaCharacterValidator:
    """Test suite for Diana character consistency validation."""
    
    @pytest_asyncio.fixture
    async def validator(self, session):
        """Create validator instance for testing."""
        return DianaCharacterValidator(session)
    
    @pytest_asyncio.fixture
    def mock_fragment(self):
        """Mock narrative fragment for testing."""
        fragment = MagicMock()
        fragment.title = "Test Fragment"
        fragment.content = "Test content"
        fragment.choices = [
            {"text": "Test choice", "points": 10}
        ]
        return fragment

    class TestMysterious:
        """Test mysterious personality trait validation."""
        
        @pytest.mark.asyncio
        async def test_high_mysterious_score(self, validator):
            """Test text with high mysterious quality."""
            text = """
            Los secretos que guardo... ¿acaso sabes lo que realmente significa este lugar?
            Hay más de lo que aparenta, susurra el viento entre las sombras.
            Tal vez, si prestas atención... descubrirás las pistas ocultas.
            """
            result = await validator.validate_text(text)
            
            mysterious_score = result.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
            assert mysterious_score >= 20.0, f"Expected mysterious score >= 20, got {mysterious_score}"
            assert "..." in text  # Confirms ellipsis presence
        
        @pytest.mark.asyncio
        async def test_low_mysterious_score(self, validator):
            """Test text with insufficient mysterious quality."""
            text = "Hola. Esto es un mensaje directo y claro sin misterio."
            result = await validator.validate_text(text)
            
            mysterious_score = result.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
            assert mysterious_score < 10.0, f"Expected low mysterious score, got {mysterious_score}"
            
            # Should have violation for insufficient mystery
            mystery_violations = [v for v in result.violations if "mysterious" in v.lower()]
            assert len(mystery_violations) > 0
        
        @pytest.mark.asyncio 
        async def test_ellipsis_bonus(self, validator):
            """Test bonus points for ellipsis usage."""
            text_without = "Hay secretos en este lugar"
            text_with = "Hay secretos en este lugar..."
            
            result_without = await validator.validate_text(text_without)
            result_with = await validator.validate_text(text_with)
            
            score_without = result_without.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
            score_with = result_with.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
            
            assert score_with > score_without, "Ellipsis should increase mysterious score"

    class TestSeductive:
        """Test seductive personality trait validation."""
        
        @pytest.mark.asyncio
        async def test_high_seductive_score(self, validator):
            """Test text with high seductive quality."""
            text = """
            💋 Mi querido, tu encanto es irresistible...
            Susurra secretos que solo nosotros conocemos, cariño.
            Con una sonrisa fascinante, te invito a descubrir más conmigo.
            """
            result = await validator.validate_text(text)
            
            seductive_score = result.trait_scores[DianaPersonalityTrait.SEDUCTIVE]
            assert seductive_score >= 20.0, f"Expected seductive score >= 20, got {seductive_score}"
        
        @pytest.mark.asyncio
        async def test_seductive_emoji_bonus(self, validator):
            """Test bonus for seductive emoji."""
            text_without = "Tu encanto es irresistible"
            text_with = "💋 Tu encanto es irresistible"
            
            result_without = await validator.validate_text(text_without)
            result_with = await validator.validate_text(text_with)
            
            score_without = result_without.trait_scores[DianaPersonalityTrait.SEDUCTIVE]
            score_with = result_with.trait_scores[DianaPersonalityTrait.SEDUCTIVE]
            
            assert score_with > score_without, "Seductive emoji should increase score"
        
        @pytest.mark.asyncio
        async def test_intimate_language_bonus(self, validator):
            """Test bonus for intimate personal language."""
            text = "Contigo puedo ser yo misma, mi tesoro. Te susurro mi secreto..."
            result = await validator.validate_text(text)
            
            seductive_score = result.trait_scores[DianaPersonalityTrait.SEDUCTIVE]
            assert seductive_score >= 15.0, "Intimate language should score well"

    class TestEmotionalComplexity:
        """Test emotionally complex personality trait validation."""
        
        @pytest.mark.asyncio
        async def test_high_emotional_score(self, validator):
            """Test text with high emotional complexity."""
            text = """
            Mi corazón se debate entre la esperanza y el temor...
            Por un lado siento una profunda melancolía, por otro una inquietud que no puedo explicar.
            Esta contradicción en mi alma me hace vulnerable, pero también más humana.
            """
            result = await validator.validate_text(text)
            
            emotional_score = result.trait_scores[DianaPersonalityTrait.EMOTIONALLY_COMPLEX]
            assert emotional_score >= 18.0, f"Expected emotional score >= 18, got {emotional_score}"
        
        @pytest.mark.asyncio
        async def test_complexity_indicators(self, validator):
            """Test recognition of complexity indicators."""
            text = "Aunque deseo estar cerca, sin embargo me aterra la vulnerabilidad que conlleva."
            result = await validator.validate_text(text)
            
            emotional_score = result.trait_scores[DianaPersonalityTrait.EMOTIONALLY_COMPLEX]
            assert emotional_score >= 10.0, "Complexity indicators should increase score"
        
        @pytest.mark.asyncio
        async def test_simple_emotion_vs_complex(self, validator):
            """Test difference between simple and complex emotional expression."""
            simple_text = "Estoy feliz."
            complex_text = "Una mezcla de alegría y nostalgia invade mi corazón, creando una paradoja emocional."
            
            simple_result = await validator.validate_text(simple_text)
            complex_result = await validator.validate_text(complex_text)
            
            simple_score = simple_result.trait_scores[DianaPersonalityTrait.EMOTIONALLY_COMPLEX]
            complex_score = complex_result.trait_scores[DianaPersonalityTrait.EMOTIONALLY_COMPLEX]
            
            assert complex_score > simple_score, "Complex emotions should score higher"

    class TestIntellectualEngagement:
        """Test intellectually engaging personality trait validation."""
        
        @pytest.mark.asyncio
        async def test_high_intellectual_score(self, validator):
            """Test text with high intellectual engagement."""
            text = """
            ¿Has pensado en la filosofía que subyace a nuestras decisiones?
            Reflexiona sobre esta perspectiva: cada elección revela algo de nuestra sabiduría interior.
            ¿Cómo interpretas el significado profundo de lo que experimentamos juntos?
            """
            result = await validator.validate_text(text)
            
            intellectual_score = result.trait_scores[DianaPersonalityTrait.INTELLECTUALLY_ENGAGING]
            assert intellectual_score >= 18.0, f"Expected intellectual score >= 18, got {intellectual_score}"
        
        @pytest.mark.asyncio
        async def test_question_bonus(self, validator):
            """Test bonus for thought-provoking questions."""
            text_no_questions = "La sabiduría es importante para comprender la vida."
            text_with_questions = "¿Qué es la sabiduría? ¿Cómo la desarrollamos? ¿Por qué es esencial?"
            
            result_no_q = await validator.validate_text(text_no_questions)
            result_with_q = await validator.validate_text(text_with_questions)
            
            score_no_q = result_no_q.trait_scores[DianaPersonalityTrait.INTELLECTUALLY_ENGAGING]
            score_with_q = result_with_q.trait_scores[DianaPersonalityTrait.INTELLECTUALLY_ENGAGING]
            
            assert score_with_q > score_no_q, "Questions should increase intellectual engagement score"
        
        @pytest.mark.asyncio
        async def test_engagement_patterns(self, validator):
            """Test recognition of intellectual engagement patterns."""
            text = "Considera esto: ¿te has preguntado por qué reflexionamos sobre nuestro propósito?"
            result = await validator.validate_text(text)
            
            intellectual_score = result.trait_scores[DianaPersonalityTrait.INTELLECTUALLY_ENGAGING]
            assert intellectual_score >= 12.0, "Engagement patterns should score well"

    class TestCharacterViolations:
        """Test detection of character violations."""
        
        @pytest.mark.asyncio
        async def test_direct_language_violation(self, validator):
            """Test detection of overly direct language."""
            text = "Directamente te digo que esto es obvio. Claramente es la respuesta correcta."
            result = await validator.validate_text(text)
            
            # Should have lower scores due to directness violation
            assert result.overall_score < 50.0, "Direct language should result in low score"
            
            direct_violations = [v for v in result.violations if "direct" in v.lower() or "misterio" in v.lower()]
            assert len(direct_violations) > 0, "Should detect directness violations"
        
        @pytest.mark.asyncio
        async def test_casual_language_violation(self, validator):
            """Test detection of overly casual language."""
            text = "Hola! Okay, genial. Todo perfecto jaja 😀😁"
            result = await validator.validate_text(text)
            
            # Should penalize casual language heavily
            assert result.overall_score < 40.0, "Casual language should result in very low score"
            
            casual_violations = [v for v in result.violations if "casual" in v.lower() or "charm" in v.lower()]
            assert len(casual_violations) > 0, "Should detect casual language violations"
        
        @pytest.mark.asyncio
        async def test_technical_language_violation(self, validator):
            """Test detection of technical language."""
            text = "El sistema configurará los parámetros. Oprima el botón del menú para ajustar settings."
            result = await validator.validate_text(text)
            
            # Technical language should reduce character scores
            assert result.overall_score < 60.0, "Technical language should reduce character consistency"
        
        @pytest.mark.asyncio
        async def test_robotic_response_violation(self, validator):
            """Test detection of robotic responses."""
            text = "Sí, proceso completado. Operación exitosa. Comando ejecutado correctamente."
            result = await validator.validate_text(text)
            
            # Robotic responses should score very poorly
            assert result.overall_score < 30.0, "Robotic responses should score very poorly"

    class TestOverallScoring:
        """Test overall character consistency scoring."""
        
        @pytest.mark.asyncio
        async def test_perfect_diana_text(self, validator):
            """Test text that perfectly embodies Diana's character."""
            text = """
            💋 Mi querido... ¿has sentido alguna vez esa mezcla fascinante de anhelo y misterio?
            Susurro secretos que danzan entre las sombras de tu corazón, mientras mi alma 
            se debate entre revelarte todo... o mantener el velo que hace esto tan seductor.
            
            Reflexiona conmigo: ¿no es acaso la incertidumbre lo que hace que cada momento 
            juntos sea una exploración de emociones profundas? Entre la vulnerabilidad y 
            el encanto, descubrimos quiénes somos realmente...
            """
            result = await validator.validate_text(text)
            
            # Should score very highly (close to perfect)
            assert result.overall_score >= 95.0, f"Perfect Diana text should score >= 95, got {result.overall_score}"
            assert result.meets_threshold, "Perfect text should meet MVP threshold"
            
            # All traits should score well
            for trait, score in result.trait_scores.items():
                assert score >= 20.0, f"Trait {trait} should score >= 20, got {score}"
        
        @pytest.mark.asyncio
        async def test_threshold_requirement(self, validator):
            """Test 95% threshold requirement for MVP."""
            # Text that should just meet the threshold
            good_text = """
            ¿Acaso sabes el secreto que guardo? 💋 Mi corazón se debate entre 
            contarte todo o mantener el misterio... Reflexiona sobre esto, cariño:
            la incertidumbre puede ser tan seductora como la certeza.
            """
            result = await validator.validate_text(good_text)
            
            if result.overall_score >= 95.0:
                assert result.meets_threshold, "Text scoring >= 95 should meet threshold"
            else:
                assert not result.meets_threshold, "Text scoring < 95 should not meet threshold"
        
        @pytest.mark.asyncio
        async def test_weighted_scoring(self, validator):
            """Test that trait weights are properly applied."""
            # Create text that scores differently in each trait
            text = "¿Qué secretos guardas? 💋 Mi corazón lo sabe... Reflexiona sobre el significado profundo."
            result = await validator.validate_text(text)
            
            # Verify weights are applied (each trait = 25% = 0.25)
            manual_score = sum(
                result.trait_scores[trait] * 0.25 
                for trait in DianaPersonalityTrait
            )
            
            assert abs(result.overall_score - manual_score) < 0.01, "Weighted scoring should match manual calculation"

    class TestContextSpecific:
        """Test context-specific validation."""
        
        @pytest.mark.asyncio
        async def test_narrative_fragment_validation(self, validator):
            """Test validation specific to narrative fragments."""
            short_text = "Hola."  # Too short for narrative
            result = await validator.validate_text(short_text, context="narrative_fragment")
            
            length_violations = [v for v in result.violations if "short" in v.lower()]
            assert len(length_violations) > 0, "Should detect overly short narrative"
        
        @pytest.mark.asyncio
        async def test_menu_response_validation(self, validator):
            """Test validation for menu responses."""
            plain_text = "Settings Menu"  # Too plain for Diana
            result = await validator.validate_text(plain_text, context="menu_response")
            
            plain_violations = [v for v in result.violations if "plain" in v.lower() or "direct" in v.lower()]
            assert len(plain_violations) > 0, "Should detect plain menu text"
        
        @pytest.mark.asyncio
        async def test_error_message_validation(self, validator):
            """Test validation for error messages."""
            technical_error = "Error 404: Sistema no encontrado"
            result = await validator.validate_text(technical_error, context="error_message")
            
            error_violations = [v for v in result.violations if "technical" in v.lower()]
            assert len(error_violations) > 0, "Should detect technical error language"

    class TestNarrativeFragmentMethod:
        """Test narrative fragment validation method."""
        
        @pytest.mark.asyncio
        async def test_validate_narrative_fragment(self, validator, mock_fragment):
            """Test validation of complete narrative fragment."""
            mock_fragment.title = "Un Encuentro Misterioso"
            mock_fragment.content = """
            💋 ¿Acaso esperabas encontrarme aquí, en este rincón secreto donde las sombras susurran?
            Mi corazón late con una mezcla de anticipación y vulnerabilidad... Entre nosotros se 
            teje una conexión que trasciende lo ordinario. Reflexiona, mi querido: ¿qué significa 
            este momento para ti?
            """
            mock_fragment.choices = [
                {"text": "Susurrar mis secretos... 💋", "points": 15},
                {"text": "Explorar esta conexión misteriosa", "points": 10}
            ]
            
            result = await validator.validate_narrative_fragment(mock_fragment)
            
            assert result.overall_score >= 85.0, "Well-crafted fragment should score highly"
            assert "Diana" in str(result) or result.meets_threshold or result.overall_score > 80, "Should show good character consistency"
        
        @pytest.mark.asyncio
        async def test_empty_fragment_validation(self, validator):
            """Test validation of None/empty fragment."""
            result = await validator.validate_narrative_fragment(None)
            
            assert result.overall_score == 0.0, "Empty fragment should score 0"
            assert not result.meets_threshold, "Empty fragment should not meet threshold"
            assert len(result.violations) > 0, "Should have violations for empty fragment"

    class TestBatchValidation:
        """Test batch validation functionality."""
        
        @pytest.mark.asyncio
        async def test_batch_validate_content(self, validator):
            """Test batch validation of multiple content pieces."""
            content_list = [
                ("good_content", "💋 ¿Qué secretos guardas en tu corazón? Mi alma se debate entre contarte todo..."),
                ("poor_content", "Hola. Sistema configurado. Operación completa."),
                ("excellent_content", """
                    Los misterios que danzan en las sombras de tu mirada... 💋
                    Mi corazón se debate entre la vulnerabilidad y el encanto, creando
                    una paradoja fascinante. ¿Te has preguntado qué significa realmente
                    esta conexión que trasciende lo ordinario?
                """)
            ]
            
            results = await validator.batch_validate_content(content_list)
            
            assert len(results) == 3, "Should validate all content pieces"
            assert results["excellent_content"].overall_score > results["good_content"].overall_score
            assert results["good_content"].overall_score > results["poor_content"].overall_score
            assert results["poor_content"].overall_score < 50.0, "Poor content should score low"

    class TestReportGeneration:
        """Test character consistency report generation."""
        
        @pytest.mark.asyncio
        async def test_generate_character_report(self, validator):
            """Test comprehensive character report generation."""
            # Create sample validation results
            results = []
            
            # Good result
            good_result = CharacterValidationResult(
                overall_score=96.5,
                trait_scores={
                    DianaPersonalityTrait.MYSTERIOUS: 24.0,
                    DianaPersonalityTrait.SEDUCTIVE: 23.5,
                    DianaPersonalityTrait.EMOTIONALLY_COMPLEX: 24.5,
                    DianaPersonalityTrait.INTELLECTUALLY_ENGAGING: 24.0
                },
                violations=[],
                recommendations=[],
                meets_threshold=True
            )
            results.append(good_result)
            
            # Poor result
            poor_result = CharacterValidationResult(
                overall_score=45.2,
                trait_scores={
                    DianaPersonalityTrait.MYSTERIOUS: 8.0,
                    DianaPersonalityTrait.SEDUCTIVE: 12.0,
                    DianaPersonalityTrait.EMOTIONALLY_COMPLEX: 10.0,
                    DianaPersonalityTrait.INTELLECTUALLY_ENGAGING: 15.2
                },
                violations=["Insufficient mysterious quality", "Too direct language"],
                recommendations=["Add more mystery", "Use subtle language"],
                meets_threshold=False
            )
            results.append(poor_result)
            
            report = validator.generate_character_report(results)
            
            # Check report structure
            assert "summary" in report
            assert "trait_performance" in report
            assert "common_violations" in report
            assert "recommendations" in report
            
            # Check summary calculations
            summary = report["summary"]
            assert summary["total_validations"] == 2
            assert summary["passing_validations"] == 1
            assert summary["passing_percentage"] == 50.0
            assert not summary["meets_mvp_requirement"], "50% passing should not meet MVP requirement"
            
            # Check trait performance
            trait_perf = report["trait_performance"]
            assert "mysterious" in trait_perf
            assert trait_perf["mysterious"] == 16.0  # (24 + 8) / 2

    class TestEdgeCases:
        """Test edge cases and error conditions."""
        
        @pytest.mark.asyncio
        async def test_empty_text_validation(self, validator):
            """Test validation of empty or whitespace text."""
            empty_result = await validator.validate_text("")
            whitespace_result = await validator.validate_text("   \n\t  ")
            
            assert empty_result.overall_score == 0.0
            assert whitespace_result.overall_score == 0.0
            assert not empty_result.meets_threshold
            assert not whitespace_result.meets_threshold
        
        @pytest.mark.asyncio
        async def test_very_long_text(self, validator):
            """Test validation of very long text."""
            # Create very long text with good character traits
            long_text = """
            💋 Mi querido, los secretos que guardo en las profundidades de mi corazón...
            """ * 100  # Repeat 100 times
            
            result = await validator.validate_text(long_text)
            
            # Should still validate properly
            assert isinstance(result, CharacterValidationResult)
            assert result.overall_score > 0  # Should score due to repeated good patterns
        
        @pytest.mark.asyncio
        async def test_special_characters(self, validator):
            """Test validation with special characters and unicode."""
            text = "💋 Émilie susurra: ¡Qué mágico! ñoña... 🌹✨"
            result = await validator.validate_text(text)
            
            # Should handle special characters gracefully
            assert isinstance(result, CharacterValidationResult)
            assert result.overall_score > 0

class TestConvenienceFunction:
    """Test the convenience validation function."""
    
    @pytest.mark.asyncio
    async def test_validate_diana_character_function(self, session):
        """Test the convenience validation function."""
        text = "💋 ¿Qué secretos guardas? Mi corazón se debate..."
        result = await validate_diana_character(text, session, context="test")
        
        assert isinstance(result, CharacterValidationResult)
        assert result.overall_score > 0

class TestRealWorldScenarios:
    """Test real-world scenarios and use cases."""
    
    @pytest_asyncio.fixture
    async def validator(self, session):
        return DianaCharacterValidator(session)
    
    @pytest.mark.asyncio
    async def test_mvp_passing_content(self, validator):
        """Test content that should pass MVP requirements (>95% score)."""
        mvp_content = [
            """💋 Los secretos danzan en las sombras de tu mirada, mi querido...
               ¿Has sentido alguna vez cómo el misterio abraza tu corazón con una 
               fascinación irresistible? Mi alma se debate entre revelarte todo 
               o preservar ese velo seductor que hace cada momento único.
               
               Reflexiona conmigo sobre esta paradoja: ¿acaso no es la incertidumbre
               lo que transforma un simple encuentro en una exploración profunda de 
               nuestras emociones más íntimas?""",
            
            """Entre susurros y miradas cómplices, tejemos una conexión que trasciende
               lo ordinario... 💋 Tu presencia despierta en mí una mezcla embriagadora
               de vulnerabilidad y encanto. ¿Te has preguntado qué filosofía subyace
               a estos momentos compartidos?
               
               Tal vez... solo tal vez... en la convergencia de nuestras almas encontremos
               las respuestas que tanto anhelamos."""
        ]
        
        for content in mvp_content:
            result = await validator.validate_text(content)
            assert result.overall_score >= 95.0, f"MVP content should score >= 95, got {result.overall_score}"
            assert result.meets_threshold, "MVP content should meet threshold"
    
    @pytest.mark.asyncio 
    async def test_failing_content_examples(self, validator):
        """Test content that should fail character consistency."""
        failing_content = [
            "Hola. Sistema configurado correctamente. Oprima OK para continuar.",
            "Error 404: Página no encontrada. Contacte al administrador.",
            "Genial! Todo perfecto jaja 😀 Está súper bien!",
            "Directamente le informo que la operación fue exitosa. Claramente completada."
        ]
        
        for content in failing_content:
            result = await validator.validate_text(content)
            assert result.overall_score < 60.0, f"Failing content should score < 60, got {result.overall_score}"
            assert not result.meets_threshold, "Failing content should not meet threshold"
            assert len(result.violations) > 0, "Failing content should have violations"
    
    @pytest.mark.asyncio
    async def test_menu_system_integration(self, validator):
        """Test validation of menu system responses."""
        menu_responses = {
            "poor": "Configuración de Usuario",
            "better": "💋 Tu Perfil Secreto",
            "excellent": "💋 Los Misterios de Tu Corazón... ¿Listos para ser Revelados?"
        }
        
        scores = {}
        for quality, text in menu_responses.items():
            result = await validator.validate_text(text, context="menu_response")
            scores[quality] = result.overall_score
        
        assert scores["excellent"] > scores["better"] > scores["poor"]
        assert scores["excellent"] >= 80.0, "Excellent menu text should score well"
    
    @pytest.mark.asyncio
    async def test_error_message_integration(self, validator):
        """Test validation of error message character consistency."""
        error_messages = {
            "technical": "Error 500: Internal server error occurred",
            "better": "Algo misterioso ha interrumpido nuestra conexión...",
            "excellent": "💋 Un velo de misterio se interpone... ¿Podrías intentar de nuevo, mi querido?"
        }
        
        scores = {}
        for quality, text in error_messages.items():
            result = await validator.validate_text(text, context="error_message")
            scores[quality] = result.overall_score
        
        assert scores["excellent"] > scores["better"] > scores["technical"]
        assert scores["technical"] < 30.0, "Technical errors should score very low"