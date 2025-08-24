import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from database.transaction_models import VipTransaction
from services.subscription_service import SubscriptionService


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def subscription_service(mock_session):
    return SubscriptionService(mock_session)


@pytest.mark.asyncio
async def test_grant_vip_creates_transaction(subscription_service, mock_session):
    """Test that grant_vip creates a VipTransaction record."""
    user_id = 12345
    duration_days = 30
    source = "subscription"
    
    # Setup mock user
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    mock_user.vip_expires_at = None
    mock_session.get.return_value = mock_user
    
    # Mock the transaction context
    mock_transaction = AsyncMock()
    mock_session.begin.return_value = mock_transaction
    
    # Mock refresh to update user
    mock_session.refresh = AsyncMock()
    
    # Mock the deactivate method
    subscription_service._deactivate_previous_vip = AsyncMock()
    
    # Call the method
    await subscription_service.grant_vip(user_id, duration_days, source)
    
    # Verify transaction was created
    assert mock_session.add.called
    added_obj = mock_session.add.call_args[0][0]
    assert isinstance(added_obj, VipTransaction)
    assert added_obj.user_id == user_id
    assert added_obj.action == "grant"
    assert added_obj.source == source
    assert added_obj.duration_days == duration_days
    assert added_obj.is_active is True
    
    # Verify user was updated
    assert mock_user.vip_expires_at is not None


@pytest.mark.asyncio
async def test_deactivate_previous_vip(subscription_service, mock_session):
    """Test that _deactivate_previous_vip deactivates existing transactions."""
    user_id = 12345
    
    # Setup mock transactions
    mock_transaction1 = Mock(spec=VipTransaction)
    mock_transaction1.is_active = True
    
    mock_transaction2 = Mock(spec=VipTransaction)
    mock_transaction2.is_active = True
    
    mock_transactions = [mock_transaction1, mock_transaction2]
    
    # Mock the query result
    mock_result = AsyncMock()
    mock_result.scalars = Mock()
    mock_result.scalars().all = Mock(return_value=mock_transactions)
    mock_session.execute.return_value = mock_result
    
    # Setup mock user
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    mock_user.vip_expires_at = "some_date"
    mock_session.get.return_value = mock_user
    
    # Call the method
    await subscription_service._deactivate_previous_vip(user_id)
    
    # Verify transactions were deactivated
    assert mock_transaction1.is_active is False
    assert mock_transaction2.is_active is False
    
    # Verify user was updated
    assert mock_user.vip_expires_at is None


@pytest.mark.asyncio
async def test_is_subscription_active_with_transactions(subscription_service, mock_session):
    """Test that is_subscription_active correctly checks VIP status using transactions."""
    user_id = 12345
    
    # Setup mock transaction
    mock_transaction = Mock(spec=VipTransaction)
    mock_transaction.expires_at = "future_date"
    
    # Mock the query result
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(return_value=mock_transaction)
    mock_session.execute.return_value = mock_result
    
    # Setup mock user
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    mock_user.vip_expires_at = None
    mock_session.get.return_value = mock_user
    
    # Call the method
    result = await subscription_service.is_subscription_active(user_id)
    
    # Verify the result
    assert result is True
    
    # Verify user was updated
    assert mock_user.vip_expires_at == "future_date"