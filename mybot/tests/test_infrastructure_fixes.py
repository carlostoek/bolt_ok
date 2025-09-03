"""
Test Infrastructure Fixes - Critical Testing Components
This file implements the missing testing infrastructure components identified in the audit.
"""
import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Fix import path issues
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.coordinador_central import CoordinadorCentral
from services.point_service import PointService
from services.event_bus import EventBus
from services.notification_service import NotificationService
from database.models import User


@pytest.mark.asyncio
class TestAsyncSessionMockingFixes:
    """Tests to verify async session mocking is working correctly."""
    
    async def test_async_session_mock_setup(self):
        """Verify AsyncMock configuration for SQLAlchemy sessions works."""
        # Proper AsyncMock configuration for SQLAlchemy sessions
        session_mock = AsyncMock(spec=AsyncSession)
        result_mock = MagicMock()  # Use MagicMock for result object
        result_mock.scalar.return_value = User(id=123, first_name="Test")
        result_mock.scalar_one_or_none.return_value = User(id=123, first_name="Test")
        session_mock.execute.return_value = result_mock
        
        # Test the mock works correctly
        query_result = await session_mock.execute(select(User))
        user = query_result.scalar()  # This should be synchronous now
        
        assert user.id == 123
        assert user.first_name == "Test"
        session_mock.execute.assert_called_once()
        
    async def test_async_context_manager_handling(self):
        """Fix async context manager mocking issues."""
        session_mock = AsyncMock(spec=AsyncSession)
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = session_mock
        session_mock.begin.return_value = mock_context
        
        # Test context manager works
        async with session_mock.begin() as ctx:
            assert ctx == session_mock
        
        session_mock.begin.assert_called_once()
        mock_context.__aenter__.assert_called_once()

    async def test_point_service_proper_initialization(self, session, level_service, achievement_service):
        """Test PointService initializes correctly with all dependencies."""
        mock_bot = AsyncMock()
        notification_service = NotificationService(session, mock_bot)
        
        # This should not raise TypeError anymore
        point_service = PointService(session, level_service, achievement_service, notification_service)
        
        assert point_service.session == session
        assert point_service.level_service == level_service
        assert point_service.achievement_service == achievement_service
        assert point_service.notification_service == notification_service


@pytest.mark.asyncio 
class TestCoordinadorCentralInitializationFixes:
    """Tests to verify CoordinadorCentral initializes correctly."""
    
    async def test_coordinador_central_proper_initialization(self, session):
        """Test CoordinadorCentral can be initialized without dependency errors."""
        # Mock all required services
        with patch('services.coordinador_central.NarrativePointService') as mock_np, \
             patch('services.coordinador_central.ChannelEngagementService') as mock_ce, \
             patch('services.coordinador_central.NarrativeAccessService') as mock_na:
            
            mock_np.return_value = AsyncMock()
            mock_ce.return_value = AsyncMock()  
            mock_na.return_value = AsyncMock()
            
            # This should not raise initialization errors
            coordinador = CoordinadorCentral(session)
            
            assert coordinador.session == session
            assert coordinador.narrative_point is not None
            assert coordinador.channel_engagement is not None
            assert coordinador.narrative_access is not None


@pytest.mark.asyncio
class TestAsyncTestPatterns:
    """Tests demonstrating correct async testing patterns."""
    
    async def test_aiogram_callback_query_mocking(self):
        """Test proper aiogram CallbackQuery mocking."""
        callback = MagicMock()
        callback.from_user.id = 123456789
        callback.data = "test_callback"
        callback.answer = AsyncMock()
        callback.edit_message_text = AsyncMock()
        
        # Test callback operations
        await callback.answer("Test response")
        await callback.edit_message_text("Updated message")
        
        callback.answer.assert_called_once_with("Test response")
        callback.edit_message_text.assert_called_once_with("Updated message")
        
    async def test_aiogram_message_mocking(self):
        """Test proper aiogram Message mocking."""
        message = MagicMock()
        message.from_user.id = 123456789
        message.chat.id = 123456789
        message.text = "Test message"
        message.reply = AsyncMock()
        
        # Test message operations
        await message.reply("Response")
        
        message.reply.assert_called_once_with("Response")

    async def test_sqlalchemy_query_result_mocking(self):
        """Test proper SQLAlchemy query result mocking."""
        session_mock = AsyncMock(spec=AsyncSession)
        
        # Mock a select query
        result_mock = MagicMock()  # Use MagicMock for result object
        user = User(id=123, first_name="Test", role="free", points=100)
        result_mock.scalar_one_or_none.return_value = user
        
        # Mock scalars() result
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = [user]
        result_mock.scalars.return_value = scalars_mock
        session_mock.execute.return_value = result_mock
        
        # Test query execution
        query_result = await session_mock.execute(select(User))
        single_user = query_result.scalar_one_or_none()
        all_users = query_result.scalars().all()
        
        assert single_user.id == 123
        assert len(all_users) == 1
        assert all_users[0].id == 123


@pytest.mark.asyncio
class TestEventBusInfrastructure:
    """Tests for EventBus infrastructure fixes."""
    
    async def test_eventbus_initialization(self):
        """Test EventBus can be initialized without errors."""
        event_bus = EventBus()
        assert event_bus is not None
        assert hasattr(event_bus, 'publish')
        assert hasattr(event_bus, 'subscribe')
        
    async def test_eventbus_mock_setup(self):
        """Test EventBus can be properly mocked for tests."""
        event_bus_mock = AsyncMock(spec=EventBus)
        event_bus_mock.publish = AsyncMock()
        event_bus_mock.subscribe = AsyncMock()
        
        # Test mock works
        await event_bus_mock.publish("test_event", {"data": "test"})
        event_bus_mock.publish.assert_called_once_with("test_event", {"data": "test"})


class TestHelperUtilities:
    """Utility functions for testing."""
    
    @staticmethod
    def create_proper_session_mock():
        """Create properly configured session mock."""
        session_mock = AsyncMock(spec=AsyncSession)
        
        # Configure common operations
        session_mock.add = MagicMock()
        session_mock.commit = AsyncMock()
        session_mock.rollback = AsyncMock()
        session_mock.close = AsyncMock()
        session_mock.refresh = AsyncMock()
        
        # Configure transaction handling
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = session_mock
        mock_context.__aexit__.return_value = None
        session_mock.begin.return_value = mock_context
        
        return session_mock
    
    @staticmethod 
    def create_user_mock(user_id: int = 123456789, role: str = "free", points: float = 100.0):
        """Create properly configured user mock."""
        user = User(
            id=user_id,
            first_name="TestUser",
            username="testuser",
            role=role,
            points=points
        )
        return user
    
    @staticmethod
    def create_callback_mock(user_id: int = 123456789, data: str = "test_callback"):
        """Create properly configured callback query mock."""
        callback = MagicMock()
        callback.from_user.id = user_id
        callback.data = data
        callback.answer = AsyncMock()
        callback.edit_message_text = AsyncMock()
        callback.message.chat.id = user_id
        callback.message.message_id = 1
        return callback