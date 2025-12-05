# DianaBot - Comprehensive Technical Documentation

## Project Overview

DianaBot is a sophisticated Telegram bot built with Python and Aiogram 3, designed as an immersive narrative experience with gamification elements and VIP exclusive features. The system consists of three interconnected modules: Narrative Immersion, Gamification System, and Channel Administration, with additional VIP features like Mi Diván (compatibility tests, anonymous messaging), auctions, and exclusive content.

## Documentation Structure

This documentation is organized into comprehensive guides covering all aspects of the DianaBot system:

### Architecture & Design
- **[Architecture Guide](architecture/ARCHITECTURE.md)** - System architecture, layers, modules, and integration patterns
- **[Module Breakdown](modules/MODULES.md)** - Detailed analysis of all modules and their functionality

### User Interface & API
- **[Commands Reference](commands/COMMANDS.md)** - Complete API and command reference for all bot functionality
- **[Integration Points](development/INTEGRATION_POINTS.md)** - All system integration points and external connections

### Setup & Configuration
- **[Configuration Guide](configuration/CONFIGURATION.md)** - Setup, installation, and configuration instructions
- **[Development Workflow](development/DEVELOPMENT.md)** - Development practices and workflow

### Specialized Features
- **[VIP Features](features/VIP_FEATURES.md)** - Comprehensive guide to Mi Diván and VIP exclusive functionality
- **[Admin Panel](development/ADMIN_PANEL.md)** - Admin panel usage and management guide

### Data Management
- **[Database Schema](schema/SCHEMA.md)** - Complete database schema documentation with all models and relationships

## System Components

### 1. Narrative Immersion System
- Interactive story fragments with character dialogue
- Branching narrative paths with requirements
- User progress tracking and state management
- Auto-advancement and decision processing

### 2. Gamification System
- Besitos currency system
- Mission-based progression
- Achievement and badge tracking
- Level and XP systems
- Shop with purchasable content

### 3. Channel Administration
- VIP and free channel access management
- Subscription verification
- Request processing workflows
- Content distribution automation

### 4. VIP Features Hub (Mi Diván)
- Compatibility quizzes with Diana
- Anonymous messaging system
- Exclusive content access
- Activity tracking and statistics

### 5. Auction System
- Real-time bidding functionality
- Participant management
- Notification system
- Winner processing

### 6. User Management System (Fase 4.5)
- Complete API: 9+ endpoints for comprehensive user management
- Admin Panel Integration: Advanced user listing, filtering, and bulk operations
- User Role Management: Free/VIP role assignment and management
- Besitos Adjustment: Tools to modify user besitos balance
- User Blocking/Deletion: Comprehensive user control features
- Narrative Progress Tracking: Monitor and reset user narrative progress
- Purchase History: Track user purchases and spending
- Advanced Filtering: Search, role, besitos range, and activity-based filtering
- Bulk Operations: Mass actions for efficient user management

## Technical Stack

- **Framework**: Aiogram 3 (Telegram Bot Framework)
- **Database**: SQLAlchemy ORM (PostgreSQL/SQLite)
- **Backend**: Python 3.8+
- **Admin Panel**: Flask
- **Migrations**: Alembic
- **Asynchronous Operations**: Async/Await patterns

## Key Features

### For Users
- Immersive narrative experience with multiple story paths
- Gamification with points, missions, and achievements
- VIP exclusive content and interactions
- Auction participation for special items
- Anonymous messaging with privacy protection

### For Administrators
- Comprehensive admin panel for content management
- Complete user management and analytics
- Narrative and shop item management
- VIP subscription management
- Channel access control

### For Developers
- Modular architecture with clear separation of concerns
- Comprehensive API for all functionality
- Extensive documentation for all components
- Robust error handling and logging
- Scalable design for future enhancements

## Getting Started

1. **Setup**: Follow the [Configuration Guide](configuration/CONFIGURATION.md) for installation
2. **Development**: Review the [Development Workflow](development/DEVELOPMENT.md) for contribution guidelines
3. **Architecture**: Study the [Architecture Guide](architecture/ARCHITECTURE.md) to understand system design
4. **API Reference**: Use the [Commands Reference](commands/COMMANDS.md) for all available functionality

## Contributing

This documentation provides comprehensive guidance for understanding, developing, and maintaining the DianaBot system. All documentation files are located in the `documentos-bajo-final` directory with clear, technical explanations of all system components.

For specific implementation details, configuration options, or development workflows, please refer to the appropriate documentation file in the directory structure above.