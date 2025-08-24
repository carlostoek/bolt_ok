# Componentes de Implementación Lucien-Diana

Este documento complementa el Plan de Implementación principal y proporciona detalles técnicos adicionales sobre los principales componentes a desarrollar.

## 1. Extensiones de Base de Datos

### 1.1 Extensión de UserNarrativeState

```python
# Extensión del modelo UserNarrativeState en database/narrative_unified.py

class UserNarrativeState(Base):
    # Campos existentes...
    
    # Nuevos campos para Lucien-Diana
    lucien_trust_level = Column(Float, default=0.0, comment="Nivel de confianza con Lucien (0.0-1.0)")
    lucien_interaction_count = Column(Integer, default=0, comment="Número de interacciones con Lucien")
    diana_appearances = Column(JSON, default=list, comment="Lista de apariciones de Diana con timestamp y contexto")
    narrative_level = Column(Integer, default=1, comment="Nivel narrativo actual (1-6)")
    archetype = Column(String, nullable=True, comment="Arquetipo identificado del usuario")
    
    # Campos auxiliares para sistema cuántico
    quantum_effects = Column(JSON, default=list, comment="Lista de efectos cuánticos aplicados")
    modified_fragments = Column(JSON, default=list, comment="Fragmentos modificados por efectos cuánticos")
```

### 1.2 Extensión de NarrativeFragment

```python
# Extensión del modelo NarrativeFragment en database/narrative_unified.py

class NarrativeFragment(Base):
    # Campos existentes...
    
    # Nuevos campos para Lucien-Diana
    presenter = Column(String, default="lucien", comment="Quién presenta el fragmento: lucien, diana, o ambos")
    diana_appearance_threshold = Column(Float, default=1.0, comment="Nivel mínimo de confianza para aparición de Diana")
    narrative_level_required = Column(Integer, default=1, comment="Nivel narrativo mínimo requerido")
    
    # Campos para fragmentos temporales
    is_temporal = Column(Boolean, default=False, comment="Indica si es un fragmento temporal")
    temporal_weekdays = Column(JSON, nullable=True, comment="Días de la semana disponibles (0-6)")
    temporal_hours = Column(JSON, nullable=True, comment="Horas del día disponibles (0-23)")
    temporal_expiration_minutes = Column(Integer, nullable=True, comment="Minutos hasta expirar desde activación")
    
    # Campos para fragmentos cuánticos
    is_quantum = Column(Boolean, default=False, comment="Puede cambiar retroactivamente")
    quantum_trigger_type = Column(String, nullable=True, comment="Tipo de disparador que puede modificarlo")
    alternative_versions = Column(JSON, default=dict, comment="Versiones alternativas del fragmento")
```

## 2. LucienService

### 2.1 Estructura y Funcionalidades

