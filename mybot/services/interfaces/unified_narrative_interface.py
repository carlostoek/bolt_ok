"""
Interfaz unificada para operaciones narrativas.
Sistema central que orquesta todas las operaciones relacionadas con la narrativa Diana.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from .user_narrative_interface import IUserNarrativeService
from .emotional_state_interface import IEmotionalStateManager, EmotionalState
from .content_delivery_interface import IContentDeliveryService, ContentPackage, ContentType
from .user_interaction_interface import IUserInteractionProcessor, InteractionResult
from database.narrative_unified import NarrativeFragment, UserNarrativeState


@dataclass
class NarrativeOperationResult:
    """Resultado estandarizado para operaciones narrativas."""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)


@dataclass
class AnalyticsResult:
    """Resultado estandarizado para analíticas narrativas."""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)


@dataclass
class ConfigurationResult:
    """Resultado estandarizado para operaciones de configuración."""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)


class IUnifiedNarrativeOrchestrator(ABC):
    """
    Interfaz para el orquestador narrativo unificado.
    Coordina todas las operaciones narrativas de forma cohesiva y consistente.
    """
    
    @abstractmethod
    async def process_narrative_interaction(self, user_id: int, interaction_data: Dict[str, Any]) -> NarrativeOperationResult:
        """
        Procesa una interacción narrativa de forma completa e integrada.
        
        Args:
            user_id (int): ID del usuario de Telegram
            interaction_data (Dict[str, Any]): Datos completos de la interacción
            
        Returns:
            NarrativeOperationResult: Resultado completo con efectos en narrativa, emociones y contenido
        """
        pass
    
    @abstractmethod
    async def advance_user_narrative(self, user_id: int, target_fragment_id: str, context: Dict[str, Any]) -> NarrativeOperationResult:
        """
        Avanza la narrativa del usuario con análisis emocional y entrega personalizada.
        
        Args:
            user_id (int): ID del usuario de Telegram
            target_fragment_id (str): ID del fragmento objetivo
            context (Dict[str, Any]): Contexto de la progresión
            
        Returns:
            NarrativeOperationResult: Estado actualizado con contenido personalizado
        """
        pass
    
    @abstractmethod
    async def deliver_personalized_narrative_content(self, user_id: int, fragment_id: str) -> ContentPackage:
        """
        Prepara y personaliza contenido narrativo basado en el perfil emocional del usuario.
        
        Args:
            user_id (int): ID del usuario de Telegram
            fragment_id (str): ID del fragmento narrativo
            
        Returns:
            ContentPackage: Contenido narrativo personalizado
            
        Raises:
            ValueError: Si el fragmento no existe o no es accesible
        """
        pass
    
    @abstractmethod
    async def analyze_narrative_engagement(self, user_id: int, timeframe_days: int = 30) -> AnalyticsResult:
        """
        Analiza el engagement narrativo del usuario en un periodo específico.
        
        Args:
            user_id (int): ID del usuario de Telegram
            timeframe_days (int): Días hacia atrás para el análisis
            
        Returns:
            AnalyticsResult: Análisis completo de engagement narrativo
        """
        pass
    
    @abstractmethod
    async def recommend_narrative_path(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Recomienda el siguiente camino narrativo basado en preferencias y estado emocional.
        
        Args:
            user_id (int): ID del usuario de Telegram
            
        Returns:
            List[Dict[str, Any]]: Lista de recomendaciones narrativas priorizadas
        """
        pass
    
    @abstractmethod
    async def get_comprehensive_user_status(self, user_id: int) -> NarrativeOperationResult:
        """
        Obtiene el estado completo del usuario en el ecosistema narrativo.
        
        Args:
            user_id (int): ID del usuario de Telegram
            
        Returns:
            NarrativeOperationResult: Estado completo incluyendo narrativa, emociones y métricas
        """
        pass


class IUnifiedNarrativeAnalytics(ABC):
    """
    Interfaz para analíticas unificadas del sistema narrativo.
    Proporciona insights sobre rendimiento, engagement y optimización.
    """
    
    @abstractmethod
    async def generate_narrative_performance_report(self, fragment_ids: Optional[List[str]] = None) -> AnalyticsResult:
        """
        Genera un reporte de rendimiento narrativo detallado.
        
        Args:
            fragment_ids (Optional[List[str]]): IDs específicos de fragmentos o None para todos
            
        Returns:
            AnalyticsResult: Reporte de rendimiento con métricas detalladas
        """
        pass
    
    @abstractmethod
    async def analyze_emotional_patterns(self, user_ids: Optional[List[int]] = None) -> AnalyticsResult:
        """
        Analiza patrones emocionales en interacciones narrativas.
        
        Args:
            user_ids (Optional[List[int]]): IDs de usuarios específicos o None para todos
            
        Returns:
            AnalyticsResult: Análisis de patrones emocionales
        """
        pass
    
    @abstractmethod
    async def identify_content_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """
        Identifica oportunidades de optimización de contenido narrativo.
        
        Returns:
            List[Dict[str, Any]]: Lista de oportunidades de optimización priorizadas
        """
        pass
    
    @abstractmethod
    async def track_user_journey_analytics(self, user_id: int) -> AnalyticsResult:
        """
        Rastrea y analiza el journey completo de un usuario en la narrativa.
        
        Args:
            user_id (int): ID del usuario de Telegram
            
        Returns:
            AnalyticsResult: Analytics del journey del usuario
        """
        pass
    
    @abstractmethod
    async def generate_predictive_insights(self, forecast_days: int = 30) -> AnalyticsResult:
        """
        Genera insights predictivos sobre engagement y comportamiento narrativo.
        
        Args:
            forecast_days (int): Días para el pronóstico
            
        Returns:
            AnalyticsResult: Insights predictivos con recomendaciones
        """
        pass


class IUnifiedNarrativeConfiguration(ABC):
    """
    Interfaz para configuración unificada del sistema narrativo.
    Gestiona parámetros y políticas del ecosistema narrativo.
    """
    
    @abstractmethod
    async def update_narrative_policy(self, policy_name: str, policy_config: Dict[str, Any]) -> ConfigurationResult:
        """
        Actualiza una política del sistema narrativo.
        
        Args:
            policy_name (str): Nombre de la política
            policy_config (Dict[str, Any]): Configuración de la política
            
        Returns:
            ConfigurationResult: Resultado de la actualización de política
        """
        pass
    
    @abstractmethod
    async def get_narrative_configuration(self) -> ConfigurationResult:
        """
        Obtiene la configuración actual del sistema narrativo.
        
        Returns:
            ConfigurationResult: Configuración completa del sistema
        """
        pass
    
    @abstractmethod
    async def validate_narrative_integrity(self) -> ConfigurationResult:
        """
        Valida la integridad del sistema narrativo completo.
        
        Returns:
            ConfigurationResult: Reporte de integridad con errores y advertencias
        """
        pass
    
    @abstractmethod
    async def backup_narrative_state(self, backup_name: str) -> ConfigurationResult:
        """
        Crea un backup del estado narrativo completo.
        
        Args:
            backup_name (str): Nombre del backup
            
        Returns:
            ConfigurationResult: Resultado de la operación de backup
        """
        pass
    
    @abstractmethod
    async def restore_narrative_state(self, backup_id: str) -> ConfigurationResult:
        """
        Restaura el estado narrativo desde un backup.
        
        Args:
            backup_id (str): ID del backup a restaurar
            
        Returns:
            ConfigurationResult: Resultado de la operación de restauración
        """
        pass