from dataclasses import dataclass
from typing import Dict, List, Optional
import time
from enum import Enum


@dataclass
class ArchetypeScores:
    """Variables primarias de arquetipo (0-10)"""
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
    """Variables secundarias para sub-clasificación"""
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
    def __init__(self):
        self.archetype_weights = self._load_archetype_weights()

    def _load_archetype_weights(self) -> Dict:
        """Carga los pesos de arquetipo predeterminados"""
        return {
            'intellectual': {
                'choice_keywords': ['intellectual', 'theory', 'think', 'analyze', 'understand', 'explore'],
                'primary_weight': 2.0,
                'secondary_weight': 1.0
            },
            'emotional': {
                'choice_keywords': ['emotional', 'feel', 'vulnerable', 'connect', 'honest', 'open'],
                'primary_weight': 2.0,
                'secondary_weight': 1.0
            },
            'exploratory': {
                'choice_keywords': ['explore', 'adventure', 'discover', 'new', 'different', 'unknown'],
                'primary_weight': 2.0,
                'secondary_weight': 0.5
            }
        }

    def analyze_l1_choices(self, choices: List[Dict], timings: List[float]) -> Dict:
        """Analiza elecciones de L1 para determinar arquetipo del jugador"""
        scores = ArchetypeScores()
        sub_scores = SubArchetypeScores()

        for choice, timing in zip(choices, timings):
            self._process_choice(choice, timing, scores, sub_scores)

        return self._calculate_final_archetype(scores, sub_scores, timings)

    def _process_choice(self, choice: Dict, timing: float, scores: ArchetypeScores, sub_scores: SubArchetypeScores):
        """Procesa una elección individual y actualiza scores"""
        choice_id = choice.get('id', '')
        choice_text = choice.get('text', '').lower()

        # Análisis por tipo de elección
        if any(keyword in choice_id or keyword in choice_text for keyword in ['intellectual', 'theory', 'think', 'analyze', 'understand']):
            scores.intellectual += 2.0
            scores.philosophical += 1.0
            sub_scores.pure_theorist += 0.5
            sub_scores.skeptical_thinker += 0.3

        if any(keyword in choice_id or keyword in choice_text for keyword in ['emotional', 'feel', 'vulnerable', 'connect', 'honest', 'open']):
            scores.emotional += 2.0
            scores.vulnerable += 1.0
            sub_scores.empathetic_emotional += 0.5
            sub_scores.wounded_healer += 0.3

        if any(keyword in choice_id or keyword in choice_text for keyword in ['explore', 'adventure', 'discover', 'new']):
            scores.exploratory += 2.0
            sub_scores.adventure_seeker += 0.5
            sub_scores.collector_explorer += 0.3

        if any(keyword in choice_id or keyword in choice_text for keyword in ['romantic', 'seduce', 'ideas']):
            scores.intellectual += 1.0
            scores.emotional += 1.0
            sub_scores.romantic_intellectual += 1.0
            sub_scores.hedonist_philosopher += 0.3

        if any(keyword in choice_id or keyword in choice_text for keyword in ['freedom', 'expectations', 'ataduras']):
            scores.exploratory += 1.5
            scores.direct += 1.0
            sub_scores.freedom_lover += 1.0

        # Análisis temporal para sub-arquetipos
        if timing > 30:  # Respuesta deliberada
            scores.philosophical += 1.0
            sub_scores.skeptical_thinker += 0.5
            scores.patient += 0.5
        elif timing < 10:  # Respuesta rápida
            scores.direct += 1.0
            sub_scores.passionate_emotional += 0.5
        else:  # Respuesta media
            scores.reciprocal += 0.5

    def _calculate_final_archetype(self, scores: ArchetypeScores, sub_scores: SubArchetypeScores, timings: List[float]) -> Dict:
        """Calcula arquetipo final basado en todos los scores"""
        primary_scores = {
            'intellectual': scores.intellectual + scores.philosophical,
            'emotional': scores.emotional + scores.vulnerable,
            'exploratory': scores.exploratory
        }

        primary_archetype = max(primary_scores, key=primary_scores.get)

        return {
            'primary_archetype': primary_archetype,
            'sub_archetype': self._determine_sub_archetype(primary_archetype, sub_scores),
            'confidence_level': self._calculate_confidence(primary_scores),
            'cognitive_style': self._analyze_cognitive_style(timings),
            'raw_scores': scores,
            'sub_scores': sub_scores
        }

    def _determine_sub_archetype(self, primary_archetype: str, sub_scores: SubArchetypeScores) -> str:
        """Determina el sub-arquetipo basado en el arquetipo primario y los scores secundarios"""
        if primary_archetype == 'intellectual':
            sub_scores_dict = {
                'romantic_intellectual': sub_scores.romantic_intellectual,
                'skeptical_thinker': sub_scores.skeptical_thinker,
                'hedonist_philosopher': sub_scores.hedonist_philosopher,
                'pure_theorist': sub_scores.pure_theorist
            }
        elif primary_archetype == 'emotional':
            sub_scores_dict = {
                'empathetic_emotional': sub_scores.empathetic_emotional,
                'passionate_emotional': sub_scores.passionate_emotional,
                'wounded_healer': sub_scores.wounded_healer,
            }
        elif primary_archetype == 'exploratory':
            sub_scores_dict = {
                'adventure_seeker': sub_scores.adventure_seeker,
                'collector_explorer': sub_scores.collector_explorer,
                'freedom_lover': sub_scores.freedom_lover
            }
        else:
            # Default to emotional if somehow we get unexpected primary archetype
            sub_scores_dict = {
                'empathetic_emotional': sub_scores.empathetic_emotional,
                'passionate_emotional': sub_scores.passionate_emotional,
                'wounded_healer': sub_scores.wounded_healer,
            }

        return max(sub_scores_dict, key=sub_scores_dict.get)

    def _calculate_confidence(self, primary_scores: Dict[str, float]) -> float:
        """Calcula el nivel de confianza en la clasificación"""
        max_score = max(primary_scores.values())
        min_score = min(primary_scores.values())
        
        # Confidence is higher when there's a clear difference between top score and others
        score_difference = max_score - min_score
        total_score = sum(primary_scores.values())
        
        if total_score == 0:
            return 0.0
        
        # Normalize the confidence (0-1 scale)
        confidence = min(1.0, score_difference / total_score * 2)
        return confidence

    def _analyze_cognitive_style(self, timings: List[float]) -> str:
        """Analiza el estilo cognitivo basado en tiempos de respuesta"""
        if not timings:
            return 'unknown'
        
        avg_time = sum(timings) / len(timings)
        
        if avg_time > 30:
            return 'deliberative'
        elif avg_time > 15:
            return 'balanced'
        else:
            return 'intuitive'


