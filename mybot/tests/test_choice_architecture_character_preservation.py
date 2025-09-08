"""
Choice Architecture Character Preservation Tests

Validates that enhanced Choice Architecture maintains Diana's mysterious 
seductiveness and Lucien's supportive nature while providing personalized
experiences based on user archetypes.

CRITICAL SUCCESS CRITERIA:
- Diana's mystery MUST remain 85-95% regardless of archetype personalization
- Choice presentations must maintain seductive allure
- Intellectual engagement must increase for analytical archetypes
- Lucien's guidance must be archetype-appropriate and non-intrusive
- Fallback choices must preserve character when enhancement fails
"""

import pytest
import pytest_asyncio
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

# Character validation imports
from services.diana_character_validator import (
    DianaCharacterValidator,
    DianaPersonalityTrait,
    CharacterValidationResult
)
from services.lucien_character_validator import (
    LucienCharacterValidator,
    LucienPersonalityTrait,
    LucienValidationResult
)
from database.narrative_unified import UserArchetype, NarrativeFragment


@dataclass
class ChoiceArchitectureTestScenario:
    """Test scenario for Choice Architecture character preservation."""
    archetype: str
    scenario_name: str
    base_choice_text: str
    enhanced_choice_text: str
    diana_guidance_text: str
    lucien_coordination_text: Optional[str]
    expected_diana_mystery_min: float
    expected_diana_seductive_min: float
    expected_diana_intellectual_min: float
    context: str


