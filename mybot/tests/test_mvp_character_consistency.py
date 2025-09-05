"""
MVP Character Consistency Validation Tests

Comprehensive test suite for Diana's character consistency >95% requirement,
automated validation, and personality trait maintenance across all interactions.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from database.narrative_unified import (
    NarrativeFragment, 
    NarrativeCharacterValidation,
    UserNarrativeState
)
from services.diana_character_validator import (
    DianaCharacterValidator,
    DianaPersonalityTrait,
    CharacterValidationResult
)


class TestDianaCharacterConsistencyRequirement:
    """Test Diana maintains >95% character consistency across all content."""

    @pytest_asyncio.fixture
    async def character_validator(self, session):
        """Create character validator for testing."""
        return DianaCharacterValidator(session)

    def get_mvp_content_samples(self):
        """Get content samples that should meet character consistency."""
        return [
            {
                'id': 'fragment_content_1',
                'content': '💋 **Bienvenido a mis dominios, querido...** \n\nAquí, donde las sombras danzan con secretos no revelados, te encuentras en el umbral de algo más profundo de lo que imaginas. ¿Sientes esa energía misteriosa que flota en el aire?',
                'type': 'narrative_fragment'
            },
            {
                'id': 'menu_response_1', 
                'content': '✨ Explorar las sombras con curiosidad',
                'type': 'menu_response'
            },
            {
                'id': 'error_message_1',
                'content': '🌙 Los misterios parecen elusivos en este momento... ¿Intentas de nuevo, mi curioso explorador?',
                'type': 'error_message'
            },
            {
                'id': 'notification_1',
                'content': '🌟 Has desbloqueado un nuevo secreto... La verdad se revela poco a poco.',
                'type': 'notification'
            },
            {
                'id': 'choice_text_1',
                'content': '💫 Susurrar una pregunta al viento nocturno',
                'type': 'menu_response'
            }
        ]

    async def test_all_content_meets_95_percent_threshold(self, character_validator):
        """Test all MVP content meets 95% character consistency threshold."""
        content_samples = self.get_mvp_content_samples()
        
        validation_results = []
        for sample in content_samples:
            result = await character_validator.validate_text(
                sample['content'], 
                context=sample['type']
            )
            validation_results.append((sample['id'], result))
        
        # Verify each piece meets threshold
        for content_id, result in validation_results:
            assert result.meets_threshold, f"Content {content_id} fails 95% threshold: {result.overall_score:.1f}%"
            assert result.overall_score >= 95.0, f"Content {content_id} score {result.overall_score:.1f}% below 95%"

    async def test_personality_trait_balance(self, character_validator):
        """Test Diana's personality traits are balanced across content."""
        content_samples = self.get_mvp_content_samples()
        
        trait_scores_aggregate = {
            DianaPersonalityTrait.MYSTERIOUS: [],
            DianaPersonalityTrait.SEDUCTIVE: [],
            DianaPersonalityTrait.EMOTIONALLY_COMPLEX: [],
            DianaPersonalityTrait.INTELLECTUALLY_ENGAGING: []
        }
        
        for sample in content_samples:
            result = await character_validator.validate_text(sample['content'])
            
            for trait, score in result.trait_scores.items():
                trait_scores_aggregate[trait].append(score)
        
        # Verify all traits have reasonable representation
        for trait, scores in trait_scores_aggregate.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            assert avg_score >= 15.0, f"Trait {trait.value} average {avg_score:.1f} below 15 (60% of max 25)"

    async def test_character_consistency_automation(self, character_validator, session):
        """Test automated character consistency validation workflow."""
        # Create test fragment
        fragment = NarrativeFragment(
            id='consistency_test_fragment',
            title='Test Fragment for Consistency',
            content='💋 **Diana te observa con una sonrisa enigmática...** \n\nSus ojos brillan con secretos no revelados mientras susurra: "¿Acaso pensaste que sería tan simple, querido mío?" La complejidad de sus emociones se refleja en cada palabra.',
            fragment_type='STORY',
            diana_personality_weight=98,
            character_validation_required=True,
            is_active=True
        )
        session.add(fragment)
        await session.commit()
        
        # Run automated validation
        result = await character_validator.validate_narrative_fragment(fragment)
        
        # Store validation result
        validation_record = NarrativeCharacterValidation(
            fragment_id='consistency_test_fragment',
            validated_content=fragment.content,
            content_type='narrative_fragment',
            consistency_score=int(result.overall_score),
            mysterious_score=int(result.trait_scores.get(DianaPersonalityTrait.MYSTERIOUS, 0)),
            seductive_score=int(result.trait_scores.get(DianaPersonalityTrait.SEDUCTIVE, 0)),
            emotional_complexity_score=int(result.trait_scores.get(DianaPersonalityTrait.EMOTIONALLY_COMPLEX, 0)),
            intellectual_engagement_score=int(result.trait_scores.get(DianaPersonalityTrait.INTELLECTUALLY_ENGAGING, 0)),
            meets_threshold=result.meets_threshold,
            violations_detected=result.violations,
            recommendations=result.recommendations
        )
        session.add(validation_record)
        await session.commit()
        
        # Verify automated validation
        assert result.meets_threshold, f"Automated validation failed: {result.overall_score:.1f}%"
        assert validation_record.consistency_score >= 95, "Stored validation score below threshold"

    async def test_character_regression_prevention(self, character_validator):
        """Test system prevents character consistency regression."""
        # Good content that should pass
        good_content = '💋 **Diana te mira con ojos llenos de misterio...** \n\n"Los secretos más profundos", susurra con voz terciopelada, "requieren de almas valientes dispuestas a explorar lo desconocido." Su sonrisa insinúa promesas no reveladas.'
        
        # Bad content that should fail
        bad_content = 'Hello! Click here to continue to the next level. This is a simple message without any special formatting or personality.'
        
        good_result = await character_validator.validate_text(good_content, context="narrative_fragment")
        bad_result = await character_validator.validate_text(bad_content, context="narrative_fragment")
        
        # Verify regression detection
        assert good_result.meets_threshold, f"Good content should pass: {good_result.overall_score:.1f}%"
        assert not bad_result.meets_threshold, f"Bad content should fail: {bad_result.overall_score:.1f}%"
        assert len(bad_result.violations) > 0, "Bad content should have violations listed"
        assert len(bad_result.recommendations) > 0, "Bad content should have improvement recommendations"


