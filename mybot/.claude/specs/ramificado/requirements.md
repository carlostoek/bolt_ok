# Requirements Document - Sistema Narrativo Ramificado Diana

## Introduction

The Sistema Narrativo Ramificado Diana aims to transform the current linear narrative system into an intelligent branching ecosystem where each player experiences a completely different story based on their psychological archetype. This sophisticated system will analyze user behavior, response patterns, and emotional markers during Level 1 interactions to classify users into distinct psychological archetypes, then deliver personalized narrative experiences that evolve and branch based on their authentic personality traits.

The system leverages advanced behavioral analysis, timing pattern recognition, and emotional intelligence to create truly personalized storytelling experiences that drive deeper engagement and higher VIP conversion rates through meaningful character connection.

## Alignment with Product Vision

This feature directly supports the core product goals outlined in product.md:

- **Drive VIP subscriptions through engagement and emotional attachment**: By creating personalized narrative experiences that feel uniquely crafted for each user's psychological profile, users develop stronger emotional connections that naturally lead to VIP conversions.

- **Sophisticated psychological framework**: Builds upon the existing narrative philosophy of authentic vulnerability, emotional intelligence evaluation, and progressive revelation by making these elements adaptive to individual user archetypes.

- **Character consistency with enhanced personalization**: Maintains Diana's mysterious seductive essence and Lucien's supportive role while allowing their interactions to adapt to different user psychological profiles for maximum resonance.

- **Quality over quantity approach**: Each narrative branch represents a carefully crafted experience designed specifically for users with similar psychological patterns, ensuring high-quality, meaningful interactions rather than generic content.

## Requirements

### Requirement 1: Archetype Analysis System

**User Story:** As a system administrator, I want an intelligent archetype classification system that analyzes user behavior patterns during Level 1 interactions, so that users can be automatically classified into psychological archetypes for personalized narrative delivery.

#### Acceptance Criteria

1. WHEN a user completes their first interaction with L1F1 (redesigned archetype analyzer fragment) THEN the system SHALL capture response timing, choice selection, and behavioral markers for archetype analysis
2. WHEN a user's response time is under 10 seconds THEN the system SHALL increment their "direct" and "passionate_emotional" archetype scores
3. WHEN a user's response time is between 15-35 seconds THEN the system SHALL increment their "thoughtful" and "philosophical" archetype scores
4. WHEN a user selects choices containing intellectual keywords THEN the system SHALL increase their "intellectual" and "analytical" scores by 2.0 points
5. WHEN a user selects choices containing emotional keywords THEN the system SHALL increase their "emotional" and "vulnerable" scores by 2.0 points
6. WHEN a user completes 3-5 Level 1 interactions THEN the system SHALL calculate their primary archetype classification with confidence scores
7. IF archetype confidence is above 0.8 THEN the system SHALL activate personalized narrative branching for that user
8. WHEN archetype classification is complete THEN the system SHALL store the results in the existing ArchetypeClassification model with primary and secondary trait mappings

### Requirement 2: Dynamic L1F1 Fragment System

**User Story:** As a content creator, I want L1F1 to be redesigned as an intelligent archetype detection system with sophisticated choice options, so that user responses can effectively reveal their psychological patterns while maintaining Diana's mysterious character voice.

#### Acceptance Criteria

1. WHEN a user encounters the redesigned L1F1 THEN the system SHALL present 5 distinct choice options each targeting different archetype detection
2. WHEN L1F1 displays choices THEN each choice SHALL contain embedded archetype_weights and sub_archetype_weights for scoring
3. WHEN user makes a choice THEN the system SHALL track response_time, choice_index, and hesitation_patterns automatically
4. WHEN choice tracking is active THEN the system SHALL capture behavioral_markers including depth_seeking, authenticity_declaration, aesthetic_appreciation, pattern_recognition, and persistence_explanation
5. IF user shows "choice_l1_curiosity_intellectual" pattern THEN the system SHALL weight intellectual(3.0), philosophical(2.0), and analytical(1.0) scores
6. IF user shows "choice_l1_curiosity_emotional" pattern THEN the system SHALL weight emotional(3.0), vulnerable(2.0), and reciprocal(1.0) scores
7. WHEN fragment displays THEN Diana's voice SHALL maintain mysterious seductive essence while introducing archetype-revealing scenarios naturally

### Requirement 3: Response Time Analysis Engine

**User Story:** As a behavioral analyst, I want sophisticated response timing analysis that reveals cognitive and emotional processing patterns, so that the system can distinguish between quick intuitive responses, thoughtful deliberation, and various emotional processing styles.

#### Acceptance Criteria

1. WHEN user response time is under 10 seconds THEN the system SHALL classify as "quick_intuitive" and increment directness scores
2. WHEN user response time is 10-30 seconds THEN the system SHALL classify as "thoughtful" and increment philosophical scores
3. WHEN user response time exceeds 30 seconds THEN the system SHALL classify as "deliberate" and increment contemplative scores
4. WHEN analyzing response patterns THEN the system SHALL calculate consistency_score based on timing variance across interactions
5. WHEN response patterns show acceleration (getting faster) THEN the system SHALL flag "growing_comfort" behavioral pattern
6. WHEN response patterns show deceleration (getting slower) THEN the system SHALL flag "increasing_thoughtfulness" behavioral pattern
7. IF response timing is extremely consistent (variance < 1 second) THEN the system SHALL flag potential artificial behavior for review
8. WHEN timing analysis is complete THEN the system SHALL store patterns in EmotionalInteraction model with response_type classification

