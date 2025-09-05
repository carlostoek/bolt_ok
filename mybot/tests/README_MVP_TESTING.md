# Diana Bot MVP Narrative System Testing Framework

Comprehensive testing framework for the Diana Bot MVP narrative system, ensuring quality, performance, and character consistency across all levels and user interactions.

## 🎯 Testing Overview

This framework validates the complete MVP narrative system with 8 implemented fragments across 3 levels (1→2→3), maintaining Diana's character consistency >95% and performance <500ms requirements.

### Key Testing Areas

1. **Fragment Validation** - All 8 MVP narrative fragments
2. **Progression Logic** - Level 1→2→3 advancement and gating
3. **Choice System** - User choices and archetyping data collection
4. **Diana Menu Integration** - Complete menu system functionality
5. **Character Consistency** - >95% Diana personality validation
6. **Performance Requirements** - <500ms response time compliance
7. **Error Handling** - Graceful degradation and character maintenance
8. **End-to-End Journeys** - Complete user experience validation

## 🚀 Quick Start

### Run All Tests
```bash
# Complete test suite
./tests/run_mvp_narrative_tests.py

# Quick development tests
./tests/run_mvp_narrative_tests.py --quick

# Verbose output
./tests/run_mvp_narrative_tests.py --verbose
```

### Run Specific Categories
```bash
# Character consistency only
./tests/run_mvp_narrative_tests.py --character

# Performance tests only  
./tests/run_mvp_narrative_tests.py --performance

# Specific category
./tests/run_mvp_narrative_tests.py --category fragment_validation
```

### With Coverage Reporting
```bash
./tests/run_mvp_narrative_tests.py --coverage
```

## 📋 Test Categories

### 1. Fragment Validation (`test_mvp_narrative_fragment_validation.py`)
- **Purpose**: Validate all 8 MVP narrative fragments
- **Coverage**: Fragment structure, JSON validation, character consistency
- **Key Tests**:
  - Fragment count validation (exactly 8)
  - Level distribution (3-3-2 across levels 1-2-3)
  - Tier classifications (los_kinkys → observadores → comprensores)
  - Choice structure and archetyping data
  - Content quality and character elements
  - Database operations and performance

### 2. Progression Logic (`test_mvp_narrative_progression.py`)
- **Purpose**: Test Level 1→2→3 progression mechanics
- **Coverage**: User state persistence, clue gating, level advancement
- **Key Tests**:
  - Sequential fragment progression
  - Level access requirements
  - Clue unlocking mechanisms
  - User state persistence between sessions
  - Decision logging and history tracking

### 3. Choice System & Archetyping (`test_mvp_choice_system_archetyping.py`)
- **Purpose**: Validate choice processing and user archetyping
- **Coverage**: Choice validation, points awarding, behavioral analysis
- **Key Tests**:
  - Choice structure validation
  - Points calculation accuracy
  - Archetyping data collection and processing
  - User personality development over time
  - Personalization based on archetype

### 4. Diana Menu Integration (`test_mvp_diana_menu_integration.py`)
- **Purpose**: Test Diana Menu System integration
- **Coverage**: Menu navigation, state management, character consistency
- **Key Tests**:
  - Menu system initialization
  - Role-based routing (admin vs user)
  - Narrative menu integration
  - Performance requirements
  - Multi-tenant isolation
  - Besitos integration display

### 5. Character Consistency (`test_mvp_character_consistency.py`)
- **Purpose**: Ensure >95% Diana character consistency requirement
- **Coverage**: Automated validation, personality traits, context adaptation
- **Key Tests**:
  - All content meets 95% threshold
  - Personality trait balance (mysterious, seductive, emotional, intellectual)
  - Context-specific validation (fragments, menus, errors)
  - Violation detection and recommendations
  - Comprehensive consistency reporting

### 6. Performance Requirements (`test_mvp_performance_requirements.py`)
- **Purpose**: Validate <500ms performance requirements
- **Coverage**: Core operations, concurrent users, scalability
- **Key Tests**:
  - Fragment retrieval performance
  - Choice processing speed
  - Character validation performance
  - Concurrent user handling
  - Database optimization
  - Memory usage under load

### 7. Error Handling & Recovery (`test_mvp_error_handling_recovery.py`)
- **Purpose**: Test error scenarios and graceful degradation
- **Coverage**: Database errors, API failures, character-consistent errors
- **Key Tests**:
  - Database connection failures
  - Transaction rollbacks
  - Telegram API error handling
  - Character-consistent error messages
  - System recovery mechanisms
  - Data corruption recovery

### 8. End-to-End User Journeys (`test_mvp_e2e_user_journeys.py`)
- **Purpose**: Validate complete user experience flows
- **Coverage**: Full Level 1→3 journeys, besitos integration, menu flows
- **Key Tests**:
  - Complete Level 1 journey (3 fragments)
  - Complete Level 2 journey (3 fragments)
  - Complete Level 3 journey (2 fragments)
  - Archetyping development throughout journey
  - Besitos accumulation and display
  - Menu system journey integration
  - Performance throughout complete journey
  - Error recovery during journeys

