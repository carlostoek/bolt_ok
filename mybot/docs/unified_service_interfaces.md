# Unified Service Interfaces Documentation

## Overview

This document describes the unified service interfaces designed for the Diana narrative ecosystem. These interfaces provide standardized APIs for all narrative operations, ensuring consistency, extensibility, and maintainability across the entire system.

## Interface Categories

### 1. Core Narrative Operations
- **IUserNarrativeService**: User narrative state management
- **IUnifiedNarrativeOrchestrator**: Central narrative coordination
- **IUnifiedNarrativeAnalytics**: Narrative performance analytics
- **IUnifiedNarrativeConfiguration**: System configuration management

### 2. User Experience Management
- **IUserInteractionProcessor**: Centralized interaction processing
- **IEmotionalStateManager**: Emotional analysis and adaptation
- **IContentDeliveryService**: Personalized content delivery

### 3. System Integration
- **IRewardSystem**: Unified reward management
- **INotificationService**: Notification orchestration
- **IPointService**: Points economy management

## Interface Design Principles

### 1. SOLID Compliance
All interfaces follow SOLID principles:
- **Single Responsibility**: Each interface handles one domain
- **Open/Closed**: Extensible without modification
- **Liskov Substitution**: Implementations are interchangeable
- **Interface Segregation**: Focused, minimal interfaces
- **Dependency Inversion**: Depend on abstractions

### 2. Consistent Return Types
All interfaces now use standardized result types following this pattern:

```python
# Standard response pattern for all services
@dataclass
class StandardResult:
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
```

**Specific Result Types by Domain:**

```python
# User Interaction Results
@dataclass
class ValidationResult:
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)

@dataclass
class InteractionResult:
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)

# Emotional State Results
@dataclass
class EmotionalAnalysisResult:
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)

@dataclass
class EmotionalProfileResult:
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)

# Content Delivery Results
@dataclass
class DeliveryResult:
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)

@dataclass
class QueueOperationResult:
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)

# Narrative Operation Results
@dataclass
class NarrativeOperationResult:
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)

@dataclass
class AnalyticsResult:
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)

@dataclass
class ConfigurationResult:
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
```

### 3. Standardized Error Handling

**Error Information Structure:**
```python
# All result types include structured error information
result = SomeResult(
    success=False,
    data={},
    metadata={"error_context": "validation", "timestamp": "2023-01-01T00:00:00Z"},
    errors=[
        "Validation failed: missing required field 'user_id'",
        "Authorization check failed: insufficient permissions"
    ]
)
```

**Error Handling Patterns:**
```python
# Pattern 1: Check success flag and handle errors
async def handle_service_call(service_method, *args, **kwargs):
    result = await service_method(*args, **kwargs)
    
    if not result.success:
        # Log errors with context
        for error in result.errors:
            logger.error(f"Service error: {error}", extra=result.metadata)
        
        # Return structured error response
        return {
            "success": False,
            "message": "Operation failed",
            "details": result.errors,
            "context": result.metadata
        }
    
    return {
        "success": True,
        "data": result.data,
        "metadata": result.metadata
    }

# Pattern 2: Error aggregation across multiple services  
async def orchestrate_multiple_services(user_id: int):
    all_errors = []
    all_metadata = {}
    combined_data = {}
    
    # Call service 1
    result1 = await service1.some_operation(user_id)
    if result1.success:
        combined_data.update(result1.data)
        all_metadata["service1"] = result1.metadata
    else:
        all_errors.extend([f"Service1: {e}" for e in result1.errors])
    
    # Call service 2 only if service 1 succeeded
    if result1.success:
        result2 = await service2.some_operation(user_id)
        if result2.success:
            combined_data.update(result2.data)
            all_metadata["service2"] = result2.metadata
        else:
            all_errors.extend([f"Service2: {e}" for e in result2.errors])
    
    return NarrativeOperationResult(
        success=len(all_errors) == 0,
        data=combined_data,
        metadata=all_metadata,
        errors=all_errors
    )

# Pattern 3: Graceful degradation
async def robust_content_delivery(user_id: int, content_id: str):
    # Try primary content delivery
    result = await primary_delivery_service.deliver_content(content_id, user_id)
    
    if result.success:
        return result
    
    # Primary failed, try fallback
    fallback_result = await fallback_delivery_service.deliver_basic_content(content_id, user_id)
    
    if fallback_result.success:
        # Add metadata about fallback usage
        fallback_result.metadata["fallback_used"] = True
        fallback_result.metadata["primary_errors"] = result.errors
        return fallback_result
    
    # Both failed, return aggregated error
    return DeliveryResult(
        success=False,
        data={},
        metadata={"primary_attempt": True, "fallback_attempt": True},
        errors=result.errors + fallback_result.errors
    )
```

