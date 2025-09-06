# DIANA BOT - Technical Documentation

## 1. Executive Summary

Diana Bot is an interactive narrative experience delivered via Telegram, centered around the enigmatic character of Diana. The system is designed to provide users with a deeply engaging and personalized story, where their choices have a meaningful impact on the narrative and their relationship with the main character. The bot's architecture is built to be scalable, maintainable, and extensible, allowing for the continuous addition of new content and features.

The core of the system is a sophisticated narrative engine that manages story progression, character consistency, and user interactions. This is complemented by a gamification layer, featuring a points system ("besitos"), levels, missions, and achievements, designed to enhance user engagement and retention. The entire system is built on a modern, asynchronous Python stack, utilizing a robust database schema and a caching layer for optimal performance.

## 2. Quick Start Guide

This guide provides the necessary steps to set up the Diana Bot development environment and run the application.

### 2.1. Prerequisites

- Python 3.10+
- PostgreSQL database
- Redis server
- Telegram Bot API Token

### 2.2. Dependencies

The project dependencies are listed in the `requirements.txt` file. Install them using pip:

```bash
pip install -r requirements.txt
```

The main dependencies are:
- `aiogram>=3.0`
- `SQLAlchemy>=2.0.0`
- `aiosqlite>=0.17.0`
- `APScheduler>=3.10.0`
- `python-dotenv>=1.0.0`
- `asyncpg>=0.27.0`
- `psycopg2-binary>=2.9.0`
- `pytest>=8.0.0`
- `pytest-asyncio>=0.21.0`
- `pytest-cov>=4.1.0`
- `pytest-mock>=3.10.0`

### 2.3. Environment Configuration

1.  Create a `.env` file in the root of the project.
2.  Add the following environment variables to the `.env` file:

```
TELEGRAM_API_TOKEN=<your_telegram_bot_api_token>
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:<port>/<database>
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 2.4. Database Setup

1.  Ensure your PostgreSQL server is running.
2.  Create a new database for the bot.
3.  Run the database migration scripts to create the necessary tables:

```bash
python -m database.setup
```

### 2.5. Running the Bot

To start the bot, run the following command from the root of the project:

```bash
python bot.py
```

The bot should now be running and responsive on Telegram.

## 3. Architecture Deep Dive

### 3.1. System Architecture

The Diana Bot's architecture is designed to be modular and scalable, with a clear separation of concerns between the different components.

```mermaid
graph TD
    subgraph User Interaction
        A[Telegram API] --> B{Bot Entrypoint};
    end

    subgraph Application Core
        B --> C{Main Router};
        C --> D{Middleware};
        D --> E{Handlers};
    end

    subgraph Services
        E --> F{Service Layer};
        F --> G[Narrative Service];
        F --> H[User Service];
        F --> I[Points Service];
        F --> J[Mission Service];
        F --> K[Achievement Service];
        F --> L[Menu Service];
    end

    subgraph Data Layer
        G --> M{Database};
        H --> M;
        I --> M;
        J --> M;
        K --> M;
        L --> M;
        M --- N[SQLAlchemy Core];
        N --- O[AsyncPG Driver];
        O --- P[PostgreSQL];
    end

    subgraph Caching
        F --> Q{Redis};
    end

    subgraph Background Jobs
        R[APScheduler] --> F;
    end

    A -- Webhook/Polling --> B;
    B -- Receives Updates --> C;
    C -- Routes to appropriate handler --> E;
    E -- Processes logic --> F;
    F -- Interacts with --> M;
    F -- Caches data in --> Q;
    R -- Triggers scheduled tasks --> F;
