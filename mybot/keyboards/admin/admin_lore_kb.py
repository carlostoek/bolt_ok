"""
Comprehensive lore management keyboard layouts.
Provides elegant and intuitive navigation for all lore management functions.
"""
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


# ============================================================================
# MAIN LORE MANAGEMENT DASHBOARD
# ============================================================================

def get_lore_management_main_kb() -> InlineKeyboardMarkup:
    """Return the main lore management dashboard keyboard with elegant layout."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Gestión principal de fragmentos
    builder.button(text="📝 Crear Fragmento", callback_data="admin_lore_create")
    builder.button(text="📚 Lista Fragmentos", callback_data="admin_lore_list")

    # Fila 2: Integración y análisis
    builder.button(text="🔗 Vincular Item", callback_data="admin_lore_link_item")
    builder.button(text="📊 Analytics", callback_data="admin_lore_analytics")

    # Fila 3: Gestión avanzada
    builder.button(text="🏷️ Categorías", callback_data="admin_lore_categories")
    builder.button(text="🔍 Búsqueda", callback_data="admin_lore_search")

    # Fila 4: Operaciones masivas
    builder.button(text="📦 Operaciones Lote", callback_data="admin_lore_bulk_operations")
    builder.button(text="📄 Exportar Datos", callback_data="admin_lore_export_csv")

    # Fila 5: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_narrative_lore")
    builder.button(text="🔙 Volver", callback_data="admin_narrative_main")

    # Distribución: 2x2, luego 2x2, luego 2
    builder.adjust(2, 2, 2, 2, 2)
    return builder.as_markup()


# ============================================================================
# LORE PIECE LISTING AND NAVIGATION
# ============================================================================

def get_lore_list_navigation_kb(current_page: int = 0, total_pages: int = 1, has_lore: bool = True) -> InlineKeyboardMarkup:
    """Return navigation keyboard for lore list pagination."""
    builder = InlineKeyboardBuilder()

    if has_lore and total_pages > 1:
        # Navegación de páginas
        if current_page > 0:
            builder.button(text="⬅️ Anterior", callback_data=f"admin_lore_list:{current_page - 1}")

        builder.button(text=f"📄 {current_page + 1}/{total_pages}", callback_data="admin_lore_list_info")

        if current_page < total_pages - 1:
            builder.button(text="➡️ Siguiente", callback_data=f"admin_lore_list:{current_page + 1}")

    # Opciones adicionales
    builder.button(text="🔍 Buscar", callback_data="admin_lore_search")
    builder.button(text="📊 Analytics", callback_data="admin_lore_analytics")

    # Acciones rápidas
    builder.button(text="➕ Crear Nuevo", callback_data="admin_lore_create")
    builder.button(text="🔗 Vincular Item", callback_data="admin_lore_link_item")

    # Navegación principal
    builder.button(text="🔄 Actualizar", callback_data="admin_lore_list")
    builder.button(text="🔙 Volver", callback_data="admin_narrative_lore")

    # Ajustar según el número de botones
    if total_pages > 1:
        if current_page == 0:
            builder.adjust(2, 2, 2, 2)  # Sin botón anterior
        elif current_page == total_pages - 1:
            builder.adjust(2, 2, 2, 2)  # Sin botón siguiente
        else:
            builder.adjust(3, 2, 2, 2)  # Con ambos botones
    else:
        builder.adjust(2, 2, 2)

    return builder.as_markup()


def get_lore_detail_kb(lore_id: int) -> InlineKeyboardMarkup:
    """Return keyboard for individual lore piece detail view and actions."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Acciones principales de edición
    builder.button(text="✏️ Editar", callback_data=f"admin_lore_edit:{lore_id}")
    builder.button(text="📊 Analytics", callback_data=f"admin_lore_analytics_detail:{lore_id}")

    # Fila 2: Estado y configuración
    builder.button(text="⚡ Alternar Estado", callback_data=f"admin_lore_toggle_status:{lore_id}")
    builder.button(text="🏷️ Cambiar Categoría", callback_data=f"admin_lore_edit_category:{lore_id}")

    # Fila 3: Relaciones y vínculos
    builder.button(text="🔗 Gestionar Vínculos", callback_data=f"admin_lore_manage_links:{lore_id}")
    builder.button(text="🔓 Condiciones", callback_data=f"admin_lore_edit_conditions:{lore_id}")

    # Fila 4: Acciones destructivas
    builder.button(text="🗑️ Eliminar", callback_data=f"admin_lore_delete:{lore_id}")
    builder.button(text="📋 Duplicar", callback_data=f"admin_lore_duplicate:{lore_id}")

    # Fila 5: Navegación
    builder.button(text="↩️ Volver a Lista", callback_data="admin_lore_list")
    builder.button(text="🏠 Dashboard", callback_data="admin_narrative_lore")

    builder.adjust(2, 2, 2, 2, 2)
    return builder.as_markup()


