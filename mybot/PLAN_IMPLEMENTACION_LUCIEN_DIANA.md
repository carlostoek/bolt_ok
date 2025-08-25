# Plan de Implementación: El Mayordomo del Diván

## Resumen Ejecutivo

Este documento presenta un plan detallado para transformar el bot Diana en "El Mayordomo del Diván", un sistema narrativo donde Lucien actúa como guardián principal y Diana aparece como figura misteriosa en momentos clave. La implementación aprovecha la arquitectura existente del bot mientras introduce nuevas mecánicas de narrativa evolutiva.

## Fases de Implementación

### Fase 1: Preparación y Modelos de Datos (Tiempo estimado: 3-4 días)

#### 1.1. Extensión de Modelos de Base de Datos
- **Actualizar `database/narrative_unified.py`**:
  - Añadir campos específicos de Lucien al modelo `UserNarrativeState`:
    - `lucien_trust_level`: Nivel de confianza con Lucien (Float, default 0.0)
    - `lucien_interaction_count`: Contador de interacciones (Integer, default 0)
    - `diana_appearances`: Registro de apariciones de Diana (JSON, default list)
    - `narrative_level`: Nivel narrativo del usuario (Integer, default 1)
    - `archetype`: Arquetipo identificado del usuario (String, nullable)
  - Añadir campos al modelo `NarrativeFragment`:
    - `presenter`: Quién presenta el fragmento (String, default "lucien")
    - `diana_appearance_threshold`: Nivel de confianza mínimo (Float, default 1.0)
    - `narrative_level_required`: Nivel narrativo requerido (Integer, default 1)
    - `is_temporal`: Indica fragmento restringido por tiempo (Boolean, default False)
    - `temporal_weekdays`: Días de la semana disponibles (JSON, nullable)
    - `temporal_hours`: Horas del día disponibles (JSON, nullable)

#### 1.2. Extensión del Sistema de Eventos
- **Actualizar `services/event_bus.py`**:
  - Añadir nuevos tipos de eventos para dinámica Lucien-Diana:
    - `LUCIEN_CHALLENGE_ISSUED`
    - `LUCIEN_CHALLENGE_COMPLETED`
    - `LUCIEN_TRUST_INCREASED`
    - `DIANA_APPEARED`
    - `QUANTUM_FRAGMENT_CHANGED`
    - `NARRATIVE_LEVEL_ADVANCED`

#### 1.3. Extensión del Enum AccionUsuario
- **Actualizar `services/coordinador_central.py`**:
  - Añadir nuevos tipos de acción:
    - `LUCIEN_CHALLENGE`
    - `LUCIEN_DIALOGUE`
    - `DIANA_APPEARANCE`
    - `QUANTUM_TRIGGER`

### Fase 2: Servicios Core (Tiempo estimado: 5-7 días)

#### 2.1. Implementación del LucienService
- **Crear `services/lucien_service.py`**:
  - Métodos principales:
    - `handle_initial_greeting`: Saludo inicial después de solicitud de canal
    - `evaluate_user_reaction`: Evaluación de reacciones del usuario
    - `determine_diana_appearance`: Lógica para apariciones de Diana
    - `interpret_reaction`: Interpretación de reacciones emocionales
    - `create_challenge`: Creación de desafíos de observación
    - `format_challenge_presentation`: Formateo de presentación de desafíos
    - `explain_quantum_change`: Explicación de cambios en fragmentos cuánticos
    - `explain_diana_reaction`: Contextualización de apariciones de Diana
    - `get_temporal_moment_introduction`: Introducción para momentos temporales

#### 2.2. Implementación del ObservationChallengeService
- **Crear `services/observation_challenge_service.py`**:
  - Métodos principales:
    - `create_observation_challenge`: Creación de desafíos de observación
    - `evaluate_observation_attempt`: Evaluación de intentos de resolución
    - `get_challenge`: Obtención de detalles de desafío
    - `start_challenge`: Inicialización de desafío para usuario

#### 2.3. Implementación del NarrativeReactionService
- **Crear `services/narrative_reaction_service.py`**:
  - Métodos principales:
    - `register_reaction`: Registro e interpretación de reacciones emocionales
    - `get_reactions_history`: Obtención del historial de reacciones
    - `calculate_reaction_pattern`: Análisis de patrones de reacción

#### 2.4. Implementación del QuantumFragmentService
- **Crear `services/quantum_fragment_service.py`**:
  - Métodos principales:
    - `apply_quantum_trigger`: Aplicación de disparadores cuánticos
    - `_find_affected_fragments`: Determinación de fragmentos afectados
    - `_modify_fragment_perception`: Modificación de fragmentos pasados

#### 2.5. Implementación del TemporalMomentService
- **Crear `services/temporal_moment_service.py`**:
  - Métodos principales:
    - `get_available_moments`: Obtención de momentos disponibles por tiempo
    - `_calculate_expiration_minutes`: Cálculo de tiempo de expiración
    - `schedule_moment_notification`: Programación de notificaciones temporales

#### 2.6. Implementación del DianaAppearanceService
- **Crear `services/diana_appearance_service.py`**:
  - Métodos principales:
    - `get_diana_response`: Obtención de respuesta de Diana según contexto
    - `_get_diana_reaction_responses`: Respuestas a reacciones específicas
    - `_get_diana_milestone_responses`: Respuestas a hitos narrativos
    - `register_diana_reaction`: Registro de reacciones a apariciones
    - `_record_diana_appearance`: Registro de apariciones en historial

### Fase 3: Extensión de Servicios Existentes (Tiempo estimado: 3-5 días)

