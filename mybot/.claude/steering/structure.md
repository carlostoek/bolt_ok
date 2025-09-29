# Project Structure & Conventions

## Directory Organization
```
mybot/
├── services/           # Business logic and core functionality
├── handlers/          # Telegram message/callback handlers
├── database/          # Data models and database setup
├── middlewares/       # Request processing middleware
├── keyboards/         # Telegram inline keyboards and UI
├── utils/            # Shared utilities and configuration
├── states/           # FSM states for conversation flows
├── tests/            # Test suites and test utilities
├── data/             # Static data and configuration files
├── docs/             # Documentation and guides
└── examples/         # Usage examples and demos
```

## Naming Conventions
- **Files**: `snake_case.py` for all Python files
- **Classes**: `PascalCase` for class names
- **Functions/Variables**: `snake_case` for functions and variables
- **Constants**: `UPPER_SNAKE_CASE` for constants
- **Services**: Descriptive names ending in `_service.py`
- **Handlers**: Functional names ending in `_handler.py`

## Code Organization Patterns
- **Services**: One primary class per file, focused responsibility
- **Handlers**: Router-based organization with related handlers grouped
- **Models**: Database models grouped by functional area
- **Integration**: Cross-service coordination in dedicated integration services

## File Structure Standards
1. **Imports**: Standard library → Third party → Local imports
2. **Logging**: Module-level logger configuration
3. **Type Hints**: Comprehensive typing for all public interfaces
4. **Docstrings**: Class and function documentation following Google style
5. **Error Handling**: Consistent exception handling patterns

## Service Architecture Pattern
```python
class SomeService:
    """Service class with clear responsibility."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logging.getLogger(__name__)

    async def public_method(self) -> ReturnType:
        """Public interface with full documentation."""
        try:
            # Implementation with error handling
            pass
        except Exception as e:
            self.logger.error(f"Error in method: {e}")
            raise
```

## Handler Organization Pattern
```python
router = Router()

@router.message(Command("command_name"))
async def handle_command(message: Message, session: AsyncSession):
    """Handler with clear purpose and error handling."""
    try:
        # Handler implementation
        pass
    except Exception as e:
        logger.error(f"Handler error: {e}")
        await message.answer("Error occurred")
```

## Integration Guidelines
- **Cross-Service Communication**: Use `CoordinadorCentral` for complex workflows
- **Database Sessions**: Always use dependency injection for AsyncSession
- **Error Propagation**: Let business logic errors bubble up to handlers
- **Logging Context**: Include user_id and operation context in logs

## Testing Standards
- **Unit Tests**: Individual service method testing
- **Integration Tests**: Cross-service workflow testing
- **Handler Tests**: Mock-based handler testing
- **Coverage**: Aim for >80% coverage on business logic

## Documentation Requirements
- **Service Documentation**: Clear purpose, interfaces, and usage examples
- **Handler Documentation**: Command descriptions and expected flows
- **Integration Documentation**: Cross-service dependency mapping
- **Deployment Documentation**: Setup and configuration guides

## Development Workflow
1. **Feature Planning**: Define service interfaces before implementation
2. **Service-First Development**: Implement business logic before handlers
3. **Integration Testing**: Test cross-service workflows early
4. **Handler Implementation**: Build UI layer after business logic is stable
5. **Documentation**: Update docs alongside code changes

## Migration and Evolution
- **Database Changes**: Use SQLAlchemy migrations for schema updates
- **Service Changes**: Maintain backward compatibility during transitions
- **Handler Changes**: Version API responses for breaking changes
- **Configuration Changes**: Environment variable versioning and defaults