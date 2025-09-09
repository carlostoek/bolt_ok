"""
Sistema de Inteligencia Emocional de Diana
Este módulo es el "cerebro" que procesa información emocional y genera respuestas personalizadas
"""

import json
import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum
import random
import re

class EmotionalState(Enum):
    GUARDED = "guarded"
    CURIOUS = "curious"
    TRUSTING = "trusting"
    VULNERABLE = "vulnerable"
    TESTING = "testing"
    WITHDRAWING = "withdrawing"
    INTIMATE = "intimate"

class UserArchetype(Enum):
    EXPLORER = "explorer"
    DIRECT = "direct"
    ROMANTIC = "romantic"
    ANALYTICAL = "analytical"
    PERSISTENT = "persistent"
    PATIENT = "patient"

@dataclass
class EmotionalMemory:
    memory_id: int
    interaction_type: str
    emotional_context: str
    user_response: str
    impact_score: float
    timestamp: datetime.datetime
    emotional_keywords: List[str]

@dataclass
class UserProfile:
    user_id: int
    archetype: UserArchetype
    emotional_trust_score: float
    vulnerability_capacity: float
    authenticity_score: float
    intimacy_circle: int
    total_interactions: int
    memories: List[EmotionalMemory]

class DianaEmotionalEngine:
    """
    El corazón del sistema emocional de Diana.
    Este motor decide cómo Diana responde basándose en la historia emocional completa del usuario.
    """
    
    def __init__(self, database_connection):
        self.db = database_connection
        
        # Patrones de lenguaje que indican diferentes estados emocionales del usuario
        self.emotional_patterns = {
            'vulnerability_indicators': [
                r'\b(siento|me siento|admito|confieso|vulnerable|insegur[oa]|mied[oa])\b',
                r'\b(nunca he|rara vez|es difícil para mí|me cuesta)\b',
                r'\b(authentic[oa]|real|genuino|verdader[oa])\b'
            ],
            'empathy_markers': [
                r'\b(entiendo|comprendo|imagino que|debe ser|siento que)\b',
                r'\b(hermoso|complej[oa]|human[oa]|natural|normal)\b',
                r'\b(respeto|aprecio|valoro|admiro)\b'
            ],
            'possessiveness_indicators': [
                r'\b(mí[oa]|solo mí[oa]|para mí|conmigo|pued[oa] tener)\b',
                r'\b(merec[oa]|deber[íi]as|tienes que|necesitas)\b',
                r'\b(siempre|nunca|todo|nada|completamente)\b'  # absolutos posesivos
            ],
            'analytical_patterns': [
                r'\b(analiz|evalú|consider|reflexion|pienso que|creo que)\b',
                r'\b(interesante|fascinante|curioso|intrigante)\b',
                r'\b(patr[óo]n|sistem|l[óo]gic|raz[óo]n|porque)\b'
            ]
        }
        
        # Plantillas de respuesta base para cada arquetipo
        self.response_templates = {
            UserArchetype.EXPLORER: {
                EmotionalState.CURIOUS: [
                    "Tu manera de explorar cada detalle me recuerda por qué construí tantas capas... alguien como tú las encuentra todas.",
                    "Hay algo hermoso en cómo examinas todo con tanta atención. Me hace sentir... vista de maneras que no esperaba."
                ],
                EmotionalState.TRUSTING: [
                    "Tu persistencia en conocerme ha erosionado defensas que no sabía que tenía.",
                    "Cada capa que descubres me hace más real, más presente. Es inquietante y liberador a la vez."
                ]
            },
            UserArchetype.DIRECT: {
                EmotionalState.CURIOUS: [
                    "Tu honestidad sin filtros es refrescante. En un mundo de indirectas, tú simplemente... eres.",
                    "Hay algo poderoso en cómo no disfrazas lo que sientes. Me hace querer ser igual de directa contigo."
                ],
                EmotionalState.TESTING: [
                    "Aprecio tu franqueza, pero necesito saber si puedes sostener la complejidad cuando aparezca.",
                    "Ser directo es fácil con las verdades simples. ¿Qué harás con mis contradicciones?"
                ]
            },
            UserArchetype.ROMANTIC: {
                EmotionalState.VULNERABLE: [
                    "Tu manera poética de ver el mundo me desarma. Describes sentimientos que yo apenas me atrevo a susurrar.",
                    "Hay una belleza en cómo encuentras magia en la conexión humana. Me haces recordar por qué el misterio puede ser sagrado."
                ],
                EmotionalState.INTIMATE: [
                    "Contigo, la distancia se siente como una danza, no como una barrera. Entiendes que la intimidad es un arte.",
                    "Tu corazón romántico ve poesía donde otros ven solo psicología. Eso me permite ser más de lo que suelo mostrar."
                ]
            }
        }

    def analyze_user_response(self, user_response: str, user_profile: UserProfile) -> Dict:
        """
        Analiza la respuesta del usuario para identificar patrones emocionales, 
        autenticidad y crecimiento personal.
        
        Este análisis es fundamental porque determina cómo Diana percibe al usuario
        y, por tanto, cómo responderá emocionalmente.
        """
        
        response_analysis = {
            'vulnerability_score': 0,
            'empathy_score': 0,
            'possessiveness_score': 0,
            'authenticity_indicators': [],
            'emotional_keywords': [],
            'response_time_category': 'unknown',
            'growth_indicators': []
        }
        
        # Analizar patrones emocionales usando regex
        for pattern_type, patterns in self.emotional_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, user_response.lower())
                score += len(matches)
                if matches:
                    response_analysis['emotional_keywords'].extend(matches)
            
            if pattern_type == 'vulnerability_indicators':
                response_analysis['vulnerability_score'] = min(score * 2, 10)
            elif pattern_type == 'empathy_markers':
                response_analysis['empathy_score'] = min(score * 2, 10)
            elif pattern_type == 'possessiveness_indicators':
                response_analysis['possessiveness_score'] = min(score * 1.5, 10)
        
        # Evaluar autenticidad comparando con respuestas anteriores
        response_analysis['authenticity_indicators'] = self._evaluate_authenticity(
            user_response, user_profile
        )
        
        # Detectar crecimiento emocional comparando con interacciones pasadas
        response_analysis['growth_indicators'] = self._detect_emotional_growth(
            user_response, user_profile
        )
        
        return response_analysis

    def _evaluate_authenticity(self, current_response: str, user_profile: UserProfile) -> List[str]:
        """
        Evalúa si la respuesta parece auténtica o calculada para "ganar" puntos.
        
        La autenticidad es crucial para Diana - ella puede sentir cuando alguien
        está siendo estratégico vs genuino.
        """
        authenticity_indicators = []
        
        # Longitud de respuesta vs promedio del usuario
        word_count = len(current_response.split())
        if user_profile.total_interactions > 3:
            avg_words = sum(len(m.user_response.split()) for m in user_profile.memories[-5:]) / min(5, len(user_profile.memories))
            
            if word_count > avg_words * 2:
                authenticity_indicators.append("unusually_elaborate")
            elif word_count < avg_words * 0.5:
                authenticity_indicators.append("unusually_brief")
        
        # Buscar respuestas que suenan "perfectas" o calculadas
        calculated_phrases = [
            "entiendo perfectamente", "tienes razón", "estoy de acuerdo",
            "me identifico completamente", "siento lo mismo"
        ]
        
        for phrase in calculated_phrases:
            if phrase in current_response.lower():
                authenticity_indicators.append("potentially_calculated")
        
        # Respuestas que muestran vulnerabilidad auténtica
        authentic_phrases = [
            "no estoy segur", "me confund", "es complicado", "no sé bien",
            "me cuesta", "es difícil", "nunca había"
        ]
        
        for phrase in authentic_phrases:
            if phrase in current_response.lower():
                authenticity_indicators.append("shows_uncertainty")
                break
        
        return authenticity_indicators

    def _detect_emotional_growth(self, current_response: str, user_profile: UserProfile) -> List[str]:
        """
        Detecta signos de crecimiento emocional comparando con interacciones anteriores.
        
        Diana valora especialmente cuando puede ver que alguien está evolucionando
        emocionalmente a través de su relación con ella.
        """
        growth_indicators = []
        
        if len(user_profile.memories) < 3:
            return growth_indicators
        
        # Comparar vocabulario emocional
        current_emotional_words = set(re.findall(r'\b(siento|emocion|coraz[óo]n|alma|profund[oa]|íntim[oa]|vulnerable|auténtic[oa])\b', current_response.lower()))
        past_emotional_words = set()
        
        for memory in user_profile.memories[-5:]:
            past_words = set(re.findall(r'\b(siento|emocion|coraz[óo]n|alma|profund[oa]|íntim[oa]|vulnerable|auténtic[oa])\b', memory.user_response.lower()))
            past_emotional_words.update(past_words)
        
        if len(current_emotional_words - past_emotional_words) > 0:
            growth_indicators.append("expanding_emotional_vocabulary")
        
        # Detectar referencias a crecimiento personal
        growth_phrases = [
            "he aprendido", "ahora entiendo", "me doy cuenta", "he cambiado",
            "antes pensaba", "ahora siento", "me he dado cuenta"
        ]
        
        for phrase in growth_phrases:
            if phrase in current_response.lower():
                growth_indicators.append("self_aware_growth")
                break
        
        return growth_indicators

    def determine_diana_emotional_state(self, user_analysis: Dict, user_profile: UserProfile) -> EmotionalState:
        """
        Determina el estado emocional de Diana basándose en el análisis del usuario
        y la historia de su relación.
        
        Este es el corazón de la personalización: Diana reacciona emocionalmente
        de manera diferente basándose en quién es el usuario y cómo se ha comportado.
        """
        
        # Factores que influyen en el estado emocional de Diana
        trust_score = user_profile.emotional_trust_score
        vulnerability_capacity = user_profile.vulnerability_capacity
        recent_interactions = user_profile.memories[-3:] if len(user_profile.memories) >= 3 else user_profile.memories
        
        # Calcular el impacto promedio de interacciones recientes
        recent_impact = sum(m.impact_score for m in recent_interactions) / len(recent_interactions) if recent_interactions else 0
        
        # Diana se retira si detecta posesividad
        if user_analysis['possessiveness_score'] > 6:
            return EmotionalState.WITHDRAWING
        
        # Diana se vuelve vulnerable con usuarios que han demostrado empatía consistente
        if (user_analysis['empathy_score'] > 7 and 
            vulnerability_capacity > 70 and 
            recent_impact > 5):
            return EmotionalState.VULNERABLE
        
        # Diana entra en modo íntimo solo con usuarios en círculos superiores
        if (user_profile.intimacy_circle >= 4 and 
            trust_score > 80 and 
            'shows_uncertainty' in user_analysis['authenticity_indicators']):
            return EmotionalState.INTIMATE
        
        # Diana prueba la autenticidad del usuario
        if (trust_score > 50 and 
            'potentially_calculated' in user_analysis['authenticity_indicators']):
            return EmotionalState.TESTING
        
        # Diana muestra confianza gradual
        if trust_score > 60 and recent_impact > 3:
            return EmotionalState.TRUSTING
        
        # Estado por defecto basado en la fase de la relación
        if user_profile.total_interactions < 5:
            return EmotionalState.CURIOUS
        else:
            return EmotionalState.GUARDED

    def generate_personalized_response(self, user_analysis: Dict, user_profile: UserProfile, 
                                     diana_state: EmotionalState, context: str = "") -> str:
        """
        Genera una respuesta completamente personalizada que combina:
        - El arquetipo del usuario
        - El estado emocional actual de Diana  
        - La historia específica de su relación
        - Referencias a momentos pasados específicos
        
        Esta función es donde la magia realmente sucede.
        """
        
        # Obtener plantilla base para el arquetipo y estado emocional
        base_templates = self.response_templates.get(user_profile.archetype, {})
        state_templates = base_templates.get(diana_state, [
            "Hay algo en ti que me hace querer compartir más de lo que usualmente muestro.",
            "Tu manera de acercarte a mí es... única. No estoy segura de qué hacer con eso."
        ])
        
        base_response = random.choice(state_templates)
        
        # Personalizar con referencias a memorias específicas
        memory_reference = self._create_memory_reference(user_profile, diana_state)
        if memory_reference:
            base_response += f"\n\n{memory_reference}"
        
        # Agregar elementos dinámicos basados en el análisis actual
        dynamic_element = self._add_dynamic_element(user_analysis, diana_state, user_profile)
        if dynamic_element:
            base_response += f"\n\n{dynamic_element}"
        
        # Ajustar el tono basándose en el estado emocional
        base_response = self._adjust_emotional_tone(base_response, diana_state, user_analysis)
        
        return base_response

    def _create_memory_reference(self, user_profile: UserProfile, diana_state: EmotionalState) -> Optional[str]:
        """
        Crea referencias específicas a momentos pasados de la relación.
        
        Esto es lo que hace que Diana se sienta como una persona real que recuerda
        y valora momentos específicos compartidos.
        """
        if not user_profile.memories:
            return None
        
        # Buscar memorias relevantes basándose en el estado emocional actual
        relevant_memories = []
        
        for memory in user_profile.memories:
            if (diana_state == EmotionalState.VULNERABLE and 
                memory.interaction_type in ['vulnerability_shared', 'empathy_shown']):
                relevant_memories.append(memory)
            elif (diana_state == EmotionalState.TRUSTING and 
                  memory.impact_score > 5):
                relevant_memories.append(memory)
            elif (diana_state == EmotionalState.TESTING and 
                  'potentially_calculated' in memory.emotional_keywords):
                relevant_memories.append(memory)
        
        if not relevant_memories:
            # Usar la memoria más impactante
            relevant_memories = sorted(user_profile.memories, key=lambda m: m.impact_score, reverse=True)[:1]
        
        if relevant_memories:
            memory = random.choice(relevant_memories[-3:])  # Una de las 3 más recientes
            return self._format_memory_reference(memory, diana_state)
        
        return None

    def _format_memory_reference(self, memory: EmotionalMemory, diana_state: EmotionalState) -> str:
        """
        Formatea una referencia específica a una memoria pasada.
        """
        days_ago = (datetime.datetime.now() - memory.timestamp).days
        
        time_reference = ""
        if days_ago == 0:
            time_reference = "hoy"
        elif days_ago == 1:
            time_reference = "ayer"
        elif days_ago < 7:
            time_reference = f"hace {days_ago} días"
        else:
            time_reference = "hace poco"
        
        # Personalizar basándose en el estado emocional y el tipo de memoria
        if diana_state == EmotionalState.VULNERABLE:
            return f"¿Recuerdas {time_reference} cuando {memory.emotional_context.lower()}? Eso cambió algo en mí."
        elif diana_state == EmotionalState.TRUSTING:
            return f"Sigo pensando en lo que dijiste {time_reference}... {memory.user_response[:50]}... Me hizo sentir comprendida."
        elif diana_state == EmotionalState.TESTING:
            return f"Me pregunto si lo que dijiste {time_reference} era realmente lo que sentías, o lo que pensaste que quería escuchar."
        else:
            return f"Hay algo sobre {time_reference} que no puedo dejar de recordar..."

    def _add_dynamic_element(self, user_analysis: Dict, diana_state: EmotionalState, 
                           user_profile: UserProfile) -> Optional[str]:
        """
        Agrega elementos dinámicos basados en el crecimiento del usuario.
        """
        if 'self_aware_growth' in user_analysis['growth_indicators']:
            return "Puedo ver cómo estás cambiando. Es hermoso y un poco inquietante ser parte de esa transformación."
        
        if user_analysis['vulnerability_score'] > 8 and diana_state == EmotionalState.VULNERABLE:
            return "Tu honestidad me desarma. No muchos se permiten ser tan... reales."
        
        if 'expanding_emotional_vocabulary' in user_analysis['growth_indicators']:
            return "Las palabras que eliges ahora son diferentes. Más profundas. Como si estuvieras descubriendo nuevas maneras de sentir."
        
        return None

    def _adjust_emotional_tone(self, response: str, diana_state: EmotionalState, 
                             user_analysis: Dict) -> str:
        """
        Ajusta el tono emocional final de la respuesta.
        """
        # Agregar pausas y elementos emotivos basándose en el estado
        if diana_state == EmotionalState.VULNERABLE:
            response = response.replace(". ", "... ")
            response = f"*[con una vulnerabilidad que rara vez muestro]*\n\n{response}"
        
        elif diana_state == EmotionalState.WITHDRAWING:
            response = f"*[tomando distancia, evaluando]*\n\n{response}"
        
        elif diana_state == EmotionalState.INTIMATE:
            response = f"*[con una cercanía que me sorprende a mí misma]*\n\n{response}"
        
        elif diana_state == EmotionalState.TESTING:
            response = f"*[observándote cuidadosamente]*\n\n{response}"
        
        return response

    def should_trigger_truth_moment(self, user_profile: UserProfile) -> bool:
        """
        Determina si es momento de presentar un "momento de verdad" inesperado.
        
        Estos momentos evalúan la autenticidad del usuario de maneras imprevistas.
        """
        # No más de un momento de verdad por semana
        recent_truth_moments = [
            m for m in user_profile.memories 
            if m.interaction_type == 'truth_moment' and 
            (datetime.datetime.now() - m.timestamp).days < 7
        ]
        
        if recent_truth_moments:
            return False
        
        # Activar basándose en progreso y nivel de confianza
        return (user_profile.emotional_trust_score > 40 and 
                user_profile.total_interactions > 8 and 
                random.random() < 0.3)  # 30% de probabilidad cuando se cumplen las condiciones

