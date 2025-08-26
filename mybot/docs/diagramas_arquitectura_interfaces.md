# Diagramas de Arquitectura y Flujos del Sistema de Interfaces

## Diagrama de Arquitectura General

```mermaid
graph TB
    %% Capa de Presentación
    subgraph "Telegram Bot Layer"
        TG[Telegram Bot]
        H[Message Handlers]
        CB[Callback Handlers]
        CH[Command Handlers]
    end
    
    %% Capa de Coordinación
    subgraph "Coordination Layer"
        CC[CoordinadorCentral]
        EB[EventBus]
        EC[EventCoordinator]
    end
    
    %% Capa de Interfaces
    subgraph "Interface Layer"
        IES[IEmotionalStateManager]
        ICD[IContentDeliveryService]
        IUI[IUserInteractionProcessor]
        IUN[IUserNarrativeService]
    end
    
    %% Capa de Servicios
    subgraph "Service Implementation Layer"
        ESS[EmotionalStateService]
        CDS[ContentDeliveryService]
        UIS[UserInteractionService]
        UIP[UserInteractionProcessor]
        NS[NarrativeService]
    end
    
    %% Capa de Integración
    subgraph "Integration Services"
        CES[ChannelEngagementService]
        NPS[NarrativePointService]
        NAS[NarrativeAccessService]
        UMS[UnifiedMissionService]
        NotS[NotificationService]
    end
    
    %% Base de Datos
    subgraph "Database Layer"
        DB[(Database)]
        EM[Emotional Models]
        NM[Narrative Models]
        UM[User Models]
    end
    
    %% Conexiones principales
    TG --> H
    TG --> CB
    TG --> CH
    
    H --> CC
    CB --> CC
    CH --> CC
    
    CC --> EB
    CC --> EC
    CC --> IES
    CC --> ICD
    CC --> IUI
    CC --> IUN
    
    IES -.implements.-> ESS
    ICD -.implements.-> CDS
    IUI -.implements.-> UIS
    IUI -.implements.-> UIP
    IUN -.implements.-> NS
    
    CC --> CES
    CC --> NPS
    CC --> NAS
    CC --> UMS
    CC --> NotS
    
    ESS --> DB
    CDS --> DB
    UIS --> DB
    NS --> DB
    
    DB --> EM
    DB --> NM
    DB --> UM
    
    %% Event flows
    EB -.events.-> ESS
    EB -.events.-> NS
    EB -.events.-> UMS
    EB -.events.-> NotS
    
    style CC fill:#ff9999
    style EB fill:#99ccff
    style IES fill:#99ff99
    style ICD fill:#99ff99
    style IUI fill:#99ff99
    style IUN fill:#99ff99
```

## Flujo de Procesamiento de Interacciones

```mermaid
sequenceDiagram
    participant User as Usuario
    participant TG as Telegram Bot
    participant CC as CoordinadorCentral
    participant UIP as UserInteractionProcessor
    participant ESS as EmotionalStateService
    participant CDS as ContentDeliveryService
    participant EB as EventBus
    participant DB as Database
    
    User->>TG: Envía mensaje/callback
    TG->>CC: ejecutar_flujo_async()
    CC->>UIP: process_interaction()
    
    UIP->>DB: Validar usuario
    DB-->>UIP: Usuario válido
    
    UIP->>ESS: analyze_interaction_emotion()
    ESS->>DB: Consultar estado actual
    DB-->>ESS: Estado emocional
    ESS->>DB: Actualizar estado si necesario
    ESS-->>UIP: Estado emocional inferido
    
    UIP->>CC: Resultado de interacción
    CC->>ESS: get_recommended_content_tone()
    ESS-->>CC: Tono recomendado
    
    CC->>CDS: prepare_content()
    CDS->>CDS: personalize_content()
    CDS-->>CC: ContentPackage
    
    CC->>CDS: deliver_content()
    CDS->>TG: Enviar mensaje personalizado
    TG-->>User: Mensaje adaptado emocionalmente
    
    CC->>EB: publish(WORKFLOW_COMPLETED)
    EB->>EB: Notify subscribers
    
    CC->>DB: Log interacción
    
    Note over CC,EB: Eventos asíncronos no bloquean flujo principal
```

