"""Keyboard helpers for VIP menus."""

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_vip_main_kb():
    """Return the VIP main menu keyboard with shop integration."""
    builder = InlineKeyboardBuilder()
    
    # Fila 1: Historia y perfil
    builder.button(text="📖 Historia", callback_data="start_narrative")
    builder.button(text="🏆 Mi Perfil", callback_data="menu:profile")
    
    # Fila 2: Actividades principales
    builder.button(text="🎯 Misiones", callback_data="menu:missions")
    builder.button(text="🛒 Tienda", callback_data="menu:shop")
    
    # Fila 3: Recompensas y ranking
    builder.button(text="🎁 Recompensas", callback_data="menu:rewards")
    builder.button(text="👑 Ranking", callback_data="menu:ranking")
    
    # Fila 4: Funciones VIP exclusivas
    builder.button(text="🏛️ Subastas", callback_data="auction_main")
    builder.button(text="💎 Mi Suscripción", callback_data="vip_subscription")
    
    # Fila 5: Inventario y mochila
    builder.button(text="📦 Inventario", callback_data="menu:shop_inventory")
    builder.button(text="🎒 Mochila", callback_data="open_backpack")
    
    builder.adjust(2, 2, 2, 2, 2)
    
    return builder.as_markup()
