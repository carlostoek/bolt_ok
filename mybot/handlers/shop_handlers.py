import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from services.coordinador_central import CoordinadorCentral, AccionUsuario
from services.shop_cache_service import ShopCacheService
from services.subscription_service import SubscriptionService
from keyboards.common import build_shop_keyboard, get_back_kb
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()
logger = logging.getLogger(__name__)

class ShopSearchStates(StatesGroup):
    waiting_for_search_query = State()
    waiting_for_min_price = State()
    waiting_for_max_price = State()

@router.callback_query(F.data == "shop_access")
async def show_shop(callback: CallbackQuery, session: AsyncSession):
    """Show shop main page with caching optimization"""
    try:
        logger.info(f"Shop access requested by user {callback.from_user.id}")
        user_id = callback.from_user.id

        # Initialize cache service for performance optimization
        cache_service = ShopCacheService(session)
        subscription_service = SubscriptionService(session)

        # Check user VIP status for filtering
        subscription = await subscription_service.get_subscription(user_id)
        is_vip = subscription is not None and (subscription.expires_at is None or subscription.expires_at > datetime.utcnow())

        # Get cached available items for the user
        items = await cache_service.get_user_available_items(user_id, is_vip)

        logger.info(f"Retrieved {len(items)} cached items for user {user_id}")

        if items:
            # Convert items to the format expected by the keyboard builder
            items_data = []
            for item in items:
                items_data.append({
                    'id': item.id,
                    'name': item.name,
                    'price': item.price,
                    'is_vip_only': item.is_vip_only
                })

            # Build keyboard with cached data
            from keyboards.common import build_shop_keyboard
            keyboard = build_shop_keyboard(items_data)
            await callback.message.edit_text("🛒 Tienda - Elige un artículo:", reply_markup=keyboard)
        else:
            await callback.answer("❌ No hay artículos disponibles en la tienda en este momento", show_alert=True)

    except Exception as e:
        logger.error(f"Error in show_shop: {e}", exc_info=True)
        await callback.answer("❌ Error al cargar la tienda. Intenta más tarde.", show_alert=True)

@router.callback_query(F.data == "shop_browse_categories")
async def show_category_list(callback: CallbackQuery, session: AsyncSession):
    """Show list of available shop categories with caching optimization"""
    try:
        logger.info(f"Category list requested by user {callback.from_user.id}")
        user_id = callback.from_user.id

        # Initialize cache service
        cache_service = ShopCacheService(session)
        subscription_service = SubscriptionService(session)

        # Check user VIP status for filtering
        subscription = await subscription_service.get_subscription(user_id)
        is_vip = subscription is not None and (subscription.expires_at is None or subscription.expires_at > datetime.utcnow())

        # Get cached available items for the user
        user_items = await cache_service.get_user_available_items(user_id, is_vip)

        if not user_items:
            await callback.message.edit_text(
                "🛒 **Tienda por Categorías**\n\n❌ No hay categorías disponibles en este momento.",
                reply_markup=get_back_kb("shop_access")
            )
            return

        # Get cached categories and organize items by category
        categories = await cache_service.get_active_categories()

        # Organize items by category
        categorized_items = {}

        # Process items with categories
        for item in user_items:
            if item.category_id:
                # Find the category for this item
                category = next((cat for cat in categories if cat.id == item.category_id), None)
                if category and (is_vip or not category.is_vip_only):
                    category_name = category.name
                    if category_name not in categorized_items:
                        categorized_items[category_name] = []
                    categorized_items[category_name].append(item)
            else:
                # Uncategorized items
                if "Sin Categoría" not in categorized_items:
                    categorized_items["Sin Categoría"] = []
                categorized_items["Sin Categoría"].append(item)

        if not categorized_items:
            await callback.message.edit_text(
                "🛒 **Tienda por Categorías**\n\n❌ No hay categorías disponibles en este momento.",
                reply_markup=get_back_kb("shop_access")
            )
            return

        # Build category selection keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        for category_name, items in categorized_items.items():
            if items:  # Only show categories with items
                item_count = len(items)
                builder.button(
                    text=f"📁 {category_name} ({item_count})",
                    callback_data=f"shop_category:{category_name}"
                )

        builder.button(text="🔙 Volver a Tienda", callback_data="shop_access")
        builder.adjust(1)

        text = "🛒 **Tienda por Categorías**\n\n💫 Selecciona una categoría para explorar:"
        await callback.message.edit_text(text, reply_markup=builder.as_markup())

    except Exception as e:
        logger.error(f"Error showing categories for user {callback.from_user.id}: {e}", exc_info=True)
        await callback.answer("❌ Error al cargar categorías. Intenta más tarde.", show_alert=True)

