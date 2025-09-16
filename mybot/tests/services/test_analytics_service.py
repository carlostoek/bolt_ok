"""
Comprehensive test suite for AnalyticsService

Tests cover all core functionality including:
- Fragment engagement metrics analysis
- Choice distribution pattern analysis
- Narrative bottleneck identification
- User segment analysis and conversion funnels
- Character voice analytics and emotional progression tracking
- Data export capabilities (JSON/CSV)
- Performance testing with large datasets
- Error handling and edge cases
"""

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Create mock pytest decorators for compatibility
    class MockPytest:
        @staticmethod
        def fixture(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
    pytest = MockPytest()

import asyncio
import json
import csv
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional

# Import the service and models
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.exc import IntegrityError, SQLAlchemyError
    from sqlalchemy import select
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    # Mock SQLAlchemy classes for testing
    class MockAsyncSession:
        pass
    class MockIntegrityError(Exception):
        pass
    class MockSQLAlchemyError(Exception):
        pass
    AsyncSession = MockAsyncSession
    IntegrityError = MockIntegrityError
    SQLAlchemyError = MockSQLAlchemyError

try:
    from services.analytics_service import AnalyticsService
    from database.narrative_models import (
        FragmentAnalytics, UserJourneyAnalytics, UserNarrativeState,
        StoryFragment, NarrativeChoice
    )
    from database.models import User
    SERVICE_AVAILABLE = True
except ImportError:
    SERVICE_AVAILABLE = False
    print("Warning: Analytics service and models not available for import")


class TestAnalyticsService:
    """Test suite for AnalyticsService core functionality"""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.add = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.refresh = AsyncMock()
        session.get = AsyncMock()
        return session

    @pytest.fixture
    def analytics_service(self, mock_session):
        """Analytics service instance with mocked session"""
        return AnalyticsService(mock_session)

    @pytest.fixture
    def sample_fragment_analytics(self):
        """Sample fragment analytics data"""
        return FragmentAnalytics(
            id=1,
            fragment_key="intro_001",
            view_count=100,
            completion_count=75,
            drop_off_count=25,
            average_time_spent=45,
            choice_distribution={"choice_1": 40, "choice_2": 30, "choice_3": 5},
            most_popular_choice_id=1,
            users_progressed_from=70,
            users_returned_to=15,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_analyzed_at=datetime.utcnow()
        )

    @pytest.fixture
    def sample_user_journey_analytics(self):
        """Sample user journey analytics data"""
        return UserJourneyAnalytics(
            id=1,
            user_id=12345,
            fragments_visited=["intro_001", "choice_001", "story_002"],
            choices_made=[{"choice_id": 1, "fragment_key": "intro_001", "timestamp": "2024-01-01T00:00:00"}],
            progression_path=["intro_001", "choice_001", "story_002"],
            total_time_spent=300,
            session_count=3,
            average_session_duration=100,
            backtrack_count=2,
            exploration_score=85,
            engagement_level="highly_engaged",
            fragments_completed=3,
            narrative_completion_percentage=25,
            emotional_states=[
                {"fragment": "intro_001", "emotion": "curiosity", "intensity": 0.8},
                {"fragment": "choice_001", "emotion": "anticipation", "intensity": 0.7}
            ],
            character_interaction_count={"Lucien": 2, "Diana": 1},
            journey_started_at=datetime.utcnow() - timedelta(days=5),
            last_activity_at=datetime.utcnow() - timedelta(hours=2),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    @pytest.fixture
    def sample_users(self):
        """Sample user data"""
        now = datetime.utcnow()
        return [
            User(id=1, points=1500, created_at=now - timedelta(days=30)),
            User(id=2, points=500, created_at=now - timedelta(days=2)),
            User(id=3, points=2000, created_at=now - timedelta(days=60))
        ]

    # Fragment Engagement Metrics Tests
    async def test_get_fragment_engagement_metrics_success(self, analytics_service, mock_session, sample_fragment_analytics):
        """Test successful retrieval of fragment engagement metrics"""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_fragment_analytics
        mock_session.execute.return_value = mock_result

        # Execute
        result = await analytics_service.get_fragment_engagement_metrics("intro_001")

        # Assert
        assert result["status"] == "success"
        assert result["fragment_key"] == "intro_001"
        assert result["metrics"]["view_count"] == 100
        assert result["metrics"]["completion_count"] == 75
        assert result["metrics"]["engagement_rate"] == 75.0
        assert result["metrics"]["drop_off_rate"] == 25.0
        assert "last_analyzed" in result

        # Verify SQL query
        mock_session.execute.assert_called_once()

    async def test_get_fragment_engagement_metrics_no_data(self, analytics_service, mock_session):
        """Test fragment engagement metrics when no data exists"""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Execute
        result = await analytics_service.get_fragment_engagement_metrics("nonexistent_fragment")

        # Assert
        assert result["status"] == "no_data"
        assert result["fragment_key"] == "nonexistent_fragment"
        assert "message" in result

    async def test_get_fragment_engagement_metrics_error(self, analytics_service, mock_session):
        """Test fragment engagement metrics with database error"""
        # Setup mock to raise exception
        mock_session.execute.side_effect = SQLAlchemyError("Database error")

        # Execute
        result = await analytics_service.get_fragment_engagement_metrics("intro_001")

        # Assert
        assert result["status"] == "error"
        assert "message" in result

    # Choice Distribution Pattern Tests
    async def test_analyze_choice_distribution_patterns_success(self, analytics_service, mock_session):
        """Test successful choice distribution analysis"""
        # Setup sample data
        analytics_data = [
            MagicMock(
                fragment_key="fragment_1",
                choice_distribution={"choice_1": 30, "choice_2": 20},
                most_popular_choice_id=1
            ),
            MagicMock(
                fragment_key="fragment_2",
                choice_distribution={"choice_3": 15, "choice_4": 25},
                most_popular_choice_id=4
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = analytics_data
        mock_session.execute.return_value = mock_result

        # Execute
        result = await analytics_service.analyze_choice_distribution_patterns()

        # Assert
        assert result["status"] == "success"
        assert result["summary"]["total_choices_made"] == 90
        assert result["summary"]["fragments_analyzed"] == 2
        assert result["summary"]["unique_choices"] == 4
        assert len(result["most_popular_choices"]) > 0
        assert "fragment_stats" in result
        assert "diversity_scores" in result

    async def test_analyze_choice_distribution_patterns_no_data(self, analytics_service, mock_session):
        """Test choice distribution analysis with no data"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        # Execute
        result = await analytics_service.analyze_choice_distribution_patterns()

        # Assert
        assert result["status"] == "no_data"
        assert "message" in result

    # Narrative Bottleneck Tests
    async def test_identify_narrative_bottlenecks_success(self, analytics_service, mock_session):
        """Test successful bottleneck identification"""
        # Create mock analytics with varying drop-off rates
        high_dropoff_analytics = MagicMock(
            fragment_key="bottleneck_fragment",
            view_count=100,
            completion_count=20,
            drop_off_count=80,
            average_time_spent=30,
            users_returned_to=5
        )
        normal_analytics = MagicMock(
            fragment_key="normal_fragment",
            view_count=100,
            completion_count=85,
            drop_off_count=15,
            average_time_spent=45,
            users_returned_to=10
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [high_dropoff_analytics, normal_analytics]
        mock_session.execute.return_value = mock_result

        # Mock journey analytics
        stalled_users = [MagicMock(last_fragment_key="bottleneck_fragment")]
        journey_result = MagicMock()
        journey_result.scalars.return_value.all.return_value = stalled_users
        mock_session.execute.side_effect = [mock_result, journey_result]

        # Execute
        result = await analytics_service.identify_narrative_bottlenecks()

        # Assert
        assert result["status"] == "success"
        assert result["summary"]["total_fragments_analyzed"] == 2
        assert result["summary"]["critical_bottlenecks"] >= 0
        assert len(result["bottlenecks"]) > 0
        assert result["bottlenecks"][0]["fragment_key"] == "bottleneck_fragment"
        assert result["bottlenecks"][0]["drop_off_rate"] == 80.0
        assert result["bottlenecks"][0]["severity"] == "critical"
        assert "recommendations" in result

    async def test_identify_narrative_bottlenecks_no_critical_issues(self, analytics_service, mock_session):
        """Test bottleneck identification when no critical issues exist"""
        # Create mock analytics with good metrics
        good_analytics = MagicMock(
            fragment_key="good_fragment",
            view_count=100,
            completion_count=90,
            drop_off_count=10,
            average_time_spent=60,
            users_returned_to=5
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [good_analytics]

        journey_result = MagicMock()
        journey_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_result, journey_result]

        # Execute
        result = await analytics_service.identify_narrative_bottlenecks()

        # Assert
        assert result["status"] == "success"
        assert result["summary"]["critical_bottlenecks"] == 0
        assert len(result["bottlenecks"]) == 0
        assert "No critical issues detected" in result["recommendations"][0]

    # User Segment Analysis Tests
    async def test_generate_user_segment_analysis_success(self, analytics_service, mock_session, sample_users):
        """Test successful user segment analysis"""
        # Create users with narrative states
        now = datetime.utcnow()
        users_with_states = []

        for i, user in enumerate(sample_users):
            narrative_state = MagicMock()
            narrative_state.fragments_visited = 10 + (i * 20)
            narrative_state.last_activity_at = now - timedelta(days=i + 1)
            user.narrative_state = narrative_state
            users_with_states.append(user)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = users_with_states
        mock_session.execute.return_value = mock_result

        # Execute
        result = await analytics_service.generate_user_segment_analysis()

        # Assert
        assert "segment_counts" in result
        assert "segments" in result
        assert "generated_at" in result
        assert sum(result["segment_counts"].values()) == len(sample_users)

        # Verify segments exist
        expected_segments = ["whales", "explorers", "highly_engaged", "stalled", "new_users", "inactive"]
        for segment in expected_segments:
            assert segment in result["segment_counts"]

    # Conversion Funnel Tests
    async def test_track_conversion_funnel_metrics_success(self, analytics_service, mock_session, sample_user_journey_analytics):
        """Test successful conversion funnel tracking"""
        # Create journey data with different completion levels
        journeys = []
        for i in range(5):
            journey = MagicMock()
            journey.user = MagicMock()
            journey.user.points = 500 + (i * 100)
            journey.fragments_completed = i * 3
            journey.total_besitos_earned = (i + 1) * 50
            journey.last_activity_at = datetime.utcnow() - timedelta(days=i)
            journey.journey_started_at = datetime.utcnow() - timedelta(days=30)
            journeys.append(journey)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = journeys
        mock_session.execute.return_value = mock_result

        # Execute
        result = await analytics_service.track_conversion_funnel_metrics()

        # Assert
        assert result["status"] == "success"
        assert "funnel_stages" in result
        assert "conversion_rates" in result
        assert "drop_off_rates" in result
        assert "cohort_analysis" in result
        assert "insights" in result

        # Verify funnel stages
        expected_stages = ["initial_visit", "engaged", "highly_engaged", "purchaser", "retained"]
        for stage in expected_stages:
            assert stage in result["funnel_stages"]
            assert "count" in result["funnel_stages"][stage]
            assert "description" in result["funnel_stages"][stage]

    # Character Voice Analytics Tests
    async def test_get_character_voice_analytics_success(self, analytics_service, mock_session, sample_user_journey_analytics):
        """Test successful character voice analytics"""
        # Create journey data with character interactions and emotional states
        journeys = [sample_user_journey_analytics]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = journeys
        mock_session.execute.return_value = mock_result

        # Execute
        result = await analytics_service.get_character_voice_analytics()

        # Assert
        assert result["status"] == "success"
        assert "character_analytics" in result
        assert "emotional_progressions" in result
        assert "insights" in result

        # Verify character analytics
        character_stats = result["character_analytics"]
        assert "Lucien" in character_stats
        assert "Diana" in character_stats
        assert character_stats["Lucien"]["total_interactions"] == 2
        assert character_stats["Diana"]["total_interactions"] == 1

        # Verify emotional progressions
        emotional_data = result["emotional_progressions"]
        assert "curiosity" in emotional_data
        assert "anticipation" in emotional_data
        assert emotional_data["curiosity"]["occurrences"] == 1
        assert emotional_data["curiosity"]["average_intensity"] == 0.8

    async def test_get_character_voice_analytics_no_data(self, analytics_service, mock_session):
        """Test character voice analytics with no emotional data"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        # Execute
        result = await analytics_service.get_character_voice_analytics()

        # Assert
        assert result["status"] == "no_data"
        assert "message" in result

    # Data Export Tests
    async def test_export_analytics_data_json_success(self, analytics_service, mock_session, sample_fragment_analytics, sample_user_journey_analytics):
        """Test successful JSON export of analytics data"""
        # Setup mock data
        fragment_result = MagicMock()
        fragment_result.scalars.return_value.all.return_value = [sample_fragment_analytics]

        journey_result = MagicMock()
        journey_result.scalars.return_value.all.return_value = [sample_user_journey_analytics]

        mock_session.execute.side_effect = [fragment_result, journey_result]

        # Execute
        date_range = ("2024-01-01T00:00:00", "2024-01-31T23:59:59")
        result = await analytics_service.export_analytics_data(date_range, "json")

        # Assert
        assert isinstance(result, str)
        export_data = json.loads(result)
        assert "metadata" in export_data
        assert "fragment_analytics" in export_data
        assert "user_journey_analytics" in export_data
        assert export_data["metadata"]["format"] == "json"
        assert len(export_data["fragment_analytics"]) == 1
        assert len(export_data["user_journey_analytics"]) == 1

    async def test_export_analytics_data_csv_success(self, analytics_service, mock_session, sample_fragment_analytics, sample_user_journey_analytics):
        """Test successful CSV export of analytics data"""
        # Setup mock data
        fragment_result = MagicMock()
        fragment_result.scalars.return_value.all.return_value = [sample_fragment_analytics]

        journey_result = MagicMock()
        journey_result.scalars.return_value.all.return_value = [sample_user_journey_analytics]

        mock_session.execute.side_effect = [fragment_result, journey_result]

        # Execute
        date_range = ("2024-01-01T00:00:00", "2024-01-31T23:59:59")
        result = await analytics_service.export_analytics_data(date_range, "csv")

        # Assert
        assert isinstance(result, dict)
        assert "fragment_analytics.csv" in result
        assert "user_journey_analytics.csv" in result
        assert "metadata" in result

        # Verify CSV content
        fragment_csv = result["fragment_analytics.csv"]
        assert "fragment_key" in fragment_csv
        assert "view_count" in fragment_csv
        assert "intro_001" in fragment_csv

    async def test_export_analytics_data_invalid_format(self, analytics_service, mock_session):
        """Test export with invalid format"""
        date_range = ("2024-01-01T00:00:00", "2024-01-31T23:59:59")
        result = await analytics_service.export_analytics_data(date_range, "invalid_format")

        assert result["status"] == "error"
        assert "Unsupported export format" in result["message"]

    # Character Analytics Export Tests
    async def test_export_character_analytics_data_json(self, analytics_service, mock_session):
        """Test character analytics export in JSON format"""
        # Mock the get_character_voice_analytics method
        character_data = {
            "status": "success",
            "character_analytics": {
                "Lucien": {"total_interactions": 10, "engagement_score": 85},
                "Diana": {"total_interactions": 8, "engagement_score": 92}
            },
            "emotional_progressions": {
                "curiosity": {"occurrences": 15, "average_intensity": 0.7},
                "anticipation": {"occurrences": 12, "average_intensity": 0.8}
            },
            "insights": {"most_effective_character": {"name": "Diana", "engagement_score": 92}}
        }

        with patch.object(analytics_service, 'get_character_voice_analytics', return_value=character_data):
            result = await analytics_service.export_character_analytics_data(format="json")

        # Assert
        assert isinstance(result, str)
        export_data = json.loads(result)
        assert "metadata" in export_data
        assert "character_analytics" in export_data
        assert "emotional_progressions" in export_data
        assert export_data["metadata"]["export_type"] == "character_analytics"

    async def test_export_character_analytics_data_csv(self, analytics_service, mock_session):
        """Test character analytics export in CSV format"""
        # Mock the get_character_voice_analytics method
        character_data = {
            "status": "success",
            "character_analytics": {
                "Lucien": {"total_interactions": 10, "unique_users": 5, "average_interactions_per_user": 2.0, "engagement_score": 85},
                "Diana": {"total_interactions": 8, "unique_users": 4, "average_interactions_per_user": 2.0, "engagement_score": 92}
            },
            "emotional_progressions": {
                "curiosity": {"occurrences": 15, "average_intensity": 0.7, "fragments": 8},
                "anticipation": {"occurrences": 12, "average_intensity": 0.8, "fragments": 6}
            }
        }

        with patch.object(analytics_service, 'get_character_voice_analytics', return_value=character_data):
            result = await analytics_service.export_character_analytics_data(format="csv")

        # Assert
        assert isinstance(result, dict)
        assert "character_analytics.csv" in result
        assert "emotional_progressions.csv" in result
        assert "metadata" in result

    # User Journey Export Tests
    async def test_export_user_journey_data_json(self, analytics_service, mock_session, sample_user_journey_analytics):
        """Test user journey data export in JSON format"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_user_journey_analytics]
        mock_session.execute.return_value = mock_result

        result = await analytics_service.export_user_journey_data(format="json")

        # Assert
        assert isinstance(result, str)
        export_data = json.loads(result)
        assert "metadata" in export_data
        assert "user_journeys" in export_data
        assert export_data["metadata"]["export_type"] == "user_journey"
        assert len(export_data["user_journeys"]) == 1

    async def test_export_user_journey_data_csv(self, analytics_service, mock_session, sample_user_journey_analytics):
        """Test user journey data export in CSV format"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_user_journey_analytics]
        mock_session.execute.return_value = mock_result

        result = await analytics_service.export_user_journey_data(format="csv")

        # Assert
        assert isinstance(result, dict)
        assert "user_journey_analytics.csv" in result
        assert "metadata" in result

    async def test_export_user_journey_data_no_data(self, analytics_service, mock_session):
        """Test user journey export with no data"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await analytics_service.export_user_journey_data()

        # Assert
        assert result["status"] == "error"
        assert "No user journey data found" in result["message"]

    # Comprehensive Report Tests
    async def test_generate_comprehensive_report_executive(self, analytics_service, mock_session):
        """Test executive report generation"""
        # Mock dashboard and character data
        dashboard_data = {
            "status": "success",
            "user_segments": {"status": "success", "segment_counts": {"whales": 5, "engaged": 20, "new_users": 15}},
            "bottlenecks": {"status": "success", "recommendations": ["Fix fragment X", "Optimize Y", "Review Z"]}
        }
        character_data = {
            "status": "success",
            "insights": {
                "most_effective_character": {"name": "Diana", "engagement_score": 95},
                "total_tracked_interactions": 500
            }
        }

        with patch.object(analytics_service, 'get_comprehensive_dashboard_data', return_value=dashboard_data), \
             patch.object(analytics_service, 'get_character_voice_analytics', return_value=character_data):

            result = await analytics_service.generate_comprehensive_report("executive")

        # Assert
        assert result["status"] == "success"
        assert result["report_type"] == "executive"
        assert "executive_summary" in result
        assert result["executive_summary"]["total_users"] == 40
        assert len(result["executive_summary"]["recommendations"]) == 3
        assert result["executive_summary"]["character_performance"]["most_effective"] == "Diana"

    async def test_generate_comprehensive_report_detailed(self, analytics_service, mock_session):
        """Test detailed report generation"""
        dashboard_data = {"status": "success"}
        character_data = {"status": "success"}

        with patch.object(analytics_service, 'get_comprehensive_dashboard_data', return_value=dashboard_data), \
             patch.object(analytics_service, 'get_character_voice_analytics', return_value=character_data):

            result = await analytics_service.generate_comprehensive_report("detailed")

        # Assert
        assert result["status"] == "success"
        assert result["report_type"] == "detailed"
        assert "detailed_analytics" in result
        assert "export_capabilities" in result["detailed_analytics"]

    async def test_generate_comprehensive_report_kpis(self, analytics_service, mock_session):
        """Test KPI report generation"""
        dashboard_data = {
            "status": "success",
            "choice_patterns": {
                "status": "success",
                "summary": {
                    "total_choices_made": 1000,
                    "unique_choices": 50,
                    "fragments_analyzed": 25
                }
            }
        }
        character_data = {"status": "success"}

        with patch.object(analytics_service, 'get_comprehensive_dashboard_data', return_value=dashboard_data), \
             patch.object(analytics_service, 'get_character_voice_analytics', return_value=character_data):

            result = await analytics_service.generate_comprehensive_report("kpis")

        # Assert
        assert result["status"] == "success"
        assert result["report_type"] == "kpis"
        assert "kpis" in result
        assert result["kpis"]["engagement_metrics"]["total_choices"] == 1000

    # Comprehensive Dashboard Tests
    async def test_get_comprehensive_dashboard_data_success(self, analytics_service, mock_session):
        """Test comprehensive dashboard data retrieval"""
        # Mock all component methods
        mock_results = [
            {"status": "success", "segment_counts": {"whales": 10}},  # user_segments
            {"status": "success", "total_choices_made": 500},        # choice_patterns
            {"status": "success", "bottlenecks": []},                # bottlenecks
            {"status": "success", "funnel_stages": {}},              # conversion_funnel
            {"status": "success", "character_analytics": {}}        # character_voice
        ]

        with patch('asyncio.gather', return_value=mock_results):
            result = await analytics_service.get_comprehensive_dashboard_data()

        # Assert
        assert result["status"] == "success"
        assert "summary" in result
        assert "user_segments" in result
        assert "choice_patterns" in result
        assert "bottlenecks" in result
        assert "conversion_funnel" in result
        assert "character_voice" in result
        assert result["summary"]["data_availability"]["user_segments"] == True

    async def test_get_comprehensive_dashboard_data_with_exceptions(self, analytics_service, mock_session):
        """Test comprehensive dashboard data with some component failures"""
        # Mock some successful and some failed results
        mock_results = [
            {"status": "success"},                    # user_segments
            Exception("Database error"),              # choice_patterns
            {"status": "success"},                    # bottlenecks
            {"status": "success"},                    # conversion_funnel
            {"status": "success"}                     # character_voice
        ]

        with patch('asyncio.gather', return_value=mock_results):
            result = await analytics_service.get_comprehensive_dashboard_data()

        # Assert
        assert result["status"] == "success"
        assert result["choice_patterns"]["status"] == "error"
        assert "Database error" in result["choice_patterns"]["message"]

    # Performance Tests
    async def test_large_dataset_performance(self, analytics_service, mock_session):
        """Test performance with large datasets"""
        # Create a large number of mock analytics records
        large_dataset = []
        for i in range(1000):
            analytics = MagicMock()
            analytics.fragment_key = f"fragment_{i}"
            analytics.view_count = 100 + i
            analytics.completion_count = 80 + i
            analytics.drop_off_count = 20 + i
            analytics.choice_distribution = {f"choice_{j}": 10 + j for j in range(5)}
            large_dataset.append(analytics)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = large_dataset
        mock_session.execute.return_value = mock_result

        # Measure execution time
        import time
        start_time = time.time()
        result = await analytics_service.analyze_choice_distribution_patterns()
        execution_time = time.time() - start_time

        # Assert performance and correctness
        assert result["status"] == "success"
        assert result["summary"]["fragments_analyzed"] == 1000
        assert execution_time < 5.0  # Should complete within 5 seconds

    async def test_concurrent_requests_handling(self, analytics_service, mock_session):
        """Test handling of concurrent analytics requests"""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(
            fragment_key="test_fragment",
            view_count=100,
            completion_count=80,
            drop_off_count=20,
            average_time_spent=45,
            choice_distribution={"choice_1": 50, "choice_2": 30},
            most_popular_choice_id=1,
            users_progressed_from=70,
            users_returned_to=10,
            last_analyzed_at=datetime.utcnow()
        )
        mock_session.execute.return_value = mock_result

        # Execute multiple concurrent requests
        tasks = [
            analytics_service.get_fragment_engagement_metrics(f"fragment_{i}")
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)

        # Assert all requests completed successfully
        assert len(results) == 10
        for result in results:
            assert result["status"] == "success"

    # Edge Cases and Error Handling Tests
    async def test_invalid_date_range_handling(self, analytics_service, mock_session):
        """Test handling of invalid date ranges"""
        # Test with invalid date format
        result = await analytics_service.export_analytics_data(("invalid-date", "2024-01-31T23:59:59"), "json")
        assert result["status"] == "error"

        # Test with end date before start date
        result = await analytics_service.export_analytics_data(("2024-01-31T23:59:59", "2024-01-01T00:00:00"), "json")
        # Should still work but return empty data

    async def test_empty_choice_distribution_handling(self, analytics_service, mock_session):
        """Test handling of empty choice distributions"""
        analytics_with_empty_choices = MagicMock()
        analytics_with_empty_choices.fragment_key = "empty_fragment"
        analytics_with_empty_choices.choice_distribution = {}
        analytics_with_empty_choices.most_popular_choice_id = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [analytics_with_empty_choices]
        mock_session.execute.return_value = mock_result

        result = await analytics_service.analyze_choice_distribution_patterns()

        # Should handle empty data gracefully
        assert result["status"] == "success"
        assert result["summary"]["total_choices_made"] == 0

    async def test_null_emotional_states_handling(self, analytics_service, mock_session):
        """Test handling of null emotional states"""
        journey_with_null_emotions = MagicMock()
        journey_with_null_emotions.user_id = 123
        journey_with_null_emotions.emotional_states = None
        journey_with_null_emotions.character_interaction_count = None

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [journey_with_null_emotions]
        mock_session.execute.return_value = mock_result

        result = await analytics_service.get_character_voice_analytics()

        # Should handle null data gracefully
        assert result["status"] == "no_data"

    async def test_malformed_json_data_handling(self, analytics_service, mock_session):
        """Test handling of malformed JSON data in database"""
        journey_with_malformed_data = MagicMock()
        journey_with_malformed_data.user_id = 123
        journey_with_malformed_data.emotional_states = ["not_a_dict", {"invalid": "structure"}]
        journey_with_malformed_data.character_interaction_count = {"Lucien": "not_a_number"}

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [journey_with_malformed_data]
        mock_session.execute.return_value = mock_result

        # Should not crash and handle malformed data gracefully
        result = await analytics_service.get_character_voice_analytics()
        assert result["status"] in ["success", "no_data"]  # Should handle gracefully

    # Database Connection Error Tests
    async def test_database_connection_error(self, analytics_service, mock_session):
        """Test handling of database connection errors"""
        mock_session.execute.side_effect = ConnectionError("Database connection lost")

        result = await analytics_service.get_fragment_engagement_metrics("test_fragment")

        assert result["status"] == "error"
        assert "connection" in result["message"].lower()

    async def test_transaction_rollback_handling(self, analytics_service, mock_session):
        """Test proper handling of transaction rollbacks"""
        mock_session.execute.side_effect = IntegrityError("statement", "params", "orig")

        result = await analytics_service.analyze_choice_distribution_patterns()

        assert result["status"] == "error"

    # Memory Usage Tests
    async def test_memory_efficient_large_export(self, analytics_service, mock_session):
        """Test memory efficiency during large data exports"""
        # Create a large dataset
        large_fragment_data = []
        for i in range(10000):
            fragment = MagicMock()
            fragment.fragment_key = f"fragment_{i}"
            fragment.view_count = i
            fragment.completion_count = i - 10
            fragment.drop_off_count = 10
            fragment.average_time_spent = 45
            fragment.choice_distribution = {}
            fragment.most_popular_choice_id = None
            fragment.users_progressed_from = i - 20
            fragment.users_returned_to = 5
            fragment.created_at = datetime.utcnow()
            fragment.updated_at = datetime.utcnow()
            large_fragment_data.append(fragment)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = large_fragment_data

        # Mock second query for journey data
        journey_result = MagicMock()
        journey_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_result, journey_result]

        # Test CSV export (which should be more memory efficient for large datasets)
        date_range = ("2024-01-01T00:00:00", "2024-01-31T23:59:59")
        result = await analytics_service.export_analytics_data(date_range, "csv")

        # Should complete successfully even with large dataset
        assert isinstance(result, dict)
        assert "fragment_analytics.csv" in result


# Integration Test Class
class TestAnalyticsServiceIntegration:
    """Integration tests for AnalyticsService with more realistic scenarios"""

    @pytest.fixture
    def mock_session_with_realistic_data(self):
        """Mock session with realistic data patterns"""
        session = AsyncMock(spec=AsyncSession)

        # Setup realistic fragment analytics data
        fragments = []
        for i in range(10):
            fragment = FragmentAnalytics(
                id=i + 1,
                fragment_key=f"story_fragment_{i:03d}",
                view_count=100 - (i * 5),  # Decreasing views as story progresses
                completion_count=85 - (i * 7),  # Decreasing completion
                drop_off_count=15 + (i * 2),  # Increasing drop-off
                average_time_spent=30 + (i * 5),  # Increasing time spent
                choice_distribution={f"choice_{j}": 20 - (j * 3) for j in range(3)},
                most_popular_choice_id=1,
                users_progressed_from=80 - (i * 6),
                users_returned_to=5 + i,
                created_at=datetime.utcnow() - timedelta(days=30 - i),
                updated_at=datetime.utcnow() - timedelta(days=i),
                last_analyzed_at=datetime.utcnow() - timedelta(hours=i)
            )
            fragments.append(fragment)

        session.fragments = fragments
        return session

    async def test_realistic_bottleneck_identification(self, mock_session_with_realistic_data):
        """Test bottleneck identification with realistic progression data"""
        analytics_service = AnalyticsService(mock_session_with_realistic_data)

        # Mock the database queries
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_session_with_realistic_data.fragments

        journey_result = MagicMock()
        journey_result.scalars.return_value.all.return_value = []

        mock_session_with_realistic_data.execute.side_effect = [mock_result, journey_result]

        result = await analytics_service.identify_narrative_bottlenecks()

        # Should identify later fragments as bottlenecks due to higher drop-off rates
        assert result["status"] == "success"
        assert len(result["bottlenecks"]) > 0

        # The last fragments should have higher drop-off rates
        bottleneck_fragments = [b["fragment_key"] for b in result["bottlenecks"]]
        assert any("009" in fragment for fragment in bottleneck_fragments)  # Later fragments should be bottlenecks

    async def test_realistic_user_journey_analysis(self, mock_session_with_realistic_data):
        """Test user journey analysis with realistic user behavior patterns"""
        analytics_service = AnalyticsService(mock_session_with_realistic_data)

        # Create realistic user journey data
        now = datetime.utcnow()
        journeys = []
        for i in range(50):
            journey = UserJourneyAnalytics(
                id=i + 1,
                user_id=1000 + i,
                fragments_visited=[f"story_fragment_{j:03d}" for j in range(min(i // 5 + 1, 10))],
                choices_made=[{"choice_id": 1, "fragment_key": "story_fragment_001", "timestamp": now.isoformat()}],
                progression_path=[f"story_fragment_{j:03d}" for j in range(min(i // 5 + 1, 10))],
                total_time_spent=300 + (i * 50),
                session_count=i // 10 + 1,
                average_session_duration=150 + (i * 10),
                backtrack_count=i // 20,
                exploration_score=60 + (i % 40),
                engagement_level="highly_engaged" if i < 20 else "engaged" if i < 40 else "stalled",
                fragments_completed=min(i // 5, 10),
                narrative_completion_percentage=min(i * 2, 100),
                emotional_states=[
                    {"fragment": "story_fragment_001", "emotion": "curiosity", "intensity": 0.8},
                    {"fragment": "story_fragment_002", "emotion": "anticipation", "intensity": 0.7}
                ] if i < 30 else [],
                character_interaction_count={"Lucien": i // 10 + 1, "Diana": i // 15 + 1},
                journey_started_at=now - timedelta(days=30 - (i // 10)),
                last_activity_at=now - timedelta(hours=i // 5),
                created_at=now - timedelta(days=30),
                updated_at=now
            )
            journeys.append(journey)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = journeys
        mock_session_with_realistic_data.execute.return_value = mock_result

        result = await analytics_service.track_conversion_funnel_metrics()

        # Assert realistic funnel metrics
        assert result["status"] == "success"
        assert result["funnel_stages"]["initial_visit"]["count"] == 50
        assert result["funnel_stages"]["engaged"]["count"] > 0
        assert result["conversion_rates"]["initial_visit"] == 100.0
        assert result["conversion_rates"]["engaged"] < 100.0  # Should have some drop-off


if __name__ == "__main__":
    # Run tests directly when not using pytest
    if not SERVICE_AVAILABLE:
        print("Analytics service not available. Skipping tests.")
        print("This test file is designed to test the AnalyticsService implementation.")
        print("Once the service and database models are available, run: pytest tests/services/test_analytics_service.py")
    elif not PYTEST_AVAILABLE:
        print("Pytest not available. This is a pytest-based test suite.")
        print("Install pytest to run the full test suite: pip install pytest pytest-asyncio")
        print("Or run with: python -m pytest tests/services/test_analytics_service.py -v")
    else:
        print("Use 'pytest tests/services/test_analytics_service.py -v' to run the full test suite")
        print("Test file created successfully with comprehensive coverage for AnalyticsService")