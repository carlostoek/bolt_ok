# mybot/keyboards/suscripcion_kb.py
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def get_free_main_menu_kb() -> InlineKeyboardMarkup:
    """
    Return the main menu keyboard for free users.

    Estructura similar al VIP pero con restricciones estratégicas para generar conversión.
    Muestra todo para crear FOMO pero bloquea acciones con CTAs persuasivos.
    """
    builder = InlineKeyboardBuilder()

    # 🎭 NARRATIVA (Principal)
    builder.button(text="📖 Historia", callback_data="start_narrative")

    # 👤 PROGRESO PERSONAL
    builder.button(text="🏆 Mi Perfil", callback_data="menu:profile")
    builder.button(text="📂 Mi Contenido", callback_data="free_my_content")  # Unifica Packs, VIP, Custom

    # 🎯 ACTIVIDADES DIARIAS (Mostrar pero bloquear)
    builder.button(text="🎯 Misiones", callback_data="free_missions_preview")
    builder.button(text="🎁 Regalo", callback_data="free_gift")

    # 🛍️ ECONOMÍA & TIENDA (Mostrar pero bloquear)
    builder.button(text="🛒 Tienda", callback_data="free_shop_preview")
    builder.button(text="🏛️ Subastas", callback_data="free_auctions_preview")

    # 🎒 COLECCIONES (Mostrar pero bloquear)
    builder.button(text="🗺️ Mochila", callback_data="free_backpack_preview")
    builder.button(text="💝 Recompensas", callback_data="free_rewards_preview")

    # 👥 SOCIAL
    builder.button(text="👑 Ranking", callback_data="menu:ranking")

    # Ajustar layout: 1, 2, 2, 2, 2, 1
    builder.adjust(1, 2, 2, 2, 2, 1)
    return builder.as_markup()


def get_free_content_menu_kb() -> InlineKeyboardMarkup:
    """
    Keyboard para el submenú 'Mi Contenido' de usuarios free.
    Unifica: Mis Packs, Explorar VIP, Contenido Custom
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="🎀 Mis Packs", callback_data="free_packs")
    builder.button(text="🔐 Explorar VIP", callback_data="free_vip_explore")
    builder.button(text="💌 Contenido Custom", callback_data="free_custom")
    builder.button(text="↩️ Menú Principal", callback_data="free_main_menu")
    builder.adjust(1, 1, 1, 1)  # Todos en columna
    return builder.as_markup()

def get_vip_explore_kb() -> InlineKeyboardMarkup:
    """Keyboard shown in the free VIP explore section."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔥 Me Interesa", callback_data="vip_explore_interest")
    builder.button(text="↩️ Regresar", callback_data="free_main_menu")
    builder.adjust(2)
    return builder.as_markup()

def get_subscription_kb() -> InlineKeyboardMarkup:
    """Alias for backward compatibility."""
    return get_free_main_menu_kb()

def get_free_info_kb() -> InlineKeyboardMarkup:
    """Keyboard shown in the information section."""
    builder = InlineKeyboardBuilder()
    builder.button(text="❓ FAQ", callback_data="free_info_faq")
    builder.button(text="📢 Novedades", callback_data="free_info_news")
    builder.button(text="↩️ Menú Principal", callback_data="free_main")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_free_game_kb() -> InlineKeyboardMarkup:
    """Keyboard shown in the free mini game section."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🎮 Jugar", callback_data="free_game_play")
    builder.button(text="🏆 Puntuación", callback_data="free_game_score")
    builder.button(text="↩️ Menú Principal", callback_data="free_main")
    builder.adjust(2, 1)
    return builder.as_markup()
