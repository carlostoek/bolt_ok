"""
Abstract Notifier Interface for decoupling notification logic from services.
"""
from abc import ABC, abstractmethod


class NotifierInterface(ABC):
    """
    Abstract interface for sending notifications to users.
    Allows different implementations (Telegram, WebSocket, Email, etc.)
    """

    @abstractmethod
    async def send_points_notification(self, user_id: int, points: float, reason: str = "") -> None:
        """
        Send notification about points earned.

        :param user_id: User ID to notify
        :param points: Amount of points earned
        :param reason: Reason for earning points
        """
        pass

    @abstractmethod
    async def send_level_up_notification(self, user_id: int, new_level: int) -> None:
        """
        Send notification about level up.

        :param user_id: User ID to notify
        :param new_level: New level reached
        """
        pass

    @abstractmethod
    async def send_mission_complete_notification(
        self, user_id: int, mission_name: str, reward: int
    ) -> None:
        """
        Send notification about mission completion.

        :param user_id: User ID to notify
        :param mission_name: Name of completed mission
        :param reward: Reward points
        """
        pass

    @abstractmethod
    async def send_achievement_unlocked_notification(
        self, user_id: int, achievement_name: str
    ) -> None:
        """
        Send notification about achievement unlock.

        :param user_id: User ID to notify
        :param achievement_name: Name of achievement
        """
        pass

    @abstractmethod
    async def send_generic_notification(self, user_id: int, message: str) -> None:
        """
        Send generic notification message.

        :param user_id: User ID to notify
        :param message: Message to send
        """
        pass
