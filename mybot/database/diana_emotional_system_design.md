# Diana Emotional System - Design Documentation

## System Overview

The Diana Emotional System is a sophisticated database and service architecture designed to enable Diana to maintain complex emotional relationships with users. The system provides the foundation for emotional memory, relationship state tracking, contradiction detection, and personality adaptation.

### Core Components

1. **Emotional Memory (diana_emotional_memories)** - Stores individual interactions with emotional context
2. **Relationship State (diana_relationship_states)** - Maintains the current state of each user-Diana relationship
3. **Contradictions (diana_contradictions)** - Tracks contradictory information to maintain consistency
4. **Personality Adaptations (diana_personality_adaptations)** - Stores personalization data for Diana's interactions

## Database Schema Design

### Design Principles

1. **Query Performance** - All queries are optimized to execute in <100ms for real-time emotional context
2. **Natural Memory Decay** - Memories have importance and decay rates to mimic human memory
3. **Contextual Access** - Fast retrieval patterns based on emotion, time, and importance
4. **Privacy by Design** - Support for marking sensitive content and GDPR compliance
5. **Relationship Evolution** - Relationship status changes based on interaction patterns

### Emotional Memory Table (diana_emotional_memories)

This table stores individual emotional interactions between Diana and users:

```
id: Integer (PK)
user_id: BigInteger (FK to users.id)
interaction_type: Enum (GREETING, HELP_REQUEST, etc.)
timestamp: DateTime (when the interaction occurred)
summary: String (brief description)
content: Text (detailed content, potentially encrypted)
primary_emotion: Enum (JOY, SADNESS, etc.)
secondary_emotion: Enum (optional additional emotion)
intensity: Enum (VERY_LOW to VERY_HIGH)
context_data: JSON (additional structured context)
related_achievements: JSON (IDs of related achievements)
related_narrative_keys: JSON (keys of related narrative fragments)
importance_score: Float (higher = more important)
decay_rate: Float (how quickly memory fades)
last_recalled_at: DateTime (when memory was last accessed)
recall_count: Integer (how often memory has been recalled)
tags: JSON (array of string tags for filtering)
is_sensitive: Boolean (flag for sensitive content)
is_forgotten: Boolean (for GDPR compliance)
parent_memory_id: Integer (optional, for linked memories)
```

Key indices:
- user_id + timestamp (primary access pattern)
- user_id + primary_emotion (emotional search)
- user_id + importance_score (important memories)
- user_id + last_recalled_at (recently recalled)

### Relationship State Table (diana_relationship_states)

This table represents the current state of relationship between Diana and a user:

```
user_id: BigInteger (PK, FK to users.id)
status: Enum (INITIAL, ACQUAINTANCE, FRIENDLY, CLOSE, etc.)
trust_level: Float (0.0-1.0 scale)
familiarity: Float (how well Diana knows the user)
rapport: Float (quality of communication)
dominant_emotion: Enum (predominant emotion in relationship)
emotional_volatility: Float (how much emotions fluctuate)
positive_interactions: Integer (count of positive interactions)
negative_interactions: Integer (count of negative interactions)
relationship_started_at: DateTime (when relationship began)
last_interaction_at: DateTime (when last interaction occurred)
longest_absence_days: Integer (longest period without interaction)
typical_response_time_seconds: Integer (average response time)
typical_interaction_length: Integer (average message length)
communication_frequency: Float (interactions per day)
interaction_count: Integer (total number of interactions)
milestone_count: Integer (number of relationship milestones)
milestone_data: JSON (record of relationship milestones)
boundary_settings: JSON (user's boundaries)
communication_preferences: JSON (preferred communication styles)
topic_interests: JSON (topics with interest scores)
personality_adaptations: JSON (personality adaptation data)
linguistic_adaptations: JSON (linguistic adaptation data)
```

### Contradictions Table (diana_contradictions)

