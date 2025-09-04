# 🤖 Diana Bot MVP Development Manual

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Service Layer Guide](#service-layer-guide)
3. [Database Architecture](#database-architecture)
4. [Handler Implementation](#handler-implementation)
5. [Character Consistency Framework](#character-consistency-framework)
6. [Modification Guidelines](#modification-guidelines)
7. [Troubleshooting Reference](#troubleshooting-reference)
8. [Quick Reference](#quick-reference)

## Architecture Overview

### System Design Philosophy
The Diana Bot MVP is built on a modular, performance-optimized architecture designed to create an immersive, interactive narrative experience with robust gamification elements.

### Core Components
- **Enhanced Diana Menu System**: Character-consistent interface management
- **Unified Narrative System**: Story progression and user choice tracking
- **Gamification Engine**: Points, missions, and achievements
- **Character Validation Framework**: Personality and emotional state management

### Data Flow
```
User Interaction 
  ↓ 
Diana Menu System 
  ↓
Narrative Service 
  ↓
Gamification Service 
  ↓
Character Consistency Validator
  ↓
Database/Response Generation
```

## Service Layer Guide

### Enhanced Diana Menu System
Location: `/services/enhanced_diana_menu_system.py`

#### Key Services
- `show_main_menu()`: Dynamic menu generation based on user role
- `handle_callback()`: Central routing for all menu interactions
- `_handle_narrative_callbacks()`: Manages story progression and choices

#### Performance Optimization Strategies
- Lazy service initialization
- Shared template caching
- Performance metrics tracking
- Character consistency pre-validation

#### Dependency Injection Pattern
```python
def __init__(self, session: AsyncSession):
    # Inject database session
    # Initialize lazy-loaded services
    # Set up caching mechanisms
```

## Database Architecture

### Unified Models
Location: `/database/narrative_unified.py`

#### Key Models
- `UserDecisionLogUnified`
- `UserMissionProgressUnified`
- `UserArchetypesUnified`

#### Migration Patterns
- Gradual transition from legacy to unified models
- Backward compatibility preserved
- Minimal schema changes to reduce risk

## Handler Implementation

### Callback Routing Strategy
- Use of hierarchical callback handlers
- Role-based access control
- Centralized error handling

### Middleware Integration
- Session management
- Performance tracking
- Character consistency validation

## Character Consistency Framework

### Validation Mechanisms
- >95% personality match requirement
- Emotional state tracking
- Dynamic response generation

### Key Validation Metrics
- Personality Score Threshold: 95.0
- Response Time Target: <1 second
- Error Tolerance: Minimal fallback mechanisms

## Modification Guidelines

### Adding New Features

#### Narrative Fragments
1. Update unified narrative models
2. Add fragment to narrative service
3. Validate character consistency
4. Test integration with existing flows

#### Gamification Mechanics
1. Modify point service
2. Update mission/achievement models
3. Implement new tracking mechanisms
4. Integrate with character validation

#### Menu Options
1. Extend `EnhancedDianaMenuSystem`
2. Add new callback handler
3. Implement character-consistent text
4. Create appropriate keyboard markup

## Troubleshooting Reference

### Common Issues
- BaseModel initialization errors
- Callback routing problems
- Character consistency validation failures

### Debugging Strategies
- Enable debug mode in menu system
- Use performance tracking logs
- Validate character consistency scores
- Check database transaction integrity

## Quick Reference

### File Locations
- Main Bot: `bot.py`
- Menu System: `services/enhanced_diana_menu_system.py`
- Narrative Service: `services/mvp_narrative_fragment_service.py`
- Database Models: `database/narrative_unified.py`

### Configuration Checklist
- Verify database connection
- Check character validation thresholds
- Validate middleware configurations
- Ensure proper service dependencies

## Performance Best Practices
- Use lazy loading
- Implement caching strategies
- Minimize database queries
- Optimize callback routing

---

**Note**: This manual is a living document. Always refer to the latest version and consult with the development team for the most up-to-date information.
