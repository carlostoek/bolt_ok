from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.localization import get_text

def get_main_menu_keyboard():
    """Returns the main inline menu keyboard with organized categories."""
    keyboard = [
        # 🎭 NARRATIVA (Principal)
        [InlineKeyboardButton(text=get_text("main_menu_keyboard.history"), callback_data="start_narrative")],

        # 👤 PROGRESO PERSONAL
        [
            InlineKeyboardButton(text=get_text("main_menu_keyboard.profile"), callback_data="menu:profile"),
            InlineKeyboardButton(text=get_text("main_menu_keyboard.divan"), callback_data="midivan:main")
        ],

        # 🎯 ACTIVIDADES DIARIAS
        [
            InlineKeyboardButton(text=get_text("main_menu_keyboard.missions"), callback_data="menu:missions"),
            InlineKeyboardButton(text=get_text("main_menu_keyboard.minigames"), callback_data="menu:minigames")
        ],

        # 🛍️ ECONOMÍA & TIENDA
        [
            InlineKeyboardButton(text=get_text("main_menu_keyboard.shop"), callback_data="shop_access"),
            InlineKeyboardButton(text=get_text("main_menu_keyboard.auctions"), callback_data="auction_main")
        ],

        # 🎒 COLECCIONES
        [
            InlineKeyboardButton(text=get_text("main_menu_keyboard.backpack"), callback_data="open_backpack")
        ],

        # 👥 SOCIAL
        [InlineKeyboardButton(text=get_text("main_menu_keyboard.ranking"), callback_data="menu:ranking")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)