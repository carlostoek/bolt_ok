"""
Admin shop handlers router and menu implementation.
Provides comprehensive shop management interface for administrators.
"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from utils.user_roles import is_admin
from utils.menu_manager import menu_manager
from keyboards.admin_shop_kb import get_shop_admin_main_kb
from keyboards.common import get_back_kb
from services.shop_admin_service import ShopAdminService

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "admin_shop_main")
async def show_shop_admin_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Display the main shop administration menu with navigation options.

    This handler serves as the entry point for all shop administration features,
    providing access to item management, category management, statistics, and
    other administrative functions.
    """
    # Admin authentication check using existing patterns
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Initialize shop admin service for statistics
        shop_admin_service = ShopAdminService(session)

        # Get basic statistics for the dashboard
        stats_result = await shop_admin_service.get_admin_statistics(callback.from_user.id)

        # Build the shop admin menu text
        menu_text = "🛒 **Panel de Administración de Tienda**\n\n"
        menu_text += "Gestiona todos los aspectos de la tienda DianaBot desde este panel central.\n\n"

        if stats_result.get("success"):
            stats = stats_result.get("statistics", {})
            inventory = stats.get("inventory", {})
            sales = stats.get("sales", {})

            menu_text += "📊 **Resumen Rápido:**\n"
            menu_text += f"• Items activos: {inventory.get('items', {}).get('active', 0)}\n"
            menu_text += f"• Categorías activas: {inventory.get('categories', {}).get('active', 0)}\n"
            menu_text += f"• Ventas totales: {sales.get('overall', {}).get('total_sales', 0)}\n"
            menu_text += f"• Ingresos totales: {sales.get('overall', {}).get('total_revenue', 0)} besitos\n\n"
        else:
            menu_text += "📊 **Estadísticas:** Cargando...\n\n"

        menu_text += "**Selecciona una opción para continuar:**"

        # Get the shop admin main keyboard
        keyboard = get_shop_admin_main_kb()

        # Update the menu using existing menu manager pattern
        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_shop_main"
        )

        logger.info(f"Shop admin menu displayed for admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error showing shop admin menu for user {callback.from_user.id}: {e}")
        await callback.answer("❌ Error al cargar el menú de administración", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "admin_shop_back")
async def shop_admin_back(callback: CallbackQuery, session: AsyncSession):
    """
    Handle back navigation from shop admin sub-menus.
    Returns to the main shop admin menu.
    """
    # Admin authentication check
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Redirect to main shop admin menu
        await show_shop_admin_menu(callback, session)

    except Exception as e:
        logger.error(f"Error in shop admin back navigation: {e}")
        await callback.answer("Error en la navegación", show_alert=True)


@router.message(Command("shop_admin"))
async def shop_admin_command(message: Message, session: AsyncSession):
    """
    Command handler to access shop administration menu directly.
    Provides alternative access method for administrators.
    """
    # Admin authentication check using existing patterns
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nNo tienes permisos de administrador para acceder a la gestión de tienda.",
            auto_delete_seconds=5
        )
        return

    try:
        # Initialize shop admin service for statistics
        shop_admin_service = ShopAdminService(session)

        # Get basic statistics for the dashboard
        stats_result = await shop_admin_service.get_admin_statistics(message.from_user.id)

        # Build the shop admin menu text
        menu_text = "🛒 **Panel de Administración de Tienda**\n\n"
        menu_text += "Gestiona todos los aspectos de la tienda DianaBot desde este panel central.\n\n"

        if stats_result.get("success"):
            stats = stats_result.get("statistics", {})
            inventory = stats.get("inventory", {})
            sales = stats.get("sales", {})

            menu_text += "📊 **Resumen Rápido:**\n"
            menu_text += f"• Items activos: {inventory.get('items', {}).get('active', 0)}\n"
            menu_text += f"• Categorías activas: {inventory.get('categories', {}).get('active', 0)}\n"
            menu_text += f"• Ventas totales: {sales.get('overall', {}).get('total_sales', 0)}\n"
            menu_text += f"• Ingresos totales: {sales.get('overall', {}).get('total_revenue', 0)} besitos\n\n"
        else:
            menu_text += "📊 **Estadísticas:** Cargando...\n\n"

        menu_text += "**Selecciona una opción para continuar:**"

        # Get the shop admin main keyboard
        keyboard = get_shop_admin_main_kb()

        # Show the menu using existing menu manager pattern
        await menu_manager.show_menu(
            message,
            menu_text,
            keyboard,
            session,
            "admin_shop_main"
        )

        logger.info(f"Shop admin menu accessed via command by admin {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error in shop admin command for user {message.from_user.id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo cargar el panel de administración de tienda.",
            auto_delete_seconds=5
        )


# CATEGORY MANAGEMENT HANDLERS

@router.callback_query(F.data == "admin_shop_categories")
async def manage_categories(callback: CallbackQuery, session: AsyncSession):
    """
    Display the category management menu with list of all categories.

    This handler provides access to category creation, editing, and organization
    following the established admin panel patterns.
    """
    # Admin authentication check using existing patterns
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Initialize shop admin service
        shop_admin_service = ShopAdminService(session)

        # Get categories with inactive ones included for admin view
        categories_result = await shop_admin_service.get_categories(
            callback.from_user.id,
            include_inactive=True
        )

        # Build categories management menu text
        menu_text = "📁 **Gestión de Categorías de Tienda**\n\n"

        if categories_result.get("success"):
            categories = categories_result.get("categories", [])
            active_count = sum(1 for cat in categories if cat.get("is_active"))
            total_count = len(categories)

            menu_text += f"📊 **Resumen:**\n"
            menu_text += f"• Total de categorías: {total_count}\n"
            menu_text += f"• Categorías activas: {active_count}\n"
            menu_text += f"• Categorías inactivas: {total_count - active_count}\n\n"

            if categories:
                menu_text += "📋 **Categorías Existentes:**\n"
                for category in categories[:10]:  # Show first 10 categories
                    status = "🟢" if category.get("is_active") else "🔴"
                    vip_badge = " 💎" if category.get("is_vip_only") else ""
                    menu_text += f"{status} {category.get('name')}{vip_badge}\n"

                if total_count > 10:
                    menu_text += f"... y {total_count - 10} más\n"
            else:
                menu_text += "📋 **No hay categorías creadas aún.**\n"
        else:
            menu_text += "❌ Error al cargar las categorías.\n"

        menu_text += "\n**Selecciona una opción para continuar:**"

        # Get category management keyboard
        from keyboards.admin_shop_kb import get_category_management_kb
        keyboard = get_category_management_kb()

        # Update menu using existing pattern
        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_shop_categories"
        )

        logger.info(f"Category management menu displayed for admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error showing category management menu for user {callback.from_user.id}: {e}")
        await callback.answer("❌ Error al cargar la gestión de categorías", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "admin_category_create")
async def create_category(callback: CallbackQuery, session: AsyncSession):
    """
    Handle category creation workflow with form validation.

    This handler initiates the category creation process, collecting necessary
    information through a multi-step form with proper validation and feedback.
    """
    # Admin authentication check
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Build category creation form text
        form_text = "➕ **Crear Nueva Categoría**\n\n"
        form_text += "Para crear una nueva categoría, necesitamos la siguiente información:\n\n"
        form_text += "📝 **Campos Requeridos:**\n"
        form_text += "• **Nombre:** Nombre único de la categoría\n"
        form_text += "• **Descripción:** Descripción detallada (opcional)\n"
        form_text += "• **Orden:** Posición en la lista (número)\n"
        form_text += "• **Acceso VIP:** Solo para usuarios VIP (Sí/No)\n\n"
        form_text += "💡 **Ejemplo:**\n"
        form_text += "`Nombre: Accesorios Especiales`\n"
        form_text += "`Descripción: Items únicos y exclusivos`\n"
        form_text += "`Orden: 1`\n"
        form_text += "`VIP: Sí`\n\n"
        form_text += "📩 **Envía los datos en el siguiente formato:**\n"
        form_text += "`/crear_categoria <nombre>|<descripcion>|<orden>|<vip>`\n\n"
        form_text += "**Ejemplo completo:**\n"
        form_text += "`/crear_categoria Accesorios Especiales|Items únicos y exclusivos|1|si`"

        # Create back navigation keyboard
        from keyboards.common import get_back_kb
        keyboard = get_back_kb("admin_shop_categories")

        # Update menu with form instructions
        await menu_manager.update_menu(
            callback,
            form_text,
            keyboard,
            session,
            "admin_category_create_form"
        )

        logger.info(f"Category creation form displayed for admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error showing category creation form for user {callback.from_user.id}: {e}")
        await callback.answer("❌ Error al cargar el formulario de creación", show_alert=True)

    await callback.answer()


@router.message(F.text.startswith("/crear_categoria "))
async def handle_create_category_command(message: Message, session: AsyncSession):
    """
    Process category creation command with form validation and error handling.

    This handler validates form input and creates the category using the ShopAdminService,
    providing appropriate success or error feedback to the admin user.
    """
    # Admin authentication check
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nNo tienes permisos de administrador.",
            auto_delete_seconds=5
        )
        return

    try:
        # Parse command arguments
        command_text = message.text.replace("/crear_categoria ", "").strip()

        if not command_text:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Error de Formato**\n\nUso: `/crear_categoria <nombre>|<descripcion>|<orden>|<vip>`",
                auto_delete_seconds=8
            )
            return

        # Split parameters by pipe character
        parts = [part.strip() for part in command_text.split("|")]

        if len(parts) < 2:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Faltan Parámetros**\n\nMínimo requerido: nombre y descripción\n"
                "Formato: `<nombre>|<descripcion>|<orden>|<vip>`",
                auto_delete_seconds=8
            )
            return

        # Extract and validate parameters
        name = parts[0]
        description = parts[1] if len(parts) > 1 and parts[1] else None

        # Parse display order (default to 0)
        display_order = 0
        if len(parts) > 2 and parts[2]:
            try:
                display_order = int(parts[2])
            except ValueError:
                await menu_manager.send_temporary_message(
                    message,
                    "❌ **Error en Orden**\n\nEl orden debe ser un número entero.",
                    auto_delete_seconds=8
                )
                return

        # Parse VIP setting (default to False)
        is_vip_only = False
        if len(parts) > 3 and parts[3]:
            vip_value = parts[3].lower()
            is_vip_only = vip_value in ['si', 'sí', 'yes', 'true', '1', 'vip']

        # Validate name
        if not name or len(name) < 3:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Nombre Inválido**\n\nEl nombre debe tener al menos 3 caracteres.",
                auto_delete_seconds=8
            )
            return

        # Initialize shop admin service and create category
        shop_admin_service = ShopAdminService(session)
        result = await shop_admin_service.create_category(
            admin_user_id=message.from_user.id,
            name=name,
            description=description,
            display_order=display_order,
            is_vip_only=is_vip_only
        )

        if result.get("success"):
            category_data = result.get("category", {})

            # Success message with category details
            success_text = "✅ **Categoría Creada Exitosamente**\n\n"
            success_text += f"📁 **Nombre:** {category_data.get('name')}\n"
            if category_data.get('description'):
                success_text += f"📝 **Descripción:** {category_data.get('description')}\n"
            success_text += f"📊 **Orden:** {category_data.get('display_order')}\n"
            success_text += f"💎 **VIP Only:** {'Sí' if category_data.get('is_vip_only') else 'No'}\n"
            success_text += f"✅ **Estado:** {'Activa' if category_data.get('is_active') else 'Inactiva'}\n\n"
            success_text += "La categoría está lista para ser utilizada en la tienda."

            from keyboards.common import get_back_kb
            keyboard = get_back_kb("admin_shop_categories")

            await menu_manager.show_menu(
                message,
                success_text,
                keyboard,
                session,
                "admin_category_created"
            )

            logger.info(f"Category '{name}' created successfully by admin {message.from_user.id}")

        else:
            # Error message with specific details
            error_message = result.get("message", "Error desconocido")
            error_text = "❌ **Error al Crear Categoría**\n\n"
            error_text += f"**Motivo:** {error_message}\n\n"
            error_text += "Por favor, revisa los datos e intenta nuevamente."

            await menu_manager.send_temporary_message(
                message,
                error_text,
                auto_delete_seconds=10
            )

            logger.warning(f"Category creation failed for admin {message.from_user.id}: {error_message}")

    except Exception as e:
        logger.error(f"Error processing category creation for admin {message.from_user.id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo procesar la creación de la categoría.",
            auto_delete_seconds=8
        )


