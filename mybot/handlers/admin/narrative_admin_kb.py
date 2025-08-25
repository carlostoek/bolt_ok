"""
Teclados para la administración narrativa.
Define la estructura de teclados y botones para la interfaz de administración de contenido narrativo.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Optional, Dict, Any

def get_narrative_admin_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado principal de administración narrativa.
    
    Returns:
        InlineKeyboardMarkup: Teclado con opciones principales
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Fragmentos", callback_data="admin_fragments_list"),
                InlineKeyboardButton(text="🔖 Storyboard", callback_data="admin_narrative_storyboard")
            ],
            [
                InlineKeyboardButton(text="📊 Analíticas", callback_data="admin_narrative_analytics"),
                InlineKeyboardButton(text="🔍 Buscar", callback_data="admin_narrative_search")
            ],
            [
                InlineKeyboardButton(text="➕ Nuevo Fragmento", callback_data="admin_create_fragment")
            ],
            [
                InlineKeyboardButton(text="🔄 Actualizar", callback_data="admin_narrative_refresh"),
                InlineKeyboardButton(text="🏠 Panel Admin", callback_data="admin_menu")
            ],
        ]
    )
    return keyboard

def get_fragments_list_keyboard(
    page: int = 1, 
    total_pages: int = 1, 
    filter_type: Optional[str] = None
) -> InlineKeyboardMarkup:
    """
    Teclado para listado de fragmentos con paginación.
    
    Args:
        page: Página actual
        total_pages: Total de páginas disponibles
        filter_type: Tipo de fragmento filtrado (STORY, DECISION, INFO)
        
    Returns:
        InlineKeyboardMarkup: Teclado con paginación y filtros
    """
    # Botones de filtro
    filter_buttons = [
        [
            InlineKeyboardButton(
                text="🔄 Todos" if filter_type else "✅ Todos",
                callback_data="admin_fragments_list?filter=all"
            ),
            InlineKeyboardButton(
                text="✅ Historia" if filter_type == "STORY" else "📖 Historia",
                callback_data="admin_fragments_list?filter=STORY"
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Decisión" if filter_type == "DECISION" else "🔀 Decisión",
                callback_data="admin_fragments_list?filter=DECISION"
            ),
            InlineKeyboardButton(
                text="✅ Info" if filter_type == "INFO" else "ℹ️ Info",
                callback_data="admin_fragments_list?filter=INFO"
            )
        ]
    ]
    
    # Botones de paginación
    pagination_buttons = []
    if total_pages > 1:
        row = []
        if page > 1:
            row.append(InlineKeyboardButton(
                text="⬅️ Anterior",
                callback_data=f"admin_fragments_list?page={page-1}&filter={filter_type or 'all'}"
            ))
        
        row.append(InlineKeyboardButton(
            text=f"📄 {page}/{total_pages}",
            callback_data=f"admin_fragments_current_page"
        ))
        
        if page < total_pages:
            row.append(InlineKeyboardButton(
                text="➡️ Siguiente",
                callback_data=f"admin_fragments_list?page={page+1}&filter={filter_type or 'all'}"
            ))
        
        pagination_buttons.append(row)
    
    # Botones de acción
    action_buttons = [
        [
            InlineKeyboardButton(text="🔍 Buscar", callback_data="admin_narrative_search"),
            InlineKeyboardButton(text="➕ Nuevo", callback_data="admin_create_fragment")
        ],
        [
            InlineKeyboardButton(text="◀️ Volver", callback_data="admin_narrative_menu"),
            InlineKeyboardButton(text="🏠 Panel Admin", callback_data="admin_menu")
        ]
    ]
    
    # Combinar todos los botones
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=filter_buttons + pagination_buttons + action_buttons
    )
    return keyboard

def get_fragment_detail_keyboard(fragment_id: str) -> InlineKeyboardMarkup:
    """
    Teclado para detalle de fragmento.
    
    Args:
        fragment_id: ID del fragmento
        
    Returns:
        InlineKeyboardMarkup: Teclado con opciones para gestionar fragmento
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Editar", callback_data=f"admin_edit_fragment?id={fragment_id}"),
                InlineKeyboardButton(text="🔄 Conexiones", callback_data=f"admin_fragment_connections?id={fragment_id}")
            ],
            [
                InlineKeyboardButton(text="📊 Estadísticas", callback_data=f"admin_fragment_stats?id={fragment_id}"),
                InlineKeyboardButton(text="👁️ Ver Usuarios", callback_data=f"admin_fragment_users?id={fragment_id}")
            ],
            [
                InlineKeyboardButton(text="🗑️ Eliminar", callback_data=f"admin_delete_fragment?id={fragment_id}"),
                InlineKeyboardButton(text="📋 Duplicar", callback_data=f"admin_duplicate_fragment?id={fragment_id}")
            ],
            [
                InlineKeyboardButton(text="◀️ Volver", callback_data="admin_fragments_list"),
                InlineKeyboardButton(text="🏠 Panel Admin", callback_data="admin_menu")
            ],
        ]
    )
    return keyboard

