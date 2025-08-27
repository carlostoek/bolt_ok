"""Point aggregate repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from database.models import User
from database.transaction_models import PointTransaction
from datetime import datetime


class IPointRepository(ABC):
    """Repository interface for Point aggregate operations."""
    
    # Point balance operations
    @abstractmethod
    async def get_user_balance(self, user_id: int) -> float:
        """Get user's current point balance."""
        pass
    
    @abstractmethod
    async def add_points(self, user_id: int, amount: float, source: str, description: str = "") -> PointTransaction:
        """Add points to user account."""
        pass
    
    @abstractmethod
    async def deduct_points(self, user_id: int, amount: float, source: str, description: str = "") -> Optional[PointTransaction]:
        """Deduct points from user account if sufficient balance."""
        pass
    
    @abstractmethod
    async def transfer_points(self, from_user_id: int, to_user_id: int, amount: float, description: str = "") -> bool:
        """Transfer points between users."""
        pass
    
    # Transaction history
    @abstractmethod
    async def get_transaction_history(self, user_id: int, limit: int = 100) -> List[PointTransaction]:
        """Get user's point transaction history."""
        pass
    
    @abstractmethod
    async def get_transactions_by_source(self, user_id: int, source: str) -> List[PointTransaction]:
        """Get transactions by source."""
        pass
    
    @abstractmethod
    async def get_transactions_by_date_range(self, user_id: int, start_date: datetime, end_date: datetime) -> List[PointTransaction]:
        """Get transactions within date range."""
        pass
    
    # Bulk operations
    @abstractmethod
    async def get_top_users_by_points(self, limit: int = 10) -> List[User]:
        """Get users with highest point balances."""
        pass
    
    @abstractmethod
    async def get_users_with_balance_above(self, threshold: float) -> List[User]:
        """Get users with balance above threshold."""
        pass
    
    @abstractmethod
    async def get_users_with_balance_below(self, threshold: float) -> List[User]:
        """Get users with balance below threshold."""
        pass
    
    # Statistics and reporting
    @abstractmethod
    async def get_total_points_in_system(self) -> float:
        """Get total points across all users."""
        pass
    
    @abstractmethod
    async def get_point_statistics(self) -> Dict[str, Any]:
        """Get comprehensive point system statistics."""
        pass
    
    @abstractmethod
    async def get_daily_point_activity(self, date: datetime) -> Dict[str, Any]:
        """Get point activity for specific date."""
        pass
    
    @abstractmethod
    async def get_user_point_activity_summary(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get user's point activity summary for last N days."""
        pass
    
    # Validation and checks
    @abstractmethod
    async def has_sufficient_balance(self, user_id: int, amount: float) -> bool:
        """Check if user has sufficient balance for transaction."""
        pass
    
    @abstractmethod
    async def validate_transaction_integrity(self, user_id: int) -> bool:
        """Validate user's transaction history integrity."""
        pass
    
    # Batch operations
    @abstractmethod
    async def add_points_bulk(self, transactions: List[Dict[str, Any]]) -> List[PointTransaction]:
        """Add points to multiple users in batch."""
        pass
    
    @abstractmethod
    async def get_leaderboard(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get point leaderboard with rankings."""
        pass
    
    @abstractmethod
    async def get_user_rank_by_points(self, user_id: int) -> Optional[int]:
        """Get user's rank in points leaderboard."""
        pass