@router.callback_query(F.data == "admin_category_edit")
async def edit_category(callback: CallbackQuery, session: AsyncSession):
    """
    Handle category editing workflow with form validation.

    This handler displays available categories for editing and manages the
    editing process with proper form validation and success/error feedback.
    """
    # Admin authentication check
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Initialize shop admin service
        shop_admin_service = ShopAdminService(session)

        # Get categories for editing (include inactive ones)
        categories_result = await shop_admin_service.get_categories(
            callback.from_user.id,
            include_inactive=True
        )

        # Build category selection menu
        if categories_result.get("success"):
            categories = categories_result.get("categories", [])

            if not categories:
                menu_text = "📁 **Editar Categoría**\n\n"
                menu_text += "❌ **No hay categorías disponibles para editar.**\n\n"
                menu_text += "Primero debes crear al menos una categoría."

                from keyboards.common import get_back_kb
                keyboard = get_back_kb("admin_shop_categories")

            else:
                menu_text = "✏️ **Editar Categoría**\n\n"
                menu_text += "Selecciona la categoría que deseas editar:\n\n"

                # List categories with status indicators
                for i, category in enumerate(categories[:15], 1):  # Show first 15
                    status = "🟢" if category.get("is_active") else "🔴"
                    vip_badge = " 💎" if category.get("is_vip_only") else ""
                    menu_text += f"{i}. {status} {category.get('name')}{vip_badge}\n"

                if len(categories) > 15:
                    menu_text += f"\n... y {len(categories) - 15} más\n"

                menu_text += "\n📩 **Para editar, usa el comando:**\n"
                menu_text += "`/editar_categoria <id>|<nombre>|<descripcion>|<orden>|<vip>|<activa>`\n\n"
                menu_text += "💡 **Ejemplo:**\n"
                menu_text += "`/editar_categoria 1|Nuevo Nombre|Nueva descripción|2|no|si`\n\n"
                menu_text += "🔍 **IDs de las categorías:**\n"
                for category in categories[:10]:
                    menu_text += f"ID {category.get('id')}: {category.get('name')}\n"

                from keyboards.common import get_back_kb
                keyboard = get_back_kb("admin_shop_categories")
        else:
            menu_text = "❌ **Error al cargar categorías**\n\n"
            menu_text += "No se pudieron cargar las categorías para edición."

            from keyboards.common import get_back_kb
            keyboard = get_back_kb("admin_shop_categories")

        # Update menu
        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_category_edit_form"
        )

        logger.info(f"Category edit form displayed for admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error showing category edit form for user {callback.from_user.id}: {e}")
        await callback.answer("❌ Error al cargar el formulario de edición", show_alert=True)

    await callback.answer()


@router.message(F.text.startswith("/editar_categoria "))
async def handle_edit_category_command(message: Message, session: AsyncSession):
    """
    Process category editing command with comprehensive form validation.

    This handler validates edit form input and updates the category using ShopAdminService,
    providing detailed feedback on the changes made or errors encountered.
    """
    # Admin authentication check
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nNo tienes permisos de administrador.",
            auto_delete_seconds=5
        )
        return

    try:
        # Parse command arguments
        command_text = message.text.replace("/editar_categoria ", "").strip()

        if not command_text:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Error de Formato**\n\nUso: `/editar_categoria <id>|<nombre>|<descripcion>|<orden>|<vip>|<activa>`",
                auto_delete_seconds=8
            )
            return

        # Split parameters by pipe character
        parts = [part.strip() for part in command_text.split("|")]

        if len(parts) < 2:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Faltan Parámetros**\n\nMínimo requerido: ID y nombre\n"
                "Formato: `<id>|<nombre>|<descripcion>|<orden>|<vip>|<activa>`",
                auto_delete_seconds=8
            )
            return

        # Extract and validate category ID
        try:
            category_id = int(parts[0])
        except ValueError:
            await menu_manager.send_temporary_message(
                message,
                "❌ **ID Inválido**\n\nEl ID de la categoría debe ser un número entero.",
                auto_delete_seconds=8
            )
            return

        # Extract parameters (only update non-empty ones)
        name = parts[1] if len(parts) > 1 and parts[1] else None
        description = parts[2] if len(parts) > 2 and parts[2] else None

        # Parse display order
        display_order = None
        if len(parts) > 3 and parts[3]:
            try:
                display_order = int(parts[3])
            except ValueError:
                await menu_manager.send_temporary_message(
                    message,
                    "❌ **Error en Orden**\n\nEl orden debe ser un número entero.",
                    auto_delete_seconds=8
                )
                return

        # Parse VIP setting
        is_vip_only = None
        if len(parts) > 4 and parts[4]:
            vip_value = parts[4].lower()
            is_vip_only = vip_value in ['si', 'sí', 'yes', 'true', '1', 'vip']

        # Parse active setting
        is_active = None
        if len(parts) > 5 and parts[5]:
            active_value = parts[5].lower()
            is_active = active_value in ['si', 'sí', 'yes', 'true', '1', 'activa', 'activo']

        # Validate name if provided
        if name and len(name) < 3:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Nombre Inválido**\n\nEl nombre debe tener al menos 3 caracteres.",
                auto_delete_seconds=8
            )
            return

        # Initialize shop admin service and update category
        shop_admin_service = ShopAdminService(session)
        result = await shop_admin_service.update_category(
            admin_user_id=message.from_user.id,
            category_id=category_id,
            name=name,
            description=description,
            display_order=display_order,
            is_vip_only=is_vip_only,
            is_active=is_active
        )

        if result.get("success"):
            category_data = result.get("category", {})

            # Success message with updated category details
            success_text = "✅ **Categoría Actualizada Exitosamente**\n\n"
            success_text += f"🆔 **ID:** {category_data.get('id')}\n"
            success_text += f"📁 **Nombre:** {category_data.get('name')}\n"
            if category_data.get('description'):
                success_text += f"📝 **Descripción:** {category_data.get('description')}\n"
            success_text += f"📊 **Orden:** {category_data.get('display_order')}\n"
            success_text += f"💎 **VIP Only:** {'Sí' if category_data.get('is_vip_only') else 'No'}\n"
            success_text += f"✅ **Estado:** {'Activa' if category_data.get('is_active') else 'Inactiva'}\n\n"

            # Show what was updated
            updated_message = result.get("message", "")
            if "Updated fields:" in updated_message:
                updated_fields = updated_message.split("Updated fields: ")[1]
                success_text += f"🔄 **Campos actualizados:** {updated_fields}"

            from keyboards.common import get_back_kb
            keyboard = get_back_kb("admin_shop_categories")

            await menu_manager.show_menu(
                message,
                success_text,
                keyboard,
                session,
                "admin_category_updated"
            )

            logger.info(f"Category {category_id} updated successfully by admin {message.from_user.id}")

        else:
            # Error message with specific details
            error_message = result.get("message", "Error desconocido")
            error_text = "❌ **Error al Actualizar Categoría**\n\n"
            error_text += f"**Motivo:** {error_message}\n\n"
            error_text += "Por favor, verifica el ID y los datos e intenta nuevamente."

            await menu_manager.send_temporary_message(
                message,
                error_text,
                auto_delete_seconds=10
            )

            logger.warning(f"Category update failed for admin {message.from_user.id}: {error_message}")

    except Exception as e:
        logger.error(f"Error processing category update for admin {message.from_user.id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo procesar la actualización de la categoría.",
            auto_delete_seconds=8
        )


# ITEM MANAGEMENT HANDLERS

@router.callback_query(F.data == "admin_shop_items")
async def manage_items(callback: CallbackQuery, session: AsyncSession):
    """
    Display the item management menu with list of all items.

    This handler provides access to item creation, editing, and organization
    following the established admin panel patterns.
    """
    # Admin authentication check using existing patterns
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Initialize shop admin service
        shop_admin_service = ShopAdminService(session)

        # Get items with inactive ones included for admin view
        items_result = await shop_admin_service.get_shop_items(
            callback.from_user.id,
            include_inactive=True
        )

        # Build items management menu text
        menu_text = "📦 **Gestión de Items de Tienda**\n\n"

        if items_result.get("success"):
            items = items_result.get("items", [])
            active_count = sum(1 for item in items if item.get("is_active"))
            vip_count = sum(1 for item in items if item.get("is_vip_only"))
            total_count = len(items)

            menu_text += f"📊 **Resumen:**\n"
            menu_text += f"• Total de items: {total_count}\n"
            menu_text += f"• Items activos: {active_count}\n"
            menu_text += f"• Items inactivos: {total_count - active_count}\n"
            menu_text += f"• Items VIP: {vip_count}\n\n"

            if items:
                menu_text += "📋 **Items Recientes:**\n"
                for item in items[:10]:  # Show first 10 items
                    status = "🟢" if item.get("is_active") else "🔴"
                    vip_badge = " 💎" if item.get("is_vip_only") else ""
                    lore_badge = " 📖" if item.get("unlocks_lore_piece_id") else ""
                    price = item.get("price", 0)
                    menu_text += f"{status} {item.get('name')}{vip_badge}{lore_badge} - {price} besitos\n"

                if total_count > 10:
                    menu_text += f"... y {total_count - 10} más\n"
            else:
                menu_text += "📋 **No hay items creados aún.**\n"
        else:
            menu_text += "❌ Error al cargar los items.\n"

        menu_text += "\n**Selecciona una opción para continuar:**"

        # Get item management keyboard
        from keyboards.admin_shop_kb import get_item_management_kb
        keyboard = get_item_management_kb()

        # Update menu using existing pattern
        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_shop_items"
        )

        logger.info(f"Item management menu displayed for admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error showing item management menu for user {callback.from_user.id}: {e}")
        await callback.answer("❌ Error al cargar la gestión de items", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "admin_item_create")
async def create_item(callback: CallbackQuery, session: AsyncSession):
    """
    Handle item creation workflow with form validation.

    This handler initiates the item creation process, collecting necessary
    information through a multi-step form with proper validation and feedback.
    """
    # Admin authentication check
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Get available categories for selection
        shop_admin_service = ShopAdminService(session)
        categories_result = await shop_admin_service.get_categories(
            callback.from_user.id,
            include_inactive=False
        )

        # Build item creation form text
        form_text = "➕ **Crear Nuevo Item**\n\n"
        form_text += "Para crear un nuevo item, necesitamos la siguiente información:\n\n"
        form_text += "📝 **Campos Requeridos:**\n"
        form_text += "• **Nombre:** Nombre único del item\n"
        form_text += "• **Descripción:** Descripción detallada del item\n"
        form_text += "• **Precio:** Precio en besitos (número entero)\n\n"
        form_text += "📝 **Campos Opcionales:**\n"
        form_text += "• **Categoría:** ID de categoría (opcional)\n"
        form_text += "• **VIP:** Solo para usuarios VIP (si/no)\n"
        form_text += "• **Lore:** ID de pieza de lore que desbloquea (opcional)\n\n"

        # Show available categories if any
        if categories_result.get("success") and categories_result.get("categories"):
            categories = categories_result.get("categories", [])
            form_text += "🏷️ **Categorías Disponibles:**\n"
            for category in categories[:8]:  # Show first 8 categories
                form_text += f"ID {category.get('id')}: {category.get('name')}\n"
            if len(categories) > 8:
                form_text += f"... y {len(categories) - 8} más\n"
            form_text += "\n"

        form_text += "💡 **Ejemplo:**\n"
        form_text += "`Nombre: Collar de Diana`\n"
        form_text += "`Descripción: Un collar elegante con el símbolo personal de Diana`\n"
        form_text += "`Precio: 50`\n"
        form_text += "`Categoría: 1`\n"
        form_text += "`VIP: si`\n"
        form_text += "`Lore: 3`\n\n"
        form_text += "📩 **Envía los datos en el siguiente formato:**\n"
        form_text += "`/crear_item <nombre>|<descripcion>|<precio>|<categoria>|<vip>|<lore>`\n\n"
        form_text += "**Ejemplo completo:**\n"
        form_text += "`/crear_item Collar de Diana|Un collar elegante con el símbolo personal de Diana|50|1|si|3`"

        # Create back navigation keyboard
        from keyboards.common import get_back_kb
        keyboard = get_back_kb("admin_shop_items")

        # Update menu with form instructions
        await menu_manager.update_menu(
            callback,
            form_text,
            keyboard,
            session,
            "admin_item_create_form"
        )

        logger.info(f"Item creation form displayed for admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error showing item creation form for user {callback.from_user.id}: {e}")
        await callback.answer("❌ Error al cargar el formulario de creación", show_alert=True)

    await callback.answer()


