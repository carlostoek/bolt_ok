from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class INotificationService(ABC):
    """
    Interfaz para el servicio centralizado de notificaciones.
    Define las operaciones necesarias para gestionar notificaciones a usuarios.
    """
    
    @abstractmethod
    async def add_notification(self, user_id: int, notification_type: str, 
                               data: Dict[str, Any], priority: int) -> None:
        """
        Añade una notificación a la cola con detección de duplicados.
        
        Args:
            user_id: ID del usuario de Telegram
            notification_type: Tipo de notificación
            data: Datos específicos de la notificación
            priority: Prioridad de la notificación
        """
        pass
    
    @abstractmethod
    async def send_immediate_notification(self, user_id: int, message: str, 
                                          priority: int) -> None:
        """
        Envía una notificación inmediata sin agregación.
        Útil para notificaciones críticas o de error.
        
        Args:
            user_id: ID del usuario
            message: Mensaje a enviar
            priority: Prioridad de la notificación
        """
        pass
    
    @abstractmethod
    async def flush_pending_notifications(self, user_id: int) -> None:
        """
        Fuerza el envío inmediato de todas las notificaciones pendientes.
        Útil para asegurar que el usuario reciba todo antes de una desconexión.
        
        Args:
            user_id: ID del usuario
        """
        pass
    
    @abstractmethod
    def get_pending_count(self, user_id: int) -> int:
        """
        Obtiene el número de notificaciones pendientes para un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            int: Número de notificaciones pendientes
        """
        pass
    
    @abstractmethod
    async def cleanup_user(self, user_id: int) -> None:
        """
        Limpia todos los datos relacionados con un usuario.
        
        Args:
            user_id: ID del usuario
        """
        pass