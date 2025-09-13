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


def build_shop_keyboard(items):
    """
    Build a keyboard for the shop with available items.
    Handles both ShopItem objects and dictionaries.
    """
    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    for item in items:
        try:
            # Handle both object and dictionary
            if hasattr(item, 'name'):
                # It's a ShopItem object
                item_name = item.name
                item_price = item.price
                item_id = item.id
            elif isinstance(item, dict):
                # It's a dictionary
                item_name = item.get('name')
                item_price = item.get('price')
                item_id = item.get('id')
            else:
                continue
                
            builder.button(
                text=f"{item_name} - {item_price} besitos",
                callback_data=f"buy_item:{item_id}"
            )
        except (AttributeError, KeyError) as e:
            # Log if there's an issue with the item structure
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Invalid item structure: {item}, error: {e}")
    
    builder.button(text="🔙 Volver", callback_data="menu_principal")
    builder.adjust(1)
    return builder.as_markup()

def get_interactive_post_kb(
    reactions: list[str],
    current_counts: Dict[str, int] | None,
    message_id: int,
    channel_id: int,
) -> InlineKeyboardMarkup:
    """
    Keyboard with reaction buttons for channel posts.
    Always returns a valid InlineKeyboardMarkup.
    """
    builder = InlineKeyboardBuilder()

    if not isinstance(current_counts, dict):
        logger.error(
            f"Expected current_counts to be a dict, but got {type(current_counts)}"
        )
        current_counts = {}

    reactions_to_use = reactions if reactions else DEFAULT_REACTION_BUTTONS

    for emoji in reactions_to_use[:10]:
        count = current_counts.get(emoji, 0)
        display = f"{emoji} {count}"
        callback_data = f"ip_{channel_id}_{message_id}_{emoji}"
        builder.button(text=display, callback_data=callback_data)

    keyboard_data = builder.export()
    if keyboard_data:
        # ``buttons`` is a generator, therefore ``len`` cannot be applied
        # directly. ``export`` returns a list of rows with the created buttons,
        # which allows us to count them reliably.
        num_buttons = sum(len(row) for row in keyboard_data)
        if num_buttons <= 4:
            builder.adjust(num_buttons)
        else:
            builder.adjust(4)

    return builder.as_markup()
