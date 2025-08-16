"""
Manejadores para interacciones en canales con integración completa.
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_MEMBER, IS_NOT_MEMBER, Command
from sqlalchemy.ext.asyncio import AsyncSession

from services.coordinador_central import CoordinadorCentral, AccionUsuario
from utils.handler_decorators import safe_handler, track_usage, transaction
from utils.message_safety import safe_answer, safe_send_message

router = Router()
logger = logging.getLogger(__name__)

@router.message(F.chat.type.in_({"supergroup", "channel"}))
@safe_handler("Error al procesar mensaje del canal.")
@track_usage("channel_participation")
@transaction()
async def handle_channel_message(message: Message, session: AsyncSession):
    """
    Maneja mensajes en canales y grupos.
    Otorga puntos por participación activa.
    """
    if not message.from_user:
        return  # Mensajes de canal sin autor específico
    
    user_id = message.from_user.id
    channel_id = message.chat.id
    
    # Determinar tipo de acción
    action_type = "message"
    if message.reply_to_message:
        action_type = "comment"
    elif message.poll:
        action_type = "poll_vote"
    elif message.forward_from or message.forward_from_chat:
        action_type = "forward"
    
    # Usar el coordinador central para el flujo completo
    coordinador = CoordinadorCentral(session)
    result = await coordinador.ejecutar_flujo(
        user_id,
        AccionUsuario.PARTICIPAR_CANAL,
        channel_id=channel_id,
        action_type=action_type,
        bot=message.bot
    )
    
    # No enviamos respuesta directa en el canal para no interrumpir conversaciones
    # Solo notificamos al usuario en privado si la acción fue exitosa
    if result["success"]:
        await safe_send_message(
            message.bot,
            user_id,
            result["message"]
        )

@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_MEMBER))
@safe_handler("Error al procesar entrada al canal.")
@track_usage("channel_join")
@transaction()
async def user_joined_channel(event: ChatMemberUpdated, session: AsyncSession):
    """
    Maneja eventos de usuario uniéndose a un canal.
    Otorga puntos por unirse a canales oficiales.
    """
    user_id = event.from_user.id
    channel_id = event.chat.id
    
    # Usar el coordinador central para el flujo completo
    coordinador = CoordinadorCentral(session)
    result = await coordinador.ejecutar_flujo(
        user_id,
        AccionUsuario.PARTICIPAR_CANAL,
        channel_id=channel_id,
        action_type="join_channel",
        bot=event.bot
    )
    
    if result["success"]:
        await safe_send_message(
            event.bot,
            user_id,
            f"Diana sonríe al verte unirte a su círculo íntimo...\n\n*+5 besitos* 💋 por unirte al canal."
        )

@router.message(Command("daily"))
@safe_handler("Error al verificar engagement diario.")
@track_usage("daily_engagement_check")
@transaction()
async def check_daily_engagement(message: Message, session: AsyncSession):
    """
    Verifica el engagement diario del usuario y otorga bonificaciones.
    """
    user_id = message.from_user.id
    
    # Usar el coordinador central para el flujo completo
    coordinador = CoordinadorCentral(session)
    result = await coordinador.ejecutar_flujo(
        user_id,
        AccionUsuario.VERIFICAR_ENGAGEMENT,
        bot=message.bot
    )
    
    await safe_answer(message, result["message"])