# ============================================================================
# SHOP ITEM LINKING INTERFACE
# ============================================================================

def get_shop_item_selection_kb(shop_items: list, page: int = 0, items_per_page: int = 5) -> InlineKeyboardMarkup:
    """Return keyboard for shop item selection during linking process."""
    builder = InlineKeyboardBuilder()

    # Mostrar items de la página actual
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_items = shop_items[start_idx:end_idx]

    for item in page_items:
        price_text = f"{item.price} besitos" if item.price > 0 else "Gratis"
        builder.button(
            text=f"{item.name} ({price_text})",
            callback_data=f"admin_lore_select_item:{item.id}"
        )

    # Paginación si hay múltiples páginas
    total_pages = (len(shop_items) + items_per_page - 1) // items_per_page
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(("⬅️ Anterior", f"admin_lore_shop_page:{page - 1}"))

        nav_buttons.append((f"📄 {page + 1}/{total_pages}", "admin_lore_shop_page_info"))

        if page < total_pages - 1:
            nav_buttons.append(("➡️ Siguiente", f"admin_lore_shop_page:{page + 1}"))

        for text, callback in nav_buttons:
            builder.button(text=text, callback_data=callback)

    # Opciones adicionales
    builder.button(text="🔍 Buscar Item", callback_data="admin_lore_search_shop_item")
    builder.button(text="🔙 Volver", callback_data="admin_narrative_lore")

    # Ajuste del layout
    builder.adjust(1)  # Items en una columna
    if total_pages > 1:
        builder.adjust(*([1] * len(page_items) + [len(nav_buttons), 2]))
    else:
        builder.adjust(*([1] * len(page_items) + [2]))

    return builder.as_markup()


def get_lore_selection_for_linking_kb(lore_pieces: list, item_id: int, page: int = 0, items_per_page: int = 5) -> InlineKeyboardMarkup:
    """Return keyboard for lore piece selection during shop item linking."""
    builder = InlineKeyboardBuilder()

    # Mostrar fragmentos de la página actual
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_lore = lore_pieces[start_idx:end_idx]

    for lore in page_lore:
        status_icon = "✅" if lore.is_active else "❌"
        builder.button(
            text=f"{status_icon} {lore.title}",
            callback_data=f"admin_lore_confirm_link:{lore.id}"
        )

    # Paginación
    total_pages = (len(lore_pieces) + items_per_page - 1) // items_per_page
    if total_pages > 1:
        if page > 0:
            builder.button(text="⬅️ Anterior", callback_data=f"admin_lore_select_page:{page - 1}:{item_id}")

        builder.button(text=f"📄 {page + 1}/{total_pages}", callback_data="admin_lore_select_page_info")

        if page < total_pages - 1:
            builder.button(text="➡️ Siguiente", callback_data=f"admin_lore_select_page:{page + 1}:{item_id}")

    # Navegación
    builder.button(text="🔙 Volver", callback_data="admin_lore_link_item")

    # Ajuste del layout
    builder.adjust(1)  # Lore pieces en una columna
    if total_pages > 1:
        builder.adjust(*([1] * len(page_lore) + [3, 1]))
    else:
        builder.adjust(*([1] * len(page_lore) + [1]))

    return builder.as_markup()


