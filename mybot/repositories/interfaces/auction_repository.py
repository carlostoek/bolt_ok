"""Auction aggregate repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from database.models import Auction, Bid, AuctionParticipant, AuctionStatus
from datetime import datetime


class IAuctionRepository(ABC):
    """Repository interface for Auction aggregate operations."""
    
    # Auction operations
    @abstractmethod
    async def get_auction_by_id(self, auction_id: int) -> Optional[Auction]:
        """Get auction by ID."""
        pass
    
    @abstractmethod
    async def get_all_auctions(self) -> List[Auction]:
        """Get all auctions."""
        pass
    
    @abstractmethod
    async def get_auctions_by_status(self, status: AuctionStatus) -> List[Auction]:
        """Get auctions by status."""
        pass
    
    @abstractmethod
    async def get_active_auctions(self) -> List[Auction]:
        """Get all active auctions."""
        pass
    
    @abstractmethod
    async def get_pending_auctions(self) -> List[Auction]:
        """Get all pending auctions."""
        pass
    
    @abstractmethod
    async def get_ended_auctions(self) -> List[Auction]:
        """Get all ended auctions."""
        pass
    
    @abstractmethod
    async def create_auction(self, auction_data: Dict[str, Any]) -> Auction:
        """Create a new auction."""
        pass
    
    @abstractmethod
    async def update_auction(self, auction: Auction) -> Auction:
        """Update existing auction."""
        pass
    
    @abstractmethod
    async def delete_auction(self, auction_id: int) -> bool:
        """Delete auction."""
        pass
    
    @abstractmethod
    async def search_auctions_by_name(self, query: str, limit: int = 50) -> List[Auction]:
        """Search auctions by name."""
        pass
    
    # Auction lifecycle management
    @abstractmethod
    async def start_auction(self, auction_id: int) -> Auction:
        """Start a pending auction."""
        pass
    
    @abstractmethod
    async def end_auction(self, auction_id: int, winner_id: Optional[int] = None) -> Auction:
        """End an active auction."""
        pass
    
    @abstractmethod
    async def cancel_auction(self, auction_id: int) -> Auction:
        """Cancel an auction."""
        pass
    
    @abstractmethod
    async def extend_auction(self, auction_id: int, minutes: int) -> Auction:
        """Extend auction end time."""
        pass
    
    # Bid operations
    @abstractmethod
    async def get_bid_by_id(self, bid_id: int) -> Optional[Bid]:
        """Get bid by ID."""
        pass
    
    @abstractmethod
    async def get_auction_bids(self, auction_id: int) -> List[Bid]:
        """Get all bids for an auction."""
        pass
    
    @abstractmethod
    async def get_user_bids(self, user_id: int) -> List[Bid]:
        """Get all bids by a user."""
        pass
    
    @abstractmethod
    async def get_user_auction_bids(self, user_id: int, auction_id: int) -> List[Bid]:
        """Get user's bids for specific auction."""
        pass
    
    @abstractmethod
    async def create_bid(self, bid_data: Dict[str, Any]) -> Bid:
        """Create a new bid."""
        pass
    
    @abstractmethod
    async def get_highest_bid(self, auction_id: int) -> Optional[Bid]:
        """Get highest bid for auction."""
        pass
    
    @abstractmethod
    async def get_winning_bid(self, auction_id: int) -> Optional[Bid]:
        """Get current winning bid for auction."""
        pass
    
    @abstractmethod
    async def update_winning_bid(self, auction_id: int, bid_id: int) -> bool:
        """Update which bid is winning for auction."""
        pass
    
    # Participant management
    @abstractmethod
    async def get_auction_participants(self, auction_id: int) -> List[AuctionParticipant]:
        """Get all participants in an auction."""
        pass
    
    @abstractmethod
    async def add_auction_participant(self, auction_id: int, user_id: int) -> AuctionParticipant:
        """Add user as auction participant."""
        pass
    
    @abstractmethod
    async def remove_auction_participant(self, auction_id: int, user_id: int) -> bool:
        """Remove user from auction participants."""
        pass
    
    @abstractmethod
    async def is_user_participating(self, auction_id: int, user_id: int) -> bool:
        """Check if user is participating in auction."""
        pass
    
    @abstractmethod
    async def get_user_participated_auctions(self, user_id: int) -> List[Auction]:
        """Get auctions user has participated in."""
        pass
    
    # Notification management
    @abstractmethod
    async def enable_notifications_for_participant(self, auction_id: int, user_id: int) -> bool:
        """Enable notifications for auction participant."""
        pass
    
    @abstractmethod
    async def disable_notifications_for_participant(self, auction_id: int, user_id: int) -> bool:
        """Disable notifications for auction participant."""
        pass
    
    @abstractmethod
    async def get_participants_with_notifications(self, auction_id: int) -> List[int]:
        """Get participant user IDs with notifications enabled."""
        pass
    
    @abstractmethod
    async def update_last_notified(self, auction_id: int, user_id: int) -> bool:
        """Update last notification timestamp for participant."""
        pass
    
    # Auction statistics and analytics
    @abstractmethod
    async def get_auction_statistics(self, auction_id: int) -> Dict[str, Any]:
        """Get statistics for specific auction."""
        pass
    
    @abstractmethod
    async def get_user_auction_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get user's auction participation statistics."""
        pass
    
    @abstractmethod
    async def get_global_auction_statistics(self) -> Dict[str, Any]:
        """Get global auction system statistics."""
        pass
    
    @abstractmethod
    async def get_auction_activity_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get auction activity summary for last N days."""
        pass
    
    # Time-based queries
    @abstractmethod
    async def get_auctions_ending_soon(self, minutes: int = 60) -> List[Auction]:
        """Get auctions ending within specified minutes."""
        pass
    
    @abstractmethod
    async def get_auctions_starting_soon(self, minutes: int = 60) -> List[Auction]:
        """Get auctions starting within specified minutes."""
        pass
    
    @abstractmethod
    async def get_expired_auctions(self) -> List[Auction]:
        """Get auctions that have passed end time but not marked as ended."""
        pass
    
    # Bulk operations
    @abstractmethod
    async def get_auctions_by_ids(self, auction_ids: List[int]) -> List[Auction]:
        """Get multiple auctions by IDs."""
        pass
    
    @abstractmethod
    async def get_auctions_by_creator(self, creator_id: int) -> List[Auction]:
        """Get auctions created by specific user."""
        pass
    
    @abstractmethod
    async def get_recent_auctions(self, days: int = 7) -> List[Auction]:
        """Get recently created auctions."""
        pass
    
    @abstractmethod
    async def cleanup_old_ended_auctions(self, days: int = 90) -> int:
        """Clean up old ended auctions and return count deleted."""
        pass