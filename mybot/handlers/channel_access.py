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


@router.callback_query(lambda c: c.data == "check_join_status")
async def check_join_status_handler(callback, session: AsyncSession):
    """Handler para verificar el estado de la solicitud de ingreso al canal gratuito."""
    from aiogram import F
    from aiogram.types import CallbackQuery
    from datetime import datetime, timedelta
    from utils.onboarding_messages import DEFAULT_SOCIAL_LINKS
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    user_id = callback.from_user.id

    try:
        # Buscar solicitud pendiente del usuario
        stmt = select(PendingChannelRequest).where(
            PendingChannelRequest.user_id == user_id,
            PendingChannelRequest.approved == False
        )
        result = await session.execute(stmt)
        pending_request = result.scalar_one_or_none()

        if not pending_request:
            await callback.answer(
                "✅ Tu solicitud ya fue aprobada. Revisa el canal.",
                show_alert=True
            )
            return

        # Calcular tiempo restante
        config = await session.get(BotConfig, 1)
        wait_minutes = config.free_channel_wait_time_minutes if config else 15

        elapsed_time = datetime.utcnow() - pending_request.request_timestamp
        elapsed_minutes = int(elapsed_time.total_seconds() / 60)
        remaining_minutes = max(0, wait_minutes - elapsed_minutes)

        if remaining_minutes == 0:
            status_message = "⏰ Tu solicitud está siendo procesada. Serás aprobado en cualquier momento."
        elif remaining_minutes < 5:
            status_message = f"⏰ **Casi listo!**\n\nTiempo restante: aproximadamente {remaining_minutes} minutos.\n\nPrepárate para la bienvenida de Diana..."
        else:
            status_message = f"""⏰ **Estado de tu Solicitud**

Tiempo transcurrido: {elapsed_minutes} minutos
Tiempo restante: **{remaining_minutes} minutos**

_Recuerda: seguir a Diana en sus redes sociales demuestra tu interés genuino._

¿Ya la sigues en todas sus plataformas?"""

        # Construir teclado con enlaces sociales
        builder = InlineKeyboardBuilder()

        if DEFAULT_SOCIAL_LINKS.get('instagram'):
            builder.button(text="📸 Instagram", url=DEFAULT_SOCIAL_LINKS['instagram'])
        if DEFAULT_SOCIAL_LINKS.get('tiktok'):
            builder.button(text="🎵 TikTok", url=DEFAULT_SOCIAL_LINKS['tiktok'])

        builder.button(text="🔄 Actualizar Estado", callback_data="check_join_status")
        builder.adjust(2, 1)

        await callback.message.edit_text(
            status_message,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error checking join status for user {user_id}: {e}", exc_info=True)
        await callback.answer("❌ Error al verificar el estado", show_alert=True)
