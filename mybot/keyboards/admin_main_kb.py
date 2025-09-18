from aiogram.utils.keyboard import InlineKeyboardBuilder

# Check if automation is available for keyboard layout
try:
    from handlers.admin.automation_handlers import automation_service
    AUTOMATION_AVAILABLE = True
except ImportError:
    AUTOMATION_AVAILABLE = False

def get_admin_main_kb():
    """Return the main admin inline keyboard with elegant layout and automation support."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Gestión de canales principales
    builder.button(text="💎 Canal VIP", callback_data="admin_vip")
    builder.button(text="💬 Canal Free", callback_data="admin_free")

    # Fila 2: Entretenimiento y juegos
    builder.button(text="🎮 Gamificación", callback_data="admin_kinky_game")
    builder.button(text="🛒 Tienda", callback_data="admin_shop_main")

    # Fila 3: Gestión de contenido narrativo
    builder.button(text="📚 Narrativa", callback_data="admin_narrative_main")
    builder.button(text="📈 Analytics", callback_data="admin_analytics_main")

    # Fila 4: Sistema y automatización
    if AUTOMATION_AVAILABLE:
        builder.button(text="🤖 Automatización", callback_data="automation")
        builder.button(text="⚙️ Config", callback_data="admin_config")
    else:
        builder.button(text="📊 Estadísticas", callback_data="admin_stats")
        builder.button(text="⚙️ Configuración", callback_data="admin_config")

    # Fila 5: Navegación y estadísticas
    if AUTOMATION_AVAILABLE:
        builder.button(text="📊 Estadísticas", callback_data="admin_stats")
        builder.button(text="🔄 Actualizar", callback_data="admin_main_menu")
    else:
        builder.button(text="🔄 Actualizar", callback_data="admin_main_menu")
        builder.button(text="↩️ Volver", callback_data="admin_back")

    # Distribución: 2x2, luego 2x2, luego 2
    builder.adjust(2, 2, 2, 2, 2)
    return builder.as_markup()

def get_enhanced_admin_main_kb():
    """Enhanced admin keyboard with automation and improved layout."""
    return get_admin_main_kb()  # Use the same enhanced logic
