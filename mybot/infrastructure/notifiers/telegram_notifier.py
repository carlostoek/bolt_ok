"""
Telegram implementation of NotifierInterface.
"""
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from core.interfaces.notifier import NotifierInterface

logger = logging.getLogger(__name__)


class TelegramNotifier(NotifierInterface):
    """
    Telegram-specific notifier implementation.
    Sends notifications via Telegram bot.
    """

    def __init__(self, bot: Bot):
        """
        Initialize Telegram notifier.

        :param bot: Aiogram Bot instance
        """
        self.bot = bot

    async def send_points_notification(self, user_id: int, points: float, reason: str = "") -> None:
        """Send points notification via Telegram."""
        try:
            message = f"💰 ¡+{points} besitos!"
            if reason:
                message += f"\n{reason}"
            await self.bot.send_message(user_id, message)
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.warning(f"Could not send points notification to user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error sending points notification to user {user_id}: {e}")

    async def send_level_up_notification(self, user_id: int, new_level: int) -> None:
        """Send level up notification via Telegram."""
        try:
            message = f"🎉 ¡Felicidades! Has alcanzado el nivel {new_level}"
            await self.bot.send_message(user_id, message)
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.warning(f"Could not send level up notification to user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error sending level up notification to user {user_id}: {e}")

    async def send_mission_complete_notification(
        self, user_id: int, mission_name: str, reward: int
    ) -> None:
        """Send mission completion notification via Telegram."""
        try:
            message = f"✅ ¡Misión completada!\n\n{mission_name}\n💰 +{reward} besitos"
            await self.bot.send_message(user_id, message)
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.warning(f"Could not send mission notification to user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error sending mission notification to user {user_id}: {e}")

    async def send_achievement_unlocked_notification(
        self, user_id: int, achievement_name: str
    ) -> None:
        """Send achievement unlock notification via Telegram."""
        try:
            message = f"🏆 ¡Logro desbloqueado!\n\n{achievement_name}"
            await self.bot.send_message(user_id, message)
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.warning(f"Could not send achievement notification to user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error sending achievement notification to user {user_id}: {e}")

    async def send_generic_notification(self, user_id: int, message: str) -> None:
        """Send generic notification via Telegram."""
        try:
            await self.bot.send_message(user_id, message)
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.warning(f"Could not send notification to user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
