from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_content_daily_gifts_keyboard():
    """Keyboard for daily gift configuration options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎁 Configurar Regalo", callback_data="admin_game_test"),
                InlineKeyboardButton(text="📊 Estadísticas", callback_data="admin_daily_stats")
            ],
            [
                InlineKeyboardButton(text="🔄 Actualizar", callback_data="admin_content_daily_gifts"),
                InlineKeyboardButton(text="↩️ Volver", callback_data="admin_manage_content")
            ],
        ]
    )
    return keyboard
