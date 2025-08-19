import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from services.message_service import MessageService
from services.channel_service import ChannelService
from services.message_registry import validate_message
from services.coordinador_central import CoordinadorCentral, AccionUsuario
from utils.messages import BOT_MESSAGES
from utils.handler_decorators import safe_handler, track_usage, transaction

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("ip_"))
@safe_handler("Error al procesar tu reacción. Inténtalo de nuevo.")
@track_usage("inline_reaction")
@transaction()
async def handle_reaction_callback(
    callback: CallbackQuery, session: AsyncSession, bot: Bot
) -> None:
    """
    Maneja reacciones a través de botones inline usando el CoordinadorCentral.
    Procesa la reacción y envía notificaciones unificadas.
    """
    try:
        # Parsear datos del callback
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
        user_id = callback.from_user.id

        if not callback.message:
            return await callback.answer()

        chat_id = callback.message.chat.id
        
        # Validar que el mensaje sea válido
        valid = validate_message(chat_id, message_id)
        logger.info(
            "Inline reaction attempt: user=%s, chat_id=%s, message_id=%s, reaction=%s, valid=%s", 
            user_id, chat_id, message_id, reaction_type, valid
        )

        if not valid:
            logger.warning(
                "[ERROR] El mensaje que se intenta editar no fue enviado por este bot o el chat_id es incorrecto."
            )
            return await callback.answer("Mensaje no válido.", show_alert=True)

        # Verificar si la reacción ya existe y registrarla
        service = MessageService(session, bot)
        reaction_result = await service.register_reaction(user_id, message_id, reaction_type)

        if reaction_result is None:
            await callback.answer(
                BOT_MESSAGES.get("reaction_already", "Ya has reaccionado a este post."),
                show_alert=True,
            )
            # Asegurarse de que los conteos sean actualizados aún cuando no hay cambio
            await service.update_reaction_markup(chat_id, message_id)
            return

        # Usar CoordinadorCentral para procesar la reacción unificadamente
        coordinador = CoordinadorCentral(session)
        result = await coordinador.ejecutar_flujo(
            user_id,
            AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=message_id,
            channel_id=channel_id,
            reaction_type=reaction_type,
            is_native_reaction=False,
            bot=bot,
            skip_unified_notifications=False  # CoordinadorCentral manejará las notificaciones unificadas
        )

        # Forzar actualizar el markup del mensaje con los conteos actualizados
        # Asegurarnos que los cambios estén visibles en la BD antes de actualizar
        await session.expire_all()
        await service.update_reaction_markup(chat_id, message_id)
        
        # Responder al callback con mensaje simple
        if result.get("success"):
            await callback.answer("✅ Reacción registrada")
            logger.info(f"Inline reaction processed successfully: user {user_id}, message {message_id}")
        else:
            error_message = result.get("message", "No se pudo procesar tu reacción.")
            await callback.answer(error_message, show_alert=True)
            logger.warning(f"Inline reaction failed: user {user_id}, message {message_id}, error: {error_message}")

    except Exception as e:
        logger.exception(f"Error processing inline reaction: {e}")
        try:
            await callback.answer("Diana parece confundida por tu reacción... Inténtalo de nuevo.", show_alert=True)
        except:
            pass  # Evitar loops de error
