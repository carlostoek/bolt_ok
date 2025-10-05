from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_content_levels_keyboard():
    """Keyboard for level management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Añadir Nivel", callback_data="admin_level_add"),
                InlineKeyboardButton(text="📝 Editar Nivel", callback_data="admin_level_edit")
            ],
            [
                InlineKeyboardButton(text="📋 Ver Niveles", callback_data="admin_levels_view"),
                InlineKeyboardButton(text="🗑 Eliminar Nivel", callback_data="admin_level_delete")
            ],
            [
                InlineKeyboardButton(text="🔄 Actualizar", callback_data="admin_content_levels"),
                InlineKeyboardButton(text="↩️ Volver", callback_data="admin_manage_content")
            ],
        ]
    )
    return keyboard
