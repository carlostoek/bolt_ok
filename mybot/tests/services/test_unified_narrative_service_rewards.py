import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from services.unified_narrative_service import UnifiedNarrativeService
from database.narrative_unified import NarrativeFragment

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
def unified_narrative_service(mock_session):
    """Crea una instancia del servicio con una sesión mock."""
    return UnifiedNarrativeService(mock_session)

@pytest.mark.asyncio
async def test_process_fragment_triggers_with_points(unified_narrative_service, mock_session):
    """Test que verifica el procesamiento de triggers con recompensa de puntos."""
    # Crear un fragmento mock con triggers de puntos
    mock_fragment = MagicMock(spec=NarrativeFragment)
    mock_fragment.id = MOCK_FRAGMENT_ID
    mock_fragment.title = "Test Fragment"
    mock_fragment.triggers = {"reward_points": MOCK_POINTS}
    
    # Mockear el RewardSystem
    with patch('services.unified_narrative_service.RewardSystem') as mock_reward_system_class:
        mock_reward_system = AsyncMock()
        mock_reward_system_class.return_value = mock_reward_system
        
        # Llamar al método
        await unified_narrative_service._process_fragment_triggers(MOCK_USER_ID, mock_fragment)
        
        # Verificar que se llamó al sistema de recompensas
        mock_reward_system.grant_reward.assert_called_once_with(
            user_id=MOCK_USER_ID,
            reward_type='points',
            reward_data={
                'amount': MOCK_POINTS,
                'description': f'Recompensa por fragmento: {mock_fragment.title}'
            },
            source='unified_narrative_fragment'
        )

@pytest.mark.asyncio
async def test_process_fragment_triggers_with_clue(unified_narrative_service, mock_session):
    """Test que verifica el procesamiento de triggers con desbloqueo de pista."""
    # Crear un fragmento mock con triggers de pista
    mock_fragment = MagicMock(spec=NarrativeFragment)
    mock_fragment.id = MOCK_FRAGMENT_ID
    mock_fragment.title = "Test Fragment"
    mock_fragment.triggers = {"unlock_lore": MOCK_CLUE_CODE}
    
    # Mockear el RewardSystem
    with patch('services.unified_narrative_service.RewardSystem') as mock_reward_system_class:
        mock_reward_system = AsyncMock()
        mock_reward_system_class.return_value = mock_reward_system
        
        # Llamar al método
        await unified_narrative_service._process_fragment_triggers(MOCK_USER_ID, mock_fragment)
        
        # Verificar que se llamó al sistema de recompensas
        mock_reward_system.grant_reward.assert_called_once_with(
            user_id=MOCK_USER_ID,
            reward_type='clue',
            reward_data={
                'clue_code': MOCK_CLUE_CODE,
                'description': f'Pista desbloqueada por fragmento: {mock_fragment.title}'
            },
            source='unified_narrative_fragment'
        )

@pytest.mark.asyncio
async def test_process_fragment_triggers_with_both(unified_narrative_service, mock_session):
    """Test que verifica el procesamiento de triggers con ambos tipos de recompensa."""
    # Crear un fragmento mock con ambos tipos de triggers
    mock_fragment = MagicMock(spec=NarrativeFragment)
    mock_fragment.id = MOCK_FRAGMENT_ID
    mock_fragment.title = "Test Fragment"
    mock_fragment.triggers = {
        "reward_points": MOCK_POINTS,
        "unlock_lore": MOCK_CLUE_CODE
    }
    
    # Mockear el RewardSystem
    with patch('services.unified_narrative_service.RewardSystem') as mock_reward_system_class:
        mock_reward_system = AsyncMock()
        mock_reward_system_class.return_value = mock_reward_system
        
        # Llamar al método
        await unified_narrative_service._process_fragment_triggers(MOCK_USER_ID, mock_fragment)
        
        # Verificar que se llamó al sistema de recompensas dos veces
        assert mock_reward_system.grant_reward.call_count == 2
        
        # Verificar la llamada para puntos
        mock_reward_system.grant_reward.assert_any_call(
            user_id=MOCK_USER_ID,
            reward_type='points',
            reward_data={
                'amount': MOCK_POINTS,
                'description': f'Recompensa por fragmento: {mock_fragment.title}'
            },
            source='unified_narrative_fragment'
        )
        
        # Verificar la llamada para pista
        mock_reward_system.grant_reward.assert_any_call(
            user_id=MOCK_USER_ID,
            reward_type='clue',
            reward_data={
                'clue_code': MOCK_CLUE_CODE,
                'description': f'Pista desbloqueada por fragmento: {mock_fragment.title}'
            },
            source='unified_narrative_fragment'
        )