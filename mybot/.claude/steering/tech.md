# Technology Stack & Architecture

## Core Technologies
- **Language**: Python 3.x with async/await patterns
- **Bot Framework**: aiogram 3.0+ (modern async Telegram bot library)
- **Database**: SQLAlchemy with AsyncIO support
- **Storage**: SQLite with aiosqlite driver (current), prepared for PostgreSQL scaling
- **Task Scheduling**: APScheduler for background processes
- **Configuration**: python-dotenv for environment management

## Architecture Principles
- **Service-Oriented Architecture**: Clear separation of business logic into dedicated services
- **Async-First Design**: All I/O operations use async/await patterns
- **Coordinator Pattern**: Central orchestration via `CoordinadorCentral` for cross-service integration
- **Middleware Chain**: Request processing through configurable middleware layers
- **Error-First Design**: Comprehensive error handling and logging at all levels

## Key Architectural Components
1. **Services Layer**: Core business logic (user, points, narrative, emotional analysis)
2. **Handlers Layer**: Telegram-specific message and callback processing
3. **Database Layer**: SQLAlchemy models with async session management
4. **Integration Layer**: Cross-service coordination and data flow management
5. **Middleware Layer**: Request preprocessing, user registration, points tracking

## Performance Considerations
- **Database**: Async SQLAlchemy with connection pooling
- **Memory**: In-memory FSM storage for bot states
- **Concurrency**: Proper async task management with BackgroundTaskManager
- **Error Recovery**: Graceful degradation and automatic retry mechanisms

## Development Standards
- **Async Patterns**: Consistent use of async/await, proper session management
- **Error Handling**: Try-catch blocks with detailed logging
- **Type Hints**: Comprehensive typing for better IDE support and maintenance
- **Logging**: Structured logging with appropriate levels and context

## Scaling Considerations
- **Database Migration Path**: SQLite → PostgreSQL for production scaling
- **Session Management**: Designed for easy transition to Redis-backed sessions
- **Service Isolation**: Services can be extracted to separate processes if needed
- **Background Tasks**: Scheduler system designed for distributed task management

## Integration Points
- **Telegram Bot API**: Primary user interface
- **Database**: Persistent storage for all user data and content
- **Scheduler**: Background task execution for automated processes
- **Coordinator**: Central integration point for complex workflows

## Security Principles
- **Environment Variables**: Sensitive configuration via .env files
- **Input Validation**: All user inputs validated before processing
- **Database Security**: Parameterized queries, no raw SQL injection vectors
- **Token Management**: Secure bot token handling and rotation support