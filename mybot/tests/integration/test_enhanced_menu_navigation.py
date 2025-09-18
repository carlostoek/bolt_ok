"""
Integration Tests for Enhanced Menu Navigation.

Tests the overall navigation flow, including access paths to enhanced menus,
back navigation, and menu state management, as per requirements 2.1.6 and
the usability NFRs.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock, call

# Add project root to path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aiogram.types import CallbackQuery, User as TelegramUser, Message as TelegramMessage

# Mock dependencies
@pytest.fixture(scope="session", autouse=True)
def mock_dependencies():
    sys.modules['sqlalchemy'] = MagicMock()
    sys.modules['sqlalchemy.ext'] = MagicMock()
    sys.modules['sqlalchemy.ext.asyncio'] = MagicMock()
    sys.modules['services.coordinador_central'] = MagicMock()
    sys.modules['utils.html_formatter'] = MagicMock()
    sys.modules['services.cached_analytics_service'] = MagicMock()
    sys.modules['services.cache_service'] = MagicMock()
    sys.modules['services.enhanced_vip_service'] = MagicMock()

# Import application components after mocking
from handlers.admin import admin_menu
from database.models import User
from utils.menu_manager import menu_manager

class TestNavigationBase:
    """Base class with common fixtures for navigation tests."""

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
    def mock_callback_query(self, mock_bot):
        """Creates a mock CallbackQuery object."""
        def _creator(user, data):
            callback = AsyncMock(spec=CallbackQuery)
            callback.from_user = TelegramUser(id=user.id, is_bot=False, first_name=user.username)
            callback.message = AsyncMock(spec=TelegramMessage)
            callback.bot = mock_bot
            callback.answer = AsyncMock()
            callback.data = data
            return callback
        return _creator


class TestEnhancedMenuNavigation(TestNavigationBase):
    """Test suite for enhanced menu navigation flows."""

    @pytest.mark.asyncio
    @patch('handlers.admin.admin_menu.is_admin', return_value=True)
    async def test_vip_menu_navigation_and_back(
        self, mock_is_admin, mock_callback_query, admin_user, mock_session
    ):
        """
        Tests navigating to the enhanced VIP menu and then back to the main menu.
        """
        # 1. Navigate to Enhanced VIP Menu
        callback_to_vip = mock_callback_query(admin_user, "admin_vip_enhanced")
        with patch('handlers.admin.enhanced_vip_handlers.show_enhanced_vip_menu') as mock_show_vip:
            await admin_menu.admin_vip_enhanced(callback_to_vip, mock_session)
            mock_show_vip.assert_called_once_with(callback_to_vip, mock_session)

        # 2. Navigate Back from VIP Menu
        callback_back = mock_callback_query(admin_user, "admin_back")
        with patch('utils.menu_factory.menu_factory') as mock_menu_factory, \
             patch.object(menu_manager, 'update_menu', new_callable=AsyncMock) as mock_update_menu:
            
            mock_menu_factory.create_menu = AsyncMock(return_value=("Main Menu Text", MagicMock()))
            menu_manager._nav_history[admin_user.id] = [("admin_main", "HTML"), ("vip_enhanced_main", "HTML")]

            await menu_manager.go_back(callback_back, mock_session)

            mock_menu_factory.create_menu.assert_called_once()
            mock_update_menu.assert_called_once()
            assert mock_update_menu.call_args.args[4] == "admin_main"

    @pytest.mark.asyncio
    @patch('handlers.admin.admin_menu.is_admin', return_value=True)
    async def test_analytics_menu_navigation_and_back(
        self, mock_is_admin, mock_callback_query, admin_user, mock_session
    ):
        """
        Tests navigating to the enhanced analytics menu and then back.
        """
        # 1. Navigate to Enhanced Analytics Menu
        callback_to_analytics = mock_callback_query(admin_user, "admin_analytics_enhanced")
        with patch('handlers.admin.enhanced_analytics.show_enhanced_analytics_main') as mock_show_analytics:
            await admin_menu.admin_analytics_enhanced(callback_to_analytics, mock_session)
            mock_show_analytics.assert_called_once_with(callback_to_analytics, mock_session)

        # 2. Navigate Back from Analytics Menu
        callback_back = mock_callback_query(admin_user, "admin_back")
        with patch('utils.menu_factory.menu_factory') as mock_menu_factory, \
             patch.object(menu_manager, 'update_menu', new_callable=AsyncMock) as mock_update_menu:

            mock_menu_factory.create_menu = AsyncMock(return_value=("Main Menu Text", MagicMock()))
            menu_manager._nav_history[admin_user.id] = [("admin_main", "HTML"), ("admin_analytics_enhanced", "HTML")]

            await menu_manager.go_back(callback_back, mock_session)

            mock_menu_factory.create_menu.assert_called_once()
            mock_update_menu.assert_called_once()
            assert mock_update_menu.call_args.args[4] == "admin_main"
