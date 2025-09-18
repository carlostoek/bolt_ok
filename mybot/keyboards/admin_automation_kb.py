"""
Keyboard definitions for Admin Automation interface.
Provides navigation and control options for automation management.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_automation_main_kb() -> InlineKeyboardMarkup:
    """
    Main automation management keyboard with all primary options.

    Returns:
        InlineKeyboardMarkup with automation control buttons
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⚡ Iniciar Todo",
                callback_data="automation_start_all"
            ),
            InlineKeyboardButton(
                text="⏹️ Detener Todo",
                callback_data="automation_stop_all"
            )
        ],
        [
            InlineKeyboardButton(
                text="📊 Ver Estado",
                callback_data="automation_status"
            ),
            InlineKeyboardButton(
                text="🔧 Configurar",
                callback_data="automation_config"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Volver",
                callback_data="admin_main_menu"
            )
        ]
    ])

    return keyboard

def get_automation_task_kb(task_name: str) -> InlineKeyboardMarkup:
    """
    Keyboard for individual task management.

    Args:
        task_name: Name of the specific automation task

    Returns:
        InlineKeyboardMarkup with task-specific controls
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="▶️ Iniciar",
                callback_data=f"automation_start_{task_name}"
            ),
            InlineKeyboardButton(
                text="⏸️ Pausar",
                callback_data=f"automation_pause_{task_name}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏹️ Detener",
                callback_data=f"automation_stop_{task_name}"
            ),
            InlineKeyboardButton(
                text="🔄 Reiniciar",
                callback_data=f"automation_restart_{task_name}"
            )
        ],
        [
            InlineKeyboardButton(
                text="⚙️ Configurar",
                callback_data=f"automation_config_{task_name}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Volver",
                callback_data="automation_main"
            )
        ]
    ])

    return keyboard

def get_automation_config_kb() -> InlineKeyboardMarkup:
    """
    Configuration keyboard for automation settings.

    Returns:
        InlineKeyboardMarkup with configuration options
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💌 Recordatorios VIP",
                callback_data="automation_config_vip_reminders"
            )
        ],
        [
            InlineKeyboardButton(
                text="🧹 Limpieza Mensajes",
                callback_data="automation_config_message_cleanup"
            )
        ],
        [
            InlineKeyboardButton(
                text="👥 Gestión Usuarios",
                callback_data="automation_config_user_management"
            )
        ],
        [
            InlineKeyboardButton(
                text="📖 Eventos Narrativos",
                callback_data="automation_config_narrative_events"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Volver",
                callback_data="automation_main"
            )
        ]
    ])

    return keyboard