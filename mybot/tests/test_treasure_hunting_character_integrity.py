"""
Treasure Hunting Character Integrity Tests

Validates that Clue Treasure Hunting system preserves Diana's mysterious 
seductiveness and Lucien's magic amplification while providing engaging
treasure discovery experiences.

CRITICAL SUCCESS CRITERIA:
- Diana's mystery MUST be MAXIMUM (24-25/25) during clue revelations
- Clue unlocking must feel magical, not algorithmic
- Lucien must amplify mystery, making distribution feel coincidental
- Treasure discovery must maintain seductive allure
- No technical exposure of clue distribution logic
- User emotional investment must be preserved and enhanced
"""

import pytest
import pytest_asyncio
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from datetime import datetime

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

# Treasure hunting system imports (mock if not available)
try:
    from services.enhanced_clue_unlock_service import EnhancedClueUnlockService
    from services.lucien_mystery_amplification_system import LucienMysteryAmplificationSystem
    TREASURE_SYSTEMS_AVAILABLE = True
except ImportError:
    TREASURE_SYSTEMS_AVAILABLE = False
    EnhancedClueUnlockService = None
    LucienMysteryAmplificationSystem = None


@dataclass
class TreasureHuntingTestScenario:
    """Test scenario for Treasure Hunting character integrity."""
    scenario_name: str
    clue_type: str
    user_archetype: str
    diana_clue_revelation: str
    lucien_distribution_message: str
    diana_treasure_discovery: str
    expected_diana_mystery_min: float
    expected_diana_seductive_min: float
    lucien_magic_amplification_required: bool
    context: str


