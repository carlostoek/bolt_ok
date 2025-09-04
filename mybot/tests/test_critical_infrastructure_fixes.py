"""
Critical Infrastructure Fixes - Testing Foundation
This file implements the most critical fixes for the test infrastructure without depending on complex service hierarchies.
"""
import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import time

# Fix import path issues
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import User


@pytest.mark.asyncio
class TestAsyncTestingInfrastructure:
    """Tests to verify async testing infrastructure works correctly."""
    
    async def test_proper_async_session_mocking(self):
        """Test the correct way to mock SQLAlchemy AsyncSession."""
        # Create proper AsyncSession mock
        session_mock = AsyncMock(spec=AsyncSession)
        
        # Create result mock (should be MagicMock, not AsyncMock)
        result_mock = MagicMock()
        test_user = User(id=123, first_name="Test", role="free", points=100)
        result_mock.scalar_one_or_none.return_value = test_user
        
        # Configure session mock
        session_mock.execute.return_value = result_mock
        
        # Test query execution
        query_result = await session_mock.execute(select(User))
        user = query_result.scalar_one_or_none()
        
        # Validate
        assert user.id == 123
        assert user.first_name == "Test"
        session_mock.execute.assert_called_once()
    
    async def test_proper_async_context_manager_mocking(self):
        """Test async context manager mocking for transactions."""
        session_mock = AsyncMock(spec=AsyncSession)
        
        # Create context manager mock
        context_mock = AsyncMock()
        context_mock.__aenter__.return_value = session_mock
        context_mock.__aexit__.return_value = None
        session_mock.begin.return_value = context_mock
        
        # Test context manager usage
        async with session_mock.begin() as transaction:
            assert transaction == session_mock
            
        session_mock.begin.assert_called_once()
        context_mock.__aenter__.assert_called_once()
        
    async def test_aiogram_callback_query_mocking_pattern(self):
        """Test correct pattern for mocking aiogram CallbackQuery."""
        callback = MagicMock()
        callback.from_user.id = 123456789
        callback.data = "test_callback_data"
        callback.answer = AsyncMock()
        callback.edit_message_text = AsyncMock()
        callback.message.chat.id = 123456789
        callback.message.message_id = 1
        
        # Test callback operations
        await callback.answer("Response")
        await callback.edit_message_text("Updated text")
        
        # Verify calls
        callback.answer.assert_called_once_with("Response")
        callback.edit_message_text.assert_called_once_with("Updated text")

    async def test_scalars_result_mocking_pattern(self):
        """Test correct pattern for mocking SQLAlchemy result.scalars().all()."""
        session_mock = AsyncMock(spec=AsyncSession)
        
        # Create proper result mock chain
        result_mock = MagicMock()
        test_user = User(id=123, first_name="Test", role="free", points=100)
        
        # Mock scalars() chain correctly
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = [test_user]
        result_mock.scalars.return_value = scalars_mock
        result_mock.scalar_one_or_none.return_value = test_user
        
        session_mock.execute.return_value = result_mock
        
        # Test both patterns work
        query_result = await session_mock.execute(select(User))
        single_user = query_result.scalar_one_or_none()
        all_users = query_result.scalars().all()
        
        assert single_user.id == 123
        assert len(all_users) == 1
        assert all_users[0].id == 123

    async def test_async_service_method_chaining(self):
        """Test proper async service method chaining for complex scenarios."""
        # Mock a service with async methods
        service_mock = AsyncMock()
        service_mock.get_user.return_value = AsyncMock(id=123, points=100)
        service_mock.award_points.return_value = True
        service_mock.check_achievements.return_value = []
        
        # Test method chaining
        user = await service_mock.get_user(123)
        success = await service_mock.award_points(123, 10)
        achievements = await service_mock.check_achievements(123)
        
        assert user.id == 123
        assert success is True
        assert achievements == []


