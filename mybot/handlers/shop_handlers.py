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
    try:
        logger.info(f"Shop access requested by user {callback.from_user.id}")
        coordinador = CoordinadorCentral(session)
        result = await coordinador.ejecutar_flujo(
            callback.from_user.id, 
            AccionUsuario.ACCEDER_TIENDA
        )
        
        logger.info(f"Shop access result: {result}")
        
        if result["success"]:
            items = result.get("items", [])
            # Make sure build_shop_keyboard is imported
            from keyboards.common import build_shop_keyboard
            keyboard = build_shop_keyboard(items)
            await callback.message.edit_text("🛒 Tienda - Elige un artículo:", reply_markup=keyboard)
        else:
            await callback.answer(f"❌ {result.get('message', 'Error al acceder a la tienda')}", show_alert=True)
    except Exception as e:
        logger.error(f"Error in show_shop: {e}", exc_info=True)
        await callback.answer("❌ Error al cargar la tienda. Intenta más tarde.", show_alert=True)

@router.callback_query(F.data.startswith("buy_item:"))
async def handle_purchase(callback: CallbackQuery, session: AsyncSession):
    try:
        # Parse the item ID
        item_id = int(callback.data.split(":")[1])
        user_id = callback.from_user.id
        
        coordinador = CoordinadorCentral(session)
        result = await coordinador.ejecutar_flujo(
            user_id,
            AccionUsuario.COMPRAR_ITEM,
            item_id=item_id
        )
        
        if result["success"]:
            # Show success notification
            await callback.answer("✅ Compra exitosa!", show_alert=False)
            # Send a follow-up message if lore was unlocked
            if result.get("unlocked_lore"):
                await callback.message.answer("🎉 ¡Has desbloqueado nuevo contenido narrativo!")
        else:
            # Show error notification
            await callback.answer(f"❌ {result.get('message', 'Error al procesar la compra')}", show_alert=True)
    except ValueError:
        await callback.answer("❌ ID de artículo inválido", show_alert=True)
    except Exception as e:
        logger.error(f"Error handling purchase for user {callback.from_user.id}: {str(e)}")
        await callback.answer("❌ Error interno al procesar la compra", show_alert=True)