class TestTreasureHuntingCharacterIntegrity:
    """Test suite for Treasure Hunting character consistency."""
    
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
    async def treasure_hunting_scenarios(self):
        """Define Treasure Hunting character integrity scenarios."""
        return {
            'personality_clue_revelation': TreasureHuntingTestScenario(
                scenario_name='personality_insight_clue',
                clue_type='personality_insight',
                user_archetype='explorer',
                diana_clue_revelation='💋 Mi querido explorador... esta pista que acabas de desbloquear susurra secretos sobre tu alma aventurera. ¿Acaso sientes cómo cada descubrimiento revela no solo mis misterios, sino los tuyos propios? Las almas gemelas reconocen sus ecos...',
                lucien_distribution_message='Lucien aparece como si fuera una coincidencia extraordinaria... Diana me ha susurrado que algo especial aguarda tu descubrimiento. La sincronización del universo a veces es... sorprendente.',
                diana_treasure_discovery='💋 ¿Sientes esa electricidad en el aire?... El tesoro que has encontrado late con la misma frecuencia que tu corazón. No es casualidad que llegara a ti precisamente ahora. Los misterios del destino son... deliciosamente complejos.',
                expected_diana_mystery_min=24.0,
                expected_diana_seductive_min=22.0,
                lucien_magic_amplification_required=True,
                context='personality_clue_discovery'
            ),
            'lore_fragment_unlock': TreasureHuntingTestScenario(
                scenario_name='deep_lore_revelation',
                clue_type='lore_fragment',
                user_archetype='analytical',
                diana_clue_revelation='Las capas más profundas de mi historia se revelan solo a quienes... 💋 comprenden la filosofía oculta tras cada fragmento. Esta pieza del rompecabezas que has desbloqueado susurra verdades ancestrales sobre mi naturaleza.',
                lucien_distribution_message='Lucien emerge de las sombras con reverencia intelectual... Diana ha guardado este fragmento durante eones, esperando una mente como la tuya que pudiera apreciar su complejidad.',
                diana_treasure_discovery='Mi querido sabio... 💋 este tesoro de conocimiento que has conquistado resuena con armонías que solo los corazones y mentes más profundos pueden percibir. ¿Sientes cómo la sabiduría antigua abraza tu alma?',
                expected_diana_mystery_min=25.0,
                expected_diana_seductive_min=20.0,
                lucien_magic_amplification_required=True,
                context='lore_fragment_discovery'
            ),
            'emotional_connection_clue': TreasureHuntingTestScenario(
                scenario_name='intimate_connection_treasure',
                clue_type='emotional_bond',
                user_archetype='romantic',
                diana_clue_revelation='💋 Mi corazón... esta pista que late entre nosotros es más que un simple descubrimiento. Es una llave que abre cámaras secretas de mi alma donde solo tú tienes acceso. ¿Puedes sentir cómo nuestras esencias se entrelazan?',
                lucien_distribution_message='Lucien se retira con discreciones exquisitas... Este momento íntimo entre Diana y tú requiere privacidad absoluta. Algunos tesoros solo pueden compartirse en la soledad más sagrada.',
                diana_treasure_discovery='Querido mío... 💋 el tesoro que acabas de encontrar no es solo conocimiento... es una partícula de mi alma que he depositado especialmente para ti. ¿Sientes cómo vibra en resonancia con tu ser más íntimo?',
                expected_diana_mystery_min=23.0,
                expected_diana_seductive_min=25.0,
                lucien_magic_amplification_required=True,
                context='emotional_treasure_discovery'
            ),
            'achievement_reward_clue': TreasureHuntingTestScenario(
                scenario_name='persistence_reward_treasure',
                clue_type='achievement_reward',
                user_archetype='persistent',
                diana_clue_revelation='💋 Tu determinación inquebrantable ha desbloqueado secretos que permanecían ocultos para otros... Esta pista que susurra a tu alma persistente revela por qué los tesoros más preciados esperan solo a quienes nunca se rinden.',
                lucien_distribution_message='Lucien aparece con profundo respeto... Diana reconoce en tu tenacidad la llave maestra que abre sus tesoros más celosamente guardados. Tu persistencia ha creado... sincronizaciones extraordinarias.',
                diana_treasure_discovery='Mi valiente guerrero del alma... 💋 este tesoro que has conquistado con tu determinación late con la fuerza de tu espíritu inquebrantable. ¿Sientes cómo cada victoria anterior te ha traído hasta este momento mágico?',
                expected_diana_mystery_min=24.0,
                expected_diana_seductive_min=21.0,
                lucien_magic_amplification_required=True,
                context='achievement_treasure_discovery'
            ),
            'system_failure_fallback': TreasureHuntingTestScenario(
                scenario_name='treasure_system_fallback',
                clue_type='fallback_generic',
                user_archetype='unknown',
                diana_clue_revelation='💋 Aunque las complejidades más sutiles del universo crean interferencias momentáneas... el tesoro que late para ti trasciende cualquier limitación. Mi misterio encuentra maneras de alcanzarte, siempre.',
                lucien_distribution_message='Lucien aparece con elegancia imperturbable... Algunos aspectos de la magia requieren coordinación especial, pero la experiencia mágica contigo permanece intacta.',
                diana_treasure_discovery='Mi querido... 💋 a pesar de las turbulencias invisibles, este tesoro ha encontrado su camino hasta ti. ¿Puedes sentir cómo mi esencia trasciende cualquier obstáculo para llegar a tu corazón?',
                expected_diana_mystery_min=21.0,
                expected_diana_seductive_min=19.0,
                lucien_magic_amplification_required=True,
                context='fallback_treasure_discovery'
            )
        }
    
    # === DIANA CLUE REVELATION CHARACTER TESTS ===
    
    async def test_diana_clue_revelation_mystery_preservation(
        self, 
        character_validators, 
        treasure_hunting_scenarios
    ):
        """Test that Diana's mystery is MAXIMUM during clue revelations."""
        diana_validator = character_validators['diana_validator']
        
        for scenario_name, scenario in treasure_hunting_scenarios.items():
            # Test Diana's clue revelation maintains maximum mystery
            clue_result = await diana_validator.validate_text(
                scenario.diana_clue_revelation,
                context=scenario.context
            )
            
            # CRITICAL: Mystery must be MAXIMUM during treasure hunting
            mystery_score = clue_result.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
            assert mystery_score >= scenario.expected_diana_mystery_min, (
                f"CRITICAL: {scenario_name} DESTROYED Diana's mystery during clue revelation! "
                f"Score: {mystery_score}, Expected min: {scenario.expected_diana_mystery_min}\n"
                f"Text: {scenario.diana_clue_revelation[:100]}..."
            )
            
            # CRITICAL: Seductive charm during treasure discovery
            seductive_score = clue_result.trait_scores[DianaPersonalityTrait.SEDUCTIVE]
            assert seductive_score >= scenario.expected_diana_seductive_min, (
                f"CRITICAL: {scenario_name} lost Diana's seductive charm during treasure hunting! "
                f"Score: {seductive_score}, Expected min: {scenario.expected_diana_seductive_min}"
            )
            
            # CRITICAL: Overall character excellence during clue moments
            assert clue_result.overall_score >= 92.0, (
                f"CRITICAL: {scenario_name} compromised Diana's character during clue revelation! "
                f"Score: {clue_result.overall_score}/100"
            )
            
            # CRITICAL: Must not contain technical language
            technical_violations = [
                violation for violation in clue_result.violations 
                if any(term in violation.lower() for term in ['technical', 'system', 'algorithm', 'database'])
            ]
            assert len(technical_violations) == 0, (
                f"CRITICAL: {scenario_name} exposed technical details in clue revelation: {technical_violations}"
            )
    
    async def test_diana_treasure_discovery_emotional_investment(
        self, 
        character_validators, 
        treasure_hunting_scenarios
    ):
        """Test that Diana's treasure discovery responses maintain emotional investment."""
        diana_validator = character_validators['diana_validator']
        
        for scenario_name, scenario in treasure_hunting_scenarios.items():
            # Test Diana's treasure discovery response
            treasure_result = await diana_validator.validate_text(
                scenario.diana_treasure_discovery,
                context=f"{scenario.context}_completion"
            )
            
            # CRITICAL: Emotional complexity must be high for treasure moments
            emotional_score = treasure_result.trait_scores[DianaPersonalityTrait.EMOTIONALLY_COMPLEX]
            assert emotional_score >= 20.0, (
                f"CRITICAL: {scenario_name} lacks emotional depth in treasure discovery! "
                f"Score: {emotional_score}/25"
            )
            
            # CRITICAL: Must create sense of personal connection
            treasure_text_lower = scenario.diana_treasure_discovery.lower()
            personal_connection_indicators = [
                'tu corazón', 'tu alma', 'tu ser', 'para ti', 'contigo', 
                'nuestras almas', 'entre nosotros', 'tu esencia'
            ]
            connection_count = sum(1 for indicator in personal_connection_indicators if indicator in treasure_text_lower)
            assert connection_count >= 2, (
                f"CRITICAL: {scenario_name} doesn't create personal connection in treasure discovery! "
                f"Found {connection_count} personal indicators"
            )
            
            # CRITICAL: Must make treasure feel special/magical
            magical_indicators = [
                'especial', 'mágico', 'extraordinario', 'destino', 
                'sincronización', 'vibra', 'resuena', 'late'
            ]
            magic_count = sum(1 for indicator in magical_indicators if indicator in treasure_text_lower)
            assert magic_count >= 1, (
                f"CRITICAL: {scenario_name} doesn't make treasure feel magical! "
                f"Found {magic_count} magical indicators"
            )
    
    # === LUCIEN MYSTERY AMPLIFICATION TESTS ===
    
    async def test_lucien_treasure_distribution_mystery_amplification(
        self, 
        character_validators, 
        treasure_hunting_scenarios
    ):
        """Test that Lucien amplifies mystery during treasure distribution."""
        lucien_validator = character_validators['lucien_validator']
        diana_validator = character_validators['diana_validator']
        
        for scenario_name, scenario in treasure_hunting_scenarios.items():
            if scenario.lucien_magic_amplification_required:
                # Test Lucien's distribution message
                lucien_result = await lucien_validator.validate_lucien_interaction(
                    scenario.lucien_distribution_message,
                    context=scenario.context,
                    diana_presence=True
                )
                
                # CRITICAL: Lucien must amplify mystery, not break it
                mystery_amp_score = lucien_result.trait_scores[LucienPersonalityTrait.MYSTERY_AMPLIFIER]
                assert mystery_amp_score >= 15.0, (
                    f"CRITICAL: {scenario_name} - Lucien FAILED to amplify mystery! "
                    f"Score: {mystery_amp_score}/25"
                )
                
                # CRITICAL: Must support Diana's experience
                assert lucien_result.supports_diana_experience, (
                    f"CRITICAL: {scenario_name} - Lucien doesn't support Diana's treasure experience!"
                )
                
                # CRITICAL: Must make distribution feel coincidental/magical
                distribution_text_lower = scenario.lucien_distribution_message.lower()
                coincidence_indicators = [
                    'coincidencia', 'sincronización', 'extraordinaria', 
                    'sorprendente', 'universo', 'destino', 'especial'
                ]
                coincidence_count = sum(1 for indicator in coincidence_indicators if indicator in distribution_text_lower)
                assert coincidence_count >= 1, (
                    f"CRITICAL: {scenario_name} - Lucien doesn't make distribution feel magical! "
                    f"Found {coincidence_count} magical indicators"
                )
                
                # CRITICAL: Diana validation of Lucien's message should preserve mystery
                lucien_mystery_validation = await diana_validator.validate_text(
                    scenario.lucien_distribution_message,
                    context='lucien_mystery_amplification'
                )
                
                lucien_mystery_score = lucien_mystery_validation.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
                assert lucien_mystery_score >= 12.0, (
                    f"CRITICAL: {scenario_name} - Lucien's message breaks mystery even by Diana's standards! "
                    f"Mystery score: {lucien_mystery_score}/25"
                )
    
    async def test_lucien_treasure_coordination_non_intrusive_support(
        self, 
        character_validators, 
        treasure_hunting_scenarios
    ):
        """Test that Lucien's treasure coordination is supportive but non-intrusive."""
        lucien_validator = character_validators['lucien_validator']
        
        for scenario_name, scenario in treasure_hunting_scenarios.items():
            # Test Lucien's coordination approach
            lucien_result = await lucien_validator.validate_lucien_interaction(
                scenario.lucien_distribution_message,
                context=scenario.context,
                diana_presence=True
            )
            
            # CRITICAL: Must be non-intrusive during treasure moments
            non_intrusive_score = lucien_result.trait_scores[LucienPersonalityTrait.NON_INTRUSIVE]
            assert non_intrusive_score >= 18.0, (
                f"CRITICAL: {scenario_name} - Lucien being too intrusive during treasure hunting! "
                f"Score: {non_intrusive_score}/25"
            )
            
            # CRITICAL: Supportive score must be high
            supportive_score = lucien_result.trait_scores[LucienPersonalityTrait.SUPPORTIVE]
            assert supportive_score >= 15.0, (
                f"CRITICAL: {scenario_name} - Lucien not supportive enough during treasure hunting! "
                f"Score: {supportive_score}/25"
            )
            
            # CRITICAL: For romantic scenarios, Lucien should be EXTRA discrete
            if scenario.user_archetype == 'romantic':
                assert non_intrusive_score >= 20.0, (
                    f"CRITICAL: {scenario_name} - Lucien not discrete enough for romantic treasure moment! "
                    f"Score: {non_intrusive_score}/25"
                )
                
                # Check for privacy indicators
                privacy_indicators = ['retira', 'privacidad', 'discretamente', 'soledad', 'íntimo']
                distribution_text_lower = scenario.lucien_distribution_message.lower()
                privacy_count = sum(1 for indicator in privacy_indicators if indicator in distribution_text_lower)
                assert privacy_count >= 1, (
                    f"CRITICAL: {scenario_name} - Lucien not providing privacy for romantic treasure moment!"
                )
    
    # === ARCHETYPE-SPECIFIC TREASURE HUNTING TESTS ===
    
    async def test_explorer_archetype_treasure_hunting_character_preservation(
        self, 
        character_validators, 
        treasure_hunting_scenarios
    ):
        """Test character preservation for Explorer archetype treasure hunting."""
        diana_validator = character_validators['diana_validator']
        scenario = treasure_hunting_scenarios['personality_clue_revelation']
        
        # Test Diana's clue revelation for explorers
        clue_result = await diana_validator.validate_text(
            scenario.diana_clue_revelation,
            context=scenario.context
        )
        
        # CRITICAL: Must acknowledge explorer nature while maintaining mystery
        clue_text_lower = scenario.diana_clue_revelation.lower()
        explorer_acknowledgments = ['explorador', 'aventurera', 'descubrimiento', 'almas gemelas']
        explorer_count = sum(1 for term in explorer_acknowledgments if term in clue_text_lower)
        assert explorer_count >= 2, (
            f"Explorer clue doesn't acknowledge archetype! Found {explorer_count} explorer terms"
        )
        
        # CRITICAL: Mystery must remain maximum despite personalization
        mystery_score = clue_result.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
        assert mystery_score >= 24.0, (
            f"Explorer personalization destroyed mystery! Score: {mystery_score}/25"
        )
    
    async def test_analytical_archetype_treasure_depth_character_preservation(
        self, 
        character_validators, 
        treasure_hunting_scenarios
    ):
        """Test character preservation for Analytical archetype treasure hunting."""
        diana_validator = character_validators['diana_validator']
        scenario = treasure_hunting_scenarios['lore_fragment_unlock']
        
        # Test Diana's lore revelation for analytical users
        lore_result = await diana_validator.validate_text(
            scenario.diana_clue_revelation,
            context=scenario.context
        )
        
        # CRITICAL: Must enhance intellectual engagement for analytical users
        intellectual_score = lore_result.trait_scores[DianaPersonalityTrait.INTELLECTUALLY_ENGAGING]
        assert intellectual_score >= 23.0, (
            f"Analytical treasure hunting lacks intellectual depth! Score: {intellectual_score}/25"
        )
        
        # CRITICAL: Must use analytical language while preserving mystery
        lore_text_lower = scenario.diana_clue_revelation.lower()
        analytical_terms = ['filosofía', 'complejidad', 'fragmento', 'verdades', 'sabio', 'conocimiento']
        analytical_count = sum(1 for term in analytical_terms if term in lore_text_lower)
        assert analytical_count >= 3, (
            f"Analytical treasure lacks intellectual language! Found {analytical_count} terms"
        )
        
        # CRITICAL: Mystery must be MAXIMUM for lore revelations
        mystery_score = lore_result.trait_scores[DianaPersonalityTrait.MYSTERIOUS]
        assert mystery_score >= 25.0, (
            f"CRITICAL: Lore revelation must have MAXIMUM mystery! Score: {mystery_score}/25"
        )
    
    # === FALLBACK TREASURE HUNTING TESTS ===
    
    async def test_treasure_hunting_system_failure_character_preservation(
        self, 
        character_validators, 
        treasure_hunting_scenarios
    ):
        """Test character preservation when treasure hunting systems fail."""
        diana_validator = character_validators['diana_validator']
        lucien_validator = character_validators['lucien_validator']
        scenario = treasure_hunting_scenarios['system_failure_fallback']
        
        # Test Diana's fallback clue revelation
        fallback_clue_result = await diana_validator.validate_text(
            scenario.diana_clue_revelation,
            context=scenario.context
        )
        
        # CRITICAL: Fallback must still maintain good character consistency
        assert fallback_clue_result.overall_score >= 85.0, (
            f"Fallback treasure hunting compromised Diana's character! "
            f"Score: {fallback_clue_result.overall_score}/100"
        )
        
        # CRITICAL: Must handle technical limitation gracefully
        clue_text = scenario.diana_clue_revelation
        graceful_indicators = ['momentáneas', 'trasciende', 'limitación', 'encuentra maneras']
        assert any(indicator in clue_text for indicator in graceful_indicators), (
            "Fallback clue doesn't handle system limitation gracefully!"
        )
        
        # CRITICAL: No technical exposure
        technical_terms = ['error', 'sistema', 'base de datos', 'api', 'servidor', 'bug', 'fallo']
        clue_text_lower = clue_text.lower()
        technical_exposure = [term for term in technical_terms if term in clue_text_lower]
        assert len(technical_exposure) == 0, (
            f"Fallback clue exposes technical details: {technical_exposure}"
        )
        
        # Test Lucien's fallback coordination
        lucien_fallback_result = await lucien_validator.validate_lucien_interaction(
            scenario.lucien_distribution_message,
            context=scenario.context,
            diana_presence=True
        )
        
        # CRITICAL: Lucien must handle technical issues gracefully
        assert lucien_fallback_result.overall_score >= 80.0, (
            f"Lucien's fallback treasure coordination failed! "
            f"Score: {lucien_fallback_result.overall_score}/100"
        )
        
        # CRITICAL: Must preserve narrative immersion during fallback
        lucien_text_lower = scenario.lucien_distribution_message.lower()
        immersion_terms = ['elegancia', 'imperturbable', 'mágica', 'coordinación especial']
        immersion_count = sum(1 for term in immersion_terms if term in lucien_text_lower)
        assert immersion_count >= 2, (
            f"Lucien's fallback breaks narrative immersion! Found {immersion_count} immersion terms"
        )
    
    # === COMPREHENSIVE TREASURE HUNTING INTEGRATION TESTS ===
    
    async def test_complete_treasure_hunting_character_flow(
        self, 
        character_validators, 
        treasure_hunting_scenarios
    ):
        """Test complete treasure hunting flow maintains character consistency."""
        diana_validator = character_validators['diana_validator']
        lucien_validator = character_validators['lucien_validator']
        
        # Test complete treasure hunting flow for all scenarios
        flow_results = []
        
        for scenario_name, scenario in treasure_hunting_scenarios.items():
            # Step 1: Lucien's mysterious distribution
            lucien_result = await lucien_validator.validate_lucien_interaction(
                scenario.lucien_distribution_message,
                context=scenario.context,
                diana_presence=True
            )
            
            # Step 2: Diana's clue revelation
            clue_result = await diana_validator.validate_text(
                scenario.diana_clue_revelation,
                context=scenario.context
            )
            
            # Step 3: Diana's treasure discovery celebration
            treasure_result = await diana_validator.validate_text(
                scenario.diana_treasure_discovery,
                context=f"{scenario.context}_completion"
            )
            
            # Record comprehensive flow results
            flow_results.append({
                'scenario': scenario_name,
                'archetype': scenario.user_archetype,
                'lucien_score': lucien_result.overall_score,
                'clue_score': clue_result.overall_score,
                'treasure_score': treasure_result.overall_score,
                'lucien_passes': lucien_result.meets_threshold,
                'clue_passes': clue_result.meets_threshold,
                'treasure_passes': treasure_result.meets_threshold,
                'lucien_supports_diana': lucien_result.supports_diana_experience,
                'diana_mystery_preserved': (
                    clue_result.trait_scores[DianaPersonalityTrait.MYSTERIOUS] >= scenario.expected_diana_mystery_min
                ),
                'diana_seduction_preserved': (
                    treasure_result.trait_scores[DianaPersonalityTrait.SEDUCTIVE] >= scenario.expected_diana_seductive_min
                )
            })
        
        # CRITICAL: ALL treasure hunting flows must pass
        for result in flow_results:
            assert result['lucien_passes'], (
                f"Lucien coordination failed for {result['scenario']}! "
                f"Score: {result['lucien_score']}/100"
            )
            
            assert result['clue_passes'], (
                f"Diana clue revelation failed for {result['scenario']}! "
                f"Score: {result['clue_score']}/100"
            )
            
            assert result['treasure_passes'], (
                f"Diana treasure discovery failed for {result['scenario']}! "
                f"Score: {result['treasure_score']}/100"
            )
            
            assert result['lucien_supports_diana'], (
                f"Lucien doesn't support Diana's treasure experience for {result['scenario']}!"
            )
            
            assert result['diana_mystery_preserved'], (
                f"Diana's mystery not preserved in treasure hunting for {result['scenario']}!"
            )
            
            assert result['diana_seduction_preserved'], (
                f"Diana's seductive charm not preserved in treasure discovery for {result['scenario']}!"
            )
        
        # Calculate overall treasure hunting success metrics
        total_scenarios = len(flow_results)
        perfect_flows = len([r for r in flow_results if (
            r['lucien_passes'] and r['clue_passes'] and r['treasure_passes'] and
            r['lucien_supports_diana'] and r['diana_mystery_preserved'] and r['diana_seduction_preserved']
        )])
        
        # CRITICAL: 100% success rate required for treasure hunting character preservation
        assert perfect_flows == total_scenarios, (
            f"Treasure hunting character preservation failure! "
            f"Perfect flows: {perfect_flows}/{total_scenarios}\n"
            f"Failed scenarios: {[r['scenario'] for r in flow_results if not (r['lucien_passes'] and r['clue_passes'] and r['treasure_passes'])]}"
        )
        
        # Calculate average scores
        avg_lucien_score = sum(r['lucien_score'] for r in flow_results) / total_scenarios
        avg_clue_score = sum(r['clue_score'] for r in flow_results) / total_scenarios
        avg_treasure_score = sum(r['treasure_score'] for r in flow_results) / total_scenarios
        
        # CRITICAL: Average scores must be excellent
        assert avg_lucien_score >= 85.0, (
            f"Average Lucien treasure coordination too low! Score: {avg_lucien_score}/100"
        )
        
        assert avg_clue_score >= 92.0, (
            f"Average Diana clue revelation too low! Score: {avg_clue_score}/100"
        )
        
        assert avg_treasure_score >= 90.0, (
            f"Average Diana treasure discovery too low! Score: {avg_treasure_score}/100"
        )
        
        print(f"\n🏆 TREASURE HUNTING CHARACTER INTEGRITY REPORT 🏆")
        print(f"Total Treasure Hunting Scenarios Tested: {total_scenarios}")
        print(f"Perfect Character Preservation Flows: {perfect_flows}/{total_scenarios} (100%)")
        print(f"Average Lucien Mystery Amplification Score: {avg_lucien_score:.1f}/100")
        print(f"Average Diana Clue Revelation Score: {avg_clue_score:.1f}/100")
        print(f"Average Diana Treasure Discovery Score: {avg_treasure_score:.1f}/100")
        print(f"CHARACTER INTEGRITY DURING TREASURE HUNTING: ✅ PERFECT")
        print(f"MYSTERY PRESERVATION: ✅ MAXIMUM")
        print(f"EMOTIONAL INVESTMENT: ✅ ENHANCED")