```python
# services/lucien_service.py

from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import random

from services.notification_service import NotificationService, NotificationPriority
from database.models import User
from database.narrative_unified import UserNarrativeState, NarrativeFragment

class LucienPersonality:
    """Configuración de personalidad de Lucien."""
    
    FORMAL_EXPRESSIONS = [
        "Si me permite observar...",
        "Permítame señalar que...",
        "Debo indicar que...",
        "Es mi deber informarle que...",
        "Si puedo ofrecer mi perspectiva..."
    ]
    
    GREETING_TEMPLATES = {
        "initial": "Permítame presentarme: Lucien, guardián de los secretos de Diana... y evaluador de quienes desean conocerla.",
        "return": "Bienvenido de nuevo. Lucien a su servicio.",
        "level_up": "Su progreso es... notable. Permítame felicitarle por alcanzar un nuevo nivel de confianza."
    }
    
    CHALLENGE_TEMPLATES = {
        "observation": "Su capacidad de observación será evaluada. Le invito a examinar detenidamente {subject}.",
        "deduction": "Este desafío requerirá sus habilidades deductivas. Analice los detalles presentados y extraiga conclusiones.",
        "connection": "Le presento un ejercicio de conexiones. Identifique el hilo común entre estos elementos aparentemente dispares."
    }
    
    DIANA_APPEARANCE_COMMENTS = [
        "Fascinante... Diana no suele mostrar interés tan directamente. Parece que algo en ti captó su atención.",
        "Eso fue... inusual. Diana rara vez se manifiesta ante desconocidos.",
        "Curioso. Parece que Diana encuentra algo intrigante en su perspectiva.",
        "Noto que ha captado el interés de Diana. No es algo que ocurra frecuentemente."
    ]
    
    @staticmethod
    def get_formal_response(context: str, success_level: float = None) -> str:
        """Genera una respuesta formal estilo mayordomo basada en contexto."""
        intro = random.choice(LucienPersonality.FORMAL_EXPRESSIONS)
        
        if success_level is not None:
            if success_level > 0.8:
                return f"{intro} Su desempeño ha sido ejemplar. {context}"
            elif success_level > 0.5:
                return f"{intro} Su esfuerzo es encomiable aunque hay espacio para mejorar. {context}"
            else:
                return f"{intro} Lamento informar que su desempeño no ha alcanzado el nivel esperado. {context}"
        
        return f"{intro} {context}"


class LucienService:
    """Servicio para gestionar las interacciones de Lucien como Mayordomo del Diván."""
    
    def __init__(self, session: AsyncSession, notification_service: Optional[NotificationService] = None):
        self.session = session
        self.notification_service = notification_service
        self.personality = LucienPersonality()
    
    async def handle_initial_greeting(self, user_id: int) -> Dict[str, Any]:
        """Genera el saludo inicial de Lucien después de la solicitud de acceso al canal."""
        # Implementación del saludo formal estilo mayordomo
        
        # Verificar si el usuario ya existe
        user_state = await self._get_user_narrative_state(user_id)
        is_new_user = user_state.lucien_interaction_count == 0
        
        # Incrementar contador de interacciones
        user_state.lucien_interaction_count += 1
        await self.session.commit()
        
        # Seleccionar plantilla de saludo
        if is_new_user:
            greeting_template = self.personality.GREETING_TEMPLATES["initial"]
            greeting = f"{greeting_template}\n\nSu interés en Diana es comprensible, pero mi deber es determinar si es digno de su atención. Le observaré atentamente."
        else:
            greeting_template = self.personality.GREETING_TEMPLATES["return"]
            greeting = f"{greeting_template}\n\nVeo que continúa interesado en conocer más sobre Diana. Sigamos con su evaluación."
        
        return {
            "success": True,
            "greeting": greeting,
            "is_new_user": is_new_user,
            "interaction_count": user_state.lucien_interaction_count
        }
    
    async def evaluate_user_reaction(self, user_id: int, reaction_type: str, context: str) -> Dict[str, Any]:
        """Evalúa la reacción de un usuario al contenido desde la perspectiva de Lucien."""
        # Implementación con diferentes respuestas basadas en tipo de reacción y contexto
        
        user_state = await self._get_user_narrative_state(user_id)
        
        # Mapeo de tipos de reacción a interpretaciones y cambios de confianza
        reaction_mapping = {
            "comprendo": {
                "interpretation": "Su comprensión demuestra perspicacia.",
                "trust_change": 0.03,
                "positive": True
            },
            "duda": {
                "interpretation": "Sus dudas revelan un espíritu inquisitivo.",
                "trust_change": 0.02,
                "positive": True
            },
            "asombro": {
                "interpretation": "Su asombro sugiere una mente abierta a nuevas posibilidades.",
                "trust_change": 0.04,
                "positive": True
            },
            "temor": {
                "interpretation": "Su temor indica una comprensión adecuada de la gravedad.",
                "trust_change": 0.03,
                "positive": True
            }
        }
        
        reaction_data = reaction_mapping.get(reaction_type, {
            "interpretation": "Su reacción ha sido registrada.",
            "trust_change": 0.01,
            "positive": False
        })
        
        # Ajustar nivel de confianza
        trust_change = reaction_data["trust_change"]
        user_state.lucien_trust_level = min(1.0, user_state.lucien_trust_level + trust_change)
        user_state.lucien_interaction_count += 1
        
        # Construir respuesta de Lucien
        interpretation = reaction_data["interpretation"]
        context_specific = f" En el contexto de '{context}', esto sugiere una afinidad con los misterios que Diana aprecia."
        
        response = self.personality.get_formal_response(f"{interpretation}{context_specific}")
        
        # Si la reacción es positiva, añadir comentario sobre progreso
        if reaction_data["positive"]:
            response += f"\n\nSu nivel de confianza ha aumentado a {user_state.lucien_trust_level:.2f}."
        
        await self.session.commit()
        
        return {
            "success": True,
            "response": response,
            "trust_level": user_state.lucien_trust_level,
            "trust_change": trust_change,
            "positive_reaction": reaction_data["positive"],
            "interpretation": interpretation
        }
    
    async def determine_diana_appearance(self, user_id: int, trigger_type: str) -> bool:
        """Determina si una acción del usuario debería desencadenar una aparición de Diana."""
        # Implementación basada en progreso del usuario, patrones de reacción y posición narrativa
        
        user_state = await self._get_user_narrative_state(user_id)
        
        # Factores que influyen en la aparición de Diana
        base_probability = 0.05  # Probabilidad base muy baja
        trust_factor = user_state.lucien_trust_level * 0.3  # Mayor confianza, mayor probabilidad
        
        # Penalizar apariciones frecuentes (últimas 24 horas)
        recent_appearances = await self._count_recent_appearances(user_id)
        recency_penalty = min(0.8, recent_appearances * 0.2)  # Hasta 80% de reducción
        
        # Bonificaciones basadas en el tipo de disparador
        trigger_bonuses = {
            "reaction": 0.1,
            "challenge_success": 0.15,
            "milestone": 0.25,
            "temporal_moment": 0.3,
            "vip_action": 0.4
        }
        
        trigger_bonus = trigger_bonuses.get(trigger_type, 0)
        
        # Cálculo final de probabilidad
        appearance_probability = (base_probability + trust_factor + trigger_bonus) * (1 - recency_penalty)
        
        # Implementar límite estricto de tasa si es necesario
        if recent_appearances >= 3:  # Máximo 3 apariciones en 24 horas
            appearance_probability *= 0.1  # Reducción drástica
        
        # Decisión final
        should_appear = random.random() < appearance_probability
        
        return should_appear
    
    async def interpret_reaction(self, user_id: int, reaction_type: str, fragment_id: str) -> Dict[str, Any]:
        """Interpreta una reacción emocional desde la perspectiva de Lucien."""
        # Obtener datos del fragmento
        fragment = await self._get_narrative_fragment(fragment_id)
        
        # Evaluar la reacción
        evaluation = await self.evaluate_user_reaction(
            user_id, reaction_type, fragment.title
        )
        
        # Determinar si debería aparecer Diana
        should_diana_appear = await self.determine_diana_appearance(user_id, "reaction")
        
        result = {
            "response": evaluation["response"],
            "trust_change": evaluation["trust_change"],
            "diana_appears": should_diana_appear
        }
        
        # Si Diana debe aparecer, añadir su respuesta
        if should_diana_appear:
            # Aquí necesitaríamos DianaAppearanceService, pero podemos hacer una respuesta simple
            diana_responses = [
                "Interesante reacción...",
                "Tu perspectiva me intriga.",
                "Veo algo diferente en ti.",
                "Quizás haya más en ti de lo que aparenta."
            ]
            result["diana_response"] = random.choice(diana_responses)
        
        return result
    
    async def create_challenge(self, user_id: int, challenge_type: str = None) -> Dict[str, Any]:
        """Crea un desafío de observación para el usuario."""
        user_state = await self._get_user_narrative_state(user_id)
        
        # Determinar tipo de desafío si no se especifica
        if not challenge_type:
            challenge_types = ["observation", "deduction", "connection"]
            weights = [0.5, 0.3, 0.2]  # Ponderación hacia observación como tipo principal
            challenge_type = random.choices(challenge_types, weights=weights)[0]
        
        # Determinar dificultad basada en nivel narrativo y confianza
        difficulty = min(1.0, (user_state.narrative_level / 6) + (user_state.lucien_trust_level / 2))
        
        # Crear desafío
        challenge = {
            "id": f"challenge_{int(datetime.utcnow().timestamp())}",
            "type": challenge_type,
            "difficulty": difficulty,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "completed": False
        }
        
        # Diferentes contenidos según tipo
        if challenge_type == "observation":
            challenge["subject"] = "el último mensaje compartido en el canal"
            challenge["question"] = "¿Qué detalle aparentemente insignificante podría ser relevante?"
            challenge["template"] = self.personality.CHALLENGE_TEMPLATES["observation"].format(
                subject=challenge["subject"]
            )
        elif challenge_type == "deduction":
            challenge["clues"] = [
                "La respuesta está oculta en los patrones",
                "Observe las secuencias recurrentes",
                "Los detalles más pequeños revelan las mayores verdades"
            ]
            challenge["question"] = "¿Qué conclusión puede extraer de estos elementos?"
            challenge["template"] = self.personality.CHALLENGE_TEMPLATES["deduction"]
        elif challenge_type == "connection":
            challenge["elements"] = [
                "El símbolo recurrente en los mensajes de Diana",
                "La frecuencia de las apariciones",
                "Las palabras utilizadas en momentos de tensión"
            ]
            challenge["question"] = "¿Cuál es el elemento común que conecta estos aspectos?"
            challenge["template"] = self.personality.CHALLENGE_TEMPLATES["connection"]
        
        # Guardar desafío en el estado del usuario
        if "challenges" not in user_state.additional_data:
            user_state.additional_data["challenges"] = []
        
        user_state.additional_data["challenges"].append(challenge)
        await self.session.commit()
        
        return {
            "success": True,
            "challenge": challenge,
            "challenge_text": challenge["template"],
            "challenge_question": challenge["question"],
            "challenge_issued": True
        }
    
    async def _get_user_narrative_state(self, user_id: int) -> UserNarrativeState:
        """Obtiene o crea el estado narrativo del usuario."""
        stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        result = await self.session.execute(stmt)
        state = result.scalar_one_or_none()
        
        if not state:
            # Crear nuevo estado
            state = UserNarrativeState(
                user_id=user_id,
                current_fragment_id=None,
                lucien_trust_level=0.0,
                lucien_interaction_count=0,
                diana_appearances=[],
                narrative_level=1,
                additional_data={}
            )
            self.session.add(state)
            await self.session.commit()
        
        return state
    
    async def _get_narrative_fragment(self, fragment_id: str) -> NarrativeFragment:
        """Obtiene un fragmento narrativo por ID."""
        stmt = select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _count_recent_appearances(self, user_id: int) -> int:
        """Cuenta las apariciones recientes de Diana (últimas 24 horas)."""
        user_state = await self._get_user_narrative_state(user_id)
        
        # Filtrar apariciones en las últimas 24 horas
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=24)
        
        recent_count = 0
        for appearance in user_state.diana_appearances:
            try:
                appearance_time = datetime.fromisoformat(appearance.get("timestamp", ""))
                if appearance_time > cutoff:
                    recent_count += 1
            except (ValueError, TypeError):
                # Ignorar entradas con formato incorrecto
                continue
        
        return recent_count
```

