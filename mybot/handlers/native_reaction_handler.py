"""
Handler para reacciones nativas de Telegram.
Maneja el evento MessageReactionUpdated para procesar reacciones emoji nativas.
"""
import logging
from aiogram import Router, F, Bot
from aiogram.types import MessageReactionUpdated
from sqlalchemy.ext.asyncio import AsyncSession

from services.coordinador_central import CoordinadorCentral, AccionUsuario
from services.notification_service import NotificationService
from utils.handler_decorators import safe_handler, track_usage, transaction

router = Router()
logger = logging.getLogger(__name__)


@router.message_reaction(F.message_reaction)
@safe_handler("Error al procesar tu reacción nativa. Inténtalo de nuevo.")
@track_usage("native_reaction")
@transaction()
async def handle_native_reaction(
    message_reaction: MessageReactionUpdated, 
    session: AsyncSession, 
    bot: Bot
) -> None:
    """
    Maneja las reacciones nativas de Telegram (MessageReactionUpdated).
    Procesa reacciones emoji directas a mensajes usando el CoordinadorCentral.
    
    Args:
        message_reaction: Event de reacción actualizada de Telegram
        session: Sesión de base de datos
        bot: Instancia del bot
    """
    try:
        # Extraer datos de la reacción
        user_id = message_reaction.user.id
        chat_id = message_reaction.chat.id
        message_id = message_reaction.message_id
        
        # Verificar que hay reacciones nuevas
        if not message_reaction.new_reaction:
            logger.debug(f"No new reactions in update for user {user_id}, message {message_id}")
            return
        
        # Obtener el primer emoji de la reacción
        # Telegram puede enviar múltiples reacciones en un update
        reaction_type = None
        for reaction in message_reaction.new_reaction:
            if hasattr(reaction, 'emoji'):
                reaction_type = reaction.emoji
                break
            elif hasattr(reaction, 'type') and reaction.type == 'emoji':
                reaction_type = reaction.emoji
                break
        
        if not reaction_type:
            logger.debug(f"No emoji reaction found in update for user {user_id}")
            return
        
        logger.info(f"Native reaction detected: user {user_id}, message {message_id}, emoji {reaction_type}")
        
        # Inicializar servicio de notificaciones
        notification_service = NotificationService(session, bot)
        
        # Procesar la reacción usando el CoordinadorCentral
        coordinador = CoordinadorCentral(session)
        result = await coordinador.ejecutar_flujo(
            user_id,
            AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=message_id,
            channel_id=chat_id,
            reaction_type=reaction_type,
            is_native_reaction=True,
            bot=bot
        )
        
        # Enviar notificación unificada si el procesamiento fue exitoso
        if result.get("success"):
            await _send_unified_notification(notification_service, user_id, result)
        else:
            # Enviar notificación de error inmediata
            error_message = result.get("message", "No se pudo procesar tu reacción.")
            await notification_service.send_immediate_notification(user_id, error_message)
        
        logger.info(f"Native reaction processed successfully for user {user_id}")
        
    except Exception as e:
        logger.exception(f"Error processing native reaction: {e}")
        # Intentar enviar notificación de error si es posible
        try:
            if 'notification_service' in locals():
                await notification_service.send_immediate_notification(
                    user_id, 
                    "Diana parece haber perdido tu reacción entre sus pensamientos... Inténtalo de nuevo."
                )
        except:
            pass  # Evitar loops de error


async def _send_unified_notification(
    notification_service: NotificationService, 
    user_id: int, 
    result: dict
) -> None:
    """
    Envía notificaciones unificadas basadas en el resultado del procesamiento.
    
    Args:
        notification_service: Servicio de notificaciones
        user_id: ID del usuario
        result: Resultado del procesamiento de la reacción
    """
    try:
        # Agregar notificación de puntos si se otorgaron
        if result.get("points_awarded"):
            await notification_service.add_notification(
                user_id,
                "points",
                {
                    "points": result["points_awarded"],
                    "total": result.get("total_points", 0)
                }
            )
        
        # Agregar notificación de misión completada si aplica
        if result.get("mission_completed"):
            await notification_service.add_notification(
                user_id,
                "mission",
                {
                    "name": result["mission_completed"],
                    "points": result.get("mission_points", 0)
                }
            )
        
        # Agregar notificación de pista desbloqueada si aplica
        if result.get("hint_unlocked"):
            await notification_service.add_notification(
                user_id,
                "hint",
                {
                    "text": result["hint_unlocked"]
                }
            )
        
        # Agregar notificación básica de reacción
        await notification_service.add_notification(
            user_id,
            "reaction",
            {
                "type": "native",
                "processed": True
            }
        )
        
        logger.debug(f"Added unified notifications for user {user_id}")
        
    except Exception as e:
        logger.exception(f"Error sending unified notification: {e}")
        # Fallback: enviar mensaje básico
        basic_message = result.get("message", "Diana sonríe al ver tu reacción... 💋")
        await notification_service.send_immediate_notification(user_id, basic_message)


# Función de utilidad para verificar si una reacción es válida
def is_valid_reaction(reaction_update: MessageReactionUpdated) -> bool:
    """
    Verifica si una actualización de reacción es válida para procesar.
    
    Args:
        reaction_update: Actualización de reacción de Telegram
        
    Returns:
        True si la reacción es válida para procesar
    """
    try:
        # Verificar que hay usuario
        if not reaction_update.user or not reaction_update.user.id:
            return False
        
        # Verificar que hay reacciones nuevas
        if not reaction_update.new_reaction:
            return False
        
        # Verificar que al menos una reacción es emoji
        for reaction in reaction_update.new_reaction:
            if hasattr(reaction, 'emoji') or (hasattr(reaction, 'type') and reaction.type == 'emoji'):
                return True
        
        return False
        
    except Exception:
        return False


# Función de utilidad para extraer el emoji de la reacción
def extract_reaction_emoji(reaction_update: MessageReactionUpdated) -> str:
    """
    Extrae el emoji de la reacción de una actualización.
    
    Args:
        reaction_update: Actualización de reacción de Telegram
        
    Returns:
        Emoji de la reacción o string vacío si no se encuentra
    """
    try:
        if not reaction_update.new_reaction:
            return ""
        
        for reaction in reaction_update.new_reaction:
            if hasattr(reaction, 'emoji'):
                return reaction.emoji
            elif hasattr(reaction, 'type') and reaction.type == 'emoji':
                return getattr(reaction, 'emoji', "")
        
        return ""
        
    except Exception:
        return ""