from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_post_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Keyboard used to confirm publishing a channel post."""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Publicar", callback_data="confirm_channel_post"),
            InlineKeyboardButton(text="📝 Editar", callback_data="edit_channel_post")
        ],
        [
            InlineKeyboardButton(text="👀 Vista Previa", callback_data="preview_channel_post"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_vip")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
