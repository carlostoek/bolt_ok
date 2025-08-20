# ChannelService provides channel data management.
#
# This service encapsulates database operations for the Channel model.
#
# Basic usage:
#
#   channel_service = ChannelService(db_session)
#   await channel_service.add_channel(12345, 'My Channel')
#
# The module handles adding, listing, and removing channels, plus reaction settings.
# Error handling uses try/except blocks with logging. Thread safety: safe, relies on AsyncSession.
#
# For configuration, see the ChannelService constructor.
