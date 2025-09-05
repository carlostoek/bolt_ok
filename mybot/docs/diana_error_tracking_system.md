# Diana Menu Error Tracking System

A comprehensive error tracking, correlation analysis, and performance monitoring system specifically designed for the Diana menu system. This system provides complete visibility into all menu-related errors with detailed context for debugging and resolution.

## Overview

The Diana Menu Error Tracking System consists of several integrated components:

1. **Centralized Error Tracker** - Collects and categorizes all errors
2. **Correlation Analyzer** - Identifies patterns and relationships between errors
3. **Performance Monitor** - Tracks response times and performance metrics
4. **Error Dashboard** - Provides reporting and analytics
5. **Instrumentation System** - Decorators and context managers for tracking

## Key Features

### Error Categorization
- **BaseModel Errors**: Data validation and serialization issues
- **Database Errors**: Connection, query, and transaction problems
- **Service Errors**: Dependency injection and service failures
- **Menu Navigation**: UI and state management issues
- **Callback Processing**: Asynchronous processing errors
- **Character Validation**: Diana consistency issues
- **Performance**: Timeout and resource problems
- **Telegram API**: External API communication failures

### Error Correlation Analysis
- **Temporal Correlation**: Errors occurring close in time
- **Causal Relationships**: One error leading to another
- **User-Based Patterns**: Errors affecting specific users
- **Operation-Based Patterns**: Errors in related operations
- **Pattern Clustering**: Similar error signatures

### Performance Monitoring
- Response time tracking for all menu operations
- Performance threshold violations
- P95/P99 latency percentiles
- Success/error rate monitoring
- Resource utilization tracking

## Quick Start

### 1. Basic Error Tracking

```python
from services.diana_menu_error_tracker import get_error_tracker, ErrorContext

# Get the global error tracker
tracker = get_error_tracker()

# Track an error manually
try:
    # Your menu operation
    result = await process_diana_menu(user_id, menu_type)
except Exception as e:
    context = ErrorContext(
        user_id=user_id,
        menu_type=menu_type,
        operation="process_diana_menu"
    )
    await tracker.track_error(e, context)
    raise
```

### 2. Using Decorators

```python
from services.diana_menu_instrumentation import track_menu_operation

class DianaMenuHandler:
    @track_menu_operation(operation_name="admin_menu", menu_type="admin")
    async def handle_admin_menu(self, callback_query):
        # Your menu logic here
        return await self.process_admin_request(callback_query)
    
    @track_menu_operation(menu_type="user")  # Uses function name as operation
    async def handle_user_menu(self, message):
        # User menu logic
        return await self.show_user_options(message)
```

### 3. Context Manager Usage

```python
from services.diana_menu_instrumentation import get_diana_instrumentation

instrumentation = get_diana_instrumentation()

async def complex_menu_operation(user_id, operation_data):
    async with instrumentation.operation_context(
        "complex_operation",
        user_id=user_id,
        menu_type="vip",
        correlation_id=f"op_{user_id}_{int(time.time())}"
    ) as context:
        # Your complex operation here
        step1_result = await validate_user_permissions(user_id)
        step2_result = await process_vip_request(operation_data)
        return combine_results(step1_result, step2_result)
```

### 4. Dashboard and Reporting

```python
from services.diana_error_dashboard import get_error_dashboard

dashboard = get_error_dashboard()

# Get current system metrics
metrics = await dashboard.get_dashboard_metrics(hours=24)
print(f"System Health: {metrics.system_health_score:.1f}%")
print(f"Total Errors: {metrics.total_errors}")
print(f"Error Rate: {metrics.error_rate_per_hour:.1f}/hour")

# Check for active alerts
alerts = await dashboard.check_alerts()
for alert in alerts:
    print(f"ALERT: {alert['message']}")

# Generate error report
report = dashboard.generate_report(dashboard.ReportType.SUMMARY, hours=24)
print(report)
```

## Advanced Usage

### Custom Error Categories

```python
from services.diana_menu_error_tracker import ErrorCategory, ErrorContext

# Add custom categorization rules
tracker = get_error_tracker()
tracker.categorization_rules[r"custom.*pattern"] = ErrorCategory.SERVICE

# Track with custom tags
context = ErrorContext(
    user_id=123,
    operation="custom_operation",
    request_params={"param1": "value1"}
)
await tracker.track_error(exception, context, tags={"custom", "important"})
```

### Performance Thresholds

```python
# Set custom performance thresholds
tracker.performance_thresholds.update({
    'vip_menu_response': 0.8,  # 800ms for VIP menus
    'admin_menu_response': 1.5,  # 1.5s for admin menus
    'character_validation': 0.3   # 300ms for validation
})
```

### Correlation Analysis