## 3. ObservationChallengeService

```python
# services/observation_challenge_service.py

from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import random
import uuid

from database.narrative_unified import UserNarrativeState
from services.lucien_service import LucienService

class ObservationChallengeService:
    """Servicio para gestionar los desafíos de observación de Lucien."""
    
    def __init__(self, session: AsyncSession, lucien_service: Optional[LucienService] = None):
        self.session = session
        self.lucien_service = lucien_service or LucienService(session)
    
    async def create_observation_challenge(self, user_id: int, challenge_level: int = 1) -> Dict[str, Any]:
        """Crea un nuevo desafío de observación apropiado para el nivel del usuario."""
        # Obtener estado del usuario
        user_state = await self._get_user_narrative_state(user_id)
        
        # Determinar nivel de desafío si no se especifica
        if challenge_level < 1:
            challenge_level = max(1, min(5, user_state.narrative_level))
        
        # Diferentes tipos de desafíos según nivel
        challenge_types = {
            1: ["visual_element", "message_pattern", "symbol_recognition"],
            2: ["hidden_message", "sequence_pattern", "contextual_clue"],
            3: ["narrative_inconsistency", "emotional_subtext", "symbolic_meaning"],
            4: ["multi_layer_puzzle", "temporal_pattern", "cross_reference"],
            5: ["quantum_perception", "meta_narrative", "symbolic_transformation"]
        }
        
        available_types = challenge_types.get(challenge_level, challenge_types[1])
        challenge_type = random.choice(available_types)
        
        # Crear desafío específico
        challenge_id = f"obs_{uuid.uuid4().hex[:8]}"
        challenge = {
            "id": challenge_id,
            "type": challenge_type,
            "level": challenge_level,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=48)).isoformat(),
            "completed": False,
            "attempts": 0,
            "max_attempts": 3
        }
        
        # Contenido específico según tipo
        if challenge_type == "visual_element":
            challenge["description"] = "Encuentre el elemento visual que aparece en los últimos tres mensajes del canal."
            challenge["hint"] = "Observe los detalles en las imágenes compartidas."
            challenge["success_criteria"] = ["logo", "símbolo", "marca de agua"]
        
        elif challenge_type == "message_pattern":
            challenge["description"] = "Identifique el patrón en los mensajes recientes de Diana."
            challenge["hint"] = "Preste atención a las primeras letras de cada párrafo."
            challenge["success_criteria"] = ["iniciales", "acróstico", "secuencia"]
        
        # Guardar desafío en estado del usuario
        if "observation_challenges" not in user_state.additional_data:
            user_state.additional_data["observation_challenges"] = []
        
        user_state.additional_data["observation_challenges"].append(challenge)
        await self.session.commit()
        
        # Formatear presentación
        presentation = await self.lucien_service.format_challenge_presentation(
            user_id, challenge
        ) if self.lucien_service else {
            "challenge_text": f"Desafío de observación nivel {challenge_level}: {challenge['description']}",
            "hint": challenge["hint"]
        }
        
        return {
            "success": True,
            "challenge_id": challenge_id,
            "challenge": challenge,
            "presentation": presentation
        }
    
    async def evaluate_observation_attempt(self, user_id: int, challenge_id: str, answer: str) -> Dict[str, Any]:
        """Evalúa el intento de un usuario de resolver un desafío de observación."""
        # Obtener estado y desafío
        user_state = await self._get_user_narrative_state(user_id)
        challenge = await self._get_challenge(user_state, challenge_id)
        
        if not challenge:
            return {
                "success": False,
                "error": "Desafío no encontrado"
            }
        
        # Verificar si expiró
        if await self._is_challenge_expired(challenge):
            return {
                "success": False,
                "error": "El desafío ha expirado",
                "expired": True
            }
        
        # Incrementar intentos
        challenge["attempts"] += 1
        
        # Normalizar respuesta para comparación
        normalized_answer = answer.lower().strip()
        success_criteria = [c.lower() for c in challenge.get("success_criteria", [])]
        
        # Evaluar respuesta
        success = any(criterion in normalized_answer for criterion in success_criteria)
        partial_match = any(criterion in normalized_answer or normalized_answer in criterion 
                          for criterion in success_criteria)
        
        # Calcular nivel de éxito
        if success:
            success_level = 1.0
        elif partial_match:
            success_level = 0.5
        else:
            success_level = 0.0
        
        # Actualizar estado del desafío
        challenge["completed"] = success
        challenge["success_level"] = success_level
        challenge["completed_at"] = datetime.utcnow().isoformat() if success else None
        
        # Calcular cambio de confianza
        trust_change = 0
        if success:
            trust_change = 0.05 * challenge["level"]  # Mayor nivel, mayor recompensa
        elif partial_match:
            trust_change = 0.02 * challenge["level"]
        
        # Aplicar cambio de confianza
        if trust_change > 0:
            user_state.lucien_trust_level = min(1.0, user_state.lucien_trust_level + trust_change)
        
        await self.session.commit()
        
        # Preparar respuesta de Lucien
        if self.lucien_service:
            if success:
                context = f"Ha completado el desafío con precisión. Su respuesta demuestra una notable capacidad de observación."
            elif partial_match:
                context = f"Su respuesta contiene elementos correctos, pero no ha capturado la esencia completa del desafío."
            else:
                context = f"Lamento informar que su respuesta no cumple con los criterios esperados."
            
            lucien_response = await self.lucien_service.get_formal_response(context, success_level)
        else:
            lucien_response = f"Evaluación: {'Éxito' if success else 'Intento fallido'}"
        
        # Determinar si esto debería desencadenar una aparición de Diana
        diana_appears = False
        diana_response = None
        
        if self.lucien_service and success:
            diana_appears = await self.lucien_service.determine_diana_appearance(
                user_id, "challenge_success"
            )
            
            if diana_appears:
                diana_responses = [
                    "Una mente observadora... interesante.",
                    "Veo que tienes una perspectiva única.",
                    "Tu atención al detalle es... poco común.",
                    "Quizás haya más en ti de lo que pensaba inicialmente."
                ]
                diana_response = random.choice(diana_responses)
        
        return {
            "success": True,
            "challenge_success": success,
            "partial_match": partial_match and not success,
            "success_level": success_level,
            "attempts_remaining": challenge["max_attempts"] - challenge["attempts"],
            "trust_change": trust_change,
            "lucien_response": lucien_response,
            "diana_appears": diana_appears,
            "diana_response": diana_response
        }
    
    async def get_challenge(self, challenge_id: str) -> Dict[str, Any]:
        """Obtiene detalles de un desafío específico."""
        # Buscar en todos los usuarios
        stmt = select(UserNarrativeState)
        result = await self.session.execute(stmt)
        all_states = result.scalars().all()
        
        for state in all_states:
            challenges = state.additional_data.get("observation_challenges", [])
            for challenge in challenges:
                if challenge.get("id") == challenge_id:
                    # Añadir información sobre expiración
                    challenge["is_expired"] = await self._is_challenge_expired(challenge)
                    return challenge
        
        return None
    
    async def _get_user_narrative_state(self, user_id: int) -> UserNarrativeState:
        """Obtiene estado narrativo del usuario."""
        stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_challenge(self, user_state: UserNarrativeState, challenge_id: str) -> Dict[str, Any]:
        """Obtiene un desafío específico del estado del usuario."""
        challenges = user_state.additional_data.get("observation_challenges", [])
        for challenge in challenges:
            if challenge.get("id") == challenge_id:
                return challenge
        return None
    
    async def _is_challenge_expired(self, challenge: Dict[str, Any]) -> bool:
        """Verifica si un desafío ha expirado."""
        try:
            expires_at = datetime.fromisoformat(challenge.get("expires_at", ""))
            return datetime.utcnow() > expires_at
        except (ValueError, TypeError):
            # Si hay error en el formato, asumir no expirado
            return False
```

