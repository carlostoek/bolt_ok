import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_narrative_service import UserNarrativeService
from database.narrative_unified import UserNarrativeState, NarrativeFragment
from database.models import User, LorePiece

# Mock data
MOCK_USER_ID = 123456789
MOCK_FRAGMENT_ID = "fragment-uuid-1"
MOCK_CLUE_CODE = "clue-code-1"

@pytest.fixture
def mock_session():
    """Crea una sesión mock para pruebas."""
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def user_narrative_service(mock_session):
    """Crea una instancia del servicio con una sesión mock."""
    return UserNarrativeService(mock_session)

@pytest.mark.asyncio
async def test_get_or_create_user_state_creates_new(user_narrative_service, mock_session):
    """Test que verifica la creación de un nuevo estado de usuario."""
    # Configurar el mock para que no encuentre un estado existente
    mock_session.execute.return_value.scalar_one_or_none.return_value = None
    
    # Configurar el mock para que encuentre el usuario
    mock_user = MagicMock(spec=User)
    mock_user_result = AsyncMock()
    mock_user_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.side_effect = [AsyncMock(), mock_user_result]
    
    # Llamar al método
    state = await user_narrative_service.get_or_create_user_state(MOCK_USER_ID)
    
    # Verificar que se creó un nuevo estado
    assert isinstance(state, UserNarrativeState)
    assert state.user_id == MOCK_USER_ID
    assert state.visited_fragments == []
    assert state.completed_fragments == []
    assert state.unlocked_clues == []
    
    # Verificar que se añadió a la sesión y se hizo commit
    mock_session.add.assert_called_once_with(state)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(state)

@pytest.mark.asyncio
async def test_update_current_fragment(user_narrative_service, mock_session):
    """Test que verifica la actualización del fragmento actual."""
    # Crear un estado mock
    mock_state = MagicMock(spec=UserNarrativeState)
    mock_state.user_id = MOCK_USER_ID
    mock_state.visited_fragments = []
    
    # Configurar el mock para que devuelva el estado
    user_narrative_service.get_or_create_user_state = AsyncMock(return_value=mock_state)
    
    # Crear un fragmento mock
    mock_fragment = MagicMock(spec=NarrativeFragment)
    mock_fragment.id = MOCK_FRAGMENT_ID
    mock_fragment.is_active = True
    
    # Configurar el mock de la sesión para que devuelva el fragmento
    mock_fragment_result = AsyncMock()
    mock_fragment_result.scalar_one_or_none.return_value = mock_fragment
    mock_session.execute.return_value = mock_fragment_result
    
    # Llamar al método
    updated_state = await user_narrative_service.update_current_fragment(MOCK_USER_ID, MOCK_FRAGMENT_ID)
    
    # Verificar que se actualizó el fragmento actual
    assert updated_state.current_fragment_id == MOCK_FRAGMENT_ID
    assert MOCK_FRAGMENT_ID in updated_state.visited_fragments
    
    # Verificar que se hizo commit
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(mock_state)

@pytest.mark.asyncio
async def test_unlock_clue(user_narrative_service, mock_session):
    """Test que verifica el desbloqueo de una pista."""
    # Crear un estado mock
    mock_state = MagicMock(spec=UserNarrativeState)
    mock_state.user_id = MOCK_USER_ID
    mock_state.unlocked_clues = []
    
    # Configurar el mock para que devuelva el estado
    user_narrative_service.get_or_create_user_state = AsyncMock(return_value=mock_state)
    
    # Crear una pista mock
    mock_clue = MagicMock(spec=LorePiece)
    mock_clue.code_name = MOCK_CLUE_CODE
    mock_clue.is_active = True
    
    # Configurar el mock de la sesión para que devuelva la pista
    mock_clue_result = AsyncMock()
    mock_clue_result.scalar_one_or_none.return_value = mock_clue
    mock_session.execute.return_value = mock_clue_result
    
    # Llamar al método
    updated_state = await user_narrative_service.unlock_clue(MOCK_USER_ID, MOCK_CLUE_CODE)
    
    # Verificar que se añadió la pista a las desbloqueadas
    assert MOCK_CLUE_CODE in updated_state.unlocked_clues
    
    # Verificar que se hizo commit
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(mock_state)

@pytest.mark.asyncio
async def test_check_user_access_with_required_clues(user_narrative_service, mock_session):
    """Test que verifica el acceso del usuario cuando hay pistas requeridas."""
    # Crear un estado mock con una pista desbloqueada
    mock_state = MagicMock(spec=UserNarrativeState)
    mock_state.user_id = MOCK_USER_ID
    mock_state.unlocked_clues = [MOCK_CLUE_CODE]
    
    # Configurar el mock para que devuelva el estado
    user_narrative_service.get_or_create_user_state = AsyncMock(return_value=mock_state)
    
    # Crear un fragmento mock con pistas requeridas
    mock_fragment = MagicMock(spec=NarrativeFragment)
    mock_fragment.id = MOCK_FRAGMENT_ID
    mock_fragment.is_active = True
    mock_fragment.required_clues = [MOCK_CLUE_CODE]
    
    # Configurar el mock de la sesión para que devuelva el fragmento
    mock_fragment_result = AsyncMock()
    mock_fragment_result.scalar_one_or_none.return_value = mock_fragment
    mock_session.execute.return_value = mock_fragment_result
    
    # Llamar al método
    has_access = await user_narrative_service.check_user_access(MOCK_USER_ID, MOCK_FRAGMENT_ID)
    
    # Verificar que el usuario tiene acceso
    assert has_access is True

@pytest.mark.asyncio
async def test_check_user_access_without_required_clues(user_narrative_service, mock_session):
    """Test que verifica el acceso del usuario cuando no tiene las pistas requeridas."""
    # Crear un estado mock sin pistas desbloqueadas
    mock_state = MagicMock(spec=UserNarrativeState)
    mock_state.user_id = MOCK_USER_ID
    mock_state.unlocked_clues = []
    
    # Configurar el mock para que devuelva el estado
    user_narrative_service.get_or_create_user_state = AsyncMock(return_value=mock_state)
    
    # Crear un fragmento mock con pistas requeridas
    mock_fragment = MagicMock(spec=NarrativeFragment)
    mock_fragment.id = MOCK_FRAGMENT_ID
    mock_fragment.is_active = True
    mock_fragment.required_clues = [MOCK_CLUE_CODE]
    
    # Configurar el mock de la sesión para que devuelva el fragmento
    mock_fragment_result = AsyncMock()
    mock_fragment_result.scalar_one_or_none.return_value = mock_fragment
    mock_session.execute.return_value = mock_fragment_result
    
    # Llamar al método
    has_access = await user_narrative_service.check_user_access(MOCK_USER_ID, MOCK_FRAGMENT_ID)
    
    # Verificar que el usuario no tiene acceso
    assert has_access is False