def get_fragment_edit_keyboard(fragment_id: str) -> InlineKeyboardMarkup:
    """
    Teclado para edición de fragmento.
    
    Args:
        fragment_id: ID del fragmento
        
    Returns:
        InlineKeyboardMarkup: Teclado con opciones de edición
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Editar Título", callback_data=f"admin_edit_fragment_title?id={fragment_id}"),
                InlineKeyboardButton(text="📄 Editar Contenido", callback_data=f"admin_edit_fragment_content?id={fragment_id}")
            ],
            [
                InlineKeyboardButton(text="🔀 Editar Tipo", callback_data=f"admin_edit_fragment_type?id={fragment_id}"),
                InlineKeyboardButton(text="🔄 Editar Conexiones", callback_data=f"admin_fragment_connections?id={fragment_id}")
            ],
            [
                InlineKeyboardButton(text="🎯 Editar Requisitos", callback_data=f"admin_edit_fragment_requirements?id={fragment_id}"),
                InlineKeyboardButton(text="🔔 Editar Triggers", callback_data=f"admin_edit_fragment_triggers?id={fragment_id}")
            ],
            [
                InlineKeyboardButton(text="📋 Ver Completo", callback_data=f"admin_view_fragment?id={fragment_id}"),
                InlineKeyboardButton(text="◀️ Volver", callback_data=f"admin_view_fragment?id={fragment_id}")
            ],
        ]
    )
    return keyboard

def get_storyboard_keyboard(
    root_fragment_id: Optional[str] = None,
    view_type: str = "tree"
) -> InlineKeyboardMarkup:
    """
    Teclado para visualización de storyboard.
    
    Args:
        root_fragment_id: ID del fragmento raíz del storyboard
        view_type: Tipo de visualización (tree, flow, map)
        
    Returns:
        InlineKeyboardMarkup: Teclado con opciones de visualización
    """
    view_text = {
        "tree": "🌳 Vista Árbol",
        "flow": "📊 Vista Flujo",
        "map": "🗺️ Vista Mapa"
    }
    
    # Botones para cambiar el tipo de visualización
    view_buttons = []
    for key, text in view_text.items():
        if key == view_type:
            # Marcar el tipo de visualización actual
            view_buttons.append(InlineKeyboardButton(
                text=f"✅ {text}",
                callback_data=f"admin_narrative_storyboard?view={key}"
            ))
        else:
            view_buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=f"admin_narrative_storyboard?view={key}"
            ))
    
    # Botones de navegación del storyboard
    nav_buttons = []
    if root_fragment_id:
        nav_buttons = [
            InlineKeyboardButton(text="⬆️ Nivel Superior", callback_data="admin_storyboard_up"),
            InlineKeyboardButton(text="🔍 Expandir", callback_data="admin_storyboard_expand")
        ]
    else:
        nav_buttons = [
            InlineKeyboardButton(text="🏠 Inicio", callback_data="admin_storyboard_root"),
            InlineKeyboardButton(text="🔍 Buscar Fragmento", callback_data="admin_narrative_search")
        ]
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            view_buttons,
            nav_buttons,
            [
                InlineKeyboardButton(text="◀️ Volver", callback_data="admin_narrative_menu"),
                InlineKeyboardButton(text="🏠 Panel Admin", callback_data="admin_menu")
            ],
        ]
    )
    return keyboard

def get_fragment_connections_keyboard(
    fragment_id: str,
    connections: List[Dict[str, Any]] = None
) -> InlineKeyboardMarkup:
    """
    Teclado para gestionar conexiones de un fragmento.
    
    Args:
        fragment_id: ID del fragmento
        connections: Lista de conexiones existentes
        
    Returns:
        InlineKeyboardMarkup: Teclado con opciones de conexión
    """
    buttons = []
    
    # Mostrar conexiones existentes
    if connections and len(connections) > 0:
        for i, connection in enumerate(connections):
            target_id = connection.get("id")
            title = connection.get("title", "Fragmento")
            if len(title) > 20:
                title = title[:17] + "..."
                
            buttons.append([
                InlineKeyboardButton(
                    text=f"{i+1}. {title}",
                    callback_data=f"admin_view_fragment?id={target_id}"
                ),
                InlineKeyboardButton(
                    text="🗑️",
                    callback_data=f"admin_delete_connection?id={fragment_id}&index={i}"
                )
            ])
    
    # Botón para añadir nueva conexión
    buttons.append([
        InlineKeyboardButton(
            text="➕ Añadir Conexión",
            callback_data=f"admin_add_connection?id={fragment_id}"
        )
    ])
    
    # Botones de navegación
    buttons.append([
        InlineKeyboardButton(text="◀️ Volver", callback_data=f"admin_view_fragment?id={fragment_id}"),
        InlineKeyboardButton(text="🏠 Panel Admin", callback_data="admin_menu")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard

def get_narrative_analytics_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado para analíticas narrativas.
    
    Returns:
        InlineKeyboardMarkup: Teclado con opciones de analíticas
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Resumen General", callback_data="admin_narrative_stats_summary"),
                InlineKeyboardButton(text="👤 Analíticas Usuarios", callback_data="admin_narrative_stats_users")
            ],
            [
                InlineKeyboardButton(text="📑 Fragmentos Populares", callback_data="admin_narrative_stats_popular"),
                InlineKeyboardButton(text="🔀 Análisis de Decisiones", callback_data="admin_narrative_stats_decisions")
            ],
            [
                InlineKeyboardButton(text="📈 Gráficos", callback_data="admin_narrative_stats_graphs"),
                InlineKeyboardButton(text="📋 Exportar Datos", callback_data="admin_narrative_stats_export")
            ],
            [
                InlineKeyboardButton(text="◀️ Volver", callback_data="admin_narrative_menu"),
                InlineKeyboardButton(text="🏠 Panel Admin", callback_data="admin_menu")
            ],
        ]
    )
    return keyboard

def get_fragment_type_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado para seleccionar tipo de fragmento.
    
    Returns:
        InlineKeyboardMarkup: Teclado con tipos de fragmento
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📖 Historia (STORY)", callback_data="admin_fragment_type_select?type=STORY")
            ],
            [
                InlineKeyboardButton(text="🔀 Decisión (DECISION)", callback_data="admin_fragment_type_select?type=DECISION")
            ],
            [
                InlineKeyboardButton(text="ℹ️ Información (INFO)", callback_data="admin_fragment_type_select?type=INFO")
            ],
            [
                InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_narrative_menu")
            ],
        ]
    )
    return keyboard

def get_confirm_delete_keyboard(fragment_id: str) -> InlineKeyboardMarkup:
    """
    Teclado para confirmar eliminación de fragmento.
    
    Args:
        fragment_id: ID del fragmento a eliminar
        
    Returns:
        InlineKeyboardMarkup: Teclado con opciones de confirmación
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Sí, eliminar",
                    callback_data=f"admin_confirm_delete_fragment?id={fragment_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ No, cancelar",
                    callback_data=f"admin_view_fragment?id={fragment_id}"
                )
            ],
        ]
    )
    return keyboard

