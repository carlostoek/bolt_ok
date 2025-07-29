from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()

@router.callback_query(F.data.startswith("wait_"))
async def set_wait_time(callback: CallbackQuery):
    """Configurar tiempo de espera"""
    minutes = callback.data.split("_")[-1]
    await callback.answer(f"Tiempo de espera configurado: {minutes} minutos")

@router.callback_query(F.data.startswith("remove_channel_"))
async def remove_channel(callback: CallbackQuery):
    """Eliminar canal"""
    channel_id = callback.data.split("_")[-1]
    await callback.answer(f"Eliminando canal {channel_id}")
