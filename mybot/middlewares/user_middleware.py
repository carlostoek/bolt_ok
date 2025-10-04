from __future__ import annotations

import logging
from typing import Any, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Update
from sqlalchemy.ext.asyncio import AsyncSession

from services.user_service import UserService
from services.user_journey_service import UserJourneyService

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
            user = await service.get_user(user_info.id)
            if not user:
                user = await service.create_user(
                    user_info.id,
                    first_name=getattr(user_info, "first_name", None),
                    last_name=getattr(user_info, "last_name", None),
                    username=getattr(user_info, "username", None),
                )
                logger.info("Created new user via middleware: %s", user_info.id)

                # Inicializar milestones del journey para el nuevo usuario
                try:
                    journey_service = UserJourneyService(session)
                    await journey_service.initialize_user_milestones(user.id)
                    logger.info(f"Journey milestones initialized for new user {user.id}")
                    
                    # QUICK WIN: Enviar mensaje de bienvenida mejorado
                    if hasattr(event, 'message') and event.message:
                        try:
                            from utils.messages import get_loading_message
                            welcome_msg = (
                                f"✨ **¡Bienvenid@ a El Diván de Diana!** ✨\n\n"
                                f"Me alegra tenerte aquí. Soy Lucien, tu guía en este mundo de misterio y sensualidad.\n\n"
                                f"💫 **Tu aventura comienza ahora...**\n"
                                f"• Explora tu historia personal con /start\n"
                                f"• Descubre desafíos con /missions\n"
                                f"• Gana besitos y desbloquea recompensas\n\n"
                                f"{get_loading_message('narrative_progression')}"
                            )
                            bot = data.get("bot")
                            if bot:
                                await bot.send_message(
                                    user_info.id,
                                    welcome_msg,
                                    parse_mode="Markdown"
                                )
                        except Exception as welcome_error:
                            logger.debug(f"Could not send enhanced welcome: {welcome_error}")
                            
                except Exception as e:
                    logger.error(f"Error initializing journey milestones for user {user.id}: {e}")

            data.setdefault("user", user)

        return await handler(event, data)
