from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.localization import L

def get_admin_content_daily_gifts_keyboard():
    """Keyboard for daily gift configuration options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=L("gift.keyboards.main_menu_send"), callback_data="admin_game_test"),
                InlineKeyboardButton(text=L("gift.keyboards.main_menu_stats"), callback_data="admin_daily_stats")
            ],
            [
                InlineKeyboardButton(text=L("gift.keyboards.pagination_next"), callback_data="admin_content_daily_gifts"),
                InlineKeyboardButton(text=L("gift.keyboards.main_menu_back"), callback_data="admin_manage_content")
            ],
        ]
    )
    return keyboard
