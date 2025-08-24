from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_tarifas_kb(tariffs=None):
    """Keyboard showing information about the updated VIP system."""
    builder = InlineKeyboardBuilder()
    builder.button(text="ℹ️ Sistema Actualizado", callback_data="info_vip_system")
    builder.button(text="🔙 Volver", callback_data="vip_config")
    builder.adjust(1)
    return builder.as_markup()


def get_tariff_options_kb(tariff_id: int):
    """Keyboard showing information about the updated VIP system."""
    builder = InlineKeyboardBuilder()
    builder.button(text="ℹ️ Sistema Actualizado", callback_data="info_vip_system")
    builder.button(text="🔙 Volver", callback_data="config_tarifas")
    builder.adjust(1)
    return builder.as_markup()


def get_duration_kb():
    """Keyboard showing information about the updated VIP system."""
    builder = InlineKeyboardBuilder()
    builder.button(text="ℹ️ Sistema Actualizado", callback_data="info_vip_system")
    builder.button(text="🔙 Volver", callback_data="config_tarifas")
    builder.adjust(1)
    return builder.as_markup()


def get_plan_list_kb(plans):
    """Keyboard showing information about the updated VIP system."""
    builder = InlineKeyboardBuilder()
    builder.button(text="ℹ️ Sistema Actualizado", callback_data="info_vip_system")
    builder.adjust(1)
    return builder.as_markup()