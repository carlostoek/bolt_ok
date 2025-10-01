from aiogram import Router, Bot
from aiogram.types import ChatJoinRequest, ChatMemberUpdated
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging

from database.models import PendingChannelRequest, BotConfig, User
from services.config_service import ConfigService
from services.free_channel_service import FreeChannelService

logger = logging.getLogger(__name__)
router = Router()

@router.chat_join_request()
async def handle_join_request(event: ChatJoinRequest, bot: Bot, session: AsyncSession):
    """
    Manejar solicitudes de unión a canales (gratuito y VIP).
    - Canal gratuito: Registra la solicitud para aprobación automática posterior.
    - Canal VIP: Aprueba inmediatamente si el usuario tiene rol VIP activo.
    """
    config_service = ConfigService(session)
    vip_channel_id = await config_service.get_vip_channel_id()

    # Si es solicitud al canal VIP
    if vip_channel_id and event.chat.id == vip_channel_id:
        user_id = event.from_user.id

        # Verificar si el usuario tiene rol VIP activo
        user = await session.get(User, user_id)
        if user and user.role == "vip":
            # Verificar que la suscripción no haya expirado
            if user.vip_expires_at is None or user.vip_expires_at > datetime.utcnow():
                try:
                    # Aprobar automáticamente la solicitud
                    await bot.approve_chat_join_request(vip_channel_id, user_id)
                    logger.info(f"Auto-approved VIP channel join request for user {user_id}")

                    # Enviar mensaje de bienvenida
                    try:
                        await bot.send_message(
                            user_id,
                            "🎉 **¡Bienvenido al Canal VIP!**\n\n"
                            "Tu acceso ha sido confirmado exitosamente.\n"
                            "¡Disfruta de todo el contenido exclusivo!",
                            parse_mode="Markdown"
                        )
                    except Exception as e:
                        logger.warning(f"Could not send VIP welcome message to user {user_id}: {e}")

                    return
                except Exception as e:
                    logger.error(f"Failed to auto-approve VIP join request for user {user_id}: {e}")
            else:
                logger.warning(f"User {user_id} tried to join VIP channel but subscription expired")
        else:
            logger.warning(f"User {user_id} tried to join VIP channel without VIP role")

        return

    # Si es solicitud al canal gratuito, usar el servicio existente
    free_service = FreeChannelService(session, bot)
    await free_service.handle_join_request(event)

@router.chat_member()
async def handle_chat_member(update: ChatMemberUpdated, bot: Bot, session: AsyncSession):
    """
    Manejar cambios de membresía en el canal.
    Limpia solicitudes pendientes cuando el usuario se une o sale.
    """
    free_service = FreeChannelService(session, bot)
    free_id = await free_service.get_free_channel_id()
    
    if not free_id or update.chat.id != free_id:
        return

    user_id = update.from_user.id
    status = update.new_chat_member.status
    
    if status in {"member", "administrator", "creator"}:
        # Usuario se unió al canal
        try:
            await bot.send_message(
                user_id, 
                "🎉 **¡Bienvenido al Canal Gratuito!**\n\n"
                "Tu acceso ha sido confirmado exitosamente.\n"
                "¡Disfruta de todo el contenido gratuito disponible!"
            )
        except Exception:
            pass  # Usuario podría tener mensajes privados deshabilitados
        
        # Limpiar solicitud pendiente
        stmt = select(PendingChannelRequest).where(
            PendingChannelRequest.user_id == user_id,
            PendingChannelRequest.chat_id == update.chat.id,
        )
        result = await session.execute(stmt)
        req = result.scalar_one_or_none()
        if req:
            await session.delete(req)
            await session.commit()
            
    elif status in {"kicked", "left"}:
        # Usuario salió o fue expulsado del canal
        stmt = select(PendingChannelRequest).where(
            PendingChannelRequest.user_id == user_id,
            PendingChannelRequest.chat_id == update.chat.id,
        )
        result = await session.execute(stmt)
        req = result.scalar_one_or_none()
        if req:
            await session.delete(req)
            await session.commit()
