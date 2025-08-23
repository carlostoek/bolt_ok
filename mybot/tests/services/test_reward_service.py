import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from services.reward_service import RewardSystem
from database.models import User, LorePiece, UserLorePiece
from database.transaction_models import RewardLog

# Mock data
MOCK_USER_ID = 123456789
MOCK_CLUE_CODE = "CLUE-001"
MOCK_ACHIEVEMENT_ID = "ACHIEVEMENT-001"

@pytest.fixture
def mock_session():
    """Crea una sesión mock para pruebas."""
    return AsyncMock(spec=AsyncSession)

@pytest.fixture
def reward_system(mock_session):
    """Crea una instancia del sistema de recompensas con una sesión mock."""
    return RewardSystem(mock_session)

@pytest.mark.asyncio
async def test_grant_points_reward(reward_system, mock_session):
    """Test que verifica la concesión de recompensa de puntos."""
    # Configurar el mock para que encuentre el usuario
    mock_user = MagicMock(spec=User)
    mock_user.id = MOCK_USER_ID
    mock_user_result = AsyncMock()
    mock_user_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_user_result
    
    # Configurar el mock de PointService
    with pytest.MonkeyPatch().context() as m:
        mock_point_service = AsyncMock()
        m.setattr('services.reward_service.PointService', lambda session: mock_point_service)
        
        # Llamar al método
        await reward_system.grant_reward(
            user_id=MOCK_USER_ID,
            reward_type='points',
            reward_data={'amount': 100, 'description': 'Test reward'},
            source='test'
        )
        
        # Verificar que se llamó a PointService.add_points
        mock_point_service.add_points.assert_called_once_with(
            user_id=MOCK_USER_ID,
            points=100,
            source='test',
            description='Test reward'
        )
        
        # Verificar que se registró en el log de recompensas
        mock_session.add.assert_called_once()
        reward_log = mock_session.add.call_args[0][0]
        assert isinstance(reward_log, RewardLog)
        assert reward_log.user_id == MOCK_USER_ID
        assert reward_log.reward_type == 'points'
        assert reward_log.reward_data == {'amount': 100, 'description': 'Test reward'}
        assert reward_log.source == 'test'
        
        # Verificar que se hizo commit
        mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_grant_clue_reward(reward_system, mock_session):
    """Test que verifica la concesión de recompensa de pista."""
    # Configurar el mock para que encuentre el usuario
    mock_user = MagicMock(spec=User)
    mock_user.id = MOCK_USER_ID
    mock_user_result = AsyncMock()
    mock_user_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.side_effect = [mock_user_result]
    
    # Configurar el mock para que encuentre la pista
    mock_clue = MagicMock(spec=LorePiece)
    mock_clue.id = 1
    mock_clue.code_name = MOCK_CLUE_CODE
    mock_clue.is_active = True
    mock_clue_result = AsyncMock()
    mock_clue_result.scalar_one_or_none.return_value = mock_clue
    mock_session.execute.side_effect = [mock_user_result, mock_clue_result]
    
    # Configurar el mock para que no encuentre la relación usuario-pista
    mock_user_clue_result = AsyncMock()
    mock_user_clue_result.scalar_one_or_none.return_value = None
    mock_session.execute.side_effect = [mock_user_result, mock_clue_result, mock_user_clue_result]
    
    # Llamar al método
    await reward_system.grant_reward(
        user_id=MOCK_USER_ID,
        reward_type='clue',
        reward_data={'clue_code': MOCK_CLUE_CODE, 'description': 'Test clue'},
        source='test'
    )
    
    # Verificar que se añadió la relación usuario-pista
    mock_session.add.assert_called_once()
    user_lore_piece = mock_session.add.call_args[0][0]
    assert isinstance(user_lore_piece, UserLorePiece)
    assert user_lore_piece.user_id == MOCK_USER_ID
    assert user_lore_piece.lore_piece_id == 1
    
    # Verificar que se registró en el log de recompensas
    assert mock_session.add.call_count == 2
    reward_log = mock_session.add.call_args_list[1][0][0]
    assert isinstance(reward_log, RewardLog)
    assert reward_log.user_id == MOCK_USER_ID
    assert reward_log.reward_type == 'clue'
    assert reward_log.reward_data == {'clue_code': MOCK_CLUE_CODE, 'description': 'Test clue'}
    assert reward_log.source == 'test'
    
    # Verificar que se hizo commit
    mock_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_grant_achievement_reward(reward_system, mock_session):
    """Test que verifica la concesión de recompensa de logro."""
    # Configurar el mock para que encuentre el usuario
    mock_user = MagicMock(spec=User)
    mock_user.id = MOCK_USER_ID
    mock_user.achievements = {}
    mock_user_result = AsyncMock()
    mock_user_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_user_result
    
    # Llamar al método
    await reward_system.grant_reward(
        user_id=MOCK_USER_ID,
        reward_type='achievement',
        reward_data={'achievement_id': MOCK_ACHIEVEMENT_ID, 'description': 'Test achievement'},
        source='test'
    )
    
    # Verificar que se añadió el logro al usuario
    assert MOCK_ACHIEVEMENT_ID in mock_user.achievements
    
    # Verificar que se registró en el log de recompensas
    mock_session.add.assert_called_once()
    reward_log = mock_session.add.call_args[0][0]
    assert isinstance(reward_log, RewardLog)
    assert reward_log.user_id == MOCK_USER_ID
    assert reward_log.reward_type == 'achievement'
    assert reward_log.reward_data == {'achievement_id': MOCK_ACHIEVEMENT_ID, 'description': 'Test achievement'}
    assert reward_log.source == 'test'
    
    # Verificar que se hizo commit
    mock_session.commit.assert_called_once()