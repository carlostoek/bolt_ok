"""
Keyboards para el CMS de contenido (Content Management System)
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_cms_main_keyboard():
    """Menú principal del CMS"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📤 Subir Nuevo Set", callback_data="cms_create_set")
            ],
            [
                InlineKeyboardButton(text="📋 Ver Sets", callback_data="cms_list_sets"),
                InlineKeyboardButton(text="🔍 Buscar Set", callback_data="cms_search_set")
            ],
            [
                InlineKeyboardButton(text="📨 Enviar Set a Usuario", callback_data="cms_send_set"),
                InlineKeyboardButton(text="📊 Estadísticas", callback_data="cms_stats")
            ],
            [
                InlineKeyboardButton(text="🎯 Journey Management", callback_data="journey_main")
            ],
            [
                InlineKeyboardButton(text="🔙 Volver", callback_data="admin_manage_content")
            ]
        ]
    )
    return keyboard


def get_content_type_keyboard():
    """Teclado para seleccionar tipo de contenido"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Set de Fotos", callback_data="cms_type_photo_set")],
            [InlineKeyboardButton(text="🎬 Video", callback_data="cms_type_video")],
            [InlineKeyboardButton(text="🎵 Audio", callback_data="cms_type_audio")],
            [InlineKeyboardButton(text="🎭 Mixto (Fotos + Videos)", callback_data="cms_type_mixed")],
            [InlineKeyboardButton(text="🔙 Cancelar", callback_data="cms_main")]
        ]
    )
    return keyboard


def get_tier_keyboard():
    """Teclado para seleccionar tier del contenido"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🆓 Free", callback_data="cms_tier_free")],
            [InlineKeyboardButton(text="⭐ VIP", callback_data="cms_tier_vip")],
            [InlineKeyboardButton(text="🎁 Gift/Milestone", callback_data="cms_tier_gift")],
            [InlineKeyboardButton(text="💎 Premium", callback_data="cms_tier_premium")],
            [InlineKeyboardButton(text="🔙 Cancelar", callback_data="cms_main")]
        ]
    )
    return keyboard


def get_category_keyboard():
    """Teclado para seleccionar categoría del contenido"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👁️ Teaser", callback_data="cms_cat_teaser")],
            [InlineKeyboardButton(text="👋 Bienvenida", callback_data="cms_cat_welcome")],
            [InlineKeyboardButton(text="🎯 Milestone", callback_data="cms_cat_milestone")],
            [InlineKeyboardButton(text="🎉 Sorpresa", callback_data="cms_cat_surprise")],
            [InlineKeyboardButton(text="🎁 Regalo", callback_data="cms_cat_gift")],
            [InlineKeyboardButton(text="➡️ Omitir", callback_data="cms_cat_skip")],
            [InlineKeyboardButton(text="🔙 Cancelar", callback_data="cms_main")]
        ]
    )
    return keyboard


def get_archetype_keyboard():
    """Teclado para seleccionar arquetipo"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="☀️ Luz (Diurno)", callback_data="cms_arch_luz")],
            [InlineKeyboardButton(text="🌙 Sombra (Nocturno)", callback_data="cms_arch_sombra")],
            [InlineKeyboardButton(text="🌐 Todos", callback_data="cms_arch_all")],
            [InlineKeyboardButton(text="🔙 Cancelar", callback_data="cms_main")]
        ]
    )
    return keyboard


def get_file_upload_keyboard():
    """Teclado durante el proceso de subida de archivos"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Listo, Continuar", callback_data="cms_files_done")],
            [InlineKeyboardButton(text="🔙 Cancelar", callback_data="cms_main")]
        ]
    )
    return keyboard


def get_sets_list_keyboard(sets, page=0, per_page=5):
    """
    Genera teclado con lista de sets

    Args:
        sets: Lista de ContentSet objetos
        page: Página actual (0-indexed)
        per_page: Cantidad de sets por página
    """
    builder = InlineKeyboardBuilder()

    # Calcular rango de sets para esta página
    start = page * per_page
    end = start + per_page
    page_sets = sets[start:end]

    # Botones de sets
    for content_set in page_sets:
        # Emoji según tipo
        type_emoji = {
            "photo_set": "📸",
            "video": "🎬",
            "audio": "🎵",
            "mixed": "🎭"
        }.get(content_set.type, "📦")

        # Emoji según tier
        tier_emoji = {
            "free": "🆓",
            "vip": "⭐",
            "gift": "🎁",
            "premium": "💎"
        }.get(content_set.tier, "")

        button_text = f"{type_emoji}{tier_emoji} {content_set.name}"
        builder.button(
            text=button_text,
            callback_data=f"cms_view_set_{content_set.id}"
        )

    builder.adjust(1)

    # Botones de navegación
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Anterior", callback_data=f"cms_list_page_{page-1}"))
    if end < len(sets):
        nav_buttons.append(InlineKeyboardButton(text="▶️ Siguiente", callback_data=f"cms_list_page_{page+1}"))

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="🔙 Volver", callback_data="cms_main"))

    return builder.as_markup()


def get_set_actions_keyboard(set_id: str):
    """Teclado de acciones para un set específico"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📨 Enviar a Usuario", callback_data=f"cms_send_{set_id}"),
                InlineKeyboardButton(text="✏️ Editar", callback_data=f"cms_edit_{set_id}")
            ],
            [
                InlineKeyboardButton(text="📊 Ver Estadísticas", callback_data=f"cms_stats_{set_id}"),
                InlineKeyboardButton(text="🔍 Ver Archivos", callback_data=f"cms_files_{set_id}")
            ],
            [
                InlineKeyboardButton(text="🗑️ Desactivar", callback_data=f"cms_deactivate_{set_id}"),
                InlineKeyboardButton(text="❌ Eliminar", callback_data=f"cms_delete_{set_id}")
            ],
            [
                InlineKeyboardButton(text="🔙 Volver a Lista", callback_data="cms_list_sets")
            ]
        ]
    )
    return keyboard


def get_confirm_keyboard(action: str, set_id: str = None):
    """Teclado de confirmación genérico"""
    callback_confirm = f"cms_confirm_{action}"
    if set_id:
        callback_confirm += f"_{set_id}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Confirmar", callback_data=callback_confirm),
                InlineKeyboardButton(text="❌ Cancelar", callback_data="cms_main")
            ]
        ]
    )
    return keyboard