def analyze_choice_progression(choices: List[Dict]) -> Dict:
    """Analiza cómo progresionan las elecciones del jugador"""
    if len(choices) < 2:
        return {'pattern': 'insufficient_data'}

    # Detectar patrones de cambio en tipo de elecciones
    choice_types = [categorize_choice_type(choice.get('id', '')) for choice in choices]

    patterns = {
        'pattern': detect_progression_pattern(choice_types),
        'consistency': calculate_choice_consistency(choice_types),
        'risk_taking': analyze_risk_progression(choices)
    }

    return patterns


def categorize_choice_type(choice_id: str) -> str:
    """Categoriza el tipo de elección basado en el ID"""
    if any(keyword in choice_id for keyword in ['intellectual', 'theory', 'think', 'analyze']):
        return 'intellectual'
    elif any(keyword in choice_id for keyword in ['emotional', 'feel', 'vulnerable', 'connect']):
        return 'emotional'
    elif any(keyword in choice_id for keyword in ['explore', 'adventure', 'discover', 'new']):
        return 'exploratory'
    else:
        return 'other'


def detect_progression_pattern(choice_types: List[str]) -> str:
    """Detecta patrones en la progresión de tipos de elecciones"""
    if len(choice_types) < 2:
        return 'insufficient_data'

    # Contar transiciones
    transitions = []
    for i in range(1, len(choice_types)):
        transitions.append((choice_types[i-1], choice_types[i]))

    # Detectar si hay consistencia o cambio
    unique_transitions = len(set(transitions))
    total_choices = len(choice_types)

    if unique_transitions == 1 and len(set(choice_types)) == 1:
        return 'consistent_focus'
    elif unique_transitions > total_choices * 0.7:
        return 'diverse_exploration'
    else:
        return 'progressive_evolution'