This table records contradictions in user information:

```
id: Integer (PK)
user_id: BigInteger (FK to users.id)
contradiction_type: String (type of contradiction)
original_statement: Text (original statement)
contradicting_statement: Text (contradicting statement)
resolution: Text (how contradiction was resolved)
detected_at: DateTime (when contradiction was detected)
context_data: JSON (additional context)
is_resolved: Boolean (whether contradiction is resolved)
resolved_at: DateTime (when contradiction was resolved)
related_memory_ids: JSON (IDs of related memories)
```

### Personality Adaptation Table (diana_personality_adaptations)

This table tracks how Diana adapts her personality to match user preferences:

```
id: Integer (PK)
user_id: BigInteger (FK to users.id)
warmth: Float (0.0-1.0 scale)
formality: Float (0.0-1.0 scale)
humor: Float (0.0-1.0 scale)
directness: Float (0.0-1.0 scale)
assertiveness: Float (0.0-1.0 scale)
curiosity: Float (0.0-1.0 scale)
emotional_expressiveness: Float (0.0-1.0 scale)
message_length_preference: Integer (optimal message length)
complexity_level: Float (0.0 simple to 1.0 complex)
emoji_usage: Float (0.0 none to 1.0 frequent)
response_delay: Integer (artificial delay in seconds)
topic_preferences: JSON (preferred topics)
taboo_topics: JSON (topics to avoid)
memory_reference_frequency: Float (how often to reference past)
adaptation_reason: Text (reason for adaptation)
last_significant_change: DateTime (when adaptation changed significantly)
confidence_score: Float (confidence in adaptation)
```

## Relationship Status Transitions

The system defines clear thresholds for relationship status transitions based on quantifiable metrics:

1. **INITIAL → ACQUAINTANCE**
   - Requirements: 5+ interactions

2. **ACQUAINTANCE → FRIENDLY**
   - Requirements: familiarity ≥ 0.3, trust_level ≥ 0.2

3. **FRIENDLY → CLOSE**
   - Requirements: trust_level ≥ 0.6, rapport ≥ 0.5, interaction_count ≥ 20

4. **CLOSE → INTIMATE**
   - Requirements: trust_level ≥ 0.8, rapport ≥ 0.7, interaction_count ≥ 50

5. **Any → STRAINED**
   - Triggered when: negative_interactions > positive_interactions AND interaction_count > 10

6. **STRAINED → REPAIRED**
   - Can be manually set when relationship issues are resolved

## Emotional Memory Evolution

Memories evolve over time through several mechanisms:

1. **Recall Reinforcement** - Each time a memory is recalled, its recall_count increases and last_recalled_at is updated
2. **Importance Scoring** - Memories with higher emotional intensity or significance get higher importance_score
3. **Memory Decay** - The decay_rate parameter determines how quickly a memory becomes less prominent
4. **Memory Linking** - Memories can be linked through parent_memory_id to create connected memory chains

## Service Layer Implementation

The DianaEmotionalService provides a comprehensive API for interacting with the emotional system:

### Memory Management

- `store_emotional_memory()` - Store a new emotional memory
- `get_recent_memories()` - Retrieve recent memories
- `get_memories_by_emotion()` - Get memories with specific emotions
- `get_important_memories()` - Get high-importance memories
- `get_contextual_memories()` - Get memories based on tags
- `forget_memory()` - Mark a memory as forgotten (GDPR)
- `forget_all_user_memories()` - Forget all memories for a user

### Relationship Management

- `get_relationship_state()` - Get current relationship state
- `update_relationship_status()` - Update relationship status
- `record_interaction()` - Record a general interaction

### Contradiction Management

- `record_contradiction()` - Record a contradiction
- `resolve_contradiction()` - Resolve a contradiction
- `get_unresolved_contradictions()` - Get unresolved contradictions

### Personality Adaptation