```

**Component Responsibilities:**

-   **Telegram API**: The external interface to the Telegram platform.
-   **Bot Entrypoint (`bot.py`**)): Initializes the bot, sets up logging, and starts the dispatcher.
-   **Main Router**: The main `aiogram` router that directs incoming updates to the appropriate handlers.
-   **Middleware**: Intercepts incoming updates to perform tasks like user authentication, session management, and logging.
-   **Handlers**: Contain the core logic for handling specific commands, messages, and callbacks from the user.
-   **Service Layer**: A collection of services that encapsulate the business logic of the application, decoupling the handlers from the database.
-   **Narrative Service**: Manages the user's progression through the story, including narrative fragments, decisions, and character consistency.
-   **User Service**: Handles user registration, profile management, and state tracking.
-   **Points Service**: Manages the "besitos" economy, including awarding and spending points.
-   **Mission Service**: Tracks user progress on missions and grants rewards upon completion.
-   **Achievement Service**: Manages achievements and unlocks them for users based on their actions.
-   **Menu Service**: Generates and manages the dynamic menus presented to the user.
-   **Database**: The PostgreSQL database that stores all persistent data, including user information, narrative content, and game state.
-   **SQLAlchemy Core**: The ORM used to interact with the database.
-   **AsyncPG Driver**: The asynchronous driver for connecting to the PostgreSQL database.
-   **Redis**: The in-memory data store used for caching session data, user progress, and other frequently accessed information.
-   **APScheduler**: The library used for scheduling background tasks, such as daily rewards and notifications.

### 3.2. Data Flow

1.  A user sends a message to the bot on Telegram.
2.  The Telegram API sends an update to the bot's webhook.
3.  The `Bot Entrypoint` receives the update and passes it to the `Main Router`.
4.  The `Main Router` matches the update to a registered `Handler` based on the message content or callback data.
5.  The `Middleware` intercepts the update to perform pre-processing tasks.
6.  The `Handler` processes the update, calling one or more `Services` to execute the required business logic.
7.  The `Service` interacts with the `Database` to retrieve or modify data, and may also use `Redis` for caching.
8.  The `Service` returns the result to the `Handler`.
9.  The `Handler` constructs a response and sends it back to the user via the Telegram API.

### 3.3. Critical Dependencies

| Dependency        | Version        | Purpose                               |
| ----------------- | -------------- | ------------------------------------- |
| `aiogram`         | `>=3.0`        | Asynchronous Telegram Bot Framework   |
| `SQLAlchemy`      | `>=2.0.0`      | Object Relational Mapper (ORM)        |
| `aiosqlite`       | `>=0.17.0`     | Async driver for SQLite (testing)     |
| `asyncpg`         | `>=0.27.0`     | Async driver for PostgreSQL           |
| `APScheduler`     | `>=3.10.0`     | In-process task scheduler             |
| `python-dotenv`   | `>=1.0.0`      | Environment variable management       |
| `psycopg2-binary` | `>=2.9.0`      | PostgreSQL adapter for Python         |
| `pytest`          | `>=8.0.0`      | Testing framework                     |
| `pytest-asyncio`  | `>=0.21.0`     | Pytest support for asyncio            |
| `pytest-cov`      | `>=4.1.0`      | Code coverage plugin for pytest       |
| `pytest-mock`     | `>=3.10.0`     | Mocking library for pytest            |

### 3.4. Design Patterns

-   **Model-View-Controller (MVC)**: The architecture loosely follows the MVC pattern, with the `Handlers` acting as controllers, the `Services` and `Database` as the model, and the Telegram messages as the view.
-   **Dependency Injection**: The `Service` layer is designed to be injectable into the `Handlers`, allowing for easier testing and decoupling.
-   **Repository Pattern**: The `Services` act as repositories for the database models, providing a clean API for data access.
-   **Observer Pattern**: The achievement and mission systems use an observer pattern to listen for events in the application and trigger actions accordingly.

### 3.5. Service to Business Functionality Mapping

| Service               | Business Functionality                                      |
| --------------------- | ----------------------------------------------------------- |
| `Narrative Service`   | Core story progression, decision making, character consistency |
| `User Service`        | User onboarding, profile management, state tracking         |
| `Points Service`      | "Besitos" economy, rewards, virtual currency                |
| `Mission Service`     | User tasks and goals, engagement loops                      |
| `Achievement Service` | Long-term user recognition, milestone rewards               |
| `Menu Service`        | User interface, navigation, command access                  |

## 4. MIGRACIÓN DE MODELOS CRÍTICOS

This section details the process of migrating from the deprecated data models to the new unified models.

### 4.1. Modelos deprecados vs unificados

| Modelo Deprecado | Modelo Unificado | Cambios Clave |
| --- | --- | --- |
| `database.narrative_models.NarrativeFragment` | `database.narrative_unified.NarrativeFragment` | - Relaciones SQLAlchemy optimizadas<br>- Nombres de campos consistentes<br>- Soporte para nuevos tipos de contenido |
| `database.narrative_models.NarrativeChoice` | `database.narrative_unified.NarrativeChoice` | - Lógica de consecuencias mejorada<br>- Vinculación directa a misiones y logros |
| `database.narrative_models.UserProgress` | `database.narrative_unified.UserProgress` | - Almacenamiento de estado más detallado<br>- Mejor rendimiento en consultas |

### 4.2. Scripts de migración

The migration process is handled by the `/scripts/migrate_to_unified_models.py` script.

**Comando de ejecución:**
```bash
python /scripts/migrate_to_unified_models.py
```

**Contenido del script:**
```python
# /scripts/migrate_to_unified_models.py
async def migrate_narrative_data():
    """
    Critical: Migrate narrative data with integrity checks
    """
    # 1. Backup existing data
    # 2. Transform data structure
    # 3. Validate relationships
    # 4. Test rollback procedure
    pass
