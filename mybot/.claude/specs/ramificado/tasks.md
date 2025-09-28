# Implementation Plan - Sistema de Arquetipos Expandido

## Task Overview
Implementation of the expanded archetype classification system through atomic, agent-friendly tasks that build upon existing infrastructure while adding sophisticated psychological profiling capabilities. Each task is designed to be completable in 15-30 minutes with clear inputs/outputs and minimal context switching.

## Steering Document Compliance
All tasks follow structure.md conventions by extending existing services in `services/` directory, enhancing existing models in `database/`, and building upon established testing patterns in `tests/emotional/`. Implementation leverages tech.md patterns including async/await, service-oriented architecture, and graceful error handling.

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
- Reference existing code to leverage using: `_Leverage: path/to/file.py, path/to/model.py_`
- Focus only on coding tasks (no deployment, user testing, etc.)
- **Avoid broad terms**: No "system", "integration", "complete" in task titles

## Good vs Bad Task Examples
L **Bad Examples (Too Broad)**:
- "Implement archetype analysis system" (affects many files, multiple purposes)
- "Add user behavioral tracking features" (vague scope, no file specification)
- "Build complete classification algorithm" (too large, multiple components)

 **Good Examples (Atomic)**:
- "Create ArchetypeScores dataclass in services/archetype_analyzer.py with 8 primary variables"
- "Add intellectual_score column to ArchetypeClassification model in database/emotional_models.py"
- "Create analyze_response_pattern method in ResponseTimeAnalyzer class with timing classification logic"

## Tasks

### Phase 1: Core Data Structures and Models

- [ ] 1. Create ArchetypeScores dataclass in services/archetype_analyzer.py
  - File: services/archetype_analyzer.py (new)
  - Define dataclass with 8 primary variables: intellectual, emotional, exploratory, vulnerable, philosophical, direct, patient, reciprocal
  - Set default values to 0.0 for all fields
  - Add type hints for float values
  - Purpose: Establish primary archetype scoring structure for analysis
  - _Requirements: 4.1_

- [ ] 2. Create SubArchetypeScores dataclass in services/archetype_analyzer.py
  - File: services/archetype_analyzer.py (continue from task 1)
  - Define dataclass with 10 sub-archetype variables: romantic_intellectual, skeptical_thinker, hedonist_philosopher, pure_theorist, empathetic_emotional, passionate_emotional, wounded_healer, adventure_seeker, collector_explorer, freedom_lover
  - Set default values to 0.0 for all fields
  - Add comprehensive docstring explaining sub-archetype purposes
  - Purpose: Create secondary classification structure for granular profiling
  - _Requirements: 4.3, 4.5_

- [ ] 3. Extend ArchetypeClassification model in database/emotional_models.py with primary score fields
  - File: database/emotional_models.py
  - Add 8 new columns: intellectual_score, emotional_score, exploratory_score, vulnerable_score, philosophical_score, direct_score, patient_score, reciprocal_score
  - Use Column(Float, default=0.0) for all new fields
  - Add index=True for frequently queried fields
  - Purpose: Store primary archetype scores in database with backward compatibility
  - _Leverage: existing ArchetypeClassification model structure_
  - _Requirements: 1.8, 4.7_

- [ ] 4. Extend ArchetypeClassification model in database/emotional_models.py with sub-archetype score fields
  - File: database/emotional_models.py (continue from task 3)
  - Add 10 sub-archetype columns: romantic_intellectual_score, skeptical_thinker_score, hedonist_philosopher_score, pure_theorist_score, empathetic_emotional_score, passionate_emotional_score, wounded_healer_score, adventure_seeker_score, collector_explorer_score, freedom_lover_score
  - Use Column(Float, default=0.0) for all sub-archetype fields
  - Purpose: Complete database schema for expanded archetype classification
  - _Leverage: existing ArchetypeClassification model patterns_
  - _Requirements: 4.3, 4.7_

- [ ] 5. Add cognitive style tracking fields to ArchetypeClassification model in database/emotional_models.py
  - File: database/emotional_models.py (continue from task 4)
  - Add cognitive_style Column(String(50), nullable=True) for timing analysis results
  - Add response_consistency Column(Float, default=0.5) for timing pattern consistency
  - Add temporal_pattern Column(String(50), nullable=True) for progression detection
  - Purpose: Store timing analysis results alongside archetype classification
  - _Leverage: existing ArchetypeClassification model structure_
  - _Requirements: 3.1, 3.4, 3.5_

### Phase 2: Response Time Analysis Component

