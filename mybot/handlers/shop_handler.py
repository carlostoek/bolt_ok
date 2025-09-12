# handlers/shop_handler.py
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from services.shop_service import ShopService
from keyboards.shop_kb import get_shop_keyboard

router = Router()

@router.callback_query(F.data == "menu:shop")
async def handle_shop_menu(callback_query: CallbackQuery, session: AsyncSession):
    """Handles the shop menu button."""
    shop_service = ShopService(session)
    items = await shop_service.get_shop_items(callback_query.from_user.id)
    
    await callback_query.message.edit_text(
        "🛍️ **Tienda**\n\n¡Bienvenido a la tienda! Aquí podrás comprar artículos con tus besitos.",
        reply_markup=get_shop_keyboard(items)
    )
    await callback_query.answer()

@router.callback_query(F.data.startswith("shop:page:"))
async def handle_shop_page(callback_query: CallbackQuery, session: AsyncSession):
    """Handles shop pagination."""
    offset = int(callback_query.data.split(":")[-1])
    shop_service = ShopService(session)
    items = await shop_service.get_shop_items(callback_query.from_user.id)
    
    await callback_query.message.edit_text(
        "🛍️ **Tienda**\n\n¡Bienvenido a la tienda! Aquí podrás comprar artículos con tus besitos.",
        reply_markup=get_shop_keyboard(items, offset=offset)
    )
    await callback_query.answer()