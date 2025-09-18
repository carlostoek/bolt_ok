from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_channels_kb(channels: list | None = None):
    builder = InlineKeyboardBuilder()
    if channels:
        for channel in channels:
            label = channel.title or str(channel.id)
            builder.button(text=f"❌ {label}", callback_data=f"remove_channel_{channel.id}")
    builder.button(text="➕ Agregar Canal", callback_data="admin_add_channel")
    builder.button(text="⏱ Configurar Espera", callback_data="admin_wait_time")
    builder.button(text="🔙 Volver", callback_data="admin_back")
    builder.adjust(1)
    return builder.as_markup()


def get_wait_time_kb():
    builder = InlineKeyboardBuilder()
    options = [0, 5, 10, 15, 20, 60, 120, 180]
    for m in options:
        label = f"{m} min" if m < 60 else f"{m//60} h"
        if m == 0:
            label = "0 min"
        builder.button(text=label, callback_data=f"wait_{m}")
    builder.button(text="🔙 Volver", callback_data="admin_channels")
    builder.adjust(3)
    return builder.as_markup()


def get_enhanced_channel_kb():
    """
    Enhanced channel administration keyboard with bulk operations and content protection.
    Features prominent bulk operations access and analytics service integration.
    """
    builder = InlineKeyboardBuilder()

    # Row 1: VIP Management and Analytics
    builder.button(text="👤 Gestión VIP", callback_data="channel_vip_management")
    builder.button(text="📊 Analytics Plus", callback_data="channel_analytics_enhanced")

    # Row 2: Bulk Operations (prominent placement)
    builder.button(text="🔄 Ops. Masivas", callback_data="channel_bulk_operations")
    builder.button(text="⚡ Batch VIP", callback_data="channel_bulk_vip_access")

    # Row 3: Content Management
    builder.button(text="🛡️ Protección", callback_data="channel_content_protection")
    builder.button(text="📝 Publicación", callback_data="channel_publish_content")

    # Row 4: Reports and Analytics
    builder.button(text="📈 Reportes", callback_data="channel_generate_report")
    builder.button(text="📊 Analytics Base", callback_data="channel_analytics")

    # Row 5: Configuration and navigation
    builder.button(text="⚙️ Config. Canales", callback_data="admin_channels")
    builder.button(text="🔙 Volver", callback_data="admin_main_menu")

    builder.adjust(2, 2, 2, 2, 2)
    return builder.as_markup()
