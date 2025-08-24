from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from utils.user_roles import is_admin
from utils.admin_state import AdminTariffStates
from keyboards.tarifas_kb import (
    get_duration_kb,
    get_tarifas_kb,
    get_tariff_options_kb,
)
from keyboards.common import get_back_kb
from utils.menu_utils import send_temporary_reply, update_menu
from utils.text_utils import sanitize_text
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "config_tarifas")
async def config_tarifas(callback: CallbackQuery, session: AsyncSession):
    """Show information about the updated VIP system."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    text = (
        "💳 **Sistema VIP Actualizado**\n\n"
        "El sistema de tarifas VIP ha sido actualizado y ahora utiliza "
        "el nuevo sistema de transacciones VIP. Las tarifas antiguas "
        "ya no están disponibles.\n\n"
        "Para gestionar accesos VIP, use el panel de administración de VIP."
    )
    
    # Create a simple keyboard with a back button
    from keyboards.common import get_back_kb
    await update_menu(callback, text, get_back_kb("admin_main_menu"), session, "config_tarifas")
    await callback.answer()


@router.callback_query(F.data.startswith("tariff_"))
async def tariff_options(callback: CallbackQuery, session: AsyncSession):
    """Display information about the updated VIP system."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()

    await callback.answer(
        "ℹ️ Sistema actualizado\n\n"
        "El sistema de tarifas VIP ha sido actualizado. "
        "Use el panel de administración de VIP para gestionar accesos.",
        show_alert=True
    )


@router.callback_query(F.data.startswith("edit_tariff_"))
async def start_edit_tariff(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Inform about the updated VIP system."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()

    await callback.answer(
        "ℹ️ Sistema actualizado\n\n"
        "El sistema de tarifas VIP ha sido actualizado. "
        "Las tarifas antiguas ya no están disponibles.",
        show_alert=True
    )


@router.callback_query(AdminTariffStates.editing_tariff_duration)
async def edit_tariff_duration(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()

    await callback.answer(
        "ℹ️ Sistema actualizado\n\n"
        "El sistema de tarifas VIP ha sido actualizado.",
        show_alert=True
    )


@router.message(AdminTariffStates.editing_tariff_price)
async def edit_tariff_price(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return

    await send_temporary_reply(
        message,
        "ℹ️ Sistema actualizado\n\n"
        "El sistema de tarifas VIP ha sido actualizado."
    )


@router.message(AdminTariffStates.editing_tariff_name)
async def finish_edit_tariff(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return

    await send_temporary_reply(
        message,
        "ℹ️ Sistema actualizado\n\n"
        "El sistema de tarifas VIP ha sido actualizado."
    )



@router.callback_query(F.data == "tarifa_new")
async def start_new_tarifa(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    await callback.answer(
        "ℹ️ Sistema actualizado\n\n"
        "El sistema de tarifas VIP ha sido actualizado. "
        "Use el panel de administración de VIP para gestionar accesos.",
        show_alert=True
    )


@router.message(Command("admin_configure_tariffs"))
async def admin_configure_tariffs(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return
    
    await send_temporary_reply(
        message,
        "ℹ️ Sistema actualizado\n\n"
        "El sistema de tarifas VIP ha sido actualizado. "
        "Use el panel de administración de VIP para gestionar accesos."
    )


@router.callback_query(AdminTariffStates.waiting_for_tariff_duration)
async def tariff_duration_selected(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    await callback.answer(
        "ℹ️ Sistema actualizado\n\n"
        "El sistema de tarifas VIP ha sido actualizado.",
        show_alert=True
    )


@router.message(AdminTariffStates.waiting_for_tariff_price)
async def tariff_price(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return
    
    await send_temporary_reply(
        message,
        "ℹ️ Sistema actualizado\n\n"
        "El sistema de tarifas VIP ha sido actualizado."
    )


@router.message(AdminTariffStates.waiting_for_tariff_name)
async def tariff_name(message: Message, state: FSMContext, session: AsyncSession):
    if not await is_admin(message.from_user.id, session):
        return
    
    await send_temporary_reply(
        message,
        "ℹ️ Sistema actualizado\n\n"
        "El sistema de tarifas VIP ha sido actualizado."
    )


@router.callback_query(F.data.startswith("delete_tariff_"))
async def delete_tariff(callback: CallbackQuery, session: AsyncSession):
    """Inform about the updated VIP system."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    
    await callback.answer(
        "ℹ️ Sistema actualizado\n\n"
        "El sistema de tarifas VIP ha sido actualizado. "
        "Las tarifas antiguas ya no están disponibles.",
        show_alert=True
    )