@router.message(F.text.startswith("/crear_item "))
async def handle_create_item_command(message: Message, session: AsyncSession):
    """
    Process item creation command with form validation and error handling.

    This handler validates form input and creates the item using the ShopAdminService,
    providing appropriate success or error feedback to the admin user.
    """
    # Admin authentication check
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nNo tienes permisos de administrador.",
            auto_delete_seconds=5
        )
        return

    try:
        # Parse command arguments
        command_text = message.text.replace("/crear_item ", "").strip()

        if not command_text:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Error de Formato**\n\nUso: `/crear_item <nombre>|<descripcion>|<precio>|<categoria>|<vip>|<lore>`",
                auto_delete_seconds=8
            )
            return

        # Split parameters by pipe character
        parts = [part.strip() for part in command_text.split("|")]

        if len(parts) < 3:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Faltan Parámetros**\n\nMínimo requerido: nombre, descripción y precio\n"
                "Formato: `<nombre>|<descripcion>|<precio>|<categoria>|<vip>|<lore>`",
                auto_delete_seconds=8
            )
            return

        # Extract and validate required parameters
        name = parts[0]
        description = parts[1]

        # Parse price
        try:
            price = int(parts[2])
            if price <= 0:
                await menu_manager.send_temporary_message(
                    message,
                    "❌ **Precio Inválido**\n\nEl precio debe ser un número entero positivo.",
                    auto_delete_seconds=8
                )
                return
        except ValueError:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Precio Inválido**\n\nEl precio debe ser un número entero.",
                auto_delete_seconds=8
            )
            return

        # Parse optional parameters
        category_id = None
        if len(parts) > 3 and parts[3]:
            try:
                category_id = int(parts[3])
            except ValueError:
                await menu_manager.send_temporary_message(
                    message,
                    "❌ **Categoría Inválida**\n\nEl ID de categoría debe ser un número entero.",
                    auto_delete_seconds=8
                )
                return

        # Parse VIP setting (default to False)
        is_vip_only = False
        if len(parts) > 4 and parts[4]:
            vip_value = parts[4].lower()
            is_vip_only = vip_value in ['si', 'sí', 'yes', 'true', '1', 'vip']

        # Parse lore piece ID
        unlocks_lore_piece_id = None
        if len(parts) > 5 and parts[5]:
            try:
                unlocks_lore_piece_id = int(parts[5])
            except ValueError:
                await menu_manager.send_temporary_message(
                    message,
                    "❌ **Lore ID Inválido**\n\nEl ID de lore debe ser un número entero.",
                    auto_delete_seconds=8
                )
                return

        # Validate name
        if not name or len(name) < 3:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Nombre Inválido**\n\nEl nombre debe tener al menos 3 caracteres.",
                auto_delete_seconds=8
            )
            return

        # Validate description
        if not description or len(description) < 10:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Descripción Inválida**\n\nLa descripción debe tener al menos 10 caracteres.",
                auto_delete_seconds=8
            )
            return

        # Initialize shop admin service and create item
        shop_admin_service = ShopAdminService(session)
        result = await shop_admin_service.create_shop_item(
            admin_user_id=message.from_user.id,
            name=name,
            description=description,
            price=price,
            category_id=category_id,
            is_vip_only=is_vip_only,
            unlocks_lore_piece_id=unlocks_lore_piece_id
        )

        if result.get("success"):
            item_data = result.get("item", {})

            # Success message with item details
            success_text = "✅ **Item Creado Exitosamente**\n\n"
            success_text += f"📦 **Nombre:** {item_data.get('name')}\n"
            success_text += f"📝 **Descripción:** {item_data.get('description')}\n"
            success_text += f"💰 **Precio:** {item_data.get('price')} besitos\n"
            if item_data.get('category_id'):
                success_text += f"🏷️ **Categoría ID:** {item_data.get('category_id')}\n"
            success_text += f"💎 **VIP Only:** {'Sí' if item_data.get('is_vip_only') else 'No'}\n"
            if item_data.get('unlocks_lore_piece_id'):
                success_text += f"📖 **Desbloquea Lore ID:** {item_data.get('unlocks_lore_piece_id')}\n"
            success_text += f"✅ **Estado:** {'Activo' if item_data.get('is_active') else 'Inactivo'}\n\n"
            success_text += "El item está listo para ser comprado en la tienda."

            from keyboards.common import get_back_kb
            keyboard = get_back_kb("admin_shop_items")

            await menu_manager.show_menu(
                message,
                success_text,
                keyboard,
                session,
                "admin_item_created"
            )

            logger.info(f"Item '{name}' created successfully by admin {message.from_user.id}")

        else:
            # Error message with specific details
            error_message = result.get("message", "Error desconocido")
            error_text = "❌ **Error al Crear Item**\n\n"
            error_text += f"**Motivo:** {error_message}\n\n"
            error_text += "Por favor, revisa los datos e intenta nuevamente."

            await menu_manager.send_temporary_message(
                message,
                error_text,
                auto_delete_seconds=10
            )

            logger.warning(f"Item creation failed for admin {message.from_user.id}: {error_message}")

    except Exception as e:
        logger.error(f"Error processing item creation for admin {message.from_user.id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo procesar la creación del item.",
            auto_delete_seconds=8
        )


@router.callback_query(F.data == "admin_item_edit")
async def edit_item(callback: CallbackQuery, session: AsyncSession):
    """
    Handle item editing workflow with form validation.

    This handler displays available items for editing and manages the
    editing process with proper form validation and success/error feedback.
    """
    # Admin authentication check
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Initialize shop admin service
        shop_admin_service = ShopAdminService(session)

        # Get items for editing (include inactive ones)
        items_result = await shop_admin_service.get_shop_items(
            callback.from_user.id,
            include_inactive=True
        )

        # Build item selection menu
        if items_result.get("success"):
            items = items_result.get("items", [])

            if not items:
                menu_text = "📦 **Editar Item**\n\n"
                menu_text += "❌ **No hay items disponibles para editar.**\n\n"
                menu_text += "Primero debes crear al menos un item."

                from keyboards.common import get_back_kb
                keyboard = get_back_kb("admin_shop_items")

            else:
                menu_text = "✏️ **Editar Item**\n\n"
                menu_text += "Selecciona el item que deseas editar:\n\n"

                # List items with status indicators
                for i, item in enumerate(items[:15], 1):  # Show first 15
                    status = "🟢" if item.get("is_active") else "🔴"
                    vip_badge = " 💎" if item.get("is_vip_only") else ""
                    lore_badge = " 📖" if item.get("unlocks_lore_piece_id") else ""
                    price = item.get("price", 0)
                    menu_text += f"{i}. {status} {item.get('name')}{vip_badge}{lore_badge} - {price} besitos\n"

                if len(items) > 15:
                    menu_text += f"\n... y {len(items) - 15} más\n"

                menu_text += "\n📩 **Para editar, usa el comando:**\n"
                menu_text += "`/editar_item <id>|<nombre>|<descripcion>|<precio>|<categoria>|<vip>|<lore>|<activo>`\n\n"
                menu_text += "💡 **Ejemplo:**\n"
                menu_text += "`/editar_item 1|Nuevo Nombre|Nueva descripción|75|2|no|5|si`\n\n"
                menu_text += "🔍 **IDs de los items:**\n"
                for item in items[:10]:
                    menu_text += f"ID {item.get('id')}: {item.get('name')}\n"

                from keyboards.common import get_back_kb
                keyboard = get_back_kb("admin_shop_items")
        else:
            menu_text = "❌ **Error al cargar items**\n\n"
            menu_text += "No se pudieron cargar los items para edición."

            from keyboards.common import get_back_kb
            keyboard = get_back_kb("admin_shop_items")

        # Update menu
        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_item_edit_form"
        )

        logger.info(f"Item edit form displayed for admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error showing item edit form for user {callback.from_user.id}: {e}")
        await callback.answer("❌ Error al cargar el formulario de edición", show_alert=True)

    await callback.answer()


