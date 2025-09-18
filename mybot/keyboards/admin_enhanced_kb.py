from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_enhanced_admin_main_kb():
    """
    Returns the enhanced main admin inline keyboard with an organized layout.
    This keyboard aligns with the enhanced admin module design.
    """
    builder = InlineKeyboardBuilder()

    # Row 1: Core Channel Management
    builder.button(text="💎 Canal VIP", callback_data="admin_vip_enhanced")
    builder.button(text="💬 Canal Free", callback_data="admin_free_enhanced")

    # Row 2: Analytics and Automation
    builder.button(text="📈 Análisis", callback_data="admin_analytics_enhanced")
    builder.button(text="🤖 Automatización", callback_data="admin_automation_enhanced")

    # Row 3: System and Navigation
    builder.button(text="⚙️ Configuración", callback_data="admin_config_enhanced")
    builder.button(text="↩️ Volver al Menú Principal", callback_data="main_menu")

    builder.adjust(2, 2, 2)
    return builder.as_markup()


def get_enhanced_back_kb(callback_data: str = "admin_main_enhanced"):
    """
    Returns a simple keyboard with a 'Back' button for enhanced admin menus.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="↩️ Volver", callback_data=callback_data)
    return builder.as_markup()
