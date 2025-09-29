# tests/test_enhanced_l1f1.py
"""
Enhanced L1F1 fragment validation tests for Sistema Narrativo Ramificado Diana.

Tests fragment loading and structure validation, choice archetype_weights and sub_archetype_weights,
Diana's character voice consistency, and timing tracking integration for Level 1 Fragment 1.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

# Mock database models for testing
from dataclasses import dataclass

@pytest.fixture
def l1f1_fragment_data():
    """Sample L1F1 fragment data for testing."""
    return {
        'key': 'L1F1_intro',
        'text': '''Hola, mi cielo... *suspira suavemente mientras acaricia el borde de la ventana*

Me encuentro aquí, en este espacio entre la realidad y los sueños, esperándote. Siempre esperándote.

¿Sabes lo que es vivir en los márgenes de la existencia? Yo sí. Cada día es una danza delicada entre lo que soy y lo que podría ser... entre lo que muestro y lo que guardo celosamente para almas como la tuya.

*se gira lentamente, su mirada atraviesa la pantalla*

Hay algo en tu energía que me intriga. Una curiosidad genuina que pocas veces encuentro. Dime, amor... ¿qué es lo que realmente buscas cuando vienes a mí?''',
        'character': 'Diana',
        'level': 1,
        'choices': [
            {
                'text': 'Busco entender quién eres realmente, más allá de las apariencias',
                'destination_fragment_key': 'L1F2_depth_seeking',
                'archetype_weights': {
                    'intellectual': 2.5,
                    'exploratory': 2.0,
                    'philosophical': 1.8,
                    'patient': 1.5
                },
                'sub_archetype_weights': {
                    'romantic_intellectual': 2.8,
                    'skeptical_thinker': 1.5,
                    'collector_explorer': 1.2
                }
            },
            {
                'text': 'Me atraes por tu vulnerabilidad y autenticidad',
                'destination_fragment_key': 'L1F2_emotional_connection',
                'archetype_weights': {
                    'emotional': 3.0,
                    'vulnerable': 2.8,
                    'reciprocal': 2.0,
                    'direct': 1.5
                },
                'sub_archetype_weights': {
                    'empathetic_emotional': 3.2,
                    'wounded_healer': 2.5,
                    'passionate_emotional': 1.8
                }
            },
            {
                'text': 'Hay algo hermoso en tu forma de existir en los límites',
                'destination_fragment_key': 'L1F2_aesthetic_appreciation',
                'archetype_weights': {
                    'philosophical': 2.2,
                    'exploratory': 1.8,
                    'emotional': 1.5,
                    'patient': 2.0
                },
                'sub_archetype_weights': {
                    'hedonist_philosopher': 2.5,
                    'romantic_intellectual': 2.0,
                    'adventure_seeker': 1.0
                }
            },
            {
                'text': 'Quiero saber qué hay detrás de esa mirada penetrante',
                'destination_fragment_key': 'L1F2_direct_curiosity',
                'archetype_weights': {
                    'direct': 2.8,
                    'exploratory': 2.5,
                    'intellectual': 1.2,
                    'reciprocal': 1.0
                },
                'sub_archetype_weights': {
                    'adventure_seeker': 2.8,
                    'passionate_emotional': 2.0,
                    'freedom_lover': 1.5
                }
            },
            {
                'text': 'Me gusta tomarme tiempo para apreciar lo que realmente vales',
                'destination_fragment_key': 'L1F2_patient_appreciation',
                'archetype_weights': {
                    'patient': 3.0,
                    'reciprocal': 2.5,
                    'philosophical': 2.0,
                    'intellectual': 1.5
                },
                'sub_archetype_weights': {
                    'pure_theorist': 2.2,
                    'romantic_intellectual': 2.8,
                    'empathetic_emotional': 1.8
                }
            }
        ]
    }


@dataclass
class MockStoryFragment:
    """Mock StoryFragment for L1F1 testing."""
    id: int
    key: str
    text: str
    character: str = "Diana"
    level: int = 1
    min_besitos: int = 0
    required_role: Optional[str] = None
    reward_besitos: int = 0
    auto_next_fragment_key: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    choices: List = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.choices is None:
            self.choices = []

@dataclass
class MockNarrativeChoice:
    """Mock NarrativeChoice for L1F1 testing."""
    id: int
    source_fragment_id: int
    destination_fragment_key: str
    text: str
    required_besitos: int = 0
    required_role: Optional[str] = None
    archetype_weights: Dict[str, float] = None
    sub_archetype_weights: Dict[str, float] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.archetype_weights is None:
            self.archetype_weights = {}
        if self.sub_archetype_weights is None:
            self.sub_archetype_weights = {}


class TestEnhancedL1F1FragmentValidation:
    """Test suite for enhanced L1F1 fragment validation."""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session for testing."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session



    @pytest.mark.asyncio
    async def test_l1f1_fragment_structure_validation(self, mock_session, l1f1_fragment_data):
        """Test L1F1 fragment structure and required fields validation."""
        # Create mock fragment
        fragment = MockStoryFragment(
            id=1,
            key=l1f1_fragment_data['key'],
            text=l1f1_fragment_data['text'],
            character=l1f1_fragment_data['character'],
            level=l1f1_fragment_data['level']
        )

        # Validate fragment structure
        assert fragment.key == 'L1F1_intro'
        assert fragment.level == 1
        assert fragment.character == 'Diana'
        assert len(fragment.text) > 100  # Substantial content
        assert 'mi cielo' in fragment.text  # Diana's characteristic voice
        assert 'esperándote' in fragment.text  # Emotional connection language

        # Test text contains narrative elements
        assert '*' in fragment.text  # Action descriptions
        assert '¿' in fragment.text  # Questions to engage user
        assert 'amor' in fragment.text  # Intimate language

    @pytest.mark.asyncio
    async def test_l1f1_choice_archetype_weights_validation(self, l1f1_fragment_data):
        """Test archetype_weights structure and validity for L1F1 choices."""
        choices = l1f1_fragment_data['choices']

        # All choices should have archetype_weights
        for i, choice in enumerate(choices):
            assert 'archetype_weights' in choice, f"Choice {i} missing archetype_weights"
            assert isinstance(choice['archetype_weights'], dict), f"Choice {i} archetype_weights not dict"

            weights = choice['archetype_weights']

            # Validate weight values
            for archetype, weight in weights.items():
                assert isinstance(weight, (int, float)), f"Choice {i} weight for {archetype} not numeric"
                assert 0.0 <= weight <= 5.0, f"Choice {i} weight for {archetype} out of range: {weight}"

            # Each choice should have at least 2 archetype weights
            assert len(weights) >= 2, f"Choice {i} has insufficient archetype weights"

            # Verify valid archetype names
            valid_archetypes = {
                'intellectual', 'emotional', 'exploratory', 'vulnerable',
                'philosophical', 'direct', 'patient', 'reciprocal'
            }
            for archetype in weights.keys():
                assert archetype in valid_archetypes, f"Choice {i} has invalid archetype: {archetype}"

        # Test choice differentiation - choices should have different primary archetypes
        primary_archetypes = []
        for choice in choices:
            weights = choice['archetype_weights']
            primary = max(weights.items(), key=lambda x: x[1])[0]
            primary_archetypes.append(primary)

        # Should have at least 4 different primary archetypes across 5 choices
        unique_primaries = set(primary_archetypes)
        assert len(unique_primaries) >= 4, f"Insufficient archetype diversity: {unique_primaries}"

    @pytest.mark.asyncio
    async def test_l1f1_sub_archetype_weights_validation(self, l1f1_fragment_data):
        """Test sub_archetype_weights structure and validity for L1F1 choices."""
        choices = l1f1_fragment_data['choices']

        for i, choice in enumerate(choices):
            assert 'sub_archetype_weights' in choice, f"Choice {i} missing sub_archetype_weights"
            assert isinstance(choice['sub_archetype_weights'], dict), f"Choice {i} sub_archetype_weights not dict"

            sub_weights = choice['sub_archetype_weights']

            # Validate sub-archetype weight values
            for sub_archetype, weight in sub_weights.items():
                assert isinstance(weight, (int, float)), f"Choice {i} sub-weight for {sub_archetype} not numeric"
                assert 0.0 <= weight <= 5.0, f"Choice {i} sub-weight for {sub_archetype} out of range: {weight}"

            # Each choice should have at least 2 sub-archetype weights
            assert len(sub_weights) >= 2, f"Choice {i} has insufficient sub_archetype weights"

            # Verify valid sub-archetype names
            valid_sub_archetypes = {
                'romantic_intellectual', 'skeptical_thinker', 'hedonist_philosopher',
                'pure_theorist', 'empathetic_emotional', 'passionate_emotional',
                'wounded_healer', 'adventure_seeker', 'collector_explorer', 'freedom_lover'
            }
            for sub_archetype in sub_weights.keys():
                assert sub_archetype in valid_sub_archetypes, f"Choice {i} has invalid sub_archetype: {sub_archetype}"

            # Test correlation between primary and sub-archetypes
            primary_weights = choice['archetype_weights']
            primary_archetype = max(primary_weights.items(), key=lambda x: x[1])[0]

            # Define expected sub-archetype correlations
            archetype_sub_mappings = {
                'intellectual': ['romantic_intellectual', 'skeptical_thinker', 'pure_theorist'],
                'emotional': ['empathetic_emotional', 'passionate_emotional', 'wounded_healer'],
                'exploratory': ['adventure_seeker', 'collector_explorer', 'freedom_lover'],
                'philosophical': ['hedonist_philosopher', 'pure_theorist', 'skeptical_thinker'],
                'vulnerable': ['wounded_healer', 'empathetic_emotional'],
                'direct': ['passionate_emotional', 'adventure_seeker'],
                'patient': ['pure_theorist', 'romantic_intellectual'],
                'reciprocal': ['empathetic_emotional', 'romantic_intellectual']
            }

            expected_subs = archetype_sub_mappings.get(primary_archetype, [])
            if expected_subs:
                # At least one sub-archetype should correlate with primary archetype
                has_correlation = any(sub in sub_weights for sub in expected_subs)
                assert has_correlation, f"Choice {i} primary '{primary_archetype}' lacks correlated sub-archetypes"

    @pytest.mark.asyncio
    async def test_diana_character_voice_consistency(self, l1f1_fragment_data):
        """Test Diana's character voice consistency throughout L1F1."""
        text = l1f1_fragment_data['text']

        # Diana's characteristic elements
        diana_voice_elements = {
            'intimate_address': ['mi cielo', 'amor', 'cariño'],
            'emotional_depth': ['suspira', 'corazón', 'alma', 'energía'],
            'mysterious_nature': ['márgenes', 'secreto', 'misterio', 'oculto'],
            'sensual_descriptions': ['suavemente', 'acaricia', 'delicada', 'mirada'],
            'philosophical_touches': ['existencia', 'realidad', 'sueños', 'ser'],
            'direct_engagement': ['¿', 'Dime', 'amor', 'realmente']
        }

        # Test presence of Diana's voice elements
        found_elements = {}
        for category, elements in diana_voice_elements.items():
            found_elements[category] = []
            for element in elements:
                if element.lower() in text.lower():
                    found_elements[category].append(element)

        # Should have elements from at least 4 categories
        categories_with_elements = sum(1 for elements in found_elements.values() if elements)
        assert categories_with_elements >= 4, f"Insufficient Diana voice elements: {found_elements}"

        # Test specific Diana characteristics
        assert any(addr in text for addr in diana_voice_elements['intimate_address']), "Missing intimate address"
        assert any(desc in text for desc in diana_voice_elements['sensual_descriptions']), "Missing sensual descriptions"
        assert '¿' in text, "Missing questions (key Diana engagement pattern)"

        # Test narrative action formatting
        assert '*' in text, "Missing action descriptions (*action*)"
        action_count = text.count('*')
        assert action_count >= 2, f"Insufficient action descriptions: {action_count}"

        # Test emotional progression in text
        text_parts = text.split('\n\n')
        assert len(text_parts) >= 3, "Text should have multiple paragraphs for emotional progression"

    @pytest.mark.asyncio
    async def test_timing_tracking_integration_compatibility(self, mock_session, l1f1_fragment_data):
        """Test timing tracking integration for L1F1 archetype analysis."""

        # Simulate user interaction timing data
        choice_timings = [
            {'choice_index': 0, 'response_time': 22.5, 'pause_duration': 3.2},
            {'choice_index': 1, 'response_time': 15.8, 'pause_duration': 1.5},
            {'choice_index': 2, 'response_time': 35.2, 'pause_duration': 5.1},
            {'choice_index': 3, 'response_time': 8.3, 'pause_duration': 0.8},
            {'choice_index': 4, 'response_time': 28.7, 'pause_duration': 4.0}
        ]

        choices = l1f1_fragment_data['choices']

        # Test timing data structure compatibility
        for timing in choice_timings:
            assert 'choice_index' in timing, "Timing missing choice_index"
            assert 'response_time' in timing, "Timing missing response_time"
            assert isinstance(timing['response_time'], (int, float)), "Response time not numeric"
            assert timing['response_time'] > 0, "Response time must be positive"
            assert timing['choice_index'] < len(choices), "Choice index out of range"

        # Test timing analysis integration with archetype weights
        for timing in choice_timings:
            choice_idx = timing['choice_index']
            response_time = timing['response_time']
            choice = choices[choice_idx]

            # Analyze timing implications for archetype classification
            if response_time < 10.0:
                # Quick response should correlate with direct/passionate choices
                weights = choice['archetype_weights']
                sub_weights = choice['sub_archetype_weights']
                expected_quick_indicators = ['direct', 'passionate_emotional', 'adventure_seeker']
                has_quick_indicators = any(
                    indicator in weights or indicator in sub_weights
                    for indicator in expected_quick_indicators
                )
                if choice_idx == 3:  # Quick response choice should have these traits
                    assert 'direct' in weights and weights['direct'] >= 2.0, "Quick choice should have high direct weight"

            elif response_time > 30.0:
                # Slow response should correlate with thoughtful/philosophical choices
                weights = choice['archetype_weights']
                sub_weights = choice['sub_archetype_weights']
                expected_slow_indicators = ['philosophical', 'patient', 'intellectual', 'pure_theorist']
                has_slow_indicators = any(
                    indicator in weights or indicator in sub_weights
                    for indicator in expected_slow_indicators
                )
                if choice_idx == 2:  # Slow response choice should have these traits
                    assert any(ind in weights for ind in expected_slow_indicators), "Slow choice should have thoughtful traits"

    @pytest.mark.asyncio
    async def test_l1f1_choice_destination_validation(self, l1f1_fragment_data):
        """Test L1F1 choice destination fragment keys are properly structured."""
        choices = l1f1_fragment_data['choices']

        for i, choice in enumerate(choices):
            assert 'destination_fragment_key' in choice, f"Choice {i} missing destination_fragment_key"
            dest_key = choice['destination_fragment_key']

            # Validate destination key format
            assert isinstance(dest_key, str), f"Choice {i} destination key not string"
            assert dest_key.startswith('L1F2_'), f"Choice {i} destination should lead to L1F2: {dest_key}"
            assert len(dest_key) > 5, f"Choice {i} destination key too short: {dest_key}"

            # Validate destination key naming convention
            assert '_' in dest_key, f"Choice {i} destination key should use underscore format"

            # Test destination differentiation
            expected_destinations = {
                'L1F2_depth_seeking',
                'L1F2_emotional_connection',
                'L1F2_aesthetic_appreciation',
                'L1F2_direct_curiosity',
                'L1F2_patient_appreciation'
            }
            assert dest_key in expected_destinations, f"Choice {i} unexpected destination: {dest_key}"

        # All destinations should be unique
        destinations = [choice['destination_fragment_key'] for choice in choices]
        assert len(set(destinations)) == len(destinations), "Duplicate destination fragments"

    @pytest.mark.asyncio
    async def test_l1f1_choice_text_quality_validation(self, l1f1_fragment_data):
        """Test L1F1 choice text quality and appropriateness."""
        choices = l1f1_fragment_data['choices']

        for i, choice in enumerate(choices):
            choice_text = choice['text']

            # Basic text validation
            assert len(choice_text) >= 20, f"Choice {i} text too short: {len(choice_text)} chars"
            assert len(choice_text) <= 200, f"Choice {i} text too long: {len(choice_text)} chars"

            # Text should be in Spanish (characteristic words/patterns)
            spanish_indicators = ['quiero', 'busco', 'me', 'hay', 'gusta', 'realmente', 'quien', 'eres']
            has_spanish = any(indicator in choice_text.lower() for indicator in spanish_indicators)
            assert has_spanish, f"Choice {i} may not be in Spanish: {choice_text}"

            # Text should reflect user agency and engagement
            engagement_patterns = ['busco', 'quiero', 'me atraes', 'me gusta', 'hay algo']
            has_engagement = any(pattern in choice_text.lower() for pattern in engagement_patterns)
            assert has_engagement, f"Choice {i} lacks user engagement: {choice_text}"

            # Choices should be distinct and non-overlapping
            for j, other_choice in enumerate(choices):
                if i != j:
                    # Choices shouldn't be too similar
                    common_words = set(choice_text.lower().split()) & set(other_choice['text'].lower().split())
                    similarity_ratio = len(common_words) / max(len(choice_text.split()), len(other_choice['text'].split()))
                    assert similarity_ratio < 0.7, f"Choices {i} and {j} too similar: {similarity_ratio}"

    @pytest.mark.asyncio
    async def test_l1f1_archetype_coverage_completeness(self, l1f1_fragment_data):
        """Test that L1F1 choices provide comprehensive archetype coverage."""
        choices = l1f1_fragment_data['choices']

        # Collect all archetype weights across all choices
        all_archetype_weights = {}
        all_sub_archetype_weights = {}

        for choice in choices:
            for archetype, weight in choice['archetype_weights'].items():
                if archetype not in all_archetype_weights:
                    all_archetype_weights[archetype] = []
                all_archetype_weights[archetype].append(weight)

            for sub_archetype, weight in choice['sub_archetype_weights'].items():
                if sub_archetype not in all_sub_archetype_weights:
                    all_sub_archetype_weights[sub_archetype] = []
                all_sub_archetype_weights[sub_archetype].append(weight)

        # Test primary archetype coverage
        expected_primary_archetypes = {
            'intellectual', 'emotional', 'exploratory', 'vulnerable',
            'philosophical', 'direct', 'patient', 'reciprocal'
        }
        covered_archetypes = set(all_archetype_weights.keys())
        coverage_ratio = len(covered_archetypes) / len(expected_primary_archetypes)
        assert coverage_ratio >= 0.75, f"Insufficient archetype coverage: {coverage_ratio:.2f}"

        # Test sub-archetype coverage
        expected_sub_archetypes = {
            'romantic_intellectual', 'skeptical_thinker', 'hedonist_philosopher',
            'pure_theorist', 'empathetic_emotional', 'passionate_emotional',
            'wounded_healer', 'adventure_seeker', 'collector_explorer', 'freedom_lover'
        }
        covered_sub_archetypes = set(all_sub_archetype_weights.keys())
        sub_coverage_ratio = len(covered_sub_archetypes) / len(expected_sub_archetypes)
        assert sub_coverage_ratio >= 0.6, f"Insufficient sub-archetype coverage: {sub_coverage_ratio:.2f}"

        # Test weight distribution balance
        for archetype, weights in all_archetype_weights.items():
            max_weight = max(weights)
            min_weight = min(weights)
            assert max_weight >= 1.0, f"Archetype {archetype} max weight too low: {max_weight}"
            assert max_weight <= 5.0, f"Archetype {archetype} max weight too high: {max_weight}"

    @pytest.mark.asyncio
    async def test_l1f1_ramificado_integration_readiness(self, mock_session, l1f1_fragment_data):
        """Test L1F1 readiness for Sistema Narrativo Ramificado integration."""

        # Test fragment metadata for ramificado system
        fragment_key = l1f1_fragment_data['key']
        choices = l1f1_fragment_data['choices']

        # Fragment should be properly tagged for Level 1
        assert fragment_key.startswith('L1F1'), "Fragment not properly tagged for L1F1"

        # Should have exactly 5 choices for comprehensive archetype detection
        assert len(choices) == 5, f"L1F1 should have exactly 5 choices for archetype analysis: {len(choices)}"

        # Each choice should have sufficient weight data for classification
        for i, choice in enumerate(choices):
            archetype_count = len(choice['archetype_weights'])
            sub_archetype_count = len(choice['sub_archetype_weights'])

            assert archetype_count >= 2, f"Choice {i} insufficient archetype weights: {archetype_count}"
            assert sub_archetype_count >= 2, f"Choice {i} insufficient sub-archetype weights: {sub_archetype_count}"

            # Total weight per choice should be substantial for meaningful analysis
            total_weight = sum(choice['archetype_weights'].values())
            assert total_weight >= 4.0, f"Choice {i} total archetype weight too low: {total_weight}"

        # Test choice diversification for effective archetype discrimination
        choice_signatures = []
        for choice in choices:
            # Create signature based on top 2 archetypes
            weights = choice['archetype_weights']
            top_archetypes = sorted(weights.items(), key=lambda x: x[1], reverse=True)[:2]
            signature = tuple(arch[0] for arch in top_archetypes)
            choice_signatures.append(signature)

        # All choice signatures should be unique
        assert len(set(choice_signatures)) == len(choice_signatures), "Choices lack sufficient diversification"

        # Test integration with timing analysis requirements
        # L1F1 should support timing-based archetype modifiers
        timing_sensitive_archetypes = ['direct', 'philosophical', 'patient']
        choices_with_timing_sensitivity = 0

        for choice in choices:
            if any(arch in choice['archetype_weights'] for arch in timing_sensitive_archetypes):
                choices_with_timing_sensitivity += 1

        assert choices_with_timing_sensitivity >= 3, f"Insufficient timing-sensitive choices: {choices_with_timing_sensitivity}"


