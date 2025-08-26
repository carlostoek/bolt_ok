# Manual Técnico de Implementación e Integración de Interfaces

## Resumen Ejecutivo

Este manual documenta el sistema de interfaces implementado para el bot Diana, proporcionando una guía comprehensiva para desarrolladores que trabajen con integraciones cross-módulos. El sistema está diseñado alrededor de cuatro interfaces principales que gestionan estados emocionales, entrega de contenido, procesamiento de interacciones y servicios narrativos contextualizados.

**Versión:** 1.0  
**Última actualización:** 26 de agosto, 2025  
**Audiencia:** Desarrolladores del equipo, integradores de sistemas, arquitectos de software

## Arquitectura del Sistema

### Componentes Principales

#### 1. CoordinadorCentral (Facade Pattern)
**Ubicación:** `services/coordinador_central.py`  
**Propósito:** Orquesta la integración entre todos los módulos del sistema

El CoordinadorCentral actúa como punto central de coordinación para todos los flujos de trabajo del sistema:

```python
class CoordinadorCentral:
    def __init__(self, session: AsyncSession):
        # Servicios de integración
        self.channel_engagement = ChannelEngagementService(session)
        self.narrative_point = NarrativePointService(session)
        self.narrative_access = NarrativeAccessService(session)
        self.event_coordinator = EventCoordinator(session)
        
        # Servicios nuevos de interfaces
        self.emotional_state_service = EmotionalStateService(session)
        self.content_delivery_service = ContentDeliveryService()
        self.interaction_processor = create_interaction_processor(session)
        
        # Event bus para comunicación inter-módulos
        self.event_bus = get_event_bus()
```

**Flujos Soportados:**
- `AccionUsuario.REACCIONAR_PUBLICACION_NATIVA`
- `AccionUsuario.REACCIONAR_PUBLICACION_INLINE`
- `AccionUsuario.ACCEDER_NARRATIVA_VIP`
- `AccionUsuario.TOMAR_DECISION`
- `AccionUsuario.PARTICIPAR_CANAL`
- `AccionUsuario.VERIFICAR_ENGAGEMENT`
- `AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO`
- `AccionUsuario.DESBLOQUEAR_PISTA`
- `AccionUsuario.ANALIZAR_ESTADO_EMOCIONAL` *(nuevo)*

#### 2. EventBus (Observer Pattern)
**Ubicación:** `services/event_bus.py`  
**Propósito:** Comunicación asíncrona desacoplada entre módulos

```python
class EventBus:
    async def publish(self, event_type: EventType, user_id: int, 
                     data: Dict[str, Any], source: str = None, 
                     correlation_id: str = None) -> Event
```

**Tipos de Eventos:**
- `USER_REACTION`, `USER_PARTICIPATION`, `USER_DAILY_CHECKIN`
- `NARRATIVE_DECISION`, `NARRATIVE_PROGRESS`, `NARRATIVE_ACCESS_DENIED`
- `POINTS_AWARDED`, `ACHIEVEMENT_UNLOCKED`, `LEVEL_UP`
- `CHANNEL_ENGAGEMENT`, `VIP_ACCESS_REQUIRED`
- `WORKFLOW_COMPLETED`, `ERROR_OCCURRED`, `CONSISTENCY_CHECK`

## Interfaces Principales

### 1. IEmotionalStateManager

**Ubicación:** `services/interfaces/emotional_state_interface.py`  
**Implementación:** `services/emotional_state_service.py`  

#### Estructuras de Datos

```python
class EmotionalState(Enum):
    NEUTRAL = "neutral"
    CURIOUS = "curious"
    ENGAGED = "engaged"
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"
    SATISFIED = "satisfied"
    EXCITED = "excited"

@dataclass
class EmotionalContext:
    primary_state: EmotionalState
    intensity: float  # 0.0 to 1.0
    secondary_states: Dict[EmotionalState, float]
    last_updated: datetime
    triggers: List[str]
```

#### API Principal

##### `async get_user_emotional_state(user_id: int) -> EmotionalContext`
Obtiene el contexto emocional actual del usuario. Si no existe, crea uno neutral por defecto.

**Ejemplo de uso:**
```python
coordinator = CoordinadorCentral(session)
context = await coordinator.emotional_state_service.get_user_emotional_state(123456)
print(f"Estado: {context.primary_state.value}, Intensidad: {context.intensity}")
```

