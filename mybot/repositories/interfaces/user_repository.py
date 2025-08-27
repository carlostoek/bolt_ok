"""User aggregate repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from database.models import User, UserStats, Badge, UserBadge


class IUserRepository(ABC):
    """Repository interface for User aggregate operations."""
    
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        pass
    
    @abstractmethod
    async def create(self, user_data: Dict[str, Any]) -> User:
        """Create a new user."""
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        """Update existing user."""
        pass
    
    @abstractmethod
    async def delete(self, user_id: int) -> bool:
        """Delete user by ID."""
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        pass
    
    @abstractmethod
    async def get_top_by_points(self, limit: int = 10) -> List[User]:
        """Get top users by points."""
        pass
    
    @abstractmethod
    async def get_admins(self) -> List[User]:
        """Get all admin users."""
        pass
    
    @abstractmethod
    async def get_vip_users(self) -> List[User]:
        """Get all VIP users."""
        pass
    
    @abstractmethod
    async def search_by_name(self, name: str, limit: int = 50) -> List[User]:
        """Search users by first/last name."""
        pass
    
    # User stats operations
    @abstractmethod
    async def get_user_stats(self, user_id: int) -> Optional[UserStats]:
        """Get user statistics."""
        pass
    
    @abstractmethod
    async def update_user_stats(self, user_stats: UserStats) -> UserStats:
        """Update user statistics."""
        pass
    
    @abstractmethod
    async def create_user_stats(self, user_id: int) -> UserStats:
        """Create user statistics."""
        pass
    
    # Badge operations
    @abstractmethod
    async def get_user_badges(self, user_id: int) -> List[Badge]:
        """Get all badges for a user."""
        pass
    
    @abstractmethod
    async def award_badge(self, user_id: int, badge_id: int) -> UserBadge:
        """Award a badge to user."""
        pass
    
    @abstractmethod
    async def has_badge(self, user_id: int, badge_id: int) -> bool:
        """Check if user has specific badge."""
        pass
    
    @abstractmethod
    async def revoke_badge(self, user_id: int, badge_id: int) -> bool:
        """Revoke badge from user."""
        pass
    
    # Bulk operations
    @abstractmethod
    async def get_users_by_ids(self, user_ids: List[int]) -> List[User]:
        """Get multiple users by IDs."""
        pass
    
    @abstractmethod
    async def get_active_users_count(self, days: int = 30) -> int:
        """Get count of active users in last N days."""
        pass
    
    @abstractmethod
    async def get_users_with_role(self, role: str) -> List[User]:
        """Get users with specific role."""
        pass