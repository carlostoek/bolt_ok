from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_reward_type_keyboard() -> InlineKeyboardMarkup:
    """Keyboard to select reward type."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏅 Insignia", callback_data="reward_type_badge"),
                InlineKeyboardButton(text="📁 Archivo", callback_data="reward_type_file")
            ],
            [
                InlineKeyboardButton(text="🔓 Acceso VIP", callback_data="reward_type_access"),
                InlineKeyboardButton(text="💰 Besitos", callback_data="reward_type_besitos")
            ],
            [
                InlineKeyboardButton(text="↩️ Volver", callback_data="admin_content_rewards")
            ]
        ]
    )
    return keyboard
