"""
Narrative Performance Optimization Service

Provides comprehensive performance optimization and caching for narrative operations
to ensure <500ms response times while maintaining system reliability and scalability.

Key Features:
- Multi-level caching (memory, Redis, database)
- Database query optimization with connection pooling
- Async operation batching and parallel processing
- Performance monitoring and alerting
- Adaptive caching strategies based on usage patterns
- Circuit breaker patterns for reliability
- Request coalescing to prevent duplicate operations
"""

import logging
import asyncio
import time
import json
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import hashlib
import weakref
from functools import wraps

# Note: Redis and other caching libraries would be imported in a real implementation
# For now, we'll use in-memory alternatives

logger = logging.getLogger(__name__)

class CacheLevel(Enum):
    """Cache levels for different data types."""
    MEMORY = "memory"           # Fast, volatile, small capacity
    DISTRIBUTED = "distributed" # Redis/Memcached, persistent, large capacity  
    DATABASE = "database"       # Slowest, permanent, unlimited capacity

class PerformanceMetric(Enum):
    """Performance metrics to track."""
    RESPONSE_TIME = "response_time"
    CACHE_HIT_RATE = "cache_hit_rate"
    QUERY_COUNT = "query_count"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"

@dataclass
class CacheConfig:
    """Configuration for cache management."""
    memory_ttl: int = 300           # 5 minutes
    distributed_ttl: int = 3600     # 1 hour
    database_ttl: int = 86400       # 24 hours
    max_memory_size: int = 1000     # Maximum items in memory cache
    enable_compression: bool = False # Enable compression for large objects
    cache_warming_enabled: bool = True # Pre-load frequently accessed data

@dataclass
class PerformanceBudget:
    """Performance budget for operations."""
    max_response_time_ms: int = 500
    max_database_queries: int = 5
    max_cache_misses: int = 2
    warning_threshold_ms: int = 300

@dataclass
class PerformanceResult:
    """Result of performance tracking."""
    operation_name: str
    duration_ms: int
    cache_hits: int
    cache_misses: int
    database_queries: int
    warnings: List[str] = field(default_factory=list)
    exceeded_budget: bool = False

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open" # Testing if service recovered

@dataclass
class CircuitBreaker:
    """Circuit breaker for service reliability."""
    name: str
    failure_threshold: int = 5
    recovery_timeout: int = 60
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    successful_calls: int = 0

