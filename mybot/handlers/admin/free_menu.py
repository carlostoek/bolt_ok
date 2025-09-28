from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from utils.menu_factory import menu_factory
from sqlalchemy.ext.asyncio import AsyncSession
from utils.user_roles import is_admin
from utils.menu_utils import update_menu
from keyboards.common import get_back_kb
from keyboards.free_channel_admin_kb import get_free_channel_admin_kb

router = Router()


@router.callback_query(F.data == "admin_free")
async def free_menu(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Free channel admin menu."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    text, keyboard = await menu_factory.create_menu(
        "admin_free", callback.from_user.id, session, bot
    )
    await update_menu(
        callback,
        text,
        keyboard,
        session,
        "admin_free",
    )
    await callback.answer()
