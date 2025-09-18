"""
Enhanced VIP Keyboard Layouts for Advanced VIP Management

Provides keyboard layouts for the enhanced VIP handlers with batch operations,
analytics navigation, and comprehensive VIP management features.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional

def get_enhanced_vip_main_kb() -> InlineKeyboardMarkup:
    """
    Main enhanced VIP management keyboard with advanced features.

    Returns:
        InlineKeyboardMarkup with enhanced VIP management options
    """
    builder = InlineKeyboardBuilder()

    # Row 1: Token generation
    builder.button(text="🎫 Token Individual", callback_data="vip_enhanced_single_token")
    builder.button(text="📦 Lote de Tokens", callback_data="vip_enhanced_batch_tokens")

    # Row 2: Analytics and users
    builder.button(text="📊 Analytics", callback_data="vip_enhanced_analytics")
    builder.button(text="👥 Usuarios VIP", callback_data="vip_enhanced_users_list")

    # Row 3: Automation and management
    builder.button(text="🔔 Recordatorios", callback_data="vip_enhanced_reminders")
    builder.button(text="🎯 Gestión", callback_data="vip_enhanced_management")

    # Row 4: Navigation
    builder.button(text="🔄 Actualizar", callback_data="vip_enhanced_refresh")
    builder.button(text="🔙 Volver", callback_data="admin_main_menu")

    builder.adjust(2, 2, 2, 2)
    return builder.as_markup()

def get_batch_token_quantities_kb(tariff_id: int) -> InlineKeyboardMarkup:
    """
    Keyboard for selecting batch token quantities.

    Args:
        tariff_id: ID of the tariff for which to generate tokens

    Returns:
        InlineKeyboardMarkup with quantity selection buttons
    """
    builder = InlineKeyboardBuilder()

    # Predefined quantities
    quantities = [5, 10, 25, 50]
    for qty in quantities:
        builder.button(
            text=f"{qty} tokens",
            callback_data=f"vip_batch_qty_{tariff_id}_{qty}"
        )

    # Custom quantity option
    builder.button(
        text="✏️ Cantidad personalizada",
        callback_data=f"vip_batch_custom_{tariff_id}"
    )

    # Navigation
    builder.button(text="🔙 Volver", callback_data="vip_enhanced_batch_tokens")

    builder.adjust(2, 1, 1)
    return builder.as_markup()

def get_vip_analytics_kb() -> InlineKeyboardMarkup:
    """
    Keyboard for VIP analytics navigation.

    Returns:
        InlineKeyboardMarkup with analytics options
    """
    builder = InlineKeyboardBuilder()

    # Analytics categories
    builder.button(text="💰 Ingresos", callback_data="vip_analytics_revenue")
    builder.button(text="📈 Tendencias", callback_data="vip_analytics_trends")
    builder.button(text="👥 Engagement", callback_data="vip_analytics_engagement")
    builder.button(text="📊 Resumen", callback_data="vip_analytics_summary")

    # Export and refresh
    builder.button(text="📋 Exportar", callback_data="vip_analytics_export")
    builder.button(text="🔄 Actualizar", callback_data="vip_enhanced_analytics")

    # Navigation
    builder.button(text="🔙 Volver", callback_data="admin_vip_enhanced")

    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

def get_vip_users_management_kb() -> InlineKeyboardMarkup:
    """
    Keyboard for VIP users management.

    Returns:
        InlineKeyboardMarkup with user management options
    """
    builder = InlineKeyboardBuilder()

    # User management options
    builder.button(text="📊 Estadísticas", callback_data="vip_users_stats")
    builder.button(text="⚠️ Por Expirar", callback_data="vip_users_expiring")
    builder.button(text="🔔 Recordatorios", callback_data="vip_enhanced_reminders")
    builder.button(text="📋 Exportar", callback_data="vip_users_export")

    # Refresh and navigation
    builder.button(text="🔄 Actualizar", callback_data="vip_enhanced_users_list")
    builder.button(text="🔙 Volver", callback_data="admin_vip_enhanced")

    builder.adjust(2, 2, 2)
    return builder.as_markup()

def get_vip_reminders_kb(is_running: bool = False) -> InlineKeyboardMarkup:
    """
    Keyboard for VIP reminder management.

    Args:
        is_running: Whether reminder automation is currently running

    Returns:
        InlineKeyboardMarkup with reminder management options
    """
    builder = InlineKeyboardBuilder()

    # Start/stop button based on current state
    if is_running:
        builder.button(text="⏸️ Pausar Recordatorios", callback_data="vip_reminders_stop")
    else:
        builder.button(text="▶️ Iniciar Recordatorios", callback_data="vip_reminders_start")

    # Management options
    builder.button(text="🔄 Estado", callback_data="vip_reminders_status")
    builder.button(text="⚙️ Configurar", callback_data="vip_reminders_config")
    builder.button(text="📊 Historial", callback_data="vip_reminders_history")

    # Navigation
    builder.button(text="🔙 Volver", callback_data="admin_vip_enhanced")

    builder.adjust(2, 2, 1)
    return builder.as_markup()

def get_tariff_selection_kb(tariffs: List, action_prefix: str = "vip_batch_tariff") -> InlineKeyboardMarkup:
    """
    Keyboard for tariff selection.

    Args:
        tariffs: List of Tariff objects
        action_prefix: Prefix for callback data

    Returns:
        InlineKeyboardMarkup with tariff selection buttons
    """
    builder = InlineKeyboardBuilder()

    for tariff in tariffs:
        builder.button(
            text=f"💎 {tariff.name} - {tariff.duration_days}d (${tariff.price})",
            callback_data=f"{action_prefix}_{tariff.id}"
        )

    # Navigation
    builder.button(text="🔙 Volver", callback_data="admin_vip_enhanced")

    builder.adjust(1)
    return builder.as_markup()

def get_batch_result_kb(tariff_id: int, quantity: int) -> InlineKeyboardMarkup:
    """
    Keyboard for batch token generation results.

    Args:
        tariff_id: ID of the tariff used
        quantity: Number of tokens generated

    Returns:
        InlineKeyboardMarkup with result actions
    """
    builder = InlineKeyboardBuilder()

    # Result actions
    builder.button(text="📋 Exportar Lista", callback_data=f"vip_batch_export_{tariff_id}_{quantity}")
    builder.button(text="📊 Ver Analytics", callback_data="vip_enhanced_analytics")

    # Generate more or navigate
    builder.button(text="🔄 Generar Más", callback_data="vip_enhanced_batch_tokens")
    builder.button(text="🔙 Volver", callback_data="admin_vip_enhanced")

    builder.adjust(2, 2)
    return builder.as_markup()

def get_analytics_detail_kb(analytics_type: str) -> InlineKeyboardMarkup:
    """
    Keyboard for detailed analytics views.

    Args:
        analytics_type: Type of analytics being displayed

    Returns:
        InlineKeyboardMarkup with detail navigation options
    """
    builder = InlineKeyboardBuilder()

    # Detail view options
    builder.button(text="📊 Vista Completa", callback_data="vip_enhanced_analytics")
    builder.button(text="📋 Exportar Datos", callback_data=f"vip_export_{analytics_type}")

    # Time range options
    builder.button(text="📅 7 días", callback_data=f"vip_analytics_{analytics_type}_7d")
    builder.button(text="📅 30 días", callback_data=f"vip_analytics_{analytics_type}_30d")
    builder.button(text="📅 90 días", callback_data=f"vip_analytics_{analytics_type}_90d")

    # Navigation
    builder.button(text="🔙 Volver", callback_data="vip_enhanced_analytics")

    builder.adjust(2, 3, 1)
    return builder.as_markup()

def get_user_action_kb(user_id: int) -> InlineKeyboardMarkup:
    """
    Keyboard for individual user actions.

    Args:
        user_id: ID of the user

    Returns:
        InlineKeyboardMarkup with user-specific actions
    """
    builder = InlineKeyboardBuilder()

    # User actions
    builder.button(text="📊 Ver Perfil", callback_data=f"vip_user_profile_{user_id}")
    builder.button(text="📅 Extender", callback_data=f"vip_user_extend_{user_id}")
    builder.button(text="🔔 Recordar", callback_data=f"vip_user_remind_{user_id}")
    builder.button(text="❌ Revocar", callback_data=f"vip_user_revoke_{user_id}")

    # Navigation
    builder.button(text="🔙 Lista", callback_data="vip_enhanced_users_list")

    builder.adjust(2, 2, 1)
    return builder.as_markup()

def get_confirmation_kb(action: str, item_id: str) -> InlineKeyboardMarkup:
    """
    Keyboard for confirmation dialogs.

    Args:
        action: Action to confirm
        item_id: ID of the item being acted upon

    Returns:
        InlineKeyboardMarkup with confirmation options
    """
    builder = InlineKeyboardBuilder()

    # Confirmation buttons
    builder.button(text="✅ Confirmar", callback_data=f"vip_confirm_{action}_{item_id}")
    builder.button(text="❌ Cancelar", callback_data=f"vip_cancel_{action}_{item_id}")

    builder.adjust(2)
    return builder.as_markup()

def get_export_options_kb(data_type: str) -> InlineKeyboardMarkup:
    """
    Keyboard for data export options.

    Args:
        data_type: Type of data to export

    Returns:
        InlineKeyboardMarkup with export format options
    """
    builder = InlineKeyboardBuilder()

    # Export formats
    builder.button(text="📄 Texto", callback_data=f"vip_export_{data_type}_text")
    builder.button(text="📊 CSV", callback_data=f"vip_export_{data_type}_csv")
    builder.button(text="📋 JSON", callback_data=f"vip_export_{data_type}_json")

    # Navigation
    builder.button(text="🔙 Volver", callback_data="admin_vip_enhanced")

    builder.adjust(3, 1)
    return builder.as_markup()