- [ ] 6. Create ResponseTimeAnalyzer class in services/response_time_analyzer.py
  - File: services/response_time_analyzer.py (new)
  - Create class with __init__ method setting timing thresholds dictionary
  - Define threshold constants: quick_intuitive (0-10s), thoughtful (10-30s), deliberate (30s+)
  - Add comprehensive class docstring explaining timing analysis purpose
  - Purpose: Establish response timing analysis component foundation
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 7. Implement analyze_response_pattern method in ResponseTimeAnalyzer class
  - File: services/response_time_analyzer.py (continue from task 6)
  - Create method taking List[float] timings parameter
  - Calculate average time, classify style based on thresholds
  - Return Dict with style, average_time, consistency, pattern fields
  - Handle empty timings list with default return values
  - Purpose: Core timing analysis algorithm for cognitive style detection
  - _Requirements: 3.1, 3.4_

- [ ] 8. Implement _calculate_consistency method in ResponseTimeAnalyzer class
  - File: services/response_time_analyzer.py (continue from task 7)
  - Create private method calculating coefficient of variation for timing consistency
  - Handle edge case of less than 2 timings (return 1.0)
  - Calculate mean, variance, and coefficient of variation
  - Return consistency score between 0.0 and 1.0
  - Purpose: Measure response timing consistency for behavioral analysis
  - _Requirements: 3.4_

- [ ] 9. Implement _detect_pattern method in ResponseTimeAnalyzer class
  - File: services/response_time_analyzer.py (continue from task 8)
  - Create method detecting acceleration/deceleration in response times
  - Calculate differences between consecutive timings
  - Classify as 'getting_slower', 'getting_faster', or 'consistent' based on average difference
  - Handle insufficient data case (< 3 timings)
  - Purpose: Detect temporal progression patterns in user behavior
  - _Requirements: 3.5, 3.6_

### Phase 3: Core ArchetypeAnalyzer Implementation

- [ ] 10. Create ArchetypeAnalyzer class foundation in services/archetype_analyzer.py
  - File: services/archetype_analyzer.py (continue from tasks 1-2)
  - Create class with __init__ method taking AsyncSession parameter
  - Initialize ResponseTimeAnalyzer instance
  - Add session attribute for database operations
  - Add comprehensive class docstring explaining archetype analysis purpose
  - Purpose: Establish main archetype analysis service class
  - _Leverage: existing service patterns from EmotionalAnalysisService_
  - _Requirements: 1.1, 4.1_

- [ ] 11. Implement analyze_l1_choices method signature in ArchetypeAnalyzer class
  - File: services/archetype_analyzer.py (continue from task 10)
  - Create async method with parameters: user_id (int), choices (List[Dict]), timings (List[float])
  - Initialize ArchetypeScores and SubArchetypeScores instances
  - Add method docstring with parameter descriptions and return type
  - Return empty Dict for now (implementation in next tasks)
  - Purpose: Define main entry point for L1 choice analysis
  - _Requirements: 1.1, 4.1_

- [ ] 12. Implement _process_choice_weights method in ArchetypeAnalyzer class
  - File: services/archetype_analyzer.py (continue from task 11)
  - Create async method processing individual choice with archetype_weights
  - Extract archetype_weights and sub_archetype_weights from choice Dict
  - Update scores using setattr based on weights dictionary
  - Handle missing weights gracefully
  - Purpose: Apply choice-specific archetype weights to user scores
  - _Requirements: 2.2, 2.5, 2.6_

- [ ] 13. Implement _apply_timing_modifiers method in ArchetypeAnalyzer class
  - File: services/archetype_analyzer.py (continue from task 12)
  - Create async method modifying scores based on response timing
  - Apply timing rules: <10s increment direct/passionate_emotional, 10-30s increment philosophical/intellectual, >30s increment philosophical/skeptical_thinker/patient
  - Use exact timing thresholds from requirements
  - Purpose: Apply timing-based score modifications for cognitive style detection
  - _Requirements: 1.2, 1.3, 3.1, 3.2, 3.3_

- [ ] 14. Implement _calculate_primary_archetype method in ArchetypeAnalyzer class
  - File: services/archetype_analyzer.py (continue from task 13)
  - Create async method determining highest-scoring primary dimension
  - Calculate composite scores with weighted combinations
  - Handle tied scores by selecting first alphabetically
  - Return primary archetype string
  - Purpose: Determine user's primary psychological archetype from scores
  - _Requirements: 4.2_

