# Repository Pattern Implementation for DianaBot

## Overview

This repository pattern implementation provides a comprehensive data access abstraction layer for the DianaBot narrative system. It enables flexibility, testability, and performance optimization while maintaining clean separation of concerns.

## Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Services      │────│  Repositories   │────│    Database     │
│   (Business     │    │  (Data Access   │    │   (SQLAlchemy   │
│    Logic)       │    │   Abstraction)  │    │    Models)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Caching       │
                       │   Layer         │
                       └─────────────────┘
```

### Domain Aggregates

The system is organized around the following domain aggregates:

1. **User Aggregate** - User management, profiles, statistics, badges
2. **Point Aggregate** - Point transactions, balances, leaderboards  
3. **Mission Aggregate** - Missions, user progress, completion tracking
4. **Narrative Aggregate** - Story fragments, user progress, lore pieces
5. **Achievement Aggregate** - Achievements, badges, user awards
6. **Channel Aggregate** - Channel configuration, requests, permissions
7. **Auction Aggregate** - Auction system, bids, participants
8. **Game Aggregate** - Trivia, minigames, challenges, events
9. **Config Aggregate** - System configuration, feature flags, tokens

## Key Features

### 🚀 Performance Optimization

- **Query Caching**: Intelligent caching with TTL and pattern-based invalidation
- **Query Profiling**: Automatic performance monitoring and bottleneck identification
- **Index Recommendations**: AI-powered index suggestions based on usage patterns
- **Bulk Operations**: Optimized batch operations for high-throughput scenarios

### 🔄 Flexibility

- **Multiple Cache Backends**: Memory, Redis, or custom backends
- **Swappable Implementations**: Easy to switch between different data sources
- **Adapter Pattern**: Seamless integration with existing services
- **Migration Support**: Gradual migration from legacy code

### 🧪 Testability

- **Interface-Based Design**: Easy mocking and unit testing
- **Test Fixtures**: Comprehensive test utilities and sample data
- **Integration Tests**: Full end-to-end testing scenarios
- **Performance Benchmarks**: Automated performance regression testing

### 📊 Monitoring & Analytics

- **Health Checks**: System-wide health monitoring
- **Performance Metrics**: Detailed performance analytics
- **Usage Patterns**: Query pattern analysis and optimization suggestions
- **Cache Statistics**: Hit rates, utilization, and performance metrics

## Usage Examples

### Basic Repository Usage

```python
from repositories.implementations.user_repository import SqlUserRepository
from repositories.caching import create_memory_cache

# Create repository with caching
cache_layer = create_memory_cache(max_size=10000, default_ttl=300)
user_repo = SqlUserRepository(session)
user_repo._cache_layer = cache_layer

# Basic operations
user = await user_repo.get_by_id(123)
top_users = await user_repo.get_top_by_points(limit=10)
admin_users = await user_repo.get_admins()
```

### Service Integration

```python
from services.repository_service_adapter import create_repository_adapter

# Create adapter with Redis caching
cache_config = {
    'type': 'redis',
    'redis_url': 'redis://localhost:6379',
    'key_prefix': 'bot_cache',
    'default_ttl': 600
}

adapter = create_repository_adapter(session, cache_config)

# Use in service
class UserService:
    def __init__(self, repository_adapter):
        self.user_repo = repository_adapter.get_user_repository()
        self.point_repo = repository_adapter.get_point_repository()
    
    async def get_user_profile(self, user_id: int):
        user = await self.user_repo.get_by_id(user_id)
        balance = await self.point_repo.get_user_balance(user_id)
        rank = await self.user_repo.get_user_rank_by_points(user_id)
        
        return {
            'user': user,
            'balance': balance,
            'rank': rank
        }
```

### Caching Strategies

```python
from repositories.caching import cache_result, invalidate_cache_pattern

class UserRepository:
    @cache_result(ttl=300, key_prefix="user_profile")
    async def get_user_profile(self, user_id: int):
        # Expensive operation cached for 5 minutes
        return await self._build_user_profile(user_id)
    
    @invalidate_cache_pattern("user_profile:{user_id}")
    async def update_user(self, user_id: int, updates: dict):
        # Automatically invalidates cached profile when user is updated
        return await self._update_user_data(user_id, updates)
```

### Query Optimization

```python
from repositories.query_optimization import (
    query_optimizer, 
    index_recommender, 
    query_profiler
)

# Record query patterns for analysis
index_recommender.record_query_pattern(
    table="users",
    columns=["username", "email"],
    query_type="SELECT",
    frequency=100
)

# Get optimization recommendations
recommendations = index_recommender.get_index_recommendations(min_frequency=10)
performance_report = query_profiler.get_performance_report()
```

## Configuration

### Cache Configuration

```python
# Memory Cache
cache_config = {
    'type': 'memory',
    'max_size': 10000,
    'default_ttl': 300
}

# Redis Cache
cache_config = {
    'type': 'redis',
    'redis_url': 'redis://localhost:6379',
    'key_prefix': 'bot_cache',
    'default_ttl': 600
}

# Disabled Cache
cache_config = {
    'type': 'disabled'
}
```

### Performance Monitoring

```python
# Get system health
health = await repository_adapter.get_system_health()

# Get performance metrics
metrics = await repository_adapter.get_performance_metrics()

# Optimize system
optimization_results = await repository_adapter.optimize_system(
    auto_create_indexes=False  # Set to True to automatically create recommended indexes
)
```

## Testing

### Unit Tests

```python
import pytest
from repositories.implementations.user_repository import SqlUserRepository