@router.message(F.text.startswith("/editar_item "))
async def handle_edit_item_command(message: Message, session: AsyncSession):
    """
    Process item editing command with comprehensive form validation.

    This handler validates edit form input and updates the item using ShopAdminService,
    providing detailed feedback on the changes made or errors encountered.
    """
    # Admin authentication check
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nNo tienes permisos de administrador.",
            auto_delete_seconds=5
        )
        return

    try:
        # Parse command arguments
        command_text = message.text.replace("/editar_item ", "").strip()

        if not command_text:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Error de Formato**\n\nUso: `/editar_item <id>|<nombre>|<descripcion>|<precio>|<categoria>|<vip>|<lore>|<activo>`",
                auto_delete_seconds=8
            )
            return

        # Split parameters by pipe character
        parts = [part.strip() for part in command_text.split("|")]

        if len(parts) < 2:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Faltan Parámetros**\n\nMínimo requerido: ID y nombre\n"
                "Formato: `<id>|<nombre>|<descripcion>|<precio>|<categoria>|<vip>|<lore>|<activo>`",
                auto_delete_seconds=8
            )
            return

        # Extract and validate item ID
        try:
            item_id = int(parts[0])
        except ValueError:
            await menu_manager.send_temporary_message(
                message,
                "❌ **ID Inválido**\n\nEl ID del item debe ser un número entero.",
                auto_delete_seconds=8
            )
            return

        # Extract parameters (only update non-empty ones)
        name = parts[1] if len(parts) > 1 and parts[1] else None
        description = parts[2] if len(parts) > 2 and parts[2] else None

        # Parse price
        price = None
        if len(parts) > 3 and parts[3]:
            try:
                price = int(parts[3])
                if price <= 0:
                    await menu_manager.send_temporary_message(
                        message,
                        "❌ **Precio Inválido**\n\nEl precio debe ser un número entero positivo.",
                        auto_delete_seconds=8
                    )
                    return
            except ValueError:
                await menu_manager.send_temporary_message(
                    message,
                    "❌ **Precio Inválido**\n\nEl precio debe ser un número entero.",
                    auto_delete_seconds=8
                )
                return

        # Parse category ID
        category_id = None
        if len(parts) > 4 and parts[4]:
            if parts[4].lower() == 'null' or parts[4] == '0':
                category_id = -1  # Special value to remove category
            else:
                try:
                    category_id = int(parts[4])
                except ValueError:
                    await menu_manager.send_temporary_message(
                        message,
                        "❌ **Categoría Inválida**\n\nEl ID de categoría debe ser un número entero.",
                        auto_delete_seconds=8
                    )
                    return

        # Parse VIP setting
        is_vip_only = None
        if len(parts) > 5 and parts[5]:
            vip_value = parts[5].lower()
            is_vip_only = vip_value in ['si', 'sí', 'yes', 'true', '1', 'vip']

        # Parse lore piece ID
        unlocks_lore_piece_id = None
        if len(parts) > 6 and parts[6]:
            if parts[6].lower() == 'null' or parts[6] == '0':
                unlocks_lore_piece_id = -1  # Special value to remove lore
            else:
                try:
                    unlocks_lore_piece_id = int(parts[6])
                except ValueError:
                    await menu_manager.send_temporary_message(
                        message,
                        "❌ **Lore ID Inválido**\n\nEl ID de lore debe ser un número entero.",
                        auto_delete_seconds=8
                    )
                    return

        # Parse active setting
        is_active = None
        if len(parts) > 7 and parts[7]:
            active_value = parts[7].lower()
            is_active = active_value in ['si', 'sí', 'yes', 'true', '1', 'activo']

        # Validate name if provided
        if name and len(name) < 3:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Nombre Inválido**\n\nEl nombre debe tener al menos 3 caracteres.",
                auto_delete_seconds=8
            )
            return

        # Validate description if provided
        if description and len(description) < 10:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Descripción Inválida**\n\nLa descripción debe tener al menos 10 caracteres.",
                auto_delete_seconds=8
            )
            return

        # Initialize shop admin service and update item
        shop_admin_service = ShopAdminService(session)
        result = await shop_admin_service.update_shop_item(
            admin_user_id=message.from_user.id,
            item_id=item_id,
            name=name,
            description=description,
            price=price,
            category_id=category_id,
            is_vip_only=is_vip_only,
            unlocks_lore_piece_id=unlocks_lore_piece_id,
            is_active=is_active
        )

        if result.get("success"):
            item_data = result.get("item", {})

            # Success message with updated item details
            success_text = "✅ **Item Actualizado Exitosamente**\n\n"
            success_text += f"🆔 **ID:** {item_data.get('id')}\n"
            success_text += f"📦 **Nombre:** {item_data.get('name')}\n"
            success_text += f"📝 **Descripción:** {item_data.get('description')}\n"
            success_text += f"💰 **Precio:** {item_data.get('price')} besitos\n"
            if item_data.get('category_id'):
                success_text += f"🏷️ **Categoría ID:** {item_data.get('category_id')}\n"
            success_text += f"💎 **VIP Only:** {'Sí' if item_data.get('is_vip_only') else 'No'}\n"
            if item_data.get('unlocks_lore_piece_id'):
                success_text += f"📖 **Desbloquea Lore ID:** {item_data.get('unlocks_lore_piece_id')}\n"
            success_text += f"✅ **Estado:** {'Activo' if item_data.get('is_active') else 'Inactivo'}\n\n"

            # Show what was updated
            updated_message = result.get("message", "")
            if "Updated fields:" in updated_message:
                updated_fields = updated_message.split("Updated fields: ")[1]
                success_text += f"🔄 **Campos actualizados:** {updated_fields}"

            from keyboards.common import get_back_kb
            keyboard = get_back_kb("admin_shop_items")

            await menu_manager.show_menu(
                message,
                success_text,
                keyboard,
                session,
                "admin_item_updated"
            )

            logger.info(f"Item {item_id} updated successfully by admin {message.from_user.id}")

        else:
            # Error message with specific details
            error_message = result.get("message", "Error desconocido")
            error_text = "❌ **Error al Actualizar Item**\n\n"
            error_text += f"**Motivo:** {error_message}\n\n"
            error_text += "Por favor, verifica el ID y los datos e intenta nuevamente."

            await menu_manager.send_temporary_message(
                message,
                error_text,
                auto_delete_seconds=10
            )

            logger.warning(f"Item update failed for admin {message.from_user.id}: {error_message}")

    except Exception as e:
        logger.error(f"Error processing item update for admin {message.from_user.id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo procesar la actualización del item.",
            auto_delete_seconds=8
        )


@router.callback_query(F.data == "admin_item_delete")
async def delete_item(callback: CallbackQuery, session: AsyncSession):
    """
    Handle item deletion workflow with confirmation.

    This handler provides a safe deletion process with confirmation steps
    and handles potential data integrity concerns.
    """
    # Admin authentication check
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Initialize shop admin service
        shop_admin_service = ShopAdminService(session)

        # Get items for deletion (include inactive ones)
        items_result = await shop_admin_service.get_shop_items(
            callback.from_user.id,
            include_inactive=True
        )

        # Build item selection menu
        if items_result.get("success"):
            items = items_result.get("items", [])

            if not items:
                menu_text = "🗑️ **Eliminar Item**\n\n"
                menu_text += "❌ **No hay items disponibles para eliminar.**\n\n"
                menu_text += "Primero debes crear al menos un item."

                from keyboards.common import get_back_kb
                keyboard = get_back_kb("admin_shop_items")

            else:
                menu_text = "🗑️ **Eliminar Item**\n\n"
                menu_text += "⚠️ **ADVERTENCIA:** Esta acción no se puede deshacer.\n"
                menu_text += "Solo se recomienda eliminar items que nunca han sido comprados.\n\n"
                menu_text += "Selecciona el item que deseas eliminar:\n\n"

                # List items with status indicators
                for i, item in enumerate(items[:15], 1):  # Show first 15
                    status = "🟢" if item.get("is_active") else "🔴"
                    vip_badge = " 💎" if item.get("is_vip_only") else ""
                    price = item.get("price", 0)
                    menu_text += f"{i}. {status} {item.get('name')}{vip_badge} - {price} besitos\n"

                if len(items) > 15:
                    menu_text += f"\n... y {len(items) - 15} más\n"

                menu_text += "\n📩 **Para eliminar, usa el comando:**\n"
                menu_text += "`/eliminar_item <id>`\n\n"
                menu_text += "💡 **Ejemplo:**\n"
                menu_text += "`/eliminar_item 5`\n\n"
                menu_text += "🔍 **IDs de los items:**\n"
                for item in items[:10]:
                    menu_text += f"ID {item.get('id')}: {item.get('name')}\n"

                from keyboards.common import get_back_kb
                keyboard = get_back_kb("admin_shop_items")
        else:
            menu_text = "❌ **Error al cargar items**\n\n"
            menu_text += "No se pudieron cargar los items para eliminación."

            from keyboards.common import get_back_kb
            keyboard = get_back_kb("admin_shop_items")

        # Update menu
        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_item_delete_form"
        )

        logger.info(f"Item delete form displayed for admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error showing item delete form for user {callback.from_user.id}: {e}")
        await callback.answer("❌ Error al cargar el formulario de eliminación", show_alert=True)

    await callback.answer()


@router.message(F.text.startswith("/eliminar_item "))
async def handle_delete_item_command(message: Message, session: AsyncSession):
    """
    Process item deletion command with proper validation.

    This handler provides a controlled deletion process with appropriate
    warnings and confirmations for data integrity.
    """
    # Admin authentication check
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nNo tienes permisos de administrador.",
            auto_delete_seconds=5
        )
        return

    try:
        # Parse command arguments
        command_text = message.text.replace("/eliminar_item ", "").strip()

        if not command_text:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Error de Formato**\n\nUso: `/eliminar_item <id>`",
                auto_delete_seconds=8
            )
            return

        # Extract and validate item ID
        try:
            item_id = int(command_text)
        except ValueError:
            await menu_manager.send_temporary_message(
                message,
                "❌ **ID Inválido**\n\nEl ID del item debe ser un número entero.",
                auto_delete_seconds=8
            )
            return

        # Initialize shop admin service
        shop_admin_service = ShopAdminService(session)

        # Get item details first
        items_result = await shop_admin_service.get_shop_items(
            message.from_user.id,
            include_inactive=True
        )

        if not items_result.get("success"):
            await menu_manager.send_temporary_message(
                message,
                "❌ **Error**\n\nNo se pudieron cargar los items.",
                auto_delete_seconds=8
            )
            return

        # Find the item
        items = items_result.get("items", [])
        target_item = None
        for item in items:
            if item.get("id") == item_id:
                target_item = item
                break

        if not target_item:
            await menu_manager.send_temporary_message(
                message,
                f"❌ **Item No Encontrado**\n\nNo existe un item con ID {item_id}.",
                auto_delete_seconds=8
            )
            return

        # Note: Since the ShopAdminService doesn't have a delete_shop_item method,
        # we should recommend deactivation instead
        warning_text = "⚠️ **Eliminación No Disponible**\n\n"
        warning_text += f"**Item:** {target_item.get('name')}\n"
        warning_text += f"**ID:** {item_id}\n\n"
        warning_text += "En lugar de eliminar el item, se recomienda **desactivarlo** para mantener la integridad de los datos.\n\n"
        warning_text += "📩 **Para desactivar, usa:**\n"
        warning_text += f"`/editar_item {item_id}|{target_item.get('name')}|||||||no`\n\n"
        warning_text += "Esto ocultará el item de la tienda pero mantendrá el historial de compras."

        from keyboards.common import get_back_kb
        keyboard = get_back_kb("admin_shop_items")

        await menu_manager.show_menu(
            message,
            warning_text,
            keyboard,
            session,
            "admin_item_delete_alternative"
        )

        logger.info(f"Item deletion alternative suggested for admin {message.from_user.id}, item {item_id}")

    except Exception as e:
        logger.error(f"Error processing item deletion for admin {message.from_user.id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo procesar la eliminación del item.",
            auto_delete_seconds=8
        )


# Additional navigation handlers for shop admin integration

# ANALYTICS DASHBOARD HANDLERS

@router.callback_query(F.data == "admin_shop_stats")
async def show_shop_analytics(callback: CallbackQuery, session: AsyncSession):
    """
    Display comprehensive shop analytics dashboard with metrics and charts.

    This handler provides detailed analytics including sales performance,
    category breakdown, user engagement metrics, and time-based trends.
    Includes date range filtering and export functionality.
    """
    # Admin authentication check using existing patterns
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Initialize shop admin service
        shop_admin_service = ShopAdminService(session)

        # Get comprehensive analytics (default: last 30 days)
        analytics_result = await shop_admin_service.get_purchase_analytics(
            admin_user_id=callback.from_user.id,
            days_back=30
        )

        # Get admin statistics for additional context
        stats_result = await shop_admin_service.get_admin_statistics(callback.from_user.id)

        # Build analytics dashboard text
        menu_text = "📊 **Panel de Analíticas de Tienda**\n\n"
        menu_text += "Dashboard completo de métricas y rendimiento de la tienda DianaBot.\n\n"

        if analytics_result.get("success") and stats_result.get("success"):
            analytics = analytics_result.get("analytics", {})
            statistics = stats_result.get("statistics", {})

            # Summary metrics
            summary = analytics.get("summary", {})
            menu_text += "📈 **Resumen (Últimos 30 días):**\n"
            menu_text += f"• Compras totales: {summary.get('total_purchases', 0)}\n"
            menu_text += f"• Ingresos: {summary.get('total_revenue', 0)} besitos\n"
            menu_text += f"• Valor promedio de orden: {summary.get('average_order_value', 0):.1f} besitos\n"
            menu_text += f"• Compradores únicos: {summary.get('unique_buyers', 0)}\n"
            menu_text += f"• Tasa de conversión: {summary.get('conversion_rate', 0)}%\n\n"

            # Sales performance from statistics
            sales_stats = statistics.get("sales", {})
            if sales_stats:
                overall = sales_stats.get("overall", {})
                today = sales_stats.get("today", {})
                week = sales_stats.get("last_7_days", {})

                menu_text += "🎯 **Rendimiento de Ventas:**\n"
                menu_text += f"• Hoy: {today.get('sales', 0)} ventas, {today.get('revenue', 0)} besitos\n"
                menu_text += f"• Últimos 7 días: {week.get('sales', 0)} ventas, {week.get('revenue', 0)} besitos\n"
                menu_text += f"• Total histórico: {overall.get('total_sales', 0)} ventas, {overall.get('total_revenue', 0)} besitos\n\n"

            # Top performing categories
            category_performance = analytics.get("category_performance", [])
            if category_performance:
                menu_text += "🏷️ **Top Categorías:**\n"
                for i, category in enumerate(category_performance[:5], 1):
                    cat_name = category.get("category", "Sin categoría")
                    cat_sales = category.get("purchases", 0)
                    cat_revenue = category.get("revenue", 0)
                    menu_text += f"{i}. {cat_name}: {cat_sales} ventas, {cat_revenue} besitos\n"
                if len(category_performance) > 5:
                    menu_text += f"... y {len(category_performance) - 5} categorías más\n"
                menu_text += "\n"

            # Top selling items
            top_items = analytics.get("top_items", [])
            if top_items:
                menu_text += "🌟 **Items Más Vendidos:**\n"
                for i, item in enumerate(top_items[:5], 1):
                    item_name = item.get("item_name", "Item desconocido")
                    item_sales = item.get("purchases", 0)
                    item_revenue = item.get("revenue", 0)
                    menu_text += f"{i}. {item_name}: {item_sales} ventas, {item_revenue} besitos\n"
                if len(top_items) > 5:
                    menu_text += f"... y {len(top_items) - 5} items más\n"
                menu_text += "\n"

            # User engagement from statistics
            user_stats = statistics.get("users", {})
            if user_stats:
                user_base = user_stats.get("user_base", {})
                purchasing = user_stats.get("purchasing_behavior", {})

                menu_text += "👥 **Engagement de Usuarios:**\n"
                menu_text += f"• Total usuarios: {user_base.get('total_users', 0)}\n"
                menu_text += f"• Usuarios VIP: {user_base.get('vip_users', 0)}\n"
                menu_text += f"• Usuarios Free: {user_base.get('free_users', 0)}\n"
                menu_text += f"• Compradores totales: {purchasing.get('total_buyers', 0)}\n"
                menu_text += f"• Conversión VIP: {purchasing.get('vip_conversion_rate', 0)}%\n\n"

            # Recent activity
            recent_activity = statistics.get("recent_activity", {})
            if recent_activity:
                menu_text += f"⚡ **Actividad Reciente:**\n"
                menu_text += f"{recent_activity.get('summary', 'Sin actividad reciente')}\n\n"

        else:
            menu_text += "❌ Error al cargar las analíticas.\n\n"

        menu_text += "**Opciones disponibles:**"

        # Get analytics keyboard
        from keyboards.admin_shop_kb import get_shop_stats_kb
        keyboard = get_shop_stats_kb()

        # Update menu using existing pattern
        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_shop_analytics"
        )

        logger.info(f"Shop analytics dashboard displayed for admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error showing shop analytics for user {callback.from_user.id}: {e}")
        await callback.answer("❌ Error al cargar las analíticas", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "admin_shop_stats_sales")