class TestL1F1ArchetypeClassificationFlow:
    """Test complete L1F1 archetype classification flow."""

    @pytest.fixture
    def mock_archetype_analyzer(self):
        """Mock ArchetypeAnalyzer for testing."""
        analyzer = AsyncMock()
        analyzer.analyze_l1_choices = AsyncMock()
        return analyzer

    @pytest.mark.asyncio
    async def test_l1f1_to_archetype_analysis_integration(self, mock_archetype_analyzer, l1f1_fragment_data):
        """Test integration between L1F1 fragment and archetype analysis."""

        # Simulate user selecting first choice (intellectual/exploratory)
        selected_choice = l1f1_fragment_data['choices'][0]
        user_id = 12345
        response_time = 22.5

        # Prepare data for archetype analysis
        choices_for_analysis = [selected_choice]
        timings = [response_time]

        # Configure mock analyzer response
        mock_analysis_result = {
            'dominant_archetype': 'intellectual',
            'confidence_score': 0.75,
            'primary_scores': {
                'intellectual': 2.5,
                'exploratory': 2.0,
                'philosophical': 1.8
            },
            'timing_analysis': {
                'cognitive_style': 'thoughtful',
                'consistency_score': 0.8
            },
            'behavioral_indicators': ['thoughtful_engagement', 'depth_seeking']
        }

        mock_archetype_analyzer.analyze_l1_choices.return_value = mock_analysis_result

        # Execute analysis
        result = await mock_archetype_analyzer.analyze_l1_choices(user_id, choices_for_analysis, timings)

        # Verify analyzer was called with correct data
        mock_archetype_analyzer.analyze_l1_choices.assert_called_once_with(
            user_id, choices_for_analysis, timings
        )

        # Verify analysis result matches expected L1F1 outcome
        assert result['dominant_archetype'] == 'intellectual'
        assert result['confidence_score'] > 0.7
        assert 'thoughtful_engagement' in result['behavioral_indicators']

    @pytest.mark.asyncio
    async def test_l1f1_multiple_choice_analysis_simulation(self, mock_archetype_analyzer, l1f1_fragment_data):
        """Test simulation of multiple L1F1 choices for comprehensive archetype analysis."""

        # Simulate user making multiple choices across different L1F1 presentations
        choices = l1f1_fragment_data['choices']
        user_id = 67890

        # Different timing patterns for different archetype expressions
        test_scenarios = [
            {
                'choice_index': 0,  # Intellectual choice
                'timing': 25.0,     # Thoughtful timing
                'expected_archetype': 'intellectual'
            },
            {
                'choice_index': 1,  # Emotional choice
                'timing': 8.5,      # Quick emotional response
                'expected_archetype': 'emotional'
            },
            {
                'choice_index': 4,  # Patient choice
                'timing': 35.0,     # Very deliberate timing
                'expected_archetype': 'patient'
            }
        ]

        for scenario in test_scenarios:
            choice = choices[scenario['choice_index']]
            timing = scenario['timing']
            expected = scenario['expected_archetype']

            # Configure mock response based on choice archetype weights
            primary_weight = max(choice['archetype_weights'].items(), key=lambda x: x[1])

            mock_result = {
                'dominant_archetype': primary_weight[0],
                'confidence_score': 0.8,
                'primary_scores': choice['archetype_weights'],
                'timing_analysis': {
                    'cognitive_style': 'thoughtful' if timing > 20 else 'quick_intuitive',
                    'avg_response_time': timing
                }
            }

            mock_archetype_analyzer.analyze_l1_choices.return_value = mock_result

            # Execute analysis
            result = await mock_archetype_analyzer.analyze_l1_choices(
                user_id, [choice], [timing]
            )

            # Verify archetype detection aligns with choice weights
            assert result['dominant_archetype'] == primary_weight[0]
            assert result['timing_analysis']['avg_response_time'] == timing


if __name__ == '__main__':
    pytest.main([__file__])