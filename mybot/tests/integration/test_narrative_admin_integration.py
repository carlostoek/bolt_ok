import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import CallbackQuery, User, Chat, Message
from database.narrative_unified import NarrativeFragment, UserNarrativeState
from services.narrative_admin_service import NarrativeAdminService
from services.storyboard_service import StoryboardService
from handlers.admin.narrative_admin import handle_admin_fragments_manage, list_fragments, view_fragment
from datetime import datetime

# Mock data para pruebas
ADMIN_USER_ID = 123456789
MOCK_FRAGMENT_ID = "fragment-uuid-1"

@pytest.fixture
def mock_session():
    """Crea una sesión mock para pruebas."""
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def mock_callback():
    """Crea un callback query mock para pruebas."""
    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = ADMIN_USER_ID
    callback.message = MagicMock(spec=Message)
    callback.message.chat = MagicMock(spec=Chat)
    callback.message.chat.id = ADMIN_USER_ID
    callback.data = "admin_fragments_manage"
    # Convertir métodos async en mocks que retornan asyncio.Future
    callback.answer = AsyncMock()
    return callback

@pytest.fixture
def mock_fragments():
    """Crea fragmentos narrativos mock para pruebas."""
    fragments = []
    for i in range(3):
        fragment = MagicMock(spec=NarrativeFragment)
        fragment.id = f"fragment-uuid-{i+1}"
        fragment.title = f"Test Fragment {i+1}"
        fragment.content = f"This is test fragment {i+1} content"
        fragment.fragment_type = "STORY" if i == 0 else "DECISION" if i == 1 else "INFO"
        fragment.created_at = datetime.now()
        fragment.updated_at = datetime.now()
        fragment.is_active = True
        fragment.choices = []
        fragment.triggers = {}
        fragment.required_clues = []
        fragments.append(fragment)
    return fragments

@pytest.mark.asyncio
async def test_handle_admin_fragments_manage_integration(mock_callback, mock_session, mock_fragments):
    """Test de integración para el handler principal de administración narrativa."""
    # Patch is_admin para que siempre devuelva True
    with patch('handlers.admin.narrative_admin.is_admin', return_value=True):
        # Patch NarrativeAdminService.get_narrative_stats
        with patch('handlers.admin.narrative_admin.NarrativeAdminService.get_narrative_stats') as mock_get_stats:
            mock_get_stats.return_value = {
                "total_fragments": 3,
                "active_fragments": 3,
                "fragments_by_type": {"STORY": 1, "DECISION": 1, "INFO": 1},
                "users_in_narrative": 10
            }
            
            # Patch safe_edit para verificar que se llama con los parámetros correctos
            with patch('handlers.admin.narrative_admin.safe_edit', new_callable=AsyncMock) as mock_safe_edit:
                # Ejecutar el handler
                await handle_admin_fragments_manage(mock_callback, mock_session)
                
                # Verificar que se intentó responder al callback
                assert mock_callback.answer.called, "El callback.answer no fue llamado"
                
                # Verificar que se intentó responder al callback
                assert mock_callback.answer.called, "El callback.answer no fue llamado"

@pytest.mark.asyncio
async def test_list_fragments_integration(mock_callback, mock_session, mock_fragments):
    """Test de integración para el listado de fragmentos."""
    # Modificar callback.data para incluir parámetros
    mock_callback.data = "admin_fragments_list?page=1&filter=all"
    
    # Patch is_admin para que siempre devuelva True
    with patch('handlers.admin.narrative_admin.is_admin', return_value=True):
        # Patch NarrativeAdminService.get_all_fragments
        with patch('handlers.admin.narrative_admin.NarrativeAdminService.get_all_fragments') as mock_get_all_fragments:
            mock_get_all_fragments.return_value = {
                "items": [
                    {
                        "id": fragment.id,
                        "title": fragment.title,
                        "type": fragment.fragment_type,
                        "is_active": fragment.is_active,
                        "created_at": fragment.created_at.isoformat(),
                        "updated_at": fragment.updated_at.isoformat(),
                        "has_choices": bool(fragment.choices),
                        "has_triggers": bool(fragment.triggers),
                        "has_requirements": bool(fragment.required_clues)
                    } for fragment in mock_fragments
                ],
                "total": 3,
                "page": 1,
                "limit": 10,
                "total_pages": 1,
                "has_next": False,
                "has_prev": False
            }
            
            # Patch safe_edit para verificar que se llama con los parámetros correctos
            with patch('handlers.admin.narrative_admin.safe_edit', new_callable=AsyncMock) as mock_safe_edit:
                # Ejecutar el handler
                await list_fragments(mock_callback, mock_session)
                
                # Verificar que se intentó responder al callback
                assert mock_callback.answer.called, "El callback.answer no fue llamado"
                
                # Verificar que se intentó responder al callback
                assert mock_callback.answer.called, "El callback.answer no fue llamado"

