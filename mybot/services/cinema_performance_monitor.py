"""
Cinema Performance Monitor
========================

Performance monitoring and caching service for cinema operations to ensure
optimal response times and system stability.

Key Features:
- Response time monitoring (<500ms target)
- Cinema operation caching
- Performance metrics collection
- Automatic fallback triggers
- Memory usage optimization
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import json
import weakref
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Individual performance measurement."""
    operation: str
    user_id: int
    start_time: float
    end_time: float
    success: bool
    error: Optional[str] = None
    cache_hit: bool = False
    enhancement_type: str = "none"
    
    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000
    
    @property
    def meets_target(self) -> bool:
        return self.duration_ms <= 500  # 500ms target

@dataclass
class CacheEntry:
    """Cache entry with TTL and metadata."""
    key: str
    value: Any
    created_at: datetime
    ttl_seconds: int
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.created_at + timedelta(seconds=self.ttl_seconds)
    
    def access(self) -> Any:
        """Access the cached value and update metrics."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()
        return self.value

class CinemaPerformanceMonitor:
    """
    Enhanced performance monitoring and caching service for cinema operations.
    Integrates with the new CinemaPerformanceOptimizer for advanced optimization.
    """
    
    def __init__(self, session: Optional[AsyncSession] = None, max_metrics: int = 1000, cache_size_limit: int = 500):
        self.session = session
        self.max_metrics = max_metrics
        self.cache_size_limit = cache_size_limit
        
        # Performance tracking
        self.metrics: deque[PerformanceMetric] = deque(maxlen=max_metrics)
        self.operation_counts: Dict[str, int] = {}
        self.error_counts: Dict[str, int] = {}
        
        # Integration with advanced optimizer
        self._performance_optimizer = None
        
        # Caching system
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Enhanced performance thresholds
        self.response_time_target_ms = 400  # Improved from 500ms to 400ms
        self.character_validation_target_ms = 30  # New target for character validation
        self.error_rate_threshold = 0.05  # 5%
        self.cache_hit_rate_target = 0.90  # Improved from 70% to 90%
        
        # System health
        self.system_healthy = True
        self.last_health_check = datetime.utcnow()
        
    def start_operation(self, operation: str, user_id: int, **context) -> str:
        """
        Start tracking a cinema operation.
        
        Args:
            operation: Operation name
            user_id: User ID
            **context: Additional context data
            
        Returns:
            Operation tracking ID
        """
        tracking_id = f"{operation}_{user_id}_{time.time()}"
        
        # Increment operation count
        self.operation_counts[operation] = self.operation_counts.get(operation, 0) + 1
        
        return tracking_id
    
    def end_operation(self, tracking_id: str, operation: str, user_id: int, 
                     success: bool, error: Optional[str] = None, 
                     cache_hit: bool = False, enhancement_type: str = "none") -> PerformanceMetric:
        """
        End tracking a cinema operation and record metrics.
        
        Args:
            tracking_id: Operation tracking ID
            operation: Operation name
            user_id: User ID
            success: Whether operation succeeded
            error: Error message if failed
            cache_hit: Whether result was from cache
            enhancement_type: Type of cinema enhancement applied
            
        Returns:
            Performance metric
        """
        end_time = time.time()
        
        # Extract start time from tracking ID
        try:
            start_time = float(tracking_id.split('_')[-1])
        except (ValueError, IndexError):
            start_time = end_time  # Fallback
            
        metric = PerformanceMetric(
            operation=operation,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            success=success,
            error=error,
            cache_hit=cache_hit,
            enhancement_type=enhancement_type
        )
        
        self.metrics.append(metric)
        
        # Track errors
        if not success and error:
            self.error_counts[f"{operation}:{error}"] = self.error_counts.get(f"{operation}:{error}", 0) + 1
        
        # Log slow operations
        if metric.duration_ms > self.response_time_target_ms:
            logger.warning(f"Slow cinema operation: {operation} took {metric.duration_ms:.2f}ms for user {user_id}")
        
        # Update system health if needed
        if metric.duration_ms > self.response_time_target_ms * 2:  # Very slow
            self._check_system_health()
        
        return metric
    
    def cache_get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if exists and not expired, None otherwise
        """
        entry = self.cache.get(key)
        if not entry:
            self.cache_misses += 1
            return None
            
        if entry.is_expired:
            del self.cache[key]
            self.cache_misses += 1
            return None
        
        self.cache_hits += 1
        return entry.access()
    
    def cache_set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (default 5 minutes)
        """
        # Evict expired entries if cache is full
        if len(self.cache) >= self.cache_size_limit:
            self._evict_expired_entries()
            
            # If still full, evict least recently accessed
            if len(self.cache) >= self.cache_size_limit:
                self._evict_lru_entries(self.cache_size_limit // 4)  # Evict 25%
        
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.utcnow(),
            ttl_seconds=ttl_seconds
        )
        
        self.cache[key] = entry
    
    def cache_key_for_operation(self, operation: str, user_id: int, **params) -> str:
        """
        Generate standardized cache key for cinema operations.
        
        Args:
            operation: Operation name
            user_id: User ID
            **params: Additional parameters
            
        Returns:
            Cache key
        """
        param_str = json.dumps(params, sort_keys=True, default=str)
        return f"cinema:{operation}:{user_id}:{hash(param_str)}"
    
    async def monitor_operation(self, operation: str, user_id: int, 
                              operation_func: Callable, cache_ttl: int = 300, 
                              use_advanced_optimization: bool = True,
                              **kwargs) -> Dict[str, Any]:
        """
        Monitor and cache a cinema operation with advanced optimization.
        
        Args:
            operation: Operation name
            user_id: User ID
            operation_func: Async function to execute
            cache_ttl: Cache TTL in seconds
            use_advanced_optimization: Whether to use the advanced optimizer
            **kwargs: Arguments for operation_func
            
        Returns:
            Operation result with performance metadata
        """
        # Use advanced optimizer if available and requested
        if use_advanced_optimization and self._get_performance_optimizer():
            try:
                optimizer = self._get_performance_optimizer()
                return await optimizer.optimize_operation(operation, user_id, operation_func, **kwargs)
            except Exception as e:
                logger.warning(f"Advanced optimization failed for {operation}, falling back to basic monitoring: {e}")
        
        # Generate cache key
        cache_key = self.cache_key_for_operation(operation, user_id, **kwargs)
        
        # Try cache first
        cached_result = self.cache_get(cache_key)
        if cached_result is not None:
            return {
                "result": cached_result,
                "cached": True,
                "cache_key": cache_key,
                "performance": {"cache_hit": True}
            }
        
        # Execute operation with monitoring
        tracking_id = self.start_operation(operation, user_id)
        success = False
        error = None
        result = None
        
        try:
            result = await operation_func(**kwargs)
            success = True
            
            # Cache successful results
            if result is not None:
                self.cache_set(cache_key, result, cache_ttl)
            
        except Exception as e:
            error = str(e)
            logger.exception(f"Error in monitored cinema operation {operation}: {e}")
            result = {"error": error, "success": False}
        
        # Record metrics
        metric = self.end_operation(
            tracking_id, operation, user_id, success, error, 
            cache_hit=False, enhancement_type=kwargs.get('enhancement_type', 'none')
        )
        
        return {
            "result": result,
            "cached": False,
            "cache_key": cache_key,
            "performance": {
                "duration_ms": metric.duration_ms,
                "meets_target": metric.meets_target,
                "cache_hit": False,
                "success": success
            }
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        if not self.metrics:
            return {
                "total_operations": 0,
                "system_health": "unknown"
            }
        
        total_ops = len(self.metrics)
        successful_ops = sum(1 for m in self.metrics if m.success)
        cache_hits = sum(1 for m in self.metrics if m.cache_hit)
        
        durations = [m.duration_ms for m in self.metrics]
        meeting_target = sum(1 for m in self.metrics if m.meets_target)
        
        # Calculate rates
        success_rate = successful_ops / total_ops if total_ops > 0 else 0
        error_rate = 1 - success_rate
        cache_hit_rate = (self.cache_hits / (self.cache_hits + self.cache_misses) 
                         if (self.cache_hits + self.cache_misses) > 0 else 0)
        target_meet_rate = meeting_target / total_ops if total_ops > 0 else 0
        
        return {
            "total_operations": total_ops,
            "success_rate": success_rate,
            "error_rate": error_rate,
            "cache_hit_rate": cache_hit_rate,
            "target_meet_rate": target_meet_rate,
            "system_health": self._calculate_system_health(),
            "performance": {
                "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
                "min_duration_ms": min(durations) if durations else 0,
                "max_duration_ms": max(durations) if durations else 0,
                "operations_over_target": total_ops - meeting_target
            },
            "cache": {
                "size": len(self.cache),
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": cache_hit_rate
            },
            "operation_counts": dict(self.operation_counts),
            "top_errors": dict(sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        }
    
    def should_use_fallback(self, operation: str) -> bool:
        """
        Determine if fallback should be used for an operation.
        
        Args:
            operation: Operation name
            
        Returns:
            True if fallback should be used
        """
        # Check recent performance for this operation
        recent_metrics = [m for m in self.metrics 
                         if m.operation == operation and 
                         (time.time() - m.end_time) < 300]  # Last 5 minutes
        
        if len(recent_metrics) < 5:  # Not enough data
            return False
        
        # Check error rate
        error_count = sum(1 for m in recent_metrics if not m.success)
        error_rate = error_count / len(recent_metrics)
        
        if error_rate > self.error_rate_threshold:
            logger.warning(f"High error rate for {operation}: {error_rate:.2%}")
            return True
        
        # Check performance
        slow_count = sum(1 for m in recent_metrics if not m.meets_target)
        slow_rate = slow_count / len(recent_metrics)
        
        if slow_rate > 0.5:  # More than 50% slow
            logger.warning(f"High slow rate for {operation}: {slow_rate:.2%}")
            return True
        
        return False
    
    def _evict_expired_entries(self):
        """Remove expired entries from cache."""
        expired_keys = [key for key, entry in self.cache.items() if entry.is_expired]
        for key in expired_keys:
            del self.cache[key]
    
    def _evict_lru_entries(self, count: int):
        """Remove least recently used entries."""
        sorted_entries = sorted(
            self.cache.items(), 
            key=lambda x: x[1].last_accessed
        )
        
        for key, _ in sorted_entries[:count]:
            del self.cache[key]
    
    def _check_system_health(self):
        """Check and update system health status."""
        now = datetime.utcnow()
        
        # Don't check too frequently
        if (now - self.last_health_check).total_seconds() < 30:
            return
            
        self.last_health_check = now
        
        # Get recent metrics (last 5 minutes)
        recent_metrics = [m for m in self.metrics 
                         if (now.timestamp() - m.end_time) < 300]
        
        if not recent_metrics:
            return
        
        # Calculate health indicators
        error_rate = sum(1 for m in recent_metrics if not m.success) / len(recent_metrics)
        slow_rate = sum(1 for m in recent_metrics if not m.meets_target) / len(recent_metrics)
        
        # Update health status
        previous_health = self.system_healthy
        self.system_healthy = error_rate < self.error_rate_threshold and slow_rate < 0.3
        
        if previous_health != self.system_healthy:
            if self.system_healthy:
                logger.info("Cinema system health recovered")
            else:
                logger.warning(f"Cinema system health degraded - error_rate: {error_rate:.2%}, slow_rate: {slow_rate:.2%}")
    
    def _calculate_system_health(self) -> str:
        """Calculate current system health status."""
        if not self.metrics:
            return "unknown"
        
        # Recent performance
        recent_metrics = [m for m in self.metrics 
                         if (time.time() - m.end_time) < 300]  # Last 5 minutes
        
        if not recent_metrics:
            return "idle"
        
        error_rate = sum(1 for m in recent_metrics if not m.success) / len(recent_metrics)
        slow_rate = sum(1 for m in recent_metrics if not m.meets_target) / len(recent_metrics)
        
        if error_rate > self.error_rate_threshold:
            return "unhealthy"
        elif slow_rate > 0.5:
            return "degraded"
        elif slow_rate > 0.2:
            return "warning"
        else:
            return "healthy"
    
    def _get_performance_optimizer(self):
        """Get the advanced performance optimizer if available."""
        if self._performance_optimizer is None and self.session:
            try:
                from .cinema_performance_optimizer import get_cinema_performance_optimizer
                self._performance_optimizer = get_cinema_performance_optimizer(self.session)
            except ImportError:
                logger.debug("Advanced performance optimizer not available")
        return self._performance_optimizer
    
    async def trigger_advanced_optimization(self) -> Dict[str, Any]:
        """Trigger advanced system optimization if available."""
        optimizer = self._get_performance_optimizer()
        if optimizer:
            return await optimizer.trigger_full_system_optimization()
        return {"success": False, "reason": "Advanced optimizer not available"}
    
    async def get_comprehensive_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report including advanced metrics."""
        basic_summary = self.get_performance_summary()
        
        optimizer = self._get_performance_optimizer()
        if optimizer:
            advanced_report = optimizer.get_comprehensive_performance_report()
            return {
                "basic_monitoring": basic_summary,
                "advanced_optimization": advanced_report,
                "integration_active": True
            }
        
        return {
            "basic_monitoring": basic_summary,
            "integration_active": False
        }

# Global performance monitor instance
_performance_monitor = None

def get_cinema_performance_monitor(session: Optional[AsyncSession] = None) -> CinemaPerformanceMonitor:
    """Get or create the global cinema performance monitor."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = CinemaPerformanceMonitor(session)
    elif session and _performance_monitor.session != session:
        _performance_monitor = CinemaPerformanceMonitor(session)
    return _performance_monitor

async def monitor_cinema_operation(operation: str, user_id: int, 
                                 operation_func: Callable, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to monitor a cinema operation.
    
    Args:
        operation: Operation name
        user_id: User ID  
        operation_func: Async function to execute
        **kwargs: Arguments for operation_func
        
    Returns:
        Operation result with performance data
    """
    monitor = get_cinema_performance_monitor()
    return await monitor.monitor_operation(operation, user_id, operation_func, **kwargs)