@router.callback_query(F.data.startswith("shop_category:"))
async def show_category_items(callback: CallbackQuery, session: AsyncSession):
    """Show items in a specific category with caching optimization"""
    try:
        # Parse the category name
        category_name = callback.data.split(":", 1)[1]
        user_id = callback.from_user.id

        logger.info(f"Category '{category_name}' requested by user {user_id}")

        # Initialize cache service
        cache_service = ShopCacheService(session)
        subscription_service = SubscriptionService(session)

        # Check user VIP status for filtering
        subscription = await subscription_service.get_subscription(user_id)
        is_vip = subscription is not None and (subscription.expires_at is None or subscription.expires_at > datetime.utcnow())

        # Get cached available items for the user
        user_items = await cache_service.get_user_available_items(user_id, is_vip)

        if not user_items:
            await callback.message.edit_text(
                f"📁 **{category_name}**\n\n❌ No hay artículos disponibles en esta categoría.",
                reply_markup=get_back_kb("shop_browse_categories")
            )
            return

        # Get cached categories to match category name to ID
        categories = await cache_service.get_active_categories()

        # Find category items using cache
        category_items = []

        if category_name == "Sin Categoría":
            # Get uncategorized items
            category_items = [item for item in user_items if item.category_id is None]
        else:
            # Find the category ID for the given name
            target_category = next((cat for cat in categories if cat.name == category_name and (is_vip or not cat.is_vip_only)), None)
            if target_category:
                category_items = [item for item in user_items if item.category_id == target_category.id]

        if not category_items:
            await callback.message.edit_text(
                f"📁 **{category_name}**\n\n❌ No hay artículos disponibles en esta categoría.",
                reply_markup=get_back_kb("shop_browse_categories")
            )
            return

        # Build items keyboard for this category
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        for item in category_items:
            vip_badge = " 👑" if item.is_vip_only else ""
            builder.button(
                text=f"{item.name} - {item.price} besitos{vip_badge}",
                callback_data=f"item_details:{item.id}"
            )

        # Navigation buttons
        builder.button(text="🔙 Volver a Categorías", callback_data="shop_browse_categories")
        builder.button(text="🏪 Tienda Principal", callback_data="shop_access")
        builder.adjust(1)

        text = f"📁 **{category_name}**\n\n💫 Artículos disponibles:"
        await callback.message.edit_text(text, reply_markup=builder.as_markup())

    except Exception as e:
        logger.error(f"Error showing category items for user {callback.from_user.id}: {e}", exc_info=True)
        await callback.answer("❌ Error al cargar artículos. Intenta más tarde.", show_alert=True)

