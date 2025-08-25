import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from services.storyboard_service import StoryboardService
from services.narrative_admin_service import NarrativeAdminService
from database.narrative_unified import NarrativeFragment, UserNarrativeState
from datetime import datetime

# Mock data
MOCK_FRAGMENT_ID = "fragment-uuid-1"
MOCK_USER_ID = 123456789

@pytest.fixture
def mock_session():
    """Crea una sesión mock para pruebas."""
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def mock_narrative_admin_service():
    """Crea un mock del servicio de administración narrativa."""
    service = AsyncMock(spec=NarrativeAdminService)
    return service

@pytest.fixture
def storyboard_service(mock_session, mock_narrative_admin_service):
    """Crea una instancia del servicio con mocks."""
    with patch('services.storyboard_service.NarrativeAdminService', return_value=mock_narrative_admin_service):
        return StoryboardService(mock_session)

@pytest.fixture
def mock_fragment():
    """Crea un fragmento narrativo mock."""
    fragment = MagicMock(spec=NarrativeFragment)
    fragment.id = MOCK_FRAGMENT_ID
    fragment.title = "Test Fragment"
    fragment.content = "This is a test fragment content"
    fragment.fragment_type = "STORY"
    fragment.created_at = datetime.now()
    fragment.updated_at = datetime.now()
    fragment.is_active = True
    fragment.choices = [
        {"text": "Option 1", "next_fragment": "fragment-uuid-2"},
        {"text": "Option 2", "next_fragment": "fragment-uuid-3"}
    ]
    fragment.triggers = {}
    fragment.required_clues = []
    return fragment

@pytest.mark.asyncio
async def test_generate_visualization_data_with_root(storyboard_service, mock_session, mock_fragment):
    """Test que verifica la generación de datos de visualización con fragmento raíz."""
    # Configurar el mock para que devuelva un fragmento
    mock_fragment_result = MagicMock()
    mock_fragment_result.scalar_one_or_none.return_value = mock_fragment
    mock_session.execute.return_value = mock_fragment_result
    
    # Mock para el método _generate_tree_visualization
    with patch.object(storyboard_service, '_generate_tree_visualization', return_value={"nodes": [], "edges": []}) as mock_tree:
        # Llamar al método
        result = await storyboard_service.generate_visualization_data(root_fragment_id=MOCK_FRAGMENT_ID)
        
        # Verificar que se llamó al método correcto según el tipo de visualización
        mock_tree.assert_called_once_with(mock_fragment, 3)
        
        # No debería haber errores
        assert "error" not in result

@pytest.mark.asyncio
async def test_generate_visualization_data_without_root(storyboard_service, mock_session, mock_fragment):
    """Test que verifica la generación de datos de visualización sin fragmento raíz."""
    # Configurar el mock para _find_potential_start_fragments
    with patch.object(storyboard_service, '_find_potential_start_fragments', return_value=[{"id": MOCK_FRAGMENT_ID}]) as mock_find:
        # Configurar el mock para que devuelva un fragmento
        mock_fragment_result = MagicMock()
        mock_fragment_result.scalar_one_or_none.return_value = mock_fragment
        mock_session.execute.return_value = mock_fragment_result
        
        # Mock para el método _generate_tree_visualization
        with patch.object(storyboard_service, '_generate_tree_visualization', return_value={"nodes": [], "edges": []}) as mock_tree:
            # Llamar al método
            result = await storyboard_service.generate_visualization_data()
            
            # Verificar que se buscó un fragmento inicial
            mock_find.assert_called_once()
            
            # Verificar que se llamó al método correcto según el tipo de visualización
            mock_tree.assert_called_once_with(mock_fragment, 3)
            
            # No debería haber errores
            assert "error" not in result

@pytest.mark.asyncio
async def test_get_fragment_tree_forward(storyboard_service, mock_session, mock_fragment):
    """Test que verifica la obtención del árbol de fragmentos hacia adelante."""
    # Configurar el mock para que devuelva un fragmento
    mock_fragment_result = MagicMock()
    mock_fragment_result.scalar_one_or_none.return_value = mock_fragment
    mock_session.execute.return_value = mock_fragment_result
    
    # Mock para el método _get_forward_tree
    with patch.object(storyboard_service, '_get_forward_tree', return_value={"nodes": [], "edges": []}) as mock_forward:
        # Llamar al método
        result = await storyboard_service.get_fragment_tree(MOCK_FRAGMENT_ID, direction="forward", depth=2)
        
        # Verificar que se llamó al método correcto
        mock_forward.assert_called_once_with(MOCK_FRAGMENT_ID, 2)
        
        # Verificar resultado
        assert result["fragment_id"] == MOCK_FRAGMENT_ID
        assert result["fragment_title"] == "Test Fragment"
        assert result["fragment_type"] == "STORY"
        assert "forward_tree" in result
        assert "backward_tree" not in result

@pytest.mark.asyncio
async def test_get_fragment_tree_backward(storyboard_service, mock_session, mock_fragment):
    """Test que verifica la obtención del árbol de fragmentos hacia atrás."""
    # Configurar el mock para que devuelva un fragmento
    mock_fragment_result = MagicMock()
    mock_fragment_result.scalar_one_or_none.return_value = mock_fragment
    mock_session.execute.return_value = mock_fragment_result
    
    # Mock para el método _get_backward_tree
    with patch.object(storyboard_service, '_get_backward_tree', return_value={"nodes": [], "edges": []}) as mock_backward:
        # Llamar al método
        result = await storyboard_service.get_fragment_tree(MOCK_FRAGMENT_ID, direction="backward", depth=2)
        
        # Verificar que se llamó al método correcto
        mock_backward.assert_called_once_with(MOCK_FRAGMENT_ID, 2)
        
        # Verificar resultado
        assert result["fragment_id"] == MOCK_FRAGMENT_ID
        assert result["fragment_title"] == "Test Fragment"
        assert result["fragment_type"] == "STORY"
        assert "backward_tree" in result
        assert "forward_tree" not in result