def get_link_confirmation_kb(lore_id: int, item_id: int) -> InlineKeyboardMarkup:
    """Return confirmation keyboard for lore-item linking."""
    builder = InlineKeyboardBuilder()

    # Confirmación
    builder.button(text="✅ Confirmar Vinculación", callback_data=f"admin_lore_confirm_link_final:{lore_id}:{item_id}")
    builder.button(text="❌ Cancelar", callback_data=f"admin_lore_select_item:{item_id}")

    # Vista previa de la vinculación
    builder.button(text="👁️ Vista Previa", callback_data=f"admin_lore_preview_link:{lore_id}:{item_id}")

    # Navegación
    builder.button(text="🔙 Cambiar Selección", callback_data=f"admin_lore_select_item:{item_id}")

    builder.adjust(2, 1, 1)
    return builder.as_markup()


# ============================================================================
# ANALYTICS DASHBOARD NAVIGATION
# ============================================================================

def get_lore_analytics_main_kb() -> InlineKeyboardMarkup:
    """Return main analytics dashboard keyboard for lore management."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Análisis generales
    builder.button(text="📊 Resumen General", callback_data="admin_lore_analytics_overview")
    builder.button(text="📈 Tendencias", callback_data="admin_lore_analytics_trends")

    # Fila 2: Análisis por fragmento
    builder.button(text="🏆 Top Fragmentos", callback_data="admin_lore_analytics_top")
    builder.button(text="📉 Bajo Rendimiento", callback_data="admin_lore_analytics_underperforming")

    # Fila 3: Análisis por categoría
    builder.button(text="🏷️ Por Categorías", callback_data="admin_lore_analytics_categories")
    builder.button(text="🔗 Efectividad Vínculos", callback_data="admin_lore_analytics_links")

    # Fila 4: Análisis temporal
    builder.button(text="📅 Por Período", callback_data="admin_lore_analytics_period")
    builder.button(text="🔥 Actividad Reciente", callback_data="admin_lore_analytics_recent")

    # Fila 5: Exportación y herramientas
    builder.button(text="📄 Exportar Reporte", callback_data="admin_lore_export_analytics")
    builder.button(text="📊 Analytics Detallados", callback_data="admin_lore_detailed_analytics")

    # Fila 6: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_lore_analytics")
    builder.button(text="🔙 Volver", callback_data="admin_narrative_lore")

    builder.adjust(2, 2, 2, 2, 2, 2)
    return builder.as_markup()


def get_analytics_period_selection_kb() -> InlineKeyboardMarkup:
    """Return keyboard for analytics period selection."""
    builder = InlineKeyboardBuilder()

    # Períodos predefinidos
    builder.button(text="📅 Últimos 7 días", callback_data="admin_lore_analytics_period:7")
    builder.button(text="📅 Último mes", callback_data="admin_lore_analytics_period:30")

    builder.button(text="📅 Últimos 3 meses", callback_data="admin_lore_analytics_period:90")
    builder.button(text="📅 Último año", callback_data="admin_lore_analytics_period:365")

    # Opciones personalizadas
    builder.button(text="📆 Rango Personalizado", callback_data="admin_lore_analytics_custom_period")
    builder.button(text="📊 Comparar Períodos", callback_data="admin_lore_analytics_compare_periods")

    # Navegación
    builder.button(text="🔙 Volver", callback_data="admin_lore_analytics")

    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def get_analytics_export_kb() -> InlineKeyboardMarkup:
    """Return keyboard for analytics export options."""
    builder = InlineKeyboardBuilder()

    # Formatos de exportación
    builder.button(text="📄 CSV Básico", callback_data="admin_lore_export:csv_basic")
    builder.button(text="📊 CSV Detallado", callback_data="admin_lore_export:csv_detailed")

    builder.button(text="📈 Reporte PDF", callback_data="admin_lore_export:pdf_report")
    builder.button(text="📋 Resumen Ejecutivo", callback_data="admin_lore_export:executive_summary")

    # Opciones de filtrado
    builder.button(text="🔍 Solo Activos", callback_data="admin_lore_export_filter:active")
    builder.button(text="🏷️ Por Categoría", callback_data="admin_lore_export_filter:category")

    # Navegación
    builder.button(text="🔙 Volver", callback_data="admin_lore_analytics")

    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


# ============================================================================
# SEARCH AND FILTERING
# ============================================================================

def get_lore_search_options_kb() -> InlineKeyboardMarkup:
    """Return keyboard for lore search options."""
    builder = InlineKeyboardBuilder()

    # Tipos de búsqueda
    builder.button(text="🔍 Búsqueda Rápida", callback_data="admin_lore_search_quick")
    builder.button(text="🔎 Búsqueda Avanzada", callback_data="admin_lore_search_advanced")

    # Filtros predefinidos
    builder.button(text="✅ Solo Activos", callback_data="admin_lore_filter:active")
    builder.button(text="❌ Solo Inactivos", callback_data="admin_lore_filter:inactive")

    builder.button(text="🔗 Con Vínculos", callback_data="admin_lore_filter:linked")
    builder.button(text="🆓 Sin Vínculos", callback_data="admin_lore_filter:unlinked")

    # Ordenamiento
    builder.button(text="📅 Por Fecha", callback_data="admin_lore_sort:date")
    builder.button(text="📊 Por Popularidad", callback_data="admin_lore_sort:popularity")

    # Navegación
    builder.button(text="🔙 Volver", callback_data="admin_narrative_lore")

    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup()


def get_search_results_kb(results: list, search_term: str, page: int = 0, items_per_page: int = 5) -> InlineKeyboardMarkup:
    """Return keyboard for search results navigation."""
    builder = InlineKeyboardBuilder()

    # Mostrar resultados de la página actual
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_results = results[start_idx:end_idx]

    for lore in page_results:
        status_icon = "✅" if lore.is_active else "❌"
        builder.button(
            text=f"{status_icon} {lore.title}",
            callback_data=f"admin_lore_edit:{lore.id}"
        )

    # Paginación
    total_pages = (len(results) + items_per_page - 1) // items_per_page
    if total_pages > 1:
        if page > 0:
            builder.button(text="⬅️ Anterior", callback_data=f"admin_lore_search_results:{page - 1}")

        builder.button(text=f"📄 {page + 1}/{total_pages}", callback_data="admin_lore_search_results_info")

        if page < total_pages - 1:
            builder.button(text="➡️ Siguiente", callback_data=f"admin_lore_search_results:{page + 1}")

    # Acciones adicionales
    builder.button(text="🔍 Nueva Búsqueda", callback_data="admin_lore_search")
    builder.button(text="📊 Analytics Resultados", callback_data=f"admin_lore_search_analytics:{search_term}")

    # Navegación
    builder.button(text="🔙 Volver", callback_data="admin_narrative_lore")

    # Ajuste del layout
    builder.adjust(1)  # Resultados en una columna
    if total_pages > 1:
        builder.adjust(*([1] * len(page_results) + [3, 2, 1]))
    else:
        builder.adjust(*([1] * len(page_results) + [2, 1]))

    return builder.as_markup()


# ============================================================================
# BULK OPERATIONS INTERFACE
# ============================================================================

def get_bulk_operations_main_kb() -> InlineKeyboardMarkup:
    """Return main bulk operations keyboard."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Operaciones de estado
    builder.button(text="⚡ Cambio Estado Masivo", callback_data="admin_lore_bulk_status")
    builder.button(text="🏷️ Cambio Categoría Masivo", callback_data="admin_lore_bulk_category")

    # Fila 2: Operaciones de contenido
    builder.button(text="📝 Edición Masiva", callback_data="admin_lore_bulk_edit")
    builder.button(text="🔗 Vinculación Masiva", callback_data="admin_lore_bulk_link")

    # Fila 3: Análisis y exportación
    builder.button(text="📊 Análisis Masivo", callback_data="admin_lore_bulk_analytics")
    builder.button(text="📄 Exportar Selección", callback_data="admin_lore_bulk_export")

    # Fila 4: Operaciones destructivas
    builder.button(text="🗑️ Eliminación Masiva", callback_data="admin_lore_bulk_delete")
    builder.button(text="📋 Duplicación Masiva", callback_data="admin_lore_bulk_duplicate")

    # Fila 5: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_lore_bulk_operations")
    builder.button(text="🔙 Volver", callback_data="admin_narrative_lore")

    builder.adjust(2, 2, 2, 2, 2)
    return builder.as_markup()


