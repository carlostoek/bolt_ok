from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_content_rewards_keyboard():
    """Keyboard for reward management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎁 Ver Recompensas", callback_data="admin_reward_view"),
                InlineKeyboardButton(text="➕ Añadir Recompensa", callback_data="admin_reward_add")
            ],
            [
                InlineKeyboardButton(text="✏️ Editar Recompensa", callback_data="admin_reward_edit"),
                InlineKeyboardButton(text="❌ Eliminar Recompensa", callback_data="admin_reward_delete")
            ],
            [
                InlineKeyboardButton(text="🔄 Actualizar", callback_data="admin_content_rewards"),
                InlineKeyboardButton(text="↩️ Volver", callback_data="admin_manage_content")
            ],
        ]
    )
    return keyboard