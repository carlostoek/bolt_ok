"""
Servicio centralizado de notificaciones para evitar duplicaciones y gestionar
la auto-eliminación de mensajes temporales del sistema.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Set, Tuple
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Servicio centralizado para gestionar notificaciones al usuario.

    Características:
    - Deduplicación: Evita enviar la misma notificación múltiples veces
    - Auto-eliminación: Borra mensajes temporales automáticamente
    - Agrupación: Combina notificaciones similares
    """

    # Almacenamiento temporal de notificaciones enviadas (user_id -> Set[(tipo, timestamp)])
    _recent_notifications: Dict[int, Set[Tuple[str, datetime]]] = {}

    # Mensajes pendientes de eliminación
    _pending_deletions: Dict[int, list[Message]] = {}

    # Configuración de deduplicación (segundos)
    DEDUP_WINDOW = {
        "points": 3,  # Notificaciones de puntos: 3 segundos
        "mission": 5,  # Misiones completadas: 5 segundos
        "achievement": 5,  # Logros: 5 segundos
        "level_up": 10,  # Subida de nivel: 10 segundos
        "badge": 5,  # Insignias: 5 segundos
        "reaction": 2,  # Reacciones: 2 segundos
        "narrative": 3,  # Fragmentos narrativos: 3 segundos
    }

    # Configuración de auto-eliminación (segundos)
    AUTO_DELETE_DELAY = {
        "points": 5,  # Mensajes de puntos
        "reaction": 4,  # Confirmación de reacción
        "mission": 8,  # Misión completada (más tiempo para leer)
        "narrative": 4,  # Puntos de narrativa
        "default": 5,  # Por defecto
    }

    def __init__(self):
        self._cleanup_task: Optional[asyncio.Task] = None

    @classmethod
    def _should_send(cls, user_id: int, notification_type: str) -> bool:
        """
        Verifica si se debe enviar una notificación basándose en deduplicación.

        Returns:
            True si se debe enviar, False si es duplicada
        """
        now = datetime.now()
        window = timedelta(seconds=cls.DEDUP_WINDOW.get(notification_type, 5))

        # Inicializar si no existe
        if user_id not in cls._recent_notifications:
            cls._recent_notifications[user_id] = set()

        # Limpiar notificaciones antiguas
        user_notifs = cls._recent_notifications[user_id]
        cls._recent_notifications[user_id] = {
            (ntype, ts) for ntype, ts in user_notifs
            if now - ts < window
        }

        # Verificar si ya se envió este tipo recientemente
        for ntype, timestamp in cls._recent_notifications[user_id]:
            if ntype == notification_type and now - timestamp < window:
                logger.debug(
                    f"Deduplicating notification type={notification_type} for user={user_id} "
                    f"(sent {(now - timestamp).total_seconds():.1f}s ago)"
                )
                return False

        # Registrar esta notificación
        cls._recent_notifications[user_id].add((notification_type, now))
        return True

    @classmethod
    async def send_notification(
        cls,
        bot: Bot,
        user_id: int,
        text: str,
        notification_type: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        auto_delete: bool = True,
        force_send: bool = False
    ) -> Optional[Message]:
        """
        Envía una notificación al usuario con deduplicación y auto-eliminación.

        Args:
            bot: Bot instance
            user_id: ID del usuario
            text: Texto de la notificación
            notification_type: Tipo de notificación (para deduplicación)
            reply_markup: Teclado inline opcional
            auto_delete: Si debe auto-eliminarse
            force_send: Forzar envío sin deduplicación

        Returns:
            Message enviado o None si fue deduplicado
        """
        # Verificar deduplicación
        if not force_send and not cls._should_send(user_id, notification_type):
            return None

        try:
            # Enviar mensaje
            msg = await bot.send_message(
                user_id,
                text,
                reply_markup=reply_markup
            )

            # Programar auto-eliminación si está habilitado
            if auto_delete:
                delay = cls.AUTO_DELETE_DELAY.get(notification_type, cls.AUTO_DELETE_DELAY["default"])
                asyncio.create_task(cls._schedule_deletion(bot, msg, delay))

            logger.info(
                f"Sent {notification_type} notification to user {user_id}"
                f"{' (auto-delete in ' + str(delay) + 's)' if auto_delete else ''}"
            )

            return msg

        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
            return None

    @staticmethod
    async def _schedule_deletion(bot: Bot, message: Message, delay: int):
        """
        Programa la eliminación de un mensaje después de un delay.

        Args:
            bot: Bot instance
            message: Mensaje a eliminar
            delay: Segundos de espera antes de eliminar
        """
        try:
            await asyncio.sleep(delay)
            await bot.delete_message(message.chat.id, message.message_id)
            logger.debug(f"Auto-deleted message {message.message_id} from chat {message.chat.id}")
        except Exception as e:
            logger.debug(f"Could not auto-delete message: {e}")

    @classmethod
    async def send_points_notification(
        cls,
        bot: Bot,
        user_id: int,
        points_gained: float,
        total_points: float,
        multiplier: float = 1.0,
        context: str = "general"
    ) -> Optional[Message]:
        """
        Envía notificación de puntos ganados con formato consistente.

        Args:
            bot: Bot instance
            user_id: ID del usuario
            points_gained: Puntos ganados en esta acción
            total_points: Total de puntos del usuario
            multiplier: Multiplicador aplicado
            context: Contexto de los puntos (reaction, narrative, mission, etc.)
        """
        # Formato del mensaje según contexto
        if context == "reaction":
            text = f"💋 +{points_gained:.0f} besitos por reacción"
        elif context == "narrative":
            text = f"📖 +{points_gained:.0f} besitos narrativos"
        elif context == "mission":
            text = f"✅ +{points_gained:.0f} besitos por misión"
        else:
            text = f"💎 +{points_gained:.0f} besitos"

        # Añadir multiplicador si es mayor a 1
        if multiplier > 1:
            text += f" (x{multiplier:.1f})"

        # Añadir total si ha acumulado suficientes puntos
        if total_points >= 10:
            text += f"\n💰 Total: {total_points:.0f} besitos"

        return await cls.send_notification(
            bot=bot,
            user_id=user_id,
            text=text,
            notification_type="points",
            auto_delete=True
        )

    @classmethod
    async def send_mission_completed(
        cls,
        bot: Bot,
        user_id: int,
        mission_name: str,
        reward_points: float,
        reply_markup: Optional[InlineKeyboardMarkup] = None
    ) -> Optional[Message]:
        """
        Envía notificación de misión completada.
        """
        text = f"✅ **Misión Completada**\n\n"
        text += f"📜 {mission_name}\n"
        text += f"💎 +{reward_points:.0f} besitos"

        return await cls.send_notification(
            bot=bot,
            user_id=user_id,
            text=text,
            notification_type="mission",
            reply_markup=reply_markup,
            auto_delete=True  # Se elimina después de 8 segundos
        )

    @classmethod
    async def send_level_up(
        cls,
        bot: Bot,
        user_id: int,
        new_level: int,
        reward_points: float = 0,
        unlocked_content: Optional[str] = None
    ) -> Optional[Message]:
        """
        Envía notificación de subida de nivel.
        """
        text = f"🎉 **¡Nivel {new_level}!**\n\n"

        if reward_points > 0:
            text += f"💎 +{reward_points:.0f} besitos de recompensa\n"

        if unlocked_content:
            text += f"\n🔓 Desbloqueado: {unlocked_content}"

        return await cls.send_notification(
            bot=bot,
            user_id=user_id,
            text=text,
            notification_type="level_up",
            auto_delete=False,  # Las subidas de nivel no se auto-eliminan
            force_send=True  # Siempre enviar subidas de nivel
        )

    @classmethod
    async def send_achievement(
        cls,
        bot: Bot,
        user_id: int,
        achievement_name: str,
        icon: str = "🏆",
        description: Optional[str] = None
    ) -> Optional[Message]:
        """
        Envía notificación de logro/insignia obtenida.
        """
        text = f"{icon} **Insignia Obtenida**\n\n"
        text += f"{achievement_name}"

        if description:
            text += f"\n\n_{description}_"

        return await cls.send_notification(
            bot=bot,
            user_id=user_id,
            text=text,
            notification_type="achievement",
            auto_delete=False,  # Los logros no se auto-eliminan
            force_send=True  # Siempre enviar logros
        )

    @classmethod
    def clear_user_history(cls, user_id: int):
        """Limpia el historial de notificaciones de un usuario."""
        if user_id in cls._recent_notifications:
            del cls._recent_notifications[user_id]

    @classmethod
    def get_stats(cls) -> Dict:
        """Obtiene estadísticas del servicio de notificaciones."""
        total_users = len(cls._recent_notifications)
        total_notifs = sum(len(notifs) for notifs in cls._recent_notifications.values())

        return {
            "users_with_recent_notifications": total_users,
            "total_recent_notifications": total_notifs,
            "dedup_windows": cls.DEDUP_WINDOW,
            "auto_delete_delays": cls.AUTO_DELETE_DELAY
        }
