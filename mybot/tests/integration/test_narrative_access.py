"""
Tests for the NarrativeAccessService integration.
"""
import pytest
from unittest.mock import AsyncMock, patch
from mybot.services.integration.narrative_access_service import NarrativeAccessService

@pytest.mark.asyncio
async def test_can_access_fragment_non_vip():
    """Test that non-VIP fragments are accessible to all users."""
    # Setup
    session_mock = AsyncMock()
    service = NarrativeAccessService(session_mock)
    
    # Mock subscription service
    service.subscription_service.is_subscription_active = AsyncMock(return_value=False)
    
    # Test
    result = await service.can_access_fragment(123, "level1_intro")
    
    # Assert
    assert result is True
    # Verify subscription service was not called for non-VIP content
    service.subscription_service.is_subscription_active.assert_not_called()

@pytest.mark.asyncio
async def test_can_access_fragment_vip_with_subscription():
    """Test that VIP fragments are accessible to subscribed users."""
    # Setup
    session_mock = AsyncMock()
    service = NarrativeAccessService(session_mock)
    
    # Mock subscription service
    service.subscription_service.is_subscription_active = AsyncMock(return_value=True)
    
    # Test
    result = await service.can_access_fragment(123, "level4_secret")
    
    # Assert
    assert result is True
    service.subscription_service.is_subscription_active.assert_called_once_with(123)

@pytest.mark.asyncio
async def test_can_access_fragment_vip_without_subscription():
    """Test that VIP fragments are not accessible to non-subscribed users."""
    # Setup
    session_mock = AsyncMock()
    service = NarrativeAccessService(session_mock)
    
    # Mock subscription service
    service.subscription_service.is_subscription_active = AsyncMock(return_value=False)
    
    # Test
    result = await service.can_access_fragment(123, "level4_secret")
    
    # Assert
    assert result is False
    service.subscription_service.is_subscription_active.assert_called_once_with(123)

@pytest.mark.asyncio
async def test_get_accessible_fragment_subscription_required():
    """Test that subscription required message is returned for inaccessible fragments."""
    # Setup
    session_mock = AsyncMock()
    service = NarrativeAccessService(session_mock)
    
    # Mock methods
    service.can_access_fragment = AsyncMock(return_value=False)
    
    # Test
    result = await service.get_accessible_fragment(123, "level5_exclusive")
    
    # Assert
    assert result["type"] == "subscription_required"
    assert "requested_fragment" in result
    assert result["requested_fragment"] == "level5_exclusive"
