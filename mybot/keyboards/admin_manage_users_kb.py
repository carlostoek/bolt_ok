from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_manage_users_keyboard():
    """Returns the keyboard for user management options in the admin panel."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Sumar Besitos", callback_data="admin_add_points"),
                InlineKeyboardButton(text="➖ Restar Besitos", callback_data="admin_deduct_points")
            ],
            [
                InlineKeyboardButton(text="👁 Ver Perfil", callback_data="admin_view_user"),
                InlineKeyboardButton(text="🔍 Buscar Usuario", callback_data="admin_search_user")
            ],
            [
                InlineKeyboardButton(text="📢 Notificar Usuarios", callback_data="admin_notify_users")
            ],
            [
                InlineKeyboardButton(text="🔄 Actualizar", callback_data="admin_manage_users"),
                InlineKeyboardButton(text="🏠 Panel Admin", callback_data="admin_main_menu")
            ],
        ]
    )
    return keyboard