## 4. Extensión de CoordinadorCentral

```python
# Extensión para services/coordinador_central.py

# Añadir nuevo tipo de acción
class AccionUsuario(Enum):
    # Tipos existentes...
    
    # Nuevos tipos para Lucien-Diana
    LUCIEN_CHALLENGE = "lucien_challenge"
    LUCIEN_DIALOGUE = "lucien_dialogue"
    DIANA_APPEARANCE = "diana_appearance"
    QUANTUM_TRIGGER = "quantum_trigger"

# Añadir nuevo método para manejar dinámica Lucien-Diana
async def _flujo_lucien_diana_dynamic(self, user_id: int, action: str, 
                                     context: Dict[str, Any] = None, bot=None) -> Dict[str, Any]:
    """
    Flujo para gestionar la dinámica de interacción Lucien-Diana.
    
    Args:
        user_id: ID del usuario
        action: Tipo de acción ("lucien_challenge", "diana_appearance", etc.)
        context: Contexto adicional para la acción
        bot: Instancia del bot para enviar mensajes
        
    Returns:
        Dict con resultados y mensajes
    """
    # Crear servicios necesarios
    lucien_service = LucienService(self.session, self.notification_service)
    
    if action == "lucien_challenge":
        # Maneja a Lucien presentando un desafío al usuario
        challenge_type = context.get("challenge_type")
        observation_service = ObservationChallengeService(self.session, lucien_service)
        
        if context.get("evaluation"):
            # Evaluar respuesta a desafío
            challenge_id = context.get("challenge_id")
            answer = context.get("answer")
            
            evaluation = await observation_service.evaluate_observation_attempt(
                user_id, challenge_id, answer
            )
            
            # Verificar si esto debería desencadenar una aparición de Diana
            should_diana_appear = evaluation.get("diana_appears", False)
            
            result = {
                "success": evaluation["success"],
                "challenge_success": evaluation.get("challenge_success", False),
                "lucien_response": evaluation.get("lucien_response", ""),
                "trust_change": evaluation.get("trust_change", 0),
                "diana_appeared": should_diana_appear
            }
            
            if should_diana_appear:
                result["diana_response"] = evaluation.get("diana_response", "")
                
                # Registrar aparición de Diana
                await self._record_diana_appearance(
                    user_id, 
                    "challenge_success", 
                    {"challenge_id": challenge_id}
                )
            
            return result
        else:
            # Crear nuevo desafío
            challenge_result = await observation_service.create_observation_challenge(
                user_id, 
                context.get("challenge_level", 1)
            )
            
            return {
                "success": challenge_result["success"],
                "challenge_id": challenge_result["challenge_id"],
                "challenge_text": challenge_result["presentation"]["challenge_text"],
                "hint": challenge_result["presentation"].get("hint", ""),
                "challenge_issued": True
            }
    
    elif action == "evaluate_reaction":
        # Evalúa la reacción del usuario con la perspectiva de Lucien
        reaction_type = context.get("reaction_type")
        reaction_context = context.get("reaction_context")
        
        # Si no hay servicio de reacción narrativa, usar Lucien directamente
        evaluation = await lucien_service.evaluate_user_reaction(
            user_id, reaction_type, reaction_context
        )
        
        # Determinar si esto debería desencadenar una aparición de Diana
        should_diana_appear = await lucien_service.determine_diana_appearance(
            user_id, "reaction_evaluation"
        )
        
        result = {
            "success": True,
            "lucien_response": evaluation["response"],
            "trust_change": evaluation["trust_change"],
            "diana_appeared": should_diana_appear
        }
        
        if should_diana_appear:
            # Obtener respuesta de Diana
            diana_service = DianaAppearanceService(self.session)
            diana_context = {
                "type": "reaction",
                "reaction_type": reaction_type,
                "fragment_context": reaction_context
            }
            
            diana_response = await diana_service.get_diana_response(
                user_id, diana_context
            )
            
            result["diana_response"] = diana_response
            
            # Registrar aparición de Diana
            await self._record_diana_appearance(
                user_id, 
                "reaction", 
                {"reaction_type": reaction_type}
            )
        
        return result
    
    elif action == "quantum_trigger":
        # Maneja disparadores que modifican fragmentos pasados
        trigger_type = context.get("trigger_type")
        trigger_fragment_id = context.get("fragment_id")
        decision = context.get("decision")
        
        quantum_service = QuantumFragmentService(self.session, lucien_service)
        
        result = await quantum_service.apply_quantum_trigger(
            user_id, trigger_fragment_id, decision
        )
        
        return {
            "success": result["success"],
            "affected_fragments": result["affected_fragments"],
            "lucien_explanation": result["lucien_explanation"],
            "should_review_past": result["should_review_past"]
        }
    
    elif action == "temporal_moment":
        # Maneja momentos narrativos restringidos por tiempo
        temporal_service = TemporalMomentService(self.session, lucien_service)
        
        if context.get("get_available"):
            # Obtener momentos temporales disponibles
            available_moments = await temporal_service.get_available_moments(user_id)
            
            return {
                "success": True,
                "available_moments": available_moments,
                "count": len(available_moments)
            }
        elif context.get("moment_id"):
            # Acceder a un momento temporal específico
            moment_id = context.get("moment_id")
            
            access_result = await temporal_service.access_temporal_moment(
                user_id, moment_id
            )
            
            # Determinar si Diana debería aparecer
            should_diana_appear = access_result.get("diana_appears", False)
            
            result = {
                "success": access_result["success"],
                "moment_text": access_result.get("moment_text", ""),
                "lucien_introduction": access_result.get("lucien_introduction", ""),
                "diana_appeared": should_diana_appear
            }
            
            if should_diana_appear:
                result["diana_response"] = access_result.get("diana_response", "")
                
                # Registrar aparición de Diana
                await self._record_diana_appearance(
                    user_id, 
                    "temporal_moment", 
                    {"moment_id": moment_id}
                )
            
            return result
    
    # Acción no reconocida
    return {
        "success": False,
        "error": f"Acción no reconocida: {action}"
    }

# Método auxiliar para registrar apariciones de Diana
async def _record_diana_appearance(self, user_id: int, context_type: str, 
                                 context_data: Dict[str, Any]) -> None:
    """Registra una aparición de Diana en el historial del usuario."""
    stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
    result = await self.session.execute(stmt)
    user_state = result.scalar_one_or_none()
    
    if not user_state:
        return
    
    # Crear registro de aparición
    appearance = {
        "timestamp": datetime.utcnow().isoformat(),
        "context_type": context_type,
        "context_data": context_data
    }
    
    # Añadir al historial
    user_state.diana_appearances.append(appearance)
    await self.session.commit()

# Añadir integración de emisión de eventos
async def _emit_workflow_events(self, user_id: int, accion: AccionUsuario, 
                               result: Dict[str, Any], correlation_id: str) -> None:
    # ...código existente...
    
    # Manejar eventos específicos de Lucien-Diana
    if accion == AccionUsuario.LUCIEN_CHALLENGE:
        await self.event_bus.publish(
            EventType.LUCIEN_CHALLENGE_ISSUED if result.get("challenge_issued") else EventType.LUCIEN_CHALLENGE_COMPLETED,
            user_id,
            {
                "challenge_type": result.get("challenge_type"),
                "success_level": result.get("success_level"),
                "trust_change": result.get("trust_change"),
                "diana_appeared": result.get("diana_appeared", False)
            },
            source="coordinador_central",
            correlation_id=correlation_id
        )
        
        if result.get("diana_appeared"):
            await self.event_bus.publish(
                EventType.DIANA_APPEARED,
                user_id,
                {
                    "context": "lucien_challenge",
                    "challenge_type": result.get("challenge_type"),
                    "response": result.get("diana_response")
                },
                source="coordinador_central",
                correlation_id=correlation_id
            )
    
    elif accion == AccionUsuario.QUANTUM_TRIGGER:
        await self.event_bus.publish(
            EventType.QUANTUM_FRAGMENT_CHANGED,
            user_id,
            {
                "affected_fragments": result.get("affected_fragments", 0),
                "should_review_past": result.get("should_review_past", False)
            },
            source="coordinador_central",
            correlation_id=correlation_id
        )
    
    # ...resto del código existente...
```

