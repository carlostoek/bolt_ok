# Archetype Analysis Service Documentation

## Overview

The Archetype Analysis Service is a comprehensive psychological profiling system for Diana's Sistema Narrativo Ramificado. It analyzes user interactions during Level 1 Fragment 1 (L1F1) to classify users into distinct psychological archetypes, enabling personalized narrative experiences and enhanced user engagement.

## Table of Contents

- [System Architecture](#system-architecture)
- [Core Components](#core-components)
- [API Reference](#api-reference)
- [Integration Guide](#integration-guide)
- [Usage Examples](#usage-examples)
- [Error Handling](#error-handling)
- [Performance Considerations](#performance-considerations)
- [Troubleshooting](#troubleshooting)

## System Architecture

The archetype analysis system consists of several interconnected components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   L1F1 Choices  │───▶│ ArchetypeAnalyzer│───▶│ Classification  │
│   + Timings     │    │                 │    │   Storage       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Integration     │
                    │ Service         │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Narrative       │
                    │ Branching       │
                    └─────────────────┘
```

### Primary Components

1. **ArchetypeAnalyzer**: Core analysis engine
2. **ArchetypeIntegrationService**: System integration and fallback handling
3. **ResponseTimeAnalyzer**: Cognitive style analysis
4. **ArchetypeClassification**: Database model for storage
5. **Monitoring Service**: Performance and health tracking

## Core Components

### ArchetypeAnalyzer

The main analysis engine that processes L1F1 interaction data to determine user archetypes.

**Key Features:**
- Processes choice weights and timing data
- Calculates primary and sub-archetype scores
- Provides confidence scoring and behavioral indicators
- Robust error handling with graceful fallbacks

**Primary Methods:**
- `analyze_l1_choices()`: Main analysis workflow
- `store_classification_results()`: Database persistence
- `get_user_classification()`: Retrieve stored classification

### Archetype Classification System

#### Primary Archetypes (8 categories)

| Archetype | Description | Key Characteristics |
|-----------|-------------|-------------------|
| **Intellectual** | Analytical thinking and knowledge-seeking | Logic-driven, curious, systematic |
| **Emotional** | Emotional depth and expression | Empathetic, feeling-oriented, connective |
| **Exploratory** | Curiosity and discovery-oriented | Adventurous, open to new experiences |
| **Vulnerable** | Open to emotional vulnerability | Authentic, sharing, trust-building |
| **Philosophical** | Deep thinking and meaning-seeking | Contemplative, wisdom-seeking, profound |
| **Direct** | Straightforward communication style | Clear, decisive, action-oriented |
| **Patient** | Tolerance for longer interactions | Reflective, thorough, persistent |
| **Reciprocal** | Mutual exchange and relationship building | Collaborative, giving, balanced |

#### Sub-Archetypes (10 categories)

Sub-archetypes provide granular classification for nuanced personalization:

| Sub-Archetype | Primary Correlation | Description |
|---------------|-------------------|-------------|
| **Romantic Intellectual** | Intellectual + Emotional | Seeks meaningful connections through intellectual discourse |
| **Skeptical Thinker** | Intellectual + Philosophical | Questions assumptions, values critical analysis |
| **Hedonist Philosopher** | Philosophical + Exploratory | Balances pleasure-seeking with deep contemplation |
| **Pure Theorist** | Intellectual + Patient | Focuses on abstract concepts and frameworks |
| **Empathetic Emotional** | Emotional + Reciprocal | High emotional intelligence, seeks harmony |
| **Passionate Emotional** | Emotional + Direct | Intense emotional expressions, authentic connections |
| **Wounded Healer** | Vulnerable + Emotional | Uses personal growth to help others |
| **Adventure Seeker** | Exploratory + Direct | Craves new experiences and challenges |
| **Collector Explorer** | Exploratory + Patient | Systematically gathers knowledge/experiences |
| **Freedom Lover** | Direct + Exploratory | Values independence and autonomy |

## API Reference

### ArchetypeAnalyzer

#### analyze_l1_choices()

Analyzes Level 1 Fragment 1 choices to determine user archetype.

```python
async def analyze_l1_choices(
    self,
    user_id: int,
    choices: List[Dict[str, Any]],
    timings: List[float]
) -> Dict[str, Any]
```

**Parameters:**
- `user_id`: Unique user identifier
- `choices`: List of user choice data with archetype weights
- `timings`: Response times in seconds for each choice

**Choice Data Structure:**
```python
{
    'choice_id': 1,
    'archetype_weights': {
        'intellectual': 2.5,
        'philosophical': 1.8,
        'patient': 1.0
    },
    'sub_archetype_weights': {
        'romantic_intellectual': 2.0,
        'pure_theorist': 1.5
    }
}
```

**Returns:**
```python
{
    'primary_scores': ArchetypeScores,      # Primary archetype scores
    'sub_scores': SubArchetypeScores,       # Sub-archetype scores
    'timing_analysis': Dict[str, Any],      # Cognitive style analysis
    'dominant_archetype': str,              # Primary archetype name
    'sub_archetype': str,                   # Dominant sub-archetype
    'confidence_score': float,              # Classification confidence (0.0-1.0)
    'behavioral_indicators': List[str],     # Detected behavioral patterns
    'analysis_metadata': Dict[str, Any]     # Analysis statistics
}
```

#### store_classification_results()

Stores archetype classification in the database.

```python
async def store_classification_results(
    self,
    user_id: int,
    analysis_results: Dict[str, Any]
) -> Optional[ArchetypeClassification]
```

**Parameters:**
- `user_id`: Unique user identifier
- `analysis_results`: Results from `analyze_l1_choices()`

**Returns:**
- `ArchetypeClassification` instance or `None` on failure

#### get_user_classification()

Retrieves stored archetype classification for a user.

```python
async def get_user_classification(self, user_id: int) -> Optional[Dict[str, Any]]
```

**Returns:**
```python
{
    'primary_archetype': str,
    'archetype_confidence': float,
    'primary_scores': Dict[str, float],
    'sub_scores': Dict[str, float],
    'cognitive_style': str,
    'response_consistency': float,
    'temporal_pattern': str,
    'secondary_traits': List[str],
    'trait_strengths': List[str],
    'created_at': datetime,
    'updated_at': datetime
}
```

### ArchetypeIntegrationService

#### evaluate_ramificado_activation()

Evaluates whether to activate the ramificado system for a user.

```python
async def evaluate_ramificado_activation(self, user_id: int) -> ArchetypeBranchingDecision
```

**Returns:**
```python
ArchetypeBranchingDecision(
    activate_ramificado=bool,           # Whether to activate ramificado
    primary_archetype=str,              # User's primary archetype
    confidence_score=float,             # Classification confidence
    recommended_narrative_branch=str,   # Recommended narrative path
    fallback_to_standard=bool,          # Whether to use standard system
    detection_metadata=Dict[str, Any]   # Additional metadata
)
```

#### get_fallback_archetype()

Maps expanded archetypes to the legacy 5-archetype system.

```python
async def get_fallback_archetype(self, user_id: int) -> str
```

**Archetype Mapping:**
- `intellectual` → `achiever`
- `emotional` → `socializer`
- `exploratory` → `explorer`
- `vulnerable` → `socializer`
- `philosophical` → `achiever`
- `direct` → `challenger`
- `patient` → `creator`
- `reciprocal` → `socializer`

## Integration Guide

### Basic Integration

```python
from services.archetype_analyzer import ArchetypeAnalyzer
from services.archetype_integration_service import ArchetypeIntegrationService

# Initialize services
analyzer = ArchetypeAnalyzer(session)
integration_service = ArchetypeIntegrationService(session)

# Analyze user choices
choices = [/* L1F1 choice data */]
timings = [22.3, 18.5, 25.1]

analysis_result = await analyzer.analyze_l1_choices(user_id, choices, timings)

# Store results
classification = await analyzer.store_classification_results(user_id, analysis_result)

# Check ramificado activation
decision = await integration_service.evaluate_ramificado_activation(user_id)

if decision.activate_ramificado:
    # Use expanded narrative system
    narrative_branch = decision.recommended_narrative_branch
else:
    # Use fallback system
    fallback_archetype = await integration_service.get_fallback_archetype(user_id)
```

### Error Handling Integration

```python
try:
    analysis_result = await analyzer.analyze_l1_choices(user_id, choices, timings)

    if analysis_result.get('analysis_metadata', {}).get('error_fallback'):
        # Handle fallback result
        logger.warning(f"Using fallback analysis for user {user_id}")

    # Proceed with classification
    classification = await analyzer.store_classification_results(user_id, analysis_result)

except Exception as e:
    # Use integration service for graceful fallback
    fallback_result = await integration_service.handle_analysis_failure(
        user_id,
        {'error_type': 'analysis_failure', 'severity': 'medium'}
    )

    # Continue with fallback strategy
    archetype = fallback_result['archetype_classification']['archetype']
```

## Usage Examples

### Example 1: Complete L1F1 Analysis

```python
async def process_l1f1_completion(user_id: int, user_choices: List[Dict], response_times: List[float]):
    """Process completion of L1F1 and determine archetype."""

    analyzer = ArchetypeAnalyzer(session)
    integration_service = ArchetypeIntegrationService(session)

    # Perform archetype analysis
    analysis_result = await analyzer.analyze_l1_choices(user_id, user_choices, response_times)

    # Log analysis details
    logger.info(f"Archetype analysis for user {user_id}: "
               f"{analysis_result['dominant_archetype']} "
               f"(confidence: {analysis_result['confidence_score']:.2f})")

    # Store classification
    classification = await analyzer.store_classification_results(user_id, analysis_result)

    # Determine system activation
    decision = await integration_service.evaluate_ramificado_activation(user_id)

    if decision.activate_ramificado:
        # Activate enhanced narrative system
        await activate_ramificado_experience(user_id, decision.recommended_narrative_branch)
        return {
            'system': 'ramificado',
            'archetype': analysis_result['dominant_archetype'],
            'branch': decision.recommended_narrative_branch
        }
    else:
        # Use standard system with fallback archetype
        fallback_archetype = await integration_service.get_fallback_archetype(user_id)
        await activate_standard_experience(user_id, fallback_archetype)
        return {
            'system': 'standard',
            'archetype': fallback_archetype,
            'reason': decision.detection_metadata.get('reason')
        }
```

### Example 2: Confidence-Based Decisions

```python
async def make_archetype_decision(user_id: int) -> str:
    """Make archetype-based decision with confidence thresholds."""

    integration_service = ArchetypeIntegrationService(session)
    confidence_check = await integration_service.check_classification_confidence(user_id)

    if confidence_check['confidence_level'] == 'high':
        # High confidence - use full ramificado system
        return 'ramificado_full'
    elif confidence_check['confidence_level'] == 'medium':
        # Medium confidence - enhanced standard system
        return 'standard_enhanced'
    elif confidence_check['confidence_level'] == 'low':
        # Low confidence - basic personalization
        return 'standard_basic'
    else:
        # No/insufficient data - default experience
        return 'default'
```

### Example 3: Fallback Integration

```python
async def ensure_user_experience(user_id: int) -> Dict[str, Any]:
    """Ensure user gets appropriate experience regardless of system state."""

    integration_service = ArchetypeIntegrationService(session)

    # Try comprehensive fallback compatibility
    compatibility_result = await integration_service.ensure_fallback_compatibility(user_id)

    if compatibility_result['integration_mode'] == 'expanded':
        # Full expanded system
        return {
            'experience_type': 'personalized_ramificado',
            'archetype': compatibility_result['primary_archetype'],
            'features': compatibility_result['recommendations']
        }

    elif compatibility_result['integration_mode'] in ['enhanced_fallback', 'basic_fallback']:
        # Fallback to 5-archetype system
        return {
            'experience_type': 'standard_personalized',
            'archetype': compatibility_result['fallback_archetype'],
            'features': ['basic_personalization', 'standard_content']
        }

    else:
        # Error fallback - safe minimal experience
        return {
            'experience_type': 'safe_default',
            'archetype': 'explorer',
            'features': ['basic_content_only']
        }
```

## Error Handling

The archetype analysis system implements comprehensive error handling at multiple levels:

### Error Types

1. **Input Validation Errors**
   - Invalid user_id
   - Malformed choice data
   - Invalid timing values

2. **Analysis Errors**
   - Choice weight processing failures
   - Timing modifier calculation errors
   - Confidence calculation issues

3. **Database Errors**
   - Connection failures
   - Storage failures
   - Retrieval errors

4. **System Integration Errors**
   - Service initialization failures
   - Inter-service communication errors

### Error Recovery Strategies

1. **Graceful Degradation**
   - Use fallback analysis when primary analysis fails
   - Provide default values for missing data
   - Continue with reduced functionality

2. **Automatic Retry**
   - Retry failed operations with exponential backoff
   - Use circuit breaker pattern for repeated failures

3. **Fallback Integration**
   - Map to 5-archetype system when expanded analysis fails
   - Use emotional analysis data for inference
   - Provide safe default archetypes

### Logging Levels

- **DEBUG**: Detailed processing information
- **INFO**: Successful operations and analysis results
- **WARNING**: Non-critical errors and fallback usage
- **ERROR**: Critical errors that affect functionality

## Performance Considerations

### Requirements

- **Analysis Time**: < 2 seconds per user
- **Concurrent Users**: Up to 100 simultaneous analyses
- **Memory Usage**: < 1GB for 500 concurrent analyses
- **Database Performance**: < 500ms for storage operations

### Optimization Strategies

1. **Efficient Choice Processing**
   - Vectorized operations where possible
   - Early termination for invalid data
   - Minimal object creation

2. **Database Optimization**
   - Use appropriate indexes
   - Batch operations when possible
   - Connection pooling

3. **Caching Strategy**
   - Cache frequently accessed classifications
   - Use Redis for temporary analysis results
   - Implement TTL for cache invalidation

4. **Monitoring**
   - Track analysis performance metrics
   - Monitor database query times
   - Alert on performance degradation

## Troubleshooting

### Common Issues

#### Issue: Low Confidence Classifications

**Symptoms:**
- Users receiving default experiences
- High fallback usage
- Confidence scores < 0.7

**Diagnostic Steps:**
1. Check choice data quality
2. Verify timing data accuracy
3. Review archetype weight calibration

**Solutions:**
- Recalibrate archetype weights
- Improve L1F1 choice design
- Adjust confidence thresholds

#### Issue: Analysis Failures

**Symptoms:**
- High error rates in logs
- Users getting emergency fallbacks
- Database storage failures

**Diagnostic Steps:**
1. Check system resources
2. Verify database connectivity
3. Review error logs for patterns

**Solutions:**
- Scale system resources
- Implement connection retry logic
- Add circuit breakers

#### Issue: Performance Degradation

**Symptoms:**
- Analysis times > 2 seconds
- Timeout errors
- High memory usage

**Diagnostic Steps:**
1. Profile analysis workflow
2. Check database query performance
3. Monitor memory usage patterns

**Solutions:**
- Optimize database queries
- Implement result caching
- Scale infrastructure

### Monitoring Commands

#### Check System Health
```bash
# Check analysis performance
grep "archetype analysis" /var/log/diana.log | tail -100

# Monitor error rates
grep "ERROR.*archetype" /var/log/diana.log | wc -l

# Check confidence distribution
grep "confidence:" /var/log/diana.log | awk '{print $NF}' | sort -n
```

#### Database Diagnostics
```sql
-- Check classification distribution
SELECT primary_archetype, COUNT(*)
FROM archetype_classifications
GROUP BY primary_archetype;

-- Monitor confidence levels
SELECT
    CASE
        WHEN archetype_confidence >= 0.8 THEN 'high'
        WHEN archetype_confidence >= 0.7 THEN 'medium'
        WHEN archetype_confidence >= 0.5 THEN 'low'
        ELSE 'insufficient'
    END as confidence_level,
    COUNT(*)
FROM archetype_classifications
GROUP BY confidence_level;

-- Recent analysis activity
SELECT DATE(created_at), COUNT(*)
FROM archetype_classifications
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY DATE(created_at);
```

### Support Resources

- **Error Code Reference**: See `services/archetype_analyzer.py` for detailed error handling
- **Performance Metrics**: Available through monitoring service
- **API Documentation**: This document and inline code documentation
- **System Architecture**: See system design documents

For additional support, check the comprehensive logging output and monitoring dashboards for real-time system status.