**Legacy Exception Handling (for backward compatibility):**
```python
# Some legacy methods may still raise exceptions
# Wrap these to convert to result types
async def safe_legacy_call(legacy_service_method, *args, **kwargs):
    try:
        data = await legacy_service_method(*args, **kwargs)
        return SomeResult(
            success=True,
            data={"result": data},
            metadata={"legacy_call": True}
        )
    except ValueError as e:
        return SomeResult(
            success=False,
            data={},
            metadata={"legacy_call": True, "exception_type": "ValueError"},
            errors=[f"Validation error: {str(e)}"]
        )
    except Exception as e:
        return SomeResult(
            success=False,
            data={},
            metadata={"legacy_call": True, "exception_type": type(e).__name__},
            errors=[f"Unexpected error: {str(e)}"]
        )
```

## Interface Usage Examples

### User Narrative Service
```python
from services.interfaces import IUserNarrativeService

async def progress_user_story(narrative_service: IUserNarrativeService, user_id: int, fragment_id: str):
    # Get current state
    user_state = await narrative_service.get_or_create_user_state(user_id)
    
    # Check access
    has_access = await narrative_service.check_user_access(user_id, fragment_id)
    if not has_access:
        raise ValueError("User lacks access to fragment")
    
    # Update progress
    updated_state = await narrative_service.update_current_fragment(user_id, fragment_id)
    await narrative_service.mark_fragment_completed(user_id, fragment_id)
    
    return updated_state
```

### Emotional State Manager
```python
from services.interfaces import IEmotionalStateManager

async def analyze_user_emotion(emotion_manager: IEmotionalStateManager, user_id: int, message_data: dict):
    # Analyze interaction
    emotional_state = await emotion_manager.analyze_interaction_emotion(user_id, message_data)
    
    # Update profile
    profile = await emotion_manager.update_user_emotional_profile(user_id, emotional_state)
    
    # Get content adaptation suggestions
    base_content = {"type": "narrative_fragment", "id": "story_001"}
    adapted_content = await emotion_manager.suggest_content_adaptation(user_id, base_content)
    
    return adapted_content
```

### Content Delivery Service
```python
from services.interfaces import IContentDeliveryService, ContentType, DeliveryPriority
from services.interfaces.content_delivery_interface import ContentContext

async def deliver_personalized_narrative(delivery_service: IContentDeliveryService, user_id: int, fragment_id: str):
    # Prepare context
    context = ContentContext(
        user_id=user_id,
        session_data={"current_chapter": "prologue"},
        emotional_state=None,  # Will be fetched by service
        user_preferences={"language": "es", "difficulty": "medium"},
        interaction_history=[],
        timestamp=datetime.now()
    )
    
    # Prepare content
    content_package = await delivery_service.prepare_content(
        fragment_id, 
        ContentType.NARRATIVE_FRAGMENT, 
        context
    )
    
    # Deliver content
    delivery_options = {"immediate": True, "adaptive": True}
    result = await delivery_service.deliver_content(content_package, delivery_options)
    
    return result
```