@router.callback_query(F.data.startswith("item_details:"))
async def show_item_details(callback: CallbackQuery, session: AsyncSession):
    """Show detailed information about a specific shop item"""
    try:
        # Parse the item ID
        item_id = int(callback.data.split(":", 1)[1])
        user_id = callback.from_user.id

        logger.info(f"Item details requested for item {item_id} by user {user_id}")

        # Import ShopService to get item details
        from services.shop_service import ShopService
        shop_service = ShopService(session)
        item_details = await shop_service.get_item_details(user_id, item_id)

        if not item_details:
            await callback.message.edit_text(
                "❌ **Artículo no encontrado**\n\nEl artículo solicitado no está disponible.",
                reply_markup=get_back_kb("shop_access")
            )
            return

        # Build detailed item information text
        text_parts = []

        # Header with item name and category
        category_name = item_details["category"]["name"]
        vip_badge = " 👑" if item_details["is_vip_only"] else ""
        text_parts.append(f"🛍️ **{item_details['name']}**{vip_badge}")
        text_parts.append(f"📁 *Categoría: {category_name}*")
        text_parts.append("")

        # Description
        text_parts.append(f"📝 **Descripción:**")
        text_parts.append(item_details["description"])
        text_parts.append("")

        # Pricing information
        pricing = item_details["pricing"]
        if pricing["is_on_sale"]:
            text_parts.append(f"💰 **Precio:** ~~{pricing['base_price']}~~ **{pricing['current_price']} besitos** ({pricing['discount_percentage']}% descuento)")
            if pricing["promotion_name"]:
                text_parts.append(f"🎉 *Promoción: {pricing['promotion_name']}*")
        else:
            text_parts.append(f"💰 **Precio:** {pricing['current_price']} besitos")
        text_parts.append("")

        # User's current points
        user_info = item_details["user_info"]
        text_parts.append(f"💎 **Tus besitos:** {user_info['current_points']}")
        text_parts.append("")

        # Unlock preview if available
        if item_details["unlocks_content"] and item_details["lore_preview"]:
            lore = item_details["lore_preview"]
            text_parts.append("🔓 **Desbloquea contenido exclusivo:**")
            text_parts.append(f"📖 *{lore['title']}*")
            if lore["description"]:
                text_parts.append(lore["description"])

            # Content type indicator
            content_type_emoji = {
                "text": "📄",
                "image": "🖼️",
                "audio": "🎵",
                "video": "🎬"
            }
            type_emoji = content_type_emoji.get(lore["content_type"], "📄")
            text_parts.append(f"{type_emoji} *Tipo: {lore['content_type'].title()}*")

            # Preview of content
            if lore["content_preview"]:
                text_parts.append("")
                text_parts.append("👁️ **Vista previa:**")
                text_parts.append(f"*{lore['content_preview']}*")

            # Story indicator
            if lore.get("is_main_story"):
                text_parts.append("⭐ *Parte de la historia principal*")

            text_parts.append("")

        # Purchase eligibility and status
        eligibility = user_info["purchase_eligibility"]

        if user_info["already_purchased"]:
            text_parts.append("✅ **Ya tienes este artículo**")
            text_parts.append("Este artículo está en tu mochila.")
        elif eligibility["can_purchase"]:
            text_parts.append("🟢 **Disponible para comprar**")
            text_parts.append("Puedes adquirir este artículo ahora.")
        else:
            text_parts.append("🔴 **No disponible para comprar**")
            reasons = eligibility["reasons"]

            if "vip_required" in reasons:
                text_parts.append("👑 Requiere suscripción VIP")
            if "insufficient_points" in reasons:
                points_needed = eligibility.get("points_needed", 0)
                text_parts.append(f"💎 Te faltan {points_needed} besitos")

        # VIP requirement notice
        if item_details["is_vip_only"] and not user_info["is_vip"]:
            text_parts.append("")
            text_parts.append("👑 **Artículo exclusivo VIP**")
            text_parts.append("Este artículo requiere una suscripción VIP activa.")

        final_text = "\n".join(text_parts)

        # Build action keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        # Purchase button (if eligible)
        if not user_info["already_purchased"] and eligibility["can_purchase"]:
            builder.button(
                text=f"💳 Comprar por {pricing['current_price']} besitos",
                callback_data=f"buy_item:{item_id}"
            )

        # VIP upgrade button (if VIP required and user is not VIP)
        if item_details["is_vip_only"] and not user_info["is_vip"]:
            builder.button(
                text="👑 Obtener VIP",
                callback_data="vip_upgrade"
            )

        # Navigation buttons
        builder.button(text="🔙 Volver a Categorías", callback_data="shop_browse_categories")
        builder.button(text="🏪 Tienda Principal", callback_data="shop_access")
        builder.adjust(1)

        await callback.message.edit_text(final_text, reply_markup=builder.as_markup())

    except ValueError:
        await callback.answer("❌ ID de artículo inválido", show_alert=True)
    except Exception as e:
        logger.error(f"Error showing item details for user {callback.from_user.id}: {e}", exc_info=True)
        await callback.answer("❌ Error al cargar detalles del artículo. Intenta más tarde.", show_alert=True)

@router.callback_query(F.data.startswith("buy_item:"))
async def handle_purchase(callback: CallbackQuery, session: AsyncSession):
    try:
        # Parse the item ID
        item_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id

        # Get item details first to display promotional pricing in confirmation
        from services.shop_service import ShopService
        shop_service = ShopService(session)
        item_details = await shop_service.get_item_details(user_id, item_id)

        if not item_details:
            await callback.answer("❌ Artículo no encontrado", show_alert=True)
            return

        # Check if user can purchase before showing confirmation
        eligibility = item_details["user_info"]["purchase_eligibility"]
        if not eligibility["can_purchase"]:
            reasons = eligibility["reasons"]
            if "already_purchased" in reasons:
                await callback.answer("❌ Ya tienes este artículo", show_alert=True)
            elif "vip_required" in reasons:
                await callback.answer("❌ Requiere suscripción VIP", show_alert=True)
            elif "insufficient_points" in reasons:
                points_needed = eligibility.get("points_needed", 0)
                await callback.answer(f"❌ Te faltan {points_needed} besitos", show_alert=True)
            else:
                await callback.answer("❌ No puedes comprar este artículo", show_alert=True)
            return

        # Build enhanced purchase confirmation with promotional pricing
        pricing = item_details["pricing"]
        confirmation_parts = []

        confirmation_parts.append(f"🛍️ **Confirmar Compra**")
        confirmation_parts.append(f"📦 **Artículo:** {item_details['name']}")

        # Enhanced pricing display with promotion information
        if pricing["is_on_sale"]:
            confirmation_parts.append(f"💰 **Precio:** ~~{pricing['base_price']}~~ **{pricing['current_price']} besitos**")
            confirmation_parts.append(f"🎉 **Descuento:** {pricing['discount_percentage']}% OFF")
            if pricing["promotion_name"]:
                confirmation_parts.append(f"✨ **Promoción:** {pricing['promotion_name']}")
        else:
            confirmation_parts.append(f"💰 **Precio:** {pricing['current_price']} besitos")

        user_info = item_details["user_info"]
        confirmation_parts.append(f"💎 **Tus besitos:** {user_info['current_points']}")

        # Calculate remaining points after purchase
        remaining_points = user_info['current_points'] - pricing['current_price']
        confirmation_parts.append(f"💎 **Después de la compra:** {remaining_points} besitos")

        # Add content unlock information if applicable
        if item_details["unlocks_content"] and item_details["lore_preview"]:
            confirmation_parts.append("")
            confirmation_parts.append("🔓 **Desbloquearás:**")
            lore = item_details["lore_preview"]
            confirmation_parts.append(f"📖 {lore['title']}")

        confirmation_parts.append("")
        confirmation_parts.append("¿Confirmar la compra?")

        confirmation_text = "\n".join(confirmation_parts)

        # Build confirmation keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        # Use current price from promotional pricing calculation
        builder.button(
            text=f"✅ Confirmar ({pricing['current_price']} besitos)",
            callback_data=f"confirm_purchase:{item_id}"
        )
        builder.button(text="❌ Cancelar", callback_data=f"item_details:{item_id}")
        builder.adjust(1)

        await callback.message.edit_text(confirmation_text, reply_markup=builder.as_markup())

    except ValueError:
        await callback.answer("❌ ID de artículo inválido", show_alert=True)
    except Exception as e:
        logger.error(f"Error handling purchase for user {callback.from_user.id}: {str(e)}")
        await callback.answer("❌ Error interno al procesar la compra", show_alert=True)

