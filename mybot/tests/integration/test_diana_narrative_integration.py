import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import CallbackQuery

# Patch modules that don't exist in test environment
patch('utils.callback_utils.parse_callback_data', MagicMock()).start()

# Now that we've patched the module, we can import these
from services.diana_menu_system import DianaMenuSystem
from services.diana_menus.admin_menu import DianaAdminMenu
from handlers.admin.narrative_admin import handle_admin_fragments_manage


@pytest.fixture
def mock_callback_query():
    """Create a mock callback query for testing."""
    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = Mock()
    callback.from_user.id = 123456789
    callback.message = Mock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()
    callback.data = "admin_fragments_manage"
    return callback


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.mark.asyncio
async def test_diana_admin_narrative_integration(mock_callback_query, mock_session):
    """Test integration between Diana Admin Menu and Narrative Admin functionality."""
    # Setup Diana Menu System
    diana_system = DianaMenuSystem(mock_session)
    
    # Setup mock admin service stats
    mock_stats = {
        'total_fragments': 15,
        'active_fragments': 12,
        'users_in_narrative': 45,
        'fragments_by_type': {
            'STORY': 8,
            'DECISION': 5,
            'INFO': 2
        }
    }

    with patch('services.diana_menus.admin_menu.is_admin', return_value=True), \
         patch('handlers.admin.narrative_admin.is_admin', return_value=True), \
         patch('handlers.admin.narrative_admin.NarrativeAdminService') as mock_service_class:
        
        # Configure mock service instance
        mock_service_instance = AsyncMock()
        mock_service_instance.get_narrative_stats.return_value = mock_stats
        mock_service_class.return_value = mock_service_instance

        # Test that Diana Admin Menu correctly calls narrative admin handler
        # This simulates clicking the 'Gestionar Fragmentos' button in the Diana Admin Menu
        mock_callback_query.data = "admin_fragments_manage"
        
        # Call the handler through the Diana menu system
        await handle_admin_fragments_manage(mock_callback_query, mock_session)

        # Verify the narrative admin interface was displayed
        assert mock_callback_query.message.edit_text.called
        assert mock_callback_query.answer.called
        
        # Check that correct text was sent with narrative admin details
        call_args = mock_callback_query.message.edit_text.call_args
        text = call_args[0][0]
        assert "SISTEMA DE ADMINISTRACIÓN NARRATIVA" in text
        assert "Fragmentos totales: 15" in text
        assert "Fragmentos activos: 12" in text


@pytest.mark.asyncio
async def test_admin_narrative_menu_button_integration(mock_callback_query, mock_session):
    """Test that the admin_narrative_hub button in Diana Admin Menu works correctly."""
    # Setup Diana Admin Menu
    admin_menu = DianaAdminMenu(mock_session)
    
    # Setup mock stats for narrative section
    mock_narrative_stats = {
        'total_fragments': 20,
        'vip_fragments': 8,
        'users_in_story': 55,
        'total_decisions': 12,
        'diana_fragments': 15,
        'lucien_fragments': 5,
        'active_interactions': 25,
        'vip_access_today': 7,
        'premium_content': 8,
        'vip_conversions': 2
    }

    with patch('services.diana_menus.admin_menu.is_admin', return_value=True), \
         patch('services.diana_menus.admin_menu.DianaAdminMenu._get_narrative_stats') as mock_stats_method:
        
        # Configure mock stats method
        mock_stats_method.return_value = mock_narrative_stats

        # Test showing narrative admin panel
        await admin_menu.show_narrative_admin(mock_callback_query)

        # Verify the response
        assert mock_callback_query.message.edit_text.called
        assert mock_callback_query.answer.called
        
        # Check that correct text was sent with narrative admin details
        call_args = mock_callback_query.message.edit_text.call_args
        text = call_args[0][0]
        assert "ADMINISTRACIÓN NARRATIVA" in text
        assert "Fragmentos totales: 20" in text
        assert "Fragmentos VIP: 8" in text
        assert "Usuarios en historia: 55" in text


@pytest.mark.asyncio
async def test_compatibility_bridge_integration(mock_callback_query, mock_session):
    """Test the integration of compatibility bridge with narrative admin."""
    # Import here to avoid circular imports
    from services.diana_menu_integration_impl import DianaCompatibilityBridge
    
    # Create the bridge
    bridge = DianaCompatibilityBridge(mock_session)
    
    # Configure mocks
    mock_handle_callback = AsyncMock(return_value=True)
    
    with patch.object(bridge.diana_system, 'handle_callback', mock_handle_callback):
        # Ensure callback data is set
        mock_callback_query.data = "admin_fragments_manage"
        
        # Execute the handle_callback method of the bridge
        result = await bridge.handle_callback(mock_callback_query)
        
        # Verify that it returned True (callback handled)
        assert result is True
        
        # Verify that it called the handle_callback method of diana_system
        assert mock_handle_callback.called
        assert mock_handle_callback.call_args[0][0] == mock_callback_query