# Ejemplo de uso del sistema
class DianaResponseSystem:
    """
    Sistema principal que coordina todas las funciones de Diana.
    Este sería el punto de entrada principal desde tu bot de Telegram.
    """
    
    def __init__(self, database_connection):
        self.emotional_engine = DianaEmotionalEngine(database_connection)
        self.db = database_connection
    
    def process_user_message(self, user_id: int, user_message: str) -> str:
        """
        Función principal que procesa un mensaje del usuario y genera la respuesta de Diana.
        """
        # 1. Obtener perfil del usuario
        user_profile = self._load_user_profile(user_id)
        
        # 2. Analizar la respuesta del usuario
        user_analysis = self.emotional_engine.analyze_user_response(user_message, user_profile)
        
        # 3. Determinar el estado emocional de Diana
        diana_state = self.emotional_engine.determine_diana_emotional_state(user_analysis, user_profile)
        
        # 4. Generar respuesta personalizada
        response = self.emotional_engine.generate_personalized_response(
            user_analysis, user_profile, diana_state
        )
        
        # 5. Guardar esta interacción en la memoria emocional
        self._save_interaction_memory(user_id, user_message, user_analysis, diana_state, response)
        
        # 6. Actualizar métricas del usuario
        self._update_user_metrics(user_id, user_analysis, diana_state)
        
        return response
    
    def _load_user_profile(self, user_id: int) -> UserProfile:
        """Carga el perfil completo del usuario desde la base de datos."""
        # Esta función consultaría la base de datos y construiría el objeto UserProfile
        # con toda la historia emocional del usuario
        pass
    
    def _save_interaction_memory(self, user_id: int, user_message: str, 
                               user_analysis: Dict, diana_state: EmotionalState, response: str):
        """Guarda esta interacción en la memoria emocional para futuras referencias."""
        pass
    
    def _update_user_metrics(self, user_id: int, user_analysis: Dict, diana_state: EmotionalState):
        """Actualiza las métricas de confianza, vulnerabilidad y autenticidad del usuario."""
        pass