### Requirement 4: Multi-Archetype Classification Algorithm

**User Story:** As a user experience designer, I want a sophisticated archetype classification system that can identify primary and secondary personality traits, so that narrative branching can accommodate complex psychological profiles rather than simple categories.

#### Acceptance Criteria

1. WHEN user completes archetype analysis THEN the system SHALL calculate scores for all 8 primary archetype dimensions (intellectual, emotional, exploratory, vulnerable, philosophical, direct, patient, reciprocal)
2. WHEN primary scores are calculated THEN the system SHALL determine the highest-scoring dimension as primary_archetype
3. WHEN primary archetype is determined THEN the system SHALL calculate sub_archetype based on secondary score combinations
4. IF intellectual and emotional scores are both high THEN the system SHALL classify as "romantic_intellectual" sub-archetype
5. IF intellectual and philosophical scores dominate THEN the system SHALL classify as "skeptical_thinker" or "pure_theorist" based on additional patterns
6. WHEN archetype confidence is below 0.7 THEN the system SHALL classify as "mixed_traits" and include multiple secondary_archetypes
7. WHEN classification is complete THEN the system SHALL store comprehensive archetype data including raw_scores, sub_scores, confidence_level, and cognitive_style in the database
8. IF user shows inconsistent patterns THEN the system SHALL flag for "requires_observation" and continue gathering data

### Requirement 5: Narrative Branch Selection Engine

**User Story:** As a narrative designer, I want an intelligent system that selects appropriate narrative branches based on user archetypes, so that each user receives story content specifically crafted for their psychological profile and behavioral patterns.

#### Acceptance Criteria

1. WHEN user's archetype classification is confirmed THEN the system SHALL select narrative fragments tagged for their primary archetype
2. WHEN branching decision point is reached THEN the system SHALL present choices weighted toward user's archetype preferences
3. IF user is classified as "explorer_deep" THEN the system SHALL prioritize fragments with complexity, pattern recognition challenges, and layered meaning
4. IF user is classified as "direct_authentic" THEN the system SHALL prioritize fragments with emotional honesty, clear communication, and genuine connection opportunities
5. IF user is classified as "poet_desire" THEN the system SHALL prioritize fragments with aesthetic beauty, metaphorical language, and artistic expression
6. WHEN mixed archetype traits are detected THEN the system SHALL blend narrative elements from multiple archetype-specific fragment sets
7. WHEN narrative branch is selected THEN the system SHALL maintain Diana's character consistency while adapting interaction style to match user psychological preferences
8. IF archetype-specific content is unavailable THEN the system SHALL fall back to default linear progression without breaking user experience

### Requirement 6: Behavioral Tracking Integration

**User Story:** As a system architect, I want seamless integration with existing emotional analysis and user tracking systems, so that archetype classification enhances rather than duplicates current behavioral analysis capabilities.

#### Acceptance Criteria

1. WHEN archetype analysis is performed THEN the system SHALL integrate with existing EmotionalAnalysisService without breaking current functionality
2. WHEN user interactions are tracked THEN the system SHALL update both new archetype scores AND existing emotional profile data
3. WHEN timing analysis is performed THEN the system SHALL leverage existing EmotionalInteraction model to store detailed behavioral data
4. WHEN archetype classification changes THEN the system SHALL update ArchetypeClassification model and maintain evolution history
5. IF existing CoordinadorCentral workflows are active THEN the new archetype system SHALL integrate through established service patterns
6. WHEN behavioral patterns are detected THEN the system SHALL flag unusual patterns using existing EmotionalAnalysisService warning mechanisms
7. WHEN user shows archetype evolution THEN the system SHALL track progression in archetype_stability field while maintaining data continuity
8. IF integration fails THEN the system SHALL gracefully degrade to existing linear narrative without user-facing errors

## Non-Functional Requirements

### Performance
- Archetype classification analysis must complete within 2 seconds of user choice submission
- Response time tracking must not introduce perceptible delays in user interactions
- Narrative branch selection must complete within 1 second to maintain conversation flow
- System must handle concurrent archetype analysis for up to 100 users simultaneously
- Database queries for archetype-based fragment selection must execute within 500ms

### Security
- User psychological data must be encrypted at rest using existing database encryption
- Archetype analysis data must be accessible only to authorized admin users
- Behavioral tracking must comply with existing privacy policies
- User consent must be obtained before psychological profiling as per current bot terms
- Archetype classification data must be anonymized for any analytics reporting

### Reliability
- Archetype classification system must maintain 99.5% uptime aligned with existing bot availability
- Graceful degradation to linear narrative required if archetype system encounters errors
- Behavioral data collection must continue even if analysis services are temporarily unavailable
- Database integrity must be maintained during archetype classification updates
- System must recover automatically from temporary analysis service failures

### Usability
- Archetype classification must be invisible to users (no explicit "you are being analyzed" messaging)
- Narrative transitions between branches must feel natural and maintain immersion
- Users must not notice when they receive archetype-specific vs. default content
- Diana's character voice must remain consistent across all archetype-specific interactions
- Administrative interface for archetype management must integrate with existing admin panel patterns