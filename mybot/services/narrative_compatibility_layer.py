"""
Narrative Compatibility Layer - Compatibilidad entre sistemas narrativos
Este módulo proporciona una capa de compatibilidad para normalizar el acceso
a los datos y funcionalidades narrativas desde diferentes subsistemas.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .narrative_service import NarrativeService
from database.models import User
from database.narrative_models import UserNarrativeState, StoryFragment, NarrativeFragment

logger = logging.getLogger(__name__)

class NarrativeCompatibilityLayer:
    """
    Capa de compatibilidad para el sistema narrativo que normaliza
    el acceso a datos entre los diferentes subsistemas (legacy y Diana).
    """
    
    def __init__(self, session: AsyncSession):
        """
        Inicializa la capa de compatibilidad con los servicios necesarios.
        
        Args:
            session: Sesión de base de datos para operaciones
        """
        self.session = session
        self.narrative_service = NarrativeService(session)
    
    async def get_user_narrative_data(self, user_id: int) -> Dict[str, Any]:
        """
        Obtiene datos normalizados del progreso narrativo del usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Diccionario con datos narrativos normalizados
        """
        try:
            # Obtener progreso del usuario usando el servicio narrativo
            user_progress = await self.narrative_service.get_user_progress(user_id)
            
            if not user_progress:
                return self._get_default_narrative_data()
            
            # Obtener fragmento actual
            fragment_key = user_progress.current_fragment_key if hasattr(user_progress, 'current_fragment_key') else None
            current_fragment = await self.narrative_service.get_fragment_by_key(fragment_key)
            
            # Calcular métricas y datos normalizados
            return {
                "progress_percentage": await self._calculate_progress_percentage(user_id),
                "completion_percentage": await self._calculate_progress_percentage(user_id),
                "current_fragment": current_fragment.fragment_key if current_fragment else "inicio",
                "fragment_title": current_fragment.title if current_fragment else "Prólogo",
                "hints_unlocked": await self._count_unlocked_hints(user_id),
                "decisions": await self._get_user_decisions(user_id),
                "chapters_completed": await self._count_completed_chapters(user_id),
                "total_chapters": await self._count_total_chapters(),
                "character": "diana",  # Por defecto, se podría determinar según progreso
                "content_access_level": user_progress.content_access_level if user_progress else 1,
                "last_interaction": user_progress.updated_at if user_progress else None
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos narrativos para usuario {user_id}: {e}")
            return self._get_default_narrative_data()
    
    async def _calculate_progress_percentage(self, user_id: int) -> int:
        """
        Calcula el porcentaje de progreso en la narrativa.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Porcentaje de progreso (0-100)
        """
        try:
            # Implementación básica - en un sistema real, se basaría en puntos clave de historia
            total_fragments = await self._count_total_fragments()
            if total_fragments == 0:
                return 0
                
            # Contar fragmentos visitados
            user_progress = await self.narrative_service.get_user_progress(user_id)
            if not user_progress:
                return 0
                
            visited_count = len(user_progress.visited_fragments.split(',')) if user_progress.visited_fragments else 0
            
            # Calcular porcentaje
            return min(int((visited_count / total_fragments) * 100), 100)
            
        except Exception as e:
            logger.error(f"Error calculando porcentaje de progreso para usuario {user_id}: {e}")
            return 0
    
    async def _count_unlocked_hints(self, user_id: int) -> int:
        """
        Cuenta las pistas desbloqueadas por el usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Número de pistas desbloqueadas
        """
        try:
            # En un sistema real, se conectaría con el sistema de pistas
            # Por ahora, devolvemos un valor simulado basado en el progreso
            progress = await self._calculate_progress_percentage(user_id)
            return max(int(progress / 10), 0)  # 1 pista por cada 10% de progreso
            
        except Exception as e:
            logger.error(f"Error contando pistas desbloqueadas para usuario {user_id}: {e}")
            return 0
    
    async def _get_user_decisions(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene las decisiones tomadas por el usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de decisiones con metadata
        """
        try:
            # En un sistema real, se obtendría de una tabla de decisiones
            # Por ahora, devolvemos una lista vacía
            return []
            
        except Exception as e:
            logger.error(f"Error obteniendo decisiones para usuario {user_id}: {e}")
            return []
    
    async def _count_completed_chapters(self, user_id: int) -> int:
        """
        Cuenta los capítulos completados por el usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Número de capítulos completados
        """
        try:
            # Simplificación - basado en progreso general
            progress = await self._calculate_progress_percentage(user_id)
            total_chapters = await self._count_total_chapters()
            
            return int((progress / 100) * total_chapters)
            
        except Exception as e:
            logger.error(f"Error contando capítulos completados para usuario {user_id}: {e}")
            return 0
    
    async def _count_total_chapters(self) -> int:
        """
        Cuenta el número total de capítulos en la narrativa.
        
        Returns:
            Número total de capítulos
        """
        try:
            # En un sistema real, se contarían los capítulos de la narrativa
            # Por ahora, devolvemos un valor fijo
            return 5
            
        except Exception as e:
            logger.error(f"Error contando total de capítulos: {e}")
            return 0
    
    async def _count_total_fragments(self) -> int:
        """
        Cuenta el número total de fragmentos en la narrativa.
        
        Returns:
            Número total de fragmentos
        """
        try:
            result = await self.session.execute(select(StoryFragment).with_only_columns(StoryFragment.id))
            return len(result.scalars().all())
            
        except Exception as e:
            logger.error(f"Error contando total de fragmentos: {e}")
            return 0
    
    def _get_default_narrative_data(self) -> Dict[str, Any]:
        """
        Devuelve datos narrativos por defecto para usuarios sin progreso.
        
        Returns:
            Diccionario con datos narrativos por defecto
        """
        return {
            "progress_percentage": 0,
            "completion_percentage": 0,
            "current_fragment": "inicio",
            "fragment_title": "Prólogo",
            "hints_unlocked": 0,
            "decisions": [],
            "chapters_completed": 0,
            "total_chapters": 5,
            "character": "diana",
            "content_access_level": 1,
            "last_interaction": None
        }

# Instancia global para acceso simplificado
_narrative_compatibility = None

def get_narrative_compatibility(session: AsyncSession) -> NarrativeCompatibilityLayer:
    """
    Obtiene o crea una instancia de la capa de compatibilidad narrativa.
    
    Args:
        session: Sesión de base de datos
        
    Returns:
        Instancia de NarrativeCompatibilityLayer
    """
    global _narrative_compatibility
    if _narrative_compatibility is None or _narrative_compatibility.session != session:
        _narrative_compatibility = NarrativeCompatibilityLayer(session)
    return _narrative_compatibility