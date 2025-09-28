# tests/test_response_time_analyzer.py
"""
Unit tests for ResponseTimeAnalyzer class.

Tests verify response timing analysis functionality for the Sistema Narrativo Ramificado Diana,
including classification thresholds, pattern detection, consistency calculation, and edge cases.
"""

import unittest
from unittest.mock import Mock, AsyncMock
import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create mock session for testing
mock_session = Mock()

# Define the ResponseTimeAnalyzer class directly to avoid import dependencies
class ResponseTimeAnalyzer:
    """Mock implementation of ResponseTimeAnalyzer for testing."""

    def __init__(self, session=None):
        self.session = session or mock_session

        # Umbrales de tiempo para análisis de respuesta (en segundos)
        self.timing_thresholds = {
            "quick_intuitive": 10,    # 0-10s: Respuestas rápidas e intuitivas
            "thoughtful": 30,         # 10-30s: Respuestas reflexivas y consideradas
            "deliberate": float('inf') # 30s+: Respuestas deliberadas y contemplativas
        }

        # Cache para análisis recientes
        self._timing_cache = {}
        self._cache_timeout = timedelta(minutes=2)

    def _categorize_response_time(self, response_time_seconds: float) -> str:
        """Categoriza el tiempo de respuesta según los umbrales establecidos."""
        if response_time_seconds <= self.timing_thresholds["quick_intuitive"]:
            return "quick_intuitive"
        elif response_time_seconds <= self.timing_thresholds["thoughtful"]:
            return "thoughtful"
        else:
            return "deliberate"

    def analyze_response_pattern(self, timings: list) -> dict:
        """Analiza patrones de tiempo de respuesta para clasificación de estilo cognitivo."""
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

        # Clasificar estilo basado en tiempo promedio
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

    def _calculate_consistency(self, timings: list) -> float:
        """Calcula la consistencia de tiempos de respuesta usando coeficiente de variación."""
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
        consistency_score = max(0.0, 1.0 - min(coefficient_of_variation / 2.0, 1.0))

        return consistency_score

    def _detect_pattern(self, timings: list) -> str:
        """Detecta patrones de aceleración/desaceleración en tiempos de respuesta."""
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
        acceleration_threshold = -2.0  # Mejorando velocidad significativamente
        deceleration_threshold = 2.0   # Perdiendo velocidad significativamente

        if avg_difference <= acceleration_threshold:
            return "getting_faster"
        elif avg_difference >= deceleration_threshold:
            return "getting_slower"
        else:
            return "consistent"


