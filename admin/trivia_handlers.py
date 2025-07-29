from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()

@router.callback_query(F.data == "multiple")
async def set_multiple_choice(callback: CallbackQuery):
    """Configurar pregunta de opción múltiple"""
    await callback.answer("Configurando pregunta de opción múltiple")

@router.callback_query(F.data == "open")
async def set_open_question(callback: CallbackQuery):
    """Configurar pregunta abierta"""
    await callback.answer("Configurando pregunta abierta")
