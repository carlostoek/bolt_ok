# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Telegram bot built with `aiogram` (v3+) and SQLAlchemy. The bot, called "Diana", implements a gamified interactive narrative experience with VIP subscription features, reaction systems, and channel engagement functionality. The bot has multiple user roles (free, VIP, admin) and integrates several core modules:

- Narrative system (interactive storytelling)
- Gamification (points, missions, achievements)
- Admin management
- Channel/community features
- Auction system

## Common Commands

### Running the Bot

```bash
# Start the bot
python bot.py
```

### Running Tests

```bash
# Run all tests with pytest (recomendado para tests asíncronos)
python -m pytest tests/

# Run a specific test file
python -m pytest tests/services/test_reaction_system.py

# Run a specific test function
python -m pytest tests/integration/test_narrative_admin_integration.py::test_view_fragment_integration

# Run with verbose output
python -m pytest -v tests/

# Run with coverage report
python -m pytest --cov=. --cov-report=term-missing

# Run narrative admin tests specifically
./run_narrative_admin_tests.py

# Run with scripts de utilidad
./test.sh           # Ejecutar todos los tests
./test.sh quick     # Ejecutar tests rápidos
./test.sh coverage  # Ejecutar tests con cobertura
```

### Notification System Script

```bash
# Verify unified notifications
python scripts/verify_unified_notifications.py

# Migrate to unified notifications
python scripts/migrate_to_unified_notifications.py
```

## System Architecture

The application is built using a modular architecture with several key components:

### Core Components

1. **CoordinadorCentral**: Central coordinator that orchestrates integration between different modules. Implements a Facade pattern to simplify subsystem interaction. Located in `services/coordinador_central.py`.

2. **Diana Menu System**: Unified interface between admin, gamification, and narrative modules. Provides a cohesive user experience. Located in `services/diana_menu_system.py`.

3. **Event Bus**: Centralized event dispatching system for module communication. Implements a publish-subscribe pattern.

4. **Database Layer**: SQLAlchemy models in `database/models.py` and `database/narrative_unified.py`. Note: `database/narrative_models.py` is now deprecated; use the unified models instead.

### Key Services

- **UserNarrativeService**: Manages interactive storylines and user progress using the unified narrative models
- **PointService**: Handles user points economy and transactions
- **MissionService**: Manages user missions and completion criteria
- **AchievementService**: Handles unlocking of achievements
- **NotificationService**: Unified notification system with priority-based queuing
- **ReconciliationService**: Ensures data consistency across modules

### Middleware Components

- **UserRegistrationMiddleware**: Ensures user registration in the database
- **PointsMiddleware**: Awards points for various user interactions
- **DBSessionMiddleware**: Injects database sessions into handlers

### Handlers Organization

Handlers are organized by functionality:
- `handlers/admin/`: Administrative functions
- `handlers/vip/`: VIP user features
- `handlers/user/`: Regular user functionality
- Root handlers directory: Common functionality shared across user types

## Diana Menu System Integration

The Diana Menu System provides a unified interface across all modules:

1. **Usage**:
   - Use `/diana` command to access the main Diana menu
   - Use `/diana_admin` for admin panel

2. **Integration Bridge**:
   ```python
   from services.diana_menu_integration_impl import get_compatibility_bridge
   
   async def my_handler(callback: CallbackQuery, session: AsyncSession):
       # Try Diana first
       diana_bridge = get_compatibility_bridge(session)
       handled = await diana_bridge.bridge_user_menu(callback)
       
       # Fall back to existing system if needed
       if not handled:
           # Existing logic here
   ```

3. **Menu Structure**:
   - Admin menu: Configuration and system management
   - User menu: Main user interface
   - Narrative menu: Storytelling interface
   - Gamification menu: Points, missions, achievements

## Development Guidelines

1. **Commit Strategy**:
   - Make commits after each implementation is complete
   - Avoid referencing external tools in commits