### Unified Narrative Orchestrator
```python
from services.interfaces import IUnifiedNarrativeOrchestrator

async def process_complete_narrative_interaction(orchestrator: IUnifiedNarrativeOrchestrator, user_id: int, interaction: dict):
    # Process interaction with full integration - returns NarrativeOperationResult
    result = await orchestrator.process_narrative_interaction(user_id, interaction)
    
    if not result.success:
        return {
            "success": False,
            "errors": result.errors,
            "metadata": result.metadata
        }
    
    # Get comprehensive status - returns NarrativeOperationResult
    user_status = await orchestrator.get_comprehensive_user_status(user_id)
    
    # Get recommendations - returns List[Dict[str, Any]] (legacy method)
    recommendations = await orchestrator.recommend_narrative_path(user_id)
    
    return {
        "success": True,
        "data": {
            "interaction_processed": result.data,
            "user_status": user_status.data if user_status.success else {},
            "recommendations": recommendations
        },
        "metadata": {
            "interaction_metadata": result.metadata,
            "status_metadata": user_status.metadata if user_status.success else {},
            "processing_timestamp": "2023-01-01T00:00:00Z"
        },
        "errors": result.errors + (user_status.errors if not user_status.success else [])
    }
```

## Implementation Guidelines

### 1. Service Registration
```python
# services/container.py
from services.interfaces import IEmotionalStateManager

class ServiceContainer:
    def __init__(self):
        self._services = {}
    
    def register(self, interface: type, implementation: object):
        self._services[interface] = implementation
    
    def get(self, interface: type):
        return self._services.get(interface)

# Usage
container = ServiceContainer()
container.register(IEmotionalStateManager, EmotionalStateManagerImpl())
```

### 2. Dependency Injection
```python
# services/di_setup.py
def setup_narrative_dependencies(container: ServiceContainer, session: AsyncSession):
    # Register core services
    container.register(IUserNarrativeService, UserNarrativeService(session))
    container.register(IEmotionalStateManager, EmotionalStateManager(session))
    container.register(IContentDeliveryService, ContentDeliveryService(session))
    
    # Register orchestrator with dependencies
    orchestrator = UnifiedNarrativeOrchestrator(
        narrative_service=container.get(IUserNarrativeService),
        emotion_manager=container.get(IEmotionalStateManager),
        content_delivery=container.get(IContentDeliveryService)
    )
    container.register(IUnifiedNarrativeOrchestrator, orchestrator)
```

### 3. Testing with Interfaces
```python
# tests/test_narrative_integration.py
import pytest
from unittest.mock import AsyncMock
from services.interfaces import IUserNarrativeService, IEmotionalStateManager

@pytest.fixture
async def mock_narrative_service():
    service = AsyncMock(spec=IUserNarrativeService)
    service.get_or_create_user_state.return_value = UserNarrativeState(user_id=123)
    return service

@pytest.fixture
async def mock_emotion_manager():
    manager = AsyncMock(spec=IEmotionalStateManager)
    manager.analyze_interaction_emotion.return_value = EmotionalState(
        user_id=123, 
        primary_tone=EmotionalTone.POSITIVE,
        intensity=EmotionalIntensity.MEDIUM,
        confidence=0.8
    )
    return manager

async def test_unified_orchestrator(mock_narrative_service, mock_emotion_manager):
    # Test with mocked interfaces
    orchestrator = UnifiedNarrativeOrchestrator(
        narrative_service=mock_narrative_service,
        emotion_manager=mock_emotion_manager
    )
    
    result = await orchestrator.process_narrative_interaction(123, {"type": "message"})
    assert result["success"] is True
```

## Performance Considerations

### 1. Interface Overhead
- Minimal performance impact due to Python's duck typing
- Method resolution is O(1) for direct calls
- Dependency injection adds negligible overhead

### 2. Caching Strategy
```python
# services/implementations/cached_narrative_service.py
from functools import lru_cache
from services.interfaces import IUserNarrativeService

class CachedNarrativeService(IUserNarrativeService):
    def __init__(self, base_service: IUserNarrativeService):
        self.base_service = base_service
    
    @lru_cache(maxsize=1000)
    async def get_or_create_user_state(self, user_id: int):
        return await self.base_service.get_or_create_user_state(user_id)
```

### 3. Async Optimization
- All interface methods are async by design
- Supports concurrent operation execution
- Enables non-blocking I/O for database operations

## Migration Guide

