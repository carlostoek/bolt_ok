"""
Interfaz para la entrega unificada de contenido narrativo.
Sistema centralizado para gestionar la entrega personalizada de contenido a usuarios.
"""
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .emotional_state_interface import EmotionalState


class ContentType(Enum):
    """Tipos de contenido disponibles en el sistema."""
    NARRATIVE_FRAGMENT = "narrative_fragment"
    LORE_PIECE = "lore_piece" 
    ACHIEVEMENT_NOTIFICATION = "achievement_notification"
    MISSION_UPDATE = "mission_update"
    SYSTEM_MESSAGE = "system_message"
    PROMOTIONAL = "promotional"
    EDUCATIONAL = "educational"


class DeliveryPriority(Enum):
    """Prioridad de entrega de contenido."""
    CRITICAL = 1    # Debe entregarse inmediatamente
    HIGH = 2        # Alta prioridad, entrega rápida
    MEDIUM = 3      # Prioridad normal
    LOW = 4         # Puede agregarse o diferirse
    BACKGROUND = 5  # Entrega en segundo plano


@dataclass
class ContentContext:
    """Contexto para la entrega de contenido."""
    user_id: int
    session_data: Dict[str, Any]
    emotional_state: Optional[EmotionalState]
    user_preferences: Dict[str, Any]
    interaction_history: List[Dict[str, Any]]
    timestamp: datetime


@dataclass
class ContentPackage:
    """Paquete de contenido preparado para entrega."""
    content_id: str
    content_type: ContentType
    priority: DeliveryPriority
    payload: Dict[str, Any]
    personalization_metadata: Dict[str, Any]
    delivery_constraints: Dict[str, Any]
    expiry_timestamp: Optional[datetime] = None


@dataclass
class DeliveryResult:
    """Resultado estandarizado de la entrega de contenido."""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)


@dataclass
class QueueOperationResult:
    """Resultado estandarizado de operaciones de cola."""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)


class IContentDeliveryService(ABC):
    """
    Interfaz para el servicio de entrega de contenido.
    Define las operaciones necesarias para personalizar y entregar contenido de forma unificada.
    """
    
    @abstractmethod
    async def prepare_content(self, content_id: str, content_type: ContentType, context: ContentContext) -> ContentPackage:
        """
        Prepara contenido para entrega personalizada basada en el contexto del usuario.
        
        Args:
            content_id (str): Identificador único del contenido
            content_type (ContentType): Tipo de contenido a preparar
            context (ContentContext): Contexto del usuario y sesión
            
        Returns:
            ContentPackage: Paquete de contenido personalizado listo para entrega
            
        Raises:
            ValueError: Si el contenido no existe o el contexto es inválido
            RuntimeError: Si falla la preparación del contenido
        """
        pass
    
    @abstractmethod
    async def deliver_content(self, content_package: ContentPackage, delivery_options: Dict[str, Any]) -> DeliveryResult:
        """
        Entrega contenido al usuario usando el canal apropiado.
        
        Args:
            content_package (ContentPackage): Paquete de contenido a entregar
            delivery_options (Dict[str, Any]): Opciones específicas de entrega
            
        Returns:
            DeliveryResult: Resultado de la operación de entrega
            
        Raises:
            RuntimeError: Si falla la entrega del contenido
        """
        pass
    
    @abstractmethod
    async def queue_content_for_delivery(self, content_packages: List[ContentPackage], user_id: int) -> QueueOperationResult:
        """
        Añade contenido a la cola de entrega con gestión de prioridades.
        
        Args:
            content_packages (List[ContentPackage]): Lista de contenido a encolar
            user_id (int): ID del usuario destinatario
            
        Returns:
            QueueOperationResult: Resultado de la operación de encolado
        """
        pass
    
    @abstractmethod
    async def get_personalized_content_queue(self, user_id: int) -> List[ContentPackage]:
        """
        Obtiene la cola de contenido personalizada para un usuario.
        
        Args:
            user_id (int): ID del usuario de Telegram
            
        Returns:
            List[ContentPackage]: Cola de contenido ordenada por prioridad y personalización
        """
        pass
    
    @abstractmethod
    async def optimize_content_timing(self, user_id: int, content_packages: List[ContentPackage]) -> List[Tuple[ContentPackage, datetime]]:
        """
        Optimiza el momento de entrega de contenido basado en patrones de usuario.
        
        Args:
            user_id (int): ID del usuario de Telegram
            content_packages (List[ContentPackage]): Contenido a optimizar
            
        Returns:
            List[Tuple[ContentPackage, datetime]]: Contenido con momentos óptimos de entrega
        """
        pass
    
    @abstractmethod
    async def track_content_engagement(self, user_id: int, content_id: str, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rastrea y analiza el engagement del usuario con contenido entregado.
        
        Args:
            user_id (int): ID del usuario de Telegram
            content_id (str): ID del contenido
            interaction_data (Dict[str, Any]): Datos de la interacción del usuario
            
        Returns:
            Dict[str, Any]: Métricas de engagement y análisis
        """
        pass
    
    @abstractmethod
    async def get_content_performance_analytics(self, content_type: Optional[ContentType] = None) -> Dict[str, Any]:
        """
        Obtiene analíticas de rendimiento del contenido entregado.
        
        Args:
            content_type (Optional[ContentType]): Tipo específico de contenido o None para todos
            
        Returns:
            Dict[str, Any]: Analíticas de rendimiento y engagement
        """
        pass
    
    @abstractmethod
    async def adapt_content_strategy(self, user_id: int, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapta la estrategia de entrega de contenido basada en datos de rendimiento.
        
        Args:
            user_id (int): ID del usuario de Telegram
            performance_data (Dict[str, Any]): Datos de rendimiento histórico
            
        Returns:
            Dict[str, Any]: Nueva estrategia de entrega adaptada
        """
        pass