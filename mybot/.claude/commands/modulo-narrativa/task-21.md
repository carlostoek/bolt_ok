# modulo-narrativa - Task 21

Execute task 21 for the modulo-narrativa specification.

## Task Description
Implement personalized teaser content system

## Code Reuse
**Leverage existing code**: existing teaser fragments, character voice service integration

## Requirements Reference
**Requirements**: 3.2, 5.1

## Usage
```
/Task:21-modulo-narrativa
```

## Instructions

Execute with @spec-task-executor agent the following task: "Implement personalized teaser content system"

```
Use the @spec-task-executor agent to implement task 21: "Implement personalized teaser content system" for the modulo-narrativa specification and include all the below context.

# Steering Context
## Steering Documents Context

No steering documents found or all are empty.

# Specification Context
## Specification Context (Pre-loaded): modulo-narrativa

### Requirements
# Requirements Document

## Introduction

The complete narrative module system represents the evolution from a concept validation prototype to a full-featured, production-ready system. This specification defines the development of a comprehensive narrative system that integrates seamlessly with the existing shop and administration systems through the central coordinator. The system will provide both an enhanced user experience for narrative progression and a comprehensive administrative panel for content management.

The current system has successfully validated the core concept of item-conditioned narrative progression, as documented in the `docs/guia-fragmentos-condicionados-items-2025-09-15.md`. Now we need to build upon this foundation to create a complete, scalable, and maintainable narrative experience.

## Alignment with Product Vision

This narrative module development supports the core vision outlined in the `Narrativo.md` document by:

- **Scaling the intimacy progression system**: Moving from basic narrative flow to sophisticated emotional and psychological depth across all levels
- **Maintaining character authenticity**: Ensuring Diana and Lucien's voices remain consistent while expanding their narrative range
- **Preserving the item-conditioning system**: Building upon the successful shop integration that connects narrative access to user investment
- **Creating sustainable content creation workflows**: Providing administrators with tools to continuously expand and refine the narrative experience

## Requirements

### Requirement 1: Enhanced Narrative Content Management System

**User Story:** As a narrative administrator, I want a comprehensive panel to create, edit, and manage all narrative content so that I can efficiently expand and maintain the story experience.

#### Acceptance Criteria

1. WHEN an administrator accesses the narrative admin panel THEN the system SHALL display all existing story fragments organized by level and progression path
2. WHEN creating a new story fragment THEN the system SHALL provide rich text editing capabilities with support for character voice guidelines and emotional context markers
3. WHEN editing existing fragments THEN the system SHALL preserve the narrative flow integrity and warn of potential breaking changes to user progression paths
4. WHEN configuring fragment access conditions THEN the system SHALL integrate with the existing shop item system and allow complex conditional logic (item ownership, user stats, previous choices)
5. WHEN saving narrative changes THEN the system SHALL validate narrative consistency and automatically update the progression graph

### Requirement 2: Advanced Lore Piece Management and Integration

**User Story:** As a content administrator, I want to create and manage lore pieces that can be linked to shop items and narrative progression so that I can provide rich, unlockable content experiences.

#### Acceptance Criteria

1. WHEN creating a new lore piece THEN the system SHALL support multiple content types (text, image, video, interactive content) with rich metadata
2. WHEN linking lore pieces to shop items THEN the system SHALL provide a visual interface to select existing lore pieces or create new ones directly from the shop item creation flow
3. WHEN configuring lore unlock conditions THEN the system SHALL support complex unlock logic (specific items, narrative progress, user engagement levels, time-based conditions)
4. WHEN users access unlocked lore THEN the system SHALL track access patterns and provide analytics for content effectiveness
5. WHEN managing lore categories THEN the system SHALL organize content hierarchically with tags and search capabilities

### Requirement 3: Sophisticated User Experience Enhancement

**User Story:** As a user engaging with the narrative system, I want a seamless, immersive experience that responds intelligently to my choices and progress so that I feel truly connected to the characters and story.

#### Acceptance Criteria

1. WHEN making narrative choices THEN the system SHALL provide immediate feedback that reflects my historical choices and relationship with characters
2. WHEN accessing item-restricted content THEN the system SHALL present contextually appropriate teaser content that motivates engagement rather than simply blocking access
3. WHEN progressing through narrative levels THEN the system SHALL remember and reference previous interactions to create continuity and depth
4. WHEN revisiting narrative content THEN the system SHALL offer new perspectives or details based on items owned and progress achieved
5. WHEN the narrative system detects inconsistencies THEN it SHALL gracefully handle errors while maintaining immersion

### Requirement 4: Comprehensive Analytics and User Journey Tracking

**User Story:** As a system administrator, I want detailed analytics about user engagement with narrative content so that I can optimize the experience and identify areas for improvement.

#### Acceptance Criteria

1. WHEN users interact with narrative content THEN the system SHALL track choice patterns, time spent, and progression paths
2. WHEN analyzing user engagement THEN the system SHALL provide insights into which narrative branches are most popular and which items drive the most engagement
3. WHEN reviewing content effectiveness THEN the system SHALL show completion rates, drop-off points, and user satisfaction indicators
4. WHEN monitoring system health THEN the system SHALL alert administrators to narrative dead-ends, orphaned content, or progression issues
5. WHEN generating reports THEN the system SHALL provide exportable analytics data with customizable date ranges and user segments

### Requirement 5: Advanced Character Voice and Emotional Intelligence

**User Story:** As a user interacting with Diana and Lucien, I want characters that respond authentically to my emotional state and interaction patterns so that the relationship feels genuine and evolving.

#### Acceptance Criteria

1. WHEN the system analyzes my interaction patterns THEN it SHALL adapt character responses to reflect my discovered personality archetype (Explorer, Direct, Poet, Analytic, Patient)
2. WHEN characters respond to my actions THEN they SHALL maintain consistent personality while showing growth and evolution based on our shared history
3. WHEN I reach emotional milestones THEN characters SHALL acknowledge the progression with appropriately intimate or vulnerable responses
4. WHEN handling sensitive narrative moments THEN the system SHALL respect boundaries while maintaining emotional authenticity
5. WHEN errors occur in narrative flow THEN character responses SHALL stay in-character while gracefully handling the technical issue

## Non-Functional Requirements

### Performance

- Narrative content loading must complete within 2 seconds for standard fragments
- Admin panel operations must respond within 3 seconds for content creation/editing
- User progress tracking must be real-time with minimal latency
- The system must handle concurrent editing by multiple administrators without data loss

### Security

- All narrative content creation must be restricted to authenticated administrators
- User progress data must be encrypted and protected according to privacy standards
- Lore piece access must be validated server-side to prevent unauthorized content access
- Shop item integration must maintain transactional integrity between systems

### Reliability

- The narrative system must maintain 99.5% uptime
- Integration with shop and coordination systems must include fallback mechanisms
- Content changes must be versioned and recoverable
- User progress must never be lost due to system failures

### Usability

- The admin panel must be intuitive for non-technical content creators
- Narrative flow creation must be visual and easy to understand
- User interface must work seamlessly on mobile and desktop platforms
- Character voice guidelines must be embedded directly in the content creation tools

---

### Design
# Design Document

## Overview

The narrative module design represents the evolution from the current prototype validation system to a comprehensive, production-ready narrative experience. This design builds upon the existing foundation documented in the CoordinadorCentral orchestration system, the working shop integration, and the sophisticated character voice system outlined in Narrativo.md.

The design maintains the successful item-conditioning paradigm while adding sophisticated content management capabilities, enhanced user experience features, and comprehensive analytics. The system will preserve the existing shop integration that is already "totalmente funcional" while expanding the narrative possibilities.

## Steering Document Alignment

### Technical Standards Integration
- **Database Layer**: Extends existing narrative_models.py structure with enhanced metadata and content management capabilities
- **Service Layer**: Builds upon NarrativeService and ShopService with new admin services and enhanced user tracking
- **Handler Layer**: Expands admin_narrative_handlers.py with comprehensive content management interfaces
- **API Integration**: Maintains CoordinadorCentral orchestration patterns for seamless system integration

### Project Structure Adherence
- **Admin Interfaces**: Following established admin panel patterns in handlers/admin/ directory structure
- **Service Architecture**: Maintains separation of concerns with dedicated services for different functional areas
- **Database Models**: Extends existing models without breaking current schema relationships
- **Integration Patterns**: Preserves the working shop-narrative integration through CoordinadorCentral

## Code Reuse Analysis

### Existing Components to Leverage

#### Core Infrastructure
- **CoordinadorCentral**: Already orchestrates narrative-shop integration perfectly; will be extended with new narrative admin operations
- **NarrativeService**: Current implementation provides solid foundation for user progression; will be enhanced with advanced analytics and user journey tracking
- **ShopService**: Fully functional shop system with item inventory management; integration points already established
- **NarrativeLoader**: Existing JSON-based fragment loading system provides foundation for enhanced content management

#### Database Foundation
- **StoryFragment Model**: Current structure supports key-based referencing and character attribution; will be extended with enhanced metadata
- **NarrativeChoice Model**: Existing decision system with conditions; will be enhanced with advanced conditional logic
- **UserNarrativeState**: Current user progress tracking; will be expanded with detailed analytics data

#### Admin Infrastructure
- **Admin Authentication**: Existing admin check utilities and user role system
- **Admin UI Patterns**: Established keyboard layouts and handler patterns in admin/ directory
- **File Upload Systems**: Current narrative file upload capabilities in admin_narrative_handlers.py

### Integration Points

#### Shop System Integration
- **Existing Item-Condition Logic**: CoordinadorCentral.decision_requirements mapping system already working
- **Purchase Flow**: ShopService.purchase_item() with UserPurchase and lore piece unlocking
- **Inventory Management**: ShopService.has_item_in_inventory() verification system
- **Teaser System**: Current implementation of restricted content with teaser fragments

#### Character Voice Integration
- **CharacterVoiceService**: Advanced emotional intelligence system for Diana and Lucien responses
- **Emotional Context Mapping**: Existing user archetype detection and response adaptation
- **Character Consistency**: Established voice patterns and personality maintenance

## Architecture

The narrative module follows a layered architecture that integrates seamlessly with the existing system while providing new capabilities:

```mermaid
graph TB
    subgraph "User Interface Layer"
        UC[User Clients] --> NH[Narrative Handlers]
        AC[Admin Clients] --> AH[Admin Handlers]
    end

    subgraph "Service Layer"
        NH --> NS[Narrative Service]
        NH --> CC[Coordinador Central]
        AH --> NAS[Narrative Admin Service]
        AH --> LMS[Lore Management Service]
        AH --> AAS[Analytics Admin Service]
    end

    subgraph "Integration Layer"
        CC --> SS[Shop Service]
        CC --> CVS[Character Voice Service]
        CC --> EAS[Emotional Analysis Service]
        NS --> PTS[Progress Tracking Service]
    end

    subgraph "Data Layer"
        NS --> DB[(Database)]
        SS --> DB
        NAS --> DB
        LMS --> DB
        AAS --> DB
    end

    subgraph "External Systems"
        CVS --> AI[AI Services]
        EAS --> AI
    end