##### `async update_emotional_state(user_id: int, state: EmotionalState, intensity: float, trigger: str) -> EmotionalContext`
Actualiza el estado emocional y registra el cambio en historial.

**Validaciones:**
- `0.0 <= intensity <= 1.0`
- Usuario debe existir en base de datos
- Se registra en `EmotionalStateHistory`

##### `async analyze_interaction_emotion(user_id: int, interaction_data: Dict) -> EmotionalState`
Analiza datos de interacción para inferir estado emocional.

**Patrones de Análisis Implementados:**

```python
# Completar fragmento narrativo
if interaction_type == "fragment_completion":
    completion_time = interaction_data.get("completion_time", 60)
    if completion_time < 30:
        return EmotionalState.EXCITED if "positive" in choice else EmotionalState.ENGAGED
    elif completion_time > 180:
        return EmotionalState.CONFUSED
    else:
        return EmotionalState.SATISFIED

# Selección de decisiones
elif interaction_type == "choice_selection":
    choice_text = interaction_data.get("choice_text", "").lower()
    if any(word in choice_text for word in ["ayudar", "positivo", "bueno"]):
        return EmotionalState.SATISFIED
    elif any(word in choice_text for word in ["explorar", "descubrir"]):
        return EmotionalState.CURIOUS

# Intentos fallidos
elif interaction_type == "failed_attempt":
    attempts = interaction_data.get("attempts", 1)
    return EmotionalState.FRUSTRATED if attempts >= 3 else EmotionalState.CONFUSED
```

##### `async get_recommended_content_tone(user_id: int) -> str`
Retorna el tono recomendado basado en estado emocional:

```python
tone_mapping = {
    EmotionalState.NEUTRAL: "balanced",
    EmotionalState.CURIOUS: "intriguing", 
    EmotionalState.ENGAGED: "energetic",
    EmotionalState.CONFUSED: "supportive",
    EmotionalState.FRUSTRATED: "gentle",
    EmotionalState.SATISFIED: "encouraging",
    EmotionalState.EXCITED: "enthusiastic"
}
```

#### Integración con CoordinadorCentral

El CoordinadorCentral incluye un flujo específico para análisis emocional:

```python
async def _flujo_analizar_estado_emocional(self, user_id: int, 
                                         interaction_data: Dict[str, Any], 
                                         bot=None) -> Dict[str, Any]:
    # 1. Analizar emoción basada en la interacción
    inferred_emotion = await self.emotional_state_service.analyze_interaction_emotion(
        user_id, interaction_data
    )
    
    # 2. Obtener contexto emocional actual
    current_context = await self.emotional_state_service.get_user_emotional_state(user_id)
    
    # 3. Calcular intensidad basada en cambio emocional
    intensity = self._calculate_emotional_intensity(
        current_context.primary_state, inferred_emotion, interaction_data
    )
    
    # 4. Actualizar si hay cambio significativo
    if (inferred_emotion != current_context.primary_state or 
        abs(intensity - current_context.intensity) > 0.2):
        
        trigger = self._generate_emotional_trigger(interaction_data)
        updated_context = await self.emotional_state_service.update_emotional_state(
            user_id, inferred_emotion, intensity, trigger
        )
```

### 2. IContentDeliveryService

**Ubicación:** `services/interfaces/content_delivery_interface.py`  
**Implementación:** `services/content_delivery_service.py` *(implementación básica)*

#### Estructuras de Datos

```python
class ContentType(Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    INTERACTIVE = "interactive"

class DeliveryChannel(Enum):
    DIRECT_MESSAGE = "direct_message"
    CHANNEL = "channel"
    CALLBACK = "callback"
    INLINE = "inline"

@dataclass
class ContentPackage:
    content_id: str
    content_type: ContentType
    payload: Union[str, bytes, Dict[str, Any]]
    metadata: Dict[str, Any]
    delivery_options: Dict[str, Any]
```

#### API Principal

##### `async prepare_content(content_id: str, context: Dict[str, Any]) -> ContentPackage`
Prepara contenido para entrega con personalización contextual.

**Implementación actual:**
```python
async def prepare_content(self, content_id: str, context: Dict[str, Any]) -> ContentPackage:
    return ContentPackage(
        content_id=content_id,
        content_type=ContentType.TEXT,
        payload=context.get("text", f"Contenido para {content_id}"),
        metadata={"reply_markup": context.get("reply_markup")},
        delivery_options={}
    )
```

