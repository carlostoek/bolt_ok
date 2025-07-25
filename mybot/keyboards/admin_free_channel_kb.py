"""
Keyboards for free channel administration.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, Any


def create_free_channel_config_keyboard(stats: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Crear teclado para configuración del canal gratuito.
    
    Args:
        stats: Estadísticas del canal gratuito
    """
    buttons = []
    
    # Primera fila - Configuraciones básicas
    buttons.append([
        InlineKeyboardButton(
            text="⏰ Tiempo de Espera", 
            callback_data="config_wait_time"
        ),
        InlineKeyboardButton(
            text="📱 Mensaje Social", 
            callback_data="config_social_message"
        )
    ])
    
    # Segunda fila - Mensaje de bienvenida
    buttons.append([
        InlineKeyboardButton(
            text="🎉 Mensaje de Bienvenida", 
            callback_data="config_welcome_message"
        )
    ])
    
    # Tercera fila - Información y estadísticas
    if stats.get('pending_requests', 0) > 0:
        buttons.append([
            InlineKeyboardButton(
                text=f"📋 Ver Pendientes ({stats['pending_requests']})", 
                callback_data="view_pending_requests"
            ),
            InlineKeyboardButton(
                text="🔄 Procesar Ahora", 
                callback_data="test_approval_flow"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="📋 Ver Pendientes", 
                callback_data="view_pending_requests"
            ),
            InlineKeyboardButton(
                text="🔄 Procesar Ahora", 
                callback_data="test_approval_flow"
            )
        ])
    
    # Cuarta fila - Canal y estadísticas
    if stats.get('channel_configured'):
        buttons.append([
            InlineKeyboardButton(
                text="📊 Estadísticas Detalladas", 
                callback_data="channel_detailed_stats"
            )
        ])
    
    # Quinta fila - Toggle auto-approval (si está disponible)
    buttons.append([
        InlineKeyboardButton(
            text="🔧 Configuración Avanzada", 
            callback_data="advanced_channel_config"
        )
    ])
    
    # Sexta fila - Volver
    buttons.append([
        InlineKeyboardButton(
            text="🔙 Volver", 
            callback_data="admin_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_channel_stats_keyboard() -> InlineKeyboardMarkup:
    """Crear teclado para estadísticas detalladas del canal."""
    buttons = [
        [
            InlineKeyboardButton(
                text="📊 Exportar Datos", 
                callback_data="export_channel_data"
            ),
            InlineKeyboardButton(
                text="🧹 Limpiar Antiguos", 
                callback_data="cleanup_old_requests"
            )
        ],
        [
            InlineKeyboardButton(
                text="📈 Métricas Semanales", 
                callback_data="weekly_channel_metrics"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Volver", 
                callback_data="admin_free_channel_config"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_advanced_config_keyboard(auto_approval_enabled: bool = True) -> InlineKeyboardMarkup:
    """Crear teclado para configuración avanzada."""
    approval_text = "🔴 Desactivar Auto-aprobación" if auto_approval_enabled else "🟢 Activar Auto-aprobación"
    
    buttons = [
        [
            InlineKeyboardButton(
                text=approval_text, 
                callback_data="toggle_auto_approval"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔗 Crear Enlace de Invitación", 
                callback_data="create_invite_link"
            )
        ],
        [
            InlineKeyboardButton(
                text="📝 Configurar Canal", 
                callback_data="set_free_channel"
            ),
            InlineKeyboardButton(
                text="🧹 Limpiar Todo", 
                callback_data="clear_all_requests"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Volver", 
                callback_data="admin_free_channel_config"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
    """Crear teclado de confirmación para acciones peligrosas."""
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Confirmar", 
                callback_data=f"confirm_{action}"
            ),
            InlineKeyboardButton(
                text="❌ Cancelar", 
                callback_data="admin_free_channel_config"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)