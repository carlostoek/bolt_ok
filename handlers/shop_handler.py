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
            user_id,
            AccionUsuario.LISTAR_TIENDA,
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

@router.callback_query(F.data == "shop_main")
async def shop_main_callback(callback: CallbackQuery, session: AsyncSession):
    """Callback para volver al menú principal de tienda."""
    user_id = callback.from_user.id
    
    try:
        coordinador = CoordinadorCentral(session)
        result = await coordinador.ejecutar_flujo(
            user_id,
            AccionUsuario.LISTAR_TIENDA,
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
        logger.error(f"Error in shop main callback for user {user_id}: {e}")
        await callback.answer("Error cargando la tienda", show_alert=True)

@router.callback_query(F.data.startswith("shop_category:"))
async def shop_category_callback(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Callback para navegar por categorías de tienda."""
    user_id = callback.from_user.id
    category = callback.data.split(":", 1)[1]
    
    try:
        coordinador = CoordinadorCentral(session)
        result = await coordinador.ejecutar_flujo(
            user_id,
            AccionUsuario.LISTAR_TIENDA,
            category=category,
            bot=callback.bot
        )
        
        if result["success"]:
            catalog_data = result.get("catalog_data", {})
            category_items = catalog_data.get("items_by_category", {}).get(category, [])
            
            if category_items:
                category_text = f"🛒 **Categoría: {category.title()}**\n\n"
                category_text += f"Artículos disponibles en esta categoría:"
                
                await safe_edit(
                    callback.message,
                    category_text,
                    reply_markup=get_shop_category_kb(category, category_items)
                )
                await state.set_state(ShopStates.browsing_category)
                await state.update_data(current_category=category)
            else:
                await callback.answer("No hay artículos en esta categoría", show_alert=True)
        else:
            await callback.answer(result["message"], show_alert=True)
            
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in shop category callback for user {user_id}: {e}")
        await callback.answer("Error cargando categoría", show_alert=True)

@router.callback_query(F.data.startswith("shop_item:"))
async def shop_item_details_callback(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Callback para ver detalles de un artículo específico."""
    user_id = callback.from_user.id
    item_id = int(callback.data.split(":", 1)[1])
    
    try:
        from services.shop_service import ShopService
        shop_service = ShopService(session)
        
        # Obtener detalles del artículo
        item = await shop_service.get_item_by_id(item_id)
        if not item:
            await callback.answer("Artículo no encontrado", show_alert=True)
            return
        
        # Verificar elegibilidad de compra
        can_purchase, error_msg = await shop_service.can_purchase_item(user_id, item_id)
        
        # Calcular precio final con descuentos
        final_price = await shop_service._calculate_final_price(user_id, item)
        discount_applied = final_price < item.price
        
        # Crear mensaje de detalles
        details_text = f"🛒 **{item.name}**\n\n"
        
        if item.description:
            details_text += f"📝 **Descripción**: {item.description}\n\n"
        
        details_text += f"💰 **Precio**: {item.price} besitos"
        if discount_applied:
            details_text += f" ~~{item.price}~~ **{final_price} besitos** (¡Descuento aplicado!)"
        details_text += "\n"
        
        if item.is_vip_exclusive:
            details_text += "💎 **Exclusivo VIP**\n"
        
        if item.required_level > 1:
            details_text += f"📊 **Nivel requerido**: {item.required_level}\n"
        
        if item.unlocks_lore_piece_code:
            details_text += "🗝️ **Desbloquea pista narrativa**\n"
        
        if item.stock_quantity > 0:
            details_text += f"📦 **Stock disponible**: {item.stock_quantity}\n"
        
        if not can_purchase:
            details_text += f"\n❌ **No disponible**: {error_msg}"
        
        await safe_edit(
            callback.message,
            details_text,
            reply_markup=get_shop_item_detail_kb(item_id, can_purchase, final_price)
        )
        
        await state.set_state(ShopStates.viewing_item_details)
        await state.update_data(current_item_id=item_id, final_price=final_price)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing item details for user {user_id}, item {item_id}: {e}")
        await callback.answer("Error cargando detalles del artículo", show_alert=True)

@router.callback_query(F.data.startswith("shop_buy:"))
async def shop_purchase_callback(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Callback para confirmar compra de artículo."""
    user_id = callback.from_user.id
    item_id = int(callback.data.split(":", 1)[1])
    
    try:
        # Usar CoordinadorCentral para flujo de compra integrado
        coordinador = CoordinadorCentral(session)
        result = await coordinador.ejecutar_flujo(
            user_id,
            AccionUsuario.COMPRAR_ARTICULO,
            item_id=item_id,
            bot=callback.bot
        )
        
        if result["success"]:
            # Compra exitosa
            await safe_edit(
                callback.message,
                result["message"],
                reply_markup=get_shop_main_kb({})  # Volver al menú principal
            )
            
            # Limpiar estado
            await state.clear()
            
            # Notificar efectos secundarios si los hay
            side_effects = result.get("side_effects", {})
            if side_effects.get("achievements_unlocked") or side_effects.get("level_up"):
                await callback.bot.send_message(
                    user_id,
                    "🎉 **¡Efectos especiales de tu compra!**\n"
                    "Revisa tus logros y nivel para ver las novedades."
                )
        else:
            # Error en compra
            await callback.answer(result["message"], show_alert=True)
            
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error processing purchase for user {user_id}, item {item_id}: {e}")
        await callback.answer("Error procesando la compra", show_alert=True)

@router.callback_query(F.data == "shop_inventory")
async def shop_inventory_callback(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Callback para ver inventario del usuario."""
    user_id = callback.from_user.id
    
    try:
        from services.shop_service import ShopService
        shop_service = ShopService(session)
        
        # Obtener inventario
        inventory = await shop_service.get_user_inventory(user_id)
        
        if not inventory:
            inventory_text = "📦 **Tu Inventario**\n\n" \
                           "Tu inventario está vacío.\n" \
                           "¡Compra algunos artículos para empezar a coleccionar!"
        else:
            inventory_text = f"📦 **Tu Inventario** ({len(inventory)} artículos)\n\n"
            
            # Organizar por categoría
            by_category = {}
            for item_data in inventory:
                category = item_data["category"] or "general"
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(item_data)
            
            for category, items in by_category.items():
                inventory_text += f"**{category.title()}**:\n"
                for item_data in items:
                    quantity_text = f" x{item_data['quantity']}" if item_data['quantity'] > 1 else ""
                    used_text = " (usado)" if item_data['is_used'] else ""
                    lore_text = " 🗝️" if item_data['unlocks_lore'] else ""
                    
                    inventory_text += f"• {item_data['name']}{quantity_text}{used_text}{lore_text}\n"
                inventory_text += "\n"
        
        await safe_edit(
            callback.message,
            inventory_text,
            reply_markup=get_shop_inventory_kb(inventory)
        )
        
        await state.set_state(ShopStates.viewing_inventory)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing inventory for user {user_id}: {e}")
        await callback.answer("Error cargando inventario", show_alert=True)

@router.callback_query(F.data.startswith("use_item:"))
async def use_inventory_item_callback(callback: CallbackQuery, session: AsyncSession):
    """Callback para usar un artículo del inventario."""
    user_id = callback.from_user.id
    item_id = int(callback.data.split(":", 1)[1])
    
    try:
        from services.shop_service import ShopService
        shop_service = ShopService(session)
        
        # Usar el artículo
        success, message = await shop_service.use_inventory_item(user_id, item_id)
        
        if success:
            await callback.answer(message, show_alert=True)
            # Actualizar vista de inventario
            await shop_inventory_callback(callback, session, None)
        else:
            await callback.answer(message, show_alert=True)
            
    except Exception as e:
        logger.error(f"Error using inventory item for user {user_id}, item {item_id}: {e}")
        await callback.answer("Error usando el artículo", show_alert=True)

@router.callback_query(F.data == "shop_back")
async def shop_back_callback(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Callback para navegación hacia atrás en la tienda."""
    user_id = callback.from_user.id
    
    try:
        # Obtener estado actual
        current_state = await state.get_state()
        
        if current_state == ShopStates.viewing_item_details:
            # Volver a la categoría
            data = await state.get_data()
            category = data.get("current_category", "general")
            await shop_category_callback(
                type("MockCallback", (), {
                    "data": f"shop_category:{category}",
                    "from_user": callback.from_user,
                    "message": callback.message,
                    "bot": callback.bot,
                    "answer": callback.answer
                })(),
                session,
                state
            )
        elif current_state == ShopStates.browsing_category:
            # Volver al menú principal
            await shop_main_callback(callback, session)
            await state.clear()
        else:
            # Por defecto, volver al menú principal
            await shop_main_callback(callback, session)
            await state.clear()
            
    except Exception as e:
        logger.error(f"Error in shop back navigation for user {user_id}: {e}")
        await callback.answer("Error en navegación", show_alert=True)

# === COMANDOS ADICIONALES ===

@router.message(Command("inventario"))
async def inventory_command(message: Message, session: AsyncSession):
    """Comando para ver inventario directamente."""
    user_id = message.from_user.id
    
    try:
        from services.shop_service import ShopService
        shop_service = ShopService(session)
        
        inventory = await shop_service.get_user_inventory(user_id)
        
        if not inventory:
            await safe_answer(
                message,
                "📦 **Tu Inventario**\n\n"
                "Tu inventario está vacío. Usa `/tienda` para comprar artículos."
            )
        else:
            inventory_text = f"📦 **Tu Inventario** ({len(inventory)} artículos)\n\n"
            
            for item_data in inventory[:10]:  # Mostrar primeros 10
                quantity_text = f" x{item_data['quantity']}" if item_data['quantity'] > 1 else ""
                lore_text = " 🗝️" if item_data['unlocks_lore'] else ""
                inventory_text += f"• {item_data['name']}{quantity_text}{lore_text}\n"
            
            if len(inventory) > 10:
                inventory_text += f"\n... y {len(inventory) - 10} artículos más"
            
            inventory_text += "\n\nUsa `/tienda` para gestionar tu inventario completo."
            
            await safe_answer(message, inventory_text)
            
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
            user_id,
            AccionUsuario.COMPRAR_ARTICULO,
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