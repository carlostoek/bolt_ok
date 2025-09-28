from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_manage_content_keyboard():
    """Returns the keyboard for content management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👥 Usuarios", callback_data="admin_manage_users"),
                InlineKeyboardButton(text="🎯 Misiones", callback_data="admin_content_missions")
            ],
            [
                InlineKeyboardButton(text="🏅 Insignias", callback_data="admin_content_badges"),
                InlineKeyboardButton(text="📈 Niveles", callback_data="admin_content_levels")
            ],
            [
                InlineKeyboardButton(text="🎁 Catálogo VIP", callback_data="admin_content_rewards"),
                InlineKeyboardButton(text="🏛️ Subastas", callback_data="admin_auction_main")
            ],
            [
                InlineKeyboardButton(text="🎁 Regalos Diarios", callback_data="admin_content_daily_gifts"),
                InlineKeyboardButton(text="🕹 Minijuegos", callback_data="admin_content_minigames")
            ],
            [
                InlineKeyboardButton(text="🗺️ Pistas", callback_data="admin_content_lore_pieces"),
                InlineKeyboardButton(text="🎉 Eventos", callback_data="admin_manage_events_sorteos")
            ],
            [
                InlineKeyboardButton(text="🔄 Actualizar", callback_data="admin_manage_content"),
                InlineKeyboardButton(text="🏠 Panel Admin", callback_data="admin_main_menu")
            ],
        ]
    )
    return keyboard
