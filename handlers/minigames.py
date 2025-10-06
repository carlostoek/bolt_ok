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

@router.message(F.text.regexp("/ruleta"))
async def play_roulette(message: Message, session: AsyncSession, bot: Bot):
    config = ConfigService(session)
    if (await config.get_value("minigames_enabled")) == "false":
        await message.answer(BOT_MESSAGES.get("minigames_disabled", "Minijuegos deshabilitados."))
        return
    from services.minigame_service import MiniGameService
    service = MiniGameService(session)
    score = await service.play_roulette(message.from_user.id, bot)
    await message.answer(BOT_MESSAGES.get("dice_points", "Ganaste {points} puntos").format(points=score))

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

@router.message(F.text.regexp("/dice"))
async def play_dice(message: Message, session: AsyncSession, bot: Bot):
    config = ConfigService(session)
    if (await config.get_value("minigames_enabled")) == "false":
        await message.answer("🔮 Los portales mágicos están temporalmente cerrados. Vuelve cuando las estrellas se alineen nuevamente.")
        return

    user_id = message.from_user.id
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
        await message.answer("🎲 Tu energía mística se ha agotado por hoy. Los dados necesitan descansar bajo la luz de la luna. ¡Vuelve mañana!")
        return

    # Enviar mensaje de anticipación
    loading_msg = await message.answer("🎲 Diana está concentrando energía cósmica en los dados...")
    
    dice_msg = await bot.send_dice(message.chat.id)
    score = dice_msg.dice.value
    
    # Feedback emocional basado en resultado
    emotional_responses = {
        1: "😔 Los espíritus del azar no estaban de tu lado... pero cada caída te hace más fuerte.",
        2: "🤔 La suerte es esquiva hoy, pero mañana será otro día.",
        3: "😊 La energía fluye suavemente... un resultado digno.",
        4: "🎯 ¡Bien! Los dados responden a tu aura positiva.",
        5: "🌟 ¡Excelente! Las estrellas se alinean a tu favor.",
        6: "💫 ¡INCREÍBLE! El universo conspira para tu éxito máximo."
    }
    
    response = emotional_responses.get(score, f"🎲 Obtuviste {score} puntos de energía cósmica.")
    
    await PointService(session).add_points(user_id, score, bot=bot)
    await loading_msg.edit_text(f"{response}\n\n✨ +{score} puntos de energía acumulados")
    
    # Actualizar racha y logros
    if not dice_milestone:
        dice_milestone = UserMilestone(
            user_id=user_id,
            milestone_type="dice_plays",
            data={
                "plays_today": 1, 
                "last_play_at": today.isoformat(),
                "total_plays": 1,
                "current_streak": 1,
                "max_streak": 1,
                "last_play_date": today.isoformat()
            }
        )
        session.add(dice_milestone)
    else:
        # Verificar y actualizar racha
        last_play = datetime.datetime.fromisoformat(dice_milestone.data.get("last_play_date")).date()
        yesterday = today - datetime.timedelta(days=1)
        
        if last_play == yesterday:
            current_streak = dice_milestone.data.get("current_streak", 0) + 1
            dice_milestone.data["current_streak"] = current_streak
            dice_milestone.data["max_streak"] = max(dice_milestone.data.get("max_streak", 0), current_streak)
            
            # Celebrar rachas especiales
            if current_streak in [3, 7, 30]:
                streak_bonus = {3: 5, 7: 15, 30: 50}[current_streak]
                await PointService(session).add_points(user_id, streak_bonus, bot=bot)
                await message.answer(f"🎉 ¡Racha de {current_streak} días consecutivos! Bonus de +{streak_bonus} puntos")
        elif last_play != today:
            dice_milestone.data["current_streak"] = 1
            
        dice_milestone.data["plays_today"] = plays_today + 1
        dice_milestone.data["last_play_at"] = today.isoformat()
        dice_milestone.data["last_play_date"] = today.isoformat()
        dice_milestone.data["total_plays"] = dice_milestone.data.get("total_plays", 0) + 1
        
    await session.commit()
    
    # Mostrar progreso de racha
    current_streak = dice_milestone.data.get("current_streak", 1)
    if current_streak >= 2:
        await message.answer(f"🔥 ¡Llevas {current_streak} días seguidos jugando! La magia se fortalece contigo.")

@router.message(F.text.regexp("/trivia"))
async def send_trivia(message: Message, session: AsyncSession):
    config = ConfigService(session)
    if (await config.get_value("minigames_enabled")) == "false":
        await message.answer(BOT_MESSAGES.get("minigames_disabled", "Minijuegos deshabilitados."))
        return
    q = random.choice(TRIVIA)
    buttons = [
        [InlineKeyboardButton(text=opt, callback_data="trivia_correct" if i==q["answer"] else "trivia_wrong")]
        for i, opt in enumerate(q["opts"])
    ]
    await message.answer(q["q"], reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.in_({"trivia_correct", "trivia_wrong"}))
async def trivia_answer(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    config = ConfigService(session)
    if (await config.get_value("minigames_enabled")) == "false":
        return await callback.answer(BOT_MESSAGES.get("minigames_disabled", "Minijuegos deshabilitados."), show_alert=True)
    if callback.data == "trivia_correct":
        await PointService(session).add_points(callback.from_user.id, 5, bot=bot)
        await callback.message.edit_text(BOT_MESSAGES.get("trivia_correct", "¡Correcto! +5 puntos"))
    else:
        await callback.message.edit_text(BOT_MESSAGES.get("trivia_wrong", "Respuesta incorrecta."))
    await callback.answer()