@router.callback_query(F.data.startswith("confirm_purchase:"))
async def confirm_purchase(callback: CallbackQuery, session: AsyncSession):
    """Handle the final purchase confirmation with enhanced feedback"""
    try:
        # Parse the item ID
        item_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id

        # Execute purchase through CoordinadorCentral
        coordinador = CoordinadorCentral(session)
        result = await coordinador.ejecutar_flujo(
            user_id,
            AccionUsuario.COMPRAR_ITEM,
            item_id=item_id
        )

        if result["success"]:
            # Get item details again for success message with promotional info
            from services.shop_service import ShopService
            shop_service = ShopService(session)
            item_details = await shop_service.get_item_details(user_id, item_id)

            # Enhanced success message
            success_parts = []
            success_parts.append("🎉 **¡Compra Exitosa!**")
            success_parts.append(f"✅ Has adquirido: **{item_details['name'] if item_details else 'Artículo'}**")

            # Show promotional savings if applicable
            if item_details and item_details["pricing"]["is_on_sale"]:
                savings = item_details["pricing"]["base_price"] - item_details["pricing"]["current_price"]
                success_parts.append(f"💰 **Ahorro:** {savings} besitos ({item_details['pricing']['discount_percentage']}% descuento)")

            success_parts.append("")
            success_parts.append("🎒 El artículo se ha añadido a tu inventario.")

            if result.get("unlocked_lore"):
                success_parts.append("📖 ¡Has desbloqueado nuevo contenido narrativo!")

            success_text = "\n".join(success_parts)

            # Build navigation keyboard
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="🎒 Ver Inventario", callback_data="show_user_inventory")
            builder.button(text="🛒 Seguir Comprando", callback_data="shop_access")
            builder.adjust(1)

            await callback.message.edit_text(success_text, reply_markup=builder.as_markup())

            # Show brief success notification
            await callback.answer("✅ ¡Compra completada!", show_alert=False)

        else:
            # Enhanced error handling with promotional context
            error_message = result.get('message', 'Error al procesar la compra')
            await callback.answer(f"❌ {error_message}", show_alert=True)

            # Return to item details on error
            await show_item_details(callback, session)

    except ValueError:
        await callback.answer("❌ ID de artículo inválido", show_alert=True)
    except Exception as e:
        logger.error(f"Error confirming purchase for user {callback.from_user.id}: {str(e)}")
        await callback.answer("❌ Error interno al confirmar la compra", show_alert=True)

@router.callback_query(F.data == "shop_search")
async def show_search_menu(callback: CallbackQuery, session: AsyncSession):
    """Show search options menu"""
    try:
        logger.info(f"Search menu requested by user {callback.from_user.id}")

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        # Search options
        builder.button(text="🔍 Buscar por nombre", callback_data="search_by_name")
        builder.button(text="💰 Filtrar por precio", callback_data="search_by_price")
        builder.button(text="🔍💰 Búsqueda avanzada", callback_data="search_advanced")
        builder.button(text="📁 Ver categorías", callback_data="shop_browse_categories")
        builder.button(text="🔙 Volver a Tienda", callback_data="shop_access")
        builder.adjust(1)

        text = (
            "🔍 **Búsqueda y Filtros**\n\n"
            "💫 Selecciona cómo quieres buscar artículos:\n\n"
            "🔍 **Buscar por nombre** - Encuentra artículos específicos\n"
            "💰 **Filtrar por precio** - Busca dentro de tu presupuesto\n"
            "🔍💰 **Búsqueda avanzada** - Combina nombre y precio\n"
            "📁 **Ver categorías** - Navega por categorías organizadas"
        )

        await callback.message.edit_text(text, reply_markup=builder.as_markup())

    except Exception as e:
        logger.error(f"Error showing search menu for user {callback.from_user.id}: {e}", exc_info=True)
        await callback.answer("❌ Error al cargar el menú de búsqueda", show_alert=True)

