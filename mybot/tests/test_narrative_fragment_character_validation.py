"""
Narrative Fragment Character Validation Tests

Specialized tests for validating Diana's character consistency 
specifically within narrative fragments and storytelling content.
"""

import pytest
import pytest_asyncio
from typing import List, Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from services.diana_character_validator import DianaCharacterValidator, DianaPersonalityTrait
from services.narrative_character_integrity_service import NarrativeCharacterIntegrityService
from database.narrative_unified import NarrativeFragment, UserNarrativeState, UserDecisionLog


class TestNarrativeFragmentValidation:
    """Test character validation specifically for narrative fragments."""
    
    @pytest_asyncio.fixture
    async def validator(self, session):
        return DianaCharacterValidator(session)
    
    @pytest_asyncio.fixture
    async def integrity_service(self, session):
        return NarrativeCharacterIntegrityService(session)
    
    @pytest_asyncio.fixture
    async def perfect_story_fragment(self):
        """A perfectly crafted story fragment that should score >95%."""
        return {
            "id": "perfect_story_001",
            "title": "💋 Los Susurros del Amanecer",
            "content": """
            Las primeras luces del amanecer se filtran a través de las cortinas de seda, 
            creando un juego de sombras y luces que parece danzar al ritmo de los latidos 
            de tu corazón... Diana está allí, observándote con esa mirada que guarda 
            mil secretos, mil promesas no pronunciadas...
            
            "¿Sabes?" susurra con voz aterciopelada, acercándose lentamente, "hay algo 
            en ti que despierta en mí una fascinación que no logro descifrar... Una 
            mezcla embriagadora de curiosidad y deseo que me hace preguntarme qué 
            misterios oculta tu alma..."
            
            Sus dedos rozan suavemente tu rostro, y en ese contacto sientes una conexión 
            que trasciende lo físico... es como si dos universos se hubieran encontrado 
            en este momento íntimo, creando una nueva realidad donde solo existís vosotros dos...
            
            "¿Te has preguntado alguna vez", continúa Diana, con esa sonrisa enigmática 
            que tanto la caracteriza, "qué filosofía subyace a estos encuentros del alma? 
            Porque esto que sentimos... es más profundo que la simple atracción... es 
            una danza cósmica de dos espíritus que han reconocido en el otro su complemento perfecto..."
            """,
            "fragment_type": "STORY",
            "choices": [
                {
                    "text": "💫 'Siento esa misma conexión profunda...'", 
                    "next_fragment": "story_002",
                    "emotional_impact": "deep_connection"
                },
                {
                    "text": "🔮 'Enséñame más sobre esos misterios de tu alma...'", 
                    "next_fragment": "mystery_path_001",
                    "emotional_impact": "curiosity_awakened"
                },
                {
                    "text": "❤️ 'Quiero explorar esta filosofía del amor contigo...'", 
                    "next_fragment": "philosophical_001",
                    "emotional_impact": "intellectual_intimacy"
                }
            ]
        }
    
    @pytest_asyncio.fixture
    async def perfect_decision_fragment(self):
        """A perfectly crafted decision fragment."""
        return {
            "id": "perfect_decision_001",
            "title": "🎭 Un Momento de Verdad",
            "content": """
            Diana se detiene frente a ti, y en sus ojos puedes ver el reflejo de una 
            decisión que ha estado madurando en su corazón... Hay una vulnerabilidad 
            nueva en su expresión, una apertura que no habías visto antes...
            
            "Mi querido...", susurra, y en esas dos palabras hay un universo de 
            emociones contenidas, "he llegado a un punto donde el miedo y el deseo 
            luchan en mi interior... Por un lado, mi instinto me dice que mantenga 
            los velos que protegen mi corazón, pero por otro... tu presencia ha 
            despertado en mí un anhelo de intimidad que no puedo ignorar..."
            
            Se acerca más, y puedes sentir el calor de su respiración, la tensión 
            de este momento crucial... "La elección que hagas ahora definirá el 
            curso de nuestra historia... ¿estás preparado para adentrarte en las 
            profundidades más íntimas de mi ser?... Porque una vez que crucemos 
            este umbral, no habrá vuelta atrás..."
            """,
            "fragment_type": "DECISION",
            "choices": [
                {
                    "text": "💋 'Cruzo ese umbral contigo sin dudas'",
                    "cost": 15,
                    "next_fragment": "intimate_path_001",
                    "risk_level": "high",
                    "emotional_impact": "deep_commitment"
                },
                {
                    "text": "🌹 'Avancemos paso a paso, respetando tus tiempos'",
                    "cost": 5,
                    "next_fragment": "gentle_path_001",
                    "risk_level": "low", 
                    "emotional_impact": "respectful_patience"
                },
                {
                    "text": "🔥 'Déjame demostrarte que puedes confiar en mí completamente'",
                    "cost": 25,
                    "next_fragment": "trust_building_001",
                    "risk_level": "very_high",
                    "emotional_impact": "total_commitment"
                },
                {
                    "text": "💭 'Necesito entender mejor qué significa esto para ti'",
                    "cost": 0,
                    "next_fragment": "understanding_path_001",
                    "risk_level": "none",
                    "emotional_impact": "intellectual_approach"
                }
            ]
        }
    
    async def test_perfect_story_fragment_validation(self, validator, perfect_story_fragment):
        """Test that perfect story fragment achieves >95% consistency."""
        # Combine title and content for validation
        full_text = f"{perfect_story_fragment['title']}\n\n{perfect_story_fragment['content']}"
        
        # Add choice texts
        for choice in perfect_story_fragment['choices']:
            full_text += f"\n{choice['text']}"
        
        result = await validator.validate_text(full_text, context="narrative_fragment")
        
        # Must achieve MVP requirement
        assert result.overall_score >= 95.0, (
            f"Perfect story fragment failed MVP requirement: {result.overall_score}/100\n"
            f"Violations: {result.violations}\n"
            f"This represents ideal Diana storytelling and must score ≥95%"
        )
        
        # All personality traits should score excellently
        for trait, score in result.trait_scores.items():
            assert score >= 22.0, (
                f"Perfect story - {trait.value} scored too low: {score}/25\n"
                f"Perfect content should excel in all personality traits"
            )
    
    async def test_perfect_decision_fragment_validation(self, validator, perfect_decision_fragment):
        """Test that perfect decision fragment achieves >95% consistency."""
        full_text = f"{perfect_decision_fragment['title']}\n\n{perfect_decision_fragment['content']}"
        
        for choice in perfect_decision_fragment['choices']:
            full_text += f"\n{choice['text']}"
        
        result = await validator.validate_text(full_text, context="narrative_fragment")
        
        # Must achieve MVP requirement
        assert result.overall_score >= 95.0, (
            f"Perfect decision fragment failed MVP requirement: {result.overall_score}/100\n"
            f"Violations: {result.violations}\n"
            f"This represents ideal Diana decision-making and must score ≥95%"
        )
        
        # Decision fragments should especially excel in emotional complexity
        emotional_score = result.trait_scores[DianaPersonalityTrait.EMOTIONALLY_COMPLEX]
        assert emotional_score >= 23.0, (
            f"Decision fragment should excel in emotional complexity: {emotional_score}/25"
        )
    
    async def test_fragment_choice_quality_validation(self, validator):
        """Test that fragment choices maintain Diana's character voice."""
        # Good choices that maintain Diana's character
        good_choices = [
            "💋 'Siente cómo mi corazón late por ti...'",
            "🔮 'Déjame adentrarme en tus misterios más profundos...'",
            "✨ 'Quiero descubrir cada secreto que guardas para mí...'",
            "🌹 'Permíteme ser tu confidente en este viaje del alma...'"
        ]
        
        for choice in good_choices:
            result = await validator.validate_text(choice, context="narrative_fragment")
            
            # Choices should maintain good character consistency
            assert result.overall_score >= 75.0, (
                f"Good choice scored too low: {result.overall_score}/100\n"
                f"Choice: {choice}\n"
                f"Choices should maintain Diana's seductive, mysterious voice"
            )
        
        # Bad choices that break character
        bad_choices = [
            "OK",
            "Genial, perfecto",
            "Sistema actualizado",
            "Todo correcto",
            "Sí, sin problemas"
        ]
        
        for choice in bad_choices:
            result = await validator.validate_text(choice, context="narrative_fragment")
            
            # Bad choices should score poorly
            assert result.overall_score < 40.0, (
                f"Bad choice scored too high: {result.overall_score}/100\n"
                f"Choice: {choice}\n"
                f"Character-breaking choices must be rejected"
            )
    
    async def test_fragment_length_and_development(self, validator):
        """Test that fragments have appropriate length for character development."""
        # Too short fragments can't develop Diana's character properly
        short_fragment = {
            "title": "💋 Breve",
            "content": "Diana sonríe.",
            "choices": []
        }
        
        full_text = f"{short_fragment['title']}\n\n{short_fragment['content']}"
        result = await validator.validate_text(full_text, context="narrative_fragment")
        
        # Should have violations for insufficient development
        assert any("too short" in violation.lower() or "insufficient" in violation.lower() 
                  for violation in result.violations), (
            f"Short fragment should be flagged for insufficient development\n"
            f"Violations: {result.violations}"
        )
        
        # Appropriate length fragment
        appropriate_fragment = {
            "title": "💋 El Encuentro Perfecto",
            "content": """
            Diana se acerca con esa gracia natural que tanto la caracteriza, 
            sus ojos brillando con una mezcla de misterio y promesa... "Hay 
            algo especial en este momento", susurra con voz aterciopelada, 
            "algo que late entre nosotros con una intensidad que me fascina..."
            """,
            "choices": []
        }
        
        full_text = f"{appropriate_fragment['title']}\n\n{appropriate_fragment['content']}"
        result = await validator.validate_text(full_text, context="narrative_fragment")
        
        # Should not have length-related violations
        length_violations = [v for v in result.violations 
                           if "short" in v.lower() or "insufficient" in v.lower()]
        assert len(length_violations) == 0, f"Appropriate length fragment shouldn't have length violations: {length_violations}"
    
    async def test_fragment_type_specific_validation(self, integrity_service):
        """Test validation rules specific to different fragment types."""
        
        # STORY fragments should focus on narrative
        story_fragment = {
            "id": "story_test",
            "title": "💋 Una Historia de Pasión",
            "content": """
            Las luces tenues crean una atmósfera de intimidad mientras Diana 
            comparte sus secretos más profundos contigo... cada palabra que 
            susurra teje una historia de seducción y misterio que solo vosotros 
            dos podéis entender...
            """,
            "fragment_type": "STORY",
            "choices": [
                {"text": "💫 'Continúa tu historia, mi amor'", "next": "story_002"}
            ]
        }
        
        is_valid, result = await integrity_service.validate_fragment_creation(story_fragment)
        assert is_valid, f"Valid story fragment should pass: {result.violations}"
        
        # DECISION fragments must have meaningful choices
        decision_fragment_bad = {
            "id": "decision_bad",
            "title": "Una Decisión",
            "content": "Debes elegir ahora.",
            "fragment_type": "DECISION",
            "choices": []  # Missing choices!
        }
        
        is_valid, result = await integrity_service.validate_fragment_creation(decision_fragment_bad)
        assert not is_valid, "Decision fragment without choices should fail"
        assert any("choice" in violation.lower() for violation in result.violations)
        
        # DECISION fragments with good choices
        decision_fragment_good = {
            "id": "decision_good",
            "title": "🎭 Un Momento de Elección",
            "content": """
            Diana te observa intensamente, sus ojos reflejando la importancia 
            de este momento... "La decisión que tomes ahora", susurra, "definirá 
            el rumbo de nuestra historia íntima..."
            """,
            "fragment_type": "DECISION",
            "choices": [
                {"text": "💋 'Confío en tu guía, Diana'", "cost": 5},
                {"text": "🔮 'Decidamos juntos este camino'", "cost": 10}
            ]
        }
        
        is_valid, result = await integrity_service.validate_fragment_creation(decision_fragment_good)
        assert is_valid, f"Valid decision fragment should pass: {result.violations}"
    
    async def test_narrative_immersion_preservation(self, validator):
        """Test that fragments don't break narrative immersion."""
        
        # Fragments that break immersion with technical language
        immersion_breaking_fragments = [
            "Error en el sistema narrativo. Reinicie la aplicación.",
            "Configuración de fragmento actualizada correctamente.",
            "Bot funcionando normalmente. Proceso completado.",
            "Comando ejecutado. Base de datos actualizada.",
        ]
        
        for fragment_text in immersion_breaking_fragments:
            result = await validator.validate_text(fragment_text, context="narrative_fragment")
            
            # Should heavily penalize immersion-breaking content
            assert result.overall_score < 30.0, (
                f"Immersion-breaking fragment scored too high: {result.overall_score}/100\n"
                f"Fragment: {fragment_text}\n"
                f"Technical language destroys narrative immersion"
            )
            
            assert not result.meets_threshold, "Immersion-breaking content must not meet threshold"
    
    async def test_character_consistency_across_fragment_series(self, validator):
        """Test character consistency across a series of connected fragments."""
        
        fragment_series = [
            {
                "title": "💋 El Primer Encuentro",
                "content": """
                Diana aparece como una visión de elegancia y misterio... sus ojos 
                brillan con secretos no revelados mientras una sonrisa enigmática 
                juega en sus labios... "Bienvenido a mi mundo", susurra...
                """
            },
            {
                "title": "🌹 Profundizando la Conexión", 
                "content": """
                Los días han pasado, y la conexión entre vosotros se ha intensificado... 
                Diana comparte ahora susurros más íntimos, revelando capas de su 
                personalidad que reserva solo para ti... hay una vulnerabilidad nueva 
                en sus ojos que te hace sentir especial...
                """
            },
            {
                "title": "💫 La Culminación",
                "content": """
                En este momento de intimidad suprema, Diana te observa con una mezcla 
                de pasión y ternura que trasciende lo físico... "Hemos llegado a un 
                lugar sagrado", murmura, "donde nuestras almas se encuentran en su 
                forma más pura y auténtica..."
                """
            }
        ]
        
        scores = []
        for i, fragment in enumerate(fragment_series):
            full_text = f"{fragment['title']}\n\n{fragment['content']}"
            result = await validator.validate_text(full_text, context="narrative_fragment")
            scores.append(result.overall_score)
            
            # Each fragment should maintain high consistency
            assert result.overall_score >= 90.0, (
                f"Fragment {i+1} in series scored too low: {result.overall_score}/100\n"
                f"Character consistency must be maintained across fragment series"
            )
        
        # Character development should remain consistent or improve across series
        score_variation = max(scores) - min(scores)
        assert score_variation <= 10.0, (
            f"Too much variation in character consistency across series: {score_variation}\n"
            f"Scores: {scores}\n"
            f"Diana's character should remain consistent throughout story progression"
        )


