"""
Unit tests for narrative engine's emotional analysis capabilities.
Tests the core emotional intelligence of Diana's narrative system.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

from services.narrative_engine import NarrativeEngine
from database.narrative_models import StoryFragment, UserNarrativeState
from .conftest import TEST_USER_ARCHETYPES, EmotionalTestDataGenerator


class TestEmotionalAnalysis:
    """Test suite for emotional analysis components."""

    @pytest.mark.asyncio
    async def test_response_timing_analysis(self, mock_session, emotional_test_scenarios):
        """Test that response timing is properly analyzed for authenticity."""
        engine = NarrativeEngine(mock_session)
        
        # Test authentic immediate responses
        timing_data = emotional_test_scenarios["timing_patterns"]["authentic_immediate"]
        result = await engine._analyze_response_timing(timing_data)
        
        assert result["authenticity_score"] > 0.7
        assert result["pattern_type"] == "authentic_immediate"
        assert result["consistency_score"] > 0.8

    @pytest.mark.asyncio
    async def test_calculated_timing_detection(self, mock_session, emotional_test_scenarios):
        """Test detection of calculated/artificial response patterns."""
        engine = NarrativeEngine(mock_session)
        
        # Test calculated responses (too consistent)
        timing_data = emotional_test_scenarios["timing_patterns"]["calculated"]
        result = await engine._analyze_response_timing(timing_data)
        
        assert result["authenticity_score"] < 0.5
        assert result["pattern_type"] == "calculated"
        assert result["flags"]["artificial_consistency"] is True

    @pytest.mark.asyncio 
    async def test_emotional_depth_analysis(self, mock_session, emotional_test_scenarios):
        """Test analysis of emotional depth in user responses."""
        engine = NarrativeEngine(mock_session)
        
        # Test high vulnerability response
        response = emotional_test_scenarios["cartography_responses"]["high_vulnerability"][0]
        result = await engine._analyze_emotional_depth(response)
        
        assert result["depth_score"] > 0.8
        assert result["vulnerability_level"] > 0.7
        assert "metaphorical_language" in result["emotional_markers"]
        assert "self_reflection" in result["emotional_markers"]

    @pytest.mark.asyncio
    async def test_surface_response_detection(self, mock_session, emotional_test_scenarios):
        """Test detection of surface-level responses."""
        engine = NarrativeEngine(mock_session)
        
        # Test low vulnerability response
        response = emotional_test_scenarios["cartography_responses"]["low_vulnerability"][0]
        result = await engine._analyze_emotional_depth(response)
        
        assert result["depth_score"] < 0.4
        assert result["vulnerability_level"] < 0.3
        assert result["flags"]["surface_level"] is True

    @pytest.mark.asyncio
    async def test_authenticity_validation_comprehensive(self, mock_session):
        """Test comprehensive authenticity validation combining multiple factors."""
        engine = NarrativeEngine(mock_session)
        
        # Mock a complete user interaction
        interaction_data = {
            "response_text": "The last time I wanted something without explanation was seeing my reflection and feeling completely unknown to myself.",
            "response_time": 18.3,  # Thoughtful timing
            "previous_responses": [],
            "user_id": 12345,
            "context": {"level": "level_3", "fragment_key": "cartography_desire"}
        }
        
        result = await engine.validate_emotional_authenticity(interaction_data)
        
        assert result["overall_authenticity"] > 0.8
        assert result["components"]["timing_authenticity"] > 0.7
        assert result["components"]["emotional_depth"] > 0.8
        assert result["components"]["consistency"] > 0.6
        assert result["confidence_level"] > 0.75


class TestArchetypeClassification:
    """Test suite for user archetype classification."""

    @pytest.mark.asyncio
    async def test_explorer_deep_classification(self, mock_session, user_behavior_profiles):
        """Test classification of Explorer Deep archetype."""
        engine = NarrativeEngine(mock_session)
        profile = user_behavior_profiles["explorer_deep"]
        
        # Simulate conversation history
        conversation_data = EmotionalTestDataGenerator.generate_conversation_sequence(
            profile, num_interactions=3, scenario="cartography_exploration"
        )
        
        result = await engine.classify_user_archetype(12345, conversation_data)
        
        assert result["primary_archetype"] == "explorer_deep"
        assert result["confidence"] > 0.8
        assert result["traits"]["attention_to_detail"] > 0.8
        assert result["traits"]["depth_seeking"] > 0.8

    @pytest.mark.asyncio
    async def test_direct_authentic_classification(self, mock_session, user_behavior_profiles):
        """Test classification of Direct Authentic archetype."""
        engine = NarrativeEngine(mock_session)
        profile = user_behavior_profiles["direct_authentic"]
        
        conversation_data = EmotionalTestDataGenerator.generate_conversation_sequence(
            profile, num_interactions=3, scenario="direct_responses"
        )
        
        result = await engine.classify_user_archetype(12345, conversation_data)
        
        assert result["primary_archetype"] == "direct_authentic"
        assert result["confidence"] > 0.8
        assert result["traits"]["directness"] > 0.8
        assert result["traits"]["authenticity"] > 0.8

    @pytest.mark.asyncio
    async def test_archetype_evolution_tracking(self, mock_session):
        """Test tracking of archetype evolution over time."""
        engine = NarrativeEngine(mock_session)
        
        # Simulate archetype evolution (should be stable, not erratic)
        classifications_over_time = [
            {"archetype": "explorer_deep", "confidence": 0.7, "timestamp": datetime.utcnow() - timedelta(days=7)},
            {"archetype": "explorer_deep", "confidence": 0.8, "timestamp": datetime.utcnow() - timedelta(days=3)},
            {"archetype": "explorer_deep", "confidence": 0.85, "timestamp": datetime.utcnow()}
        ]
        
        result = await engine._analyze_archetype_evolution(12345, classifications_over_time)
        
        assert result["stability_score"] > 0.9
        assert result["primary_archetype"] == "explorer_deep"
        assert result["confidence_trend"] == "increasing"

    @pytest.mark.asyncio 
    async def test_mixed_archetype_detection(self, mock_session):
        """Test detection of users showing mixed archetype traits."""
        engine = NarrativeEngine(mock_session)
        
        # Mixed traits conversation
        mixed_conversation = [
            {"response_time": 1.2, "depth_score": 0.9},  # Quick but deep (unusual)
            {"response_time": 25.0, "depth_score": 0.3},  # Slow but shallow (unusual)
            {"response_time": 15.0, "depth_score": 0.8}   # Normal thoughtful
        ]
        
        result = await engine.classify_user_archetype(12345, mixed_conversation)
        
        assert "mixed_traits" in result
        assert result["confidence"] < 0.7  # Lower confidence for mixed patterns
        assert len(result["secondary_archetypes"]) > 0


class TestNarrativeAdaptation:
    """Test suite for narrative content adaptation based on emotional analysis."""

    @pytest.mark.asyncio
    async def test_diana_response_adaptation_high_vulnerability(self, mock_session, diana_response_validation):
        """Test Diana's response adaptation for high vulnerability users."""
        engine = NarrativeEngine(mock_session)
        
        user_profile = {
            "archetype": "explorer_deep",
            "vulnerability_level": 0.9,
            "authenticity_score": 0.85,
            "emotional_depth": 0.9
        }
        
        result = await engine.adapt_narrative_content("level_3_recognition", user_profile)
        
        # Validate Diana's response contains appropriate recognition patterns
        response_text = result["adapted_content"]["diana_response"]
        validation_patterns = diana_response_validation["recognition_patterns"]["high_vulnerability"]
        
        assert any(pattern in response_text.lower() for pattern in validation_patterns)
        assert result["adaptation_confidence"] > 0.8
        assert result["personalization_level"] == "high"

    @pytest.mark.asyncio
    async def test_lucien_guidance_adaptation(self, mock_session):
        """Test Lucien's guidance adaptation based on user behavior patterns."""
        engine = NarrativeEngine(mock_session)
        
        user_profile = {
            "archetype": "persistent_patient",
            "consistency_score": 0.9,
            "patience_indicators": 0.8
        }
        
        result = await engine.adapt_narrative_content("level_2_lucien_guidance", user_profile)
        
        lucien_response = result["adapted_content"]["lucien_response"]
        assert "persistencia" in lucien_response.lower() or "paciencia" in lucien_response.lower()
        assert result["character_voice"]["lucien"]["recognition_level"] == "high"

    @pytest.mark.asyncio
    async def test_content_adaptation_archetype_specific(self, mock_session, diana_response_validation):
        """Test archetype-specific content adaptation."""
        engine = NarrativeEngine(mock_session)
        
        for archetype in ["explorer_deep", "direct_authentic", "poet_desire", "analytic_empathic", "persistent_patient"]:
            user_profile = {
                "archetype": archetype,
                "authenticity_score": 0.8,
                "consistency_score": 0.8
            }
            
            result = await engine.adapt_narrative_content("archetype_recognition", user_profile)
            
            # Validate archetype-specific responses
            expected_pattern = diana_response_validation["archetype_specific"][archetype]
            response_text = result["adapted_content"]["diana_response"]
            
            assert expected_pattern.lower() in response_text.lower()

    @pytest.mark.asyncio
    async def test_progressive_intimacy_adaptation(self, mock_session):
        """Test progressive intimacy level adaptation."""
        engine = NarrativeEngine(mock_session)
        
        # Test progression through intimacy levels
        intimacy_levels = [
            {"level": 1, "trust_score": 0.3, "expected_intimacy": "curious"},
            {"level": 3, "trust_score": 0.6, "expected_intimacy": "vulnerable"}, 
            {"level": 5, "trust_score": 0.9, "expected_intimacy": "deeply_intimate"}
        ]
        
        for test_case in intimacy_levels:
            user_profile = {
                "level": test_case["level"],
                "trust_score": test_case["trust_score"],
                "interaction_history": []
            }
            
            result = await engine.adapt_narrative_content("diana_intimacy_response", user_profile)
            
            assert result["intimacy_level"] == test_case["expected_intimacy"]
            assert result["vulnerability_shared"] <= test_case["trust_score"]


