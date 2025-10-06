"Enhanced shop handlers for users with improved UX.

Flow:
1. Shop list → Shows available products with visual indicators
2. Product detail → Shows full product information
3. Purchase confirmation → Summary with confirm/cancel buttons
4. Result → Success message with unlocks or clear error
"
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
from services.upsell_service import UpsellService
from database.models import ShopItem, UserPurchase, LorePiece
from keyboards.common import build_shop_keyboard
from keyboards.besitos_kb import get_besitos_packs_list_kb, get_besitos_pack_detail_kb, get_upsell_keyboard
from utils.localization import get_text
from utils.messages import BOT_MESSAGES

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
                get_text("shop.empty_shop"),
                show_alert=True
            )
            return

        # Get user's current points
        from database.models import User
        user = await session.get(User, user_id)
        user_points = user.points if user else 0

        text = f"""⛓️ **{get_text("shop.welcome_title")}**

💰 {get_text("shop.current_besitos", user_points=user_points)}

{get_text("shop.recommendation")}

📦 {get_text("shop.products_available", count=len(items))}

{get_text("shop.select_product")}"""

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
                    button_text += f" [{get_text("shop.stock_remaining_alert", remaining=remaining)}]"
                elif remaining <= 10:
                    button_text += f" [{get_text("shop.stock_remaining", remaining=remaining)}]"

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
        await callback.answer(get_text("shop.load_error"), show_alert=True)

@router.callback_query(F.data.startswith("view_product:"))
async def view_product_detail(callback: CallbackQuery, session: AsyncSession):
    """Show detailed product information."""
    try:
        item_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id

        # Get product
        item = await session.get(ShopItem, item_id)
        if not item or not item.is_active:
            await callback.answer(get_text("shop.product_not_found"), show_alert=True)
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
        text = f"""👜 **{get_text("shop.product_detail_title", name=item.name)}**

{get_text("shop.product_description", description=item.description or get_text("shop.default_product_description"))}

💰 {get_text("shop.price", price=item.price)}
"""

        # Add your current points
        can_afford = user_points >= item.price
        text += f"💎 {get_text("shop.your_besitos", user_points=user_points)}"
        if not can_afford:
            text += f" {get_text("shop.besitos_needed", missing=item.price - user_points)}"
        text += "\n\n"

        # Show what it unlocks
        if item.unlocks_lore_piece_id:
            lore_piece = await session.get(LorePiece, item.unlocks_lore_piece_id)
            if lore_piece:
                text += f"""
🔓 {get_text("shop.unlocks_lore", title=lore_piece.title, description=lore_piece.description or get_text("shop.default_lore_description"))}

"""

        # Stock info
        if item.stock_limit is not None:
            purchases_stmt = select(func.count(UserPurchase.id)).where(
                UserPurchase.shop_item_id == item_id
            )
            total_purchases = (await session.execute(purchases_stmt)).scalar() or 0
            remaining = item.stock_limit - total_purchases

            text += f"📦 {get_text("shop.stock_info", remaining=remaining, stock_limit=item.stock_limit)}\n"

            if remaining <= 5:
                text += f"⚠️ {get_text("shop.limited_edition_warning")}\n"

        # Purchase limit info
        if item.max_purchases_per_user > 0:
            remaining_purchases = item.max_purchases_per_user - user_purchases_count
            if already_owns:
                if remaining_purchases > 0:
                    text += f"\n✅ {get_text("shop.already_owned_can_buy", count=user_purchases_count, limit=item.max_purchases_per_user)}\n"
                    text += f"{get_text("shop.can_buy_more", remaining=remaining_purchases, times=get_text('shop.times_single') if remaining_purchases == 1 else get_text('shop.times_plural'))}\n"
                else:
                    text += f"\n✅ {get_text("shop.already_owned_limit", count=user_purchases_count, limit=item.max_purchases_per_user)}\n"

        # Availability info
        if item.available_until:
            from datetime import datetime
            now = datetime.now()
            days_remaining = (item.available_until - now).days

            if days_remaining > 0:
                text += f"\n⏰ {get_text("shop.time_limited", days=days_remaining)}\n"

        # Build keyboard
        builder = InlineKeyboardBuilder()

        # Add buy button if can purchase
        can_purchase = (
            can_afford and
            (item.max_purchases_per_user == 0 or user_purchases_count < item.max_purchases_per_user)
        )

        if can_purchase:
            builder.button(text=get_text("shop.buy_button"), callback_data=f"confirm_purchase:{item_id}")
        elif not can_afford:
            # CRÍTICO: Momento de conversión - ofrecer compra de besitos
            missing = item.price - user_points
            builder.button(text=get_text("shop.buy_besitos_button"), callback_data=f"besitos_insufficient:{item_id}:{int(missing)}")
        elif user_purchases_count >= item.max_purchases_per_user:
            builder.button(text=get_text("shop.owned_limit_reached_button"), callback_data="noop")

        builder.button(text=get_text("shop.back_to_shop_button"), callback_data="shop_access")
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
        await callback.answer(get_text("shop.invalid_product_id"), show_alert=True)
    except Exception as e:
        logger.error(f"Error viewing product: {e}", exc_info=True)
        await callback.answer(get_text("shop.product_load_error"), show_alert=True)


