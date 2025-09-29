# Implementation Plan - Ramificado Fase 2: Sistema de Diana Evolutiva con Ramificación Inteligente

## Task Overview
This implementation plan breaks down the ramificado-fase2 system into atomic, agent-friendly tasks that can be executed independently. The approach focuses on building the core personality system infrastructure first, then adding intelligent branching capabilities, and finally integrating with existing narrative workflows.

## Steering Document Compliance
Tasks follow structure.md conventions by placing new services in `/services/`, extending existing database models in `/database/emotional_models.py`, and using established integration patterns through CoordinadorCentral orchestration.

## Atomic Task Requirements
**Each task meets these criteria for optimal agent execution:**
- **File Scope**: Touches 1-3 related files maximum
- **Time Boxing**: Completable in 15-30 minutes
- **Single Purpose**: One testable outcome per task
- **Specific Files**: Must specify exact files to create/modify
- **Agent-Friendly**: Clear input/output with minimal context switching

## Task Format Guidelines
- Use checkbox format: `- [ ] Task number. Task description`
- **Specify files**: Always include exact file paths to create/modify
- **Include implementation details** as bullet points
- Reference requirements using: `_Requirements: X.Y, Z.A_`
- Reference existing code to leverage using: `_Leverage: path/to/file.py, path/to/service.py_`
- Focus only on coding tasks (no deployment, user testing, etc.)
- **Avoid broad terms**: No "system", "integration", "complete" in task titles

## Good vs Bad Task Examples
❌ **Bad Examples (Too Broad)**:
- "Implement personality system" (affects many files, multiple purposes)
- "Add behavioral tracking features" (vague scope, no file specification)
- "Build complete branching engine" (too large, multiple components)

✅ **Good Examples (Atomic)**:
- "Create PersonaType enum in database/emotional_models.py with 7 personality types"
- "Add behavioral pattern keyword detection method in DianaPersonalityService with exact matching logic"
- "Create route compatibility calculation method in BranchingEngineService using requirements formulas"

## Tasks

### Database Models and Core Infrastructure

- [ ] 1. Create PersonaType enum in database/emotional_models.py
  - File: database/emotional_models.py
  - Add PersonaType enum with PERFORMER, INTELLECTUAL, EMOTIONAL, WILD, ARTIST, PHILOSOPHER, HEALER values
  - Import enum module at top of file
  - Purpose: Define personality types for Diana's persona system
  - _Leverage: existing enum patterns in database/emotional_models.py (ResponseType, VulnerabilityLevel)_
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 2. Create DianaPersonality model in database/emotional_models.py
  - File: database/emotional_models.py
  - Add DianaPersonality class extending Base with all emotional state fields per design
  - Include foreign key relationship to user_emotional_profiles.user_id
  - Add JSON fields for available_facets and evolution_tracker with defaults
  - Purpose: Store Diana's personality state and emotional metrics for each user
  - _Leverage: existing Base class and relationship patterns in emotional_models.py_
  - _Requirements: 2.1, 2.2, 2.3, 7.4, 7.5_

- [ ] 3. Create PlayerMemory model in database/emotional_models.py
  - File: database/emotional_models.py
  - Add PlayerMemory class with JSON fields for key_moments, behavior_patterns, diana_observations
  - Include foreign key to diana_personalities.id with unique constraint
  - Add record_key_moment and update_behavior_pattern methods per design
  - Purpose: Store player behavioral patterns and memory data for personalized content
  - _Leverage: existing JSON column patterns and relationship definitions_
  - _Requirements: 1.1, 1.2, 1.3, 3.1, 3.2, 3.3_

- [ ] 4. Create PersonalityEvolution model in database/emotional_models.py
  - File: database/emotional_models.py
  - Add PersonalityEvolution class for tracking personality changes over time
  - Include evolution_type, before_state, after_state JSON fields
  - Add user_id index and timestamp fields
  - Purpose: Audit trail for Diana's personality development and debugging
  - _Leverage: existing timestamp patterns and index definitions_
  - _Requirements: 2.4, 7.5_

- [ ] 5. Add DianaPersonality relationship to UserEmotionalProfile model
  - File: database/emotional_models.py
  - Modify existing UserEmotionalProfile class to add back_populates relationship
  - Add diana_personality = relationship("DianaPersonality", back_populates="user_profile", uselist=False)
  - Purpose: Enable bidirectional relationship between user profiles and Diana personalities
  - _Leverage: existing relationship patterns in UserEmotionalProfile_
  - _Requirements: 2.1, Integration requirements_

