import logging
import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import get_user_role
from utils.menu_manager import menu_manager
from keyboards.subscription_kb import get_free_main_menu_kb, get_vip_explore_kb, get_free_content_menu_kb
from keyboards.packs_kb import get_packs_list_kb, get_pack_detail_kb
from utils.messages import BOT_MESSAGES
from keyboards.common import get_back_kb
from utils.notify_admins import notify_admins
from utils.vip_cta_messages import get_vip_cta
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("subscribe"))
async def show_free_main_menu(message: Message, session: AsyncSession):
    """Display the menu for free users."""
    if await get_user_role(message.bot, message.from_user.id, session=session) != "free":
        return

    await menu_manager.show_menu(
        message,
        BOT_MESSAGES.get("FREE_MENU_TEXT", "Menú gratuito"),
        get_free_main_menu_kb(),
        session,
        "free_main",
        delete_origin_message=True,
    )


@router.callback_query(F.data == "free_main_menu")
async def cb_free_main_menu(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_MENU_TEXT", "Menú gratuito"),
        get_free_main_menu_kb(),
        session,
        "free_main",
    )
    await callback.answer()


@router.callback_query(F.data == "free_gift")
async def cb_free_gift(callback: CallbackQuery, session: AsyncSession):
    message = callback.message
    await message.answer(BOT_MESSAGES["FREE_GIFT_TEXT"])
    await message.answer(BOT_MESSAGES["verify_instagram"])
    await asyncio.sleep(2)
    await message.answer(BOT_MESSAGES["reconnecting"])
    await asyncio.sleep(2)
    await message.answer(BOT_MESSAGES["verified"])
    await asyncio.sleep(1)
    await message.answer(
        BOT_MESSAGES["gift_unlocked"],
        reply_markup=get_back_kb("free_main_menu"),
    )
    await callback.answer()


@router.callback_query(F.data == "free_packs")
async def cb_free_packs(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("PACKS_MENU_TEXT", "Packs"),
        get_packs_list_kb(),
        session,
        "free_packs",
    )
    await callback.answer()


@router.callback_query(F.data == "free_vip_explore")
async def cb_free_vip_explore(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_VIP_EXPLORE_TEXT", "Canal VIP"),
        get_vip_explore_kb(),
        session,
        "free_vip_explore",
    )
    await callback.answer()


@router.callback_query(F.data == "free_custom")
async def cb_free_custom(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_CUSTOM_TEXT", "Contenido personalizado"),
        get_back_kb("free_main_menu"),
        session,
        "free_custom",
    )
    await callback.answer()


@router.callback_query(F.data == "free_game")
async def cb_free_game(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_GAME_TEXT", "Mini juego"),
        get_back_kb("free_main_menu"),
        session,
        "free_game",
    )
    await callback.answer()


@router.callback_query(F.data == "free_follow")
async def cb_free_follow(callback: CallbackQuery, session: AsyncSession):
    await menu_manager.update_menu(
        callback,
        BOT_MESSAGES.get("FREE_FOLLOW_TEXT", "Dónde seguirme"),
        get_back_kb("free_main_menu"),
        session,
        "free_follow",
    )
    await callback.answer()


@router.callback_query(F.data == "vip_explore_interest")
async def cb_vip_explore_interest(callback: CallbackQuery, session: AsyncSession):
    """
    Maneja el interés en VIP con mensaje personalizado por arquetipo.

    Obtiene el arquetipo del usuario (basado en decisiones narrativas) y
    muestra un CTA personalizado que resuena con su estilo.
    """
    from services.narrative_service import NarrativeService
    from utils.vip_cta_messages import get_vip_cta
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    user = callback.from_user
    user_id = user.id

    # Obtener arquetipo del usuario
    narrative_service = NarrativeService(session, callback.bot)
    archetype = await narrative_service.get_user_archetype(user_id)

    # Notificar a admins con arquetipo
    notify_text = (
        f"💎 Interés en VIP\n"
        f"Usuario: {user.first_name} (@{user.username or user.id})\n"
        f"Arquetipo: {archetype}"
    )
    await notify_admins(callback.bot, notify_text)

    # Obtener CTA personalizado por arquetipo
    cta = get_vip_cta("general", archetype=archetype)

    # Crear keyboard con información de contacto
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Contactar para suscripción", url="https://t.me/tu_usuario_admin")
    builder.button(text="↩️ Menú Principal", callback_data="free_main_menu")
    builder.adjust(1)

    await menu_manager.update_menu(
        callback,
        cta["message"],
        builder.as_markup(),
        session,
        "vip_interest_personalized"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pack_"))
async def cb_pack_details(callback: CallbackQuery, session: AsyncSession):
    data = callback.data
    if data.startswith("pack_interest_"):
        pack_id = data.split("_")[-1]
        user = callback.from_user
        notify_text = (
            f"Interés en pack {pack_id} de {user.first_name} "
            f"(@{user.username or user.id})"
        )
        await notify_admins(callback.bot, notify_text)
        await menu_manager.send_temporary_message(
            callback.message,
            BOT_MESSAGES.get("PACK_INTEREST_REPLY"),
            auto_delete_seconds=8,
        )
        await callback.answer()
        return

    # Handle pack detail display
    pack_id = data.split("_")[-1]
    text = BOT_MESSAGES.get(f"PACK_{pack_id}_DETAILS", "Detalles")
    await menu_manager.update_menu(
        callback,
        text,
        get_pack_detail_kb(pack_id),
        session,
        f"pack_{pack_id}",
    )
    await callback.answer()

# ═══════════════════════════════════════════════════════════════════════════════
# NUEVOS HANDLERS - MENÚ MEJORADO PARA USUARIOS FREE
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "free_my_content")
async def cb_free_my_content(callback: CallbackQuery, session: AsyncSession):
    """Mostrar el submenú 'Mi Contenido' que unifica Packs, VIP Explore y Custom."""
    text = (
        "📂 **Mi Contenido Exclusivo**\n\n"
        "Aquí puedes explorar todo lo que tengo para ofrecerte:\n\n"
        "🎀 **Mis Packs:** Colecciones temáticas especiales\n"
        "🔐 **Explorar VIP:** Descubre el mundo premium\n"
        "💌 **Contenido Custom:** Solicita algo personalizado\n\n"
        "¿Qué te gustaría ver?"
    )

    await menu_manager.update_menu(
        callback,
        text,
        get_free_content_menu_kb(),
        session,
        "free_my_content",
    )
    await callback.answer()


