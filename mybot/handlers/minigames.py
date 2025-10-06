from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from services.config_service import ConfigService
from services.point_service import PointService
from utils.messages import BOT_MESSAGES
import random
import json
import datetime
from database.models import UserMilestone
from sqlalchemy import select

router = Router()

@router.message(F.text.regexp("/reto"))
async def start_reaction_challenge(message: Message, session: AsyncSession, bot: Bot):
    config = ConfigService(session)
    if (await config.get_value("minigames_enabled")) == "false":
        await message.answer(BOT_MESSAGES.get("minigames_disabled", "Minijuegos deshabilitados."))
        return
    from services.minigame_service import MiniGameService
    service = MiniGameService(session)
    challenge = await service.start_reaction_challenge(message.from_user.id, reactions=3)
    await message.answer(
        BOT_MESSAGES.get("challenge_started", "¡Reto iniciado! Reacciona a {count} publicaciones en pocos minutos.").format(count=challenge.target_reactions)
    )

import json

TRIVIA = []
try:
    with open("data/trivia.json", "r", encoding="utf-8") as f:
        TRIVIA = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    pass

import datetime
from database.models import UserMilestone
from sqlalchemy import select

@router.callback_query(F.data == "minigame:dados")
async def handle_dice_callback(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Handles the dice minigame callback."""
    config = ConfigService(session)
    if (await config.get_value("minigames_enabled")) == "false":
        await callback.answer(BOT_MESSAGES.get("minigames_disabled", "Minijuegos deshabilitados."), show_alert=True)
        return

    user_id = callback.from_user.id
    today = datetime.datetime.utcnow().date()

    stmt = select(UserMilestone).where(
        UserMilestone.user_id == user_id,
        UserMilestone.milestone_type == "dice_plays"
    )
    result = await session.execute(stmt)
    dice_milestone = result.scalar_one_or_none()

    plays_today = 0
    if dice_milestone:
        last_play_date = datetime.datetime.fromisoformat(dice_milestone.data.get("last_play_at")).date()
        if last_play_date == today:
            plays_today = dice_milestone.data.get("plays_today", 0)

    if plays_today >= 2:
        await callback.answer("Ya has usado tus dos tiradas de dados de hoy. ¡Vuelve mañana!", show_alert=True)
        return

    dice_msg = await bot.send_dice(callback.message.chat.id)
    score = dice_msg.dice.value
    await PointService(session).add_points(user_id, score, bot=bot)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Volver", callback_data="menu:minigames")]])
    await callback.message.answer(BOT_MESSAGES.get("dice_points", "Ganaste {points} puntos").format(points=score), reply_markup=keyboard)

    if not dice_milestone:
        dice_milestone = UserMilestone(
            user_id=user_id,
            milestone_type="dice_plays",
            data={"plays_today": 1, "last_play_at": today.isoformat()}
        )
        session.add(dice_milestone)
    else:
        if datetime.datetime.fromisoformat(dice_milestone.data.get("last_play_at")).date() != today:
            dice_milestone.data["plays_today"] = 1
        else:
            dice_milestone.data["plays_today"] += 1
        dice_milestone.data["last_play_at"] = today.isoformat()
        
    await session.commit()
    await callback.message.delete()
    await callback.answer()

@router.callback_query(F.data == "minigame:trivia")
async def handle_trivia_callback(callback: CallbackQuery, session: AsyncSession):
    """Handles the trivia minigame callback."""
    config = ConfigService(session)
    if (await config.get_value("minigames_enabled")) == "false":
        await callback.answer(BOT_MESSAGES.get("minigames_disabled", "Minijuegos deshabilitados."), show_alert=True)
        return
    q = random.choice(TRIVIA)
    buttons = [
        [InlineKeyboardButton(text=opt, callback_data="trivia_correct" if i==q["answer"] else "trivia_wrong")]
        for i, opt in enumerate(q["opts"])
    ]
    buttons.append([InlineKeyboardButton(text="⬅️ Volver", callback_data="menu:minigames")])
    await callback.message.edit_text(q["q"], reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@router.callback_query(F.data.in_({"trivia_correct", "trivia_wrong"}))
async def trivia_answer(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    config = ConfigService(session)
    if (await config.get_value("minigames_enabled")) == "false":
        return await callback.answer(BOT_MESSAGES.get("minigames_disabled", "Minijuegos deshabilitados."), show_alert=True)
    
    # Record trivia attempt
    from database.models import TriviaAttempt
    score = 5 if callback.data == "trivia_correct" else 0
    trivia_attempt = TriviaAttempt(
        user_id=callback.from_user.id,
        score=score,
        completed_at=datetime.datetime.utcnow()
    )
    session.add(trivia_attempt)
    await session.commit()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Jugar de nuevo", callback_data="minigame:trivia")],
        [InlineKeyboardButton(text="⬅️ Volver al menú", callback_data="menu:main")]
    ])

    if callback.data == "trivia_correct":
        await PointService(session).add_points(callback.from_user.id, 5, bot=bot)
        await callback.message.edit_text(BOT_MESSAGES.get("trivia_correct", "¡Correcto! +5 puntos"), reply_markup=keyboard)
    else:
        await callback.message.edit_text(BOT_MESSAGES.get("trivia_wrong", "Respuesta incorrecta."), reply_markup=keyboard)
    await callback.answer()
