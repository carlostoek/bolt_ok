from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_experiences_main_kb():
    """Return the main experiences management keyboard."""
    builder = InlineKeyboardBuilder()
    
    # Fila 1: Experiencias principales
    builder.button(text="📋 Lista de Experiencias", callback_data="admin_experiences_list")
    builder.button(text="✨ Nueva Experiencia", callback_data="admin_experience_create")
    
    # Fila 2: Gestión de elementos
    builder.button(text="🔍 Ver Elementos", callback_data="admin_experience_elements")
    builder.button(text="⚙️ Configuración", callback_data="admin_experience_config")
    
    # Fila 3: Navegación
    builder.button(text="🔄 Actualizar", callback_data="admin_experiences_main")
    builder.button(text="🏠 Panel Admin", callback_data="admin_main_menu")
    
    builder.adjust(2, 2, 2)
    return builder.as_markup()


def get_admin_experiences_list_kb(experiences, page=0, page_size=5):
    """Return keyboard for experiences list with pagination."""
    builder = InlineKeyboardBuilder()
    
    # Add experience buttons
    start_idx = page * page_size
    end_idx = start_idx + page_size
    
    for experience in experiences[start_idx:end_idx]:
        builder.button(
            text=f"{experience.name} ({'✅' if experience.is_active else '❌'})", 
            callback_data=f"admin_experience_view_{experience.id}"
        )
    
    # Pagination controls
    if page > 0:
        builder.button(text="⬅️ Anterior", callback_data=f"admin_experiences_list_{page-1}")
    
    if end_idx < len(experiences):
        builder.button(text="➡️ Siguiente", callback_data=f"admin_experiences_list_{page+1}")
    
    # Navigation
    builder.button(text="✨ Nueva Experiencia", callback_data="admin_experience_create")
    builder.button(text="🏠 Panel Principal", callback_data="admin_experiences_main")
    
    # Adjust layout based on content
    if experiences:
        builder.adjust(1, 2, 2)
    else:
        builder.adjust(2)
    
    return builder.as_markup()


def get_admin_experience_view_kb(experience_id):
    """Return keyboard for viewing a specific experience."""
    builder = InlineKeyboardBuilder()
    
    # Main actions
    builder.button(text="✏️ Editar", callback_data=f"admin_experience_edit_{experience_id}")
    builder.button(text="🔄 Estado", callback_data=f"admin_experience_toggle_{experience_id}")
    
    # Element management
    builder.button(text="📖 Fragmentos", callback_data=f"admin_experience_fragments_{experience_id}")
    builder.button(text="🛒 Items", callback_data=f"admin_experience_items_{experience_id}")
    builder.button(text="🎯 Misiones", callback_data=f"admin_experience_missions_{experience_id}")
    
    # Navigation
    builder.button(text="📋 Lista", callback_data="admin_experiences_list")
    builder.button(text="🏠 Principal", callback_data="admin_experiences_main")
    
    builder.adjust(2, 3, 2)
    return builder.as_markup()


def get_admin_experience_elements_kb():
    """Return keyboard for viewing all propagated elements."""
    builder = InlineKeyboardBuilder()
    
    # Element types
    builder.button(text="📖 Fragmentos Narrativos", callback_data="admin_experience_all_fragments")
    builder.button(text="🛒 Items de Tienda", callback_data="admin_experience_all_items")
    builder.button(text="🎯 Misiones", callback_data="admin_experience_all_missions")
    
    # Navigation
    builder.button(text="🏠 Panel Principal", callback_data="admin_experiences_main")
    
    builder.adjust(1, 1, 1, 1)
    return builder.as_markup()


def get_admin_experience_back_kb(target="admin_experiences_main"):
    """Return simple back navigation keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="↩️ Volver", callback_data=target)
    return builder.as_markup()


# Wizard-specific keyboards
def get_admin_experience_wizard_start_kb():
    """Return keyboard for starting the experience wizard."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✨ Iniciar Asistente", callback_data="admin_experience_wizard_start")
    builder.button(text="📋 Ver Lista", callback_data="admin_experiences_list")
    builder.button(text="🏠 Panel Principal", callback_data="admin_experiences_main")
    
    builder.adjust(1, 2)
    return builder.as_markup()


