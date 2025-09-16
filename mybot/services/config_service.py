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

    # Narrative System Configuration Keys
    NARRATIVE_ANALYTICS_ENABLED_KEY = "narrative_analytics_enabled"
    NARRATIVE_AUTO_PROGRESS_KEY = "narrative_auto_progress_enabled"
    LORE_AUTO_UNLOCK_KEY = "lore_auto_unlock_enabled"
    ADMIN_PANEL_ACCESS_KEY = "admin_panel_access_enabled"
    CONTENT_VALIDATION_KEY = "content_validation_enabled"
    PERFORMANCE_MONITORING_KEY = "performance_monitoring_enabled"
    AI_INTEGRATION_KEY = "ai_integration_enabled"
    COORDINATOR_ENABLED_KEY = "coordinator_enabled"

    # Performance Configuration Keys
    CACHE_TTL_KEY = "cache_ttl_seconds"
    ANALYTICS_BATCH_SIZE_KEY = "analytics_batch_size"
    DB_POOL_SIZE_KEY = "db_pool_size"
    RATE_LIMIT_ADMIN_KEY = "rate_limit_admin_operations"
    RATE_LIMIT_USER_KEY = "rate_limit_user_interactions"

    # Security Configuration Keys
    ADMIN_SESSION_TIMEOUT_KEY = "admin_session_timeout_minutes"
    MAX_CONTENT_LENGTH_KEY = "max_content_length"
    MAX_FILE_SIZE_KEY = "max_file_size_mb"
    ALLOWED_FILE_TYPES_KEY = "allowed_file_types"

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
        value = await self.get_value(self.VIP_CHANNEL_KEY)
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    async def set_vip_channel_id(self, chat_id: int) -> ConfigEntry:
        return await self.set_value(self.VIP_CHANNEL_KEY, str(chat_id))

    async def get_free_channel_id(self) -> int | None:
        value = await self.get_value(self.FREE_CHANNEL_KEY)
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

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

    # ===== NARRATIVE SYSTEM CONFIGURATION METHODS =====

    async def get_narrative_analytics_enabled(self) -> bool:
        """Check if narrative analytics are enabled."""
        value = await self.get_value(self.NARRATIVE_ANALYTICS_ENABLED_KEY)
        return value == "true" if value else True

    async def set_narrative_analytics_enabled(self, enabled: bool) -> ConfigEntry:
        """Enable or disable narrative analytics."""
        return await self.set_value(self.NARRATIVE_ANALYTICS_ENABLED_KEY, str(enabled).lower())

    async def get_lore_auto_unlock_enabled(self) -> bool:
        """Check if automatic lore unlocking is enabled."""
        value = await self.get_value(self.LORE_AUTO_UNLOCK_KEY)
        return value == "true" if value else True

    async def set_lore_auto_unlock_enabled(self, enabled: bool) -> ConfigEntry:
        """Enable or disable automatic lore unlocking."""
        return await self.set_value(self.LORE_AUTO_UNLOCK_KEY, str(enabled).lower())

    async def get_content_validation_enabled(self) -> bool:
        """Check if content validation is enabled."""
        value = await self.get_value(self.CONTENT_VALIDATION_KEY)
        return value == "true" if value else True

    async def set_content_validation_enabled(self, enabled: bool) -> ConfigEntry:
        """Enable or disable content validation."""
        return await self.set_value(self.CONTENT_VALIDATION_KEY, str(enabled).lower())

    async def get_performance_monitoring_enabled(self) -> bool:
        """Check if performance monitoring is enabled."""
        value = await self.get_value(self.PERFORMANCE_MONITORING_KEY)
        return value == "true" if value else True

    async def set_performance_monitoring_enabled(self, enabled: bool) -> ConfigEntry:
        """Enable or disable performance monitoring."""
        return await self.set_value(self.PERFORMANCE_MONITORING_KEY, str(enabled).lower())

    async def get_ai_integration_enabled(self) -> bool:
        """Check if AI integration is enabled."""
        value = await self.get_value(self.AI_INTEGRATION_KEY)
        return value == "true" if value else True

    async def set_ai_integration_enabled(self, enabled: bool) -> ConfigEntry:
        """Enable or disable AI integration."""
        return await self.set_value(self.AI_INTEGRATION_KEY, str(enabled).lower())

    async def get_coordinator_enabled(self) -> bool:
        """Check if CoordinadorCentral is enabled."""
        value = await self.get_value(self.COORDINATOR_ENABLED_KEY)
        return value == "true" if value else True

    async def set_coordinator_enabled(self, enabled: bool) -> ConfigEntry:
        """Enable or disable CoordinadorCentral."""
        return await self.set_value(self.COORDINATOR_ENABLED_KEY, str(enabled).lower())

    # ===== PERFORMANCE CONFIGURATION METHODS =====

    async def get_cache_ttl_seconds(self) -> int:
        """Get cache TTL in seconds."""
        value = await self.get_value(self.CACHE_TTL_KEY)
        try:
            return int(value) if value else 3600
        except (ValueError, TypeError):
            return 3600

    async def set_cache_ttl_seconds(self, ttl: int) -> ConfigEntry:
        """Set cache TTL in seconds."""
        return await self.set_value(self.CACHE_TTL_KEY, str(ttl))

    async def get_analytics_batch_size(self) -> int:
        """Get analytics batch processing size."""
        value = await self.get_value(self.ANALYTICS_BATCH_SIZE_KEY)
        try:
            return int(value) if value else 100
        except (ValueError, TypeError):
            return 100

    async def set_analytics_batch_size(self, size: int) -> ConfigEntry:
        """Set analytics batch processing size."""
        return await self.set_value(self.ANALYTICS_BATCH_SIZE_KEY, str(size))

    async def get_rate_limit_admin(self) -> int:
        """Get admin operations rate limit per hour."""
        value = await self.get_value(self.RATE_LIMIT_ADMIN_KEY)
        try:
            return int(value) if value else 100
        except (ValueError, TypeError):
            return 100

    async def set_rate_limit_admin(self, limit: int) -> ConfigEntry:
        """Set admin operations rate limit per hour."""
        return await self.set_value(self.RATE_LIMIT_ADMIN_KEY, str(limit))

    async def get_rate_limit_user(self) -> int:
        """Get user interactions rate limit per hour."""
        value = await self.get_value(self.RATE_LIMIT_USER_KEY)
        try:
            return int(value) if value else 1000
        except (ValueError, TypeError):
            return 1000

    async def set_rate_limit_user(self, limit: int) -> ConfigEntry:
        """Set user interactions rate limit per hour."""
        return await self.set_value(self.RATE_LIMIT_USER_KEY, str(limit))

    # ===== SECURITY CONFIGURATION METHODS =====

    async def get_admin_session_timeout_minutes(self) -> int:
        """Get admin session timeout in minutes."""
        value = await self.get_value(self.ADMIN_SESSION_TIMEOUT_KEY)
        try:
            return int(value) if value else 30
        except (ValueError, TypeError):
            return 30

    async def set_admin_session_timeout_minutes(self, timeout: int) -> ConfigEntry:
        """Set admin session timeout in minutes."""
        return await self.set_value(self.ADMIN_SESSION_TIMEOUT_KEY, str(timeout))

    async def get_max_content_length(self) -> int:
        """Get maximum content length."""
        value = await self.get_value(self.MAX_CONTENT_LENGTH_KEY)
        try:
            return int(value) if value else 5000
        except (ValueError, TypeError):
            return 5000

    async def set_max_content_length(self, length: int) -> ConfigEntry:
        """Set maximum content length."""
        return await self.set_value(self.MAX_CONTENT_LENGTH_KEY, str(length))

    async def get_max_file_size_mb(self) -> int:
        """Get maximum file size in MB."""
        value = await self.get_value(self.MAX_FILE_SIZE_KEY)
        try:
            return int(value) if value else 10
        except (ValueError, TypeError):
            return 10

    async def set_max_file_size_mb(self, size: int) -> ConfigEntry:
        """Set maximum file size in MB."""
        return await self.set_value(self.MAX_FILE_SIZE_KEY, str(size))

    async def get_allowed_file_types(self) -> list[str]:
        """Get list of allowed file types."""
        value = await self.get_value(self.ALLOWED_FILE_TYPES_KEY)
        if value:
            return [t.strip().lower() for t in value.split(",") if t.strip()]
        return ["jpg", "jpeg", "png", "gif", "mp4", "mp3", "txt", "pdf"]

    async def set_allowed_file_types(self, file_types: list[str]) -> ConfigEntry:
        """Set allowed file types."""
        clean_types = [t.strip().lower() for t in file_types if t.strip()]
        return await self.set_value(self.ALLOWED_FILE_TYPES_KEY, ",".join(clean_types))

    # ===== CONFIGURATION VALIDATION AND HELPERS =====

    async def validate_narrative_config(self) -> dict[str, bool]:
        """Validate narrative system configuration and return status."""
        validation_results = {}

        try:
            # Check basic narrative features
            validation_results["analytics_enabled"] = await self.get_narrative_analytics_enabled()
            validation_results["lore_auto_unlock"] = await self.get_lore_auto_unlock_enabled()
            validation_results["content_validation"] = await self.get_content_validation_enabled()
            validation_results["ai_integration"] = await self.get_ai_integration_enabled()
            validation_results["coordinator"] = await self.get_coordinator_enabled()

            # Check performance settings are reasonable
            cache_ttl = await self.get_cache_ttl_seconds()
            validation_results["cache_ttl_valid"] = 60 <= cache_ttl <= 86400  # 1 min to 1 day

            batch_size = await self.get_analytics_batch_size()
            validation_results["batch_size_valid"] = 10 <= batch_size <= 1000

            # Check security settings
            session_timeout = await self.get_admin_session_timeout_minutes()
            validation_results["session_timeout_valid"] = 5 <= session_timeout <= 480  # 5 min to 8 hours

            max_content = await self.get_max_content_length()
            validation_results["content_length_valid"] = 100 <= max_content <= 50000

            file_size = await self.get_max_file_size_mb()
            validation_results["file_size_valid"] = 1 <= file_size <= 100

        except Exception as e:
            validation_results["error"] = str(e)

        return validation_results

    async def get_narrative_config_summary(self) -> dict:
        """Get a summary of all narrative system configuration."""
        return {
            "features": {
                "analytics_enabled": await self.get_narrative_analytics_enabled(),
                "lore_auto_unlock": await self.get_lore_auto_unlock_enabled(),
                "content_validation": await self.get_content_validation_enabled(),
                "performance_monitoring": await self.get_performance_monitoring_enabled(),
                "ai_integration": await self.get_ai_integration_enabled(),
                "coordinator": await self.get_coordinator_enabled(),
            },
            "performance": {
                "cache_ttl_seconds": await self.get_cache_ttl_seconds(),
                "analytics_batch_size": await self.get_analytics_batch_size(),
                "rate_limit_admin": await self.get_rate_limit_admin(),
                "rate_limit_user": await self.get_rate_limit_user(),
            },
            "security": {
                "admin_session_timeout_minutes": await self.get_admin_session_timeout_minutes(),
                "max_content_length": await self.get_max_content_length(),
                "max_file_size_mb": await self.get_max_file_size_mb(),
                "allowed_file_types": await self.get_allowed_file_types(),
            }
        }
