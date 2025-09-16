# Implementation Plan

## Task Overview
This implementation plan breaks down the narrative module development into atomic, manageable tasks that can be executed systematically. Each task is designed to be completed in 15-30 minutes and focuses on specific file modifications or additions while preserving the existing working shop system.

## Steering Document Compliance
All tasks follow the established project structure in handlers/admin/, services/, and database/ directories. The implementation leverages existing patterns in CoordinadorCentral orchestration, admin panel designs, and database model extensions while maintaining the fully functional shop integration.

## Atomic Task Requirements
Each task meets these criteria for optimal agent execution:
- **File Scope**: Touches 1-3 related files maximum
- **Time Boxing**: Completable in 15-30 minutes
- **Single Purpose**: One testable outcome per task
- **Specific Files**: Must specify exact files to create/modify
- **Agent-Friendly**: Clear input/output with minimal context switching

## Tasks

### Phase 1: Database Layer Enhancement

- [x] 1. Extend narrative models with enhanced metadata fields
  - File: database/narrative_models.py
  - Add enhanced metadata fields to StoryFragment: content_type, emotional_tone, analytics_metadata
  - Add JSON fields for complex unlock conditions and user archetype targeting
  - Purpose: Provide foundation for advanced content management
  - _Leverage: existing StoryFragment model, Base class patterns_
  - _Requirements: 1.2, 2.1_

- [x] 2. Create analytics models for content tracking
  - File: database/narrative_models.py (continue from task 1)
  - Add FragmentAnalytics and UserJourneyAnalytics models
  - Include engagement metrics, completion rates, choice distribution tracking
  - Purpose: Enable comprehensive analytics collection and reporting
  - _Leverage: existing database model patterns, JSON field usage_
  - _Requirements: 4.1, 4.2_

- [x] 3. Enhance LorePiece model with rich content support
  - File: database/models.py (modify existing LorePiece)
  - Add rich_content_data, content_metadata, unlock_condition_tree JSON fields
  - Add related_lore_pieces relationship field for content linking
  - Purpose: Support advanced lore piece management and relationships
  - _Leverage: existing LorePiece model, ShopItem relationships_
  - _Requirements: 2.2, 2.3_

- [x] 4. Create database migration for enhanced models
  - File: database/migrations/004_enhance_narrative_models.sql
  - Create migration script for new fields in StoryFragment and LorePiece models
  - Add new analytics tables with proper indexes
  - Purpose: Safely migrate existing data to enhanced schema
  - _Leverage: existing migration patterns in database/migrations/_
  - _Requirements: 1.1, 2.1_

### Phase 2: Enhanced Services Layer

- [x] 5. Create narrative admin service interface
  - File: services/narrative_admin_service.py
  - Define NarrativeAdminService class with content management methods
  - Implement create_story_fragment, update_story_fragment, delete_story_fragment methods
  - Purpose: Provide admin-specific narrative content management functionality
  - _Leverage: services/narrative_service.py patterns, database session handling_
  - _Requirements: 1.1, 1.2_

- [x] 6. Implement narrative consistency validation in admin service
  - File: services/narrative_admin_service.py (continue from task 5)
  - Add validate_narrative_consistency and visualize_narrative_graph methods
  - Implement fragment relationship validation and orphan detection
  - Purpose: Ensure narrative flow integrity during content editing
  - _Leverage: existing NarrativeChoice relationships, graph traversal patterns_
  - _Requirements: 1.3, 1.5_

- [x] 7. Create lore management service
  - File: services/lore_management_service.py
  - Implement LoreManagementService class with lore piece CRUD operations
  - Add link_lore_to_shop_item and organize_lore_by_category methods
  - Purpose: Manage lore pieces and their relationships to shop items
  - _Leverage: services/shop_service.py patterns, existing LorePiece model_
  - _Requirements: 2.1, 2.2_

- [x] 8. Implement lore unlock analytics in lore management service
  - File: services/lore_management_service.py (continue from task 7)
  - Add get_lore_unlock_analytics and track_lore_access_patterns methods
  - Implement search_lore_pieces with advanced filtering capabilities
  - Purpose: Provide insights into lore piece effectiveness and usage
  - _Leverage: existing UserLorePiece tracking, analytics patterns_
  - _Requirements: 2.4, 4.2_

- [x] 9. Create user experience enhancement service
  - File: services/user_experience_service.py
  - Implement UserExperienceService class with journey tracking methods
  - Add track_user_choice_patterns and adapt_narrative_to_user_archetype methods
  - Purpose: Provide personalized narrative experiences based on user behavior
  - _Leverage: services/character_voice_service.py, existing user state tracking_
  - _Requirements: 3.1, 3.2_