def get_admin_experience_wizard_step_kb(next_button_text, next_callback_data):
    """Return keyboard for wizard steps with next/cancel options."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text=next_button_text, callback_data=next_callback_data)
    builder.button(text="❌ Cancelar", callback_data="admin_experience_wizard_cancel")
    
    builder.adjust(1, 1)
    return builder.as_markup()


def get_admin_experience_wizard_confirm_kb():
    """Return keyboard for final confirmation step."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ Crear Experiencia", callback_data="admin_experience_wizard_confirm")
    builder.button(text="✏️ Editar Información", callback_data="admin_experience_wizard_requirements")
    builder.button(text="❌ Cancelar", callback_data="admin_experience_wizard_cancel")
    
    builder.adjust(1, 2)
    return builder.as_markup()


def get_admin_experience_wizard_cancel_kb():
    """Return keyboard for cancel operations in wizard."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="❌ Cancelar", callback_data="admin_experience_wizard_cancel")
    
    builder.adjust(1)
    return builder.as_markup()


def get_admin_experience_wizard_requirements_kb():
    """Return keyboard for requirements configuration."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📊 Nivel: 0 (Sin requisito)", callback_data="admin_experience_wizard_level_0")
    builder.button(text="📊 Nivel: 1", callback_data="admin_experience_wizard_level_1")
    builder.button(text="📊 Nivel: 3", callback_data="admin_experience_wizard_level_3")
    builder.button(text="📊 Nivel: 5", callback_data="admin_experience_wizard_level_5")
    builder.button(text="📊 Nivel: 10", callback_data="admin_experience_wizard_level_10")
    
    builder.button(text="💎 VIP: No requerido", callback_data="admin_experience_wizard_vip_false")
    builder.button(text="💎 VIP: Requerido", callback_data="admin_experience_wizard_vip_true")
    
    builder.button(text="✅ Guardar Requisitos", callback_data="admin_experience_wizard_elements")
    builder.button(text="❌ Cancelar", callback_data="admin_experience_wizard_cancel")
    
    builder.adjust(2, 2, 2, 1, 1, 2)
    return builder.as_markup()


def get_admin_experience_wizard_elements_kb():
    """Return keyboard for elements configuration."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📖 Narrativa: Incluir", callback_data="admin_experience_wizard_narrative_true")
    builder.button(text="📖 Narrativa: No incluir", callback_data="admin_experience_wizard_narrative_false")
    
    builder.button(text="🛒 Tienda: Incluir", callback_data="admin_experience_wizard_shop_true")
    builder.button(text="🛒 Tienda: No incluir", callback_data="admin_experience_wizard_shop_false")
    
    builder.button(text="🎯 Misiones: Incluir", callback_data="admin_experience_wizard_missions_true")
    builder.button(text="🎯 Misiones: No incluir", callback_data="admin_experience_wizard_missions_false")
    
    builder.button(text="✅ Guardar Elementos", callback_data="admin_experience_wizard_rewards")
    builder.button(text="❌ Cancelar", callback_data="admin_experience_wizard_cancel")
    
    builder.adjust(2, 2, 2, 2)
    return builder.as_markup()


def get_admin_experience_wizard_rewards_kb():
    """Return keyboard for rewards configuration."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="💰 Puntos: 0", callback_data="admin_experience_wizard_points_0")
    builder.button(text="💰 Puntos: 50", callback_data="admin_experience_wizard_points_50")
    builder.button(text="💰 Puntos: 100", callback_data="admin_experience_wizard_points_100")
    builder.button(text="💰 Puntos: 200", callback_data="admin_experience_wizard_points_200")
    builder.button(text="💰 Puntos: 500", callback_data="admin_experience_wizard_points_500")
    
    builder.button(text="💎 Días VIP: 0", callback_data="admin_experience_wizard_vip_days_0")
    builder.button(text="💎 Días VIP: 1", callback_data="admin_experience_wizard_vip_days_1")
    builder.button(text="💎 Días VIP: 3", callback_data="admin_experience_wizard_vip_days_3")
    builder.button(text="💎 Días VIP: 7", callback_data="admin_experience_wizard_vip_days_7")
    
    builder.button(text="✅ Guardar Recompensas", callback_data="admin_experience_wizard_review")
    builder.button(text="❌ Cancelar", callback_data="admin_experience_wizard_cancel")
    
    builder.adjust(3, 2, 2, 2, 2)
    return builder.as_markup()