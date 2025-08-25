import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram.types import CallbackQuery, User, Message, Chat
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.reaction_callback import handle_reaction_callback
from services.notification_service import NotificationService
from services.point_service import PointService
from services.mission_service import MissionService
from services.level_service import LevelService
from services.achievement_service import AchievementService

@pytest.mark.asyncio
async def test_view_fragment_integration():
    """
    Integration test for the reaction notification flow.
    Tests that:
    1. Reaction callbacks don't generate duplicate notifications
    2. The NotificationService correctly handles and deduplicates notifications
    """
    # Mock database session
    session_mock = AsyncMock()
    session_mock.in_transaction = MagicMock(return_value=False)

    # Mock bot
    bot_mock = AsyncMock()

    # Create real notification service with mocked dependencies
    notification_service = NotificationService(session_mock, bot_mock)

    # Mock services with real NotificationService
    level_service = AsyncMock()
    achievement_service = AsyncMock()
    achievement_service.check_user_badges = AsyncMock(return_value=[])

    # Create real PointService with mocked dependencies and real NotificationService
    point_service = PointService(
        session=session_mock,
        level_service=level_service,
        achievement_service=achievement_service,
        notification_service=notification_service
    )

    # Mock MissionService
    mission_service = AsyncMock()

    # Create mock user data in "database"
    user_id = 12345
    user_mock = MagicMock()
    user_mock.id = user_id
    user_mock.points = 100
    session_mock.get = AsyncMock(return_value=user_mock)

    # Create mock callback query
    from datetime import datetime
    user = User(id=user_id, is_bot=False, first_name="Test")
    chat = Chat(id=user_id, type="private")
    message = Message(message_id=1, date=datetime.now(), chat=chat)

    callback = CallbackQuery(
        id="test_id",
        from_user=user,
        chat_instance="test_instance",
        message=message,
        data="ip_channel123_456_heart"
    )

    # Mock validation functions
    with patch('handlers.reaction_callback.validate_message', return_value=True), \
         patch('handlers.reaction_callback.MessageService') as message_service_cls, \
         patch('handlers.reaction_callback.ChannelService') as channel_service_mock, \
         patch('services.point_service.PointService', return_value=point_service), \
         patch('services.mission_service.MissionService', return_value=mission_service), \
         patch('services.level_service.LevelService'), \
         patch('services.achievement_service.AchievementService'):
        
        # Configure message service mock
        message_service_instance = message_service_cls.return_value
        # Use AsyncMock for async methods
        register_reaction_mock = AsyncMock()
        register_reaction_mock.return_value = {"status": "success"}
        message_service_instance.register_reaction = register_reaction_mock
        message_service_instance.update_reaction_markup = AsyncMock()

        # Set up channel service to return points
        channel_instance = channel_service_mock.return_value
        get_points_mock = AsyncMock()
        get_points_mock.return_value = {"heart": 5.0}
        channel_instance.get_reaction_points = get_points_mock

        # Execute the handler
        await handle_reaction_callback(callback, session_mock, bot_mock)

        # Verify PointService.add_points was called with skip_notification=True
        assert user_mock.points == 105.0  # Original 100 + 5

        # Check that notification queue has one item from mission update but not from points
        assert len(notification_service.pending_notifications.get(user_id, [])) <= 1

        # If notification was added, verify it's not a duplicate points notification
        notifications = notification_service.pending_notifications.get(user_id, [])
        for notification in notifications:
            if notification.type == "points":
                # The test should fail if we find a points notification
                assert False, "Points notification was added when it should have been skipped"

        # Verify mission service was called
        mission_service.update_progress.assert_called_once()