"""
Enhanced shop handlers for users with improved UX.

Flow:
1. Shop list → Shows available products with visual indicators
2. Product detail → Shows full product information
3. Purchase confirmation → Summary with confirm/cancel buttons
4. Result → Success message with unlocks or clear error
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from services.coordinador_central import CoordinadorCentral, AccionUsuario
from services.shop_service import ShopService
from services.condition_checker import ConditionChecker
from database.models import ShopItem, UserPurchase, LorePiece
from keyboards.common import build_shop_keyboard
from utils.localization import get_text

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "shop_access")
async def show_shop(callback: CallbackQuery, session: AsyncSession):
    """Show shop with available products."""
    try:
        logger.info(f"Shop access requested by user {callback.from_user.id}")
        user_id = callback.from_user.id

        shop_service = ShopService(session)
        items = await shop_service.get_available_items(user_id)

        if not items:
            await callback.answer(
                "🛒 La tienda está vacía o no tienes acceso a ningún producto actualmente.",
                show_alert=True
            )
            return

        # Get user's current points
        from database.models import User
        user = await session.get(User, user_id)
        user_points = user.points if user else 0

        text = f"""🛒 **Tienda de Diana**

💰 Tus besitos: **{user_points:.0f}**

📦 **Productos disponibles:** {len(items)}

Selecciona un producto para ver sus detalles."""

        # Build keyboard with product buttons
        builder = InlineKeyboardBuilder()

        for item in items:
            # Build button text with indicators
            button_text = f"{item.name}"

            # Add stock indicator if limited
            if item.stock_limit is not None:
                # Calculate remaining stock
                purchases_stmt = select(func.count(UserPurchase.id)).where(
                    UserPurchase.shop_item_id == item.id
                )
                total_purchases = (await session.execute(purchases_stmt)).scalar() or 0
                remaining = item.stock_limit - total_purchases

                if remaining <= 5:
                    button_text += f" [¡Solo {remaining}!]"
                elif remaining <= 10:
                    button_text += f" [{remaining} disponibles]"

            builder.button(
                text=button_text,
                callback_data=f"view_product:{item.id}"
            )

        # Add inventory and back buttons
        builder.button(text=get_text("backpack.title_alt"), callback_data="view_inventory")
        builder.button(text=get_text("backpack.back_button"), callback_data="narrative_main_menu")
        builder.adjust(1)  # One button per row

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in show_shop: {e}", exc_info=True)
        await callback.answer("❌ Error al cargar la tienda. Intenta más tarde.", show_alert=True)

@router.callback_query(F.data.startswith("view_product:"))
async def view_product_detail(callback: CallbackQuery, session: AsyncSession):
    """Show detailed product information."""
    try:
        item_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id

        # Get product
        item = await session.get(ShopItem, item_id)
        if not item or not item.is_active:
            await callback.answer("❌ Producto no encontrado", show_alert=True)
            return

        # Get user points
        from database.models import User
        user = await session.get(User, user_id)
        user_points = user.points if user else 0

        # Check if user already owns it
        purchase_check = await session.execute(
            select(UserPurchase).where(
                UserPurchase.user_id == user_id,
                UserPurchase.shop_item_id == item_id
            )
        )
        user_purchases_count = len(purchase_check.scalars().all())
        already_owns = user_purchases_count > 0

        # Build detailed description
        text = f"""📦 **{item.name}**

**Descripción:**
{item.description or '_Un producto exclusivo de la tienda_'}

💰 **Precio:** {item.price} besitos
"""

        # Add your current points
        can_afford = user_points >= item.price
        text += f"💎 **Tus besitos:** {user_points:.0f} besitos"
        if not can_afford:
            text += f" _(Necesitas {item.price - user_points:.0f} más)_"
        text += "\n\n"

        # Show what it unlocks
        if item.unlocks_lore_piece_id:
            lore_piece = await session.get(LorePiece, item.unlocks_lore_piece_id)
            if lore_piece:
                text += f"""🔓 **Desbloquea contenido narrativo:**
• {lore_piece.title}
_{lore_piece.description or 'Contenido exclusivo de la historia'}_