##### `async deliver_content(package: ContentPackage, context: Dict[str, Any]) -> bool`
Entrega contenido a través del canal especificado.

##### `async personalize_content(content: str, context: Dict[str, Any]) -> str`
Personaliza contenido usando variables de contexto con template replacement.

##### `async validate_delivery_constraints(package: ContentPackage, context: Dict[str, Any]) -> Tuple[bool, List[str]]`
Valida restricciones antes de la entrega.

**Estado de Implementación:** Implementación básica presente. Requiere extensión para casos de uso complejos.

### 3. IUserInteractionProcessor

**Ubicación:** `services/interfaces/user_interaction_interface.py`  
**Implementaciones:** 
- `services/user_interaction_service.py`
- `services/user_interaction_processor.py` (wrapper para integración)

#### Estructuras de Datos

```python
class InteractionType(Enum):
    MESSAGE = "message"
    CALLBACK = "callback"
    INLINE_QUERY = "inline_query"
    POLL_ANSWER = "poll_answer"
    REACTION = "reaction"
    COMMAND = "command"

@dataclass
class InteractionContext:
    user_id: int
    interaction_type: InteractionType
    raw_data: Dict[str, Any]
    timestamp: datetime
    session_data: Dict[str, Any]

@dataclass
class InteractionResult:
    success: bool
    response_data: Dict[str, Any]
    side_effects: List[str]
    emotional_impact: Optional[EmotionalState]
    points_awarded: Optional[int]
```

#### API Principal

##### `async process_interaction(context: InteractionContext) -> InteractionResult`
Procesa interacción de usuario de forma centralizada.

##### `async validate_interaction(context: InteractionContext) -> Tuple[bool, List[str]]`
Valida interacción según reglas del sistema.

##### `async log_interaction(context: InteractionContext, result: InteractionResult) -> None`
Registra interacción en el sistema de logging.

##### `async get_interaction_history(user_id: int, limit: int = 50) -> List[InteractionContext]`
Obtiene historial de interacciones del usuario.

#### UserInteractionProcessor (Wrapper de Integración)

El `UserInteractionProcessor` proporciona métodos específicos para diferentes tipos de interacciones de Telegram:

```python
class UserInteractionProcessor:
    async def process_message_interaction(self, message: Message, 
                                        session_data: Dict[str, Any] = None) -> InteractionResult
    
    async def process_callback_interaction(self, callback: CallbackQuery, 
                                         session_data: Dict[str, Any] = None) -> InteractionResult
    
    async def process_command_interaction(self, message: Message, command: str, 
                                        args: str = "", session_data: Dict[str, Any] = None) -> InteractionResult
    
    async def process_reaction_interaction(self, user_id: int, emoji: str, 
                                         target_message_id: int = None, 
                                         session_data: Dict[str, Any] = None) -> InteractionResult
    
    async def process_inline_query_interaction(self, inline_query: InlineQuery, 
                                             session_data: Dict[str, Any] = None) -> InteractionResult
```

**Integración con CoordinadorCentral:**
```python
# En __init__ del CoordinadorCentral
self.interaction_processor = create_interaction_processor(session)
self.interaction_processor.set_dependencies(
    emotional_manager=self.emotional_state_service,
    point_service=self.point_service
)
```

### 4. IUserNarrativeService (Enhanced)

**Ubicación:** `services/interfaces/user_narrative_interface.py`  

La interfaz narrativa fue extendida con capacidades de contexto emocional:

#### Nuevas Estructuras de Datos

```python
@dataclass
class ContextualizedFragment:
    fragment: NarrativeFragment
    adapted_content: str
    emotional_tone: str
    personalization_data: Dict[str, Any]

@dataclass
class NarrativeInteractionResult:
    updated_state: UserNarrativeState
    emotional_response: EmotionalState
    triggered_effects: List[Dict[str, Any]]
    next_fragment: Optional[NarrativeFragment] = None
```

#### Métodos Extendidos con Contexto Emocional

##### `async get_contextualized_fragment(user_id: int, fragment_id: str, emotional_context: Optional[EmotionalContext] = None) -> ContextualizedFragment`
Obtiene fragmento adaptado al estado emocional del usuario.

##### `async process_narrative_interaction(user_id: int, interaction_data: Dict[str, Any]) -> NarrativeInteractionResult`
Procesa interacción narrativa con análisis emocional.

