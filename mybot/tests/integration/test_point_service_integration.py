import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, UserStats
from database.transaction_models import PointTransaction
from services.point_service import PointService
from aiogram import Bot


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_bot():
    return Mock(spec=Bot)


@pytest.mark.asyncio
async def test_award_message_creates_transaction(mock_session, mock_bot):
    """Test that award_message creates a PointTransaction record."""
    point_service = PointService(mock_session)
    user_id = 12345
    
    # Setup mocks
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    mock_user.points = 0.0
    mock_session.get.return_value = mock_user
    
    mock_progress = Mock(spec=UserStats)
    mock_progress.last_activity_at = None
    mock_progress.last_notified_points = 0.0
    mock_progress.messages_sent = 0
    
    # Mock _get_or_create_progress to return our mock
    point_service._get_or_create_progress = AsyncMock(return_value=mock_progress)
    
    # Mock the transaction context
    mock_transaction = AsyncMock()
    mock_session.begin.return_value.__aenter__.return_value = mock_transaction
    
    # Mock refresh
    mock_session.refresh = AsyncMock()
    
    # Mock other services
    with patch('services.point_service.LevelService') as mock_level_service, \
         patch('services.point_service.AchievementService') as mock_achievement_service, \
         patch('services.point_service.get_points_multiplier', return_value=1.0), \
         patch('services.point_service.EventService') as mock_event_service:
        
        mock_level_service_instance = AsyncMock()
        mock_level_service.return_value = mock_level_service_instance
        
        mock_achievement_service_instance = AsyncMock()
        mock_achievement_service.return_value = mock_achievement_service_instance
        mock_achievement_service_instance.check_user_badges.return_value = []
        mock_achievement_service_instance.check_message_achievements = AsyncMock()
        
        mock_event_service_instance = AsyncMock()
        mock_event_service_instance.get_multiplier.return_value = 1.0
        mock_event_service.return_value = mock_event_service_instance
        
        # Call the method
        result = await point_service.award_message(user_id, mock_bot)
        
        # Verify transaction was created
        assert mock_session.add.called
        call_args = mock_session.add.call_args_list
        transaction_added = False
        for call in call_args:
            if isinstance(call[0][0], PointTransaction):
                transaction_added = True
                transaction = call[0][0]
                assert transaction.user_id == user_id
                assert transaction.amount == 1.0  # 1 point for message
                assert transaction.source == "unknown"  # default source
                break
        
        assert transaction_added, "No PointTransaction was added to the session"


@pytest.mark.asyncio
async def test_award_reaction_creates_transaction(mock_session, mock_bot):
    """Test that award_reaction creates a PointTransaction record."""
    point_service = PointService(mock_session)
    user_id = 12345
    message_id = 67890
    
    # Setup mocks
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    mock_user.points = 0.0
    
    mock_progress = Mock(spec=UserStats)
    mock_progress.last_reaction_at = None
    mock_progress.last_notified_points = 0.0
    
    # Mock _get_or_create_progress to return our mock
    point_service._get_or_create_progress = AsyncMock(return_value=mock_progress)
    
    # Mock the transaction context
    mock_transaction = AsyncMock()
    mock_session.begin.return_value.__aenter__.return_value = mock_transaction
    
    # Mock refresh
    mock_session.refresh = AsyncMock()
    
    # Mock other services
    with patch('services.point_service.LevelService') as mock_level_service, \
         patch('services.point_service.AchievementService') as mock_achievement_service, \
         patch('services.point_service.get_points_multiplier', return_value=1.0), \
         patch('services.point_service.EventService') as mock_event_service:
        
        mock_level_service_instance = AsyncMock()
        mock_level_service.return_value = mock_level_service_instance
        
        mock_achievement_service_instance = AsyncMock()
        mock_achievement_service.return_value = mock_achievement_service_instance
        mock_achievement_service_instance.check_user_badges.return_value = []
        
        mock_event_service_instance = AsyncMock()
        mock_event_service_instance.get_multiplier.return_value = 1.0
        mock_event_service.return_value = mock_event_service_instance
        
        # Call the method
        result = await point_service.award_reaction(mock_user, message_id, mock_bot)
        
        # Verify transaction was created
        assert mock_session.add.called
        call_args = mock_session.add.call_args_list
        transaction_added = False
        for call in call_args:
            if isinstance(call[0][0], PointTransaction):
                transaction_added = True
                transaction = call[0][0]
                assert transaction.user_id == user_id
                assert transaction.amount == 0.5  # 0.5 points for reaction
                assert transaction.source == "unknown"  # default source
                break
        
        assert transaction_added, "No PointTransaction was added to the session"


@pytest.mark.asyncio
async def test_daily_checkin_creates_transaction(mock_session, mock_bot):
    """Test that daily_checkin creates a PointTransaction record."""
    point_service = PointService(mock_session)
    user_id = 12345
    
    # Setup mocks
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    mock_user.points = 0.0
    
    mock_progress = Mock(spec=UserStats)
    mock_progress.last_checkin_at = None
    mock_progress.last_notified_points = 0.0
    mock_progress.checkin_streak = 0
    
    # Mock _get_or_create_progress to return our mock
    point_service._get_or_create_progress = AsyncMock(return_value=mock_progress)
    
    # Mock the transaction context
    mock_transaction = AsyncMock()
    mock_session.begin.return_value.__aenter__.return_value = mock_transaction
    
    # Mock refresh
    mock_session.refresh = AsyncMock()
    
    # Mock other services
    with patch('services.point_service.LevelService') as mock_level_service, \
         patch('services.point_service.AchievementService') as mock_achievement_service, \
         patch('services.point_service.get_points_multiplier', return_value=1.0), \
         patch('services.point_service.EventService') as mock_event_service:
        
        mock_level_service_instance = AsyncMock()
        mock_level_service.return_value = mock_level_service_instance
        
        mock_achievement_service_instance = AsyncMock()
        mock_achievement_service.return_value = mock_achievement_service_instance
        mock_achievement_service_instance.check_user_badges.return_value = []
        mock_achievement_service_instance.check_checkin_achievements = AsyncMock()
        
        mock_event_service_instance = AsyncMock()
        mock_event_service_instance.get_multiplier.return_value = 1.0
        mock_event_service.return_value = mock_event_service_instance
        
        # Call the method
        success, result_progress = await point_service.daily_checkin(user_id, mock_bot)
        
        # Verify transaction was created
        assert success
        assert mock_session.add.called
        call_args = mock_session.add.call_args_list
        transaction_added = False
        for call in call_args:
            if isinstance(call[0][0], PointTransaction):
                transaction_added = True
                transaction = call[0][0]
                assert transaction.user_id == user_id
                assert transaction.amount == 10.0  # 10 points for daily checkin
                assert transaction.source == "unknown"  # default source
                break
        
        assert transaction_added, "No PointTransaction was added to the session"