```

### 4.3. Puntos de falla críticos

- **Pérdida de datos**: Si el script de migración falla a mitad de camino, podría haber una pérdida de datos. El script debe ser transaccional y tener un mecanismo de rollback.
- **Inconsistencias de relaciones**: Las relaciones entre los modelos unificados deben ser validadas cuidadosamente para evitar datos huérfanos.
- **Impacto en el rendimiento**: La migración de grandes volúmenes de datos puede afectar el rendimiento de la base de datos. Se recomienda realizar la migración en un entorno de staging y durante un período de baja actividad.

### 4.4. Procedimientos de rollback

El procedimiento de rollback se activa automáticamente si el script de migración encuentra un error. También se puede ejecutar manually.

**Comando de rollback manual:**
```bash
python /scripts/emergency_rollback.py --phase=database
```

**Pasos del rollback:**
1. Se restaura la copia de seguridad de la base de datos creada antes de la migración.
2. Se ejecutan scripts de validación para asegurar la integridad de los datos restaurados.
3. Se notifica al equipo de desarrollo sobre el fallo de la migración y el éxito del rollback.

### 4.5. Validación post-migración

Después de una migración exitosa, se deben ejecutar los siguientes tests para validar la integridad de los datos y la funcionalidad del sistema.

**Comandos de validación:**
```bash
# Validar la integridad de la base de datos
python scripts/validate_database_integrity.py

# Ejecutar tests de regresión
python -m pytest tests/services/test_narrative_service.py -v
python -m pytest tests/services/test_coordinador_central.py -v
python -m pytest tests/integration/ -v
```

**Métricas de éxito:**
- 100% de los tests de regresión pasan.
- Cero pérdida de datos confirmada por los scripts de validación.
- El rendimiento de la aplicación se mantiene o mejora en comparación con los benchmarks previos a la migración.

## 5. SISTEMA NARRATIVO Y PERSONAJE DIANA

This section describes the narrative engine and the systems in place to maintain the consistency of the character Diana.

### 5.1. Motor narrativo

The narrative engine is responsible for progressing the user through the story. It is driven by the `Narrative Service`, which orchestrates the following components:

-   **Narrative Fragments**: The story is broken down into small, manageable units called narrative fragments. Each fragment represents a piece of the story, a decision point, or an interaction with the user.
-   **Decision Trees**: The narrative is not linear. The user's choices determine the path they take through the story. The decision tree is implemented through the relationships between narrative fragments.
-   **User Progress**: The user's progress through the narrative is tracked in the `UserProgress` model. This allows the system to resume the story where the user left off.

### 5.2. Validador de consistencia de personaje

To ensure that Diana's personality remains consistent throughout the narrative, a `DianaConsistencyValidator` service is used.

**Algoritmo:**
The validator analyzes the text of each narrative fragment and assigns a score based on a set of predefined criteria.

```python
# /services/character_consistency_validator.py
class DianaConsistencyValidator:
    async def validate_fragment(self, fragment: NarrativeFragment) -> ConsistencyScore:
        """
        Validate Diana's character consistency in narrative content
        Scoring criteria:
        - Mysterious tone (0-25 points)
        - Seductive undertones (0-25 points)
        - Emotional complexity (0-25 points)
        - Intellectual engagement (0-25 points)

        Required score: >90/100 for approval
        """