### Core Diana Personality Service

- [ ] 6. Create DianaPersonalityService class in services/diana_personality_service.py
  - File: services/diana_personality_service.py
  - Create service class with __init__ method taking AsyncSession parameter
  - Add module-level logger configuration following project patterns
  - Import required dependencies: DianaPersonality, PlayerMemory, PersonaType models
  - Purpose: Foundation service class for personality management operations
  - _Leverage: existing service patterns from services/emotional_analysis_service.py_
  - _Requirements: 1.1, 2.1, 7.1_

- [ ] 7. Add behavioral pattern detection method to DianaPersonalityService
  - File: services/diana_personality_service.py
  - Create update_behavioral_patterns method with exact keyword matching logic per requirements
  - Implement keyword detection for "intellectual", "theory", "vulnerable", "honest", "explore", "adventure"
  - Add response time analysis for >30s (deliberate_thinker) and <10s (intuitive_responder)
  - Purpose: Track player behavioral patterns from choice text and timing
  - _Leverage: text processing patterns from existing services_
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 8. Add emotional state evolution method to DianaPersonalityService
  - File: services/diana_personality_service.py
  - Create evolve_emotional_state method implementing threshold-based state changes
  - Add logic for INTELLECTUAL persona: thinks_before_feeling >2.0 → intellectual_trust +1.0, mask_level -0.5
  - Add logic for EMOTIONAL persona: shows_emotional_courage >2.0 → emotional_openness +1.0, vulnerability_level +0.5
  - Add logic for WILD persona: comfortable_with_unknown >2.0 → adventure_readiness +1.0
  - Purpose: Evolve Diana's emotional state based on behavioral pattern thresholds
  - _Leverage: threshold checking patterns from existing emotional services_
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 9. Add personality initialization method to DianaPersonalityService
  - File: services/diana_personality_service.py
  - Create initialize_personality_for_archetype method taking user_id and ArchetypeClassification
  - Implement archetype mapping: "intellectual" → INTELLECTUAL, "emotional" → EMOTIONAL, "exploratory" → WILD
  - Set appropriate philosophical_score, emotional_score, or adventure_score >0.5 based on archetype
  - Purpose: Initialize Diana's personality based on player's archetype classification
  - _Leverage: ArchetypeClassification model and initialization patterns_
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 10. Add get_diana_personality method to DianaPersonalityService
  - File: services/diana_personality_service.py
  - Create method to retrieve existing DianaPersonality for user_id with error handling
  - Include memory_system relationship loading with selectinload
  - Add fallback initialization if personality doesn't exist
  - Purpose: Reliable personality retrieval with automatic creation if needed
  - _Leverage: existing user lookup patterns and relationship loading_
  - _Requirements: 2.5, Integration requirements_

### Branching Engine Service

- [ ] 11. Create BranchingEngineService class in services/branching_engine_service.py
  - File: services/branching_engine_service.py
  - Create service class with AsyncSession dependency and logger configuration
  - Import DianaPersonality, PersonaType, and NarrativeService dependencies
  - Add class docstring describing route compatibility and fragment selection purpose
  - Purpose: Foundation service for intelligent narrative branching based on personality
  - _Leverage: service patterns from services/narrative_service.py_
  - _Requirements: 4.0, 5.0_

- [ ] 12. Add route compatibility calculation method to BranchingEngineService
  - File: services/branching_engine_service.py
  - Create calculate_route_compatibility method implementing exact formulas from requirements
  - Add Filosófica formula: (intellectual_trust * 0.4) + (appreciates_complexity * 0.3) + ((10 - mask_level) * 0.3)
  - Add Corazón formula: (emotional_openness * 0.4) + (safe_for_vulnerability * 0.3) + (vulnerability_level * 0.3)
  - Add Aventurera formula: (adventure_readiness * 0.4) + (comfortable_with_unknown * 0.3) + (seeks_novelty * 0.3)
  - Purpose: Calculate compatibility scores for personality routes using exact mathematical formulas
  - _Leverage: mathematical calculation patterns and error handling from existing services_
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 13. Add fragment selection method to BranchingEngineService
  - File: services/branching_engine_service.py
  - Create select_optimal_fragment method implementing compatibility tier logic
  - Add compatibility ≥6.0 mapping: filosofica_advanced, corazon_intimate, aventurera_deep
  - Add compatibility 3.0-5.9 mapping to buildup fragments
  - Add compatibility <3.0 mapping to relationship_building fragments
  - Add progressive fallback chain ending with main_salon per requirements
  - Purpose: Select appropriate narrative fragments based on compatibility scores
  - _Leverage: fragment selection patterns from NarrativeService_
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 14. Add determine_next_fragment method to BranchingEngineService
  - File: services/branching_engine_service.py
  - Create orchestration method combining compatibility calculation and fragment selection
  - Add error handling for missing Diana personality data with fallback to relationship_building
  - Return FragmentSelectionResult with selected fragment and compatibility data
  - Purpose: Complete branching workflow from personality state to fragment selection
  - _Leverage: orchestration patterns from existing integration services_
  - _Requirements: 4.5, 5.4, 5.5_

