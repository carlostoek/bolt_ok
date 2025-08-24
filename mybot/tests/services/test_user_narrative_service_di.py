import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from database.narrative_unified import UserNarrativeState, NarrativeFragment
from database.models import User, LorePiece
from services.interfaces import IUserNarrativeService, IRewardSystem
from services.user_narrative_service import UserNarrativeService


@pytest.fixture
def mock_reward_system():
    """Fixture para crear un mock del sistema de recompensas."""
    reward_system = AsyncMock(spec=IRewardSystem)
    return reward_system


@pytest.fixture
def mock_session():
    """Fixture para crear un mock de la sesión de base de datos."""
    session = AsyncMock(spec=AsyncSession)
    
    # Configurar comportamiento de execute
    session.execute.return_value = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = None
    
    return session


@pytest.fixture
def user_narrative_service(mock_session, mock_reward_system):
    """Fixture para crear una instancia del servicio de narrativa con DI."""
    return UserNarrativeService(session=mock_session, reward_system=mock_reward_system)


@pytest.mark.asyncio
async def test_get_or_create_user_state_new_user(user_narrative_service, mock_session):
    """Prueba la creación de un nuevo estado narrativo para un usuario."""
    # Configurar el mock para simular un usuario existente
    user_result_mock = MagicMock()
    user_result_mock.scalar_one_or_none.return_value = User(id=123)
    
    # Configurar retorno de execute para encontrar usuario pero no estado
    mock_session.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: None),  # No hay estado
        user_result_mock  # Hay usuario
    ]
    
    # Llamar al método
    result = await user_narrative_service.get_or_create_user_state(123)
    
    # Verificar que se creó un nuevo estado
    assert mock_session.add.called
    assert mock_session.commit.called
    assert isinstance(result, UserNarrativeState)
    assert result.user_id == 123


@pytest.mark.asyncio
async def test_unlock_clue(user_narrative_service, mock_session, mock_reward_system):
    """Prueba el desbloqueo de una pista."""
    # Configurar estado de usuario existente
    user_state = UserNarrativeState(
        user_id=123,
        unlocked_clues=[]
    )
    
    # Configurar pista existente
    clue = LorePiece(
        id=456,
        code_name="TEST_CLUE",
        is_active=True
    )
    
    # Configurar mocks para encontrar estado y pista
    mock_session.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: user_state),
        MagicMock(scalar_one_or_none=lambda: clue)
    ]
    
    # Llamar al método
    result = await user_narrative_service.unlock_clue(123, "TEST_CLUE")
    
    # Verificar que se desbloqueó la pista
    assert "TEST_CLUE" in result.unlocked_clues
    assert mock_session.commit.called


@pytest.mark.asyncio
async def test_mark_fragment_completed_with_triggers(user_narrative_service, mock_session, mock_reward_system):
    """Prueba completar un fragmento con triggers."""
    # Configurar estado de usuario existente
    user_state = UserNarrativeState(
        user_id=123,
        completed_fragments=[]
    )
    
    # Configurar fragmento con triggers
    fragment = NarrativeFragment(
        id="fragment1",
        title="Test Fragment",
        content="Test content",
        fragment_type="STORY",
        is_active=True,
        triggers={
            "reward_points": 10,
            "unlock_lore": "TEST_CLUE"
        }
    )
    
    # Configurar mocks para encontrar estado y fragmento
    mock_session.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: user_state),
        MagicMock(scalar_one_or_none=lambda: fragment)
    ]
    
    # Llamar al método
    result = await user_narrative_service.mark_fragment_completed(123, "fragment1")
    
    # Verificar que se completó el fragmento y se procesaron los triggers
    assert "fragment1" in result.completed_fragments
    assert mock_session.commit.called
    
    # Verificar que se llamó al sistema de recompensas para los triggers
    assert mock_reward_system.grant_reward.call_count == 2
    
    # Verificar llamada para los puntos
    points_call = mock_reward_system.grant_reward.call_args_list[0]
    assert points_call[1]["user_id"] == 123
    assert points_call[1]["reward_type"] == "points"
    assert points_call[1]["reward_data"]["amount"] == 10
    
    # Verificar llamada para la pista
    clue_call = mock_reward_system.grant_reward.call_args_list[1]
    assert clue_call[1]["user_id"] == 123
    assert clue_call[1]["reward_type"] == "clue"
    assert clue_call[1]["reward_data"]["clue_code"] == "TEST_CLUE"


@pytest.mark.asyncio
async def test_check_user_access(user_narrative_service, mock_session):
    """Prueba la verificación de acceso a un fragmento."""
    # Configurar estado de usuario con pistas desbloqueadas
    user_state = UserNarrativeState(
        user_id=123,
        unlocked_clues=["CLUE_A", "CLUE_B"]
    )
    
    # Configurar fragmento que requiere pistas
    fragment = NarrativeFragment(
        id="fragment1",
        title="Test Fragment",
        content="Test content",
        fragment_type="STORY",
        is_active=True,
        required_clues=["CLUE_A", "CLUE_C"]
    )
    
    # Configurar mocks para encontrar estado y fragmento
    mock_session.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: user_state),
        MagicMock(scalar_one_or_none=lambda: fragment)
    ]
    
    # Llamar al método
    result = await user_narrative_service.check_user_access(123, "fragment1")
    
    # Verificar que el acceso es denegado (falta CLUE_C)
    assert result is False