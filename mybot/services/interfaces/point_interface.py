from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Any

from aiogram import Bot
from database.models import User, UserStats
from database.transaction_models import PointTransaction


class IPointService(ABC):
    """
    Interfaz para el servicio de gestión de puntos.
    Define las operaciones necesarias para manejar la economía de puntos.
    """
    
    @abstractmethod
    async def _get_or_create_progress(self, user_id: int) -> UserStats:
        """
        Obtiene o crea el progreso de un usuario.
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            UserStats: Progreso del usuario
        """
        pass
    
    @abstractmethod
    async def award_message(self, user_id: int, bot: Bot) -> Optional[UserStats]:
        """
        Otorga puntos por envío de mensaje.
        
        Args:
            user_id (int): ID del usuario
            bot (Bot): Instancia del bot
            
        Returns:
            Optional[UserStats]: Progreso actualizado o None si no se otorgaron puntos
        """
        pass
    
    @abstractmethod
    async def award_reaction(self, user: User, message_id: int, bot: Bot) -> Optional[UserStats]:
        """
        Otorga puntos por reacción a un mensaje.
        
        Args:
            user (User): Instancia del usuario
            message_id (int): ID del mensaje
            bot (Bot): Instancia del bot
            
        Returns:
            Optional[UserStats]: Progreso actualizado o None si no se otorgaron puntos
        """
        pass
    
    @abstractmethod
    async def award_poll(self, user_id: int, bot: Bot) -> UserStats:
        """
        Otorga puntos por participación en encuesta.
        
        Args:
            user_id (int): ID del usuario
            bot (Bot): Instancia del bot
            
        Returns:
            UserStats: Progreso actualizado
        """
        pass
    
    @abstractmethod
    async def daily_checkin(self, user_id: int, bot: Bot) -> Tuple[bool, UserStats]:
        """
        Otorga puntos por check-in diario.
        
        Args:
            user_id (int): ID del usuario
            bot (Bot): Instancia del bot
            
        Returns:
            Tuple[bool, UserStats]: (Éxito, Progreso actualizado)
        """
        pass
    
    @abstractmethod
    async def add_points(self, user_id: int, points: float, *, 
                         bot: Optional[Bot] = None, 
                         skip_notification: bool = False,
                         source: str = "unknown") -> UserStats:
        """
        Añade puntos a un usuario.
        
        Args:
            user_id (int): ID del usuario
            points (float): Cantidad de puntos a añadir
            bot (Optional[Bot]): Instancia del bot
            skip_notification (bool): Si se debe omitir la notificación
            source (str): Origen de los puntos
            
        Returns:
            UserStats: Progreso actualizado
        """
        pass
    
    @abstractmethod
    async def deduct_points(self, user_id: int, points: int) -> Optional[User]:
        """
        Resta puntos a un usuario.
        
        Args:
            user_id (int): ID del usuario
            points (int): Cantidad de puntos a restar
            
        Returns:
            Optional[User]: Usuario actualizado o None si no se pudieron restar los puntos
        """
        pass
    
    @abstractmethod
    async def get_balance(self, user_id: int) -> float:
        """
        Obtiene el balance de puntos de un usuario.
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            float: Balance de puntos
        """
        pass
    
    @abstractmethod
    async def get_transaction_history(self, user_id: int) -> List[PointTransaction]:
        """
        Obtiene el historial de transacciones de un usuario.
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            List[PointTransaction]: Lista de transacciones
        """
        pass
    
    @abstractmethod
    async def get_user_points(self, user_id: int) -> int:
        """
        Obtiene los puntos de un usuario.
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            int: Puntos del usuario
        """
        pass
    
    @abstractmethod
    async def get_top_users(self, limit: int = 10) -> List[User]:
        """
        Obtiene los usuarios con más puntos.
        
        Args:
            limit (int): Límite de usuarios a retornar
            
        Returns:
            List[User]: Lista de usuarios
        """
        pass