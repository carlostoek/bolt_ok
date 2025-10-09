"""
Null implementation of NotifierInterface for testing or when notifications are not needed.
"""
import logging

from core.interfaces.notifier import NotifierInterface

logger = logging.getLogger(__name__)


class NullNotifier(NotifierInterface):
    """
    Null notifier that does nothing.
    Useful for testing or when notifications are disabled.
    """

    async def send_points_notification(self, user_id: int, points: float, reason: str = "") -> None:
        """Log instead of sending notification."""
        logger.debug(f"[NullNotifier] Points notification: user={user_id}, points={points}, reason={reason}")

    async def send_level_up_notification(self, user_id: int, new_level: int) -> None:
        """Log instead of sending notification."""
        logger.debug(f"[NullNotifier] Level up notification: user={user_id}, level={new_level}")

    async def send_mission_complete_notification(
        self, user_id: int, mission_name: str, reward: int
    ) -> None:
        """Log instead of sending notification."""
        logger.debug(
            f"[NullNotifier] Mission complete notification: user={user_id}, mission={mission_name}, reward={reward}"
        )

    async def send_achievement_unlocked_notification(
        self, user_id: int, achievement_name: str
    ) -> None:
        """Log instead of sending notification."""
        logger.debug(
            f"[NullNotifier] Achievement notification: user={user_id}, achievement={achievement_name}"
        )

    async def send_generic_notification(self, user_id: int, message: str) -> None:
        """Log instead of sending notification."""
        logger.debug(f"[NullNotifier] Generic notification: user={user_id}, message={message}")
