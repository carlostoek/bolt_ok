from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_content_missions_keyboard():
    """Keyboard for mission management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Crear Misión", callback_data="admin_create_mission"),
                InlineKeyboardButton(text="👁 Ver Activas", callback_data="admin_view_missions")
            ],
            [
                InlineKeyboardButton(text="✅ Activar", callback_data="admin_toggle_mission"),
                InlineKeyboardButton(text="🗑 Eliminar", callback_data="admin_delete_mission")
            ],
            [
                InlineKeyboardButton(text="🔄 Actualizar", callback_data="admin_content_missions"),
                InlineKeyboardButton(text="↩️ Volver", callback_data="admin_manage_content")
            ],
        ]
    )
    return keyboard