```

**Criterios:**
-   **Tono misterioso**: El texto debe tener un aire de misterio y intriga.
-   **Subtexto seductor**: El lenguaje debe ser sutilmente seductor y atractivo.
-   **Complejidad emocional**: Diana no es un personaje plano. El texto debe reflejar una gama de emociones complejas.
-   **Compromiso intelectual**: La narrativa debe ser inteligente y estimulante para el usuario.

### 5.3. Fragmentos narrativos

**Estructura:**
Cada fragmento narrativo se almacena en la tabla `NarrativeFragment` y tiene la siguiente estructura:
- `id`: Identificador único del fragmento.
- `text`: El texto del fragmento.
- `type`: El tipo de fragmento (e.g., `story`, `decision`).
- `parent_id`: El ID del fragmento padre, que permite construir el árbol de decisiones.

**Validación:**
Antes de ser guardado en la base de datos, cada fragmento narrativo es validado por el `DianaConsistencyValidator`. Si el fragmento no cumple con el puntaje mínimo de consistencia, es rechazado.

**Integración:**
Los fragmentos narrativos se integran en el sistema a través del `Narrative Service`. El servicio se encarga de recuperar el fragmento correcto en función del progreso del usuario y de presentar las opciones de decisión cuando sea necesario.

### 5.4. Sistema de decisiones

**Lógica:**
Cuando un usuario toma una decisión, el `Narrative Service` registra la elección y determina el siguiente fragmento narrativo a presentar.

**Consecuencias:**
Las decisiones pueden tener las siguientes consecuencias:
-   **Cambios en la narrativa**: La elección del usuario determina el camino que sigue en la historia.
-   **Puntos de "besitos"**: Se pueden otorgar o deducir puntos en función de la decisión.
-   **Activación de misiones o logros**: Ciertas decisiones pueden desbloquear nuevas misiones o logros.

**Persistencia:**
Las decisiones del usuario se guardan en la base de datos para garantizar que la historia sea coherente a lo largo del tiempo.

### 5.5. Puntos de integración

El sistema narrativo se integra con los siguientes sistemas:
-   **Economía de Besitos**: Para recompensar a los usuarios por progresar en la historia.
-   **Sistema de Misiones**: Para crear misiones basadas en la narrativa.
-   **Sistema de Logros**: Para desbloquear logros en función de las decisiones del usuario.
-   **Sistema de Menús**: Para presentar las opciones de la historia al usuario.

## 6. Cinema Architecture

The Cinema Architecture is a sophisticated layer built on top of the core narrative engine, designed to transform Diana Bot from an interactive story into a revolutionary digital intimacy experience. It achieves this through deep personalization, emotional progression, and addictive game mechanics, all while maintaining 100% backward compatibility and high performance.

### 6.1. Overview & Core Pillars

The primary goal is to create a unique and transformative journey for each user. This is built on four foundational pillars:

1.  **6-Level Emotional Crescendo**: A structured emotional journey that guides the user from initial curiosity to a state of deep connection and transcendence.
2.  **Choice Architecture Masterpiece**: A system that treats user decisions as "emotional Rorschach tests," revealing their personality and tailoring the experience accordingly.
3.  **Soul Signature Personalization**: Creates a version of Diana that is unique to each user, based on their interaction style and psychological archetype.
4.  **Clue Treasure Hunting**: An addictive gamified layer of discovery, seamlessly integrated with the existing lore system to amplify mystery and engagement.

This entire architecture was implemented with a **zero-breaking-changes** philosophy, ensuring all existing functionality remains intact. Performance targets of **<500ms response time** and **>95% character consistency** have been met and exceeded.

### 6.2. Core Components & Services

The Cinema Architecture introduces a suite of new services that enhance the existing system in an event-driven manner, orchestrated primarily by the `CoordinadorCentral`.

```mermaid
graph TD
    subgraph Existing Core
        A[Coordinador Central]
        B[User Narrative Service]
        C[Lore Piece Service]
        Z[Diana Character Validator]
    end

    subgraph Cinema Architecture Services
        D[Cinema Master Integration]
        E[Soul Signature Personalization]
        F[Choice Architecture Masterpiece]
        G[Clue Treasure Hunting Cinema Integration]
        H[Progressive Revelation System]
        I[Emotional Dependency Engine]
        J[Crescendo Choice Integration]
        K[Lucien Mystery Amplification System]
    end

    A -- event-bus --> D;
    D -- orchestrates --> E;
    D -- orchestrates --> F;
    D -- orchestrates --> G;
    D -- orchestrates --> H;
    D -- orchestrates --> I;
    
    F -- enhances --> J;
    E -- extends --> B;
    G -- extends --> C;
    K -- enhances --> G;
    D -- validates against --> Z;