### Memory Service

- [ ] 15. Create MemorySystemService class in services/memory_system_service.py
  - File: services/memory_system_service.py
  - Create service class with AsyncSession and CharacterVoiceService dependencies
  - Add imports for DianaPersonality, PlayerMemory, and content generation utilities
  - Add class docstring describing dynamic content generation and memory reference purpose
  - Purpose: Foundation service for personalized content generation with memory
  - _Leverage: service patterns and character voice integration from existing services_
  - _Requirements: 3.1, 6.1, 6.4_

- [ ] 16. Add memory reference generation method to MemorySystemService
  - File: services/memory_system_service.py
  - Create get_memory_references method checking behavioral pattern thresholds
  - Add shows_emotional_courage >2 reference: "Sabes? Cada vez que has elegido ser honesto conmigo, algo en mí se ha abierto más..."
  - Add appreciates_complexity >3.0 + INTELLECTUAL reference: "Sus ojos brillan con curiosidad intelectual..."
  - Add safe_for_vulnerability >2.0 + EMOTIONAL reference: "La seguridad que generas hace que partes de mí..."
  - Purpose: Generate contextual memory references based on behavioral pattern history
  - _Leverage: content generation and character voice patterns_
  - _Requirements: 3.1, 6.2, 6.3_

- [ ] 17. Add dynamic content generation method to MemorySystemService
  - File: services/memory_system_service.py
  - Create generate_dynamic_content method combining base content with memory references
  - Add behavioral pattern threshold checking and appropriate content layer selection
  - Implement persona-specific content adaptation for INTELLECTUAL, EMOTIONAL, WILD personas
  - Add error handling returning base content if generation fails
  - Purpose: Create personalized narrative content with memory-aware additions
  - _Leverage: content adaptation patterns and error handling from existing services_
  - _Requirements: 6.1, 6.4, 6.5_

- [ ] 18. Add key moment recording method to MemorySystemService
  - File: services/memory_system_service.py
  - Create record_key_moment method storing significant interaction data
  - Implement moment_type, impact_description, diana_reaction, timestamp structure
  - Add database persistence with error handling for memory storage failures
  - Purpose: Record significant relationship moments for future memory references
  - _Leverage: database persistence patterns and error handling_
  - _Requirements: 3.2, 3.3, 3.5_

### PersonalityIntegrationService Components

- [ ] 19. Create PersonalityIntegrationService class file with dependencies
  - File: services/integration/personality_integration_service.py
  - Create class with __init__ method taking AsyncSession and service dependencies
  - Add imports for DianaPersonalityService, BranchingEngineService, MemorySystemService
  - Add module-level logger and basic error handling structure
  - Purpose: Create foundation integration service class for personality workflows
  - _Leverage: existing integration service patterns from services/integration/_
  - _Requirements: Integration requirements_

- [ ] 20. Add behavioral pattern orchestration method to PersonalityIntegrationService
  - File: services/integration/personality_integration_service.py
  - Create process_behavioral_patterns method handling choice text analysis and response timing
  - Call DianaPersonalityService.update_behavioral_patterns and evolve_emotional_state
  - Add error handling with graceful degradation if personality services fail
  - Purpose: Orchestrate behavioral pattern analysis and emotional state updates
  - _Leverage: existing decision processing patterns from NarrativePointService_
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3_

