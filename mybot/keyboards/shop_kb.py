# keyboards/shop_kb.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import ShopItem

def get_shop_keyboard(items: list[ShopItem], offset: int = 0, limit: int = 5) -> InlineKeyboardMarkup:
    """
    Creates a keyboard with a paginated list of shop items.
    """
    keyboard = []
    
    # Display items for the current page
    for item in items[offset:offset + limit]:
        button_text = f"{item.name} - {item.price} besitos"
        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"shop:buy:{item.id}"
            )
        ])
    
    # Navigation buttons
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Anterior",
                callback_data=f"shop:page:{offset - limit}"
            )
        )
    if offset + limit < len(items):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Siguiente ➡️",
                callback_data=f"shop:page:{offset + limit}"
            )
        )
    
    if nav_buttons:
        keyboard.append(nav_buttons)
        
    # Back to main menu button
    keyboard.append([
        InlineKeyboardButton(text="↩️ Volver al menú principal", callback_data="menu_principal")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)