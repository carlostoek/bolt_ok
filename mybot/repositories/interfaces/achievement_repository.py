"""Achievement aggregate repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from database.models import Achievement, UserAchievement, Badge, UserBadge
from datetime import datetime


class IAchievementRepository(ABC):
    """Repository interface for Achievement aggregate operations."""
    
    # Achievement operations
    @abstractmethod
    async def get_achievement_by_id(self, achievement_id: str) -> Optional[Achievement]:
        """Get achievement by ID."""
        pass
    
    @abstractmethod
    async def get_all_achievements(self) -> List[Achievement]:
        """Get all achievements."""
        pass
    
    @abstractmethod
    async def get_achievements_by_condition_type(self, condition_type: str) -> List[Achievement]:
        """Get achievements by condition type."""
        pass
    
    @abstractmethod
    async def create_achievement(self, achievement_data: Dict[str, Any]) -> Achievement:
        """Create a new achievement."""
        pass
    
    @abstractmethod
    async def update_achievement(self, achievement: Achievement) -> Achievement:
        """Update existing achievement."""
        pass
    
    @abstractmethod
    async def delete_achievement(self, achievement_id: str) -> bool:
        """Delete achievement."""
        pass
    
    # User achievement operations
    @abstractmethod
    async def get_user_achievements(self, user_id: int) -> List[Achievement]:
        """Get all achievements unlocked by user."""
        pass
    
    @abstractmethod
    async def unlock_achievement_for_user(self, user_id: int, achievement_id: str) -> UserAchievement:
        """Unlock achievement for user."""
        pass
    
    @abstractmethod
    async def has_user_unlocked_achievement(self, user_id: int, achievement_id: str) -> bool:
        """Check if user has unlocked specific achievement."""
        pass
    
    @abstractmethod
    async def get_user_pending_achievements(self, user_id: int) -> List[Achievement]:
        """Get achievements not yet unlocked by user."""
        pass
    
    # Badge operations
    @abstractmethod
    async def get_badge_by_id(self, badge_id: int) -> Optional[Badge]:
        """Get badge by ID."""
        pass
    
    @abstractmethod
    async def get_all_badges(self) -> List[Badge]:
        """Get all badges."""
        pass
    
    @abstractmethod
    async def get_active_badges(self) -> List[Badge]:
        """Get all active badges."""
        pass
    
    @abstractmethod
    async def create_badge(self, badge_data: Dict[str, Any]) -> Badge:
        """Create a new badge."""
        pass
    
    @abstractmethod
    async def update_badge(self, badge: Badge) -> Badge:
        """Update existing badge."""
        pass
    
    @abstractmethod
    async def delete_badge(self, badge_id: int) -> bool:
        """Delete badge."""
        pass
    
    # User badge operations
    @abstractmethod
    async def get_user_badges(self, user_id: int) -> List[Badge]:
        """Get all badges awarded to user."""
        pass
    
    @abstractmethod
    async def award_badge_to_user(self, user_id: int, badge_id: int) -> UserBadge:
        """Award badge to user."""
        pass
    
    @abstractmethod
    async def has_user_badge(self, user_id: int, badge_id: int) -> bool:
        """Check if user has specific badge."""
        pass
    
    @abstractmethod
    async def revoke_badge_from_user(self, user_id: int, badge_id: int) -> bool:
        """Revoke badge from user."""
        pass
    
    @abstractmethod
    async def get_badge_holders(self, badge_id: int) -> List[int]:
        """Get all user IDs who have specific badge."""
        pass
    
    # Achievement checking and validation
    @abstractmethod
    async def check_achievement_conditions(self, user_id: int, condition_type: str, value: Any) -> List[Achievement]:
        """Check which achievements user qualifies for based on condition."""
        pass
    
    @abstractmethod
    async def get_achievements_by_points_threshold(self, points: float) -> List[Achievement]:
        """Get achievements triggered by points threshold."""
        pass
    
    @abstractmethod
    async def get_achievements_by_message_count(self, message_count: int) -> List[Achievement]:
        """Get achievements triggered by message count."""
        pass
    
    @abstractmethod
    async def get_achievements_by_checkin_streak(self, streak: int) -> List[Achievement]:
        """Get achievements triggered by checkin streak."""
        pass
    
    # Statistics and reporting
    @abstractmethod
    async def get_achievement_statistics(self, achievement_id: str) -> Dict[str, Any]:
        """Get statistics for specific achievement."""
        pass
    
    @abstractmethod
    async def get_user_achievement_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get user's achievement statistics."""
        pass
    
    @abstractmethod
    async def get_global_achievement_statistics(self) -> Dict[str, Any]:
        """Get global achievement system statistics."""
        pass
    
    @abstractmethod
    async def get_badge_statistics(self, badge_id: int) -> Dict[str, Any]:
        """Get statistics for specific badge."""
        pass
    
    @abstractmethod
    async def get_user_badge_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get user's badge statistics."""
        pass
    
    # VIP badge operations
    @abstractmethod
    async def get_vip_badges(self) -> List[Badge]:
        """Get all VIP-granting badges."""
        pass
    
    @abstractmethod
    async def get_users_with_vip_badges(self) -> List[int]:
        """Get users who have VIP-granting badges."""
        pass
    
    @abstractmethod
    async def get_user_vip_badge_expiry(self, user_id: int) -> Optional[datetime]:
        """Get VIP badge expiry date for user."""
        pass
    
    # Bulk operations
    @abstractmethod
    async def get_achievements_by_ids(self, achievement_ids: List[str]) -> List[Achievement]:
        """Get multiple achievements by IDs."""
        pass
    
    @abstractmethod
    async def get_badges_by_ids(self, badge_ids: List[int]) -> List[Badge]:
        """Get multiple badges by IDs."""
        pass
    
    @abstractmethod
    async def get_recent_achievements(self, days: int = 7) -> List[UserAchievement]:
        """Get recently unlocked achievements."""
        pass
    
    @abstractmethod
    async def get_recent_badges(self, days: int = 7) -> List[UserBadge]:
        """Get recently awarded badges."""
        pass