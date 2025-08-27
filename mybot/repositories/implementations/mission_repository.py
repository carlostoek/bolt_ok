"""SQLAlchemy implementation of Mission repository."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, text
from sqlalchemy.orm import selectinload

from database.models import Mission, UserMissionEntry
from ..interfaces.mission_repository import IMissionRepository
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SqlMissionRepository(BaseRepository[Mission], IMissionRepository):
    """SQLAlchemy implementation of Mission repository with query optimization."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Mission)
    
    # Mission operations with optimized queries
    async def get_mission_by_id(self, mission_id: str) -> Optional[Mission]:
        """Get mission by ID with efficient lookup."""
        return await self.session.get(Mission, mission_id)
    
    async def get_active_missions(self) -> List[Mission]:
        """Get all active missions with caching."""
        stmt = (
            select(Mission)
            .where(Mission.is_active == True)
            .order_by(Mission.created_at)
        )
        return await self._execute_query(stmt, use_cache=True)
    
    async def get_missions_by_type(self, mission_type: str) -> List[Mission]:
        """Get missions by type with efficient filtering."""
        stmt = (
            select(Mission)
            .where(
                and_(
                    Mission.type == mission_type,
                    Mission.is_active == True
                )
            )
            .order_by(Mission.created_at)
        )
        return await self._execute_query(stmt, use_cache=True)
    
    async def create_mission(self, mission_data: Dict[str, Any]) -> Mission:
        """Create a new mission."""
        mission = Mission(**mission_data)
        return await super().create(mission)
    
    async def update_mission(self, mission: Mission) -> Mission:
        """Update existing mission."""
        self._clear_cache()
        return await super().update(mission)
    
    async def delete_mission(self, mission_id: str) -> bool:
        """Delete mission (soft delete by marking inactive)."""
        mission = await self.get_mission_by_id(mission_id)
        if mission:
            mission.is_active = False
            await self.update_mission(mission)
            return True
        return False
    
    async def search_missions_by_name(self, query: str, limit: int = 50) -> List[Mission]:
        """Search missions by name."""
        return await self.search(
            query=query,
            search_fields=['name', 'description'],
            limit=limit
        )
    
    # User mission progress operations with optimized queries
    async def get_user_mission_entry(self, user_id: int, mission_id: str) -> Optional[UserMissionEntry]:
        """Get user's progress on specific mission."""
        return await self.session.get(UserMissionEntry, (user_id, mission_id))
    
    async def get_user_mission_entries(self, user_id: int) -> List[UserMissionEntry]:
        """Get all user mission entries with eager loading."""
        stmt = (
            select(UserMissionEntry)
            .where(UserMissionEntry.user_id == user_id)
            .order_by(UserMissionEntry.completed_at.desc().nullslast())
        )
        return await self._execute_query(stmt)
    
    async def create_user_mission_entry(self, user_id: int, mission_id: str) -> UserMissionEntry:
        """Create user mission entry with duplicate prevention."""
        # Check if entry already exists
        existing = await self.get_user_mission_entry(user_id, mission_id)
        if existing:
            return existing
        
        entry = UserMissionEntry(
            user_id=user_id,
            mission_id=mission_id,
            progress_value=0,
            completed=False
        )
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry
    
    async def update_user_mission_progress(self, entry: UserMissionEntry) -> UserMissionEntry:
        """Update user mission progress."""
        await self.session.commit()
        await self.session.refresh(entry)
        return entry
    
    async def complete_user_mission(self, user_id: int, mission_id: str) -> UserMissionEntry:
        """Mark mission as completed for user."""
        entry = await self.get_user_mission_entry(user_id, mission_id)
        if not entry:
            entry = await self.create_user_mission_entry(user_id, mission_id)
        
        entry.completed = True
        entry.completed_at = datetime.utcnow()
        return await self.update_user_mission_progress(entry)
    
    async def get_user_completed_missions(self, user_id: int) -> List[Mission]:
        """Get all completed missions for user with optimized join."""
        stmt = (
            select(Mission)
            .join(UserMissionEntry)
            .where(
                and_(
                    UserMissionEntry.user_id == user_id,
                    UserMissionEntry.completed == True
                )
            )
            .order_by(UserMissionEntry.completed_at.desc())
        )
        return await self._execute_query(stmt)
    
    async def get_user_pending_missions(self, user_id: int) -> List[Mission]:
        """Get all pending missions for user (started but not completed)."""
        stmt = (
            select(Mission)
            .join(UserMissionEntry)
            .where(
                and_(
                    UserMissionEntry.user_id == user_id,
                    UserMissionEntry.completed == False,
                    Mission.is_active == True
                )
            )
            .order_by(Mission.created_at)
        )
        return await self._execute_query(stmt)
    
    async def get_user_available_missions(self, user_id: int) -> List[Mission]:
        """Get missions available to user (not started or in progress)."""
        # Subquery to get user's mission IDs
        user_missions_subq = (
            select(UserMissionEntry.mission_id)
            .where(UserMissionEntry.user_id == user_id)
        )
        
        stmt = (
            select(Mission)
            .where(
                and_(
                    Mission.is_active == True,
                    Mission.id.notin_(user_missions_subq)
                )
            )
            .order_by(Mission.created_at)
        )
        return await self._execute_query(stmt)
    
    # Progress tracking with atomic operations
    async def increment_mission_progress(self, user_id: int, mission_id: str, amount: int = 1) -> Optional[UserMissionEntry]:
        """Increment progress on user mission atomically."""
        async with self.session.begin():
            entry = await self.get_user_mission_entry(user_id, mission_id)
            if not entry:
                entry = await self.create_user_mission_entry(user_id, mission_id)
            
            entry.progress_value += amount
            
            # Check if mission is completed
            mission = await self.get_mission_by_id(mission_id)
            if mission and entry.progress_value >= mission.target_value and not entry.completed:
                entry.completed = True
                entry.completed_at = datetime.utcnow()
            
            await self.session.flush()
            await self.session.refresh(entry)
            return entry
    
    async def set_mission_progress(self, user_id: int, mission_id: str, progress: int) -> Optional[UserMissionEntry]:
        """Set specific progress value on user mission."""
        entry = await self.get_user_mission_entry(user_id, mission_id)
        if not entry:
            entry = await self.create_user_mission_entry(user_id, mission_id)
        
        entry.progress_value = progress
        
        # Check if mission is completed
        mission = await self.get_mission_by_id(mission_id)
        if mission and entry.progress_value >= mission.target_value and not entry.completed:
            entry.completed = True
            entry.completed_at = datetime.utcnow()
        
        return await self.update_user_mission_progress(entry)
    
    async def get_user_mission_progress_percentage(self, user_id: int, mission_id: str) -> float:
        """Get progress percentage for specific mission."""
        entry = await self.get_user_mission_entry(user_id, mission_id)
        if not entry:
            return 0.0
        
        mission = await self.get_mission_by_id(mission_id)
        if not mission or mission.target_value == 0:
            return 0.0
        
        return min((entry.progress_value / mission.target_value) * 100, 100.0)
    
    # Mission statistics with advanced analytics
    async def get_mission_completion_stats(self, mission_id: str) -> Dict[str, Any]:
        """Get completion statistics for a mission."""
        mission = await self.get_mission_by_id(mission_id)
        if not mission:
            return {}
        
        query = text("""
            SELECT 
                COUNT(*) as total_attempts,
                COUNT(CASE WHEN completed = true THEN 1 END) as completed_count,
                AVG(progress_value) as avg_progress,
                MAX(progress_value) as max_progress,
                MIN(progress_value) as min_progress,
                AVG(CASE WHEN completed = true THEN progress_value END) as avg_completion_progress
            FROM user_mission_entries 
            WHERE mission_id = :mission_id
        """)
        
        result = await self.session.execute(query, {"mission_id": mission_id})
        row = result.fetchone()
        
        if not row or row[0] == 0:
            return {
                "mission_id": mission_id,
                "mission_name": mission.name,
                "total_attempts": 0,
                "completed_count": 0,
                "completion_rate": 0.0,
                "avg_progress": 0.0
            }
        
        return {
            "mission_id": mission_id,
            "mission_name": mission.name,
            "target_value": mission.target_value,
            "total_attempts": row[0],
            "completed_count": row[1],
            "completion_rate": (row[1] / row[0]) * 100 if row[0] > 0 else 0.0,
            "avg_progress": float(row[2]) if row[2] else 0.0,
            "max_progress": row[3] if row[3] else 0,
            "min_progress": row[4] if row[4] else 0,
            "avg_completion_progress": float(row[5]) if row[5] else 0.0
        }
    
    async def get_user_mission_statistics(self, user_id: int) -> Dict[str, Any]:
        """Get user's overall mission statistics."""
        query = text("""
            SELECT 
                COUNT(*) as total_missions,
                COUNT(CASE WHEN completed = true THEN 1 END) as completed_missions,
                AVG(progress_value) as avg_progress,
                SUM(CASE WHEN completed = true THEN m.reward_points ELSE 0 END) as total_points_earned
            FROM user_mission_entries ume
            JOIN missions m ON ume.mission_id = m.id
            WHERE ume.user_id = :user_id
        """)
        
        result = await self.session.execute(query, {"user_id": user_id})
        row = result.fetchone()
        
        if not row:
            return {
                "user_id": user_id,
                "total_missions": 0,
                "completed_missions": 0,
                "completion_rate": 0.0,
                "avg_progress": 0.0,
                "total_points_earned": 0
            }
        
        return {
            "user_id": user_id,
            "total_missions": row[0],
            "completed_missions": row[1],
            "completion_rate": (row[1] / row[0]) * 100 if row[0] > 0 else 0.0,
            "avg_progress": float(row[2]) if row[2] else 0.0,
            "total_points_earned": row[3] if row[3] else 0
        }
    
    async def get_global_mission_statistics(self) -> Dict[str, Any]:
        """Get global mission system statistics."""
        query = text("""
            SELECT 
                COUNT(DISTINCT m.id) as total_missions,
                COUNT(DISTINCT CASE WHEN m.is_active = true THEN m.id END) as active_missions,
                COUNT(DISTINCT ume.user_id) as users_with_missions,
                COUNT(*) as total_attempts,
                COUNT(CASE WHEN ume.completed = true THEN 1 END) as total_completions,
                AVG(ume.progress_value) as avg_progress,
                SUM(CASE WHEN ume.completed = true THEN m.reward_points ELSE 0 END) as total_points_distributed
            FROM missions m
            LEFT JOIN user_mission_entries ume ON m.id = ume.mission_id
        """)
        
        result = await self.session.execute(query)
        row = result.fetchone()
        
        return {
            "total_missions": row[0],
            "active_missions": row[1],
            "users_with_missions": row[2],
            "total_attempts": row[3],
            "total_completions": row[4],
            "global_completion_rate": (row[4] / row[3]) * 100 if row[3] > 0 else 0.0,
            "avg_progress": float(row[5]) if row[5] else 0.0,
            "total_points_distributed": row[6] if row[6] else 0
        }
    
    # Daily/Weekly mission resets with efficient bulk operations
    async def get_daily_missions_for_user(self, user_id: int) -> List[Mission]:
        """Get daily missions available to user."""
        return await self.get_missions_by_type("daily")
    
    async def get_weekly_missions_for_user(self, user_id: int) -> List[Mission]:
        """Get weekly missions available to user."""
        return await self.get_missions_by_type("weekly")
    
    async def reset_daily_missions_for_user(self, user_id: int) -> bool:
        """Reset daily missions for user."""
        daily_missions = await self.get_daily_missions_for_user(user_id)
        daily_mission_ids = [m.id for m in daily_missions]
        
        if not daily_mission_ids:
            return True
        
        # Delete existing daily mission entries
        query = text("""
            DELETE FROM user_mission_entries 
            WHERE user_id = :user_id AND mission_id = ANY(:mission_ids)
        """)
        
        await self.session.execute(query, {
            "user_id": user_id,
            "mission_ids": daily_mission_ids
        })
        await self.session.commit()
        
        return True
    
    async def reset_weekly_missions_for_user(self, user_id: int) -> bool:
        """Reset weekly missions for user."""
        weekly_missions = await self.get_weekly_missions_for_user(user_id)
        weekly_mission_ids = [m.id for m in weekly_missions]
        
        if not weekly_mission_ids:
            return True
        
        # Delete existing weekly mission entries
        query = text("""
            DELETE FROM user_mission_entries 
            WHERE user_id = :user_id AND mission_id = ANY(:mission_ids)
        """)
        
        await self.session.execute(query, {
            "user_id": user_id,
            "mission_ids": weekly_mission_ids
        })
        await self.session.commit()
        
        return True
    
    # Bulk operations with performance optimization
    async def get_missions_by_ids(self, mission_ids: List[str]) -> List[Mission]:
        """Get multiple missions by IDs with single query."""
        if not mission_ids:
            return []
        
        stmt = select(Mission).where(Mission.id.in_(mission_ids))
        return await self._execute_query(stmt)
    
    async def get_users_with_mission_progress(self, mission_id: str) -> List[int]:
        """Get user IDs who have progress on specific mission."""
        stmt = (
            select(UserMissionEntry.user_id)
            .where(UserMissionEntry.mission_id == mission_id)
            .distinct()
        )
        result = await self._execute_query(stmt)
        return [row for row in result]
    
    async def get_recently_completed_missions(self, days: int = 7) -> List[UserMissionEntry]:
        """Get recently completed mission entries."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(UserMissionEntry)
            .where(
                and_(
                    UserMissionEntry.completed == True,
                    UserMissionEntry.completed_at >= cutoff_date
                )
            )
            .order_by(UserMissionEntry.completed_at.desc())
        )
        return await self._execute_query(stmt)