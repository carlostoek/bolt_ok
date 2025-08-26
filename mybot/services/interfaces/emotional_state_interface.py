"""
Interfaz para el manejo de estados emocionales de usuario.
Sistema unificado para análisis emocional y adaptación de contenido.
"""
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


class EmotionalTone(Enum):
    """Tonalidades emocionales detectables en interacciones."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    EXCITED = "excited"
    FRUSTRATED = "frustrated"
    CURIOUS = "curious"
    BORED = "bored"
    ENGAGED = "engaged"


class EmotionalIntensity(Enum):
    """Intensidad de la respuesta emocional."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class EmotionalState:
    """Representa el estado emocional actual de un usuario."""
    user_id: int
    primary_tone: EmotionalTone
    intensity: EmotionalIntensity
    confidence: float  # 0.0 - 1.0
    context_factors: Dict[str, Any]
    timestamp: datetime
    session_data: Optional[Dict[str, Any]] = None


@dataclass
class EmotionalProfile:
    """Perfil emocional histórico de un usuario."""
    user_id: int
    dominant_patterns: List[EmotionalTone]
    engagement_level: float  # 0.0 - 1.0
    response_preferences: Dict[str, Any]
    last_updated: datetime


@dataclass
class EmotionalAnalysisResult:
    """Resultado estandarizado de análisis emocional."""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)


@dataclass
class EmotionalProfileResult:
    """Resultado estandarizado de operaciones de perfil emocional."""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)


class IEmotionalStateManager(ABC):
    """
    Interfaz para el gestor de estados emocionales.
    Define las operaciones necesarias para análisis emocional y adaptación de contenido.
    """
    
    @abstractmethod
    async def analyze_interaction_emotion(self, user_id: int, interaction_data: Dict[str, Any]) -> EmotionalState:
        """
        Analiza el estado emocional de una interacción específica.
        
        Args:
            user_id (int): ID del usuario de Telegram
            interaction_data (Dict[str, Any]): Datos de la interacción (mensaje, callback, etc.)
            
        Returns:
            EmotionalState: Estado emocional detectado
            
        Raises:
            ValueError: Si los datos de interacción son inválidos
            RuntimeError: Si falla el análisis emocional
        """
        pass
    
    @abstractmethod
    async def update_user_emotional_profile(self, user_id: int, emotional_state: EmotionalState) -> EmotionalProfileResult:
        """
        Actualiza el perfil emocional histórico del usuario.
        
        Args:
            user_id (int): ID del usuario de Telegram
            emotional_state (EmotionalState): Estado emocional nuevo
            
        Returns:
            EmotionalProfileResult: Resultado de la actualización del perfil emocional
        """
        pass
    
    @abstractmethod
    async def get_user_emotional_profile(self, user_id: int) -> EmotionalProfileResult:
        """
        Obtiene el perfil emocional actual de un usuario.
        
        Args:
            user_id (int): ID del usuario de Telegram
            
        Returns:
            EmotionalProfileResult: Resultado con el perfil emocional o información de no encontrado
        """
        pass
    
    @abstractmethod
    async def suggest_content_adaptation(self, user_id: int, base_content: Dict[str, Any]) -> EmotionalAnalysisResult:
        """
        Sugiere adaptaciones de contenido basadas en el estado emocional del usuario.
        
        Args:
            user_id (int): ID del usuario de Telegram
            base_content (Dict[str, Any]): Contenido base a adaptar
            
        Returns:
            EmotionalAnalysisResult: Resultado con contenido adaptado y recomendaciones emocionales
        """
        pass
    
    @abstractmethod
    async def detect_emotional_triggers(self, user_id: int, content_history: List[Dict[str, Any]]) -> EmotionalAnalysisResult:
        """
        Detecta patrones que desencadenan respuestas emocionales específicas.
        
        Args:
            user_id (int): ID del usuario de Telegram
            content_history (List[Dict[str, Any]]): Historial de contenido e interacciones
            
        Returns:
            EmotionalAnalysisResult: Resultado con triggers emocionales identificados
        """
        pass
    
    @abstractmethod
    async def get_engagement_recommendations(self, user_id: int) -> EmotionalAnalysisResult:
        """
        Genera recomendaciones para mejorar el engagement basado en el estado emocional.
        
        Args:
            user_id (int): ID del usuario de Telegram
            
        Returns:
            EmotionalAnalysisResult: Resultado con recomendaciones de engagement y estrategias específicas
        """
        pass