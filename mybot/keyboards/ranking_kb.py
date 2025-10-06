from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_ranking_keyboard():
    """Returns the keyboard for the ranking section."""
    keyboard = [
        [
            InlineKeyboardButton(text="🔄 Actualizar", callback_data="menu:ranking"),
            InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