- [ ] 15. Implement _determine_sub_archetype method in ArchetypeAnalyzer class
  - File: services/archetype_analyzer.py (continue from task 14)
  - Create async method mapping primary archetype to relevant sub-archetypes
  - Define sub-archetype mappings for intellectual, emotional, and exploratory primaries
  - Select highest-scoring sub-archetype within primary category
  - Return sub-archetype string or 'undefined'
  - Purpose: Determine granular sub-classification within primary archetype
  - _Requirements: 4.3, 4.5_

- [ ] 16. Implement _calculate_confidence method in ArchetypeAnalyzer class
  - File: services/archetype_analyzer.py (continue from task 15)
  - Create async method calculating classification confidence
  - Consider score separation, response consistency, and data completeness
  - Calculate confidence as float between 0.0 and 1.0
  - Apply confidence thresholds from requirements (0.7 for mixed traits, 0.8 for activation)
  - Purpose: Determine reliability of archetype classification for branching decisions
  - _Requirements: 4.6, 4.8_

- [ ] 17. Complete analyze_l1_choices method implementation in ArchetypeAnalyzer class
  - File: services/archetype_analyzer.py (continue from task 16)
  - Implement full method logic calling _process_choice_weights and _apply_timing_modifiers for each choice
  - Call _calculate_primary_archetype, _determine_sub_archetype, and _calculate_confidence
  - Integrate ResponseTimeAnalyzer for cognitive style analysis
  - Return comprehensive Dict with all classification results
  - Purpose: Complete main archetype analysis workflow
  - _Requirements: 1.1, 4.1, 4.7_

### Phase 4: Database Integration and Storage

- [ ] 18. Implement store_classification_results method in ArchetypeAnalyzer class
  - File: services/archetype_analyzer.py (continue from task 17)
  - Create async method storing classification results in ArchetypeClassification model
  - Handle both new users and existing classification updates
  - Store all primary scores, sub-archetype scores, and cognitive style data
  - Maintain backward compatibility with existing fields
  - Purpose: Persist expanded archetype classification to database
  - _Leverage: existing ArchetypeClassification model, async session patterns_
  - _Requirements: 1.8, 4.7, 6.4_

- [ ] 19. Implement get_user_classification method in ArchetypeAnalyzer class
  - File: services/archetype_analyzer.py (continue from task 18)
  - Create async method retrieving existing user classification from database
  - Return None if no classification exists
  - Include all expanded fields in returned data
  - Handle database errors gracefully
  - Purpose: Retrieve existing user archetype data for analysis and updates
  - _Leverage: existing database query patterns from EmotionalAnalysisService_
  - _Requirements: 6.2, 6.4_

- [ ] 20. Create database migration script for ArchetypeClassification model extensions
  - File: database/migrations/add_expanded_archetype_fields.py (new)
  - Create Alembic migration adding 8 primary score columns
  - Add 10 sub-archetype score columns with proper defaults
  - Add cognitive style tracking columns
  - Ensure zero-downtime migration with backward compatibility
  - Purpose: Safely extend database schema for expanded archetype classification
  - _Leverage: existing migration patterns in database/migrations/_
  - _Requirements: 4.7, 6.4_

### Phase 5: Enhanced L1F1 Fragment Implementation

- [ ] 21. Create enhanced L1F1 fragment data structure in data/fragments/enhanced_l1f1.py
  - File: data/fragments/enhanced_l1f1.py (new)
  - Define ENHANCED_L1F1 dictionary with Diana's archetype detection content
  - Include 5 choices with embedded archetype_weights and sub_archetype_weights
  - Maintain Diana's mysterious character voice from original L1F1
  - Add tracking configuration for response_time and choice_progression
  - Purpose: Create archetype-optimized L1F1 fragment for user classification
  - _Leverage: existing fragment structure patterns_
  - _Requirements: 2.1, 2.2, 2.7_

- [ ] 22. Implement load_enhanced_l1f1 function in services/narrative_loader.py
  - File: services/narrative_loader.py
  - Create function loading enhanced L1F1 fragment data
  - Handle fragment validation and error cases
  - Return structured fragment data for narrative system
  - Integrate with existing fragment loading patterns
  - Purpose: Load enhanced L1F1 fragment into narrative system
  - _Leverage: existing narrative loading functions in narrative_loader.py_
  - _Requirements: 2.1, 2.7_

