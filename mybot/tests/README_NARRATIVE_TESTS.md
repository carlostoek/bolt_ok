# Diana Narrative System Test Infrastructure

This document outlines the comprehensive test infrastructure created for the Diana Bot narrative system, covering all critical aspects of the interactive storytelling experience.

## Test Coverage Overview

The test infrastructure provides extensive coverage across five major categories:

1. **Basic Functionality Tests** (`test_narrative_engine.py`)
   - Core NarrativeEngine functions
   - Fragment retrieval and navigation
   - User state management
   - Fragment conditions and requirements

2. **Narrative Flow Validation** (`test_narrative_flow.py`)
   - Continuity between fragments
   - Validation of choice destinations
   - Detection of unreachable content
   - Cycle detection and analysis
   - Access control for VIP content

3. **Emotional State Testing** (`test_emotional_states.py`)
   - Emotional state fragment validation
   - Emotional state transitions
   - Complete emotional journeys
   - Validation of allowed emotional paths

4. **Rewards Integration** (`test_narrative_rewards.py`)
   - Fragment point rewards
   - Choice-based rewards
   - Achievement unlocking
   - Progress tracking
   - Karma multipliers
   - One-time rewards

5. **User Journey Flows** (`test_user_journey.py`)
   - Complete onboarding journeys
   - VIP content journeys
   - User role transitions
   - Handler integration
   - Statistics tracking

## Test Infrastructure Components

### 1. Core Test Framework

- `conftest.py`: Central fixture configuration providing:
  - Mock database setup
  - Mock bot and message objects
  - Mock narrative fragments and choices
  - Mock users of different types (free, VIP, admin)
  - Mock services (points, achievements)
  - Emotional state testing support

### 2. Test Data

- Fixtures provide mock data for:
  - Story fragments with varying access requirements
  - Narrative choices with different destinations
  - User states at different progression levels
  - Emotional state fragments for testing state transitions

### 3. Test Execution

- `run_narrative_tests.py`: Script to run test categories with:
  - Category selection (all, basic, flow, emotional, rewards, journey)
  - Verbosity control
  - Test report generation

### 4. Test Reports

- Generated in the `test_reports` directory
- Include test statistics, failures, and errors
- Timestamped for historical tracking

## Running Tests

```bash
# Run all narrative tests
python run_narrative_tests.py

# Run specific category
python run_narrative_tests.py -c emotional

# Adjust verbosity
python run_narrative_tests.py -v 1

# Disable report generation
python run_narrative_tests.py --no-report
```

## Test Design Principles

1. **Comprehensive Coverage**: Tests cover all narrative components from basic functions to complex user journeys.

2. **Isolated Testing**: Each component is tested in isolation using appropriate mocks.

3. **Edge Case Validation**: Tests include boundary conditions and rare scenarios:
   - Access control boundaries
   - Emotional state transitions
   - Upgrade from free to VIP
   - One-time reward claiming

4. **Integration Verification**: Tests ensure correct integration with:
   - Point system
   - Achievement system
   - User role management
   - Handler functions

5. **Zero Tolerance for Failures**: The test suite is designed to catch any potential narrative system failures before they reach production.

## Key Test Scenarios

1. **Narrative Integrity**: Ensures all fragments have valid continuation paths and there are no dead-ends.

2. **VIP Content Validation**: Verifies VIP content is properly access-controlled and unavailable to free users.

3. **Emotional Testing**: Validates the emotional state system works correctly for character interactions.

4. **Rewards Processing**: Confirms points and achievements are correctly awarded during narrative progression.

5. **User Progression**: Tests complete user journeys from onboarding through VIP content access.

## Extending the Test Suite

When adding new narrative features:

1. Add appropriate mock data to `conftest.py`
2. Create specific test cases in the relevant test file
3. Update `run_narrative_tests.py` if adding a new test category

## Emotional State Testing

Special attention is given to emotional state testing, which validates:

- All emotional states are correctly defined
- Transitions between emotions are valid
- Emotional state affects narrative presentation
- Complete emotional journeys work correctly
- Invalid emotional transitions are prevented

## Integration Test Focus

The test suite particularly focuses on integration points between:

- Narrative progression and point rewards
- Fragment completion and achievement unlocking
- User role changes and access to content
- Emotional states and narrative presentation

This ensures a cohesive, bug-free narrative experience for all users.