"""
ResponseTimeAnalyzer - Sistema de análisis de tiempos de respuesta del usuario
Analiza patrones temporales de respuesta para clasificación psicológica en el Sistema Narrativo Ramificado Diana.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

try:
    from ..database.models import User, ButtonReaction
except ImportError:
    # Fallback to absolute imports for standalone usage
    from database.models import User, ButtonReaction

logger = logging.getLogger(__name__)


class ResponseTimeAnalyzer:
    """
    Analizador de tiempos de respuesta del usuario para el Sistema Narrativo Ramificado Diana.

    Analiza los patrones temporales de respuesta del usuario durante las interacciones de Nivel 1
    para identificar arquetipos psicológicos y patrones de comportamiento. Los datos de timing
    son fundamentales para clasificar usuarios en categorías como:

    - Intuitivos rápidos: Respuestas impulsivas que revelan primeras reacciones emocionales
    - Reflexivos deliberados: Respuestas pausadas que indican procesamiento consciente
    - Contemplativos profundos: Respuestas muy pausadas que sugieren análisis emocional profundo

    El análisis de timing permite detectar:
    - Patrones de impulsividad vs deliberación
    - Momentos de vacilación emocional
    - Cambios en el estado emocional durante la interacción
    - Indicadores de vulnerabilidad psicológica
    - Niveles de engagement y conexión emocional

    Los umbrales de tiempo están calibrados para maximizar la precisión de la clasificación
    psicológica y optimizar la selección de rutas narrativas personalizadas.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el analizador de tiempos de respuesta.

        Args:
            session: Sesión de base de datos SQLAlchemy asíncrona
        """
        self.session = session

        # Umbrales de tiempo para análisis de respuesta (en segundos)
        self.timing_thresholds = {
            "quick_intuitive": 10,    # 0-10s: Respuestas rápidas e intuitivas
            "thoughtful": 30,         # 10-30s: Respuestas reflexivas y consideradas
            "deliberate": float('inf') # 30s+: Respuestas deliberadas y contemplativas
        }

        # Cache para análisis recientes (evita recálculos costosos)
        self._timing_cache = {}
        self._cache_timeout = timedelta(minutes=2)

    def _categorize_response_time(self, response_time_seconds: float) -> str:
        """
        Categoriza el tiempo de respuesta según los umbrales establecidos.

        Args:
            response_time_seconds: Tiempo de respuesta en segundos

        Returns:
            Categoría del tiempo de respuesta: 'quick_intuitive', 'thoughtful', o 'deliberate'
        """
        if response_time_seconds <= self.timing_thresholds["quick_intuitive"]:
            return "quick_intuitive"
        elif response_time_seconds <= self.timing_thresholds["thoughtful"]:
            return "thoughtful"
        else:
            return "deliberate"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica si el cache es válido para la clave dada."""
        if cache_key not in self._timing_cache:
            return False

        cached_item = self._timing_cache[cache_key]
        if "timestamp" not in cached_item:
            return False

        cache_age = datetime.utcnow() - cached_item["timestamp"]
        return cache_age < self._cache_timeout

    def _cache_analysis(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Cachea resultado de análisis temporal."""
        self._timing_cache[cache_key] = {
            **result,
            "timestamp": datetime.utcnow()
        }

        # Limpieza básica de cache (mantener solo 30 items)
        if len(self._timing_cache) > 30:
            oldest_key = min(
                self._timing_cache.keys(),
                key=lambda k: self._timing_cache[k].get("timestamp", datetime.min)
            )
            del self._timing_cache[oldest_key]

    def analyze_response_pattern(self, timings: List[float]) -> Dict[str, Any]:
        """
        Analiza patrones de tiempo de respuesta para clasificación de estilo cognitivo.

        Procesa una lista de tiempos de respuesta para determinar el estilo cognitivo
        del usuario basado en velocidad promedio, consistencia y patrones temporales.

        Args:
            timings: Lista de tiempos de respuesta en segundos

        Returns:
            Dict con claves:
            - style: Clasificación del estilo ('quick_intuitive', 'thoughtful', 'deliberate')
            - average_time: Tiempo promedio de respuesta en segundos
            - consistency: Puntuación de consistencia (0.0-1.0, mayor = más consistente)
            - pattern: Patrón temporal detectado ('getting_slower', 'getting_faster', 'consistent')
        """
        # Manejo de lista vacía con valores por defecto
        if not timings:
            return {
                "style": "thoughtful",
                "average_time": 0.0,
                "consistency": 1.0,
                "pattern": "consistent"
            }

        # Calcular tiempo promedio
        average_time = sum(timings) / len(timings)

        # Clasificar estilo basado en tiempo promedio usando umbrales existentes
        style = self._categorize_response_time(average_time)

        # Calcular consistencia
        consistency = self._calculate_consistency(timings)

        # Detectar patrón temporal
        pattern = self._detect_pattern(timings)

        return {
            "style": style,
            "average_time": average_time,
            "consistency": consistency,
            "pattern": pattern
        }

    def _calculate_consistency(self, timings: List[float]) -> float:
        """
        Calcula la consistencia de tiempos de respuesta usando coeficiente de variación.

        Mide qué tan consistentes son los tiempos de respuesta del usuario.
        Un coeficiente de variación bajo indica respuestas más consistentes.

        Args:
            timings: Lista de tiempos de respuesta en segundos

        Returns:
            Puntuación de consistencia entre 0.0 y 1.0, donde:
            - 1.0 = completamente consistente (coeficiente de variación = 0)
            - 0.0 = completamente inconsistente (coeficiente de variación muy alto)
        """
        # Manejo de casos límite
        if len(timings) < 2:
            return 1.0  # Con menos de 2 datos, asumimos consistencia perfecta

        # Calcular media
        mean_time = sum(timings) / len(timings)

        # Evitar división por cero
        if mean_time == 0.0:
            return 1.0

        # Calcular varianza
        variance = sum((t - mean_time) ** 2 for t in timings) / len(timings)

        # Calcular desviación estándar
        std_dev = variance ** 0.5

        # Calcular coeficiente de variación
        coefficient_of_variation = std_dev / mean_time

        # Convertir a puntuación de consistencia (inversa del coeficiente)
        # Limitamos el coeficiente a un máximo de 2.0 para normalización
        consistency_score = max(0.0, 1.0 - min(coefficient_of_variation / 2.0, 1.0))

        return consistency_score

    def _detect_pattern(self, timings: List[float]) -> str:
        """
        Detecta patrones de aceleración/desaceleración en tiempos de respuesta.

        Analiza la progresión temporal de respuestas para identificar si el usuario
        está acelerando, desacelerando o manteniendo un patrón consistente.

        Args:
            timings: Lista de tiempos de respuesta en segundos (orden cronológico)

        Returns:
            Patrón detectado:
            - 'getting_slower': Usuario toma progresivamente más tiempo
            - 'getting_faster': Usuario responde progresivamente más rápido
            - 'consistent': No hay patrón claro de aceleración/desaceleración
        """
        # Manejo de datos insuficientes
        if len(timings) < 3:
            return "consistent"

        # Calcular diferencias consecutivas
        differences = []
        for i in range(1, len(timings)):
            diff = timings[i] - timings[i-1]
            differences.append(diff)

        # Calcular diferencia promedio
        avg_difference = sum(differences) / len(differences)

        # Umbrales para clasificación de patrones (en segundos)
        # Estos umbrales están calibrados para detectar cambios significativos
        acceleration_threshold = -2.0  # Mejorando velocidad significativamente
        deceleration_threshold = 2.0   # Perdiendo velocidad significativamente

        if avg_difference <= acceleration_threshold:
            return "getting_faster"
        elif avg_difference >= deceleration_threshold:
            return "getting_slower"
        else:
            return "consistent"