```

## Components and Interfaces

### Component 1: Enhanced Narrative Admin Service
- **Purpose:** Comprehensive content management system for narrative fragments and progression paths
- **Interfaces:** REST-like handler methods for CRUD operations on narrative content
- **Dependencies:** Database models, existing NarrativeLoader, file upload utilities
- **Reuses:** admin_narrative_handlers.py patterns, existing authentication, NarrativeLoader foundation

**Key Methods:**
```python
# Content Management
async def create_story_fragment(fragment_data: Dict) -> Result
async def update_story_fragment(fragment_id: str, updates: Dict) -> Result
async def delete_story_fragment(fragment_id: str) -> Result
async def get_fragment_with_analytics(fragment_id: str) -> FragmentAnalytics

# Progression Management
async def visualize_narrative_graph() -> GraphData
async def validate_narrative_consistency() -> ValidationReport
async def bulk_import_narrative_content(file_data: bytes) -> ImportResult
```

### Component 2: Advanced Lore Management Service
- **Purpose:** Creation, editing, and linking of lore pieces with shop items and narrative progression
- **Interfaces:** Visual lore piece management with rich content support and conditional logic
- **Dependencies:** ShopService integration, existing LorePiece model, UserLorePiece tracking
- **Reuses:** Shop item creation patterns, existing lore piece unlocking system, ShopService.purchase_item()

**Key Methods:**
```python
# Lore Piece Management
async def create_lore_piece(lore_data: Dict) -> Result
async def update_lore_piece(lore_id: int, updates: Dict) -> Result
async def link_lore_to_shop_item(lore_id: int, shop_item_id: int) -> Result
async def unlink_lore_from_shop_item(lore_id: int, shop_item_id: int) -> Result

