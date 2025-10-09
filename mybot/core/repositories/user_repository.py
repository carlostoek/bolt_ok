import logging
from typing import List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.repositories.base_repository import BaseRepository
from database.models import User

logger = logging.getLogger(__name__)

class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_id(self, user_id: int) -> User | None:
        return await super().get_by_id(user_id)

    async def get_by_username(self, username: str) -> User | None:
        try:
            stmt = select(User).where(User.username == username)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None

    async def get_paginated_users(self, page: int, limit: int) -> tuple[list[User], int]:
        try:
            offset = (page - 1) * limit
            
            stmt = select(User).order_by(User.id).offset(offset).limit(limit)
            result = await self.session.execute(stmt)
            users = result.scalars().all()
            
            count_stmt = select(func.count()).select_from(User)
            total_result = await self.session.execute(count_stmt)
            total = total_result.scalar_one()
            
            return users, total
        except Exception as e:
            logger.error(f"Error getting paginated users (page={page}, limit={limit}): {e}")
            return [], 0

    async def search_users(self, query: str) -> list[User]:
        try:
            search_query = f"%{query}%"
            stmt = select(User).where(
                (User.username.ilike(search_query)) |
                (User.first_name.ilike(search_query))
            )
            result = await self.session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error searching users with query '{query}': {e}")
            return []

    async def update_points(self, user_id: int, points: float) -> User | None:
        return await self.update(user_id, {"points": points})