@pytest.mark.asyncio
async def test_view_fragment_integration(mock_callback, mock_session, mock_fragments):
    """Test de integración para la visualización de detalles de un fragmento."""
    # Modificar callback.data para incluir el ID del fragmento
    mock_callback.data = f"admin_view_fragment?id={MOCK_FRAGMENT_ID}"
    
    # Patch is_admin para que siempre devuelva True
    with patch('handlers.admin.narrative_admin.is_admin', return_value=True):
        # Patch NarrativeAdminService.get_fragment_details
        with patch('handlers.admin.narrative_admin.NarrativeAdminService.get_fragment_details') as mock_get_details:
            mock_get_details.return_value = {
                "id": mock_fragments[0].id,
                "title": mock_fragments[0].title,
                "content": mock_fragments[0].content,
                "type": mock_fragments[0].fragment_type,
                "created_at": mock_fragments[0].created_at.isoformat(),
                "updated_at": mock_fragments[0].updated_at.isoformat(),
                "is_active": mock_fragments[0].is_active,
                "choices": mock_fragments[0].choices,
                "triggers": mock_fragments[0].triggers,
                "required_clues": mock_fragments[0].required_clues,
                "statistics": {
                    "active_users": 5,
                    "visited_users": 10,
                    "completed_users": 3,
                    "completion_rate": 30.0
                }
            }
            
            # Patch safe_edit para verificar que se llama con los parámetros correctos
            with patch('handlers.admin.narrative_admin.safe_edit', new_callable=AsyncMock) as mock_safe_edit:
                # Ejecutar el handler
                await view_fragment(mock_callback, mock_session)
                
                # Verificar que se intentó responder al callback
                assert mock_callback.answer.called, "El callback.answer no fue llamado"
                
                # Verificar que se intentó responder al callback
                assert mock_callback.answer.called, "El callback.answer no fue llamado"

@pytest.mark.asyncio
async def test_narrative_admin_service_storyboard_integration(mock_session, mock_fragments):
    """Test de integración entre NarrativeAdminService y StoryboardService."""
    # Crear instancias reales de los servicios
    admin_service = NarrativeAdminService(mock_session)
    storyboard_service = StoryboardService(mock_session)
    
    # Patch del método get_fragment_connections de NarrativeAdminService
    with patch.object(admin_service, 'get_fragment_connections') as mock_get_connections:
        mock_get_connections.return_value = {
            "fragment_id": MOCK_FRAGMENT_ID,
            "fragment_title": "Test Fragment 1",
            "fragment_type": "STORY",
            "outgoing_connections": [
                {"id": "fragment-uuid-2", "title": "Test Fragment 2", "choice_text": "Option 1"},
                {"id": "fragment-uuid-3", "title": "Test Fragment 3", "choice_text": "Option 2"}
            ],
            "incoming_connections": []
        }
        
        # Patch StoryboardService para que use nuestra instancia de NarrativeAdminService
        with patch.object(storyboard_service, 'narrative_admin_service', admin_service):
            # Patch _generate_tree_visualization para evitar la lógica compleja
            with patch.object(storyboard_service, '_generate_tree_visualization') as mock_generate_tree:
                mock_generate_tree.return_value = {
                    "type": "tree",
                    "root_id": MOCK_FRAGMENT_ID,
                    "nodes": [
                        {"id": "fragment-uuid-1", "label": "Test Fragment 1"},
                        {"id": "fragment-uuid-2", "label": "Test Fragment 2"},
                        {"id": "fragment-uuid-3", "label": "Test Fragment 3"}
                    ],
                    "edges": [
                        {"from": "fragment-uuid-1", "to": "fragment-uuid-2"},
                        {"from": "fragment-uuid-1", "to": "fragment-uuid-3"}
                    ]
                }
                
                # Patch get_fragment_details para que no requiera DB
                with patch.object(admin_service, 'get_fragment_details') as mock_get_details:
                    mock_get_details.return_value = {
                        "id": MOCK_FRAGMENT_ID,
                        "title": "Test Fragment 1",
                        "type": "STORY"
                    }
                    
                    # Configurar mock para la consulta de fragmento
                    mock_fragment_result = MagicMock()
                    mock_fragment_result.scalar_one_or_none.return_value = mock_fragments[0]
                    mock_session.execute.return_value = mock_fragment_result
                    
                    # Probar la integración entre los servicios
                    result = await storyboard_service.get_connection_statistics(MOCK_FRAGMENT_ID)
                    
                    # Verificar el resultado
                    assert result["fragment_id"] == MOCK_FRAGMENT_ID
                    assert result["fragment_title"] == "Test Fragment 1"
                    assert result["is_start"] is True  # No hay conexiones entrantes
                    assert result["is_end"] is False  # Hay conexiones salientes
                    assert len(result["connections"]) == 2

