"""
Admin lore management handlers.
Provides comprehensive lore piece management interface for administrators.
"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.user_roles import is_admin
from utils.menu_manager import menu_manager
from utils.message_safety import safe_answer
from keyboards.admin_narrative_kb import (
    get_lore_management_kb,
    get_pagination_kb
)
from keyboards.common import get_back_kb
from services.lore_management_service import LoreManagementService
from database.models import LorePiece, ShopItem, UserLorePiece
from states.admin_states import LoreAdminStates

logger = logging.getLogger(__name__)
router = Router()

# MAIN LORE MANAGEMENT MENU

@router.callback_query(F.data == "admin_narrative_lore")
async def show_lore_management_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Display the main lore management menu with navigation options.

    This handler serves as the entry point for all lore management features,
    providing access to lore creation, listing, analytics, and linking functions.
    """
    # Admin authentication check
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Initialize lore management service for statistics
        lore_service = LoreManagementService(session)

        # Get basic statistics for the dashboard
        stmt = select(func.count(LorePiece.id)).where(LorePiece.is_active == True)
        result = await session.execute(stmt)
        total_lore_pieces = result.scalar()

        stmt = select(func.count(UserLorePiece.c.id))
        result = await session.execute(stmt)
        total_unlocks = result.scalar()

        # Build the lore management menu text
        menu_text = "📚 **Gestión de Fragmentos de Historia**\n\n"
        menu_text += "Gestiona todos los fragmentos de historia y lore desde este panel central.\n\n"

        menu_text += "📊 **Resumen Rápido:**\n"
        menu_text += f"• Fragmentos activos: {total_lore_pieces}\n"
        menu_text += f"• Desbloqueos totales: {total_unlocks}\n\n"

        menu_text += "**Selecciona una opción para continuar:**"

        # Get the lore management keyboard
        keyboard = get_lore_management_kb()

        # Update the menu using existing menu manager pattern
        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_narrative_lore"
        )

        logger.info(f"Lore management menu displayed for admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error showing lore management menu for user {callback.from_user.id}: {e}")
        await callback.answer("❌ Error al cargar el menú de gestión de lore", show_alert=True)

    await callback.answer()

# LORE PIECE CREATION