- [ ] 21. Add compatibility calculation orchestration method to PersonalityIntegrationService
  - File: services/integration/personality_integration_service.py
  - Create calculate_compatibility_and_select_fragment method
  - Call BranchingEngineService.calculate_route_compatibility and select_optimal_fragment
  - Add fallback to relationship_building fragments if compatibility calculation fails
  - Purpose: Orchestrate route compatibility and fragment selection workflow
  - _Leverage: existing orchestration patterns from integration services_
  - _Requirements: 4.1, 4.2, 4.3, 5.1, 5.2, 5.3_

- [ ] 22. Add dynamic content generation orchestration method to PersonalityIntegrationService
  - File: services/integration/personality_integration_service.py
  - Create generate_enhanced_content method combining base fragment with memory references
  - Call MemorySystemService.generate_dynamic_content and record_key_moment if significant
  - Add fallback to base content if dynamic generation fails
  - Purpose: Orchestrate personalized content generation with memory integration
  - _Leverage: content generation patterns from existing services_
  - _Requirements: 3.1, 3.2, 6.1, 6.2, 6.3_

### CoordinadorCentral Integration

- [ ] 23. Add personality decision flow to CoordinadorCentral
  - File: services/coordinador_central.py
  - Add PROCESAR_PERSONALIDAD_DECISION to AccionUsuario enum
  - Import PersonalityIntegrationService in try/except block with graceful degradation
  - Add personality integration service initialization in __init__ method
  - Purpose: Add personality decision processing capability to central coordinator
  - _Leverage: existing AccionUsuario patterns and service initialization_
  - _Requirements: Integration requirements_

- [ ] 24. Add personality decision execution method to CoordinadorCentral
  - File: services/coordinador_central.py
  - Create _flujo_personalidad_decision method calling PersonalityIntegrationService workflow methods
  - Add sequential calls to behavioral pattern processing, compatibility calculation, content generation
  - Implement fallback to normal decision processing if any personality step fails
  - Purpose: Execute complete personality workflow through existing coordinator patterns
  - _Leverage: existing flujo patterns and error handling in CoordinadorCentral_
  - _Requirements: Integration requirements_

### Narrative Handler Integration

- [ ] 25. Add personality choice detection to narrative handler
  - File: handlers/narrative_handler.py
  - Modify handle_narrative_choice callback to detect personality-relevant choices
  - Add response time calculation from callback timestamp to choice selection
  - Add routing to CoordinadorCentral for personality-aware decision processing
  - Purpose: Capture choice timing and behavioral data for personality analysis
  - _Leverage: existing callback patterns and CoordinadorCentral integration_
  - _Requirements: 1.4, 1.5_

- [ ] 26. Add personality response enhancement to narrative handler
  - File: handlers/narrative_handler.py
  - Modify _display_narrative_fragment to handle enhanced fragments with dynamic content
  - Add personality evolution data display for debugging (optional)
  - Ensure backward compatibility with non-personality-enhanced fragments
  - Purpose: Display personality-enhanced narrative content to users
  - _Leverage: existing fragment display patterns and message handling_
  - _Requirements: 6.0_

### Database Migration and Setup

- [ ] 27. Create database migration script for personality tables
  - File: database/migrations/20250929_add_personality_system.py
  - Add CREATE TABLE statements for diana_personalities, player_memories, personality_evolutions
  - Include proper indexes on user_id and foreign key fields
  - Add foreign key constraints with appropriate CASCADE options
  - Purpose: Set up database schema for personality system tables
  - _Leverage: existing migration patterns and database setup scripts_
  - _Requirements: Database integration requirements_

### Testing Infrastructure

- [ ] 28. Create DianaPersonalityService unit tests
  - File: tests/services/test_diana_personality_service.py
  - Test behavioral pattern detection with exact keyword matching
  - Test emotional state evolution with threshold-based logic
  - Test personality initialization for different archetypes
  - Test error handling for missing or corrupted personality data
  - Purpose: Ensure reliability of core personality tracking functionality
  - _Leverage: existing service test patterns from tests/services/_
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 7.1, 7.2, 7.3_

- [ ] 29. Create BranchingEngineService unit tests
  - File: tests/services/test_branching_engine_service.py
  - Test route compatibility calculation formulas with known inputs/outputs
  - Test fragment selection logic for different compatibility score ranges
  - Test error handling for missing fragments with fallback chain
  - Test boundary conditions for compatibility thresholds (exactly 6.0, 3.0, etc.)
  - Purpose: Verify mathematical accuracy of compatibility calculations and fragment selection
  - _Leverage: mathematical testing patterns and mock data generation_
  - _Requirements: 4.1, 4.2, 4.3, 5.1, 5.2, 5.3_

