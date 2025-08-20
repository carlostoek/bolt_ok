# AchievementService provides achievement and badge management.
#
# This service handles unlocking and granting achievements and badges.
#
# Basic usage:
#
#   achievement_service = AchievementService(db_session)
#   await achievement_service.check_message_achievements(user_id, 100, bot=bot)
#
# The module tracks user progress and awards achievements and badges.
# It relies on SQLAlchemy for database error handling. Thread safety: safe for asyncio.
#
# For configuration, see the AchievementService constructor.
