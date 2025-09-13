"""
Shop Keyboards - Teclados para navegación de tienda
Proporciona interfaces intuitivas para explorar y comprar artículos.
"""
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from typing import List, Dict, Any

def get_shop_main_kb(catalog_data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Teclado principal de la tienda."""
    builder = InlineKeyboardBuilder()
    
    # Información del usuario
    user_points = catalog_data.get("user_points", 0)
    is_vip = catalog_data.get("is_vip", False)
    total_items = catalog_data.get("total_items", 0)
    
    # Botones por categoría
    items_by_category = catalog_data.get("items_by_category", {})
    categories = catalog_data.get("categories", [])
    
    if categories:
        for category_info in categories:
            category_name = category_info["name"]
            emoji = category_info.get("emoji", "🛒")
            item_count = len(items_by_category.get(category_name, []))
            
            if item_count > 0:
                builder.button(
                    text=f"{emoji} {category_name.title()} ({item_count})",
                    callback_data=f"shop_category:{category_name}"
                )
    else:
        # Si no hay categorías, mostrar botón general
        builder.button(
            text=f"🛒 Ver Todos los Artículos ({total_items})",
            callback_data="shop_category:general"
        )
    
    # Botones de navegación
    builder.button(text="📦 Mi Inventario", callback_data="menu:shop_inventory")
    
    # Información VIP
    if not is_vip:
        builder.button(text="💎 Ver Artículos VIP", callback_data="shop_vip_preview")
    
    # Botón de regreso
    builder.button(text="🏠 Menú Principal", callback_data="menu_principal")
    
    # Organizar botones
    if len(categories) <= 2:
        builder.adjust(len(categories) if categories else 1, 1, 1, 1)
    else:
        builder.adjust(2, 2, 1, 1)
    
    return builder.as_markup()

def get_shop_category_kb(category: str, items: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Teclado para mostrar artículos de una categoría específica."""
    builder = InlineKeyboardBuilder()
    
    # Botones de artículos (máximo 8 por página)
    for item in items[:8]:
        item_name = item["name"]
        final_price = item["final_price"]
        can_afford = item["can_afford"]
        is_vip_exclusive = item["is_vip_exclusive"]
        
        # Crear texto del botón
        button_text = f"{item_name}"
        if is_vip_exclusive:
            button_text = f"💎 {button_text}"
        if not can_afford:
            button_text = f"🔒 {button_text}"
        
        button_text += f" ({final_price}💋)"
        
        builder.button(
            text=button_text,
            callback_data=f"shop_item:{item['id']}"
        )
    
    # Navegación
    builder.button(text="⬅️ Volver a Tienda", callback_data="menu:shop")
    builder.button(text="🏠 Menú Principal", callback_data="menu_principal")
    
    # Organizar en columnas
    builder.adjust(1)  # Un artículo por fila para mejor legibilidad
    
    return builder.as_markup()

def get_shop_item_detail_kb(
    item_id: int, 
    can_purchase: bool, 
    final_price: int
) -> InlineKeyboardMarkup:
    """Teclado para detalles de artículo específico."""
    builder = InlineKeyboardBuilder()
    
    if can_purchase:
        builder.button(
            text=f"💳 Comprar ({final_price} besitos)",
            callback_data=f"shop_buy:{item_id}"
        )
    else:
        builder.button(
            text="❌ No Disponible",
            callback_data="shop_unavailable"
        )
    
    # Navegación
    builder.button(text="⬅️ Volver", callback_data="shop_back")
    builder.button(text="🛒 Tienda Principal", callback_data="menu:shop")
    builder.button(text="🏠 Menú Principal", callback_data="menu_principal")
    
    builder.adjust(1, 1, 2)
    
    return builder.as_markup()

def get_shop_purchase_confirm_kb(item_id: int, final_price: int) -> InlineKeyboardMarkup:
    """Teclado de confirmación de compra."""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=f"✅ Confirmar ({final_price} besitos)",
        callback_data=f"shop_buy_confirm:{item_id}"
    )
    builder.button(
        text="❌ Cancelar",
        callback_data="shop_back"
    )
    
    builder.adjust(1)
    
    return builder.as_markup()

def get_shop_inventory_kb(inventory: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Teclado para gestión de inventario."""
    builder = InlineKeyboardBuilder()
    
    # Botones para artículos usables (máximo 5 mostrados)
    usable_items = [item for item in inventory if not item.get("is_used", False)][:5]
    
    for item in usable_items:
        builder.button(
            text=f"🔧 Usar {item['name']}",
            callback_data=f"use_item:{item['item_id']}"
        )
    
    # Navegación
    builder.button(text="🛒 Ir a Tienda", callback_data="menu:shop")
    builder.button(text="🏠 Menú Principal", callback_data="menu_principal")
    
    builder.adjust(1)
    
    return builder.as_markup()

def get_shop_error_kb() -> InlineKeyboardMarkup:
    """Teclado para errores de tienda."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔄 Reintentar", callback_data="menu:shop")
    builder.button(text="🏠 Menú Principal", callback_data="menu_principal")
    
    builder.adjust(1)
    
    return builder.as_markup()