class TestPersonalityTraitValidation:
    """Test individual personality trait validation."""

    @pytest_asyncio.fixture
    async def character_validator(self, session):
        return DianaCharacterValidator(session)

    async def test_mysterious_trait_detection(self, character_validator):
        """Test mysterious personality trait detection."""
        mysterious_content = [
            'Los secretos que oculta esta historia son más profundos de lo que imaginas...',
            '¿Será que hay más de lo que ves a primera vista? Las pistas están ahí, entre líneas.',
            'Algo susurra en las sombras, insinuando verdades no reveladas aún.'
        ]
        
        non_mysterious_content = [
            'Este es el nivel 1. Haz click para continuar.',
            'Mensaje directo sin ningún elemento de misterio.',
            'Instrucciones claras y obvias para el usuario.'
        ]
        
        for content in mysterious_content:
            result = await character_validator.validate_text(content)
            mysterious_score = result.trait_scores.get(DianaPersonalityTrait.MYSTERIOUS, 0)
            assert mysterious_score >= 15.0, f"Should detect mystery in: {content[:50]}... (score: {mysterious_score})"
        
        for content in non_mysterious_content:
            result = await character_validator.validate_text(content)
            mysterious_score = result.trait_scores.get(DianaPersonalityTrait.MYSTERIOUS, 0)
            assert mysterious_score < 10.0, f"Should not detect mystery in: {content[:50]}... (score: {mysterious_score})"

    async def test_seductive_trait_detection(self, character_validator):
        """Test seductive personality trait detection."""
        seductive_content = [
            '💋 Mi querido, ven más cerca... tengo algo especial que mostrarte.',
            'Diana te mira con una sonrisa encantadora, sus ojos brillando con magnetismo.',
            'Su voz terciopelada susurra promesas tentadoras al oído.'
        ]
        
        non_seductive_content = [
            'Usuario, selecciona una opción del menú.',
            'Error 404: Página no encontrada.',
            'Configuración actualizada correctamente.'
        ]
        
        for content in seductive_content:
            result = await character_validator.validate_text(content)
            seductive_score = result.trait_scores.get(DianaPersonalityTrait.SEDUCTIVE, 0)
            assert seductive_score >= 15.0, f"Should detect seduction in: {content[:50]}... (score: {seductive_score})"
        
        for content in non_seductive_content:
            result = await character_validator.validate_text(content)
            seductive_score = result.trait_scores.get(DianaPersonalityTrait.SEDUCTIVE, 0)
            assert seductive_score < 5.0, f"Should not detect seduction in: {content[:50]}... (score: {seductive_score})"

    async def test_emotional_complexity_detection(self, character_validator):
        """Test emotional complexity trait detection."""
        complex_content = [
            'En su corazón se mezcla una profunda melancolía con una esperanza ardiente, creando un conflicto interno fascinante.',
            'Los sentimientos se entrelazan en su alma como hilos de seda, tanto vulnerables como fuertes.',
            'Por un lado siente deseo, por otro temor... la paradoja de sus emociones la cautiva.'
        ]
        
        simple_content = [
            'Diana está feliz.',
            'Se siente bien hoy.',
            'Todo está perfecto.'
        ]
        
        for content in complex_content:
            result = await character_validator.validate_text(content)
            emotional_score = result.trait_scores.get(DianaPersonalityTrait.EMOTIONALLY_COMPLEX, 0)
            assert emotional_score >= 15.0, f"Should detect complexity in: {content[:50]}... (score: {emotional_score})"
        
        for content in simple_content:
            result = await character_validator.validate_text(content)
            emotional_score = result.trait_scores.get(DianaPersonalityTrait.EMOTIONALLY_COMPLEX, 0)
            assert emotional_score < 10.0, f"Should not detect complexity in: {content[:50]}... (score: {emotional_score})"

    async def test_intellectual_engagement_detection(self, character_validator):
        """Test intellectual engagement trait detection."""
        engaging_content = [
            '¿Has reflexionado alguna vez sobre la naturaleza paradójica de la realidad? Considera las múltiples dimensiones de la existencia.',
            'La filosofía de la percepción nos invita a contemplar: ¿qué es verdad y qué es ilusión?',
            '¿Te has preguntado por qué ciertos conocimientos permanecen ocultos? Analiza las capas de significado.'
        ]
        
        non_engaging_content = [
            'Botón presionado.',
            'Siguiente página.',
            'Fin del juego.'
        ]
        
        for content in engaging_content:
            result = await character_validator.validate_text(content)
            intellectual_score = result.trait_scores.get(DianaPersonalityTrait.INTELLECTUALLY_ENGAGING, 0)
            assert intellectual_score >= 15.0, f"Should detect engagement in: {content[:50]}... (score: {intellectual_score})"
        
        for content in non_engaging_content:
            result = await character_validator.validate_text(content)
            intellectual_score = result.trait_scores.get(DianaPersonalityTrait.INTELLECTUALLY_ENGAGING, 0)
            assert intellectual_score < 5.0, f"Should not detect engagement in: {content[:50]}... (score: {intellectual_score})"


