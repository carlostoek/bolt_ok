"""Mission aggregate repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from database.models import Mission, UserMissionEntry
from datetime import datetime


class IMissionRepository(ABC):
    """Repository interface for Mission aggregate operations."""
    
    # Mission operations
    @abstractmethod
    async def get_mission_by_id(self, mission_id: str) -> Optional[Mission]:
        """Get mission by ID."""
        pass
    
    @abstractmethod
    async def get_active_missions(self) -> List[Mission]:
        """Get all active missions."""
        pass
    
    @abstractmethod
    async def get_missions_by_type(self, mission_type: str) -> List[Mission]:
        """Get missions by type (one_time, daily, weekly)."""
        pass
    
    @abstractmethod
    async def create_mission(self, mission_data: Dict[str, Any]) -> Mission:
        """Create a new mission."""
        pass
    
    @abstractmethod
    async def update_mission(self, mission: Mission) -> Mission:
        """Update existing mission."""
        pass
    
    @abstractmethod
    async def delete_mission(self, mission_id: str) -> bool:
        """Delete mission."""
        pass
    
    @abstractmethod
    async def search_missions_by_name(self, query: str, limit: int = 50) -> List[Mission]:
        """Search missions by name."""
        pass
    
    # User mission progress operations
    @abstractmethod
    async def get_user_mission_entry(self, user_id: int, mission_id: str) -> Optional[UserMissionEntry]:
        """Get user's progress on specific mission."""
        pass
    
    @abstractmethod
    async def get_user_mission_entries(self, user_id: int) -> List[UserMissionEntry]:
        """Get all user mission entries."""
        pass
    
    @abstractmethod
    async def create_user_mission_entry(self, user_id: int, mission_id: str) -> UserMissionEntry:
        """Create user mission entry."""
        pass
    
    @abstractmethod
    async def update_user_mission_progress(self, entry: UserMissionEntry) -> UserMissionEntry:
        """Update user mission progress."""
        pass
    
    @abstractmethod
    async def complete_user_mission(self, user_id: int, mission_id: str) -> UserMissionEntry:
        """Mark mission as completed for user."""
        pass
    
    @abstractmethod
    async def get_user_completed_missions(self, user_id: int) -> List[Mission]:
        """Get all completed missions for user."""
        pass
    
    @abstractmethod
    async def get_user_pending_missions(self, user_id: int) -> List[Mission]:
        """Get all pending missions for user."""
        pass
    
    @abstractmethod
    async def get_user_available_missions(self, user_id: int) -> List[Mission]:
        """Get missions available to user (not started or in progress)."""
        pass
    
    # Progress tracking
    @abstractmethod
    async def increment_mission_progress(self, user_id: int, mission_id: str, amount: int = 1) -> Optional[UserMissionEntry]:
        """Increment progress on user mission."""
        pass
    
    @abstractmethod
    async def set_mission_progress(self, user_id: int, mission_id: str, progress: int) -> Optional[UserMissionEntry]:
        """Set specific progress value on user mission."""
        pass
    
    @abstractmethod
    async def get_user_mission_progress_percentage(self, user_id: int, mission_id: str) -> float:
        """Get progress percentage for specific mission."""
        pass
    
    # Mission statistics
    @abstractmethod
    async def get_mission_completion_stats(self, mission_id: str) -> Dict[str, Any]:
        """Get completion statistics for a mission."""
        pass
    
    @abstractmethod
    async def get_user_mission_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get user's overall mission statistics."""
        pass
    
    @abstractmethod
    async def get_global_mission_statistics(self) -> Dict[str, Any]:
        """Get global mission system statistics."""
        pass
    
    # Daily/Weekly mission resets
    @abstractmethod
    async def get_daily_missions_for_user(self, user_id: int) -> List[Mission]:
        """Get daily missions available to user."""
        pass
    
    @abstractmethod
    async def get_weekly_missions_for_user(self, user_id: int) -> List[Mission]:
        """Get weekly missions available to user."""
        pass
    
    @abstractmethod
    async def reset_daily_missions_for_user(self, user_id: int) -> bool:
        """Reset daily missions for user."""
        pass
    
    @abstractmethod
    async def reset_weekly_missions_for_user(self, user_id: int) -> bool:
        """Reset weekly missions for user."""
        pass
    
    # Bulk operations
    @abstractmethod
    async def get_missions_by_ids(self, mission_ids: List[str]) -> List[Mission]:
        """Get multiple missions by IDs."""
        pass
    
    @abstractmethod
    async def get_users_with_mission_progress(self, mission_id: str) -> List[int]:
        """Get user IDs who have progress on specific mission."""
        pass
    
    @abstractmethod
    async def get_recently_completed_missions(self, days: int = 7) -> List[UserMissionEntry]:
        """Get recently completed mission entries."""
        pass