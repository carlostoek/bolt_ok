"""
Enhanced shop keyboard builders with categorized navigation and purchase eligibility indicators.
"""
import logging
from typing import Dict, List, Any, Optional
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

logger = logging.getLogger(__name__)


def build_categorized_shop_keyboard(
    categorized_items: Dict[str, List[Any]],
    user_points: int = 0,
    is_vip: bool = False
) -> InlineKeyboardMarkup:
    """
    Build a categorized shop keyboard with category navigation and purchase eligibility indicators.

    Args:
        categorized_items: Dictionary with category names as keys and lists of ShopItems as values
        user_points: Current user points for affordability indicators
        is_vip: User VIP status for VIP item visibility

    Returns:
        InlineKeyboardMarkup for categorized shop navigation
    """
    builder = InlineKeyboardBuilder()

    try:
        # Sort categories to ensure consistent display order
        # VIP categories at the top, then alphabetical
        sorted_categories = sorted(
            categorized_items.keys(),
            key=lambda cat: (not cat.lower().startswith('vip'), cat.lower())
        )

        for category_name in sorted_categories:
            items = categorized_items[category_name]
            if not items:
                continue

            # Count affordable items in this category
            affordable_count = 0
            total_count = len(items)

            for item in items:
                item_price = getattr(item, 'price', 0) if hasattr(item, 'price') else item.get('price', 0)
                if user_points >= item_price:
                    affordable_count += 1

            # Build category button text with indicators
            category_text = f"📂 {category_name}"

            # Add VIP indicator for VIP categories
            if category_name.lower().startswith('vip') or any(
                getattr(item, 'is_vip_only', False) if hasattr(item, 'is_vip_only')
                else item.get('is_vip_only', False) for item in items
            ):
                category_text = f"💎 {category_name}"

            # Add item count and affordability indicator
            if affordable_count == total_count:
                # All items affordable
                category_text += f" ({total_count}) ✅"
            elif affordable_count > 0:
                # Some items affordable
                category_text += f" ({affordable_count}/{total_count}) ⚠️"
            else:
                # No items affordable
                category_text += f" ({total_count}) ❌"

            builder.button(
                text=category_text,
                callback_data=f"shop_category:{category_name}"
            )

        # Add special navigation buttons
        if not categorized_items:
            builder.button(
                text="🏪 No hay artículos disponibles",
                callback_data="shop_empty"
            )
        else:
            # Add "View All Items" option
            total_items = sum(len(items) for items in categorized_items.values())
            builder.button(
                text=f"📋 Ver Todos ({total_items})",
                callback_data="shop_view_all"
            )

        # Add search functionality
        builder.button(
            text="🔍 Buscar Artículos",
            callback_data="shop_search"
        )

        # Add back button
        builder.button(
            text="🔙 Volver al Menú",
            callback_data="menu_principal"
        )

        # Arrange buttons in a user-friendly layout
        # Categories: 1 per row for readability
        # Special buttons: 2 per row
        category_count = len([cat for cat in sorted_categories if categorized_items[cat]])
        if category_count > 0:
            builder.adjust(*([1] * category_count + [2, 1]))  # Categories in single column, then special buttons
        else:
            builder.adjust(1, 2, 1)  # Empty state, special buttons, back button

    except Exception as e:
        logger.error(f"Error building categorized shop keyboard: {str(e)}")
        # Fallback to simple keyboard
        builder.button(text="❌ Error al cargar tienda", callback_data="shop_error")
        builder.button(text="🔙 Volver", callback_data="menu_principal")
        builder.adjust(1)

    return builder.as_markup()


def build_item_details_keyboard(
    item_details: Dict[str, Any],
    show_purchase_button: bool = True
) -> InlineKeyboardMarkup:
    """
    Build a detailed item view keyboard with purchase eligibility indicators and navigation.

    Args:
        item_details: Detailed item information from ShopService.get_item_details()
        show_purchase_button: Whether to show the purchase button

    Returns:
        InlineKeyboardMarkup for item details view
    """
    builder = InlineKeyboardBuilder()

    try:
        item_id = item_details.get('id')
        user_info = item_details.get('user_info', {})
        eligibility = user_info.get('purchase_eligibility', {})
        pricing = item_details.get('pricing', {})

        # Purchase button with eligibility indicators
        if show_purchase_button and item_id:
            can_purchase = eligibility.get('can_purchase', False)
            already_purchased = user_info.get('already_purchased', False)

            if already_purchased:
                builder.button(
                    text="✅ Ya Comprado",
                    callback_data=f"shop_owned:{item_id}"
                )
            elif can_purchase:
                current_price = pricing.get('current_price', 0)
                is_on_sale = pricing.get('is_on_sale', False)

                price_text = f"💰 Comprar ({current_price} besitos)"
                if is_on_sale:
                    price_text = f"🔥 {price_text} ¡OFERTA!"

                builder.button(
                    text=price_text,
                    callback_data=f"buy_item:{item_id}"
                )
            else:
                # Show why purchase is not possible
                reasons = eligibility.get('reasons', [])
                if 'vip_required' in reasons:
                    builder.button(
                        text="💎 Requiere VIP",
                        callback_data="shop_vip_required"
                    )
                elif 'insufficient_points' in reasons:
                    points_needed = eligibility.get('points_needed', 0)
                    builder.button(
                        text=f"❌ Faltan {points_needed} besitos",
                        callback_data="shop_insufficient_points"
                    )
                else:
                    builder.button(
                        text="❌ No Disponible",
                        callback_data="shop_unavailable"
                    )

        # Content preview button if item unlocks lore
        if item_details.get('unlocks_content', False):
            lore_preview = item_details.get('lore_preview')
            if lore_preview:
                preview_text = "📖 Vista Previa del Contenido"
                if lore_preview.get('is_main_story', False):
                    preview_text = "📚 Vista Previa - Historia Principal"

                builder.button(
                    text=preview_text,
                    callback_data=f"shop_preview:{item_id}"
                )

        # Category navigation if item has category
        category_info = item_details.get('category', {})
        if category_info and category_info.get('name') != "Sin Categoría":
            category_name = category_info['name']
            builder.button(
                text=f"📂 Ver más en {category_name}",
                callback_data=f"shop_category:{category_name}"
            )

        # User status indicators (informational)
        current_points = user_info.get('current_points', 0)
        is_vip = user_info.get('is_vip', False)

        status_text = f"💰 Tus besitos: {current_points}"
        if is_vip:
            status_text += " | 💎 VIP"

        builder.button(
            text=status_text,
            callback_data="shop_user_status"
        )

        # Navigation buttons
        builder.button(
            text="🛒 Volver a Tienda",
            callback_data="shop_access"
        )

        builder.button(
            text="🔙 Menú Principal",
            callback_data="menu_principal"
        )

        # Arrange buttons in logical groups
        button_count = len(builder.export()) if hasattr(builder, 'export') else 3

        if button_count <= 3:
            builder.adjust(1)  # Single column for few buttons
        elif button_count <= 5:
            builder.adjust(1, 1, 1, 2)  # Purchase, preview, category, then navigation
        else:
            builder.adjust(1, 1, 1, 1, 2)  # All major buttons single, navigation double

    except Exception as e:
        logger.error(f"Error building item details keyboard: {str(e)}")
        # Fallback to basic navigation
        builder.button(text="❌ Error al cargar detalles", callback_data="shop_error")
        builder.button(text="🛒 Volver a Tienda", callback_data="shop_access")
        builder.button(text="🔙 Menú Principal", callback_data="menu_principal")
        builder.adjust(1)

    return builder.as_markup()