##### `async get_personalized_narrative_flow(user_id: int, emotional_context: Optional[EmotionalContext] = None) -> List[str]`
Obtiene flujo narrativo personalizado basado en emociones.

##### `async update_narrative_emotional_impact(user_id: int, fragment_id: str, emotional_response: EmotionalState, intensity: float) -> None`
Actualiza impacto emocional de fragmentos.

## Patrones de Integración

### 1. Integración Básica a través de CoordinadorCentral

**Patrón más común para nuevas funcionalidades:**

```python
async def nueva_funcionalidad(user_id: int, datos: Dict[str, Any]):
    # 1. Crear coordinador
    coordinator = CoordinadorCentral(session)
    
    # 2. Ejecutar flujo
    result = await coordinator.ejecutar_flujo(
        user_id, 
        AccionUsuario.NUEVA_ACCION, 
        **datos
    )
    
    # 3. Procesar resultado
    if result["success"]:
        return {"message": result["message"], "data": result}
    else:
        logger.error(f"Error en flujo: {result.get('error')}")
        return {"error": True, "message": result["message"]}
```

### 2. Integración con EventBus

**Para comunicación asíncrona entre módulos:**

```python
async def publicar_evento_personalizado():
    event_bus = get_event_bus()
    
    # Suscribirse a eventos
    event_bus.subscribe(EventType.POINTS_AWARDED, handle_points_awarded)
    
    # Publicar evento
    await event_bus.publish(
        EventType.POINTS_AWARDED,
        user_id=123456,
        data={"points": 10, "source": "custom_action"},
        source="my_module",
        correlation_id="custom_workflow_001"
    )

async def handle_points_awarded(event: Event):
    user_id = event.user_id
    points = event.data.get("points", 0)
    logger.info(f"Usuario {user_id} recibió {points} puntos")
```

### 3. Integración Cross-Módulo con Estados Emocionales

**Para funcionalidades que requieren adaptación emocional:**

```python
async def funcion_con_adaptacion_emocional(user_id: int, accion_data: Dict[str, Any]):
    coordinator = CoordinadorCentral(session)
    
    # 1. Analizar estado emocional de la interacción
    result = await coordinator.ejecutar_flujo(
        user_id,
        AccionUsuario.ANALIZAR_ESTADO_EMOCIONAL,
        interaction_data=accion_data
    )
    
    # 2. Obtener tono recomendado
    if result["success"]:
        recommended_tone = result["recommended_tone"]
        
        # 3. Personalizar contenido basado en emoción
        content_service = coordinator.content_delivery_service
        personalized_content = await content_service.personalize_content(
            "Hola {user_name}, Diana {emotional_response}",
            {
                "user_name": "Usuario",
                "emotional_response": "sonríe cálidamente" if recommended_tone == "supportive" 
                                    else "te mira con intensidad"
            }
        )
        
        return {"content": personalized_content, "tone": recommended_tone}
```

### 4. Transacciones Complejas con Context Manager

**Para operaciones que requieren atomicidad:**

```python
async def flujo_complejo_transaccional(user_id: int, data: Dict[str, Any]):
    coordinator = CoordinadorCentral(session)
    
    async def workflow_complejo(*args, **kwargs):
        # 1. Actualizar estado emocional
        await coordinator.ejecutar_flujo(user_id, AccionUsuario.ANALIZAR_ESTADO_EMOCIONAL, **data)
        
        # 2. Procesar narrativa
        narrative_result = await coordinator.ejecutar_flujo(
            user_id, AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO, **data
        )
        
        # 3. Otorgar puntos
        if narrative_result["success"]:
            await coordinator.ejecutar_flujo(user_id, AccionUsuario.PARTICIPAR_CANAL, **data)
        
        return {"workflow_completed": True, "results": [narrative_result]}
    
    # Ejecutar en transacción
    async with coordinator.with_transaction(workflow_complejo, user_id, data) as result:
        logger.info(f"Workflow transaccional completado: {result}")
        return result
```

### 5. Workflows Paralelos

**Para optimización de performance:**

```python
async def procesar_multiples_usuarios(usuarios_data: List[Dict[str, Any]]):
    coordinator = CoordinadorCentral(session)
    
    # Preparar workflows para ejecución paralela
    workflows = [
        {
            "user_id": data["user_id"],
            "accion": AccionUsuario.VERIFICAR_ENGAGEMENT,
            "kwargs": {"bot": data.get("bot")}
        }
        for data in usuarios_data
    ]
    
    # Ejecutar en paralelo
    results = await coordinator.execute_parallel_workflows(workflows)
    
    # Procesar resultados
    successful = [r for r in results if r.get("success", False)]
    failed = [r for r in results if not r.get("success", False)]
    
    return {
        "processed": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "results": results
    }
```