- [ ] 23. Update narrative_handler.py to use enhanced L1F1 for new users
  - File: handlers/narrative_handler.py
  - Modify start_narrative_command to load enhanced L1F1 for new users
  - Preserve existing L1F1 for users already in progress
  - Add archetype analysis trigger after L1F1 completion
  - Maintain backward compatibility with existing narrative flow
  - Purpose: Integrate enhanced L1F1 into narrative progression for new users
  - _Leverage: existing narrative handler patterns, start_narrative_command function_
  - _Requirements: 2.1, 6.1, 6.8_

- [ ] 24. Implement choice tracking enhancement in narrative_handler.py
  - File: handlers/narrative_handler.py (continue from task 23)
  - Enhance handle_narrative_choice to capture response timing data
  - Store choice timing in user session or temporary storage
  - Trigger archetype analysis after sufficient L1 interactions
  - Preserve existing choice processing logic
  - Purpose: Capture response timing data for archetype analysis
  - _Leverage: existing choice handling in handle_narrative_choice_
  - _Requirements: 1.1, 2.3, 3.8_

### Phase 6: Service Integration and Orchestration

- [ ] 25. Create ArchetypeIntegrationService in services/archetype_integration_service.py
  - File: services/archetype_integration_service.py (new)
  - Create service class bridging ArchetypeAnalyzer and existing systems
  - Add methods for activating archetype branching and checking confidence
  - Implement graceful fallback to existing 5-archetype system
  - Purpose: Coordinate expanded archetype system with existing infrastructure
  - _Leverage: existing service patterns from EmotionalAnalysisService_
  - _Requirements: 6.1, 6.5, 6.8_

- [ ] 26. Implement activate_archetype_branching method in ArchetypeIntegrationService
  - File: services/archetype_integration_service.py (continue from task 25)
  - Create async method enabling archetype-based narrative branching for user
  - Check classification confidence thresholds (>0.8 for activation)
  - Update user flags or database markers for branching eligibility
  - Return boolean success status
  - Purpose: Enable personalized narrative branching when archetype is sufficiently confident
  - _Requirements: 1.7, 4.6_

- [ ] 27. Implement get_archetype_confidence method in ArchetypeIntegrationService
  - File: services/archetype_integration_service.py (continue from task 26)
  - Create async method retrieving user's current archetype confidence score
  - Return confidence float or None if no classification exists
  - Handle database access errors gracefully
  - Purpose: Check archetype classification stability for branching decisions
  - _Requirements: 4.6, 6.1_

- [ ] 28. Integrate ArchetypeAnalyzer with CoordinadorCentral workflows
  - File: services/coordinador_central.py
  - Add archetype analysis integration to existing AccionUsuario.TEST_EVALUACION_EMOCIONAL workflow
  - Create new workflow for L1 completion archetype analysis
  - Maintain existing workflow patterns and error handling
  - Purpose: Integrate archetype analysis with established coordination patterns
  - _Leverage: existing CoordinadorCentral workflows and AccionUsuario patterns_
  - _Requirements: 6.5, 6.1_

### Phase 7: Testing and Validation

- [ ] 29. Create unit tests for ArchetypeScores and SubArchetypeScores dataclasses
  - File: tests/test_archetype_data_structures.py (new)
  - Test dataclass instantiation with default values
  - Verify field types and value ranges
  - Test serialization and deserialization
  - Purpose: Validate core archetype data structures
  - _Leverage: existing test patterns from tests/test_emotional_models.py_
  - _Requirements: 4.1, 4.3_

- [ ] 30. Create unit tests for ResponseTimeAnalyzer class
  - File: tests/test_response_time_analyzer.py (new)
  - Test analyze_response_pattern with various timing inputs
  - Verify classification thresholds (quick_intuitive, thoughtful, deliberate)
  - Test consistency calculation and pattern detection
  - Handle edge cases like empty input or single timing
  - Purpose: Validate response timing analysis accuracy
  - _Requirements: 3.1, 3.4, 3.5_

- [ ] 31. Create unit tests for ArchetypeAnalyzer core methods
  - File: tests/test_archetype_analyzer.py (new)
  - Test _process_choice_weights with various choice configurations
  - Test _apply_timing_modifiers with different timing ranges
  - Test _calculate_primary_archetype with various score combinations
  - Test _determine_sub_archetype mapping logic
  - Purpose: Validate core archetype analysis algorithms
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 32. Create integration tests for complete archetype analysis flow
  - File: tests/emotional/test_expanded_archetype_integration.py
  - Test full analyze_l1_choices workflow with realistic choice data
  - Verify database storage and retrieval of classification results
  - Test integration with existing EmotionalAnalysisService
  - Test graceful fallback to 5-archetype system
  - Purpose: Validate end-to-end archetype classification functionality
  - _Leverage: existing integration test patterns from tests/emotional/_
  - _Requirements: 1.1, 4.7, 6.1, 6.8_