@router.callback_query(F.data.startswith("confirm_purchase:"))
async def confirm_purchase(callback: CallbackQuery, session: AsyncSession):
    """Show purchase confirmation dialog with emotional feedback."""
    try:
        item_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id

        # Immediate emotional feedback
        await callback.answer(get_text("shop.emotional_feedback_processing"))
        
        # Show visual processing feedback
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        processing_builder = InlineKeyboardBuilder()
        processing_builder.button(text=get_text("shop.preparing_details"), callback_data="noop")
        
        processing_text = f"""✩ **{get_text("shop.diana_emotional_choice")}**
"""
        
        # Update message with processing feedback
        try:
            await callback.message.edit_text(
                processing_text,
                reply_markup=processing_builder.as_markup(),
                parse_mode="Markdown"
            )
        except Exception:
            # If message edit fails, continue with the flow
            pass

        # Get product
        item = await session.get(ShopItem, item_id)
        if not item:
            await callback.answer(get_text("shop.product_not_found"), show_alert=True)
            return

        # Get user points
        from database.models import User
        user = await session.get(User, user_id)
        user_points = user.points if user else 0

        # Build confirmation message
        text = f"""📦 **{get_text("shop.purchase_confirmation_title")}**

**{get_text("shop.product")}:** {item.name}
**{get_text("shop.price", price=item.price)}**

💰 **{get_text("shop.your_current_besitos")}:** {user_points:.0f}
💎 **{get_text("shop.besitos_after_purchase")}:** {user_points - item.price:.0f} besitos
"""

        if item.unlocks_lore_piece_id:
            lore_piece = await session.get(LorePiece, item.unlocks_lore_piece_id)
            if lore_piece:
                text += f"\n🔓 **{get_text("shop.will_unlock")}:** {lore_piece.title}\n"

        text += f"\n**{get_text("shop.confirm_purchase_prompt")}**"

        # Build keyboard
        builder = InlineKeyboardBuilder()
        builder.button(text=get_text("shop.confirm_button"), callback_data=f"buy_item:{item_id}")
        builder.button(text=get_text("shop.cancel_button"), callback_data=f"view_product:{item_id}")
        builder.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer(get_text("shop.ready_to_confirm"))

    except ValueError:
        await callback.answer(get_text("shop.invalid_product_id"), show_alert=True)
    except Exception as e:
        logger.error(f"Error in confirm_purchase: {e}", exc_info=True)
        await callback.answer(get_text("shop.purchase_processing_error"), show_alert=True)