## Escenarios de Integración Comunes

### Escenario 1: Agregar Nueva Acción de Usuario

**Pasos para implementar una nueva acción:**

1. **Definir la Acción:**
```python
# En coordinador_central.py
class AccionUsuario(enum.Enum):
    # ... acciones existentes
    MI_NUEVA_ACCION = "mi_nueva_accion"
```

2. **Implementar el Flujo:**
```python
# En CoordinadorCentral.ejecutar_flujo()
elif accion == AccionUsuario.MI_NUEVA_ACCION:
    result = await self._flujo_mi_nueva_accion(user_id, **kwargs)
    # Enviar notificaciones unificadas si está habilitado
    if notification_service and result.get("success") and not kwargs.get("skip_unified_notifications"):
        await self._send_unified_notifications(notification_service, user_id, result, accion)
    return result

async def _flujo_mi_nueva_accion(self, user_id: int, parametro_especifico: str, bot=None) -> Dict[str, Any]:
    try:
        # 1. Validar parámetros
        if not parametro_especifico:
            return {
                "success": False,
                "message": "Parámetro requerido no proporcionado",
                "action": "validation_error"
            }
        
        # 2. Procesar lógica específica
        # ... implementación específica
        
        # 3. Interactuar con otros servicios si es necesario
        emotional_result = await self.emotional_state_service.analyze_interaction_emotion(
            user_id, {"type": "mi_nueva_accion", "data": parametro_especifico}
        )
        
        # 4. Retornar resultado
        return {
            "success": True,
            "message": "Nueva acción completada exitosamente",
            "emotional_state": emotional_result.value,
            "action": "nueva_accion_completada"
        }
        
    except Exception as e:
        logger.exception(f"Error en nueva acción para usuario {user_id}: {e}")
        return {
            "success": False,
            "message": "Error procesando nueva acción",
            "error": str(e),
            "action": "nueva_accion_error"
        }
```

3. **Agregar Eventos del EventBus (opcional):**
```python
# En _emit_workflow_events()
elif accion == AccionUsuario.MI_NUEVA_ACCION:
    await self.event_bus.publish(
        EventType.CUSTOM_ACTION,  # Definir nuevo tipo si es necesario
        user_id,
        {
            "parametro_especifico": result.get("parametro_especifico"),
            "emotional_state": result.get("emotional_state")
        },
        source="coordinador_central",
        correlation_id=correlation_id
    )
```

### Escenario 2: Integrar Nuevo Servicio con Interfaces Existentes

**Ejemplo: Crear un servicio de recomendaciones que use estados emocionales**

1. **Crear la Interfaz:**
```python
# services/interfaces/recommendation_interface.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .emotional_state_interface import EmotionalContext

class IRecommendationService(ABC):
    @abstractmethod
    async def get_personalized_recommendations(self, user_id: int, 
                                             emotional_context: EmotionalContext,
                                             category: str = "general") -> List[Dict[str, Any]]:
        pass
```

2. **Implementar el Servicio:**
```python
# services/recommendation_service.py
from .interfaces.recommendation_interface import IRecommendationService
from .interfaces.emotional_state_interface import EmotionalState

class RecommendationService(IRecommendationService):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_personalized_recommendations(self, user_id: int,
                                             emotional_context: EmotionalContext,
                                             category: str = "general") -> List[Dict[str, Any]]:
        
        recommendations = []
        
        # Lógica basada en estado emocional
        if emotional_context.primary_state == EmotionalState.CURIOUS:
            recommendations.extend(await self._get_exploratory_content(user_id))
        elif emotional_context.primary_state == EmotionalState.FRUSTRATED:
            recommendations.extend(await self._get_supportive_content(user_id))
        elif emotional_context.primary_state == EmotionalState.EXCITED:
            recommendations.extend(await self._get_engaging_content(user_id))
        
        # Ajustar intensidad
        for rec in recommendations:
            rec["priority"] = rec.get("priority", 1.0) * emotional_context.intensity
        
        return sorted(recommendations, key=lambda x: x["priority"], reverse=True)
```