"""

        # Stock info
        if item.stock_limit is not None:
            purchases_stmt = select(func.count(UserPurchase.id)).where(
                UserPurchase.shop_item_id == item_id
            )
            total_purchases = (await session.execute(purchases_stmt)).scalar() or 0
            remaining = item.stock_limit - total_purchases

            text += f"📦 **Stock:** {remaining} de {item.stock_limit} disponibles\n"

            if remaining <= 5:
                text += "⚠️ _¡Edición limitada! Quedan pocas unidades_\n"

        # Purchase limit info
        if item.max_purchases_per_user > 0:
            remaining_purchases = item.max_purchases_per_user - user_purchases_count
            if already_owns:
                if remaining_purchases > 0:
                    text += f"\n✅ **Ya lo compraste** ({user_purchases_count}/{item.max_purchases_per_user} veces)\n"
                    text += f"_Puedes comprar {remaining_purchases} {'vez' if remaining_purchases == 1 else 'veces'} más_\n"
                else:
                    text += f"\n✅ **Ya lo compraste** (límite alcanzado: {user_purchases_count}/{item.max_purchases_per_user})\n"

        # Availability info
        if item.available_until:
            from datetime import datetime
            now = datetime.now()
            days_remaining = (item.available_until - now).days

            if days_remaining > 0:
                text += f"\n⏰ **Disponible por tiempo limitado:** {days_remaining} días restantes\n"

        # Build keyboard
        builder = InlineKeyboardBuilder()

        # Add buy button if can purchase
        can_purchase = (
            can_afford and
            (item.max_purchases_per_user == 0 or user_purchases_count < item.max_purchases_per_user)
        )

        if can_purchase:
            builder.button(text="🛒 Comprar", callback_data=f"confirm_purchase:{item_id}")
        elif not can_afford:
            builder.button(text="💰 No tienes suficientes besitos", callback_data="noop")
        elif user_purchases_count >= item.max_purchases_per_user:
            builder.button(text="✅ Ya lo compraste (límite alcanzado)", callback_data="noop")

        builder.button(text="🔙 Volver a la tienda", callback_data="shop_access")
        builder.adjust(1)

        # Send product image if available
        if item.image_file_id:
            try:
                await callback.message.delete()
                await callback.bot.send_photo(
                    chat_id=callback.from_user.id,
                    photo=item.image_file_id,
                    caption=text,
                    reply_markup=builder.as_markup(),
                    parse_mode="Markdown"
                )
            except Exception as img_error:
                logger.warning(f"Could not send product image: {img_error}")
                await callback.message.edit_text(
                    text,
                    reply_markup=builder.as_markup(),
                    parse_mode="Markdown"
                )
        else:
            await callback.message.edit_text(
                text,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )

        await callback.answer()

    except ValueError:
        await callback.answer("❌ ID de producto inválido", show_alert=True)
    except Exception as e:
        logger.error(f"Error viewing product: {e}", exc_info=True)
        await callback.answer("❌ Error al cargar producto", show_alert=True)


@router.callback_query(F.data.startswith("confirm_purchase:"))
async def confirm_purchase(callback: CallbackQuery, session: AsyncSession):
    """Show purchase confirmation dialog."""
    try:
        item_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id

        # Get product
        item = await session.get(ShopItem, item_id)
        if not item:
            await callback.answer("❌ Producto no encontrado", show_alert=True)
            return

        # Get user points
        from database.models import User
        user = await session.get(User, user_id)
        user_points = user.points if user else 0

        # Build confirmation message
        text = f"""🛒 **Confirmación de Compra**

**Producto:** {item.name}
**Precio:** {item.price} besitos

💰 **Tus besitos actuales:** {user_points:.0f}
💎 **Tras la compra:** {user_points - item.price:.0f} besitos
"""

        if item.unlocks_lore_piece_id:
            lore_piece = await session.get(LorePiece, item.unlocks_lore_piece_id)
            if lore_piece:
                text += f"\n🔓 **Se desbloqueará:** {lore_piece.title}\n"

        text += "\n**¿Confirmas la compra?**"

        # Build keyboard
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Sí, comprar", callback_data=f"buy_item:{item_id}")
        builder.button(text="❌ Cancelar", callback_data=f"view_product:{item_id}")
        builder.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except ValueError:
        await callback.answer("❌ ID de producto inválido", show_alert=True)
    except Exception as e:
        logger.error(f"Error in confirm_purchase: {e}", exc_info=True)
        await callback.answer("❌ Error al procesar", show_alert=True)


@router.callback_query(F.data.startswith("buy_item:"))
async def handle_purchase(callback: CallbackQuery, session: AsyncSession):
    """Execute the purchase."""
    try:
        item_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id

        shop_service = ShopService(session)
        result = await shop_service.purchase_item(user_id, item_id)

        if result["success"]:
            # Get item info for success message
            item = await session.get(ShopItem, item_id)

            success_text = f"""✅ **¡Compra Exitosa!**