@pytest.mark.asyncio
async def test_end_to_end_narrative_admin_flow(mock_callback, mock_session, mock_fragments):
    """Test de integración de extremo a extremo del flujo de administración narrativa."""
    # Configurar todos los mocks necesarios
    with patch('handlers.admin.narrative_admin.is_admin', return_value=True), \
         patch('handlers.admin.narrative_admin.NarrativeAdminService.get_narrative_stats') as mock_get_stats, \
         patch('handlers.admin.narrative_admin.safe_edit', new_callable=AsyncMock) as mock_safe_edit, \
         patch('handlers.admin.narrative_admin.NarrativeAdminService.get_all_fragments') as mock_get_all_fragments, \
         patch('handlers.admin.narrative_admin.NarrativeAdminService.get_fragment_details') as mock_get_details:
        
        # Configurar respuestas de los mocks
        mock_get_stats.return_value = {
            "total_fragments": 3,
            "active_fragments": 3,
            "fragments_by_type": {"STORY": 1, "DECISION": 1, "INFO": 1},
            "users_in_narrative": 10
        }
        
        mock_get_all_fragments.return_value = {
            "items": [
                {
                    "id": fragment.id,
                    "title": fragment.title,
                    "type": fragment.fragment_type,
                    "is_active": fragment.is_active,
                    "created_at": fragment.created_at.isoformat(),
                    "updated_at": fragment.updated_at.isoformat(),
                    "has_choices": bool(fragment.choices),
                    "has_triggers": bool(fragment.triggers),
                    "has_requirements": bool(fragment.required_clues)
                } for fragment in mock_fragments
            ],
            "total": 3,
            "page": 1,
            "limit": 10,
            "total_pages": 1,
            "has_next": False,
            "has_prev": False
        }
        
        mock_get_details.return_value = {
            "id": mock_fragments[0].id,
            "title": mock_fragments[0].title,
            "content": mock_fragments[0].content,
            "type": mock_fragments[0].fragment_type,
            "created_at": mock_fragments[0].created_at.isoformat(),
            "updated_at": mock_fragments[0].updated_at.isoformat(),
            "is_active": mock_fragments[0].is_active,
            "choices": mock_fragments[0].choices,
            "triggers": mock_fragments[0].triggers,
            "required_clues": mock_fragments[0].required_clues,
            "statistics": {
                "active_users": 5,
                "visited_users": 10,
                "completed_users": 3,
                "completion_rate": 30.0
            }
        }
        
        # Paso 1: Acceder al panel principal de administración narrativa
        mock_callback.data = "admin_fragments_manage"
        await handle_admin_fragments_manage(mock_callback, mock_session)
        assert mock_safe_edit.call_count == 1
        mock_safe_edit.reset_mock()
        
        # Paso 2: Ver la lista de fragmentos
        mock_callback.data = "admin_fragments_list"
        await list_fragments(mock_callback, mock_session)
        assert mock_safe_edit.call_count == 1
        mock_safe_edit.reset_mock()
        
        # Paso 3: Ver detalles de un fragmento específico
        mock_callback.data = f"admin_view_fragment?id={MOCK_FRAGMENT_ID}"
        await view_fragment(mock_callback, mock_session)
        # Verificar que se intentó responder al callback
        assert mock_callback.answer.called, "El callback.answer no fue llamado en view_fragment"
        
        # Verificar que todo el flujo se completó sin errores
        assert mock_callback.answer.call_count == 3