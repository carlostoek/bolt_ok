"""
Integration Tests for Emotional Analysis System

Tests the complete integration between EmotionalAnalysisService and CoordinadorCentral.
Validates that the emotional analysis enhances narrative flows without breaking existing functionality.

CRITICAL: These tests ensure zero breaking changes to existing functionality.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.coordinador_central import CoordinadorCentral, AccionUsuario
from services.emotional_analysis_service import EmotionalAnalysisService
from database.emotional_models import UserEmotionalProfile, ResponseType, VulnerabilityLevel


class TestEmotionalAnalysisIntegration:
    """Integration tests for emotional analysis with existing narrative system"""
    
    @pytest.fixture
    async def mock_session(self):
        """Mock database session for integration tests"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.add = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session
    
    @pytest.fixture
    async def coordinador(self, mock_session):
        """CoordinadorCentral instance with mocked dependencies"""
        # Mock all the service dependencies
        with patch('services.coordinador_central.ChannelEngagementService'):
            with patch('services.coordinador_central.NarrativePointService'):
                with patch('services.coordinador_central.NarrativeAccessService'):
                    with patch('services.coordinador_central.NarrativeService'):
                        with patch('services.coordinador_central.PointService'):
                            with patch('services.coordinador_central.UserArchetypeService'):
                                coordinador = CoordinadorCentral(mock_session)
                                
                                # Mock the services to return predictable results
                                coordinador.narrative_point.process_decision_with_points = AsyncMock(return_value={
                                    "type": "success",
                                    "fragment": {"key": "test_fragment", "text": "Test narrative"},
                                    "decision_content": "Test decision content"
                                })
                                
                                coordinador.archetype_service.track_behavioral_event = AsyncMock()
                                coordinador.archetype_service.get_personalized_response = AsyncMock(
                                    return_value="Personalized message from Diana"
                                )
                                
                                return coordinador
    
    @pytest.fixture
    def sample_emotional_profile(self):
        """Sample emotional profile for testing"""
        return UserEmotionalProfile(
            user_id=12345,
            impulso_autentico_percentage=25.0,
            pausa_reflexiva_percentage=60.0,
            contemplacion_percentage=10.0,
            abandono_percentage=5.0,
            consistency_score=0.8,
            vulnerability_progression=0.4,
            authenticity_score=0.75,
            dominant_emotional_pattern=ResponseType.PAUSA_REFLEXIVA,
            current_vulnerability_level=VulnerabilityLevel.TENTATIVE,
            emotional_growth_trajectory=0.12,
            total_interactions=30,
            average_response_time=8.2
        )

    # Core Integration Tests
    
    async def test_decision_flow_with_emotional_analysis(self, coordinador, mock_session, sample_emotional_profile):
        """Test that decision flow includes emotional analysis without breaking existing functionality"""
        user_id = 12345
        decision_id = 42
        
        # Mock emotional profile retrieval
        mock_session.execute.return_value.scalar_one_or_none.return_value = sample_emotional_profile
        
        # Execute decision flow
        result = await coordinador._flujo_tomar_decision(user_id, decision_id)
        
        # Verify existing functionality still works
        assert result["success"] is True
        assert result["action"] == "decision_success"
        assert "message" in result
        assert "fragment" in result
        assert "decision_type" in result
        
        # Verify emotional analysis was integrated
        assert "emotional_analysis" in result
        emotional_data = result["emotional_analysis"]
        assert "response_type" in emotional_data
        assert "vulnerability_level" in emotional_data
        assert "analysis_time_ms" in emotional_data
        
        # Verify performance requirement
        assert emotional_data["analysis_time_ms"] < 50
        
        # Verify archetype service was still called (existing functionality preserved)
        coordinador.archetype_service.track_behavioral_event.assert_called()
        coordinador.archetype_service.get_personalized_response.assert_called()
    
    async def test_emotional_analysis_performance_impact(self, coordinador, mock_session, sample_emotional_profile):
        """Test that emotional analysis doesn't significantly impact response times"""
        user_id = 12345
        decision_id = 42
        
        # Mock profile
        mock_session.execute.return_value.scalar_one_or_none.return_value = sample_emotional_profile
        
        # Measure execution time
        start_time = time.time()
        result = await coordinador._flujo_tomar_decision(user_id, decision_id)
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Verify total response time is still reasonable
        assert execution_time_ms < 100, f"Total flow took {execution_time_ms}ms, too slow"
        assert result["success"] is True
        
        # Verify emotional analysis was performed within performance budget
        if result.get("emotional_analysis"):
            assert result["emotional_analysis"]["analysis_time_ms"] < 50
    
    async def test_decision_flow_with_error_handling(self, coordinador, mock_session):
        """Test that emotional analysis errors don't break existing flows"""
        user_id = 12345
        decision_id = 42
        
        # Mock database error for emotional analysis
        mock_session.execute.side_effect = Exception("Database connection error")
        
        # Execute flow - should still complete successfully despite emotional analysis error
        result = await coordinador._flujo_tomar_decision(user_id, decision_id)
        
        # Core functionality should still work
        assert result["success"] is True or "error" in result  # Either succeeds or fails gracefully
        
        # If emotional analysis failed, it shouldn't break the entire flow
        if result.get("emotional_analysis") is None:
            # Flow should still complete without emotional data
            assert result["action"] == "decision_success"
    
    async def test_decision_flow_backwards_compatibility(self, coordinador, mock_session, sample_emotional_profile):
        """Test that existing decision flow behavior is preserved"""
        user_id = 12345
        decision_id = 42
        
        # Mock profile
        mock_session.execute.return_value.scalar_one_or_none.return_value = sample_emotional_profile
        
        result = await coordinador._flujo_tomar_decision(user_id, decision_id)
        
        # Verify all existing fields are still present
        required_existing_fields = ["success", "message", "fragment", "action", "decision_type"]
        for field in required_existing_fields:
            assert field in result, f"Existing field '{field}' missing from result"
        
        # Verify existing behavior patterns
        assert result["action"] == "decision_success"
        assert isinstance(result["message"], str)
        assert isinstance(result["fragment"], dict)
        assert result["decision_type"] in [
            "quick_decision", "thoughtful_decision", "aesthetic_preference",
            "systematic_navigation", "detailed_exploration"
        ]
    
    async def test_multiple_user_concurrent_analysis(self, coordinador, mock_session, sample_emotional_profile):
        """Test concurrent emotional analysis for multiple users"""
        # Mock profile for all users
        mock_session.execute.return_value.scalar_one_or_none.return_value = sample_emotional_profile
        
        # Create concurrent decision flows for different users
        tasks = []
        for i in range(5):
            user_id = 10000 + i
            decision_id = 40 + i
            task = coordinador._flujo_tomar_decision(user_id, decision_id)
            tasks.append(task)
        
        # Execute all tasks concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time_ms = (time.time() - start_time) * 1000
        
        # Verify all flows succeeded
        for result in results:
            assert result["success"] is True
            assert "emotional_analysis" in result
            if result["emotional_analysis"]:
                assert result["emotional_analysis"]["analysis_time_ms"] < 50
        
        # Verify reasonable total time for concurrent processing
        assert total_time_ms < 300, f"Concurrent processing took {total_time_ms}ms, too slow"
    
    async def test_emotional_analysis_data_accuracy(self, coordinador, mock_session, sample_emotional_profile):
        """Test that emotional analysis produces accurate and consistent data"""
        user_id = 12345
        decision_id = 42
        
        # Mock profile
        mock_session.execute.return_value.scalar_one_or_none.return_value = sample_emotional_profile
        
        # Execute flow multiple times
        results = []
        for _ in range(3):
            result = await coordinador._flujo_tomar_decision(user_id, decision_id)
            results.append(result)
        
        # Verify emotional analysis data consistency
        for result in results:
            assert result["success"] is True
            emotional_data = result["emotional_analysis"]
            
            # Verify response_type is valid
            valid_response_types = [rt.value for rt in ResponseType]
            assert emotional_data["response_type"] in valid_response_types
            
            # Verify vulnerability_level is valid
            valid_vulnerability_levels = [vl.value for vl in VulnerabilityLevel]
            assert emotional_data["vulnerability_level"] in valid_vulnerability_levels
            
            # Verify analysis_time_ms is reasonable
            assert 0 <= emotional_data["analysis_time_ms"] <= 50
    
    async def test_emotional_profile_creation_and_updates(self, coordinador, mock_session):
        """Test that emotional profiles are created and updated correctly"""
        user_id = 99999  # New user without profile
        decision_id = 42
        
        # Mock no existing profile (will create new one)
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        # Execute flow
        result = await coordinador._flujo_tomar_decision(user_id, decision_id)
        
        # Verify flow succeeded
        assert result["success"] is True
        
        # Verify profile creation was attempted
        mock_session.add.assert_called()  # Should have added new profile
        mock_session.commit.assert_called()  # Should have committed changes
    
    async def test_emotional_insights_generation(self, coordinador, mock_session):
        """Test that emotional insights are generated appropriately"""
        user_id = 12345
        decision_id = 42
        
        # Create profile that should trigger insights (milestone user)
        milestone_profile = UserEmotionalProfile(
            user_id=user_id,
            total_interactions=50,  # Milestone number
            consistency_score=0.9,
            authenticity_score=0.85
        )
        
        mock_session.execute.return_value.scalar_one_or_none.return_value = milestone_profile
        
        result = await coordinador._flujo_tomar_decision(user_id, decision_id)
        
        # Verify flow succeeded
        assert result["success"] is True
        
        # Insights should be generated for milestone user
        # (This would be verified by checking database calls for insight creation)
        assert mock_session.add.called
        assert mock_session.commit.called

    # Error Handling Tests
    
    async def test_emotional_service_failure_graceful_degradation(self, coordinador, mock_session):
        """Test that emotional service failures don't break existing functionality"""
        user_id = 12345
        decision_id = 42
        
        # Mock emotional analysis service failure
        with patch.object(coordinador.emotional_analysis, 'analyze_interaction', side_effect=Exception("Analysis error")):
            result = await coordinador._flujo_tomar_decision(user_id, decision_id)
        
        # Core functionality should still work
        assert result["success"] is True
        assert "message" in result
        assert "fragment" in result
        
        # Emotional analysis should be None due to error
        assert result.get("emotional_analysis") is None
    
    async def test_partial_emotional_data_handling(self, coordinador, mock_session, sample_emotional_profile):
        """Test handling of partial emotional analysis results"""
        user_id = 12345
        decision_id = 42
        
        mock_session.execute.return_value.scalar_one_or_none.return_value = sample_emotional_profile
        
        # Mock partial emotional analysis result
        with patch.object(coordinador.emotional_analysis, 'analyze_interaction', return_value={
            "success": True,
            "response_type": "pausa_reflexiva",
            "analysis_time_ms": 25,
            # Missing some fields that would normally be present
        }):
            result = await coordinador._flujo_tomar_decision(user_id, decision_id)
        
        # Should handle partial data gracefully
        assert result["success"] is True
        assert result["emotional_analysis"]["response_type"] == "pausa_reflexiva"
        assert result["emotional_analysis"]["analysis_time_ms"] == 25

    # Performance and Load Tests
    
    async def test_emotional_analysis_memory_usage(self, coordinador, mock_session, sample_emotional_profile):
        """Test that emotional analysis doesn't cause memory leaks"""
        import psutil
        import os
        
        user_id = 12345
        decision_id = 42
        
        mock_session.execute.return_value.scalar_one_or_none.return_value = sample_emotional_profile
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Execute many analysis operations
        for _ in range(100):
            await coordinador._flujo_tomar_decision(user_id, decision_id)
        
        # Check final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 10MB for 100 operations)
        assert memory_increase < 10 * 1024 * 1024, f"Memory increased by {memory_increase} bytes"
    
    async def test_emotional_analysis_cache_effectiveness(self, coordinador, mock_session, sample_emotional_profile):
        """Test that emotional analysis caching works effectively"""
        user_id = 12345
        decision_id = 42
        
        mock_session.execute.return_value.scalar_one_or_none.return_value = sample_emotional_profile
        
        # First execution
        start_time = time.time()
        result1 = await coordinador._flujo_tomar_decision(user_id, decision_id)
        first_execution_time = time.time() - start_time
        
        # Second execution (should benefit from caching)
        start_time = time.time()
        result2 = await coordinador._flujo_tomar_decision(user_id, decision_id)
        second_execution_time = time.time() - start_time
        
        # Both should succeed
        assert result1["success"] is True
        assert result2["success"] is True
        
        # Second execution might be faster due to caching (though not guaranteed)
        # At minimum, both should be within performance limits
        assert first_execution_time < 0.1  # 100ms
        assert second_execution_time < 0.1  # 100ms

    # Data Integrity Tests
    
    async def test_emotional_data_consistency_across_flows(self, coordinador, mock_session, sample_emotional_profile):
        """Test that emotional data remains consistent across different flow types"""
        user_id = 12345
        
        mock_session.execute.return_value.scalar_one_or_none.return_value = sample_emotional_profile
        
        # Execute decision flow
        decision_result = await coordinador._flujo_tomar_decision(user_id, 42)
        
        # Mock other flow methods for comparison
        with patch.object(coordinador, '_flujo_reaccion_publicacion', return_value={
            "success": True,
            "action": "reaction_success",
            "message": "Test message"
        }) as mock_reaction:
            reaction_result = await coordinador.ejecutar_flujo(
                user_id, 
                AccionUsuario.REACCIONAR_PUBLICACION,
                message_id=123,
                channel_id=456,
                reaction_type="❤️"
            )
        
        # Verify both flows succeed
        assert decision_result["success"] is True
        assert reaction_result["success"] is True
        
        # Verify emotional analysis was integrated into decision flow
        assert "emotional_analysis" in decision_result
    
    async def test_database_transaction_integrity(self, coordinador, mock_session, sample_emotional_profile):
        """Test that database transactions maintain integrity with emotional analysis"""
        user_id = 12345
        decision_id = 42
        
        mock_session.execute.return_value.scalar_one_or_none.return_value = sample_emotional_profile
        
        # Execute flow
        result = await coordinador._flujo_tomar_decision(user_id, decision_id)
        
        # Verify all database operations were called in correct order
        assert mock_session.add.called  # Profile and interaction should be added
        assert mock_session.commit.called  # Changes should be committed
        assert mock_session.refresh.called  # Objects should be refreshed
        
        # Verify result is successful
        assert result["success"] is True


@pytest.mark.integration
class TestEmotionalAnalysisRealWorldScenarios:
    """Real-world scenario tests for emotional analysis integration"""
    
    async def test_new_user_onboarding_flow(self):
        """Test emotional analysis during new user onboarding"""
        # This would test the complete flow for a new user
        # making their first narrative decision
        pass
    
    async def test_experienced_user_complex_decision(self):
        """Test emotional analysis for users with rich emotional history"""
        # This would test how the system handles users with
        # extensive interaction history and complex emotional patterns
        pass
    
    async def test_vulnerable_moment_detection(self):
        """Test detection and handling of emotionally vulnerable moments"""
        # This would test the system's ability to detect when a user
        # is in a particularly vulnerable or sensitive emotional state
        pass
    
    async def test_emotional_breakthrough_recognition(self):
        """Test recognition of emotional breakthroughs and milestones"""
        # This would test the system's ability to recognize when a user
        # experiences a significant emotional breakthrough or milestone
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])