- [x] 10. Implement personalized content generation in UX service
  - File: services/user_experience_service.py (continue from task 9)
  - Add generate_personalized_teaser_content and get_user_narrative_insights methods
  - Implement predict_user_engagement_path functionality
  - Purpose: Create contextually appropriate content based on user history
  - _Leverage: existing teaser system in CoordinadorCentral, user archetype detection_
  - _Requirements: 3.2, 3.4_

- [x] 11. Create comprehensive analytics service
  - File: services/analytics_service.py
  - Implement AnalyticsService class with engagement metrics collection
  - Add get_fragment_engagement_metrics and analyze_choice_distribution_patterns methods
  - Purpose: Provide detailed analytics for content optimization
  - _Leverage: existing user progress tracking, database aggregation patterns_
  - _Requirements: 4.1, 4.2_

- [x] 12. Implement user segmentation analytics
  - File: services/analytics_service.py (continue from task 11)
  - Add generate_user_segment_analysis and track_conversion_funnel_metrics methods
  - Implement export_analytics_data with multiple format support
  - Purpose: Enable data-driven content and business decisions
  - _Leverage: existing user data, point system analytics_
  - _Requirements: 4.3, 4.4_

### Phase 3: Admin Interface Development

- [x] 13. Create narrative admin keyboard layouts
  - File: keyboards/admin_narrative_kb.py
  - Design keyboard layouts for narrative content management interface
  - Add fragment creation, editing, and navigation keyboards
  - Purpose: Provide intuitive admin interface for narrative management
  - _Leverage: keyboards/admin_shop_kb.py patterns, existing admin keyboard designs_
  - _Requirements: 1.1_

- [x] 14. Enhance admin narrative handlers with content management
  - File: handlers/admin_narrative_handlers.py (modify existing)
  - Add handlers for create_fragment, edit_fragment, delete_fragment operations
  - Implement narrative graph visualization and consistency checking handlers
  - Purpose: Provide comprehensive admin interface for narrative content
  - _Leverage: existing admin_narrative_handlers.py, services/narrative_admin_service.py_
  - _Requirements: 1.1, 1.3_

- [x] 15. Create lore management admin handlers
  - File: handlers/admin/lore_admin.py
  - Implement handlers for lore piece creation, editing, and shop item linking
  - Add lore analytics and search functionality handlers
  - Purpose: Provide visual interface for lore piece management
  - _Leverage: handlers/admin/shop_admin.py patterns, services/lore_management_service.py_
  - _Requirements: 2.1, 2.2_

- [x] 16. Create lore management keyboard layouts
  - File: keyboards/admin_lore_kb.py
  - Design keyboards for lore piece management and shop item linking
  - Add category organization and analytics view keyboards
  - Purpose: Support efficient lore content management workflows
  - _Leverage: keyboards/admin_shop_kb.py, existing admin keyboard patterns_
  - _Requirements: 2.2, 2.4_

- [x] 17. Create analytics admin interface
  - File: handlers/admin/analytics_admin.py
  - Implement handlers for analytics dashboard and report generation
  - Add user segment analysis and conversion funnel viewing capabilities
  - Purpose: Provide comprehensive analytics interface for administrators
  - _Leverage: handlers/admin/shop_admin.py patterns, services/analytics_service.py_
  - _Requirements: 4.1, 4.3_

- [x] 18. Create analytics keyboard layouts and data export
  - File: keyboards/admin_analytics_kb.py
  - Design keyboards for analytics navigation and report configuration
  - Add date range selection and export format options
  - Purpose: Enable efficient analytics data access and export
  - _Leverage: existing admin keyboard patterns, export functionality_
  - _Requirements: 4.3, 4.5_

### Phase 4: Enhanced User Experience

- [x] 19. Extend CoordinadorCentral with narrative admin operations
  - File: services/coordinador_central.py (modify existing)
  - Add new AccionUsuario enum values for narrative admin operations
  - Implement _flujo_narrative_admin_operation method
  - Purpose: Integrate narrative admin functionality with existing orchestration
  - _Leverage: existing CoordinadorCentral patterns, admin operation flows_
  - _Requirements: 1.1, 2.1_

- [x] 20. Enhance narrative service with analytics integration
  - File: services/narrative_service.py (modify existing)
  - Add analytics tracking to user progression methods
  - Implement get_user_narrative_insights and track_choice_patterns methods
  - Purpose: Integrate user analytics with core narrative progression
  - _Leverage: existing narrative progression logic, user state tracking_
  - _Requirements: 3.1, 4.1_

- [x] 21. Implement personalized teaser content system
  - File: services/narrative_service.py (continue from task 20)
  - Add generate_contextual_teaser for restricted content scenarios
  - Integrate user archetype data for personalized messaging
  - Purpose: Provide engaging alternatives to simple access denial
  - _Leverage: existing teaser fragments, character voice service integration_
  - _Requirements: 3.2, 5.1_