@router.callback_query(F.data == "admin_lore_create")
async def create_lore_piece_handler(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Start the lore piece creation process."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    menu_text = "📝 **Crear Nuevo Fragmento de Historia**\n\n"
    menu_text += "Vamos a crear un nuevo fragmento paso a paso.\n\n"
    menu_text += "**Paso 1:** Ingresa el código único del fragmento\n"
    menu_text += "_Ejemplo: story_chapter_1, secret_diary_entry_5_"

    await state.set_state(LoreAdminStates.waiting_for_code)

    await menu_manager.update_menu(
        callback,
        menu_text,
        get_back_kb("admin_narrative_lore"),
        session,
        "admin_lore_create"
    )
    await callback.answer()

@router.message(LoreAdminStates.waiting_for_code)
async def handle_lore_code_input(message: Message, session: AsyncSession, state: FSMContext):
    """Handle lore piece code input."""
    if not await is_admin(message.from_user.id, session):
        return await message.answer("❌ Acceso denegado")

    code_name = message.text.strip()

    # Validate code format
    if not code_name or len(code_name) < 3:
        await message.answer("❌ El código debe tener al menos 3 caracteres.")
        return

    # Check if code already exists
    stmt = select(LorePiece).where(LorePiece.code_name == code_name)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        await message.answer(f"❌ Ya existe un fragmento con el código '{code_name}'.")
        return

    # Save code and move to next step
    await state.update_data(code_name=code_name)
    await state.set_state(LoreAdminStates.waiting_for_title)

    menu_text = f"✅ **Código:** `{code_name}`\n\n"
    menu_text += "**Paso 2:** Ingresa el título del fragmento\n"
    menu_text += "_Este será el nombre visible para los usuarios_"

    await message.answer(menu_text)

@router.message(LoreAdminStates.waiting_for_title)
async def handle_lore_title_input(message: Message, session: AsyncSession, state: FSMContext):
    """Handle lore piece title input."""
    if not await is_admin(message.from_user.id, session):
        return await message.answer("❌ Acceso denegado")

    title = message.text.strip()

    if not title or len(title) < 3:
        await message.answer("❌ El título debe tener al menos 3 caracteres.")
        return

    # Save title and move to next step
    data = await state.get_data()
    await state.update_data(title=title)
    await state.set_state(LoreAdminStates.waiting_for_content)

    menu_text = f"✅ **Código:** `{data['code_name']}`\n"
    menu_text += f"✅ **Título:** {title}\n\n"
    menu_text += "**Paso 3:** Ingresa el contenido del fragmento\n"
    menu_text += "_Puedes usar Markdown para formato_"

    await message.answer(menu_text)

@router.message(LoreAdminStates.waiting_for_content)
async def handle_lore_content_input(message: Message, session: AsyncSession, state: FSMContext):
    """Handle lore piece content input and create the lore piece."""
    if not await is_admin(message.from_user.id, session):
        return await message.answer("❌ Acceso denegado")

    content = message.text.strip()

    if not content or len(content) < 10:
        await message.answer("❌ El contenido debe tener al menos 10 caracteres.")
        return

    try:
        # Get all stored data
        data = await state.get_data()

        # Create the lore piece
        new_lore = LorePiece(
            code_name=data['code_name'],
            title=data['title'],
            content=content,
            content_type='text',  # Default to text, can be enhanced later
            is_active=True,
            created_at=datetime.utcnow()
        )

        session.add(new_lore)
        await session.commit()
        await session.refresh(new_lore)

        # Clear state
        await state.clear()

        success_text = "✅ **Fragmento Creado Exitosamente**\n\n"
        success_text += f"**ID:** {new_lore.id}\n"
        success_text += f"**Código:** `{new_lore.code_name}`\n"
        success_text += f"**Título:** {new_lore.title}\n"
        success_text += f"**Contenido:** {content[:100]}{'...' if len(content) > 100 else ''}\n\n"
        success_text += "El fragmento está ahora disponible en el sistema."

        await message.answer(success_text)

        logger.info(f"Lore piece created by admin {message.from_user.id}: {new_lore.id}")

    except Exception as e:
        logger.error(f"Error creating lore piece: {e}")
        await message.answer("❌ Error al crear el fragmento. Inténtalo de nuevo.")
        await state.clear()

# LORE PIECE LISTING

@router.callback_query(F.data == "admin_lore_list")
@router.callback_query(F.data.startswith("admin_lore_list:"))
async def list_lore_pieces_handler(callback: CallbackQuery, session: AsyncSession):
    """List all lore pieces with pagination."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Parse page number from callback data
        page = 0
        if ":" in callback.data:
            page = int(callback.data.split(":")[1])

        page_size = 5
        offset = page * page_size

        # Get total count for pagination
        count_stmt = select(func.count(LorePiece.id)).where(LorePiece.is_active == True)
        count_result = await session.execute(count_stmt)
        total_count = count_result.scalar()
        total_pages = max(1, (total_count + page_size - 1) // page_size)

        # Get lore pieces for current page
        stmt = select(LorePiece).where(
            LorePiece.is_active == True
        ).order_by(desc(LorePiece.created_at)).offset(offset).limit(page_size)

        result = await session.execute(stmt)
        lore_pieces = result.scalars().all()

        # Build the list display
        menu_text = f"📚 **Lista de Fragmentos** (Página {page + 1}/{total_pages})\n\n"

        if not lore_pieces:
            menu_text += "_No hay fragmentos disponibles._"
        else:
            for lore in lore_pieces:
                # Get unlock count for this lore piece
                unlock_stmt = select(func.count(UserLorePiece.c.id)).where(
                    UserLorePiece.lore_piece_id == lore.id
                )
                unlock_result = await session.execute(unlock_stmt)
                unlock_count = unlock_result.scalar()

                status_icon = "✅" if lore.is_active else "❌"
                menu_text += f"{status_icon} **{lore.title}**\n"
                menu_text += f"   `ID: {lore.id}` | `Código: {lore.code_name}`\n"
                menu_text += f"   📊 {unlock_count} desbloqueos\n"
                menu_text += f"   📅 {lore.created_at.strftime('%d/%m/%Y')}\n"
                menu_text += f"   ✏️ Editar (ID: {lore.id})\n\n"

        # Create keyboard with pagination
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        # Pagination controls
        if total_pages > 1:
            if page > 0:
                builder.button(text="⬅️ Anterior", callback_data=f"admin_lore_list:{page - 1}")
            if page < total_pages - 1:
                builder.button(text="Siguiente ➡️", callback_data=f"admin_lore_list:{page + 1}")
            builder.adjust(2)

        # Action buttons
        builder.button(text="🔍 Buscar", callback_data="admin_lore_search")
        builder.button(text="📊 Analytics", callback_data="admin_lore_analytics")
        builder.button(text="🔗 Vincular Item", callback_data="admin_lore_link_item")
        builder.button(text="🔙 Volver", callback_data="admin_narrative_lore")
        builder.adjust(2, 1, 1)

        await menu_manager.update_menu(
            callback,
            menu_text,
            builder.as_markup(),
            session,
            "admin_lore_list"
        )

        logger.info(f"Lore list displayed for admin {callback.from_user.id}, page {page}")

    except Exception as e:
        logger.error(f"Error listing lore pieces: {e}")
        await callback.answer("❌ Error al cargar la lista de fragmentos", show_alert=True)

    await callback.answer()

# SHOP ITEM LINKING

@router.callback_query(F.data == "admin_lore_link_item")
async def link_lore_to_item_handler(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Start the process of linking lore to shop items."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Get available shop items
        stmt = select(ShopItem).where(ShopItem.is_active == True).order_by(ShopItem.name)
        result = await session.execute(stmt)
        shop_items = result.scalars().all()

        if not shop_items:
            await callback.answer("❌ No hay items disponibles en la tienda", show_alert=True)
            return

        # Build item selection menu
        menu_text = "🔗 **Vincular Fragmento con Item de Tienda**\n\n"
        menu_text += "Selecciona un item de tienda para vincular con un fragmento de historia.\n\n"
        menu_text += "**Items disponibles:**\n"

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        for item in shop_items[:10]:  # Limit to first 10 items
            menu_text += f"• {item.name} ({item.price} besitos)\n"
            builder.button(
                text=f"{item.name}",
                callback_data=f"admin_lore_select_item:{item.id}"
            )

        builder.button(text="🔙 Volver", callback_data="admin_narrative_lore")
        builder.adjust(1)

        await menu_manager.update_menu(
            callback,
            menu_text,
            builder.as_markup(),
            session,
            "admin_lore_link_item"
        )

    except Exception as e:
        logger.error(f"Error in link lore to item handler: {e}")
        await callback.answer("❌ Error al cargar items", show_alert=True)

    await callback.answer()

@router.callback_query(F.data.startswith("admin_lore_select_item:"))
async def select_item_for_linking(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Handle shop item selection for linking."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        item_id = int(callback.data.split(":")[1])

        # Get the selected item
        stmt = select(ShopItem).where(ShopItem.id == item_id)
        result = await session.execute(stmt)
        shop_item = result.scalar_one_or_none()

        if not shop_item:
            await callback.answer("❌ Item no encontrado", show_alert=True)
            return

        # Get available lore pieces
        stmt = select(LorePiece).where(LorePiece.is_active == True).order_by(LorePiece.title)
        result = await session.execute(stmt)
        lore_pieces = result.scalars().all()

        if not lore_pieces:
            await callback.answer("❌ No hay fragmentos disponibles", show_alert=True)
            return

        # Save selected item to state
        await state.update_data(selected_item_id=item_id)

        # Build lore selection menu
        menu_text = f"🔗 **Vincular con: {shop_item.name}**\n\n"
        menu_text += "Selecciona el fragmento de historia que se desbloqueará al comprar este item:\n\n"

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        for lore in lore_pieces[:10]:  # Limit to first 10 lore pieces
            menu_text += f"• {lore.title}\n"
            builder.button(
                text=f"{lore.title}",
                callback_data=f"admin_lore_confirm_link:{lore.id}"
            )

        builder.button(text="🔙 Volver", callback_data="admin_lore_link_item")
        builder.adjust(1)

        await menu_manager.update_menu(
            callback,
            menu_text,
            builder.as_markup(),
            session,
            "admin_lore_select_lore"
        )

    except Exception as e:
        logger.error(f"Error selecting item for linking: {e}")
        await callback.answer("❌ Error en la selección", show_alert=True)

    await callback.answer()

@router.callback_query(F.data.startswith("admin_lore_confirm_link:"))
async def confirm_lore_item_link(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Confirm and create the lore-item link."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        lore_id = int(callback.data.split(":")[1])
        data = await state.get_data()
        item_id = data.get('selected_item_id')

        if not item_id:
            await callback.answer("❌ Error: Item no seleccionado", show_alert=True)
            return

        # Get both records
        stmt = select(LorePiece).where(LorePiece.id == lore_id)
        result = await session.execute(stmt)
        lore_piece = result.scalar_one_or_none()

        stmt = select(ShopItem).where(ShopItem.id == item_id)
        result = await session.execute(stmt)
        shop_item = result.scalar_one_or_none()

        if not lore_piece or not shop_item:
            await callback.answer("❌ Error: Fragmento o item no encontrado", show_alert=True)
            return

        # Update lore piece with unlock condition
        lore_piece.unlock_condition_type = 'shop_purchase'
        lore_piece.unlock_condition_value = str(item_id)

        await session.commit()
        await state.clear()

        success_text = "✅ **Vinculación Exitosa**\n\n"
        success_text += f"**Fragmento:** {lore_piece.title}\n"
        success_text += f"**Item:** {shop_item.name}\n\n"
        success_text += "El fragmento se desbloqueará automáticamente cuando los usuarios compren este item."

        await menu_manager.update_menu(
            callback,
            success_text,
            get_back_kb("admin_narrative_lore"),
            session,
            "admin_lore_link_success"
        )

        logger.info(f"Lore {lore_id} linked to shop item {item_id} by admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error confirming lore-item link: {e}")
        await callback.answer("❌ Error al crear la vinculación", show_alert=True)

    await callback.answer()

# LORE ANALYTICS

@router.callback_query(F.data == "admin_lore_analytics")
async def show_lore_analytics(callback: CallbackQuery, session: AsyncSession):
    """Display lore analytics dashboard."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Get analytics data
        lore_service = LoreManagementService(session)

        # Basic statistics
        stmt = select(func.count(LorePiece.id)).where(LorePiece.is_active == True)
        result = await session.execute(stmt)
        total_lore = result.scalar()

        stmt = select(func.count(UserLorePiece.c.id))
        result = await session.execute(stmt)
        total_unlocks = result.scalar()

        # Top unlocked lore pieces
        stmt = select(
            LorePiece.title,
            func.count(UserLorePiece.c.id).label('unlock_count')
        ).join(
            UserLorePiece, LorePiece.id == UserLorePiece.lore_piece_id
        ).group_by(
            LorePiece.id, LorePiece.title
        ).order_by(
            desc('unlock_count')
        ).limit(5)

        result = await session.execute(stmt)
        top_lore = result.all()

        # Build analytics display
        menu_text = "📊 **Analytics de Fragmentos de Historia**\n\n"

        menu_text += "**📈 Estadísticas Generales:**\n"
        menu_text += f"• Total de fragmentos: {total_lore}\n"
        menu_text += f"• Total de desbloqueos: {total_unlocks}\n"

        if total_lore > 0:
            avg_unlocks = total_unlocks / total_lore
            menu_text += f"• Promedio desbloqueos/fragmento: {avg_unlocks:.1f}\n"

        menu_text += "\n**🏆 Top 5 Fragmentos Más Desbloqueados:**\n"
        if top_lore:
            for i, (title, count) in enumerate(top_lore, 1):
                menu_text += f"{i}. {title}: {count} desbloqueos\n"
        else:
            menu_text += "_No hay datos de desbloqueos aún._"

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="📊 Analytics Detallados", callback_data="admin_lore_detailed_analytics")
        builder.button(text="🔙 Volver", callback_data="admin_narrative_lore")
        builder.adjust(1)

        await menu_manager.update_menu(
            callback,
            menu_text,
            builder.as_markup(),
            session,
            "admin_lore_analytics"
        )

        logger.info(f"Lore analytics displayed for admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error showing lore analytics: {e}")
        await callback.answer("❌ Error al cargar analytics", show_alert=True)

    await callback.answer()

