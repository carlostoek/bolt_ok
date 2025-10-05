from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.localization import get_text

def get_missions_keyboard(missions: list, offset: int = 0):
    """Returns the keyboard for missions, with pagination."""
    keyboard = []
    # Display up to 4 missions per page for better readability
    for mission in missions[offset : offset + 4]:
        status_emoji = "✅" if hasattr(mission, 'completed') and mission.completed else "🎯"
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{status_emoji} {mission.name} ({mission.reward_points} {get_text('missions.kisses_suffix')})",
                    callback_data=f"mission_{mission.id}",
                )
            ]
        )

    # Add navigation buttons if there are more missions
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text=get_text("missions.button_previous"), callback_data=f"missions_page_{offset - 4}"
            )
        )
    if offset + 4 < len(missions):
        nav_buttons.append(
            InlineKeyboardButton(
                text=get_text("missions.button_next"), callback_data=f"missions_page_{offset + 4}"
            )
        )
    if nav_buttons:
        keyboard.append(nav_buttons)

    # Action buttons
    keyboard.append([
        InlineKeyboardButton(text=get_text("missions.button_refresh"), callback_data="menu:missions"),
        InlineKeyboardButton(text=get_text("missions.button_main_menu"), callback_data="menu_principal")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