## 5. Handlers de Canal

```python
# handlers/channel_handlers.py

from aiogram import Router, Bot, F
from aiogram.types import ChatJoinRequest
from aiogram.filters import ChatJoinRequestFilter
from sqlalchemy.ext.asyncio import AsyncSession
import datetime
import logging

from database.models import User
from services.lucien_service import LucienService
from scheduler import scheduler

router = Router()
logger = logging.getLogger(__name__)

# Funciones auxiliares
async def get_or_create_user(session: AsyncSession, user_info):
    """Obtiene o crea un usuario en la base de datos."""
    result = await session.execute(select(User).where(User.id == user_info.id))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            id=user_info.id,
            username=user_info.username,
            first_name=user_info.first_name,
            last_name=user_info.last_name,
            points=0,
            level=1
        )
        session.add(user)
        await session.commit()
    
    return user

async def send_lucien_welcome(bot: Bot, user_id: int, chat_id: int):
    """Envía el mensaje de bienvenida de Lucien."""
    try:
        # Crear sesión de base de datos para esta función aislada
        async with async_session() as session:
            lucien_service = LucienService(session)
            
            # Obtener saludo de Lucien
            greeting_result = await lucien_service.handle_initial_greeting(user_id)
            
            # Enviar mensaje de bienvenida
            await bot.send_message(
                user_id,
                greeting_result["greeting"],
                parse_mode="HTML"
            )
            
            logger.info(f"Enviado mensaje de bienvenida de Lucien a usuario {user_id}")
    except Exception as e:
        logger.exception(f"Error al enviar bienvenida de Lucien: {e}")

async def approve_channel_request(bot: Bot, user_id: int, chat_id: int):
    """Aprueba la solicitud de unión al canal después del tiempo de espera."""
    try:
        # Aprobar solicitud
        await bot.approve_chat_join_request(
            chat_id=chat_id,
            user_id=user_id
        )
        
        # Enviar mensaje de aprobación
        async with async_session() as session:
            lucien_service = LucienService(session)
            
            approval_message = "Su solicitud ha sido aprobada. Le doy la bienvenida formal a Los Kinkys. Como su mayordomo, estaré observando su progreso y comportamiento. Demuestre que es digno de conocer a Diana."
            
            await bot.send_message(
                user_id,
                approval_message,
                parse_mode="HTML"
            )
        
        logger.info(f"Aprobada solicitud de usuario {user_id} para chat {chat_id}")
    except Exception as e:
        logger.exception(f"Error al aprobar solicitud de canal: {e}")

@router.chat_join_request(ChatJoinRequestFilter())
async def handle_join_request(join_request: ChatJoinRequest, bot: Bot, session: AsyncSession):
    """Maneja una solicitud de usuario para unirse al canal."""
    try:
        user_id = join_request.from_user.id
        chat_id = join_request.chat.id
        
        # Registra la solicitud de unión
        logger.info(f"Solicitud de unión del usuario {user_id} para chat {chat_id}")
        
        # Crea usuario si no existe
        user = await get_or_create_user(session, join_request.from_user)
        
        # Programa mensaje de bienvenida de Lucien (5 minutos después de la solicitud)
        scheduler.add_job(
            send_lucien_welcome,
            'date',
            run_date=datetime.datetime.now() + datetime.timedelta(minutes=5),
            args=[bot, user_id, join_request.chat.id]
        )
        
        # Programa aprobación del canal (15 minutos después de la solicitud)
        scheduler.add_job(
            approve_channel_request,
            'date',
            run_date=datetime.datetime.now() + datetime.timedelta(minutes=15),
            args=[bot, user_id, join_request.chat.id]
        )
        
        logger.info(f"Programada bienvenida y aprobación para usuario {user_id}")
        
    except Exception as e:
        logger.exception(f"Error al manejar solicitud de unión: {e}")
```

