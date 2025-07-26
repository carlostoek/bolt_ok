from __future__ import annotations

import logging
from typing import Any, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Update
from sqlalchemy.ext.asyncio import AsyncSession

from services.user_service import UserService

logger = logging.getLogger(__name__)


class UserRegistrationMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Any],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        session: AsyncSession | None = data.get("session")
        if not session:
            return await handler(event, data)

        user_info = None
        if getattr(event, "message", None) and event.message.from_user:
            user_info = event.message.from_user
        elif getattr(event, "callback_query", None) and event.callback_query.from_user:
            user_info = event.callback_query.from_user
        elif getattr(event, "from_user", None):
            user_info = event.from_user
        elif getattr(event, "user", None):  # e.g., PollAnswer
            user_info = event.user

        if user_info:
            service = UserService(session)
            try:
                # Try to get the user first
                user = await service.get_user(user_info.id)
                
                # If user doesn't exist, create a new one
                if not user:
                    user = await service.create_user(
                        user_info.id,
                        first_name=getattr(user_info, "first_name", None),
                        last_name=getattr(user_info, "last_name", None),
                        username=getattr(user_info, "username", None),
                    )
                    logger.info("Created new user via middleware: %s", user_info.id)
                
                # Update user data in the handler
                data.setdefault("user", user)
            except Exception as e:
                # Log error but don't crash the middleware
                logger.error(f"Error processing user in middleware: {e}")
                # Continue with handler even if user registration fails
                # The service layer will handle and log the specific error

        return await handler(event, data)