- [x] 22. Enhance character intelligence integration
  - File: services/narrative_service.py (continue from task 21)
  - Add adapt_character_response_to_user_archetype method
  - Implement relationship progression tracking with characters
  - Purpose: Provide deeper character intelligence and relationship evolution
  - _Leverage: services/character_voice_service.py, emotional analysis integration_
  - _Requirements: 5.1, 5.2_

### Phase 5: Testing and Validation

- [x] 23. Create narrative admin service unit tests
  - File: tests/services/test_narrative_admin_service.py
  - Write tests for content CRUD operations and validation methods
  - Test narrative consistency checking and graph visualization
  - Purpose: Ensure reliability of narrative content management
  - _Leverage: existing test patterns in tests/services/, pytest fixtures_
  - _Requirements: 1.1, 1.3_

- [x] 24. Create lore management service unit tests
  - File: tests/services/test_lore_management_service.py
  - Write tests for lore piece operations and shop item linking
  - Test analytics tracking and search functionality
  - Purpose: Validate lore management functionality and integrations
  - _Leverage: existing service test patterns, mock shop service integration_
  - _Requirements: 2.1, 2.4_

- [ ] 25. Create analytics service unit tests
  - File: tests/services/test_analytics_service.py
  - Write tests for engagement metrics calculation and user segmentation
  - Test data export functionality and report generation
  - Purpose: Ensure accurate analytics calculations and data handling
  - _Leverage: existing test utilities, database test fixtures_
  - _Requirements: 4.1, 4.3_

- [ ] 26. Create integration tests for enhanced narrative flow
  - File: tests/integration/test_enhanced_narrative_flow.py
  - Write end-to-end tests for complete user journeys with analytics tracking
  - Test shop integration with enhanced lore management
  - Purpose: Validate complete system integration and user experience
  - _Leverage: existing integration test patterns, test user fixtures_
  - _Requirements: 3.1, 3.2_

- [ ] 27. Create admin interface integration tests
  - File: tests/integration/test_admin_narrative_interface.py
  - Write tests for admin content management workflows
  - Test lore piece creation and shop item linking processes
  - Purpose: Ensure admin interfaces work correctly with backend services
  - _Leverage: existing admin test patterns, handler testing utilities_
  - _Requirements: 1.1, 2.2_

### Phase 6: Performance and Security

- [ ] 28. Implement analytics data caching layer
  - File: services/analytics_cache_service.py
  - Create caching service for frequently accessed analytics data
  - Implement cache invalidation strategies for real-time data updates
  - Purpose: Meet 2-second loading requirement for analytics dashboards
  - _Leverage: existing caching patterns, Redis integration if available_
  - _Requirements: Performance_

- [ ] 29. Add content validation and security measures
  - File: utils/narrative_validation.py
  - Implement content sanitization and validation utilities
  - Add access control validation for admin operations
  - Purpose: Ensure content security and prevent unauthorized access
  - _Leverage: existing admin_check utilities, validation patterns_
  - _Requirements: Security_

- [ ] 30. Optimize database queries for analytics performance
  - File: services/analytics_service.py (optimize existing methods)
  - Add database indexes for analytics queries
  - Implement query optimization for large dataset operations
  - Purpose: Meet 3-second response time requirement for admin operations
  - _Leverage: existing database optimization patterns, SQLAlchemy query optimization_
  - _Requirements: Performance_

### Phase 7: Documentation and Deployment

- [ ] 31. Update admin menu integration
  - File: handlers/admin/admin_menu.py (modify existing)
  - Add narrative management and analytics menu options
  - Integrate new admin interfaces with existing menu structure
  - Purpose: Provide unified admin interface with new narrative features
  - _Leverage: existing admin_menu.py structure, menu navigation patterns_
  - _Requirements: 1.1, 4.1_

- [ ] 32. Create narrative admin documentation
  - File: docs/admin/narrative_management.md
  - Document narrative content creation and management workflows
  - Include lore piece management and analytics usage guides
  - Purpose: Enable administrators to effectively use new features
  - _Leverage: existing documentation patterns, admin guide structures_
  - _Requirements: 1.1, 2.1_

- [ ] 33. Update system configuration for new features
  - File: config/narrative_config.py
  - Add configuration options for analytics processing and caching
  - Include settings for content validation and security measures
  - Purpose: Enable flexible system configuration for different environments
  - _Leverage: existing configuration patterns, environment-specific settings_
  - _Requirements: Performance, Security_

**Note**: All tasks maintain backward compatibility with the existing shop system and preserve the fully functional CoordinadorCentral orchestration. Each task includes specific file paths and leverages existing code patterns to ensure consistency with the established codebase architecture.