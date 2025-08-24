"""
Tests de integración simples para verificar la integración del bridge.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import CallbackQuery, User, Chat

from services.diana_menu_integration_impl import DianaCompatibilityBridge


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_callback():
    callback = AsyncMock(spec=CallbackQuery)
    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = 123456789
    callback.message = AsyncMock()
    callback.message.chat = MagicMock(spec=Chat)
    callback.message.chat.id = 123456789
    callback.data = "admin_fragments_manage"
    return callback


@pytest.mark.asyncio
async def test_compatibility_bridge_handles_admin_fragments_manage(mock_callback, mock_session):
    """Test that DianaCompatibilityBridge correctly handles admin_fragments_manage callback."""
    # Create mock diana_system
    mock_diana_system = MagicMock()
    mock_diana_system.handle_callback = AsyncMock(return_value=True)
    
    # Patch get_diana_menu_system to return our mock
    with patch('services.diana_menu_integration_impl.get_diana_menu_system', return_value=mock_diana_system):
        # Create the bridge now that we've patched the dependency
        bridge = DianaCompatibilityBridge(mock_session)
        
        # Set the callback data
        mock_callback.data = "admin_fragments_manage"
        
        # Call the handle_callback method
        result = await bridge.handle_callback(mock_callback)
        
        # Verify that it returned True (callback was handled)
        assert result is True
        
        # Verify that handle_callback was called with the callback
        assert mock_diana_system.handle_callback.called
        assert mock_diana_system.handle_callback.call_args[0][0] == mock_callback