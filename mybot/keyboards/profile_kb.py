from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_profile_keyboard():
    """Returns the keyboard for the profile section."""
    keyboard = [
        [
            InlineKeyboardButton(text="🔄 Actualizar", callback_data="menu:profile"),
            InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