class TestCharacterValidationViolations:
    """Test character validation violation detection."""

    @pytest_asyncio.fixture
    async def character_validator(self, session):
        return DianaCharacterValidator(session)

    async def test_directness_violation_detection(self, character_validator):
        """Test detection of overly direct communication."""
        direct_violations = [
            'Directamente, sin rodeos: esta es la respuesta.',
            'Claramente, la opción correcta es la A.',
            'Obviamente, tienes que hacer esto.'
        ]
        
        for content in direct_violations:
            result = await character_validator.validate_text(content)
            
            # Should detect directness violations
            directness_violations = [v for v in result.violations if 'direct' in v.lower()]
            assert len(directness_violations) > 0, f"Should detect directness in: {content}"
            assert not result.meets_threshold, "Overly direct content should fail threshold"

    async def test_casualness_violation_detection(self, character_validator):
        """Test detection of overly casual language."""
        casual_violations = [
            'Hola! Okay, genial, perfecto!',
            'Jaja, este nivel está súper fácil 😀',
            'Hey, que tal? Todo bien por aquí.'
        ]
        
        for content in casual_violations:
            result = await character_validator.validate_text(content)
            
            casual_violations_found = [v for v in result.violations if 'casual' in v.lower()]
            assert len(casual_violations_found) > 0, f"Should detect casualness in: {content}"

    async def test_technical_language_violation_detection(self, character_validator):
        """Test detection of technical language that breaks character."""
        technical_violations = [
            'Sistema configurado. Parámetros actualizados correctamente.',
            'Error en la base de datos. Revisa la configuración del menú.',
            'Proceso completado. Operación ejecutada con éxito.'
        ]
        
        for content in technical_violations:
            result = await character_validator.validate_text(content)
            
            technical_violations_found = [v for v in result.violations if 'technical' in v.lower() or 'técnico' in v.lower()]
            assert len(technical_violations_found) > 0 or not result.meets_threshold, f"Should detect technical language in: {content}"

    async def test_violation_recommendations_quality(self, character_validator):
        """Test quality and usefulness of improvement recommendations."""
        poor_content = 'Hello user. Click button A or B. System ready.'
        
        result = await character_validator.validate_text(poor_content)
        
        assert len(result.violations) > 0, "Poor content should have violations"
        assert len(result.recommendations) > 0, "Poor content should have recommendations"
        
        # Verify recommendations are actionable
        for recommendation in result.recommendations:
            assert len(recommendation) > 20, "Recommendations should be detailed"
            assert any(keyword in recommendation.lower() for keyword in ['add', 'use', 'include', 'avoid']), "Recommendations should be actionable"