class TestEmotionalConsistencyValidation:
    """Test suite for emotional consistency validation across interactions."""

    @pytest.mark.asyncio
    async def test_personality_consistency_validation(self, mock_session, emotional_consistency_validators):
        """Test validation of personality consistency over time."""
        engine = NarrativeEngine(mock_session)
        
        # Consistent interaction history
        consistent_history = [
            {"personality_consistency": 0.8, "timestamp": datetime.utcnow() - timedelta(days=3)},
            {"personality_consistency": 0.85, "timestamp": datetime.utcnow() - timedelta(days=1)},
            {"personality_consistency": 0.82, "timestamp": datetime.utcnow()}
        ]
        
        validator = emotional_consistency_validators["validate_progression_coherence"]
        result = validator(consistent_history)
        
        assert result["valid"] is True
        assert result["coherence_score"] > 0.7

    @pytest.mark.asyncio
    async def test_inconsistency_detection(self, mock_session, emotional_consistency_validators):
        """Test detection of personality inconsistencies."""
        engine = NarrativeEngine(mock_session)
        
        # Inconsistent interaction history
        inconsistent_history = [
            {"personality_consistency": 0.9, "timestamp": datetime.utcnow() - timedelta(days=3)},
            {"personality_consistency": 0.2, "timestamp": datetime.utcnow() - timedelta(days=1)}, # Sudden drop
            {"personality_consistency": 0.8, "timestamp": datetime.utcnow()}
        ]
        
        validator = emotional_consistency_validators["validate_progression_coherence"]
        result = validator(inconsistent_history)
        
        assert result["valid"] is False
        assert result["reason"] == "personality_inconsistency"
        assert result["variance"] > 0.3

    @pytest.mark.asyncio
    async def test_archetype_stability_validation(self, mock_session, emotional_consistency_validators):
        """Test archetype classification stability over time."""
        engine = NarrativeEngine(mock_session)
        
        # Stable archetype classification
        stable_classifications = ["explorer_deep", "explorer_deep", "explorer_deep", "explorer_deep"]
        
        validator = emotional_consistency_validators["validate_archetype_stability"]
        result = validator(stable_classifications)
        
        assert result["valid"] is True
        assert result["primary_archetype"] == "explorer_deep"

    @pytest.mark.asyncio
    async def test_archetype_instability_detection(self, mock_session, emotional_consistency_validators):
        """Test detection of unstable archetype classifications."""
        engine = NarrativeEngine(mock_session)
        
        # Unstable archetype classification
        unstable_classifications = ["explorer_deep", "direct_authentic", "poet_desire", "analytic_empathic"]
        
        validator = emotional_consistency_validators["validate_archetype_stability"]
        result = validator(unstable_classifications)
        
        assert result["valid"] is False
        assert result["reason"] == "archetype_instability"


