from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_content_auctions_keyboard():
    """Keyboard for auction management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏛️ Gestionar Subastas", callback_data="admin_auction_main"),
                InlineKeyboardButton(text="📊 Estadísticas", callback_data="admin_auction_stats")
            ],
            [
                InlineKeyboardButton(text="🔄 Actualizar", callback_data="admin_content_auctions"),
                InlineKeyboardButton(text="↩️ Volver", callback_data="admin_manage_content")
            ],
        ]
    )
    return keyboard
