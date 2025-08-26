# Diseño de Interfaces Unificadas - Reporte Técnico

**Fecha:** 26 de agosto, 2025  
**Arquitecto:** Claude Sonnet 4  
**Versión:** 1.0  

## Resumen Ejecutivo

Se han diseñado cuatro interfaces unificadas para mejorar la consistencia y mantenibilidad del sistema narrativo de Diana Bot. Las interfaces proporcionan APIs estándar para gestión de estados emocionales, entrega de contenido, procesamiento de interacciones y operaciones narrativas unificadas.

## Análisis de Arquitectura Actual

### Interfaces Existentes

1. **IUserNarrativeService** (`services/interfaces/user_narrative_interface.py`)
   - ✅ Operaciones básicas narrativas (fragmentos, progreso, pistas)
   - ❌ Sin contexto emocional
   - ❌ Sin entrega de contenido personalizada

2. **INotificationService** (`services/interfaces/notification_interface.py`)
   - ✅ Sistema de notificaciones con prioridades
   - ✅ Agregación y cola de mensajes

3. **IPointService** (`services/interfaces/point_interface.py`)
   - ✅ Economía de puntos completa
   - ✅ Historial de transacciones

4. **IRewardSystem** (`services/interfaces/reward_interface.py`)
   - ✅ Sistema unificado de recompensas
   - ✅ Soporte para puntos, pistas y logros

### Gaps Identificados

- **Sin gestión de estados emocionales**: No hay tracking ni personalización basada en emociones del usuario
- **Sin sistema unificado de entrega de contenido**: Cada módulo maneja contenido independientemente
- **Sin procesamiento centralizado de interacciones**: Lógica dispersa entre handlers
- **Interfaz narrativa limitada**: Falta integración emocional y contextual

## Diseño de Nuevas Interfaces

### 1. IEmotionalStateManager

**Propósito:** Gestionar estados emocionales de usuarios para personalización narrativa

**Ubicación:** `services/interfaces/emotional_state_interface.py`

**Componentes Clave:**
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

**Métodos Principales:**
- `get_user_emotional_state(user_id)` → EmotionalContext
- `update_emotional_state(user_id, state, intensity, trigger)` → EmotionalContext
- `analyze_interaction_emotion(user_id, interaction_data)` → EmotionalState
- `get_recommended_content_tone(user_id)` → str

### 2. IContentDeliveryService

**Propósito:** Sistema unificado de entrega de contenido con personalización contextual

**Ubicación:** `services/interfaces/content_delivery_interface.py`

**Componentes Clave:**
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

**Métodos Principales:**
- `prepare_content(content_id, context)` → ContentPackage
- `deliver_content(package, context)` → bool
- `personalize_content(content, context)` → str
- `validate_delivery_constraints(package, context)` → Tuple[bool, List[str]]

### 3. IUserInteractionProcessor

**Propósito:** Procesamiento centralizado y consistente de todas las interacciones de usuario

**Ubicación:** `services/interfaces/user_interaction_interface.py`

**Componentes Clave:**
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

**Métodos Principales:**
- `process_interaction(context)` → InteractionResult
- `validate_interaction(context)` → Tuple[bool, List[str]]
- `log_interaction(context, result)` → None
- `get_interaction_history(user_id, limit)` → List[InteractionContext]

### 4. IUserNarrativeService (Enhanced)

**Propósito:** Extender interfaz narrativa existente con contexto emocional y entrega de contenido

**Ubicación:** `services/interfaces/user_narrative_interface.py` (modificación)

**Métodos Agregados:**
```python
@abstractmethod
async def get_contextualized_fragment(self, user_id: int, fragment_id: str, 
                                     emotional_context: EmotionalContext) -> ContentPackage:
    """Get narrative fragment adapted for user's emotional state"""

@abstractmethod  
async def process_narrative_interaction(self, user_id: int, interaction_data: Dict[str, Any]) -> InteractionResult:
    """Process narrative-specific interactions with emotional analysis"""

@abstractmethod
async def get_personalized_narrative_flow(self, user_id: int) -> List[str]:
    """Get recommended narrative path based on user state and emotions"""

@abstractmethod
async def update_narrative_emotional_impact(self, user_id: int, fragment_id: str, 
                                          emotional_response: EmotionalState) -> None:
    """Update narrative system with user's emotional response to fragment"""
```

## Especificación TDD

### Estructura de Tests

**Directorios:**
```
tests/interfaces/
├── __init__.py
├── conftest.py
├── test_emotional_state_interface.py
├── test_content_delivery_interface.py
├── test_user_interaction_interface.py
└── test_unified_narrative_interface.py
```

### Tests por Interface

1. **IEmotionalStateManager** (8 tests)
   - `test_get_user_emotional_state_new_user_returns_neutral`
   - `test_get_user_emotional_state_existing_user_returns_current_state`
   - `test_update_emotional_state_valid_parameters_updates_successfully`
   - `test_update_emotional_state_invalid_intensity_raises_validation_error`
   - `test_analyze_interaction_emotion_positive_interaction_returns_engaged`
   - `test_analyze_interaction_emotion_negative_interaction_returns_frustrated`
   - `test_get_recommended_content_tone_excited_state_returns_energetic`
   - `test_get_recommended_content_tone_confused_state_returns_supportive`

2. **IContentDeliveryService** (8 tests)
   - `test_prepare_content_valid_context_returns_personalized_package`
   - `test_prepare_content_invalid_content_id_raises_not_found_error`
   - `test_deliver_content_direct_message_channel_sends_successfully`
   - `test_deliver_content_invalid_channel_returns_false`
   - `test_personalize_content_emotional_context_adapts_tone`
   - `test_personalize_content_no_context_returns_original`
   - `test_validate_delivery_constraints_valid_package_returns_true`
   - `test_validate_delivery_constraints_violates_constraints_returns_false_with_errors`