3. **Integrar con CoordinadorCentral:**
```python
# En CoordinadorCentral.__init__()
self.recommendation_service = RecommendationService(session)

# Nuevo método de flujo
async def get_personalized_recommendations(self, user_id: int, category: str = "general") -> Dict[str, Any]:
    try:
        # Obtener contexto emocional actual
        emotional_context = await self.emotional_state_service.get_user_emotional_state(user_id)
        
        # Obtener recomendaciones personalizadas
        recommendations = await self.recommendation_service.get_personalized_recommendations(
            user_id, emotional_context, category
        )
        
        return {
            "success": True,
            "recommendations": recommendations,
            "emotional_context": emotional_context.primary_state.value,
            "category": category
        }
        
    except Exception as e:
        logger.exception(f"Error obteniendo recomendaciones para usuario {user_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error obteniendo recomendaciones personalizadas"
        }
```

### Escenario 3: Manejar Estados Emocionales en Narrativa Existente

**Modificar un handler narrativo existente para usar contexto emocional:**

```python
# En un handler de narrativa
@narrative_router.callback_query(F.data.startswith("fragment:"))
async def handle_narrative_fragment(callback: CallbackQuery, session: AsyncSession):
    fragment_key = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    # Usar coordinador para integración completa
    coordinator = CoordinadorCentral(session)
    
    # 1. Analizar interacción emocional
    interaction_data = {
        "type": "fragment_selection",
        "fragment_key": fragment_key,
        "selection_time": datetime.now().isoformat()
    }
    
    emotional_result = await coordinator.ejecutar_flujo(
        user_id,
        AccionUsuario.ANALIZAR_ESTADO_EMOCIONAL,
        interaction_data=interaction_data
    )
    
    # 2. Obtener fragmento contextualizado
    if hasattr(coordinator.narrative_service, 'get_contextualized_fragment'):
        emotional_context = await coordinator.emotional_state_service.get_user_emotional_state(user_id)
        contextualized_fragment = await coordinator.narrative_service.get_contextualized_fragment(
            user_id, fragment_key, emotional_context
        )
        content = contextualized_fragment.adapted_content
    else:
        # Fallback a método tradicional
        fragment = await coordinator.narrative_service.get_fragment_by_key(fragment_key)
        content = fragment.content
    
    # 3. Personalizar entrega de contenido
    content_package = await coordinator.content_delivery_service.prepare_content(
        fragment_key,
        {
            "text": content,
            "reply_markup": create_narrative_keyboard(fragment_key)
        }
    )
    
    await coordinator.content_delivery_service.deliver_content(
        content_package,
        {
            "bot": callback.bot,
            "message": callback.message
        }
    )
    
    # 4. Completar flujo narrativo
    completion_result = await coordinator.ejecutar_flujo(
        user_id,
        AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
        fragment_id=fragment_key,
        bot=callback.bot
    )
    
    await callback.answer()
```

## Monitoreo y Debugging

### 1. Event History

El EventBus mantiene un historial de eventos para debugging:

```python
event_bus = get_event_bus()
recent_events = event_bus.get_event_history(50)

for event in recent_events:
    print(f"{event.timestamp}: {event.event_type.value} - User {event.user_id}")
    print(f"  Source: {event.source}, Correlation: {event.correlation_id}")
    print(f"  Data: {event.data}")
```

### 2. System Health Check

El CoordinadorCentral incluye capacidades de health check:

```python
coordinator = CoordinadorCentral(session)

# Health check comprehensivo
health_report = await coordinator.perform_system_health_check()
print(f"System Status: {health_report['overall_status']}")

if health_report["recommendations"]:
    print("Recommendations:")
    for rec in health_report["recommendations"]:
        print(f"  - {rec}")
```

### 3. Consistency Checks

Para verificar consistencia de datos entre módulos:

```python
# Check específico de usuario
consistency_report = await coordinator.check_system_consistency(user_id=123456)

if consistency_report["checks"]["issues_found"] > 0:
    print("Inconsistencias encontradas:")
    for error in consistency_report["errors"]:
        print(f"  ERROR: {error}")
    for warning in consistency_report["warnings"]:
        print(f"  WARNING: {warning}")
```

### 4. Logging y Correlation IDs

Todos los workflows soportan correlation IDs para tracking:

