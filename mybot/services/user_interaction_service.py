"""
Implementación del servicio de procesamiento de interacciones de usuario.
Procesa, valida y registra todas las interacciones del bot de forma centralizada.
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError

from services.interfaces.user_interaction_interface import (
    IUserInteractionProcessor,
    InteractionContext,
    InteractionResult,
    InteractionType
)
from services.interfaces.emotional_state_interface import (
    IEmotionalStateManager,
    EmotionalState
)
from services.interfaces.point_interface import IPointService
from services.interfaces.notification_interface import INotificationService
from database.models import InteractionLog, User
from database.emotional_state_models import UserEmotionalState
from utils.handler_decorators import safe_handler


logger = logging.getLogger(__name__)


class UserInteractionService(IUserInteractionProcessor):
    """
    Servicio concreto para el procesamiento de interacciones de usuario.
    Implementa logging, validación y procesamiento centralizado.
    """
    
    def __init__(self, 
                 session: AsyncSession, 
                 emotional_manager: Optional[IEmotionalStateManager] = None,
                 point_service: Optional[IPointService] = None,
                 notification_service: Optional[INotificationService] = None):
        """
        Inicializa el servicio con las dependencias necesarias.
        
        Args:
            session: Sesión de base de datos
            emotional_manager: Gestor de estados emocionales (opcional)
            point_service: Servicio de puntos (opcional)
            notification_service: Servicio de notificaciones (opcional)
        """
        self.session = session
        self.emotional_manager = emotional_manager
        self.point_service = point_service
        self.notification_service = notification_service
    
    async def process_interaction(self, context: InteractionContext) -> InteractionResult:
        """
        Procesa una interacción de usuario de forma centralizada y consistente.
        
        Args:
            context: Contexto completo de la interacción
            
        Returns:
            InteractionResult: Resultado del procesamiento con efectos secundarios
            
        Raises:
            ValueError: Si el contexto es inválido
            RuntimeError: Si ocurre un error durante el procesamiento
        """
        logger.debug(f"Processing interaction for user {context.user_id}, type: {context.interaction_type.value}")
        
        try:
            # Validar contexto antes del procesamiento
            is_valid, validation_errors = await self.validate_interaction(context)
            if not is_valid:
                logger.warning(f"Invalid interaction context: {validation_errors}")
                return InteractionResult(
                    success=False,
                    response_data={"errors": validation_errors},
                    side_effects=["validation_failed"],
                    emotional_impact=None,
                    points_awarded=None
                )
            
            # Inicializar resultado
            result = InteractionResult(
                success=True,
                response_data={},
                side_effects=[],
                emotional_impact=None,
                points_awarded=None
            )
            
            # Procesar según el tipo de interacción
            await self._process_by_type(context, result)
            
            # Analizar impacto emocional si hay gestor disponible
            if self.emotional_manager:
                try:
                    emotional_state = await self.emotional_manager.analyze_interaction_emotion(
                        context.user_id, 
                        context.raw_data
                    )
                    result.emotional_impact = emotional_state
                    result.side_effects.append("emotional_analysis_completed")
                    logger.debug(f"Emotional impact analyzed: {emotional_state.value}")
                except Exception as e:
                    logger.warning(f"Failed to analyze emotional impact: {e}")
                    result.side_effects.append("emotional_analysis_failed")
            
            # Procesar puntos si hay servicio disponible
            if self.point_service and result.success:
                points = await self._calculate_interaction_points(context)
                if points > 0:
                    try:
                        await self.point_service.add_points(context.user_id, points, "interaction_reward")
                        result.points_awarded = points
                        result.side_effects.append("points_awarded")
                        logger.debug(f"Awarded {points} points to user {context.user_id}")
                    except Exception as e:
                        logger.error(f"Failed to award points: {e}")
                        result.side_effects.append("points_award_failed")
            
            # Registrar la interacción
            await self.log_interaction(context, result)
            
            logger.info(f"Interaction processed successfully for user {context.user_id}")
            return result
            
        except ValueError as e:
            logger.error(f"Validation error in process_interaction: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in process_interaction: {e}", exc_info=True)
            raise RuntimeError(f"Failed to process interaction: {str(e)}")
    
    async def validate_interaction(self, context: InteractionContext) -> Tuple[bool, List[str]]:
        """
        Valida si una interacción puede ser procesada según las reglas del sistema.
        
        Args:
            context: Contexto de la interacción a validar
            
        Returns:
            Tuple[bool, List[str]]: (Es válida, Lista de errores de validación)
        """
        errors = []
        
        # Validar contexto básico
        if not context.user_id:
            errors.append("user_id is required")
        
        if not context.interaction_type:
            errors.append("interaction_type is required")
        
        if not context.raw_data:
            errors.append("raw_data cannot be empty")
        
        if not context.timestamp:
            errors.append("timestamp is required")
        
        # Validar que el usuario existe
        try:
            result = await self.session.execute(select(User).where(User.id == context.user_id))
            user = result.scalar_one_or_none()
            if not user:
                errors.append(f"User {context.user_id} not found")
        except SQLAlchemyError as e:
            logger.error(f"Database error during user validation: {e}")
            errors.append("database_error_during_validation")
        
        # Validar tipo de interacción específicos
        if context.interaction_type == InteractionType.CALLBACK:
            if "callback_data" not in context.raw_data:
                errors.append("callback_data required for CALLBACK interactions")
        
        elif context.interaction_type == InteractionType.MESSAGE:
            if "text" not in context.raw_data and "content_type" not in context.raw_data:
                errors.append("text or content_type required for MESSAGE interactions")
        
        # Validar rate limiting (máximo 100 interacciones por minuto por usuario)
        try:
            recent_count = await self._get_recent_interaction_count(context.user_id, minutes=1)
            if recent_count > 100:
                errors.append("rate_limit_exceeded")
        except Exception as e:
            logger.warning(f"Failed to check rate limit: {e}")
            # No agregamos como error crítico, solo lo registramos
        
        return len(errors) == 0, errors
    
    async def log_interaction(self, context: InteractionContext, result: InteractionResult) -> None:
        """
        Registra una interacción y su resultado en el sistema de logging.
        
        Args:
            context: Contexto de la interacción
            result: Resultado del procesamiento
            
        Raises:
            RuntimeError: Si falla el logging
        """
        try:
            interaction_log = InteractionLog(
                user_id=context.user_id,
                interaction_type=context.interaction_type.value,
                raw_data=context.raw_data,
                result_data=result.response_data,
                emotional_impact=result.emotional_impact.value if result.emotional_impact else None,
                points_awarded=result.points_awarded,
                success=result.success,
                side_effects=result.side_effects,
                session_data=context.session_data,
                created_at=context.timestamp
            )
            
            self.session.add(interaction_log)
            await self.session.commit()
            
            logger.debug(f"Interaction logged successfully for user {context.user_id}")
            
        except SQLAlchemyError as e:
            logger.error(f"Database error during interaction logging: {e}")
            await self.session.rollback()
            raise RuntimeError(f"Failed to log interaction: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during interaction logging: {e}")
            await self.session.rollback()
            raise RuntimeError(f"Failed to log interaction: {str(e)}")
    
    async def get_interaction_history(self, user_id: int, limit: int = 50) -> List[InteractionContext]:
        """
        Obtiene el historial de interacciones de un usuario.
        
        Args:
            user_id: ID del usuario de Telegram
            limit: Número máximo de interacciones a retornar
            
        Returns:
            List[InteractionContext]: Lista de interacciones en orden cronológico descendente
            
        Raises:
            ValueError: Si el user_id es inválido o limit es negativo
        """
        if not user_id or user_id <= 0:
            raise ValueError("user_id must be a positive integer")
        
        if limit < 0:
            raise ValueError("limit cannot be negative")
        
        # Limitar el máximo para prevenir sobrecarga
        limit = min(limit, 500)
        
        try:
            result = await self.session.execute(
                select(InteractionLog)
                .where(InteractionLog.user_id == user_id)
                .order_by(InteractionLog.created_at.desc())
                .limit(limit)
            )
            
            logs = result.scalars().all()
            
            # Convertir logs a InteractionContext
            interactions = []
            for log in logs:
                try:
                    interaction_type = InteractionType(log.interaction_type)
                    context = InteractionContext(
                        user_id=log.user_id,
                        interaction_type=interaction_type,
                        raw_data=log.raw_data or {},
                        timestamp=log.created_at,
                        session_data=log.session_data or {}
                    )
                    interactions.append(context)
                except ValueError as e:
                    logger.warning(f"Invalid interaction type in log {log.id}: {e}")
                    continue
            
            logger.debug(f"Retrieved {len(interactions)} interactions for user {user_id}")
            return interactions
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving interaction history: {e}")
            raise RuntimeError(f"Failed to retrieve interaction history: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving interaction history: {e}")
            raise RuntimeError(f"Failed to retrieve interaction history: {str(e)}")
    
    async def _process_by_type(self, context: InteractionContext, result: InteractionResult) -> None:
        """
        Procesa la interacción según su tipo específico.
        
        Args:
            context: Contexto de la interacción
            result: Resultado a modificar con los datos del procesamiento
        """
        if context.interaction_type == InteractionType.MESSAGE:
            result.response_data["processed_as"] = "message"
            result.side_effects.append("message_processed")
            
        elif context.interaction_type == InteractionType.CALLBACK:
            result.response_data["processed_as"] = "callback"
            result.response_data["callback_data"] = context.raw_data.get("callback_data")
            result.side_effects.append("callback_processed")
            
        elif context.interaction_type == InteractionType.REACTION:
            result.response_data["processed_as"] = "reaction"
            result.response_data["reaction_type"] = context.raw_data.get("emoji")
            result.side_effects.append("reaction_processed")
            
        elif context.interaction_type == InteractionType.COMMAND:
            result.response_data["processed_as"] = "command"
            result.response_data["command"] = context.raw_data.get("command")
            result.side_effects.append("command_processed")
            
        else:
            result.response_data["processed_as"] = "generic"
            result.side_effects.append("generic_processing")
    
    async def _calculate_interaction_points(self, context: InteractionContext) -> int:
        """
        Calcula los puntos a otorgar por una interacción.
        
        Args:
            context: Contexto de la interacción
            
        Returns:
            int: Puntos a otorgar (0 si no aplica)
        """
        base_points = {
            InteractionType.MESSAGE: 1,
            InteractionType.CALLBACK: 2,
            InteractionType.REACTION: 3,
            InteractionType.COMMAND: 1,
            InteractionType.INLINE_QUERY: 2,
            InteractionType.POLL_ANSWER: 5
        }
        
        return base_points.get(context.interaction_type, 0)
    
    async def _get_recent_interaction_count(self, user_id: int, minutes: int) -> int:
        """
        Obtiene el conteo de interacciones recientes para rate limiting.
        
        Args:
            user_id: ID del usuario
            minutes: Minutos hacia atrás a considerar
            
        Returns:
            int: Número de interacciones en el período
        """
        from datetime import datetime, timedelta
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        try:
            result = await self.session.execute(
                select(InteractionLog)
                .where(
                    InteractionLog.user_id == user_id,
                    InteractionLog.created_at >= cutoff_time
                )
            )
            
            return len(result.scalars().all())
            
        except SQLAlchemyError:
            # En caso de error, permitir la interacción
            return 0