#### 3.1. Extensión del CoordinadorCentral
- **Actualizar `services/coordinador_central.py`**:
  - Añadir método `_flujo_lucien_diana_dynamic`: Orquestación de dinámica Lucien-Diana
  - Integrar con `_emit_workflow_events`: Publicación de eventos específicos
  - Extender `handle_user_action`: Soporte para nuevos tipos de acción

#### 3.2. Extensión del NotificationService
- **Actualizar `services/notification_service.py`**:
  - Extender `_build_enhanced_unified_message`: Soporte para mensajes de Lucien y Diana
  - Añadir tipos de notificación: `lucien_message` y `diana_appearance`
  - Implementar formateo especial para apariciones de Diana

#### 3.3. Integración con DianaMenuSystem
- **Actualizar `services/diana_menu_system.py`**:
  - Añadir sección de menú para Desafíos de Lucien
  - Integrar con niveles de confianza para desbloqueo progresivo

### Fase 4: Handlers y Frontend (Tiempo estimado: 5-7 días)

#### 4.1. Implementación de ChannelHandler
- **Crear/Actualizar `handlers/channel_handlers.py`**:
  - Implementar `handle_join_request`: Manejo de solicitudes de canal
  - Implementar funciones auxiliares:
    - `send_lucien_welcome`: Envío de bienvenida de Lucien (5 min)
    - `approve_channel_request`: Aprobación automática (15 min)

#### 4.2. Implementación de LucienChallengeHandlers
- **Crear `handlers/lucien_challenge_handlers.py`**:
  - Implementar router para desafíos:
    - `handle_lucien_challenge`: Manejo de interacciones con desafíos
    - Estados FSM para flujo de respuesta a desafíos

#### 4.3. Implementación de LucienReactionHandlers
- **Crear `handlers/lucien_handlers.py`**:
  - Implementar router para reacciones:
    - `handle_lucien_reaction`: Manejo de reacciones a fragmentos
  - Integrar con sistema de reacciones emocionales

#### 4.4. Implementación de DianaHandlers
- **Crear `handlers/diana_handlers.py`**:
  - Implementar router para apariciones:
    - `handle_diana_reaction`: Manejo de reacciones a apariciones
  - Integrar con sistema de apariciones raras

#### 4.5. Actualización de UI y Teclados
- **Crear `keyboards/lucien_keyboards.py`**:
  - Teclados para desafíos de observación
  - Teclados para reacciones emocionales (comprendo, duda, asombro, temor)

### Fase 5: Pruebas y Refinamiento (Tiempo estimado: 3-4 días)

#### 5.1. Implementación de Pruebas Unitarias
- **Crear pruebas para cada servicio nuevo**:
  - `tests/services/test_lucien_service.py`
  - `tests/services/test_observation_challenge_service.py`
  - `tests/services/test_narrative_reaction_service.py`
  - `tests/services/test_quantum_fragment_service.py`
  - `tests/services/test_temporal_moment_service.py`
  - `tests/services/test_diana_appearance_service.py`

#### 5.2. Implementación de Pruebas de Integración
- **Crear pruebas de integración**:
  - `tests/integration/test_lucien_diana_flow.py`:
    - `test_lucien_diana_full_flow`: Flujo completo desde solicitud
    - `test_lucien_challenge_progression`: Progresión de desafíos
    - `test_diana_appearance_impact`: Impacto de apariciones de Diana

#### 5.3. Datos de Prueba y Seeds
- **Crear scripts de seed para datos iniciales**:
  - `scripts/seed_lucien_challenges.py`: Desafíos de observación iniciales
  - `scripts/seed_quantum_fragments.py`: Fragmentos cuánticos iniciales
  - `scripts/seed_temporal_moments.py`: Momentos temporales iniciales

## Consideraciones Técnicas

### Integración con Sistemas Existentes
- Utilizar CoordinadorCentral como orquestador principal
- Extender NotificationService para mensajes diferenciados
- Utilizar EventBus para transiciones entre personajes
- Aprovechar sistema narrativo unificado para diálogos contextuales
- Integrar con DianaMenuSystem para experiencia fluida

### Manejo de Estado y Concurrencia
- Implementar bloqueos de semáforo para transiciones Lucien-Diana
- Utilizar transacciones para operaciones de estado cuántico
- Implementar caching para respuestas de personajes frecuentes

### Estrategia de Mitigación de Riesgos
- **Riesgo de Consistencia Narrativa**: Implementar capa de validación para respuestas de personajes
- **Riesgo de Equilibrio de Progresión**: Crear herramientas de monitoreo para tasas de progreso
- **Riesgo de Aparición de Diana**: Establecer límites estrictos de tasa de aparición

## Cronograma Estimado

| Fase | Actividad | Tiempo Estimado |
|------|-----------|-----------------|
| 1    | Preparación y Modelos | 3-4 días |
| 2    | Servicios Core | 5-7 días |
| 3    | Extensión de Servicios | 3-5 días |
| 4    | Handlers y Frontend | 5-7 días |
| 5    | Pruebas y Refinamiento | 3-4 días |
| **Total** | | **19-27 días** |

## Conclusión

Este plan de implementación transforma el bot Diana en "El Mayordomo del Diván" aprovechando la arquitectura existente mientras introduce mecánicas sofisticadas de narrativa evolutiva. La implementación se enfoca en crear una experiencia donde Lucien actúa como guardián formal y Diana aparece como figura misteriosa en momentos significativos, manteniendo un balance narrativo y progresión cuidadosamente diseñados.