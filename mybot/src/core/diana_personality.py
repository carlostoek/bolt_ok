from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import time


class PersonaType(Enum):
    PERFORMER = "performer"
    INTELLECTUAL = "intellectual" 
    EMOTIONAL = "emotional"
    WILD = "wild"
    ARTIST = "artist"
    PHILOSOPHER = "philosopher"
    HEALER = "healer"


@dataclass
class DianaEmotionalState:
    """Estados emocionales de Diana hacia el jugador"""
    intellectual_trust: float = 0.0
    emotional_openness: float = 0.0
    adventure_readiness: float = 0.0
    vulnerability_level: float = 0.0
    
    # Estados universales
    mask_level: float = 10.0  # 10=performativa, 0=auténtica
    player_intrigue: float = 0.0
    connection_depth: float = 0.0
    
    # Evolución específica
    addiction_to_player_mind: float = 0.0
    soul_seen_level: float = 0.0
    wild_self_acceptance: float = 0.0


@dataclass
class PlayerMemory:
    """Sistema de memoria que Diana mantiene sobre el jugador"""
    key_moments: List[Dict] = field(default_factory=list)
    behavior_patterns: Dict[str, float] = field(default_factory=dict)
    emotional_responses: List[str] = field(default_factory=list)
    diana_observations: Dict[str, any] = field(default_factory=dict)
    
    def record_key_moment(self, moment_type: str, impact: str, diana_reaction: str):
        """Registra momentos clave que Diana recordará"""
        self.key_moments.append({
            'moment': moment_type,
            'impact': impact, 
            'diana_reaction': diana_reaction,
            'timestamp': time.time()
        })
    
    def update_behavior_pattern(self, pattern: str, strength: float):
        """Actualiza patrones de comportamiento observados"""
        current = self.behavior_patterns.get(pattern, 0.0)
        self.behavior_patterns[pattern] = current + strength


