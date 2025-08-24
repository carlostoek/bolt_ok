import pytest
from unittest.mock import AsyncMock, Mock
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.subscription_service import SubscriptionService


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def subscription_service(mock_session):
    return SubscriptionService(mock_session)


@pytest.mark.asyncio
async def test_subscription_service_backward_compatibility(subscription_service, mock_session):
    """Test that the refactored SubscriptionService maintains backward compatibility."""
    user_id = 123456789
    
    # Test is_subscription_active (should work as before)
    # Setup mock transaction result
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_session.execute.return_value = mock_result
    
    is_active = await subscription_service.is_subscription_active(user_id)
    assert is_active is False  # Should be False as no VIP granted yet


@pytest.mark.asyncio
async def test_subscription_service_integration_with_user_model(subscription_service, mock_session):
    """Test that the refactored SubscriptionService integrates properly with the User model."""
    user_id = 123456789
    
    # Setup mock user
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    mock_user.vip_expires_at = None
    mock_user.role = "free"
    mock_session.get.return_value = mock_user
    
    # Mock refresh to update user
    mock_session.refresh = AsyncMock()
    
    # Mock the deactivate method
    subscription_service._deactivate_previous_vip = AsyncMock()
    
    # Grant VIP access using new method
    await subscription_service.grant_vip(user_id=user_id, duration_days=30, source="subscription")
    
    # Check that the method was called
    assert subscription_service._deactivate_previous_vip.called
    
    # Check that session.add was called with a VipTransaction
    assert mock_session.add.called


@pytest.mark.asyncio
async def test_subscription_service_mixed_usage(subscription_service, mock_session):
    """Test mixing new transaction-based methods with legacy methods."""
    user_id = 123456789
    
    # Test is_subscription_active still works
    # Setup mock transaction result
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = Mock(return_value=None)
    mock_session.execute.return_value = mock_result
    
    is_active = await subscription_service.is_subscription_active(user_id)
    assert is_active is False  # Should be False as no VIP granted yet
    
    # Test grant_vip (new method)
    # Setup mock user
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    mock_user.vip_expires_at = None
    mock_user.role = "free"
    mock_session.get.return_value = mock_user
    
    # Mock the deactivate method
    subscription_service._deactivate_previous_vip = AsyncMock()
    
    await subscription_service.grant_vip(user_id=user_id, duration_days=15, source="badge")
    
    # Check that the method was called
    assert subscription_service._deactivate_previous_vip.called
    
    # Check that session.add was called with a VipTransaction
    assert mock_session.add.called