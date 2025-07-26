from __future__ import annotations

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from utils.text_utils import sanitize_text

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, telegram_id: int) -> User | None:
        try:
            return await self.session.get(User, telegram_id)
        except Exception as e:
            logger.error(f"Error getting user {telegram_id}: {e}")
            # Try more explicit query if the direct get fails
            from sqlalchemy import select
            try:
                stmt = select(User).where(User.id == telegram_id)
                result = await self.session.execute(stmt)
                return result.scalar_one_or_none()
            except Exception as e2:
                logger.error(f"Secondary error getting user {telegram_id}: {e2}")
                return None

    async def create_user(
        self,
        telegram_id: int,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        username: str | None = None,
    ) -> User:
        try:
            # First try to get the user in case it exists but wasn't found earlier
            existing_user = await self.get_user(telegram_id)
            if existing_user:
                logger.info("User already exists, returning existing user: %s", telegram_id)
                return existing_user
                
            # Create new user if not found
            user = User(
                id=telegram_id,
                first_name=sanitize_text(first_name),
                last_name=sanitize_text(last_name),
                username=sanitize_text(username),
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            logger.info("Created new user: %s", telegram_id)
            return user
        except Exception as e:
            # Handle IntegrityError (duplicate key) and other exceptions
            logger.error("Error creating user %s: %s", telegram_id, str(e))
            await self.session.rollback()
            
            # If we get here, try one more time to get the user
            existing_user = await self.get_user(telegram_id)
            if existing_user:
                logger.info("Found existing user after error: %s", telegram_id)
                return existing_user
            
            # Re-raise the exception if we still can't get the user
            raise

    async def update_user_info(
        self,
        user: User,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        username: str | None = None,
    ) -> User:
        user.first_name = sanitize_text(first_name)
        user.last_name = sanitize_text(last_name)
        user.username = sanitize_text(username)
        await self.session.commit()
        await self.session.refresh(user)
        return user