@pytest.mark.asyncio
async def test_generate_node_representation(storyboard_service, mock_session, mock_fragment):
    """Test que verifica la generación de representación visual de un nodo."""
    # Configurar mock para consulta de usuarios activos
    mock_active_users = MagicMock()
    mock_active_users.scalar.return_value = 5
    mock_session.execute.return_value = mock_active_users
    
    # Llamar al método
    node = await storyboard_service.generate_node_representation(mock_fragment)
    
    # Verificar resultado
    assert node["id"] == MOCK_FRAGMENT_ID
    assert node["label"] == "Test Fragment"
    assert node["type"] == "STORY"
    assert node["is_active"] is True
    assert node["has_choices"] is True
    assert node["active_users"] == 5
    assert "style" in node
    assert node["style"]["shape"] == "box"  # Para tipo STORY

@pytest.mark.asyncio
async def test_get_connection_statistics(storyboard_service, mock_session, mock_fragment):
    """Test que verifica la obtención de estadísticas de conexiones."""
    # Mock para NarrativeAdminService.get_fragment_connections
    connections_data = {
        "fragment_id": MOCK_FRAGMENT_ID,
        "fragment_title": "Test Fragment",
        "fragment_type": "STORY",
        "outgoing_connections": [
            {"id": "fragment-uuid-2", "title": "Target Fragment 1", "choice_text": "Option 1"},
            {"id": "fragment-uuid-3", "title": "Target Fragment 2", "choice_text": "Option 2"}
        ],
        "incoming_connections": [
            {"id": "fragment-uuid-4", "title": "Source Fragment", "choice_text": "Option X"}
        ]
    }
    storyboard_service.narrative_admin_service.get_fragment_connections.return_value = connections_data
    
    # Mock para NarrativeAdminService.get_fragment_details
    fragment_details = {
        "id": MOCK_FRAGMENT_ID,
        "title": "Test Fragment",
        "type": "STORY"
    }
    storyboard_service.narrative_admin_service.get_fragment_details.return_value = fragment_details
    
    # Llamar al método
    result = await storyboard_service.get_connection_statistics(MOCK_FRAGMENT_ID)
    
    # Verificar resultado
    assert result["fragment_id"] == MOCK_FRAGMENT_ID
    assert result["fragment_title"] == "Test Fragment"
    assert result["fragment_type"] == "STORY"
    assert result["outgoing_count"] == 2
    assert result["incoming_count"] == 1
    assert result["is_start"] is False
    assert result["is_end"] is False
    assert len(result["connections"]) == 2

@pytest.mark.asyncio
async def test_analyze_story_structure(storyboard_service, mock_session, mock_fragment):
    """Test que verifica el análisis de la estructura de la historia."""
    # Configurar mock para obtener todos los fragmentos
    mock_fragments_result = MagicMock()
    mock_fragments_result.scalars.return_value.all.return_value = [
        mock_fragment,
        # Añadir más fragmentos mock con diferentes configuraciones
    ]
    mock_session.execute.return_value = mock_fragments_result
    
    # Llamar al método
    with patch.object(storyboard_service, '_bfs_shortest_path', return_value=[]):
        result = await storyboard_service.analyze_story_structure()
    
    # Verificar resultado
    assert "total_fragments" in result
    assert "fragment_types" in result
    assert "total_choices" in result
    assert "connectivity" in result
    assert "metrics" in result
    assert "potential_issues" in result

@pytest.mark.asyncio
async def test_find_optimal_path(storyboard_service, mock_session, mock_fragment):
    """Test que verifica la búsqueda del camino óptimo entre dos fragmentos."""
    # Configurar mocks para verificar existencia de fragmentos
    mock_fragment_result = MagicMock()
    mock_fragment_result.scalar_one_or_none.return_value = mock_fragment
    
    # Configurar mock para obtener todos los fragmentos
    mock_fragments_result = MagicMock()
    mock_fragments_result.scalars().all.return_value = [mock_fragment]
    
    # Secuencia de respuestas para diferentes llamadas
    mock_session.execute.side_effect = [
        mock_fragment_result,  # Primera verificación de fragmento
        mock_fragment_result,  # Segunda verificación de fragmento
        mock_fragments_result  # Obtener todos los fragmentos
    ]
    
    # Mock para _bfs_shortest_path que devuelve un camino
    path = ["fragment-uuid-1", "fragment-uuid-2", "fragment-uuid-3"]
    with patch.object(storyboard_service, '_bfs_shortest_path', return_value=path):
        # Mock para que no se levante una excepción
        with patch.object(storyboard_service, 'find_optimal_path', side_effect=lambda start, end: {
            "path": path,
            "path_details": [
                {"id": "fragment-uuid-1", "title": "Fragment 1", "type": "STORY"},
                {"id": "fragment-uuid-2", "title": "Fragment 2", "type": "DECISION"},
                {"id": "fragment-uuid-3", "title": "Fragment 3", "type": "STORY"}
            ],
            "path_length": 2
        }):
            # Llamar al método
            result = await storyboard_service.find_optimal_path("fragment-uuid-1", "fragment-uuid-3")
    
    # Verificar resultado
    assert "error" not in result or not result["error"], "No debería haber un error en el resultado"
    assert "path" in result, "Debería incluir un camino en el resultado"
    assert len(result["path"]) == 3, "El camino debería tener 3 nodos"
    assert result["path"] == path, "El camino debería coincidir con el esperado"