@pytest.mark.asyncio
class TestServiceMockingPatterns:
    """Demonstrates correct mocking patterns for all major services."""
    
    async def test_point_service_mocking_pattern(self):
        """Test how to properly mock PointService for integration tests."""
        # Mock all dependencies
        session_mock = AsyncMock(spec=AsyncSession)
        level_service_mock = AsyncMock()
        achievement_service_mock = AsyncMock()
        notification_service_mock = AsyncMock()
        
        # Configure level service mock
        level_service_mock.check_for_level_up = AsyncMock(return_value=None)
        level_service_mock.get_level_for_points = AsyncMock(return_value=1)
        
        # Configure achievement service mock
        achievement_service_mock.check_achievements = AsyncMock(return_value=[])
        
        # Mock PointService constructor
        with patch('services.point_service.PointService') as mock_class:
            point_service_mock = AsyncMock()
            point_service_mock.get_user_points = AsyncMock(return_value=100.0)
            point_service_mock.award_points = AsyncMock(return_value=True)
            mock_class.return_value = point_service_mock
            
            # Test service usage
            from services.point_service import PointService
            service = PointService(session_mock, level_service_mock, achievement_service_mock)
            
            points = await service.get_user_points(123)
            success = await service.award_points(123, 10, "test")
            
            assert points == 100.0
            assert success is True

    async def test_coordinador_central_facade_mocking(self):
        """Test complete mocking of CoordinadorCentral facade."""
        session_mock = AsyncMock(spec=AsyncSession)
        
        # Mock all service constructors that CoordinadorCentral uses
        with patch('services.integration.narrative_point_service.NarrativePointService') as mock_np, \
             patch('services.integration.channel_engagement_service.ChannelEngagementService') as mock_ce, \
             patch('services.integration.narrative_access_service.NarrativeAccessService') as mock_na, \
             patch('services.integration.event_coordinator.EventCoordinator') as mock_ec, \
             patch('services.reconciliation_service.ReconciliationService') as mock_rs:
            
            # Configure all mocks
            mock_np.return_value = AsyncMock()
            mock_ce.return_value = AsyncMock()
            mock_na.return_value = AsyncMock()
            mock_ec.return_value = AsyncMock()
            mock_rs.return_value = AsyncMock()
            
            # Now CoordinadorCentral should initialize correctly
            from services.coordinador_central import CoordinadorCentral
            coordinador = CoordinadorCentral(session_mock)
            
            # Validate initialization
            assert coordinador.session == session_mock
            assert coordinador.narrative_point is not None
            assert coordinador.channel_engagement is not None
            assert coordinador.narrative_access is not None
            assert coordinador.event_coordinator is not None

    async def test_eventbus_basic_functionality(self):
        """Test EventBus can be imported and used without errors."""
        from services.event_bus import EventBus
        
        event_bus = EventBus()
        
        # Test basic operations don't fail
        assert hasattr(event_bus, 'publish')
        assert hasattr(event_bus, 'subscribe')
        assert hasattr(event_bus, '_subscribers')

    async def test_notification_service_basic_creation(self):
        """Test NotificationService can be created for tests."""
        session_mock = AsyncMock(spec=AsyncSession)
        bot_mock = AsyncMock()
        
        from services.notification_service import NotificationService
        
        # This should work without issues
        notification_service = NotificationService(session_mock, bot_mock)
        
        assert notification_service.session == session_mock
        assert notification_service.bot == bot_mock


@pytest.mark.asyncio 
class TestPerformanceBaseline:
    """Baseline performance tests for critical components."""
    
    async def test_simple_user_creation_performance(self, session):
        """Test simple user creation performance baseline."""
        start_time = time.perf_counter()
        
        # Create user (simplest database operation)
        user = User(
            id=999999999,
            first_name="PerfTest",
            role="free",
            points=0
        )
        session.add(user)
        await session.commit()
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Basic operation should be very fast
        assert duration_ms < 100, f"User creation took {duration_ms:.2f}ms, too slow"
        
        # Cleanup
        await session.delete(user)
        await session.commit()

    async def test_simple_query_performance(self, session):
        """Test simple query performance baseline."""
        # Create test user
        user = User(
            id=888888888,
            first_name="QueryTest",
            role="free",
            points=50
        )
        session.add(user)
        await session.commit()
        
        start_time = time.perf_counter()
        
        # Execute query
        result = await session.execute(select(User).where(User.id == 888888888))
        found_user = result.scalar_one_or_none()
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Query should be very fast
        assert duration_ms < 50, f"Query took {duration_ms:.2f}ms, too slow"
        assert found_user is not None
        assert found_user.id == 888888888
        
        # Cleanup
        await session.delete(found_user)
        await session.commit()


@pytest.mark.asyncio
class TestAsyncPatternValidation:
    """Validates async patterns work correctly in test environment."""
    
    async def test_async_context_manager_pattern(self, session):
        """Test async context manager patterns work in test environment."""
        # Test transaction context manager
        async with session.begin():
            user = User(id=777777777, first_name="ContextTest", role="free")
            session.add(user)
            # Transaction should commit automatically
        
        # Verify user was created
        result = await session.execute(select(User).where(User.id == 777777777))
        found_user = result.scalar_one_or_none()
        assert found_user is not None
        assert found_user.first_name == "ContextTest"
        
        # Cleanup
        await session.delete(found_user)
        await session.commit()

    async def test_async_exception_handling_pattern(self):
        """Test async exception handling patterns."""
        mock_service = AsyncMock()
        mock_service.risky_operation = AsyncMock(side_effect=Exception("Test error"))
        
        # Test exception handling
        try:
            await mock_service.risky_operation()
            assert False, "Exception should have been raised"
        except Exception as e:
            assert str(e) == "Test error"
            
        mock_service.risky_operation.assert_called_once()

    async def test_concurrent_async_operations(self):
        """Test concurrent async operations work correctly."""
        async def slow_operation(delay, result):
            await asyncio.sleep(delay / 1000)  # Convert ms to seconds
            return result
        
        start_time = time.perf_counter()
        
        # Run operations concurrently
        results = await asyncio.gather(
            slow_operation(10, "result1"),
            slow_operation(15, "result2"),
            slow_operation(20, "result3")
        )
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Should complete in ~20ms (slowest operation), not 45ms (sum)
        assert duration_ms < 30, f"Concurrent operations took {duration_ms:.2f}ms, should be ~20ms"
        assert results == ["result1", "result2", "result3"]