@router.callback_query(F.data == "search_by_name")
async def start_name_search(callback: CallbackQuery, state: FSMContext):
    """Start search by name flow"""
    try:
        logger.info(f"Name search started by user {callback.from_user.id}")

        await state.set_state(ShopSearchStates.waiting_for_search_query)

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="❌ Cancelar", callback_data="shop_search")

        text = (
            "🔍 **Búsqueda por nombre**\n\n"
            "💫 Escribe el nombre o parte del nombre del artículo que buscas.\n"
            "La búsqueda también incluye las descripciones de los artículos.\n\n"
            "✨ Ejemplos: \"diario\", \"secreto\", \"íntimo\""
        )

        await callback.message.edit_text(text, reply_markup=builder.as_markup())

    except Exception as e:
        logger.error(f"Error starting name search for user {callback.from_user.id}: {e}", exc_info=True)
        await callback.answer("❌ Error al iniciar búsqueda", show_alert=True)

@router.message(ShopSearchStates.waiting_for_search_query)
async def handle_shop_search(message: Message, state: FSMContext, session: AsyncSession):
    """Handle search query and display results"""
    try:
        search_query = message.text.strip()
        user_id = message.from_user.id

        logger.info(f"Processing search query '{search_query}' for user {user_id}")

        if len(search_query) < 2:
            await message.answer(
                "❌ **Búsqueda muy corta**\n\n"
                "Por favor, escribe al menos 2 caracteres para buscar.",
                reply_markup=get_back_kb("shop_search")
            )
            return

        # Clear the state
        await state.clear()

        # Search items using ShopService
        from services.shop_service import ShopService
        shop_service = ShopService(session)
        search_results = await shop_service.search_items(
            user_id=user_id,
            search_query=search_query,
            limit=20  # Limit results for better UX
        )

        if not search_results:
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="🔍 Nueva búsqueda", callback_data="search_by_name")
            builder.button(text="🔙 Volver a búsqueda", callback_data="shop_search")

            text = (
                f"🔍 **Búsqueda: \"{search_query}\"**\n\n"
                "❌ No se encontraron artículos que coincidan con tu búsqueda.\n\n"
                "💡 **Sugerencias:**\n"
                "• Intenta con palabras más cortas\n"
                "• Revisa la ortografía\n"
                "• Usa términos más generales"
            )

            await message.answer(text, reply_markup=builder.as_markup())
            return

        # Display search results
        await _display_search_results(message, search_results, search_query)

    except Exception as e:
        logger.error(f"Error handling search for user {message.from_user.id}: {e}", exc_info=True)
        await state.clear()
        await message.answer(
            "❌ Error al procesar la búsqueda. Intenta nuevamente.",
            reply_markup=get_back_kb("shop_search")
        )

@router.callback_query(F.data == "search_by_price")
async def start_price_filter(callback: CallbackQuery, state: FSMContext):
    """Start price filter flow"""
    try:
        logger.info(f"Price filter started by user {callback.from_user.id}")

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        # Common price ranges
        builder.button(text="💎 0-25 besitos", callback_data="price_range:0:25")
        builder.button(text="💎 26-50 besitos", callback_data="price_range:26:50")
        builder.button(text="💎 51-100 besitos", callback_data="price_range:51:100")
        builder.button(text="💎 101+ besitos", callback_data="price_range:101:")
        builder.button(text="🔧 Rango personalizado", callback_data="price_range_custom")
        builder.button(text="🔙 Volver a búsqueda", callback_data="shop_search")
        builder.adjust(1)

        text = (
            "💰 **Filtro por precio**\n\n"
            "💫 Selecciona un rango de precios o define uno personalizado:\n\n"
            "💎 Puedes elegir rangos predefinidos o crear tu propio rango de precios."
        )

        await callback.message.edit_text(text, reply_markup=builder.as_markup())

    except Exception as e:
        logger.error(f"Error starting price filter for user {callback.from_user.id}: {e}", exc_info=True)
        await callback.answer("❌ Error al iniciar filtro de precio", show_alert=True)

