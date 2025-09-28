from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_mission_completed_keyboard() -> InlineKeyboardMarkup:
    """Keyboard shown after completing a mission."""
    keyboard = [
        [
            InlineKeyboardButton(text="🎯 Ver Misiones", callback_data="menu:missions"),
            InlineKeyboardButton(text="🎁 Recompensas", callback_data="menu:rewards")
        ],
        [
            InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
