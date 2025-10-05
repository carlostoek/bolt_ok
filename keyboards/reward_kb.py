from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_reward_keyboard(
    rewards: list, claimed_ids: set[int], offset: int = 0
) -> InlineKeyboardMarkup:
    """Return reward keyboard with pagination and claim status."""

    keyboard = []
    # Display up to 4 rewards per page
    for reward in rewards[offset : offset + 4]:
        if reward.id in claimed_ids:
            text = f"✅ {reward.title}"
            callback = f"claimed_{reward.id}"
        else:
            text = f"🎁 {reward.title} ({reward.required_points} besitos)"
            callback = f"claim_reward_{reward.id}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    # Navigation buttons
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Anterior", callback_data=f"rewards_page_{offset - 4}"
            )
        )
    if offset + 4 < len(rewards):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Siguiente ➡️", callback_data=f"rewards_page_{offset + 4}"
            )
        )
    if nav_buttons:
        keyboard.append(nav_buttons)

    # Action buttons
    keyboard.append([
        InlineKeyboardButton(text="🔄 Actualizar", callback_data="menu:rewards"),
        InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
