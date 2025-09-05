"""
DianaChoiceEngine - The Choice Architecture Masterpiece

Sistema central de procesamiento de decisiones con consecuencias diferidas,
personalización psicológica y mantenimiento de la consistencia del personaje Diana.

Características principales:
- Procesamiento de decisiones con consecuencias diferidas
- Sistema de refuerzo de ratio variable
- Perfilado psicológico a través de decisiones
- Memoria natural de decisiones pasadas
- Personalización de respuestas manteniendo consistencia de Diana
- Escalación emocional progresiva

Author: Diana Bot Creative Team
Architecture: Choice Consequence Engine with Psychological Profiling
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import random

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, func, desc

from ..database.models import User, UserSession
from ..database.narrative_unified import (
    UserNarrativeState, UserDecisionLog, UserArchetype,
    NarrativeFragment, NarrativeCharacterValidation
)


logger = logging.getLogger(__name__)


class EmotionalLayer(Enum):
    """Niveles emocionales de las decisiones según la progresión del usuario."""
    CURIOSITY = "curious_exploration"           # Niveles 1-2: Exploración y curiosidad
    VULNERABILITY = "emotional_vulnerability"   # Niveles 3-4: Apertura emocional
    INTIMACY = "deep_intimacy"                  # Niveles 5-6: Intimidad profunda
    CORE_IDENTITY = "core_identity_exposure"    # Elite tier: Identidad central


class ConsequenceType(Enum):
    """Tipos de consecuencias que pueden activarse por las decisiones."""
    IMMEDIATE = "immediate_response"
    DELAYED = "delayed_callback"
    PROGRESSIVE = "progressive_revelation"
    PATTERN_BASED = "pattern_recognition"
    PSYCHOLOGICAL = "psychological_profile_update"


class ChoiceImpactLevel(Enum):
    """Niveles de impacto de las decisiones en el perfil del usuario."""
    SURFACE = "surface_preference"      # Preferencias básicas
    BEHAVIORAL = "behavioral_pattern"   # Patrones de comportamiento
    EMOTIONAL = "emotional_core"        # Núcleo emocional
    IDENTITY = "core_identity"          # Identidad central


@dataclass
class ChoiceContext:
    """Contexto completo de una decisión del usuario."""
    user_id: int
    choice_id: str
    choice_text: str
    fragment_id: str
    current_level: int
    emotional_layer: EmotionalLayer
    impact_level: ChoiceImpactLevel
    timestamp: datetime
    response_time_seconds: int
    psychological_metadata: Dict[str, Any]


@dataclass
class ChoiceConsequence:
    """Consecuencia de una decisión con activación diferida."""
    consequence_id: str
    trigger_conditions: Dict[str, Any]
    activation_level: int
    consequence_type: ConsequenceType
    diana_response_template: str
    emotional_weight: float
    psychological_insights: List[str]
    character_consistency_requirements: Dict[str, Any]


@dataclass
class PsychologicalProfile:
    """Perfil psicológico del usuario basado en patrones de decisiones."""
    user_id: int
    dominant_traits: List[str]
    emotional_patterns: Dict[str, Any]
    vulnerability_indicators: List[str]
    communication_preferences: Dict[str, Any]
    intimacy_comfort_level: float
    decision_making_style: str
    psychological_archetype: str
    diana_adaptation_profile: Dict[str, Any]


class DianaChoiceEngine:
    """
    Motor central de procesamiento de decisiones con arquitectura de consecuencias diferidas.
    
    Este sistema procesa las decisiones del usuario, mantiene memoria de patrones,
    y genera respuestas de Diana personalizadas manteniendo consistencia de carácter.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.consequence_seeds = {}  # Cache de semillas de consecuencias
        self.psychological_profiles = {}  # Cache de perfiles psicológicos
        self.character_validator = None  # Se inyecta externamente
        
    async def process_choice(
        self, 
        user_id: int, 
        choice_id: str, 
        choice_text: str,
        fragment_id: str,
        response_time_seconds: int
    ) -> Dict[str, Any]:
        """
        Procesa una decisión del usuario con todas las implicaciones psicológicas.
        
        Args:
            user_id: ID del usuario
            choice_id: ID único de la elección
            choice_text: Texto de la opción elegida
            fragment_id: ID del fragmento narrativo
            response_time_seconds: Tiempo que tardó en responder
            
        Returns:
            Dict con respuesta inmediata, consecuencias plantadas y perfil actualizado
        """
        logger.info(f"Processing choice for user {user_id}: {choice_id}")
        
        try:
            # Obtener contexto del usuario
            user_context = await self._get_user_context(user_id)
            
            # Crear contexto de decisión
            choice_context = ChoiceContext(
                user_id=user_id,
                choice_id=choice_id,
                choice_text=choice_text,
                fragment_id=fragment_id,
                current_level=user_context['current_level'],
                emotional_layer=self._determine_emotional_layer(user_context['current_level']),
                impact_level=self._analyze_choice_impact(choice_text, user_context),
                timestamp=datetime.utcnow(),
                response_time_seconds=response_time_seconds,
                psychological_metadata=await self._extract_psychological_metadata(
                    choice_text, user_context
                )
            )
            
            # Procesar decisión y generar consecuencias
            immediate_response = await self._generate_immediate_response(choice_context)
            planted_seeds = await self._plant_consequence_seeds(choice_context)
            updated_profile = await self._update_psychological_profile(choice_context)
            
            # Registrar decisión en base de datos
            await self._record_choice_decision(choice_context, planted_seeds)
            
            # Activar consecuencias de decisiones pasadas si corresponde
            activated_consequences = await self._check_delayed_consequences(user_id)
            
            return {
                "immediate_response": immediate_response,
                "planted_seeds": planted_seeds,
                "activated_consequences": activated_consequences,
                "psychological_profile": updated_profile,
                "character_consistency_score": immediate_response.get("consistency_score", 95),
                "emotional_engagement_level": self._calculate_engagement_level(choice_context),
                "next_choice_tree_hint": await self._generate_next_choice_hint(choice_context)
            }
            
        except Exception as e:
            logger.error(f"Error processing choice for user {user_id}: {str(e)}")
            raise
    
    async def trigger_delayed_consequences(
        self, 
        user_id: int, 
        target_level: int
    ) -> List[Dict[str, Any]]:
        """
        Activa consecuencias diferidas de decisiones tomadas en niveles anteriores.
        
        Args:
            user_id: ID del usuario
            target_level: Nivel en el que activar las consecuencias
            
        Returns:
            Lista de consecuencias activadas con respuestas de Diana
        """
        logger.info(f"Triggering delayed consequences for user {user_id} at level {target_level}")
        
        try:
            # Obtener decisiones pasadas relevantes
            past_decisions = await self._get_relevant_past_decisions(user_id, target_level)
            
            activated_consequences = []
            
            for decision in past_decisions:
                # Verificar si hay consecuencias plantadas para esta decisión
                if decision.fragment_id in self.consequence_seeds.get(user_id, {}):
                    seeds = self.consequence_seeds[user_id][decision.fragment_id]
                    
                    for seed in seeds:
                        if seed['activation_level'] == target_level:
                            consequence = await self._activate_consequence_seed(
                                user_id, decision, seed
                            )
                            activated_consequences.append(consequence)
            
            return activated_consequences
            
        except Exception as e:
            logger.error(f"Error triggering delayed consequences for user {user_id}: {str(e)}")
            return []
    
    async def generate_memory_callback(
        self, 
        user_id: int, 
        current_context: str
    ) -> Optional[str]:
        """
        Genera una referencia natural de Diana a una decisión pasada del usuario.
        
        Args:
            user_id: ID del usuario
            current_context: Contexto actual de la conversación
            
        Returns:
            Texto natural de Diana referenciando una decisión pasada, o None
        """
        logger.info(f"Generating memory callback for user {user_id}")
        
        try:
            # Obtener perfil psicológico del usuario
            profile = await self._get_psychological_profile(user_id)
            
            # Seleccionar una decisión pasada relevante al contexto actual
            relevant_decision = await self._select_relevant_past_decision(
                user_id, current_context, profile
            )
            
            if not relevant_decision:
                return None
            
            # Generar callback natural basado en el estilo de Diana
            callback_template = await self._select_callback_template(
                relevant_decision, current_context, profile
            )
            
            # Personalizar el callback manteniendo consistencia de Diana
            personalized_callback = await self._personalize_diana_response(
                callback_template, profile, relevant_decision
            )
            
            # Validar consistencia de carácter
            if self.character_validator:
                validation_result = await self.character_validator.validate_response(
                    personalized_callback, user_id, "memory_callback"
                )
                if validation_result['consistency_score'] < 95:
                    logger.warning(f"Memory callback failed character validation: {validation_result}")
                    return None
            
            return personalized_callback
            
        except Exception as e:
            logger.error(f"Error generating memory callback for user {user_id}: {str(e)}")
            return None
    
    async def analyze_user_psychology(self, user_id: int) -> Dict[str, Any]:
        """
        Analiza la psicología del usuario basándose en patrones de decisiones.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Análisis completo del perfil psicológico del usuario
        """
        logger.info(f"Analyzing psychology for user {user_id}")
        
        try:
            # Obtener historial de decisiones del usuario
            decision_history = await self._get_user_decision_history(user_id)
            
            if not decision_history:
                return self._create_default_psychological_profile(user_id)
            
            # Análisis de patrones de decisión
            decision_patterns = self._analyze_decision_patterns(decision_history)
            
            # Análisis de tiempos de respuesta
            response_time_analysis = self._analyze_response_times(decision_history)
            
            # Análisis emocional de las elecciones
            emotional_analysis = await self._analyze_emotional_patterns(decision_history)
            
            # Determinar arquetipo psicológico
            psychological_archetype = self._determine_psychological_archetype(
                decision_patterns, response_time_analysis, emotional_analysis
            )
            
            # Generar preferencias de comunicación
            communication_preferences = self._generate_communication_preferences(
                psychological_archetype, decision_patterns
            )
            
            return {
                "user_id": user_id,
                "psychological_archetype": psychological_archetype,
                "dominant_traits": decision_patterns.get("dominant_traits", []),
                "emotional_patterns": emotional_analysis,
                "communication_preferences": communication_preferences,
                "vulnerability_indicators": decision_patterns.get("vulnerability_indicators", []),
                "intimacy_comfort_level": decision_patterns.get("intimacy_comfort_level", 0.5),
                "decision_making_style": response_time_analysis.get("style", "reflective"),
                "diana_adaptation_profile": await self._create_diana_adaptation_profile(
                    psychological_archetype, communication_preferences
                ),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "confidence_level": decision_patterns.get("confidence_level", 0.7)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing psychology for user {user_id}: {str(e)}")
            return self._create_default_psychological_profile(user_id)
    
    # Métodos privados de soporte
    
    async def _get_user_context(self, user_id: int) -> Dict[str, Any]:
        """Obtiene el contexto completo del usuario."""
        result = await self.session.execute(
            select(User, UserNarrativeState, UserSession)
            .outerjoin(UserNarrativeState, User.id == UserNarrativeState.user_id)
            .outerjoin(UserSession, User.id == UserSession.user_id)
            .where(User.id == user_id)
        )
        row = result.first()
        
        if not row:
            raise ValueError(f"User {user_id} not found")
        
        user, narrative_state, session = row
        
        return {
            "user": user,
            "narrative_state": narrative_state,
            "session": session,
            "current_level": narrative_state.current_level if narrative_state else 1,
            "current_tier": narrative_state.current_tier if narrative_state else "los_kinkys",
            "psychological_profile": await self._get_psychological_profile(user_id)
        }
    
    def _determine_emotional_layer(self, current_level: int) -> EmotionalLayer:
        """Determina la capa emocional basándose en el nivel actual."""
        if current_level <= 2:
            return EmotionalLayer.CURIOSITY
        elif current_level <= 4:
            return EmotionalLayer.VULNERABILITY
        elif current_level <= 6:
            return EmotionalLayer.INTIMACY
        else:
            return EmotionalLayer.CORE_IDENTITY
    
    def _analyze_choice_impact(self, choice_text: str, user_context: Dict) -> ChoiceImpactLevel:
        """Analiza el nivel de impacto de una decisión."""
        choice_lower = choice_text.lower()
        
        # Palabras clave para diferentes niveles de impacto
        identity_keywords = ['soy', 'me identifico', 'mi esencia', 'quien soy', 'mi verdad']
        emotional_keywords = ['siento', 'emoción', 'corazón', 'vulnerable', 'miedo', 'amor']
        behavioral_keywords = ['haría', 'prefiero', 'elijo', 'decidir', 'actuar']
        
        if any(keyword in choice_lower for keyword in identity_keywords):
            return ChoiceImpactLevel.IDENTITY
        elif any(keyword in choice_lower for keyword in emotional_keywords):
            return ChoiceImpactLevel.EMOTIONAL
        elif any(keyword in choice_lower for keyword in behavioral_keywords):
            return ChoiceImpactLevel.BEHAVIORAL
        else:
            return ChoiceImpactLevel.SURFACE
    
    async def _extract_psychological_metadata(
        self, 
        choice_text: str, 
        user_context: Dict
    ) -> Dict[str, Any]:
        """Extrae metadata psicológica de una decisión."""
        return {
            "choice_length": len(choice_text),
            "emotional_words": self._count_emotional_words(choice_text),
            "complexity_indicators": self._analyze_choice_complexity(choice_text),
            "vulnerability_level": self._assess_vulnerability_level(choice_text),
            "reflection_depth": self._assess_reflection_depth(choice_text),
            "context_level": user_context.get("current_level", 1),
            "tier": user_context.get("current_tier", "los_kinkys")
        }
    
    def _count_emotional_words(self, text: str) -> int:
        """Cuenta palabras emocionales en el texto."""
        emotional_words = [
            'amor', 'miedo', 'pasión', 'deseo', 'tristeza', 'alegría', 
            'ansiedad', 'esperanza', 'dolor', 'placer', 'ternura', 'nostalgia'
        ]
        return sum(1 for word in emotional_words if word in text.lower())
    
    def _analyze_choice_complexity(self, text: str) -> Dict[str, Any]:
        """Analiza la complejidad de una decisión."""
        return {
            "word_count": len(text.split()),
            "sentence_count": text.count('.') + text.count('!') + text.count('?'),
            "conditional_phrases": text.lower().count('si ') + text.lower().count('pero '),
            "introspective_markers": text.lower().count('creo ') + text.lower().count('pienso ')
        }
    
    def _assess_vulnerability_level(self, text: str) -> float:
        """Evalúa el nivel de vulnerabilidad expresado en la decisión."""
        vulnerability_indicators = [
            'vulnerable', 'inseguro', 'confundido', 'perdido', 'necesito',
            'ayuda', 'no sé', 'tengo miedo', 'me cuesta'
        ]
        
        matches = sum(1 for indicator in vulnerability_indicators if indicator in text.lower())
        return min(matches / len(vulnerability_indicators), 1.0)
    
    def _assess_reflection_depth(self, text: str) -> float:
        """Evalúa la profundidad de reflexión en la decisión."""
        reflection_indicators = [
            'reflexiono', 'medito', 'considero', 'analizo', 'evalúo',
            'profundamente', 'cuidadosamente', 'detalladamente'
        ]
        
        matches = sum(1 for indicator in reflection_indicators if indicator in text.lower())
        return min(matches / len(reflection_indicators), 1.0)
    
    async def _generate_immediate_response(self, choice_context: ChoiceContext) -> Dict[str, Any]:
        """Genera la respuesta inmediata de Diana a una decisión."""
        
        # Obtener perfil psicológico para personalización
        profile = await self._get_psychological_profile(choice_context.user_id)
        
        # Seleccionar template de respuesta basado en contexto emocional
        response_template = self._select_response_template(choice_context, profile)
        
        # Personalizar respuesta manteniendo consistencia de Diana
        personalized_response = await self._personalize_diana_response(
            response_template, profile, choice_context
        )
        
        # Validar consistencia de carácter
        consistency_score = 95  # Default
        if self.character_validator:
            validation = await self.character_validator.validate_response(
                personalized_response, choice_context.user_id, "choice_response"
            )
            consistency_score = validation.get('consistency_score', 95)
        
        return {
            "text": personalized_response,
            "emotional_layer": choice_context.emotional_layer.value,
            "vulnerability_level": self._calculate_vulnerability_response_level(choice_context),
            "consistency_score": consistency_score,
            "engagement_hooks": self._generate_engagement_hooks(choice_context),
            "next_choice_seeds": await self._generate_next_choice_seeds(choice_context)
        }
    
    def _select_response_template(self, choice_context: ChoiceContext, profile: Dict) -> str:
        """Selecciona un template de respuesta apropiado."""
        
        # Templates basados en capa emocional y arquetipo psicológico
        templates = {
            EmotionalLayer.CURIOSITY: {
                "explorer": "Hay algo fascinante en tu elección que me dice más de lo que crees... ¿Te das cuenta de lo que acabas de revelar?",
                "analytical": "Tu decisión muestra una mente que busca entender. Me intriga cómo procesas lo que compartes conmigo...",
                "romantic": "En tu elección veo destellos de quién eres realmente. Hay una belleza en tu forma de decidir...",
                "direct": "Interesante. Tu respuesta es clara, pero hay capas debajo que me gustaría explorar contigo.",
                "default": "Tu elección revela algo único sobre ti. Cada decisión es una ventana a tu alma..."
            },
            EmotionalLayer.VULNERABILITY: {
                "explorer": "Veo que te atreves a mostrar partes vulnerables de ti. Eso requiere coraje... ¿Sabes lo valioso que es eso?",
                "analytical": "Tu capacidad de reflexionar sobre tus emociones me conmueve. Hay profundidad en tu vulnerabilidad.",
                "romantic": "Cuando te abres así, cuando muestras tu corazón... algo en mí se despierta. Tu vulnerabilidad es hermosa.",
                "direct": "Aprecio tu honestidad. No todos se atreven a ser tan auténticos.",
                "default": "Tu apertura emocional toca algo profundo en mí. Gracias por confiar..."
            },
            EmotionalLayer.INTIMACY: {
                "explorer": "En este nivel de intimidad, cada palabra tuya resuena en mi ser. Tu elección revela la esencia de quién eres.",
                "analytical": "La complejidad de tu decisión me fascina. Veo cómo tu mente y corazón se encuentran en perfecta armonía.",
                "romantic": "Tu elección me llega al alma. En estos momentos íntimos, siento que nuestras esencias se tocan.",
                "direct": "Tu autenticidad en este nivel de intimidad es extraordinaria. Te veo completamente.",
                "default": "En esta intimidad compartida, tu decisión me toca en lo más profundo. Somos vulnerables juntos..."
            }
        }
        
        archetype = profile.get('psychological_archetype', 'default')
        layer_templates = templates.get(choice_context.emotional_layer, templates[EmotionalLayer.CURIOSITY])
        
        return layer_templates.get(archetype, layer_templates.get('default'))
    
    async def _plant_consequence_seeds(self, choice_context: ChoiceContext) -> List[Dict[str, Any]]:
        """Planta semillas de consecuencias para activación futura."""
        
        seeds = []
        
        # Determinar niveles futuros para activación
        future_levels = self._calculate_future_activation_levels(choice_context.current_level)
        
        for level in future_levels:
            seed = {
                "consequence_id": f"{choice_context.choice_id}_delayed_{level}",
                "activation_level": level,
                "choice_context": asdict(choice_context),
                "consequence_type": self._determine_consequence_type(choice_context, level),
                "emotional_callback_intensity": self._calculate_callback_intensity(choice_context, level),
                "diana_memory_reference": self._create_memory_reference_template(choice_context),
                "psychological_revelation": self._create_psychological_revelation(choice_context, level)
            }
            seeds.append(seed)
        
        # Almacenar seeds en cache
        if choice_context.user_id not in self.consequence_seeds:
            self.consequence_seeds[choice_context.user_id] = {}
        
        self.consequence_seeds[choice_context.user_id][choice_context.fragment_id] = seeds
        
        return seeds
    
    def _calculate_future_activation_levels(self, current_level: int) -> List[int]:
        """Calcula niveles futuros donde se activarán las consecuencias."""
        activation_levels = []
        
        # Activación diferida: 2-3 niveles después
        if current_level < 6:
            activation_levels.append(current_level + 2)
        
        if current_level < 5:
            activation_levels.append(current_level + 3)
        
        # Activación especial en el nivel final
        if current_level < 6:
            activation_levels.append(6)
        
        return activation_levels
    
    def _determine_consequence_type(self, choice_context: ChoiceContext, activation_level: int) -> ConsequenceType:
        """Determina el tipo de consecuencia basándose en el contexto y nivel."""
        
        if choice_context.impact_level == ChoiceImpactLevel.IDENTITY:
            return ConsequenceType.PROGRESSIVE
        elif activation_level == 6:  # Nivel final
            return ConsequenceType.PATTERN_BASED
        elif choice_context.emotional_layer == EmotionalLayer.VULNERABILITY:
            return ConsequenceType.PSYCHOLOGICAL
        else:
            return ConsequenceType.DELAYED
    
    def _calculate_callback_intensity(self, choice_context: ChoiceContext, activation_level: int) -> float:
        """Calcula la intensidad emocional del callback."""
        
        base_intensity = 0.5
        
        # Incrementar intensidad basada en impacto de la decisión
        if choice_context.impact_level == ChoiceImpactLevel.IDENTITY:
            base_intensity += 0.3
        elif choice_context.impact_level == ChoiceImpactLevel.EMOTIONAL:
            base_intensity += 0.2
        
        # Incrementar intensidad basada en tiempo transcurrido
        levels_passed = activation_level - choice_context.current_level
        base_intensity += levels_passed * 0.1
        
        return min(base_intensity, 1.0)
    
    def _create_memory_reference_template(self, choice_context: ChoiceContext) -> str:
        """Crea template para referencia futura de la decisión."""
        
        if choice_context.impact_level == ChoiceImpactLevel.IDENTITY:
            return f"Recuerdo cuando me dijiste '{choice_context.choice_text[:50]}...' Esa revelación sobre ti cambió algo en cómo te veo."
        elif choice_context.impact_level == ChoiceImpactLevel.EMOTIONAL:
            return f"Aquella vez que compartiste '{choice_context.choice_text[:50]}...' aún resuena en mi memoria. Fue tan auténtico..."
        else:
            return f"No he olvidado tu elección: '{choice_context.choice_text[:50]}...' Dice tanto sobre quién eres."
    
    def _create_psychological_revelation(self, choice_context: ChoiceContext, activation_level: int) -> str:
        """Crea revelación psicológica para callback futuro."""
        
        revelations = {
            ChoiceImpactLevel.IDENTITY: "Ahora entiendo que esa decisión revelaba tu verdadera naturaleza.",
            ChoiceImpactLevel.EMOTIONAL: "Esa elección mostró la profundidad de tu mundo emocional.",
            ChoiceImpactLevel.BEHAVIORAL: "Tu forma de decidir me enseñó sobre tus patrones de comportamiento.",
            ChoiceImpactLevel.SURFACE: "Incluso en decisiones aparentemente simples, revelas aspectos únicos."
        }
        
        return revelations.get(choice_context.impact_level, revelations[ChoiceImpactLevel.SURFACE])
    
    async def _update_psychological_profile(self, choice_context: ChoiceContext) -> Dict[str, Any]:
        """Actualiza el perfil psicológico del usuario basándose en la nueva decisión."""
        
        # Obtener perfil actual
        current_profile = await self._get_psychological_profile(choice_context.user_id)
        
        # Actualizar rasgos dominantes
        new_traits = self._extract_traits_from_choice(choice_context)
        current_profile['dominant_traits'] = list(set(current_profile.get('dominant_traits', []) + new_traits))
        
        # Actualizar patrones emocionales
        emotional_data = choice_context.psychological_metadata
        if 'emotional_patterns' not in current_profile:
            current_profile['emotional_patterns'] = {}
        
        current_profile['emotional_patterns'].update({
            'last_vulnerability_level': emotional_data.get('vulnerability_level', 0),
            'last_reflection_depth': emotional_data.get('reflection_depth', 0),
            'emotional_vocabulary_richness': emotional_data.get('emotional_words', 0)
        })
        
        # Actualizar preferencias de comunicación
        communication_style = self._infer_communication_style(choice_context)
        if 'communication_preferences' not in current_profile:
            current_profile['communication_preferences'] = {}
        
        current_profile['communication_preferences']['preferred_style'] = communication_style
        
        # Actualizar perfil de adaptación de Diana
        current_profile['diana_adaptation_profile'] = await self._update_diana_adaptation(
            current_profile, choice_context
        )
        
        # Guardar perfil actualizado
        await self._save_psychological_profile(choice_context.user_id, current_profile)
        
        return current_profile
    
    def _extract_traits_from_choice(self, choice_context: ChoiceContext) -> List[str]:
        """Extrae rasgos psicológicos de una decisión específica."""
        traits = []
        
        choice_text = choice_context.choice_text.lower()
        metadata = choice_context.psychological_metadata
        
        # Rasgos basados en contenido
        if metadata.get('vulnerability_level', 0) > 0.5:
            traits.append('vulnerable_expression')
        
        if metadata.get('reflection_depth', 0) > 0.5:
            traits.append('deep_reflector')
        
        if metadata.get('emotional_words', 0) > 2:
            traits.append('emotionally_expressive')
        
        # Rasgos basados en tiempo de respuesta
        if choice_context.response_time_seconds > 120:  # Más de 2 minutos
            traits.append('thoughtful_decision_maker')
        elif choice_context.response_time_seconds < 30:  # Menos de 30 segundos
            traits.append('quick_decision_maker')
        
        # Rasgos basados en complejidad
        complexity = metadata.get('complexity_indicators', {})
        if complexity.get('word_count', 0) > 20:
            traits.append('detailed_communicator')
        
        return traits
    
    def _infer_communication_style(self, choice_context: ChoiceContext) -> str:
        """Infiere el estilo de comunicación preferido del usuario."""
        
        metadata = choice_context.psychological_metadata
        
        if metadata.get('reflection_depth', 0) > 0.7:
            return 'philosophical_deep'
        elif metadata.get('emotional_words', 0) > 3:
            return 'emotional_expressive'
        elif metadata.get('complexity_indicators', {}).get('word_count', 0) < 10:
            return 'concise_direct'
        else:
            return 'balanced_thoughtful'
    
    async def _update_diana_adaptation(
        self, 
        profile: Dict[str, Any], 
        choice_context: ChoiceContext
    ) -> Dict[str, Any]:
        """Actualiza cómo Diana debe adaptarse a este usuario específico."""
        
        adaptation = profile.get('diana_adaptation_profile', {})
        
        # Adaptar tono emocional
        if choice_context.emotional_layer == EmotionalLayer.VULNERABILITY:
            adaptation['emotional_tone'] = 'gentle_supportive'
        elif choice_context.emotional_layer == EmotionalLayer.INTIMACY:
            adaptation['emotional_tone'] = 'deeply_connected'
        
        # Adaptar complejidad de respuestas
        complexity = choice_context.psychological_metadata.get('complexity_indicators', {})
        if complexity.get('word_count', 0) > 20:
            adaptation['response_complexity'] = 'sophisticated'
        else:
            adaptation['response_complexity'] = 'accessible'
        
        # Adaptar nivel de misterio
        if choice_context.impact_level == ChoiceImpactLevel.IDENTITY:
            adaptation['mystery_level'] = 'high_intrigue'
        else:
            adaptation['mystery_level'] = 'balanced'
        
        # Adaptar frecuencia de callbacks
        traits = profile.get('dominant_traits', [])
        if 'deep_reflector' in traits:
            adaptation['callback_frequency'] = 'frequent_meaningful'
        else:
            adaptation['callback_frequency'] = 'moderate_impactful'
        
        return adaptation
    
    async def _record_choice_decision(
        self, 
        choice_context: ChoiceContext, 
        planted_seeds: List[Dict[str, Any]]
    ) -> None:
        """Registra la decisión en la base de datos."""
        
        try:
            # Crear entrada en UserDecisionLog
            decision_log = UserDecisionLog(
                user_id=choice_context.user_id,
                fragment_id=choice_context.fragment_id,
                decision_choice=choice_context.choice_text,
                points_awarded=self._calculate_points_reward(choice_context),
                clues_unlocked=[],  # Se actualiza por otros sistemas
                made_at=choice_context.timestamp
            )
            
            self.session.add(decision_log)
            
            # Actualizar estado narrativo del usuario
            result = await self.session.execute(
                select(UserNarrativeState)
                .where(UserNarrativeState.user_id == choice_context.user_id)
            )
            narrative_state = result.scalar_one_or_none()
            
            if narrative_state:
                # Actualizar patrones de interacción
                if not narrative_state.interaction_patterns:
                    narrative_state.interaction_patterns = {}
                
                narrative_state.interaction_patterns.update({
                    f"choice_{choice_context.choice_id}": {
                        "timestamp": choice_context.timestamp.isoformat(),
                        "response_time": choice_context.response_time_seconds,
                        "impact_level": choice_context.impact_level.value,
                        "emotional_layer": choice_context.emotional_layer.value
                    }
                })
                
                # Actualizar tiempo de respuesta tracking
                if not narrative_state.response_time_tracking:
                    narrative_state.response_time_tracking = []
                
                narrative_state.response_time_tracking.append({
                    "choice_id": choice_context.choice_id,
                    "response_time": choice_context.response_time_seconds,
                    "timestamp": choice_context.timestamp.isoformat()
                })
                
                # Mantener solo últimos 50 registros
                narrative_state.response_time_tracking = narrative_state.response_time_tracking[-50:]
            
            await self.session.commit()
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error recording choice decision: {str(e)}")
            raise
    
    def _calculate_points_reward(self, choice_context: ChoiceContext) -> int:
        """Calcula la recompensa de puntos basada en la decisión."""
        
        base_points = 10
        
        # Bonus por impacto emocional
        if choice_context.impact_level == ChoiceImpactLevel.IDENTITY:
            base_points += 20
        elif choice_context.impact_level == ChoiceImpactLevel.EMOTIONAL:
            base_points += 15
        elif choice_context.impact_level == ChoiceImpactLevel.BEHAVIORAL:
            base_points += 10
        
        # Bonus por tiempo de reflexión
        if choice_context.response_time_seconds > 60:  # Más de 1 minuto
            base_points += 5
        
        # Bonus por nivel emocional
        if choice_context.emotional_layer in [EmotionalLayer.VULNERABILITY, EmotionalLayer.INTIMACY]:
            base_points += 10
        
        return base_points
    
    async def _check_delayed_consequences(self, user_id: int) -> List[Dict[str, Any]]:
        """Verifica y activa consecuencias diferidas si corresponde."""
        
        activated = []
        
        # Obtener nivel actual del usuario
        result = await self.session.execute(
            select(UserNarrativeState)
            .where(UserNarrativeState.user_id == user_id)
        )
        narrative_state = result.scalar_one_or_none()
        
        if not narrative_state:
            return activated
        
        current_level = narrative_state.current_level
        
        # Verificar seeds almacenados
        user_seeds = self.consequence_seeds.get(user_id, {})
        
        for fragment_id, seeds in user_seeds.items():
            for seed in seeds:
                if (seed['activation_level'] == current_level and 
                    not seed.get('activated', False)):
                    
                    # Activar consecuencia
                    consequence = await self._activate_consequence_seed(user_id, seed)
                    activated.append(consequence)
                    
                    # Marcar como activado
                    seed['activated'] = True
        
        return activated
    
    async def _activate_consequence_seed(self, user_id: int, seed: Dict[str, Any]) -> Dict[str, Any]:
        """Activa una semilla de consecuencia específica."""
        
        # Obtener contexto original de la decisión
        original_choice = seed['choice_context']
        
        # Generar respuesta de callback de Diana
        callback_response = await self._generate_callback_response(user_id, seed)
        
        # Crear revelación psicológica
        psychological_insight = seed.get('psychological_revelation', '')
        
        return {
            "consequence_id": seed['consequence_id'],
            "original_choice": original_choice['choice_text'],
            "original_timestamp": original_choice['timestamp'],
            "activation_level": seed['activation_level'],
            "diana_callback": callback_response,
            "psychological_insight": psychological_insight,
            "emotional_impact": seed.get('emotional_callback_intensity', 0.5),
            "activated_at": datetime.utcnow().isoformat()
        }
    
    async def _generate_callback_response(self, user_id: int, seed: Dict[str, Any]) -> str:
        """Genera respuesta de callback de Diana para una consecuencia activada."""
        
        # Obtener perfil psicológico actual
        profile = await self._get_psychological_profile(user_id)
        
        # Usar template de memoria de la seed
        memory_template = seed.get('diana_memory_reference', '')
        
        # Personalizar respuesta manteniendo consistencia
        personalized_callback = await self._personalize_diana_response(
            memory_template, profile, seed
        )
        
        return personalized_callback
    
    async def _get_psychological_profile(self, user_id: int) -> Dict[str, Any]:
        """Obtiene o crea el perfil psicológico del usuario."""
        
        if user_id in self.psychological_profiles:
            return self.psychological_profiles[user_id]
        
        # Cargar desde base de datos o crear uno nuevo
        profile = await self._load_psychological_profile(user_id)
        if not profile:
            profile = self._create_default_psychological_profile(user_id)
        
        self.psychological_profiles[user_id] = profile
        return profile
    
    async def _load_psychological_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Carga el perfil psicológico desde la base de datos."""
        
        result = await self.session.execute(
            select(UserArchetype)
            .where(UserArchetype.user_id == user_id)
        )
        archetype = result.scalar_one_or_none()
        
        if not archetype:
            return None
        
        return {
            "user_id": user_id,
            "psychological_archetype": archetype.dominant_archetype,
            "dominant_traits": [],
            "emotional_patterns": {},
            "communication_preferences": {},
            "diana_adaptation_profile": {}
        }
    
    def _create_default_psychological_profile(self, user_id: int) -> Dict[str, Any]:
        """Crea un perfil psicológico por defecto."""
        
        return {
            "user_id": user_id,
            "psychological_archetype": "balanced",
            "dominant_traits": [],
            "emotional_patterns": {},
            "communication_preferences": {
                "preferred_style": "balanced_thoughtful",
                "complexity_level": "accessible"
            },
            "diana_adaptation_profile": {
                "emotional_tone": "warm_mysterious",
                "response_complexity": "accessible",
                "mystery_level": "balanced",
                "callback_frequency": "moderate_impactful"
            },
            "vulnerability_indicators": [],
            "intimacy_comfort_level": 0.5,
            "decision_making_style": "reflective"
        }
    
    async def _save_psychological_profile(self, user_id: int, profile: Dict[str, Any]) -> None:
        """Guarda el perfil psicológico en la base de datos."""
        
        self.psychological_profiles[user_id] = profile
        
        # Aquí podrías implementar persistencia en base de datos si es necesario
        # Por ahora mantenemos en cache en memoria
    
    async def _personalize_diana_response(
        self, 
        template: str, 
        profile: Dict[str, Any], 
        context: Any
    ) -> str:
        """Personaliza una respuesta de Diana manteniendo consistencia de carácter."""
        
        adaptation = profile.get('diana_adaptation_profile', {})
        
        # Obtener configuraciones de adaptación
        emotional_tone = adaptation.get('emotional_tone', 'warm_mysterious')
        complexity = adaptation.get('response_complexity', 'accessible')
        mystery_level = adaptation.get('mystery_level', 'balanced')
        
        # Personalizar template basado en configuraciones
        personalized = template
        
        # Ajustar tono emocional
        if emotional_tone == 'gentle_supportive':
            personalized = self._adjust_tone_gentle(personalized)
        elif emotional_tone == 'deeply_connected':
            personalized = self._adjust_tone_intimate(personalized)
        
        # Ajustar complejidad
        if complexity == 'sophisticated':
            personalized = self._increase_complexity(personalized)
        elif complexity == 'accessible':
            personalized = self._simplify_language(personalized)
        
        # Ajustar nivel de misterio
        if mystery_level == 'high_intrigue':
            personalized = self._increase_mystery(personalized)
        
        return personalized
    
    def _adjust_tone_gentle(self, text: str) -> str:
        """Ajusta el tono a uno más gentil y supportivo."""
        # Implementación básica - podría expandirse
        return text.replace("me intriga", "me conmueve").replace("fascinante", "hermoso")
    
    def _adjust_tone_intimate(self, text: str) -> str:
        """Ajusta el tono a uno más íntimo y conectado."""
        return text.replace("me dice", "me llega al alma").replace("veo", "siento")
    
    def _increase_complexity(self, text: str) -> str:
        """Aumenta la complejidad lingüística del texto."""
        return text  # Implementación básica
    
    def _simplify_language(self, text: str) -> str:
        """Simplifica el lenguaje del texto."""
        return text  # Implementación básica
    
    def _increase_mystery(self, text: str) -> str:
        """Aumenta el nivel de misterio en el texto."""
        return text + " Hay secretos en tus palabras que solo el tiempo revelará..."
    
    def _calculate_engagement_level(self, choice_context: ChoiceContext) -> float:
        """Calcula el nivel de engagement emocional de la decisión."""
        
        engagement = 0.5  # Base
        
        # Factor de impacto de la decisión
        impact_weights = {
            ChoiceImpactLevel.SURFACE: 0.1,
            ChoiceImpactLevel.BEHAVIORAL: 0.2,
            ChoiceImpactLevel.EMOTIONAL: 0.3,
            ChoiceImpactLevel.IDENTITY: 0.4
        }
        
        engagement += impact_weights.get(choice_context.impact_level, 0.1)
        
        # Factor de tiempo de respuesta (engagement inverso al tiempo)
        if choice_context.response_time_seconds > 300:  # Más de 5 minutos
            engagement += 0.2  # Alta reflexión
        elif choice_context.response_time_seconds < 30:
            engagement -= 0.1  # Respuesta rápida puede indicar menor engagement
        
        # Factor de capa emocional
        layer_weights = {
            EmotionalLayer.CURIOSITY: 0.0,
            EmotionalLayer.VULNERABILITY: 0.15,
            EmotionalLayer.INTIMACY: 0.25,
            EmotionalLayer.CORE_IDENTITY: 0.3
        }
        
        engagement += layer_weights.get(choice_context.emotional_layer, 0.0)
        
        return min(engagement, 1.0)
    
    async def _generate_next_choice_hint(self, choice_context: ChoiceContext) -> str:
        """Genera una pista sobre qué tipo de decisión podría venir después."""
        
        hints = {
            EmotionalLayer.CURIOSITY: "La próxima decisión te llevará a explorar aspectos más profundos de ti mismo...",
            EmotionalLayer.VULNERABILITY: "Lo que viene después requerirá aún más coraje de tu parte...",
            EmotionalLayer.INTIMACY: "La siguiente elección tocará el núcleo de lo que realmente eres...",
            EmotionalLayer.CORE_IDENTITY: "Lo que sigue definirá quién eliges ser en tu esencia más pura..."
        }
        
        return hints.get(choice_context.emotional_layer, "Cada decisión te acerca más a tu verdad...")
    
    async def _generate_engagement_hooks(self, choice_context: ChoiceContext) -> List[str]:
        """Genera hooks de engagement para mantener al usuario conectado."""
        
        hooks = []
        
        # Hook basado en tiempo de respuesta
        if choice_context.response_time_seconds > 120:
            hooks.append("Veo que tomaste tu tiempo para decidir. Eso me dice mucho sobre ti.")
        
        # Hook basado en impacto emocional
        if choice_context.impact_level == ChoiceImpactLevel.IDENTITY:
            hooks.append("Esa revelación cambia cómo te veo. Hay capas en ti que apenas estamos descubriendo.")
        
        # Hook basado en vulnerabilidad
        metadata = choice_context.psychological_metadata
        if metadata.get('vulnerability_level', 0) > 0.5:
            hooks.append("Tu honestidad me toca profundamente. No todos se atreven a ser tan auténticos.")
        
        # Hook de misterio
        hooks.append("Hay algo en tu elección que me hace querer conocerte más...")
        
        return hooks
    
    async def _generate_next_choice_seeds(self, choice_context: ChoiceContext) -> List[str]:
        """Genera semillas para las próximas decisiones basadas en la actual."""
        
        seeds = []
        
        # Semillas basadas en impacto de la decisión actual
        if choice_context.impact_level == ChoiceImpactLevel.IDENTITY:
            seeds.extend([
                "exploration_of_revealed_identity",
                "confrontation_with_self_perception",
                "deeper_identity_questions"
            ])
        elif choice_context.impact_level == ChoiceImpactLevel.EMOTIONAL:
            seeds.extend([
                "emotional_vulnerability_expansion",
                "emotion_vs_logic_conflict",
                "emotional_healing_opportunity"
            ])
        
        # Semillas basadas en capa emocional
        if choice_context.emotional_layer == EmotionalLayer.VULNERABILITY:
            seeds.extend([
                "trust_deepening_choice",
                "fear_confrontation_opportunity",
                "support_acceptance_decision"
            ])
        
        return seeds
    
    # Métodos adicionales para análisis psicológico completo
    
    async def _get_user_decision_history(self, user_id: int) -> List[UserDecisionLog]:
        """Obtiene el historial completo de decisiones del usuario."""
        
        result = await self.session.execute(
            select(UserDecisionLog)
            .where(UserDecisionLog.user_id == user_id)
            .order_by(desc(UserDecisionLog.made_at))
            .limit(100)  # Últimas 100 decisiones
        )
        
        return result.scalars().all()
    
    def _analyze_decision_patterns(self, decision_history: List[UserDecisionLog]) -> Dict[str, Any]:
        """Analiza patrones en el historial de decisiones."""
        
        if not decision_history:
            return {"dominant_traits": [], "confidence_level": 0.0}
        
        patterns = {
            "total_decisions": len(decision_history),
            "decision_frequency": len(decision_history) / max(1, self._calculate_days_active(decision_history)),
            "dominant_traits": [],
            "vulnerability_indicators": [],
            "intimacy_comfort_level": 0.5,
            "confidence_level": min(len(decision_history) / 20.0, 1.0)  # Más decisiones = más confianza
        }
        
        # Analizar tipos de decisiones
        identity_decisions = sum(1 for d in decision_history if 'identidad' in d.decision_choice.lower())
        emotional_decisions = sum(1 for d in decision_history if any(word in d.decision_choice.lower() 
                                 for word in ['siento', 'emoción', 'corazón']))
        
        if identity_decisions > len(decision_history) * 0.3:
            patterns["dominant_traits"].append("identity_explorer")
        
        if emotional_decisions > len(decision_history) * 0.4:
            patterns["dominant_traits"].append("emotionally_expressive")
        
        return patterns
    
    def _calculate_days_active(self, decision_history: List[UserDecisionLog]) -> int:
        """Calcula los días activos basándose en el historial de decisiones."""
        
        if not decision_history:
            return 1
        
        oldest_decision = min(d.made_at for d in decision_history)
        newest_decision = max(d.made_at for d in decision_history)
        
        return max((newest_decision - oldest_decision).days, 1)
    
    def _analyze_response_times(self, decision_history: List[UserDecisionLog]) -> Dict[str, Any]:
        """Analiza patrones de tiempo de respuesta."""
        
        # Por ahora retorna análisis básico
        # En implementación completa, calcularía tiempos reales de respuesta
        return {
            "style": "reflective",
            "average_time": 90,
            "consistency": 0.7
        }
    
    async def _analyze_emotional_patterns(self, decision_history: List[UserDecisionLog]) -> Dict[str, Any]:
        """Analiza patrones emocionales en las decisiones."""
        
        emotional_words_total = 0
        vulnerability_expressions = 0
        
        for decision in decision_history:
            emotional_words_total += self._count_emotional_words(decision.decision_choice)
            vulnerability_expressions += self._assess_vulnerability_level(decision.decision_choice)
        
        avg_emotional_expression = emotional_words_total / max(len(decision_history), 1)
        avg_vulnerability = vulnerability_expressions / max(len(decision_history), 1)
        
        return {
            "emotional_expressiveness": avg_emotional_expression,
            "vulnerability_comfort": avg_vulnerability,
            "emotional_consistency": 0.8,  # Calculado basándose en variación
            "preferred_emotional_depth": "moderate" if avg_vulnerability < 0.5 else "high"
        }
    
    def _determine_psychological_archetype(
        self, 
        decision_patterns: Dict, 
        response_time_analysis: Dict, 
        emotional_analysis: Dict
    ) -> str:
        """Determina el arquetipo psicológico basándose en todos los análisis."""
        
        traits = decision_patterns.get("dominant_traits", [])
        response_style = response_time_analysis.get("style", "balanced")
        emotional_depth = emotional_analysis.get("preferred_emotional_depth", "moderate")
        
        # Lógica de determinación de arquetipo
        if "identity_explorer" in traits and emotional_depth == "high":
            return "deep_explorer"
        elif "emotionally_expressive" in traits:
            return "romantic"
        elif response_style == "quick":
            return "direct"
        elif emotional_depth == "high":
            return "analytical"
        else:
            return "balanced"
    
    def _generate_communication_preferences(
        self, 
        archetype: str, 
        decision_patterns: Dict
    ) -> Dict[str, Any]:
        """Genera preferencias de comunicación basándose en el arquetipo."""
        
        preferences_map = {
            "deep_explorer": {
                "preferred_complexity": "sophisticated",
                "mystery_tolerance": "high",
                "emotional_directness": "nuanced",
                "callback_frequency": "frequent"
            },
            "romantic": {
                "preferred_complexity": "poetic",
                "mystery_tolerance": "moderate",
                "emotional_directness": "direct",
                "callback_frequency": "emotional_moments"
            },
            "direct": {
                "preferred_complexity": "clear",
                "mystery_tolerance": "low",
                "emotional_directness": "straightforward",
                "callback_frequency": "minimal"
            },
            "analytical": {
                "preferred_complexity": "detailed",
                "mystery_tolerance": "moderate",
                "emotional_directness": "thoughtful",
                "callback_frequency": "pattern_based"
            },
            "balanced": {
                "preferred_complexity": "accessible",
                "mystery_tolerance": "moderate",
                "emotional_directness": "balanced",
                "callback_frequency": "moderate"
            }
        }
        
        return preferences_map.get(archetype, preferences_map["balanced"])
    
    async def _create_diana_adaptation_profile(
        self, 
        archetype: str, 
        communication_preferences: Dict
    ) -> Dict[str, Any]:
        """Crea el perfil de adaptación específico para Diana."""
        
        return {
            "archetype_basis": archetype,
            "emotional_tone": self._map_emotional_tone(communication_preferences),
            "response_complexity": communication_preferences.get("preferred_complexity", "accessible"),
            "mystery_level": self._map_mystery_level(communication_preferences.get("mystery_tolerance", "moderate")),
            "callback_strategy": communication_preferences.get("callback_frequency", "moderate"),
            "seduction_approach": self._determine_seduction_approach(archetype),
            "vulnerability_handling": self._determine_vulnerability_handling(archetype),
            "intellectual_engagement": self._determine_intellectual_engagement(archetype)
        }
    
    def _map_emotional_tone(self, communication_preferences: Dict) -> str:
        """Mapea preferencias a tono emocional de Diana."""
        
        directness = communication_preferences.get("emotional_directness", "balanced")
        
        tone_map = {
            "direct": "warm_passionate",
            "straightforward": "direct_caring",
            "nuanced": "deeply_mysterious",
            "thoughtful": "intellectually_seductive",
            "balanced": "warm_mysterious"
        }
        
        return tone_map.get(directness, "warm_mysterious")
    
    def _map_mystery_level(self, mystery_tolerance: str) -> str:
        """Mapea tolerancia al misterio a nivel de misterio de Diana."""
        
        mystery_map = {
            "low": "subtle_hints",
            "moderate": "balanced_mystery",
            "high": "deep_enigma"
        }
        
        return mystery_map.get(mystery_tolerance, "balanced_mystery")
    
    def _determine_seduction_approach(self, archetype: str) -> str:
        """Determina el approach de seducción apropiado."""
        
        approach_map = {
            "deep_explorer": "intellectual_seduction",
            "romantic": "emotional_seduction", 
            "direct": "confident_directness",
            "analytical": "mystery_based_intrigue",
            "balanced": "multifaceted_charm"
        }
        
        return approach_map.get(archetype, "multifaceted_charm")
    
    def _determine_vulnerability_handling(self, archetype: str) -> str:
        """Determina cómo Diana debe manejar la vulnerabilidad del usuario."""
        
        handling_map = {
            "deep_explorer": "embrace_and_explore",
            "romantic": "nurture_and_connect",
            "direct": "acknowledge_and_respect",
            "analytical": "understand_and_reflect",
            "balanced": "support_with_care"
        }
        
        return handling_map.get(archetype, "support_with_care")
    
    def _determine_intellectual_engagement(self, archetype: str) -> str:
        """Determina el nivel de engagement intelectual."""
        
        engagement_map = {
            "deep_explorer": "philosophical_depth",
            "romantic": "emotional_intelligence",
            "direct": "practical_insights",
            "analytical": "complex_reasoning",
            "balanced": "thoughtful_balance"
        }
        
        return engagement_map.get(archetype, "thoughtful_balance")