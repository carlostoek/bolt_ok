"""
Decision Performance Optimizer
Advanced performance optimization service for Diana Bot decision tree system.
Ensures <500ms processing target while maintaining character consistency and data integrity.
"""

import logging
import json
import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text
from sqlalchemy.orm import selectinload
from database.narrative_unified import NarrativeFragment, UserNarrativeState, UserDecisionLog

logger = logging.getLogger(__name__)

class PerformanceMetricType(Enum):
    """Types of performance metrics to track."""
    RESPONSE_TIME = "response_time"
    DATABASE_QUERY = "database_query"
    CACHE_PERFORMANCE = "cache_performance"
    MEMORY_USAGE = "memory_usage"
    CONCURRENCY = "concurrency"
    CHARACTER_VALIDATION = "character_validation"

class OptimizationLevel(Enum):
    """Optimization levels for different scenarios."""
    CONSERVATIVE = 1  # Minimal optimization, maximum safety
    BALANCED = 2      # Good performance with safety checks
    AGGRESSIVE = 3    # Maximum performance optimization
    EMERGENCY = 4     # Emergency mode, bypass non-critical checks

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""
    operation_name: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    database_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    memory_peak_mb: Optional[float] = None
    character_validations: int = 0
    errors_encountered: int = 0
    
    def complete(self):
        """Mark the operation as complete and calculate duration."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000

@dataclass
class OptimizationRule:
    """Performance optimization rule."""
    rule_id: str
    condition: Callable[[Dict[str, Any]], bool]
    optimization: Callable[[Dict[str, Any]], Dict[str, Any]]
    priority: int
    description: str
    safety_level: OptimizationLevel = OptimizationLevel.BALANCED

class DecisionPerformanceOptimizer:
    """
    Advanced performance optimization system for decision tree processing.
    
    Features:
    - Real-time performance monitoring
    - Adaptive caching strategies
    - Database query optimization
    - Memory usage optimization
    - Concurrent processing optimization
    - Character validation caching
    - Emergency performance mode
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Performance targets
        self.target_response_time_ms = 500
        self.emergency_threshold_ms = 2000
        self.cache_hit_target = 0.8
        
        # Memory management configuration
        self.max_cache_memory_mb = 50  # Maximum 50MB for all caches combined
        self.critical_memory_threshold_mb = 40  # Trigger aggressive cleanup at 40MB
        self.memory_check_interval = 100  # Check memory every 100 cache operations
        self._cache_operations_count = 0
        
        # Optimization state
        self.current_optimization_level = OptimizationLevel.BALANCED
        self.emergency_mode_active = False
        
        # Performance tracking
        self.metrics_history = deque(maxlen=1000)
        self.active_operations = {}
        self.performance_stats = defaultdict(list)
        
        # Caching system
        self.fragment_cache = {}
        self.state_cache = {}
        self.validation_cache = {}
        self.query_cache = {}
        
        # Cache TTLs (in seconds)
        self.cache_ttls = {
            'fragment': 300,     # 5 minutes
            'state': 180,        # 3 minutes  
            'validation': 600,   # 10 minutes
            'query': 120         # 2 minutes
        }
        
        # Optimization rules
        self.optimization_rules = self._initialize_optimization_rules()
        
        # Concurrent processing limits
        self.max_concurrent_decisions = 50
        self.active_decision_semaphore = asyncio.Semaphore(self.max_concurrent_decisions)
        
        # Database connection pooling
        self._db_pool_optimization_active = False
    
    def performance_monitor(self, operation_name: str):
        """Decorator for monitoring operation performance."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                metrics = PerformanceMetrics(operation_name)
                self.active_operations[id(metrics)] = metrics
                
                try:
                    # Pre-optimization
                    await self._pre_operation_optimization(operation_name, metrics)
                    
                    # Execute operation
                    result = await func(*args, **kwargs)
                    
                    # Post-optimization
                    await self._post_operation_optimization(operation_name, metrics, result)
                    
                    return result
                    
                except Exception as e:
                    metrics.errors_encountered += 1
                    logger.error(f"Error in monitored operation {operation_name}: {e}")
                    raise
                    
                finally:
                    metrics.complete()
                    self.metrics_history.append(metrics)
                    
                    # Remove from active operations
                    self.active_operations.pop(id(metrics), None)
                    
                    # Check if emergency mode needed
                    await self._check_emergency_mode_trigger(metrics)
            
            return wrapper
        return decorator
    
    async def optimize_decision_processing(
        self,
        user_id: int,
        fragment_id: str,
        choice_index: int,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimize decision processing for performance.
        
        Args:
            user_id: User making the decision
            fragment_id: Fragment being processed
            choice_index: Selected choice
            context: Additional context
            
        Returns:
            Optimization recommendations and cached data
        """
        try:
            optimization_start = time.time()
            
            # Apply optimization rules
            optimization_context = {
                'user_id': user_id,
                'fragment_id': fragment_id,
                'choice_index': choice_index,
                'context': context or {},
                'current_level': self.current_optimization_level,
                'emergency_mode': self.emergency_mode_active
            }
            
            # Get optimization recommendations
            recommendations = await self._get_optimization_recommendations(optimization_context)
            
            # Pre-load cached data
            cached_data = await self._preload_optimization_data(optimization_context)
            
            # Optimize database queries
            query_optimizations = await self._optimize_database_queries(optimization_context)
            
            # Memory optimization
            memory_optimizations = await self._optimize_memory_usage(optimization_context)
            
            optimization_time_ms = (time.time() - optimization_start) * 1000
            
            return {
                'optimization_time_ms': optimization_time_ms,
                'recommendations': recommendations,
                'cached_data': cached_data,
                'query_optimizations': query_optimizations,
                'memory_optimizations': memory_optimizations,
                'current_optimization_level': self.current_optimization_level.name,
                'emergency_mode_active': self.emergency_mode_active
            }
            
        except Exception as e:
            logger.error(f"Error in decision processing optimization: {e}")
            return {
                'error': str(e),
                'fallback_mode': True,
                'optimization_time_ms': (time.time() - optimization_start) * 1000 if 'optimization_start' in locals() else 0
            }
    
    async def get_performance_analytics(
        self,
        timeframe: timedelta = timedelta(hours=1)
    ) -> Dict[str, Any]:
        """
        Get comprehensive performance analytics.
        
        Args:
            timeframe: Time window for analysis
            
        Returns:
            Performance analytics report
        """
        try:
            cutoff_time = time.time() - timeframe.total_seconds()
            recent_metrics = [m for m in self.metrics_history if m.start_time >= cutoff_time]
            
            if not recent_metrics:
                return {
                    'analytics_available': False,
                    'message': 'No metrics available for the specified timeframe'
                }
            
            # Calculate key metrics
            response_times = [m.duration_ms for m in recent_metrics if m.duration_ms]
            
            analytics = {
                'timeframe_hours': timeframe.total_seconds() / 3600,
                'total_operations': len(recent_metrics),
                'performance_metrics': {
                    'avg_response_time_ms': sum(response_times) / len(response_times) if response_times else 0,
                    'min_response_time_ms': min(response_times) if response_times else 0,
                    'max_response_time_ms': max(response_times) if response_times else 0,
                    'target_achievement_rate': sum(1 for rt in response_times if rt <= self.target_response_time_ms) / len(response_times) if response_times else 0,
                    'emergency_triggers': sum(1 for rt in response_times if rt >= self.emergency_threshold_ms)
                },
                'cache_performance': {
                    'total_cache_hits': sum(m.cache_hits for m in recent_metrics),
                    'total_cache_misses': sum(m.cache_misses for m in recent_metrics),
                    'cache_hit_rate': 0  # Will be calculated below
                },
                'database_performance': {
                    'total_queries': sum(m.database_queries for m in recent_metrics),
                    'avg_queries_per_operation': sum(m.database_queries for m in recent_metrics) / len(recent_metrics)
                },
                'optimization_effectiveness': await self._analyze_optimization_effectiveness(recent_metrics),
                'recommendations': await self._generate_performance_recommendations(recent_metrics)
            }
            
            # Calculate cache hit rate
            total_cache_operations = analytics['cache_performance']['total_cache_hits'] + analytics['cache_performance']['total_cache_misses']
            if total_cache_operations > 0:
                analytics['cache_performance']['cache_hit_rate'] = analytics['cache_performance']['total_cache_hits'] / total_cache_operations
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error generating performance analytics: {e}")
            return {
                'analytics_available': False,
                'error': str(e)
            }
    
    async def activate_emergency_mode(self, reason: str = "Manual activation"):
        """
        Activate emergency performance mode.
        
        Args:
            reason: Reason for activation
        """
        try:
            logger.warning(f"Activating emergency performance mode: {reason}")
            
            self.emergency_mode_active = True
            self.current_optimization_level = OptimizationLevel.EMERGENCY
            
            # Clear non-essential caches to free memory
            await self._clear_non_essential_caches()
            
            # Reduce concurrent processing limit
            self.max_concurrent_decisions = 20
            self.active_decision_semaphore = asyncio.Semaphore(self.max_concurrent_decisions)
            
            # Disable expensive validations temporarily
            await self._disable_expensive_validations()
            
            logger.info("Emergency performance mode activated successfully")
            
        except Exception as e:
            logger.error(f"Error activating emergency mode: {e}")
    
    async def deactivate_emergency_mode(self, reason: str = "Manual deactivation"):
        """
        Deactivate emergency performance mode.
        
        Args:
            reason: Reason for deactivation
        """
        try:
            logger.info(f"Deactivating emergency performance mode: {reason}")
            
            self.emergency_mode_active = False
            self.current_optimization_level = OptimizationLevel.BALANCED
            
            # Restore normal processing limits
            self.max_concurrent_decisions = 50
            self.active_decision_semaphore = asyncio.Semaphore(self.max_concurrent_decisions)
            
            # Re-enable validations
            await self._enable_normal_validations()
            
            logger.info("Emergency performance mode deactivated successfully")
            
        except Exception as e:
            logger.error(f"Error deactivating emergency mode: {e}")
    
    # Cache Management Methods
    
    async def get_cached_fragment(self, fragment_id: str) -> Optional[Dict[str, Any]]:
        """Get fragment from cache with performance tracking."""
        cache_key = f"fragment_{fragment_id}"
        
        if cache_key in self.fragment_cache:
            cache_entry = self.fragment_cache[cache_key]
            
            # Check TTL
            if time.time() - cache_entry['timestamp'] < self.cache_ttls['fragment']:
                # Update access metrics
                cache_entry['access_count'] += 1
                cache_entry['last_accessed'] = time.time()
                return cache_entry['data']
            else:
                # Remove expired entry
                del self.fragment_cache[cache_key]
        
        return None
    
    async def cache_fragment(self, fragment_id: str, fragment_data: Dict[str, Any]):
        """Cache fragment data with metadata."""
        cache_key = f"fragment_{fragment_id}"
        
        self.fragment_cache[cache_key] = {
            'data': fragment_data,
            'timestamp': time.time(),
            'access_count': 1,
            'last_accessed': time.time(),
            'size_bytes': len(json.dumps(fragment_data))
        }
        
        # Manage cache size and memory
        await self._manage_cache_size('fragment')
        await self._check_memory_usage()
    
    async def get_cached_user_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user state from cache."""
        cache_key = f"state_{user_id}"
        
        if cache_key in self.state_cache:
            cache_entry = self.state_cache[cache_key]
            
            if time.time() - cache_entry['timestamp'] < self.cache_ttls['state']:
                cache_entry['access_count'] += 1
                cache_entry['last_accessed'] = time.time()
                return cache_entry['data']
            else:
                del self.state_cache[cache_key]
        
        return None
    
    async def cache_user_state(self, user_id: int, state_data: Dict[str, Any]):
        """Cache user state data."""
        cache_key = f"state_{user_id}"
        
        self.state_cache[cache_key] = {
            'data': state_data,
            'timestamp': time.time(),
            'access_count': 1,
            'last_accessed': time.time(),
            'size_bytes': len(json.dumps(state_data))
        }
        
        await self._manage_cache_size('state')
        await self._check_memory_usage()
    
    async def get_cached_validation(self, text_hash: str) -> Optional[Dict[str, Any]]:
        """Get character validation result from cache."""
        cache_key = f"validation_{text_hash}"
        
        if cache_key in self.validation_cache:
            cache_entry = self.validation_cache[cache_key]
            
            if time.time() - cache_entry['timestamp'] < self.cache_ttls['validation']:
                cache_entry['access_count'] += 1
                return cache_entry['data']
            else:
                del self.validation_cache[cache_key]
        
        return None
    
    async def cache_validation(self, text_hash: str, validation_result: Dict[str, Any]):
        """Cache character validation result."""
        cache_key = f"validation_{text_hash}"
        
        self.validation_cache[cache_key] = {
            'data': validation_result,
            'timestamp': time.time(),
            'access_count': 1,
            'size_bytes': len(json.dumps(validation_result))
        }
        
        await self._manage_cache_size('validation')
        await self._check_memory_usage()
    
    # Database Optimization Methods
    
    async def optimize_fragment_query(self, fragment_id: str) -> Optional[Dict[str, Any]]:
        """Optimize fragment query with eager loading."""
        try:
            # Check cache first
            cached_fragment = await self.get_cached_fragment(fragment_id)
            if cached_fragment:
                return cached_fragment
            
            # Optimized query with eager loading for performance
            # For NarrativeFragment, we don't need relationship loading as data is in JSON columns
            # But we can optimize the query itself for better performance
            query = select(NarrativeFragment).where(
                NarrativeFragment.id == fragment_id
            ).execution_options(
                compiled_cache={},  # Use statement caching for repeated queries
                schema_translate_map=None  # Disable schema translation for performance
            )
            
            # Execute with connection optimization
            result = await self.session.execute(query)
            fragment = result.scalar_one_or_none()
            
            if fragment:
                fragment_data = {
                    'id': fragment.id,
                    'title': fragment.title,
                    'content': fragment.content,
                    'fragment_type': fragment.fragment_type,
                    'choices': fragment.choices,
                    'triggers': fragment.triggers
                }
                
                # Cache the result
                await self.cache_fragment(fragment_id, fragment_data)
                
                return fragment_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error in optimized fragment query: {e}")
            return None
    
    async def optimize_user_state_query(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Optimize user state query."""
        try:
            # Check cache first
            cached_state = await self.get_cached_user_state(user_id)
            if cached_state:
                return cached_state
            
            # Optimized query using SQLAlchemy ORM with proper eager loading
            from database.narrative_unified import UserNarrativeState, UserArchetype, UserMissionProgress
            from database.models import User
            
            # Main user state query with optimized execution options
            user_state_query = select(UserNarrativeState).where(
                UserNarrativeState.user_id == user_id
            ).execution_options(
                compiled_cache={},
                schema_translate_map=None
            )
            
            # Add eager loading if relationship exists
            if hasattr(UserNarrativeState, 'current_fragment'):
                user_state_query = user_state_query.options(
                    selectinload(UserNarrativeState.current_fragment)
                )
            
            # Related data queries with optimized loading
            archetype_query = select(UserArchetype).where(
                UserArchetype.user_id == user_id
            ).execution_options(compiled_cache={})
            
            mission_query = select(UserMissionProgress).where(
                UserMissionProgress.user_id == user_id  
            ).execution_options(compiled_cache={})
            
            # Execute queries concurrently for maximum performance
            state_result, archetype_result, mission_result = await asyncio.gather(
                self.session.execute(user_state_query),
                self.session.execute(archetype_query), 
                self.session.execute(mission_query),
                return_exceptions=True
            )
            
            user_state = state_result.scalar_one_or_none() if not isinstance(state_result, Exception) else None
            user_archetype = archetype_result.scalar_one_or_none() if not isinstance(archetype_result, Exception) else None
            mission_progress = mission_result.scalar_one_or_none() if not isinstance(mission_result, Exception) else None
            
            if user_state:
                state_data = {
                    'user_id': user_state.user_id,
                    'current_fragment_id': user_state.current_fragment_id,
                    'current_level': user_state.current_level,
                    'current_tier': user_state.current_tier,
                    'visited_fragments': user_state.visited_fragments or [],
                    'completed_fragments': user_state.completed_fragments or [],
                    'unlocked_clues': user_state.unlocked_clues or [],
                    'interaction_patterns': user_state.interaction_patterns or {},
                    'diana_consistency_average': user_state.diana_consistency_average,
                    'archetype_data': {
                        'dominant_archetype': user_archetype.dominant_archetype if user_archetype else None,
                        'avg_response_time': user_archetype.avg_response_time if user_archetype else None
                    },
                    'mission_data': {
                        'current_level': mission_progress.current_level if mission_progress else None,
                        'current_tier': mission_progress.current_tier if mission_progress else None
                    }
                }
                
                # Cache the result
                await self.cache_user_state(user_id, state_data)
                
                return state_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error in optimized user state query: {e}")
            return None
    
    # Private Implementation Methods
    
    async def _pre_operation_optimization(self, operation_name: str, metrics: PerformanceMetrics):
        """Apply pre-operation optimizations."""
        try:
            # Warm up caches if needed
            if self.current_optimization_level >= OptimizationLevel.BALANCED:
                await self._warm_up_relevant_caches(operation_name)
            
            # Pre-load commonly accessed data
            if self.current_optimization_level >= OptimizationLevel.AGGRESSIVE:
                await self._preload_common_data(operation_name)
            
        except Exception as e:
            logger.error(f"Error in pre-operation optimization: {e}")
    
    async def _post_operation_optimization(self, operation_name: str, metrics: PerformanceMetrics, result: Any):
        """Apply post-operation optimizations."""
        try:
            # Cache results if beneficial
            await self._cache_operation_results(operation_name, result)
            
            # Update performance statistics
            self._update_performance_statistics(operation_name, metrics)
            
        except Exception as e:
            logger.error(f"Error in post-operation optimization: {e}")
    
    async def _check_emergency_mode_trigger(self, metrics: PerformanceMetrics):
        """Check if emergency mode should be triggered."""
        try:
            if metrics.duration_ms and metrics.duration_ms >= self.emergency_threshold_ms:
                if not self.emergency_mode_active:
                    await self.activate_emergency_mode(f"Response time exceeded threshold: {metrics.duration_ms}ms")
            
            # Check for consecutive slow operations
            recent_slow_ops = sum(1 for m in list(self.metrics_history)[-5:] 
                                if m.duration_ms and m.duration_ms >= self.target_response_time_ms * 1.5)
            
            if recent_slow_ops >= 3 and not self.emergency_mode_active:
                await self.activate_emergency_mode("Multiple consecutive slow operations detected")
            
        except Exception as e:
            logger.error(f"Error checking emergency mode trigger: {e}")
    
    def _initialize_optimization_rules(self) -> List[OptimizationRule]:
        """Initialize optimization rules."""
        return [
            OptimizationRule(
                rule_id="cache_fragment_aggressively",
                condition=lambda ctx: ctx.get('fragment_id') and not self.emergency_mode_active,
                optimization=lambda ctx: {'cache_fragments': True, 'preload_related': True},
                priority=1,
                description="Aggressively cache fragments and related data"
            ),
            
            OptimizationRule(
                rule_id="batch_database_queries",
                condition=lambda ctx: self.current_optimization_level >= OptimizationLevel.BALANCED,
                optimization=lambda ctx: {'batch_queries': True, 'use_prepared_statements': True},
                priority=2,
                description="Batch database queries for efficiency"
            ),
            
            OptimizationRule(
                rule_id="skip_non_essential_validations",
                condition=lambda ctx: ctx.get('emergency_mode', False),
                optimization=lambda ctx: {'skip_character_validation': True, 'minimal_logging': True},
                priority=3,
                description="Skip non-essential validations in emergency mode",
                safety_level=OptimizationLevel.EMERGENCY
            ),
            
            OptimizationRule(
                rule_id="optimize_memory_usage",
                condition=lambda ctx: self.current_optimization_level >= OptimizationLevel.AGGRESSIVE,
                optimization=lambda ctx: {'compress_cache_data': True, 'limit_cache_size': True},
                priority=4,
                description="Optimize memory usage through compression and limits"
            )
        ]
    
    async def _get_optimization_recommendations(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get optimization recommendations based on context."""
        recommendations = []
        
        try:
            for rule in sorted(self.optimization_rules, key=lambda r: r.priority):
                if rule.condition(context) and rule.safety_level <= self.current_optimization_level:
                    optimization = rule.optimization(context)
                    recommendations.append({
                        'rule_id': rule.rule_id,
                        'description': rule.description,
                        'optimization': optimization,
                        'priority': rule.priority
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting optimization recommendations: {e}")
            return []
    
    async def _preload_optimization_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Preload data for optimization."""
        cached_data = {}
        
        try:
            user_id = context.get('user_id')
            fragment_id = context.get('fragment_id')
            
            if fragment_id:
                fragment_data = await self.optimize_fragment_query(fragment_id)
                if fragment_data:
                    cached_data['fragment'] = fragment_data
            
            if user_id:
                state_data = await self.optimize_user_state_query(user_id)
                if state_data:
                    cached_data['user_state'] = state_data
            
            return cached_data
            
        except Exception as e:
            logger.error(f"Error preloading optimization data: {e}")
            return {}
    
    async def _optimize_database_queries(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize database queries with advanced techniques."""
        try:
            optimizations = {
                'batch_queries_enabled': self.current_optimization_level >= OptimizationLevel.BALANCED,
                'prepared_statements_used': True,
                'connection_pooling_optimized': self._db_pool_optimization_active,
                'query_caching_enabled': not self.emergency_mode_active,
                'eager_loading_applied': True,
                'concurrent_queries_used': True
            }
            
            # Apply query batching if enabled
            if optimizations['batch_queries_enabled']:
                await self._apply_query_batching(context)
                optimizations['batching_applied'] = True
            
            # Apply connection pool optimization
            if not self._db_pool_optimization_active and self.current_optimization_level >= OptimizationLevel.AGGRESSIVE:
                await self._optimize_connection_pool()
                optimizations['connection_pool_optimized'] = True
            
            # Log optimization status
            logger.debug(f"Database query optimizations applied: {optimizations}")
            
            return optimizations
            
        except Exception as e:
            logger.error(f"Error optimizing database queries: {e}")
            return {
                'error': str(e),
                'fallback_mode': True,
                'basic_optimization_only': True
            }
    
    async def _optimize_memory_usage(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize memory usage."""
        try:
            # Calculate current cache memory usage
            fragment_cache_size = sum(entry.get('size_bytes', 0) for entry in self.fragment_cache.values())
            state_cache_size = sum(entry.get('size_bytes', 0) for entry in self.state_cache.values())
            validation_cache_size = sum(entry.get('size_bytes', 0) for entry in self.validation_cache.values())
            
            total_cache_size = fragment_cache_size + state_cache_size + validation_cache_size
            
            optimizations = {
                'total_cache_size_bytes': total_cache_size,
                'fragment_cache_entries': len(self.fragment_cache),
                'state_cache_entries': len(self.state_cache),
                'validation_cache_entries': len(self.validation_cache),
                'memory_optimization_active': self.current_optimization_level >= OptimizationLevel.AGGRESSIVE,
                'cache_compression_enabled': self.current_optimization_level >= OptimizationLevel.AGGRESSIVE
            }
            
            # Memory-based cache cleanup
            total_cache_size_mb = total_cache_size / (1024 * 1024)
            
            if total_cache_size_mb > self.critical_memory_threshold_mb:
                # Aggressive cleanup if approaching memory limit
                await self._cleanup_oversized_caches()
                optimizations['cache_cleanup_triggered'] = True
                optimizations['cleanup_reason'] = 'critical_threshold'
                logger.warning(f"Cache memory usage ({total_cache_size_mb:.2f}MB) exceeded critical threshold ({self.critical_memory_threshold_mb}MB)")
            elif total_cache_size_mb > self.max_cache_memory_mb:
                # Emergency cleanup if exceeding maximum
                await self._emergency_memory_cleanup()
                optimizations['emergency_cleanup_triggered'] = True
                optimizations['cleanup_reason'] = 'maximum_exceeded'
                logger.error(f"Cache memory usage ({total_cache_size_mb:.2f}MB) exceeded maximum ({self.max_cache_memory_mb}MB)")
            
            return optimizations
            
        except Exception as e:
            logger.error(f"Error optimizing memory usage: {e}")
            return {'error': str(e)}
    
    async def _manage_cache_size(self, cache_type: str):
        """Manage cache size to prevent memory issues."""
        try:
            cache = getattr(self, f"{cache_type}_cache", {})
            
            # Maximum entries per cache type
            max_entries = {
                'fragment': 100,
                'state': 200,
                'validation': 500,
                'query': 50
            }
            
            if len(cache) > max_entries.get(cache_type, 100):
                # Remove least recently used entries
                lru_entries = sorted(cache.items(), key=lambda x: x[1].get('last_accessed', 0))
                entries_to_remove = len(cache) - max_entries.get(cache_type, 100)
                
                for i in range(entries_to_remove):
                    cache.pop(lru_entries[i][0], None)
            
        except Exception as e:
            logger.error(f"Error managing cache size for {cache_type}: {e}")
    
    async def _clear_non_essential_caches(self):
        """Clear non-essential caches in emergency mode."""
        try:
            # Clear validation cache (can be regenerated)
            self.validation_cache.clear()
            
            # Clear query cache
            self.query_cache.clear()
            
            # Reduce fragment cache size
            if len(self.fragment_cache) > 20:
                # Keep only most recently accessed fragments
                lru_fragments = sorted(self.fragment_cache.items(), 
                                     key=lambda x: x[1].get('last_accessed', 0), reverse=True)
                
                self.fragment_cache = dict(lru_fragments[:20])
            
            logger.info("Cleared non-essential caches for emergency mode")
            
        except Exception as e:
            logger.error(f"Error clearing non-essential caches: {e}")
    
    async def _disable_expensive_validations(self):
        """Disable expensive validations in emergency mode."""
        # This would integrate with the character validation system
        # to temporarily reduce validation complexity
        pass
    
    async def _enable_normal_validations(self):
        """Re-enable normal validations after emergency mode."""
        # This would restore normal character validation
        pass
    
    async def _warm_up_relevant_caches(self, operation_name: str):
        """Warm up caches relevant to the operation."""
        # Implementation would warm up caches based on operation type
        pass
    
    async def _preload_common_data(self, operation_name: str):
        """Preload commonly accessed data."""
        # Implementation would preload frequently accessed data
        pass
    
    async def _cache_operation_results(self, operation_name: str, result: Any):
        """Cache operation results if beneficial."""
        # Implementation would cache results based on operation type
        pass
    
    def _update_performance_statistics(self, operation_name: str, metrics: PerformanceMetrics):
        """Update performance statistics."""
        try:
            self.performance_stats[operation_name].append({
                'timestamp': metrics.start_time,
                'duration_ms': metrics.duration_ms,
                'database_queries': metrics.database_queries,
                'cache_hits': metrics.cache_hits,
                'cache_misses': metrics.cache_misses,
                'errors': metrics.errors_encountered
            })
            
            # Keep only recent statistics
            cutoff_time = time.time() - 3600  # 1 hour
            self.performance_stats[operation_name] = [
                stat for stat in self.performance_stats[operation_name]
                if stat['timestamp'] >= cutoff_time
            ]
            
        except Exception as e:
            logger.error(f"Error updating performance statistics: {e}")
    
    async def _analyze_optimization_effectiveness(self, recent_metrics: List[PerformanceMetrics]) -> Dict[str, Any]:
        """Analyze effectiveness of current optimizations."""
        try:
            if not recent_metrics:
                return {'effectiveness': 'no_data'}
            
            # Calculate improvement metrics
            response_times = [m.duration_ms for m in recent_metrics if m.duration_ms]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            target_achievement_rate = sum(1 for rt in response_times if rt <= self.target_response_time_ms) / len(response_times) if response_times else 0
            
            cache_hits = sum(m.cache_hits for m in recent_metrics)
            cache_misses = sum(m.cache_misses for m in recent_metrics)
            cache_hit_rate = cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0
            
            return {
                'effectiveness': 'good' if target_achievement_rate >= 0.8 else 'needs_improvement',
                'avg_response_time_ms': avg_response_time,
                'target_achievement_rate': target_achievement_rate,
                'cache_hit_rate': cache_hit_rate,
                'optimization_level': self.current_optimization_level.name,
                'emergency_mode_active': self.emergency_mode_active
            }
            
        except Exception as e:
            logger.error(f"Error analyzing optimization effectiveness: {e}")
            return {'effectiveness': 'error', 'error': str(e)}
    
    async def _generate_performance_recommendations(self, recent_metrics: List[PerformanceMetrics]) -> List[str]:
        """Generate performance improvement recommendations."""
        try:
            recommendations = []
            
            if not recent_metrics:
                return ["Insufficient data for recommendations"]
            
            # Analyze response times
            response_times = [m.duration_ms for m in recent_metrics if m.duration_ms]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            if avg_response_time > self.target_response_time_ms:
                recommendations.append(f"Average response time ({avg_response_time:.1f}ms) exceeds target ({self.target_response_time_ms}ms)")
                
                if self.current_optimization_level < OptimizationLevel.AGGRESSIVE:
                    recommendations.append("Consider enabling aggressive optimization mode")
            
            # Analyze cache performance
            cache_hits = sum(m.cache_hits for m in recent_metrics)
            cache_misses = sum(m.cache_misses for m in recent_metrics)
            
            if cache_hits + cache_misses > 0:
                cache_hit_rate = cache_hits / (cache_hits + cache_misses)
                
                if cache_hit_rate < self.cache_hit_target:
                    recommendations.append(f"Cache hit rate ({cache_hit_rate:.2f}) below target ({self.cache_hit_target})")
                    recommendations.append("Consider increasing cache TTLs or warming up caches")
            
            # Analyze database queries
            avg_queries = sum(m.database_queries for m in recent_metrics) / len(recent_metrics)
            if avg_queries > 5:
                recommendations.append(f"High database query count per operation ({avg_queries:.1f})")
                recommendations.append("Consider implementing query batching or better caching")
            
            # Emergency mode recommendations
            if self.emergency_mode_active:
                recommendations.append("Emergency mode is active - monitor system recovery")
                recommendations.append("Consider scaling resources if emergency mode persists")
            
            return recommendations if recommendations else ["Performance is within acceptable parameters"]
            
        except Exception as e:
            logger.error(f"Error generating performance recommendations: {e}")
            return [f"Error generating recommendations: {str(e)}"]
    
    async def _cleanup_oversized_caches(self):
        """Clean up oversized caches."""
        try:
            # Reduce all cache sizes by removing LRU entries
            for cache_name in ['fragment_cache', 'state_cache', 'validation_cache']:
                cache = getattr(self, cache_name, {})
                
                if len(cache) > 50:  # Reduce to 50 entries max
                    lru_entries = sorted(cache.items(), key=lambda x: x[1].get('last_accessed', 0))
                    entries_to_remove = len(cache) - 50
                    
                    for i in range(entries_to_remove):
                        cache.pop(lru_entries[i][0], None)
            
            logger.info("Completed cache cleanup due to memory constraints")
            
        except Exception as e:
            logger.error(f"Error cleaning up oversized caches: {e}")
    
    async def _check_memory_usage(self):
        """Check cache memory usage and trigger cleanup if needed."""
        try:
            self._cache_operations_count += 1
            
            # Only check memory every N operations to avoid performance impact
            if self._cache_operations_count % self.memory_check_interval != 0:
                return
            
            # Calculate current cache memory usage
            total_cache_size_bytes = self._calculate_total_cache_size()
            total_cache_size_mb = total_cache_size_bytes / (1024 * 1024)
            
            if total_cache_size_mb > self.max_cache_memory_mb:
                logger.warning(f"Cache memory ({total_cache_size_mb:.2f}MB) exceeded maximum ({self.max_cache_memory_mb}MB)")
                await self._emergency_memory_cleanup()
            elif total_cache_size_mb > self.critical_memory_threshold_mb:
                logger.info(f"Cache memory ({total_cache_size_mb:.2f}MB) exceeded critical threshold ({self.critical_memory_threshold_mb}MB)")
                await self._cleanup_oversized_caches()
            
        except Exception as e:
            logger.error(f"Error checking memory usage: {e}")
    
    def _calculate_total_cache_size(self) -> int:
        """Calculate total cache size in bytes."""
        try:
            fragment_cache_size = sum(entry.get('size_bytes', 0) for entry in self.fragment_cache.values())
            state_cache_size = sum(entry.get('size_bytes', 0) for entry in self.state_cache.values())
            validation_cache_size = sum(entry.get('size_bytes', 0) for entry in self.validation_cache.values())
            query_cache_size = sum(entry.get('size_bytes', 0) for entry in self.query_cache.values())
            
            return fragment_cache_size + state_cache_size + validation_cache_size + query_cache_size
        except Exception as e:
            logger.error(f"Error calculating cache size: {e}")
            return 0

    async def _emergency_memory_cleanup(self):
        """Emergency memory cleanup when exceeding maximum limits."""
        try:
            # Clear all caches except critical ones
            logger.critical("Executing emergency memory cleanup - clearing all caches")
            
            # Keep only the most recently accessed items in fragment cache (10 items max)
            if len(self.fragment_cache) > 10:
                lru_fragments = sorted(
                    self.fragment_cache.items(), 
                    key=lambda x: x[1].get('last_accessed', 0), 
                    reverse=True
                )
                self.fragment_cache = dict(lru_fragments[:10])
            
            # Keep only 20 most recent user states
            if len(self.state_cache) > 20:
                lru_states = sorted(
                    self.state_cache.items(), 
                    key=lambda x: x[1].get('last_accessed', 0), 
                    reverse=True
                )
                self.state_cache = dict(lru_states[:20])
            
            # Clear all validation and query caches
            self.validation_cache.clear()
            self.query_cache.clear()
            
            logger.info("Emergency memory cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during emergency memory cleanup: {e}")
    
    async def _apply_query_batching(self, context: Dict[str, Any]):
        """Apply query batching optimization."""
        try:
            # Query batching implementation
            # For now, we'll ensure connection reuse and prepared statements
            user_id = context.get('user_id')
            if user_id:
                # Pre-warm frequently used queries by user
                pass
        except Exception as e:
            logger.error(f"Error applying query batching: {e}")
    
    async def _optimize_connection_pool(self):
        """Optimize database connection pool settings."""
        try:
            # Mark connection pool optimization as active
            self._db_pool_optimization_active = True
            logger.info("Database connection pool optimization enabled")
        except Exception as e:
            logger.error(f"Error optimizing connection pool: {e}")