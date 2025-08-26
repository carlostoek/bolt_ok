"""
Interfaz para el manejo de estados emocionales de usuarios.
Sistema de gestión de emociones para personalización narrativa.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class EmotionalState(Enum):
    """Estados emocionales disponibles para los usuarios."""
    NEUTRAL = "neutral"
    CURIOUS = "curious"
    ENGAGED = "engaged"
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"
    SATISFIED = "satisfied"
    EXCITED = "excited"


@dataclass
class EmotionalContext:
    """Contexto emocional completo de un usuario."""
    primary_state: EmotionalState
    intensity: float  # 0.0 to 1.0
    secondary_states: Dict[EmotionalState, float]
    last_updated: datetime
    triggers: List[str]  # What caused this state


class IEmotionalStateManager(ABC):
    """
    Interfaz para el gestor de estados emocionales.
    Define las operaciones necesarias para rastrear y analizar estados emocionales de usuarios.
    """
    
    @abstractmethod
    async def get_user_emotional_state(self, user_id: int) -> EmotionalContext:
        """
        Obtiene el contexto emocional actual de un usuario.
        
        Args:
            user_id (int): ID del usuario de Telegram
            
        Returns:
            EmotionalContext: Contexto emocional actual del usuario
            
        Raises:
            ValueError: Si el usuario no existe
        """
        pass
    
    @abstractmethod
    async def update_emotional_state(self, user_id: int, state: EmotionalState, 
                                   intensity: float, trigger: str) -> EmotionalContext:
        """
        Actualiza el estado emocional de un usuario basado en interacción.
        
        Args:
            user_id (int): ID del usuario
            state (EmotionalState): Nuevo estado emocional primario
            intensity (float): Intensidad del estado (0.0 a 1.0)
            trigger (str): Descripción de lo que causó este cambio
            
        Returns:
            EmotionalContext: Contexto emocional actualizado
            
        Raises:
            ValueError: Si la intensidad está fuera del rango válido o el usuario no existe
        """
        pass
    
    @abstractmethod
    async def analyze_interaction_emotion(self, user_id: int, 
                                        interaction_data: Dict) -> EmotionalState:
        """
        Analiza los datos de interacción para determinar el estado emocional resultante.
        
        Args:
            user_id (int): ID del usuario
            interaction_data (Dict): Datos de la interacción a analizar
            
        Returns:
            EmotionalState: Estado emocional inferido de la interacción
        """
        pass
    
    @abstractmethod
    async def get_recommended_content_tone(self, user_id: int) -> str:
        """
        Obtiene el tono recomendado para el contenido basado en el estado emocional.
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            str: Tono recomendado para el contenido ('energetic', 'supportive', 'gentle', etc.)
        """
        pass