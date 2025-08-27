"""Configuration aggregate repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from database.models import ConfigEntry, BotConfig, InviteToken
from datetime import datetime


class IConfigRepository(ABC):
    """Repository interface for Configuration aggregate operations."""
    
    # Configuration entry operations
    @abstractmethod
    async def get_config_value(self, key: str) -> Optional[str]:
        """Get configuration value by key."""
        pass
    
    @abstractmethod
    async def set_config_value(self, key: str, value: str) -> ConfigEntry:
        """Set configuration value."""
        pass
    
    @abstractmethod
    async def delete_config_entry(self, key: str) -> bool:
        """Delete configuration entry."""
        pass
    
    @abstractmethod
    async def get_all_config_entries(self) -> List[ConfigEntry]:
        """Get all configuration entries."""
        pass
    
    @abstractmethod
    async def get_config_entries_by_prefix(self, prefix: str) -> List[ConfigEntry]:
        """Get configuration entries starting with prefix."""
        pass
    
    @abstractmethod
    async def bulk_set_config(self, config_dict: Dict[str, str]) -> List[ConfigEntry]:
        """Set multiple configuration values in bulk."""
        pass
    
    # Bot configuration operations
    @abstractmethod
    async def get_bot_config(self) -> Optional[BotConfig]:
        """Get bot configuration."""
        pass
    
    @abstractmethod
    async def create_bot_config(self, config_data: Dict[str, Any]) -> BotConfig:
        """Create bot configuration."""
        pass
    
    @abstractmethod
    async def update_bot_config(self, config: BotConfig) -> BotConfig:
        """Update bot configuration."""
        pass
    
    @abstractmethod
    async def update_bot_config_partial(self, updates: Dict[str, Any]) -> BotConfig:
        """Update specific bot configuration fields."""
        pass
    
    @abstractmethod
    async def get_free_channel_wait_time(self) -> int:
        """Get free channel wait time in minutes."""
        pass
    
    @abstractmethod
    async def set_free_channel_wait_time(self, minutes: int) -> BotConfig:
        """Set free channel wait time."""
        pass
    
    @abstractmethod
    async def get_social_media_message(self) -> Optional[str]:
        """Get social media message template."""
        pass
    
    @abstractmethod
    async def set_social_media_message(self, message: str) -> BotConfig:
        """Set social media message template."""
        pass
    
    @abstractmethod
    async def get_welcome_message_template(self) -> Optional[str]:
        """Get welcome message template."""
        pass
    
    @abstractmethod
    async def set_welcome_message_template(self, message: str) -> BotConfig:
        """Set welcome message template."""
        pass
    
    @abstractmethod
    async def get_token_welcome_message(self) -> Optional[str]:
        """Get token welcome message."""
        pass
    
    @abstractmethod
    async def set_token_welcome_message(self, message: str) -> BotConfig:
        """Set token welcome message."""
        pass
    
    @abstractmethod
    async def is_auto_approval_enabled(self) -> bool:
        """Check if auto approval is enabled."""
        pass
    
    @abstractmethod
    async def set_auto_approval(self, enabled: bool) -> BotConfig:
        """Enable or disable auto approval."""
        pass
    
    # Invite token operations
    @abstractmethod
    async def get_invite_token_by_token(self, token: str) -> Optional[InviteToken]:
        """Get invite token by token string."""
        pass
    
    @abstractmethod
    async def get_invite_token_by_id(self, token_id: int) -> Optional[InviteToken]:
        """Get invite token by ID."""
        pass
    
    @abstractmethod
    async def create_invite_token(self, token_data: Dict[str, Any]) -> InviteToken:
        """Create a new invite token."""
        pass
    
    @abstractmethod
    async def use_invite_token(self, token: str, used_by: int) -> Optional[InviteToken]:
        """Mark invite token as used."""
        pass
    
    @abstractmethod
    async def get_tokens_created_by_user(self, user_id: int) -> List[InviteToken]:
        """Get all tokens created by specific user."""
        pass
    
    @abstractmethod
    async def get_active_invite_tokens(self) -> List[InviteToken]:
        """Get all active (unused and not expired) invite tokens."""
        pass
    
    @abstractmethod
    async def get_expired_invite_tokens(self) -> List[InviteToken]:
        """Get all expired invite tokens."""
        pass
    
    @abstractmethod
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens and return count deleted."""
        pass
    
    @abstractmethod
    async def is_token_valid(self, token: str) -> bool:
        """Check if token is valid (exists, unused, not expired)."""
        pass
    
    @abstractmethod
    async def generate_unique_token(self, created_by: int, expires_at: Optional[datetime] = None) -> InviteToken:
        """Generate a unique invite token."""
        pass
    
    # Token statistics
    @abstractmethod
    async def get_token_statistics(self) -> Dict[str, Any]:
        """Get invite token system statistics."""
        pass
    
    @abstractmethod
    async def get_user_token_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get token statistics for specific user."""
        pass
    
    @abstractmethod
    async def get_token_usage_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get token usage statistics for last N days."""
        pass
    
    # Backup and restore operations
    @abstractmethod
    async def export_all_config(self) -> Dict[str, Any]:
        """Export all configuration data."""
        pass
    
    @abstractmethod
    async def import_config(self, config_data: Dict[str, Any]) -> bool:
        """Import configuration data."""
        pass
    
    @abstractmethod
    async def backup_config_to_dict(self) -> Dict[str, Any]:
        """Create backup of all configuration."""
        pass
    
    @abstractmethod
    async def restore_config_from_dict(self, backup_data: Dict[str, Any]) -> bool:
        """Restore configuration from backup."""
        pass
    
    # Feature flags and toggles
    @abstractmethod
    async def get_feature_flag(self, feature_name: str) -> bool:
        """Get feature flag status."""
        pass
    
    @abstractmethod
    async def set_feature_flag(self, feature_name: str, enabled: bool) -> bool:
        """Set feature flag status."""
        pass
    
    @abstractmethod
    async def get_all_feature_flags(self) -> Dict[str, bool]:
        """Get all feature flags."""
        pass
    
    @abstractmethod
    async def toggle_feature_flag(self, feature_name: str) -> bool:
        """Toggle feature flag and return new status."""
        pass
    
    # System maintenance
    @abstractmethod
    async def is_maintenance_mode(self) -> bool:
        """Check if system is in maintenance mode."""
        pass
    
    @abstractmethod
    async def set_maintenance_mode(self, enabled: bool, message: Optional[str] = None) -> bool:
        """Enable or disable maintenance mode."""
        pass
    
    @abstractmethod
    async def get_maintenance_message(self) -> Optional[str]:
        """Get maintenance mode message."""
        pass