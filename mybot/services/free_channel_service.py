"""
Servicio para gestión completa del canal gratuito.
Incluye aprobación automática, envío de mensajes y protección de contenido.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from aiogram import Bot
from aiogram.types import (
    ChatJoinRequest, 
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaDocument,
    InputMediaAudio
)
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database.models import PendingChannelRequest, User, BotConfig
from services.config_service import ConfigService
from services.message_registry import store_message
from utils.text_utils import sanitize_text

logger = logging.getLogger(__name__)


class FreeChannelService:
    """
    Servicio completo para gestión del canal gratuito.
    """
    
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
        self.config_service = ConfigService(session)
    
    async def get_free_channel_id(self) -> Optional[int]:
        """Obtener ID del canal gratuito configurado."""
        return await self.config_service.get_free_channel_id()
    
    async def set_free_channel_id(self, channel_id: int) -> bool:
        """Configurar el canal gratuito."""
        try:
            await self.config_service.set_free_channel_id(channel_id)
            logger.info(f"Free channel configured: {channel_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting free channel ID: {e}")
            return False
    
    async def get_wait_time_minutes(self) -> int:
        """Obtener tiempo de espera configurado para aprobaciones."""
        config = await self.session.get(BotConfig, 1)
        return config.free_channel_wait_time_minutes if config else 0
    
    async def set_wait_time_minutes(self, minutes: int) -> bool:
        """Configurar tiempo de espera para aprobaciones."""
        try:
            config = await self.session.get(BotConfig, 1)
            if not config:
                config = BotConfig(id=1, free_channel_wait_time_minutes=minutes)
                self.session.add(config)
            else:
                config.free_channel_wait_time_minutes = minutes
            
            await self.session.commit()
            logger.info(f"Wait time set to {minutes} minutes")
            return True
        except Exception as e:
            logger.error(f"Error setting wait time: {e}")
            return False
    
    async def handle_join_request(self, join_request: ChatJoinRequest) -> bool:
        """
        Procesar solicitud de unión al canal gratuito.
        Registra la solicitud para aprobación automática posterior y envía mensaje de redes sociales.
        """
        free_channel_id = await self.get_free_channel_id()
        if not free_channel_id or join_request.chat.id != free_channel_id:
            return False
        
        user_id = join_request.from_user.id
        user_name = join_request.from_user.first_name or "Usuario"
        
        try:
            # Verificar si ya existe una solicitud pendiente
            existing_stmt = select(PendingChannelRequest).where(
                PendingChannelRequest.user_id == user_id,
                PendingChannelRequest.chat_id == join_request.chat.id,
                PendingChannelRequest.approved == False
            )
            existing_result = await self.session.execute(existing_stmt)
            existing_request = existing_result.scalar_one_or_none()
            
            if existing_request:
                logger.info(f"User {user_id} already has pending request for channel {join_request.chat.id}")
                # Si no se ha enviado el mensaje de redes sociales, enviarlo ahora
                if not existing_request.social_media_message_sent:
                    await self._send_social_media_message(user_id, user_name)
                    existing_request.social_media_message_sent = True
                    await self.session.commit()
                return True
            
            # Crear nueva solicitud pendiente
            pending_request = PendingChannelRequest(
                user_id=user_id,
                chat_id=join_request.chat.id,
                request_timestamp=datetime.utcnow(),
                approved=False,
                social_media_message_sent=False,
                welcome_message_sent=False
            )
            
            self.session.add(pending_request)
            await self.session.commit()
            
            # 1. ENVIAR MENSAJE DE REDES SOCIALES INMEDIATAMENTE
            social_sent = await self._send_social_media_message(user_id, user_name)
            if social_sent:
                pending_request.social_media_message_sent = True
                await self.session.commit()
            
            # 2. ENVIAR NOTIFICACIÓN SOBRE EL TIEMPO DE ESPERA
            wait_minutes = await self.get_wait_time_minutes()
            
            if wait_minutes > 0:
                wait_text = f"{wait_minutes} minutos"
                if wait_minutes >= 60:
                    hours = wait_minutes // 60
                    remaining_minutes = wait_minutes % 60
                    if remaining_minutes > 0:
                        wait_text = f"{hours} horas y {remaining_minutes} minutos"
                    else:
                        wait_text = f"{hours} horas"
                
                notification_message = (
                    f"📋 **Solicitud Recibida**\n\n"
                    f"Tu solicitud para unirte al canal gratuito ha sido registrada.\n\n"
                    f"⏰ **Tiempo de espera**: {wait_text}\n"
                    f"✅ Serás aprobado automáticamente una vez transcurrido este tiempo.\n\n"
                    f"¡Gracias por tu paciencia!"
                )
            else:
                notification_message = (
                    f"📋 **Solicitud Recibida**\n\n"
                    f"Tu solicitud para unirte al canal gratuito ha sido registrada.\n\n"
                    f"✅ Serás aprobado inmediatamente.\n\n"
                    f"¡Bienvenido!"
                )
            
            try:
                await self.bot.send_message(
                    user_id,
                    notification_message,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.warning(f"Could not notify user {user_id} about join request: {e}")
            
            logger.info(f"Join request registered for user {user_id} in channel {join_request.chat.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling join request for user {user_id}: {e}")
            return False
    
    async def process_pending_requests(self) -> int:
        """
        Procesar solicitudes pendientes que han cumplido el tiempo de espera.
        Retorna el número de solicitudes procesadas.
        """
        # Verificar si la aprobación automática está habilitada
        if not await self.get_auto_approval_enabled():
            logger.info("Auto-approval is disabled, skipping pending requests processing")
            return 0
            
        wait_minutes = await self.get_wait_time_minutes()
        threshold_time = datetime.utcnow() - timedelta(minutes=wait_minutes)
        
        # Obtener solicitudes que han cumplido el tiempo de espera
        stmt = select(PendingChannelRequest).where(
            PendingChannelRequest.approved == False,
            PendingChannelRequest.request_timestamp <= threshold_time
        )
        
        result = await self.session.execute(stmt)
        pending_requests = result.scalars().all()
        
        processed_count = 0
        
        for request in pending_requests:
            try:
                # Aprobar la solicitud en Telegram
                await self.bot.approve_chat_join_request(
                    request.chat_id, 
                    request.user_id
                )
                
                # Marcar como aprobada en la base de datos con timestamp
                request.approved = True
                request.approval_timestamp = datetime.utcnow()
                
                # VERIFICAR Y ASIGNAR ROL CORRECTO (NO DEGRADAR VIP)
                await self._ensure_user_free_role(request.user_id)
                
                # Enviar mensaje de bienvenida si no se ha enviado
                if not request.welcome_message_sent:
                    welcome_sent = await self._send_welcome_message(request.user_id)
                    if welcome_sent:
                        request.welcome_message_sent = True
                
                processed_count += 1
                logger.info(f"Approved join request for user {request.user_id} in channel {request.chat_id}")
                
            except TelegramBadRequest as e:
                if "USER_ALREADY_PARTICIPANT" in str(e):
                    # Usuario ya está en el canal, marcar como aprobado
                    request.approved = True
                    request.approval_timestamp = datetime.utcnow()
                    # VERIFICAR Y ASIGNAR ROL CORRECTO (NO DEGRADAR VIP)
                    await self._ensure_user_free_role(request.user_id)
                    processed_count += 1
                    logger.info(f"User {request.user_id} already in channel {request.chat_id}")
                elif "CHAT_JOIN_REQUEST_NOT_FOUND" in str(e):
                    # La solicitud ya no existe, marcar como procesada
                    request.approved = True
                    request.approval_timestamp = datetime.utcnow()
                    # VERIFICAR Y ASIGNAR ROL CORRECTO (NO DEGRADAR VIP)
                    await self._ensure_user_free_role(request.user_id)
                    processed_count += 1
                    logger.info(f"Join request not found for user {request.user_id}, marking as processed")
                else:
                    logger.error(f"Error approving join request for user {request.user_id}: {e}")
            except Exception as e:
                logger.error(f"Error processing join request for user {request.user_id}: {e}")
        
        if processed_count > 0:
            await self.session.commit()
            logger.info(f"Processed {processed_count} pending join requests")
        
        return processed_count
    
    async def _send_welcome_message(self, user_id: int) -> bool:
        """
        Enviar mensaje de bienvenida personalizado al usuario aprobado.
        """
        try:
            # Obtener mensaje de bienvenida personalizado o usar por defecto
            welcome_message = await self._get_welcome_message()
            
            await self.bot.send_message(
                user_id,
                welcome_message,
                parse_mode="Markdown"
            )
            
            logger.info(f"Welcome message sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.warning(f"Could not send welcome message to user {user_id}: {e}")
            return False
    
    async def _get_welcome_message(self) -> str:
        """
        Obtener mensaje de bienvenida configurado o usar mensaje por defecto.
        """
        try:
            config = await self.session.get(BotConfig, 1)
            if config and config.welcome_message_template:
                return config.welcome_message_template
        except Exception as e:
            logger.warning(f"Error getting welcome message from config: {e}")
        
        # Mensaje por defecto
        return (
            "🎉 **¡Bienvenido al Canal Gratuito!**\n\n"
            "✅ Tu solicitud ha sido aprobada exitosamente.\n"
            "🎯 Ya puedes acceder a todo el contenido gratuito disponible.\n\n"
            "📱 Explora nuestro contenido y participa en las actividades.\n"
            "🎮 ¡No olvides usar los comandos del bot para ganar puntos!\n\n"
            "¡Disfruta de la experiencia! 🚀"
        )
    
    async def set_welcome_message(self, message: str) -> bool:
        """
        Configurar mensaje personalizado de bienvenida.
        """
        try:
            config = await self.session.get(BotConfig, 1)
            if not config:
                config = BotConfig(id=1, welcome_message_template=message)
                self.session.add(config)
            else:
                config.welcome_message_template = message
            
            await self.session.commit()
            logger.info("Welcome message updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting welcome message: {e}")
            return False
    
    async def _send_social_media_message(self, user_id: int, user_name: str) -> bool:
        """
        Enviar mensaje de invitación a seguir en redes sociales inmediatamente después de la solicitud.
        """
        try:
            # Obtener mensaje personalizado de redes sociales de la configuración
            social_message = await self._get_social_media_message()
            
            # Personalizar el mensaje con el nombre del usuario
            personalized_message = social_message.replace("{user_name}", user_name)
            
            await self.bot.send_message(
                user_id,
                personalized_message,
                parse_mode="Markdown",
                disable_web_page_preview=False
            )
            
            logger.info(f"Social media message sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending social media message to user {user_id}: {e}")
            return False
    
    async def _get_social_media_message(self) -> str:
        """
        Obtener mensaje de redes sociales configurado o usar mensaje por defecto.
        """
        try:
            config = await self.session.get(BotConfig, 1)
            if config and config.social_media_message:
                return config.social_media_message
        except Exception as e:
            logger.warning(f"Error getting social media message from config: {e}")
        
        # Mensaje por defecto si no hay configuración personalizada
        return (
            "🌟 **¡Hola {user_name}!**\n\n"
            "¡Gracias por tu interés en unirte a nuestro canal gratuito!\n\n"
            "🔗 **Mientras esperas la aprobación, ¡síguenos en nuestras redes sociales!**\n\n"
            "📱 **Instagram**: @tu_instagram\n"
            "🐦 **Twitter**: @tu_twitter\n"
            "📘 **Facebook**: facebook.com/tu_pagina\n"
            "🎵 **TikTok**: @tu_tiktok\n\n"
            "📺 **YouTube**: youtube.com/tu_canal\n\n"
            "¡No te pierdas nuestro contenido exclusivo y mantente al día con todas las novedades!\n\n"
            "⏰ Tu solicitud de acceso al canal será procesada automáticamente pronto.\n\n"
            "¡Gracias por acompañarnos en esta aventura! 🚀"
        )
    
    async def set_social_media_message(self, message: str) -> bool:
        """
        Configurar mensaje personalizado de redes sociales.
        """
        try:
            config = await self.session.get(BotConfig, 1)
            if not config:
                config = BotConfig(id=1, social_media_message=message)
                self.session.add(config)
            else:
                config.social_media_message = message
            
            await self.session.commit()
            logger.info("Social media message updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting social media message: {e}")
            return False
    
    async def get_auto_approval_enabled(self) -> bool:
        """
        Verificar si la aprobación automática está habilitada.
        """
        try:
            config = await self.session.get(BotConfig, 1)
            return config.auto_approval_enabled if config else True
        except Exception:
            return True
    
    async def _ensure_user_free_role(self, user_id: int) -> bool:
        """
        Asegurar que el usuario tenga el rol correcto al acceder al canal gratuito.
        
        LÓGICA DE PRIORIDAD DE ROLES:
        1. Admin > VIP > Free (no degradar roles superiores)
        2. Verificar suscripción VIP activa en BD
        3. Verificar membresía en canal VIP como respaldo
        4. Solo asignar 'free' si no tiene rol superior
        """
        try:
            from database.models import User
            from services.user_service import UserService
            from sqlalchemy import select
            from datetime import datetime
            
            # Obtener o crear usuario
            user_service = UserService(self.session)
            user = await user_service.get_user(user_id)
            
            if not user:
                # Usuario no existe, crear con rol free
                user = await user_service.create_user(user_id)
                logger.info(f"Created new user {user_id} with role 'free'")
                return True
            
            # VERIFICACIÓN 1: Si es admin, mantener admin
            if user.is_admin or user_id in self._get_admin_ids():
                if not user.is_admin:
                    user.is_admin = True
                    await self.session.commit()
                    logger.info(f"Confirmed admin role for user {user_id}")
                return True
            
            # VERIFICACIÓN 2: Verificar suscripción VIP activa en BD
            current_role = await self._determine_user_role(user_id, user)
            
            # Actualizar rol solo si es necesario
            role_updated = False
            if user.role != current_role:
                old_role = user.role
                user.role = current_role
                role_updated = True
                logger.info(f"Updated user {user_id} role from '{old_role}' to '{current_role}'")
                await self.session.commit()
            
            if not role_updated:
                logger.debug(f"User {user_id} already has correct role '{current_role}'")
            
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring correct role for user {user_id}: {e}")
            return False
    
    async def _determine_user_role(self, user_id: int, user) -> str:
        """
        Determinar el rol correcto del usuario basado en múltiples fuentes.
        
        ORDEN DE VERIFICACIÓN:
        1. Suscripción VIP activa en BD
        2. Membresía en canal VIP (respaldo)
        3. Por defecto: 'free'
        """
        try:
            # VERIFICACIÓN 1: Suscripción VIP en base de datos
            if user.vip_expires_at and user.vip_expires_at > datetime.utcnow():
                logger.debug(f"User {user_id} has active VIP subscription until {user.vip_expires_at}")
                return "vip"
            
            # VERIFICACIÓN 2: Membresía en canal VIP (respaldo)
            vip_channel_id = await self.config_service.get_vip_channel_id()
            if vip_channel_id:
                is_vip_member = await self._check_vip_channel_membership(user_id, vip_channel_id)
                if is_vip_member:
                    logger.info(f"User {user_id} is VIP member by channel membership")
                    # Si está en canal VIP pero no tiene suscripción en BD, crear una temporal
                    if not user.vip_expires_at or user.vip_expires_at <= datetime.utcnow():
                        # Crear suscripción temporal para evitar conflictos
                        from datetime import timedelta
                        user.vip_expires_at = datetime.utcnow() + timedelta(days=30)
                        logger.info(f"Created temporary VIP subscription for user {user_id}")
                    return "vip"
            
            # VERIFICACIÓN 3: Por defecto es free
            logger.debug(f"User {user_id} determined as 'free' user")
            return "free"
            
        except Exception as e:
            logger.warning(f"Error determining role for user {user_id}: {e}")
            return "free"  # Fallback seguro
    
    async def _check_vip_channel_membership(self, user_id: int, vip_channel_id: int) -> bool:
        """
        Verificar si el usuario es miembro del canal VIP.
        """
        try:
            member = await self.bot.get_chat_member(vip_channel_id, user_id)
            is_member = member.status in {"member", "administrator", "creator"}
            logger.debug(f"User {user_id} VIP channel membership: {is_member}")
            return is_member
        except Exception as e:
            logger.debug(f"Could not check VIP membership for user {user_id}: {e}")
            return False
    
    def _get_admin_ids(self) -> list:
        """Obtener lista de IDs de administradores desde configuración."""
        try:
            from utils.config import ADMIN_IDS
            return ADMIN_IDS
        except Exception:
            return []
    
    async def create_invite_link(
        self, 
        expire_hours: int = 24, 
        member_limit: Optional[int] = None,
        creates_join_request: bool = True
    ) -> Optional[str]:
        """
        Crear enlace de invitación para el canal gratuito.
        """
        free_channel_id = await self.get_free_channel_id()
        if not free_channel_id:
            logger.error("Free channel not configured")
            return None
        
        try:
            expire_date = datetime.utcnow() + timedelta(hours=expire_hours)
            
            invite_link = await self.bot.create_chat_invite_link(
                chat_id=free_channel_id,
                expire_date=expire_date,
                member_limit=member_limit,
                creates_join_request=creates_join_request,
                name=f"Enlace Gratuito - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )
            
            logger.info(f"Created invite link for free channel: {invite_link.invite_link}")
            return invite_link.invite_link
            
        except Exception as e:
            logger.error(f"Error creating invite link for free channel: {e}")
            return None
    
    async def send_message_to_channel(
        self,
        text: str,
        protect_content: bool = True,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        media_files: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Message]:
        """
        Enviar mensaje al canal gratuito con protección opcional.
        
        Args:
            text: Texto del mensaje
            protect_content: Si proteger el contenido (no se puede reenviar/copiar)
            reply_markup: Teclado inline opcional
            media_files: Lista de archivos multimedia [{'type': 'photo/video/document/audio', 'file_id': 'xxx', 'caption': 'xxx'}]
        """
        free_channel_id = await self.get_free_channel_id()
        if not free_channel_id:
            logger.error("Free channel not configured")
            return None
        
        try:
            # Si hay archivos multimedia, enviar como álbum
            if media_files and len(media_files) > 1:
                media_group = []
                for i, media in enumerate(media_files[:10]):  # Máximo 10 archivos
                    media_type = media.get('type', 'photo')
                    file_id = media.get('file_id')
                    caption = media.get('caption', text if i == 0 else None)
                    
                    if media_type == 'photo':
                        media_group.append(InputMediaPhoto(media=file_id, caption=caption))
                    elif media_type == 'video':
                        media_group.append(InputMediaVideo(media=file_id, caption=caption))
                    elif media_type == 'document':
                        media_group.append(InputMediaDocument(media=file_id, caption=caption))
                    elif media_type == 'audio':
                        media_group.append(InputMediaAudio(media=file_id, caption=caption))
                
                if media_group:
                    messages = await self.bot.send_media_group(
                        chat_id=free_channel_id,
                        media=media_group,
                        protect_content=protect_content
                    )
                    logger.info(f"Sent media group to free channel: {len(messages)} messages")
                    return messages[0] if messages else None
            
            # Si hay un solo archivo multimedia
            elif media_files and len(media_files) == 1:
                media = media_files[0]
                media_type = media.get('type', 'photo')
                file_id = media.get('file_id')
                
                if media_type == 'photo':
                    sent_message = await self.bot.send_photo(
                        chat_id=free_channel_id,
                        photo=file_id,
                        caption=text,
                        reply_markup=reply_markup,
                        protect_content=protect_content,
                        parse_mode="Markdown"
                    )
                elif media_type == 'video':
                    sent_message = await self.bot.send_video(
                        chat_id=free_channel_id,
                        video=file_id,
                        caption=text,
                        reply_markup=reply_markup,
                        protect_content=protect_content,
                        parse_mode="Markdown"
                    )
                elif media_type == 'document':
                    sent_message = await self.bot.send_document(
                        chat_id=free_channel_id,
                        document=file_id,
                        caption=text,
                        reply_markup=reply_markup,
                        protect_content=protect_content,
                        parse_mode="Markdown"
                    )
                elif media_type == 'audio':
                    sent_message = await self.bot.send_audio(
                        chat_id=free_channel_id,
                        audio=file_id,
                        caption=text,
                        reply_markup=reply_markup,
                        protect_content=protect_content,
                        parse_mode="Markdown"
                    )
                else:
                    # Fallback a mensaje de texto
                    sent_message = await self.bot.send_message(
                        chat_id=free_channel_id,
                        text=text,
                        reply_markup=reply_markup,
                        protect_content=protect_content,
                        parse_mode="Markdown"
                    )
            else:
                # Mensaje de texto simple
                sent_message = await self.bot.send_message(
                    chat_id=free_channel_id,
                    text=text,
                    reply_markup=reply_markup,
                    protect_content=protect_content,
                    parse_mode="Markdown"
                )
            
            logger.info(f"Message sent to free channel: {sent_message.message_id}")
            if reply_markup:
                store_message(free_channel_id, sent_message.message_id)
            return sent_message
            
        except Exception as e:
            logger.error(f"Error sending message to free channel: {e}")
            return None
    
    async def get_channel_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas del canal gratuito."""
        free_channel_id = await self.get_free_channel_id()
        
        stats = {
            "channel_configured": bool(free_channel_id),
            "channel_id": free_channel_id,
            "pending_requests": 0,
            "total_processed": 0,
            "wait_time_minutes": await self.get_wait_time_minutes(),
            "free_users_count": 0
        }
        
        if free_channel_id:
            try:
                # Contar solicitudes pendientes
                pending_stmt = select(func.count()).select_from(PendingChannelRequest).where(
                    PendingChannelRequest.chat_id == free_channel_id,
                    PendingChannelRequest.approved == False
                )
                pending_result = await self.session.execute(pending_stmt)
                stats["pending_requests"] = pending_result.scalar() or 0
                
                # Contar total procesadas
                total_stmt = select(func.count()).select_from(PendingChannelRequest).where(
                    PendingChannelRequest.chat_id == free_channel_id,
                    PendingChannelRequest.approved == True
                )
                total_result = await self.session.execute(total_stmt)
                stats["total_processed"] = total_result.scalar() or 0
                
                # Contar usuarios con rol free
                from database.models import User
                free_users_stmt = select(func.count()).select_from(User).where(
                    User.role == "free"
                )
                free_users_result = await self.session.execute(free_users_stmt)
                stats["free_users_count"] = free_users_result.scalar() or 0
                
                # Información del canal
                try:
                    chat_info = await self.bot.get_chat(free_channel_id)
                    stats["channel_title"] = chat_info.title
                    stats["channel_username"] = chat_info.username
                    stats["channel_member_count"] = await self.bot.get_chat_member_count(free_channel_id)
                except Exception as e:
                    logger.warning(f"Could not get channel info: {e}")
                    
            except Exception as e:
                logger.error(f"Error getting channel statistics: {e}")
        
        return stats
    
    async def cleanup_old_requests(self, days_old: int = 30) -> int:
        """
        Limpiar solicitudes antiguas de la base de datos.
        Retorna el número de solicitudes eliminadas.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        try:
            # Obtener solicitudes antiguas
            old_requests_stmt = select(PendingChannelRequest).where(
                PendingChannelRequest.request_timestamp < cutoff_date
            )
            result = await self.session.execute(old_requests_stmt)
            old_requests = result.scalars().all()
            
            # Eliminar solicitudes antiguas
            for request in old_requests:
                await self.session.delete(request)
            
            await self.session.commit()
            
            logger.info(f"Cleaned up {len(old_requests)} old channel requests")
            return len(old_requests)
            
        except Exception as e:
            logger.error(f"Error cleaning up old requests: {e}")
            return 0
