from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()

@router.callback_query(F.data == "vip_manage")
async def manage_vip_subscribers(callback: CallbackQuery):
    """Gestión de suscriptores VIP"""
    await callback.answer("Mostrando gestión de suscriptores VIP")