@router.callback_query(F.data.startswith("price_range:"))
async def handle_price_range_search(callback: CallbackQuery, session: AsyncSession):
    """Handle predefined price range search"""
    try:
        # Parse price range from callback data
        parts = callback.data.split(":")
        min_price = int(parts[1]) if parts[1] else None
        max_price = int(parts[2]) if len(parts) > 2 and parts[2] else None

        user_id = callback.from_user.id

        logger.info(f"Price range search: {min_price}-{max_price} for user {user_id}")

        # Search items using ShopService
        from services.shop_service import ShopService
        shop_service = ShopService(session)
        search_results = await shop_service.search_items(
            user_id=user_id,
            min_price=min_price,
            max_price=max_price,
            limit=30
        )

        # Format price range for display
        if min_price is not None and max_price is not None:
            price_display = f"{min_price}-{max_price} besitos"
        elif min_price is not None:
            price_display = f"{min_price}+ besitos"
        else:
            price_display = f"hasta {max_price} besitos"

        if not search_results:
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="💰 Otro rango", callback_data="search_by_price")
            builder.button(text="🔙 Volver a búsqueda", callback_data="shop_search")

            text = (
                f"💰 **Rango de precio: {price_display}**\n\n"
                "❌ No se encontraron artículos en este rango de precios.\n\n"
                "💡 Intenta con un rango diferente."
            )

            await callback.message.edit_text(text, reply_markup=builder.as_markup())
            return

        # Display search results
        await _display_search_results_callback(callback, search_results, f"Precio: {price_display}")

    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing price range for user {callback.from_user.id}: {e}")
        await callback.answer("❌ Rango de precio inválido", show_alert=True)
    except Exception as e:
        logger.error(f"Error handling price range search for user {callback.from_user.id}: {e}", exc_info=True)
        await callback.answer("❌ Error al procesar el filtro de precio", show_alert=True)

@router.callback_query(F.data == "search_advanced")
async def start_advanced_search(callback: CallbackQuery, state: FSMContext):
    """Start advanced search flow (name + price)"""
    try:
        logger.info(f"Advanced search started by user {callback.from_user.id}")

        await state.set_state(ShopSearchStates.waiting_for_search_query)
        await state.update_data(is_advanced=True)

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="❌ Cancelar", callback_data="shop_search")

        text = (
            "🔍💰 **Búsqueda avanzada**\n\n"
            "**Paso 1 de 3:** Escribe el nombre o parte del nombre del artículo\n\n"
            "💫 Después podrás definir el rango de precios.\n"
            "✨ También puedes dejar este paso en blanco para buscar solo por precio."
        )

        await callback.message.edit_text(text, reply_markup=builder.as_markup())

    except Exception as e:
        logger.error(f"Error starting advanced search for user {callback.from_user.id}: {e}", exc_info=True)
        await callback.answer("❌ Error al iniciar búsqueda avanzada", show_alert=True)

async def _display_search_results(message: Message, results: list, search_criteria: str):
    """Display search results in a message"""
    try:
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        # Add items to keyboard
        for item in results[:15]:  # Limit to 15 items for better UX
            vip_badge = " 👑" if item.is_vip_only else ""
            builder.button(
                text=f"{item.name} - {item.price} besitos{vip_badge}",
                callback_data=f"item_details:{item.id}"
            )

        # Navigation buttons
        builder.button(text="🔍 Nueva búsqueda", callback_data="shop_search")
        builder.button(text="🏪 Tienda Principal", callback_data="shop_access")
        builder.adjust(1)

        # Build results text
        text_parts = [f"🔍 **Resultados de búsqueda: \"{search_criteria}\"**\n"]
        text_parts.append(f"📊 Encontrados: {len(results)} artículo(s)\n")

        if len(results) > 15:
            text_parts.append("📌 Mostrando los primeros 15 resultados\n")

        text_parts.append("💫 Selecciona un artículo para ver detalles:")

        await message.answer("\n".join(text_parts), reply_markup=builder.as_markup())

    except Exception as e:
        logger.error(f"Error displaying search results: {e}", exc_info=True)
        await message.answer("❌ Error al mostrar resultados", reply_markup=get_back_kb("shop_search"))

async def _display_search_results_callback(callback: CallbackQuery, results: list, search_criteria: str):
    """Display search results in a callback response"""
    try:
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        # Add items to keyboard
        for item in results[:15]:  # Limit to 15 items for better UX
            vip_badge = " 👑" if item.is_vip_only else ""
            builder.button(
                text=f"{item.name} - {item.price} besitos{vip_badge}",
                callback_data=f"item_details:{item.id}"
            )

        # Navigation buttons
        builder.button(text="🔍 Nueva búsqueda", callback_data="shop_search")
        builder.button(text="🏪 Tienda Principal", callback_data="shop_access")
        builder.adjust(1)

        # Build results text
        text_parts = [f"🔍 **Resultados de búsqueda: {search_criteria}**\n"]
        text_parts.append(f"📊 Encontrados: {len(results)} artículo(s)\n")

        if len(results) > 15:
            text_parts.append("📌 Mostrando los primeros 15 resultados\n")

        text_parts.append("💫 Selecciona un artículo para ver detalles:")

        await callback.message.edit_text("\n".join(text_parts), reply_markup=builder.as_markup())

    except Exception as e:
        logger.error(f"Error displaying search results: {e}", exc_info=True)
        await callback.answer("❌ Error al mostrar resultados", show_alert=True)

