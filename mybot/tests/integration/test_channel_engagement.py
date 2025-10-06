"""
Tests for the ChannelEngagementService integration.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from mybot.services.integration.channel_engagement_service import ChannelEngagementService

@pytest.mark.asyncio
async def test_award_channel_reaction_success():
    """Test successful awarding of points for channel reactions."""
    # Setup
    session_mock = AsyncMock()
    service = ChannelEngagementService(session_mock)
    
    # Mock user service
    user_mock = MagicMock()
    service.user_service.get_user = AsyncMock(return_value=user_mock)
    
    # Mock config service
    service.config_service.get_managed_channels = AsyncMock(return_value=["123456"])
    
    # Mock point service
    service.point_service.award_reaction = AsyncMock()
    
    # Test
    result = await service.award_channel_reaction(123, 456, 123456)
    
    # Assert
    assert result is True
    service.user_service.get_user.assert_called_once_with(123)
    service.config_service.get_managed_channels.assert_called_once()
    service.point_service.award_reaction.assert_called_once()

@pytest.mark.asyncio
async def test_award_channel_reaction_unmanaged_channel():
    """Test that points are not awarded for reactions in unmanaged channels."""
    # Setup
    session_mock = AsyncMock()
    service = ChannelEngagementService(session_mock)
    
    # Mock user service
    user_mock = MagicMock()
    service.user_service.get_user = AsyncMock(return_value=user_mock)
    
    # Mock config service
    service.config_service.get_managed_channels = AsyncMock(return_value=["789012"])
    
    # Mock point service
    service.point_service.award_reaction = AsyncMock()
    
    # Test
    result = await service.award_channel_reaction(123, 456, 123456)
    
    # Assert
    assert result is False
    service.user_service.get_user.assert_called_once_with(123)
    service.config_service.get_managed_channels.assert_called_once()
    service.point_service.award_reaction.assert_not_called()

@pytest.mark.asyncio
async def test_award_channel_participation_post():
    """Test awarding points for posting in a channel."""
    # Setup
    session_mock = AsyncMock()
    service = ChannelEngagementService(session_mock)
    
    # Mock config service
    service.config_service.get_managed_channels = AsyncMock(return_value=["123456"])
    
    # Mock point service
    service.point_service.add_points = AsyncMock()
    
    # Test
    result = await service.award_channel_participation(123, 123456, "post")
    
    # Assert
    assert result is True
    service.config_service.get_managed_channels.assert_called_once()
    service.point_service.add_points.assert_called_once_with(123, 5, bot=None)

@pytest.mark.asyncio
async def test_check_daily_engagement_success():
    """Test successful daily engagement check and bonus award."""
    # Setup
    session_mock = AsyncMock()
    service = ChannelEngagementService(session_mock)
    
    # Mock progress
    progress_mock = MagicMock()
    progress_mock.checkin_streak = 7
    
    # Mock point service
    service.point_service.daily_checkin = AsyncMock(return_value=(True, progress_mock))
    service.point_service.add_points = AsyncMock()
    
    # Mock bot
    bot_mock = AsyncMock()
    
    # Test
    result = await service.check_daily_engagement(123, bot_mock)
    
    # Assert
    assert result is True
    service.point_service.daily_checkin.assert_called_once_with(123, bot_mock)
    service.point_service.add_points.assert_called_once()  # Weekly bonus
    bot_mock.send_message.assert_called_once()  # Streak message
