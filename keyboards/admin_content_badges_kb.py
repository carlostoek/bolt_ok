from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_content_badges_keyboard():
    """Keyboard for badge management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Crear Insignia", callback_data="admin_create_badge"),
                InlineKeyboardButton(text="👁 Ver Insignias", callback_data="admin_view_badges")
            ],
            [
                InlineKeyboardButton(text="🗑 Eliminar Insignia", callback_data="admin_delete_badge")
            ],
            [
                InlineKeyboardButton(text="🔄 Actualizar", callback_data="admin_content_badges"),
                InlineKeyboardButton(text="↩️ Volver", callback_data="admin_manage_content")
            ],
        ]
    )
    return keyboard
