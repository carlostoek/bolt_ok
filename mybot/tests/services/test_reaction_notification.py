import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from handlers.reaction_callback import handle_reaction_callback
from services.mission_service import MissionService

@pytest.mark.asyncio
async def test_reaction_callback_no_duplicate_notification():
    """Test that reaction_callback sets skip_notification=True."""
    # Set up mocked services
    session_mock = AsyncMock()
    bot_mock = AsyncMock()
    callback_mock = AsyncMock()
    callback_mock.data = "ip_123_456_heart"
    callback_mock.from_user = MagicMock()
    callback_mock.from_user.id = 789
    callback_mock.message = MagicMock()
    callback_mock.message.chat = MagicMock()
    callback_mock.message.chat.id = 789

    # Set up validation mock
    validate_mock = MagicMock(return_value=True)
    
    # Set up reaction_result
    message_service_mock = AsyncMock()
    message_service_mock.register_reaction.return_value = {"status": "success"}
    
    # Set up reaction points
    channel_service_mock = AsyncMock()
    channel_service_mock.get_reaction_points.return_value = {"heart": 5.0}

    # Mock services
    point_service_mock = AsyncMock()
    mission_service_mock = AsyncMock()
    level_service_mock = AsyncMock()
    achievement_service_mock = AsyncMock()

    # Patch the required services
    with patch('handlers.reaction_callback.validate_message', validate_mock), \
         patch('handlers.reaction_callback.MessageService', return_value=message_service_mock), \
         patch('handlers.reaction_callback.ChannelService', return_value=channel_service_mock), \
         patch('services.point_service.PointService', return_value=point_service_mock), \
         patch('services.mission_service.MissionService', return_value=mission_service_mock), \
         patch('services.level_service.LevelService', return_value=level_service_mock), \
         patch('services.achievement_service.AchievementService', return_value=achievement_service_mock):

        # Execute the handler
        await handle_reaction_callback(callback_mock, session_mock, bot_mock)

        # Verify point_service.add_points was called with skip_notification=True
        point_service_mock.add_points.assert_called_once()
        call_args = point_service_mock.add_points.call_args[1]
        assert call_args['skip_notification'] is True

        # Verify mission service was called with _skip_notification=True
        mission_service_mock.update_progress.assert_called_once()
        mission_call_args = mission_service_mock.update_progress.call_args[1]
        assert '_skip_notification' in mission_call_args
        assert mission_call_args['_skip_notification'] is True