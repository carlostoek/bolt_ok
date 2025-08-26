"""
Servicio de gestión de estados emocionales para usuarios.
Implementa la lógica de análisis y personalización basada en emociones.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert

from services.interfaces.emotional_state_interface import (
    IEmotionalStateManager, EmotionalState, EmotionalContext
)
from database.emotional_state_models import (
    UserEmotionalState, EmotionalStateHistory, EmotionalStateEnum
)
from database.models import User

logger = logging.getLogger(__name__)


class EmotionalStateService(IEmotionalStateManager):
    """
    Implementación concreta del gestor de estados emocionales.
    Gestiona el tracking y análisis de estados emocionales de usuarios.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio de estados emocionales.
        
        Args:
            session: Sesión de base de datos asíncrona
        """
        self.session = session
        
        # Mapeo de tonos basados en estados emocionales
        self.tone_mapping = {
            EmotionalState.NEUTRAL: "balanced",
            EmotionalState.CURIOUS: "intriguing", 
            EmotionalState.ENGAGED: "energetic",
            EmotionalState.CONFUSED: "supportive",
            EmotionalState.FRUSTRATED: "gentle",
            EmotionalState.SATISFIED: "encouraging",
            EmotionalState.EXCITED: "enthusiastic"
        }
    
    async def get_user_emotional_state(self, user_id: int) -> EmotionalContext:
        """
        Obtiene el contexto emocional actual de un usuario.
        Si el usuario no tiene estado registrado, crea uno neutral.
        """
        try:
            # Verificar que el usuario existe
            user_result = await self.session.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise ValueError(f"Usuario {user_id} no encontrado")
            
            # Obtener estado emocional actual
            result = await self.session.execute(
                select(UserEmotionalState).where(UserEmotionalState.user_id == user_id)
            )
            emotional_state = result.scalar_one_or_none()
            
            if not emotional_state:
                # Crear estado neutral por defecto
                logger.info(f"Creando estado emocional neutral para usuario {user_id}")
                emotional_state = await self._create_default_emotional_state(user_id)
            
            return self._convert_to_emotional_context(emotional_state)
            
        except Exception as e:
            logger.error(f"Error obteniendo estado emocional para usuario {user_id}: {e}")
            raise
    
    async def update_emotional_state(self, user_id: int, state: EmotionalState, 
                                   intensity: float, trigger: str) -> EmotionalContext:
        """
        Actualiza el estado emocional de un usuario.
        Registra el cambio en el historial.
        """
        # Validar intensidad
        if not 0.0 <= intensity <= 1.0:
            raise ValueError("Intensity must be between 0.0 and 1.0")
        
        try:
            # Verificar que el usuario existe
            user_result = await self.session.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                raise ValueError(f"Usuario {user_id} no encontrado")
            
            # Obtener estado actual para historial
            current_result = await self.session.execute(
                select(UserEmotionalState).where(UserEmotionalState.user_id == user_id)
            )
            current_state = current_result.scalar_one_or_none()
            
            # Convertir EmotionalState a EmotionalStateEnum
            state_enum = EmotionalStateEnum(state.value)
            
            # Actualizar o crear estado emocional
            if current_state:
                # Registrar en historial antes de actualizar
                await self._record_state_change(
                    user_id, current_state.primary_state, state_enum, 
                    current_state.intensity, intensity, trigger
                )
                
                # Actualizar estado existente
                await self.session.execute(
                    update(UserEmotionalState)
                    .where(UserEmotionalState.user_id == user_id)
                    .values(
                        primary_state=state_enum,
                        intensity=intensity,
                        triggers=self._update_triggers_list(current_state.triggers, trigger),
                        updated_at=datetime.now()
                    )
                )
            else:
                # Crear nuevo estado
                new_state = UserEmotionalState(
                    user_id=user_id,
                    primary_state=state_enum,
                    intensity=intensity,
                    secondary_states={},
                    triggers=[trigger]
                )
                self.session.add(new_state)
                
                # Registrar en historial
                await self._record_state_change(
                    user_id, None, state_enum, None, intensity, trigger
                )
            
            await self.session.commit()
            
            # Retornar contexto actualizado
            updated_result = await self.session.execute(
                select(UserEmotionalState).where(UserEmotionalState.user_id == user_id)
            )
            updated_state = updated_result.scalar_one()
            
            logger.info(f"Estado emocional actualizado para usuario {user_id}: {state.value} (intensity={intensity})")
            return self._convert_to_emotional_context(updated_state)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error actualizando estado emocional para usuario {user_id}: {e}")
            raise
    
    async def analyze_interaction_emotion(self, user_id: int, 
                                        interaction_data: Dict) -> EmotionalState:
        """
        Analiza los datos de interacción para inferir el estado emocional.
        Implementa lógica heurística basada en patrones de interacción.
        """
        try:
            interaction_type = interaction_data.get("type", "")
            
            # Análisis basado en tipo de interacción
            if interaction_type == "fragment_completion":
                completion_time = interaction_data.get("completion_time", 60)
                choice = interaction_data.get("user_choice", "")
                
                if completion_time < 30:  # Completado rápidamente
                    if "positive" in choice.lower():
                        return EmotionalState.EXCITED
                    else:
                        return EmotionalState.ENGAGED
                elif completion_time > 180:  # Tardó mucho
                    return EmotionalState.CONFUSED
                else:
                    return EmotionalState.SATISFIED
            
            elif interaction_type == "choice_selection":
                choice_text = interaction_data.get("choice_text", "").lower()
                if any(word in choice_text for word in ["ayudar", "positivo", "bueno"]):
                    return EmotionalState.SATISFIED
                elif any(word in choice_text for word in ["explorar", "descubrir", "investigar"]):
                    return EmotionalState.CURIOUS
                else:
                    return EmotionalState.ENGAGED
            
            elif interaction_type == "failed_attempt":
                attempts = interaction_data.get("attempts", 1)
                if attempts >= 3:
                    return EmotionalState.FRUSTRATED
                else:
                    return EmotionalState.CONFUSED
            
            # Por defecto, mantener estado neutral
            return EmotionalState.NEUTRAL
            
        except Exception as e:
            logger.error(f"Error analizando emoción de interacción para usuario {user_id}: {e}")
            return EmotionalState.NEUTRAL
    
    async def get_recommended_content_tone(self, user_id: int) -> str:
        """
        Obtiene el tono recomendado para el contenido basado en el estado emocional actual.
        """
        try:
            context = await self.get_user_emotional_state(user_id)
            tone = self.tone_mapping.get(context.primary_state, "balanced")
            
            logger.debug(f"Tono recomendado para usuario {user_id}: {tone} (estado: {context.primary_state.value})")
            return tone
            
        except Exception as e:
            logger.error(f"Error obteniendo tono recomendado para usuario {user_id}: {e}")
            return "balanced"  # Tono por defecto
    
    # Métodos privados auxiliares
    
    async def _create_default_emotional_state(self, user_id: int) -> UserEmotionalState:
        """Crea un estado emocional neutral por defecto."""
        emotional_state = UserEmotionalState(
            user_id=user_id,
            primary_state=EmotionalStateEnum.NEUTRAL,
            intensity=0.0,
            secondary_states={},
            triggers=["initial_state"]
        )
        self.session.add(emotional_state)
        await self.session.commit()
        return emotional_state
    
    def _convert_to_emotional_context(self, db_state: UserEmotionalState) -> EmotionalContext:
        """Convierte el modelo de DB a EmotionalContext."""
        # Convertir EmotionalStateEnum de vuelta a EmotionalState
        primary_state = EmotionalState(db_state.primary_state.value)
        
        # Convertir secondary_states si existen
        secondary_states = {}
        for state_str, intensity in db_state.secondary_states.items():
            try:
                secondary_states[EmotionalState(state_str)] = float(intensity)
            except (ValueError, TypeError):
                continue  # Ignorar entradas inválidas
        
        return EmotionalContext(
            primary_state=primary_state,
            intensity=db_state.intensity,
            secondary_states=secondary_states,
            last_updated=db_state.updated_at,
            triggers=db_state.triggers or []
        )
    
    async def _record_state_change(self, user_id: int, previous_state: Optional[EmotionalStateEnum], 
                                 new_state: EmotionalStateEnum, previous_intensity: Optional[float],
                                 new_intensity: float, trigger: str):
        """Registra un cambio de estado en el historial."""
        history_entry = EmotionalStateHistory(
            user_id=user_id,
            previous_state=previous_state,
            new_state=new_state,
            previous_intensity=previous_intensity,
            new_intensity=new_intensity,
            trigger=trigger
        )
        self.session.add(history_entry)
    
    def _update_triggers_list(self, current_triggers: List[str], new_trigger: str) -> List[str]:
        """Actualiza la lista de triggers manteniendo los últimos 10."""
        triggers = current_triggers or []
        triggers.append(new_trigger)
        return triggers[-10:]  # Mantener solo los últimos 10 triggers