Has adquirido: **{item.name}**

💰 **Besitos gastados:** {item.price}
"""

            # Check if lore was unlocked
            unlocked_lore = result.get("unlocked_lore")
            if unlocked_lore:
                success_text += f"""
🎉 **¡Contenido Desbloqueado!**

Has desbloqueado la pista narrativa:
📜 **{unlocked_lore['title']}**

_{unlocked_lore.get('description', 'Nuevo contenido disponible')}_

Puedes acceder a este contenido desde el menú narrativo.
"""

            # Check if narrative fragment was unlocked
            unlocked_fragment = result.get("unlocked_fragment")
            if unlocked_fragment:
                success_text += f"""
📖 **¡Fragmento de Historia Desbloqueado!**

Has desbloqueado un nuevo fragmento narrativo.
Usa "📖 Continuar historia" para verlo.
"""

            success_text += "\n🎒 El producto se ha agregado a tu mochila."

            # Build keyboard
            builder = InlineKeyboardBuilder()
            builder.button(text="🛒 Seguir comprando", callback_data="shop_access")
            builder.button(text="🎒 Ver mi mochila", callback_data="view_inventory")
            builder.button(text="📖 Continuar historia", callback_data="return_from_shop")
            builder.adjust(1)

            await callback.message.edit_text(
                success_text,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
            await callback.answer("✅ Compra realizada!", show_alert=False)

        else:
            # Show error
            error_msg = result.get('message', 'Error desconocido')
            await callback.answer(f"❌ {error_msg}", show_alert=True)

            # Return to shop
            await show_shop(callback, session)

    except ValueError:
        await callback.answer("❌ ID de artículo inválido", show_alert=True)
    except Exception as e:
        logger.error(f"Error handling purchase: {e}", exc_info=True)
        await callback.answer("❌ Error al procesar la compra", show_alert=True)


@router.callback_query(F.data == "view_inventory")
async def view_inventory(callback: CallbackQuery, session: AsyncSession):
    """Show user's purchased items (inventory/backpack)."""
    try:
        user_id = callback.from_user.id

        # Get all purchases with shop_item loaded in single query (eliminates N+1)
        purchases_stmt = select(UserPurchase).where(
            UserPurchase.user_id == user_id
        ).options(
            selectinload(UserPurchase.shop_item)
        ).order_by(UserPurchase.purchased_at.desc())

        purchases_result = await session.execute(purchases_stmt)
        purchases = purchases_result.scalars().all()

        if not purchases:
            text = get_text("backpack.title_alt") + "\n\n" + get_text("backpack.empty_message_shop")

            builder = InlineKeyboardBuilder()
            builder.button(text=get_text("backpack.go_to_shop_button"), callback_data="shop_access")
            builder.button(text=get_text("backpack.back_button"), callback_data="narrative_main_menu")
            builder.adjust(1)

            await callback.message.edit_text(
                text,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
            await callback.answer()
            return

        # Build inventory list
        product_plural = get_text("backpack.product") if len(purchases) == 1 else get_text("backpack.products")
        text = get_text("backpack.title_alt") + "\n\n" + get_text("backpack.inventory_summary", count=len(purchases), product_plural=product_plural)

        # Group purchases by item (shop_item already loaded via selectinload)
        from collections import defaultdict
        items_count = defaultdict(int)
        items_info = {}

        for purchase in purchases:
            item = purchase.shop_item  # No DB query - already loaded!
            if item:
                items_count[item.id] += 1
                if item.id not in items_info:
                    items_info[item.id] = item

        # Display items
        for item_id, count in items_count.items():
            item = items_info[item_id]
            count_text = f" x{count}" if count > 1 else ""
            text += f"• {item.name}{count_text}\n"

            if item.unlocks_lore_piece_id:
                text += get_text("backpack.unlocks_lore_info") + "\n"

        text += get_text("backpack.persistent_item_note")

        # Build keyboard
        builder = InlineKeyboardBuilder()
        builder.button(text=get_text("backpack.go_to_shop_button"), callback_data="shop_access")
        builder.button(text=get_text("backpack.back_button"), callback_data="narrative_main_menu")
        builder.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error viewing inventory: {e}", exc_info=True)
        await callback.answer(get_text("backpack.load_error"), show_alert=True)