- [ ] 33. Create enhanced L1F1 fragment validation tests
  - File: tests/test_enhanced_l1f1.py (new)
  - Test fragment loading and structure validation
  - Verify choice archetype_weights and sub_archetype_weights
  - Test Diana's character voice consistency
  - Validate timing tracking integration
  - Purpose: Ensure enhanced L1F1 fragment functions correctly
  - _Leverage: existing narrative testing patterns_
  - _Requirements: 2.1, 2.2, 2.7_

- [ ] 34. Create performance tests for archetype analysis system
  - File: tests/test_archetype_performance.py (new)
  - Test analysis completion within 2-second requirement
  - Test concurrent analysis for up to 100 users
  - Measure database query performance for classification operations
  - Verify memory usage stays within acceptable limits
  - Purpose: Ensure archetype system meets performance requirements
  - _Requirements: Performance section - 2 seconds, 100 concurrent users_

### Phase 8: Error Handling and Fallback Systems

- [ ] 35. Implement error handling in ArchetypeAnalyzer methods
  - File: services/archetype_analyzer.py (enhance existing methods)
  - Add try-catch blocks around database operations
  - Implement graceful fallback when timing analysis fails
  - Log errors appropriately without breaking user experience
  - Return safe default values when analysis fails
  - Purpose: Ensure robust error handling throughout archetype analysis
  - _Leverage: existing error handling patterns from EmotionalAnalysisService_
  - _Requirements: 6.8, Reliability section_

- [ ] 36. Implement fallback integration with existing 5-archetype system
  - File: services/archetype_integration_service.py (enhance existing methods)
  - Add fallback logic when expanded analysis fails
  - Map expanded archetypes to existing 5-archetype categories when needed
  - Maintain seamless user experience during fallback scenarios
  - Purpose: Ensure backward compatibility and graceful degradation
  - _Leverage: existing archetype classification patterns_
  - _Requirements: 6.8, Reliability section_

- [ ] 37. Add comprehensive logging to archetype analysis workflow
  - File: services/archetype_analyzer.py (enhance existing methods)
  - Add INFO level logging for successful classifications
  - Add WARNING level logging for low confidence classifications
  - Add ERROR level logging for analysis failures
  - Include user_id and classification details in logs
  - Purpose: Enable monitoring and debugging of archetype classification system
  - _Leverage: existing logging patterns from other services_
  - _Requirements: Reliability section, admin monitoring_

### Phase 9: Documentation and Admin Interface

- [ ] 38. Create archetype analysis service documentation
  - File: docs/archetype_analysis_service.md (new)
  - Document ArchetypeAnalyzer class API and usage patterns
  - Include examples of archetype classification results
  - Document integration with existing systems
  - Add troubleshooting guide for common issues
  - Purpose: Provide comprehensive documentation for development team
  - _Requirements: Usability section - admin interface integration_

- [ ] 39. Add archetype management to existing admin interface
  - File: handlers/admin/archetype_admin.py (new)
  - Create admin commands for viewing user archetype classifications
  - Add ability to manually trigger archetype re-analysis
  - Include archetype statistics and distribution reports
  - Maintain existing admin interface patterns and security
  - Purpose: Enable administrative management of archetype classification system
  - _Leverage: existing admin handler patterns from handlers/admin/_
  - _Requirements: Usability section - admin interface integration_

- [ ] 40. Create archetype classification monitoring and alerting
  - File: services/archetype_monitoring_service.py (new)
  - Implement monitoring for classification success rates
  - Add alerts for unusual classification patterns or failures
  - Track performance metrics and confidence score distributions
  - Integrate with existing monitoring infrastructure
  - Purpose: Monitor archetype system health and performance
  - _Leverage: existing monitoring patterns_
  - _Requirements: Reliability section, performance monitoring_

**Implementation Notes:**
- All tasks maintain 100% backward compatibility with existing systems
- Database migrations include proper rollback procedures
- Error handling follows existing service patterns for graceful degradation
- Testing coverage includes both unit and integration tests
- Performance requirements are validated through dedicated test tasks
- Admin interface integration follows established patterns for consistency

**Ready for Execution:** Tasks are designed for immediate implementation by development agents with clear file specifications, leveraging existing code patterns, and maintaining system reliability throughout the implementation process.