# SEARCH FUNCTIONALITY

@router.callback_query(F.data == "admin_lore_search")
async def start_lore_search(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Start lore search process."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    menu_text = "🔍 **Buscar Fragmentos**\n\n"
    menu_text += "Ingresa un término de búsqueda para encontrar fragmentos por:\n"
    menu_text += "• Título\n"
    menu_text += "• Código\n"
    menu_text += "• Contenido\n\n"
    menu_text += "_Escribe el término que deseas buscar:_"

    await state.set_state(LoreAdminStates.waiting_for_search)

    await menu_manager.update_menu(
        callback,
        menu_text,
        get_back_kb("admin_lore_list"),
        session,
        "admin_lore_search"
    )
    await callback.answer()

@router.message(LoreAdminStates.waiting_for_search)
async def handle_lore_search(message: Message, session: AsyncSession, state: FSMContext):
    """Handle lore search query."""
    if not await is_admin(message.from_user.id, session):
        return await message.answer("❌ Acceso denegado")

    search_term = message.text.strip()

    if len(search_term) < 2:
        await message.answer("❌ El término de búsqueda debe tener al menos 2 caracteres.")
        return

    try:
        # Search in title, code_name, and content
        search_pattern = f"%{search_term.lower()}%"
        stmt = select(LorePiece).where(
            and_(
                LorePiece.is_active == True,
                or_(
                    func.lower(LorePiece.title).like(search_pattern),
                    func.lower(LorePiece.code_name).like(search_pattern),
                    func.lower(LorePiece.content).like(search_pattern)
                )
            )
        ).order_by(LorePiece.title)

        result = await session.execute(stmt)
        lore_pieces = result.scalars().all()

        await state.clear()

        # Build search results display
        menu_text = f"🔍 **Resultados de búsqueda: '{search_term}'**\n\n"

        if not lore_pieces:
            menu_text += "_No se encontraron fragmentos que coincidan con el término de búsqueda._"
        else:
            menu_text += f"**{len(lore_pieces)} fragmento(s) encontrado(s):**\n\n"
            for lore in lore_pieces[:10]:  # Limit to 10 results
                menu_text += f"🔹 **{lore.title}**\n"
                menu_text += f"   `ID: {lore.id}` | `Código: {lore.code_name}`\n"
                menu_text += f"   📅 {lore.created_at.strftime('%d/%m/%Y')}\n\n"

        await message.answer(menu_text)

        logger.info(f"Lore search performed by admin {message.from_user.id}: '{search_term}', {len(lore_pieces)} results")

    except Exception as e:
        logger.error(f"Error in lore search: {e}")
        await message.answer("❌ Error al realizar la búsqueda.")
        await state.clear()

# ADVANCED LORE EDITING

@router.callback_query(F.data.startswith("admin_lore_edit:"))
async def edit_lore_piece(callback: CallbackQuery, session: AsyncSession):
    """Start editing a specific lore piece."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        lore_id = int(callback.data.split(":")[1])

        # Get the lore piece
        stmt = select(LorePiece).where(LorePiece.id == lore_id)
        result = await session.execute(stmt)
        lore_piece = result.scalar_one_or_none()

        if not lore_piece:
            await callback.answer("❌ Fragmento no encontrado", show_alert=True)
            return

        # Build edit menu
        menu_text = f"✏️ **Editar Fragmento: {lore_piece.title}**\n\n"
        menu_text += f"**ID:** {lore_piece.id}\n"
        menu_text += f"**Código:** `{lore_piece.code_name}`\n"
        menu_text += f"**Título:** {lore_piece.title}\n"
        menu_text += f"**Categoría:** {lore_piece.category or 'Sin categoría'}\n"
        menu_text += f"**Tipo de contenido:** {lore_piece.content_type}\n"
        menu_text += f"**Estado:** {'Activo' if lore_piece.is_active else 'Inactivo'}\n"
        menu_text += f"**Condición de desbloqueo:** {lore_piece.unlock_condition_type or 'Ninguna'}\n\n"
        menu_text += "Selecciona qué deseas editar:"

        builder = InlineKeyboardBuilder()

        builder.button(text="📝 Título", callback_data=f"admin_lore_edit_title:{lore_id}")
        builder.button(text="📋 Contenido", callback_data=f"admin_lore_edit_content:{lore_id}")
        builder.button(text="🏷️ Categoría", callback_data=f"admin_lore_edit_category:{lore_id}")
        builder.button(text="🔓 Condiciones", callback_data=f"admin_lore_edit_conditions:{lore_id}")
        builder.button(text="⚡ Estado", callback_data=f"admin_lore_toggle_status:{lore_id}")
        builder.button(text="🗑️ Eliminar", callback_data=f"admin_lore_delete:{lore_id}")
        builder.button(text="🔙 Volver", callback_data="admin_lore_list")
        builder.adjust(2, 2, 1, 1, 1)

        await menu_manager.update_menu(
            callback,
            menu_text,
            builder.as_markup(),
            session,
            f"admin_lore_edit:{lore_id}"
        )

    except Exception as e:
        logger.error(f"Error editing lore piece: {e}")
        await callback.answer("❌ Error al cargar el fragmento", show_alert=True)

    await callback.answer()

@router.callback_query(F.data.startswith("admin_lore_toggle_status:"))
async def toggle_lore_status(callback: CallbackQuery, session: AsyncSession):
    """Toggle lore piece active status."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        lore_id = int(callback.data.split(":")[1])

        # Get and update the lore piece
        stmt = select(LorePiece).where(LorePiece.id == lore_id)
        result = await session.execute(stmt)
        lore_piece = result.scalar_one_or_none()

        if not lore_piece:
            await callback.answer("❌ Fragmento no encontrado", show_alert=True)
            return

        # Toggle status
        lore_piece.is_active = not lore_piece.is_active
        await session.commit()

        status_text = "activado" if lore_piece.is_active else "desactivado"
        await callback.answer(f"✅ Fragmento {status_text}", show_alert=True)

        # Create a new callback query object for redirection
        new_callback = type('CallbackQuery', (), {
            'id': callback.id,
            'from_user': callback.from_user,
            'chat_instance': callback.chat_instance,
            'data': f"admin_lore_edit:{lore_id}",
            'answer': callback.answer
        })()

        # Redirect back to edit menu
        await edit_lore_piece(new_callback, session)

        logger.info(f"Lore piece {lore_id} status toggled by admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error toggling lore status: {e}")
        await callback.answer("❌ Error al cambiar el estado", show_alert=True)

# CATEGORY MANAGEMENT

@router.callback_query(F.data == "admin_lore_categories")
async def manage_lore_categories(callback: CallbackQuery, session: AsyncSession):
    """Manage lore categories."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Get category statistics
        stmt = select(
            LorePiece.category,
            func.count(LorePiece.id).label('count')
        ).where(
            LorePiece.is_active == True
        ).group_by(
            LorePiece.category
        ).order_by(
            desc('count')
        )

        result = await session.execute(stmt)
        categories = result.all()

        # Build category management menu
        menu_text = "🏷️ **Gestión de Categorías**\n\n"
        menu_text += "**Categorías existentes:**\n"

        if categories:
            for category, count in categories:
                cat_name = category or "Sin categoría"
                menu_text += f"• {cat_name}: {count} fragmentos\n"
        else:
            menu_text += "_No hay categorías definidas._"

        menu_text += "\n**Acciones disponibles:**"

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        builder.button(text="➕ Crear Categoría", callback_data="admin_lore_create_category")
        builder.button(text="📊 Ver por Categoría", callback_data="admin_lore_view_by_category")
        builder.button(text="🔄 Reorganizar", callback_data="admin_lore_reorganize_categories")
        builder.button(text="🔙 Volver", callback_data="admin_narrative_lore")
        builder.adjust(1)

        await menu_manager.update_menu(
            callback,
            menu_text,
            builder.as_markup(),
            session,
            "admin_lore_categories"
        )

    except Exception as e:
        logger.error(f"Error managing categories: {e}")
        await callback.answer("❌ Error al cargar categorías", show_alert=True)

    await callback.answer()

@router.callback_query(F.data == "admin_lore_view_by_category")
async def view_lore_by_category(callback: CallbackQuery, session: AsyncSession):
    """View lore pieces organized by category."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Get lore pieces grouped by category
        stmt = select(LorePiece).where(
            LorePiece.is_active == True
        ).order_by(
            LorePiece.category.nulls_last(),
            LorePiece.title
        )

        result = await session.execute(stmt)
        lore_pieces = result.scalars().all()

        # Group by category
        categorized_lore = {}
        for lore in lore_pieces:
            category = lore.category or "Sin categoría"
            if category not in categorized_lore:
                categorized_lore[category] = []
            categorized_lore[category].append(lore)

        # Build categorized display
        menu_text = "📂 **Fragmentos por Categoría**\n\n"

        for category, lore_list in categorized_lore.items():
            menu_text += f"**📁 {category}** ({len(lore_list)} fragmentos)\n"
            for lore in lore_list[:5]:  # Show first 5 in each category
                menu_text += f"  • {lore.title}\n"
            if len(lore_list) > 5:
                menu_text += f"  ... y {len(lore_list) - 5} más\n"
            menu_text += "\n"

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Volver", callback_data="admin_lore_categories")
        builder.adjust(1)

        await menu_manager.update_menu(
            callback,
            menu_text,
            builder.as_markup(),
            session,
            "admin_lore_view_by_category"
        )

    except Exception as e:
        logger.error(f"Error viewing by category: {e}")
        await callback.answer("❌ Error al cargar vista por categorías", show_alert=True)

    await callback.answer()

# BULK OPERATIONS

@router.callback_query(F.data == "admin_lore_bulk_operations")
async def bulk_operations_menu(callback: CallbackQuery, session: AsyncSession):
    """Show bulk operations menu."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    menu_text = "📦 **Operaciones en Lote**\n\n"
    menu_text += "Gestiona múltiples fragmentos simultáneamente:\n\n"
    menu_text += "**Operaciones disponibles:**\n"
    menu_text += "• Activar/Desactivar fragmentos por categoría\n"
    menu_text += "• Cambiar categoría de múltiples fragmentos\n"
    menu_text += "• Exportar fragmentos a CSV\n"
    menu_text += "• Análisis masivo de efectividad\n"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    builder.button(text="⚡ Cambio Estado Masivo", callback_data="admin_lore_bulk_status")
    builder.button(text="🏷️ Cambio Categoría Masivo", callback_data="admin_lore_bulk_category")
    builder.button(text="📄 Exportar CSV", callback_data="admin_lore_export_csv")
    builder.button(text="📊 Análisis Masivo", callback_data="admin_lore_bulk_analytics")
    builder.button(text="🔙 Volver", callback_data="admin_narrative_lore")
    builder.adjust(2, 2, 1)

    await menu_manager.update_menu(
        callback,
        menu_text,
        builder.as_markup(),
        session,
        "admin_lore_bulk_operations"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_lore_export_csv")
async def export_lore_csv(callback: CallbackQuery, session: AsyncSession):
    """Export lore pieces to CSV format."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Get all lore pieces
        stmt = select(LorePiece).order_by(LorePiece.created_at)
        result = await session.execute(stmt)
        lore_pieces = result.scalars().all()

        if not lore_pieces:
            await callback.answer("❌ No hay fragmentos para exportar", show_alert=True)
            return

        # Create CSV content
        import io
        import csv
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow([
            'ID', 'Código', 'Título', 'Categoría', 'Tipo Contenido',
            'Estado', 'Condición Desbloqueo', 'Fecha Creación', 'Contenido (preview)'
        ])

        # Write data
        for lore in lore_pieces:
            writer.writerow([
                lore.id,
                lore.code_name,
                lore.title,
                lore.category or '',
                lore.content_type,
                'Activo' if lore.is_active else 'Inactivo',
                lore.unlock_condition_type or '',
                lore.created_at.strftime('%Y-%m-%d %H:%M'),
                lore.content[:100] + '...' if len(lore.content) > 100 else lore.content
            ])

        csv_content = output.getvalue()
        output.close()

        # Create response with CSV data
        menu_text = f"📄 **Exportación CSV Generada**\n\n"
        menu_text += f"**Total de fragmentos:** {len(lore_pieces)}\n"
        menu_text += f"**Fecha de exportación:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\n"
        menu_text += f"**Tamaño del archivo:** {len(csv_content)} caracteres\n\n"
        menu_text += "_El archivo CSV contiene todos los fragmentos con sus metadatos._\n\n"
        menu_text += "**Columnas incluidas:**\n"
        menu_text += "• ID, Código, Título\n"
        menu_text += "• Categoría, Tipo de Contenido\n"
        menu_text += "• Estado, Condiciones de Desbloqueo\n"
        menu_text += "• Fecha de Creación, Preview del Contenido"

        # For now, just show the confirmation. In a real implementation,
        # you would send the CSV as a file
        await menu_manager.update_menu(
            callback,
            menu_text,
            get_back_kb("admin_lore_bulk_operations"),
            session,
            "admin_lore_export_csv"
        )

        logger.info(f"CSV export requested by admin {callback.from_user.id}: {len(lore_pieces)} lore pieces")

    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        await callback.answer("❌ Error al exportar CSV", show_alert=True)

    await callback.answer()

# DETAILED ANALYTICS

@router.callback_query(F.data == "admin_lore_detailed_analytics")
async def show_detailed_analytics(callback: CallbackQuery, session: AsyncSession):
    """Show detailed lore analytics."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Get comprehensive analytics
        lore_service = LoreManagementService(session)

        # Content type distribution
        stmt = select(
            LorePiece.content_type,
            func.count(LorePiece.id).label('count')
        ).where(
            LorePiece.is_active == True
        ).group_by(
            LorePiece.content_type
        )
        result = await session.execute(stmt)
        content_types = result.all()

        # Unlock condition analysis
        stmt = select(
            LorePiece.unlock_condition_type,
            func.count(LorePiece.id).label('count')
        ).where(
            LorePiece.is_active == True
        ).group_by(
            LorePiece.unlock_condition_type
        )
        result = await session.execute(stmt)
        unlock_conditions = result.all()

        # Recent activity (last 7 days)
        from datetime import timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        stmt = select(func.count(UserLorePiece.c.id)).where(
            UserLorePiece.unlocked_at >= seven_days_ago
        )
        result = await session.execute(stmt)
        recent_unlocks = result.scalar()

        # Build detailed analytics display
        menu_text = "📊 **Analytics Detallados**\n\n"

        menu_text += "**📈 Distribución por Tipo de Contenido:**\n"
        if content_types:
            for content_type, count in content_types:
                menu_text += f"• {content_type}: {count} fragmentos\n"
        else:
            menu_text += "_No hay datos disponibles._\n"

        menu_text += "\n**🔓 Condiciones de Desbloqueo:**\n"
        if unlock_conditions:
            for condition, count in unlock_conditions:
                condition_name = condition or "Sin condición"
                menu_text += f"• {condition_name}: {count} fragmentos\n"
        else:
            menu_text += "_No hay datos disponibles._\n"

        menu_text += f"\n**📅 Actividad Reciente (7 días):**\n"
        menu_text += f"• {recent_unlocks} desbloqueos en la última semana\n"

        # Get average content length
        stmt = select(func.avg(func.length(LorePiece.content))).where(
            LorePiece.is_active == True
        )
        result = await session.execute(stmt)
        avg_length = result.scalar()

        if avg_length:
            menu_text += f"• Longitud promedio del contenido: {int(avg_length)} caracteres\n"

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(text="📊 Exportar Reporte", callback_data="admin_lore_export_analytics")
        builder.button(text="🔙 Volver", callback_data="admin_lore_analytics")
        builder.adjust(1)

        await menu_manager.update_menu(
            callback,
            menu_text,
            builder.as_markup(),
            session,
            "admin_lore_detailed_analytics"
        )

        logger.info(f"Detailed analytics displayed for admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error showing detailed analytics: {e}")
        await callback.answer("❌ Error al cargar analytics detallados", show_alert=True)

    await callback.answer()
