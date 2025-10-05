"""
Keyboards para paquetes de besitos y productos monetizables.
Patrón: Usuario ve opciones → Click "Me interesa" → Notificación admin
"""
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_besitos_packs_list_kb(highlight_pack: int = None) -> InlineKeyboardMarkup:
    """
    Muestra lista de paquetes de besitos disponibles

    Args:
        highlight_pack: Índice del pack a destacar (cuando se sabe cuántos necesita)
    """
    builder = InlineKeyboardBuilder()

    packs = [
        {"id": 1, "name": "Pack Básico", "besitos": 500, "price": 50, "emoji": "💋"},
        {"id": 2, "name": "Pack Premium", "besitos": 1000, "price": 90, "bonus": "+100 gratis", "emoji": "💋💋"},
        {"id": 3, "name": "Pack Luxury", "besitos": 2500, "price": 200, "bonus": "+500 gratis", "emoji": "💋💋💋"},
    ]

    for pack in packs:
        bonus_text = f" {pack['bonus']}" if 'bonus' in pack else ""
        highlight = "✨ " if highlight_pack == pack['id'] else ""

        text = f"{highlight}{pack['emoji']} {pack['name']} - {pack['besitos']} besitos{bonus_text} - ${pack['price']} MXN"
        builder.button(text=text, callback_data=f"besitos_pack_{pack['id']}")

    builder.button(text="🎯 Ganar besitos gratis (Misiones)", callback_data="show_missions")
    builder.button(text="🔙 Volver a tienda", callback_data="shop_access")
    builder.adjust(1)
    return builder.as_markup()


def get_besitos_pack_detail_kb(pack_id: int) -> InlineKeyboardMarkup:
    """Muestra detalles de un pack específico con botón 'Me interesa'"""
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Me interesa este pack", callback_data=f"besitos_interest_{pack_id}")
    builder.button(text="🔙 Ver otros packs", callback_data="besitos_packs_list")
    builder.adjust(1)
    return builder.as_markup()


def get_session_interest_kb(session_type: str = "standard") -> InlineKeyboardMarkup:
    """
    Keyboard para sesión individual

    Args:
        session_type: "standard", "vip_special", "loyalty_discount"
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="💋 Quiero mi sesión con Diana", callback_data=f"session_interest_{session_type}")
    builder.button(text="💭 Tal vez después", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_upsell_keyboard(upsell_type: str, item_data: dict = None) -> InlineKeyboardMarkup:
    """
    Genera keyboard de upsell post-compra

    Args:
        upsell_type: "premium_pack", "vip_upgrade", "session_offer", "besitos_reload"
        item_data: Datos adicionales del item para personalizar
    """
    builder = InlineKeyboardBuilder()

    if upsell_type == "premium_pack":
        # Ofrecer pack de contenido premium
        pack_id = item_data.get('pack_id', 2) if item_data else 2
        builder.button(text="🔥 Sí, quiero el pack completo", callback_data=f"pack_interest_{pack_id}")
        builder.button(text="📖 Continuar historia", callback_data="continue_narrative_after_purchase")
        builder.button(text="🛒 Seguir comprando", callback_data="shop_access")

    elif upsell_type == "vip_upgrade":
        # Ofrecer upgrade a VIP
        builder.button(text="💎 Activar VIP gratis", callback_data="vip_interest_special")
        builder.button(text="📖 Continuar como free", callback_data="continue_narrative_after_purchase")

    elif upsell_type == "session_offer":
        # Ofrecer sesión individual
        session_type = item_data.get('session_type', 'vip_special') if item_data else 'vip_special'
        builder.button(text="💋 Solicitar sesión", callback_data=f"session_interest_{session_type}")
        builder.button(text="🎁 Ver más contenido", callback_data="shop_access")

    elif upsell_type == "besitos_reload":
        # Ofrecer recarga de besitos con bonus
        builder.button(text="💰 Ver packs con bonus", callback_data="besitos_packs_bonus")
        builder.button(text="🛒 Seguir comprando", callback_data="shop_access")

    else:
        # Default: continuar narrativa o tienda
        builder.button(text="📖 Continuar historia", callback_data="continue_narrative_after_purchase")
        builder.button(text="🛒 Seguir comprando", callback_data="shop_access")
        builder.button(text="🎯 Ver misiones", callback_data="show_missions")

    builder.adjust(1)
    return builder.as_markup()


def get_vip_product_kb(product_type: str) -> InlineKeyboardMarkup:
    """
    Keyboards para productos VIP en tienda

    Args:
        product_type: "vip_day", "vip_month"
    """
    builder = InlineKeyboardBuilder()

    if product_type == "vip_day":
        builder.button(text="✨ Quiero 1 día VIP", callback_data="vip_day_interest")
    elif product_type == "vip_month":
        builder.button(text="💎 Quiero 1 mes VIP", callback_data="vip_month_interest")

    builder.button(text="🔙 Volver a tienda", callback_data="shop_access")
    builder.adjust(1)
    return builder.as_markup()
