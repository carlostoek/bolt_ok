from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from typing import Dict
import logging

from utils.config import DEFAULT_REACTION_BUTTONS

logger = logging.getLogger(__name__)


def get_reaction_kb(
    reactions: list[str],
    current_counts: Dict[str, int] | None,
    message_id: int,
    channel_id: int,
) -> InlineKeyboardMarkup:
    """Build inline keyboard for reaction buttons."""
    builder = InlineKeyboardBuilder()

    if not isinstance(current_counts, dict):
        logger.error(
            "Expected current_counts to be a dict, got %s", type(current_counts)
        )
        current_counts = {}
    
    # Depuración: ver los conteos que llegan
    logger.debug(f"Building reaction keyboard with counts: {current_counts}")

    reactions_to_use = reactions if reactions else DEFAULT_REACTION_BUTTONS

    for emoji in reactions_to_use[:10]:
        # Obtener conteo, asegurándonos de que sea un entero y evitar valores None
        try:
            count = int(current_counts.get(emoji, 0))
        except (TypeError, ValueError):
            count = 0
            logger.warning(f"Invalid count for emoji {emoji}, using 0 instead")
            
        display = f"{emoji} {count}"
        callback_data = f"ip_{channel_id}_{message_id}_{emoji}"
        builder.button(text=display, callback_data=callback_data)
        logger.debug(f"Added button: {emoji} with count {count}")


    keyboard_data = builder.export()
    if keyboard_data:
        num_buttons = sum(len(row) for row in keyboard_data)
        builder.adjust(num_buttons if num_buttons <= 4 else 4)

    return builder.as_markup()