class TestEdgeCasesAndErrorHandling:
    """Test suite for edge cases and error handling in emotional system."""

    @pytest.mark.asyncio
    async def test_empty_response_handling(self, mock_session):
        """Test handling of empty or null responses."""
        engine = NarrativeEngine(mock_session)
        
        # Test empty string
        result = await engine._analyze_emotional_depth("")
        assert result["error"] == "insufficient_data"
        assert result["depth_score"] == 0.0
        
        # Test None
        result = await engine._analyze_emotional_depth(None)
        assert result["error"] == "invalid_input"

    @pytest.mark.asyncio
    async def test_extremely_long_response_handling(self, mock_session):
        """Test handling of extremely long responses."""
        engine = NarrativeEngine(mock_session)
        
        # Extremely long response
        long_response = "test " * 2000  # Very long response
        result = await engine._analyze_emotional_depth(long_response)
        
        assert result["warning"] == "input_truncated"
        assert len(result["processed_text"]) <= engine.MAX_RESPONSE_LENGTH

    @pytest.mark.asyncio
    async def test_invalid_timing_data_handling(self, mock_session):
        """Test handling of invalid timing data."""
        engine = NarrativeEngine(mock_session)
        
        # Invalid timing data
        invalid_timing = [-1, None, "invalid", 1000000]  # Mix of invalid values
        result = await engine._analyze_response_timing(invalid_timing)
        
        assert result["error"] == "invalid_timing_data"
        assert result["cleaned_data_points"] < len(invalid_timing)

    @pytest.mark.asyncio
    async def test_memory_efficiency_large_history(self, mock_session, performance_benchmarks):
        """Test memory efficiency with large interaction histories."""
        engine = NarrativeEngine(mock_session)
        
        # Create large interaction history
        large_history = []
        for i in range(1000):
            large_history.append({
                "timestamp": datetime.utcnow() - timedelta(minutes=i),
                "response": f"Test response {i}" * 50,  # Reasonably sized responses
                "analysis": {"depth": 0.5, "authenticity": 0.7}
            })
        
        # Process with memory monitoring
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        result = await engine.process_large_interaction_history(12345, large_history)
        
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before
        
        assert memory_used < performance_benchmarks["memory_limits"]["max_session_memory_mb"]
        assert result["processed_interactions"] == 1000
        assert result["memory_optimized"] is True


