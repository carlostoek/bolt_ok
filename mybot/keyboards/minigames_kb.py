from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_minigames_keyboard():
    """Returns the minigames inline menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(text="🧩 Trivia", callback_data="minigame:trivia"),
            InlineKeyboardButton(text="🎲 Dados", callback_data="minigame:dados")
        ],
        [
            InlineKeyboardButton(text="⬅️ Volver", callback_data="menu:main")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