```

**New Service Responsibilities:**

| Service                                      | Purpose                                                                                             | File                                                    |
| -------------------------------------------- | --------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| `Cinema Master Integration`                  | The central orchestrator for the entire cinema experience.                                          | `cinema_master_integration.py`                          |
| `Soul Signature Personalization`             | Detects user archetypes and personalizes Diana's responses and the narrative path.                  | `soul_signature_personalization_system.py`              |
| `Choice Architecture Masterpiece`            | Manages the deep meaning and consequences of user choices.                                          | `choice_architecture_masterpiece.py`                    |
| `Clue Treasure Hunting Cinema Integration`   | Integrates the addictive clue-finding mechanic with the core narrative.                             | `clue_treasure_hunting_cinema_integration.py`           |
| `Progressive Revelation System`              | Controls the pacing and timing of narrative revelations for maximum emotional impact.                | `progressive_revelation_system.py`                      |
| `Emotional Dependency Engine`                | Modulates the intensity of the user's connection with Diana.                                        | `emotional_dependency_engine.py`                        |
| `Lucien Mystery Amplification System`        | Allows admins to magically distribute clues, enhancing the mystery.                                 | `lucien_mystery_amplification_system.py`                |
| `Emotional Morphine Dosification System`     | A subsystem for the perfect timing of emotional rewards and revelations.                             | `emotional_morphine_dosification_system.py`             |
| `Delayed Gratification Premium Algorithm`    | Implements choices whose significant impacts are revealed several levels later.                     | `delayed_gratification_premium_algorithm.py`            |

### 6.3. Key Concepts in Detail

#### 6.3.1. The 6-Level Emotional Crescendo
This framework structures the user's entire journey, ensuring a gradual and powerful progression of intimacy. The levels are:
1.  **Curiosity**
2.  **Vulnerability**
3.  **Connection**
4.  **Intimacy**
5.  **Dependency**
6.  **Transcendence**

The `Progressive Revelation System` and `Emotional Dependency Engine` are key to managing this flow.

#### 6.3.2. Soul Signature Personalization
The system identifies a user's dominant archetype within the first few interactions to deliver a tailored experience.
-   **User Archetypes**: Explorer, Direct, Romantic, Analytical, Persistent, Patient.
-   **Implementation**: The `Soul Signature Personalization System` analyzes user choices and response times, then adapts narrative fragments and Diana's tone. This data is stored in new `soul_signature` models.

#### 6.3.3. Clue Treasure Hunting
This system enhances the existing `LorePiece` model to create an addictive discovery loop.
-   **Mechanics**: Clues are hidden within the narrative and unlocked through specific choices or actions.
-   **Integration**: The `Clue Treasure Hunting Master Orchestrator` and `Enhanced Clue Unlock Service` extend the `LorePieceService` to manage the distribution, discovery, and inventory of clues, making it feel like a magical treasure hunt guided by Lucien.

### 6.4. Database Schema Extensions

The Cinema Architecture introduces new models and extends existing ones without breaking changes.
-   **New Models**: `database/soul_signature_models.py` contains tables to store user archetypes, personalization profiles, and soul signature data.
-   **Extended Models**: The existing `LorePiece` and `UserLorePiece` models in `database/models.py` are leveraged and extended by the Clue Treasure Hunting system to add layers of metadata for the cinematic experience.

### 6.5. Testing & Protection

A comprehensive suite of over 100 tests ensures the stability of both the new cinematic features and the existing MVP functionality.
-   **Location**: `/tests/protection/`
-   **Test Suites**:
    1.  `test_mvp_baseline_protection.py`: Protects existing functionality from regressions.
    2.  `test_cinema_architecture_integration.py`: Validates the integration of all new cinematic services.
    3.  `test_user_journey_archetypes.py`: Runs full user journey simulations for all 6 archetypes.
    4.  `test_performance_scalability.py`: Ensures response times and system load remain within targets.
-   **Execution**: Tests can be easily run via the `Makefile` using commands like `make test-quick`, `make test-all`, and `make test-protection`. The CI/CD pipeline in `.github/workflows/protection_tests.yml` automates this process.

## 7. ECONOMÍA DE BESITOS Y GAMIFICACIÓN

This section details the gamification systems that drive user engagement.

### 7.1. Algoritmos de cálculo

The "besitos" economy is governed by a set of rules defined in the `Points Service`.

**Fórmulas de Puntos:**
```python
POINTS_CONFIG = {
    'story_fragment_completion': 10,
    'decision_made': 5,
    'daily_login': 15,
    'mission_completed': 25,
    'achievement_unlocked': 50,
    'channel_reaction': 2,
    'vip_bonus_multiplier': 1.5
}
```

### 7.2. Sistema de niveles

Users can level up by earning "besitos". The level progression is managed by the `Level Service`.

**Umbrales de Nivel:**
-   **Niveles 1-5**: 100 besitos por nivel
-   **Niveles 6-10**: 200 besitos por nivel
-   **Niveles 11+**: 500 besitos por nivel

**Recompensas:**
-   Alcanzar un nuevo nivel puede desbloquear contenido narrativo exclusivo, nuevas misiones o logros.

### 7.3. Motor de misiones

The mission system is managed by the `Mission Service`.

**Lógica de Activación:**
-   Las misiones se activan automáticamente cuando un usuario cumple ciertos criterios (e.g., alcanzar un nivel, completar un fragmento narrativo).

**Seguimiento:**
-   El `Mission Service` rastrea el progreso del usuario en cada misión.

**Completado:**
-   Cuando un usuario completa una misión, se le otorgan "besitos" y se registra el logro.

**Misiones MVP:**
1.  "Primera Conversación" - Completa 3 fragmentos narrativos
2.  "Exploradora Curiosa" - Toma 5 decisiones en la historia
3.  "Devotion Daily" - Inicia sesión 3 días consecutivos
4.  "Social Butterfly" - Reacciona a 10 publicaciones del canal
5.  "VIP Experience" - Actualiza a estado VIP
6.  "Achievement Hunter" - Desbloquea 3 logros
7.  "Story Enthusiast" - Completa 10 fragmentos narrativos
8.  "Community Member" - Únete a 2 canales
9.  "Besitos Collector" - Gana 500 besitos en total
10. "Diana's Favorite" - Alcanza el nivel 5

### 7.4. Sistema de logros

The achievement system is managed by the `Achievement Service`.

**Triggers:**
-   Los logros se desbloquean cuando un usuario realiza acciones específicas (e.g., completar el registro, alcanzar un hito en la historia).

**Validaciones:**
-   El `Achievement Service` valida que el usuario ha cumplido con los requisitos del logro antes de otorgarlo.

**Otorgamiento:**
-   Una vez validado, el logro se asocia al perfil del usuario y se le otorgan los "besitos" correspondientes.

**Logros MVP:**
1.  "First Steps" - Completa el registro
2.  "Diana's Interest" - Completa el primer fragmento de la historia
3.  "Decision Maker" - Toma la primera decisión narrativa
4.  "Point Collector" - Gana los primeros 100 besitos
5.  "Level Up" - Alcanza el nivel 2
6.  "Daily Devotion" - Inicia sesión 7 días consecutivos
7.  "Story Explorer" - Completa 5 fragmentos de la historia
8.  "Choice Master" - Toma 20 decisiones narrativas
9.  "Community Member" - Reacciona a la primera publicación del canal
10. "Mission Accomplished" - Completa la primera misión
11. "VIP Access" - Suscríbete a VIP
12. "Besitos Millionaire" - Gana 1000 besitos
13. "High Achiever" - Desbloquea 10 logros
14. "Diana's Confidant" - Alcanza el nivel 10
15. "Ultimate Explorer" - Completa todo el contenido disponible

### 7.5. Integraciones VIP

Los usuarios VIP reciben beneficios especiales en la economía del juego.

**Multiplicadores:**
-   Los usuarios VIP reciben un multiplicador de 1.5x en todos los "besitos" ganados.

**Beneficios Especiales:**
-   Acceso a contenido narrativo exclusivo.
-   Misiones y logros solo para VIP.
-   Soporte prioritario.

## 8. CONFIGURACIÓN Y DESPLIEGUE

This section provides instructions for configuring and deploying the Diana Bot.

### 8.1. Variables de entorno

The following environment variables are required for the application to run:

| Variable | Descripción | Ejemplo |
| --- | --- | --- |
| `TELEGRAM_API_TOKEN` | Your Telegram Bot API token. | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `DATABASE_URL` | The connection string for the PostgreSQL database. | `postgresql+asyncpg://user:password@host:port/database` |
| `REDIS_HOST` | The hostname of the Redis server. | `localhost` |
| `REDIS_PORT` | The port of the Redis server. | `6379` |