def get_bulk_selection_kb(lore_pieces: list, selected_ids: list = None, page: int = 0, items_per_page: int = 5) -> InlineKeyboardMarkup:
    """Return keyboard for bulk selection of lore pieces."""
    if selected_ids is None:
        selected_ids = []

    builder = InlineKeyboardBuilder()

    # Mostrar fragmentos de la página actual
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_lore = lore_pieces[start_idx:end_idx]

    for lore in page_lore:
        is_selected = lore.id in selected_ids
        status_icon = "✅" if lore.is_active else "❌"
        selection_icon = "☑️" if is_selected else "☐"

        builder.button(
            text=f"{selection_icon} {status_icon} {lore.title}",
            callback_data=f"admin_lore_bulk_toggle:{lore.id}"
        )

    # Paginación
    total_pages = (len(lore_pieces) + items_per_page - 1) // items_per_page
    if total_pages > 1:
        if page > 0:
            builder.button(text="⬅️ Anterior", callback_data=f"admin_lore_bulk_page:{page - 1}")

        builder.button(text=f"📄 {page + 1}/{total_pages}", callback_data="admin_lore_bulk_page_info")

        if page < total_pages - 1:
            builder.button(text="➡️ Siguiente", callback_data=f"admin_lore_bulk_page:{page + 1}")

    # Acciones de selección
    builder.button(text="☑️ Seleccionar Todo", callback_data="admin_lore_bulk_select_all")
    builder.button(text="☐ Deseleccionar Todo", callback_data="admin_lore_bulk_deselect_all")

    # Acciones sobre selección
    if selected_ids:
        builder.button(text=f"⚡ Procesar ({len(selected_ids)})", callback_data="admin_lore_bulk_process")

    # Navegación
    builder.button(text="🔙 Volver", callback_data="admin_lore_bulk_operations")

    # Ajuste del layout
    builder.adjust(1)  # Lore pieces en una columna
    action_rows = []
    if total_pages > 1:
        action_rows.append(3)  # Paginación
    action_rows.extend([2])  # Selección
    if selected_ids:
        action_rows.append(1)  # Procesar
    action_rows.append(1)  # Volver

    builder.adjust(*([1] * len(page_lore) + action_rows))

    return builder.as_markup()


