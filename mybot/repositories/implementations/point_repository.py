"""SQLAlchemy implementation of Point repository."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, text
from sqlalchemy.orm import selectinload

from database.models import User
from database.transaction_models import PointTransaction
from ..interfaces.point_repository import IPointRepository
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SqlPointRepository(BaseRepository[PointTransaction], IPointRepository):
    """SQLAlchemy implementation of Point repository with advanced query optimization."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, PointTransaction)
    
    # Point balance operations with optimized queries
    async def get_user_balance(self, user_id: int) -> float:
        """Get user's current point balance with efficient lookup."""
        user = await self.session.get(User, user_id)
        return user.points if user else 0.0
    
    async def add_points(self, user_id: int, amount: float, source: str, description: str = "") -> PointTransaction:
        """Add points to user account with atomic transaction."""
        async with self.session.begin():
            # Get or create user
            user = await self.session.get(User, user_id)
            if not user:
                user = User(id=user_id, points=0.0)
                self.session.add(user)
                await self.session.flush()  # Ensure user is persisted
            
            # Calculate new balance
            old_balance = user.points
            new_balance = old_balance + amount
            
            # Create transaction record
            transaction = PointTransaction(
                user_id=user_id,
                amount=amount,
                balance_after=new_balance,
                source=source,
                description=description
            )
            
            # Update user balance
            user.points = new_balance
            
            self.session.add(transaction)
            await self.session.flush()
            await self.session.refresh(transaction)
            
            logger.info(f"Added {amount} points to user {user_id}. New balance: {new_balance}")
            return transaction
    
    async def deduct_points(self, user_id: int, amount: float, source: str, description: str = "") -> Optional[PointTransaction]:
        """Deduct points from user account if sufficient balance."""
        async with self.session.begin():
            user = await self.session.get(User, user_id)
            if not user or user.points < amount:
                logger.warning(f"Cannot deduct {amount} points from user {user_id}. Current balance: {user.points if user else 0}")
                return None
            
            # Calculate new balance
            old_balance = user.points
            new_balance = old_balance - amount
            
            # Create transaction record
            transaction = PointTransaction(
                user_id=user_id,
                amount=-amount,  # Negative for deductions
                balance_after=new_balance,
                source=source,
                description=description
            )
            
            # Update user balance
            user.points = new_balance
            
            self.session.add(transaction)
            await self.session.flush()
            await self.session.refresh(transaction)
            
            logger.info(f"Deducted {amount} points from user {user_id}. New balance: {new_balance}")
            return transaction
    
    async def transfer_points(self, from_user_id: int, to_user_id: int, amount: float, description: str = "") -> bool:
        """Transfer points between users atomically."""
        async with self.session.begin():
            # Deduct from source user
            deduct_transaction = await self.deduct_points(
                from_user_id, amount, "transfer_out", 
                f"Transfer to user {to_user_id}: {description}"
            )
            
            if not deduct_transaction:
                return False
            
            # Add to target user
            add_transaction = await self.add_points(
                to_user_id, amount, "transfer_in",
                f"Transfer from user {from_user_id}: {description}"
            )
            
            logger.info(f"Transferred {amount} points from user {from_user_id} to user {to_user_id}")
            return True
    
    # Transaction history with optimized queries
    async def get_transaction_history(self, user_id: int, limit: int = 100) -> List[PointTransaction]:
        """Get user's point transaction history with pagination."""
        stmt = (
            select(PointTransaction)
            .where(PointTransaction.user_id == user_id)
            .order_by(desc(PointTransaction.created_at))
            .limit(limit)
        )
        return await self._execute_query(stmt)
    
    async def get_transactions_by_source(self, user_id: int, source: str) -> List[PointTransaction]:
        """Get transactions by source with efficient filtering."""
        stmt = (
            select(PointTransaction)
            .where(
                and_(
                    PointTransaction.user_id == user_id,
                    PointTransaction.source == source
                )
            )
            .order_by(desc(PointTransaction.created_at))
        )
        return await self._execute_query(stmt)
    
    async def get_transactions_by_date_range(self, user_id: int, start_date: datetime, end_date: datetime) -> List[PointTransaction]:
        """Get transactions within date range with optimized query."""
        stmt = (
            select(PointTransaction)
            .where(
                and_(
                    PointTransaction.user_id == user_id,
                    PointTransaction.created_at >= start_date,
                    PointTransaction.created_at <= end_date
                )
            )
            .order_by(desc(PointTransaction.created_at))
        )
        return await self._execute_query(stmt)
    
    # Bulk operations with performance optimization
    async def get_top_users_by_points(self, limit: int = 10) -> List[User]:
        """Get users with highest point balances using optimized query."""
        stmt = (
            select(User)
            .where(User.points > 0)
            .order_by(desc(User.points))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_users_with_balance_above(self, threshold: float) -> List[User]:
        """Get users with balance above threshold."""
        stmt = select(User).where(User.points >= threshold)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_users_with_balance_below(self, threshold: float) -> List[User]:
        """Get users with balance below threshold."""
        stmt = select(User).where(User.points < threshold)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    # Statistics and reporting with advanced analytics
    async def get_total_points_in_system(self) -> float:
        """Get total points across all users with efficient aggregation."""
        stmt = select(func.sum(User.points))
        result = await self.session.execute(stmt)
        total = result.scalar()
        return total if total is not None else 0.0
    
    async def get_point_statistics(self) -> Dict[str, Any]:
        """Get comprehensive point system statistics."""
        # Use raw SQL for complex analytics query
        query = text("""
            SELECT 
                COUNT(DISTINCT u.id) as total_users,
                COALESCE(SUM(u.points), 0) as total_points,
                COALESCE(AVG(u.points), 0) as avg_points,
                COALESCE(MAX(u.points), 0) as max_points,
                COALESCE(MIN(u.points), 0) as min_points,
                COUNT(DISTINCT CASE WHEN u.points > 0 THEN u.id END) as users_with_points,
                COUNT(DISTINCT t.id) as total_transactions,
                COALESCE(SUM(CASE WHEN t.amount > 0 THEN t.amount ELSE 0 END), 0) as total_earned,
                COALESCE(SUM(CASE WHEN t.amount < 0 THEN ABS(t.amount) ELSE 0 END), 0) as total_spent
            FROM users u
            LEFT JOIN point_transactions t ON u.id = t.user_id
        """)
        
        result = await self.session.execute(query)
        row = result.fetchone()
        
        return {
            "total_users": row[0],
            "total_points": float(row[1]),
            "average_points": float(row[2]),
            "max_points": float(row[3]),
            "min_points": float(row[4]),
            "users_with_points": row[5],
            "total_transactions": row[6],
            "total_points_earned": float(row[7]),
            "total_points_spent": float(row[8])
        }
    
    async def get_daily_point_activity(self, date: datetime) -> Dict[str, Any]:
        """Get point activity for specific date."""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        query = text("""
            SELECT 
                COUNT(*) as transaction_count,
                COUNT(DISTINCT user_id) as active_users,
                COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) as points_earned,
                COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0) as points_spent,
                COALESCE(SUM(amount), 0) as net_points
            FROM point_transactions 
            WHERE created_at >= :start_date AND created_at < :end_date
        """)
        
        result = await self.session.execute(query, {
            "start_date": start_of_day,
            "end_date": end_of_day
        })
        row = result.fetchone()
        
        return {
            "date": date.date(),
            "transaction_count": row[0],
            "active_users": row[1],
            "points_earned": float(row[2]),
            "points_spent": float(row[3]),
            "net_points": float(row[4])
        }
    
    async def get_user_point_activity_summary(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Get user's point activity summary for last N days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = text("""
            SELECT 
                COUNT(*) as transaction_count,
                COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0) as points_earned,
                COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0) as points_spent,
                COALESCE(AVG(CASE WHEN amount > 0 THEN amount END), 0) as avg_earning,
                COUNT(DISTINCT DATE(created_at)) as active_days
            FROM point_transactions 
            WHERE user_id = :user_id AND created_at >= :cutoff_date
        """)
        
        result = await self.session.execute(query, {
            "user_id": user_id,
            "cutoff_date": cutoff_date
        })
        row = result.fetchone()
        
        current_balance = await self.get_user_balance(user_id)
        
        return {
            "user_id": user_id,
            "period_days": days,
            "current_balance": current_balance,
            "transaction_count": row[0],
            "points_earned": float(row[1]),
            "points_spent": float(row[2]),
            "average_earning": float(row[3]),
            "active_days": row[4],
            "net_change": float(row[1]) - float(row[2])
        }
    
    # Validation and checks
    async def has_sufficient_balance(self, user_id: int, amount: float) -> bool:
        """Check if user has sufficient balance for transaction."""
        balance = await self.get_user_balance(user_id)
        return balance >= amount
    
    async def validate_transaction_integrity(self, user_id: int) -> bool:
        """Validate user's transaction history integrity."""
        # Get all transactions for user in chronological order
        stmt = (
            select(PointTransaction)
            .where(PointTransaction.user_id == user_id)
            .order_by(PointTransaction.created_at)
        )
        transactions = await self._execute_query(stmt)
        
        if not transactions:
            return True
        
        # Validate that balance_after matches cumulative sum
        running_balance = 0.0
        for transaction in transactions:
            running_balance += transaction.amount
            if abs(running_balance - transaction.balance_after) > 0.01:  # Account for floating point precision
                logger.error(f"Transaction integrity violation for user {user_id}, transaction {transaction.id}")
                return False
        
        # Validate against current user balance
        current_balance = await self.get_user_balance(user_id)
        if abs(running_balance - current_balance) > 0.01:
            logger.error(f"Final balance mismatch for user {user_id}")
            return False
        
        return True
    
    # Batch operations
    async def add_points_bulk(self, transactions: List[Dict[str, Any]]) -> List[PointTransaction]:
        """Add points to multiple users in batch with optimized performance."""
        result_transactions = []
        
        async with self.session.begin():
            for transaction_data in transactions:
                transaction = await self.add_points(
                    user_id=transaction_data['user_id'],
                    amount=transaction_data['amount'],
                    source=transaction_data.get('source', 'bulk_operation'),
                    description=transaction_data.get('description', '')
                )
                result_transactions.append(transaction)
        
        return result_transactions
    
    async def get_leaderboard(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get point leaderboard with rankings and pagination."""
        stmt = (
            select(User)
            .where(User.points > 0)
            .order_by(desc(User.points))
            .limit(limit)
            .offset(offset)
        )
        
        users = await self._execute_query(stmt)
        
        leaderboard = []
        for i, user in enumerate(users, offset + 1):
            leaderboard.append({
                "rank": i,
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "points": user.points,
                "level": user.level
            })
        
        return leaderboard
    
    async def get_user_rank_by_points(self, user_id: int) -> Optional[int]:
        """Get user's rank in points leaderboard with efficient query."""
        user = await self.session.get(User, user_id)
        if not user:
            return None
        
        # Count users with more points
        stmt = select(func.count()).where(User.points > user.points)
        higher_ranked_count = await self._execute_query(stmt, single=True)
        
        return higher_ranked_count + 1  # Rank is count + 1