## Flujo de Estados Emocionales

```mermaid
stateDiagram-v2
    [*] --> NEUTRAL: Usuario nuevo
    
    NEUTRAL --> CURIOUS: Explorar contenido
    NEUTRAL --> ENGAGED: Interacción positiva
    NEUTRAL --> CONFUSED: Dificultad/error
    
    CURIOUS --> ENGAGED: Contenido interesante
    CURIOUS --> EXCITED: Descubrimiento importante
    CURIOUS --> CONFUSED: Contenido complejo
    
    ENGAGED --> SATISFIED: Completar tarea
    ENGAGED --> EXCITED: Gran progreso
    ENGAGED --> FRUSTRATED: Obstáculo
    
    CONFUSED --> FRUSTRATED: Errores repetidos
    CONFUSED --> CURIOUS: Obtener ayuda
    CONFUSED --> NEUTRAL: Reset/tiempo
    
    FRUSTRATED --> CONFUSED: Reducir intensidad
    FRUSTRATED --> NEUTRAL: Intervención/descanso
    FRUSTRATED --> ENGAGED: Resolver problema
    
    SATISFIED --> ENGAGED: Continuar actividad
    SATISFIED --> EXCITED: Nuevo logro
    SATISFIED --> NEUTRAL: Finalizar sesión
    
    EXCITED --> ENGAGED: Mantener momentum
    EXCITED --> SATISFIED: Completar objetivo
    EXCITED --> NEUTRAL: Calmar intensidad
    
    note right of NEUTRAL
        Estado por defecto
        Intensidad: 0.0-0.3
    end note
    
    note right of EXCITED
        Estado de alta energía
        Intensidad: 0.7-1.0
    end note
    
    note right of FRUSTRATED
        Requiere intervención
        Trigger: failed_attempts >= 3
    end note
```

## Arquitectura de EventBus

```mermaid
graph LR
    subgraph "Event Publishers"
        CC[CoordinadorCentral]
        ESS[EmotionalStateService]
        NS[NarrativeService]
        PS[PointService]
    end
    
    subgraph "EventBus Core"
        EB[EventBus]
        EH[Event History]
        SL[Subscriber Lists]
        SH[Safe Handler Executor]
    end
    
    subgraph "Event Subscribers"
        UMS[UnifiedMissionService]
        NotS[NotificationService]
        AS[AchievementService]
        RS[ReconciliationService]
        CUSTOM[Custom Handlers]
    end
    
    subgraph "Event Types"
        UR[USER_REACTION]
        PA[POINTS_AWARDED]
        ND[NARRATIVE_DECISION]
        AU[ACHIEVEMENT_UNLOCKED]
        WC[WORKFLOW_COMPLETED]
        EO[ERROR_OCCURRED]
    end
    
    CC -->|publish| EB
    ESS -->|publish| EB
    NS -->|publish| EB
    PS -->|publish| EB
    
    EB --> SL
    EB --> EH
    EB --> SH
    
    EB -->|notify| UMS
    EB -->|notify| NotS
    EB -->|notify| AS
    EB -->|notify| RS
    EB -->|notify| CUSTOM
    
    SL -.contains.-> UR
    SL -.contains.-> PA
    SL -.contains.-> ND
    SL -.contains.-> AU
    SL -.contains.-> WC
    SL -.contains.-> EO
    
    style EB fill:#ff9999
    style EH fill:#99ccff
    style SH fill:#ffcc99
```

## Flujo de Integración Cross-Módulo

