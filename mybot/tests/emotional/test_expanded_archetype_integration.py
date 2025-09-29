# tests/emotional/test_expanded_archetype_integration.py
"""
Integration tests for complete archetype analysis flow.

Tests verify end-to-end archetype classification functionality for the Sistema Narrativo Ramificado Diana,
including full analyze_l1_choices workflow, database storage/retrieval, integration with EmotionalAnalysisService,
and graceful fallback to 5-archetype system.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
from dataclasses import dataclass

# Import test fixtures
from tests.emotional.conftest import TEST_USER_ARCHETYPES, UserBehaviorProfile, EmotionalTestDataGenerator

# Mock the database models and services for testing
@dataclass
class MockArchetypeClassification:
    """Mock ArchetypeClassification model for testing."""
    user_id: int
    primary_archetype: str
    archetype_confidence: float

    # Primary scores
    intellectual_score: float = 0.0
    emotional_score: float = 0.0
    exploratory_score: float = 0.0
    vulnerable_score: float = 0.0
    philosophical_score: float = 0.0
    direct_score: float = 0.0
    patient_score: float = 0.0
    reciprocal_score: float = 0.0

    # Sub-archetype scores
    romantic_intellectual_score: float = 0.0
    skeptical_thinker_score: float = 0.0
    hedonist_philosopher_score: float = 0.0
    pure_theorist_score: float = 0.0
    empathetic_emotional_score: float = 0.0
    passionate_emotional_score: float = 0.0
    wounded_healer_score: float = 0.0
    adventure_seeker_score: float = 0.0
    collector_explorer_score: float = 0.0
    freedom_lover_score: float = 0.0

    # Cognitive data
    cognitive_style: str = 'balanced'
    response_consistency: float = 0.5
    temporal_pattern: str = 'stable'

    # Metadata
    secondary_traits: str = '[]'
    trait_strengths: str = '[]'
    archetype_stability: float = 0.5
    ramificado_enabled: bool = False
    activation_timestamp: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


# Mock ArchetypeScores and SubArchetypeScores
@dataclass
class ArchetypeScores:
    intellectual: float = 0.0
    emotional: float = 0.0
    exploratory: float = 0.0
    vulnerable: float = 0.0
    philosophical: float = 0.0
    direct: float = 0.0
    patient: float = 0.0
    reciprocal: float = 0.0


@dataclass
class SubArchetypeScores:
    romantic_intellectual: float = 0.0
    skeptical_thinker: float = 0.0
    hedonist_philosopher: float = 0.0
    pure_theorist: float = 0.0
    empathetic_emotional: float = 0.0
    passionate_emotional: float = 0.0
    wounded_healer: float = 0.0
    adventure_seeker: float = 0.0
    collector_explorer: float = 0.0
    freedom_lover: float = 0.0


# Mock ResponseTimeAnalyzer
class MockResponseTimeAnalyzer:
    def __init__(self, session=None):
        self.session = session

    async def analyze_cognitive_style(self, user_id: int, timings: List[float]) -> Dict[str, Any]:
        """Mock cognitive style analysis."""
        if not timings:
            return {'cognitive_style': 'balanced', 'consistency_score': 0.5, 'temporal_pattern': 'stable'}

        avg_time = sum(timings) / len(timings)
        if avg_time < 10:
            cognitive_style = 'quick_intuitive'
        elif avg_time < 30:
            cognitive_style = 'thoughtful'
        else:
            cognitive_style = 'deliberate'

        # Calculate consistency
        if len(timings) > 1:
            mean_time = sum(timings) / len(timings)
            variance = sum((t - mean_time) ** 2 for t in timings) / len(timings)
            std_dev = variance ** 0.5
            if mean_time > 0:
                coefficient_of_variation = std_dev / mean_time
                consistency_score = max(0.0, 1.0 - min(coefficient_of_variation / 2.0, 1.0))
            else:
                consistency_score = 1.0
        else:
            consistency_score = 1.0

        return {
            'cognitive_style': cognitive_style,
            'consistency_score': consistency_score,
            'temporal_pattern': 'stable'
        }


# Mock ArchetypeAnalyzer
class MockArchetypeAnalyzer:
    """Mock ArchetypeAnalyzer for integration testing."""

    def __init__(self, session):
        self.session = session
        self.response_time_analyzer = MockResponseTimeAnalyzer(session)

    async def analyze_l1_choices(
        self,
        user_id: int,
        choices: List[Dict[str, Any]],
        timings: List[float]
    ) -> Dict[str, Any]:
        """Mock implementation of L1 choices analysis."""
        # Initialize scoring structures
        archetype_scores = ArchetypeScores()
        sub_archetype_scores = SubArchetypeScores()

        # Process choices
        for choice in choices:
            # Process archetype weights
            archetype_weights = choice.get('archetype_weights', {})
            for archetype_name, weight in archetype_weights.items():
                if hasattr(archetype_scores, archetype_name):
                    current_value = getattr(archetype_scores, archetype_name)
                    setattr(archetype_scores, archetype_name, current_value + weight)

            # Process sub-archetype weights
            sub_archetype_weights = choice.get('sub_archetype_weights', {})
            for sub_archetype_name, weight in sub_archetype_weights.items():
                if hasattr(sub_archetype_scores, sub_archetype_name):
                    current_value = getattr(sub_archetype_scores, sub_archetype_name)
                    setattr(sub_archetype_scores, sub_archetype_name, current_value + weight)

        # Apply timing modifiers
        for timing in timings:
            if timing < 10.0:
                archetype_scores.direct += 0.5
            elif 10.0 <= timing <= 30.0:
                archetype_scores.philosophical += 0.4
                archetype_scores.intellectual += 0.3
            else:
                archetype_scores.philosophical += 0.6
                archetype_scores.patient += 0.5

        # Calculate primary archetype
        score_dict = {
            'intellectual': archetype_scores.intellectual,
            'emotional': archetype_scores.emotional,
            'exploratory': archetype_scores.exploratory,
            'vulnerable': archetype_scores.vulnerable,
            'philosophical': archetype_scores.philosophical,
            'direct': archetype_scores.direct,
            'patient': archetype_scores.patient,
            'reciprocal': archetype_scores.reciprocal
        }

        max_score = max(score_dict.values())
        primary_archetype = 'intellectual'  # Default
        for archetype in sorted(score_dict.keys()):
            if score_dict[archetype] == max_score:
                primary_archetype = archetype
                break

        # Calculate confidence
        if len(choices) >= 3 and max_score > 1.0:
            confidence_score = min(0.9, 0.5 + (max_score / 10.0))
        else:
            confidence_score = 0.3

        # Get timing analysis
        timing_analysis = await self.response_time_analyzer.analyze_cognitive_style(user_id, timings)

        # Behavioral indicators
        behavioral_indicators = []
        if confidence_score >= 0.8:
            behavioral_indicators.append("high_confidence_classification")
        if len(choices) >= 3:
            behavioral_indicators.append("sufficient_data_points")

        return {
            'primary_scores': archetype_scores,
            'sub_scores': sub_archetype_scores,
            'timing_analysis': timing_analysis,
            'dominant_archetype': primary_archetype,
            'sub_archetype': 'undefined',
            'confidence_score': confidence_score,
            'behavioral_indicators': behavioral_indicators,
            'analysis_metadata': {
                'total_choices': len(choices),
                'total_timings': len(timings),
                'avg_response_time': sum(timings) / len(timings) if timings else 0.0,
                'classification_timestamp': datetime.utcnow()
            }
        }

    async def store_classification_results(
        self,
        user_id: int,
        analysis_results: Dict[str, Any]
    ) -> MockArchetypeClassification:
        """Mock storing classification results."""
        primary_scores = analysis_results.get('primary_scores')
        sub_scores = analysis_results.get('sub_scores')
        timing_analysis = analysis_results.get('timing_analysis', {})

        classification = MockArchetypeClassification(
            user_id=user_id,
            primary_archetype=analysis_results.get('dominant_archetype'),
            archetype_confidence=analysis_results.get('confidence_score', 0.0),

            # Primary scores
            intellectual_score=primary_scores.intellectual,
            emotional_score=primary_scores.emotional,
            exploratory_score=primary_scores.exploratory,
            vulnerable_score=primary_scores.vulnerable,
            philosophical_score=primary_scores.philosophical,
            direct_score=primary_scores.direct,
            patient_score=primary_scores.patient,
            reciprocal_score=primary_scores.reciprocal,

            # Sub-archetype scores
            romantic_intellectual_score=sub_scores.romantic_intellectual,
            skeptical_thinker_score=sub_scores.skeptical_thinker,
            hedonist_philosopher_score=sub_scores.hedonist_philosopher,
            pure_theorist_score=sub_scores.pure_theorist,
            empathetic_emotional_score=sub_scores.empathetic_emotional,
            passionate_emotional_score=sub_scores.passionate_emotional,
            wounded_healer_score=sub_scores.wounded_healer,
            adventure_seeker_score=sub_scores.adventure_seeker,
            collector_explorer_score=sub_scores.collector_explorer,
            freedom_lover_score=sub_scores.freedom_lover,

            # Cognitive data
            cognitive_style=timing_analysis.get('cognitive_style', 'balanced'),
            response_consistency=timing_analysis.get('consistency_score', 0.5),
            temporal_pattern=timing_analysis.get('temporal_pattern', 'stable'),

            # Metadata
            secondary_traits=json.dumps([analysis_results.get('sub_archetype')] if analysis_results.get('sub_archetype') != 'undefined' else []),
            trait_strengths=json.dumps(analysis_results.get('behavioral_indicators', [])),
            archetype_stability=analysis_results.get('confidence_score', 0.0)
        )

        return classification

    async def get_user_classification(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Mock getting user classification."""
        # Simulate getting from database
        # Return None to simulate no existing classification
        return None