3. **IUserInteractionProcessor** (7 tests)
   - `test_process_interaction_valid_message_returns_success_result`
   - `test_process_interaction_invalid_data_returns_failure_result`
   - `test_validate_interaction_valid_context_returns_true`
   - `test_validate_interaction_insufficient_permissions_returns_false_with_errors`
   - `test_log_interaction_successful_interaction_creates_log_entry`
   - `test_get_interaction_history_existing_user_returns_chronological_list`
   - `test_get_interaction_history_new_user_returns_empty_list`

4. **IUserNarrativeService Enhanced** (5 tests)
   - `test_get_contextualized_fragment_with_emotional_context_adapts_content`
   - `test_get_contextualized_fragment_neutral_emotion_returns_standard_content`
   - `test_process_narrative_interaction_choice_selection_updates_progress_and_emotion`
   - `test_get_personalized_narrative_flow_considers_emotional_state`
   - `test_update_narrative_emotional_impact_records_user_response`

**Total:** 28 tests específicos implementados antes de crear interfaces

## Plan de Implementación

### Fase 1: Preparación TDD
1. Crear estructura de directorios de tests
2. Implementar fixtures y mocks en `conftest.py`
3. Escribir todos los 28 tests (deben fallar inicialmente)
4. Verificar que todos fallen por razones esperadas

### Fase 2: Implementación de Interfaces
1. Crear archivos de interfaces con definiciones mínimas
2. Implementar clases concretas básicas
3. Hacer pasar tests uno por uno
4. Refactorizar manteniendo tests en verde

### Fase 3: Integración
1. Integrar con `CoordinadorCentral`
2. Actualizar `DianaMenuSystem`  
3. Crear modelos de base de datos necesarios
4. Actualizar handlers existentes

### Fase 4: Testing de Integración
1. Tests de integración entre interfaces
2. Tests end-to-end del flujo completo
3. Performance testing
4. Validación en entorno de staging

## Modelos de Base de Datos Requeridos

### Nuevas Tablas

1. **user_emotional_states**
   ```sql
   CREATE TABLE user_emotional_states (
       id SERIAL PRIMARY KEY,
       user_id BIGINT NOT NULL,
       primary_state VARCHAR(20) NOT NULL,
       intensity FLOAT NOT NULL CHECK (intensity >= 0.0 AND intensity <= 1.0),
       secondary_states JSONB DEFAULT '{}',
       triggers JSONB DEFAULT '[]',
       created_at TIMESTAMP DEFAULT NOW(),
       updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

2. **interaction_logs**
   ```sql
   CREATE TABLE interaction_logs (
       id SERIAL PRIMARY KEY,
       user_id BIGINT NOT NULL,
       interaction_type VARCHAR(20) NOT NULL,
       raw_data JSONB NOT NULL,
       result_data JSONB,
       emotional_impact VARCHAR(20),
       points_awarded INTEGER,
       created_at TIMESTAMP DEFAULT NOW()
   );
   ```

3. **content_delivery_history**
   ```sql
   CREATE TABLE content_delivery_history (
       id SERIAL PRIMARY KEY,
       user_id BIGINT NOT NULL,
       content_id VARCHAR(100) NOT NULL,
       content_type VARCHAR(20) NOT NULL,
       delivery_channel VARCHAR(20) NOT NULL,
       personalized BOOLEAN DEFAULT FALSE,
       delivered_at TIMESTAMP DEFAULT NOW()
   );
   ```

## Puntos de Integración

### CoordinadorCentral
- Registrar nuevas interfaces en el coordinador
- Implementar flujos de comunicación entre módulos
- Manejar eventos entre sistemas emocionales y narrativos

### DianaMenuSystem  
- Integrar interfaces para personalización de menús
- Usar contexto emocional para adaptar opciones
- Implementar entrega consistente de contenido

### Handlers Existentes
- Usar `IUserInteractionProcessor` para procesamiento estándar
- Integrar `IEmotionalStateManager` en handlers narrativos
- Usar `IContentDeliveryService` para todas las respuestas

## Consideraciones de Rendimiento

- **Caché de estados emocionales:** 15 minutos TTL
- **Personalización de contenido:** Async con fallback a contenido estándar
- **Logging de interacciones:** Async batch processing
- **Validación de restricciones:** Cache de reglas de validación

## Riesgos y Mitigación

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Interfaces incompatibles con sistema actual | Media | Alto | Tests de integración extensivos |
| Performance degradada por personalización | Media | Medio | Cache agresivo y fallbacks |
| Complejidad aumentada para desarrollo | Alta | Medio | Documentación detallada y ejemplos |
| Cambios de schema problemáticos | Baja | Alto | Migraciones incrementales con rollback |

## Métricas de Éxito

- **Tests:** 100% de tests pasando
- **Coverage:** >95% de cobertura de código  
- **Performance:** <100ms latencia adicional promedio
- **Adoptión:** 80% de handlers usando nuevas interfaces en 30 días
- **Bugs:** <5 bugs críticos en los primeros 30 días post-deploy

## Next Steps

1. **Inmediato:** Implementar estructura de tests TDD
2. **Semana 1:** Crear interfaces básicas y hacer pasar tests
3. **Semana 2:** Integración completa con arquitectura existente
4. **Semana 3:** Testing de integración y optimización de performance
5. **Semana 4:** Deploy a staging y validación completa

---

**Nota:** Este diseño sigue los principios SOLID y patrones establecidos en CLAUDE.md. Todas las interfaces son async-first y compatibles con aiogram v3+ y SQLAlchemy async.