"""
Comprehensive test suite for EmotionalAnalysisService

Tests cover all core functionality including:
- Response timing classification
- Emotional metric calculation
- Profile management
- Integration performance
- Error handling
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

# Import the service and models
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.emotional_analysis_service import EmotionalAnalysisService
from database.emotional_models import (
    UserEmotionalProfile, EmotionalInteraction, ResponseType, 
    VulnerabilityLevel, EmotionalIntensity
)


class TestEmotionalAnalysisService:
    """Test suite for EmotionalAnalysisService core functionality"""
    
    @pytest.fixture
    async def mock_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.add = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session
    
    @pytest.fixture
    async def service(self, mock_session):
        """EmotionalAnalysisService instance with mocked session"""
        return EmotionalAnalysisService(mock_session)
    
    @pytest.fixture
    def sample_profile(self):
        """Sample user emotional profile"""
        return UserEmotionalProfile(
            user_id=12345,
            impulso_autentico_percentage=30.0,
            pausa_reflexiva_percentage=50.0,
            contemplacion_percentage=15.0,
            abandono_percentage=5.0,
            consistency_score=0.75,
            vulnerability_progression=0.6,
            authenticity_score=0.8,
            dominant_emotional_pattern=ResponseType.PAUSA_REFLEXIVA,
            current_vulnerability_level=VulnerabilityLevel.TENTATIVE,
            emotional_growth_trajectory=0.15,
            total_interactions=25,
            average_response_time=7.5
        )
    
    @pytest.fixture
    def sample_interaction_data(self):
        """Sample interaction data for testing"""
        return {
            "response_time": 8.5,
            "interaction_type": "decision",
            "content": "I choose to explore the mysterious garden path",
            "fragment_key": "level2_garden_choice",
            "context": {"decision_id": 42}
        }

    # Core Analysis Tests
    
    async def test_analyze_interaction_success(self, service, mock_session, sample_interaction_data):
        """Test successful interaction analysis"""
        user_id = 12345
        
        # Mock profile retrieval
        mock_profile = UserEmotionalProfile(user_id=user_id)
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_profile
        
        # Execute analysis
        result = await service.analyze_interaction(user_id, sample_interaction_data)
        
        # Verify results
        assert result["success"] is True
        assert result["response_type"] == ResponseType.PAUSA_REFLEXIVA.value
        assert result["analysis_time_ms"] < 50  # Performance requirement
        assert "emotional_metrics" in result
        assert "recommendations" in result
        
        # Verify database interactions
        mock_session.add.assert_called()
        mock_session.commit.assert_called()
    
    async def test_analyze_interaction_performance(self, service, mock_session, sample_interaction_data):
        """Test that analysis meets <50ms performance requirement"""
        user_id = 12345
        
        # Mock profile
        mock_profile = UserEmotionalProfile(user_id=user_id)
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_profile
        
        # Measure execution time
        start_time = time.time()
        result = await service.analyze_interaction(user_id, sample_interaction_data)
        execution_time_ms = (time.time() - start_time) * 1000
        
        # Verify performance requirement
        assert execution_time_ms < 50, f"Analysis took {execution_time_ms}ms, exceeds 50ms requirement"
        assert result["analysis_time_ms"] < 50
        
    async def test_invalid_interaction_data(self, service, mock_session):
        """Test handling of invalid interaction data"""
        user_id = 12345
        invalid_data = {"invalid": "data"}  # Missing required fields
        
        result = await service.analyze_interaction(user_id, invalid_data)
        
        assert result["success"] is False
        assert "Invalid interaction data" in result["error"]

    # Response Type Classification Tests
    
    def test_classify_response_timing_impulso_autentico(self, service):
        """Test classification of quick authentic responses"""
        response_type = service._classify_response_timing(2.5)
        assert response_type == ResponseType.IMPULSO_AUTENTICO
    
    def test_classify_response_timing_pausa_reflexiva(self, service):
        """Test classification of thoughtful responses"""
        response_type = service._classify_response_timing(8.0)
        assert response_type == ResponseType.PAUSA_REFLEXIVA
    
    def test_classify_response_timing_contemplacion(self, service):
        """Test classification of deep contemplation responses"""
        response_type = service._classify_response_timing(30.0)
        assert response_type == ResponseType.CONTEMPLACION
    
    def test_classify_response_timing_abandono(self, service):
        """Test classification of abandonment scenarios"""
        response_type = service._classify_response_timing(75.0)
        assert response_type == ResponseType.ABANDONO

    # Emotional Metrics Tests
    
    async def test_calculate_emotional_intensity(self, service, sample_profile):
        """Test emotional intensity calculation"""
        # Quick response should indicate high intensity
        intensity = service._calculate_emotional_intensity(1.5, "Intense content!", sample_profile)
        assert intensity == EmotionalIntensity.HIGH
        
        # Moderate response time
        intensity = service._calculate_emotional_intensity(4.0, "Moderate content", sample_profile)
        assert intensity == EmotionalIntensity.MODERATE
        
        # Slow response
        intensity = service._calculate_emotional_intensity(10.0, "Slow content", sample_profile)
        assert intensity == EmotionalIntensity.LOW
    
    async def test_assess_vulnerability_level(self, service, sample_profile):
        """Test vulnerability level assessment"""
        user_id = 12345
        
        # Test with profile's current level
        vulnerability = await service._assess_vulnerability_level(
            user_id, "test content", "decision", sample_profile
        )
        
        assert isinstance(vulnerability, VulnerabilityLevel)
        assert vulnerability == sample_profile.current_vulnerability_level
    
    async def test_calculate_authenticity_score(self, service, sample_profile, sample_interaction_data):
        """Test authenticity score calculation"""
        user_id = 12345
        
        score = await service._calculate_authenticity_score(
            user_id, sample_interaction_data, sample_profile
        )
        
        assert 0.0 <= score <= 1.0
        assert score >= sample_profile.authenticity_score  # Should not decrease
    
    def test_calculate_engagement_depth(self, service):
        """Test engagement depth calculation"""
        # Optimal response time should increase engagement
        depth = service._calculate_engagement_depth(7.0, "Detailed response content", "decision")
        assert depth > 0.5
        
        # Very quick response might indicate shallow engagement
        depth_quick = service._calculate_engagement_depth(1.0, "Quick", "decision")
        assert depth_quick < depth
        
        # Very long content should increase engagement
        depth_long = service._calculate_engagement_depth(
            7.0, 
            "This is a very long and detailed response that shows deep engagement",
            "decision"
        )
        assert depth_long > 0.5

    # Profile Management Tests
    
    async def test_get_or_create_profile_existing(self, service, mock_session, sample_profile):
        """Test retrieving existing profile"""
        user_id = 12345
        mock_session.execute.return_value.scalar_one_or_none.return_value = sample_profile
        
        result = await service._get_or_create_profile(user_id)
        
        assert result == sample_profile
        mock_session.add.assert_not_called()  # Should not create new profile
    
    async def test_get_or_create_profile_new(self, service, mock_session):
        """Test creating new profile"""
        user_id = 12345
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        result = await service._get_or_create_profile(user_id)
        
        assert result.user_id == user_id
        mock_session.add.assert_called()
        mock_session.commit.assert_called()
    
    async def test_update_profile_with_interaction(self, service, sample_profile):
        """Test profile updating with new interaction data"""
        # Create mock interaction
        interaction = EmotionalInteraction(
            user_id=12345,
            response_time=5.0,
            response_type=ResponseType.PAUSA_REFLEXIVA,
            emotional_intensity=EmotionalIntensity.MODERATE,
            vulnerability_exhibited=VulnerabilityLevel.GENUINE,
            engagement_depth=0.8
        )
        
        emotional_metrics = {
            "authenticity_score": 0.85,
            "vulnerability_level": VulnerabilityLevel.GENUINE.value,
            "engagement_depth": 0.8
        }
        
        initial_interactions = sample_profile.total_interactions
        
        await service._update_profile_with_interaction(
            sample_profile, interaction, emotional_metrics
        )
        
        # Verify updates
        assert sample_profile.total_interactions == initial_interactions + 1
        assert sample_profile.authenticity_score >= 0.8  # Should improve
        assert sample_profile.current_vulnerability_level == VulnerabilityLevel.GENUINE

    # User State Retrieval Tests
    
    async def test_get_user_emotional_state_success(self, service, mock_session, sample_profile):
        """Test successful emotional state retrieval"""
        user_id = 12345
        mock_session.execute.return_value.scalar_one_or_none.return_value = sample_profile
        
        # Mock recent interactions
        mock_interactions = [
            EmotionalInteraction(
                user_id=user_id, 
                response_type=ResponseType.PAUSA_REFLEXIVA,
                engagement_depth=0.7
            )
        ]
        
        with patch.object(service, '_get_recent_interactions', return_value=mock_interactions):
            with patch.object(service, '_calculate_emotional_trends', return_value={"trend": "positive"}):
                result = await service.get_user_emotional_state(user_id)
        
        assert result["success"] is True
        assert result["profile"]["dominant_pattern"] == ResponseType.PAUSA_REFLEXIVA.value
        assert result["profile"]["vulnerability_level"] == VulnerabilityLevel.TENTATIVE.value
        assert "trends" in result
    
    async def test_get_user_emotional_state_not_found(self, service, mock_session):
        """Test emotional state retrieval for non-existent user"""
        user_id = 99999
        mock_session.execute.return_value.scalar_one_or_none.return_value = None
        
        result = await service.get_user_emotional_state(user_id)
        
        assert result["success"] is False
        assert "Profile not found" in result["message"]

    # Engagement Prediction Tests
    
    async def test_predict_user_engagement_success(self, service, mock_session, sample_profile):
        """Test successful engagement prediction"""
        user_id = 12345
        mock_session.execute.return_value.scalar_one_or_none.return_value = sample_profile
        
        with patch.object(service, '_get_recent_evolution', return_value=[]):
            with patch.object(service, '_calculate_engagement_prediction', return_value=0.75):
                with patch.object(service, '_identify_engagement_risks', return_value=["low_risk"]):
                    with patch.object(service, '_generate_engagement_recommendations', return_value=["recommendation"]):
                        with patch.object(service, '_predict_optimal_interaction_time', return_value="2_hours"):
                            result = await service.predict_user_engagement(user_id)
        
        assert result["success"] is True
        assert result["engagement_prediction"]["score"] == 0.75
        assert result["engagement_prediction"]["level"] == "high"  # 0.75 should be classified as high
        assert "risk_factors" in result
        assert "recommendations" in result
    
    async def test_calculate_engagement_prediction(self, service, sample_profile):
        """Test engagement prediction calculation"""
        evolution_data = []  # Empty for simplicity
        
        score = await service._calculate_engagement_prediction(sample_profile, evolution_data)
        
        assert 0.0 <= score <= 1.0
        # High authenticity and consistency should result in good engagement
        assert score > 0.5
    
    def test_classify_engagement_level(self, service):
        """Test engagement level classification"""
        assert service._classify_engagement_level(0.9) == "very_high"
        assert service._classify_engagement_level(0.7) == "high"
        assert service._classify_engagement_level(0.5) == "moderate"
        assert service._classify_engagement_level(0.3) == "low"
        assert service._classify_engagement_level(0.1) == "very_low"
    
    async def test_identify_engagement_risks(self, service, sample_profile):
        """Test engagement risk identification"""
        user_id = 12345
        evolution_data = []
        
        # Test with high abandonment rate
        sample_profile.abandono_percentage = 30.0
        risks = await service._identify_engagement_risks(user_id, sample_profile, evolution_data)
        assert "high_abandonment_rate" in risks
        
        # Test with low consistency
        sample_profile.consistency_score = 0.2
        risks = await service._identify_engagement_risks(user_id, sample_profile, evolution_data)
        assert "low_behavioral_consistency" in risks
    
    async def test_generate_engagement_recommendations(self, service, sample_profile):
        """Test engagement recommendation generation"""
        risk_factors = ["high_abandonment_rate"]
        engagement_score = 0.3
        
        recommendations = await service._generate_engagement_recommendations(
            sample_profile, engagement_score, risk_factors
        )
        
        assert len(recommendations) > 0
        assert any("content complexity" in rec for rec in recommendations)

    # Error Handling Tests
    
    async def test_analyze_interaction_database_error(self, service, mock_session, sample_interaction_data):
        """Test handling of database errors during analysis"""
        user_id = 12345
        
        # Mock database error
        mock_session.execute.side_effect = Exception("Database connection error")
        
        result = await service.analyze_interaction(user_id, sample_interaction_data)
        
        assert result["success"] is False
        assert "error" in result
    
    async def test_get_emotional_state_database_error(self, service, mock_session):
        """Test handling of database errors during state retrieval"""
        user_id = 12345
        
        # Mock database error
        mock_session.execute.side_effect = Exception("Database error")
        
        result = await service.get_user_emotional_state(user_id)
        
        assert result["success"] is False
        assert "Database error" in result["message"]

    # Trend Calculation Tests
    
    def test_calculate_engagement_trend_improving(self, service):
        """Test engagement trend calculation - improving case"""
        interactions = [
            # Recent interactions (higher engagement)
            EmotionalInteraction(engagement_depth=0.8),
            EmotionalInteraction(engagement_depth=0.9),
            EmotionalInteraction(engagement_depth=0.85),
            # Older interactions (lower engagement)
            EmotionalInteraction(engagement_depth=0.6),
            EmotionalInteraction(engagement_depth=0.5),
            EmotionalInteraction(engagement_depth=0.55)
        ]
        
        trend = service._calculate_engagement_trend(interactions)
        assert trend == "improving"
    
    def test_calculate_engagement_trend_declining(self, service):
        """Test engagement trend calculation - declining case"""
        interactions = [
            # Recent interactions (lower engagement)
            EmotionalInteraction(engagement_depth=0.4),
            EmotionalInteraction(engagement_depth=0.3),
            EmotionalInteraction(engagement_depth=0.35),
            # Older interactions (higher engagement)
            EmotionalInteraction(engagement_depth=0.8),
            EmotionalInteraction(engagement_depth=0.9),
            EmotionalInteraction(engagement_depth=0.85)
        ]
        
        trend = service._calculate_engagement_trend(interactions)
        assert trend == "declining"
    
    def test_calculate_engagement_trend_stable(self, service):
        """Test engagement trend calculation - stable case"""
        interactions = [
            EmotionalInteraction(engagement_depth=0.6),
            EmotionalInteraction(engagement_depth=0.65),
            EmotionalInteraction(engagement_depth=0.55),
            EmotionalInteraction(engagement_depth=0.6),
            EmotionalInteraction(engagement_depth=0.58),
            EmotionalInteraction(engagement_depth=0.62)
        ]
        
        trend = service._calculate_engagement_trend(interactions)
        assert trend == "stable"
    
    def test_calculate_engagement_trend_insufficient_data(self, service):
        """Test engagement trend with insufficient data"""
        interactions = [EmotionalInteraction(engagement_depth=0.5)]
        
        trend = service._calculate_engagement_trend(interactions)
        assert trend == "insufficient_data"
    
    def test_determine_overall_trend(self, service):
        """Test overall trend determination from individual metrics"""
        positive_trends = ["improving", "improving", "stable"]
        overall = service._determine_overall_trend(positive_trends)
        assert overall == "positive"
        
        negative_trends = ["declining", "declining", "stable"]
        overall = service._determine_overall_trend(negative_trends)
        assert overall == "negative"
        
        neutral_trends = ["stable", "stable", "stable"]
        overall = service._determine_overall_trend(neutral_trends)
        assert overall == "stable"

    # Recommendation Tests
    
    def test_generate_immediate_recommendations_surface_vulnerability(self, service, sample_profile):
        """Test recommendations for surface-level vulnerability"""
        emotional_metrics = {"vulnerability_level": VulnerabilityLevel.SURFACE.value}
        triggers = []
        
        recommendations = service._generate_immediate_recommendations(
            emotional_metrics, sample_profile, triggers
        )
        
        assert any("deeper narrative content" in rec for rec in recommendations)
    
    def test_generate_immediate_recommendations_high_abandonment(self, service, sample_profile):
        """Test recommendations for high abandonment rate"""
        sample_profile.abandono_percentage = 25.0
        emotional_metrics = {"vulnerability_level": VulnerabilityLevel.TENTATIVE.value}
        triggers = []
        
        recommendations = service._generate_immediate_recommendations(
            emotional_metrics, sample_profile, triggers
        )
        
        assert any("shorter" in rec and "engaging" in rec for rec in recommendations)
    
    def test_generate_immediate_recommendations_high_impulso(self, service, sample_profile):
        """Test recommendations for high impulso auténtico percentage"""
        sample_profile.impulso_autentico_percentage = 75.0
        emotional_metrics = {"vulnerability_level": VulnerabilityLevel.TENTATIVE.value}
        triggers = []
        
        recommendations = service._generate_immediate_recommendations(
            emotional_metrics, sample_profile, triggers
        )
        
        assert any("quick interactions" in rec for rec in recommendations)

    # Utility Function Tests
    
    def test_create_error_response(self, service):
        """Test error response creation"""
        error_message = "Test error"
        
        response = service._create_error_response(error_message)
        
        assert response["success"] is False
        assert response["error"] == error_message
        assert "analysis_time_ms" in response
    
    def test_calculate_prediction_confidence(self, service, sample_profile):
        """Test prediction confidence calculation"""
        confidence = service._calculate_prediction_confidence(sample_profile)
        
        assert 0.0 <= confidence <= 1.0
        # Profile with good stats should have reasonable confidence
        assert confidence > 0.5


@pytest.mark.integration
class TestEmotionalAnalysisIntegration:
    """Integration tests for EmotionalAnalysisService with real database interactions"""
    
    @pytest.fixture
    async def real_session(self):
        """Real database session for integration tests"""
        # This would be configured with a test database
        # For now, we'll use mock but structure for real implementation
        session = AsyncMock(spec=AsyncSession)
        return session
    
    async def test_full_analysis_workflow(self, real_session):
        """Test complete analysis workflow from start to finish"""
        service = EmotionalAnalysisService(real_session)
        user_id = 12345
        
        interaction_data = {
            "response_time": 6.5,
            "interaction_type": "decision",
            "content": "I want to explore the mysterious garden with Diana",
            "fragment_key": "level2_garden_entrance",
            "context": {"decision_id": 15}
        }
        
        # Mock successful database operations
        mock_profile = UserEmotionalProfile(user_id=user_id)
        real_session.execute.return_value.scalar_one_or_none.return_value = mock_profile
        
        # Execute full workflow
        result = await service.analyze_interaction(user_id, interaction_data)
        
        # Verify complete workflow
        assert result["success"] is True
        assert result["response_type"] == ResponseType.PAUSA_REFLEXIVA.value
        assert result["analysis_time_ms"] < 50
        assert "emotional_metrics" in result
        assert "recommendations" in result
        
        # Verify database interactions occurred
        assert real_session.add.called
        assert real_session.commit.called
    
    async def test_concurrent_analysis_performance(self, real_session):
        """Test performance with concurrent analysis requests"""
        service = EmotionalAnalysisService(real_session)
        
        # Mock profile for all users
        real_session.execute.return_value.scalar_one_or_none.return_value = UserEmotionalProfile()
        
        # Create multiple concurrent analysis tasks
        tasks = []
        for i in range(10):
            interaction_data = {
                "response_time": 5.0 + i * 0.5,
                "interaction_type": "decision",
                "content": f"Test content {i}",
                "fragment_key": f"test_fragment_{i}",
                "context": {"decision_id": i}
            }
            task = service.analyze_interaction(10000 + i, interaction_data)
            tasks.append(task)
        
        # Execute all tasks concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000
        
        # Verify all succeeded and performance is reasonable
        for result in results:
            assert result["success"] is True
            assert result["analysis_time_ms"] < 50
        
        # Total time should be reasonable for concurrent processing
        assert total_time < 500  # 10 concurrent 50ms operations shouldn't take more than 500ms


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])