class TestRegressionSafety:
    """Test suite to ensure new emotional features don't break existing functionality."""

    @pytest.mark.asyncio
    async def test_basic_narrative_progression_still_works(self, mock_session):
        """Test that basic narrative progression isn't broken by emotional analysis."""
        engine = NarrativeEngine(mock_session)
        
        # Mock basic fragment progression
        mock_session.execute.return_value.scalar_one_or_none.return_value = MagicMock(
            key="level_2_fragment",
            reward_besitos=10,
            unlocks_achievement_id=None
        )
        
        result = await engine.process_user_decision(12345, 0)
        
        # Basic progression should still work
        assert result is not None
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_point_rewards_unaffected(self, mock_session):
        """Test that point reward system isn't affected by emotional analysis."""
        engine = NarrativeEngine(mock_session)
        
        # Should still process rewards normally
        fragment = MagicMock()
        fragment.reward_besitos = 50
        fragment.unlocks_achievement_id = None
        
        await engine._process_fragment_rewards(12345, fragment)
        
        # Point service should be called normally
        assert engine.point_service is not None or engine.bot is None  # Expected behavior

    @pytest.mark.asyncio
    async def test_existing_handlers_compatibility(self, mock_session):
        """Test that existing handlers can still call narrative engine."""
        engine = NarrativeEngine(mock_session)
        
        # Simulate existing handler call patterns
        user_state = await engine._get_or_create_user_state(12345)
        
        # Should create user state without emotional analysis errors
        assert user_state is not None
        assert hasattr(user_state, 'user_id')
        assert user_state.user_id == 12345


