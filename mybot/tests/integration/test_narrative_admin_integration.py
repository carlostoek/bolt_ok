import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import CallbackQuery, Message
from handlers.admin_narrative_handlers import handle_admin_fragments_manage
from services.narrative_admin_service import NarrativeAdminService
from services.diana_menu_integration_impl import DianaCompatibilityBridge


# Create a simple parse_callback_data function for testing
def parse_callback_data(data):
    """Simple callback data parser for testing."""
    if '?' not in data:
        return {}
    
    parts = data.split('?', 1)
    if len(parts) != 2:
        return {}
    
    params = {}
    for param in parts[1].split('&'):
        if '=' in param:
            key, value = param.split('=', 1)
            params[key] = value
    
    return params


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
async def test_handle_admin_fragments_manage_success(mock_callback_query, mock_session):
    """Test successful execution of handle_admin_fragments_manage."""
    # Setup mock admin service
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

    with patch('handlers.admin_narrative_handlers.is_admin', return_value=True), \
         patch('handlers.admin_narrative_handlers.NarrativeAdminService') as mock_service_class:
        
        # Configure mock service instance
        mock_service_instance = AsyncMock()
        mock_service_instance.get_narrative_stats.return_value = mock_stats
        mock_service_class.return_value = mock_service_instance

        # Call the handler
        await handle_admin_fragments_manage(mock_callback_query, mock_session)

        # Verify the response
        assert mock_callback_query.message.edit_text.called
        assert mock_callback_query.answer.called
        
        # Check that correct text was sent
        call_args = mock_callback_query.message.edit_text.call_args
        text = call_args[0][0]  # First positional argument is the text
        assert "SISTEMA DE ADMINISTRACIÓN NARRATIVA" in text
        assert "Fragmentos totales: 15" in text
        assert "Fragmentos activos: 12" in text
        assert "Usuarios en narrativa: 45" in text


@pytest.mark.asyncio
async def test_handle_admin_fragments_manage_access_denied(mock_callback_query, mock_session):
    """Test access denied for non-admin users."""
    with patch('handlers.admin_narrative_handlers.is_admin', return_value=False):
        await handle_admin_fragments_manage(mock_callback_query, mock_session)
        
        # Verify access denied
        assert mock_callback_query.answer.called
        call_args = mock_callback_query.answer.call_args
        assert "Acceso denegado" in call_args[1].get("text", "") or "Acceso denegado" in call_args[0]


@pytest.mark.asyncio
async def test_list_fragments_success(mock_callback_query, mock_session):
    """Test successful listing of fragments."""
    # Setup callback data for listing fragments
    mock_callback_query.data = "admin_fragments_list?page=1&filter=all"
    
    # Setup mock fragments data
    mock_fragments_data = {
        "items": [
            {
                "id": "frag1",
                "title": "Fragment 1",
                "type": "STORY",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-02T00:00:00",
                "is_active": True,
                "has_choices": False,
                "has_triggers": False,
                "has_requirements": False
            }
        ],
        "total": 1,
        "page": 1,
        "limit": 10,
        "total_pages": 1,
        "has_next": False,
        "has_prev": False,
        "filter_type": None,
        "search_query": None
    }

    with patch('handlers.admin_narrative_handlers.is_admin', return_value=True), \
         patch('handlers.admin_narrative_handlers.NarrativeAdminService') as mock_service_class, \
         patch('handlers.admin_narrative_handlers.parse_callback_data', side_effect=parse_callback_data):
        
        # Configure mock service instance
        mock_service_instance = AsyncMock()
        mock_service_instance.get_all_fragments.return_value = mock_fragments_data
        mock_service_class.return_value = mock_service_instance

        # Call the handler
        await list_fragments(mock_callback_query, mock_session)

        # Verify the response
        assert mock_callback_query.message.edit_text.called
        assert mock_callback_query.answer.called
        
        # Check that correct text was sent
        call_args = mock_callback_query.message.edit_text.call_args
        text = call_args[0][0]
        assert "FRAGMENTOS NARRATIVOS" in text
        assert "Fragment 1" in text
        assert "✅ 📖" in text  # Active story fragment


@pytest.mark.asyncio
async def test_view_fragment_success(mock_callback_query, mock_session):
    """Test successful viewing of fragment details."""
    # Setup callback data for viewing fragment
    mock_callback_query.data = "admin_view_fragment?id=frag1"
    
    # Setup mock fragment details
    mock_fragment_details = {
        "id": "frag1",
        "title": "Fragment 1",
        "content": "Content of fragment 1",
        "type": "STORY",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-02T00:00:00",
        "is_active": True,
        "choices": [],
        "triggers": {},
        "required_clues": [],
        "statistics": {
            "active_users": 5,
            "visited_users": 10,
            "completed_users": 3,
            "completion_rate": 30.0
        }
    }

    with patch('handlers.admin_narrative_handlers.is_admin', return_value=True), \
         patch('handlers.admin_narrative_handlers.NarrativeAdminService') as mock_service_class, \
         patch('handlers.admin_narrative_handlers.parse_callback_data', side_effect=parse_callback_data):
        
        # Configure mock service instance
        mock_service_instance = AsyncMock()
        mock_service_instance.get_fragment_details.return_value = mock_fragment_details
        mock_service_class.return_value = mock_service_instance

        # Call the handler
        await view_fragment(mock_callback_query, mock_session)

        # Verify the response
        assert mock_callback_query.message.edit_text.called
        assert mock_callback_query.answer.called
        
        # Check that correct text was sent
        call_args = mock_callback_query.message.edit_text.call_args
        text = call_args[0][0]
        assert "FRAGMENTO NARRATIVO: Fragment 1" in text
        assert "Content of fragment 1" in text
        assert "Usuarios actuales: 5" in text
        assert "Tasa de finalización: 30.0%" in text


@pytest.mark.asyncio
async def test_compatibility_bridge_integration(mock_callback_query, mock_session):
    """Test the integration of DianaCompatibilityBridge with narrative admin."""
    # Create bridge instance
    bridge = DianaCompatibilityBridge(mock_session)
    
    # Set callback data to admin_fragments_manage
    mock_callback_query.data = "admin_fragments_manage"
    
    with patch.object(bridge.diana_system, 'handle_callback', AsyncMock()) as mock_handle_callback:
        # Call the handle_callback method
        result = await bridge.handle_callback(mock_callback_query)
        
        # Verify that it recognized and handled the callback
        assert result is True
        assert mock_handle_callback.called
        assert mock_handle_callback.call_args[0][0] == mock_callback_query
        
        # Verify that the original callback data was preserved
        assert mock_callback_query.data == "admin_fragments_manage"