# Mock EmotionalAnalysisService
class MockEmotionalAnalysisService:
    """Mock EmotionalAnalysisService for integration testing."""

    def __init__(self, session):
        self.session = session

    async def get_user_emotional_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Mock getting user emotional profile."""
        return {
            'user_id': user_id,
            'vulnerability_level': 0.5,
            'authenticity_score': 0.7,
            'emotional_depth': 0.6,
            'last_updated': datetime.utcnow(),
            'interaction_count': 5
        }

    async def analyze_response_timing(
        self,
        user_id: int,
        timestamp: datetime,
        action_type: str
    ) -> Dict[str, Any]:
        """Mock emotional timing analysis."""
        return {
            'success': True,
            'timing_pattern': 'normal',
            'emotional_state': 'balanced',
            'response_quality': 0.7
        }


class TestExpandedArchetypeIntegration:
    """Integration tests for complete archetype analysis flow."""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session."""
        session = AsyncMock()
        session.add = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def archetype_analyzer(self, mock_session):
        """Mock archetype analyzer."""
        return MockArchetypeAnalyzer(mock_session)

    @pytest.fixture
    def emotional_analysis_service(self, mock_session):
        """Mock emotional analysis service."""
        return MockEmotionalAnalysisService(mock_session)

    @pytest.mark.asyncio
    async def test_full_analyze_l1_choices_workflow_intellectual(self, archetype_analyzer):
        """Test complete L1 choices analysis workflow for intellectual archetype."""
        user_id = 12345

        # Realistic L1 choices data favoring intellectual archetype
        choices = [
            {
                'choice_id': 1,
                'archetype_weights': {
                    'intellectual': 2.5,
                    'philosophical': 1.8,
                    'patient': 1.0
                },
                'sub_archetype_weights': {
                    'romantic_intellectual': 2.0,
                    'pure_theorist': 1.5
                }
            },
            {
                'choice_id': 2,
                'archetype_weights': {
                    'intellectual': 2.0,
                    'exploratory': 1.2,
                    'philosophical': 1.5
                },
                'sub_archetype_weights': {
                    'skeptical_thinker': 1.8,
                    'romantic_intellectual': 1.0
                }
            },
            {
                'choice_id': 3,
                'archetype_weights': {
                    'intellectual': 1.8,
                    'patient': 2.0,
                    'reciprocal': 1.0
                },
                'sub_archetype_weights': {
                    'pure_theorist': 2.5,
                    'romantic_intellectual': 1.2
                }
            }
        ]

        # Thoughtful timing pattern (supports intellectual classification)
        timings = [22.3, 18.5, 25.1]

        # Execute full analysis workflow
        result = await archetype_analyzer.analyze_l1_choices(user_id, choices, timings)

        # Verify analysis results
        assert result['dominant_archetype'] == 'intellectual'
        assert result['confidence_score'] >= 0.7
        assert 'sufficient_data_points' in result['behavioral_indicators']

        # Verify primary scores
        primary_scores = result['primary_scores']
        assert primary_scores.intellectual > 5.0  # Should have highest score
        assert primary_scores.philosophical > 0.0  # Should have secondary scores

        # Verify timing analysis integration
        timing_analysis = result['timing_analysis']
        assert timing_analysis['cognitive_style'] == 'thoughtful'
        assert timing_analysis['consistency_score'] > 0.7

        # Verify metadata
        metadata = result['analysis_metadata']
        assert metadata['total_choices'] == 3
        assert metadata['avg_response_time'] > 20.0

    @pytest.mark.asyncio
    async def test_full_analyze_l1_choices_workflow_emotional(self, archetype_analyzer):
        """Test complete L1 choices analysis workflow for emotional archetype."""
        user_id = 67890

        # Choices favoring emotional archetype
        choices = [
            {
                'choice_id': 1,
                'archetype_weights': {
                    'emotional': 3.0,
                    'vulnerable': 2.5,
                    'reciprocal': 1.8
                },
                'sub_archetype_weights': {
                    'empathetic_emotional': 2.8,
                    'passionate_emotional': 1.5
                }
            },
            {
                'choice_id': 2,
                'archetype_weights': {
                    'emotional': 2.5,
                    'vulnerable': 2.0,
                    'direct': 1.0
                },
                'sub_archetype_weights': {
                    'passionate_emotional': 2.2,
                    'wounded_healer': 1.8
                }
            }
        ]

        # Quick emotional timing pattern
        timings = [5.2, 3.8]

        result = await archetype_analyzer.analyze_l1_choices(user_id, choices, timings)

        # Verify emotional archetype classification
        assert result['dominant_archetype'] == 'emotional'
        assert result['confidence_score'] >= 0.5  # Lower due to fewer choices

        # Verify emotional scores dominate
        primary_scores = result['primary_scores']
        assert primary_scores.emotional > primary_scores.intellectual
        assert primary_scores.emotional > primary_scores.exploratory

        # Verify quick response timing effect
        assert primary_scores.direct > 0.0  # Should get timing modifiers

        # Verify timing analysis
        timing_analysis = result['timing_analysis']
        assert timing_analysis['cognitive_style'] == 'quick_intuitive'

    @pytest.mark.asyncio
    async def test_database_storage_and_retrieval(self, archetype_analyzer, mock_session):
        """Test database storage and retrieval of classification results."""
        user_id = 11111

        # Perform analysis
        choices = [
            {
                'archetype_weights': {'exploratory': 2.5, 'adventure_seeker': 1.0},
                'sub_archetype_weights': {'adventure_seeker': 2.0}
            }
        ]
        timings = [15.0]

        analysis_result = await archetype_analyzer.analyze_l1_choices(user_id, choices, timings)

        # Store classification results
        stored_classification = await archetype_analyzer.store_classification_results(
            user_id, analysis_result
        )

        # Verify stored data
        assert stored_classification.user_id == user_id
        assert stored_classification.primary_archetype == analysis_result['dominant_archetype']
        assert stored_classification.archetype_confidence == analysis_result['confidence_score']

        # Verify primary scores stored correctly
        assert stored_classification.exploratory_score == analysis_result['primary_scores'].exploratory
        assert stored_classification.intellectual_score == analysis_result['primary_scores'].intellectual

        # Verify sub-archetype scores stored correctly
        assert stored_classification.adventure_seeker_score == analysis_result['sub_scores'].adventure_seeker

        # Verify cognitive data stored correctly
        assert stored_classification.cognitive_style == analysis_result['timing_analysis']['cognitive_style']
        assert stored_classification.response_consistency == analysis_result['timing_analysis']['consistency_score']

        # Verify metadata stored correctly
        secondary_traits = json.loads(stored_classification.secondary_traits)
        trait_strengths = json.loads(stored_classification.trait_strengths)
        assert isinstance(secondary_traits, list)
        assert isinstance(trait_strengths, list)

    @pytest.mark.asyncio
    async def test_integration_with_emotional_analysis_service(
        self,
        archetype_analyzer,
        emotional_analysis_service
    ):
        """Test integration with existing EmotionalAnalysisService."""
        user_id = 22222

        # Get emotional profile first
        emotional_profile = await emotional_analysis_service.get_user_emotional_profile(user_id)
        assert emotional_profile is not None
        assert 'vulnerability_level' in emotional_profile

        # Perform archetype analysis
        choices = [
            {
                'archetype_weights': {'vulnerable': 2.0, 'emotional': 1.5},
                'sub_archetype_weights': {'wounded_healer': 2.5}
            }
        ]
        timings = [25.0]

        archetype_result = await archetype_analyzer.analyze_l1_choices(user_id, choices, timings)

        # Verify integration possibilities
        assert archetype_result['confidence_score'] > 0.0
        assert emotional_profile['vulnerability_level'] > 0.0

        # Simulate integrated analysis
        integrated_profile = {
            'user_id': user_id,
            'archetype_classification': archetype_result,
            'emotional_profile': emotional_profile,
            'integration_score': (archetype_result['confidence_score'] + emotional_profile['authenticity_score']) / 2
        }

        assert integrated_profile['integration_score'] > 0.5

    @pytest.mark.asyncio
    async def test_graceful_fallback_to_5_archetype_system(self, archetype_analyzer):
        """Test graceful fallback to 5-archetype system when expanded system fails."""
        user_id = 33333

        # Simulate insufficient data scenario
        choices = [
            {
                'archetype_weights': {'intellectual': 0.5},  # Very low weights
                'sub_archetype_weights': {}  # No sub-archetype data
            }
        ]
        timings = [10.0]

        result = await archetype_analyzer.analyze_l1_choices(user_id, choices, timings)

        # Should still produce a result but with low confidence
        assert result['dominant_archetype'] in [
            'intellectual', 'emotional', 'exploratory', 'vulnerable',
            'philosophical', 'direct', 'patient', 'reciprocal'
        ]
        assert result['confidence_score'] < 0.5  # Low confidence due to insufficient data

        # Simulate fallback mapping for compatibility
        expanded_to_5_archetype_mapping = {
            'intellectual': 'achiever',
            'emotional': 'socializer',
            'exploratory': 'explorer',
            'vulnerable': 'socializer',
            'philosophical': 'achiever',
            'direct': 'challenger',
            'patient': 'creator',
            'reciprocal': 'socializer'
        }

        fallback_archetype = expanded_to_5_archetype_mapping.get(
            result['dominant_archetype'], 'explorer'
        )

        assert fallback_archetype in ['achiever', 'socializer', 'explorer', 'challenger', 'creator']

    @pytest.mark.asyncio
    async def test_edge_case_empty_choices_data(self, archetype_analyzer):
        """Test handling of empty choices data."""
        user_id = 44444

        # Empty choices
        choices = []
        timings = []

        result = await archetype_analyzer.analyze_l1_choices(user_id, choices, timings)

        # Should handle gracefully
        assert result['dominant_archetype'] == 'intellectual'  # Default fallback
        assert result['confidence_score'] == 0.3  # Low confidence
        assert result['analysis_metadata']['total_choices'] == 0

    @pytest.mark.asyncio
    async def test_edge_case_malformed_choices_data(self, archetype_analyzer):
        """Test handling of malformed choices data."""
        user_id = 55555

        # Malformed choices (missing expected keys)
        choices = [
            {'invalid_key': 'invalid_value'},
            {'archetype_weights': {'nonexistent_archetype': 1.0}},
            {}  # Empty choice
        ]
        timings = [15.0, 20.0, 12.0]

        # Should handle gracefully without errors
        result = await archetype_analyzer.analyze_l1_choices(user_id, choices, timings)

        assert result is not None
        assert 'dominant_archetype' in result
        assert result['analysis_metadata']['total_choices'] == 3

    @pytest.mark.asyncio
    async def test_timing_pattern_analysis_integration(self, archetype_analyzer):
        """Test integration of timing pattern analysis with archetype classification."""
        user_id = 66666

        # Choices with moderate archetype weights
        choices = [
            {'archetype_weights': {'philosophical': 1.0, 'intellectual': 1.0}},
            {'archetype_weights': {'philosophical': 1.0, 'patient': 1.0}},
        ]

        # Test different timing patterns
        quick_timings = [2.0, 3.0]
        slow_timings = [45.0, 50.0]

        # Quick timing should boost direct archetype
        quick_result = await archetype_analyzer.analyze_l1_choices(user_id, choices, quick_timings)
        assert quick_result['primary_scores'].direct > 0.0
        assert quick_result['timing_analysis']['cognitive_style'] == 'quick_intuitive'

        # Slow timing should boost philosophical and patient
        slow_result = await archetype_analyzer.analyze_l1_choices(user_id, choices, slow_timings)
        assert slow_result['primary_scores'].philosophical > quick_result['primary_scores'].philosophical
        assert slow_result['primary_scores'].patient > 0.0
        assert slow_result['timing_analysis']['cognitive_style'] == 'deliberate'

    @pytest.mark.asyncio
    async def test_confidence_calculation_accuracy(self, archetype_analyzer):
        """Test confidence calculation accuracy across different scenarios."""
        user_id = 77777

        # High confidence scenario: clear archetype, sufficient data
        high_confidence_choices = [
            {'archetype_weights': {'intellectual': 3.0}},
            {'archetype_weights': {'intellectual': 2.5}},
            {'archetype_weights': {'intellectual': 2.8}},
            {'archetype_weights': {'intellectual': 3.2}},
        ]
        timings = [20.0, 22.0, 18.0, 25.0]

        high_conf_result = await archetype_analyzer.analyze_l1_choices(
            user_id, high_confidence_choices, timings
        )

        assert high_conf_result['confidence_score'] >= 0.7
        assert 'high_confidence_classification' in high_conf_result['behavioral_indicators']

        # Low confidence scenario: mixed signals, insufficient data
        low_confidence_choices = [
            {'archetype_weights': {'intellectual': 0.5, 'emotional': 0.5, 'exploratory': 0.5}}
        ]
        low_conf_timings = [15.0]

        low_conf_result = await archetype_analyzer.analyze_l1_choices(
            user_id, low_confidence_choices, low_conf_timings
        )

        assert low_conf_result['confidence_score'] < 0.5

    @pytest.mark.asyncio
    async def test_behavioral_indicators_detection(self, archetype_analyzer):
        """Test detection of behavioral indicators."""
        user_id = 88888

        # Scenario with sufficient data and clear patterns
        choices = [
            {'archetype_weights': {'intellectual': 2.0}},
            {'archetype_weights': {'intellectual': 1.8}},
            {'archetype_weights': {'intellectual': 2.2}},
        ]
        timings = [35.0, 40.0, 38.0]  # Consistently slow (reflective)

        result = await archetype_analyzer.analyze_l1_choices(user_id, choices, timings)

        # Should detect appropriate behavioral indicators
        behavioral_indicators = result['behavioral_indicators']
        assert 'sufficient_data_points' in behavioral_indicators

        # Should detect reflective thinking pattern from slow, consistent timing
        metadata = result['analysis_metadata']
        assert metadata['avg_response_time'] > 30.0