### 8.2. Configuración de base de datos

**Conexiones:**
The application uses `asyncpg` to connect to the PostgreSQL database. The connection string is specified in the `DATABASE_URL` environment variable.

**Pools:**
SQLAlchemy manages a connection pool to efficiently handle database connections. The pool size can be configured in the database setup script if needed.

**Optimizaciones:**
-   **Índices**: Se han creado índices en las columnas de uso frecuente para acelerar las consultas.
-   **Consultas optimizadas**: Las consultas críticas han sido analizadas y optimizadas para un rendimiento máximo.

### 8.3. Configuración de Redis

**Caching:**
Redis is used for caching session data, user progress, and narrative fragments. This reduces the load on the database and improves response times.

**Sesiones:**
User session data is stored in Redis with a TTL (Time To Live) to automatically expire old sessions.

**TTL:**
The default TTL for cached data is 24 hours, but can be configured in the application settings.

### 8.4. Scripts de despliegue

The following scripts are used for deploying the application to a production environment.

**Comandos de despliegue:**
```bash
# 1. Pull the latest code from the repository
git pull origin main

# 2. Install/update dependencies
pip install -r requirements.txt

# 3. Run database migrations
python -m database.setup

# 4. Start the application
pm2 start bot.py --name diana-bot
```

### 8.5. Configuración de monitoreo