@router.callback_query(F.data == "free_shop_preview")
async def cb_free_shop_preview(callback: CallbackQuery, session: AsyncSession):
    """Mostrar preview de la tienda con CTA persuasivo."""
    from services.shop_service import ShopService

    shop_service = ShopService(session)
    all_items = await shop_service.get_all_items()

    # Obtener CTA personalizado con el número de items
    cta = get_vip_cta("shop", total_items=len(all_items))

    # Crear keyboard con botón CTA
    builder = InlineKeyboardBuilder()
    builder.button(text=cta["button_text"], callback_data="vip_explore_interest")
    builder.button(text="↩️ Menú Principal", callback_data="free_main_menu")
    builder.adjust(1)

    await menu_manager.update_menu(
        callback,
        cta["message"],
        builder.as_markup(),
        session,
        "free_shop_preview",
    )
    await callback.answer()


@router.callback_query(F.data == "free_missions_preview")
async def cb_free_missions_preview(callback: CallbackQuery, session: AsyncSession):
    """Mostrar preview de misiones con CTA persuasivo."""
    from services.mission_service import MissionService

    mission_service = MissionService(session)
    all_missions = await mission_service.get_active_missions()

    # Obtener CTA personalizado con el número de misiones
    cta = get_vip_cta("missions", total_missions=len(all_missions))

    # Crear keyboard con botón CTA
    builder = InlineKeyboardBuilder()
    builder.button(text=cta["button_text"], callback_data="vip_explore_interest")
    builder.button(text="↩️ Menú Principal", callback_data="free_main_menu")
    builder.adjust(1)

    await menu_manager.update_menu(
        callback,
        cta["message"],
        builder.as_markup(),
        session,
        "free_missions_preview",
    )
    await callback.answer()


@router.callback_query(F.data == "free_auctions_preview")
async def cb_free_auctions_preview(callback: CallbackQuery, session: AsyncSession):
    """Mostrar preview de subastas con CTA persuasivo."""
    cta = get_vip_cta("auctions")

    # Crear keyboard con botón CTA
    builder = InlineKeyboardBuilder()
    builder.button(text=cta["button_text"], callback_data="vip_explore_interest")
    builder.button(text="↩️ Menú Principal", callback_data="free_main_menu")
    builder.adjust(1)

    await menu_manager.update_menu(
        callback,
        cta["message"],
        builder.as_markup(),
        session,
        "free_auctions_preview",
    )
    await callback.answer()


@router.callback_query(F.data == "free_backpack_preview")
async def cb_free_backpack_preview(callback: CallbackQuery, session: AsyncSession):
    """Mostrar preview de la mochila con CTA persuasivo."""
    cta = get_vip_cta("backpack")

    # Crear keyboard con botón CTA
    builder = InlineKeyboardBuilder()
    builder.button(text=cta["button_text"], callback_data="vip_explore_interest")
    builder.button(text="↩️ Menú Principal", callback_data="free_main_menu")
    builder.adjust(1)

    await menu_manager.update_menu(
        callback,
        cta["message"],
        builder.as_markup(),
        session,
        "free_backpack_preview",
    )
    await callback.answer()


@router.callback_query(F.data == "free_rewards_preview")
async def cb_free_rewards_preview(callback: CallbackQuery, session: AsyncSession):
    """Mostrar preview de recompensas con CTA persuasivo."""
    cta = get_vip_cta("rewards")

    # Crear keyboard con botón CTA
    builder = InlineKeyboardBuilder()
    builder.button(text=cta["button_text"], callback_data="vip_explore_interest")
    builder.button(text="↩️ Menú Principal", callback_data="free_main_menu")
    builder.adjust(1)

    await menu_manager.update_menu(
        callback,
        cta["message"],
        builder.as_markup(),
        session,
        "free_rewards_preview",
    )
    await callback.answer()
