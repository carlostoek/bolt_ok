from __future__ import annotations

from aiogram import Bot
from aiogram.types import Message, ReactionTypeEmoji
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramAPIError,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import datetime
import logging

from .config_service import ConfigService
from .channel_service import ChannelService
from database.models import ButtonReaction
from keyboards.inline_post_kb import get_reaction_kb
from services.message_registry import store_message
from utils.config import VIP_CHANNEL_ID, FREE_CHANNEL_ID

logger = logging.getLogger(__name__)


class MessageService:
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
        self.channel_service = ChannelService(self.session)

    async def send_interactive_post(
        self,
        text: str,
        channel_type: str = "vip",
    ) -> Message | bool | None:
        """Send a message with interactive buttons to the configured channel.

        Returns the ``Message`` object on success, ``None`` when the channel
        isn't configured and ``False`` if sending fails due to Telegram
        errors.
        """
        config = ConfigService(self.session)

        target_channel_id: int | str | None = None
        channel_type = channel_type.lower()
        if channel_type == "vip":
            target_channel_id = await config.get_vip_channel_id()
            if target_channel_id is None:
                target_channel_id = VIP_CHANNEL_ID
        elif channel_type == "free":
            target_channel_id = await config.get_free_channel_id()
            if target_channel_id is None:
                target_channel_id = FREE_CHANNEL_ID

        if not target_channel_id:
            logger.warning(f"No channel ID configured for type: {channel_type}")
            return None

        target_channel_id_str = str(target_channel_id)

        if not text or not text.strip():
            text = "\u00a1Un nuevo post interactivo! Reacciona para ganar puntos."

        try:
            raw_reactions, _ = await self.channel_service.get_reactions_and_points(target_channel_id)

            sent = await self.bot.send_message(
                chat_id=target_channel_id_str,
                text=text,
                reply_markup=None,
            )

            real_message_id = sent.message_id

            counts = await self.get_reaction_counts(real_message_id)

            updated_markup = get_reaction_kb(
                reactions=raw_reactions,
                current_counts=counts,
                message_id=real_message_id,
                channel_id=target_channel_id,
            )

            logger.info(f"DEBUG: Markup to edit: {updated_markup}")

            await self.bot.edit_message_reply_markup(
                chat_id=target_channel_id_str,
                message_id=real_message_id,
                reply_markup=updated_markup,
            )
            store_message(target_channel_id, real_message_id)

            if channel_type == "vip":
                vip_reactions = await config.get_vip_reactions()
                if vip_reactions:
                    try:
                        await self.bot.set_message_reaction(
                            chat_id=target_channel_id_str,
                            message_id=real_message_id,
                            reaction=[ReactionTypeEmoji(emoji=r) for r in vip_reactions[:10]],
                        )
                    except TelegramAPIError as e:
                        logger.error(
                            f"Error al establecer reacciones nativas en mensaje {real_message_id} del canal {target_channel_id}: {e}",
                            exc_info=True,
                        )

            from services.mission_service import MissionService
            mission_service = MissionService(self.session)
            await mission_service.create_mission(
                name=f"Reaccionar {real_message_id}",
                description="Reacciona a la publicaci\u00f3n para ganar puntos",
                mission_type="reaction",
                target_value=1,
                reward_points=1,
                duration_days=7,
                requires_action=True,
                action_data={"target_message_id": real_message_id},
            )
            return sent
        except (TelegramBadRequest, TelegramForbiddenError, TelegramAPIError) as e:
            logger.error(
                f"Failed to send interactive post to channel {target_channel_id}: {e}",
                exc_info=True,
            )
            return False

    async def register_reaction(
        self, user_id: int, message_id: int, reaction_type: str
    ) -> ButtonReaction | None:
        # Asegurarnos de que message_id sea un entero
        message_id = int(message_id)
        user_id = int(user_id)
        
        # Verificar si ya existe esta reacción exacta
        stmt = select(ButtonReaction).where(
            ButtonReaction.message_id == message_id,
            ButtonReaction.user_id == user_id,
            ButtonReaction.reaction_type == reaction_type,
        )
        result = await self.session.execute(stmt)
        existing_reaction = result.scalar()
        
        # Si ya existe esta reacción exacta, no hacer nada
        if existing_reaction:
            logger.info(f"User {user_id} already reacted with {reaction_type} to message {message_id}")
            return None

        # Verificar y eliminar si el usuario ya reaccionó con otro emoji
        # para permitir solo una reacción por usuario por mensaje
        stmt = select(ButtonReaction).where(
            ButtonReaction.message_id == message_id,
            ButtonReaction.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        existing_different_reaction = result.scalar()
        
        if existing_different_reaction:
            logger.info(f"User {user_id} changing reaction from {existing_different_reaction.reaction_type} to {reaction_type} on message {message_id}")
            # Eliminar la reacción anterior
            await self.session.delete(existing_different_reaction)
            await self.session.flush()

        # Crear nueva reacción
        reaction = ButtonReaction(
            message_id=message_id,
            user_id=user_id,
            reaction_type=reaction_type,
        )
        self.session.add(reaction)
        await self.session.commit()
        await self.session.refresh(reaction)
        
        # Forzar actualización de contadores invalidando caché de la sesión
        await self.session.expire_all()

        from services.mission_service import MissionService
        mission_service = MissionService(self.session)
        mission_id = f"reaction_reaccionar_{message_id}"
        await mission_service.complete_mission(
            user_id,
            mission_id,
            reaction_type=reaction_type,
            target_message_id=message_id,
            bot=self.bot,
        )
        from services.minigame_service import MiniGameService
        await MiniGameService(self.session).record_reaction(user_id, self.bot)

        return reaction

    async def get_reaction_counts(self, message_id: int) -> dict[str, int]:
        """Return reaction counts for the given message."""
        try:
            # Usar un logger para ayudar en la depuración
            logger.debug(f"Getting reaction counts for message_id={message_id}")
            
            # Asegurarse de que message_id sea un entero
            message_id = int(message_id)
            
            # Consulta para obtener conteos de reacciones - usar una consulta más directa
            stmt = (
                select(ButtonReaction.reaction_type, func.count(ButtonReaction.id).label("count"))
                .where(ButtonReaction.message_id == message_id)
                .group_by(ButtonReaction.reaction_type)
            )
            result = await self.session.execute(stmt)
            
            # Convertir resultado a diccionario
            counts = {row[0]: row[1] for row in result.all()}
            
            # Verificar que tenemos datos y loguear para depuración
            logger.debug(f"Found reaction counts: {counts}")
            
            # Para depuración detallada: consultar directamente todas las reacciones para este mensaje
            debug_stmt = select(ButtonReaction).where(ButtonReaction.message_id == message_id)
            debug_result = await self.session.execute(debug_stmt)
            debug_reactions = debug_result.scalars().all()
            logger.debug(f"Raw reactions in DB for message {message_id}: {len(debug_reactions)}")
            for reaction in debug_reactions:
                logger.debug(f"  - User {reaction.user_id}: {reaction.reaction_type}")
            
            return counts
        except Exception as e:
            logger.error(f"Error getting reaction counts: {e}", exc_info=True)
            return {}  # Retornar diccionario vacío en caso de error

    async def update_reaction_markup(self, chat_id: int, message_id: int) -> None:
        """Update inline keyboard of an interactive post with current counts."""
        chat_id_str = str(chat_id)

        # Obtener conteos actuales siempre frescos - forzar una consulta a la BD
        await self.session.expire_all()  # Forzar refrescar los datos de la sesión
        counts = await self.get_reaction_counts(message_id)
        
        # Mostrar los conteos que estamos usando para depuración
        logger.info(f"Current reaction counts for message {message_id}: {counts}")
        
        # Obtener las reacciones disponibles del canal
        raw_reactions, _ = await self.channel_service.get_reactions_and_points(chat_id)
        if not raw_reactions:
            from utils.config import DEFAULT_REACTION_BUTTONS
            raw_reactions = DEFAULT_REACTION_BUTTONS

        try:
            # Crear markup con los conteos actualizados
            # Usar get_reaction_kb de keyboards/inline_post_kb.py para consistencia
            markup_to_edit = get_reaction_kb(
                reactions=raw_reactions,
                current_counts=counts,
                message_id=message_id,
                channel_id=chat_id,
            )
            logger.info(f"DEBUG: Markup being sent for update: {markup_to_edit}")

            # Intentar actualizar el markup
            await self.bot.edit_message_reply_markup(
                chat_id=chat_id_str,
                message_id=message_id,
                reply_markup=markup_to_edit,
            )
            logger.info(f"Successfully updated reaction markup for message {message_id} with counts: {counts}")
            
        except TelegramBadRequest as e:
            # Solo registrar como error si no es un "message is not modified"
            if "message is not modified" in str(e):
                logger.info(
                    f"No changes needed for markup in chat {chat_id}, message {message_id}"
                )
            else:
                logger.error(
                    f"Failed to update reaction markup for chat {chat_id}, message {message_id}: {e}",
                    exc_info=True,
                )
        except TelegramAPIError as e:
            logger.error(
                f"Unexpected API error updating reaction markup for chat {chat_id}, message {message_id}: {e}",
                exc_info=True,
            )

    async def get_weekly_reaction_ranking(self, limit: int = 3) -> list[tuple[int, int]]:
        """Return a list of (user_id, count) for reactions in last 7 days."""
        since = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        stmt = (
            select(ButtonReaction.user_id, func.count(ButtonReaction.id))
            .where(ButtonReaction.created_at >= since)
            .group_by(ButtonReaction.user_id)
            .order_by(func.count(ButtonReaction.id).desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.all()
