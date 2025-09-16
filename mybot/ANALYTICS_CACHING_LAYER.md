# Analytics Data Caching Layer Implementation

## Overview

This document describes the implementation of the analytics data caching layer for the narrative module (Task 28). The caching layer is designed to improve performance by reducing database queries for frequently accessed analytics data.

## Implementation Details

### 1. Cache Service (`services/cache_service.py`)

The cache service provides a flexible caching solution that can work with both in-memory storage and Redis (when available).

#### Features:
- **Dual Backend Support**: Works with in-memory cache by default, with optional Redis support
- **Automatic Fallback**: Falls back to in-memory cache if Redis is not available
- **TTL Management**: Automatic expiration of cached entries
- **Prefix-based Organization**: Cache keys are organized by prefixes for easy management
- **Statistics Tracking**: Provides cache usage statistics

#### Methods:
- `get(prefix, key)`: Retrieve a value from cache
- `set(prefix, key, value, ttl)`: Store a value in cache
- `delete(prefix, key)`: Remove a value from cache
- `clear_prefix(prefix)`: Clear all entries with a specific prefix
- `clear_all()`: Clear all cache entries
- `get_stats()`: Get cache statistics

### 2. Cached Analytics Service (`services/cached_analytics_service.py`)

This service wraps the existing `AnalyticsService` and adds caching functionality to its methods.

#### Cached Methods:
- `get_fragment_engagement_metrics(fragment_key)`: 5-minute cache
- `analyze_choice_distribution_patterns()`: 10-minute cache
- `identify_narrative_bottlenecks()`: 10-minute cache
- `generate_user_segment_analysis()`: 15-minute cache
- `track_conversion_funnel_metrics()`: 15-minute cache
- `get_character_voice_analytics()`: 10-minute cache
- `get_comprehensive_dashboard_data()`: 5-minute cache

#### Cache Invalidation:
- `invalidate_fragment_cache(fragment_key)`: Invalidate cache for a specific fragment
- `invalidate_all_analytics_cache()`: Invalidate all analytics cache entries

### 3. Integration with Analytics Handlers (`handlers/admin/analytics_handlers.py`)

All analytics handlers have been updated to use the `CachedAnalyticsService` instead of the direct `AnalyticsService`. This provides transparent caching for all analytics operations.

Additional features added to the UI:
- Cache backend information displayed in the main analytics menu
- Cache statistics shown in the dashboard

### 4. Dependencies

The implementation adds Redis as an optional dependency in `requirements.txt`:
```
redis>=5.0.1
```

The cache service will automatically detect if Redis is available and use it. If not, it falls back to in-memory caching.

## Cache Strategy

### TTL (Time To Live) Settings:
- **Fragment metrics**: 5 minutes (300 seconds)
- **Choice patterns**: 10 minutes (600 seconds)
- **Bottlenecks**: 10 minutes (600 seconds)
- **User segments**: 15 minutes (900 seconds)
- **Conversion funnel**: 15 minutes (900 seconds)
- **Character voice**: 10 minutes (600 seconds)
- **Dashboard data**: 5 minutes (300 seconds)

### Cache Keys:
- Fragment metrics: `fragment_metrics:fragment_{fragment_key}`
- Choice patterns: `choice_patterns:global`
- Bottlenecks: `bottlenecks:global`
- User segments: `user_segments:global`
- Conversion funnel: `conversion_funnel:global`
- Character voice: `character_voice:global`
- Dashboard data: `dashboard:global`

## Performance Benefits

1. **Reduced Database Load**: Frequently accessed analytics data is served from cache
2. **Faster Response Times**: Cached data retrieval is significantly faster than database queries
3. **Scalability**: Redis backend allows for distributed caching in multi-instance deployments
4. **Graceful Degradation**: Falls back to database queries if cache is unavailable

## Usage Examples

### Using the Cache Service Directly:
```python
from services.cache_service import CacheService

# Create cache service (will use Redis if available)
cache_service = CacheService()

# Store data in cache
await cache_service.set("fragment_metrics", "fragment_123", fragment_data, ttl=300)

# Retrieve data from cache
cached_data = await cache_service.get("fragment_metrics", "fragment_123")
```

### Using the Cached Analytics Service:
```python
from services.cached_analytics_service import CachedAnalyticsService
from services.cache_service import CacheService

# Create services
cache_service = CacheService()
cached_analytics = CachedAnalyticsService(session, cache_service)

# Get cached fragment metrics (automatically cached)
metrics = await cached_analytics.get_fragment_engagement_metrics("fragment_123")

# Invalidate cache when data changes
await cached_analytics.invalidate_fragment_cache("fragment_123")
```

## Future Improvements

1. **Cache Warming**: Pre-populate cache with frequently accessed data
2. **Cache Invalidation Events**: Automatically invalidate cache when underlying data changes
3. **Advanced Redis Features**: Use Redis pub/sub for distributed cache invalidation
4. **Compression**: Compress large cached data to save memory
5. **Cache Monitoring**: Add detailed cache hit/miss statistics