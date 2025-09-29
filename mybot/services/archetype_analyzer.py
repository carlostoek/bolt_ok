# services/archetype_analyzer.py
"""
Archetype Analysis Service for Diana's Sistema Narrativo Ramificado
Implements psychological archetype classification for personalized narrative experiences.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json
import logging

try:
    from .response_time_analyzer import ResponseTimeAnalyzer
    from ..database.emotional_models import ArchetypeClassification
except ImportError:
    # Fallback to absolute imports for standalone usage
    from services.response_time_analyzer import ResponseTimeAnalyzer
    from database.emotional_models import ArchetypeClassification

logger = logging.getLogger(__name__)


@dataclass
class ArchetypeScores:
    """
    Primary archetype scoring structure for psychological analysis.

    Contains the 8 primary variables used for user archetype classification:
    - intellectual: Analytical thinking and knowledge-seeking patterns
    - emotional: Emotional depth and expression patterns
    - exploratory: Curiosity and discovery-oriented behavior
    - vulnerable: Openness to emotional vulnerability and sharing
    - philosophical: Deep thinking and meaning-seeking tendencies
    - direct: Straightforward communication and decision-making style
    - patient: Tolerance for longer interactions and deeper exploration
    - reciprocal: Tendency toward mutual exchange and relationship building

    All scores default to 0.0 and are designed to be populated during
    Level 1 Fragment 1 (L1F1) interactions for archetype detection.
    """
    intellectual: float = 0.0
    emotional: float = 0.0
    exploratory: float = 0.0
    vulnerable: float = 0.0
    philosophical: float = 0.0
    direct: float = 0.0
    patient: float = 0.0
    reciprocal: float = 0.0


@dataclass
class SubArchetypeScores:
    """
    Secondary archetype scoring structure for granular psychological profiling.

    Contains 10 sub-archetype variables that provide deeper classification
    beyond the primary 8 archetypes. These sub-archetypes enable more
    nuanced narrative personalization and user journey optimization:

    - romantic_intellectual: Combines emotional depth with analytical thinking,
      seeks meaningful connections through intellectual discourse
    - skeptical_thinker: Questions assumptions, requires evidence-based approaches,
      values critical analysis over emotional appeals
    - hedonist_philosopher: Balances pleasure-seeking with deep contemplation,
      enjoys existential discussions while pursuing immediate gratification
    - pure_theorist: Focuses on abstract concepts and theoretical frameworks,
      less concerned with practical applications
    - empathetic_emotional: High emotional intelligence, deeply attuned to others'
      feelings, seeks harmony and understanding
    - passionate_emotional: Intense emotional expressions, driven by strong feelings,
      values authentic emotional connections
    - wounded_healer: Has experienced significant emotional challenges,
      uses personal growth to help others, values healing narratives
    - adventure_seeker: Craves new experiences and challenges,
      motivated by exploration and discovery
    - collector_explorer: Systematically gathers knowledge or experiences,
      combines methodical approach with curiosity
    - freedom_lover: Values independence and autonomy above all,
      resists constraints and seeks liberation

    All scores default to 0.0 and are calculated based on primary archetype
    combinations and behavioral patterns observed during user interactions.
    """
    romantic_intellectual: float = 0.0
    skeptical_thinker: float = 0.0
    hedonist_philosopher: float = 0.0
    pure_theorist: float = 0.0
    empathetic_emotional: float = 0.0
    passionate_emotional: float = 0.0
    wounded_healer: float = 0.0
    adventure_seeker: float = 0.0
    collector_explorer: float = 0.0
    freedom_lover: float = 0.0


class ArchetypeAnalyzer:
    """
    Analizador de arquetipos psicológicos para el Sistema Narrativo Ramificado Diana.

    Esta clase es el núcleo del sistema de análisis psicológico que procesa las interacciones
    de Nivel 1 Fragmento 1 (L1F1) para clasificar usuarios en arquetipos específicos.
    Utiliza análisis multidimensional que combina:

    - Análisis de elecciones narrativas y sus pesos psicológicos
    - Análisis de patrones temporales de respuesta (ResponseTimeAnalyzer)
    - Detección de marcadores emocionales y comportamentales
    - Clasificación en 8 arquetipos primarios y 10 sub-arquetipos

    El análisis permite la personalización dinámica de rutas narrativas, optimizando
    el engagement emocional y maximizando las probabilidades de conversión VIP.

    La clasificación se basa en frameworks psicológicos validados y está calibrada
    específicamente para la detección de vulnerabilidad emocional y patrones de
    comportamiento que indican receptividad a experiencias narrativas premium.

    Arquetipos Primarios:
    - Intellectual: Orientación analítica y búsqueda de conocimiento
    - Emotional: Profundidad emocional y expresión afectiva
    - Exploratory: Curiosidad y comportamiento de descubrimiento
    - Vulnerable: Apertura a vulnerabilidad emocional y compartir
    - Philosophical: Pensamiento profundo y búsqueda de significado
    - Direct: Comunicación directa y toma de decisiones
    - Patient: Tolerancia a interacciones largas y exploración profunda
    - Reciprocal: Tendencia hacia intercambio mutuo y construcción de relaciones

    Sub-arquetipos para personalización granular:
    - Romantic Intellectual, Skeptical Thinker, Hedonist Philosopher
    - Pure Theorist, Empathetic Emotional, Passionate Emotional
    - Wounded Healer, Adventure Seeker, Collector Explorer, Freedom Lover
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el analizador de arquetipos con acceso a base de datos.

        Args:
            session: Sesión de base de datos SQLAlchemy asíncrona para
                    acceso a datos de usuario, interacciones y análisis previos
        """
        self.session = session
        try:
            self.response_time_analyzer = ResponseTimeAnalyzer(session)
            logger.info("ArchetypeAnalyzer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ResponseTimeAnalyzer: {e}")
            # Create a fallback response time analyzer
            self.response_time_analyzer = None

    async def analyze_l1_choices(
        self,
        user_id: int,
        choices: List[Dict[str, Any]],
        timings: List[float]
    ) -> Dict[str, Any]:
        """
        Analiza las elecciones de Nivel 1 para clasificación de arquetipo psicológico.

        Este es el punto de entrada principal para el análisis de arquetipos. Procesa
        las elecciones narrativas del usuario durante L1F1, sus tiempos de respuesta,
        y calcula puntuaciones para arquetipos primarios y sub-arquetipos.

        Args:
            user_id: ID único del usuario en la base de datos
            choices: Lista de diccionarios con elecciones del usuario. Cada elección
                    debe contener claves 'archetype_weights' y 'sub_archetype_weights'
                    con los pesos psicológicos asociados a esa opción narrativa
            timings: Lista de tiempos de respuesta en segundos correspondientes
                    a cada elección (orden cronológico)

        Returns:
            Diccionario con análisis completo del arquetipo:
            - primary_scores: ArchetypeScores con puntuaciones de arquetipos primarios
            - sub_scores: SubArchetypeScores con puntuaciones de sub-arquetipos
            - timing_analysis: Análisis temporal del ResponseTimeAnalyzer
            - dominant_archetype: Arquetipo primario con mayor puntuación
            - confidence_score: Nivel de confianza en la clasificación (0.0-1.0)
            - behavioral_indicators: Lista de indicadores comportamentales detectados
        """
        try:
            logger.info(f"Starting archetype analysis for user {user_id} with {len(choices)} choices")

            # Validate input parameters
            if not isinstance(user_id, int) or user_id <= 0:
                raise ValueError(f"Invalid user_id: {user_id}")

            if not isinstance(choices, list):
                raise ValueError(f"Choices must be a list, got {type(choices)}")

            if not isinstance(timings, list):
                raise ValueError(f"Timings must be a list, got {type(timings)}")

            # Inicializar estructuras de puntuación
            archetype_scores = ArchetypeScores()
            sub_archetype_scores = SubArchetypeScores()

            # Procesar cada elección y su timing correspondiente
            for i, choice in enumerate(choices):
                try:
                    # Aplicar pesos de la elección
                    await self._process_choice_weights(choice, archetype_scores, sub_archetype_scores)
                    logger.debug(f"Processed choice {i} for user {user_id}")
                except Exception as e:
                    logger.warning(f"Error processing choice {i} for user {user_id}: {e}")
                    # Continue with next choice instead of failing completely
                    continue

                # Aplicar modificadores de timing si disponible
                if i < len(timings):
                    try:
                        await self._apply_timing_modifiers(timings[i], archetype_scores)
                    except Exception as e:
                        logger.warning(f"Error applying timing modifiers for choice {i}, user {user_id}: {e}")
                        # Continue without timing modifiers for this choice

            # Aplicar timing modifiers para sub-arquetipos basado en tiempos promedio
            if timings:
                try:
                    avg_timing = sum(timings) / len(timings)
                    # Aplicar modificadores de sub-arquetipos según timing promedio
                    if avg_timing < 10.0:
                        sub_archetype_scores.passionate_emotional += 0.3
                    elif avg_timing > 30.0:
                        sub_archetype_scores.skeptical_thinker += 0.4
                except (ZeroDivisionError, TypeError) as e:
                    logger.warning(f"Error calculating average timing for user {user_id}: {e}")

            # Calcular arquetipo primario
            try:
                primary_archetype = await self._calculate_primary_archetype(archetype_scores)
            except Exception as e:
                logger.error(f"Error calculating primary archetype for user {user_id}: {e}")
                primary_archetype = 'intellectual'  # Safe fallback

            # Determinar sub-arquetipo
            try:
                sub_archetype = await self._determine_sub_archetype(primary_archetype, sub_archetype_scores)
            except Exception as e:
                logger.warning(f"Error determining sub-archetype for user {user_id}: {e}")
                sub_archetype = 'undefined'  # Safe fallback

            # Calcular confianza
            try:
                confidence_score = await self._calculate_confidence(archetype_scores, choices, primary_archetype)
            except Exception as e:
                logger.warning(f"Error calculating confidence for user {user_id}: {e}")
                confidence_score = 0.3  # Low confidence fallback

            # Integrar análisis temporal del ResponseTimeAnalyzer
            timing_analysis = {}
            if self.response_time_analyzer:
                try:
                    timing_analysis = await self.response_time_analyzer.analyze_cognitive_style(user_id, timings)
                except Exception as e:
                    logger.warning(f"Error in timing analysis for user {user_id}: {e}")
                    # Provide fallback timing analysis
                    timing_analysis = {
                        'cognitive_style': 'balanced',
                        'consistency_score': 0.5,
                        'temporal_pattern': 'stable'
                    }
            else:
                logger.warning(f"ResponseTimeAnalyzer not available for user {user_id}, using fallback")
                timing_analysis = {
                    'cognitive_style': 'balanced',
                    'consistency_score': 0.5,
                    'temporal_pattern': 'stable'
                }

            # Preparar indicadores comportamentales
            behavioral_indicators = []
            try:
                if confidence_score >= 0.8:
                    behavioral_indicators.append("high_confidence_classification")
                if confidence_score >= 0.7:
                    behavioral_indicators.append("valid_archetype_pattern")
                if len(choices) >= 3:
                    behavioral_indicators.append("sufficient_data_points")
                if timings:
                    if max(timings) > 30.0:
                        behavioral_indicators.append("reflective_thinking_pattern")
                    if min(timings) < 10.0:
                        behavioral_indicators.append("intuitive_response_pattern")
            except Exception as e:
                logger.warning(f"Error preparing behavioral indicators for user {user_id}: {e}")

            # Calculate average response time safely
            avg_response_time = 0.0
            try:
                avg_response_time = sum(timings) / len(timings) if timings else 0.0
            except (ZeroDivisionError, TypeError) as e:
                logger.warning(f"Error calculating average response time for user {user_id}: {e}")

            logger.info(f"Successfully completed archetype analysis for user {user_id}: {primary_archetype} (confidence: {confidence_score:.2f})")

            # Retornar análisis completo
            return {
                'primary_scores': archetype_scores,
                'sub_scores': sub_archetype_scores,
                'timing_analysis': timing_analysis,
                'dominant_archetype': primary_archetype,
                'sub_archetype': sub_archetype,
                'confidence_score': confidence_score,
                'behavioral_indicators': behavioral_indicators,
                'analysis_metadata': {
                    'total_choices': len(choices),
                    'total_timings': len(timings),
                    'avg_response_time': avg_response_time,
                    'classification_timestamp': datetime.utcnow()
                }
            }

        except Exception as e:
            logger.error(f"Critical error in archetype analysis for user {user_id}: {e}")
            # Return safe fallback result
            return self._get_fallback_analysis_result(user_id, choices, timings)

    async def _process_choice_weights(
        self,
        choice: Dict[str, Any],
        archetype_scores: ArchetypeScores,
        sub_archetype_scores: SubArchetypeScores
    ) -> None:
        """
        Procesa los pesos de arquetipo de una elección individual y actualiza las puntuaciones.

        Extrae los pesos psicológicos de una elección narrativa específica y los aplica
        a las estructuras de puntuación usando setattr para actualización dinámica.
        Maneja graciosamente casos donde los pesos pueden estar ausentes.

        Args:
            choice: Diccionario con la elección del usuario, debe contener:
                   - 'archetype_weights': Dict con pesos para arquetipos primarios
                   - 'sub_archetype_weights': Dict con pesos para sub-arquetipos
            archetype_scores: Instancia de ArchetypeScores a actualizar
            sub_archetype_scores: Instancia de SubArchetypeScores a actualizar
        """
        try:
            # Validate choice structure
            if not isinstance(choice, dict):
                logger.warning(f"Invalid choice type: {type(choice)}, expected dict")
                return

            # Procesar pesos de arquetipos primarios
            archetype_weights = choice.get('archetype_weights', {})
            if not isinstance(archetype_weights, dict):
                logger.warning(f"Invalid archetype_weights type: {type(archetype_weights)}, expected dict")
                archetype_weights = {}

            for archetype_name, weight in archetype_weights.items():
                try:
                    # Validate weight is numeric
                    if not isinstance(weight, (int, float)):
                        logger.warning(f"Invalid weight type for {archetype_name}: {type(weight)}, expected numeric")
                        continue

                    # Verificar que el arquetipo existe en la estructura de datos
                    if hasattr(archetype_scores, archetype_name):
                        # Obtener valor actual y agregar peso
                        current_value = getattr(archetype_scores, archetype_name)
                        new_value = current_value + weight
                        setattr(archetype_scores, archetype_name, new_value)
                    else:
                        logger.warning(f"Unknown archetype: {archetype_name}")
                except Exception as e:
                    logger.warning(f"Error processing archetype weight {archetype_name}: {e}")
                    continue

            # Procesar pesos de sub-arquetipos
            sub_archetype_weights = choice.get('sub_archetype_weights', {})
            if not isinstance(sub_archetype_weights, dict):
                logger.warning(f"Invalid sub_archetype_weights type: {type(sub_archetype_weights)}, expected dict")
                sub_archetype_weights = {}

            for sub_archetype_name, weight in sub_archetype_weights.items():
                try:
                    # Validate weight is numeric
                    if not isinstance(weight, (int, float)):
                        logger.warning(f"Invalid weight type for {sub_archetype_name}: {type(weight)}, expected numeric")
                        continue

                    # Verificar que el sub-arquetipo existe en la estructura de datos
                    if hasattr(sub_archetype_scores, sub_archetype_name):
                        # Obtener valor actual y agregar peso
                        current_value = getattr(sub_archetype_scores, sub_archetype_name)
                        new_value = current_value + weight
                        setattr(sub_archetype_scores, sub_archetype_name, new_value)
                    else:
                        logger.warning(f"Unknown sub-archetype: {sub_archetype_name}")
                except Exception as e:
                    logger.warning(f"Error processing sub-archetype weight {sub_archetype_name}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Critical error in _process_choice_weights: {e}")
            # Don't re-raise, just log and continue with defaults

    async def _apply_timing_modifiers(
        self,
        timing: float,
        archetype_scores: ArchetypeScores
    ) -> None:
        """
        Aplica modificadores basados en tiempo de respuesta para detección de estilo cognitivo.

        Analiza el tiempo de respuesta para modificar puntuaciones de arquetipos según
        patrones cognitivos identificados. Los tiempos rápidos indican procesamiento
        emocional/intuitivo, mientras que tiempos largos sugieren análisis reflexivo.

        Reglas de timing según especificación:
        - <10s: Incrementa direct (+0.5) y passionate_emotional (+0.3)
        - 10-30s: Incrementa philosophical (+0.4) y intellectual (+0.3)
        - >30s: Incrementa philosophical (+0.6), skeptical_thinker (+0.4), patient (+0.5)

        Args:
            timing: Tiempo de respuesta en segundos para la elección
            archetype_scores: Instancia de ArchetypeScores a modificar
        """
        try:
            # Validate timing value
            if not isinstance(timing, (int, float)):
                logger.warning(f"Invalid timing type: {type(timing)}, expected numeric")
                return

            if timing < 0:
                logger.warning(f"Negative timing value: {timing}, using absolute value")
                timing = abs(timing)

            if timing > 300:  # 5 minutes seems unreasonable
                logger.warning(f"Extremely high timing value: {timing}s, capping at 300s")
                timing = 300.0

            if timing < 10.0:
                # Respuesta rápida: procesamiento emocional/intuitivo
                archetype_scores.direct += 0.5
                # Note: passionate_emotional es sub-arquetipo, se maneja en análisis posterior

            elif 10.0 <= timing <= 30.0:
                # Respuesta moderada: procesamiento analítico balanceado
                archetype_scores.philosophical += 0.4
                archetype_scores.intellectual += 0.3

            else:  # timing > 30.0
                # Respuesta lenta: procesamiento reflexivo profundo
                archetype_scores.philosophical += 0.6
                archetype_scores.patient += 0.5
                # Note: skeptical_thinker es sub-arquetipo, se maneja en análisis posterior

        except Exception as e:
            logger.error(f"Error applying timing modifiers for timing {timing}: {e}")
            # Don't re-raise, just log and continue without timing modifiers

    async def _calculate_primary_archetype(
        self,
        archetype_scores: ArchetypeScores
    ) -> str:
        """
        Calcula el arquetipo primario determinando la dimensión con mayor puntuación.

        Evalúa todas las puntuaciones de arquetipos primarios y determina cuál
        tiene la puntuación más alta. En caso de empate, selecciona el primero
        alfabéticamente para consistencia.

        El cálculo puede incluir puntuaciones compuestas con combinaciones ponderadas
        de múltiples dimensiones para arquetipos híbridos complejos.

        Args:
            archetype_scores: Instancia de ArchetypeScores con puntuaciones calculadas

        Returns:
            Nombre del arquetipo primario como string (ej: 'intellectual', 'emotional')
        """
        # Obtener todas las puntuaciones como diccionario
        score_dict = {
            'intellectual': archetype_scores.intellectual,
            'emotional': archetype_scores.emotional,
            'exploratory': archetype_scores.exploratory,
            'vulnerable': archetype_scores.vulnerable,
            'philosophical': archetype_scores.philosophical,
            'direct': archetype_scores.direct,
            'patient': archetype_scores.patient,
            'reciprocal': archetype_scores.reciprocal
        }

        # Encontrar la puntuación máxima
        max_score = max(score_dict.values())

        # Fallback en caso de todas las puntuaciones siendo 0
        if max_score == 0.0:
            return 'intellectual'  # Default por especificación

        # En caso de empate, seleccionar alfabéticamente el primero
        for archetype in sorted(score_dict.keys()):
            if score_dict[archetype] == max_score:
                return archetype

        # Fallback adicional (no debería llegarse aquí)
        return 'intellectual'

    async def _determine_sub_archetype(
        self,
        primary_archetype: str,
        sub_archetype_scores: SubArchetypeScores
    ) -> str:
        """
        Determina el sub-arquetipo mapeando arquetipo primario a sub-arquetipos relevantes.

        Mapea el arquetipo primario a sus sub-arquetipos correspondientes y selecciona
        el que tenga la puntuación más alta dentro de esa categoría. Si no hay
        sub-arquetipos relevantes o las puntuaciones son 0, retorna 'undefined'.

        Args:
            primary_archetype: Nombre del arquetipo primario calculado
            sub_archetype_scores: Instancia de SubArchetypeScores con puntuaciones

        Returns:
            Nombre del sub-arquetipo como string o 'undefined' si no aplicable
        """
        # Mapeo de arquetipos primarios a sub-arquetipos relevantes
        archetype_sub_mappings = {
            'intellectual': ['romantic_intellectual', 'skeptical_thinker', 'pure_theorist'],
            'emotional': ['empathetic_emotional', 'passionate_emotional', 'wounded_healer'],
            'exploratory': ['adventure_seeker', 'collector_explorer', 'freedom_lover'],
            'philosophical': ['hedonist_philosopher', 'pure_theorist', 'skeptical_thinker'],
            'vulnerable': ['wounded_healer', 'empathetic_emotional'],
            'direct': ['passionate_emotional', 'adventure_seeker'],
            'patient': ['pure_theorist', 'romantic_intellectual'],
            'reciprocal': ['empathetic_emotional', 'romantic_intellectual']
        }

        # Obtener sub-arquetipos relevantes para el arquetipo primario
        relevant_sub_archetypes = archetype_sub_mappings.get(primary_archetype, [])

        if not relevant_sub_archetypes:
            return 'undefined'

        # Obtener puntuaciones de sub-arquetipos relevantes
        sub_scores = {}
        for sub_archetype in relevant_sub_archetypes:
            if hasattr(sub_archetype_scores, sub_archetype):
                score = getattr(sub_archetype_scores, sub_archetype)
                sub_scores[sub_archetype] = score

        # Si no hay puntuaciones o todas son 0, retornar undefined
        if not sub_scores or max(sub_scores.values()) == 0.0:
            return 'undefined'

        # Seleccionar sub-arquetipo con mayor puntuación
        max_score = max(sub_scores.values())
        for sub_archetype in sorted(sub_scores.keys()):  # Ordenar para consistencia
            if sub_scores[sub_archetype] == max_score:
                return sub_archetype

        return 'undefined'

    async def _calculate_confidence(
        self,
        archetype_scores: ArchetypeScores,
        choices: List[Dict[str, Any]],
        primary_archetype: str
    ) -> float:
        """
        Calcula el nivel de confianza en la clasificación de arquetipo.

        Considera múltiples factores para determinar la confiabilidad de la clasificación:
        - Separación de puntuaciones entre arquetipos (mayor separación = mayor confianza)
        - Consistencia de respuestas (patrones coherentes = mayor confianza)
        - Completitud de datos (más elecciones = mayor confianza)

        Aplica umbrales de confianza según especificación:
        - 0.7 para rasgos mixtos (clasificación válida pero no definitiva)
        - 0.8 para activación de sistema ramificado

        Args:
            archetype_scores: Puntuaciones calculadas de arquetipos primarios
            choices: Lista de elecciones del usuario para análisis de consistencia
            primary_archetype: Arquetipo primario determinado

        Returns:
            Nivel de confianza como float entre 0.0 y 1.0
        """
        # Obtener todas las puntuaciones como lista ordenada
        score_values = [
            archetype_scores.intellectual,
            archetype_scores.emotional,
            archetype_scores.exploratory,
            archetype_scores.vulnerable,
            archetype_scores.philosophical,
            archetype_scores.direct,
            archetype_scores.patient,
            archetype_scores.reciprocal
        ]

        # Ordenar puntuaciones de mayor a menor
        sorted_scores = sorted(score_values, reverse=True)

        # Factor 1: Separación de puntuaciones (0.0-0.5)
        if len(sorted_scores) >= 2 and sorted_scores[0] > 0:
            # Calcular separación entre primera y segunda puntuación
            separation = (sorted_scores[0] - sorted_scores[1]) / sorted_scores[0]
            separation_confidence = min(separation * 0.5, 0.5)
        else:
            separation_confidence = 0.0

        # Factor 2: Completitud de datos (0.0-0.3)
        data_completeness = min(len(choices) / 5.0, 1.0) * 0.3  # Máximo 5 elecciones esperadas

        # Factor 3: Consistencia de respuestas (0.0-0.2)
        # Verificar si hay un patrón coherente en las elecciones
        primary_score = getattr(archetype_scores, primary_archetype)
        total_possible_score = len(choices) * 2.0  # Asumiendo peso promedio de 2.0 por elección

        if total_possible_score > 0:
            consistency = min(primary_score / total_possible_score, 1.0) * 0.2
        else:
            consistency = 0.0

        # Calcular confianza total
        total_confidence = separation_confidence + data_completeness + consistency

        # Aplicar límites y normalizar
        total_confidence = max(0.0, min(1.0, total_confidence))

        return total_confidence

    def _get_fallback_analysis_result(
        self,
        user_id: int,
        choices: List[Dict[str, Any]],
        timings: List[float]
    ) -> Dict[str, Any]:
        """
        Provide a safe fallback result when analysis fails.

        Returns a minimal but valid analysis result to ensure the system
        continues functioning even when errors occur.
        """
        logger.warning(f"Using fallback analysis result for user {user_id}")

        # Safe calculation of metadata
        avg_response_time = 0.0
        try:
            avg_response_time = sum(timings) / len(timings) if timings else 0.0
        except:
            pass

        return {
            'primary_scores': ArchetypeScores(),
            'sub_scores': SubArchetypeScores(),
            'timing_analysis': {
                'cognitive_style': 'balanced',
                'consistency_score': 0.5,
                'temporal_pattern': 'stable'
            },
            'dominant_archetype': 'intellectual',  # Safe default
            'sub_archetype': 'undefined',
            'confidence_score': 0.1,  # Very low confidence
            'behavioral_indicators': ['fallback_analysis', 'error_occurred'],
            'analysis_metadata': {
                'total_choices': len(choices) if isinstance(choices, list) else 0,
                'total_timings': len(timings) if isinstance(timings, list) else 0,
                'avg_response_time': avg_response_time,
                'classification_timestamp': datetime.utcnow(),
                'error_fallback': True
            }
        }

    async def store_classification_results(
        self,
        user_id: int,
        analysis_results: Dict[str, Any]
    ) -> Optional[ArchetypeClassification]:
        """
        Almacena los resultados de clasificación de arquetipo en la base de datos.

        Maneja tanto usuarios nuevos como actualizaciones de clasificaciones existentes.
        Almacena todas las puntuaciones primarias, puntuaciones de sub-arquetipos y datos
        de estilo cognitivo manteniendo compatibilidad hacia atrás con campos existentes.

        Args:
            user_id: ID único del usuario en la base de datos
            analysis_results: Diccionario con resultados del análisis de analyze_l1_choices

        Returns:
            Instancia de ArchetypeClassification actualizada o creada

        Raises:
            SQLAlchemy exceptions si hay errores de base de datos
        """
        try:
            logger.info(f"Storing classification results for user {user_id}")

            # Validate input parameters
            if not isinstance(user_id, int) or user_id <= 0:
                raise ValueError(f"Invalid user_id: {user_id}")

            if not isinstance(analysis_results, dict):
                raise ValueError(f"Analysis results must be a dict, got {type(analysis_results)}")

            # Extraer datos del análisis con validación
            primary_scores = analysis_results.get('primary_scores')
            if not primary_scores:
                logger.error(f"Missing primary_scores in analysis results for user {user_id}")
                return None

            sub_scores = analysis_results.get('sub_scores')
            if not sub_scores:
                logger.error(f"Missing sub_scores in analysis results for user {user_id}")
                return None

            timing_analysis = analysis_results.get('timing_analysis', {})
            confidence_score = analysis_results.get('confidence_score', 0.0)
            dominant_archetype = analysis_results.get('dominant_archetype')
            sub_archetype = analysis_results.get('sub_archetype', 'undefined')
            behavioral_indicators = analysis_results.get('behavioral_indicators', [])

            # Validate extracted data
            if not isinstance(confidence_score, (int, float)):
                logger.warning(f"Invalid confidence_score type for user {user_id}: {type(confidence_score)}")
                confidence_score = 0.0

            if not dominant_archetype:
                logger.warning(f"Missing dominant_archetype for user {user_id}, using fallback")
                dominant_archetype = 'intellectual'

            # Buscar clasificación existente
            stmt = select(ArchetypeClassification).where(ArchetypeClassification.user_id == user_id)
            result = await self.session.execute(stmt)
            classification = result.scalar_one_or_none()

            if classification:
                # Actualizar clasificación existente
                classification.primary_archetype = dominant_archetype
                classification.archetype_confidence = confidence_score

                # Actualizar puntuaciones primarias
                classification.intellectual_score = primary_scores.intellectual
                classification.emotional_score = primary_scores.emotional
                classification.exploratory_score = primary_scores.exploratory
                classification.vulnerable_score = primary_scores.vulnerable
                classification.philosophical_score = primary_scores.philosophical
                classification.direct_score = primary_scores.direct
                classification.patient_score = primary_scores.patient
                classification.reciprocal_score = primary_scores.reciprocal

                # Actualizar puntuaciones de sub-arquetipos
                classification.romantic_intellectual_score = sub_scores.romantic_intellectual
                classification.skeptical_thinker_score = sub_scores.skeptical_thinker
                classification.hedonist_philosopher_score = sub_scores.hedonist_philosopher
                classification.pure_theorist_score = sub_scores.pure_theorist
                classification.empathetic_emotional_score = sub_scores.empathetic_emotional
                classification.passionate_emotional_score = sub_scores.passionate_emotional
                classification.wounded_healer_score = sub_scores.wounded_healer
                classification.adventure_seeker_score = sub_scores.adventure_seeker
                classification.collector_explorer_score = sub_scores.collector_explorer
                classification.freedom_lover_score = sub_scores.freedom_lover

                # Actualizar datos de estilo cognitivo
                classification.cognitive_style = timing_analysis.get('cognitive_style', 'balanced')
                classification.response_consistency = timing_analysis.get('consistency_score', 0.5)
                classification.temporal_pattern = timing_analysis.get('temporal_pattern', 'stable')

                # Actualizar metadatos
                classification.secondary_traits = json.dumps([sub_archetype] if sub_archetype != 'undefined' else [])
                classification.trait_strengths = json.dumps(behavioral_indicators)
                classification.updated_at = datetime.utcnow()

            else:
                # Crear nueva clasificación
                classification = ArchetypeClassification(
                    user_id=user_id,
                    primary_archetype=dominant_archetype,
                    archetype_confidence=confidence_score,

                    # Puntuaciones primarias
                    intellectual_score=primary_scores.intellectual,
                    emotional_score=primary_scores.emotional,
                    exploratory_score=primary_scores.exploratory,
                    vulnerable_score=primary_scores.vulnerable,
                    philosophical_score=primary_scores.philosophical,
                    direct_score=primary_scores.direct,
                    patient_score=primary_scores.patient,
                    reciprocal_score=primary_scores.reciprocal,

                    # Puntuaciones de sub-arquetipos
                    romantic_intellectual_score=sub_scores.romantic_intellectual,
                    skeptical_thinker_score=sub_scores.skeptical_thinker,
                    hedonist_philosopher_score=sub_scores.hedonist_philosopher,
                    pure_theorist_score=sub_scores.pure_theorist,
                    empathetic_emotional_score=sub_scores.empathetic_emotional,
                    passionate_emotional_score=sub_scores.passionate_emotional,
                    wounded_healer_score=sub_scores.wounded_healer,
                    adventure_seeker_score=sub_scores.adventure_seeker,
                    collector_explorer_score=sub_scores.collector_explorer,
                    freedom_lover_score=sub_scores.freedom_lover,

                    # Datos de estilo cognitivo
                    cognitive_style=timing_analysis.get('cognitive_style', 'balanced'),
                    response_consistency=timing_analysis.get('consistency_score', 0.5),
                    temporal_pattern=timing_analysis.get('temporal_pattern', 'stable'),

                    # Metadatos
                    secondary_traits=json.dumps([sub_archetype] if sub_archetype != 'undefined' else []),
                    trait_strengths=json.dumps(behavioral_indicators),
                    archetype_stability=confidence_score,  # Usar confianza como estabilidad inicial
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )

                self.session.add(classification)

            # Confirmar cambios
            await self.session.commit()
            await self.session.refresh(classification)

            logger.info(f"Successfully stored classification for user {user_id}: {dominant_archetype}")
            return classification

        except Exception as e:
            logger.error(f"Error storing classification results for user {user_id}: {e}")
            try:
                await self.session.rollback()
                logger.info(f"Database transaction rolled back for user {user_id}")
            except Exception as rollback_error:
                logger.error(f"Error during rollback for user {user_id}: {rollback_error}")

            # Return None to indicate failure, allowing calling code to handle gracefully
            return None

    async def get_user_classification(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Recupera la clasificación de arquetipo existente para un usuario.

        Busca en la base de datos una clasificación de arquetipo previamente almacenada
        para el usuario especificado. Retorna todos los campos expandidos incluyendo
        puntuaciones primarias, sub-arquetipos y datos de estilo cognitivo.

        Args:
            user_id: ID único del usuario en la base de datos

        Returns:
            Diccionario con clasificación completa del usuario o None si no existe:
            - primary_archetype: Arquetipo primario clasificado
            - archetype_confidence: Nivel de confianza en la clasificación
            - primary_scores: Dict con puntuaciones de arquetipos primarios
            - sub_scores: Dict con puntuaciones de sub-arquetipos
            - cognitive_style: Estilo cognitivo detectado
            - response_consistency: Consistencia de respuestas
            - temporal_pattern: Patrón temporal de respuestas
            - secondary_traits: Lista de rasgos secundarios
            - trait_strengths: Lista de fortalezas de rasgos
            - archetype_stability: Estabilidad de la clasificación
            - created_at: Fecha de creación
            - updated_at: Fecha de última actualización

        Raises:
            SQLAlchemy exceptions si hay errores de base de datos
        """
        try:
            logger.debug(f"Retrieving classification for user {user_id}")

            # Validate user_id
            if not isinstance(user_id, int) or user_id <= 0:
                logger.warning(f"Invalid user_id provided: {user_id}")
                return None

            # Buscar clasificación existente
            stmt = select(ArchetypeClassification).where(ArchetypeClassification.user_id == user_id)
            result = await self.session.execute(stmt)
            classification = result.scalar_one_or_none()

            if not classification:
                logger.debug(f"No classification found for user {user_id}")
                return None

            # Construir puntuaciones primarias
            primary_scores = {
                'intellectual': classification.intellectual_score,
                'emotional': classification.emotional_score,
                'exploratory': classification.exploratory_score,
                'vulnerable': classification.vulnerable_score,
                'philosophical': classification.philosophical_score,
                'direct': classification.direct_score,
                'patient': classification.patient_score,
                'reciprocal': classification.reciprocal_score
            }

            # Construir puntuaciones de sub-arquetipos
            sub_scores = {
                'romantic_intellectual': classification.romantic_intellectual_score,
                'skeptical_thinker': classification.skeptical_thinker_score,
                'hedonist_philosopher': classification.hedonist_philosopher_score,
                'pure_theorist': classification.pure_theorist_score,
                'empathetic_emotional': classification.empathetic_emotional_score,
                'passionate_emotional': classification.passionate_emotional_score,
                'wounded_healer': classification.wounded_healer_score,
                'adventure_seeker': classification.adventure_seeker_score,
                'collector_explorer': classification.collector_explorer_score,
                'freedom_lover': classification.freedom_lover_score
            }

            # Decodificar campos JSON si existen
            secondary_traits = []
            trait_strengths = []

            try:
                if classification.secondary_traits:
                    secondary_traits = json.loads(classification.secondary_traits)
            except (json.JSONDecodeError, TypeError):
                secondary_traits = []

            try:
                if classification.trait_strengths:
                    trait_strengths = json.loads(classification.trait_strengths)
            except (json.JSONDecodeError, TypeError):
                trait_strengths = []

            # Retornar clasificación completa
            return {
                'primary_archetype': classification.primary_archetype,
                'archetype_confidence': classification.archetype_confidence,
                'primary_scores': primary_scores,
                'sub_scores': sub_scores,
                'cognitive_style': classification.cognitive_style,
                'response_consistency': classification.response_consistency,
                'temporal_pattern': classification.temporal_pattern,
                'secondary_traits': secondary_traits,
                'trait_strengths': trait_strengths,
                'archetype_stability': classification.archetype_stability,
                'created_at': classification.created_at,
                'updated_at': classification.updated_at
            }

        except Exception as e:
            logger.error(f"Error retrieving classification for user {user_id}: {e}")
            # Log error gracefully and return None instead of raising
            # This allows the system to continue with fallback behavior
            return None