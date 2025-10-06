"""
Integration tests for emotional system interactions.
Tests the complete emotional analysis pipeline and service integrations.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

from services.narrative_engine import NarrativeEngine
from services.narrative_service import NarrativeService
from database.models import User, UserNarrativeState
from database.narrative_models import StoryFragment, NarrativeChoice


class TestEmotionalServiceIntegration:
    """Test integration between emotional analysis and other services."""

    @pytest.fixture
    async def integrated_services(self, mock_session):
        """Setup integrated services for testing."""
        narrative_engine = NarrativeEngine(mock_session)
        narrative_service = NarrativeService(mock_session)
        
        # Mock point service integration
        with patch('services.point_service.PointService') as mock_point_service:
            mock_point_service.return_value.add_points = AsyncMock()
            yield {
                "narrative_engine": narrative_engine,
                "narrative_service": narrative_service,
                "point_service": mock_point_service.return_value,
                "session": mock_session
            }

    @pytest.mark.asyncio
    async def test_emotional_analysis_triggers_rewards(self, integrated_services):
        """Test that high emotional authenticity triggers reward bonuses."""
        engine = integrated_services["narrative_engine"]
        session = integrated_services["session"]
        
        # Mock user with high authenticity score
        user_data = {
            "user_id": 12345,
            "authenticity_score": 0.9,
            "emotional_depth": 0.85,
            "vulnerability_level": 0.8
        }
        
        # Mock fragment with emotional rewards
        mock_fragment = MagicMock()
        mock_fragment.key = "level_3_vulnerable_moment"
        mock_fragment.reward_besitos = 50
        mock_fragment.emotional_bonus_multiplier = 1.5  # New field for emotional bonuses
        
        # Process fragment with emotional analysis
        result = await engine._process_fragment_with_emotional_analysis(
            user_data["user_id"], 
            mock_fragment,
            user_data
        )
        
        # Should apply emotional bonus
        assert result["base_reward"] == 50
        assert result["emotional_bonus"] == 25  # 50% bonus for high authenticity
        assert result["total_reward"] == 75

    @pytest.mark.asyncio
    async def test_archetype_influences_narrative_path(self, integrated_services):
        """Test that user archetype influences available narrative paths."""
        engine = integrated_services["narrative_engine"]
        session = integrated_services["session"]
        
        # Mock user with specific archetype
        session.execute.return_value.scalar_one_or_none.side_effect = [
            # First call: user narrative state
            MagicMock(
                user_id=12345,
                current_fragment_key="level_3_crossroads",
                archetype_classification="explorer_deep",
                emotional_profile={"depth_seeking": 0.9, "patience": 0.8}
            ),
            # Second call: current fragment  
            MagicMock(
                key="level_3_crossroads",
                available_paths=["path_surface", "path_deep", "path_mysterious"]
            )
        ]
        
        result = await engine.get_archetype_adapted_paths(12345)
        
        # Explorer Deep should get access to deeper paths
        available_paths = result["available_paths"]
        assert "path_deep" in available_paths
        assert "path_mysterious" in available_paths
        assert result["recommended_path"] == "path_deep"  # Best match for archetype

    @pytest.mark.asyncio
    async def test_emotional_state_persists_across_sessions(self, integrated_services):
        """Test that emotional analysis state persists across user sessions."""
        engine = integrated_services["narrative_engine"]
        session = integrated_services["session"]
        
        # Simulate user session 1
        user_id = 12345
        session_1_data = {
            "responses": ["Deep thoughtful response about vulnerability"],
            "timing": [18.5],  # Thoughtful timing
            "authenticity_score": 0.85
        }
        
        # Process session 1
        await engine.process_emotional_session(user_id, session_1_data)
        
        # Mock saved state
        emotional_state = MagicMock()
        emotional_state.user_id = user_id
        emotional_state.archetype_classification = "explorer_deep"
        emotional_state.authenticity_history = [0.85]
        emotional_state.consistency_score = 0.8
        
        session.execute.return_value.scalar_one_or_none.return_value = emotional_state
        
        # Simulate user session 2 (later time)
        session_2_data = {
            "responses": ["Another deep response building on previous themes"],
            "timing": [22.1],  # Similar thoughtful timing
            "context": {"previous_sessions": 1}
        }
        
        result = await engine.process_emotional_session(user_id, session_2_data)
        
        # Should maintain continuity
        assert result["archetype_classification"] == "explorer_deep"
        assert result["consistency_maintained"] is True
        assert len(result["authenticity_history"]) == 2
        assert result["progression_coherent"] is True

    @pytest.mark.asyncio
    async def test_emotional_analysis_affects_diana_responses(self, integrated_services):
        """Test that emotional analysis directly affects Diana's response generation."""
        engine = integrated_services["narrative_engine"]
        session = integrated_services["session"]
        
        # Mock high emotional authenticity user
        user_profile = {
            "user_id": 12345,
            "archetype": "direct_authentic",
            "authenticity_score": 0.9,
            "vulnerability_level": 0.8,
            "emotional_consistency": 0.85
        }
        
        # Mock fragment requiring emotional adaptation
        fragment_key = "level_3_diana_recognition"
        
        result = await engine.generate_emotionally_adapted_response(
            fragment_key, 
            user_profile
        )
        
        # Diana's response should be highly personalized
        diana_response = result["diana_response"]
        assert result["personalization_level"] == "high"
        assert result["emotional_recognition"] > 0.8
        
        # Should contain authenticity recognition patterns
        authenticity_patterns = [
            "tu honestidad", "sin máscaras", "genuino", "auténtico"
        ]
        assert any(pattern in diana_response.lower() for pattern in authenticity_patterns)

    @pytest.mark.asyncio
    async def test_emotional_failure_graceful_degradation(self, integrated_services):
        """Test graceful degradation when emotional analysis fails."""
        engine = integrated_services["narrative_engine"]
        session = integrated_services["session"]
        
        # Mock emotional analysis service failure
        with patch.object(engine, '_analyze_emotional_depth', side_effect=Exception("Analysis service down")):
            
            user_interaction = {
                "user_id": 12345,
                "response": "Test response",
                "fragment_key": "level_2_progression"
            }
            
            result = await engine.process_user_interaction_with_fallback(user_interaction)
            
            # Should fall back to basic narrative progression
            assert result["emotional_analysis"] == "unavailable"
            assert result["narrative_progression"] == "success"
            assert result["fallback_mode"] is True
            assert result["basic_functionality_maintained"] is True

    @pytest.mark.asyncio
    async def test_cross_level_emotional_continuity(self, integrated_services):
        """Test emotional continuity across narrative levels."""
        engine = integrated_services["narrative_engine"]
        session = integrated_services["session"]
        
        # Simulate progression through multiple levels
        level_interactions = [
            {
                "level": 1,
                "fragment_key": "level_1_intro",
                "user_response": "Curious but cautious response",
                "expected_archetype": "explorer_cautious"
            },
            {
                "level": 2, 
                "fragment_key": "level_2_deeper",
                "user_response": "More open, detailed response showing growth",
                "expected_archetype": "explorer_deep"  # Evolution
            },
            {
                "level": 3,
                "fragment_key": "level_3_vulnerable",
                "user_response": "Very vulnerable, authentic sharing",
                "expected_archetype": "explorer_deep"  # Consistency
            }
        ]
        
        user_id = 12345
        emotional_journey = []
        
        for interaction in level_interactions:
            result = await engine.process_level_progression_with_emotional_tracking(
                user_id, 
                interaction,
                previous_journey=emotional_journey
            )
            emotional_journey.append(result)
        
        # Validate emotional journey coherence
        assert len(emotional_journey) == 3
        
        # Should show growth, not inconsistency
        authenticity_scores = [j["authenticity_score"] for j in emotional_journey]
        assert authenticity_scores[2] > authenticity_scores[0]  # Growth over time
        
        # Archetype should evolve logically
        archetypes = [j["archetype"] for j in emotional_journey]
        assert archetypes[-1] == "explorer_deep"  # Final classification stable
        
        # Diana's recognition should acknowledge the journey
        final_response = emotional_journey[-1]["diana_response"]
        journey_recognition_patterns = [
            "cómo has evolucionado", "desde nuestro primer encuentro", 
            "tu crecimiento", "esta transformación"
        ]
        assert any(pattern in final_response.lower() for pattern in journey_recognition_patterns)