### From Existing Services
1. **Identify Interface Match**: Map existing services to interfaces
2. **Implement Interface**: Create implementation class
3. **Update Dependencies**: Replace direct imports with interface usage
4. **Register in Container**: Add to dependency injection system

### Example Migration
```python
# Before: Direct service usage
from services.user_narrative_service import UserNarrativeService

class NarrativeHandler:
    def __init__(self, session):
        self.narrative_service = UserNarrativeService(session)

# After: Interface-based usage
from services.interfaces import IUserNarrativeService

class NarrativeHandler:
    def __init__(self, narrative_service: IUserNarrativeService):
        self.narrative_service = narrative_service
```

## Error Handling Patterns

### 1. Graceful Degradation
```python
async def robust_narrative_processing(orchestrator: IUnifiedNarrativeOrchestrator, user_id: int):
    try:
        return await orchestrator.process_narrative_interaction(user_id, data)
    except ValidationError as e:
        logger.warning(f"Validation failed for user {user_id}: {e}")
        return {"success": False, "error": "invalid_input"}
    except ProcessingError as e:
        logger.error(f"Processing failed for user {user_id}: {e}")
        return {"success": False, "error": "processing_failed"}
```

### 2. Circuit Breaker Pattern
```python
class CircuitBreakerWrapper:
    def __init__(self, service, failure_threshold=5, timeout=60):
        self.service = service
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
```

## Monitoring and Observability

### 1. Interface Metrics
```python
# services/monitoring/interface_metrics.py
from functools import wraps
import time
import logging

def monitor_interface_calls(interface_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"{interface_name}.{func.__name__} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{interface_name}.{func.__name__} failed in {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator
```

### 2. Health Checks
```python
# services/health/interface_health.py
async def check_interface_health(service_container: ServiceContainer) -> Dict[str, bool]:
    health_status = {}
    
    for interface_type in [IUserNarrativeService, IEmotionalStateManager, IContentDeliveryService]:
        try:
            service = service_container.get(interface_type)
            # Perform basic health check
            await service.health_check() if hasattr(service, 'health_check') else True
            health_status[interface_type.__name__] = True
        except Exception as e:
            logger.error(f"Health check failed for {interface_type.__name__}: {e}")
            health_status[interface_type.__name__] = False
    
    return health_status
```

## Best Practices

### 1. Interface Design
- Keep interfaces focused and cohesive
- Use descriptive method names
- Include comprehensive docstrings
- Define clear parameter and return types
- Handle edge cases gracefully

### 2. Implementation
- Implement all interface methods
- Follow consistent error handling patterns
- Use dependency injection for testability
- Add logging for observability
- Validate inputs thoroughly

### 3. Testing
- Mock interfaces for unit tests
- Test interface contracts
- Use integration tests for cross-interface interactions
- Verify error handling behavior
- Test performance under load

### 4. Documentation
- Document interface purpose and scope
- Provide usage examples
- Explain error conditions
- Include performance characteristics
- Maintain changelog for interface modifications

## Future Enhancements

### 1. Interface Versioning
```python
from services.interfaces.v2 import IUserNarrativeService as IUserNarrativeServiceV2

class VersionedServiceContainer:
    def register_versioned(self, interface_type, version: str, implementation):
        key = f"{interface_type.__name__}_v{version}"
        self._services[key] = implementation
```

### 2. Async Context Managers
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def narrative_transaction(orchestrator: IUnifiedNarrativeOrchestrator):
    transaction = await orchestrator.begin_transaction()
    try:
        yield transaction
        await transaction.commit()
    except Exception:
        await transaction.rollback()
        raise
```

### 3. Event-Driven Integration
```python
class EventDrivenInterface:
    def __init__(self, base_service, event_bus):
        self.base_service = base_service
        self.event_bus = event_bus
    
    async def process_with_events(self, *args, **kwargs):
        await self.event_bus.publish("operation_started", {"args": args, "kwargs": kwargs})
        result = await self.base_service.process(*args, **kwargs)
        await self.event_bus.publish("operation_completed", {"result": result})
        return result
```