```python
from services.diana_error_correlation_analyzer import DianaErrorCorrelationAnalyzer

analyzer = DianaErrorCorrelationAnalyzer()

# Analyze error correlations
correlations = await analyzer.analyze_correlations(hours=24)

# Get detailed correlation report
report = analyzer.get_correlation_report(hours=24)
print(f"Found {report['total_correlations']} correlations")
print(f"High strength: {report['high_strength_correlations']}")

# Cluster similar errors
clusters = await analyzer.cluster_errors(hours=24)
for cluster in clusters:
    print(f"Cluster {cluster.cluster_id}: {cluster.cluster_size} errors")
```

## Integration with Existing Code

### Method 1: Decorator Integration

Replace existing methods with decorated versions:

```python
# Before
class EnhancedDianaMenuSystem:
    async def process_admin_menu(self, callback_query):
        # existing logic
        pass

# After  
from services.diana_menu_instrumentation import track_menu_operation

class EnhancedDianaMenuSystem:
    @track_menu_operation(operation_name="admin_menu", menu_type="admin")
    async def process_admin_menu(self, callback_query):
        # existing logic - no changes needed
        pass
```

### Method 2: Wrapper Classes

```python
from services.diana_menu_instrumentation import get_diana_instrumentation

class InstrumentedDianaMenuSystem:
    def __init__(self, original_system):
        self.original = original_system
        self.instrumentation = get_diana_instrumentation()
    
    async def process_admin_menu(self, callback_query):
        async with self.instrumentation.operation_context(
            "admin_menu", 
            user_id=callback_query.from_user.id,
            menu_type="admin"
        ):
            return await self.original.process_admin_menu(callback_query)
```

### Method 3: Manual Instrumentation

```python
# In existing methods, add manual tracking
async def existing_menu_method(self, callback_query):
    from services.diana_menu_error_tracker import get_error_tracker, ErrorContext
    
    tracker = get_error_tracker()
    start_time = time.time()
    
    try:
        # Existing logic
        result = await self.process_request(callback_query)
        
        # Track successful operation
        duration = time.time() - start_time
        context = ErrorContext(
            user_id=callback_query.from_user.id,
            operation="existing_menu_method"
        )
        tracker.track_performance("existing_menu_method", duration, context)
        
        return result
        
    except Exception as e:
        # Track error
        context = ErrorContext(
            user_id=callback_query.from_user.id,
            operation="existing_menu_method",
            callback_data=callback_query.data
        )
        await tracker.track_error(e, context)
        raise
```

## Monitoring and Alerting

### Alert Configuration

```python
dashboard = get_error_dashboard()

# Configure alert thresholds
dashboard.alert_thresholds.update({
    'error_rate_per_hour': 25,        # 25 errors per hour
    'critical_errors_per_hour': 2,    # 2 critical errors per hour
    'performance_violations_per_hour': 10,  # 10 slow operations per hour
    'system_health_score': 90.0       # Health score below 90%
})

# Check alerts periodically
alerts = await dashboard.check_alerts()
if alerts:
    # Send notifications to administrators
    await send_admin_notifications(alerts)
```

### Periodic Monitoring

```python
import asyncio

async def monitor_diana_errors():
    dashboard = get_error_dashboard()
    
    while True:
        try:
            # Check every 5 minutes
            await asyncio.sleep(300)
            
            # Get current metrics
            metrics = await dashboard.get_dashboard_metrics(1)
            
            # Log system status
            logger.info(f"Diana Menu Health: {metrics.system_health_score:.1f}%")
            
            # Check for alerts
            alerts = await dashboard.check_alerts()
            for alert in alerts:
                logger.warning(f"Diana Alert: {alert['message']}")
                
        except Exception as e:
            logger.error(f"Monitoring error: {e}")

# Start monitoring task
asyncio.create_task(monitor_diana_errors())
```

## Error Resolution Workflow

### 1. Error Detection
- Automatic error tracking captures all exceptions
- Real-time alerts notify of critical issues
- Dashboard provides immediate visibility

### 2. Error Analysis
- Use correlation analysis to identify patterns
- Check root cause analysis for specific errors
- Review performance metrics for context

### 3. Error Resolution
- Apply suggested actions from the system
- Test fixes with error tracking enabled
- Mark errors as resolved with notes

```python
# After fixing an error
tracker = get_error_tracker()
tracker.resolve_error(
    error_id="err_1234567890",
    resolution_notes="Fixed BaseModel initialization by adding default values"
)
```

## Common Error Patterns and Solutions

### BaseModel Initialization Errors

**Pattern**: `BaseModel.__init__() takes 1 positional argument but X were given`

**Solution**:
```python
# Use keyword arguments for BaseModel initialization
@track_basemodel_init("MenuResponse")
def create_menu_response(**kwargs):
    return MenuResponse(**kwargs)  # Use **kwargs, not positional args
```

### Database Connection Errors

