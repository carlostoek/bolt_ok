# LevelService provides user level management.
#
# This service handles level-up logic and database operations for levels.
#
# Basic usage:
#
#   level_service = LevelService(db_session)
#   await level_service.check_for_level_up(user, bot=bot)
#
# The module determines user levels, handles level-ups, and unlocks rewards.
# It relies on SQLAlchemy for database error handling. Thread safety: safe for asyncio.
#
# For configuration, see the LevelService constructor.