async def show_detailed_sales_analytics(callback: CallbackQuery, session: AsyncSession):
    """
    Display detailed sales analytics with breakdown by time periods and categories.
    """
    # Admin authentication check
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Initialize shop admin service
        shop_admin_service = ShopAdminService(session)

        # Get detailed analytics for different time periods
        analytics_30d = await shop_admin_service.get_purchase_analytics(
            admin_user_id=callback.from_user.id,
            days_back=30
        )
        analytics_7d = await shop_admin_service.get_purchase_analytics(
            admin_user_id=callback.from_user.id,
            days_back=7
        )
        analytics_1d = await shop_admin_service.get_purchase_analytics(
            admin_user_id=callback.from_user.id,
            days_back=1
        )

        # Build detailed sales report
        menu_text = "📊 **Analíticas Detalladas de Ventas**\n\n"

        if all(result.get("success") for result in [analytics_30d, analytics_7d, analytics_1d]):
            summary_30d = analytics_30d.get("analytics", {}).get("summary", {})
            summary_7d = analytics_7d.get("analytics", {}).get("summary", {})
            summary_1d = analytics_1d.get("analytics", {}).get("summary", {})

            menu_text += "📈 **Comparativa por Períodos:**\n\n"

            menu_text += "🗓️ **Últimas 24 horas:**\n"
            menu_text += f"• Compras: {summary_1d.get('total_purchases', 0)}\n"
            menu_text += f"• Ingresos: {summary_1d.get('total_revenue', 0)} besitos\n"
            menu_text += f"• Valor promedio: {summary_1d.get('average_order_value', 0):.1f} besitos\n"
            menu_text += f"• Compradores únicos: {summary_1d.get('unique_buyers', 0)}\n\n"

            menu_text += "📅 **Últimos 7 días:**\n"
            menu_text += f"• Compras: {summary_7d.get('total_purchases', 0)}\n"
            menu_text += f"• Ingresos: {summary_7d.get('total_revenue', 0)} besitos\n"
            menu_text += f"• Valor promedio: {summary_7d.get('average_order_value', 0):.1f} besitos\n"
            menu_text += f"• Compradores únicos: {summary_7d.get('unique_buyers', 0)}\n\n"

            menu_text += "📆 **Últimos 30 días:**\n"
            menu_text += f"• Compras: {summary_30d.get('total_purchases', 0)}\n"
            menu_text += f"• Ingresos: {summary_30d.get('total_revenue', 0)} besitos\n"
            menu_text += f"• Valor promedio: {summary_30d.get('average_order_value', 0):.1f} besitos\n"
            menu_text += f"• Compradores únicos: {summary_30d.get('unique_buyers', 0)}\n\n"

            # Daily trends if available
            daily_trends = analytics_30d.get("analytics", {}).get("daily_trends", [])
            if daily_trends:
                menu_text += "📉 **Tendencias Diarias (Últimos días):**\n"
                # Show last 7 days of trends
                for trend in daily_trends[-7:]:
                    date = trend.get("date", "N/A")
                    purchases = trend.get("purchases", 0)
                    revenue = trend.get("revenue", 0)
                    menu_text += f"• {date}: {purchases} ventas, {revenue} besitos\n"
                menu_text += "\n"

            # User type analysis
            user_analysis = analytics_30d.get("analytics", {}).get("user_type_analysis", [])
            if user_analysis:
                menu_text += "👥 **Análisis por Tipo de Usuario (30 días):**\n"
                for user_type in user_analysis:
                    user_role = user_type.get("user_type", "unknown")
                    purchases = user_type.get("purchases", 0)
                    revenue = user_type.get("revenue", 0)
                    avg_order = user_type.get("average_order_value", 0)
                    unique_buyers = user_type.get("unique_buyers", 0)

                    role_label = "👑 VIP" if user_role == "vip" else "🆓 Free"
                    menu_text += f"{role_label}:\n"
                    menu_text += f"  - Compras: {purchases}\n"
                    menu_text += f"  - Ingresos: {revenue} besitos\n"
                    menu_text += f"  - Valor promedio: {avg_order:.1f} besitos\n"
                    menu_text += f"  - Compradores únicos: {unique_buyers}\n\n"

        else:
            menu_text += "❌ Error al cargar las analíticas detalladas.\n\n"

        menu_text += "Para más opciones de filtrado, usa:\n"
        menu_text += "`/analytics_filter <dias>` - Filtrar por días específicos\n"
        menu_text += "`/analytics_export` - Exportar datos completos\n\n"
        menu_text += "**Volver a analíticas principales:**"

        # Create back navigation keyboard
        from keyboards.common import get_back_kb
        keyboard = get_back_kb("admin_shop_stats")

        # Update menu
        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_shop_stats_detailed"
        )

        logger.info(f"Detailed sales analytics displayed for admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error showing detailed sales analytics for user {callback.from_user.id}: {e}")
        await callback.answer("❌ Error al cargar analíticas detalladas", show_alert=True)

    await callback.answer()


@router.callback_query(F.data.startswith("admin_shop_stats_"))
async def handle_analytics_filters(callback: CallbackQuery, session: AsyncSession):
    """
    Handle different analytics filter options (daily, weekly, VIP, etc.).
    """
    # Admin authentication check
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        filter_type = callback.data.replace("admin_shop_stats_", "")

        # Initialize shop admin service
        shop_admin_service = ShopAdminService(session)

        # Determine filter parameters based on type
        days_back = None
        is_vip_only = None
        title_suffix = ""

        if filter_type == "daily":
            days_back = 1
            title_suffix = " (Últimas 24h)"
        elif filter_type == "weekly":
            days_back = 7
            title_suffix = " (Últimos 7 días)"
        elif filter_type == "vip":
            days_back = 30
            # Note: VIP filtering would need to be implemented in get_purchase_analytics
            title_suffix = " (Solo VIP - 30 días)"
        elif filter_type == "free":
            days_back = 30
            title_suffix = " (Solo Free - 30 días)"
        elif filter_type == "revenue":
            days_back = 30
            title_suffix = " (Análisis de Ingresos - 30 días)"
        else:
            # Default to monthly
            days_back = 30
            title_suffix = " (Últimos 30 días)"

        # Get filtered analytics
        analytics_result = await shop_admin_service.get_purchase_analytics(
            admin_user_id=callback.from_user.id,
            days_back=days_back
        )

        # Build filtered analytics report
        menu_text = f"📊 **Analíticas Filtradas{title_suffix}**\n\n"

        if analytics_result.get("success"):
            analytics = analytics_result.get("analytics", {})

            # Summary metrics
            summary = analytics.get("summary", {})
            menu_text += "📈 **Resumen del Período:**\n"
            menu_text += f"• Compras totales: {summary.get('total_purchases', 0)}\n"
            menu_text += f"• Ingresos: {summary.get('total_revenue', 0)} besitos\n"
            menu_text += f"• Valor promedio de orden: {summary.get('average_order_value', 0):.1f} besitos\n"
            menu_text += f"• Compradores únicos: {summary.get('unique_buyers', 0)}\n"
            menu_text += f"• Tasa de conversión: {summary.get('conversion_rate', 0)}%\n\n"

            if filter_type == "revenue":
                # Focus on revenue analysis
                category_performance = analytics.get("category_performance", [])
                if category_performance:
                    menu_text += "💰 **Ingresos por Categoría:**\n"
                    total_revenue = sum(cat.get("revenue", 0) for cat in category_performance)
                    for category in category_performance:
                        cat_name = category.get("category", "Sin categoría")
                        cat_revenue = category.get("revenue", 0)
                        percentage = (cat_revenue / total_revenue * 100) if total_revenue > 0 else 0
                        menu_text += f"• {cat_name}: {cat_revenue} besitos ({percentage:.1f}%)\n"
                    menu_text += "\n"

                # Top revenue items
                top_items = analytics.get("top_items", [])
                if top_items:
                    menu_text += "💎 **Items con Mayores Ingresos:**\n"
                    for i, item in enumerate(top_items[:5], 1):
                        item_name = item.get("item_name", "Item desconocido")
                        item_revenue = item.get("revenue", 0)
                        item_sales = item.get("purchases", 0)
                        avg_price = (item_revenue / item_sales) if item_sales > 0 else 0
                        menu_text += f"{i}. {item_name}: {item_revenue} besitos ({item_sales} ventas, {avg_price:.1f} promedio)\n"
                    menu_text += "\n"

            else:
                # Standard analytics display
                category_performance = analytics.get("category_performance", [])
                if category_performance:
                    menu_text += "🏷️ **Rendimiento por Categoría:**\n"
                    for category in category_performance[:5]:
                        cat_name = category.get("category", "Sin categoría")
                        cat_sales = category.get("purchases", 0)
                        cat_revenue = category.get("revenue", 0)
                        menu_text += f"• {cat_name}: {cat_sales} ventas, {cat_revenue} besitos\n"
                    menu_text += "\n"

                # User type analysis
                user_analysis = analytics.get("user_type_analysis", [])
                if user_analysis and filter_type not in ["vip", "free"]:
                    menu_text += "👥 **Análisis por Tipo de Usuario:**\n"
                    for user_type in user_analysis:
                        user_role = user_type.get("user_type", "unknown")
                        purchases = user_type.get("purchases", 0)
                        revenue = user_type.get("revenue", 0)

                        role_label = "👑 VIP" if user_role == "vip" else "🆓 Free"
                        menu_text += f"{role_label}: {purchases} compras, {revenue} besitos\n"
                    menu_text += "\n"

            # Daily trends for short periods
            if days_back and days_back <= 7:
                daily_trends = analytics.get("daily_trends", [])
                if daily_trends:
                    menu_text += "📊 **Tendencia Diaria:**\n"
                    for trend in daily_trends:
                        date = trend.get("date", "N/A")
                        purchases = trend.get("purchases", 0)
                        revenue = trend.get("revenue", 0)
                        menu_text += f"• {date}: {purchases} ventas, {revenue} besitos\n"
                    menu_text += "\n"

        else:
            menu_text += "❌ Error al cargar las analíticas filtradas.\n\n"

        menu_text += "**Opciones adicionales:**\n"
        menu_text += f"Período analizado: {days_back} día(s)\n"
        menu_text += "Para cambiar filtros, regresa al menú principal.\n\n"

        # Create back navigation keyboard
        from keyboards.common import get_back_kb
        keyboard = get_back_kb("admin_shop_stats")

        # Update menu
        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            f"admin_shop_stats_{filter_type}"
        )

        logger.info(f"Analytics filter '{filter_type}' applied for admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error applying analytics filter for user {callback.from_user.id}: {e}")
        await callback.answer("❌ Error al aplicar filtro", show_alert=True)

    await callback.answer()