# Performance benchmarking tests
class TestPerformanceBenchmarks:
    """Test suite for performance validation of emotional analysis."""

    @pytest.mark.asyncio
    async def test_emotional_analysis_performance(self, mock_session, performance_benchmarks):
        """Test that emotional analysis meets performance requirements."""
        engine = NarrativeEngine(mock_session)
        
        import time
        
        # Test emotional analysis performance
        start_time = time.time()
        
        response_data = "This is a moderately deep emotional response that contains some vulnerability and authenticity markers."
        result = await engine._analyze_emotional_depth(response_data)
        
        end_time = time.time()
        analysis_time = end_time - start_time
        
        benchmark = performance_benchmarks["response_time_limits"]["emotional_analysis"]
        assert analysis_time < benchmark, f"Emotional analysis took {analysis_time}s, limit is {benchmark}s"
        assert result["depth_score"] > 0

    @pytest.mark.asyncio
    async def test_archetype_classification_performance(self, mock_session, performance_benchmarks):
        """Test that archetype classification meets performance requirements."""
        engine = NarrativeEngine(mock_session)
        
        import time
        
        # Create realistic conversation data
        conversation_data = [
            {"response_time": 15.0, "response": "Thoughtful response", "depth_score": 0.8}
            for _ in range(5)
        ]
        
        start_time = time.time()
        result = await engine.classify_user_archetype(12345, conversation_data)
        end_time = time.time()
        
        classification_time = end_time - start_time
        benchmark = performance_benchmarks["response_time_limits"]["archetype_classification"]
        
        assert classification_time < benchmark, f"Archetype classification took {classification_time}s, limit is {benchmark}s"

    @pytest.mark.asyncio
    async def test_concurrent_user_analysis(self, mock_session, performance_benchmarks):
        """Test performance with multiple concurrent users."""
        engine = NarrativeEngine(mock_session)
        
        async def analyze_user(user_id: int):
            """Simulate analysis for one user."""
            conversation = [
                {"response": f"User {user_id} response", "response_time": 10.0}
                for _ in range(3)
            ]
            return await engine.classify_user_archetype(user_id, conversation)
        
        import time
        
        # Test with multiple concurrent users
        start_time = time.time()
        
        tasks = [analyze_user(i) for i in range(50)]  # 50 concurrent users
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should handle concurrent analysis efficiently
        assert total_time < 5.0  # Should complete within 5 seconds
        assert len(results) == 50
        assert all(result["primary_archetype"] is not None for result in results if result)