class NarrativePerformanceOptimizationService:
    """
    Service for optimizing narrative operations performance.
    Provides caching, query optimization, and performance monitoring.
    """
    
    def __init__(self, cache_config: CacheConfig = None, performance_budget: PerformanceBudget = None):
        self.cache_config = cache_config or CacheConfig()
        self.performance_budget = performance_budget or PerformanceBudget()
        
        # Multi-level cache system
        self.memory_cache = {}
        self.cache_access_times = {}
        self.cache_hit_counts = defaultdict(int)
        
        # Performance tracking
        self.performance_metrics = {
            metric: deque(maxlen=1000) for metric in PerformanceMetric
        }
        self.active_operations = {}
        
        # Circuit breakers for external services
        self.circuit_breakers = {
            'database': CircuitBreaker('database'),
            'character_validator': CircuitBreaker('character_validator'),
            'vip_service': CircuitBreaker('vip_service')
        }
        
        # Request coalescing
        self.pending_requests = {}
        self.request_locks = defaultdict(asyncio.Lock)
        
        # Query optimization
        self.query_cache = {}
        self.prepared_statements = {}
        
        # Background tasks
        self._cleanup_task = None
        self._metrics_task = None
        self._start_background_tasks()
    
    def performance_tracked(self, operation_name: str, budget: PerformanceBudget = None):
        """Decorator for tracking operation performance."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await self.track_operation_performance(
                    operation_name, func, budget or self.performance_budget, *args, **kwargs
                )
            return wrapper
        return decorator
    
    async def track_operation_performance(
        self, 
        operation_name: str, 
        func: Callable, 
        budget: PerformanceBudget,
        *args, **kwargs
    ) -> Tuple[Any, PerformanceResult]:
        """Track performance of an operation against budget."""
        start_time = time.time()
        operation_id = f"{operation_name}_{id(args)}_{time.time()}"
        
        # Initialize tracking
        self.active_operations[operation_id] = {
            'start_time': start_time,
            'cache_hits': 0,
            'cache_misses': 0,
            'database_queries': 0,
            'warnings': []
        }
        
        try:
            # Execute operation
            result = await func(*args, **kwargs)
            
            # Calculate metrics
            duration_ms = int((time.time() - start_time) * 1000)
            operation_data = self.active_operations.get(operation_id, {})
            
            # Check budget compliance
            warnings = []
            exceeded_budget = False
            
            if duration_ms > budget.max_response_time_ms:
                warnings.append(f"Exceeded response time budget: {duration_ms}ms > {budget.max_response_time_ms}ms")
                exceeded_budget = True
            elif duration_ms > budget.warning_threshold_ms:
                warnings.append(f"Approaching response time limit: {duration_ms}ms")
            
            if operation_data.get('database_queries', 0) > budget.max_database_queries:
                warnings.append(f"Exceeded database query budget: {operation_data['database_queries']} > {budget.max_database_queries}")
                exceeded_budget = True
            
            if operation_data.get('cache_misses', 0) > budget.max_cache_misses:
                warnings.append(f"Exceeded cache miss budget: {operation_data['cache_misses']} > {budget.max_cache_misses}")
            
            # Record metrics
            performance_result = PerformanceResult(
                operation_name=operation_name,
                duration_ms=duration_ms,
                cache_hits=operation_data.get('cache_hits', 0),
                cache_misses=operation_data.get('cache_misses', 0),
                database_queries=operation_data.get('database_queries', 0),
                warnings=warnings,
                exceeded_budget=exceeded_budget
            )
            
            # Update metrics
            self._update_performance_metrics(performance_result)
            
            if exceeded_budget:
                logger.warning(f"Performance budget exceeded for {operation_name}: {warnings}")
            elif warnings:
                logger.info(f"Performance warnings for {operation_name}: {warnings}")
            
            return result, performance_result
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Operation {operation_name} failed after {duration_ms}ms: {e}")
            
            performance_result = PerformanceResult(
                operation_name=operation_name,
                duration_ms=duration_ms,
                cache_hits=0,
                cache_misses=0,
                database_queries=0,
                warnings=[f"Operation failed: {str(e)}"],
                exceeded_budget=True
            )
            
            raise e
            
        finally:
            # Clean up tracking
            if operation_id in self.active_operations:
                del self.active_operations[operation_id]
    
    async def get_cached_or_compute(
        self,
        cache_key: str,
        compute_func: Callable,
        cache_level: CacheLevel = CacheLevel.MEMORY,
        ttl: Optional[int] = None,
        operation_id: str = None,
        *args, **kwargs
    ) -> Any:
        """Get data from cache or compute if not available."""
        # Check cache first
        cached_value = await self._get_from_cache(cache_key, cache_level)
        if cached_value is not None:
            self._record_cache_hit(operation_id)
            return cached_value
        
        # Use request coalescing to prevent duplicate computations
        async with self.request_locks[cache_key]:
            # Double-check cache after acquiring lock
            cached_value = await self._get_from_cache(cache_key, cache_level)
            if cached_value is not None:
                self._record_cache_hit(operation_id)
                return cached_value
            
            # Compute value
            self._record_cache_miss(operation_id)
            computed_value = await compute_func(*args, **kwargs)
            
            # Store in cache
            await self._store_in_cache(cache_key, computed_value, cache_level, ttl)
            
            return computed_value
    
    async def batch_operations(self, operations: List[Tuple[str, Callable, tuple, dict]]) -> List[Any]:
        """Execute multiple operations in parallel with performance tracking."""
        start_time = time.time()
        
        # Create tasks for parallel execution
        tasks = []
        for operation_name, func, args, kwargs in operations:
            task = asyncio.create_task(
                self.track_operation_performance(operation_name, func, self.performance_budget, *args, **kwargs)
            )
            tasks.append(task)
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and extract actual values
        actual_results = []
        performance_results = []
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch operation failed: {result}")
                actual_results.append(None)
                performance_results.append(None)
            else:
                actual_value, perf_result = result
                actual_results.append(actual_value)
                performance_results.append(perf_result)
        
        # Log batch performance
        total_duration = int((time.time() - start_time) * 1000)
        logger.info(f"Batch operation completed in {total_duration}ms for {len(operations)} operations")
        
        return actual_results
    
    async def execute_with_circuit_breaker(
        self,
        service_name: str,
        func: Callable,
        *args, **kwargs
    ) -> Any:
        """Execute function with circuit breaker protection."""
        circuit_breaker = self.circuit_breakers.get(service_name)
        if not circuit_breaker:
            return await func(*args, **kwargs)
        
        # Check circuit state
        if circuit_breaker.state == CircuitState.OPEN:
            if self._should_attempt_reset(circuit_breaker):
                circuit_breaker.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker {service_name} is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            
            # Success - update circuit breaker
            if circuit_breaker.state == CircuitState.HALF_OPEN:
                circuit_breaker.state = CircuitState.CLOSED
                circuit_breaker.failure_count = 0
                logger.info(f"Circuit breaker {service_name} reset to CLOSED")
            
            circuit_breaker.successful_calls += 1
            return result
            
        except Exception as e:
            # Failure - update circuit breaker
            circuit_breaker.failure_count += 1
            circuit_breaker.last_failure_time = datetime.utcnow()
            
            if circuit_breaker.failure_count >= circuit_breaker.failure_threshold:
                circuit_breaker.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {service_name} opened due to {circuit_breaker.failure_count} failures")
            
            raise e
    
    def get_performance_summary(self, time_window_minutes: int = 10) -> Dict[str, Any]:
        """Get performance summary for the specified time window."""
        cutoff_time = time.time() - (time_window_minutes * 60)
        
        # Filter recent metrics
        recent_metrics = {}
        for metric_type, values in self.performance_metrics.items():
            recent_values = [v for v in values if v.get('timestamp', 0) >= cutoff_time]
            recent_metrics[metric_type.value] = recent_values
        
        # Calculate summary statistics
        summary = {
            'time_window_minutes': time_window_minutes,
            'total_operations': len(recent_metrics.get('response_time', [])),
            'performance_metrics': {},
            'cache_performance': self._calculate_cache_performance(),
            'circuit_breaker_status': {name: cb.state.value for name, cb in self.circuit_breakers.items()},
            'active_operations': len(self.active_operations)
        }
        
        # Response time statistics
        response_times = [m['value'] for m in recent_metrics.get('response_time', [])]
        if response_times:
            summary['performance_metrics']['response_time'] = {
                'avg_ms': sum(response_times) / len(response_times),
                'max_ms': max(response_times),
                'min_ms': min(response_times),
                'p95_ms': self._calculate_percentile(response_times, 95),
                'p99_ms': self._calculate_percentile(response_times, 99),
                'budget_violations': len([rt for rt in response_times if rt > self.performance_budget.max_response_time_ms])
            }
        
        # Error rate
        errors = [m for m in recent_metrics.get('error_rate', []) if m.get('value', 0) > 0]
        summary['performance_metrics']['error_rate'] = len(errors) / max(len(recent_metrics.get('response_time', [])), 1) * 100
        
        # Throughput
        summary['performance_metrics']['throughput_ops_per_minute'] = len(recent_metrics.get('response_time', []))
        
        return summary
    
    async def warm_cache(self, warming_config: Dict[str, Any]):
        """Pre-load frequently accessed data into cache."""
        if not self.cache_config.cache_warming_enabled:
            return
        
        logger.info("Starting cache warming process")
        warming_tasks = []
        
        # Warm commonly accessed narrative fragments
        if 'fragments' in warming_config:
            fragment_ids = warming_config['fragments']
            for fragment_id in fragment_ids:
                task = asyncio.create_task(
                    self._warm_fragment_cache(fragment_id)
                )
                warming_tasks.append(task)
        
        # Warm user archetype data
        if 'user_archetypes' in warming_config:
            user_ids = warming_config['user_archetypes']
            for user_id in user_ids:
                task = asyncio.create_task(
                    self._warm_user_archetype_cache(user_id)
                )
                warming_tasks.append(task)
        
        # Execute warming tasks
        if warming_tasks:
            await asyncio.gather(*warming_tasks, return_exceptions=True)
            logger.info(f"Cache warming completed for {len(warming_tasks)} items")
    
    def optimize_query(self, query_template: str, parameters: Dict[str, Any]) -> str:
        """Optimize database query for better performance."""
        # Simple query optimization strategies
        optimized_query = query_template
        
        # Add query hints for common patterns
        if 'SELECT' in query_template.upper():
            # Add LIMIT if not present for large result sets
            if 'LIMIT' not in query_template.upper() and 'COUNT' not in query_template.upper():
                optimized_query += ' LIMIT 1000'
        
        # Cache prepared statement
        query_hash = hashlib.md5(query_template.encode()).hexdigest()
        self.prepared_statements[query_hash] = optimized_query
        
        return optimized_query
    
    # Private methods
    
    async def _get_from_cache(self, key: str, cache_level: CacheLevel) -> Any:
        """Get value from specified cache level."""
        if cache_level == CacheLevel.MEMORY:
            cached_item = self.memory_cache.get(key)
            if cached_item:
                # Check expiry
                if time.time() - cached_item['timestamp'] < self.cache_config.memory_ttl:
                    self.cache_hit_counts[key] += 1
                    return cached_item['value']
                else:
                    # Expired, remove from cache
                    del self.memory_cache[key]
        
        # For distributed and database cache levels, would integrate with Redis/DB
        # For now, return None (cache miss)
        return None
    
    async def _store_in_cache(self, key: str, value: Any, cache_level: CacheLevel, ttl: Optional[int] = None):
        """Store value in specified cache level."""
        if cache_level == CacheLevel.MEMORY:
            # Implement LRU eviction if cache is full
            if len(self.memory_cache) >= self.cache_config.max_memory_size:
                self._evict_lru_items()
            
            self.memory_cache[key] = {
                'value': value,
                'timestamp': time.time(),
                'access_count': 1
            }
            self.cache_access_times[key] = time.time()
    
    def _evict_lru_items(self, count: int = None):
        """Evict least recently used items from memory cache."""
        if not count:
            count = max(1, len(self.memory_cache) // 10)  # Evict 10% of cache
        
        # Sort by last access time
        items_by_access_time = sorted(
            self.cache_access_times.items(),
            key=lambda x: x[1]
        )
        
        # Remove oldest items
        for key, _ in items_by_access_time[:count]:
            if key in self.memory_cache:
                del self.memory_cache[key]
            if key in self.cache_access_times:
                del self.cache_access_times[key]
    
    def _record_cache_hit(self, operation_id: str = None):
        """Record cache hit for performance tracking."""
        if operation_id and operation_id in self.active_operations:
            self.active_operations[operation_id]['cache_hits'] += 1
        
        self.performance_metrics[PerformanceMetric.CACHE_HIT_RATE].append({
            'timestamp': time.time(),
            'value': 1,  # Hit
            'operation_id': operation_id
        })
    
    def _record_cache_miss(self, operation_id: str = None):
        """Record cache miss for performance tracking."""
        if operation_id and operation_id in self.active_operations:
            self.active_operations[operation_id]['cache_misses'] += 1
        
        self.performance_metrics[PerformanceMetric.CACHE_HIT_RATE].append({
            'timestamp': time.time(),
            'value': 0,  # Miss
            'operation_id': operation_id
        })
    
    def _should_attempt_reset(self, circuit_breaker: CircuitBreaker) -> bool:
        """Check if circuit breaker should attempt reset."""
        if circuit_breaker.last_failure_time is None:
            return True
        
        time_since_failure = (datetime.utcnow() - circuit_breaker.last_failure_time).total_seconds()
        return time_since_failure >= circuit_breaker.recovery_timeout
    
    def _update_performance_metrics(self, performance_result: PerformanceResult):
        """Update performance metrics with operation result."""
        timestamp = time.time()
        
        self.performance_metrics[PerformanceMetric.RESPONSE_TIME].append({
            'timestamp': timestamp,
            'value': performance_result.duration_ms,
            'operation': performance_result.operation_name
        })
        
        self.performance_metrics[PerformanceMetric.QUERY_COUNT].append({
            'timestamp': timestamp,
            'value': performance_result.database_queries,
            'operation': performance_result.operation_name
        })
        
        if performance_result.exceeded_budget or performance_result.warnings:
            self.performance_metrics[PerformanceMetric.ERROR_RATE].append({
                'timestamp': timestamp,
                'value': 1,
                'operation': performance_result.operation_name,
                'warnings': performance_result.warnings
            })
    
    def _calculate_cache_performance(self) -> Dict[str, Any]:
        """Calculate cache performance statistics."""
        total_hits = sum(self.cache_hit_counts.values())
        cache_items = len(self.memory_cache)
        
        return {
            'memory_cache_size': cache_items,
            'memory_cache_limit': self.cache_config.max_memory_size,
            'memory_utilization_percent': (cache_items / self.cache_config.max_memory_size) * 100,
            'total_cache_hits': total_hits,
            'most_accessed_keys': sorted(
                self.cache_hit_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * (percentile / 100)
        f = int(k)
        c = k - f
        
        if f == len(sorted_values) - 1:
            return sorted_values[f]
        else:
            return sorted_values[f] * (1 - c) + sorted_values[f + 1] * c
    
    async def _warm_fragment_cache(self, fragment_id: str):
        """Warm cache for a specific narrative fragment."""
        try:
            # This would typically load the fragment from database
            # For now, just simulate the cache warming
            cache_key = f"fragment:{fragment_id}"
            # Simulate loading fragment data
            await asyncio.sleep(0.01)  # Simulate database query
            fragment_data = {'id': fragment_id, 'warmed': True}
            await self._store_in_cache(cache_key, fragment_data, CacheLevel.MEMORY)
            
        except Exception as e:
            logger.error(f"Failed to warm cache for fragment {fragment_id}: {e}")
    
    async def _warm_user_archetype_cache(self, user_id: int):
        """Warm cache for user archetype data."""
        try:
            cache_key = f"user_archetype:{user_id}"
            # Simulate loading archetype data
            await asyncio.sleep(0.01)  # Simulate database query
            archetype_data = {'user_id': user_id, 'archetype': 'explorer', 'warmed': True}
            await self._store_in_cache(cache_key, archetype_data, CacheLevel.MEMORY)
            
        except Exception as e:
            logger.error(f"Failed to warm cache for user archetype {user_id}: {e}")
    
    def _start_background_tasks(self):
        """Start background maintenance tasks."""
        self._cleanup_task = asyncio.create_task(self._cache_cleanup_loop())
        self._metrics_task = asyncio.create_task(self._metrics_cleanup_loop())
    
    async def _cache_cleanup_loop(self):
        """Background task to clean up expired cache entries."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Clean up expired memory cache entries
                current_time = time.time()
                expired_keys = []
                
                for key, item in self.memory_cache.items():
                    if current_time - item['timestamp'] > self.cache_config.memory_ttl:
                        expired_keys.append(key)
                
                for key in expired_keys:
                    if key in self.memory_cache:
                        del self.memory_cache[key]
                    if key in self.cache_access_times:
                        del self.cache_access_times[key]
                
                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                
            except Exception as e:
                logger.error(f"Error in cache cleanup loop: {e}")
    
    async def _metrics_cleanup_loop(self):
        """Background task to clean up old performance metrics."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Clean up old metrics (keep only last 24 hours)
                cutoff_time = time.time() - 86400  # 24 hours
                
                for metric_type in self.performance_metrics:
                    old_metrics = self.performance_metrics[metric_type]
                    self.performance_metrics[metric_type] = deque(
                        [m for m in old_metrics if m.get('timestamp', 0) >= cutoff_time],
                        maxlen=1000
                    )
                
                logger.debug("Cleaned up old performance metrics")
                
            except Exception as e:
                logger.error(f"Error in metrics cleanup loop: {e}")
    
    def __del__(self):
        """Cleanup background tasks when service is destroyed."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._metrics_task:
            self._metrics_task.cancel()