@pytest.mark.asyncio
async def test_user_repository_get_by_id(session, sample_users):
    repo = SqlUserRepository(session)
    user = await repo.get_by_id(1)
    
    assert user is not None
    assert user.username == "test_user"
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_cross_repository_workflow(repositories):
    user_repo = repositories['user']
    point_repo = repositories['point']
    
    # Create user
    user = await user_repo.create({'id': 123, 'username': 'test'})
    
    # Award points
    transaction = await point_repo.add_points(123, 100.0, 'test', 'Test points')
    
    # Verify integration
    balance = await point_repo.get_user_balance(123)
    assert balance == 100.0
```

### Performance Tests

```python
@pytest.mark.asyncio
async def test_repository_performance(user_repository):
    import time
    
    # Test bulk operations
    start_time = time.time()
    
    for i in range(100):
        await user_repository.get_by_id(1)  # Should hit cache after first call
    
    execution_time = time.time() - start_time
    assert execution_time < 1.0  # Should complete in under 1 second with caching
```

## Migration Guide

### From Legacy Services

1. **Gradual Migration**: Use `LegacyServiceMigrationHelper` to gradually migrate existing services
2. **Adapter Pattern**: Wrap existing services with repository adapters
3. **Feature Flags**: Use configuration to toggle between legacy and repository implementations
4. **Testing**: Ensure comprehensive testing during migration

```python
from services.repository_service_adapter import LegacyServiceMigrationHelper

# Migrate existing service
migration_helper = LegacyServiceMigrationHelper(session, repository_adapter)
await migration_helper.migrate_user_operations(legacy_user_service)
await migration_helper.migrate_point_operations(legacy_point_service)

# Check migration log
migration_log = migration_helper.get_migration_log()
```

## Best Practices

### Repository Design

1. **Single Responsibility**: Each repository handles one aggregate
2. **Interface Segregation**: Keep interfaces focused and cohesive
3. **Dependency Injection**: Use constructor injection for dependencies
4. **Error Handling**: Graceful handling of database and cache errors

### Caching Strategy

1. **Cache Hot Data**: Cache frequently accessed, slowly changing data
2. **TTL Strategy**: Set appropriate TTL based on data volatility
3. **Cache Invalidation**: Implement proper invalidation patterns
4. **Monitoring**: Monitor cache hit rates and performance

### Performance Optimization

1. **Query Analysis**: Regularly analyze slow queries
2. **Index Management**: Create indexes based on usage patterns
3. **Batch Operations**: Use bulk operations for high-volume scenarios
4. **Connection Pooling**: Optimize database connection management

### Monitoring

1. **Health Checks**: Implement comprehensive health monitoring
2. **Metrics Collection**: Track performance and usage metrics
3. **Alerting**: Set up alerts for performance degradation
4. **Capacity Planning**: Monitor growth and plan for scaling

## API Reference

### Core Interfaces

- `IUserRepository`: User aggregate operations
- `IPointRepository`: Point transaction operations
- `IMissionRepository`: Mission and progress operations
- `INarrativeRepository`: Story and narrative operations
- `IAchievementRepository`: Achievement and badge operations
- `IChannelRepository`: Channel management operations
- `IAuctionRepository`: Auction system operations
- `IGameRepository`: Game and trivia operations
- `IConfigRepository`: Configuration management operations

### Implementation Classes

- `SqlUserRepository`: SQLAlchemy implementation of user repository
- `SqlPointRepository`: SQLAlchemy implementation of point repository
- `SqlMissionRepository`: SQLAlchemy implementation of mission repository
- `SqlNarrativeRepository`: SQLAlchemy implementation of narrative repository

### Caching Components

- `CacheLayer`: Main caching abstraction
- `MemoryCacheBackend`: In-memory cache implementation
- `RedisCacheBackend`: Redis cache implementation
- `CacheableMixin`: Mixin for adding caching to repositories

### Optimization Tools

- `QueryOptimizer`: Query result caching and optimization
- `IndexRecommendation`: Database index recommendations
- `QueryProfiler`: Query performance profiling and analysis

## Troubleshooting

### Common Issues

1. **Cache Misses**: Check cache configuration and TTL settings
2. **Slow Queries**: Use query profiler to identify bottlenecks
3. **Memory Usage**: Monitor cache size and implement eviction policies
4. **Connection Issues**: Check database and Redis connection settings

### Debugging

```python
# Enable debug logging
import logging
logging.getLogger('repositories').setLevel(logging.DEBUG)

# Check cache health
health = await repo.cache_health_check()
print(f"Cache health: {health}")

# Get performance metrics
metrics = await repository_adapter.get_performance_metrics()
print(f"Performance metrics: {metrics}")

# Profile specific operations
import time
start = time.time()
result = await repo.some_operation()
execution_time = time.time() - start
print(f"Operation took {execution_time:.3f} seconds")
```

### Performance Tuning

1. **Cache Hit Rate**: Aim for >80% hit rate on frequently accessed data
2. **Query Response Time**: Target <100ms for cached queries, <500ms for uncached
3. **Memory Usage**: Monitor cache memory usage and tune max_size accordingly
4. **Database Connections**: Monitor connection pool utilization

## Contributing

When contributing to the repository pattern:

1. **Follow Interfaces**: Implement all interface methods completely
2. **Add Tests**: Include comprehensive unit and integration tests
3. **Document Changes**: Update documentation for any API changes
4. **Performance Testing**: Include performance benchmarks for new features
5. **Backward Compatibility**: Maintain backward compatibility where possible

## License

This implementation follows the same license as the main DianaBot project.