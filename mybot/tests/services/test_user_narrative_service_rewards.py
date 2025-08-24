import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_narrative_service import UserNarrativeService
from database.narrative_unified import UserNarrativeState, NarrativeFragment
from database.models import User, LorePiece

# Mock data
MOCK_USER_ID = 123456789
MOCK_FRAGMENT_ID = "fragment-uuid-1"
MOCK_POINTS = 100
MOCK_CLUE_CODE = "CLUE-001"

@pytest.fixture
def mock_session():
    """Crea una sesión mock para pruebas."""
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def user_narrative_service(mock_session):
    """Crea una instancia del servicio con una sesión mock."""
    return UserNarrativeService(mock_session)

@pytest.mark.asyncio
async def test_process_fragment_triggers_with_points(user_narrative_service, mock_session):
    """Test que verifica el procesamiento de triggers con recompensa de puntos."""
    # Configurar el mock para que encuentre el usuario
    mock_user = MagicMock(spec=User)
    mock_user.id = MOCK_USER_ID
    mock_user_result = AsyncMock()
    mock_user_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_user_result
    
    # Crear un fragmento mock con triggers de puntos
    mock_fragment = MagicMock(spec=NarrativeFragment)
    mock_fragment.id = MOCK_FRAGMENT_ID
    mock_fragment.title = "Test Fragment"
    mock_fragment.triggers = {"reward_points": MOCK_POINTS}
    
    # Mockear el RewardSystem
    with patch('services.user_narrative_service.RewardSystem') as mock_reward_system_class:
        mock_reward_system = AsyncMock()
        mock_reward_system_class.return_value = mock_reward_system
        
        # Llamar al método
        await user_narrative_service._process_fragment_triggers(MOCK_USER_ID, mock_fragment)
        
        # Verificar que se llamó al sistema de recompensas
        mock_reward_system.grant_reward.assert_called_once_with(
            user_id=MOCK_USER_ID,
            reward_type='points',
            reward_data={
                'amount': MOCK_POINTS,
                'description': f'Recompensa por completar fragmento: {mock_fragment.title}'
            },
            source='narrative_fragment'
        )

@pytest.mark.asyncio
async def test_process_fragment_triggers_with_clue(user_narrative_service, mock_session):
    """Test que verifica el procesamiento de triggers con desbloqueo de pista."""
    # Configurar el mock para que encuentre el usuario
    mock_user = MagicMock(spec=User)
    mock_user.id = MOCK_USER_ID
    mock_user_result = AsyncMock()
    mock_user_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_user_result
    
    # Crear un fragmento mock con triggers de pista
    mock_fragment = MagicMock(spec=NarrativeFragment)
    mock_fragment.id = MOCK_FRAGMENT_ID
    mock_fragment.title = "Test Fragment"
    mock_fragment.triggers = {"unlock_lore": MOCK_CLUE_CODE}
    
    # Mockear el RewardSystem
    with patch('services.user_narrative_service.RewardSystem') as mock_reward_system_class:
        mock_reward_system = AsyncMock()
        mock_reward_system_class.return_value = mock_reward_system
        
        # Llamar al método
        await user_narrative_service._process_fragment_triggers(MOCK_USER_ID, mock_fragment)
        
        # Verificar que se llamó al sistema de recompensas
        mock_reward_system.grant_reward.assert_called_once_with(
            user_id=MOCK_USER_ID,
            reward_type='clue',
            reward_data={
                'clue_code': MOCK_CLUE_CODE,
                'description': f'Pista desbloqueada por completar fragmento: {mock_fragment.title}'
            },
            source='narrative_fragment'
        )

@pytest.mark.asyncio
async def test_process_fragment_triggers_with_both(user_narrative_service, mock_session):
    """Test que verifica el procesamiento de triggers con ambos tipos de recompensa."""
    # Configurar el mock para que encuentre el usuario
    mock_user = MagicMock(spec=User)
    mock_user.id = MOCK_USER_ID
    mock_user_result = AsyncMock()
    mock_user_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_user_result
    
    # Crear un fragmento mock con ambos tipos de triggers
    mock_fragment = MagicMock(spec=NarrativeFragment)
    mock_fragment.id = MOCK_FRAGMENT_ID
    mock_fragment.title = "Test Fragment"
    mock_fragment.triggers = {
        "reward_points": MOCK_POINTS,
        "unlock_lore": MOCK_CLUE_CODE
    }
    
    # Mockear el RewardSystem
    with patch('services.user_narrative_service.RewardSystem') as mock_reward_system_class:
        mock_reward_system = AsyncMock()
        mock_reward_system_class.return_value = mock_reward_system
        
        # Llamar al método
        await user_narrative_service._process_fragment_triggers(MOCK_USER_ID, mock_fragment)
        
        # Verificar que se llamó al sistema de recompensas dos veces
        assert mock_reward_system.grant_reward.call_count == 2
        
        # Verificar la llamada para puntos
        mock_reward_system.grant_reward.assert_any_call(
            user_id=MOCK_USER_ID,
            reward_type='points',
            reward_data={
                'amount': MOCK_POINTS,
                'description': f'Recompensa por completar fragmento: {mock_fragment.title}'
            },
            source='narrative_fragment'
        )
        
        # Verificar la llamada para pista
        mock_reward_system.grant_reward.assert_any_call(
            user_id=MOCK_USER_ID,
            reward_type='clue',
            reward_data={
                'clue_code': MOCK_CLUE_CODE,
                'description': f'Pista desbloqueada por completar fragmento: {mock_fragment.title}'
            },
            source='narrative_fragment'
        )