## 📊 MVP Compliance Validation

The test framework validates these MVP requirements:

### ✅ Character Consistency >95%
- All narrative content validated with Diana Character Validator
- Personality traits balanced across all fragments
- Error messages maintain character even during failures
- Menu responses consistent with Diana's voice

### ✅ Performance <500ms
- Fragment retrieval operations
- Choice processing
- Character validation
- Menu system responses
- Database transactions

### ✅ 8 Fragments Implementation
- Level 1: 3 fragments (los_kinkys tier)
- Level 2: 3 fragments (observadores tier)  
- Level 3: 2 fragments (comprensores tier)
- All fragments validate structure and content

### ✅ Level Progression 1→2→3
- Sequential access requirements
- Clue-based gating
- User state persistence
- Progress tracking

### ✅ Choice System & Archetyping
- Valid choice structures
- Points calculation
- Archetyping data collection
- Personality development tracking

### ✅ Diana Menu System
- Integrated navigation
- Character-consistent interface
- Performance compliance
- Multi-user support

### ✅ Besitos Integration
- Points awarding accuracy
- Character-consistent display
- Integration with narrative progression
- Menu system display

### ✅ Error Handling
- Graceful degradation
- Character-consistent error messages
- Recovery mechanisms
- Data integrity maintenance

## 🔧 Test Configuration

### Environment Variables
```bash
# Enable coverage reporting
export MVP_TEST_COVERAGE=1

# Database configuration for testing
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
```

### Test Database Setup
Tests use in-memory SQLite databases created fresh for each test session, ensuring isolation and consistency.

### Dependencies
```bash
# Install test dependencies
pip install pytest pytest-asyncio sqlalchemy[asyncio] aiosqlite
```

## 📈 Performance Benchmarks

### Target Performance Metrics
- Fragment retrieval: <100ms
- Choice processing: <200ms
- Character validation: <300ms
- Menu operations: <150ms
- Complete user operation: <500ms

### Concurrent User Support
- Tests validate 10-20 concurrent users
- Performance degradation monitoring
- Memory usage validation
- Database connection efficiency

## 🎭 Character Consistency Standards

### Diana Personality Requirements
- **Mysterious**: >15/25 points per content piece
- **Seductive**: >15/25 points per content piece
- **Emotionally Complex**: >15/25 points per content piece
- **Intellectually Engaging**: >15/25 points per content piece
- **Overall Score**: >95/100 points

### Content Standards
- Narrative fragments: Detailed, atmospheric, character-rich
- Menu responses: Brief but character-consistent
- Error messages: Technical concepts wrapped in character voice
- Notifications: Celebratory while maintaining mystery

## 🚨 Continuous Integration

### Pre-commit Testing
```bash
# Quick validation before commits
./tests/run_mvp_narrative_tests.py --quick
```

### Full Validation
```bash
# Complete test suite for releases
./tests/run_mvp_narrative_tests.py --coverage
```

### Performance Monitoring
```bash
# Performance-focused testing
./tests/run_mvp_narrative_tests.py --performance
```

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure SQLAlchemy async dependencies installed
   - Check database URL configuration
   - Verify table creation permissions

2. **Character Validation Failures**
   - Review content against Diana personality guidelines
   - Check for technical language violations
   - Ensure proper emoji and character elements

3. **Performance Test Failures**
   - Check system load during testing
   - Verify database optimization
   - Review concurrent operation limits

4. **Import Errors**
   - Ensure project root in Python path
   - Verify all dependencies installed
   - Check for circular imports

### Debug Mode
```bash
# Run with verbose output for debugging
./tests/run_mvp_narrative_tests.py --verbose --category fragment_validation
```

## 📚 Additional Resources

- [Diana Character Consistency Framework](../docs/diana_character_consistency_framework.md)
- [MVP System Architecture](../docs/MIGRATION_FIELD_MAPPING.md)
- [Database Models Documentation](../database/narrative_unified.py)
- [Performance Optimization Guide](../TROUBLESHOOTING.md)

## 🎉 Success Criteria

The MVP narrative system is considered fully validated when:

1. ✅ All 8 test categories pass completely
2. ✅ Character consistency >95% across all content
3. ✅ Performance <500ms for all operations
4. ✅ Complete user journeys function end-to-end
5. ✅ Error scenarios handle gracefully with character maintenance
6. ✅ Concurrent users supported without degradation
7. ✅ All fragments validate structure and content requirements
8. ✅ Progression logic works reliably across all levels

When all criteria are met, the system is ready for MVP deployment with confidence in quality, performance, and user experience consistency.