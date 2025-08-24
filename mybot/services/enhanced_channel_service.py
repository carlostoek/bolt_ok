"""
Enhanced channel service with support for configurable messages, 
subscription reminders, and user management.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from aiogram import Bot
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User, BotConfig, PendingChannelRequest
from services.config_service import ConfigService
from services.free_channel_service import FreeChannelService
from services.subscription_service import SubscriptionService
from utils.text_utils import sanitize_text

logger = logging.getLogger(__name__)


class EnhancedChannelService:
    """
    Enhanced service for managing channel communications and user lifecycle.
    """
    
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
        self.config_service = ConfigService(session)
        self.free_service = FreeChannelService(session, bot)
    
    # --- MESSAGE CONFIGURATION METHODS ---
    
    async def get_free_welcome_message(self) -> str:
        """Get the configurable welcome message for free channel."""
        try:
            config = await self.session.get(BotConfig, 1)
            if config and config.welcome_message_template:
                return config.welcome_message_template
        except Exception as e:
            logger.warning(f"Error getting free welcome message: {e}")
        
        # Default message
        return (
            "🎉 **¡Bienvenido al Canal Gratuito!**\n\n"
            "✅ Tu solicitud ha sido aprobada exitosamente.\n"
            "🎯 Ya puedes acceder a todo el contenido gratuito disponible.\n\n"
            "📱 Explora nuestro contenido y participa en las actividades.\n"
            "🎮 ¡No olvides usar los comandos del bot para ganar puntos!\n\n"
            "¡Disfruta de la experiencia! 🚀"
        )
    
    async def set_free_welcome_message(self, message: str) -> bool:
        """Set the configurable welcome message for free channel."""
        try:
            config = await self.session.get(BotConfig, 1)
            if not config:
                config = BotConfig(id=1, welcome_message_template=message)
                self.session.add(config)
            else:
                config.welcome_message_template = message
            
            await self.session.commit()
            logger.info("Free welcome message updated successfully")
            return True
        except Exception as e:
            logger.error(f"Error setting free welcome message: {e}")
            return False
    
    async def get_token_welcome_message(self) -> str:
        """Get the configurable welcome message for token-based access."""
        try:
            config = await self.session.get(BotConfig, 1)
            if config and config.token_welcome_message:
                return config.token_welcome_message
        except Exception as e:
            logger.warning(f"Error getting token welcome message: {e}")
        
        # Default message
        return (
            "🎉 **¡Bienvenido a nuestro contenido exclusivo!**\n\n"
            "✅ Tu acceso ha sido activado exitosamente mediante token.\n"
            "🎯 Disfruta de todo el contenido premium disponible.\n\n"
            "📱 Explora nuestro contenido especial y participa en las actividades VIP.\n"
            "🎮 ¡No olvides usar los comandos del bot para ganar puntos exclusivos!\n\n"
            "¡Disfruta de la experiencia premium! 🚀"
        )
    
    async def set_token_welcome_message(self, message: str) -> bool:
        """Set the configurable welcome message for token-based access."""
        try:
            config = await self.session.get(BotConfig, 1)
            if not config:
                config = BotConfig(id=1, token_welcome_message=message)
                self.session.add(config)
            else:
                config.token_welcome_message = message
            
            await self.session.commit()
            logger.info("Token welcome message updated successfully")
            return True
        except Exception as e:
            logger.error(f"Error setting token welcome message: {e}")
            return False
    
    async def get_subscription_reminder_message(self) -> str:
        """Get the configurable subscription reminder message."""
        try:
            message = await self.config_service.get_value("vip_reminder_message")
            if message:
                return message
        except Exception as e:
            logger.warning(f"Error getting subscription reminder message: {e}")
        
        # Default message
        return (
            "⏰ **Recordatorio de Suscripción**\n\n"
            "Tu suscripción VIP expira en 24 horas.\n\n"
            "¿Deseas renovar tu acceso para continuar disfrutando de los beneficios exclusivos?\n\n"
            "Contacta con un administrador para más información."
        )
    
    async def set_subscription_reminder_message(self, message: str) -> bool:
        """Set the configurable subscription reminder message."""
        try:
            await self.config_service.set_value("vip_reminder_message", message)
            logger.info("Subscription reminder message updated successfully")
            return True
        except Exception as e:
            logger.error(f"Error setting subscription reminder message: {e}")
            return False
    
    async def get_farewell_message(self) -> str:
        """Get the configurable farewell message."""
        try:
            message = await self.config_service.get_value("vip_farewell_message")
            if message:
                return message
        except Exception as e:
            logger.warning(f"Error getting farewell message: {e}")
        
        # Default message
        return (
            "👋 **Hasta pronto**\n\n"
            "Tu suscripción VIP ha expirado.\n\n"
            "Gracias por ser parte de nuestra comunidad.\n"
            "Esperamos verte pronto nuevamente.\n\n"
            "Si deseas renovar tu acceso, contacta con un administrador."
        )
    
    async def set_farewell_message(self, message: str) -> bool:
        """Set the configurable farewell message."""
        try:
            await self.config_service.set_value("vip_farewell_message", message)
            logger.info("Farewell message updated successfully")
            return True
        except Exception as e:
            logger.error(f"Error setting farewell message: {e}")
            return False
    
    # --- MESSAGE SENDING METHODS ---
    
    async def send_message_to_channel(
        self,
        text: str,
        protect_content: bool = True,
        reply_markup: Optional[Any] = None,
        media_files: Optional[list] = None
    ) -> Optional[Message]:
        """
        Send message to free channel with protection option.
        """
        return await self.free_service.send_message_to_channel(
            text=text,
            protect_content=protect_content,
            reply_markup=reply_markup,
            media_files=media_files
        )
    
    async def send_free_welcome_message(self, user_id: int) -> bool:
        """
        Send welcome message to user who joined free channel.
        """
        try:
            welcome_message = await self.get_free_welcome_message()
            await self.bot.send_message(
                user_id,
                welcome_message,
                parse_mode="Markdown"
            )
            logger.info(f"Free welcome message sent to user {user_id}")
            return True
        except Exception as e:
            logger.warning(f"Could not send free welcome message to user {user_id}: {e}")
            return False
    
    async def send_token_welcome_message(self, user_id: int) -> bool:
        """
        Send welcome message to user who accessed via token.
        """
        try:
            welcome_message = await self.get_token_welcome_message()
            await self.bot.send_message(
                user_id,
                welcome_message,
                parse_mode="Markdown"
            )
            logger.info(f"Token welcome message sent to user {user_id}")
            return True
        except Exception as e:
            logger.warning(f"Could not send token welcome message to user {user_id}: {e}")
            return False
    
    # --- SCHEDULER METHODS ---
    
    async def send_subscription_reminders(self) -> int:
        """
        Send subscription reminder messages 1 day before expiration.
        Returns number of reminders sent.
        """
        try:
            now = datetime.utcnow()
            remind_threshold = now + timedelta(hours=24)
            
            # Get users with expiring subscriptions
            stmt = select(User).where(
                User.role == "vip",
                User.vip_expires_at <= remind_threshold,
                User.vip_expires_at > now,
                (User.last_reminder_sent_at.is_(None)) |
                (User.last_reminder_sent_at <= now - timedelta(hours=24)),
            )
            result = await self.session.execute(stmt)
            users = result.scalars().all()
            
            reminder_msg = await self.get_subscription_reminder_message()
            sent_count = 0
            
            for user in users:
                try:
                    await self.bot.send_message(user.id, reminder_msg)
                    user.last_reminder_sent_at = now
                    sent_count += 1
                    logger.info(f"Sent subscription reminder to user {user.id}")
                except Exception as e:
                    logger.warning(f"Failed to send reminder to user {user.id}: {e}")
            
            if sent_count > 0:
                await self.session.commit()
            
            return sent_count
        except Exception as e:
            logger.error(f"Error sending subscription reminders: {e}")
            return 0
    
    async def process_expired_subscriptions(self) -> int:
        """
        Process expired subscriptions: send farewell message and remove from channel.
        Returns number of users processed.
        """
        try:
            now = datetime.utcnow()
            
            # Get expired users
            stmt = select(User).where(
                User.role == "vip",
                User.vip_expires_at.is_not(None),
                User.vip_expires_at <= now,
            )
            result = await self.session.execute(stmt)
            expired_users = result.scalars().all()
            
            farewell_msg = await self.get_farewell_message()
            vip_channel_id = await self.config_service.get_vip_channel_id()
            processed_count = 0
            
            for user in expired_users:
                try:
                    # Remove from VIP channel
                    if vip_channel_id:
                        try:
                            await self.bot.ban_chat_member(vip_channel_id, user.id)
                            await self.bot.unban_chat_member(vip_channel_id, user.id)
                        except Exception as e:
                            logger.warning(f"Failed to remove user {user.id} from VIP channel: {e}")
                    
                    # Update user role
                    user.role = "free"
                    user.vip_expires_at = None
                    
                    # Send farewell message
                    await self.bot.send_message(user.id, farewell_msg)
                    
                    processed_count += 1
                    logger.info(f"Processed expired subscription for user {user.id}")
                except Exception as e:
                    logger.error(f"Error processing expired subscription for user {user.id}: {e}")
            
            if processed_count > 0:
                await self.session.commit()
            
            return processed_count
        except Exception as e:
            logger.error(f"Error processing expired subscriptions: {e}")
            return 0