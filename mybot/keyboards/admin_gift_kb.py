"""
Keyboards para el Gift Service Admin Panel
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_gift_main_keyboard():
    """Menú principal del Gift Service"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎁 Enviar Regalo", callback_data="gift_send")
            ],
            [
                InlineKeyboardButton(text="📊 Estadísticas", callback_data="gift_stats"),
                InlineKeyboardButton(text="📋 Historial", callback_data="gift_history")
            ],
            [
                InlineKeyboardButton(text="🔙 Volver", callback_data="cms_main")
            ]
        ]
    )
    return keyboard


def get_event_type_keyboard():
    """Teclado para seleccionar tipo de evento"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏆 Ganó Subasta", callback_data="gift_event_auction_won")],
            [InlineKeyboardButton(text="🛍️ Compró en Tienda", callback_data="gift_event_shop_purchase")],
            [InlineKeyboardButton(text="🎯 Alcanzó Nivel", callback_data="gift_event_level_reached")],
            [InlineKeyboardButton(text="💝 Sorpresa Espontánea", callback_data="gift_event_surprise")],
            [InlineKeyboardButton(text="💎 Recompensa Lealtad", callback_data="gift_event_loyalty")],
            [InlineKeyboardButton(text="🎂 Cumpleaños", callback_data="gift_event_birthday")],
            [InlineKeyboardButton(text="✨ Personalizado", callback_data="gift_event_custom")],
            [InlineKeyboardButton(text="🔙 Cancelar", callback_data="gift_main")]
        ]
    )
    return keyboard


def get_gift_sets_keyboard(sets, page=0, per_page=5):
    """
    Genera teclado con lista de content sets para regalar

    Args:
        sets: Lista de ContentSet objetos
        page: Página actual
        per_page: Sets por página
    """
    builder = InlineKeyboardBuilder()

    # Calcular rango
    start = page * per_page
    end = start + per_page
    page_sets = sets[start:end]

    # Botones de sets
    for content_set in page_sets:
        type_emoji = {
            "photo_set": "📸",
            "video": "🎬",
            "audio": "🎵",
            "mixed": "🎭"
        }.get(content_set.type, "📦")

        button_text = f"{type_emoji} {content_set.name}"
        builder.button(
            text=button_text,
            callback_data=f"gift_select_{content_set.id}"
        )

    builder.adjust(1)

    # Navegación
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Anterior", callback_data=f"gift_sets_page_{page-1}"))
    if end < len(sets):
        nav_buttons.append(InlineKeyboardButton(text="▶️ Siguiente", callback_data=f"gift_sets_page_{page+1}"))

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="🔙 Cancelar", callback_data="gift_main"))

    return builder.as_markup()


def get_custom_message_keyboard():
    """Teclado para decidir si agregar mensaje personalizado"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Mensaje Personalizado", callback_data="gift_custom_yes")],
            [InlineKeyboardButton(text="📋 Usar Template", callback_data="gift_custom_no")],
            [InlineKeyboardButton(text="🔙 Cancelar", callback_data="gift_main")]
        ]
    )
    return keyboard


def get_confirm_gift_keyboard():
    """Teclado de confirmación para enviar regalo"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Enviar Regalo", callback_data="gift_confirm_send"),
                InlineKeyboardButton(text="❌ Cancelar", callback_data="gift_main")
            ]
        ]
    )
    return keyboard


def get_user_segment_keyboard():
    """Teclado para seleccionar segmento de usuarios (envío masivo)"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Todos los VIP", callback_data="gift_segment_vip")],
            [InlineKeyboardButton(text="🆓 Todos los Free", callback_data="gift_segment_free")],
            [InlineKeyboardButton(text="☀️ Arquetipo Luz", callback_data="gift_segment_luz")],
            [InlineKeyboardButton(text="🌙 Arquetipo Sombra", callback_data="gift_segment_sombra")],
            [InlineKeyboardButton(text="👥 Todos", callback_data="gift_segment_all")],
            [InlineKeyboardButton(text="🔙 Cancelar", callback_data="gift_main")]
        ]
    )
    return keyboard
