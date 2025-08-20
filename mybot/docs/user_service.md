# UserService provides user data management.
#
# This service encapsulates database operations for the User model.
#
# Basic usage:
#
#   user_service = UserService(db_session)
#   user = await user_service.get_user(12345)
#
# The module handles creating, retrieving, and updating user info using an AsyncSession.
# Error handling uses try/except blocks with logging. Thread safety: safe, relies on AsyncSession.
#
# For configuration, see the UserService constructor.
