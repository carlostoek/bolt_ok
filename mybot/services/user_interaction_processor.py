"""
Procesador principal de interacciones de usuario con integración al ecosistema existente.
Proporciona una interfaz simplificada para usar el sistema de procesamiento de interacciones.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from aiogram.types import Message, CallbackQuery, InlineQuery
from sqlalchemy.ext.asyncio import AsyncSession

from services.user_interaction_service import UserInteractionService
from services.interfaces.user_interaction_interface import (
    InteractionContext,
    InteractionType,
    InteractionResult
)
from services.interfaces.emotional_state_interface import IEmotionalStateManager
from services.interfaces.point_interface import IPointService
from services.interfaces.notification_interface import INotificationService
from utils.handler_decorators import safe_handler


logger = logging.getLogger(__name__)


class UserInteractionProcessor:
    """
    Procesador principal que integra el sistema de interacciones con los servicios existentes.
    Proporciona métodos convenientes para procesar diferentes tipos de interacciones.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Inicializa el procesador con una sesión de base de datos.
        
        Args:
            session: Sesión de base de datos activa
        """
        self.session = session
        self._service: Optional[UserInteractionService] = None
    
    def _get_service(self) -> UserInteractionService:
        """
        Obtiene o crea la instancia del servicio de interacciones.
        Lazy initialization para evitar dependencias circulares.
        
        Returns:
            UserInteractionService: Instancia del servicio
        """
        if self._service is None:
            # Aquí podríamos inyectar dependencias desde el container
            # Por ahora creamos una instancia básica
            self._service = UserInteractionService(
                session=self.session,
                emotional_manager=None,  # Se puede inyectar después
                point_service=None,      # Se puede inyectar después
                notification_service=None # Se puede inyectar después
            )
        
        return self._service
    
    def set_dependencies(self, 
                        emotional_manager: Optional[IEmotionalStateManager] = None,
                        point_service: Optional[IPointService] = None,
                        notification_service: Optional[INotificationService] = None):
        """
        Configura las dependencias del procesador.
        
        Args:
            emotional_manager: Gestor de estados emocionales
            point_service: Servicio de puntos
            notification_service: Servicio de notificaciones
        """
        service = self._get_service()
        if emotional_manager:
            service.emotional_manager = emotional_manager
        if point_service:
            service.point_service = point_service
        if notification_service:
            service.notification_service = notification_service
        
        logger.debug("Dependencies configured for UserInteractionProcessor")
    
    @safe_handler("Error procesando interacción de mensaje")
    async def process_message_interaction(self, message: Message, session_data: Dict[str, Any] = None) -> InteractionResult:
        """
        Procesa una interacción de mensaje de Telegram.
        
        Args:
            message: Objeto Message de aiogram
            session_data: Datos adicionales de sesión
            
        Returns:
            InteractionResult: Resultado del procesamiento
        """
        raw_data = {
            "text": message.text,
            "message_id": message.message_id,
            "chat_id": message.chat.id,
            "content_type": message.content_type,
            "date": message.date.isoformat() if message.date else None
        }
        
        # Agregar datos adicionales si existen
        if message.photo:
            raw_data["has_photo"] = True
        if message.document:
            raw_data["has_document"] = True
        if message.video:
            raw_data["has_video"] = True
        
        context = InteractionContext(
            user_id=message.from_user.id,
            interaction_type=InteractionType.MESSAGE,
            raw_data=raw_data,
            timestamp=message.date or datetime.now(),
            session_data=session_data or {}
        )
        
        service = self._get_service()
        return await service.process_interaction(context)
    
    @safe_handler("Error procesando interacción de callback")
    async def process_callback_interaction(self, callback: CallbackQuery, session_data: Dict[str, Any] = None) -> InteractionResult:
        """
        Procesa una interacción de callback query de Telegram.
        
        Args:
            callback: Objeto CallbackQuery de aiogram
            session_data: Datos adicionales de sesión
            
        Returns:
            InteractionResult: Resultado del procesamiento
        """
        raw_data = {
            "callback_data": callback.data,
            "callback_id": callback.id,
            "message_id": callback.message.message_id if callback.message else None,
            "chat_id": callback.message.chat.id if callback.message else None,
            "inline_message_id": callback.inline_message_id
        }
        
        context = InteractionContext(
            user_id=callback.from_user.id,
            interaction_type=InteractionType.CALLBACK,
            raw_data=raw_data,
            timestamp=datetime.now(),
            session_data=session_data or {}
        )
        
        service = self._get_service()
        return await service.process_interaction(context)
    
    @safe_handler("Error procesando interacción de comando")
    async def process_command_interaction(self, message: Message, command: str, args: str = "", session_data: Dict[str, Any] = None) -> InteractionResult:
        """
        Procesa una interacción de comando de Telegram.
        
        Args:
            message: Objeto Message que contiene el comando
            command: Comando ejecutado (sin el /)
            args: Argumentos del comando
            session_data: Datos adicionales de sesión
            
        Returns:
            InteractionResult: Resultado del procesamiento
        """
        raw_data = {
            "command": command,
            "args": args,
            "full_text": message.text,
            "message_id": message.message_id,
            "chat_id": message.chat.id
        }
        
        context = InteractionContext(
            user_id=message.from_user.id,
            interaction_type=InteractionType.COMMAND,
            raw_data=raw_data,
            timestamp=message.date or datetime.now(),
            session_data=session_data or {}
        )
        
        service = self._get_service()
        return await service.process_interaction(context)
    
    @safe_handler("Error procesando interacción de reacción")
    async def process_reaction_interaction(self, user_id: int, emoji: str, target_message_id: int = None, session_data: Dict[str, Any] = None) -> InteractionResult:
        """
        Procesa una interacción de reacción.
        
        Args:
            user_id: ID del usuario que reaccionó
            emoji: Emoji usado en la reacción
            target_message_id: ID del mensaje al que se reaccionó
            session_data: Datos adicionales de sesión
            
        Returns:
            InteractionResult: Resultado del procesamiento
        """
        raw_data = {
            "emoji": emoji,
            "target_message_id": target_message_id,
            "reaction_type": "add"  # Podría ser 'add' o 'remove'
        }
        
        context = InteractionContext(
            user_id=user_id,
            interaction_type=InteractionType.REACTION,
            raw_data=raw_data,
            timestamp=datetime.now(),
            session_data=session_data or {}
        )
        
        service = self._get_service()
        return await service.process_interaction(context)
    
    @safe_handler("Error procesando consulta inline")
    async def process_inline_query_interaction(self, inline_query: InlineQuery, session_data: Dict[str, Any] = None) -> InteractionResult:
        """
        Procesa una interacción de inline query.
        
        Args:
            inline_query: Objeto InlineQuery de aiogram
            session_data: Datos adicionales de sesión
            
        Returns:
            InteractionResult: Resultado del procesamiento
        """
        raw_data = {
            "query": inline_query.query,
            "query_id": inline_query.id,
            "offset": inline_query.offset,
            "chat_type": inline_query.chat_type
        }
        
        context = InteractionContext(
            user_id=inline_query.from_user.id,
            interaction_type=InteractionType.INLINE_QUERY,
            raw_data=raw_data,
            timestamp=datetime.now(),
            session_data=session_data or {}
        )
        
        service = self._get_service()
        return await service.process_interaction(context)
    
    async def get_user_interaction_history(self, user_id: int, limit: int = 50) -> list:
        """
        Obtiene el historial de interacciones de un usuario.
        
        Args:
            user_id: ID del usuario
            limit: Límite de interacciones a retornar
            
        Returns:
            list: Lista de InteractionContext
        """
        service = self._get_service()
        return await service.get_interaction_history(user_id, limit)
    
    async def validate_user_interaction(self, context: InteractionContext) -> tuple:
        """
        Valida una interacción de usuario.
        
        Args:
            context: Contexto de la interacción
            
        Returns:
            tuple: (es_válida, errores)
        """
        service = self._get_service()
        return await service.validate_interaction(context)


# Factory function para crear instancias del procesador
def create_interaction_processor(session: AsyncSession) -> UserInteractionProcessor:
    """
    Crea una instancia del procesador de interacciones.
    
    Args:
        session: Sesión de base de datos
        
    Returns:
        UserInteractionProcessor: Instancia configurada del procesador
    """
    return UserInteractionProcessor(session)