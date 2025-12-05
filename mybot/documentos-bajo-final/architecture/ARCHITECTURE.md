# DianaBot - System Architecture

## Overview

DianaBot is a sophisticated Telegram bot built with Python and Aiogram 3, designed as an immersive narrative experience with gamification elements and VIP exclusive features. The system follows a modular architecture with clear separation of concerns across multiple interconnected modules.

## Architecture Layers

### 1. Presentation Layer
- **Telegram Bot Interface**: Aiogram 3-based bot handling user interactions
- **Inline/Reply Keyboards**: Dynamic keyboards generated based on user context and permissions
- **Menu System**: Role-based menu management with VIP, Free, and Admin views

### 2. Application Layer
- **Handlers**: Command and callback handlers organized by functionality
- **Services**: Business logic and domain services
- **Middlewares**: Cross-cutting concerns (authentication, points, visual feedback)
- **State Management**: FSM (Finite State Machine) for complex workflows

### 3. Data Layer
- **Database**: SQLAlchemy-based ORM with PostgreSQL/SQLite support
- **Models**: Comprehensive data models for all features
- **Repositories**: Data access patterns

### 4. Infrastructure Layer
- **Background Tasks**: Schedulers for channel requests, VIP subscriptions, auctions
- **Message Safety**: Enhanced message handling with error recovery
- **Configuration**: Environment-based configuration management

## Core Modules

### 1. Narrative Immersion System
- **Story Fragments**: Modular narrative components with character dialogue
- **Narrative Choices**: Branching story paths with requirements
- **User State Machine**: Tracks user progress through narrative
- **Auto-advancement**: Seamless story flow without decisions

### 2. Gamification System
- **Besitos Points**: Core currency system
- **Missions**: Daily, weekly, and special missions
- **Achievements**: Progress-based rewards
- **Level System**: XP and progression tracking
- **Shop**: Points-based item purchases

### 3. Channel Administration
- **Access Management**: Channel subscription verification
- **VIP Channel**: Exclusive content access
- **Request Processing**: Manual approval workflows
- **Content Distribution**: Automated channel management

### 4. VIP Features Hub (Mi Diván)
- **Compatibility Tests**: Personality-based quizzes with Diana
- **Anonymous Messaging**: Secure messaging system with privacy
- **VIP Exclusive Content**: Premium narrative and features

### 5. Auction System
- **Real-time Auctions**: Bidding system with notifications
- **Participant Management**: Tracking and engagement
- **Winner Processing**: Automated prize distribution

## Technical Components

### Main Entry Point (bot.py)
- **DB Middleware**: Session injection for all handlers
- **Error Handling**: Global exception management
- **Background Tasks**: Scheduled operations for automated processes
- **Middleware Pipeline**: Authentication, points, gamification, visual feedback

### Service Layer
- **Coordinador Central**: Centralized business logic execution
- **Narrative Service**: Story management and progression
- **Auction Service**: Real-time bidding and management
- **Shop Service**: Purchase and inventory management
- **Subscription Service**: VIP membership management

### Data Models
- **User Management**: Roles, permissions, and profile data
- **Narrative Models**: Story fragments, choices, user states
- **Gamification Models**: Points, missions, achievements, levels
- **VIP Models**: Subscriptions, grants, exclusive features
- **Auction Models**: Auctions, bids, participants

## Architecture Patterns

### 1. Event-Driven Architecture
- Telegram updates trigger handlers
- Background schedulers for periodic tasks
- Real-time notifications for auctions and responses

### 2. Service-Oriented Design
- Each major feature has dedicated services
- Services communicate through well-defined interfaces
- Decoupled components for maintainability

### 3. State Management
- FSM for complex workflows (quizzes, purchases)
- Database-based state persistence
- Context-aware navigation

### 4. Security & Privacy
- VIP-only feature access control
- Anonymous messaging with privacy preservation
- Admin IP whitelisting for panel access

## Integration Points

### Telegram API
- Message handling and updates
- Inline keyboards and callbacks
- Media file management
- Message reactions (native support)

### Database Systems
- Primary: PostgreSQL/SQLite with SQLAlchemy
- Migration support with Alembic
- Connection pooling and async operations

### External Services
- Admin Panel: Flask-based web interface
- Background Task Schedulers: Automated processes
- Notification Systems: Admin alerts and user updates

## Scalability Considerations

### Performance Optimizations
- Database connection pooling
- Query optimization with eager loading
- Caching strategies for frequently accessed data
- Background processing for heavy operations

### Error Handling
- Comprehensive exception handling
- Graceful degradation for failed operations
- Logging and monitoring capabilities
- Recovery mechanisms for failed transactions

This architecture provides a robust, scalable foundation for the DianaBot ecosystem while maintaining clear separation of concerns and enabling independent development of different modules.