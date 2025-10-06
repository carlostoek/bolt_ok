from typing import Dict, List
from src.core.archetype_analyzer import ArchetypeAnalyzer, classify_player_archetype
from src.core.diana_personality import DianaPersonality
from src.core.branching_engine import BranchingEngine
from src.core.conversion_engine import ConversionEngine


class NarrativeSystem:
    def __init__(self):
        self.archetype_analyzer = ArchetypeAnalyzer()
        self.branching_engine = BranchingEngine()
        self.conversion_engine = ConversionEngine()
        self.diana_personality = None
        
    def initialize_player_session(self, l1_choices: List[Dict], timings: List[float]):
        """Inicializa sesión del jugador basada en L1"""
        
        # Analizar arquetipo del jugador
        player_archetype = self.archetype_analyzer.analyze_l1_choices(l1_choices, timings)
        
        # Inicializar Diana personalizada
        self.diana_personality = DianaPersonality(player_archetype)
        
        # Determinar ruta inicial
        initial_route = self._determine_initial_route(player_archetype)
        
        return {
            'player_archetype': player_archetype,
            'diana_initial_state': self.diana_personality.emotional_state,
            'recommended_route': initial_route
        }
    
    def process_player_interaction(self, fragment_id: str, choice: Dict) -> Dict:
        """Procesa interacción del jugador y retorna próximo fragmento"""
        
        # Determinar próximo fragmento
        next_fragment_data = self.branching_engine.determine_next_fragment(
            fragment_id, choice, self.diana_personality, {}
        )
        
        # Verificar conversión
        conversion_moment = self.conversion_engine.evaluate_conversion_readiness(
            self.diana_personality, {}
        )
        
        if conversion_moment:
            next_fragment_data['conversion'] = conversion_moment
            
        return next_fragment_data
    
    def _determine_initial_route(self, player_archetype: Dict) -> str:
        """Determina la ruta inicial basada en el arquetipo del jugador"""
        primary_archetype = player_archetype.get('primary_archetype', 'emotional')
        
        route_mapping = {
            'intellectual': 'filosofa',
            'emotional': 'corazon',
            'exploratory': 'aventurera'
        }
        
        return route_mapping.get(primary_archetype, 'corazon')