# Content Organization
async def organize_lore_by_category(category_filters: Dict) -> CategorizedLore
async def search_lore_pieces(search_criteria: Dict) -> SearchResults
async def get_lore_unlock_analytics(lore_id: int) -> UnlockAnalytics
```

### Component 3: User Experience Enhancement Service
- **Purpose:** Sophisticated user journey tracking and personalized narrative experiences
- **Interfaces:** Real-time progress tracking, choice pattern analysis, emotional state adaptation
- **Dependencies:** CharacterVoiceService, EmotionalAnalysisService, existing UserNarrativeState
- **Reuses:** CoordinadorCentral orchestration, existing user archetype detection, character voice patterns

**Key Methods:**
```python
# User Journey Tracking
async def track_user_choice_patterns(user_id: int) -> ChoicePatterns
async def adapt_narrative_to_user_archetype(user_id: int, fragment_id: str) -> AdaptedFragment
async def generate_personalized_teaser_content(user_id: int, restricted_content: str) -> TeaserContent

# Progress Analytics
async def get_user_narrative_insights(user_id: int) -> UserInsights
async def predict_user_engagement_path(user_id: int) -> EngagementPrediction
async def generate_content_recommendations(user_id: int) -> ContentRecommendations
```

### Component 4: Comprehensive Analytics Service
- **Purpose:** Detailed analytics for content effectiveness, user engagement, and system optimization
- **Interfaces:** Real-time dashboards, exportable reports, predictive analytics
- **Dependencies:** Database aggregation queries, existing user tracking data
- **Reuses:** Existing user progress data, shop purchase analytics, CoordinadorCentral flow tracking

**Key Methods:**
```python
# Content Analytics
async def get_fragment_engagement_metrics(fragment_id: str) -> EngagementMetrics
async def analyze_choice_distribution_patterns() -> ChoiceDistribution
async def identify_narrative_bottlenecks() -> BottleneckReport