class TestDatabaseIntegrationEmotional:
    """Test database operations for emotional analysis data."""

    @pytest.mark.asyncio
    async def test_emotional_state_persistence(self, mock_session):
        """Test persistence of emotional analysis state."""
        
        # Create emotional state data
        emotional_state = {
            "user_id": 12345,
            "archetype_classification": "explorer_deep",
            "authenticity_history": [0.7, 0.8, 0.85],
            "consistency_score": 0.82,
            "emotional_profile": {
                "depth_seeking": 0.9,
                "vulnerability_comfort": 0.7,
                "patience_level": 0.8
            },
            "last_updated": datetime.utcnow()
        }
        
        # Mock database save
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        # Save emotional state
        from services.emotional_state_service import EmotionalStateService
        emotion_service = EmotionalStateService(mock_session)
        
        result = await emotion_service.save_emotional_state(emotional_state)
        
        assert result["saved"] is True
        assert mock_session.add.called
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_emotional_history_retrieval(self, mock_session):
        """Test retrieval of emotional analysis history."""
        
        # Mock historical data
        mock_history = [
            {
                "timestamp": datetime.utcnow() - timedelta(days=7),
                "archetype": "explorer_cautious",
                "authenticity": 0.6
            },
            {
                "timestamp": datetime.utcnow() - timedelta(days=3),
                "archetype": "explorer_deep",
                "authenticity": 0.8
            },
            {
                "timestamp": datetime.utcnow(),
                "archetype": "explorer_deep", 
                "authenticity": 0.85
            }
        ]
        
        mock_session.execute.return_value.scalars.return_value.all.return_value = mock_history
        
        from services.emotional_state_service import EmotionalStateService
        emotion_service = EmotionalStateService(mock_session)
        
        history = await emotion_service.get_emotional_history(12345, days_back=7)
        
        assert len(history) == 3
        assert history[-1]["authenticity"] > history[0]["authenticity"]  # Shows growth

    @pytest.mark.asyncio
    async def test_emotional_analytics_aggregation(self, mock_session):
        """Test aggregation of emotional analytics across users."""
        
        # Mock aggregate data
        mock_aggregates = {
            "total_users_analyzed": 1000,
            "archetype_distribution": {
                "explorer_deep": 0.35,
                "direct_authentic": 0.25,
                "poet_desire": 0.15,
                "analytic_empathic": 0.15,
                "persistent_patient": 0.10
            },
            "average_authenticity_score": 0.73,
            "emotional_engagement_trend": "increasing"
        }
        
        mock_session.execute.return_value.scalar.return_value = 1000
        
        from services.emotional_analytics_service import EmotionalAnalyticsService
        analytics_service = EmotionalAnalyticsService(mock_session)
        
        result = await analytics_service.get_system_emotional_analytics()
        
        assert result["total_users"] > 0
        assert "archetype_distribution" in result
        assert result["average_authenticity"] > 0