def build_category_items_keyboard(
    category_name: str,
    items: List[Any],
    user_points: int = 0,
    page: int = 0,
    items_per_page: int = 8
) -> InlineKeyboardMarkup:
    """
    Build a keyboard for items within a specific category with pagination support.

    Args:
        category_name: Name of the category
        items: List of ShopItem objects in the category
        user_points: Current user points for affordability indicators
        page: Current page number (0-based)
        items_per_page: Number of items to show per page

    Returns:
        InlineKeyboardMarkup for category items view
    """
    builder = InlineKeyboardBuilder()

    try:
        # Calculate pagination
        total_items = len(items)
        start_idx = page * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        page_items = items[start_idx:end_idx]

        # Add item buttons
        for item in page_items:
            try:
                # Handle both object and dictionary
                if hasattr(item, 'name'):
                    item_name = item.name
                    item_price = item.price
                    item_id = item.id
                    is_vip_only = getattr(item, 'is_vip_only', False)
                elif isinstance(item, dict):
                    item_name = item.get('name')
                    item_price = item.get('price')
                    item_id = item.get('id')
                    is_vip_only = item.get('is_vip_only', False)
                else:
                    continue

                # Build item button text with affordability indicator
                affordability_indicator = "✅" if user_points >= item_price else "❌"
                vip_indicator = "💎 " if is_vip_only else ""

                button_text = f"{vip_indicator}{item_name} - {item_price} besitos {affordability_indicator}"

                builder.button(
                    text=button_text,
                    callback_data=f"shop_item_details:{item_id}"
                )

            except (AttributeError, KeyError) as e:
                logger.error(f"Invalid item structure in category {category_name}: {item}, error: {e}")
                continue

        # Pagination controls
        total_pages = (total_items + items_per_page - 1) // items_per_page
        if total_pages > 1:
            pagination_buttons = []

            # Previous page
            if page > 0:
                pagination_buttons.append({
                    'text': '⬅️ Anterior',
                    'callback_data': f'shop_category_page:{category_name}:{page-1}'
                })

            # Page indicator
            pagination_buttons.append({
                'text': f'{page + 1}/{total_pages}',
                'callback_data': f'shop_page_info:{page}'
            })

            # Next page
            if page < total_pages - 1:
                pagination_buttons.append({
                    'text': 'Siguiente ➡️',
                    'callback_data': f'shop_category_page:{category_name}:{page+1}'
                })

            # Add pagination buttons
            for btn in pagination_buttons:
                builder.button(text=btn['text'], callback_data=btn['callback_data'])

        # Navigation buttons
        builder.button(
            text="🛒 Todas las Categorías",
            callback_data="shop_access"
        )

        builder.button(
            text="🔙 Menú Principal",
            callback_data="menu_principal"
        )

        # Layout: items in single column, pagination controls inline, navigation separate
        items_count = len(page_items)
        pagination_count = len([btn for btn in builder.export()[-4:-2]]) if total_pages > 1 else 0

        if items_count > 0:
            layout = [1] * items_count  # Items in single column
            if pagination_count > 0:
                layout.extend([pagination_count])  # Pagination in one row
            layout.extend([2])  # Navigation buttons in one row
            builder.adjust(*layout)
        else:
            builder.adjust(2)  # Just navigation if no items

    except Exception as e:
        logger.error(f"Error building category items keyboard for {category_name}: {str(e)}")
        # Fallback
        builder.button(text="❌ Error al cargar categoría", callback_data="shop_error")
        builder.button(text="🛒 Volver a Tienda", callback_data="shop_access")
        builder.adjust(1)

    return builder.as_markup()