def get_bulk_action_confirmation_kb(action: str, count: int) -> InlineKeyboardMarkup:
    """Return confirmation keyboard for bulk actions."""
    builder = InlineKeyboardBuilder()

    # Confirmación específica según la acción
    if action == "delete":
        builder.button(text="🗑️ CONFIRMAR ELIMINACIÓN", callback_data=f"admin_lore_bulk_confirm:{action}")
        builder.button(text="❌ Cancelar", callback_data="admin_lore_bulk_operations")
    elif action == "activate":
        builder.button(text="✅ Activar Fragmentos", callback_data=f"admin_lore_bulk_confirm:{action}")
        builder.button(text="❌ Cancelar", callback_data="admin_lore_bulk_operations")
    elif action == "deactivate":
        builder.button(text="❌ Desactivar Fragmentos", callback_data=f"admin_lore_bulk_confirm:{action}")
        builder.button(text="🔙 Cancelar", callback_data="admin_lore_bulk_operations")
    else:
        builder.button(text="✅ Confirmar", callback_data=f"admin_lore_bulk_confirm:{action}")
        builder.button(text="❌ Cancelar", callback_data="admin_lore_bulk_operations")

    # Vista previa de la acción
    builder.button(text="👁️ Vista Previa", callback_data=f"admin_lore_bulk_preview:{action}")

    builder.adjust(2, 1)
    return builder.as_markup()


# ============================================================================
# CATEGORY MANAGEMENT
# ============================================================================

