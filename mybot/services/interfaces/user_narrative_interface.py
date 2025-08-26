from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field

from database.narrative_unified import UserNarrativeState, NarrativeFragment


@dataclass
class NarrativeServiceResult:
    """Resultado estandarizado para operaciones del servicio narrativo."""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)


class IUserNarrativeService(ABC):
    """
    Interfaz para el servicio de gestión narrativa de usuario.
    Define las operaciones necesarias para manejar el estado narrativo de los usuarios.
    """
    
    @abstractmethod
    async def get_or_create_user_state(self, user_id: int) -> UserNarrativeState:
        """
        Obtiene o crea el estado narrativo de un usuario.
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            UserNarrativeState: Estado narrativo del usuario
            
        Raises:
            ValueError: Si el usuario no existe
        """
        pass
    
    @abstractmethod
    async def update_current_fragment(self, user_id: int, fragment_id: str) -> UserNarrativeState:
        """
        Actualiza el fragmento actual del usuario.
        
        Args:
            user_id (int): ID del usuario
            fragment_id (str): ID del fragmento
            
        Returns:
            UserNarrativeState: Estado narrativo actualizado del usuario
            
        Raises:
            ValueError: Si el fragmento no existe o está inactivo
        """
        pass
    
    @abstractmethod
    async def mark_fragment_completed(self, user_id: int, fragment_id: str) -> UserNarrativeState:
        """
        Marca un fragmento como completado por el usuario.
        
        Args:
            user_id (int): ID del usuario
            fragment_id (str): ID del fragmento
            
        Returns:
            UserNarrativeState: Estado narrativo actualizado del usuario
            
        Raises:
            ValueError: Si el fragmento no existe o está inactivo
        """
        pass
    
    @abstractmethod
    async def unlock_clue(self, user_id: int, clue_code: str) -> UserNarrativeState:
        """
        Desbloquea una pista para el usuario.
        
        Args:
            user_id (int): ID del usuario
            clue_code (str): Código de la pista a desbloquear
            
        Returns:
            UserNarrativeState: Estado narrativo actualizado del usuario
            
        Raises:
            ValueError: Si la pista no existe o está inactiva
        """
        pass
    
    @abstractmethod
    async def check_user_access(self, user_id: int, fragment_id: str) -> bool:
        """
        Verifica si un usuario tiene acceso a un fragmento.
        
        Args:
            user_id (int): ID del usuario
            fragment_id (str): ID del fragmento
            
        Returns:
            bool: True si el usuario tiene acceso, False en caso contrario
        """
        pass
    
    @abstractmethod
    async def get_user_progress_percentage(self, user_id: int) -> float:
        """
        Obtiene el porcentaje de progreso del usuario.
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            float: Porcentaje de progreso (0-100)
        """
        pass
    
    @abstractmethod
    async def reset_user_progress(self, user_id: int) -> UserNarrativeState:
        """
        Restablece el progreso narrativo del usuario.
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            UserNarrativeState: Estado narrativo reiniciado del usuario
        """
        pass