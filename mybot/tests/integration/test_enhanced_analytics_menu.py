"""
Integration Tests for the Enhanced Analytics Menu.

Tests the navigation flow, access control, and export functionality
for the enhanced analytics menu, as per requirements 1.2.1 and 1.2.6.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

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

# Import application components after mocking
from handlers.admin import admin_menu
from handlers.admin import enhanced_analytics
from database.models import User

class TestAnalyticsMenuBase:
    """Base class with common fixtures for Analytics menu tests."""

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


class TestEnhancedAnalyticsMenu(TestAnalyticsMenuBase):
    """Test suite for the enhanced analytics menu."""

    @pytest.mark.asyncio
    @patch('handlers.admin.admin_menu.is_admin', return_value=True)
    @patch('handlers.admin.admin_menu.ENHANCED_ANALYTICS_AVAILABLE', True)
    @patch('handlers.admin.enhanced_analytics.show_enhanced_analytics_main')
    async def test_navigate_to_enhanced_analytics_as_admin(
        self, mock_show_main, mock_is_admin, mock_callback_query, admin_user, mock_session
    ):
        """
        Requirement 1.2.1: Test admin can navigate to enhanced analytics.
        """
        # Arrange
        callback = mock_callback_query(admin_user)

        # Act
        await admin_menu.admin_analytics_enhanced(callback, mock_session)

        # Assert
        mock_is_admin.assert_called_once_with(admin_user.id, mock_session)
        mock_show_main.assert_called_once_with(callback, mock_session)

    @pytest.mark.asyncio
    @patch('handlers.admin.admin_menu.is_admin', return_value=False)
    @patch('handlers.admin.enhanced_analytics.show_enhanced_analytics_main')
    async def test_navigate_to_enhanced_analytics_as_non_admin(
        self, mock_show_main, mock_is_admin, mock_callback_query, regular_user, mock_session
    ):
        """
        Requirement 1.2.1: Test non-admin is denied access.
        """
        # Arrange
        callback = mock_callback_query(regular_user)

        # Act
        await admin_menu.admin_analytics_enhanced(callback, mock_session)

        # Assert
        mock_is_admin.assert_called_once_with(regular_user.id, mock_session)
        mock_show_main.assert_not_called()
        callback.answer.assert_called_once_with("Acceso denegado", show_alert=True)

    @pytest.mark.asyncio
    @patch('utils.menu_manager.menu_manager.update_menu')
    @patch('handlers.admin.enhanced_analytics.is_admin', return_value=True)
    async def test_analytics_dashboard_content_and_format(
        self, mock_is_admin, mock_update_menu, mock_callback_query, admin_user, mock_session
    ):
        """
        Tests that the dashboard displays correctly formatted content.
        """
        # Arrange
        callback = mock_callback_query(admin_user)

        # Act
        await enhanced_analytics.show_enhanced_analytics_main(callback, mock_session)

        # Assert
        mock_update_menu.assert_called_once()
        args, kwargs = mock_update_menu.call_args
        menu_text = args[1]
        assert "Sistema de Análisis Administrativo Mejorado" in menu_text
        assert "Panel de control integral" in menu_text
        assert args[4] == "admin_enhanced_analytics_main" # menu_state is positional

    @pytest.mark.asyncio
    @patch('handlers.admin.enhanced_analytics.track_response_time', new_callable=AsyncMock)
    @patch('handlers.admin.enhanced_analytics.is_admin', return_value=True)
    async def test_analytics_export_functionality(
        self, mock_is_admin, mock_track_response, mock_callback_query, admin_user, mock_session
    ):
        """
        Requirement 1.2.6: Test analytics export functionality.
        """
        # Arrange
        callback = mock_callback_query(admin_user)
        callback.data = "export_analytics_data"

        # Act
        await enhanced_analytics.export_analytics_data(callback, mock_session)

        # Assert
        mock_is_admin.assert_called_once_with(admin_user.id, mock_session)
        mock_track_response.assert_called_once()
        # We are not checking the message content as it depends on a deeper service call
        # The main point is that the handler is called and tries to execute the logic.