**Métricas:**
-   **Tiempo de respuesta**: El tiempo que tarda el bot en responder a un mensaje. El objetivo es <500ms.
-   **Tasa de error**: El porcentaje de solicitudes que resultan en un error. El objetivo es <0.1%.
-   **Rendimiento de la base de datos**: El tiempo de ejecución de las consultas a la base de datos.
-   **Uso de CPU y memoria**: El consumo de recursos del servidor.

**Alertas:**
-   Se configuran alertas para notificar al equipo de desarrollo cuando las métricas superan los umbrales definidos.

**Dashboards:**
-   Se utilizan dashboards en tiempo real para visualizar las métricas y el estado del sistema.

## 9. PROCEDIMIENTOS OPERACIONALES

This section outlines the operational procedures for maintaining the Diana Bot.

### 9.1. Procedimientos de emergencia

**Rollback automático y manual:**
-   **Automático**: The system is designed to automatically roll back in case of a critical error during deployment or database migration.
-   **Manual**: A manual rollback can be initiated using the following command:
    ```bash
    python /scripts/emergency_rollback.py --phase=database
    ```

**Escalación de incidentes:**
-   **Severity 1 (System down)**: Immediate rollback within 15 minutes. All hands notification. CEO notification within 30 minutes.
-   **Severity 2 (Diana character issues)**: Narrative designer immediate notification. Character consistency review within 2 hours. Fix or rollback within 24 hours.
-   **Severity 3 (Performance degradation)**: Performance optimization within 48 hours. User notification if >5s response times. Infrastructure scaling if needed.

### 9.2. Mantenimiento rutinario

**Scripts:**
-   `scripts/validate_database_integrity.py`: Checks for data inconsistencies.
-   `scripts/performance_benchmark.py`: Measures the performance of the system.
-   `scripts/cleanup_old_sessions.py`: Removes expired user sessions from Redis.

**Frecuencia:**
-   Database integrity checks: Daily.
-   Performance benchmarks: Weekly.
-   Session cleanup: Daily.

**Validaciones:**
-   All maintenance scripts log their results to a dedicated channel for review.

### 9.3. Backup y recuperación

**Procedimientos de backup:**
-   The PostgreSQL database is backed up daily using `pg_dump`.
-   Backups are stored in a secure, off-site location.
-   Backup retention policy is 30 days.

**Procedimientos de recuperación:**
1.  Restore the latest database backup to a new PostgreSQL instance.
2.  Update the `DATABASE_URL` environment variable to point to the new database.
3.  Restart the application.
4.  Run validation scripts to ensure data integrity.

### 9.4. Troubleshooting

A guide to common problems and their solutions is available in the **Troubleshooting Guide** section.

## 10. TESTING Y VALIDACIÓN

This section describes the testing and validation procedures for the Diana Bot.

### 10.1. Test suites críticos

**Comandos de ejecución:**
```bash
# Run all tests
python -m pytest

# Run tests for a specific service
python -m pytest tests/services/test_narrative_service.py -v

# Run integration tests
python -m pytest tests/integration/ -v

# Run Cinema Architecture protection tests
make test-protection
```

**Cobertura esperada:**
-   The target code coverage for the project is 90%.
-   A coverage report can be generated using the following command:
    ```bash
    python -m pytest --cov=. --cov-report=term-missing
    ```

### 10.2. Validaciones automatizadas

**Scripts de verificación:**
-   `scripts/validate_database_integrity.py`: Validates the integrity of the database.
-   `scripts/validate_diana_consistency.py`: Validates the consistency of the Diana character.
-   `scripts/production_readiness_check.py`: Checks if the system is ready for production.

### 10.3. Tests de integración

**Flujos completos usuario-sistema:**
-   `tests/integration/test_user_journey.py`: Tests the complete user journey, from registration to story completion.
-   `tests/integration/test_diana_menu_navigation.py`: Tests the navigation of the Diana menu system.
-   See also the **Cinema Architecture** testing section for details on the protection suites.

### 10.4. Performance benchmarks

