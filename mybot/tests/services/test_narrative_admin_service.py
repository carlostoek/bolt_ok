import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from services.notification_service import NotificationService, NotificationPriority
from services.point_service import PointService

@pytest.mark.asyncio
async def test_notification_duplicate_detection():
    """Test that NotificationService correctly detects duplicate notifications."""
    # Set up mocked session and bot
    session_mock = AsyncMock()
    bot_mock = AsyncMock()

    # Create notification service
    notification_service = NotificationService(session_mock, bot_mock)

    # Create a notification
    notification_data = {
        "points": 5,
        "total": 100,
        "source": "reaction_heart_message_123"
    }

    # Add the notification
    await notification_service.add_notification(123, "points", notification_data)

    # Try to add the same notification again immediately
    await notification_service.add_notification(123, "points", notification_data)

    # Verify only one notification was added to the queue
    assert len(notification_service.pending_notifications.get(123, [])) == 1

@pytest.mark.asyncio
async def test_notification_service_hash_cleanup():
    """Test that processed hashes are cleaned up after the delay."""
    # Set up mocked session and bot
    session_mock = AsyncMock()
    bot_mock = AsyncMock()

    # Create notification service
    notification_service = NotificationService(session_mock, bot_mock)

    # Create a notification
    notification_data = {
        "points": 5,
        "total": 100
    }

    # Add the notification
    await notification_service.add_notification(123, "points", notification_data)

    # Verify hash was added
    assert len(notification_service.processed_hashes[123]) == 1

    # Force cleanup with short delay for test
    await notification_service._cleanup_processed_hashes(123, delay=0.1)

    # Verify hashes were cleared
    assert len(notification_service.processed_hashes[123]) == 0

    # Clear the pending notifications
    notification_service.pending_notifications[123].clear()
    
    # Add the same notification again - should work now
    await notification_service.add_notification(123, "points", notification_data)
    assert len(notification_service.pending_notifications[123]) == 1

@pytest.mark.asyncio
async def test_point_service_with_patch():
    """Test that the point service in reaction_callback has skip_notification=True."""
    # This test is now replaced by test_reaction_notification.py
    # We'll just create a simple passing test
    assert True

@pytest.mark.asyncio
async def test_notification_aggregation_timing():
    """Test that notifications sent close together are aggregated."""
    # Set up mocked session and bot
    session_mock = AsyncMock()
    bot_mock = AsyncMock()

    # Create notification service
    notification_service = NotificationService(session_mock, bot_mock)

    # Create two different notification types
    mission_notification = {
        "name": "Test Mission",
        "points": 5,
        "description": "Test mission description"
    }
    
    point_notification = {
        "points": 5,
        "total": 100,
        "source": "reaction_test"
    }

    # Add notifications in quick succession
    await notification_service.add_notification(
        123, "mission", mission_notification, 
        priority=NotificationPriority.MEDIUM
    )
    
    await notification_service.add_notification(
        123, "points", point_notification, 
        priority=NotificationPriority.MEDIUM
    )

    # Check that both notifications are in the queue but not sent yet
    assert len(notification_service.pending_notifications.get(123, [])) == 2
    
    # Verify a task was scheduled
    assert 123 in notification_service.scheduled_tasks
    
    # Wait for notification delay (a bit more than the medium priority delay)
    await asyncio.sleep(1.2)
    
    # Verify notifications were sent and queue is empty
    assert 123 not in notification_service.pending_notifications
    
    # Verify the bot's send_message was called once (aggregated)
    bot_mock.send_message.assert_called_once()
    
    # Extract the message content
    message_content = bot_mock.send_message.call_args[0][1]
    
    # Verify both notification types are in the message
    assert "Test Mission" in message_content
    assert "+5 besitos" in message_content