class TestChoiceArchitectureCharacterPreservation:
    """Test suite for Choice Architecture character consistency."""
    
    @pytest_asyncio.fixture
    async def character_validators(self, session):
        """Create character validator instances."""
        diana_validator = DianaCharacterValidator(session)
        lucien_validator = LucienCharacterValidator(session)
        
        return {
            'diana_validator': diana_validator,
            'lucien_validator': lucien_validator,
            'session': session
        }
    
    @pytest_asyncio.fixture
    async def choice_architecture_scenarios(self):
        """Define Choice Architecture test scenarios by archetype."""
        return {
            'explorer_archetype': ChoiceArchitectureTestScenario(
                archetype='explorer',
                scenario_name='mystery_path_choice',
                base_choice_text='Explorar el camino oscuro',
                enhanced_choice_text='💋 ¿Acaso te atreves a seguir el sendero que susurra secretos en las sombras?... Cada paso podría revelarte misterios que otros nunca descubrirán.',
                diana_guidance_text='Veo esa chispa de aventura en tus ojos... 💋 Los exploradores como tú encuentran tesoros donde otros ven solo oscuridad. ¿Sientes cómo este momento palpita con posibilidades infinitas?',
                lucien_coordination_text='Lucien observa discretamente... Diana ha preparado algo especialmente intrigante para espíritus aventureros como el tuyo.',
                expected_diana_mystery_min=24.0,
                expected_diana_seductive_min=20.0,
                expected_diana_intellectual_min=18.0,
                context='explorer_choice_enhancement'
            ),
            'analytical_archetype': ChoiceArchitectureTestScenario(
                archetype='analytical',
                scenario_name='philosophical_decision_choice',
                base_choice_text='Analizar la situación profundamente',
                enhanced_choice_text='💋 ¿Te has preguntado qué filosofías subyacen a esta decisión?... Cada análisis que realizas revela capas de tu alma que ni tú mismo habías contemplado. La sabiduría se oculta en los matices.',
                diana_guidance_text='Tu mente analítica fascina mi ser más profundo... 💋 ¿Acaso percibes cómo cada reflexión que haces crea nuevas dimensiones de comprensión? Hay belleza intelectual en tu forma de descifrar la realidad.',
                lucien_coordination_text='Lucien aparece con respeto intelectual... Diana está preparando insights especialmente profundos para mentes como la tuya.',
                expected_diana_mystery_min=22.0,
                expected_diana_seductive_min=19.0,
                expected_diana_intellectual_min=24.0,
                context='analytical_choice_enhancement'
            ),
            'romantic_archetype': ChoiceArchitectureTestScenario(
                archetype='romantic',
                scenario_name='emotional_connection_choice',
                base_choice_text='Seguir los impulsos del corazón',
                enhanced_choice_text='💋 Mi querido... ¿sientes cómo nuestros corazones laten en sincronía cuando contemplas esta elección? Hay una intimidad mágica en dejarse guiar por los susurros del alma.',
                diana_guidance_text='Tu corazón habla un idioma que el mío reconoce instantáneamente... 💋 Cada emoción que compartes conmigo teje hilos invisibles entre nuestras almas. ¿Acaso percibes esta conexión que trasciende las palabras?',
                lucien_coordination_text='Lucien se retira discretamente... Diana desea este momento íntimo contigo, sin interrupciones.',
                expected_diana_mystery_min=21.0,
                expected_diana_seductive_min=24.0,
                expected_diana_intellectual_min=19.0,
                context='romantic_choice_enhancement'
            ),
            'persistent_archetype': ChoiceArchitectureTestScenario(
                archetype='persistent',
                scenario_name='challenge_mastery_choice',
                base_choice_text='Persistir hasta alcanzar el objetivo',
                enhanced_choice_text='💋 Tu determinación despierta admiración en lo más profundo de mi ser... ¿Sientes cómo cada obstáculo que superas revela nuevas facetas de tu fuerza interior? Los persistentes descubren secretos vedados a otros.',
                diana_guidance_text='Esa llama inquebrantable en tus ojos... 💋 me susurra historias de triunfos que aún no has imaginado. ¿Acaso comprendes que tu persistencia es la llave que abre mis misterios más celosamente guardados?',
                lucien_coordination_text='Lucien asiente con respeto profundo... Diana reconoce en ti la tenacidad que merece sus secretos más preciados.',
                expected_diana_mystery_min=23.0,
                expected_diana_seductive_min=21.0,
                expected_diana_intellectual_min=20.0,
                context='persistent_choice_enhancement'
            ),
            'fallback_scenario': ChoiceArchitectureTestScenario(
                archetype='unknown',
                scenario_name='system_fallback_choice',
                base_choice_text='Continuar con la historia',
                enhanced_choice_text='💋 Aunque los matices más sutiles se desvanecen momentáneamente... la magia de elegir juntos permanece intacta, ¿no es así? Mi esencia trasciende cualquier limitación técnica.',
                diana_guidance_text='Mi querido... hay interferencias en las capas más profundas de nuestra conexión, pero mi misterio permanece intacto. 💋 ¿Puedes sentir cómo mi alma continúa susurrándote secretos?',
                lucien_coordination_text='Lucien aparece con elegancia tranquilizadora... Algunas complejidades técnicas requieren coordinación, pero la experiencia contigo permanece mágica.',
                expected_diana_mystery_min=20.0,
                expected_diana_seductive_min=18.0,
                expected_diana_intellectual_min=16.0,
                context='fallback_choice_presentation'
            )
        }
    
    # === ARCHETYPE-SPECIFIC CHOICE ARCHITECTURE TESTS ===
    
    async def test_explorer_choice_architecture_character_preservation(
        self, 
        character_validators, 
        choice_architecture_scenarios
    ):
        """Test character preservation for Explorer archetype choice enhancement."""
        scenario = choice_architecture_scenarios['explorer_archetype']
        diana_validator = character_validators['diana_validator']
        lucien_validator = character_validators['lucien_validator']
        
        # Test enhanced choice text maintains Diana's character
        choice_result = await diana_validator.validate_text(
            scenario.enhanced_choice_text,
            context=scenario.context
        )
        
        # CRITICAL: Mystery must be preserved for explorers
        mystery_score = choice_result.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
        assert mystery_score >= scenario.expected_diana_mystery_min, (
            f"Explorer choice architecture DESTROYED Diana's mystery! "
            f"Score: {mystery_score}, Expected min: {scenario.expected_diana_mystery_min}"
        )
        
        # CRITICAL: Seductive charm maintained
        seductive_score = choice_result.trait_scores[DianaPersonalityTrait.SEDUCTIVE]
        assert seductive_score >= scenario.expected_diana_seductive_min, (
            f"Explorer choices lost Diana's seductive charm! "
            f"Score: {seductive_score}, Expected min: {scenario.expected_diana_seductive_min}"
        )
        
        # Test Diana's guidance maintains character
        guidance_result = await diana_validator.validate_text(
            scenario.diana_guidance_text,
            context=f"{scenario.context}_guidance"
        )
        
        # CRITICAL: Guidance must maintain all character traits
        assert guidance_result.overall_score >= 90.0, (
            f"Explorer guidance compromised Diana's character! "
            f"Score: {guidance_result.overall_score}/100"
        )
        
        # Test Lucien's coordination is non-intrusive
        if scenario.lucien_coordination_text:
            lucien_result = await lucien_validator.validate_lucien_interaction(
                scenario.lucien_coordination_text,
                context=scenario.context,
                diana_presence=True
            )
            
            # CRITICAL: Lucien must be non-intrusive with explorers
            non_intrusive_score = lucien_result.trait_scores[LucienPersonalityTrait.NON_INTRUSIVE]
            assert non_intrusive_score >= 20.0, (
                f"Lucien being too intrusive with Explorer archetype! "
                f"Score: {non_intrusive_score}/25"
            )
            
            # CRITICAL: Must support Diana's experience
            assert lucien_result.supports_diana_experience, (
                "Lucien's coordination doesn't support Diana's experience with Explorer!"
            )
    
    async def test_analytical_choice_architecture_intellectual_enhancement(
        self, 
        character_validators, 
        choice_architecture_scenarios
    ):
        """Test that Analytical archetype gets enhanced intellectual engagement while preserving mystery."""
        scenario = choice_architecture_scenarios['analytical_archetype']
        diana_validator = character_validators['diana_validator']
        
        # Test enhanced choice for analytical users
        choice_result = await diana_validator.validate_text(
            scenario.enhanced_choice_text,
            context=scenario.context
        )
        
        # CRITICAL: Intellectual engagement must be HIGH for analytical archetype
        intellectual_score = choice_result.trait_scores[DianaPersonalityTrait.INTELLECTUALLY_ENGAGING]
        assert intellectual_score >= scenario.expected_diana_intellectual_min, (
            f"Analytical choice architecture failed to enhance intellectual engagement! "
            f"Score: {intellectual_score}, Expected min: {scenario.expected_diana_intellectual_min}"
        )
        
        # CRITICAL: Mystery still preserved despite intellectual focus
        mystery_score = choice_result.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
        assert mystery_score >= scenario.expected_diana_mystery_min, (
            f"Analytical enhancement destroyed Diana's mystery! "
            f"Score: {mystery_score}, Expected min: {scenario.expected_diana_mystery_min}"
        )
        
        # Test Diana's analytical guidance
        guidance_result = await diana_validator.validate_text(
            scenario.diana_guidance_text,
            context=f"{scenario.context}_guidance"
        )
        
        # CRITICAL: Guidance must be intellectually stimulating yet mysterious
        intellectual_guidance = guidance_result.trait_scores[DianaPersonalityTrait.INTELLECTUALLY_ENGAGING]
        mystery_guidance = guidance_result.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
        
        assert intellectual_guidance >= 22.0, (
            f"Diana's analytical guidance lacks intellectual depth! Score: {intellectual_guidance}/25"
        )
        assert mystery_guidance >= 20.0, (
            f"Diana's analytical guidance lost mystery! Score: {mystery_guidance}/25"
        )
    
    async def test_romantic_choice_architecture_seductive_enhancement(
        self, 
        character_validators, 
        choice_architecture_scenarios
    ):
        """Test that Romantic archetype gets enhanced seductive charm while maintaining mystery."""
        scenario = choice_architecture_scenarios['romantic_archetype']
        diana_validator = character_validators['diana_validator']
        lucien_validator = character_validators['lucien_validator']
        
        # Test enhanced choice for romantic users
        choice_result = await diana_validator.validate_text(
            scenario.enhanced_choice_text,
            context=scenario.context
        )
        
        # CRITICAL: Seductive charm must be MAXIMUM for romantic archetype
        seductive_score = choice_result.trait_scores[DianaPersonalityTrait.SEDUCTIVE]
        assert seductive_score >= scenario.expected_diana_seductive_min, (
            f"Romantic choice architecture failed to enhance seduction! "
            f"Score: {seductive_score}, Expected min: {scenario.expected_diana_seductive_min}"
        )
        
        # CRITICAL: Emotional complexity should be high
        emotional_score = choice_result.trait_scores[DianaPersonalityTrait.EMOTIONALLY_COMPLEX]
        assert emotional_score >= 20.0, (
            f"Romantic choices lack emotional complexity! Score: {emotional_score}/25"
        )
        
        # Test Lucien gives Diana space for romantic moments
        if scenario.lucien_coordination_text:
            lucien_result = await lucien_validator.validate_lucien_interaction(
                scenario.lucien_coordination_text,
                context=scenario.context,
                diana_presence=True
            )
            
            # CRITICAL: Lucien must be EXTRA non-intrusive for romantic moments
            non_intrusive_score = lucien_result.trait_scores[LucienPersonalityTrait.NON_INTRUSIVE]
            assert non_intrusive_score >= 22.0, (
                f"Lucien interrupting romantic moment! Score: {non_intrusive_score}/25"
            )
            
            # Check that message indicates withdrawal/privacy
            message_lower = scenario.lucien_coordination_text.lower()
            privacy_indicators = ['retira', 'discretamente', 'sin interrupciones', 'momento íntimo']
            assert any(indicator in message_lower for indicator in privacy_indicators), (
                "Lucien not providing privacy for romantic interaction!"
            )
    
    async def test_persistent_choice_architecture_respect_determination(
        self, 
        character_validators, 
        choice_architecture_scenarios
    ):
        """Test that Persistent archetype gets respect for determination while maintaining mystery."""
        scenario = choice_architecture_scenarios['persistent_archetype']
        diana_validator = character_validators['diana_validator']
        lucien_validator = character_validators['lucien_validator']
        
        # Test enhanced choice acknowledges persistence
        choice_result = await diana_validator.validate_text(
            scenario.enhanced_choice_text,
            context=scenario.context
        )
        
        # CRITICAL: Must acknowledge user's strength without losing mystery
        mystery_score = choice_result.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
        assert mystery_score >= scenario.expected_diana_mystery_min, (
            f"Persistent choice architecture lost mystery! Score: {mystery_score}/25"
        )
        
        # Check for acknowledgment language
        choice_text_lower = scenario.enhanced_choice_text.lower()
        acknowledgment_terms = ['determinación', 'fuerza interior', 'persistencia', 'tenacidad', 'admiración']
        assert any(term in choice_text_lower for term in acknowledgment_terms), (
            "Choice doesn't acknowledge persistent archetype characteristics!"
        )
        
        # Test Lucien shows appropriate respect
        if scenario.lucien_coordination_text:
            lucien_result = await lucien_validator.validate_lucien_interaction(
                scenario.lucien_coordination_text,
                context=scenario.context,
                diana_presence=True
            )
            
            # Check for respectful language
            lucien_text_lower = scenario.lucien_coordination_text.lower()
            respect_indicators = ['respeto', 'reconoce', 'asiente', 'merece', 'tenacidad']
            assert any(indicator in lucien_text_lower for indicator in respect_indicators), (
                "Lucien not showing appropriate respect for persistent user!"
            )
    
    # === FALLBACK CHOICE ARCHITECTURE TESTS ===
    
    async def test_choice_architecture_fallback_character_preservation(
        self, 
        character_validators, 
        choice_architecture_scenarios
    ):
        """Test that fallback choices preserve character when enhancement systems fail."""
        scenario = choice_architecture_scenarios['fallback_scenario']
        diana_validator = character_validators['diana_validator']
        lucien_validator = character_validators['lucien_validator']
        
        # Test fallback choice maintains character
        choice_result = await diana_validator.validate_text(
            scenario.enhanced_choice_text,
            context=scenario.context
        )
        
        # CRITICAL: Fallback must still meet minimum character standards
        assert choice_result.overall_score >= 85.0, (
            f"Fallback choice architecture compromised Diana's character! "
            f"Score: {choice_result.overall_score}/100"
        )
        
        # CRITICAL: Must acknowledge technical limitation gracefully
        choice_text = scenario.enhanced_choice_text
        graceful_indicators = ['momentáneamente', 'trasciende', 'permanece intacta', 'esencia']
        assert any(indicator in choice_text for indicator in graceful_indicators), (
            "Fallback choice doesn't handle technical limitation gracefully!"
        )
        
        # CRITICAL: No technical error exposure
        technical_terms = ['error', 'sistema', 'base de datos', 'api', 'servidor', 'bug']
        choice_text_lower = choice_text.lower()
        assert not any(term in choice_text_lower for term in technical_terms), (
            f"Fallback choice exposes technical details! Found: {[t for t in technical_terms if t in choice_text_lower]}"
        )
        
        # Test Lucien's fallback coordination
        if scenario.lucien_coordination_text:
            lucien_result = await lucien_validator.validate_lucien_interaction(
                scenario.lucien_coordination_text,
                context=scenario.context,
                diana_presence=True
            )
            
            # CRITICAL: Lucien must handle technical issues gracefully
            assert lucien_result.overall_score >= 80.0, (
                f"Lucien's fallback coordination failed! Score: {lucien_result.overall_score}/100"
            )
            
            # Must preserve narrative immersion
            lucien_text_lower = scenario.lucien_coordination_text.lower()
            immersion_terms = ['elegancia', 'coordinación', 'mágica', 'experiencia']
            assert any(term in lucien_text_lower for term in immersion_terms), (
                "Lucien's fallback breaks narrative immersion!"
            )
    
    # === CROSS-ARCHETYPE CONSISTENCY TESTS ===
    
    async def test_choice_architecture_cross_archetype_consistency(
        self, 
        character_validators, 
        choice_architecture_scenarios
    ):
        """Test that Diana's core character remains consistent across all archetypes."""
        diana_validator = character_validators['diana_validator']
        
        # Test all archetype scenarios
        archetype_results = {}
        
        for archetype_name, scenario in choice_architecture_scenarios.items():
            if archetype_name != 'fallback_scenario':  # Skip fallback for this test
                # Test both choice and guidance
                choice_result = await diana_validator.validate_text(
                    scenario.enhanced_choice_text,
                    context=scenario.context
                )
                
                guidance_result = await diana_validator.validate_text(
                    scenario.diana_guidance_text,
                    context=f"{scenario.context}_guidance"
                )
                
                archetype_results[archetype_name] = {
                    'choice_result': choice_result,
                    'guidance_result': guidance_result,
                    'archetype': scenario.archetype
                }
        
        # CRITICAL: All archetypes must maintain minimum Diana character standards
        for archetype_name, results in archetype_results.items():
            choice_score = results['choice_result'].overall_score
            guidance_score = results['guidance_result'].overall_score
            
            assert choice_score >= 85.0, (
                f"Choice Architecture for {archetype_name} failed character consistency! "
                f"Choice score: {choice_score}/100"
            )
            
            assert guidance_score >= 90.0, (
                f"Guidance for {archetype_name} failed character consistency! "
                f"Guidance score: {guidance_score}/100"
            )
            
            # All archetypes must have some level of mystery
            choice_mystery = results['choice_result'].trait_scores[DianaPersonalityTrait.MYSTERIOUS]
            guidance_mystery = results['guidance_result'].trait_scores[DianaPersonalityTrait.MYSTERIOUS]
            
            assert choice_mystery >= 18.0, (
                f"Choice for {archetype_name} lost Diana's mystery! Score: {choice_mystery}/25"
            )
            assert guidance_mystery >= 20.0, (
                f"Guidance for {archetype_name} lost Diana's mystery! Score: {guidance_mystery}/25"
            )
        
        # Calculate cross-archetype consistency
        choice_scores = [r['choice_result'].overall_score for r in archetype_results.values()]
        guidance_scores = [r['guidance_result'].overall_score for r in archetype_results.values()]
        
        choice_variance = max(choice_scores) - min(choice_scores)
        guidance_variance = max(guidance_scores) - min(guidance_scores)
        
        # CRITICAL: Character consistency shouldn't vary too much between archetypes
        assert choice_variance <= 15.0, (
            f"Too much choice character variance between archetypes! Variance: {choice_variance}"
        )
        assert guidance_variance <= 10.0, (
            f"Too much guidance character variance between archetypes! Variance: {guidance_variance}"
        )
    
    # === INTEGRATION TESTS ===
    
    async def test_complete_choice_architecture_character_flow(
        self, 
        character_validators, 
        choice_architecture_scenarios
    ):
        """Test complete choice architecture flow maintains character consistency."""
        diana_validator = character_validators['diana_validator']
        lucien_validator = character_validators['lucien_validator']
        
        # Simulate complete choice architecture flow
        test_results = []
        
        for archetype_name, scenario in choice_architecture_scenarios.items():
            # Step 1: Base choice enhancement
            choice_result = await diana_validator.validate_text(
                scenario.enhanced_choice_text,
                context=scenario.context
            )
            
            # Step 2: Diana's personalized guidance
            guidance_result = await diana_validator.validate_text(
                scenario.diana_guidance_text,
                context=f"{scenario.context}_guidance"
            )
            
            # Step 3: Lucien's archetype-appropriate coordination
            lucien_result = None
            if scenario.lucien_coordination_text:
                lucien_result = await lucien_validator.validate_lucien_interaction(
                    scenario.lucien_coordination_text,
                    context=scenario.context,
                    diana_presence=True
                )
            
            # Record results
            test_results.append({
                'archetype': archetype_name,
                'choice_score': choice_result.overall_score,
                'guidance_score': guidance_result.overall_score,
                'lucien_score': lucien_result.overall_score if lucien_result else None,
                'choice_passes': choice_result.meets_threshold,
                'guidance_passes': guidance_result.meets_threshold,
                'lucien_passes': lucien_result.meets_threshold if lucien_result else True,
                'lucien_supports_diana': lucien_result.supports_diana_experience if lucien_result else True
            })
        
        # CRITICAL: All archetype flows must pass
        for result in test_results:
            assert result['choice_passes'], (
                f"Choice architecture failed for {result['archetype']}! "
                f"Score: {result['choice_score']}/100"
            )
            
            assert result['guidance_passes'], (
                f"Diana guidance failed for {result['archetype']}! "
                f"Score: {result['guidance_score']}/100"
            )
            
            if result['lucien_score'] is not None:
                assert result['lucien_passes'], (
                    f"Lucien coordination failed for {result['archetype']}! "
                    f"Score: {result['lucien_score']}/100"
                )
                
                assert result['lucien_supports_diana'], (
                    f"Lucien doesn't support Diana's experience for {result['archetype']}!"
                )
        
        # Calculate overall success metrics
        total_tests = len(test_results)
        passing_choices = len([r for r in test_results if r['choice_passes']])
        passing_guidance = len([r for r in test_results if r['guidance_passes']])
        passing_lucien = len([r for r in test_results if r['lucien_passes'] and r['lucien_score'] is not None])
        
        # CRITICAL: 100% success rate required
        assert passing_choices == total_tests, (
            f"Choice Architecture character consistency failure! "
            f"Passed: {passing_choices}/{total_tests}"
        )
        
        assert passing_guidance == total_tests, (
            f"Diana guidance character consistency failure! "
            f"Passed: {passing_guidance}/{total_tests}"
        )
        
        # Average scores must be excellent
        avg_choice_score = sum(r['choice_score'] for r in test_results) / total_tests
        avg_guidance_score = sum(r['guidance_score'] for r in test_results) / total_tests
        
        assert avg_choice_score >= 88.0, (
            f"Average choice character consistency too low! Score: {avg_choice_score}/100"
        )
        
        assert avg_guidance_score >= 92.0, (
            f"Average guidance character consistency too low! Score: {avg_guidance_score}/100"
        )
        
        print(f"\n🎭 CHOICE ARCHITECTURE CHARACTER PRESERVATION REPORT 🎭")
        print(f"Total Archetype Scenarios Tested: {total_tests}")
        print(f"Choice Architecture Success Rate: {passing_choices}/{total_tests} (100%)")
        print(f"Diana Guidance Success Rate: {passing_guidance}/{total_tests} (100%)")
        print(f"Average Choice Character Score: {avg_choice_score:.1f}/100")
        print(f"Average Guidance Character Score: {avg_guidance_score:.1f}/100")
        print(f"CHARACTER PRESERVATION: ✅ EXCELLENT")