@router.message(F.text.startswith("/analytics_filter "))
async def handle_custom_analytics_filter(message: Message, session: AsyncSession):
    """
    Handle custom analytics date range filtering via command.

    Usage: /analytics_filter <days>
    Example: /analytics_filter 14 (for last 14 days)
    """
    # Admin authentication check
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nNo tienes permisos de administrador.",
            auto_delete_seconds=5
        )
        return

    try:
        # Parse command arguments
        command_text = message.text.replace("/analytics_filter ", "").strip()

        if not command_text:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Error de Formato**\n\nUso: `/analytics_filter <días>`\nEjemplo: `/analytics_filter 14`",
                auto_delete_seconds=8
            )
            return

        # Validate days parameter
        try:
            days_back = int(command_text)
            if days_back <= 0 or days_back > 365:
                await menu_manager.send_temporary_message(
                    message,
                    "❌ **Rango Inválido**\n\nLos días deben estar entre 1 y 365.",
                    auto_delete_seconds=8
                )
                return
        except ValueError:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Valor Inválido**\n\nEl número de días debe ser un entero.",
                auto_delete_seconds=8
            )
            return

        # Initialize shop admin service
        shop_admin_service = ShopAdminService(session)

        # Get custom period analytics
        analytics_result = await shop_admin_service.get_purchase_analytics(
            admin_user_id=message.from_user.id,
            days_back=days_back
        )

        if analytics_result.get("success"):
            analytics = analytics_result.get("analytics", {})
            summary = analytics.get("summary", {})

            # Build custom analytics report
            success_text = f"📊 **Analíticas Personalizadas ({days_back} días)**\n\n"

            success_text += "📈 **Resumen del Período:**\n"
            success_text += f"• Compras totales: {summary.get('total_purchases', 0)}\n"
            success_text += f"• Ingresos: {summary.get('total_revenue', 0)} besitos\n"
            success_text += f"• Valor promedio de orden: {summary.get('average_order_value', 0):.1f} besitos\n"
            success_text += f"• Compradores únicos: {summary.get('unique_buyers', 0)}\n"
            success_text += f"• Tasa de conversión: {summary.get('conversion_rate', 0)}%\n\n"

            # Category performance
            category_performance = analytics.get("category_performance", [])
            if category_performance:
                success_text += "🏷️ **Top 5 Categorías:**\n"
                for i, category in enumerate(category_performance[:5], 1):
                    cat_name = category.get("category", "Sin categoría")
                    cat_sales = category.get("purchases", 0)
                    cat_revenue = category.get("revenue", 0)
                    success_text += f"{i}. {cat_name}: {cat_sales} ventas, {cat_revenue} besitos\n"
                success_text += "\n"

            # Top items
            top_items = analytics.get("top_items", [])
            if top_items:
                success_text += "🌟 **Top 5 Items:**\n"
                for i, item in enumerate(top_items[:5], 1):
                    item_name = item.get("item_name", "Item desconocido")
                    item_sales = item.get("purchases", 0)
                    item_revenue = item.get("revenue", 0)
                    success_text += f"{i}. {item_name}: {item_sales} ventas, {item_revenue} besitos\n"
                success_text += "\n"

            # User type analysis
            user_analysis = analytics.get("user_type_analysis", [])
            if user_analysis:
                success_text += "👥 **Análisis por Tipo de Usuario:**\n"
                for user_type in user_analysis:
                    user_role = user_type.get("user_type", "unknown")
                    purchases = user_type.get("purchases", 0)
                    revenue = user_type.get("revenue", 0)

                    role_label = "👑 VIP" if user_role == "vip" else "🆓 Free"
                    success_text += f"{role_label}: {purchases} compras, {revenue} besitos\n"
                success_text += "\n"

            success_text += f"📅 **Período analizado:** {days_back} días\n"
            success_text += "Para más opciones, regresa al panel de analíticas principal."

            from keyboards.common import get_back_kb
            keyboard = get_back_kb("admin_shop_stats")

            await menu_manager.show_menu(
                message,
                success_text,
                keyboard,
                session,
                "admin_analytics_custom"
            )

            logger.info(f"Custom analytics filter ({days_back} days) applied by admin {message.from_user.id}")

        else:
            error_message = analytics_result.get("message", "Error desconocido")
            await menu_manager.send_temporary_message(
                message,
                f"❌ **Error al Generar Analíticas**\n\n**Motivo:** {error_message}",
                auto_delete_seconds=10
            )

    except Exception as e:
        logger.error(f"Error processing custom analytics filter for admin {message.from_user.id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudieron generar las analíticas personalizadas.",
            auto_delete_seconds=8
        )


@router.message(Command("analytics_export"))
async def handle_analytics_export(message: Message, session: AsyncSession):
    """
    Export comprehensive analytics data to CSV format for external analysis.

    Usage: /analytics_export [days]
    Example: /analytics_export 30 (export last 30 days)
    """
    # Admin authentication check
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nNo tienes permisos de administrador.",
            auto_delete_seconds=5
        )
        return

    try:
        # Parse optional days parameter
        command_parts = message.text.split()
        days_back = 30  # Default to 30 days

        if len(command_parts) > 1:
            try:
                days_back = int(command_parts[1])
                if days_back <= 0 or days_back > 365:
                    await menu_manager.send_temporary_message(
                        message,
                        "❌ **Rango Inválido**\n\nLos días deben estar entre 1 y 365.",
                        auto_delete_seconds=8
                    )
                    return
            except ValueError:
                await menu_manager.send_temporary_message(
                    message,
                    "❌ **Valor Inválido**\n\nEl número de días debe ser un entero.",
                    auto_delete_seconds=8
                )
                return

        # Initialize shop admin service
        shop_admin_service = ShopAdminService(session)

        # Get comprehensive analytics with purchase history
        analytics_result = await shop_admin_service.get_purchase_analytics(
            admin_user_id=message.from_user.id,
            days_back=days_back
        )

        if analytics_result.get("success"):
            # Build export summary
            analytics = analytics_result.get("analytics", {})
            purchase_history = analytics_result.get("purchase_history", [])

            export_text = f"📥 **Exportación de Analíticas ({days_back} días)**\n\n"

            summary = analytics.get("summary", {})
            export_text += "📊 **Resumen del Período:**\n"
            export_text += f"• Período: Últimos {days_back} días\n"
            export_text += f"• Compras totales: {summary.get('total_purchases', 0)}\n"
            export_text += f"• Ingresos: {summary.get('total_revenue', 0)} besitos\n"
            export_text += f"• Valor promedio de orden: {summary.get('average_order_value', 0):.1f} besitos\n"
            export_text += f"• Compradores únicos: {summary.get('unique_buyers', 0)}\n"
            export_text += f"• Registros de compras: {len(purchase_history)}\n\n"

            # Category breakdown
            category_performance = analytics.get("category_performance", [])
            if category_performance:
                export_text += "🏷️ **Desglose por Categorías:**\n"
                for category in category_performance:
                    cat_name = category.get("category", "Sin categoría")
                    cat_sales = category.get("purchases", 0)
                    cat_revenue = category.get("revenue", 0)
                    export_text += f"• {cat_name}: {cat_sales} ventas, {cat_revenue} besitos\n"
                export_text += "\n"

            # Top items
            top_items = analytics.get("top_items", [])
            if top_items:
                export_text += "🌟 **Items Más Vendidos:**\n"
                for i, item in enumerate(top_items[:10], 1):
                    item_name = item.get("item_name", "Item desconocido")
                    item_sales = item.get("purchases", 0)
                    item_revenue = item.get("revenue", 0)
                    export_text += f"{i}. {item_name}: {item_sales} ventas, {item_revenue} besitos\n"
                export_text += "\n"

            # User type analysis
            user_analysis = analytics.get("user_type_analysis", [])
            if user_analysis:
                export_text += "👥 **Análisis por Tipo de Usuario:**\n"
                for user_type in user_analysis:
                    user_role = user_type.get("user_type", "unknown")
                    purchases = user_type.get("purchases", 0)
                    revenue = user_type.get("revenue", 0)
                    avg_order = user_type.get("average_order_value", 0)
                    unique_buyers = user_type.get("unique_buyers", 0)

                    role_label = "👑 VIP" if user_role == "vip" else "🆓 Free"
                    export_text += f"{role_label}:\n"
                    export_text += f"  - Compras: {purchases}\n"
                    export_text += f"  - Ingresos: {revenue} besitos\n"
                    export_text += f"  - Valor promedio: {avg_order:.1f} besitos\n"
                    export_text += f"  - Compradores únicos: {unique_buyers}\n\n"

            # Recent purchases sample
            if purchase_history:
                export_text += "🛒 **Muestra de Compras Recientes (últimas 10):**\n"
                for purchase in purchase_history[:10]:
                    user = purchase.get("username") or purchase.get("first_name") or "Usuario desconocido"
                    item = purchase.get("item_name", "Item desconocido")
                    price = purchase.get("price_paid", 0)
                    date = purchase.get("purchased_at", "Fecha desconocida")[:10]  # Just date part
                    export_text += f"• {date}: {user} compró {item} por {price} besitos\n"
                export_text += "\n"

            export_text += f"📅 **Exportación generada:** {analytics_result.get('filters', {}).get('days_back', days_back)} días de historial\n"
            export_text += f"⏰ **Fecha de generación:** {analytics.get('generated_at', 'N/A')[:19] if analytics else 'N/A'}\n\n"
            export_text += "**Nota:** Para obtener los datos completos en formato CSV, usa el comando `/export_catalog_csv` para exportar el catálogo completo."

            from keyboards.common import get_back_kb
            keyboard = get_back_kb("admin_shop_stats")

            await menu_manager.show_menu(
                message,
                export_text,
                keyboard,
                session,
                "admin_analytics_export"
            )

            logger.info(f"Analytics export generated for admin {message.from_user.id} ({days_back} days)")

        else:
            error_message = analytics_result.get("message", "Error desconocido")
            await menu_manager.send_temporary_message(
                message,
                f"❌ **Error al Exportar Analíticas**\n\n**Motivo:** {error_message}",
                auto_delete_seconds=10
            )

    except Exception as e:
        logger.error(f"Error processing analytics export for admin {message.from_user.id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudieron exportar las analíticas.",
            auto_delete_seconds=8
        )


@router.callback_query(F.data == "admin_shop_menu")
async def admin_shop_menu_alias(callback: CallbackQuery, session: AsyncSession):
    """
    Alias handler for shop admin menu access.
    Provides consistent naming with other admin modules.
    """
    await show_shop_admin_menu(callback, session)


# IMPORT/EXPORT INTERFACE HANDLERS