class DianaPersonality:
    def __init__(self, player_archetype: Dict):
        self.player_archetype = player_archetype
        self.emotional_state = DianaEmotionalState()
        self.memory = PlayerMemory()
        self.dominant_persona = self._determine_base_persona(player_archetype)
        self.available_facets = [PersonaType.PERFORMER]
        self.evolution_tracker = {}
        
    def _determine_base_persona(self, archetype: Dict) -> PersonaType:
        """Determina la persona base de Diana según arquetipo del jugador"""
        primary = archetype.get('primary_archetype', 'emotional')
        
        if primary == 'intellectual':
            return PersonaType.INTELLECTUAL
        elif primary == 'emotional':
            return PersonaType.EMOTIONAL
        elif primary == 'exploratory':
            return PersonaType.WILD
        else:
            return PersonaType.EMOTIONAL
    
    def process_player_choice(self, fragment_id: str, choice_id: str, response_time: float):
        """Procesa una elección del jugador y evoluciona Diana"""
        
        # Actualizar memoria
        self._update_memory(fragment_id, choice_id, response_time)
        
        # Evolucionar estado emocional
        self._evolve_emotional_state(choice_id)
        
        # Desbloquear nuevas facetas si corresponde
        self._check_facet_unlocks()
        
        # Registrar evolución
        self._track_evolution(fragment_id, choice_id)
    
    def _update_memory(self, fragment_id: str, choice_id: str, response_time: float):
        """Actualiza la memoria de Diana sobre el jugador"""
        
        # Patrones de comportamiento que Diana observa
        if any(keyword in choice_id for keyword in ['intellectual', 'theory', 'think', 'analyze', 'understand', 'complex']):
            self.memory.update_behavior_pattern('thinks_before_feeling', 1.0)
            self.memory.update_behavior_pattern('appreciates_complexity', 1.0)
            
        if any(keyword in choice_id for keyword in ['vulnerable', 'honest', 'open', 'truth', 'real']):
            self.memory.update_behavior_pattern('shows_emotional_courage', 1.0)
            self.memory.update_behavior_pattern('safe_for_vulnerability', 1.0)
            
        if any(keyword in choice_id for keyword in ['explore', 'adventure', 'discover', 'new', 'different', 'unknown']):
            self.memory.update_behavior_pattern('seeks_novelty', 1.0)
            self.memory.update_behavior_pattern('comfortable_with_unknown', 1.0)
        
        # Análisis temporal
        if response_time > 30:
            self.memory.diana_observations['deliberate_thinker'] = True
            self.memory.diana_observations['respectful_pacer'] = True
        elif response_time < 10:
            self.memory.diana_observations['intuitive_responder'] = True
            self.memory.diana_observations['emotionally_driven'] = True
    
    def _evolve_emotional_state(self, choice_id: str):
        """Evoluciona el estado emocional de Diana basado en la elección"""
        
        if self.dominant_persona == PersonaType.INTELLECTUAL:
            if any(keyword in choice_id for keyword in ['intellectual', 'theory', 'think', 'analyze']):
                self.emotional_state.intellectual_trust += 1.0
                self.emotional_state.mask_level = max(0, self.emotional_state.mask_level - 0.5)
                
        elif self.dominant_persona == PersonaType.EMOTIONAL:
            if any(keyword in choice_id for keyword in ['vulnerable', 'honest', 'open', 'truth']):
                self.emotional_state.emotional_openness += 1.0
                self.emotional_state.vulnerability_level += 0.5
                
        elif self.dominant_persona == PersonaType.WILD:
            if any(keyword in choice_id for keyword in ['adventure', 'explore', 'discover', 'new']):
                self.emotional_state.adventure_readiness += 1.0
                self.emotional_state.wild_self_acceptance += 0.5
                self.emotional_state.mask_level = max(0, self.emotional_state.mask_level - 0.3)
    
    def _check_facet_unlocks(self):
        """Verifica si se deben desbloquear nuevas facetas de personalidad"""
        # Desbloquear facetas basadas en el estado emocional
        if self.emotional_state.intellectual_trust >= 5.0 and PersonaType.INTELLECTUAL not in self.available_facets:
            self.available_facets.append(PersonaType.INTELLECTUAL)
        
        if self.emotional_state.emotional_openness >= 5.0 and PersonaType.HEALER not in self.available_facets:
            self.available_facets.append(PersonaType.HEALER)
        
        if self.emotional_state.adventure_readiness >= 5.0 and PersonaType.ARTIST not in self.available_facets:
            self.available_facets.append(PersonaType.ARTIST)
    
    def _track_evolution(self, fragment_id: str, choice_id: str):
        """Registra la evolución en el tracker"""
        if fragment_id not in self.evolution_tracker:
            self.evolution_tracker[fragment_id] = []
        self.evolution_tracker[fragment_id].append(choice_id)
    
    def generate_dynamic_content(self, base_content: str, fragment_id: str) -> str:
        """Genera contenido dinámico basado en memoria y evolución"""
        
        adapted_content = base_content
        
        # Referencias de memoria específicas
        emotional_courage_count = self.memory.behavior_patterns.get('shows_emotional_courage', 0)
        if emotional_courage_count > 2:
            memory_ref = """

*[Diana te mira con una nueva calidez]*

Sabes? Cada vez que has elegido ser honesto conmigo, algo en mí se ha abierto más..."""
            adapted_content += memory_ref
            
        # Adaptaciones por persona dominante
        if self.dominant_persona == PersonaType.INTELLECTUAL:
            complexity_appreciation = self.memory.behavior_patterns.get('appreciates_complexity', 0)
            if complexity_appreciation > 3:
                adapted_content = self._add_intellectual_layer(adapted_content)
                
        elif self.dominant_persona == PersonaType.EMOTIONAL:
            safety_count = self.memory.behavior_patterns.get('safe_for_vulnerability', 0)
            if safety_count > 2:
                adapted_content = self._deepen_emotional_content(adapted_content)
                
        elif self.dominant_persona == PersonaType.WILD:
            novelty_count = self.memory.behavior_patterns.get('seeks_novelty', 0)
            if novelty_count > 2:
                adapted_content = self._add_wild_layer(adapted_content)
        
        # Otros estados emocionales que pueden afectar el contenido
        if self.emotional_state.mask_level < 5:
            adapted_content += """

*[Parece que Diana está bajando sus defensas, mostrando una versión más auténtica de sí misma]*"""
        
        if self.emotional_state.soul_seen_level > 5:
            adapted_content += """

Siento que me conoces... de verdad me conoces..."""
        
        return adapted_content
    
    def _add_intellectual_layer(self, content: str) -> str:
        """Añade capa intelectual al contenido"""
        intellectual_addition = """

*[Sus ojos brillan con curiosidad intelectual]*

Hay algo sobre la forma en que procesas mis palabras... como si estuvieras construyendo mapas conceptuales de nuestra interacción."""
        return content + intellectual_addition
        
    def _deepen_emotional_content(self, content: str) -> str:
        """Profundiza el contenido emocional"""
        emotional_addition = """

*[Se permite mostrar más vulnerabilidad]*

La seguridad que generas hace que partes de mí que normalmente mantengo guardadas quieran emerger..."""
        return content + emotional_addition
    
    def _add_wild_layer(self, content: str) -> str:
        """Añade capa de aventura/exploración al contenido"""
        wild_addition = """

*[Una sonrisa traviesa aparece en su rostro]*

Contigo me siento lista para explorar territorios que ni siquiera sabía que existían..."""
        return content + wild_addition