- [ ] 30. Create MemorySystemService unit tests
  - File: tests/services/test_memory_system_service.py
  - Test memory reference generation for different behavioral pattern thresholds
  - Test dynamic content generation with persona-specific adaptations
  - Test key moment recording and retrieval functionality
  - Test error handling for content generation failures
  - Purpose: Ensure accurate memory-based content personalization
  - _Leverage: content generation testing patterns and mock data_
  - _Requirements: 3.1, 3.2, 6.1, 6.2, 6.3_

- [ ] 31. Create cross-service data flow integration tests
  - File: tests/integration/test_personality_data_flow.py
  - Test data flow from DianaPersonalityService through BranchingEngineService to MemorySystemService
  - Test state persistence across service boundaries
  - Test error propagation and recovery between services
  - Purpose: Validate proper data flow between personality system components
  - _Leverage: existing integration test patterns and service communication testing_
  - _Requirements: Integration workflow requirements_

- [ ] 32. Create performance validation tests for personality processing
  - File: tests/performance/test_personality_performance.py
  - Test behavioral pattern processing completes within 500ms
  - Test route compatibility calculation completes within 200ms
  - Test concurrent user personality processing
  - Purpose: Validate performance requirements are met under load
  - _Leverage: existing performance testing patterns_
  - _Requirements: Performance requirements (500ms/200ms)_

### Configuration and Documentation

- [ ] 33. Add personality configuration to project settings
  - File: utils/config.py
  - Add personality feature flags (ENABLE_PERSONALITY_SYSTEM = True)
  - Add threshold configurations (BEHAVIORAL_PATTERN_THRESHOLD = 2.0, COMPATIBILITY_THRESHOLD = 6.0)
  - Add performance monitoring settings (MAX_PERSONALITY_PROCESSING_TIME = 500)
  - Purpose: Enable runtime configuration of personality parameters
  - _Leverage: existing configuration patterns in utils/config.py_
  - _Requirements: Performance requirements, configurability_

### Final Integration and Validation

- [ ] 34. Add personality initialization to application startup
  - File: main.py
  - Add personality service registration in dependency injection container
  - Add database table initialization check on startup
  - Add logging for personality availability and graceful degradation if unavailable
  - Purpose: Ensure personality is properly initialized when application starts
  - _Leverage: existing service registration and startup patterns in main.py_
  - _Requirements: Integration requirements_

- [ ] 35. Create user journey personality development test scenario
  - File: tests/scenarios/test_personality_development_journey.py
  - Test user journey from archetype detection through advanced route unlocking
  - Verify memory accumulation and personality evolution over multiple interactions
  - Test that Diana's responses become increasingly personalized over time
  - Purpose: Validate complete personality development user experience
  - _Leverage: scenario testing patterns and user journey simulation_
  - _Requirements: All user experience requirements_

- [ ] 36. Create route unlocking validation test
  - File: tests/scenarios/test_route_unlocking.py
  - Test that all three routes (Filosófica, Corazón, Aventurera) can be unlocked through appropriate behavioral patterns
  - Verify compatibility score progression and fragment selection accuracy
  - Test memory reference generation at different behavioral pattern thresholds
  - Purpose: Validate all personality routes are properly accessible and functional
  - _Leverage: route testing patterns and behavioral simulation_
  - _Requirements: 4.1, 4.2, 4.3, 5.1, 5.2, 5.3_

## Implementation Notes

### Dependencies and Order
- Tasks 1-5 (Database Models) must be completed first as foundation
- Tasks 6-10 (DianaPersonalityService) can be done in parallel after database models
- Tasks 11-14 (BranchingEngineService) depend on DianaPersonalityService completion
- Tasks 15-18 (MemorySystemService) can be done in parallel with BranchingEngineService
- Tasks 19-26 (Integration) require completion of all core services
- Tasks 27-36 (Testing/Setup) can be done throughout or at the end

### Performance Considerations
- Tasks should be executed with performance testing to meet 500ms/200ms requirements
- Database queries should be optimized during implementation
- Caching strategies should be implemented alongside core functionality

### Error Handling Priority
- Each service implementation task includes comprehensive error handling
- Fallback behaviors ensure operation continues functioning even with partial failures
- User experience is preserved through graceful degradation