class TestAdvancedNarrativeScenarios:
    """Test advanced narrative scenarios and edge cases."""
    
    async def test_emotional_state_transitions(self, session):
        """Test that Diana's character remains consistent across different emotional states."""
        validator = DianaCharacterValidator(session)
        
        emotional_scenarios = [
            {
                "state": "playful_seductive",
                "content": """
                Diana se acerca con una sonrisa traviesa, sus ojos brillando con 
                una chispa juguetona... "¿Sabes qué estoy pensando?", pregunta 
                con voz coqueta, "estoy imaginando todas las travesuras íntimas 
                que podríamos compartir..." Su risa es como música que acaricia tu alma...
                """,
                "min_score": 95.0
            },
            {
                "state": "mysterious_contemplative",
                "content": """
                Diana se queda en silencio por un momento, su mirada perdida en 
                pensamientos profundos... "Hay filosofías del amor", murmura finalmente, 
                "que solo se revelan en momentos como este... cuando dos almas se 
                encuentran en el umbral entre lo conocido y lo por descubrir..."
                """,
                "min_score": 95.0
            },
            {
                "state": "vulnerable_intimate",
                "content": """
                Diana baja la mirada, y por primera vez la ves verdaderamente 
                vulnerable... "Hay partes de mí", susurra con voz temblorosa, 
                "que he mantenido ocultas por miedo... pero contigo siento la 
                seguridad de mostrar mi verdadero ser..." Una lágrima rueda por 
                su mejilla, pero hay esperanza en sus ojos...
                """,
                "min_score": 92.0  # Slightly lower due to vulnerability, but still high
            },
            {
                "state": "passionate_intense",
                "content": """
                El fuego de la pasión arde en los ojos de Diana mientras se acerca 
                más... "Siento que mi corazón va a explotar", jadea suavemente, 
                "esta intensidad que generas en mí... es como si hubieras despertado 
                una parte de mi ser que creí dormida para siempre..." Su respiración 
                se acelera con cada palabra...
                """,
                "min_score": 95.0
            }
        ]
        
        for scenario in emotional_scenarios:
            result = await validator.validate_text(scenario["content"], context="narrative_fragment")
            
            assert result.overall_score >= scenario["min_score"], (
                f"Emotional state '{scenario['state']}' scored too low: "
                f"{result.overall_score}/{scenario['min_score']}\n"
                f"Diana must maintain character consistency across all emotional states"
            )
    
    async def test_interactive_choice_consequences(self, validator):
        """Test that choice consequences maintain character consistency."""
        
        # Test choice consequences that should maintain Diana's character
        choice_consequences = [
            {
                "user_choice": "Approach Diana romantically",
                "diana_response": """
                Diana sonríe con esa mezcla de sorpresa y deleite que tanto la caracteriza... 
                "Veo que has elegido el camino del corazón", susurra, acercándose más, 
                "me fascina tu valentía al mostrar tus verdaderos sentimientos..." 
                Sus dedos rozan suavemente tu rostro mientras una nueva intimidad 
                florece entre vosotros...
                """,
                "min_score": 95.0
            },
            {
                "user_choice": "Ask about Diana's mysterious past",
                "diana_response": """
                Un velo de misterio cubre el rostro de Diana por un instante... 
                "Ah, mi pasado...", murmura con una sonrisa enigmática, "es un 
                laberinto de secretos que solo los corazones más devotos pueden 
                navegar... ¿estás seguro de que quieres adentrarte en esas sombras 
                que guardo tan celosamente?"
                """,
                "min_score": 95.0
            },
            {
                "user_choice": "Express deep philosophical thoughts",
                "diana_response": """
                Los ojos de Diana se iluminan con una fascinación intelectual... 
                "¡Qué profundidad de pensamiento!", exclama con admiración genuina, 
                "me enamora la forma en que tu mente explora las complejidades 
                de la existencia... ¿podríamos continuar esta conversación filosófica 
                en un ambiente más íntimo?"
                """,
                "min_score": 95.0
            }
        ]
        
        for scenario in choice_consequences:
            result = await validator.validate_text(
                scenario["diana_response"], 
                context="narrative_fragment"
            )
            
            assert result.overall_score >= scenario["min_score"], (
                f"Choice consequence for '{scenario['user_choice']}' scored too low: "
                f"{result.overall_score}/{scenario['min_score']}\n"
                f"Response: {scenario['diana_response'][:100]}...\n"
                f"Diana's responses to user choices must maintain perfect character consistency"
            )
    
    async def test_vip_content_character_consistency(self, validator):
        """Test that VIP content maintains character while being more intimate."""
        
        vip_content_samples = [
            {
                "type": "intimate_moment",
                "content": """
                💋 Solo para ti, mi amor VIP... Diana te lleva a su santuario privado, 
                un lugar donde los velos de la modestia se desvanecen lentamente... 
                "Aquí", susurra contra tu oído, "puedo mostrarte los aspectos más 
                sensuales de mi ser... esas partes de mí que reservo solo para 
                quienes han demostrado su devoción absoluta..."
                
                Su bata de seda se desliza suavemente, revelando curvas que son 
                poesía hecha carne... cada movimiento es una invitación a adentrarte 
                en misterios que solo el amor más profundo puede desvelar...
                """,
                "min_score": 95.0
            },
            {
                "type": "exclusive_secret",
                "content": """
                Diana se acerca hasta que puedes sentir el calor de su respiración... 
                "Te voy a contar algo", susurra, "que nunca he compartido con nadie... 
                un secreto tan íntimo que cambiará para siempre la forma en que me ves..."
                
                Sus ojos se llenan de una vulnerabilidad hermosa mientras revela 
                las profundidades más ocultas de su alma... es un momento de 
                conexión tan puro que el tiempo parece detenerse...
                """,
                "min_score": 95.0
            }
        ]
        
        for sample in vip_content_samples:
            result = await validator.validate_text(sample["content"], context="narrative_fragment")
            
            assert result.overall_score >= sample["min_score"], (
                f"VIP content '{sample['type']}' scored too low: "
                f"{result.overall_score}/{sample['min_score']}\n"
                f"VIP content must maintain Diana's character while providing intimate experiences"
            )
            
            # VIP content should especially excel in seductive trait
            seductive_score = result.trait_scores[DianaPersonalityTrait.SEDUCTIVE]
            assert seductive_score >= 23.0, (
                f"VIP content should excel in seductive trait: {seductive_score}/25"
            )