```mermaid
flowchart TD
    A[Usuario interactúa] --> B{Tipo de interacción}
    
    B -->|Fragmento narrativo| C[Completar fragmento]
    B -->|Reacción canal| D[Procesar reacción]
    B -->|Comando| E[Ejecutar comando]
    
    C --> F[Analizar estado emocional]
    D --> F
    E --> F
    
    F --> G[Actualizar contexto emocional]
    G --> H[Procesar lógica específica]
    
    H --> I{Otorgar puntos?}
    I -->|Sí| J[Actualizar puntos]
    I -->|No| K[Continuar flujo]
    
    J --> L[Verificar logros/niveles]
    K --> M[Obtener tono recomendado]
    L --> M
    
    M --> N[Personalizar contenido]
    N --> O[Entregar contenido]
    O --> P[Emitir eventos]
    
    P --> Q{Notificaciones unificadas?}
    Q -->|Sí| R[Queue notificaciones]
    Q -->|No| S[Finalizar]
    
    R --> T[Procesar batch notificaciones]
    T --> S
    
    %% Event flows (asynchronous)
    P -.-> U[Event: WORKFLOW_COMPLETED]
    J -.-> V[Event: POINTS_AWARDED]
    G -.-> W[Event: EMOTIONAL_STATE_CHANGED]
    
    U -.-> X[Subscribers react]
    V -.-> X
    W -.-> X
    
    style F fill:#99ff99
    style G fill:#99ff99
    style M fill:#99ccff
    style N fill:#99ccff
    style P fill:#ff9999
```

## Flujo de Content Delivery Contextualizado

```mermaid
sequenceDiagram
    participant CC as CoordinadorCentral
    participant ESS as EmotionalStateService
    participant CDS as ContentDeliveryService
    participant UNS as UserNarrativeService
    participant User as Usuario
    
    CC->>ESS: get_user_emotional_state(user_id)
    ESS-->>CC: EmotionalContext
    
    CC->>ESS: get_recommended_content_tone(user_id)
    ESS-->>CC: "supportive" | "energetic" | "gentle"
    
    alt Si es contenido narrativo
        CC->>UNS: get_contextualized_fragment(user_id, fragment_id, emotional_context)
        UNS->>UNS: Adaptar contenido según emoción
        UNS-->>CC: ContextualizedFragment
        CC->>CDS: prepare_content(fragment_id, adapted_context)
    else Contenido general
        CC->>CDS: prepare_content(content_id, emotional_context)
    end
    
    CDS->>CDS: personalize_content(template, user_context)
    CDS-->>CC: ContentPackage
    
    CC->>CDS: validate_delivery_constraints(package, context)
    CDS-->>CC: (valid: true, errors: [])
    
    CC->>CDS: deliver_content(package, delivery_context)
    CDS->>User: Mensaje personalizado con tono emocional
    CDS-->>CC: success: true
    
    Note over ESS,User: Todo el contenido se adapta al estado emocional del usuario
```

## Diagrama de Dependencias entre Interfaces

```mermaid
graph TD
    subgraph "Core Interfaces"
        IES[IEmotionalStateManager]
        ICD[IContentDeliveryService] 
        IUI[IUserInteractionProcessor]
        IUN[IUserNarrativeService]
    end
    
    subgraph "Support Interfaces"
        IPS[IPointService]
        INS[INotificationService]
        IAS[IAchievementService]
    end
    
    subgraph "Implementation Classes"
        ESS[EmotionalStateService]
        CDS[ContentDeliveryService]
        UIS[UserInteractionService]
        UIP[UserInteractionProcessor]
        UNS[UserNarrativeServiceImpl]
    end
    
    subgraph "Integration Layer"
        CC[CoordinadorCentral]
        EB[EventBus]
    end
    
    %% Interface implementations
    IES -.implements.-> ESS
    ICD -.implements.-> CDS
    IUI -.implements.-> UIS
    IUI -.implements.-> UIP
    IUN -.implements.-> UNS
    
    %% Dependencies between interfaces
    IUI -->|uses| IES
    IUI -->|uses| IPS
    IUI -->|uses| INS
    
    IUN -->|uses| IES
    IUN -->|uses| ICD
    
    ICD -->|can use| IES
    
    %% CoordinadorCentral orchestrates all
    CC -->|orchestrates| IES
    CC -->|orchestrates| ICD
    CC -->|orchestrates| IUI
    CC -->|orchestrates| IUN
    CC -->|orchestrates| IPS
    CC -->|orchestrates| INS
    CC -->|orchestrates| IAS
    
    %% EventBus connects everything
    EB -.events.-> ESS
    EB -.events.-> UNS
    EB -.events.-> CC
    
    CC -->|publishes to| EB
    
    style CC fill:#ff9999
    style EB fill:#99ccff
    style IES fill:#99ff99
    style ICD fill:#99ff99
    style IUI fill:#99ff99
    style IUN fill:#99ff99
```

