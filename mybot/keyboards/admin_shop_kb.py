from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_shop_admin_main_kb():
    """Return the main shop admin inline keyboard with elegant layout."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Gestión principal de la tienda
    builder.button(text="📦 Gestión de Items", callback_data="admin_shop_items")
    builder.button(text="📁 Gestión de Categorías", callback_data="admin_shop_categories")

    # Fila 2: Análisis y configuración
    builder.button(text="📊 Estadísticas de Ventas", callback_data="admin_shop_stats")
    builder.button(text="🛒 Compras Recientes", callback_data="admin_shop_purchases")

    # Fila 3: Herramientas avanzadas
    builder.button(text="🔍 Buscar Items", callback_data="admin_shop_search")
    builder.button(text="⚙️ Configuración", callback_data="admin_shop_config")

    # Fila 4: Operaciones en lote
    builder.button(text="📤 Exportar Catálogo", callback_data="admin_shop_export")
    builder.button(text="📥 Importar Catálogo", callback_data="admin_shop_import")

    # Fila 5: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_shop_main")
    builder.button(text="↩️ Volver", callback_data="admin_back")

    # Distribución: 2x2, luego 2x2, luego 2
    builder.adjust(2, 2, 2, 2, 2)
    return builder.as_markup()


def get_item_management_kb():
    """Return the item management keyboard for shop administration."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Gestión básica de items
    builder.button(text="➕ Crear Item", callback_data="admin_item_create")
    builder.button(text="📋 Lista de Items", callback_data="admin_item_list")

    # Fila 2: Operaciones en lote
    builder.button(text="✏️ Editar Item", callback_data="admin_item_edit")
    builder.button(text="🗑️ Eliminar Item", callback_data="admin_item_delete")

    # Fila 3: Estado y visibilidad
    builder.button(text="👁️ Activar/Desactivar", callback_data="admin_item_toggle")
    builder.button(text="💎 Configurar VIP", callback_data="admin_item_vip")

    # Fila 4: Herramientas adicionales
    builder.button(text="🏷️ Asignar Categoría", callback_data="admin_item_category")
    builder.button(text="📖 Vincular Lore", callback_data="admin_item_lore")

    # Fila 5: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_shop_items")
    builder.button(text="↩️ Volver", callback_data="admin_shop_main")

    # Distribución: 2x2, luego 2x2, luego 2
    builder.adjust(2, 2, 2, 2, 2)
    return builder.as_markup()


def get_category_management_kb():
    """Return the category management keyboard for shop administration."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Gestión básica de categorías
    builder.button(text="➕ Crear Categoría", callback_data="admin_category_create")
    builder.button(text="📋 Lista de Categorías", callback_data="admin_category_list")

    # Fila 2: Operaciones básicas
    builder.button(text="✏️ Editar Categoría", callback_data="admin_category_edit")
    builder.button(text="🗑️ Eliminar Categoría", callback_data="admin_category_delete")

    # Fila 3: Configuración avanzada
    builder.button(text="📊 Orden de Categorías", callback_data="admin_category_order")
    builder.button(text="💎 Configurar VIP", callback_data="admin_category_vip")

    # Fila 4: Estado y visibilidad
    builder.button(text="👁️ Activar/Desactivar", callback_data="admin_category_toggle")
    builder.button(text="📦 Ver Items", callback_data="admin_category_items")

    # Fila 5: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_shop_categories")
    builder.button(text="↩️ Volver", callback_data="admin_shop_main")

    # Distribución: 2x2, luego 2x2, luego 2
    builder.adjust(2, 2, 2, 2, 2)
    return builder.as_markup()


def get_item_list_navigation_kb(current_page: int = 0, total_pages: int = 1, has_items: bool = True):
    """Return navigation keyboard for item list pagination."""
    builder = InlineKeyboardBuilder()

    if has_items and total_pages > 1:
        # Navegación de páginas
        if current_page > 0:
            builder.button(text="⬅️ Anterior", callback_data=f"admin_item_list_page_{current_page - 1}")

        builder.button(text=f"📄 {current_page + 1}/{total_pages}", callback_data="admin_item_list_info")

        if current_page < total_pages - 1:
            builder.button(text="➡️ Siguiente", callback_data=f"admin_item_list_page_{current_page + 1}")

    # Opciones adicionales
    builder.button(text="🔍 Buscar", callback_data="admin_item_search")
    builder.button(text="📊 Filtrar", callback_data="admin_item_filter")

    # Navegación principal
    builder.button(text="🔄 Actualizar", callback_data="admin_item_list")
    builder.button(text="↩️ Volver", callback_data="admin_shop_items")

    # Ajustar según el número de botones
    if total_pages > 1:
        if current_page == 0:
            builder.adjust(2, 2, 2)  # Sin botón anterior
        elif current_page == total_pages - 1:
            builder.adjust(2, 2, 2)  # Sin botón siguiente
        else:
            builder.adjust(3, 2, 2)  # Con ambos botones
    else:
        builder.adjust(2, 2)

    return builder.as_markup()


def get_category_list_navigation_kb(current_page: int = 0, total_pages: int = 1, has_categories: bool = True):
    """Return navigation keyboard for category list pagination."""
    builder = InlineKeyboardBuilder()

    if has_categories and total_pages > 1:
        # Navegación de páginas
        if current_page > 0:
            builder.button(text="⬅️ Anterior", callback_data=f"admin_category_list_page_{current_page - 1}")

        builder.button(text=f"📄 {current_page + 1}/{total_pages}", callback_data="admin_category_list_info")

        if current_page < total_pages - 1:
            builder.button(text="➡️ Siguiente", callback_data=f"admin_category_list_page_{current_page + 1}")

    # Opciones adicionales
    builder.button(text="📊 Ordenar", callback_data="admin_category_sort")
    builder.button(text="🔍 Buscar", callback_data="admin_category_search")

    # Navegación principal
    builder.button(text="🔄 Actualizar", callback_data="admin_category_list")
    builder.button(text="↩️ Volver", callback_data="admin_shop_categories")

    # Ajustar según el número de botones
    if total_pages > 1:
        if current_page == 0:
            builder.adjust(2, 2, 2)  # Sin botón anterior
        elif current_page == total_pages - 1:
            builder.adjust(2, 2, 2)  # Sin botón siguiente
        else:
            builder.adjust(3, 2, 2)  # Con ambos botones
    else:
        builder.adjust(2, 2)

    return builder.as_markup()


def get_item_detail_kb(item_id: int):
    """Return keyboard for individual item detail view and actions."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Acciones principales
    builder.button(text="✏️ Editar", callback_data=f"admin_item_edit_{item_id}")
    builder.button(text="🗑️ Eliminar", callback_data=f"admin_item_delete_{item_id}")

    # Fila 2: Estado y configuración
    builder.button(text="👁️ Alternar Estado", callback_data=f"admin_item_toggle_{item_id}")
    builder.button(text="💎 Configurar VIP", callback_data=f"admin_item_vip_{item_id}")

    # Fila 3: Relaciones
    builder.button(text="🏷️ Cambiar Categoría", callback_data=f"admin_item_category_{item_id}")
    builder.button(text="📖 Gestionar Lore", callback_data=f"admin_item_lore_{item_id}")

    # Fila 4: Navegación
    builder.button(text="↩️ Volver a Lista", callback_data="admin_item_list")
    builder.button(text="🏠 Menú Principal", callback_data="admin_shop_main")

    builder.adjust(2, 2, 2, 2)
    return builder.as_markup()