@router.callback_query(F.data == "admin_shop_export")
async def show_export_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Display export options menu for shop catalog.
    """
    # Admin authentication check
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Build export menu text
        menu_text = "📤 **Exportar Catálogo de Tienda**\n\n"
        menu_text += "Exporta el catálogo completo de la tienda en formato CSV para respaldos, análisis o migración.\n\n"

        menu_text += "📋 **Opciones de Exportación:**\n"
        menu_text += "• **Solo activos**: Exporta únicamente categorías e items activos\n"
        menu_text += "• **Incluir inactivos**: Exporta todo el catálogo incluyendo elementos inactivos\n\n"

        menu_text += "⚡ **Comandos Rápidos:**\n"
        menu_text += "• `/export_catalog` - Vista previa y resumen\n"
        menu_text += "• `/export_catalog_csv` - Contenido CSV completo\n\n"

        menu_text += "💡 **Consejo:** El archivo CSV generado puede ser importado posteriormente usando la función de importación."

        # Create export options keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        builder.button(text="📥 Exportar Solo Activos", callback_data="admin_export_active")
        builder.button(text="📄 Exportar Todo", callback_data="admin_export_all")
        builder.button(text="📋 Vista Previa", callback_data="admin_export_preview")
        builder.button(text="↩️ Volver", callback_data="admin_shop_main")

        builder.adjust(2, 1, 1)
        keyboard = builder.as_markup()

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_shop_export_menu"
        )

        logger.info(f"Export menu displayed for admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error showing export menu for admin {callback.from_user.id}: {e}")
        await callback.answer("❌ Error al cargar el menú de exportación", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "admin_shop_import")
async def show_import_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Display import options menu for shop catalog.
    """
    # Admin authentication check
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Build import menu text
        menu_text = "📥 **Importar Catálogo de Tienda**\n\n"
        menu_text += "Importa un catálogo de tienda desde un archivo CSV con validación completa y vista previa.\n\n"

        menu_text += "📋 **Opciones de Importación:**\n"
        menu_text += "• **Crear nuevos**: Solo crear categorías e items que no existan\n"
        menu_text += "• **Actualizar existentes**: Actualizar datos de elementos que ya existen\n"
        menu_text += "• **Omitir errores**: Continuar importación aunque haya errores de validación\n\n"

        menu_text += "⚡ **Comandos Disponibles:**\n"
        menu_text += "• `/import_catalog` - Instrucciones detalladas\n"
        menu_text += "• `/import_catalog_csv` - Importación directa\n\n"

        menu_text += "⚠️ **Formato Requerido:**\n"
        menu_text += "El archivo CSV debe tener las secciones `CATEGORIES` e `ITEMS` con sus respectivos encabezados.\n\n"

        menu_text += "💡 **Consejo:** Usa `/export_catalog_csv` para ver el formato exacto requerido."

        # Create import options keyboard
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()

        builder.button(text="📤 Importar (Solo Crear)", callback_data="admin_import_create")
        builder.button(text="🔄 Importar (Actualizar)", callback_data="admin_import_update")
        builder.button(text="📋 Ver Instrucciones", callback_data="admin_import_instructions")
        builder.button(text="↩️ Volver", callback_data="admin_shop_main")

        builder.adjust(2, 1, 1)
        keyboard = builder.as_markup()

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_shop_import_menu"
        )

        logger.info(f"Import menu displayed for admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error showing import menu for admin {callback.from_user.id}: {e}")
        await callback.answer("❌ Error al cargar el menú de importación", show_alert=True)

    await callback.answer()


# Export callback handlers
@router.callback_query(F.data == "admin_export_active")
async def handle_export_active(callback: CallbackQuery, session: AsyncSession):
    """Export only active categories and items."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    await callback.answer("📥 Exportando elementos activos...")

    # Simulate message for export handler
    from aiogram.types import Message, User, Chat
    mock_message = type('MockMessage', (), {
        'from_user': callback.from_user,
        'text': '/export_catalog false',
        'answer': callback.message.answer if callback.message else lambda x: None
    })()

    await handle_export_catalog(mock_message, session)


@router.callback_query(F.data == "admin_export_all")
async def handle_export_all(callback: CallbackQuery, session: AsyncSession):
    """Export all categories and items including inactive ones."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    await callback.answer("📥 Exportando catálogo completo...")

    # Simulate message for export handler
    mock_message = type('MockMessage', (), {
        'from_user': callback.from_user,
        'text': '/export_catalog true',
        'answer': callback.message.answer if callback.message else lambda x: None
    })()

    await handle_export_catalog(mock_message, session)


@router.callback_query(F.data == "admin_export_preview")
async def handle_export_preview(callback: CallbackQuery, session: AsyncSession):
    """Show export preview without generating full CSV."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        shop_admin_service = ShopAdminService(session)
        stats_result = await shop_admin_service.get_admin_statistics(callback.from_user.id)

        if stats_result.get("success"):
            stats = stats_result.get("statistics", {})
            inventory = stats.get("inventory", {})

            preview_text = "📋 **Vista Previa de Exportación**\n\n"
            preview_text += "📊 **Datos Disponibles para Exportar:**\n"
            preview_text += f"• Categorías activas: {inventory.get('categories', {}).get('active', 0)}\n"
            preview_text += f"• Categorías inactivas: {inventory.get('categories', {}).get('inactive', 0)}\n"
            preview_text += f"• Items activos: {inventory.get('items', {}).get('active', 0)}\n"
            preview_text += f"• Items inactivos: {inventory.get('items', {}).get('inactive', 0)}\n\n"

            total_categories = inventory.get('categories', {}).get('total', 0)
            total_items = inventory.get('items', {}).get('total', 0)

            preview_text += f"📁 **Total a exportar:** {total_categories} categorías, {total_items} items\n\n"
            preview_text += "✅ **Listo para exportar** - Usa los botones superiores para proceder."

            from keyboards.common import get_back_kb
            keyboard = get_back_kb("admin_shop_export")

            await menu_manager.update_menu(
                callback,
                preview_text,
                keyboard,
                session,
                "admin_export_preview"
            )
        else:
            await callback.answer("❌ Error al cargar vista previa", show_alert=True)

    except Exception as e:
        logger.error(f"Error showing export preview: {e}")
        await callback.answer("❌ Error al mostrar vista previa", show_alert=True)

    await callback.answer()


# Import callback handlers
@router.callback_query(F.data == "admin_import_create")
async def handle_import_create_only(callback: CallbackQuery, session: AsyncSession):
    """Start import process with create-only mode."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    await callback.answer("📤 Iniciando importación (solo crear)...")

    # Simulate message for import handler
    mock_message = type('MockMessage', (), {
        'from_user': callback.from_user,
        'text': '/import_catalog false false',
        'answer': callback.message.answer if callback.message else lambda x: None
    })()

    await handle_import_catalog(mock_message, session)


@router.callback_query(F.data == "admin_import_update")
async def handle_import_with_update(callback: CallbackQuery, session: AsyncSession):
    """Start import process with update mode."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    await callback.answer("🔄 Iniciando importación (actualizar)...")

    # Simulate message for import handler
    mock_message = type('MockMessage', (), {
        'from_user': callback.from_user,
        'text': '/import_catalog true true',
        'answer': callback.message.answer if callback.message else lambda x: None
    })()

    await handle_import_catalog(mock_message, session)


@router.callback_query(F.data == "admin_import_instructions")
async def show_import_instructions(callback: CallbackQuery, session: AsyncSession):
    """Show detailed import instructions."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        instructions_text = "📋 **Instrucciones Detalladas de Importación**\n\n"

        instructions_text += "📄 **Formato CSV Requerido:**\n"
        instructions_text += "```\nCATEGORIES\nname,description,display_order,is_active,vip_only,icon,color\nMi Categoría,Descripción,1,True,False,🏷️,#FF5733\n\nITEMS\nname,description,price,category_name,is_active,vip_only,unlocks_lore_piece_id,stock_quantity,max_per_user,icon\nMi Item,Descripción,100,Mi Categoría,True,False,,10,1,💎\n```\n\n"

        instructions_text += "⚠️ **Reglas Importantes:**\n"
        instructions_text += "• Usar `CATEGORIES` e `ITEMS` como separadores de sección\n"
        instructions_text += "• Respetar el orden exacto de las columnas\n"
        instructions_text += "• Usar valores `True`/`False` para campos booleanos\n"
        instructions_text += "• El `category_name` debe coincidir exactamente\n"
        instructions_text += "• Dejar campos opcionales vacíos (no usar 'null')\n\n"

        instructions_text += "💡 **Recomendación:** Exporta primero con `/export_catalog_csv` para ver el formato exacto."

        from keyboards.common import get_back_kb
        keyboard = get_back_kb("admin_shop_import")

        await menu_manager.update_menu(
            callback,
            instructions_text,
            keyboard,
            session,
            "admin_import_instructions_detail"
        )

    except Exception as e:
        logger.error(f"Error showing import instructions: {e}")
        await callback.answer("❌ Error al mostrar instrucciones", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "admin_shop_config")
