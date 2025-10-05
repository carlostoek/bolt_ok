from typing import Dict, List, Any
from .diana_personality import DianaPersonality, PersonaType
from .fragment_builder import FragmentBuilder


class BranchingEngine:
    def __init__(self):
        self.route_definitions = self._load_route_definitions()
        self.fragment_library = self._load_fragment_library()
        self.fragment_builder = FragmentBuilder()
        
    def _load_route_definitions(self) -> Dict:
        """Carga las definiciones de rutas"""
        # Esta sería la lógica para cargar las rutas desde archivos de datos
        return {
            'filosofa': {
                'progression': ['l2_f1', 'l2_f2', 'l2_f3', 'l3_f1', 'l3_f2', 'l3_f3'],
                'requirements': {'intellectual_focus': True},
                'personality_alignment': ['intellectual', 'romantic_intellectual', 'pure_theorist']
            },
            'corazon': {
                'progression': ['l2_c1', 'l2_c2', 'l2_c3', 'l3_c1', 'l3_c2', 'l3_c3'],
                'requirements': {'emotional_focus': True},
                'personality_alignment': ['empathetic_emotional', 'wounded_healer', 'passionate_emotional']
            },
            'aventurera': {
                'progression': ['l2_a1', 'l2_a2', 'l2_a3', 'l3_a1', 'l3_a2', 'l3_a3'],
                'requirements': {'exploratory_focus': True},
                'personality_alignment': ['adventure_seeker', 'collector_explorer', 'freedom_lover']
            }
        }
    
    def _load_fragment_library(self) -> Dict:
        """Carga la biblioteca de fragmentos"""
        # Esta sería la lógica para cargar fragmentos desde archivos de datos
        return {
            # Fragmentos de ejemplo - en una implementación real, estos vendrían de archivos
            'l1_f1': {
                'id': 'diana_l1_f1_arquetipo_analyzer',
                'title': 'Holis, Bienvenido a Los Kinkys - El Umbral de las Posibilidades',
                'content': 'Contenido base del fragmento L1F1',
                'choices': [
                    {'id': 'choice_l1_curiosity_intellectual', 'text': 'Opción intelectual'},
                    {'id': 'choice_l1_curiosity_emotional', 'text': 'Opción emocional'},
                    {'id': 'choice_l1_curiosity_exploratory', 'text': 'Opción exploratoria'}
                ],
                'route': 'universal'
            }
        }
    
    def determine_next_fragment(self, current_fragment: str, player_choice: Dict, 
                              diana_personality: DianaPersonality, 
                              game_state: Dict) -> Dict:
        """Determina el próximo fragmento basado en estado completo"""
        
        # 1. Procesar elección actual en Diana
        diana_personality.process_player_choice(
            current_fragment, 
            player_choice['id'], 
            player_choice.get('response_time', 15.0)
        )
        
        # 2. Evaluar compatibilidad de rutas
        route_compatibility = self._calculate_route_compatibility(
            diana_personality, game_state
        )
        
        # 3. Seleccionar fragmento óptimo
        next_fragment_id = self._select_optimal_fragment(
            current_fragment, route_compatibility, diana_personality
        )
        
        # 4. Generar contenido dinámico
        base_fragment = self._get_fragment_by_id(next_fragment_id)
        dynamic_content = diana_personality.generate_dynamic_content(
            base_fragment['content'], next_fragment_id
        )
        
        # 5. Construir respuesta completa
        return {
            'fragment': {
                **base_fragment,
                'content': dynamic_content,
                'choices': self._adapt_choices(base_fragment['choices'], diana_personality)
            },
            'diana_evolution': diana_personality.emotional_state,
            'memory_state': diana_personality.memory,
            'route_progression': route_compatibility
        }
    
    def _calculate_route_compatibility(self, diana: DianaPersonality, game_state: Dict) -> Dict:
        """Calcula compatibilidad con diferentes rutas"""
        
        compatibility = {}
        
        # Ruta Filosófica
        if diana.dominant_persona == PersonaType.INTELLECTUAL:
            compatibility['filosofa'] = (
                diana.emotional_state.intellectual_trust * 0.4 +
                diana.memory.behavior_patterns.get('appreciates_complexity', 0) * 0.3 +
                (10 - diana.emotional_state.mask_level) * 0.3
            )
        
        # Ruta Corazón
        if diana.dominant_persona == PersonaType.EMOTIONAL:
            compatibility['corazon'] = (
                diana.emotional_state.emotional_openness * 0.4 +
                diana.memory.behavior_patterns.get('safe_for_vulnerability', 0) * 0.3 +
                diana.emotional_state.vulnerability_level * 0.3
            )
        
        # Ruta Aventurera
        if diana.dominant_persona == PersonaType.WILD:
            compatibility['aventurera'] = (
                diana.emotional_state.adventure_readiness * 0.4 +
                diana.memory.behavior_patterns.get('comfortable_with_unknown', 0) * 0.3 +
                diana.memory.behavior_patterns.get('seeks_novelty', 0) * 0.3
            )
        
        return compatibility
    
    def _select_optimal_fragment(self, current_fragment: str, compatibility: Dict, 
                               diana: DianaPersonality) -> str:
        """Selecciona el fragmento óptimo basado en compatibilidad"""
        
        # Lógica de progresión por ruta
        if diana.dominant_persona == PersonaType.INTELLECTUAL:
            if compatibility.get('filosofa', 0) >= 6.0:
                return self._get_next_filosofa_fragment(current_fragment, diana)
            else:
                return self._get_buildup_filosofa_fragment(current_fragment, diana)
                
        elif diana.dominant_persona == PersonaType.EMOTIONAL:
            if compatibility.get('corazon', 0) >= 6.0:
                return self._get_next_corazon_fragment(current_fragment, diana)
            else:
                return self._get_buildup_corazon_fragment(current_fragment, diana)
                
        elif diana.dominant_persona == PersonaType.WILD:
            if compatibility.get('aventurera', 0) >= 6.0:
                return self._get_next_aventurera_fragment(current_fragment, diana)
            else:
                return self._get_buildup_aventurera_fragment(current_fragment, diana)
        
        # Fallback a fragmento de construcción
        return self._get_relationship_building_fragment(current_fragment, diana)
    
    def _get_next_filosofa_fragment(self, current_fragment: str, diana: DianaPersonality) -> str:
        """Obtiene el siguiente fragmento para la ruta filosófica"""
        # Implementación de lógica para obtener el siguiente fragmento filosófico
        # Basado en el progreso actual y el sub-arquetipo
        sub_archetype = diana.player_archetype.get('sub_archetype', 'pure_theorist')
        
        # En una implementación real, esto consultaría el estado actual del jugador
        # y seleccionaría el fragmento adecuado de la ruta filosófica
        if 'l2' in current_fragment:
            return f"diana_l3_f1_filosofa_{sub_archetype}"
        else:
            return f"diana_l2_f1_filosofa_{sub_archetype}"
    
    def _get_buildup_filosofa_fragment(self, current_fragment: str, diana: DianaPersonality) -> str:
        """Obtiene un fragmento de buildup para la ruta filosófica"""
        sub_archetype = diana.player_archetype.get('sub_archetype', 'pure_theorist')
        return f"diana_buildup_filosofa_{sub_archetype}"
    
    def _get_next_corazon_fragment(self, current_fragment: str, diana: DianaPersonality) -> str:
        """Obtiene el siguiente fragmento para la ruta del corazón"""
        sub_archetype = diana.player_archetype.get('sub_archetype', 'empathetic_emotional')
        
        if 'l2' in current_fragment:
            return f"diana_l3_c1_corazon_{sub_archetype}"
        else:
            return f"diana_l2_c1_corazon_{sub_archetype}"
    
    def _get_buildup_corazon_fragment(self, current_fragment: str, diana: DianaPersonality) -> str:
        """Obtiene un fragmento de buildup para la ruta del corazón"""
        sub_archetype = diana.player_archetype.get('sub_archetype', 'empathetic_emotional')
        return f"diana_buildup_corazon_{sub_archetype}"
    
    def _get_next_aventurera_fragment(self, current_fragment: str, diana: DianaPersonality) -> str:
        """Obtiene el siguiente fragmento para la ruta aventurera"""
        sub_archetype = diana.player_archetype.get('sub_archetype', 'adventure_seeker')
        
        if 'l2' in current_fragment:
            return f"diana_l3_a1_aventurera_{sub_archetype}"
        else:
            return f"diana_l2_a1_aventurera_{sub_archetype}"
    
    def _get_buildup_aventurera_fragment(self, current_fragment: str, diana: DianaPersonality) -> str:
        """Obtiene un fragmento de buildup para la ruta aventurera"""
        sub_archetype = diana.player_archetype.get('sub_archetype', 'adventure_seeker')
        return f"diana_buildup_aventurera_{sub_archetype}"
    
    def _get_relationship_building_fragment(self, current_fragment: str, diana: DianaPersonality) -> str:
        """Obtiene un fragmento de construcción de relación general"""
        return "diana_relationship_building_generic"
    
    def _get_fragment_by_id(self, fragment_id: str) -> Dict:
        """Obtiene un fragmento por su ID"""
        # En una implementación real, buscaría en una base de datos o archivo
        # Por ahora, retorna un fragmento por defecto
        return {
            'id': fragment_id,
            'title': f'Título para {fragment_id}',
            'content': f'Contenido base para el fragmento {fragment_id}',
            'choices': [
                {'id': f'choice_{fragment_id}_1', 'text': 'Opción 1'},
                {'id': f'choice_{fragment_id}_2', 'text': 'Opción 2'}
            ],
            'route': self._determine_route_from_id(fragment_id)
        }
    
    def _determine_route_from_id(self, fragment_id: str) -> str:
        """Determina la ruta basada en el ID del fragmento"""
        if 'filosofa' in fragment_id:
            return 'filosofa'
        elif 'corazon' in fragment_id:
            return 'corazon'
        elif 'aventurera' in fragment_id:
            return 'aventurera'
        else:
            return 'universal'
    
    def _adapt_choices(self, choices: List[Dict], diana: DianaPersonality) -> List[Dict]:
        """Adapta las opciones basadas en la personalidad de Diana y la memoria del jugador"""
        adapted_choices = []
        
        for choice in choices:
            adapted_choice = choice.copy()
            
            # Modificar el texto de la opción basado en la memoria si es relevante
            if 'safe_for_vulnerability' in diana.memory.behavior_patterns:
                if 'vulnerable' in choice['id']:
                    # Aumentar el atractivo de opciones vulnerables si el jugador ha mostrado seguridad
                    adapted_choice['text'] = f"✨ {choice['text']} (Diana siente seguridad contigo)"
            
            if 'appreciates_complexity' in diana.memory.behavior_patterns:
                if 'intellectual' in choice['id']:
                    # Aumentar el atractivo de opciones intelectuales
                    adapted_choice['text'] = f"🧠 {choice['text']} (Diana valora tu mente)"
            
            if 'seeks_novelty' in diana.memory.behavior_patterns:
                if 'adventure' in choice['id'] or 'explore' in choice['id']:
                    # Aumentar el atractivo de opciones de aventura
                    adapted_choice['text'] = f"🗺️ {choice['text']} (Diana quiere explorar contigo)"
            
            adapted_choices.append(adapted_choice)
        
        return adapted_choices