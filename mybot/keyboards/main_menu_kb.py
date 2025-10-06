from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_keyboard():
    """Returns the main inline menu keyboard with organized categories."""
    keyboard = [
        # 🎭 NARRATIVA (Principal)
        [InlineKeyboardButton(text="📖 Historia", callback_data="start_narrative")],

        # 👤 PROGRESO PERSONAL
        [
            InlineKeyboardButton(text="🏆 Mi Perfil", callback_data="menu:profile"),
            InlineKeyboardButton(text="💎 Mi Diván", callback_data="midivan:main")
        ],

        # 🎯 ACTIVIDADES DIARIAS
        [
            InlineKeyboardButton(text="🎯 Misiones", callback_data="menu:missions"),
            InlineKeyboardButton(text="🎮 Minijuegos", callback_data="menu:minigames")
        ],

        # 🛍️ ECONOMÍA & TIENDA
        [
            InlineKeyboardButton(text="🛒 Tienda", callback_data="shop_access"),
            InlineKeyboardButton(text="🏛️ Subastas", callback_data="auction_main")
        ],

        # 🎒 COLECCIONES
        [
            InlineKeyboardButton(text="🗺️ Mochila", callback_data="open_backpack")
        ],

        # 👥 SOCIAL
        [InlineKeyboardButton(text="👑 Ranking", callback_data="menu:ranking")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
