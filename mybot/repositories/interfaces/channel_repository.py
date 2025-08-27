"""Channel aggregate repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from database.models import Channel, PendingChannelRequest
from datetime import datetime


class IChannelRepository(ABC):
    """Repository interface for Channel aggregate operations."""
    
    # Channel operations
    @abstractmethod
    async def get_channel_by_id(self, channel_id: int) -> Optional[Channel]:
        """Get channel by Telegram chat ID."""
        pass
    
    @abstractmethod
    async def get_all_channels(self) -> List[Channel]:
        """Get all registered channels."""
        pass
    
    @abstractmethod
    async def get_channels_by_type(self, channel_type: str) -> List[Channel]:
        """Get channels by type (free, vip, engagement)."""
        pass
    
    @abstractmethod
    async def create_channel(self, channel_data: Dict[str, Any]) -> Channel:
        """Create a new channel."""
        pass
    
    @abstractmethod
    async def update_channel(self, channel: Channel) -> Channel:
        """Update existing channel."""
        pass
    
    @abstractmethod
    async def delete_channel(self, channel_id: int) -> bool:
        """Delete channel."""
        pass
    
    @abstractmethod
    async def search_channels_by_title(self, query: str, limit: int = 50) -> List[Channel]:
        """Search channels by title."""
        pass
    
    # Channel reaction configuration
    @abstractmethod
    async def get_channel_reactions(self, channel_id: int) -> List[str]:
        """Get configured reactions for channel."""
        pass
    
    @abstractmethod
    async def set_channel_reactions(self, channel_id: int, reactions: List[str]) -> bool:
        """Set reactions for channel."""
        pass
    
    @abstractmethod
    async def get_channel_reaction_points(self, channel_id: int) -> Dict[str, float]:
        """Get reaction point values for channel."""
        pass
    
    @abstractmethod
    async def set_channel_reaction_points(self, channel_id: int, reaction_points: Dict[str, float]) -> bool:
        """Set reaction point values for channel."""
        pass
    
    @abstractmethod
    async def add_channel_reaction(self, channel_id: int, emoji: str, points: float) -> bool:
        """Add a reaction to channel configuration."""
        pass
    
    @abstractmethod
    async def remove_channel_reaction(self, channel_id: int, emoji: str) -> bool:
        """Remove a reaction from channel configuration."""
        pass
    
    # Channel management settings
    @abstractmethod
    async def enable_auto_permissions(self, channel_id: int) -> bool:
        """Enable auto permission management for channel."""
        pass
    
    @abstractmethod
    async def disable_auto_permissions(self, channel_id: int) -> bool:
        """Disable auto permission management for channel."""
        pass
    
    @abstractmethod
    async def get_channels_with_auto_permissions(self) -> List[Channel]:
        """Get channels with auto permission management enabled."""
        pass
    
    # Pending channel requests
    @abstractmethod
    async def get_pending_request_by_id(self, request_id: int) -> Optional[PendingChannelRequest]:
        """Get pending channel request by ID."""
        pass
    
    @abstractmethod
    async def get_pending_requests(self) -> List[PendingChannelRequest]:
        """Get all pending channel requests."""
        pass
    
    @abstractmethod
    async def get_pending_requests_by_user(self, user_id: int) -> List[PendingChannelRequest]:
        """Get pending requests for specific user."""
        pass
    
    @abstractmethod
    async def create_pending_request(self, request_data: Dict[str, Any]) -> PendingChannelRequest:
        """Create a new pending channel request."""
        pass
    
    @abstractmethod
    async def approve_pending_request(self, request_id: int) -> PendingChannelRequest:
        """Approve pending channel request."""
        pass
    
    @abstractmethod
    async def reject_pending_request(self, request_id: int) -> bool:
        """Reject and delete pending channel request."""
        pass
    
    @abstractmethod
    async def get_user_request_for_chat(self, user_id: int, chat_id: int) -> Optional[PendingChannelRequest]:
        """Get user's request for specific chat."""
        pass
    
    # Channel statistics
    @abstractmethod
    async def get_channel_statistics(self, channel_id: int) -> Dict[str, Any]:
        """Get statistics for specific channel."""
        pass
    
    @abstractmethod
    async def get_global_channel_statistics(self) -> Dict[str, Any]:
        """Get global channel system statistics."""
        pass
    
    @abstractmethod
    async def get_channel_engagement_stats(self, channel_id: int, days: int = 30) -> Dict[str, Any]:
        """Get channel engagement statistics for last N days."""
        pass
    
    # Bulk operations
    @abstractmethod
    async def get_channels_by_ids(self, channel_ids: List[int]) -> List[Channel]:
        """Get multiple channels by IDs."""
        pass
    
    @abstractmethod
    async def get_free_channels(self) -> List[Channel]:
        """Get all free channels."""
        pass
    
    @abstractmethod
    async def get_vip_channels(self) -> List[Channel]:
        """Get all VIP channels."""
        pass
    
    @abstractmethod
    async def get_engagement_channels(self) -> List[Channel]:
        """Get all engagement channels."""
        pass
    
    @abstractmethod
    async def update_channels_bulk(self, channel_updates: List[Dict[str, Any]]) -> List[Channel]:
        """Update multiple channels in bulk."""
        pass
    
    # Request management
    @abstractmethod
    async def get_approved_requests(self, days: int = 30) -> List[PendingChannelRequest]:
        """Get recently approved requests."""
        pass
    
    @abstractmethod
    async def get_requests_by_date_range(self, start_date: datetime, end_date: datetime) -> List[PendingChannelRequest]:
        """Get requests within date range."""
        pass
    
    @abstractmethod
    async def cleanup_old_requests(self, days: int = 30) -> int:
        """Clean up old processed requests and return count deleted."""
        pass
    
    @abstractmethod
    async def mark_social_media_message_sent(self, request_id: int) -> bool:
        """Mark social media message as sent for request."""
        pass
    
    @abstractmethod
    async def mark_welcome_message_sent(self, request_id: int) -> bool:
        """Mark welcome message as sent for request."""
        pass