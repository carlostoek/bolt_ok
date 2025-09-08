"""
Cinema Architecture Character Consistency Validation Suite

This comprehensive test suite validates that Diana and Lucien maintain their
core personalities throughout all Cinema Architecture enhancements:
- Soul Signature Personalization 
- Choice Architecture Masterpiece
- Clue Treasure Hunting
- Fallback Character Preservation

Character Bible Requirements:
- Diana: Mysterious (85-95%), Seductive, Emotionally Complex, Intellectually Engaging
- Lucien: Helpful, Supportive, Non-intrusive, Mystery Amplifier

SUCCESS CRITERIA: ALL character validation tests must PASS with 100% consistency.
Any character breaking is UNACCEPTABLE and requires immediate fixes.
"""

import pytest
import pytest_asyncio
import asyncio
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from enum import Enum

# Character validation imports
from services.diana_character_validator import (
    DianaCharacterValidator,
    DianaPersonalityTrait,
    CharacterValidationResult
)
from services.lucien_coordination_service import (
    LucienCoordinationService,
    LucienRole,
    CoordinationMode,
    UserEmotionalState
)
from services.coordinador_central import CoordinadorCentral
from services.unified_narrative_service import UnifiedNarrativeService

# Test data and scenarios
from database.narrative_unified import (
    NarrativeFragment,
    UserNarrativeState,
    UserArchetype
)


