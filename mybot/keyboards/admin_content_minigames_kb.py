from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_content_minigames_keyboard():
    """Keyboard placeholder for minigames options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🕹 Configurar Juegos", callback_data="admin_game_test"),
                InlineKeyboardButton(text="📊 Estadísticas", callback_data="admin_games_stats")
            ],
            [
                InlineKeyboardButton(text="🔄 Actualizar", callback_data="admin_content_minigames"),
                InlineKeyboardButton(text="↩️ Volver", callback_data="admin_manage_content")
            ],
        ]
    )
    return keyboard
