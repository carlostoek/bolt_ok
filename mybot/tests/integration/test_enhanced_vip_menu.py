"""
Integration Tests for the Enhanced VIP Menu.

Tests the navigation flow, callback routing, and permission enforcement
for the enhanced VIP menu, as per requirements 1.1.1 and 1.1.2.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

# Add project root to path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aiogram.types import CallbackQuery, User as TelegramUser, Message as TelegramMessage

# Mock SQLAlchemy and other dependencies for a lightweight test environment
@pytest.fixture(scope="session", autouse=True)
def mock_dependencies():
    sys.modules['sqlalchemy'] = MagicMock()
    sys.modules['sqlalchemy.ext'] = MagicMock()
    sys.modules['sqlalchemy.ext.asyncio'] = MagicMock()
    sys.modules['services.coordinador_central'] = MagicMock()
    sys.modules['utils.html_formatter'] = MagicMock()


# Import application components after mocking
from handlers.admin import admin_menu
from handlers.admin import enhanced_vip_handlers
from database.models import User
from utils.menu_manager import menu_manager

class TestVipMenuBase:
    """Base class with common fixtures for VIP menu tests."""

    @pytest.fixture
    def mock_session(self, admin_user):
        """Mock database session."""
        session = AsyncMock()
        session.get = AsyncMock(return_value=admin_user)
        return session

    @pytest.fixture
    def mock_bot(self):
        """Mock Telegram bot instance."""
        bot = AsyncMock()
        bot.get_me = AsyncMock(return_value=MagicMock(username="test_bot"))
        return bot

    @pytest.fixture
    def admin_user(self):
        """Sample admin user for testing."""
        return User(id=999999, username="test_admin", is_admin=True)

    @pytest.fixture
    def regular_user(self):
        """Sample regular user for testing."""
        return User(id=123456, username="test_user", is_admin=False)

    @pytest.fixture
    def mock_callback_query(self, mock_bot):
        """Creates a mock CallbackQuery object."""
        def _creator(user):
            callback = AsyncMock(spec=CallbackQuery)
            callback.from_user = TelegramUser(id=user.id, is_bot=False, first_name=user.username)
            callback.message = AsyncMock(spec=TelegramMessage)
            callback.bot = mock_bot
            callback.answer = AsyncMock()
            return callback
        return _creator


class TestEnhancedVipMenu(TestVipMenuBase):
    """Test suite for the enhanced VIP menu navigation and access control."""

    @pytest.mark.asyncio
    @patch('handlers.admin.admin_menu.is_admin', return_value=True)
    @patch('handlers.admin.admin_menu.ENHANCED_VIP_AVAILABLE', True)
    @patch('handlers.admin.enhanced_vip_handlers.show_enhanced_vip_menu')
    async def test_navigate_to_enhanced_vip_menu_as_admin(
        self, mock_show_menu, mock_is_admin, mock_callback_query, admin_user, mock_session
    ):
        """
        Requirement 1.1.1 & 1.1.2: Test that an admin can successfully navigate 
        to the enhanced VIP menu.
        """
        # Arrange
        callback = mock_callback_query(admin_user)

        # Act
        await admin_menu.admin_vip_enhanced(callback, mock_session)

        # Assert
        mock_is_admin.assert_called_once_with(admin_user.id, mock_session)
        mock_show_menu.assert_called_once_with(callback, mock_session)

    @pytest.mark.asyncio
    @patch('handlers.admin.admin_menu.is_admin', return_value=False)
    @patch('handlers.admin.enhanced_vip_handlers.show_enhanced_vip_menu')
    async def test_navigate_to_enhanced_vip_menu_as_non_admin(
        self, mock_show_menu, mock_is_admin, mock_callback_query, regular_user, mock_session
    ):
        """
        Requirement 1.1.1 & 1.1.2: Test that a non-admin user is denied access
        to the enhanced VIP menu.
        """
        # Arrange
        callback = mock_callback_query(regular_user)

        # Act
        await admin_menu.admin_vip_enhanced(callback, mock_session)

        # Assert
        mock_is_admin.assert_called_once_with(regular_user.id, mock_session)
        mock_show_menu.assert_not_called()
        callback.answer.assert_called_once_with("Acceso denegado", show_alert=True)

    @pytest.mark.asyncio
    @patch('utils.menu_manager.menu_manager.update_menu')
    async def test_enhanced_vip_menu_content(
        self, mock_update_menu, mock_callback_query, admin_user, mock_session, mock_bot
    ):
        """
        Tests that the enhanced VIP menu displays the correct content and options.
        """
        # Arrange
        callback = mock_callback_query(admin_user)
        
        # Mock the service call within the handler
        with patch('handlers.admin.enhanced_vip_handlers.create_enhanced_vip_menu') as mock_create_menu:
            mock_create_menu.return_value = ("Test VIP Menu", MagicMock())

            # Act
            await enhanced_vip_handlers.show_enhanced_vip_menu(callback, mock_session)

            # Assert
            mock_create_menu.assert_called_once_with(mock_session, admin_user.id, mock_bot)
            mock_update_menu.assert_called_once()
            
            # Check the content passed to update_menu
            args, kwargs = mock_update_menu.call_args
            assert "Test VIP Menu" in args
            assert args[4] == "vip_enhanced_main" # menu_state is the 5th positional arg
