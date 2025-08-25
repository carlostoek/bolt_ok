import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from services.message_service import MessageService
from services.channel_service import ChannelService
from services.message_registry import validate_message
from utils.messages import BOT_MESSAGES

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("ip_"))
async def handle_reaction_callback(
    callback: CallbackQuery, session: AsyncSession, bot: Bot
) -> None:
    parts = callback.data.split("_")
    if len(parts) < 4:
        return await callback.answer()

    try:
        channel_id = int(parts[1])
    except ValueError:
        channel_id = parts[1]

    try:
        message_id = int(parts[2])
    except ValueError:
        return await callback.answer()

    reaction_type = parts[3]

    if not callback.message:
        return await callback.answer()

    chat_id = callback.message.chat.id
    valid = validate_message(chat_id, message_id)
    logger.info(
        "Edit attempt chat_id=%s message_id=%s valid=%s", chat_id, message_id, valid
    )

    if not valid:
        logger.warning(
            "[ERROR] El mensaje que se intenta editar no fue enviado por este bot o el chat_id es incorrecto."
        )
        return await callback.answer()

    service = MessageService(session, bot)
    channel_service = ChannelService(session)

    reaction_result = await service.register_reaction(
        callback.from_user.id,
        message_id,
        reaction_type,
    )

    if reaction_result is None:
        await callback.answer(
            BOT_MESSAGES.get("reaction_already", "Ya has reaccionado a este post."),
            show_alert=True,
        )
        return

    from services.point_service import PointService
    from services.level_service import LevelService
    from services.achievement_service import AchievementService

    points_dict = await channel_service.get_reaction_points(channel_id)
    points = float(points_dict.get(reaction_type, 0.0))

    # Crear instancias de servicios necesarios
    level_service = LevelService(session)
    achievement_service = AchievementService(session)
    point_service = PointService(session, level_service, achievement_service)

    # Award points to the user with proper transaction handling
    await point_service.add_points(
        callback.from_user.id, 
        points, 
        bot=bot, 
        skip_notification=True,  # Prevent duplicate notification
        source=f"reaction_{reaction_type}_message_{message_id}"
    )
    
    # Get mission service and update progress
    from services.mission_service import MissionService
    mission_service = MissionService(session)
    
    # Update mission progress with proper bot instance for notifications
    # Pass _skip_notification=True to avoid duplicate notifications
    await mission_service.update_progress(
        callback.from_user.id, 
        "reaction", 
        bot=bot,  # Pass bot instance for proper notifications
        increment=1,
        _skip_notification=True  # Skip notification to avoid duplication
    )
    
    logger.info(f"Reacción registrada para user_id={callback.from_user.id} con {points} puntos")

    await service.update_reaction_markup(chat_id, message_id)
    # Show popup notification with points
    await callback.answer(BOT_MESSAGES["reaction_registered_points"].format(points=points))