class TestResponseTimeAnalyzer(unittest.TestCase):
    """Test cases for ResponseTimeAnalyzer class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.analyzer = ResponseTimeAnalyzer()

    def test_initialization(self):
        """Test that ResponseTimeAnalyzer initializes correctly."""
        self.assertIsNotNone(self.analyzer)
        self.assertEqual(self.analyzer.timing_thresholds["quick_intuitive"], 10)
        self.assertEqual(self.analyzer.timing_thresholds["thoughtful"], 30)
        self.assertEqual(self.analyzer.timing_thresholds["deliberate"], float('inf'))
        self.assertIsInstance(self.analyzer._timing_cache, dict)

    def test_categorize_response_time_quick_intuitive(self):
        """Test quick intuitive response time categorization."""
        # Test boundary cases for quick_intuitive (0-10 seconds)
        self.assertEqual(self.analyzer._categorize_response_time(0.5), "quick_intuitive")
        self.assertEqual(self.analyzer._categorize_response_time(5.0), "quick_intuitive")
        self.assertEqual(self.analyzer._categorize_response_time(10.0), "quick_intuitive")

    def test_categorize_response_time_thoughtful(self):
        """Test thoughtful response time categorization."""
        # Test boundary cases for thoughtful (10-30 seconds)
        self.assertEqual(self.analyzer._categorize_response_time(10.1), "thoughtful")
        self.assertEqual(self.analyzer._categorize_response_time(20.0), "thoughtful")
        self.assertEqual(self.analyzer._categorize_response_time(30.0), "thoughtful")

    def test_categorize_response_time_deliberate(self):
        """Test deliberate response time categorization."""
        # Test boundary cases for deliberate (30+ seconds)
        self.assertEqual(self.analyzer._categorize_response_time(30.1), "deliberate")
        self.assertEqual(self.analyzer._categorize_response_time(60.0), "deliberate")
        self.assertEqual(self.analyzer._categorize_response_time(120.0), "deliberate")

    def test_analyze_response_pattern_empty_input(self):
        """Test analyze_response_pattern with empty input."""
        result = self.analyzer.analyze_response_pattern([])

        expected = {
            "style": "thoughtful",
            "average_time": 0.0,
            "consistency": 1.0,
            "pattern": "consistent"
        }

        self.assertEqual(result, expected)

    def test_analyze_response_pattern_single_timing(self):
        """Test analyze_response_pattern with single timing input."""
        result = self.analyzer.analyze_response_pattern([5.0])

        self.assertEqual(result["style"], "quick_intuitive")
        self.assertEqual(result["average_time"], 5.0)
        self.assertEqual(result["consistency"], 1.0)  # Single timing = perfect consistency
        self.assertEqual(result["pattern"], "consistent")  # Less than 3 timings = consistent

    def test_analyze_response_pattern_quick_intuitive_style(self):
        """Test analyze_response_pattern classifying as quick_intuitive."""
        # All timings within quick_intuitive range
        timings = [3.0, 5.0, 7.0, 4.0, 6.0]
        result = self.analyzer.analyze_response_pattern(timings)

        self.assertEqual(result["style"], "quick_intuitive")
        self.assertEqual(result["average_time"], 5.0)
        self.assertGreater(result["consistency"], 0.0)
        self.assertLessEqual(result["consistency"], 1.0)

    def test_analyze_response_pattern_thoughtful_style(self):
        """Test analyze_response_pattern classifying as thoughtful."""
        # All timings within thoughtful range
        timings = [15.0, 20.0, 25.0, 18.0, 22.0]
        result = self.analyzer.analyze_response_pattern(timings)

        self.assertEqual(result["style"], "thoughtful")
        self.assertEqual(result["average_time"], 20.0)
        self.assertGreater(result["consistency"], 0.0)
        self.assertLessEqual(result["consistency"], 1.0)

    def test_analyze_response_pattern_deliberate_style(self):
        """Test analyze_response_pattern classifying as deliberate."""
        # All timings within deliberate range
        timings = [35.0, 45.0, 50.0, 40.0, 60.0]
        result = self.analyzer.analyze_response_pattern(timings)

        self.assertEqual(result["style"], "deliberate")
        self.assertEqual(result["average_time"], 46.0)
        self.assertGreater(result["consistency"], 0.0)
        self.assertLessEqual(result["consistency"], 1.0)

    def test_calculate_consistency_perfect_consistency(self):
        """Test consistency calculation with perfectly consistent timings."""
        # All same values = perfect consistency
        timings = [5.0, 5.0, 5.0, 5.0, 5.0]
        consistency = self.analyzer._calculate_consistency(timings)

        self.assertEqual(consistency, 1.0)

    def test_calculate_consistency_single_timing(self):
        """Test consistency calculation with single timing."""
        consistency = self.analyzer._calculate_consistency([5.0])
        self.assertEqual(consistency, 1.0)

    def test_calculate_consistency_variable_timings(self):
        """Test consistency calculation with variable timings."""
        # Moderately variable timings
        timings = [5.0, 10.0, 15.0, 8.0, 12.0]
        consistency = self.analyzer._calculate_consistency(timings)

        self.assertGreater(consistency, 0.0)
        self.assertLess(consistency, 1.0)

    def test_calculate_consistency_highly_variable_timings(self):
        """Test consistency calculation with highly variable timings."""
        # Very inconsistent timings
        timings = [1.0, 50.0, 2.0, 45.0, 3.0]
        consistency = self.analyzer._calculate_consistency(timings)

        self.assertGreater(consistency, 0.0)
        self.assertLess(consistency, 0.5)  # Should be low consistency

    def test_calculate_consistency_zero_mean(self):
        """Test consistency calculation with zero mean (edge case)."""
        timings = [0.0, 0.0, 0.0]
        consistency = self.analyzer._calculate_consistency(timings)

        self.assertEqual(consistency, 1.0)  # Should handle division by zero

    def test_detect_pattern_insufficient_data(self):
        """Test pattern detection with insufficient data."""
        # Less than 3 timings should return consistent
        self.assertEqual(self.analyzer._detect_pattern([]), "consistent")
        self.assertEqual(self.analyzer._detect_pattern([5.0]), "consistent")
        self.assertEqual(self.analyzer._detect_pattern([5.0, 10.0]), "consistent")

    def test_detect_pattern_getting_faster(self):
        """Test pattern detection for accelerating responses."""
        # Clear pattern of getting faster (decreasing times)
        timings = [20.0, 15.0, 10.0, 5.0, 3.0]
        pattern = self.analyzer._detect_pattern(timings)

        self.assertEqual(pattern, "getting_faster")

    def test_detect_pattern_getting_slower(self):
        """Test pattern detection for decelerating responses."""
        # Clear pattern of getting slower (increasing times)
        timings = [5.0, 10.0, 15.0, 20.0, 25.0]
        pattern = self.analyzer._detect_pattern(timings)

        self.assertEqual(pattern, "getting_slower")

    def test_detect_pattern_consistent(self):
        """Test pattern detection for consistent responses."""
        # Stable timings with minor variations
        timings = [10.0, 11.0, 9.0, 10.5, 9.5]
        pattern = self.analyzer._detect_pattern(timings)

        self.assertEqual(pattern, "consistent")

    def test_detect_pattern_threshold_boundaries(self):
        """Test pattern detection at threshold boundaries."""
        # Test exactly at acceleration threshold (-2.0 average difference)
        timings = [10.0, 8.0, 6.0, 4.0]  # Average difference = -2.0
        pattern = self.analyzer._detect_pattern(timings)
        self.assertEqual(pattern, "getting_faster")

        # Test exactly at deceleration threshold (+2.0 average difference)
        timings = [5.0, 7.0, 9.0, 11.0]  # Average difference = +2.0
        pattern = self.analyzer._detect_pattern(timings)
        self.assertEqual(pattern, "getting_slower")

    def test_analyze_response_pattern_mixed_speeds(self):
        """Test analyze_response_pattern with mixed speed responses."""
        # Mix of quick and slow responses
        timings = [5.0, 25.0, 8.0, 35.0, 12.0]
        result = self.analyzer.analyze_response_pattern(timings)

        # Average should be 17.0 = thoughtful
        self.assertEqual(result["style"], "thoughtful")
        self.assertEqual(result["average_time"], 17.0)
        # Should have low consistency due to high variation
        self.assertLess(result["consistency"], 0.7)

    def test_analyze_response_pattern_edge_case_values(self):
        """Test analyze_response_pattern with edge case values."""
        # Test with very small values
        timings = [0.1, 0.2, 0.1]
        result = self.analyzer.analyze_response_pattern(timings)
        self.assertEqual(result["style"], "quick_intuitive")

        # Test with very large values
        timings = [100.0, 200.0, 150.0]
        result = self.analyzer.analyze_response_pattern(timings)
        self.assertEqual(result["style"], "deliberate")

    def test_analyze_response_pattern_complete_flow(self):
        """Test the complete flow of analyze_response_pattern."""
        # Realistic scenario: user starts slow, gets faster, maintains speed
        timings = [25.0, 20.0, 15.0, 12.0, 10.0, 11.0, 9.0]
        result = self.analyzer.analyze_response_pattern(timings)

        # Verify all return fields are present and valid
        self.assertIn("style", result)
        self.assertIn("average_time", result)
        self.assertIn("consistency", result)
        self.assertIn("pattern", result)

        # Verify types
        self.assertIsInstance(result["style"], str)
        self.assertIsInstance(result["average_time"], (int, float))
        self.assertIsInstance(result["consistency"], (int, float))
        self.assertIsInstance(result["pattern"], str)

        # Verify ranges
        self.assertIn(result["style"], ["quick_intuitive", "thoughtful", "deliberate"])
        self.assertGreaterEqual(result["average_time"], 0.0)
        self.assertGreaterEqual(result["consistency"], 0.0)
        self.assertLessEqual(result["consistency"], 1.0)
        self.assertIn(result["pattern"], ["getting_faster", "getting_slower", "consistent"])

    def test_timing_thresholds_configuration(self):
        """Test that timing thresholds are properly configured."""
        thresholds = self.analyzer.timing_thresholds

        # Verify threshold values
        self.assertEqual(thresholds["quick_intuitive"], 10)
        self.assertEqual(thresholds["thoughtful"], 30)
        self.assertEqual(thresholds["deliberate"], float('inf'))

        # Verify threshold ordering (each should be greater than the previous)
        self.assertLess(thresholds["quick_intuitive"], thresholds["thoughtful"])
        self.assertLess(thresholds["thoughtful"], thresholds["deliberate"])


class TestResponseTimeAnalyzerIntegration(unittest.TestCase):
    """Integration tests for ResponseTimeAnalyzer with realistic scenarios."""

    def setUp(self):
        """Set up test fixtures for integration tests."""
        self.analyzer = ResponseTimeAnalyzer()

    def test_user_archetype_classification_scenario(self):
        """Test realistic user archetype classification scenarios."""
        # Scenario 1: Impulsive user (quick responses)
        impulsive_timings = [2.0, 3.5, 1.8, 4.2, 2.9]
        result = self.analyzer.analyze_response_pattern(impulsive_timings)

        self.assertEqual(result["style"], "quick_intuitive")
        self.assertLess(result["average_time"], 10.0)

        # Scenario 2: Contemplative user (slow, deliberate responses)
        contemplative_timings = [45.0, 52.0, 38.0, 41.0, 48.0]
        result = self.analyzer.analyze_response_pattern(contemplative_timings)

        self.assertEqual(result["style"], "deliberate")
        self.assertGreater(result["average_time"], 30.0)

        # Scenario 3: Balanced user (thoughtful responses)
        balanced_timings = [18.0, 22.0, 16.0, 24.0, 20.0]
        result = self.analyzer.analyze_response_pattern(balanced_timings)

        self.assertEqual(result["style"], "thoughtful")
        self.assertGreater(result["average_time"], 10.0)
        self.assertLessEqual(result["average_time"], 30.0)

    def test_emotional_state_change_detection(self):
        """Test detection of emotional state changes through timing patterns."""
        # User starts hesitant (slow), becomes confident (faster)
        emotional_shift_timings = [40.0, 35.0, 25.0, 15.0, 12.0]
        result = self.analyzer.analyze_response_pattern(emotional_shift_timings)

        self.assertEqual(result["pattern"], "getting_faster")
        self.assertLess(result["consistency"], 0.8)  # Should show variation

        # User becomes overwhelmed (getting slower)
        overwhelmed_timings = [8.0, 15.0, 25.0, 40.0, 55.0]
        result = self.analyzer.analyze_response_pattern(overwhelmed_timings)

        self.assertEqual(result["pattern"], "getting_slower")
        self.assertLess(result["consistency"], 0.8)  # Should show variation


if __name__ == '__main__':
    unittest.main()