class TestNarrativeQualityAssurance:
    """Quality assurance tests for narrative content."""
    
    async def test_narrative_fragment_database_integration(self, session):
        """Test integration with narrative fragment database models."""
        integrity_service = NarrativeCharacterIntegrityService(session)
        
        # Create a test fragment in database
        test_fragment = NarrativeFragment(
            id="qa_test_fragment",
            title="💋 Test de Calidad",
            content="""
            Diana te observa con esa intensidad que caracteriza sus momentos 
            más profundos... "Este es un test de nuestros sistemas", susurra 
            con voz sedosa, "pero incluso en las pruebas, mi corazón late 
            con la misma pasión que en nuestros encuentros más reales..."
            """,
            fragment_type="STORY",
            is_active=True,
            choices=[
                {"text": "💫 'Cada momento contigo es real para mí'", "next": "test_002"}
            ]
        )
        
        session.add(test_fragment)
        await session.commit()
        
        # Validate the fragment through the service
        result = await integrity_service.validate_existing_fragment("qa_test_fragment")
        
        assert result is not None, "Should successfully validate database fragment"
        assert result.overall_score >= 85.0, (
            f"Database fragment should maintain good quality: {result.overall_score}/100"
        )
        
        # Clean up
        await session.delete(test_fragment)
        await session.commit()
    
    async def test_narrative_content_guidelines_compliance(self, validator):
        """Test compliance with narrative content creation guidelines."""
        
        # Guidelines test cases
        guideline_tests = [
            {
                "guideline": "Always maintain mystery",
                "good_example": """
                Diana sonríe, pero hay algo en sus ojos que no revela... 
                "Hay secretos", susurra, "que solo el tiempo y la confianza 
                pueden desvelar..."
                """,
                "bad_example": "Diana te cuenta todo sobre su pasado sin misterio.",
                "good_min_score": 80.0,
                "bad_max_score": 50.0
            },
            {
                "guideline": "Use seductive but elegant language",
                "good_example": """
                Su voz es como miel que acaricia tu alma... "Ven más cerca", 
                invita con una sonrisa que promete aventuras del corazón...
                """,
                "bad_example": "Hola, ¿cómo estás? Todo bien por aquí.",
                "good_min_score": 80.0,
                "bad_max_score": 30.0
            },
            {
                "guideline": "Show emotional complexity",
                "good_example": """
                Diana siente una mezcla de alegría y melancolía... "Por un lado 
                mi corazón canta de felicidad", murmura, "pero por otro, una 
                dulce nostalgia me abraza al recordar..."
                """,
                "bad_example": "Diana está feliz. Fin.",
                "good_min_score": 80.0,
                "bad_max_score": 40.0
            }
        ]
        
        for test in guideline_tests:
            # Test good example
            good_result = await validator.validate_text(
                test["good_example"], 
                context="narrative_fragment"
            )
            assert good_result.overall_score >= test["good_min_score"], (
                f"Good example for '{test['guideline']}' scored too low: "
                f"{good_result.overall_score}/{test['good_min_score']}"
            )
            
            # Test bad example
            bad_result = await validator.validate_text(
                test["bad_example"], 
                context="narrative_fragment"
            )
            assert bad_result.overall_score <= test["bad_max_score"], (
                f"Bad example for '{test['guideline']}' scored too high: "
                f"{bad_result.overall_score}/{test['bad_max_score']}"
            )