class TestRealTimeEmotionalProcessing:
    """Test real-time emotional analysis during user interactions."""

    @pytest.mark.asyncio
    async def test_real_time_authenticity_monitoring(self, integrated_services):
        """Test real-time monitoring of user authenticity during interaction."""
        engine = integrated_services["narrative_engine"]
        
        # Simulate real-time conversation
        conversation_stream = [
            {"timestamp": 0, "response": "I'm curious about this experience"},
            {"timestamp": 15, "response": "This feels different from what I expected"},
            {"timestamp": 30, "response": "I find myself genuinely moved by this interaction"},
            {"timestamp": 45, "response": "There's something authentic happening here that I wasn't prepared for"}
        ]
        
        authenticity_scores = []
        
        for message in conversation_stream:
            real_time_analysis = await engine.analyze_message_real_time(
                user_id=12345,
                message=message,
                conversation_context=authenticity_scores
            )
            
            authenticity_scores.append(real_time_analysis["authenticity_score"])
        
        # Should show increasing authenticity over time
        assert authenticity_scores[-1] > authenticity_scores[0]
        assert all(score > 0.3 for score in authenticity_scores)  # Minimum threshold
        
        # Final score should be high for authentic progression
        assert authenticity_scores[-1] > 0.8

    @pytest.mark.asyncio 
    async def test_emotional_red_flags_detection(self, integrated_services):
        """Test detection of emotional red flags in real-time."""
        engine = integrated_services["narrative_engine"]
        
        # Simulate concerning patterns
        concerning_conversation = [
            {"response": "I love this game", "timestamp": 1.2},  # Too quick, generic
            {"response": "This is exactly what I hoped for", "timestamp": 0.8},  # Too quick, performative
            {"response": "You are perfect Diana", "timestamp": 1.0},  # Too quick, idealization
        ]
        
        red_flags = []
        
        for message in concerning_conversation:
            analysis = await engine.analyze_message_real_time(
                user_id=12345,
                message=message,
                conversation_context=red_flags
            )
            
            if analysis.get("red_flags"):
                red_flags.extend(analysis["red_flags"])
        
        # Should detect multiple concerning patterns
        assert len(red_flags) > 0
        expected_flags = ["response_too_quick", "idealization", "performative_language"]
        assert any(flag in red_flags for flag in expected_flags)

    @pytest.mark.asyncio
    async def test_adaptive_response_generation(self, integrated_services):
        """Test adaptive response generation based on real-time emotional analysis."""
        engine = integrated_services["narrative_engine"]
        
        # High authenticity user interaction
        high_auth_context = {
            "user_id": 12345,
            "current_authenticity": 0.9,
            "emotional_depth": 0.8,
            "archetype": "explorer_deep",
            "interaction_quality": "high"
        }
        
        response = await engine.generate_adaptive_response(
            fragment_key="level_3_moment",
            user_context=high_auth_context
        )
        
        # Should generate highly personalized response
        assert response["personalization_level"] == "high"
        assert response["emotional_mirroring"] > 0.8
        assert len(response["diana_response"]) > 100  # Substantial response
        
        # Low authenticity user interaction
        low_auth_context = {
            "user_id": 67890,
            "current_authenticity": 0.3,
            "emotional_depth": 0.2,
            "archetype": "undetermined",
            "interaction_quality": "low"
        }
        
        response = await engine.generate_adaptive_response(
            fragment_key="level_3_moment",
            user_context=low_auth_context
        )
        
        # Should generate more guarded response
        assert response["personalization_level"] == "low"
        assert response["emotional_mirroring"] < 0.5
        # Diana should be more cautious with low authenticity users