- `get_personality_adaptation()` - Get personality adaptation
- `update_personality_adaptation()` - Update personality adaptation

## Usage Patterns

### Recording Emotional Interactions

```python
await diana_service.store_emotional_memory(
    user_id=user_id,
    interaction_type=EmotionalInteractionType.PERSONAL_SHARE,
    summary="User shared personal feelings about work",
    content="The detailed content of the interaction...",
    primary_emotion=EmotionCategory.JOY,
    intensity=EmotionalIntensity.HIGH,
    tags=["work", "happiness", "achievement"]
)
```

### Retrieving Emotional Context

```python
# Get recent memories to provide context for the current conversation
result = await diana_service.get_recent_memories(user_id, limit=5)

# Get emotionally similar memories
result = await diana_service.get_memories_by_emotion(
    user_id, 
    EmotionCategory.SADNESS
)

# Get memories with relevant tags
result = await diana_service.get_contextual_memories(
    user_id, 
    tags=["family", "birthday"]
)
```

### Tracking Relationship Evolution

```python
# Get current relationship state
result = await diana_service.get_relationship_state(user_id)

# Record a general interaction (updates metrics)
await diana_service.record_interaction(
    user_id=user_id,
    interaction_length=len(message_text)
)

# Update relationship status manually if needed
await diana_service.update_relationship_status(
    user_id=user_id,
    status=RelationshipStatus.CLOSE,
    reason="Significant trust established through personal sharing"
)
```

### Adapting Personality

```python
# Get current personality adaptation
result = await diana_service.get_personality_adaptation(user_id)

# Update personality based on observed preferences
await diana_service.update_personality_adaptation(
    user_id=user_id,
    adaptation_data={
        "warmth": 0.8,  # More warm and friendly
        "formality": 0.3,  # Less formal
        "humor": 0.7,  # More humorous
        "emoji_usage": 0.6  # Moderate emoji usage
    },
    reason="User responds better to warm, informal communication"
)
```

## Performance Considerations

1. **Indexing Strategy** - Multiple indices for different query patterns
2. **Memory Retrieval Limits** - Default limits on memory retrieval to ensure fast responses
3. **Lazy Loading** - Relationships use lazy loading patterns appropriate to access frequency
4. **JSON Optimization** - JSON fields for flexible schema without excessive normalization
5. **Session Management** - Proper session handling to prevent connection leaks

## Security and Privacy

1. **Sensitive Flag** - is_sensitive flag for content that requires special handling
2. **GDPR Compliance** - is_forgotten flag for "right to be forgotten" without deleting data
3. **Memory Access Patterns** - Memory access is always through the user_id to prevent data leakage

## Integration with Existing Systems

The emotional system integrates with the existing system through:

1. **User Table Relationship** - All tables reference the existing users table
2. **Narrative Integration** - related_narrative_keys links memories to narrative fragments
3. **Achievement Integration** - related_achievements links memories to achievements
4. **Mission Integration** - Potential for missions based on relationship milestones

## Future Extensions

1. **Emotional Analysis** - Integration with NLP for better emotion detection
2. **Memory Consolidation** - Algorithms to consolidate related memories
3. **Emotional Intelligence Metrics** - Track Diana's emotional intelligence development
4. **Multi-user Relationship Awareness** - Understanding relationships between users
5. **Emotional Timeline Visualization** - Visual representation of relationship evolution

## Example Handlers

The system includes example handlers that demonstrate how to use the emotional system:

1. `/relationship_status` - View current relationship status with Diana
2. `/recent_memories` - View recent emotional memories with Diana
3. `/personality_preferences` - View Diana's personality adaptation to the user

Additionally, a message handler processes general messages and updates emotional memory based on detected emotions.

## Conclusion

The Diana Emotional System provides a robust foundation for building emotionally intelligent interactions between Diana and users. The system's careful design balances performance, flexibility, and emotional depth to create meaningful and evolving relationships.