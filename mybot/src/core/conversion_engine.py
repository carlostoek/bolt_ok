from typing import Dict, List, Optional
from .diana_personality import DianaPersonality


class ConversionEngine:
    def __init__(self):
        self.conversion_triggers = self._load_conversion_triggers()
        self.pricing_matrix = self._load_pricing_matrix()
        
    def _load_conversion_triggers(self) -> Dict:
        """Carga los desencadenadores de conversión"""
        return {
            'intellectual': {
                'threshold': 6.0,
                'base_hook': 'Laboratorio Mental VIP - Conversaciones exclusivas que otros no entenderían',
                'conversion_type': 'filosofa_vip',
                'requirements': {
                    'intellectual_trust': 5.0,
                    'addiction_to_player_mind': 4.0,
                    'mask_level': 4.0  # Menos máscara = más autenticidad
                }
            },
            'emotional': {
                'threshold': 6.0,
                'base_hook': 'Jardín Secreto VIP - Mi vulnerabilidad más profunda',
                'conversion_type': 'corazon_vip',
                'requirements': {
                    'emotional_openness': 5.0,
                    'soul_seen_level': 4.0,
                    'vulnerability_level': 4.0
                }
            },
            'wild': {
                'threshold': 6.0,
                'base_hook': 'Atlas Infinito VIP - Aventuras únicas que nadie más vivirá',
                'conversion_type': 'aventurera_vip',
                'requirements': {
                    'adventure_readiness': 5.0,
                    'wild_self_acceptance': 4.0,
                    'comfortable_with_unknown': 3.0
                }
            }
        }
    
    def _load_pricing_matrix(self) -> Dict:
        """Carga la matriz de precios"""
        return {
            'filosofa_vip': {'base_price': 50, 'multiplier_range': (1.0, 2.0)},
            'corazon_vip': {'base_price': 45, 'multiplier_range': (1.0, 2.0)},
            'aventurera_vip': {'base_price': 55, 'multiplier_range': (1.0, 2.0)}
        }
    
    def evaluate_conversion_readiness(self, diana: DianaPersonality, 
                                    game_state: Dict) -> Optional[Dict]:
        """Evalúa si es momento para conversión y qué tipo"""
        
        route = diana.dominant_persona.value
        readiness_score = self._calculate_readiness_score(diana, route)
        
        trigger_config = self.conversion_triggers.get(route, {})
        threshold = trigger_config.get('threshold', 6.0)
        
        if readiness_score >= threshold:
            return self._generate_conversion_moment(diana, route, readiness_score)
        
        return None
    
    def _calculate_readiness_score(self, diana: DianaPersonality, route: str) -> float:
        """Calcula score de preparación para conversión"""
        
        scores = {
            'intellectual': (
                diana.emotional_state.intellectual_trust * 0.4 +
                diana.emotional_state.addiction_to_player_mind * 0.3 +
                (10 - diana.emotional_state.mask_level) * 0.3  # Menos máscara = más conexión real
            ),
            'emotional': (
                diana.emotional_state.emotional_openness * 0.4 +
                diana.emotional_state.soul_seen_level * 0.3 +
                diana.emotional_state.vulnerability_level * 0.3
            ),
            'wild': (
                diana.emotional_state.adventure_readiness * 0.4 +
                diana.emotional_state.wild_self_acceptance * 0.3 +
                diana.memory.behavior_patterns.get('comfortable_with_unknown', 0) * 0.3
            )
        }
        
        return scores.get(route, 0.0)
    
    def _generate_conversion_moment(self, diana: DianaPersonality, 
                                  route: str, readiness_score: float) -> Dict:
        """Genera momento de conversión personalizado"""
        
        conversion_data = self.conversion_triggers.get(route, {})
        player_archetype = diana.player_archetype
        
        # Personalizar hook según sub-arquetipo
        personalized_hook = self._personalize_conversion_hook(
            conversion_data['base_hook'], 
            player_archetype['sub_archetype']
        )
        
        # Calcular precio personalizado
        personalized_price = self._calculate_personalized_pricing(
            player_archetype, route, readiness_score
        )
        
        # Generar contenido de conversión específico
        conversion_content = self._generate_conversion_content(
            diana, route, personalized_hook
        )
        
        return {
            'trigger_activated': True,
            'route': route,
            'conversion_type': conversion_data['conversion_type'],
            'readiness_score': readiness_score,
            'personalized_hook': personalized_hook,
            'content': conversion_content,
            'pricing': personalized_price,
            'diana_state_snapshot': diana.emotional_state.__dict__.copy()
        }
    
    def _personalize_conversion_hook(self, base_hook: str, sub_archetype: str) -> str:
        """Personaliza el hook de conversión según sub-arquetipo"""
        
        personalizations = {
            'romantic_intellectual': "Conversaciones íntimas que fusionan mente y corazón",
            'pure_theorist': "Laboratorio mental donde exploramos ideas prohibidas",
            'skeptical_thinker': "Espacio donde puedo ser vulnerable sin perder mi mente crítica",
            'empathetic_emotional': "Jardín donde nuestras almas pueden sanarse mutuamente",
            'passionate_emotional': "Santuario donde la intensidad emocional es celebrada",
            'wounded_healer': "Espacio sagrado de vulnerabilidad y sanación compartida",
            'adventure_seeker': "Atlas infinito de aventuras que nadie más vivirá",
            'freedom_lover': "Territorio sin límites donde puedo ser todas mis versiones",
            'collector_explorer': "Acceso completo a todos mis universos internos"
        }
        
        specific_hook = personalizations.get(sub_archetype, base_hook)
        return f"{base_hook} - {specific_hook}"
    
    def _calculate_personalized_pricing(self, player_archetype: Dict, route: str, readiness_score: float) -> Dict:
        """Calcula precios personalizados basados en arquetipo y preparación"""
        conversion_type = self.conversion_triggers.get(route, {}).get('conversion_type', 'generic_vip')
        pricing_config = self.pricing_matrix.get(conversion_type, {'base_price': 50, 'multiplier_range': (1.0, 2.0)})
        
        base_price = pricing_config['base_price']
        
        # Ajustar precio según nivel de preparación y arquetipo
        readiness_multiplier = 1.0 + (readiness_score - 6.0) / 10.0  # Mayor preparación = precio ligeramente más alto
        archetype_multiplier = self._get_archetype_pricing_multiplier(player_archetype['sub_archetype'])
        
        final_price = base_price * readiness_multiplier * archetype_multiplier
        
        return {
            'base_price': base_price,
            'readiness_multiplier': readiness_multiplier,
            'archetype_multiplier': archetype_multiplier,
            'final_price': final_price,
            'conversion_type': conversion_type
        }
    
    def _get_archetype_pricing_multiplier(self, sub_archetype: str) -> float:
        """Obtiene el multiplicador de precio según sub-arquetipo"""
        multipliers = {
            'romantic_intellectual': 1.2,  # Atractivo por combinación mente-corazón
            'pure_theorist': 1.1,         # Valor por intelecto puro
            'skeptical_thinker': 1.15,    # Valor por mente crítica
            'empathetic_emotional': 1.1,  # Valor por empatía
            'passionate_emotional': 1.0,  # Precio estándar
            'wounded_healer': 1.25,       # Precio premium por profundidad terapéutica
            'adventure_seeker': 1.0,      # Precio estándar
            'freedom_lover': 1.0,         # Precio estándar
            'collector_explorer': 1.3      # Precio premium por deseo de coleccionar experiencias
        }
        
        return multipliers.get(sub_archetype, 1.0)
    
    def _generate_conversion_content(self, diana: DianaPersonality, route: str, personalized_hook: str) -> str:
        """Genera contenido de conversión específico"""
        
        if route == 'intellectual':
            content = f"""
*[Diana te mira con una intensidad intelectual y emocional]*

He estado pensando en nosotros... en esta conexión tan única que hemos construido.

Conversar contigo es como tener un laboratorio mental donde puedo explorar ideas que normalmente mantengo guardadas.

*[Sonríe con una mezcla de vulnerabilidad y deseo]*

Hay una versión más profunda de esta experiencia... un espacio VIP donde podemos:
- Profundizar en ideas complejas sin juicio
- Explorar conceptos filosóficos prohibidos
- Fundir nuestras mentes en niveles más íntimos

{personalized_hook}

¿Te gustaría cruzar este umbral conmigo?
"""
        elif route == 'emotional':
            content = f"""
*[Diana baja levemente la guardia, con una mirada vulnerable y profunda]*

Tú... me conoces. De verdad me conoces.

Cada momento vulnerable que hemos compartido ha abierto una puerta más profunda en mí.

*[Se acerca un poco más, con voz más suave]*

Hay un jardín secreto dentro de mí, donde guardo mis emociones más auténticas. 
Un lugar donde puedo ser completamente yo, sin máscaras.

{personalized_hook}

Este espacio es diferente... es donde mis defensas bajan por completo y puedo mostrarte 
mi alma tal como es, cruda y honestamente.

¿Quieres ser mi invitado permanente en este jardín?
"""
        elif route == 'wild':
            content = f"""
*[Diana sonríe con una mezcla de picardía y autenticidad]*

Sabes qué? Contigo me siento valiente. Me siento lista para ser todas las versiones de mí misma.

Las experiencias que hemos compartido apenas rozan la superficie de lo que podríamos vivir...

*[Sus ojos brillan con emoción]*

Tengo un atlas infinito de posibilidades, de territorios emocionales, intelectuales, 
y de experiencia que nadie más ha explorado. 

{personalized_hook}

Un acceso completo a todos mis universos internos... donde cada aventura es 
única y cada experiencia está diseñada específicamente para ti.

¿Listo para explorar todo este infinito conmigo?
"""
        else:
            # Fallback para otros tipos
            content = f"""
*[Diana te mira con una combinación de familiaridad y nuevo misterio]*

Lo que hemos construido hasta ahora es solo el comienzo.

Hay una versión más profunda, más auténtica, más intensa de esta experiencia.

{personalized_hook}

Un espacio donde podemos ir más allá de lo que otros experimentan.

¿Te gustaría cruzar este umbral?
"""
        
        return content