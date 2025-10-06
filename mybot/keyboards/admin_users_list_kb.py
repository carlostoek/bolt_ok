from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import User

def get_admin_users_list_keyboard(
    users: list[User], offset: int, total_count: int, limit: int = 4
) -> InlineKeyboardMarkup:
    """Return a keyboard for the paginated list of users with action buttons."""
    keyboard: list[list[InlineKeyboardButton]] = []

    # Mostrar usuarios con acciones en filas de 3 botones
    for user in users:
        user_display = f"👤 {user.username or f'ID:{user.id}'}"
        keyboard.append([
            InlineKeyboardButton(text="➕", callback_data=f"admin_user_add_{user.id}"),
            InlineKeyboardButton(text="➖", callback_data=f"admin_user_deduct_{user.id}"),
            InlineKeyboardButton(text="👁", callback_data=f"admin_user_view_{user.id}"),
        ])

    # Navegación mejorada
    nav_buttons: list[InlineKeyboardButton] = []
    if offset > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️ Anterior", callback_data=f"admin_users_page_{offset - limit}")
        )
    if offset + limit < total_count:
        nav_buttons.append(
            InlineKeyboardButton(text="Siguiente ➡️", callback_data=f"admin_users_page_{offset + limit}")
        )
    if nav_buttons:
        keyboard.append(nav_buttons)

    # Botones de acción
    keyboard.append([
        InlineKeyboardButton(text="🔄 Actualizar", callback_data="admin_manage_users"),
        InlineKeyboardButton(text="🏠 Panel Admin", callback_data="admin_main_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
