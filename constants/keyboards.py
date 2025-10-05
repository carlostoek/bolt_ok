# constants/keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from utils.localization import get_text

main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text=get_text("main_menu.button_home")),
        ],
        [
            KeyboardButton(text=get_text("main_menu.button_backpack")),
            KeyboardButton(text=get_text("main_menu.button_wallet")),
            KeyboardButton(text=get_text("main_menu.button_missions")),
        ],
        [
            KeyboardButton(text=get_text("main_menu.button_story")),
            KeyboardButton(text=get_text("main_menu.button_settings")),
            KeyboardButton(text=get_text("main_menu.button_help")),
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)
