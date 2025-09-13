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
from utils.menu_manager import menu_manager
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
    
    editing_item_field = State()
    managing_item_stock = State()
    
    creating_category_name = State()
    creating_category_description = State()

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
        
        await menu_manager.update_menu(
            callback,
            stats_text,
            get_admin_shop_main_kb(),
            session,
            "admin_shop_main"
        )
        
    except Exception as e:
        logger.error(f"Error showing admin shop main: {e}")
        await callback.answer("Error cargando panel de tienda", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data == "admin_shop_create_item")
async def admin_shop_create_item(callback: CallbackQuery, state: FSMContext):
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
async def process_item_name(message: Message, state: FSMContext):
    """Procesar nombre del artículo."""
    if not await is_admin(message.from_user.id, session):
        return
    
    name = sanitize_text(message.text.strip())
    if len(name) < 3:
        await menu_manager.send_temporary_message(
            message,
            "❌ El nombre debe tener al menos 3 caracteres.",
            auto_delete_seconds=3
        )
        return
    
    await state.update_data(item_name=name)
    await message.answer(
        f"✅ **Nombre**: {name}\n\n"
        "Ahora ingresa la descripción del artículo:",
        reply_markup=get_admin_shop_create_item_kb("cancel")
    )
    await state.set_state(AdminShopStates.creating_item_description)

@router.message(AdminShopStates.creating_item_description)
async def process_item_description(message: Message, state: FSMContext):
    """Procesar descripción del artículo."""
    if not await is_admin(message.from_user.id, session):
        return
    
    description = sanitize_text(message.text.strip())
    await state.update_data(item_description=description)
    
    await message.answer(
        f"✅ **Descripción guardada**\n\n"
        "Ingresa el precio en besitos (solo números):",
        reply_markup=get_admin_shop_create_item_kb("cancel")
    )
    await state.set_state(AdminShopStates.creating_item_price)

