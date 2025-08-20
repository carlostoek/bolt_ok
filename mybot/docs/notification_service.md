# NotificationService provides centralized notification management.
#
# This service aggregates and prioritizes notifications to improve user experience.
#
# Basic usage:
#
#   notification_service = NotificationService(db_session, bot)
#   await notification_service.add_notification(user_id, 'points', {'points': 10})
#
# The module handles queuing, aggregation, and sending of notifications.
# Error handling uses try/except blocks with logging. Thread safety: safe for asyncio.
#
# For configuration, see the NotificationService constructor.
