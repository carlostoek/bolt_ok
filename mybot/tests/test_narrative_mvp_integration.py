"""
Test suite for MVP narrative system integration
Tests the complete integration of VIP service, achievement service, and performance optimizer.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy import select

from services.mvp_decision_tree_service import MVPDecisionTreeService
from services.decision_achievement_integration import DecisionAchievementIntegration
from services.decision_performance_optimizer import DecisionPerformanceOptimizer
from services.vip_tier_management_service import VIPTierManagementService
from database.narrative_unified import NarrativeFragment, UserNarrativeState, UserDecisionLog


class TestNarrativeMVPIntegration:
    """Test MVP narrative system integration."""

    @pytest_asyncio.fixture
    async def session(self):
        """Create test database session."""
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=False
        )
        
        # Create tables (in real test, would use proper migration)
        # For this integration test, we'll mock the session
        session_mock = AsyncMock(spec=AsyncSession)
        yield session_mock
        await engine.dispose()

    @pytest_asyncio.fixture
    async def decision_tree_service(self, session):
        """Create decision tree service with mocked dependencies."""
        service = MVPDecisionTreeService(session)
        # Mock the VIP service to avoid initialization issues
        service.vip_service = AsyncMock(spec=VIPTierManagementService)
        return service

    @pytest_asyncio.fixture
    async def achievement_integration(self, session):
        """Create achievement integration service."""
        return DecisionAchievementIntegration(session)

    @pytest_asyncio.fixture
    async def performance_optimizer(self, session):
        """Create performance optimizer."""
        return DecisionPerformanceOptimizer(session)

    async def test_vip_service_integration(self, decision_tree_service):
        """Test VIP service integration in decision validation."""
        # Mock VIP service response
        vip_access_result = MagicMock()
        vip_access_result.has_access = False
        vip_access_result.reason.value = "tier_insufficient"
        vip_access_result.narrative_justification = "Diana requires VIP access for this content"
        vip_access_result.personalized_offer = {"discount": 20}
        vip_access_result.unlock_requirements = ["VIP subscription required"]

        decision_tree_service.vip_service.check_content_access.return_value = vip_access_result

        # Mock fragment that requires VIP
        fragment_mock = MagicMock()
        fragment_mock.requires_vip = True
        fragment_mock.id = "vip_fragment_test"
        fragment_mock.is_decision = True
        fragment_mock.choices = [{"text": "Test choice", "points": 10}]

        # Mock fragment service
        decision_tree_service.fragment_service._get_fragment_cached = AsyncMock(return_value=fragment_mock)
        decision_tree_service.fragment_service._get_or_create_user_state = AsyncMock(return_value=MagicMock())

        # Test validation
        result = await decision_tree_service.validate_decision(
            user_id=123,
            fragment_id="vip_fragment_test",
            choice_index=0
        )

        # Verify VIP service was called
        decision_tree_service.vip_service.check_content_access.assert_called_once_with(
            user_id=123,
            fragment_id="vip_fragment_test",
            context="decision_validation"
        )

        # Verify VIP access denial is handled correctly
        assert not result['valid']
        assert 'VIP access required' in result['error']
        assert result['diana_response'] == "Diana requires VIP access for this content"
        assert result['vip_offer'] == {"discount": 20}

    async def test_achievement_service_integration(self, achievement_integration):
        """Test achievement service integration."""
        # Mock achievement service
        achievement_integration.achievement_service._grant = AsyncMock(return_value=True)
        achievement_integration.point_service.add_points = AsyncMock()

        # Mock database queries
        achievement_integration.session.execute = AsyncMock()
        achievement_integration.session.flush = AsyncMock()

        # Create test trigger
        from services.decision_achievement_integration import AchievementTrigger, AchievementTriggerType, AchievementCategory

        test_trigger = AchievementTrigger(
            trigger_id="test_trigger",
            achievement_id="test_achievement",
            trigger_type=AchievementTriggerType.SINGLE_DECISION,
            category=AchievementCategory.NARRATIVE_PROGRESS,
            conditions={"fragment_id": "test_fragment"},
            prerequisites=[],
            diana_announcement="Test achievement unlocked!",
            points_reward=50
        )

        # Mock user context
        user_context = {
            'user_state': MagicMock(),
            'archetype': MagicMock(),
            'mission_progress': MagicMock(),
            'recent_decisions': [],
            'decision_count': 5,
            'completed_fragments': [],
            'current_level': 1,
            'current_tier': 'los_kinkys'
        }

        # Test processing triggered achievements
        result = await achievement_integration._process_triggered_achievements(
            user_id=123,
            triggers=[test_trigger],
            user_context=user_context
        )

        # Verify achievement service was called
        assert len(result['unlocked']) == 1
        assert result['unlocked'][0]['achievement_id'] == "test_achievement"
        assert result['unlocked'][0]['points_awarded'] == 50
        assert result['points_awarded'] == 50

    async def test_performance_optimizer_caching(self, performance_optimizer):
        """Test performance optimizer caching system."""
        # Test fragment caching
        fragment_data = {
            'id': 'test_fragment',
            'title': 'Test Fragment',
            'content': 'Test content',
            'fragment_type': 'STORY',
            'choices': [],
            'triggers': {}
        }

        # Cache the fragment
        await performance_optimizer.cache_fragment('test_fragment', fragment_data)

        # Verify it was cached
        cached_fragment = await performance_optimizer.get_cached_fragment('test_fragment')
        assert cached_fragment is not None
        assert cached_fragment['id'] == 'test_fragment'
        assert cached_fragment['title'] == 'Test Fragment'

        # Test cache memory management
        # Add many items to trigger memory management
        for i in range(200):
            await performance_optimizer.cache_fragment(f'fragment_{i}', fragment_data)

        # Verify cache size is managed
        assert len(performance_optimizer.fragment_cache) <= 100  # Should be limited by _manage_cache_size

    async def test_memory_based_cache_cleanup(self, performance_optimizer):
        """Test memory-based cache cleanup."""
        # Mock large cache data to trigger memory cleanup
        large_data = {'large_content': 'x' * 1024 * 1024}  # 1MB of data

        # Fill caches to trigger memory management
        for i in range(60):  # This should exceed the memory threshold
            await performance_optimizer.cache_fragment(f'large_fragment_{i}', large_data)

        # Verify memory cleanup was triggered (cache size should be limited)
        total_cache_size = performance_optimizer._calculate_total_cache_size()
        total_cache_size_mb = total_cache_size / (1024 * 1024)
        
        # Should be less than max allowed due to cleanup
        assert total_cache_size_mb <= performance_optimizer.max_cache_memory_mb

    async def test_database_query_optimization(self, performance_optimizer):
        """Test database query optimization."""
        # Mock session execute
        mock_result = MagicMock()
        mock_fragment = MagicMock()
        mock_fragment.id = 'test_fragment'
        mock_fragment.title = 'Test Fragment'
        mock_fragment.content = 'Test content'
        mock_fragment.fragment_type = 'STORY'
        mock_fragment.choices = []
        mock_fragment.triggers = {}

        mock_result.scalar_one_or_none.return_value = mock_fragment
        performance_optimizer.session.execute = AsyncMock(return_value=mock_result)

        # Test optimized fragment query
        result = await performance_optimizer.optimize_fragment_query('test_fragment')

        # Verify query was executed
        performance_optimizer.session.execute.assert_called_once()
        
        # Verify result structure
        assert result is not None
        assert result['id'] == 'test_fragment'
        assert result['title'] == 'Test Fragment'

    async def test_character_consistency_preservation(self, decision_tree_service):
        """Test that character consistency is preserved in all responses."""
        # Mock fragment
        fragment_mock = MagicMock()
        fragment_mock.requires_vip = False
        fragment_mock.id = "test_fragment"
        fragment_mock.is_decision = True
        fragment_mock.choices = [{"text": "Test choice", "points": 10}]
        fragment_mock.storyline_level = 1

        # Mock user state
        user_state_mock = MagicMock()
        user_state_mock.current_level = 1
        user_state_mock.has_unlocked_clue = lambda clue: True

        decision_tree_service.fragment_service._get_fragment_cached = AsyncMock(return_value=fragment_mock)
        decision_tree_service.fragment_service._get_or_create_user_state = AsyncMock(return_value=user_state_mock)

        # Test successful validation preserves character voice
        result = await decision_tree_service.validate_decision(
            user_id=123,
            fragment_id="test_fragment",
            choice_index=0
        )

        assert result['valid'] is True
        # Character consistency should be maintained in successful responses

        # Test error responses preserve character voice
        result_error = await decision_tree_service.validate_decision(
            user_id=123,
            fragment_id="nonexistent_fragment",
            choice_index=0
        )

        assert result_error['valid'] is False
        # Diana's voice should be preserved in error messages
        assert '💋' in result_error['diana_response'] or '✨' in result_error['diana_response']

    async def test_end_to_end_decision_processing(self, decision_tree_service):
        """Test complete end-to-end decision processing."""
        # Mock all dependencies for a complete flow
        fragment_mock = MagicMock()
        fragment_mock.requires_vip = False
        fragment_mock.id = "complete_test_fragment"
        fragment_mock.is_decision = True
        fragment_mock.choices = [{"text": "Test choice", "points": 10, "next_fragment_id": "next_fragment"}]
        fragment_mock.storyline_level = 1
        fragment_mock.triggers = {}

        user_state_mock = MagicMock()
        user_state_mock.current_level = 1
        user_state_mock.visited_fragments = []
        user_state_mock.completed_fragments = []
        user_state_mock.interaction_patterns = {}

        next_fragment_mock = MagicMock()
        next_fragment_mock.id = "next_fragment"
        next_fragment_mock.storyline_level = 1
        next_fragment_mock.tier_classification = "los_kinkys"

        # Setup mocks
        decision_tree_service.fragment_service._get_fragment_cached = AsyncMock(
            side_effect=lambda fid: fragment_mock if fid == "complete_test_fragment" else next_fragment_mock
        )
        decision_tree_service.fragment_service._get_or_create_user_state = AsyncMock(return_value=user_state_mock)
        decision_tree_service.point_service.add_points = AsyncMock()
        decision_tree_service.session.commit = AsyncMock()
        decision_tree_service.session.rollback = AsyncMock()

        # Test complete decision processing
        result = await decision_tree_service.process_decision_with_consequences(
            user_id=123,
            fragment_id="complete_test_fragment",
            choice_index=0,
            response_time_ms=250
        )

        # Verify successful processing
        assert result['success'] is True
        assert result['meets_performance_target'] is True  # Should be under 500ms
        assert 'decision_processed' in result
        assert 'next_fragment' in result

        # Verify points were awarded
        decision_tree_service.point_service.add_points.assert_called_with(123, 10, "narrative_decision")

        # Verify database commit was called
        decision_tree_service.session.commit.assert_called_once()

if __name__ == "__main__":
    # Run tests
    asyncio.run(pytest.main([__file__, "-v"]))