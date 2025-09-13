"""
Shop Admin Handler - Gestión administrativa de la tienda
Permite a los admins crear, editar y gestionar artículos de tienda.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from utils.user_roles import is_admin
from utils.message_safety import safe_answer, safe_edit
from services.shop_service import ShopService
from keyboards.admin_shop_kb import (
    get_admin_shop_main_kb,
    get_admin_shop_items_kb,
    get_admin_shop_categories_kb,
    get_admin_shop_item_actions_kb,
    get_admin_shop_create_item_kb
)
from utils.text_utils import sanitize_text

logger = logging.getLogger(__name__)
router = Router()

class AdminShopStates(StatesGroup):
    """Estados para administración de tienda."""
    creating_item_name = State()
    creating_item_description = State()
    creating_item_price = State()
    creating_item_category = State()
    creating_item_settings = State()
    confirming_item_creation = State()

@router.message(Command("shop_admin"))
async def shop_admin_command(message: Message, session: AsyncSession):
    """Comando directo para administración de tienda."""
    if not await is_admin(message.from_user.id, session):
        await safe_answer(
            message,
            "❌ **Acceso Denegado**\n\nSolo los administradores pueden gestionar la tienda."
        )
        return
    
    try:
        shop_service = ShopService(session)
        stats = await shop_service.get_shop_statistics()
        
        stats_text = f"🛒 **Panel de Administración de Tienda**\n\n"
        stats_text += f"Gestiona artículos, categorías y configuraciones de tu tienda.\n\n"
        stats_text += f"📊 **Resumen rápido**:\n"
        stats_text += f"• {stats.get('total_items', 0)} artículos\n"
        stats_text += f"• {stats.get('total_purchases', 0)} compras\n"
        stats_text += f"• {stats.get('total_revenue', 0)} besitos generados"
        
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

@router.callback_query(F.data == "admin_shop_main")
async def admin_shop_main(callback: CallbackQuery, session: AsyncSession):
    """Menú principal de administración de tienda."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        shop_service = ShopService(session)
        stats = await shop_service.get_shop_statistics()
        
        stats_text = f"🛒 **Administración de Tienda**\n\n"
        stats_text += f"📊 **Estadísticas**:\n"
        stats_text += f"• Artículos activos: {stats.get('total_items', 0)}\n"
        stats_text += f"• Compras totales: {stats.get('total_purchases', 0)}\n"
        stats_text += f"• Ingresos: {stats.get('total_revenue', 0)} besitos\n"
        
        if stats.get('most_popular_item') != "N/A":
            stats_text += f"• Más popular: {stats['most_popular_item']} ({stats['most_popular_purchases']} compras)\n"
        
        await safe_edit(
            callback.message,
            stats_text,
            reply_markup=get_admin_shop_main_kb()
        )
        
    except Exception as e:
        logger.error(f"Error showing admin shop main: {e}")
        await callback.answer("Error cargando panel de tienda", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data == "admin_shop_create_item")
async def admin_shop_create_item(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Iniciar creación de nuevo artículo."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await callback.message.edit_text(
        "➕ **Crear Nuevo Artículo**\n\n"
        "Ingresa el nombre del artículo:",
        reply_markup=get_admin_shop_create_item_kb("cancel")
    )
    
    await state.set_state(AdminShopStates.creating_item_name)
    await callback.answer()

@router.message(AdminShopStates.creating_item_name)
async def process_item_name(message: Message, state: FSMContext, session: AsyncSession):
    """Procesar nombre del artículo."""
    if not await is_admin(message.from_user.id, session):
        return
    
    name = sanitize_text(message.text.strip())
    if len(name) < 3:
        await safe_answer(
            message,
            "❌ El nombre debe tener al menos 3 caracteres."
        )
        return
    
    await state.update_data(item_name=name)
    await safe_answer(
        message,
        f"✅ **Nombre**: {name}\n\n"
        "Ahora ingresa la descripción del artículo:",
        reply_markup=get_admin_shop_create_item_kb("cancel")
    )
    await state.set_state(AdminShopStates.creating_item_description)

@router.message(AdminShopStates.creating_item_description)
async def process_item_description(message: Message, state: FSMContext, session: AsyncSession):
    """Procesar descripción del artículo."""
    if not await is_admin(message.from_user.id, session):
        return
    
    description = sanitize_text(message.text.strip())
    await state.update_data(item_description=description)
    
    await safe_answer(
        message,
        f"✅ **Descripción guardada**\n\n"
        "Ingresa el precio en besitos (solo números):",
        reply_markup=get_admin_shop_create_item_kb("cancel")
    )
    await state.set_state(AdminShopStates.creating_item_price)

@router.message(AdminShopStates.creating_item_price)
async def process_item_price(message: Message, state: FSMContext, session: AsyncSession):
    """Procesar precio del artículo."""
    if not await is_admin(message.from_user.id, session):
        return
    
    try:
        price = int(message.text.strip())
        if price < 1:
            raise ValueError("Price must be positive")
    except ValueError:
        await safe_answer(
            message,
            "❌ Ingresa un precio válido (número mayor a 0)."
        )
        return
    
    await state.update_data(item_price=price)
    
    data = await state.get_data()
    confirmation_text = f"📋 **Resumen del Artículo**\n\n"
    confirmation_text += f"📝 **Nombre**: {data['item_name']}\n"
    confirmation_text += f"📄 **Descripción**: {data['item_description']}\n"
    confirmation_text += f"💰 **Precio**: {price} besitos\n\n"
    confirmation_text += "¿Confirmas la creación de este artículo?"
    
    await safe_answer(
        message,
        confirmation_text,
        reply_markup=get_admin_shop_create_item_kb("confirm")
    )
    await state.set_state(AdminShopStates.confirming_item_creation)

@router.callback_query(AdminShopStates.confirming_item_creation, F.data == "confirm_create_item")
async def confirm_create_item(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Confirmar y crear el artículo."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        data = await state.get_data()
        shop_service = ShopService(session)
        
        # Crear el artículo
        item = await shop_service.create_item(
            name=data["item_name"],
            description=data["item_description"],
            price=data["item_price"],
            category="general"  # Categoría por defecto
        )
        
        success_text = f"✅ **Artículo Creado**\n\n"
        success_text += f"🆔 **ID**: {item.id}\n"
        success_text += f"📝 **Nombre**: {item.name}\n"
        success_text += f"💰 **Precio**: {item.price} besitos\n\n"
        success_text += "El artículo ya está disponible en la tienda."
        
        await callback.message.edit_text(
            success_text,
            reply_markup=get_admin_shop_main_kb()
        )
        
        logger.info(f"Admin {callback.from_user.id} created shop item: {item.name}")
        
    except Exception as e:
        logger.error(f"Error creating shop item: {e}")
        await callback.message.edit_text(
            f"❌ **Error al crear artículo**: {str(e)}",
            reply_markup=get_admin_shop_main_kb()
        )
    
    await state.clear()
    await callback.answer()

@router.callback_query(F.data.startswith("cancel_"))
async def cancel_shop_action(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Cancelar acción administrativa."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    await state.clear()
    await callback.message.edit_text(
        "❌ **Acción Cancelada**\n\n"
        "La operación ha sido cancelada.",
        reply_markup=get_admin_shop_main_kb()
    )
    await callback.answer()