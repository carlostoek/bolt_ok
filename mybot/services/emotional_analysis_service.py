"""
EmotionalAnalysisService - Análisis emocional y comportamental de usuarios
Integra seamlessly con CoordinadorCentral sin romper funcionalidad existente.
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc, func

try:
    from .point_service import PointService
    from .narrative_service import NarrativeService
    from ..database.models import User, UserStats, ButtonReaction
except ImportError:
    # Fallback to absolute imports for standalone usage
    from services.point_service import PointService
    from services.narrative_service import NarrativeService
    from database.models import User, UserStats, ButtonReaction

logger = logging.getLogger(__name__)

class EmotionalState:
    """Representa el estado emocional de un usuario."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.vulnerability_level = 0.0  # 0.0 - 1.0
        self.engagement_pattern = "neutral"  # engaged, passive, erratic, vulnerable
        self.emotional_intensity = 0.0  # 0.0 - 1.0
        self.response_timing_pattern = "normal"  # instant, normal, delayed, erratic
        self.behavioral_indicators = []
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "vulnerability_level": self.vulnerability_level,
            "engagement_pattern": self.engagement_pattern,
            "emotional_intensity": self.emotional_intensity,
            "response_timing_pattern": self.response_timing_pattern,
            "behavioral_indicators": self.behavioral_indicators
        }