@router.callback_query(F.data.startswith("buy_item:"))
async def handle_purchase(callback: CallbackQuery, session: AsyncSession):
    """Execute the purchase."""
    try:
        item_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id

        shop_service = ShopService(session)
        result = await shop_service.purchase_item(user_id, item_id, callback.bot)

        if result["success"]:
            # Get item info for success message
            item = await session.get(ShopItem, item_id)

            success_text = f"""💕 **{get_text("shop.purchase_success_title")}**

✩ **{get_text("shop.diana_smiles", name=item.name)}**

💰 {get_text("shop.investment_thanks", price=item.price)}
"""

            # Check if lore was unlocked
            unlocked_lore = result.get("unlocked_lore")
            if unlocked_lore:
                success_text += f"""

🎉 **{get_text("shop.lore_unlocked_title")}**

{get_text("shop.diana_reveals_secret", title=unlocked_lore.get("title", get_text("shop.default_secret_title")), description=unlocked_lore.get("description", get_text("shop.default_secret_description")))}

{get_text("shop.access_from_narrative_menu")} 
"""

            # Check if narrative fragment was unlocked
            unlocked_fragment = result.get("unlocked_fragment")
            if unlocked_fragment:
                success_text += f"""

📚 **{get_text("shop.fragment_unlocked_title")}**

{get_text("shop.fragment_unlocked_message")} 
"""

            success_text += f"""

💰 {get_text("shop.collection_grew")} 
"""

            # ========================================
            # MEJORA #2: UPSELL INTELIGENTE POST-COMPRA
            # ========================================

            # Determinar upsell inteligente
            upsell_service = UpsellService(session)
            upsell = await upsell_service.get_smart_upsell(user_id, item)

            # Si hay upsell específico, agregarlo al mensaje
            if upsell["type"] and upsell["message_key"]:
                upsell_message = BOT_MESSAGES.get(upsell["message_key"], "")
                if upsell_message:
                    # Formatear mensaje con datos
                    try:
                        upsell_message = upsell_message.format(**upsell["data"])
                    except KeyError:
                        pass  # Si falta algún dato, usar mensaje sin formatear

                    success_text += f"\n\n─────────────\n\n{upsell_message}"

            # Build keyboard según tipo de upsell
            keyboard = get_upsell_keyboard(
                upsell_type=upsell["keyboard_type"],
                item_data=upsell["keyboard_data"]
            )

            await callback.message.edit_text(
                success_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            await callback.answer(get_text("shop.purchase_complete"), show_alert=False)

        else:
            # CRÍTICO: Detectar error de insufficient_points y ofrecer besitos
            error_code = result.get('error')
            if error_code == 'insufficient_points':
                # Recuperar puntos necesarios
                from database.models import User
                user = await session.get(User, user_id)
                item = await session.get(ShopItem, item_id)
                missing = item.price - (user.points if user else 0)

                # Redirigir a oferta de besitos
                await callback.answer(get_text("shop.insufficient_points_error"), show_alert=False)
                await offer_besitos_packs(callback, session, item_id, int(missing))
                return

            # Otros errores: mostrar mensaje y volver a shop
            error_msg = result.get('message', get_text("shop.unknown_purchase_error"))
            await callback.answer(f"❌ {error_msg}", show_alert=True)

            # Return to shop
            await show_shop(callback, session)

    except ValueError:
        await callback.answer(get_text("shop.item_invalid_id"), show_alert=True)
    except Exception as e:
        logger.error(f"Error handling purchase: {e}", exc_info=True)
        await callback.answer(get_text("shop.purchase_process_error"), show_alert=True)


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


# ============================================================================
# MONETIZATION HANDLERS - Sprint 1: Conversion Focus
# ============================================================================

async def offer_besitos_packs(callback: CallbackQuery, session: AsyncSession, item_id: int, missing: int):
    """
    MOMENTO CRÍTICO DE CONVERSIÓN:
    Usuario quiere comprar pero le faltan besitos.
    Ofrecer paquetes de besitos de manera inteligente.

    Args:
        callback: CallbackQuery del botón de compra
        session: Sesión de BD
        item_id: ID del producto que querían comprar
        missing: Besitos que le faltan
    """
    try:
        # Obtener información del producto para context
        item = await session.get(ShopItem, item_id)
        item_name = item.name if item else get_text("shop.this_product")

        # Determinar pack recomendado según lo que falta
        recommended_pack = 1  # Basic por default
        if missing > 500:
            recommended_pack = 2  # Premium
        if missing > 1000:
            recommended_pack = 3  # Luxury

        # Mensaje de Lucien personalizado
        text = BOT_MESSAGES["besitos_packs_intro"].format(missing=missing)

        # Modificar mensaje para mencionar el producto
        text += f"\n\n🎁 **Recordatorio:** Querías comprar *{item_name}*
"
        text += "Con besitos suficientes, podrás conseguirlo.\n"

        await callback.message.edit_text(
            text,
            reply_markup=get_besitos_packs_list_kb(highlight_pack=recommended_pack),
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error offering besitos packs: {e}", exc_info=True)
        await callback.answer(get_text("shop.besitos_packs.load_error"), show_alert=True)


@router.callback_query(F.data == "besitos_packs_list")
async def show_besitos_packs(callback: CallbackQuery, session: AsyncSession):
    """Muestra lista de paquetes de besitos disponibles"""
    try:
        text = get_text("shop.besitos_packs.intro")

        await callback.message.edit_text(
            text,
            reply_markup=get_besitos_packs_list_kb(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing besitos packs: {e}", exc_info=True)
        await callback.answer(get_text("shop.besitos_packs.load_error"), show_alert=True)


@router.callback_query(F.data.startswith("besitos_insufficient:"))
async def handle_besitos_insufficient(callback: CallbackQuery, session: AsyncSession):
    """
    Handler para cuando usuario hace click en "Comprar besitos" desde producto
    Callback data: besitos_insufficient:{item_id}:{missing}
    """
    try:
        parts = callback.data.split(":")
        item_id = int(parts[1])
        missing = int(parts[2])

        await callback.answer(get_text("shop.besitos_packs.loading_options"))
        await offer_besitos_packs(callback, session, item_id, missing)

    except Exception as e:
        logger.error(f"Error handling besitos insufficient: {e}", exc_info=True)
        await callback.answer(get_text("shop.besitos_packs.insufficient_redirect_error"), show_alert=True)


@router.callback_query(F.data.startswith("besitos_pack_"))
async def show_besitos_pack_details(callback: CallbackQuery, session: AsyncSession):
    """Muestra detalles de un pack específico"""
    try:
        pack_id = int(callback.data.split("_")[-1])

        # Get pack details from messages
        text = BOT_MESSAGES.get(f"besitos_pack_{pack_id}_details", get_text("shop.besitos_packs.pack_not_available"))

        await callback.message.edit_text(
            text,
            reply_markup=get_besitos_pack_detail_kb(pack_id),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing pack details: {e}", exc_info=True)
        await callback.answer(get_text("shop.besitos_packs.pack_load_error"), show_alert=True)


@router.callback_query(F.data.startswith("besitos_interest_"))
async def handle_besitos_interest(callback: CallbackQuery, session: AsyncSession):
    """
    Usuario hace click en "Me interesa" en un pack de besitos
    Notifica a admin y confirma al usuario

    Callback data: besitos_interest_{pack_id}
    """
    try:
        pack_id = int(callback.data.split("_")[-1])
        user = callback.from_user

        # Pack info
        packs_info = {
            1: {"name": "Pack Básico", "price": 50, "besitos": 500},
            2: {"name": "Pack Premium", "price": 90, "besitos": 1100},
            3: {"name": "Pack Luxury", "price": 200, "besitos": 3000},
        }

        pack = packs_info.get(pack_id, {"name": "Pack", "price": 0, "besitos": 0})

        # Notificar a admins con contexto
        from utils.notify_admins import notify_admins
        from utils.config import ADMIN_IDS
        from database.models import User as UserModel

        # Get user data from DB for more context
        db_user = await session.get(UserModel, user.id)
        current_points = db_user.points if db_user else 0

        admin_msg = (
            f'{get_text("shop.besitos_packs.interest_admin_notification_title")}\n\n'
            f'{get_text("shop.besitos_packs.interest_admin_notification_body", first_name=user.first_name, username=user.username or user.id, user_id=user.id, pack_name=pack["name"], price=pack["price"], besitos=pack["besitos"], current_points=current_points)}'
        )

        await notify_admins(callback.bot, admin_msg)

        # Mensaje temporal al usuario
        from utils.menu_manager import menu_manager
        await menu_manager.send_temporary_message(
            callback.message,
            BOT_MESSAGES["besitos_interest_reply"],
            auto_delete_seconds=10
        )

        await callback.answer(get_text("shop.besitos_packs.interest_request_sent"), show_alert=False)

    except Exception as e:
        logger.error(f"Error handling besitos interest: {e}", exc_info=True)
        await callback.answer(get_text("shop.besitos_packs.interest_request_error"), show_alert=True)


@router.callback_query(F.data == "besitos_packs_bonus")
async def show_besitos_packs_bonus(callback: CallbackQuery, session: AsyncSession):
    """
    Muestra packs de besitos con bonus especial (30% extra)
    Se activa cuando usuario ha comprado mucho en un día
    """
    try:
        text = BOT_MESSAGES["besitos_packs_bonus_intro"]

        # Keyboard con bonus destacado
        builder = InlineKeyboardBuilder()
        builder.button(text=get_text("shop.besitos_packs.bonus_pack_button", base=500, bonus=150, total=650, price=50), callback_data="besitos_pack_1")
        builder.button(text=get_text("shop.besitos_packs.bonus_pack_button", base=1000, bonus=300, total=1300, price=90), callback_data="besitos_pack_2")
        builder.button(text=get_text("shop.besitos_packs.bonus_pack_button", base=2500, bonus=750, total=3250, price=200), callback_data="besitos_pack_3")
        builder.button(text=get_text("shop.besitos_packs.back_button"), callback_data="shop_access")
        builder.adjust(1)

        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing bonus packs: {e}", exc_info=True)
        await callback.answer(get_text("shop.besitos_packs.load_error"), show_alert=True)


# ============================================================================
# UPSELL HANDLERS - Post-Purchase Intelligence
# ============================================================================

@router.callback_query(F.data.startswith("session_interest_"))
async def handle_session_interest(callback: CallbackQuery, session: AsyncSession):
    """
    Usuario hace click en "Quiero mi sesión con Diana"
    Notifica a admin y confirma al usuario

    Callback data: session_interest_{session_type}
    session_type: "standard", "vip_special", "loyalty_discount", "emotional_narrative"
    """
    try:
        session_type = callback.data.split("_", 2)[2]  # Después de "session_interest_"
        user = callback.from_user

        # Get user data from DB
        from database.models import User as UserModel
        db_user = await session.get(UserModel, user.id)

        # Session types
        session_types_info = {
            "standard": {"name": "Sesión Estándar", "price": 500},
            "vip_special": {"name": "Sesión VIP Especial", "price": 500},
            "loyalty_discount": {"name": "Sesión con Descuento Lealtad", "price": 400},
            "emotional_narrative": {"name": "Sesión Post-Narrativa", "price": 500},
        }

        session_info = session_types_info.get(session_type, {"name": "Sesión Individual", "price": 500})

        # Determinar trigger reason
        trigger_reason = "post_purchase_upsell"
        if session_type == "emotional_narrative":
            trigger_reason = "emotional_fragment"
        elif session_type == "loyalty_discount":
            trigger_reason = "loyalty_reward"

        # Notificar a admins
        from utils.notify_admins import notify_admins

        vip_since_str = db_user.vip_since.strftime('%d/%m/%Y') if db_user and db_user.vip_since else 'N/A'
        current_points = db_user.points if db_user else 0

        admin_msg = (
            f'{get_text("shop.upsell.session_interest_admin_title")}\n\n'
            f'{get_text("shop.upsell.session_interest_admin_body", first_name=user.first_name, username=user.username or user.id, user_id=user.id, session_name=session_info["name"], price=session_info["price"], vip_since=vip_since_str, current_points=current_points, trigger_reason=trigger_reason)}'
        )

        await notify_admins(callback.bot, admin_msg)

        # Mensaje al usuario
        await callback.message.edit_text(
            BOT_MESSAGES["session_interest_reply"],
            parse_mode="Markdown",
            reply_markup=InlineKeyboardBuilder()
                .button(text=get_text("shop.upsell.back_to_menu_button"), callback_data="narrative_main_menu")
                .as_markup()
        )

        await callback.answer(get_text("shop.upsell.session_request_sent_to_diana"), show_alert=False)

        # Actualizar timestamp de última oferta de sesión
        if db_user:
            from datetime import datetime
            db_user.last_session_offer_at = datetime.utcnow()
            await session.commit()

    except Exception as e:
        logger.error(f"Error handling session interest: {e}", exc_info=True)
        await callback.answer(get_text("shop.upsell.session_request_error"), show_alert=True)


@router.callback_query(F.data == "vip_interest_special")
async def handle_vip_interest_special(callback: CallbackQuery, session: AsyncSession):
    """
    Usuario FREE hace click en "Activar VIP gratis" desde upsell
    Notifica a admin con contexto especial de "acabó de comprar"
    """
    try:
        user = callback.from_user

        # Get user data
        from database.models import User as UserModel
        from datetime import datetime
        db_user = await session.get(UserModel, user.id)

        days_active = (datetime.utcnow() - db_user.created_at).days if db_user else 0
        current_points = db_user.points if db_user else 0

        # Notificar admin
        from utils.notify_admins import notify_admins

        admin_msg = (
            f'{get_text("shop.upsell.vip_interest_admin_title")}\n\n'
            f'{get_text("shop.upsell.vip_interest_admin_body", first_name=user.first_name, username=user.username or user.id, user_id=user.id, days_active=days_active, current_points=current_points)}'
        )

        await notify_admins(callback.bot, admin_msg)

        # Mensaje al usuario
        await callback.message.edit_text(
            BOT_MESSAGES["vip_interest_standard"],
            parse_mode="Markdown",
            reply_markup=InlineKeyboardBuilder()
                .button(text=get_text("shop.upsell.back_to_menu_button"), callback_data="narrative_main_menu")
                .as_markup()
        )

        await callback.answer(get_text("shop.upsell.vip_request_sent"), show_alert=False)

    except Exception as e:
        logger.error(f"Error handling VIP interest special: {e}", exc_info=True)
        await callback.answer(get_text("shop.upsell.vip_request_error"), show_alert=True)


@router.callback_query(F.data == "continue_narrative_after_purchase")
async def continue_narrative_after_purchase(callback: CallbackQuery, session: AsyncSession):
    """
    Usuario elige continuar la narrativa después de comprar
    Procesa cualquier decisión pendiente y muestra siguiente fragmento
    """
    try:
        await callback.answer(get_text("shop.upsell.continue_narrative_button"))

        # Redirigir al handler de narrativa
        # Este handler ya existe y maneja el shop_redirect_fragment_key
        from handlers.narrative_handler import start_narrative_command

        # Simular mensaje para el handler
        await start_narrative_command(callback.message, session)

    except Exception as e:
        logger.error(f"Error continuing narrative after purchase: {e}", exc_info=True)
        await callback.answer(get_text("shop.upsell.continue_narrative_error"), show_alert=True)