@router.callback_query(F.data == "show_user_inventory")
async def show_user_inventory(callback: CallbackQuery, session: AsyncSession):
    """Show user's inventory (purchased items) with usage tracking"""
    try:
        user_id = callback.from_user.id
        logger.info(f"Inventory requested by user {user_id}")

        # Get user inventory using ShopService
        from services.shop_service import ShopService
        shop_service = ShopService(session)
        inventory_items = await shop_service.get_user_inventory(user_id)

        if not inventory_items:
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="🛒 Ir a la Tienda", callback_data="shop_access")
            builder.button(text="🔙 Volver al Menú", callback_data="main_menu")
            builder.adjust(1)

            text = (
                "🎒 **Tu Inventario**\n\n"
                "📭 Tu inventario está vacío.\n\n"
                "💫 ¡Visita la tienda para comprar artículos exclusivos!\n"
                "🎁 Los artículos comprados aparecerán aquí y podrás acceder a su contenido especial."
            )

            await callback.message.edit_text(text, reply_markup=builder.as_markup())
            return

        # Group items by category for better organization
        categorized_inventory = {}
        for item in inventory_items:
            category = item["category_name"]
            if category not in categorized_inventory:
                categorized_inventory[category] = []
            categorized_inventory[category].append(item)

        # Build inventory display
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        # Add items to keyboard
        for category, items in categorized_inventory.items():
            # Add category header (if more than one category)
            if len(categorized_inventory) > 1:
                builder.button(
                    text=f"📁 {category} ({len(items)})",
                    callback_data=f"inventory_category:{category}"
                )

            # Add individual items
            for item in items:
                # Create status indicators
                status_indicators = []
                if item["is_vip_only"]:
                    status_indicators.append("👑")
                if item["has_lore_content"]:
                    if item["lore_accessed"]:
                        status_indicators.append("📖✅")  # Content accessed
                    else:
                        status_indicators.append("📖🔒")  # Content not accessed

                status_text = "".join(status_indicators)
                item_text = f"{item['name']}{' ' + status_text if status_text else ''}"

                builder.button(
                    text=item_text,
                    callback_data=f"inventory_item:{item['item_id']}"
                )

        # Navigation buttons
        builder.button(text="🛒 Ir a la Tienda", callback_data="shop_access")
        builder.button(text="🔙 Volver al Menú", callback_data="main_menu")
        builder.adjust(1)

        # Build header text
        total_items = len(inventory_items)
        total_spent = sum(item["price_paid"] for item in inventory_items)
        lore_items = sum(1 for item in inventory_items if item["has_lore_content"])
        accessed_lore = sum(1 for item in inventory_items if item["has_lore_content"] and item["lore_accessed"])

        text_parts = [
            "🎒 **Tu Inventario**\n",
            f"📊 **Estadísticas:**",
            f"• Artículos totales: {total_items}",
            f"• Besitos gastados: {total_spent}",
            f"• Contenido narrativo: {accessed_lore}/{lore_items}",
            "",
            "💫 **Leyenda:**",
            "👑 Artículo VIP",
            "📖✅ Contenido leído",
            "📖🔒 Contenido disponible",
            "",
            "🎁 Selecciona un artículo para ver detalles o acceder a su contenido:"
        ]

        await callback.message.edit_text("\n".join(text_parts), reply_markup=builder.as_markup())

    except Exception as e:
        logger.error(f"Error showing inventory for user {callback.from_user.id}: {e}", exc_info=True)
        await callback.answer("❌ Error al cargar el inventario. Intenta más tarde.", show_alert=True)