class EmotionalAnalysisService:
    """
    Servicio de análisis emocional que se integra sin problemas con los flujos existentes.
    Proporciona insights sobre el estado emocional y patrones de comportamiento de usuarios.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        # Usar servicios existentes sin modificarlos
        self.point_service = PointService(session)
        self.narrative_service = NarrativeService(session)
        
        # Cache para análisis recientes (evita recálculos costosos)
        self._analysis_cache = {}
        self._cache_timeout = timedelta(minutes=5)
    
    async def analyze_response_timing(
        self, 
        user_id: int, 
        action_timestamp: datetime,
        context: str = "general"
    ) -> Dict[str, Any]:
        """
        Analiza patrones de tiempo de respuesta del usuario.
        
        Args:
            user_id: ID del usuario
            action_timestamp: Momento de la acción
            context: Contexto de la acción (reaction, decision, message)
            
        Returns:
            Dict con análisis de timing y patrones detectados
        """
        try:
            # Obtener actividad reciente del usuario (últimas 24h)
            cutoff_time = action_timestamp - timedelta(hours=24)
            
            # Consultar reacciones recientes para análisis de patrones
            recent_reactions = await self.session.execute(
                select(ButtonReaction)
                .where(
                    and_(
                        ButtonReaction.user_id == user_id,
                        ButtonReaction.created_at >= cutoff_time
                    )
                )
                .order_by(desc(ButtonReaction.created_at))
                .limit(20)
            )
            reactions = recent_reactions.scalars().all()
            
            # Analizar patrones de timing
            timing_analysis = self._analyze_timing_patterns(reactions, action_timestamp)
            
            # Detectar comportamientos emocionales basados en timing
            emotional_indicators = self._detect_timing_emotional_indicators(timing_analysis)
            
            return {
                "success": True,
                "timing_pattern": timing_analysis["pattern"],
                "response_speed": timing_analysis["avg_response_speed"],
                "consistency_score": timing_analysis["consistency"],
                "emotional_indicators": emotional_indicators,
                "analysis_confidence": timing_analysis["confidence"],
                "context": context
            }
            
        except Exception as e:
            logger.warning(f"Error en análisis de timing para usuario {user_id}: {str(e)}")
            # Graceful degradation - no romper funcionalidad existente
            return {
                "success": False,
                "timing_pattern": "unknown",
                "response_speed": "normal",
                "consistency_score": 0.5,
                "emotional_indicators": [],
                "analysis_confidence": 0.0,
                "context": context,
                "error": str(e)
            }
    
    async def detect_behavioral_patterns(
        self,
        user_id: int,
        action_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detecta patrones de comportamiento basados en el historial de acciones.
        
        Args:
            user_id: ID del usuario
            action_history: Historial reciente de acciones del usuario
            
        Returns:
            Dict con patrones detectados y nivel de confianza
        """
        try:
            # Cache check para evitar recálculos frecuentes
            cache_key = f"behavioral_{user_id}"
            if self._is_cache_valid(cache_key):
                return self._analysis_cache[cache_key]
            
            # Obtener estadísticas del usuario
            user_stats = await self.session.get(UserStats, user_id)
            if not user_stats:
                user_stats = UserStats(user_id=user_id)
            
            # Analizar patrones de engagement
            engagement_pattern = await self._analyze_engagement_pattern(user_id, user_stats)
            
            # Detectar cambios en comportamiento
            behavioral_changes = await self._detect_behavioral_changes(user_id, action_history)
            
            # Calcular puntuación de consistencia
            consistency_score = self._calculate_consistency_score(action_history)
            
            result = {
                "success": True,
                "engagement_pattern": engagement_pattern,
                "behavioral_changes": behavioral_changes,
                "consistency_score": consistency_score,
                "activity_level": self._categorize_activity_level(user_stats),
                "social_engagement": self._assess_social_engagement(user_stats),
                "pattern_confidence": min(0.8, len(action_history) * 0.1)
            }
            
            # Cache resultado
            self._cache_analysis(cache_key, result)
            return result
            
        except Exception as e:
            logger.warning(f"Error en detección de patrones para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "engagement_pattern": "unknown",
                "behavioral_changes": [],
                "consistency_score": 0.5,
                "activity_level": "normal",
                "social_engagement": "moderate",
                "pattern_confidence": 0.0,
                "error": str(e)
            }
    
    async def assess_vulnerability_level(
        self,
        user_id: int,
        response_content: str = "",
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Evalúa el nivel de vulnerabilidad emocional del usuario.
        
        Args:
            user_id: ID del usuario
            response_content: Contenido de la respuesta/interacción
            context: Contexto adicional de la interacción
            
        Returns:
            Dict con nivel de vulnerabilidad y recomendaciones
        """
        try:
            if context is None:
                context = {}
            
            # Análisis básico basado en patrones de interacción
            user = await self.session.get(User, user_id)
            user_stats = await self.session.get(UserStats, user_id)
            
            if not user or not user_stats:
                return self._default_vulnerability_assessment()
            
            # Factores de vulnerabilidad
            vulnerability_factors = []
            vulnerability_score = 0.0
            
            # Factor 1: Frecuencia de actividad reciente
            activity_factor = await self._assess_activity_vulnerability(user_stats)
            vulnerability_score += activity_factor["score"]
            if activity_factor["indicators"]:
                vulnerability_factors.extend(activity_factor["indicators"])
            
            # Factor 2: Patrones de tiempo de respuesta
            timing_factor = await self._assess_timing_vulnerability(user_id)
            vulnerability_score += timing_factor["score"]
            if timing_factor["indicators"]:
                vulnerability_factors.extend(timing_factor["indicators"])
            
            # Factor 3: Consistencia en decisiones narrativas
            narrative_factor = await self._assess_narrative_vulnerability(user_id)
            vulnerability_score += narrative_factor["score"]
            if narrative_factor["indicators"]:
                vulnerability_factors.extend(narrative_factor["indicators"])
            
            # Normalizar puntuación (0.0 - 1.0)
            final_score = min(1.0, max(0.0, vulnerability_score / 3.0))
            
            # Determinar nivel y recomendaciones
            level, recommendations = self._categorize_vulnerability(final_score, vulnerability_factors)
            
            return {
                "success": True,
                "vulnerability_level": final_score,
                "vulnerability_category": level,
                "indicators": vulnerability_factors,
                "recommendations": recommendations,
                "confidence": min(0.9, len(vulnerability_factors) * 0.2)
            }
            
        except Exception as e:
            logger.warning(f"Error en evaluación de vulnerabilidad para usuario {user_id}: {str(e)}")
            return self._default_vulnerability_assessment()
    
    async def track_emotional_evolution(
        self,
        user_id: int,
        timeframe_days: int = 7
    ) -> Dict[str, Any]:
        """
        Rastrea la evolución emocional del usuario a lo largo del tiempo.
        
        Args:
            user_id: ID del usuario
            timeframe_days: Días a analizar hacia atrás
            
        Returns:
            Dict con evolución emocional y tendencias
        """
        try:
            # Obtener datos históricos del usuario
            cutoff_date = datetime.utcnow() - timedelta(days=timeframe_days)
            
            # Consultar actividad histórica
            historical_reactions = await self.session.execute(
                select(ButtonReaction)
                .where(
                    and_(
                        ButtonReaction.user_id == user_id,
                        ButtonReaction.created_at >= cutoff_date
                    )
                )
                .order_by(ButtonReaction.created_at)
            )
            reactions = historical_reactions.scalars().all()
            
            # Analizar evolución por períodos
            evolution_data = self._analyze_temporal_evolution(reactions, timeframe_days)
            
            # Detectar tendencias emocionales
            trends = self._detect_emotional_trends(evolution_data)
            
            # Generar insights
            insights = self._generate_emotional_insights(trends, evolution_data)
            
            return {
                "success": True,
                "timeframe_days": timeframe_days,
                "evolution_data": evolution_data,
                "trends": trends,
                "insights": insights,
                "data_points": len(reactions),
                "analysis_reliability": min(0.9, len(reactions) * 0.05)
            }
            
        except Exception as e:
            logger.warning(f"Error en seguimiento emocional para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "timeframe_days": timeframe_days,
                "evolution_data": {},
                "trends": [],
                "insights": [],
                "data_points": 0,
                "analysis_reliability": 0.0,
                "error": str(e)
            }
    
    async def generate_contextual_response_enhancement(
        self,
        user_id: int,
        base_response: Dict[str, Any],
        emotional_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Genera mejoras contextuales para las respuestas basadas en análisis emocional.
        NO modifica la respuesta base, solo sugiere mejoras.
        
        Args:
            user_id: ID del usuario
            base_response: Respuesta base del sistema
            emotional_context: Contexto emocional adicional
            
        Returns:
            Dict con sugerencias de mejoras contextuales
        """
        try:
            if emotional_context is None:
                # Realizar análisis emocional rápido
                emotional_context = await self._quick_emotional_assessment(user_id)
            
            # Generar sugerencias de tono
            tone_suggestions = self._suggest_response_tone(emotional_context)
            
            # Sugerir ajustes de contenido
            content_suggestions = self._suggest_content_adjustments(
                base_response, 
                emotional_context
            )
            
            # Recomendar timing de respuesta
            timing_suggestions = self._suggest_response_timing(emotional_context)
            
            return {
                "success": True,
                "tone_suggestions": tone_suggestions,
                "content_suggestions": content_suggestions,
                "timing_suggestions": timing_suggestions,
                "emotional_context": emotional_context,
                "enhancement_confidence": emotional_context.get("confidence", 0.5)
            }
            
        except Exception as e:
            logger.warning(f"Error generando mejoras contextuales para usuario {user_id}: {str(e)}")
            return {
                "success": False,
                "tone_suggestions": {},
                "content_suggestions": {},
                "timing_suggestions": {},
                "emotional_context": {},
                "enhancement_confidence": 0.0,
                "error": str(e)
            }
    
    # Métodos auxiliares privados
    
    def _analyze_timing_patterns(
        self, 
        reactions: List[ButtonReaction], 
        current_timestamp: datetime
    ) -> Dict[str, Any]:
        """Analiza patrones en el timing de las reacciones."""
        if not reactions:
            return {
                "pattern": "insufficient_data",
                "avg_response_speed": "unknown",
                "consistency": 0.0,
                "confidence": 0.0
            }
        
        # Calcular intervalos entre reacciones
        intervals = []
        for i in range(1, len(reactions)):
            interval = (reactions[i-1].created_at - reactions[i].created_at).total_seconds()
            intervals.append(abs(interval))
        
        if not intervals:
            return {
                "pattern": "single_action",
                "avg_response_speed": "normal",
                "consistency": 1.0,
                "confidence": 0.3
            }
        
        # Análisis estadístico básico
        avg_interval = sum(intervals) / len(intervals)
        variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
        consistency = max(0.0, 1.0 - (variance / max(avg_interval, 1)))
        
        # Categorizar patrón
        if avg_interval < 30:  # Menos de 30 segundos entre acciones
            pattern = "rapid_fire"
        elif avg_interval > 3600:  # Más de una hora
            pattern = "spaced"
        else:
            pattern = "normal"
        
        return {
            "pattern": pattern,
            "avg_response_speed": self._categorize_speed(avg_interval),
            "consistency": min(1.0, consistency),
            "confidence": min(0.9, len(intervals) * 0.1)
        }
    
    def _detect_timing_emotional_indicators(
        self, 
        timing_analysis: Dict[str, Any]
    ) -> List[str]:
        """Detecta indicadores emocionales basados en timing."""
        indicators = []
        
        pattern = timing_analysis["pattern"]
        consistency = timing_analysis["consistency"]
        
        if pattern == "rapid_fire" and consistency > 0.7:
            indicators.append("high_engagement")
        elif pattern == "rapid_fire" and consistency < 0.3:
            indicators.append("impulsive_behavior")
        elif pattern == "spaced" and consistency > 0.8:
            indicators.append("deliberate_engagement")
        elif consistency < 0.2:
            indicators.append("erratic_behavior")
        
        return indicators
    
    def _categorize_speed(self, avg_interval: float) -> str:
        """Categoriza la velocidad de respuesta."""
        if avg_interval < 10:
            return "very_fast"
        elif avg_interval < 60:
            return "fast"
        elif avg_interval < 300:
            return "normal"
        elif avg_interval < 1800:
            return "slow"
        else:
            return "very_slow"
    
    async def _analyze_engagement_pattern(
        self, 
        user_id: int, 
        user_stats: UserStats
    ) -> str:
        """Analiza el patrón de engagement del usuario."""
        # Análisis basado en estadísticas existentes
        if user_stats.checkin_streak > 14:
            return "highly_engaged"
        elif user_stats.checkin_streak > 7:
            return "regularly_engaged"
        elif user_stats.messages_sent > 50:
            return "socially_active"
        elif user_stats.messages_sent < 5:
            return "passive"
        else:
            return "moderately_engaged"
    
    async def _detect_behavioral_changes(
        self, 
        user_id: int, 
        action_history: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detecta cambios significativos en el comportamiento."""
        changes = []
        
        # Análisis simple de cambios en frecuencia
        if len(action_history) >= 6:
            recent_activity = len([a for a in action_history[:3] if a])
            older_activity = len([a for a in action_history[3:6] if a])
            
            if recent_activity > older_activity * 2:
                changes.append({
                    "type": "increased_activity",
                    "confidence": 0.7,
                    "description": "Notable increase in activity"
                })
            elif recent_activity * 2 < older_activity:
                changes.append({
                    "type": "decreased_activity", 
                    "confidence": 0.7,
                    "description": "Notable decrease in activity"
                })
        
        return changes
    
    def _calculate_consistency_score(
        self, 
        action_history: List[Dict[str, Any]]
    ) -> float:
        """Calcula puntuación de consistencia basada en historial."""
        if len(action_history) < 2:
            return 0.5
        
        # Análisis simple de consistencia temporal
        timestamps = [
            action.get("timestamp", datetime.utcnow()) 
            for action in action_history 
            if action and action.get("timestamp")
        ]
        
        if len(timestamps) < 2:
            return 0.5
        
        # Calcular varianza en intervalos
        intervals = []
        for i in range(1, len(timestamps)):
            interval = (timestamps[i-1] - timestamps[i]).total_seconds()
            intervals.append(abs(interval))
        
        if not intervals:
            return 0.5
        
        avg_interval = sum(intervals) / len(intervals)
        variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
        
        # Normalizar consistencia (menor varianza = mayor consistencia)
        consistency = max(0.0, 1.0 - (variance / max(avg_interval * avg_interval, 1)))
        return min(1.0, consistency)
    
    def _categorize_activity_level(self, user_stats: UserStats) -> str:
        """Categoriza el nivel de actividad del usuario."""
        if user_stats.messages_sent > 100:
            return "very_high"
        elif user_stats.messages_sent > 50:
            return "high"
        elif user_stats.messages_sent > 20:
            return "moderate"
        elif user_stats.messages_sent > 5:
            return "low"
        else:
            return "very_low"
    
    def _assess_social_engagement(self, user_stats: UserStats) -> str:
        """Evalúa el nivel de engagement social."""
        # Basado en mensaje y racha de check-in
        social_score = user_stats.messages_sent * 0.1 + user_stats.checkin_streak * 0.5
        
        if social_score > 20:
            return "highly_social"
        elif social_score > 10:
            return "moderately_social"
        elif social_score > 5:
            return "somewhat_social"
        else:
            return "low_social"
    
    async def _assess_activity_vulnerability(
        self, 
        user_stats: UserStats
    ) -> Dict[str, Any]:
        """Evalúa vulnerabilidad basada en patrones de actividad."""
        indicators = []
        score = 0.0
        
        # Check actividad reciente vs. histórica
        now = datetime.utcnow()
        if user_stats.last_activity_at:
            hours_since_activity = (now - user_stats.last_activity_at).total_seconds() / 3600
            
            if hours_since_activity > 72:  # Más de 3 días sin actividad
                indicators.append("extended_absence")
                score += 0.3
            elif hours_since_activity < 1:  # Muy activo recientemente
                if user_stats.messages_sent > 20:  # Y alta actividad general
                    indicators.append("potential_hyperfocus")
                    score += 0.2
        
        # Racha de check-in como indicador de consistencia/obsesión
        if user_stats.checkin_streak > 30:
            indicators.append("high_routine_dependence")
            score += 0.1
        
        return {"score": score, "indicators": indicators}
    
    async def _assess_timing_vulnerability(self, user_id: int) -> Dict[str, Any]:
        """Evalúa vulnerabilidad basada en patrones temporales."""
        indicators = []
        score = 0.0
        
        # Obtener reacciones recientes para análisis temporal
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        recent_reactions = await self.session.execute(
            select(ButtonReaction)
            .where(
                and_(
                    ButtonReaction.user_id == user_id,
                    ButtonReaction.created_at >= cutoff_time
                )
            )
            .order_by(desc(ButtonReaction.created_at))
            .limit(10)
        )
        reactions = recent_reactions.scalars().all()
        
        if len(reactions) > 8:  # Muchas reacciones en 24h
            indicators.append("high_frequency_interaction")
            score += 0.2
        
        # Análisis de patrones de tiempo
        if len(reactions) >= 3:
            timestamps = [r.created_at for r in reactions]
            intervals = []
            for i in range(1, len(timestamps)):
                interval = (timestamps[i-1] - timestamps[i]).total_seconds()
                intervals.append(interval)
            
            if intervals and all(interval < 300 for interval in intervals):  # Todas las reacciones en < 5 min
                indicators.append("rapid_consecutive_reactions")
                score += 0.25
        
        return {"score": score, "indicators": indicators}
    
    async def _assess_narrative_vulnerability(self, user_id: int) -> Dict[str, Any]:
        """Evalúa vulnerabilidad basada en interacciones narrativas."""
        indicators = []
        score = 0.0
        
        try:
            # Obtener fragmento actual del usuario
            current_fragment = await self.narrative_service.get_user_current_fragment(user_id)
            
            if current_fragment and hasattr(current_fragment, 'key'):
                # Analizar progreso narrativo
                if current_fragment.key.startswith('level4_') or current_fragment.key.startswith('level5_'):
                    indicators.append("advanced_narrative_engagement")
                    score += 0.1  # Engagement alto puede indicar vulnerabilidad emocional
                
                if 'secret' in current_fragment.key.lower() or 'intimate' in current_fragment.key.lower():
                    indicators.append("intimate_content_seeking")
                    score += 0.15
        
        except Exception as e:
            logger.debug(f"Error en análisis narrativo para usuario {user_id}: {str(e)}")
            # Graceful degradation - no afectar funcionalidad
        
        return {"score": score, "indicators": indicators}
    
    def _categorize_vulnerability(
        self, 
        score: float, 
        factors: List[str]
    ) -> Tuple[str, List[str]]:
        """Categoriza el nivel de vulnerabilidad y genera recomendaciones."""
        if score > 0.7:
            level = "high"
            recommendations = [
                "consider_gentle_interaction_approach",
                "monitor_engagement_frequency", 
                "provide_emotional_support_options"
            ]
        elif score > 0.4:
            level = "moderate"
            recommendations = [
                "balanced_interaction_approach",
                "encourage_healthy_engagement_patterns"
            ]
        else:
            level = "low"
            recommendations = [
                "standard_interaction_approach",
                "maintain_current_engagement_level"
            ]
        
        return level, recommendations
    
    def _default_vulnerability_assessment(self) -> Dict[str, Any]:
        """Assessment por defecto cuando hay errores."""
        return {
            "success": True,
            "vulnerability_level": 0.3,  # Nivel medio-bajo por defecto
            "vulnerability_category": "moderate",
            "indicators": [],
            "recommendations": ["standard_interaction_approach"],
            "confidence": 0.1
        }
    
    def _analyze_temporal_evolution(
        self, 
        reactions: List[ButtonReaction], 
        timeframe_days: int
    ) -> Dict[str, Any]:
        """Analiza la evolución temporal de las interacciones."""
        if not reactions:
            return {}
        
        # Dividir timeframe en períodos
        periods = min(7, timeframe_days)  # Máximo 7 períodos
        period_duration = timeframe_days / periods
        
        now = datetime.utcnow()
        evolution = {}
        
        for period in range(periods):
            period_start = now - timedelta(days=(period + 1) * period_duration)
            period_end = now - timedelta(days=period * period_duration)
            
            period_reactions = [
                r for r in reactions 
                if period_start <= r.created_at < period_end
            ]
            
            evolution[f"period_{periods - period}"] = {
                "reaction_count": len(period_reactions),
                "start_date": period_start.isoformat(),
                "end_date": period_end.isoformat()
            }
        
        return evolution
    
    def _detect_emotional_trends(
        self, 
        evolution_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detecta tendencias emocionales en los datos de evolución."""
        trends = []
        
        if not evolution_data:
            return trends
        
        # Extraer conteos de reacciones por período
        counts = [
            data["reaction_count"] 
            for data in evolution_data.values()
        ]
        
        if len(counts) >= 3:
            # Tendencia creciente
            if counts[-1] > counts[-2] > counts[-3]:
                trends.append({
                    "type": "increasing_engagement",
                    "confidence": 0.8,
                    "description": "User engagement is increasing over time"
                })
            # Tendencia decreciente
            elif counts[-1] < counts[-2] < counts[-3]:
                trends.append({
                    "type": "decreasing_engagement",
                    "confidence": 0.8,
                    "description": "User engagement is decreasing over time"
                })
            # Volatilidad
            elif max(counts) - min(counts) > 5:
                trends.append({
                    "type": "volatile_engagement",
                    "confidence": 0.7,
                    "description": "User engagement shows high volatility"
                })
        
        return trends
    
    def _generate_emotional_insights(
        self, 
        trends: List[Dict[str, Any]], 
        evolution_data: Dict[str, Any]
    ) -> List[str]:
        """Genera insights basados en tendencias y evolución."""
        insights = []
        
        for trend in trends:
            if trend["type"] == "increasing_engagement":
                insights.append("Usuario muestra creciente interés y engagement con el contenido")
            elif trend["type"] == "decreasing_engagement":
                insights.append("Usuario podría necesitar contenido más atractivo o variado")
            elif trend["type"] == "volatile_engagement":
                insights.append("Patrones de engagement variables sugieren necesidades emocionales cambiantes")
        
        # Insights basados en datos generales
        total_reactions = sum(
            data["reaction_count"] 
            for data in evolution_data.values()
        )
        
        if total_reactions > 20:
            insights.append("Alto nivel de engagement general indica fuerte conexión emocional")
        elif total_reactions < 5:
            insights.append("Bajo engagement puede indicar necesidad de contenido más personalizado")
        
        return insights
    
    async def _quick_emotional_assessment(self, user_id: int) -> Dict[str, Any]:
        """Evaluación emocional rápida para mejoras contextuales."""
        try:
            user_stats = await self.session.get(UserStats, user_id)
            if not user_stats:
                return {"confidence": 0.1, "state": "neutral"}
            
            # Assessment básico basado en actividad reciente
            now = datetime.utcnow()
            hours_since_activity = 24  # Default
            
            if user_stats.last_activity_at:
                hours_since_activity = (now - user_stats.last_activity_at).total_seconds() / 3600
            
            if hours_since_activity < 1:
                state = "highly_engaged"
            elif hours_since_activity < 6:
                state = "engaged"
            elif hours_since_activity < 24:
                state = "moderately_engaged"
            else:
                state = "disengaged"
            
            return {
                "confidence": 0.6,
                "state": state,
                "hours_since_activity": hours_since_activity,
                "checkin_streak": user_stats.checkin_streak,
                "message_count": user_stats.messages_sent
            }
            
        except Exception:
            return {"confidence": 0.1, "state": "neutral"}
    
    def _suggest_response_tone(self, emotional_context: Dict[str, Any]) -> Dict[str, Any]:
        """Sugiere tono de respuesta basado en contexto emocional."""
        state = emotional_context.get("state", "neutral")
        
        tone_map = {
            "highly_engaged": {
                "primary": "enthusiastic",
                "secondary": "playful",
                "avoid": ["distant", "formal"]
            },
            "engaged": {
                "primary": "warm",
                "secondary": "encouraging",
                "avoid": ["overwhelming"]
            },
            "moderately_engaged": {
                "primary": "gentle",
                "secondary": "inviting",
                "avoid": ["pushy", "demanding"]
            },
            "disengaged": {
                "primary": "welcoming",
                "secondary": "patient",
                "avoid": ["aggressive", "urgent"]
            },
            "neutral": {
                "primary": "balanced",
                "secondary": "friendly",
                "avoid": ["extreme"]
            }
        }
        
        return tone_map.get(state, tone_map["neutral"])
    
    def _suggest_content_adjustments(
        self, 
        base_response: Dict[str, Any], 
        emotional_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sugiere ajustes de contenido basados en contexto emocional."""
        suggestions = {}
        
        state = emotional_context.get("state", "neutral")
        confidence = emotional_context.get("confidence", 0.5)
        
        if confidence > 0.7:
            if state == "highly_engaged":
                suggestions["add_elements"] = ["enthusiasm_markers", "engagement_rewards"]
            elif state == "disengaged":
                suggestions["add_elements"] = ["gentle_re_engagement", "low_pressure_options"]
                suggestions["modify_tone"] = "more_welcoming"
            elif state in ["engaged", "moderately_engaged"]:
                suggestions["maintain"] = "current_approach"
        
        return suggestions
    
    def _suggest_response_timing(self, emotional_context: Dict[str, Any]) -> Dict[str, Any]:
        """Sugiere timing de respuesta basado en contexto emocional."""
        state = emotional_context.get("state", "neutral")
        hours_since_activity = emotional_context.get("hours_since_activity", 24)
        
        if state == "highly_engaged" and hours_since_activity < 1:
            return {
                "suggested_delay": "minimal",
                "reasoning": "User is highly active, respond quickly"
            }
        elif state == "disengaged":
            return {
                "suggested_delay": "moderate",
                "reasoning": "Allow user space, don't overwhelm"
            }
        else:
            return {
                "suggested_delay": "standard",
                "reasoning": "Normal response timing appropriate"
            }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica si el cache es válido."""
        if cache_key not in self._analysis_cache:
            return False
        
        cached_item = self._analysis_cache[cache_key]
        if "timestamp" not in cached_item:
            return False
        
        cache_age = datetime.utcnow() - cached_item["timestamp"]
        return cache_age < self._cache_timeout
    
    def _cache_analysis(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Cachea resultado de análisis."""
        self._analysis_cache[cache_key] = {
            **result,
            "timestamp": datetime.utcnow()
        }
        
        # Limpieza básica de cache (mantener solo 50 items)
        if len(self._analysis_cache) > 50:
            oldest_key = min(
                self._analysis_cache.keys(),
                key=lambda k: self._analysis_cache[k].get("timestamp", datetime.min)
            )
            del self._analysis_cache[oldest_key]