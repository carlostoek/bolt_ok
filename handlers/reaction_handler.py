"""
Manejador de reacciones a mensajes en canales.
Implementa el flujo completo de reacción a publicaciones.
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from services.coordinador_central import CoordinadorCentral, AccionUsuario
from services.message_service import MessageService
from services.message_registry import validate_message
from utils.messages import BOT_MESSAGES

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data.startswith("ip_"))
async def handle_reaction_callback(
    callback: CallbackQuery, session: AsyncSession, bot: Bot
) -> None:
    """
    Maneja las reacciones a publicaciones en canales.
    Implementa el flujo completo de reacción con integración de todos los módulos.
    """
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

    # Usar el coordinador central para manejar el flujo completo
    coordinador = CoordinadorCentral(session)
    result = await coordinador.ejecutar_flujo(
        callback.from_user.id,
        AccionUsuario.REACCIONAR_PUBLICACION,
        message_id=message_id,
        channel_id=channel_id,
        reaction_type=reaction_type,
        bot=bot
    )
    
    # Actualizar la interfaz de usuario
    service = MessageService(session, bot)
    await service.update_reaction_markup(chat_id, message_id)
    
    # Enviar respuesta al usuario
    if result["success"]:
        await callback.answer(BOT_MESSAGES.get("reaction_registered", "Reacción registrada"))
        await bot.send_message(
            callback.from_user.id,
            result["message"]
        )
    else:
        await callback.answer(result["message"], show_alert=True)
