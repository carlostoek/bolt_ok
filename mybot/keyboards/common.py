from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from typing import Dict
import logging

from utils.config import DEFAULT_REACTION_BUTTONS

logger = logging.getLogger(__name__)


def get_back_kb(callback_data: str = "admin_back"):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Volver", callback_data=callback_data)
    builder.adjust(1)
    return builder.as_markup()


def get_interactive_post_kb(
    reactions: list[str],
    current_counts: Dict[str, int] | None,
    message_id: int,
    channel_id: int,
) -> InlineKeyboardMarkup:
    """
    Alias para get_reaction_kb para mantener compatibilidad.
    """
    from keyboards.inline_post_kb import get_reaction_kb
    return get_reaction_kb(reactions, current_counts, message_id, channel_id)
