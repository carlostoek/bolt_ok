from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_main_kb():
    """Return the main admin inline keyboard with elegant layout."""
    builder = InlineKeyboardBuilder()
    
    # Fila 1: Gestión de canales principales
    builder.button(text="💎 Canal VIP", callback_data="admin_vip")
    builder.button(text="💬 Canal Free", callback_data="admin_free")

    # Fila 2: Entretenimiento y juegos
    builder.button(text="🎮 Juego Kinky", callback_data="admin_kinky_game")
    builder.button(text="🛒 Tienda", callback_data="admin_shop_main")

    # Fila 3: Análisis y estadísticas
    builder.button(text="📊 Estadísticas", callback_data="admin_stats")
    builder.button(text="📈 Análisis", callback_data="admin_analytics_main")

    # Fila 4: Configuración
    builder.button(text="⚙️ Configuración", callback_data="admin_config")

    # Fila 5: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_main_menu")
    builder.button(text="↩️ Volver", callback_data="admin_back")

    # Distribución: 2x2, luego 2x1, luego 2
    builder.adjust(2, 2, 2, 1, 2)
    return builder.as_markup()
