import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from services.coordinador_central import CoordinadorCentral, AccionUsuario
from keyboards.common import build_shop_keyboard

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "shop_access")
async def show_shop(callback: CallbackQuery, session: AsyncSession):
    coordinador = CoordinadorCentral(session)
    result = await coordinador.ejecutar_flujo(
        callback.from_user.id, 
        AccionUsuario.ACCEDER_TIENDA
    )
    
    if result["success"]:
        items = result.get("items", [])
        keyboard = build_shop_keyboard(items)
        await callback.message.edit_text("🛒 Tienda - Elige un artículo:", reply_markup=keyboard)
    else:
        await callback.answer(f"❌ {result.get('message', 'Error al acceder a la tienda')}")

@router.callback_query(F.data.startswith("buy_item:"))
async def handle_purchase(callback: CallbackQuery, session: AsyncSession):
    item_id = int(callback.data.split(":")[1])
    coordinador = CoordinadorCentral(session)
    result = await coordinador.ejecutar_flujo(
        callback.from_user.id,
        AccionUsuario.COMPRAR_ITEM,
        item_id=item_id
    )
    
    if result["success"]:
        await callback.answer("✅ Compra exitosa!")
        if result.get("unlocked_lore"):
            await callback.message.answer("🎉 ¡Has desbloqueado nuevo contenido narrativo!")
    else:
        await callback.answer(f"❌ {result['message']}")
