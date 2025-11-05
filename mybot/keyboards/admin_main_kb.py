from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_main_kb():
    """Return the main admin inline keyboard with elegant layout."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Gestión de canales principales
    builder.button(text="💎 Canal VIP", callback_data="admin_vip")
    builder.button(text="💬 Canal Free", callback_data="admin_free")

    # Fila 2: Entretenimiento y juegos
    builder.button(text="🎮 Juego Kinky", callback_data="admin_kinky_game")
    builder.button(text="🛒 Tienda", callback_data="admin_shop")

    # Fila 3: Contenido narrativo y VIP
    builder.button(text="📖 Narrativa", callback_data="admin_narrative_panel")
    builder.button(text="💎 Mi Diván", callback_data="admin:midivan")

    # Fila 4: Experiencias unificadas
    builder.button(text="🎭 Experiencias", callback_data="admin_experiences")
    builder.button(text="📊 Estadísticas", callback_data="admin_stats")

    # Fila 5: Configuración
    builder.button(text="⚙️ Configuración", callback_data="admin_config")

    # Fila 6: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_main_menu")
    builder.button(text="↩️ Volver", callback_data="admin_back")

    # Distribución: 2x2x2x2x1x2
    builder.adjust(2, 2, 2, 2, 1, 2)
    return builder.as_markup()
