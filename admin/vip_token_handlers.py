from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()

@router.callback_query(F.data.startswith("generate_token_"))
async def generate_vip_token(callback: CallbackQuery):
    """Generar token VIP"""
    tariff_id = callback.data.split("_")[-1]
    await callback.answer(f"Generando token para tarifa {tariff_id}")
