from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Union, Dict, Any, Tuple, List

class ContentType(Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    INTERACTIVE = "interactive"

class DeliveryChannel(Enum):
    DIRECT_MESSAGE = "direct_message"
    CHANNEL = "channel"
    CALLBACK = "callback"
    INLINE = "inline"

@dataclass
class ContentPackage:
    content_id: str
    content_type: ContentType
    payload: Union[str, bytes, Dict[str, Any]]
    metadata: Dict[str, Any]
    delivery_options: Dict[str, Any]

class IContentDeliveryService(ABC):
    """
    Interfaz para un sistema unificado de entrega de contenido con personalización contextual.
    """

    @abstractmethod
    async def prepare_content(self, content_id: str, context: Dict[str, Any]) -> ContentPackage:
        """
        Prepara un paquete de contenido basado en un ID y un contexto.

        Args:
            content_id: Identificador único del contenido.
            context: Diccionario con información contextual (e.g., user_id, chat_id).

        Returns:
            Un objeto ContentPackage listo para ser entregado.
        """
        pass

    @abstractmethod
    async def deliver_content(self, package: ContentPackage, context: Dict[str, Any]) -> bool:
        """
        Entrega un paquete de contenido a un canal específico.

        Args:
            package: El paquete de contenido a entregar.
            context: Diccionario con información sobre el destino de la entrega.

        Returns:
            True si la entrega fue exitosa, False en caso contrario.
        """
        pass

    @abstractmethod
    async def personalize_content(self, content: str, context: Dict[str, Any]) -> str:
        """
        Personaliza una cadena de texto usando variables de un contexto.

        Args:
            content: La cadena de texto a personalizar.
            context: Diccionario con las variables para la personalización.

        Returns:
            La cadena de texto personalizada.
        """
        pass

    @abstractmethod
    async def validate_delivery_constraints(self, package: ContentPackage, context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida si se cumplen las restricciones de entrega para un paquete.

        Args:
            package: El paquete de contenido.
            context: El contexto de la entrega.

        Returns:
            Una tupla con un booleano (True si es válido) y una lista de razones de fallo.
        """
        pass
