from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from database.models import ConfigEntry
from utils.text_utils import sanitize_text


class ConfigService:
    VIP_CHANNEL_KEY = "VIP_CHANNEL_ID"
    FREE_CHANNEL_KEY = "FREE_CHANNEL_ID"
    REACTION_BUTTONS_KEY = "reaction_buttons"
    REACTION_POINTS_KEY = "reaction_points"
    VIP_REACTIONS_KEY = "vip_message_reactions"

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_value(self, key: str) -> str | None:
        entry = await self.session.get(ConfigEntry, key)
        return entry.value if entry else None

    async def set_value(self, key: str, value: str) -> ConfigEntry:
        """Store a configuration value, sanitizing text to avoid encoding issues."""
        clean_value = sanitize_text(value)
        entry = await self.session.get(ConfigEntry, key)
        if entry:
            entry.value = clean_value
        else:
            entry = ConfigEntry(key=key, value=clean_value)
            self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def get_vip_channel_id(self) -> int | None:
        """Get VIP channel ID from database, with fallback to environment variable."""
        value = await self.get_value(self.VIP_CHANNEL_KEY)

        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                pass

        # Fallback to environment variable if not in database
        from utils.config import VIP_CHANNEL_ID
        return VIP_CHANNEL_ID if VIP_CHANNEL_ID != 0 else None

    async def set_vip_channel_id(self, chat_id: int) -> ConfigEntry:
        return await self.set_value(self.VIP_CHANNEL_KEY, str(chat_id))

    async def get_free_channel_id(self) -> int | None:
        """Get free channel ID from database, with fallback to environment variable."""
        value = await self.get_value(self.FREE_CHANNEL_KEY)

        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                pass

        # Fallback to environment variable if not in database
        from utils.config import FREE_CHANNEL_ID
        return FREE_CHANNEL_ID if FREE_CHANNEL_ID != 0 else None

    async def set_free_channel_id(self, chat_id: int) -> ConfigEntry:
        return await self.set_value(self.FREE_CHANNEL_KEY, str(chat_id))

    async def get_reaction_buttons(self) -> list[str]:
        """Return custom reaction button texts or defaults."""
        value = await self.get_value(self.REACTION_BUTTONS_KEY)
        if value:
            texts = [t.strip() for t in value.split(";") if t.strip()]
            if texts:
                return texts[:10]
        from utils.config import DEFAULT_REACTION_BUTTONS

        return DEFAULT_REACTION_BUTTONS

    async def set_reaction_buttons(self, buttons: list[str]) -> ConfigEntry:
        """Store custom reaction button texts."""
        return await self.set_value(self.REACTION_BUTTONS_KEY, ";".join(buttons))

    async def get_vip_reactions(self) -> list[str]:
        """Return the list of default VIP message reactions."""
        value = await self.get_value(self.VIP_REACTIONS_KEY)
        if value:
            emojis = [e.strip() for e in value.split(";") if e.strip()]
            return emojis[:5]
        return []

    async def set_vip_reactions(self, reactions: list[str]) -> ConfigEntry:
        """Store the default VIP message reactions as a semicolon string."""
        return await self.set_value(self.VIP_REACTIONS_KEY, ";".join(reactions))

    async def get_reaction_points(self) -> list[float]:
        """Return configured points for each reaction button."""
        value = await self.get_value(self.REACTION_POINTS_KEY)
        if value:
            try:
                points = [float(p) for p in value.split(";") if p.strip()]
                return points[:10]
            except ValueError:
                pass
        # Default: 0.5 points for each configured reaction button
        buttons = await self.get_reaction_buttons()
        return [0.5] * len(buttons)

    async def set_reaction_points(self, points: list[float]) -> ConfigEntry:
        """Store reaction points as a semicolon separated list."""
        text = ";".join(str(p) for p in points)
        return await self.set_value(self.REACTION_POINTS_KEY, text)

    async def get_managed_channels(self) -> list[str]:
        """
        Return list of managed channel IDs for point awarding.
        Includes both VIP and FREE channels if configured.
        """
        managed_channels = []
        
        # Add VIP channel if configured
        vip_channel = await self.get_vip_channel_id()
        if vip_channel:
            managed_channels.append(str(vip_channel))
            
        # Add FREE channel if configured  
        free_channel = await self.get_free_channel_id()
        if free_channel:
            managed_channels.append(str(free_channel))
            
        return managed_channels