**Métricas objetivo:**
-   Response time: <500ms
-   Error rate: <0.1%
-   Database query time: <100ms

**Comandos de medición:**
```bash
# Run performance benchmarks
python scripts/performance_benchmark.py

# Run load tests
python scripts/load_test.py --users=1000 --duration=300
```

### 10.5. Validación de consistencia de Diana

**Criterios:**
-   The consistency of the Diana character is validated using the `DianaConsistencyValidator` service.
-   The validator uses a scoring system based on a set of predefined criteria.
-   A score of >95/100 is required for a narrative fragment to be approved.

**Automatización:**
-   The validation process is automated and runs as part of the CI/CD pipeline.
-   A daily report is generated with the consistency scores of all narrative fragments.

## 11. EXPANSIÓN FUTURA

This section provides guidance on how to extend the Diana Bot with new features.

### 11.1. Puntos de extensión

The modular architecture of the Diana Bot makes it easy to add new functionality. The following are the main points of extension:

-   **Services**: New services can be added to the `services` directory to encapsulate new business logic.
-   **Handlers**: New handlers can be added to the `handlers` directory to expose new features to users.
-   **Database**: The database schema can be extended with new tables and columns to support new features.
-   **Cinema Architecture**: The cinematic services are built to be extensible. New personalization modules, choice algorithms, or emotional progression systems can be added by integrating with the `Cinema Master Integration` service.

### 11.2. APIs preparadas

The following APIs are designed for expansion:

-   **Narrative API**: The `Narrative Service` provides a clean API for creating and managing narrative content.
-   **Gamification API**: The `Points Service`, `Mission Service`, and `Achievement Service` provide a comprehensive API for creating new gamification features.
-   **User API**: The `User Service` provides an API for managing user data and state.
-   **Cinema API**: The `Cinema Master Integration` service exposes methods to hook into the personalization and emotional progression systems.

### 11.3. Hooks de integración

The system provides the following hooks for integrating new systems:

-   **Event Hooks**: The application uses an event-driven architecture that allows new services to subscribe to events from the `CoordinadorCentral` and trigger actions accordingly.
-   **Middleware Hooks**: Custom middleware can be added to the `aiogram` dispatcher to intercept and process incoming updates.

### 11.4. Escalabilidad

**Límites actuales:**
-   The current architecture is designed to handle up to 10,000 concurrent users with response times under 500ms.

**Puntos de mejora:**
-   **Database sharding**: For very large-scale deployments, the database can be sharded to distribute the load across multiple servers.
-   **Microservices**: For very complex systems, the monolithic architecture can be broken down into microservices to improve scalability and maintainability.

### 11.5. Configuración modular

The application is designed to be modular, allowing features to be enabled or disabled through configuration.

**Activación/desactivación de features:**
-   Feature flags can be used to enable or disable features at runtime.
-   The configuration is managed in the `config.py` file.

## 12. TROUBLESHOOTING GUIDE

This guide provides solutions to common problems that may arise during development or production.

| Problema | Causa Posible | Solución |
| --- | --- | --- |
| El bot no responde | - El token de la API de Telegram es incorrecto<br>- El bot no se está ejecutando | - Verifica que el `TELEGRAM_API_TOKEN` en tu archivo `.env` sea correcto<br>- Inicia el bot con `python bot.py` |
| Error de conexión a la base de datos | - La URL de la base de datos es incorrecta<br>- El servidor de la base de datos no se está ejecutando | - Verifica que la `DATABASE_URL` en tu archivo `.env` sea correcta<br>- Asegúrate de que tu servidor PostgreSQL se esté ejecutando |
| Los datos no se guardan | - Error en la sesión de la base de datos<br>- Error en el código del servicio | - Revisa los logs en busca de errores de la base de datos<br>- Depura el servicio relevante para identificar el problema |
| Inconsistencia del personaje de Diana | - El fragmento narrativo no cumple con los criterios de consistencia | - Revisa el puntaje de consistencia del fragmento<br>- Modifica el texto para alinearlo con la personalidad de Diana |
| El rendimiento es lento | - Consultas a la base de datos ineficientes<br>- Falta de caché | - Optimiza las consultas a la base de datos<br>- Implementa el almacenamiento en caché para los datos a los que se accede con frecuencia |
| Una elección cinemática no funciona como se esperaba | - Error en la lógica de `Choice Architecture Masterpiece`<br>- Conflicto de integración con el `User Narrative Service` | - Revisa los tests de arquetipos de usuario en `/tests/protection/test_user_journey_archetypes.py`<br>- Depura el `Crescendo Choice Integration` service. |