```python
# Al ejecutar workflows
result = await coordinator.ejecutar_flujo_async(
    user_id,
    AccionUsuario.MI_ACCION,
    correlation_id="user_session_123",
    **data
)

# Los logs incluirán el correlation_id para facilitar debugging
```

## Mejores Prácticas de Implementación

### 1. Manejo de Errores

```python
try:
    result = await coordinator.ejecutar_flujo(user_id, accion, **kwargs)
    if not result["success"]:
        logger.warning(f"Flujo falló para usuario {user_id}: {result.get('message')}")
        # Implementar fallback o retry logic
        
except Exception as e:
    logger.exception(f"Error crítico en flujo {accion}: {e}")
    # Implementar recovery logic
    await coordinator.event_bus.publish(
        EventType.ERROR_OCCURRED,
        user_id,
        {"error": str(e), "workflow": accion.value},
        source="my_module"
    )
```

### 2. Dependency Injection

```python
# En lugar de instanciar servicios directamente
class MyNewService:
    def __init__(self, session: AsyncSession, emotional_manager: IEmotionalStateManager):
        self.session = session
        self.emotional_manager = emotional_manager

# Usar el patrón del CoordinadorCentral
coordinator = CoordinadorCentral(session)
my_service = MyNewService(session, coordinator.emotional_state_service)
```

### 3. Event-Driven Architecture

```python
# Suscribirse a eventos para reaccionar a cambios
async def on_points_awarded(event: Event):
    user_id = event.user_id
    points = event.data.get("points", 0)
    
    # Reaccionar automáticamente cuando se otorgan muchos puntos
    if points >= 50:
        coordinator = CoordinadorCentral(event.session)  # Obtener de contexto
        await coordinator.ejecutar_flujo(
            user_id,
            AccionUsuario.ANALIZAR_ESTADO_EMOCIONAL,
            interaction_data={"type": "high_points_awarded", "points": points}
        )

# Registrar el handler
event_bus = get_event_bus()
event_bus.subscribe(EventType.POINTS_AWARDED, on_points_awarded)
```

### 4. Testing

```python
@pytest_asyncio.fixture
async def coordinator_with_mocks(session_mock):
    coordinator = CoordinadorCentral(session_mock)
    
    # Mock de servicios para testing
    coordinator.emotional_state_service = AsyncMock()
    coordinator.content_delivery_service = AsyncMock()
    coordinator.event_bus = AsyncMock()
    
    return coordinator

@pytest.mark.asyncio
async def test_nueva_funcionalidad(coordinator_with_mocks):
    user_id = 123456
    
    # Setup mocks
    coordinator_with_mocks.emotional_state_service.get_user_emotional_state.return_value = EmotionalContext(
        primary_state=EmotionalState.NEUTRAL,
        intensity=0.5,
        secondary_states={},
        last_updated=datetime.now(),
        triggers=[]
    )
    
    # Execute
    result = await coordinator_with_mocks.ejecutar_flujo(
        user_id,
        AccionUsuario.MI_NUEVA_ACCION,
        parametro_especifico="test_value"
    )
    
    # Assert
    assert result["success"] == True
    assert "Nueva acción completada" in result["message"]
```

## Extensibilidad del Sistema

### Agregar Nuevos Tipos de Eventos

1. **Definir nuevo EventType:**
```python
# En event_bus.py
class EventType(Enum):
    # ... eventos existentes
    CUSTOM_EVENT = "custom_event"
    NEW_FEATURE_EVENT = "new_feature_event"
```

2. **Emitir eventos en workflows:**
```python
await self.event_bus.publish(
    EventType.CUSTOM_EVENT,
    user_id,
    {"custom_data": data},
    source="my_module"
)
```

### Crear Nuevas Interfaces

1. **Definir interfaz abstracta:**
```python
# services/interfaces/my_new_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class IMyNewService(ABC):
    @abstractmethod
    async def my_method(self, param: str) -> Dict[str, Any]:
        pass
```

2. **Implementar servicio concreto:**
```python
# services/my_new_service.py
from .interfaces.my_new_interface import IMyNewService

class MyNewService(IMyNewService):
    async def my_method(self, param: str) -> Dict[str, Any]:
        # Implementación específica
        return {"result": f"Processed {param}"}
```

3. **Integrar con CoordinadorCentral:**
```python
# En coordinador_central.py
self.my_new_service = MyNewService(session)
```

---

*Este manual documenta el estado actual de las interfaces implementadas y se actualizará conforme evolucione el sistema.*