def get_category_management_kb() -> InlineKeyboardMarkup:
    """Return keyboard for lore category management."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Gestión básica de categorías
    builder.button(text="➕ Crear Categoría", callback_data="admin_lore_create_category")
    builder.button(text="📋 Lista Categorías", callback_data="admin_lore_list_categories")

    # Fila 2: Visualización y organización
    builder.button(text="📂 Ver por Categoría", callback_data="admin_lore_view_by_category")
    builder.button(text="🔄 Reorganizar", callback_data="admin_lore_reorganize_categories")

    # Fila 3: Operaciones avanzadas
    builder.button(text="🔄 Mover Fragmentos", callback_data="admin_lore_move_between_categories")
    builder.button(text="📊 Analytics Categorías", callback_data="admin_lore_category_analytics")

    # Fila 4: Configuración
    builder.button(text="⚙️ Configurar Orden", callback_data="admin_lore_category_order")
    builder.button(text="🏷️ Gestionar Etiquetas", callback_data="admin_lore_category_tags")

    # Fila 5: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_lore_categories")
    builder.button(text="🔙 Volver", callback_data="admin_narrative_lore")

    builder.adjust(2, 2, 2, 2, 2)
    return builder.as_markup()


def get_category_list_kb(categories: list, page: int = 0, items_per_page: int = 10) -> InlineKeyboardMarkup:
    """Return keyboard for category list with actions."""
    builder = InlineKeyboardBuilder()

    # Mostrar categorías de la página actual
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_categories = categories[start_idx:end_idx]

    for category_name, count in page_categories:
        display_name = category_name or "Sin categoría"
        builder.button(
            text=f"📁 {display_name} ({count})",
            callback_data=f"admin_lore_category_detail:{category_name or 'uncategorized'}"
        )

    # Paginación
    total_pages = (len(categories) + items_per_page - 1) // items_per_page
    if total_pages > 1:
        if page > 0:
            builder.button(text="⬅️ Anterior", callback_data=f"admin_lore_categories_page:{page - 1}")

        builder.button(text=f"📄 {page + 1}/{total_pages}", callback_data="admin_lore_categories_page_info")

        if page < total_pages - 1:
            builder.button(text="➡️ Siguiente", callback_data=f"admin_lore_categories_page:{page + 1}")

    # Acciones adicionales
    builder.button(text="➕ Nueva Categoría", callback_data="admin_lore_create_category")
    builder.button(text="📊 Analytics Global", callback_data="admin_lore_category_analytics")

    # Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_lore_list_categories")
    builder.button(text="🔙 Volver", callback_data="admin_lore_categories")

    # Ajuste del layout
    builder.adjust(1)  # Categorías en una columna
    if total_pages > 1:
        builder.adjust(*([1] * len(page_categories) + [3, 2, 2]))
    else:
        builder.adjust(*([1] * len(page_categories) + [2, 2]))

    return builder.as_markup()


def get_category_detail_kb(category_name: str, lore_count: int) -> InlineKeyboardMarkup:
    """Return keyboard for individual category detail and actions."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Visualización
    builder.button(text="📋 Ver Fragmentos", callback_data=f"admin_lore_category_view:{category_name}")
    builder.button(text="📊 Analytics", callback_data=f"admin_lore_category_analytics:{category_name}")

    # Fila 2: Gestión de contenido
    builder.button(text="➕ Agregar Fragmentos", callback_data=f"admin_lore_category_add:{category_name}")
    builder.button(text="🔄 Mover Fragmentos", callback_data=f"admin_lore_category_move:{category_name}")

    # Fila 3: Configuración
    builder.button(text="✏️ Renombrar", callback_data=f"admin_lore_category_rename:{category_name}")
    builder.button(text="📊 Cambiar Orden", callback_data=f"admin_lore_category_reorder:{category_name}")

    # Fila 4: Acciones destructivas (solo si la categoría no está vacía)
    if lore_count > 0:
        builder.button(text="🔄 Reorganizar", callback_data=f"admin_lore_category_reorganize:{category_name}")
        builder.button(text="⚠️ Vaciar Categoría", callback_data=f"admin_lore_category_empty:{category_name}")
    else:
        builder.button(text="🗑️ Eliminar Categoría", callback_data=f"admin_lore_category_delete:{category_name}")

    # Fila 5: Navegación
    builder.button(text="↩️ Volver a Lista", callback_data="admin_lore_list_categories")
    builder.button(text="🏠 Categorías", callback_data="admin_lore_categories")

    builder.adjust(2, 2, 2, 2, 2)
    return builder.as_markup()


# ============================================================================
# LORE PIECE EDITING WORKFLOWS
# ============================================================================

