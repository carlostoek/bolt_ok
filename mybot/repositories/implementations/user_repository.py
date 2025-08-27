"""SQLAlchemy implementation of User repository."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, text
from sqlalchemy.orm import selectinload

from database.models import User, UserStats, Badge, UserBadge
from ..interfaces.user_repository import IUserRepository
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SqlUserRepository(BaseRepository[User], IUserRepository):
    """SQLAlchemy implementation of User repository with query optimization."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by Telegram ID with optimized query."""
        try:
            # Use direct get for primary key lookups (most efficient)
            return await self.session.get(User, user_id)
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def create(self, user_data: Dict[str, Any]) -> User:
        """Create a new user with validation."""
        user = User(**user_data)
        return await super().create(user)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username with case-insensitive search."""
        stmt = select(User).where(func.lower(User.username) == func.lower(username))
        return await self._execute_query(stmt, single=True)
    
    async def get_top_by_points(self, limit: int = 10) -> List[User]:
        """Get top users by points with optimized query."""
        stmt = (
            select(User)
            .where(User.points > 0)  # Filter out users with 0 points
            .order_by(desc(User.points))
            .limit(limit)
        )
        return await self._execute_query(stmt, use_cache=True)
    
    async def get_admins(self) -> List[User]:
        """Get all admin users."""
        return await self.find_by_conditions(is_admin=True)
    
    async def get_vip_users(self) -> List[User]:
        """Get all VIP users (active VIP subscription)."""
        now = datetime.utcnow()
        stmt = select(User).where(
            and_(
                User.role == "vip",
                or_(User.vip_expires_at.is_(None), User.vip_expires_at > now)
            )
        )
        return await self._execute_query(stmt)
    
    async def search_by_name(self, name: str, limit: int = 50) -> List[User]:
        """Search users by first/last name with optimized full-text search."""
        return await self.search(
            query=name,
            search_fields=['first_name', 'last_name', 'username'],
            limit=limit
        )
    
    # User stats operations with optimized queries
    async def get_user_stats(self, user_id: int) -> Optional[UserStats]:
        """Get user statistics with efficient lookup."""
        return await self.session.get(UserStats, user_id)
    
    async def update_user_stats(self, user_stats: UserStats) -> UserStats:
        """Update user statistics."""
        await self.session.commit()
        await self.session.refresh(user_stats)
        return user_stats
    
    async def create_user_stats(self, user_id: int) -> UserStats:
        """Create user statistics."""
        user_stats = UserStats(user_id=user_id)
        self.session.add(user_stats)
        await self.session.commit()
        await self.session.refresh(user_stats)
        return user_stats
    
    # Badge operations with optimized joins
    async def get_user_badges(self, user_id: int) -> List[Badge]:
        """Get all badges for a user with optimized join."""
        stmt = (
            select(Badge)
            .join(UserBadge)
            .where(UserBadge.user_id == user_id)
            .order_by(UserBadge.awarded_at.desc())
        )
        return await self._execute_query(stmt)
    
    async def award_badge(self, user_id: int, badge_id: int) -> UserBadge:
        """Award a badge to user with duplicate prevention."""
        # Check if user already has badge
        existing = await self.session.get(UserBadge, (user_id, badge_id))
        if existing:
            return existing
        
        user_badge = UserBadge(user_id=user_id, badge_id=badge_id)
        self.session.add(user_badge)
        await self.session.commit()
        await self.session.refresh(user_badge)
        return user_badge
    
    async def has_badge(self, user_id: int, badge_id: int) -> bool:
        """Check if user has specific badge with efficient lookup."""
        return await self.session.get(UserBadge, (user_id, badge_id)) is not None
    
    async def revoke_badge(self, user_id: int, badge_id: int) -> bool:
        """Revoke badge from user."""
        user_badge = await self.session.get(UserBadge, (user_id, badge_id))
        if user_badge:
            await self.session.delete(user_badge)
            await self.session.commit()
            return True
        return False
    
    # Bulk operations with optimized queries
    async def get_users_by_ids(self, user_ids: List[int]) -> List[User]:
        """Get multiple users by IDs with single query."""
        if not user_ids:
            return []
        
        stmt = select(User).where(User.id.in_(user_ids))
        return await self._execute_query(stmt)
    
    async def get_active_users_count(self, days: int = 30) -> int:
        """Get count of active users in last N days with optimized query."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Use raw SQL for better performance on large datasets
        query = text("""
            SELECT COUNT(DISTINCT u.id) 
            FROM users u 
            JOIN user_stats us ON u.id = us.user_id 
            WHERE us.last_activity_at > :cutoff_date
        """)
        
        result = await self.session.execute(query, {"cutoff_date": cutoff_date})
        return result.scalar()
    
    async def get_users_with_role(self, role: str) -> List[User]:
        """Get users with specific role."""
        return await self.find_by_conditions(role=role)
    
    # Advanced analytics queries
    async def get_user_engagement_metrics(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user engagement metrics."""
        user = await self.get_by_id(user_id)
        if not user:
            return {}
        
        user_stats = await self.get_user_stats(user_id)
        user_badges = await self.get_user_badges(user_id)
        
        # Calculate days since registration
        days_registered = (datetime.utcnow() - user.created_at).days if user.created_at else 0
        
        return {
            "user_id": user_id,
            "points": user.points,
            "level": user.level,
            "days_registered": days_registered,
            "messages_sent": user_stats.messages_sent if user_stats else 0,
            "checkin_streak": user_stats.checkin_streak if user_stats else 0,
            "badge_count": len(user_badges),
            "last_activity": user_stats.last_activity_at if user_stats else None,
            "engagement_score": self._calculate_engagement_score(user, user_stats, user_badges)
        }
    
    def _calculate_engagement_score(self, user: User, stats: Optional[UserStats], badges: List[Badge]) -> float:
        """Calculate user engagement score based on multiple factors."""
        score = 0.0
        
        # Points contribution (normalized)
        score += min(user.points / 1000.0, 10.0)  # Max 10 points from user points
        
        # Level contribution
        score += user.level * 0.5  # 0.5 points per level
        
        # Activity contribution
        if stats:
            score += min(stats.messages_sent / 100.0, 5.0)  # Max 5 points from messages
            score += stats.checkin_streak * 0.1  # 0.1 points per streak day
        
        # Badge contribution
        score += len(badges) * 0.2  # 0.2 points per badge
        
        return round(score, 2)
    
    async def get_leaderboard_with_rankings(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get leaderboard with user rankings and additional stats."""
        stmt = (
            select(User)
            .where(User.points > 0)
            .order_by(desc(User.points))
            .limit(limit)
        )
        
        users = await self._execute_query(stmt)
        
        leaderboard = []
        for i, user in enumerate(users, 1):
            user_stats = await self.get_user_stats(user.id)
            leaderboard.append({
                "rank": i,
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "points": user.points,
                "level": user.level,
                "messages_sent": user_stats.messages_sent if user_stats else 0,
                "checkin_streak": user_stats.checkin_streak if user_stats else 0
            })
        
        return leaderboard
    
    async def get_user_rank_by_points(self, user_id: int) -> Optional[int]:
        """Get user's rank in points leaderboard with efficient query."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        # Count users with more points
        stmt = select(func.count()).where(User.points > user.points)
        higher_ranked_count = await self._execute_query(stmt, single=True)
        
        return higher_ranked_count + 1  # Rank is count + 1