**Pattern**: `Cannot operate on a closed database`

**Solution**:
```python
@track_database_query("users")
async def get_user_data(session, user_id):
    # Ensure session is active
    if session.is_closed:
        logger.warning("Session closed, creating new session")
        # Handle session recreation
    
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

### Character Validation Failures

**Pattern**: Character consistency score below threshold

**Solution**:
```python
@track_menu_operation(menu_type="character_validation")
async def validate_diana_response(self, text):
    # Add fallback for validation failures
    try:
        score = await self.character_validator.validate_response(text)
        if score < 0.95:
            # Use pre-validated fallback response
            return self.get_fallback_response()
        return text
    except Exception as e:
        logger.warning(f"Character validation failed: {e}")
        return self.get_fallback_response()
```

## Performance Optimization

### Caching Strategies

```python
from functools import lru_cache

class OptimizedDianaMenu:
    @track_menu_operation(operation_name="get_menu_template")
    @lru_cache(maxsize=100)
    def get_menu_template(self, menu_type, user_role):
        # Cache menu templates to improve performance
        return self._generate_template(menu_type, user_role)
```

### Async Optimization

```python
@track_menu_operation(operation_name="parallel_menu_processing")
async def process_menu_with_parallel_tasks(self, callback_query):
    # Process independent tasks in parallel
    tasks = [
        self.validate_user_permissions(callback_query.from_user.id),
        self.load_user_preferences(callback_query.from_user.id),
        self.get_menu_template(callback_query.data)
    ]
    
    permissions, preferences, template = await asyncio.gather(*tasks)
    return self.build_menu_response(permissions, preferences, template)
```

## Best Practices

### 1. Error Context
Always provide rich context when tracking errors:

```python
context = ErrorContext(
    user_id=user_id,
    menu_type=menu_type,
    operation=operation_name,
    callback_data=callback_data,
    request_params={"param1": value1, "param2": value2},
    system_state={"cache_status": "hit", "db_pool": "healthy"}
)
```

### 2. Correlation IDs
Use correlation IDs to track related operations:

```python
correlation_id = f"menu_{user_id}_{int(time.time())}"

async with instrumentation.operation_context(
    "complex_menu_flow",
    correlation_id=correlation_id
) as context:
    # All errors in this flow will share the correlation ID
    await step1()
    await step2()
    await step3()
```

### 3. Performance Monitoring
Set appropriate performance thresholds:

```python
# Different thresholds for different operations
thresholds = {
    'simple_menu': 0.5,     # 500ms for simple menus
    'complex_menu': 2.0,    # 2s for complex menus
    'admin_operation': 5.0,  # 5s for admin operations
    'database_query': 1.0    # 1s for database queries
}
```

### 4. Error Recovery
Implement graceful error recovery:

```python
@track_menu_operation(operation_name="resilient_menu")
async def resilient_menu_operation(self, callback_query):
    try:
        return await self.primary_menu_logic(callback_query)
    except DatabaseError:
        # Fallback to cached data
        return await self.cached_menu_fallback(callback_query)
    except ValidationError:
        # Return error-safe default menu
        return await self.default_menu_response(callback_query)
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**: Adjust error history limits
2. **Performance Impact**: Use sampling for high-frequency operations
3. **False Alerts**: Tune alert thresholds based on normal operation patterns
4. **Missing Correlations**: Ensure correlation IDs are properly set

### Debug Mode

```python
from services.diana_menu_error_tracker import get_error_tracker

tracker = get_error_tracker()

# Enable detailed logging
import logging
logging.getLogger('services.diana_menu_error_tracker').setLevel(logging.DEBUG)
logging.getLogger('services.diana_error_correlation_analyzer').setLevel(logging.DEBUG)

# Export error data for analysis
error_data = tracker.export_errors(hours=24, format='json')
with open('diana_errors_debug.json', 'w') as f:
    f.write(error_data)
```

## API Reference

### DianaMenuErrorTracker
- `track_error(exception, context, performance, correlation_id, tags)`
- `track_performance(operation, duration, context, metrics)`
- `get_error_summary(hours)`
- `get_error_details(error_id)`
- `resolve_error(error_id, resolution_notes)`

### DianaErrorDashboard
- `get_dashboard_metrics(hours)`
- `get_error_trends(hours, interval_hours)`
- `get_performance_report(hours)`
- `get_correlation_insights(hours)`
- `check_alerts()`
- `generate_report(report_type, hours)`

### DianaMenuInstrumentation
- `@track_menu_operation(operation_name, menu_type, track_performance)`
- `@track_basemodel_init(model_name)`
- `@track_database_query(table_name)`
- `operation_context(operation_name, user_id, menu_type, callback_data)`

This comprehensive error tracking system provides complete visibility into the Diana menu system's health and performance, enabling proactive issue resolution and system optimization.