from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_reaction_keyboard(
    message_id: int,
    like_text: str = "💋 Me encanta",
    dislike_text: str = "😴 No me gusta",
):
    """Return an inline keyboard with like/dislike buttons for channel posts."""
    keyboard = [
        [
            InlineKeyboardButton(
                text=like_text, callback_data=f"reaction_like_{message_id}"
            ),
            InlineKeyboardButton(
                text=dislike_text, callback_data=f"reaction_dislike_{message_id}"
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_custom_reaction_keyboard(
    message_id: int, buttons: list[str]
) -> InlineKeyboardMarkup:
    """Return an inline keyboard using custom button texts for reactions."""
    if len(buttons) >= 2:
        like, dislike = buttons[0], buttons[1]
    else:
        like, dislike = "💋", "😴"
    return get_reaction_keyboard(message_id, like, dislike)