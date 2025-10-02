"""
Keyboards para el Journey Admin Panel
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_journey_main_keyboard():
    """Menú principal del Journey admin panel"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Estadísticas Journey", callback_data="journey_stats")
            ],
            [
                InlineKeyboardButton(text="▶️ Forzar Procesamiento", callback_data="journey_force_process"),
                InlineKeyboardButton(text="🧪 Test Milestone", callback_data="journey_test")
            ],
            [
                InlineKeyboardButton(text="👤 Ver Usuario", callback_data="journey_view_user"),
                InlineKeyboardButton(text="📝 Logs Recientes", callback_data="journey_logs")
            ],
            [
                InlineKeyboardButton(text="🔙 Volver", callback_data="cms_main")
            ]
        ]
    )
    return keyboard


def get_milestone_test_keyboard():
    """Teclado para seleccionar qué milestone testear"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Day 1 - Bienvenida", callback_data="journey_test_day_1")],
            [InlineKeyboardButton(text="Day 7 - Oferta VIP", callback_data="journey_test_day_7")],
            [InlineKeyboardButton(text="Day 30 - Final", callback_data="journey_test_day_30")],
            [InlineKeyboardButton(text="🔙 Cancelar", callback_data="journey_main")]
        ]
    )
    return keyboard