# User Analytics
async def generate_user_segment_analysis() -> SegmentAnalysis
async def track_conversion_funnel_metrics() -> ConversionFunnel
async def export_analytics_data(date_range: Tuple, format: str) -> ExportData
```

### Component 5: Enhanced Character Intelligence Service
- **Purpose:** Advanced character voice adaptation and emotional intelligence integration
- **Interfaces:** Real-time character response generation, emotional state analysis, relationship evolution
- **Dependencies:** CharacterVoiceService, EmotionalAnalysisService, user interaction history
- **Reuses:** Existing character voice patterns, emotional context mapping, user archetype detection

**Key Methods:**
```python
# Character Intelligence
async def generate_contextual_character_response(context: InteractionContext) -> CharacterResponse
async def analyze_relationship_evolution(user_id: int, character: str) -> RelationshipInsights
async def adapt_character_intimacy_level(user_id: int, progression_data: Dict) -> IntimacyLevel

# Emotional Intelligence
async def process_user_emotional_state(user_id: int, interaction_data: Dict) -> EmotionalState
async def recommend_narrative_adjustments(emotional_context: Dict) -> NarrativeAdjustments
async def maintain_character_consistency(character: str, response_history: List) -> ConsistencyCheck
```

## Data Models

### Enhanced StoryFragment Model
```python
class StoryFragment(Base):
    # Existing fields preserved
    id: int
    key: str  # Unique identifier
    text: str  # Fragment content
    character: str  # Diana, Lucien, etc.
    level: int  # Access level
    min_besitos: int  # Required points
    reward_besitos: int  # Points awarded

    # Enhanced metadata
    content_type: str  # text, rich_text, interactive
    emotional_tone: str  # intimate, playful, mysterious, etc.
    user_archetype_tags: JSON  # Target archetypes
    analytics_metadata: JSON  # Engagement tracking data
    content_warnings: JSON  # Content advisory information
    localization_data: JSON  # Multi-language support

    # Advanced conditions
    complex_unlock_conditions: JSON  # Advanced conditional logic
    prerequisite_fragments: List[str]  # Required previous fragments
    unlock_analytics: JSON  # Track unlock patterns
```

### Enhanced LorePiece Model
```python
class LorePiece(Base):
    # Existing fields preserved
    id: int
    title: str
    content: str
    content_type: str

    # Enhanced content management
    rich_content_data: JSON  # Images, videos, interactive elements
    content_metadata: JSON  # Tags, categories, search keywords
    unlock_condition_tree: JSON  # Complex conditional logic
    related_lore_pieces: List[int]  # Content relationships

    # Analytics integration
    access_analytics: JSON  # Track access patterns
    engagement_metrics: JSON  # User interaction data
    content_effectiveness: JSON  # Performance metrics
