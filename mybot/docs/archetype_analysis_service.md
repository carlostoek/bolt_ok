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

| Archetype       | Description                           |
|-----------------|---------------------------------------|
| **Intellectual**| Analytical thinking and knowledge-seeking |
| **Emotional**   | Emotional depth and expression        |
| **Exploratory** | Curiosity and discovery-oriented      |
| **Vulnerable**  | Open to emotional vulnerability       |
| **Philosophical**| Deep thinking and meaning-seeking    |
| **Direct**      | Straightforward communication style   |
| **Patient**     | Tolerance for longer interactions     |
| **Reciprocal**  | Mutual exchange and relationship building |

#### Sub-Archetypes (10 categories)

| Sub-Archetype            | Primary Correlation  | Description                                        |
|--------------------------|----------------------|----------------------------------------------------|
| **Romantic Intellectual**| Intellectual + Emotional | Meaningful connections through intellect         |
| **Skeptical Thinker**    | Intellectual + Philosophical | Values critical analysis                   |
| **Hedonist Philosopher** | Philosophical + Exploratory | Balances pleasure with contemplation       |
| **Pure Theorist**        | Intellectual + Patient | Focuses on abstract frameworks                |
| **Empathetic Emotional** | Emotional + Reciprocal | High emotional intelligence                   |
| **Passionate Emotional** | Emotional + Direct    | Intense emotional authenticity                |
| **Wounded Healer**       | Vulnerable + Emotional | Uses growth to help others                    |
| **Adventure Seeker**     | Exploratory + Direct  | Craves new challenges                         |
| **Collector Explorer**   | Exploratory + Patient | Systematically gathers experiences            |
| **Freedom Lover**        | Direct + Exploratory  | Values independence                           |

## API Reference

### ArchetypeAnalyzer

#### analyze_l1_choices()

```python
async def analyze_l1_choices(
    self,
    user_id: int,
    choices: List[Dict[str, Any]],
    timings: List[float]
) -> Dict[str, Any]
```

- **Returns:** primary/sub-scores, cognitive style, archetype names, confidence, indicators.

#### store_classification_results()

```python
async def store_classification_results(
    self,
    user_id: int,
    analysis_results: Dict[str, Any]
) -> Optional[ArchetypeClassification]
```

- **Returns:** Stored `ArchetypeClassification` or `None`.

#### get_user_classification()

```python
async def get_user_classification(self, user_id: int) -> Optional[Dict[str, Any]]
```

- **Returns:** Stored classification details.

### ArchetypeIntegrationService

#### evaluate_ramificado_activation()

```python
async def evaluate_ramificado_activation(self, user_id: int) -> ArchetypeBranchingDecision
```

- **Returns:** Activation flag, recommended branch, fallback flag, metadata.

#### get_fallback_archetype()

```python
async def get_fallback_archetype(self, user_id: int) -> str
```

- **Maps** expanded archetypes to legacy 5-archetype system.

## Integration Guide

Basic usage example provided for running analysis, storing results, and branching decisions.

## Usage Examples

Includes complete L1F1 flow, confidence-based decisions, fallback integration.

## Error Handling

Describes error types, recovery strategies, logging levels.

## Performance Considerations

Targets: <2s analysis, 100 concurrent users, <500ms DB.

## Troubleshooting

Common issues: low confidence, analysis failures, performance degradation.

### Monitoring & Diagnostics

Provides log grep and SQL queries for diagnostics.