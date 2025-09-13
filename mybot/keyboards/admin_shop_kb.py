"""
Admin Shop Keyboards - Teclados para administración de tienda
Proporciona interfaces para gestión administrativa de artículos y categorías.
"""
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from typing import List, Any

def get_admin_shop_main_kb() -> InlineKeyboardMarkup:
    """Teclado principal de administración de tienda."""
    builder = InlineKeyboardBuilder()
    
    # Gestión de artículos
    builder.button(text="➕ Crear Artículo", callback_data="admin_shop_create_item")
    builder.button(text="📦 Gestionar Artículos", callback_data="admin_shop_list_items")
    
    # Gestión de categorías
    builder.button(text="📂 Categorías", callback_data="admin_shop_categories")
    builder.button(text="🏷️ Descuentos", callback_data="admin_shop_discounts")
    
    # Estadísticas y reportes
    builder.button(text="📊 Estadísticas", callback_data="admin_shop_stats")
    builder.button(text="📈 Reportes", callback_data="admin_shop_reports")
    
    # Navegación
    builder.button(text="🔙 Volver", callback_data="admin_manage_content")
    
    builder.adjust(2, 2, 2, 1)
    
    return builder.as_markup()

def get_admin_shop_items_kb(items: List[Any]) -> InlineKeyboardMarkup:
    """Teclado para listar artículos con acciones administrativas."""
    builder = InlineKeyboardBuilder()
    
    # Botones de artículos (máximo 8)
    for item in items[:8]:
        status_emoji = "✅" if item.is_active else "❌"
        vip_emoji = "💎" if item.is_vip_exclusive else ""
        
        button_text = f"{status_emoji} {vip_emoji}{item.name}"
        builder.button(
            text=button_text,
            callback_data=f"admin_shop_item:{item.id}"
        )
    
    # Acciones generales
    builder.button(text="➕ Crear Nuevo", callback_data="admin_shop_create_item")
    builder.button(text="🔄 Actualizar", callback_data="admin_shop_list_items")
    builder.button(text="⬅️ Volver", callback_data="admin_shop_main")
    
    builder.adjust(1)  # Un artículo por fila
    
    return builder.as_markup()

def get_admin_shop_item_actions_kb(item_id: int, is_active: bool) -> InlineKeyboardMarkup:
    """Teclado de acciones para artículo específico."""
    builder = InlineKeyboardBuilder()
    
    # Acciones principales
    builder.button(text="✏️ Editar", callback_data=f"admin_shop_edit:{item_id}")
    
    # Toggle activo/inactivo
    toggle_text = "❌ Desactivar" if is_active else "✅ Activar"
    builder.button(text=toggle_text, callback_data=f"admin_shop_toggle:{item_id}")
    
    # Gestión de stock
    builder.button(text="📦 Gestionar Stock", callback_data=f"admin_shop_stock:{item_id}")
    
    # Eliminar
    builder.button(text="🗑️ Eliminar", callback_data=f"admin_shop_delete:{item_id}")
    
    # Navegación
    builder.button(text="⬅️ Volver a Lista", callback_data="admin_shop_list_items")
    builder.button(text="🏠 Panel Principal", callback_data="admin_shop_main")
    
    builder.adjust(2, 1, 1, 2)
    
    return builder.as_markup()

def get_admin_shop_categories_kb(categories: List[Any]) -> InlineKeyboardMarkup:
    """Teclado para gestión de categorías."""
    builder = InlineKeyboardBuilder()
    
    # Botones de categorías existentes
    for category in categories[:6]:  # Máximo 6 categorías mostradas
        status_emoji = "✅" if category.is_active else "❌"
        emoji = category.emoji or "📁"
        
        builder.button(
            text=f"{status_emoji} {emoji} {category.name}",
            callback_data=f"admin_shop_category:{category.id}"
        )
    
    # Acciones
    builder.button(text="➕ Nueva Categoría", callback_data="admin_shop_create_category")
    builder.button(text="🔄 Actualizar", callback_data="admin_shop_categories")
    builder.button(text="⬅️ Volver", callback_data="admin_shop_main")
    
    builder.adjust(1)
    
    return builder.as_markup()

def get_admin_shop_create_item_kb(action: str) -> InlineKeyboardMarkup:
    """Teclado para proceso de creación de artículo."""
    builder = InlineKeyboardBuilder()
    
    if action == "cancel":
        builder.button(text="❌ Cancelar", callback_data="admin_shop_main")
    elif action == "confirm":
        builder.button(text="✅ Crear Artículo", callback_data="confirm_create_item")
        builder.button(text="❌ Cancelar", callback_data="admin_shop_main")
    
    builder.adjust(1)
    
    return builder.as_markup()