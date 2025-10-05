# Technology Stack - DianaBot

## Core Framework
- **Python 3.8+** - Primary development language
- **aiogram 3.x** - Modern async Telegram bot framework
- **SQLAlchemy** - ORM for database operations
- **aiosqlite** - Async SQLite database driver

## Architecture Pattern
**Service-Oriented Architecture** with integration coordination

### Key Components
- **Handler Layer**: Organized by functionality (admin, VIP, shop, narrative, etc.)
- **Service Layer**: Business logic with specialized services
- **Database Layer**: Separated models by domain (emotional, narrative, main)
- **Middleware System**: User registration, points tracking, session management
- **Integration Coordinator**: Central orchestration via `CoordinadorCentral`

## Database Design

### Multi-Model Approach
- `database/models.py` - Core user, gamification, and channel management
- `database/emotional_models.py` - Emotional analysis and character voice tracking
- `database/narrative_models.py` - Story progression and decision tracking

### Key Principles
- **Async-first** - All database operations use async patterns
- **Session management** - Proper SQLAlchemy session handling via middleware
- **Data integrity** - Foreign key relationships and constraints

## Background Processing
- **APScheduler** - Handles recurring tasks
- **Background Task Manager** - Safe task execution with error handling
- **Scheduled Services**:
  - Channel access validation
  - VIP subscription management
  - Auction monitoring
  - Channel cleanup

## Character & Narrative Technology

### Emotional Analysis System
- **CharacterVoiceService** - Maintains character personality consistency
- **EmotionalAnalysisService** - Evaluates user emotional responses
- **Character Types**: Diana (mysterious/seductive), Lucien (supportive/authoritative)

### Advanced Features
- **Behavioral analysis** - Time patterns, response quality, authenticity detection
- **Personalization engine** - Adapts narrative based on user archetypes
- **Memory system** - Characters "remember" user interactions and evolution

## Performance Requirements
- **Response time**: < 2 seconds for standard interactions
- **Concurrent users**: Design for growth beyond current base
- **Data persistence**: All narrative progress and user state must survive restarts
- **Error resilience**: Comprehensive error handling and logging

## Security Considerations
- **Session security** - Proper session management and cleanup
- **Input validation** - All user inputs validated and sanitized
- **Access control** - VIP content protection and subscription validation
- **Content protection** - Narrative content should be secure against unauthorized access

## Integration Requirements
- **Telegram API** - Full Bot API compliance
- **Payment systems** - Future integration for VIP subscriptions
- **Analytics** - Tracking user engagement and conversion metrics

## Development Standards
- **Async/await** patterns throughout
- **Type hints** where beneficial for complex operations
- **Error handling** - Comprehensive logging and graceful degradation
- **Modular design** - Services should be loosely coupled and testable

## Scalability Considerations
- **Database optimization** - Proper indexing for user queries
- **Session pooling** - Efficient database connection management
- **Background task optimization** - Non-blocking scheduled operations
- **Content delivery** - Efficient narrative fragment serving

## Deployment Architecture
- **Environment management** - `.env` configuration
- **Logging** - Structured logging with multiple outputs
- **Process management** - Graceful shutdown handling
- **Resource management** - Proper cleanup of background tasks

## Technology Constraints
- **Telegram limitations** - Message size, rate limits, media restrictions
- **SQLite considerations** - Single-writer limitations for high concurrency
- **Memory usage** - Efficient handling of user sessions and narrative state