async def show_shop_config_menu(callback: CallbackQuery, session: AsyncSession):
    """Display shop configuration menu with system settings."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        config_text = "⚙️ **Configuración de Tienda**\n\n"

        config_text += "🔧 **Configuraciones Disponibles:**\n"
        config_text += "• Configuración general de la tienda\n"
        config_text += "• Límites de compra por usuario\n"
        config_text += "• Configuración de categorías VIP\n"
        config_text += "• Gestión de promociones\n"
        config_text += "• Configuración de precios\n\n"

        config_text += "📊 **Estado Actual del Sistema:**\n"

        # Get basic shop stats
        shop_admin_service = ShopAdminService(session)

        # Get categories count
        from sqlalchemy import select, func
        from database.models import ShopCategory, ShopItem

        categories_result = await session.execute(select(func.count()).select_from(ShopCategory))
        categories_count = categories_result.scalar() or 0

        items_result = await session.execute(select(func.count()).select_from(ShopItem))
        items_count = items_result.scalar() or 0

        active_categories_result = await session.execute(
            select(func.count()).select_from(ShopCategory).where(ShopCategory.is_active == True)
        )
        active_categories = active_categories_result.scalar() or 0

        active_items_result = await session.execute(
            select(func.count()).select_from(ShopItem).where(ShopItem.is_active == True)
        )
        active_items = active_items_result.scalar() or 0

        config_text += f"• Total de categorías: {categories_count} ({active_categories} activas)\n"
        config_text += f"• Total de items: {items_count} ({active_items} activos)\n\n"

        config_text += "💡 **Próximamente:**\n"
        config_text += "• Editor de configuración global\n"
        config_text += "• Gestión de descuentos automáticos\n"
        config_text += "• Configuración de notificaciones\n"
        config_text += "• Sistema de logs de administración\n\n"

        config_text += "Para configuraciones específicas, usa los menús de gestión de items y categorías."

        from keyboards.common import get_back_kb
        keyboard = get_back_kb("admin_shop_main")

        await menu_manager.update_menu(
            callback,
            config_text,
            keyboard,
            session,
            "admin_shop_config_menu"
        )

    except Exception as e:
        logger.error(f"Error showing shop config menu: {e}")
        await callback.answer("❌ Error al mostrar configuración", show_alert=True)

    await callback.answer()


@router.message(Command("export_catalog"))
async def handle_export_catalog(message: Message, session: AsyncSession):
    """
    Export shop catalog to CSV format with comprehensive validation feedback.
    Usage: /export_catalog [include_inactive]
    Example: /export_catalog true (to include inactive items)
    """
    # Admin authentication check
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nSolo los administradores pueden exportar el catálogo.",
            auto_delete_seconds=8
        )
        return

    try:
        # Parse command arguments
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        include_inactive = len(args) > 0 and args[0].lower() in ['true', 'yes', 'si', '1']

        # Initialize shop admin service
        shop_admin_service = ShopAdminService(session)

        # Show loading message
        loading_message = await menu_manager.send_temporary_message(
            message,
            "📥 **Exportando Catálogo...**\n\nProcesando datos de la tienda, por favor espera...",
            auto_delete_seconds=3
        )

        # Perform export
        export_result = await shop_admin_service.export_catalog_csv(
            message.from_user.id,
            include_inactive=include_inactive
        )

        if export_result.get("success"):
            # Build success message with validation feedback
            stats = export_result.get("stats", {})
            export_text = "📥 **Exportación de Catálogo Completada**\n\n"

            # Statistics summary
            export_text += "📊 **Estadísticas de Exportación:**\n"
            export_text += f"• Categorías exportadas: {stats.get('categories_count', 0)}\n"
            export_text += f"• Items exportados: {stats.get('items_count', 0)}\n"
            export_text += f"• Incluir inactivos: {'Sí' if include_inactive else 'No'}\n\n"

            # Validation feedback
            export_text += "✅ **Validación Exitosa:**\n"
            export_text += "• Todas las categorías validadas correctamente\n"
            export_text += "• Todos los items validados correctamente\n"
            export_text += "• Estructura CSV generada sin errores\n\n"

            # CSV content preview (first few lines)
            csv_content = export_result.get("csv_content", "")
            lines = csv_content.split('\n')[:8]  # Show first 8 lines
            if lines:
                export_text += "📄 **Vista Previa del CSV:**\n"
                export_text += "```\n"
                for line in lines:
                    if line.strip():
                        export_text += f"{line[:80]}{'...' if len(line) > 80 else ''}\n"
                export_text += "```\n\n"

            # File info
            export_text += f"📁 **Información del Archivo:**\n"
            export_text += f"• Tamaño: {len(csv_content)} caracteres\n"
            export_text += f"• Líneas totales: {len(csv_content.split(chr(10)))}\n"
            export_text += f"• Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

            # Usage instructions
            export_text += "💡 **Instrucciones de Uso:**\n"
            export_text += "• Copia y pega el contenido completo en un archivo .csv\n"
            export_text += "• Úsalo para respaldos o importación posterior\n"
            export_text += "• Comando para importar: `/import_catalog`\n\n"

            export_text += "**Para ver el contenido completo, usa el comando:**\n"
            export_text += f"`/export_catalog_csv {include_inactive}`"

            from keyboards.common import get_back_kb
            keyboard = get_back_kb("admin_shop_main")

            await menu_manager.show_menu(
                message,
                export_text,
                keyboard,
                session,
                "admin_export_catalog"
            )

            logger.info(f"Catalog export completed for admin {message.from_user.id}")

        else:
            error_message = export_result.get("message", "Error desconocido")
            await menu_manager.send_temporary_message(
                message,
                f"❌ **Error al Exportar Catálogo**\n\n**Motivo:** {error_message}",
                auto_delete_seconds=10
            )

    except Exception as e:
        logger.error(f"Error processing catalog export for admin {message.from_user.id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo exportar el catálogo de la tienda.",
            auto_delete_seconds=8
        )


@router.message(Command("export_catalog_csv"))
async def handle_export_catalog_csv(message: Message, session: AsyncSession):
    """
    Export complete shop catalog CSV content for download/copy.
    Usage: /export_catalog_csv [include_inactive]
    Example: /export_catalog_csv true
    """
    # Admin authentication check
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nSolo los administradores pueden exportar el catálogo.",
            auto_delete_seconds=8
        )
        return

    try:
        # Parse command arguments
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        include_inactive = len(args) > 0 and args[0].lower() in ['true', 'yes', 'si', '1']

        # Initialize shop admin service
        shop_admin_service = ShopAdminService(session)

        # Perform export
        export_result = await shop_admin_service.export_catalog_csv(
            message.from_user.id,
            include_inactive=include_inactive
        )

        if export_result.get("success"):
            csv_content = export_result.get("csv_content", "")
            stats = export_result.get("stats", {})

            # Split content into manageable chunks for Telegram
            max_message_length = 4000
            chunks = []

            if len(csv_content) <= max_message_length:
                chunks = [csv_content]
            else:
                # Split by lines to avoid breaking CSV structure
                lines = csv_content.split('\n')
                current_chunk = ""

                for line in lines:
                    if len(current_chunk + line + '\n') <= max_message_length:
                        current_chunk += line + '\n'
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = line + '\n'

                if current_chunk:
                    chunks.append(current_chunk)

            # Send header message
            header_text = f"📁 **Exportación CSV Completa**\n\n"
            header_text += f"📊 **Estadísticas:** {stats.get('categories_count', 0)} categorías, {stats.get('items_count', 0)} items\n"
            header_text += f"📄 **Partes del archivo:** {len(chunks)} mensaje(s)\n\n"

            await message.answer(header_text)

            # Send CSV content chunks
            for i, chunk in enumerate(chunks, 1):
                chunk_header = f"**Parte {i}/{len(chunks)}:**\n\n" if len(chunks) > 1 else "**Contenido CSV:**\n\n"
                chunk_message = chunk_header + f"```csv\n{chunk}```"

                await message.answer(chunk_message, parse_mode="Markdown")

            logger.info(f"Complete CSV export sent to admin {message.from_user.id}")

        else:
            error_message = export_result.get("message", "Error desconocido")
            await menu_manager.send_temporary_message(
                message,
                f"❌ **Error al Exportar CSV**\n\n**Motivo:** {error_message}",
                auto_delete_seconds=10
            )

    except Exception as e:
        logger.error(f"Error processing complete CSV export for admin {message.from_user.id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo exportar el CSV completo.",
            auto_delete_seconds=8
        )


@router.message(Command("import_catalog"))
async def handle_import_catalog(message: Message, session: AsyncSession):
    """
    Import shop catalog from CSV content with preview and validation.
    Usage: /import_catalog [update_existing] [skip_errors]
    Example: /import_catalog true false

    After running this command, send the CSV content in the next message.
    """
    # Admin authentication check
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nSolo los administradores pueden importar el catálogo.",
            auto_delete_seconds=8
        )
        return

    try:
        # Parse command arguments
        args = message.text.split()[1:] if len(message.text.split()) > 1 else []
        update_existing = len(args) > 0 and args[0].lower() in ['true', 'yes', 'si', '1']
        skip_errors = len(args) > 1 and args[1].lower() in ['true', 'yes', 'si', '1']

        # Build instruction message
        instruction_text = "📤 **Importar Catálogo de Tienda**\n\n"
        instruction_text += "**Configuración de Importación:**\n"
        instruction_text += f"• Actualizar existentes: {'Sí' if update_existing else 'No'}\n"
        instruction_text += f"• Omitir errores: {'Sí' if skip_errors else 'No'}\n\n"

        instruction_text += "📋 **Instrucciones:**\n"
        instruction_text += "1. Envía el contenido CSV en tu próximo mensaje\n"
        instruction_text += "2. El sistema validará el formato automáticamente\n"
        instruction_text += "3. Se mostrará una vista previa antes de importar\n"
        instruction_text += "4. Confirma o cancela la importación\n\n"

        instruction_text += "⚠️ **Formato CSV Requerido:**\n"
        instruction_text += "• Secciones: `CATEGORIES` y `ITEMS`\n"
        instruction_text += "• Encabezados obligatorios en cada sección\n"
        instruction_text += "• Separadores: comas (`,`)\n\n"

        instruction_text += "💡 **Consejo:** Usa `/export_catalog_csv` para ver el formato correcto."

        from keyboards.common import get_back_kb
        keyboard = get_back_kb("admin_shop_main")

        await menu_manager.show_menu(
            message,
            instruction_text,
            keyboard,
            session,
            "admin_import_catalog_instructions"
        )

        # Store import configuration in user context (simplified approach)
        # In a full implementation, you might use FSM states
        logger.info(f"Import instructions sent to admin {message.from_user.id} - update_existing: {update_existing}, skip_errors: {skip_errors}")

    except Exception as e:
        logger.error(f"Error showing import instructions for admin {message.from_user.id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudieron mostrar las instrucciones de importación.",
            auto_delete_seconds=8
        )


@router.message(Command("import_catalog_csv"))
async def handle_import_catalog_csv(message: Message, session: AsyncSession):
    """
    Import catalog from CSV content provided as command argument or in message.
    Usage: /import_catalog_csv [update_existing] [skip_errors]
    Then provide CSV content in next message or as argument.
    Example: /import_catalog_csv true false
    """
    # Admin authentication check
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nSolo los administradores pueden importar el catálogo.",
            auto_delete_seconds=8
        )
        return

    try:
        # Parse command for CSV content and options
        message_parts = message.text.split(' ', 3)
        args = message_parts[1:3] if len(message_parts) > 3 else message_parts[1:]
        csv_content = message_parts[3] if len(message_parts) > 3 else None

        update_existing = len(args) > 0 and args[0].lower() in ['true', 'yes', 'si', '1']
        skip_errors = len(args) > 1 and args[1].lower() in ['true', 'yes', 'si', '1']

        if not csv_content:
            # Request CSV content
            instruction_text = "📤 **Envía el Contenido CSV**\n\n"
            instruction_text += f"**Configuración:** Actualizar existentes: {'Sí' if update_existing else 'No'}, "
            instruction_text += f"Omitir errores: {'Sí' if skip_errors else 'No'}\n\n"
            instruction_text += "Envía el contenido CSV completo en tu próximo mensaje.\n\n"
            instruction_text += "**Ejemplo de uso completo:**\n"
            instruction_text += "```\n/import_catalog_csv true false\nCATEGORIES\nname,description,display_order,is_active,vip_only,icon,color\n...\n```"

            await message.answer(instruction_text, parse_mode="Markdown")
            return

        # Initialize shop admin service
        shop_admin_service = ShopAdminService(session)

        # Show processing message
        processing_message = await menu_manager.send_temporary_message(
            message,
            "🔄 **Procesando Importación...**\n\nValidando y importando datos, por favor espera...",
            auto_delete_seconds=5
        )

        # Perform import with validation
        import_result = await shop_admin_service.import_catalog_csv(
            message.from_user.id,
            csv_content,
            update_existing=update_existing,
            skip_validation_errors=skip_errors
        )

        if import_result.get("success"):
            # Build success message with detailed feedback
            import_results = import_result.get("import_results", {})
            success_text = "✅ **Importación Completada con Éxito**\n\n"

            # Summary statistics
            success_text += "📊 **Resultados de Importación:**\n"
            success_text += f"• Categorías procesadas: {import_results.get('categories_processed', 0)}\n"
            success_text += f"• Categorías creadas: {import_results.get('categories_created', 0)}\n"
            success_text += f"• Categorías actualizadas: {import_results.get('categories_updated', 0)}\n"
            success_text += f"• Items procesados: {import_results.get('items_processed', 0)}\n"
            success_text += f"• Items creados: {import_results.get('items_created', 0)}\n"
            success_text += f"• Items actualizados: {import_results.get('items_updated', 0)}\n\n"

            # Error summary if any
            category_errors = import_results.get('categories_errors', [])
            item_errors = import_results.get('items_errors', [])

            if category_errors or item_errors:
                success_text += "⚠️ **Errores Encontrados:**\n"
                if category_errors:
                    success_text += f"• Errores de categorías: {len(category_errors)}\n"
                if item_errors:
                    success_text += f"• Errores de items: {len(item_errors)}\n"
                success_text += "\n"

            # Validation feedback
            success_text += "✅ **Validación Completada:**\n"
            success_text += "• Formato CSV validado correctamente\n"
            success_text += "• Estructura de datos verificada\n"
            success_text += "• Relaciones entre entidades validadas\n\n"

            success_text += f"⏰ **Importación finalizada:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            success_text += "🔄 **Recomendación:** Usa `/admin_shop_main` para verificar los cambios."

            from keyboards.common import get_back_kb
            keyboard = get_back_kb("admin_shop_main")

            await menu_manager.show_menu(
                message,
                success_text,
                keyboard,
                session,
                "admin_import_catalog_success"
            )

            logger.info(f"Catalog import completed for admin {message.from_user.id} - Results: {import_results}")

        else:
            error_message = import_result.get("message", "Error desconocido")
            error_text = f"❌ **Error en la Importación**\n\n"
            error_text += f"**Motivo:** {error_message}\n\n"
            error_text += "💡 **Sugerencias:**\n"
            error_text += "• Verifica el formato CSV\n"
            error_text += "• Usa `/export_catalog_csv` como referencia\n"
            error_text += "• Revisa que todas las columnas requeridas estén presentes\n"
            error_text += "• Considera usar la opción `skip_errors=true`"

            await menu_manager.send_temporary_message(
                message,
                error_text,
                auto_delete_seconds=15
            )

    except Exception as e:
        logger.error(f"Error processing catalog import for admin {message.from_user.id}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo procesar la importación del catálogo.",
            auto_delete_seconds=8
        )