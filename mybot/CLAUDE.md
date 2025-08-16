
Navigation Menu
V2

Code
Issues
V2
/CLAUDE.md
carlostoek
carlostoek
last week
78 lines (54 loc) · 3.71 KB

Preview

Code

Blame
Antes de empezar a desarrollar cualquier petición que se te haga vas a revisar el directorio docs que es en donde está toda la documentación del proyecto para que tengas una visión Clara de lo que hay que hacer y en dónde hacerlo. el 90% de las funcionalidades que se necesitan ya están implementadas si tienes que obtener algún dato o una función lo más seguro es que ya está implementada primero revisa la documentación para que sepas se la desarrollas tú o no de primera instancia es usar lo que ya está en último de los casos es desarrollar algo nuevo porque si no vamos a duplicar código. procede conforme a las guías y al término de tu tarea documentas lo hecho según la guía de documentación que se encuentra en ese mismo directorio

Using Gemini CLI for Large Codebase Analysis
When analyzing large codebases or multiple files that might exceed context limits, use the Gemini CLI with its massive context window. Use gemini -p to leverage Google Gemini's large context capacity.

File and Directory Inclusion Syntax
Use the @ syntax to include files and directories in your Gemini prompts. The paths should be relative to WHERE you run the gemini command:

Examples:
Single file analysis: gemini -p "@src/main.py Explain this file's purpose and structure"

Multiple files: gemini -p "@package.json @src/index.js Analyze the dependencies used in the code"

Entire directory: gemini -p "@src/ Summarize the architecture of this codebase"

Multiple directories: gemini -p "@src/ @tests/ Analyze test coverage for the source code"

Current directory and subdirectories: gemini -p "@./ Give me an overview of this entire project"

Or use --all_files flag:
gemini --all_files -p "Analyze the project structure and dependencies"

Implementation Verification Examples

Check if a feature is implemented: gemini -p "@src/ @lib/ Has dark mode been implemented in this codebase? Show me the relevant files and functions"

Verify authentication implementation: gemini -p "@src/ @middleware/ Is JWT authentication implemented? List all auth-related endpoints and middleware"

Check for specific patterns: gemini -p "@src/ Are there any React hooks that handle WebSocket connections? List them with file paths"

Verify error handling: gemini -p "@src/ @api/ Is proper error handling implemented for all API endpoints? Show examples of try-catch blocks"

Check for rate limiting: gemini -p "@backend/ @middleware/ Is rate limiting implemented for the API? Show the implementation details"

Verify caching strategy: gemini -p "@src/ @lib/ @services/ Is Redis caching implemented? List all cache-related functions and their usage"

Check for specific security measures: gemini -p "@src/ @api/ Are SQL injection protections implemented? Show how user inputs are sanitized"

Verify test coverage for features: gemini -p "@src/payment/ @tests/ Is the payment processing module fully tested? List all test cases"

When to Use Gemini CLI

Use gemini -p when:

Analyzing entire codebases or large directories
Comparing multiple large files
Need to understand project-wide patterns or architecture
Current context window is insufficient for the task
Working with files totaling more than 100KB
Verifying if specific features, patterns, or security measures are implemented
Checking for the presence of certain coding patterns across the entire codebase
Important Notes

Paths in @ syntax are relative to your current working directory when invoking gemini
The CLI will include file contents directly in the context
No need for --yolo flag for read-only analysis
Gemini's context window can handle entire codebases that would overflow Claude's context
When checking implementations, be specific about what you're looking for to get accurate result

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a sophisticated multi-tenant Telegram bot system designed for gamified adult content delivery with VIP subscriptions, interactive narratives, and comprehensive user engagement features.

### Core Architecture

- **Framework**: aiogram v3 (Telegram Bot API)
- **Database**: SQLAlchemy async ORM with PostgreSQL support
- **Pattern**: Service layer architecture with Repository pattern
- **Multi-tenancy**: Each admin configures independent bot instances
- **Gamification**: Points system, missions, achievements, levels, auctions
- **Content Management**: Interactive narrative system with decision trees and VIP content

## Development Commands

### Running the Bot

