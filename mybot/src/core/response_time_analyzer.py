from datetime import datetime
from typing import List, Dict


class ResponseTimeAnalyzer:
    def __init__(self):
        self.timing_thresholds = {
            'quick_intuitive': 10.0,
            'thoughtful': 30.0,
            'deliberate': float('inf')
        }
    
    def analyze_response_pattern(self, timings: List[float]) -> Dict:
        """Analiza patrones de tiempo de respuesta"""
        if not timings:
            return {'style': 'unknown', 'consistency': 0.0}
            
        avg_time = sum(timings) / len(timings)
        consistency = self._calculate_consistency(timings)
        
        if avg_time <= self.timing_thresholds['quick_intuitive']:
            style = 'quick_intuitive'
        elif avg_time <= self.timing_thresholds['thoughtful']:
            style = 'thoughtful'
        else:
            style = 'deliberate'
            
        return {
            'style': style,
            'average_time': avg_time,
            'consistency': consistency,
            'pattern': self._detect_pattern(timings)
        }
    
    def _calculate_consistency(self, timings: List[float]) -> float:
        """Calcula consistencia en tiempos de respuesta"""
        if len(timings) < 2:
            return 1.0
            
        mean = sum(timings) / len(timings)
        variance = sum((t - mean) ** 2 for t in timings) / len(timings)
        coefficient_variation = (variance ** 0.5) / mean if mean > 0 else 0
        
        return max(0.0, 1.0 - coefficient_variation)
    
    def _detect_pattern(self, timings: List[float]) -> str:
        """Detecta patrones en progresión de tiempos"""
        if len(timings) < 3:
            return 'insufficient_data'
            
        # Detectar si acelera, decelera o mantiene
        diffs = [timings[i+1] - timings[i] for i in range(len(timings)-1)]
        avg_diff = sum(diffs) / len(diffs)
        
        if avg_diff > 2:
            return 'getting_slower'  # Más pensativo con el tiempo
        elif avg_diff < -2:
            return 'getting_faster'  # Más cómodo/confiado
        else:
            return 'consistent'     # Mantiene ritmo