def calculate_choice_consistency(choice_types: List[str]) -> float:
    """Calcula la consistencia en los tipos de elecciones"""
    if not choice_types:
        return 0.0

    unique_types = len(set(choice_types))
    total_choices = len(choice_types)

    # Consistency inversely related to diversity of types
    if total_choices == 1:
        return 1.0
    else:
        return max(0.0, 1.0 - (unique_types - 1) / (total_choices - 1) if total_choices > 1 else 0.0)


def analyze_risk_progression(choices: List[Dict]) -> str:
    """Analiza la tendencia de toma de riesgos"""
    # This is a placeholder - actual implementation would analyze the risk level of each choice
    return 'neutral'


def refine_sub_archetype(base_sub_archetype: str, cognitive_style: str, progression_result: Dict) -> str:
    """Refina el sub-arquetipo basado en estilo cognitivo y progresión"""
    # Combine base sub-archetype with cognitive style and progression patterns
    if cognitive_style == 'deliberative':
        if base_sub_archetype == 'adventure_seeker':
            return f"deliberate_{base_sub_archetype}"
        elif base_sub_archetype in ['romantic_intellectual', 'skeptical_thinker', 'pure_theorist']:
            return f"contemplative_{base_sub_archetype}"
    elif cognitive_style == 'intuitive':
        if base_sub_archetype in ['passionate_emotional', 'adventure_seeker']:
            return f"impulsive_{base_sub_archetype}"
    
    return base_sub_archetype


def determine_optimal_route(archetype_result: Dict, timing_result: Dict) -> str:
    """Determina la ruta óptima basada en arquetipo y análisis temporal"""
    primary_archetype = archetype_result.get('primary_archetype', 'emotional')
    
    # Define route mapping
    route_mapping = {
        'intellectual': 'filosofa',
        'emotional': 'corazon',
        'exploratory': 'aventurera'
    }
    
    return route_mapping.get(primary_archetype, 'corazon')


# Import for timing_analyzer
from .response_time_analyzer import ResponseTimeAnalyzer
from datetime import datetime
from typing import List, Dict


def classify_player_archetype(choices: List[Dict], timings: List[float], 
                            interaction_metadata: Dict = None) -> Dict:
    """Función principal para clasificar arquetipo del jugador"""
    
    analyzer = ArchetypeAnalyzer()
    
    # Análisis de elecciones
    archetype_result = analyzer.analyze_l1_choices(choices, timings)
    
    # Análisis temporal
    timing_analyzer = ResponseTimeAnalyzer()
    timing_result = timing_analyzer.analyze_response_pattern(timings)
    
    # Análisis de progresión (cómo evolucionan las elecciones)
    progression_result = analyze_choice_progression(choices)
    
    # Integrar todos los análisis
    final_classification = {
        'primary_archetype': archetype_result['primary_archetype'],
        'sub_archetype': refine_sub_archetype(
            archetype_result['sub_archetype'],
            timing_result['style'],
            progression_result
        ),
        'cognitive_style': timing_result['style'],
        'confidence_level': archetype_result['confidence_level'],
        'behavioral_patterns': {
            'decision_speed': timing_result['average_time'],
            'consistency': timing_result['consistency'],
            'evolution_pattern': progression_result['pattern']
        },
        'recommended_route': determine_optimal_route(archetype_result, timing_result)
    }
    
    return final_classification