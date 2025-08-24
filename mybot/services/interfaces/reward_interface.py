from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from database.models import User


class IRewardSystem(ABC):
    """
    Interfaz para el sistema centralizado de recompensas.
    Define las operaciones necesarias para gestionar recompensas a usuarios.
    """
    
    @abstractmethod
    async def grant_reward(self, user_id: int, reward_type: str, reward_data: dict, source: Optional[str] = None) -> None:
        """
        Otorga recompensas de manera unificada
        
        Args:
            user_id (int): ID del usuario
            reward_type (str): Tipo de recompensa ('points', 'clue', 'achievement')
            reward_data (dict): Datos específicos de la recompensa
            source (str, optional): Origen de la recompensa
            
        Raises:
            ValueError: Si el usuario no existe
        """
        pass
    
    @abstractmethod
    async def _grant_points_reward(self, user: User, reward_data: Dict[str, Any], source: Optional[str] = None) -> None:
        """
        Otorga recompensa de puntos
        
        Args:
            user (User): Instancia de User
            reward_data (dict): Datos de la recompensa
            source (str, optional): Origen de la recompensa
        """
        pass
    
    @abstractmethod
    async def _grant_clue_reward(self, user: User, reward_data: Dict[str, Any], source: Optional[str] = None) -> None:
        """
        Otorga recompensa de pista
        
        Args:
            user (User): Instancia de User
            reward_data (dict): Datos de la recompensa
            source (str, optional): Origen de la recompensa
        """
        pass
    
    @abstractmethod
    async def _grant_achievement_reward(self, user: User, reward_data: Dict[str, Any], source: Optional[str] = None) -> None:
        """
        Otorga recompensa de logro
        
        Args:
            user (User): Instancia de User
            reward_data (dict): Datos de la recompensa
            source (str, optional): Origen de la recompensa
        """
        pass