@router.callback_query(F.data.startswith("inventory_item:"))
async def show_inventory_item_details(callback: CallbackQuery, session: AsyncSession):
    """Show detailed information about a specific inventory item"""
    try:
        # Parse the item ID
        item_id = int(callback.data.split(":", 1)[1])
        user_id = callback.from_user.id

        logger.info(f"Inventory item details requested for item {item_id} by user {user_id}")

        # Get detailed item information from ShopService
        from services.shop_service import ShopService
        shop_service = ShopService(session)
        item_details = await shop_service.get_inventory_item_details(user_id, item_id)

        if not item_details:
            await callback.message.edit_text(
                "❌ **Artículo no encontrado**\n\nEl artículo no está en tu inventario.",
                reply_markup=get_back_kb("show_user_inventory")
            )
            return

        # Build detailed item information text
        text_parts = []

        # Header with item name and category
        category_name = item_details["category"]["name"]
        vip_badge = " 👑" if item_details["is_vip_only"] else ""
        text_parts.append(f"🎒 **{item_details['name']}**{vip_badge}")
        text_parts.append(f"📁 *Categoría: {category_name}*")
        text_parts.append("")

        # Purchase information
        purchase_date = item_details["purchased_at"].strftime("%d/%m/%Y %H:%M")
        text_parts.append(f"📅 **Comprado:** {purchase_date}")
        text_parts.append(f"💰 **Precio pagado:** {item_details['price_paid']} besitos")
        text_parts.append("")

        # Description
        text_parts.append(f"📝 **Descripción:**")
        text_parts.append(item_details["description"])
        text_parts.append("")

        # Lore content information
        lore_details = item_details.get("lore_details")
        if lore_details:
            text_parts.append("📖 **Contenido Narrativo Desbloqueado:**")
            text_parts.append(f"🏷️ *{lore_details['title']}*")

            if lore_details.get("description"):
                text_parts.append(lore_details["description"])

            # Content type indicator
            content_type_emoji = {
                "text": "📄",
                "image": "🖼️",
                "audio": "🎵",
                "video": "🎬"
            }
            type_emoji = content_type_emoji.get(lore_details["content_type"], "📄")
            text_parts.append(f"{type_emoji} *Tipo: {lore_details['content_type'].title()}*")

            # Access status
            if lore_details["accessed"]:
                access_date = lore_details["accessed_at"].strftime("%d/%m/%Y %H:%M")
                text_parts.append(f"✅ *Accedido el {access_date}*")
            else:
                text_parts.append("🔒 *Contenido disponible - No accedido aún*")

            # Story indicator
            if lore_details.get("is_main_story"):
                text_parts.append("⭐ *Parte de la historia principal*")

            text_parts.append("")

        final_text = "\n".join(text_parts)

        # Build action keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        # Access lore content button (if available and not accessed)
        if lore_details and not lore_details["accessed"]:
            builder.button(
                text="📖 Leer Contenido",
                callback_data=f"access_lore:{lore_details['id']}"
            )

        # View content again button (if already accessed)
        if lore_details and lore_details["accessed"]:
            builder.button(
                text="📖 Leer de Nuevo",
                callback_data=f"access_lore:{lore_details['id']}"
            )

        # Navigation buttons
        builder.button(text="🎒 Volver al Inventario", callback_data="show_user_inventory")
        builder.button(text="🛒 Ir a la Tienda", callback_data="shop_access")
        builder.adjust(1)

        await callback.message.edit_text(final_text, reply_markup=builder.as_markup())

    except ValueError:
        await callback.answer("❌ ID de artículo inválido", show_alert=True)
    except Exception as e:
        logger.error(f"Error showing inventory item details for user {callback.from_user.id}: {e}", exc_info=True)
        await callback.answer("❌ Error al cargar detalles del artículo. Intenta más tarde.", show_alert=True)

@router.callback_query(F.data.startswith("access_lore:"))
async def access_lore_content(callback: CallbackQuery, session: AsyncSession):
    """Allow user to access lore content from their inventory"""
    try:
        # Parse the lore piece ID
        lore_piece_id = int(callback.data.split(":", 1)[1])
        user_id = callback.from_user.id

        logger.info(f"Lore content access requested for lore {lore_piece_id} by user {user_id}")

        # Use CoordinadorCentral to handle lore access
        coordinador = CoordinadorCentral(session)
        result = await coordinador.ejecutar_flujo(
            user_id,
            AccionUsuario.ACCEDER_LORE,
            lore_piece_id=lore_piece_id
        )

        if result["success"]:
            await callback.answer("✅ Accediendo al contenido...", show_alert=False)

            # The CoordinadorCentral should handle the lore display
            # For now, we'll show a confirmation and redirect back to inventory
            await callback.message.answer(
                "📖 **Contenido Narrativo Desbloqueado**\n\n"
                "✨ Has accedido al contenido exclusivo. El contenido se ha mostrado en la conversación.\n\n"
                "🎒 Puedes volver a acceder a este contenido desde tu inventario en cualquier momento."
            )

            # Return to inventory
            await show_user_inventory(callback, session)
        else:
            await callback.answer(f"❌ {result.get('message', 'Error al acceder al contenido')}", show_alert=True)

    except ValueError:
        await callback.answer("❌ ID de contenido inválido", show_alert=True)
    except Exception as e:
        logger.error(f"Error accessing lore content for user {callback.from_user.id}: {e}", exc_info=True)
        await callback.answer("❌ Error al acceder al contenido. Intenta más tarde.", show_alert=True)