class TestEmotionalSystemLoadTesting:
    """Test emotional system under load conditions."""

    @pytest.mark.asyncio
    async def test_concurrent_emotional_analysis(self, integrated_services):
        """Test emotional analysis with many concurrent users."""
        engine = integrated_services["narrative_engine"]
        
        async def simulate_user_session(user_id: int):
            """Simulate one user's emotional analysis session."""
            responses = [
                f"User {user_id} - I'm exploring this experience with curiosity",
                f"User {user_id} - This feels meaningful to me in unexpected ways",
                f"User {user_id} - I find myself being more open than I anticipated"
            ]
            
            results = []
            for response in responses:
                analysis = await engine.analyze_message_real_time(
                    user_id=user_id,
                    message={"response": response, "timestamp": 15.0},
                    conversation_context=results
                )
                results.append(analysis)
            
            return results
        
        # Test with 100 concurrent users
        user_ids = range(1000, 1100)
        tasks = [simulate_user_session(user_id) for user_id in user_ids]
        
        import time
        start_time = time.time()
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should handle 100 concurrent users efficiently
        assert total_time < 10.0  # Complete within 10 seconds
        assert len(results) == 100
        assert all(len(user_results) == 3 for user_results in results)

    @pytest.mark.asyncio
    async def test_memory_efficiency_emotional_analysis(self, integrated_services):
        """Test memory efficiency of emotional analysis components."""
        engine = integrated_services["narrative_engine"]
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Get baseline memory
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process large amount of emotional data
        for user_id in range(1000, 1500):  # 500 users
            emotional_history = []
            
            # Generate substantial emotional history for each user
            for i in range(50):  # 50 interactions per user
                analysis = {
                    "user_id": user_id,
                    "timestamp": datetime.utcnow() - timedelta(minutes=i),
                    "response": f"Emotional response {i}" * 10,  # Substantial content
                    "authenticity_score": 0.7 + (i * 0.005),
                    "emotional_markers": ["depth", "authenticity", "growth"]
                }
                emotional_history.append(analysis)
            
            # Process the history
            await engine.process_emotional_history_batch(user_id, emotional_history)
        
        # Check memory usage
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        # Should not use excessive memory (less than 200MB increase)
        assert memory_increase < 200, f"Memory increase too large: {memory_increase}MB"

    @pytest.mark.asyncio
    async def test_emotional_analysis_accuracy_under_load(self, integrated_services):
        """Test that emotional analysis accuracy is maintained under load."""
        engine = integrated_services["narrative_engine"]
        
        # Create test cases with known expected results
        test_cases = [
            {
                "response": "I feel vulnerable sharing this, but there's something about this experience that touches the deepest parts of who I am.",
                "expected_depth": 0.9,
                "expected_vulnerability": 0.9,
                "expected_authenticity": 0.8
            },
            {
                "response": "This is interesting I suppose.",
                "expected_depth": 0.2,
                "expected_vulnerability": 0.1,
                "expected_authenticity": 0.4
            },
            {
                "response": "I find myself drawn to understand the complexity of connection, the way vulnerability and strength interweave in moments like these.",
                "expected_depth": 0.8,
                "expected_vulnerability": 0.7,
                "expected_authenticity": 0.8
            }
        ]
        
        # Run test cases many times concurrently
        async def analyze_test_case(test_case, iteration):
            analysis = await engine._analyze_emotional_depth(test_case["response"])
            
            return {
                "iteration": iteration,
                "depth_accurate": abs(analysis["depth_score"] - test_case["expected_depth"]) < 0.2,
                "vulnerability_accurate": abs(analysis["vulnerability_level"] - test_case["expected_vulnerability"]) < 0.2,
                "authenticity_accurate": abs(analysis.get("authenticity_score", 0.5) - test_case["expected_authenticity"]) < 0.2
            }
        
        # Run each test case 100 times concurrently
        all_tasks = []
        for test_case in test_cases:
            for i in range(100):
                all_tasks.append(analyze_test_case(test_case, i))
        
        results = await asyncio.gather(*all_tasks)
        
        # Calculate accuracy
        depth_accuracy = sum(1 for r in results if r["depth_accurate"]) / len(results)
        vulnerability_accuracy = sum(1 for r in results if r["vulnerability_accurate"]) / len(results)
        authenticity_accuracy = sum(1 for r in results if r["authenticity_accurate"]) / len(results)
        
        # Should maintain high accuracy even under load
        assert depth_accuracy > 0.85, f"Depth accuracy too low: {depth_accuracy}"
        assert vulnerability_accuracy > 0.85, f"Vulnerability accuracy too low: {vulnerability_accuracy}"
        assert authenticity_accuracy > 0.80, f"Authenticity accuracy too low: {authenticity_accuracy}"