@router.message(AdminShopStates.creating_item_price)
async def process_item_price(message: Message, state: FSMContext):
    """Procesar precio del artículo."""
    if not await is_admin(message.from_user.id, session):
        return
    
    try:
        price = int(message.text.strip())
        if price < 1:
            raise ValueError("Price must be positive")
    except ValueError:
        await menu_manager.send_temporary_message(
            message,
            "❌ Ingresa un precio válido (número mayor a 0).",
            auto_delete_seconds=3
        )
        return
    
    await state.update_data(item_price=price)
    
    data = await state.get_data()
    confirmation_text = f"📋 **Resumen del Artículo**\n\n"
    confirmation_text += f"📝 **Nombre**: {data['item_name']}\n"
    confirmation_text += f"📄 **Descripción**: {data['item_description']}\n"
    confirmation_text += f"💰 **Precio**: {price} besitos\n\n"
    confirmation_text += "¿Confirmas la creación de este artículo?"
    
    await message.answer(
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

@router.callback_query(F.data == "admin_shop_list_items")
async def admin_shop_list_items(callback: CallbackQuery, session: AsyncSession):
    """Listar todos los artículos para administración."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        from database.shop_models import ShopItem
        
        # Obtener todos los artículos
        stmt = select(ShopItem).order_by(ShopItem.category, ShopItem.name)
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        
        if not items:
            items_text = "📦 **Gestión de Artículos**\n\n" \
                        "No hay artículos en la tienda.\n" \
                        "Crea el primer artículo para empezar."
        else:
            items_text = f"📦 **Gestión de Artículos** ({len(items)} total)\n\n"
            
            # Agrupar por categoría
            by_category = {}
            for item in items:
                category = item.category or "general"
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(item)
            
            for category, category_items in by_category.items():
                items_text += f"**{category.title()}**:\n"
                for item in category_items[:5]:  # Mostrar primeros 5 por categoría
                    status = "✅" if item.is_active else "❌"
                    vip_badge = "💎" if item.is_vip_exclusive else ""
                    items_text += f"{status} {vip_badge}{item.name} ({item.price}💋)\n"
                
                if len(category_items) > 5:
                    items_text += f"... y {len(category_items) - 5} más\n"
                items_text += "\n"
        
        await callback.message.edit_text(
            items_text,
            reply_markup=get_admin_shop_items_kb(items[:10])  # Primeros 10 para botones
        )
        
    except Exception as e:
        logger.error(f"Error listing shop items: {e}")
        await callback.answer("Error cargando artículos", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data.startswith("admin_shop_item:"))
async def admin_shop_item_actions(callback: CallbackQuery, session: AsyncSession):
    """Acciones administrativas para artículo específico."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    item_id = int(callback.data.split(":", 1)[1])
    
    try:
        shop_service = ShopService(session)
        item = await shop_service.get_item_by_id(item_id)
        
        if not item:
            await callback.answer("Artículo no encontrado", show_alert=True)
            return
        
        # Obtener estadísticas del artículo
        from database.shop_models import UserPurchase
        from sqlalchemy import func
        
        purchases_stmt = select(func.count()).select_from(UserPurchase).where(
            UserPurchase.item_id == item_id
        )
        purchases_result = await session.execute(purchases_stmt)
        total_purchases = purchases_result.scalar() or 0
        
        item_text = f"🛒 **Gestión de Artículo**\n\n"
        item_text += f"📝 **Nombre**: {item.name}\n"
        item_text += f"📄 **Descripción**: {item.description or 'Sin descripción'}\n"
        item_text += f"💰 **Precio**: {item.price} besitos\n"
        item_text += f"📂 **Categoría**: {item.category or 'General'}\n"
        item_text += f"💎 **VIP Exclusivo**: {'Sí' if item.is_vip_exclusive else 'No'}\n"
        item_text += f"📊 **Nivel requerido**: {item.required_level}\n"
        item_text += f"📦 **Stock**: {item.stock_quantity if item.stock_quantity > 0 else 'Ilimitado'}\n"
        item_text += f"✅ **Activo**: {'Sí' if item.is_active else 'No'}\n"
        item_text += f"🛍️ **Compras totales**: {total_purchases}\n"
        
        if item.unlocks_lore_piece_code:
            item_text += f"🗝️ **Desbloquea pista**: {item.unlocks_lore_piece_code}\n"
        
        await callback.message.edit_text(
            item_text,
            reply_markup=get_admin_shop_item_actions_kb(item_id, item.is_active)
        )
        
    except Exception as e:
        logger.error(f"Error showing item actions for item {item_id}: {e}")
        await callback.answer("Error cargando acciones del artículo", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data.startswith("admin_shop_toggle:"))
async def admin_shop_toggle_item(callback: CallbackQuery, session: AsyncSession):
    """Activar/desactivar artículo."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    item_id = int(callback.data.split(":", 1)[1])
    
    try:
        from database.shop_models import ShopItem
        
        item = await session.get(ShopItem, item_id)
        if not item:
            await callback.answer("Artículo no encontrado", show_alert=True)
            return
        
        # Cambiar estado
        item.is_active = not item.is_active
        await session.commit()
        
        status_text = "activado" if item.is_active else "desactivado"
        await callback.answer(f"✅ Artículo {status_text}", show_alert=True)
        
        # Actualizar vista
        await admin_shop_item_actions(callback, session)
        
        logger.info(f"Admin {callback.from_user.id} toggled item {item.name} to {item.is_active}")
        
    except Exception as e:
        logger.error(f"Error toggling shop item {item_id}: {e}")
        await callback.answer("Error cambiando estado del artículo", show_alert=True)

@router.callback_query(F.data.startswith("admin_shop_delete:"))
async def admin_shop_delete_item(callback: CallbackQuery, session: AsyncSession):
    """Eliminar artículo (confirmación)."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    item_id = int(callback.data.split(":", 1)[1])
    
    try:
        from database.shop_models import ShopItem
        
        item = await session.get(ShopItem, item_id)
        if not item:
            await callback.answer("Artículo no encontrado", show_alert=True)
            return
        
        # Verificar si tiene compras asociadas
        from database.shop_models import UserPurchase
        from sqlalchemy import func
        
        purchases_stmt = select(func.count()).select_from(UserPurchase).where(
            UserPurchase.item_id == item_id
        )
        purchases_result = await session.execute(purchases_stmt)
        total_purchases = purchases_result.scalar() or 0
        
        if total_purchases > 0:
            await callback.answer(
                f"❌ No se puede eliminar. Hay {total_purchases} compras asociadas.",
                show_alert=True
            )
            return
        
        # Eliminar artículo
        await session.delete(item)
        await session.commit()
        
        await callback.message.edit_text(
            f"✅ **Artículo Eliminado**\n\n"
            f"El artículo '{item.name}' ha sido eliminado de la tienda.",
            reply_markup=get_admin_shop_main_kb()
        )
        
        logger.info(f"Admin {callback.from_user.id} deleted shop item: {item.name}")
        
    except Exception as e:
        logger.error(f"Error deleting shop item {item_id}: {e}")
        await callback.answer("Error eliminando artículo", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data == "admin_shop_categories")
async def admin_shop_categories(callback: CallbackQuery, session: AsyncSession):
    """Gestión de categorías de tienda."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        shop_service = ShopService(session)
        categories = await shop_service.get_categories()
        
        if not categories:
            categories_text = "📂 **Gestión de Categorías**\n\n" \
                           "No hay categorías creadas.\n" \
                           "Crea la primera categoría para organizar tus artículos."
        else:
            categories_text = f"📂 **Gestión de Categorías** ({len(categories)} total)\n\n"
            
            for category in categories:
                status = "✅" if category.is_active else "❌"
                emoji = category.emoji or "📁"
                categories_text += f"{status} {emoji} {category.name}\n"
                if category.description:
                    categories_text += f"   _{category.description}_\n"
                categories_text += "\n"
        
        await callback.message.edit_text(
            categories_text,
            reply_markup=get_admin_shop_categories_kb(categories)
        )
        
    except Exception as e:
        logger.error(f"Error showing shop categories: {e}")
        await callback.answer("Error cargando categorías", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data == "admin_shop_stats")
async def admin_shop_detailed_stats(callback: CallbackQuery, session: AsyncSession):
    """Estadísticas detalladas de la tienda."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        shop_service = ShopService(session)
        stats = await shop_service.get_shop_statistics()
        
        # Obtener estadísticas adicionales
        from database.shop_models import ShopItem, UserPurchase
        from sqlalchemy import func, desc
        
        # Top 5 artículos más vendidos
        top_items_stmt = select(
            ShopItem.name,
            func.count(UserPurchase.id).label('sales')
        ).join(
            UserPurchase, ShopItem.id == UserPurchase.item_id
        ).group_by(
            ShopItem.id, ShopItem.name
        ).order_by(
            desc('sales')
        ).limit(5)
        
        top_items_result = await session.execute(top_items_stmt)
        top_items = top_items_result.all()
        
        stats_text = f"📊 **Estadísticas Detalladas de Tienda**\n\n"
        stats_text += f"🛒 **Artículos totales**: {stats.get('total_items', 0)}\n"
        stats_text += f"🛍️ **Compras realizadas**: {stats.get('total_purchases', 0)}\n"
        stats_text += f"💰 **Ingresos totales**: {stats.get('total_revenue', 0)} besitos\n\n"
        
        if top_items:
            stats_text += "🏆 **Top 5 Más Vendidos**:\n"
            for i, (name, sales) in enumerate(top_items, 1):
                stats_text += f"{i}. {name} ({sales} ventas)\n"
        else:
            stats_text += "📈 **Sin ventas registradas aún**"
        
        from keyboards.common import get_back_kb
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_back_kb("admin_shop_main")
        )
        
    except Exception as e:
        logger.error(f"Error showing detailed shop stats: {e}")
        await callback.answer("Error cargando estadísticas", show_alert=True)
    
    await callback.answer()

# === COMANDOS DE ADMINISTRACIÓN ===

@router.message(Command("shop_admin"))
async def shop_admin_command(message: Message, session: AsyncSession):
    """Comando directo para administración de tienda."""
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nSolo los administradores pueden gestionar la tienda.",
            auto_delete_seconds=5
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
        
        await menu_manager.show_menu(
            message,
            stats_text,
            get_admin_shop_main_kb(),
            session,
            "admin_shop_main",
            delete_origin_message=True
        )
        
    except Exception as e:
        logger.error(f"Error in shop admin command: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo cargar el panel de administración.",
            auto_delete_seconds=5
        )

@router.callback_query(F.data.startswith("cancel_"))
async def cancel_shop_action(callback: CallbackQuery, state: FSMContext):
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