def get_lore_edit_main_kb(lore_id: int) -> InlineKeyboardMarkup:
    """Return main editing keyboard for a lore piece."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Edición de contenido
    builder.button(text="📝 Editar Título", callback_data=f"admin_lore_edit_title:{lore_id}")
    builder.button(text="📄 Editar Contenido", callback_data=f"admin_lore_edit_content:{lore_id}")

    # Fila 2: Metadatos
    builder.button(text="🏷️ Cambiar Categoría", callback_data=f"admin_lore_edit_category:{lore_id}")
    builder.button(text="🔧 Tipo de Contenido", callback_data=f"admin_lore_edit_type:{lore_id}")

    # Fila 3: Condiciones y vínculos
    builder.button(text="🔓 Condiciones Desbloqueo", callback_data=f"admin_lore_edit_conditions:{lore_id}")
    builder.button(text="🔗 Gestionar Vínculos", callback_data=f"admin_lore_manage_links:{lore_id}")

    # Fila 4: Estado y configuración
    builder.button(text="⚡ Alternar Estado", callback_data=f"admin_lore_toggle_status:{lore_id}")
    builder.button(text="📊 Ver Analytics", callback_data=f"admin_lore_analytics_detail:{lore_id}")

    # Fila 5: Navegación
    builder.button(text="↩️ Volver al Detalle", callback_data=f"admin_lore_detail:{lore_id}")
    builder.button(text="🏠 Lista Fragmentos", callback_data="admin_lore_list")

    builder.adjust(2, 2, 2, 2, 2)
    return builder.as_markup()


def get_unlock_condition_types_kb(lore_id: int) -> InlineKeyboardMarkup:
    """Return keyboard for selecting unlock condition types."""
    builder = InlineKeyboardBuilder()

    # Tipos de condiciones de desbloqueo
    builder.button(text="🛒 Compra de Item", callback_data=f"admin_lore_condition:shop_purchase:{lore_id}")
    builder.button(text="💰 Cantidad de Besitos", callback_data=f"admin_lore_condition:currency_amount:{lore_id}")

    builder.button(text="🎯 Nivel de Usuario", callback_data=f"admin_lore_condition:user_level:{lore_id}")
    builder.button(text="📅 Fecha Específica", callback_data=f"admin_lore_condition:date_unlock:{lore_id}")

    builder.button(text="🏆 Logro Específico", callback_data=f"admin_lore_condition:achievement:{lore_id}")
    builder.button(text="📖 Otro Fragmento", callback_data=f"admin_lore_condition:other_lore:{lore_id}")

    builder.button(text="🔓 Sin Condición", callback_data=f"admin_lore_condition:none:{lore_id}")
    builder.button(text="🔒 Siempre Bloqueado", callback_data=f"admin_lore_condition:locked:{lore_id}")

    # Navegación
    builder.button(text="🔙 Volver", callback_data=f"admin_lore_edit:{lore_id}")

    builder.adjust(2, 2, 2, 2, 1)
    return builder.as_markup()


# ============================================================================
# UTILITY AND NAVIGATION KEYBOARDS
# ============================================================================

def get_confirmation_kb(action: str, target_id: int, target_type: str = "lore") -> InlineKeyboardMarkup:
    """Return confirmation keyboard for destructive actions."""
    builder = InlineKeyboardBuilder()

    # Confirmación específica según la acción
    if action == "delete":
        builder.button(text="🗑️ CONFIRMAR ELIMINACIÓN", callback_data=f"admin_{target_type}_{action}_confirm_{target_id}")
        builder.button(text="❌ Cancelar", callback_data=f"admin_{target_type}_detail_{target_id}")
    else:
        builder.button(text="✅ Confirmar", callback_data=f"admin_{target_type}_{action}_confirm_{target_id}")
        builder.button(text="❌ Cancelar", callback_data=f"admin_{target_type}_detail_{target_id}")

    builder.adjust(2)
    return builder.as_markup()


def get_back_to_main_kb() -> InlineKeyboardMarkup:
    """Return simple back to main keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Volver al Dashboard", callback_data="admin_narrative_lore")
    return builder.as_markup()


def get_status_update_kb(current_status: bool, lore_id: int) -> InlineKeyboardMarkup:
    """Return keyboard for status update confirmation."""
    builder = InlineKeyboardBuilder()

    if current_status:
        builder.button(text="❌ Desactivar Fragmento", callback_data=f"admin_lore_set_status:{lore_id}:false")
    else:
        builder.button(text="✅ Activar Fragmento", callback_data=f"admin_lore_set_status:{lore_id}:true")

    builder.button(text="🔙 Cancelar", callback_data=f"admin_lore_edit:{lore_id}")

    builder.adjust(1, 1)
    return builder.as_markup()