class TestContextSpecificValidation:
    """Test validation adapts to different content contexts."""

    @pytest_asyncio.fixture
    async def character_validator(self, session):
        return DianaCharacterValidator(session)

    async def test_narrative_fragment_validation_standards(self, character_validator):
        """Test narrative fragments have higher validation standards."""
        short_content = '💋 Diana sonríe.'
        detailed_content = '💋 **Diana te observa con ojos llenos de misterio...** \n\nSus labios se curvan en una sonrisa enigmática mientras susurra: "Los secretos más profundos requieren de corazones valientes, querido mío." La complejidad de sus emociones se refleja en cada gesto delicado.'
        
        short_result = await character_validator.validate_text(short_content, context="narrative_fragment")
        detailed_result = await character_validator.validate_text(detailed_content, context="narrative_fragment")
        
        # Narrative fragments should require more substance
        assert not short_result.meets_threshold, "Short narrative content should fail"
        assert detailed_result.meets_threshold, "Detailed narrative content should pass"
        
        # Check for specific narrative requirements in violations
        short_violations = [v for v in short_result.violations if 'short' in v.lower() or 'development' in v.lower()]
        assert len(short_violations) > 0, "Should detect insufficient narrative development"

    async def test_menu_response_validation_flexibility(self, character_validator):
        """Test menu responses have appropriate validation flexibility."""
        simple_menu = '💫 Explorar más'
        elaborate_menu = '💫 Adentrarse en los misterios ocultos con curiosidad ardiente'
        
        simple_result = await character_validator.validate_text(simple_menu, context="menu_response")
        elaborate_result = await character_validator.validate_text(elaborate_menu, context="menu_response")
        
        # Both should potentially pass with appropriate character elements
        # Menu items can be shorter while maintaining character
        assert simple_result.overall_score >= 85.0, "Simple menu with character elements should score well"
        assert elaborate_result.overall_score >= 90.0, "Elaborate menu should score even better"

    async def test_error_message_character_maintenance(self, character_validator):
        """Test error messages maintain character while being informative."""
        technical_error = 'Error 404: Resource not found.'
        character_error = '🌙 Los caminos se han desvanecido en la niebla, querido... ¿Intentamos otro sendero?'
        
        technical_result = await character_validator.validate_text(technical_error, context="error_message")
        character_result = await character_validator.validate_text(character_error, context="error_message")
        
        assert not technical_result.meets_threshold, "Technical errors should fail character validation"
        assert character_result.meets_threshold, "Character-consistent errors should pass"
        
        # Verify error-specific recommendations
        error_violations = [v for v in technical_result.violations if 'error' in v.lower() or 'technical' in v.lower()]
        assert len(error_violations) > 0, "Should detect technical error language"