def get_category_detail_kb(category_id: int):
    """Return keyboard for individual category detail view and actions."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Acciones principales
    builder.button(text="✏️ Editar", callback_data=f"admin_category_edit_{category_id}")
    builder.button(text="🗑️ Eliminar", callback_data=f"admin_category_delete_{category_id}")

    # Fila 2: Estado y configuración
    builder.button(text="👁️ Alternar Estado", callback_data=f"admin_category_toggle_{category_id}")
    builder.button(text="💎 Configurar VIP", callback_data=f"admin_category_vip_{category_id}")

    # Fila 3: Gestión de contenido
    builder.button(text="📦 Ver Items", callback_data=f"admin_category_items_{category_id}")
    builder.button(text="📊 Cambiar Orden", callback_data=f"admin_category_order_{category_id}")

    # Fila 4: Navegación
    builder.button(text="↩️ Volver a Lista", callback_data="admin_category_list")
    builder.button(text="🏠 Menú Principal", callback_data="admin_shop_main")

    builder.adjust(2, 2, 2, 2)
    return builder.as_markup()


def get_shop_stats_kb():
    """Return keyboard for shop statistics view."""
    builder = InlineKeyboardBuilder()

    # Fila 1: Tipos de estadísticas
    builder.button(text="📊 Ventas Generales", callback_data="admin_shop_stats_sales")
    builder.button(text="💰 Ingresos", callback_data="admin_shop_stats_revenue")

    # Fila 2: Análisis por período
    builder.button(text="📅 Por Día", callback_data="admin_shop_stats_daily")
    builder.button(text="📆 Por Semana", callback_data="admin_shop_stats_weekly")

    # Fila 3: Análisis por tipo
    builder.button(text="💎 Items VIP", callback_data="admin_shop_stats_vip")
    builder.button(text="🆓 Items Gratuitos", callback_data="admin_shop_stats_free")

    # Fila 4: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_shop_stats")
    builder.button(text="↩️ Volver", callback_data="admin_shop_main")

    builder.adjust(2, 2, 2, 2)
    return builder.as_markup()


def get_confirmation_kb(action: str, target_id: int, target_type: str = "item"):
    """Return confirmation keyboard for destructive actions."""
    builder = InlineKeyboardBuilder()

    # Confirmación
    builder.button(text="✅ Confirmar", callback_data=f"admin_{target_type}_{action}_confirm_{target_id}")
    builder.button(text="❌ Cancelar", callback_data=f"admin_{target_type}_detail_{target_id}")

    builder.adjust(2)
    return builder.as_markup()