## 6. Extensión del NotificationService

```python
# Extensión para services/notification_service.py

# Añadir al método _build_enhanced_unified_message
async def _build_enhanced_unified_message(self, grouped: Dict[str, List[Dict[str, Any]]]) -> str:
    # ...código existente...
    
    # === SECCIÓN DE LUCIEN Y DIANA ===
    if "lucien_message" in grouped:
        lucien_messages = grouped["lucien_message"]
        latest_message = lucien_messages[-1]
        
        # Añadir sección de Lucien con tono propio de mayordomo
        sections.append("🎩 *Mensaje de Lucien:*")
        sections.append(f"_{latest_message.get('message', 'Lucien observa tu progreso...')}_")
    
    if "diana_appearance" in grouped:
        diana_appearances = grouped["diana_appearance"]
        # Las apariciones de Diana son raras y especiales, así que destacarlas
        sections.append("━━━━━━━━━━━━━━━")
        sections.append("🌸 *Diana apareció brevemente...*")
        
        for appearance in diana_appearances[:1]:  # Solo mostrar la más reciente
            sections.append(f"_{appearance.get('message', 'Sus ojos te observaron por un instante...')}_")
        
        # Añadir comentario de Lucien sobre la aparición de Diana
        sections.append("🎩 *Lucien comenta:*")
        sections.append("_\"Fascinante... Diana no suele mostrar interés tan directamente. Parece que algo en ti captó su atención.\"_")
    
    # ...resto del código existente...
```

Este documento proporciona implementaciones detalladas de los componentes principales del sistema Lucien-Diana. Se recomienda utilizar estos ejemplos como guía para la implementación, adaptándolos según sea necesario a las necesidades específicas del proyecto.