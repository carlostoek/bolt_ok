from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_keyboard():
    """Returns the main inline menu keyboard."""
    keyboard = [
        [InlineKeyboardButton(text="📖 Historia", callback_data="start_narrative")],
        [InlineKeyboardButton(text="💎 Mi Diván", callback_data="vip_subscription")],
        [
            InlineKeyboardButton(text="🎯 Misiones", callback_data="menu:missions"),
            InlineKeyboardButton(text="🎁 Regalo Diario", callback_data="daily_gift")
        ],
        [
            InlineKeyboardButton(text="🏆 Mi Perfil", callback_data="menu:profile"),
            InlineKeyboardButton(text="🗺️ Mochila", callback_data="open_backpack")
        ],
        [
            InlineKeyboardButton(text="💝 Recompensas", callback_data="menu:rewards"),
            InlineKeyboardButton(text="👑 Ranking", callback_data="menu:ranking")
        ],
        [
            InlineKeyboardButton(text="🏛️ Subastas", callback_data="auction_main"),
            InlineKeyboardButton(text="🛒 Tienda", callback_data="shop_access")
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
