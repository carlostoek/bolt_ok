# Project Structure - DianaBot

## Directory Organization

### Core Structure
```
/
├── handlers/           # Request handlers organized by functionality
│   ├── admin/         # Administrative functionality
│   ├── vip/           # VIP-specific features
│   ├── main_menu.py   # Primary navigation
│   ├── shop_handlers.py # Commerce and store
│   └── narrative_handler.py # Story progression
├── services/          # Business logic layer
│   ├── integration/   # Cross-system coordination
│   ├── narrative_service.py
│   ├── point_service.py
│   └── coordinador_central.py # Main orchestrator
├── database/          # Data layer
│   ├── models.py      # Core models
│   ├── emotional_models.py
│   └── narrative_models.py
├── keyboards/         # Telegram inline keyboards
├── middlewares/       # Request processing middleware
├── states/           # FSM state definitions
└── utils/            # Utility functions
```

## Handler Organization

### Naming Conventions
- **Descriptive names**: `shop_handlers.py`, `narrative_handler.py`
- **Domain grouping**: VIP features in `vip/` directory
- **Admin separation**: Administrative functions in `admin/` directory

### Router Registration Pattern
Handlers registered in `bot.py` with priority order:
1. Setup and admin handlers (highest priority)
2. Core functionality (start, main menu)
3. Feature-specific handlers (shop, narrative, etc.)
4. Catch-all handlers (lowest priority)

## Service Layer Patterns

### Integration Architecture
- **CoordinadorCentral**: Main facade for cross-system operations
- **Specialized services**: Domain-specific logic (narrative, points, emotions)
- **Integration services**: Handle cross-system workflows

### Service Responsibilities
- **Business logic**: Core functionality implementation
- **Data access**: Database operations and caching
- **External integration**: Telegram API interactions
- **State management**: User session and progress tracking

## Database Patterns

### Model Separation
- **Functional domains**: Separate models by business domain
- **Relationship management**: Clear foreign key relationships
- **Migration strategy**: Database schema evolution handling

### Session Management
- **Middleware injection**: Sessions provided via middleware
- **Proper cleanup**: Sessions closed in finally blocks
- **Transaction management**: Explicit commit/rollback handling

## Character System Structure

### Voice and Personality
- **CharacterVoiceService**: Maintains character consistency
- **Emotional context**: Tracks and responds to user emotional state
- **Character types**: Enum-based character identification

### Narrative Progression
- **Level-based access**: Free (1-3) vs VIP (4-6) levels
- **Decision tracking**: User choices affect story progression
- **Memory system**: Characters remember user interactions

## Code Style Guidelines

### Python Conventions
- **PEP 8 compliance**: Standard Python style guide
- **Async patterns**: Use async/await throughout
- **Type hints**: For complex functions and service interfaces
- **Docstrings**: Comprehensive documentation for services

### File Organization
- **Single responsibility**: Each file has clear, focused purpose
- **Import organization**: Local imports, then external, then stdlib
- **Configuration**: Environment variables via `.env`

## Testing Structure

### Test Organization
```
tests/
├── test_emotional_models.py
├── test_emotional_analysis_service.py
├── emotional/
│   └── test_emotional_integration.py
└── [additional test files]
```

### Testing Patterns
- **Unit tests**: Individual service testing
- **Integration tests**: Cross-system functionality
- **Emotional system tests**: Character voice and analysis validation

## Configuration Management

### Environment Variables
- **Sensitive data**: Tokens, keys, credentials in `.env`
- **Feature flags**: Enable/disable functionality
- **Channel configuration**: Free and VIP channel IDs

### Settings Pattern
- **utils/config.py**: Centralized configuration access
- **Validation**: Required environment variables checked at startup
- **Defaults**: Sensible fallbacks where appropriate

## Error Handling Patterns

### Logging Strategy
- **Structured logging**: Consistent format across all components
- **Multiple outputs**: File and console logging
- **Error levels**: Appropriate use of INFO, WARNING, ERROR, CRITICAL

### Exception Management
- **Global error handler**: Centralized error processing
- **Graceful degradation**: System continues operating when possible
- **User-friendly messages**: Errors translated to user-appropriate responses

## Development Workflow

### File Creation Guidelines
- **Edit over create**: Prefer extending existing files when logical
- **Modular additions**: New features as separate handlers/services
- **Integration points**: Use CoordinadorCentral for cross-system features

### Feature Implementation
1. **Handler**: User interaction logic
2. **Service**: Business logic implementation
3. **Database**: Model updates if needed
4. **Integration**: Connect to existing systems via coordinator
5. **Testing**: Validate functionality and character consistency

## Deployment Considerations

### File Dependencies
- **requirements.txt**: Python package dependencies
- **bot.py**: Main entry point with comprehensive setup
- **database/setup.py**: Database initialization
- **.env**: Environment configuration (not in repository)

### Process Management
- **Graceful shutdown**: Proper cleanup of background tasks
- **Resource management**: Database connections and file handles
- **Error recovery**: Automatic restart capabilities