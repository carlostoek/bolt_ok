from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def get_narrative_admin_main_kb() -> InlineKeyboardMarkup:
    """
    Returns the main keyboard for the narrative administration panel.

    Implements comprehensive narrative management with access to:
    - Story fragment management with level organization
    - Lore piece management with shop integration
    - Analytics dashboard for user journey tracking
    - System validation and consistency tools
    - Bulk import and export capabilities
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="📖 Fragmentos", callback_data="admin_narrative_fragments")
    builder.button(text="📚 Lore & Historia", callback_data="admin_narrative_lore")
    builder.button(text="📊 Analytics", callback_data="admin_narrative_analytics")
    builder.button(text="🔍 Validar Sistema", callback_data="admin_narrative_validate")
    builder.button(text="📦 Importar/Exportar", callback_data="admin_narrative_import")
    builder.button(text="🎮 Gestión Usuario", callback_data="admin_narrative_user_tools")
    builder.button(text="🔙 Menú Principal", callback_data="admin_main_menu")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

def get_fragment_management_kb() -> InlineKeyboardMarkup:
    """
    Returns the keyboard for managing story fragments.

    Implements requirement 1.1 - Enhanced fragment management with
    level organization and progression path tools.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Crear Fragmento", callback_data="admin_fragment_create")
    builder.button(text="📋 Lista Fragmentos", callback_data="admin_fragment_list")
    builder.button(text="✏️ Editar Fragmento", callback_data="admin_fragment_edit")
    builder.button(text="🗂️ Por Nivel", callback_data="admin_fragment_by_level")
    builder.button(text="🔗 Conexiones", callback_data="admin_fragment_connections")
    builder.button(text="🗑️ Eliminar", callback_data="admin_fragment_delete")
    builder.button(text="🔙 Volver", callback_data="admin_narrative_main")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

def get_lore_management_kb() -> InlineKeyboardMarkup:
    """
    Returns the keyboard for managing lore pieces.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Crear Fragmento", callback_data="admin_lore_create")
    builder.button(text="📚 Lista Fragmentos", callback_data="admin_lore_list")
    builder.button(text="🔗 Vincular Item", callback_data="admin_lore_link_item")
    builder.button(text="📊 Analytics", callback_data="admin_lore_analytics")
    builder.button(text="🏷️ Categorías", callback_data="admin_lore_categories")
    builder.button(text="📦 Operaciones Lote", callback_data="admin_lore_bulk_operations")
    builder.button(text="🔙 Volver", callback_data="admin_narrative_main")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

def get_analytics_overview_kb() -> InlineKeyboardMarkup:
    """
    Returns the keyboard for the analytics overview.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="Fragment Engagement", callback_data="admin_analytics_fragment_engagement")
    builder.button(text="Choice Distribution", callback_data="admin_analytics_choice_distribution")
    builder.button(text="Narrative Bottlenecks", callback_data="admin_analytics_bottlenecks")
    builder.button(text="User Segments", callback_data="admin_analytics_user_segments")
    builder.button(text="Back", callback_data="admin_narrative_main")
    builder.adjust(2, 2, 1)
    return builder.as_markup()

def get_pagination_kb(current_page: int, total_pages: int, callback_prefix: str) -> InlineKeyboardMarkup:
    """
    Generic pagination keyboard.
    """
    builder = InlineKeyboardBuilder()
    if current_page > 0:
        builder.button(text="<< Prev", callback_data=f"{callback_prefix}:{current_page - 1}")
    builder.button(text=f"{current_page + 1} / {total_pages}", callback_data="noop")
    if current_page < total_pages - 1:
        builder.button(text="Next >>", callback_data=f"{callback_prefix}:{current_page + 1}")
    builder.adjust(3)
    return builder.as_markup()