class TestCharacterConsistencyReporting:
    """Test character consistency reporting and analysis."""

    @pytest_asyncio.fixture
    async def character_validator(self, session):
        return DianaCharacterValidator(session)

    async def test_comprehensive_consistency_report(self, character_validator):
        """Test comprehensive character consistency report generation."""
        # Create diverse content samples for analysis
        content_samples = [
            '💋 **Diana te mira con intensidad...** Los secretos danzan en sus ojos mientras susurra promesas no reveladas.',  # High score
            '✨ Explorar los misterios ocultos con curiosidad',  # Medium score
            'Siguiente nivel disponible',  # Low score
            '🌙 ¿Has contemplado alguna vez la profundidad de los sentimientos que se ocultan tras una sonrisa enigmática?'  # High score
        ]
        
        validation_results = []
        for content in content_samples:
            result = await character_validator.validate_text(content)
            validation_results.append(result)
        
        # Generate comprehensive report
        report = character_validator.generate_character_report(validation_results)
        
        # Verify report structure
        assert 'summary' in report
        assert 'trait_performance' in report
        assert 'common_violations' in report
        assert 'recommendations' in report
        
        # Verify summary statistics
        summary = report['summary']
        assert 'average_score' in summary
        assert 'passing_percentage' in summary
        assert 'total_validations' in summary
        assert 'meets_mvp_requirement' in summary
        
        assert summary['total_validations'] == 4
        assert 0 <= summary['average_score'] <= 100
        assert 0 <= summary['passing_percentage'] <= 100

    async def test_trait_performance_analysis(self, character_validator):
        """Test trait performance analysis in reports."""
        # Content with unbalanced traits
        mysterious_heavy_content = [
            'Secretos ocultos en las sombras... pistas entre líneas... misterios no revelados...',
            '¿Qué se esconde tras el velo? Las respuestas susurran en la penumbra...'
        ]
        
        results = []
        for content in mysterious_heavy_content:
            result = await character_validator.validate_text(content)
            results.append(result)
        
        report = character_validator.generate_character_report(results)
        trait_performance = report['trait_performance']
        
        # Verify trait analysis
        assert 'mysterious' in trait_performance
        assert 'seductive' in trait_performance
        assert 'emotionally_complex' in trait_performance
        assert 'intellectually_engaging' in trait_performance
        
        # Should detect high mysterious scores
        assert trait_performance['mysterious'] > trait_performance['seductive']

    async def test_improvement_recommendation_generation(self, character_validator):
        """Test quality of generated improvement recommendations."""
        # Poor content to generate recommendations
        poor_content_samples = [
            'Click here to continue.',  # Too direct/technical
            'Hello! Everything is great!',  # Too casual
            'System updated successfully.'  # Technical language
        ]
        
        results = []
        for content in poor_content_samples:
            result = await character_validator.validate_text(content)
            results.append(result)
        
        report = character_validator.generate_character_report(results)
        recommendations = report['recommendations']
        
        # Should generate useful recommendations
        assert len(recommendations) > 0, "Should generate improvement recommendations"
        assert len(recommendations) <= 5, "Should limit to top 5 recommendations"
        
        # Recommendations should be actionable
        for rec in recommendations:
            assert len(rec) > 10, "Recommendations should be detailed"
            improvement_keywords = ['increase', 'enhance', 'add', 'reduce', 'avoid', 'use']
            assert any(keyword in rec.lower() for keyword in improvement_keywords), f"Recommendation should be actionable: {rec}"

    async def test_mvp_compliance_validation(self, character_validator):
        """Test MVP compliance validation in reporting."""
        # Create content that meets MVP standards
        mvp_compliant_content = [
            '💋 **Diana te recibe con una sonrisa enigmática...** \n\n"Bienvenido a mis dominios, querido", susurra con voz terciopelada. Sus ojos brillan con secretos no revelados mientras insinúa: "¿Tienes el valor de explorar lo desconocido?"',
            '✨ **Los misterios se despliegan ante ti...** \n\nCada decisión que tomes revelará nuevas capas de una verdad compleja. Diana te observa, curiosa por ver qué sendero elegirás en esta danza de descubrimientos.',
            '🌙 **En la profundidad de la noche de los secretos...** \n\n"Las almas valientes", murmura Diana, "encuentran en la oscuridad las gemas más preciosas. ¿Qué tesoro buscas tú, mi curioso explorador?"'
        ]
        
        results = []
        for content in mvp_compliant_content:
            result = await character_validator.validate_text(content, context="narrative_fragment")
            results.append(result)
        
        report = character_validator.generate_character_report(results)
        
        # Should meet MVP requirements
        assert report['summary']['meets_mvp_requirement'] is True, "Should meet MVP character consistency requirement"
        assert report['summary']['passing_percentage'] >= 95.0, "Should have >= 95% passing rate"
        assert report['summary']['average_score'] >= 95.0, "Should have >= 95% average score"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])