```bash
# Development mode
python bot.py

# Production with logging
python bot.py 2>&1 | tee bot.log
```

### Database Operations

```bash
# Initialize database
python -c "from database.setup import init_db; import asyncio; asyncio.run(init_db())"

# If using Alembic for migrations (setup required)
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Testing

```bash
# Run all tests
pytest

# Run specific tests
python -m pytest tests/integration/test_channel_engagement.py -v
python -m pytest tests/integration/test_coordinador_central.py -v
```

### Environment Variables

The following environment variables should be set:

```
BOT_TOKEN=your_telegram_bot_token
ADMIN_IDS=123456789;987654321
VIP_CHANNEL_ID=-1001234567890
FREE_CHANNEL_ID=-1009876543210
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/gamification
```

## Key Components and Structure

### Service Layer

The core business logic is implemented in the `services/` directory following a service-oriented architecture:

- **CoordinadorCentral**: Central facade that orchestrates interactions between services
- **FreeChannelService**: Manages automated channel access with social media messaging
- **NarrativeService**: Handles interactive story management
- **PointService**: Manages gamification and rewards
- **UserService**: Handles user data and roles
- **TenantService**: Multi-tenant configuration management

### Database Models

Database models are defined in `database/models.py` with key entities:

- **User**: Core user data with roles (admin/vip/free), points, achievements
- **Narrative Models**: Interactive story fragments and user progress
- **Gamification**: Missions, achievements, levels, points system

### Handlers

Telegram bot handlers in `handlers/` directory with dedicated modules for different functionalities:

- **Admin Handlers**: Configuration, management, and administration
- **User Handlers**: Core user interactions and commands
- **Channel Handlers**: Channel access and interaction handling
- **Narrative Handlers**: Interactive story navigation

### Middlewares

Custom middlewares for cross-cutting concerns:

- **DBSessionMiddleware**: Database session management
- **UserRegistrationMiddleware**: Automatic user registration
- **PointsMiddleware**: Points tracking for user interactions

## Common Development Patterns

### Error Handling Strategy

All services return structured responses:

```python
{
    "success": True/False,
    "message": "Human-readable message",
    "data": {...}  # Optional result data
    "error": "Error message"  # Only present if success is False
}
```

### Message Safety

All user-facing messages should use the safety utilities:

```python
from utils.message_safety import safe_answer, safe_send_message

# Always use these instead of direct message methods
await safe_answer(message, "Your message")
await safe_send_message(bot, user_id, "Your message")
```

### Service Implementation Pattern

```python
class NewService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def method_name(self, user_id: int) -> Dict[str, Any]:
        try:
            # Implementation
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"Error in NewService.method_name: {e}")
            return {"success": False, "error": str(e)}
```

### Handler Implementation Pattern

```python
@router.message(Command("command"))
async def handler_name(message: Message, session: AsyncSession):
    try:
        # Use services for business logic
        service = SomeService(session)
        result = await service.do_something(message.from_user.id)
        
        # Safe message sending
        await safe_answer(message, result["message"])
    except Exception as e:
        logger.error(f"Error in handler: {e}")
        await safe_answer(message, "Error message")
```

## Important Implementation Rules

1. **Message Safety**: Always use `safe_answer()` and `safe_send_message()` utilities
2. **Role Priority**: Admin > VIP > Free (never downgrade higher roles)
3. **Error Handling**: All services must return structured responses with success/error states
4. **Database Access**: Always use async patterns and session middleware
5. **Logging**: Use the established logging pattern for all operations
6. **Middleware Usage**: Rely on middleware for cross-cutting concerns
7. **Background Tasks**: Use the `BackgroundTaskManager` for background operations

## Troubleshooting

### Debug Mode

Enable detailed logging by setting log level to DEBUG in `bot.py`:

```python
logging.getLogger().setLevel(logging.DEBUG)
```

### Common Issues

- **Import Errors**: Check service imports and module references
- **Database Connection**: Verify DATABASE_URL and connection settings
- **Telegram API**: Ensure bot token is valid and has proper permissions
- **Channel Access**: Verify bot is admin in all configured channels
