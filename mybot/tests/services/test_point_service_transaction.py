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


@pytest.fixture
def point_service(mock_session):
    return PointService(mock_session)


@pytest.mark.asyncio
async def test_add_points_creates_transaction(point_service, mock_session):
    """Test that add_points creates a PointTransaction record."""
    user_id = 12345
    points = 10.0
    source = "test"
    
    # Setup mock user
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    mock_user.points = 50.0
    mock_session.get.return_value = mock_user
    
    # Mock the transaction context
    mock_transaction = AsyncMock()
    mock_session.begin.return_value = mock_transaction
    
    # Mock refresh to update user points
    mock_session.refresh = AsyncMock()
    
    # Mock level service
    with patch('services.point_service.LevelService') as mock_level_service, \
         patch('services.point_service.AchievementService') as mock_achievement_service:
        
        mock_level_service_instance = AsyncMock()
        mock_level_service.return_value = mock_level_service_instance
        
        mock_achievement_service_instance = AsyncMock()
        mock_achievement_service.return_value = mock_achievement_service_instance
        mock_achievement_service_instance.check_user_badges.return_value = []
        
        # Call the method
        result = await point_service.add_points(user_id, points, source=source)
        
        # Verify transaction was created
        assert mock_session.add.called
        added_obj = mock_session.add.call_args[0][0]
        assert isinstance(added_obj, PointTransaction)
        assert added_obj.user_id == user_id
        assert added_obj.amount == points
        assert added_obj.balance_after == 60.0  # 50 + 10
        assert added_obj.source == source
        
        # Verify user points were updated
        assert mock_user.points == 60.0


@pytest.mark.asyncio
async def test_deduct_points_creates_transaction(point_service, mock_session):
    """Test that deduct_points creates a PointTransaction record."""
    user_id = 12345
    points = 5
    
    # Setup mock user
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    mock_user.points = 50.0
    mock_session.get.return_value = mock_user
    
    # Mock the transaction context
    mock_transaction = AsyncMock()
    mock_session.begin.return_value = mock_transaction
    
    # Mock refresh to update user points
    mock_session.refresh = AsyncMock()
    
    # Call the method
    result = await point_service.deduct_points(user_id, points)
    
    # Verify transaction was created
    assert mock_session.add.called
    added_obj = mock_session.add.call_args[0][0]
    assert isinstance(added_obj, PointTransaction)
    assert added_obj.user_id == user_id
    assert added_obj.amount == -points  # Negative for deduction
    assert added_obj.balance_after == 45.0  # 50 - 5
    assert added_obj.source == "deduction"
    
    # Verify user points were updated
    assert mock_user.points == 45.0


@pytest.mark.asyncio
async def test_deduct_points_insufficient_balance(point_service, mock_session):
    """Test that deduct_points returns None when user has insufficient balance."""
    user_id = 12345
    points = 100
    
    # Setup mock user with insufficient points
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    mock_user.points = 50.0
    mock_session.get.return_value = mock_user
    
    # Mock the transaction context
    mock_transaction = AsyncMock()
    mock_session.begin.return_value = mock_transaction
    
    # Call the method
    result = await point_service.deduct_points(user_id, points)
    
    # Verify no transaction was created
    assert result is None
    assert not mock_session.add.called


@pytest.mark.asyncio
async def test_get_transaction_history(point_service, mock_session):
    """Test retrieving transaction history for a user."""
    user_id = 12345
    
    # Setup mock transactions
    mock_transactions = [
        PointTransaction(user_id=user_id, amount=10.0, balance_after=10.0, source="test1"),
        PointTransaction(user_id=user_id, amount=5.0, balance_after=15.0, source="test2"),
        PointTransaction(user_id=user_id, amount=-3.0, balance_after=12.0, source="deduction")
    ]
    
    # Mock the query result
    mock_result = AsyncMock()
    mock_result.scalars = Mock()
    mock_result.scalars().all = Mock(return_value=mock_transactions)
    mock_session.execute.return_value = mock_result
    
    # Call the method
    result = await point_service.get_transaction_history(user_id)
    
    # Verify the result
    assert result == mock_transactions
    assert len(result) == 3
    assert result[0].amount == 10.0
    assert result[1].amount == 5.0
    assert result[2].amount == -3.0


@pytest.mark.asyncio
async def test_get_balance(point_service, mock_session):
    """Test retrieving user balance."""
    user_id = 12345
    expected_balance = 75.5
    
    # Setup mock user
    mock_user = Mock(spec=User)
    mock_user.points = expected_balance
    mock_session.get.return_value = mock_user
    
    # Call the method
    result = await point_service.get_balance(user_id)
    
    # Verify the result
    assert result == expected_balance


@pytest.mark.asyncio
async def test_get_balance_nonexistent_user(point_service, mock_session):
    """Test retrieving balance for nonexistent user."""
    user_id = 99999
    mock_session.get.return_value = None
    
    # Call the method
    result = await point_service.get_balance(user_id)
    
    # Verify the result
    assert result == 0