## Flujo de Transacciones Complejas

```mermaid
sequenceDiagram
    participant Client as Cliente
    participant CC as CoordinadorCentral
    participant TM as TransactionManager
    participant ESS as EmotionalStateService
    participant NS as NarrativeService
    participant PS as PointService
    participant DB as Database
    
    Client->>CC: Operación compleja multi-servicio
    CC->>TM: with_transaction(complex_workflow)
    
    TM->>DB: BEGIN TRANSACTION
    
    TM->>ESS: Actualizar estado emocional
    ESS->>DB: UPDATE emotional_states
    DB-->>ESS: OK
    
    TM->>NS: Completar fragmento narrativo
    NS->>DB: UPDATE narrative_progress
    DB-->>NS: OK
    
    TM->>PS: Otorgar puntos
    PS->>DB: UPDATE user_points
    DB-->>PS: OK
    
    alt Todo exitoso
        TM->>DB: COMMIT TRANSACTION
        DB-->>TM: COMMITTED
        TM-->>CC: Success + results
        CC-->>Client: Operation completed
    else Error en algún paso
        TM->>DB: ROLLBACK TRANSACTION
        DB-->>TM: ROLLED BACK
        TM-->>CC: Error + partial results
        CC-->>Client: Operation failed (rolled back)
    end
    
    Note over TM,DB: Atomicidad garantizada
```

## Patrón de Recuperación ante Fallas

```mermaid
flowchart TD
    A[Ejecutar operación] --> B{¿Exitosa?}
    
    B -->|Sí| C[Continuar flujo normal]
    B -->|No| D{¿Es servicio crítico?}
    
    D -->|Sí| E[Intentar recovery]
    D -->|No| F[Usar fallback]
    
    E --> G{¿Recovery exitoso?}
    G -->|Sí| C
    G -->|No| H[Log error crítico]
    
    F --> I[Ejecutar fallback]
    I --> J{¿Fallback exitoso?}
    J -->|Sí| K[Continuar con funcionalidad reducida]
    J -->|No| L[Falla graceful]
    
    H --> M[Notificar administradores]
    L --> N[Mensaje de error al usuario]
    K --> O[Log uso de fallback]
    
    C --> P[Emitir eventos de éxito]
    M --> Q[Sistema en modo degradado]
    N --> R[Operación abortada]
    O --> S[Funcionalidad parcial]
    
    style E fill:#ff9999
    style F fill:#99ccff
    style H fill:#ff6666
    style L fill:#ff6666
```

## Monitoreo y Health Checks

```mermaid
graph TB
    subgraph "Monitoring System"
        HC[Health Check Coordinator]
        SHC[System Health Check]
        CSC[Consistency Check]
        PSC[Performance Stats]
    end
    
    subgraph "Services Being Monitored"
        CC[CoordinadorCentral]
        EB[EventBus]
        ESS[EmotionalStateService]
        CDS[ContentDeliveryService]
        UIP[UserInteractionProcessor]
    end
    
    subgraph "Monitoring Outputs"
        HS[Health Status]
        PM[Performance Metrics]
        AL[Alert Logs]
        REC[Recommendations]
    end
    
    HC --> SHC
    HC --> CSC
    HC --> PSC
    
    SHC --> CC
    SHC --> EB
    SHC --> ESS
    SHC --> CDS
    SHC --> UIP
    
    CSC --> CC
    PSC --> CC
    
    CC --> HS
    EB --> PM
    ESS --> AL
    
    HS --> REC
    PM --> REC
    AL --> REC
    
    %% Health check results
    HS -.status.-> HEALTHY[Healthy]
    HS -.status.-> DEGRADED[Degraded]
    HS -.status.-> UNHEALTHY[Unhealthy]
    
    style HC fill:#99ff99
    style HEALTHY fill:#99ff99
    style DEGRADED fill:#ffcc99
    style UNHEALTHY fill:#ff9999
```

---

*Estos diagramas representan la arquitectura actual del sistema de interfaces implementado y sus flujos de integración.*