2. **Error Handling**:
   - Use the global error handler for critical errors
   - Implement try/except blocks in handlers for user-facing errors
   - Use logging extensively with appropriate levels

3. **New Feature Integration**:
   - Coordinate through CoordinadorCentral for cross-module features
   - Use the EventBus for asynchronous communication between modules
   - Implement proper notification integration with the unified notification system

4. **Testing**:
   - Add unit tests for new services in `tests/services/`
   - Add integration tests for cross-module functionality in `tests/integration/`
   - Use the fixtures in `tests/conftest.py` for database and bot mocking
   - Para tests asíncronos, usar `@pytest.mark.asyncio` y `@pytest_asyncio.fixture`
   - Configurar correctamente AsyncMock para context managers asíncronos

## Database Operations

The system uses SQLAlchemy with both sync and async operations:

```python
# Example of database operations in a handler
async def my_handler(message: Message, session: AsyncSession):
    # Query
    result = await session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()
    
    # Update
    if user:
        user.points += 10
        await session.commit()
```

## Notification System

The notification system supports priority-based aggregation:

```python
# Example of sending unified notifications
from services.notification_service import NotificationService, NotificationPriority

notification_service = NotificationService(session, bot)

# Add notification to queue
await notification_service.add_notification(
    user_id=123456789,
    type="points",
    data={"points": 10, "total": 100},
    priority=NotificationPriority.MEDIUM
)

# Send immediate notification
await notification_service.send_immediate_notification(
    user_id=123456789,
    message="¡Mensaje importante!",
    priority=NotificationPriority.CRITICAL
)
```

## Common Flows and Patterns

1. **User Reaction Processing**:
   - Reactions are processed through CoordinadorCentral
   - Points are awarded and notifications sent
   - Missions and achievements may be triggered

2. **Narrative Progression**:
   - Users navigate through story fragments using the unified narrative system
   - Decisions can unlock different paths through the choice system
   - Triggers in fragments can award points, unlock clues, and more
   - VIP content requires subscription

3. **Gamification Integration**:
   - Points earned through engagement and reactions
   - Missions completed based on user actions
   - Achievements unlocked for special accomplishments

This documentation should be updated as new features are added or architectural changes are made to the system.

## Configuración y Herramientas de Testing Asíncrono

### Scripts de Desarrollo

```bash
# Configurar entorno de desarrollo
./setup.sh

# Ejecutar el bot en modo desarrollo
./dev.sh

# Ejecutar tests
./test.sh

# Ejecutar tests específicos de narrativa admin
./run_narrative_admin_tests.py
```

### Mocking Correcto para Tests Asíncronos

```python
# Configuración correcta para mocks de SQLAlchemy async
session_mock = AsyncMock()
mock_context = AsyncMock()
mock_context.__aenter__.return_value = session_mock
session_mock.begin.return_value = mock_context

# Mocks para aiogram 3
callback = MagicMock()
callback.answer = AsyncMock()
```

### Fixtures de pytest-asyncio

```python
# En conftest.py
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

@pytest.fixture(scope="session")
def event_loop():
    """Crear loop de eventos para tests async."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Crear engine de test con SQLite en memoria."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="session")
async def session_factory(test_engine):
    """Factory para crear sesiones de test."""
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    return factory

@pytest_asyncio.fixture
async def session(session_factory):
    """Sesión de base de datos para test individual."""
    async with session_factory() as session:
        yield session
```

## Documentation

- [Sistema de Notificaciones Unificadas](docs/sistema_notificaciones.md)
- [Sistema de Gestión de Solicitudes de Canal](docs/sistema_gestion_solicitudes_canal.md)
- [Sistema Narrativo Unificado](docs/LECTURA_FORZOSA_ANTES_DE_CUALQUIER_IMPLEMENTACIÓN.md)
- [Guía del Sistema Administrativo de Narrativa](docs/guia_sistema_administrativo_narrativa.md)
- [Configuración del Entorno de Desarrollo](README_SETUP.md)
- [Solución de Problemas](TROUBLESHOOTING.md)