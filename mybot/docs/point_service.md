# PointService provides point management for users.
#
# This service centralizes point-related operations and orchestrates gamification.
#
# Basic usage:
#
#   point_service = PointService(db_session)
#   await point_service.add_points(user_id, 10, bot=bot)
#
# The module handles awarding, deducting, and tracking user points.
# Error handling includes creating users on-the-fly. Thread safety: safe for asyncio.
#
# For configuration, see the PointService constructor.