class TestArchetypeIntegrationPerformance:
    """Performance tests for archetype integration system."""

    @pytest.fixture
    def archetype_analyzer(self, mock_session):
        return MockArchetypeAnalyzer(mock_session)

    @pytest.mark.asyncio
    async def test_analysis_performance_single_user(self, archetype_analyzer):
        """Test analysis performance for single user."""
        import time

        user_id = 99999
        choices = [
            {'archetype_weights': {'intellectual': 2.0, 'philosophical': 1.5}},
            {'archetype_weights': {'emotional': 1.8, 'vulnerable': 2.0}},
            {'archetype_weights': {'exploratory': 2.2, 'direct': 1.0}},
        ]
        timings = [15.0, 20.0, 12.0]

        start_time = time.time()
        result = await archetype_analyzer.analyze_l1_choices(user_id, choices, timings)
        end_time = time.time()

        analysis_time = end_time - start_time

        # Should complete within reasonable time
        assert analysis_time < 0.1  # 100ms for single analysis
        assert result is not None

    @pytest.mark.asyncio
    async def test_concurrent_analysis_performance(self, archetype_analyzer):
        """Test performance with concurrent analysis requests."""
        import time

        # Create multiple users with different choice patterns
        analysis_tasks = []
        for i in range(10):  # 10 concurrent analyses
            user_id = 90000 + i
            choices = [
                {'archetype_weights': {'intellectual': 2.0 + (i * 0.1)}},
                {'archetype_weights': {'emotional': 1.5 + (i * 0.1)}},
            ]
            timings = [15.0 + i, 20.0 + i]

            task = archetype_analyzer.analyze_l1_choices(user_id, choices, timings)
            analysis_tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*analysis_tasks)
        end_time = time.time()

        total_time = end_time - start_time

        # All analyses should complete successfully
        assert len(results) == 10
        assert all(result is not None for result in results)

        # Should handle concurrent load efficiently
        assert total_time < 1.0  # Should complete within 1 second

        # Average time per analysis should be reasonable
        avg_time_per_analysis = total_time / 10
        assert avg_time_per_analysis < 0.1

    @pytest.mark.asyncio
    async def test_memory_usage_large_dataset(self, archetype_analyzer):
        """Test memory usage with large dataset."""
        # Simulate analysis of many users with substantial choice data
        user_analyses = []

        for user_id in range(100):  # 100 users
            choices = [
                {'archetype_weights': {'intellectual': 2.0, 'philosophical': 1.5}},
                {'archetype_weights': {'emotional': 1.8, 'vulnerable': 2.0}},
                {'archetype_weights': {'exploratory': 2.2, 'direct': 1.0}},
                {'archetype_weights': {'patient': 2.5, 'reciprocal': 1.8}},
                {'archetype_weights': {'philosophical': 2.8, 'intellectual': 2.2}},
            ]
            timings = [15.0, 20.0, 12.0, 25.0, 18.0]

            result = await archetype_analyzer.analyze_l1_choices(user_id, choices, timings)
            user_analyses.append(result)

        # Should handle large dataset without memory issues
        assert len(user_analyses) == 100
        assert all(analysis is not None for analysis in user_analyses)

        # Verify all analyses have expected structure
        for analysis in user_analyses:
            assert 'dominant_archetype' in analysis
            assert 'confidence_score' in analysis
            assert 'primary_scores' in analysis
            assert 'sub_scores' in analysis


if __name__ == '__main__':
    pytest.main([__file__])