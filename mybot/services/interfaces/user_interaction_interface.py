"""
Interfaz para el procesamiento centralizado de interacciones de usuario.
Sistema unificado para manejar todas las interacciones del bot con logging y análisis emocional.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

from .emotional_state_interface import EmotionalState


class InteractionType(Enum):
    """Tipos de interacciones disponibles en el bot."""
    MESSAGE = "message"
    CALLBACK = "callback"
    INLINE_QUERY = "inline_query"
    POLL_ANSWER = "poll_answer"
    REACTION = "reaction"
    COMMAND = "command"


@dataclass
class InteractionContext:
    """Contexto completo de una interacción de usuario."""
    user_id: int
    interaction_type: InteractionType
    raw_data: Dict[str, Any]
    timestamp: datetime
    session_data: Dict[str, Any]


@dataclass
class ValidationResult:
    """Resultado estandarizado de validación."""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)


@dataclass
class InteractionResult:
    """Resultado estandarizado del procesamiento de una interacción."""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)


class IUserInteractionProcessor(ABC):
    """
    Interfaz para el procesador centralizado de interacciones de usuario.
    Define las operaciones necesarias para procesar, validar y registrar interacciones de usuario.
    """
    
    @abstractmethod
    async def process_interaction(self, context: InteractionContext) -> InteractionResult:
        """
        Procesa una interacción de usuario de forma centralizada y consistente.
        
        Args:
            context (InteractionContext): Contexto completo de la interacción
            
        Returns:
            InteractionResult: Resultado del procesamiento con efectos secundarios
            
        Raises:
            ValueError: Si el contexto es inválido
            RuntimeError: Si ocurre un error durante el procesamiento
        """
        pass
    
    @abstractmethod
    async def validate_interaction(self, context: InteractionContext) -> ValidationResult:
        """
        Valida si una interacción puede ser procesada según las reglas del sistema.
        
        Args:
            context (InteractionContext): Contexto de la interacción a validar
            
        Returns:
            ValidationResult: Resultado estructurado de la validación
        """
        pass
    
    @abstractmethod
    async def log_interaction(self, context: InteractionContext, result: InteractionResult) -> None:
        """
        Registra una interacción y su resultado en el sistema de logging.
        
        Args:
            context (InteractionContext): Contexto de la interacción
            result (InteractionResult): Resultado del procesamiento
            
        Raises:
            RuntimeError: Si falla el logging
        """
        pass
    
    @abstractmethod
    async def get_interaction_history(self, user_id: int, limit: int = 50) -> List[InteractionContext]:
        """
        Obtiene el historial de interacciones de un usuario.
        
        Args:
            user_id (int): ID del usuario de Telegram
            limit (int): Número máximo de interacciones a retornar
            
        Returns:
            List[InteractionContext]: Lista de interacciones en orden cronológico descendente
            
        Raises:
            ValueError: Si el user_id es inválido o limit es negativo
        """
        pass