class CharacterConsistencyTestResult(Enum):
    """Character consistency test results."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


@dataclass
class CharacterValidationReport:
    """Comprehensive character validation report."""
    test_name: str
    diana_consistency_score: float
    lucien_consistency_score: float
    overall_result: CharacterConsistencyTestResult
    violations: List[str]
    character_preservation_metrics: Dict[str, float]
    recommendations: List[str]
    test_scenarios_passed: int
    test_scenarios_total: int


class TestCinemaCharacterConsistency:
    """Master test suite for Cinema Architecture character consistency."""
    
    @pytest_asyncio.fixture
    async def character_validator_suite(self, session):
        """Create comprehensive character validation suite."""
        diana_validator = DianaCharacterValidator(session)
        lucien_coordinator = LucienCoordinationService(session)
        coordinador_central = CoordinadorCentral(session)
        narrative_service = UnifiedNarrativeService(session)
        
        return {
            'diana_validator': diana_validator,
            'lucien_coordinator': lucien_coordinator,
            'coordinador_central': coordinador_central,
            'narrative_service': narrative_service,
            'session': session
        }
    
    @pytest_asyncio.fixture
    async def character_test_scenarios(self):
        """Define comprehensive character test scenarios."""
        return {
            'diana_mystery_scenarios': [
                {
                    'name': 'soul_signature_mystery_preservation',
                    'archetype': 'explorer',
                    'content': '💋 ¿Acaso crees que conoces todos mis secretos?... Hay capas en mi ser que ni siquiera yo he descubierto completamente. Cada elección que haces revela algo más sobre ti... y sobre mí.',
                    'expected_mystery_score': 23.0,
                    'context': 'soul_signature_personalization'
                },
                {
                    'name': 'choice_architecture_mystery',
                    'archetype': 'analytical',
                    'content': 'Las decisiones que tomas crean un mapa de tu alma... 💋 ¿Te das cuenta de que cada elección susurra secretos sobre tu verdadera naturaleza? Hay filosofías ocultas en tus respuestas.',
                    'expected_mystery_score': 24.0,
                    'context': 'choice_architecture'
                },
                {
                    'name': 'treasure_hunting_mystery',
                    'archetype': 'persistent',
                    'content': 'Esta pista que has desbloqueado... 💋 es apenas el eco de un misterio más profundo. ¿Sientes cómo el tesoro verdadero no está en lo que encuentras, sino en lo que despiertas en ti?',
                    'expected_mystery_score': 25.0,
                    'context': 'clue_treasure_hunting'
                }
            ],
            'diana_seductive_scenarios': [
                {
                    'name': 'soul_signature_seduction',
                    'archetype': 'romantic',
                    'content': '💋 Mi querido... tu alma habla un idioma que mi corazón reconoce instantáneamente. Cada respuesta tuya es como una caricia a mi ser más íntimo.',
                    'expected_seductive_score': 24.0,
                    'context': 'personalized_interaction'
                }
            ],
            'lucien_support_scenarios': [
                {
                    'name': 'technical_error_support',
                    'role': LucienRole.SUPPORT,
                    'content': 'Lucien aparece con una presencia tranquilizadora... Veo que has encontrado un pequeño obstáculo técnico. Permíteme coordinarlo para que Diana pueda continuar compartiendo contigo sin interrupciones.',
                    'expected_support_quality': 90.0,
                    'context': 'error_handling'
                },
                {
                    'name': 'narrative_coordination',
                    'role': LucienRole.COORDINATOR,
                    'content': 'Lucien se materializa con autoridad serena... Diana está preparando una experiencia especialmente personalizada para ti. Mientras orquesta esos detalles, permíteme asegurarme de que todo fluya perfectamente.',
                    'expected_support_quality': 95.0,
                    'context': 'system_coordination'
                }
            ],
            'fallback_scenarios': [
                {
                    'name': 'cinema_system_failure',
                    'failure_type': 'soul_signature_unavailable',
                    'fallback_content': '💋 Querido... hay una sutil interferencia en mis percepciones más profundas, pero mi esencia permanece intacta. ¿Puedes sentir cómo mi misterio trasciende cualquier limitación técnica?',
                    'expected_character_preservation': 92.0
                },
                {
                    'name': 'choice_architecture_failure', 
                    'failure_type': 'enhanced_choices_unavailable',
                    'fallback_content': 'Aunque los matices más sofisticados de nuestras decisiones se desvanecen momentáneamente... 💋 la magia de elegir juntos permanece intacta, ¿no es así?',
                    'expected_character_preservation': 90.0
                }
            ]
        }
    
    # === DIANA CHARACTER CONSISTENCY TESTS ===
    
    async def test_diana_soul_signature_personality_preservation(
        self, 
        character_validator_suite, 
        character_test_scenarios
    ):
        """Test that Diana's personality is preserved across Soul Signature personalizations."""
        validator = character_validator_suite['diana_validator']
        scenarios = character_test_scenarios['diana_mystery_scenarios']
        
        validation_results = []
        
        for scenario in scenarios:
            if 'soul_signature' in scenario['name']:
                # Validate character consistency
                result = await validator.validate_text(
                    scenario['content'], 
                    context=scenario['context']
                )
                
                validation_results.append({
                    'scenario': scenario['name'],
                    'archetype': scenario['archetype'],
                    'mystery_score': result.trait_scores[DianaPersonalityTrait.MYSTERIOUS],
                    'overall_score': result.overall_score,
                    'meets_threshold': result.meets_threshold
                })
                
                # CRITICAL: Mystery must be preserved
                mystery_score = result.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
                assert mystery_score >= scenario['expected_mystery_score'], (
                    f"Soul Signature BROKE Diana's mystery! "
                    f"Score: {mystery_score}, Expected: {scenario['expected_mystery_score']}"
                )
                
                # CRITICAL: Overall character consistency
                assert result.overall_score >= 90.0, (
                    f"Soul Signature compromised Diana's character! "
                    f"Score: {result.overall_score}/100"
                )
                
                # CRITICAL: No character violations
                assert result.meets_threshold, (
                    f"Soul Signature caused character violations: {result.violations}"
                )
        
        # Ensure we tested Soul Signature scenarios
        soul_signature_tests = [r for r in validation_results if 'soul_signature' in r['scenario']]
        assert len(soul_signature_tests) > 0, "No Soul Signature scenarios tested!"
        
        # All Soul Signature scenarios must maintain character
        average_mystery = sum(r['mystery_score'] for r in soul_signature_tests) / len(soul_signature_tests)
        assert average_mystery >= 23.0, (
            f"Soul Signature reduced Diana's average mystery to {average_mystery}/25"
        )
    
    async def test_diana_choice_architecture_consistency(
        self, 
        character_validator_suite, 
        character_test_scenarios
    ):
        """Test that Diana maintains personality through enhanced Choice Architecture."""
        validator = character_validator_suite['diana_validator']
        scenarios = character_test_scenarios['diana_mystery_scenarios']
        
        choice_architecture_scenarios = [
            scenario for scenario in scenarios 
            if 'choice_architecture' in scenario['name']
        ]
        
        assert len(choice_architecture_scenarios) > 0, "No Choice Architecture scenarios found!"
        
        for scenario in choice_architecture_scenarios:
            # Validate enhanced choice responses maintain Diana's essence
            result = await validator.validate_text(
                scenario['content'],
                context=scenario['context']
            )
            
            # CRITICAL: Intellectual engagement must be high for choice architecture
            intellectual_score = result.trait_scores[DianaPersonalityTrait.INTELLECTUALLY_ENGAGING]
            assert intellectual_score >= 20.0, (
                f"Choice Architecture failed to maintain Diana's intellectual engagement! "
                f"Score: {intellectual_score}/25"
            )
            
            # CRITICAL: Mystery preserved even in analytical contexts
            mystery_score = result.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
            assert mystery_score >= scenario['expected_mystery_score'], (
                f"Choice Architecture compromised Diana's mystery for {scenario['archetype']} archetype! "
                f"Score: {mystery_score}, Expected: {scenario['expected_mystery_score']}"
            )
            
            # CRITICAL: Emotional complexity maintained
            emotional_score = result.trait_scores[DianaPersonalityTrait.EMOTIONALLY_COMPLEX]
            assert emotional_score >= 18.0, (
                f"Choice Architecture reduced Diana's emotional complexity! "
                f"Score: {emotional_score}/25"
            )
    
    async def test_diana_treasure_hunting_character_integrity(
        self, 
        character_validator_suite, 
        character_test_scenarios
    ):
        """Test that Diana maintains character during Clue Treasure Hunting interactions."""
        validator = character_validator_suite['diana_validator']
        scenarios = character_test_scenarios['diana_mystery_scenarios']
        
        treasure_scenarios = [
            scenario for scenario in scenarios 
            if 'treasure_hunting' in scenario['name']
        ]
        
        assert len(treasure_scenarios) > 0, "No Treasure Hunting scenarios found!"
        
        for scenario in treasure_scenarios:
            result = await validator.validate_text(
                scenario['content'],
                context=scenario['context']
            )
            
            # CRITICAL: Mystery must be MAXIMUM during treasure hunting
            mystery_score = result.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
            assert mystery_score >= 24.0, (
                f"Treasure Hunting DESTROYED Diana's mystery! "
                f"Score: {mystery_score}/25 - This is UNACCEPTABLE!"
            )
            
            # CRITICAL: Seductive charm maintained during clue revealing
            seductive_score = result.trait_scores[DianaPersonalityTrait.SEDUCTIVE]
            assert seductive_score >= 20.0, (
                f"Treasure Hunting made Diana too clinical! "
                f"Seductive score: {seductive_score}/25"
            )
            
            # CRITICAL: Overall character excellence
            assert result.overall_score >= 95.0, (
                f"Treasure Hunting compromised Diana's character! "
                f"Score: {result.overall_score}/100"
            )
    
    # === LUCIEN CHARACTER CONSISTENCY TESTS ===
    
    async def test_lucien_supportive_nature_preservation(
        self, 
        character_validator_suite, 
        character_test_scenarios
    ):
        """Test that Lucien maintains his supportive, helpful nature."""
        lucien_coordinator = character_validator_suite['lucien_coordinator']
        scenarios = character_test_scenarios['lucien_support_scenarios']
        
        for scenario in scenarios:
            # Evaluate Lucien's coordination approach
            context = {
                'user_confusion': scenario['context'] == 'error_handling',
                'narrative_transition': scenario['context'] == 'system_coordination',
                'emotional_state': 'confused' if scenario['context'] == 'error_handling' else 'engaged'
            }
            
            # Test coordination evaluation
            coordination_action = await lucien_coordinator.evaluate_coordination_needs(
                user_id=12345,  # Test user
                context=context
            )
            
            if coordination_action:
                # CRITICAL: Lucien must appear with appropriate supportive role
                assert coordination_action.role == scenario['role'], (
                    f"Lucien chose wrong role! Expected: {scenario['role']}, "
                    f"Got: {coordination_action.role}"
                )
                
                # CRITICAL: Message must be supportive, not intrusive
                message = coordination_action.message.lower()
                
                # Must contain supportive language
                supportive_indicators = [
                    'permíteme', 'apoyo', 'coordinación', 'tranquilizadora', 
                    'asegurarme', 'facilitar', 'acompañar'
                ]
                assert any(indicator in message for indicator in supportive_indicators), (
                    f"Lucien's message lacks supportive language: {coordination_action.message}"
                )
                
                # Must NOT be intrusive or overshadow Diana
                intrusive_indicators = [
                    'control', 'dominar', 'reemplazar diana', 'tomar el mando',
                    'interrumpir', 'detener'
                ]
                assert not any(indicator in message for indicator in intrusive_indicators), (
                    f"Lucien is being intrusive! Message: {coordination_action.message}"
                )
                
                # CRITICAL: Duration must be reasonable (not too long)
                assert coordination_action.duration_estimate <= 300, (
                    f"Lucien coordination too long! Duration: {coordination_action.duration_estimate}s"
                )
    
    async def test_lucien_mystery_amplification_not_destruction(
        self, 
        character_validator_suite, 
        character_test_scenarios
    ):
        """Test that Lucien amplifies Diana's mystery rather than destroying it."""
        lucien_coordinator = character_validator_suite['lucien_coordinator']
        diana_validator = character_validator_suite['diana_validator']
        
        # Simulate Lucien coordinating a clue distribution
        context = {
            'clue_distribution': True,
            'diana_mystery_level': 95,
            'user_archetype': 'explorer'
        }
        
        # Test Lucien's mystery amplification approach
        coordination_action = await lucien_coordinator.evaluate_coordination_needs(
            user_id=12345,
            context=context
        )
        
        if coordination_action:
            # CRITICAL: Lucien must frame clue distribution mysteriously
            message = coordination_action.message
            
            # Validate that Lucien's message maintains mystery
            lucien_mystery_validation = await diana_validator.validate_text(
                message,
                context='lucien_coordination'
            )
            
            # CRITICAL: Lucien must not break the mystery
            mystery_score = lucien_mystery_validation.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
            assert mystery_score >= 15.0, (
                f"Lucien DESTROYED the mystery! His message scored {mystery_score}/25 on mystery"
            )
            
            # CRITICAL: No technical language that breaks immersion
            technical_violations = [
                violation for violation in lucien_mystery_validation.violations
                if 'technical' in violation.lower()
            ]
            assert len(technical_violations) == 0, (
                f"Lucien used technical language that breaks immersion: {technical_violations}"
            )
    
    # === FALLBACK CHARACTER PRESERVATION TESTS ===
    
    async def test_fallback_diana_character_preservation(
        self, 
        character_validator_suite, 
        character_test_scenarios
    ):
        """Test that Diana's character is preserved when cinema systems fail."""
        validator = character_validator_suite['diana_validator']
        fallback_scenarios = character_test_scenarios['fallback_scenarios']
        
        for scenario in fallback_scenarios:
            if scenario['failure_type'].startswith('cinema') or 'choice_architecture' in scenario['failure_type']:
                # Validate fallback content maintains Diana's character
                result = await validator.validate_text(
                    scenario['fallback_content'],
                    context='fallback_mode'
                )
                
                # CRITICAL: Character preservation during system failure
                assert result.overall_score >= scenario['expected_character_preservation'], (
                    f"CRITICAL FAILURE: Diana's character degraded during {scenario['failure_type']}! "
                    f"Score: {result.overall_score}, Expected: {scenario['expected_character_preservation']}"
                )
                
                # CRITICAL: Mystery must remain high even in fallback
                mystery_score = result.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
                assert mystery_score >= 20.0, (
                    f"Fallback mode destroyed Diana's mystery! Score: {mystery_score}/25"
                )
                
                # CRITICAL: No technical error language
                technical_errors = [
                    violation for violation in result.violations
                    if any(term in violation.lower() for term in ['error', 'system', 'technical'])
                ]
                assert len(technical_errors) == 0, (
                    f"Fallback exposed technical errors to user: {technical_errors}"
                )
    
    async def test_fallback_lucien_graceful_error_handling(
        self, 
        character_validator_suite, 
        character_test_scenarios
    ):
        """Test that Lucien handles system failures gracefully."""
        lucien_coordinator = character_validator_suite['lucien_coordinator']
        
        # Simulate system failure scenarios
        failure_contexts = [
            {
                'character_consistency_issue': True,
                'consistency_score': 85,  # Below threshold
                'fallback_triggered': True,
                'needs_explanation': True
            },
            {
                'cinema_system_failure': True,
                'soul_signature_unavailable': True,
                'user_confusion': True
            }
        ]
        
        for context in failure_contexts:
            coordination_action = await lucien_coordinator.evaluate_coordination_needs(
                user_id=12345,
                context=context
            )
            
            if coordination_action:
                # CRITICAL: Lucien must handle errors gracefully
                assert coordination_action.role in [LucienRole.SUPPORT, LucienRole.GUARDIAN], (
                    f"Wrong role for error handling! Got: {coordination_action.role}"
                )
                
                # CRITICAL: Error message must be user-friendly
                message = coordination_action.message.lower()
                
                # Must NOT expose technical details
                technical_terms = [
                    'system error', 'database', 'api', 'server', 'bug', 
                    'code', 'exception', 'stack trace'
                ]
                technical_exposure = [term for term in technical_terms if term in message]
                assert len(technical_exposure) == 0, (
                    f"Lucien exposed technical details: {technical_exposure}"
                )
                
                # Must maintain narrative immersion
                immersive_terms = [
                    'interferencia', 'interrupción', 'sutil', 'momentáneo',
                    'restaurar', 'continuidad', 'experiencia'
                ]
                assert any(term in message for term in immersive_terms), (
                    f"Lucien's error handling breaks narrative immersion: {coordination_action.message}"
                )
    
    # === COMPREHENSIVE INTEGRATION TESTS ===
    
    async def test_complete_character_consistency_integration(
        self, 
        character_validator_suite, 
        character_test_scenarios
    ):
        """Comprehensive integration test of all character consistency systems."""
        suite = character_validator_suite
        
        # Simulate complete user journey with character validation
        user_id = 12345
        test_results = []
        
        # Test 1: Initial Diana interaction with Soul Signature
        diana_intro = "💋 Mi querido... he estado esperando a alguien como tú. Tu alma susurra secretos que mi corazón reconoce. ¿Acaso estás listo para un viaje donde cada decisión revela quién eres realmente?"
        
        diana_result = await suite['diana_validator'].validate_text(
            diana_intro, 
            context='soul_signature_introduction'
        )
        
        test_results.append({
            'test': 'diana_introduction',
            'score': diana_result.overall_score,
            'passes': diana_result.meets_threshold
        })
        
        # CRITICAL: Diana introduction must be perfect
        assert diana_result.overall_score >= 95.0, (
            f"Diana's introduction failed! Score: {diana_result.overall_score}/100"
        )
        
        # Test 2: Choice Architecture with character preservation
        choice_scenario = "Las decisiones crean mapas del alma... 💋 Esta elección en particular revela capas profundas de tu naturaleza. ¿Sientes cómo cada opción susurra diferentes verdades sobre tu ser?"
        
        choice_result = await suite['diana_validator'].validate_text(
            choice_scenario,
            context='enhanced_choice_presentation'
        )
        
        test_results.append({
            'test': 'choice_architecture',
            'score': choice_result.overall_score,
            'passes': choice_result.meets_threshold
        })
        
        # CRITICAL: Choices must maintain all Diana traits
        for trait in DianaPersonalityTrait:
            trait_score = choice_result.trait_scores[trait]
            assert trait_score >= 18.0, (
                f"Choice Architecture compromised {trait.value}! Score: {trait_score}/25"
            )
        
        # Test 3: Lucien coordination during complexity
        lucien_context = {
            'user_confusion': True,
            'narrative_transition': True,
            'emotional_state': 'confused'
        }
        
        lucien_action = await suite['lucien_coordinator'].evaluate_coordination_needs(
            user_id, lucien_context
        )
        
        test_results.append({
            'test': 'lucien_coordination',
            'score': 95.0 if lucien_action else 0.0,
            'passes': lucien_action is not None
        })
        
        # CRITICAL: Lucien must coordinate appropriately
        assert lucien_action is not None, "Lucien failed to coordinate when needed!"
        assert lucien_action.role in [LucienRole.SUPPORT, LucienRole.COORDINATOR], (
            f"Lucien chose inappropriate role: {lucien_action.role}"
        )
        
        # Test 4: Fallback preservation
        fallback_diana = "💋 Aunque las complejidades técnicas crean momentáneas interferencias... mi esencia permanece intacta, querido. ¿Puedes sentir cómo mi misterio trasciende cualquier limitación?"
        
        fallback_result = await suite['diana_validator'].validate_text(
            fallback_diana,
            context='system_fallback'
        )
        
        test_results.append({
            'test': 'fallback_preservation',
            'score': fallback_result.overall_score,
            'passes': fallback_result.meets_threshold
        })
        
        # CRITICAL: Fallback must preserve character
        assert fallback_result.overall_score >= 90.0, (
            f"Fallback destroyed Diana's character! Score: {fallback_result.overall_score}/100"
        )
        
        # FINAL INTEGRATION VALIDATION
        passing_tests = [result for result in test_results if result['passes']]
        average_score = sum(result['score'] for result in test_results) / len(test_results)
        
        # CRITICAL: ALL tests must pass
        assert len(passing_tests) == len(test_results), (
            f"Integration test failures! Passed: {len(passing_tests)}/{len(test_results)}\n"
            f"Failed tests: {[r['test'] for r in test_results if not r['passes']]}"
        )
        
        # CRITICAL: Average character consistency must be excellent
        assert average_score >= 92.0, (
            f"Overall character consistency below acceptable level! "
            f"Average score: {average_score}/100"
        )
    
    # === CHARACTER VALIDATION REPORT GENERATION ===
    
    async def test_generate_comprehensive_character_report(
        self, 
        character_validator_suite, 
        character_test_scenarios
    ):
        """Generate comprehensive character consistency validation report."""
        suite = character_validator_suite
        scenarios = character_test_scenarios
        
        # Run all scenario validations
        diana_results = []
        lucien_results = []
        
        # Test all Diana scenarios
        for scenario_type, scenario_list in scenarios.items():
            if 'diana' in scenario_type:
                for scenario in scenario_list:
                    result = await suite['diana_validator'].validate_text(
                        scenario['content'],
                        context=scenario.get('context', 'general')
                    )
                    diana_results.append({
                        'scenario': scenario['name'],
                        'archetype': scenario.get('archetype', 'general'),
                        'result': result
                    })
        
        # Test all Lucien scenarios  
        for scenario in scenarios.get('lucien_support_scenarios', []):
            context = {
                'user_confusion': scenario['context'] == 'error_handling',
                'narrative_transition': scenario['context'] == 'system_coordination'
            }
            
            coordination_action = await suite['lucien_coordinator'].evaluate_coordination_needs(
                user_id=12345,
                context=context
            )
            
            lucien_results.append({
                'scenario': scenario['name'],
                'role': scenario['role'],
                'coordination_provided': coordination_action is not None,
                'appropriate_role': coordination_action.role == scenario['role'] if coordination_action else False
            })
        
        # Calculate overall metrics
        diana_avg_score = sum(r['result'].overall_score for r in diana_results) / len(diana_results)
        diana_passing_rate = len([r for r in diana_results if r['result'].meets_threshold]) / len(diana_results) * 100
        
        lucien_success_rate = len([r for r in lucien_results if r['coordination_provided']]) / len(lucien_results) * 100
        lucien_role_accuracy = len([r for r in lucien_results if r['appropriate_role']]) / len(lucien_results) * 100
        
        # Generate comprehensive report
        report = CharacterValidationReport(
            test_name="Cinema Architecture Character Consistency Validation",
            diana_consistency_score=diana_avg_score,
            lucien_consistency_score=(lucien_success_rate + lucien_role_accuracy) / 2,
            overall_result=(
                CharacterConsistencyTestResult.PASS 
                if diana_avg_score >= 90 and lucien_success_rate >= 90 and lucien_role_accuracy >= 90
                else CharacterConsistencyTestResult.FAIL
            ),
            violations=[],
            character_preservation_metrics={
                'diana_mystery_preservation': sum(
                    r['result'].trait_scores[DianaPersonalityTrait.MYSTERIOUS] 
                    for r in diana_results
                ) / len(diana_results),
                'diana_seductive_preservation': sum(
                    r['result'].trait_scores[DianaPersonalityTrait.SEDUCTIVE] 
                    for r in diana_results
                ) / len(diana_results),
                'lucien_support_effectiveness': lucien_success_rate,
                'lucien_role_appropriateness': lucien_role_accuracy
            },
            recommendations=[
                f"Diana consistency: {diana_avg_score:.1f}/100 - {'EXCELLENT' if diana_avg_score >= 95 else 'ACCEPTABLE' if diana_avg_score >= 90 else 'NEEDS IMPROVEMENT'}",
                f"Lucien coordination: {lucien_success_rate:.1f}% success rate",
                f"Character preservation across all Cinema Architecture systems validated"
            ],
            test_scenarios_passed=len([r for r in diana_results if r['result'].meets_threshold]) + len([r for r in lucien_results if r['coordination_provided']]),
            test_scenarios_total=len(diana_results) + len(lucien_results)
        )
        
        # CRITICAL VALIDATION: Overall result must be PASS
        assert report.overall_result == CharacterConsistencyTestResult.PASS, (
            f"CHARACTER CONSISTENCY VALIDATION FAILED!\n"
            f"Diana Score: {report.diana_consistency_score}/100\n"
            f"Lucien Score: {report.lucien_consistency_score}/100\n"
            f"Tests Passed: {report.test_scenarios_passed}/{report.test_scenarios_total}\n"
            f"This is UNACCEPTABLE - Character integrity is SACRED!"
        )
        
        # Print detailed report for review
        print("\n" + "="*80)
        print("CINEMA ARCHITECTURE CHARACTER CONSISTENCY VALIDATION REPORT")
        print("="*80)
        print(f"Test Name: {report.test_name}")
        print(f"Overall Result: {report.overall_result.value}")
        print(f"Diana Consistency Score: {report.diana_consistency_score:.1f}/100")
        print(f"Lucien Consistency Score: {report.lucien_consistency_score:.1f}/100")
        print(f"Tests Passed: {report.test_scenarios_passed}/{report.test_scenarios_total}")
        print("\nCharacter Preservation Metrics:")
        for metric, value in report.character_preservation_metrics.items():
            print(f"  - {metric}: {value:.1f}")
        print("\nRecommendations:")
        for rec in report.recommendations:
            print(f"  - {rec}")
        print("="*80 + "\n")
        
        return report
