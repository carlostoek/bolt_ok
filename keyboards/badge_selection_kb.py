from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_badge_selection_keyboard(badges: list) -> InlineKeyboardMarkup:
    """Keyboard for badge selection with improved layout."""
    rows = []
    
    # Mostrar insignias en filas de 2 para mejor legibilidad
    for i in range(0, len(badges), 2):
        row = []
        for j in range(2):
            if i + j < len(badges):
                badge = badges[i + j]
                label = f"{badge.emoji or '🏅'} {badge.name}".strip()
                row.append(InlineKeyboardButton(text=label, callback_data=f"select_badge_{badge.id}"))
        rows.append(row)
    
    # Botones de navegación
    rows.append([
        InlineKeyboardButton(text="🔄 Actualizar", callback_data="admin_content_badges"),
        InlineKeyboardButton(text="↩️ Volver", callback_data="admin_content_badges")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)
