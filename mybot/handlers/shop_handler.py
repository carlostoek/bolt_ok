"""
Shop Handler - Manejo de comandos de tienda para usuarios
Integra con CoordinadorCentral para experiencia consistente.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from services.coordinador_central import CoordinadorCentral, AccionUsuario
from keyboards.shop_kb import (
    get_shop_main_kb,
    get_shop_category_kb,
    get_shop_item_detail_kb,
    get_shop_purchase_confirm_kb,
    get_shop_inventory_kb
)
from utils.message_safety import safe_answer, safe_edit
from utils.user_roles import get_user_role

logger = logging.getLogger(__name__)
router = Router()

class ShopStates(StatesGroup):
    """Estados para navegación de tienda."""
    browsing_category = State()
    viewing_item_details = State()
    confirming_purchase = State()
    viewing_inventory = State()

@router.message(Command("tienda"))
async def shop_command(message: Message, session: AsyncSession):
    """Comando principal para acceder a la tienda."""
    user_id = message.from_user.id
    
    try:
        # Usar CoordinadorCentral para flujo integrado
        coordinador = CoordinadorCentral(session)
        result = await coordinador.ejecutar_flujo(
            AccionUsuario.LISTAR_TIENDA,
            user_id,
            bot=message.bot
        )
        
        if result["success"]:
            await safe_answer(
                message,
                result["message"],
                reply_markup=get_shop_main_kb(result.get("catalog_data", {}))
            )
        else:
            await safe_answer(message, result["message"])
            
    except Exception as e:
        logger.error(f"Error in shop command for user {user_id}: {e}")
        await safe_answer(
            message,
            "❌ **Error Temporal**\n\nNo se pudo cargar la tienda. Intenta nuevamente."
        )

@router.message(F.text == "🛒 Tienda")
async def shop_button_handler(message: Message, session: AsyncSession):
    """Handler para el botón de tienda en el menú principal."""
    await shop_command(message, session)

@router.message(Command("inventario"))
async def inventory_command(message: Message, session: AsyncSession):
    """Comando para ver inventario directamente."""
    user_id = message.from_user.id
    
    try:
        coordinador = CoordinadorCentral(session)
        result = await coordinador.ejecutar_flujo(
            AccionUsuario.VER_INVENTARIO,
            user_id,
            bot=message.bot
        )
        
        await safe_answer(message, result["message"])
            
    except Exception as e:
        logger.error(f"Error in inventory command for user {user_id}: {e}")
        await safe_answer(message, "Error cargando inventario")

@router.message(Command("comprar"))
async def quick_purchase_command(message: Message, session: AsyncSession):
    """Comando rápido para comprar por ID de artículo."""
    user_id = message.from_user.id
    
    # Extraer ID del artículo del comando
    command_parts = message.text.split()
    if len(command_parts) < 2:
        await safe_answer(
            message,
            "❌ **Uso incorrecto**\n\n"
            "Formato: `/comprar <id_articulo>`\n"
            "Ejemplo: `/comprar 5`\n\n"
            "Usa `/tienda` para ver artículos disponibles."
        )
        return
    
    try:
        item_id = int(command_parts[1])
        
        # Usar CoordinadorCentral para compra
        coordinador = CoordinadorCentral(session)
        result = await coordinador.ejecutar_flujo(
            AccionUsuario.COMPRAR_ARTICULO,
            user_id,
            item_id=item_id,
            bot=message.bot
        )
        
        await safe_answer(message, result["message"])
        
    except ValueError:
        await safe_answer(
            message,
            "❌ **ID Inválido**\n\nEl ID del artículo debe ser un número."
        )
    except Exception as e:
        logger.error(f"Error in quick purchase for user {user_id}: {e}")
        await safe_answer(message, "Error procesando compra rápida")

@router.message(Command("shop_admin"))
async def shop_admin_command(message: Message, session: AsyncSession):
    """Comando directo para administración de tienda."""
    from utils.user_roles import is_admin
    
    if not await is_admin(message.from_user.id, session):
        await safe_answer(
            message,
            "❌ **Acceso Denegado**\n\nSolo los administradores pueden gestionar la tienda."
        )
        return
    
    try:
        from services.shop_service import ShopService
        shop_service = ShopService(session)
        stats = await shop_service.get_shop_statistics()
        
        stats_text = f"🛒 **Panel de Administración de Tienda**\n\n"
        stats_text += f"Gestiona artículos, categorías y configuraciones de tu tienda.\n\n"
        stats_text += f"📊 **Resumen rápido**:\n"
        stats_text += f"• {stats.get('total_items', 0)} artículos\n"
        stats_text += f"• {stats.get('total_purchases', 0)} compras\n"
        stats_text += f"• {stats.get('total_revenue', 0)} besitos generados"
        
        from keyboards.admin_shop_kb import get_admin_shop_main_kb
        await safe_answer(
            message,
            stats_text,
            reply_markup=get_admin_shop_main_kb()
        )
        
    except Exception as e:
        logger.error(f"Error in shop admin command: {e}")
        await safe_answer(
            message,
            "❌ **Error Temporal**\n\nNo se pudo cargar el panel de administración."
        )

# Callbacks para navegación de tienda
@router.callback_query(F.data == "menu:shop")
async def shop_menu_callback(callback: CallbackQuery, session: AsyncSession):
    """Callback para acceder a la tienda desde el menú principal."""
    user_id = callback.from_user.id
    
    try:
        coordinador = CoordinadorCentral(session)
        result = await coordinador.ejecutar_flujo(
            AccionUsuario.LISTAR_TIENDA,
            user_id,
            bot=callback.bot
        )
        
        if result["success"]:
            await safe_edit(
                callback.message,
                result["message"],
                reply_markup=get_shop_main_kb(result.get("catalog_data", {}))
            )
        else:
            await callback.answer(result["message"], show_alert=True)
            
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in shop menu callback for user {user_id}: {e}")
        await callback.answer("Error cargando la tienda", show_alert=True)

@router.callback_query(F.data == "menu:shop_inventory")
async def shop_inventory_callback(callback: CallbackQuery, session: AsyncSession):
    """Callback para ver inventario desde el menú principal."""
    user_id = callback.from_user.id
    
    try:
        coordinador = CoordinadorCentral(session)
        result = await coordinador.ejecutar_flujo(
            AccionUsuario.VER_INVENTARIO,
            user_id,
            bot=callback.bot
        )
        
        await safe_edit(callback.message, result["message"])
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in inventory callback for user {user_id}: {e}")
        await callback.answer("Error cargando inventario", show_alert=True)