def get_search_results_keyboard(
    results: List[Dict[str, Any]],
    page: int = 1,
    total_pages: int = 1,
    query: str = ""
) -> InlineKeyboardMarkup:
    """
    Teclado para resultados de búsqueda.
    
    Args:
        results: Lista de resultados de búsqueda
        page: Página actual
        total_pages: Total de páginas
        query: Término de búsqueda
        
    Returns:
        InlineKeyboardMarkup: Teclado con resultados y paginación
    """
    buttons = []
    
    # Mostrar resultados
    for result in results:
        fragment_id = result.get("id")
        title = result.get("title", "Fragmento")
        if len(title) > 30:
            title = title[:27] + "..."
            
        buttons.append([
            InlineKeyboardButton(
                text=title,
                callback_data=f"admin_view_fragment?id={fragment_id}"
            )
        ])
    
    # Paginación
    if total_pages > 1:
        pagination = []
        if page > 1:
            pagination.append(InlineKeyboardButton(
                text="⬅️ Anterior",
                callback_data=f"admin_narrative_search_results?page={page-1}&query={query}"
            ))
        
        pagination.append(InlineKeyboardButton(
            text=f"📄 {page}/{total_pages}",
            callback_data=f"admin_search_current_page"
        ))
        
        if page < total_pages:
            pagination.append(InlineKeyboardButton(
                text="➡️ Siguiente",
                callback_data=f"admin_narrative_search_results?page={page+1}&query={query}"
            ))
        
        buttons.append(pagination)
    
    # Navegación
    buttons.append([
        InlineKeyboardButton(text="🔍 Nueva Búsqueda", callback_data="admin_narrative_search"),
        InlineKeyboardButton(text="◀️ Volver", callback_data="admin_narrative_menu")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard