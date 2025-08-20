# start_handler provides user onboarding and main menu access.
#
# This handler routes users to the correct menu based on their role.
#
# Basic usage:
#
#   User sends /start command to the bot.
#
# The module handles user creation/updates and displays the main or admin menu.
# Error handling uses try/except blocks with user-friendly messages. Thread safety: N/A.
#
# For configuration, see the handler's dependencies (Session, Bot).