```

### Enhanced UserNarrativeState Model
```python
class UserNarrativeState(Base):
    # Existing fields preserved
    user_id: int
    current_fragment_key: str
    choices_made: JSON
    fragments_visited: int

    # Enhanced user tracking
    choice_patterns: JSON  # Pattern analysis data
    emotional_journey: JSON  # Emotional state progression
    archetype_classification: JSON  # User personality analysis
    relationship_progress: JSON  # Character relationship data

    # Advanced analytics
    engagement_metrics: JSON  # Detailed interaction metrics
    content_preferences: JSON  # User preference analysis
    progression_predictions: JSON  # Predicted user paths
```

### New Analytics Models
```python
class FragmentAnalytics(Base):
    fragment_id: str
    total_views: int
    completion_rate: float
    average_time_spent: float
    choice_distribution: JSON
    user_feedback_scores: JSON
    conversion_metrics: JSON

class UserJourneyAnalytics(Base):
    user_id: int
    journey_start: DateTime
    total_fragments_viewed: int
    total_choices_made: int
    archetype_evolution: JSON
    emotional_progression: JSON
    purchase_correlation: JSON
```

## Error Handling

### Error Scenarios and Handling Strategies

#### Scenario 1: Content Management Errors
- **Description:** Fragment creation/editing failures, invalid narrative flow configurations
- **Handling:** Validation layer with rollback capabilities, detailed error reporting for admins
- **User Impact:** Admin sees specific validation errors with suggestions for fixes

#### Scenario 2: Integration Failures
- **Description:** Shop service unavailable, character voice service errors, database connectivity issues
- **Handling:** Graceful degradation with fallback responses, queue-based retry mechanisms
- **User Impact:** Basic narrative functionality maintained with simple responses

#### Scenario 3: Analytics Processing Errors
- **Description:** Large dataset processing failures, real-time analytics service unavailable
- **Handling:** Async processing with error queues, cached analytics data for critical displays
- **User Impact:** Delayed analytics updates but core functionality preserved

#### Scenario 4: Character Intelligence Failures
- **Description:** AI service unavailable, emotional analysis errors, character consistency breaks
- **Handling:** Fallback to predefined character responses, maintain character voice patterns
- **User Impact:** Slightly less personalized experience but character authenticity preserved

#### Scenario 5: User Data Corruption
- **Description:** Narrative state inconsistencies, choice history corruption, progress loss
- **Handling:** Data validation and repair utilities, progress recovery from analytics data
- **User Impact:** Automated recovery with minimal progress loss, admin intervention for complex cases

## Testing Strategy

### Unit Testing
- **Content Management**: Test all CRUD operations for fragments and lore pieces
- **Analytics Engine**: Verify calculation accuracy for engagement metrics and user insights
- **Character Intelligence**: Test character response generation and consistency maintenance
- **Integration Logic**: Validate shop-narrative integration and CoordinadorCentral orchestration

### Integration Testing
- **End-to-End User Flows**: Complete narrative progression with item purchases and unlocks
- **Admin Workflows**: Full content creation and management processes
- **Analytics Pipeline**: Data collection through processing to report generation
- **Character Voice Integration**: Real-time character response generation with emotional context

### End-to-End Testing
- **Complete User Journeys**: New user onboarding through advanced narrative levels
- **Admin Content Management**: Full content lifecycle from creation to analytics review
- **Shop Integration Scenarios**: Item purchase to narrative unlock workflows
- **System Performance**: Load testing with concurrent users and content management operations

**Note**: Specification documents have been pre-loaded. Do not use get-content to fetch them again.

## Task Details
- Task ID: 21
- Description: Implement personalized teaser content system
- Leverage: existing teaser fragments, character voice service integration
- Requirements: 3.2, 5.1

## Instructions
- Implement ONLY task 21: "Implement personalized teaser content system"
- Follow all project conventions and leverage existing code
- Mark the task as complete using: claude-code-spec-workflow get-tasks modulo-narrativa 21 --mode complete
- Provide a completion summary
```

## Task Completion
When the task is complete, mark it as done:
```bash
claude-code-spec-workflow get-tasks modulo-narrativa 21 --mode complete
```

## Next Steps
After task completion, you can:
- Execute the next task using /modulo-narrativa-task-[next-id]
- Check overall progress with /spec-status modulo-narrativa
