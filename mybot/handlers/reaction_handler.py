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
from utils.handler_decorators import safe_handler, track_usage, transaction
from utils.message_safety import safe_send_message

router = Router()
logger = logging.getLogger(__name__)

# OBSOLETO: Este handler ha sido reemplazado por el de reaction_callback.py
# Se mantiene como referencia pero se ha desactivado la ruta del router

#@router.callback_query(F.data.startswith("ip_"))
@safe_handler("Error al procesar tu reacción. Inténtalo de nuevo.")
@track_usage("reaction_to_publication")
@transaction()
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
    
    if not valid:
        logger.warning(
            "Invalid message edit attempt - chat_id=%s message_id=%s", 
            chat_id, message_id
        )
        return await callback.answer("Mensaje no válido.")

    # Usar el coordinador central para manejar el flujo completo
    # Utilizar la nueva acción específica para reacciones inline
    coordinador = CoordinadorCentral(session)
    result = await coordinador.ejecutar_flujo(
        callback.from_user.id,
        AccionUsuario.REACCIONAR_PUBLICACION_INLINE,  # Nuevo tipo específico para reacciones inline
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
        
        # El sistema de notificaciones unificadas ya se encarga del envío de mensajes
        # a través del CoordinadorCentral, no necesitamos enviar mensajes duplicados aquí
        
        # Solo para depuración: mostrar que se procesó correctamente
        logger.info(f"Reaction processed successfully for user {callback.from_user.id}, "
                   f"unified notifications handled by CoordinadorCentral")
    else:
        await callback.answer(result["message"], show_alert=True)
