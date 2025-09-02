"""Redis caching service for performance optimization.

This service implements a Redis-based caching layer for:
- User session state and Diana menu system
- Narrative fragments and user progress
- Mission progress and gamification data
- Character validation results
- Query result caching

Key Requirements:
- Maintain <2s response time target
- Preserve Diana personality delivery consistency
- Cache invalidation strategies
- Multi-tenant cache isolation
- Fallback to database when cache unavailable
"""
import asyncio
import json
import logging
import pickle
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from contextlib import asynccontextmanager

import aioredis
from aioredis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RedisCachingService:
    """Redis-based caching service for performance optimization."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis: Optional[Redis] = None
        self.connection_pool = None
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }
        
        # Cache TTL settings (in seconds)
        self.ttl_settings = {
            'user_session': 3600,  # 1 hour
            'narrative_progress': 1800,  # 30 minutes
            'mission_progress': 900,  # 15 minutes
            'character_validation': 600,  # 10 minutes
            'user_archetype': 1800,  # 30 minutes
            'query_result': 300,  # 5 minutes
            'lucien_coordination': 60,  # 1 minute (real-time)
            'user_achievements': 1200  # 20 minutes
        }
        
        # Cache key prefixes for multi-tenant isolation
        self.key_prefixes = {
            'user_session': 'diana:session:user:',
            'narrative_progress': 'diana:narrative:user:',
            'mission_progress': 'diana:missions:user:',
            'character_validation': 'diana:character:',
            'user_archetype': 'diana:archetype:user:',
            'query_result': 'diana:query:',
            'lucien_coordination': 'diana:lucien:user:',
            'user_achievements': 'diana:achievements:user:'
        }
    
    async def initialize(self):
        """Initialize Redis connection with optimized pool settings."""
        try:
            # Create connection pool with production settings
            self.connection_pool = aioredis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=50,  # Production connection pool
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            self.redis = aioredis.Redis(connection_pool=self.connection_pool)
            
            # Test connection
            await self.redis.ping()
            
            logger.info("✅ Redis caching service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Redis connection: {e}")
            self.redis = None
            return False
    
    async def close(self):
        """Close Redis connections gracefully."""
        if self.connection_pool:
            await self.connection_pool.disconnect()
            logger.info("✅ Redis connections closed")
    
    def _build_cache_key(self, prefix_type: str, identifier: str, suffix: str = "") -> str:
        """Build cache key with proper prefix and multi-tenant isolation.
        
        Args:
            prefix_type: Type of cache key prefix
            identifier: Primary identifier (usually user_id)
            suffix: Optional suffix for sub-keys
            
        Returns:
            Formatted cache key
        """
        prefix = self.key_prefixes.get(prefix_type, "diana:unknown:")
        key = f"{prefix}{identifier}"
        
        if suffix:
            key += f":{suffix}"
        
        return key
    
    async def _safe_redis_operation(self, operation_name: str, operation_func):
        """Safely execute Redis operation with error handling.
        
        Args:
            operation_name: Name of operation for logging
            operation_func: Async function to execute
            
        Returns:
            Operation result or None if failed
        """
        if not self.redis:
            logger.warning(f"⚠️ Redis not available for {operation_name}")
            return None
        
        try:
            result = await operation_func()
            return result
            
        except Exception as e:
            logger.error(f"❌ Redis {operation_name} failed: {e}")
            self.cache_stats['errors'] += 1
            return None
    
    # User Session Caching
    async def cache_user_session(
        self, 
        user_id: int, 
        session_data: Dict[str, Any]
    ) -> bool:
        """Cache user session state for Diana menu system.
        
        Args:
            user_id: User identifier
            session_data: Session state data
            
        Returns:
            True if cached successfully
        """
        async def operation():
            cache_key = self._build_cache_key('user_session', str(user_id))
            
            # Add timestamp and consistency tracking
            cached_data = {
                **session_data,
                'cached_at': datetime.utcnow().isoformat(),
                'character_consistency_preserved': True
            }
            
            serialized_data = json.dumps(cached_data, default=str)
            await self.redis.setex(
                cache_key,
                self.ttl_settings['user_session'],
                serialized_data
            )
            
            self.cache_stats['sets'] += 1
            logger.debug(f"🔄 Cached user session for user {user_id}")
            return True
        
        result = await self._safe_redis_operation('cache_user_session', operation)
        return result is True
    
    async def get_cached_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve cached user session state.
        
        Args:
            user_id: User identifier
            
        Returns:
            Cached session data or None
        """
        async def operation():
            cache_key = self._build_cache_key('user_session', str(user_id))
            
            cached_data = await self.redis.get(cache_key)
            if not cached_data:
                self.cache_stats['misses'] += 1
                return None
            
            self.cache_stats['hits'] += 1
            session_data = json.loads(cached_data)
            
            logger.debug(f"✅ Retrieved cached session for user {user_id}")
            return session_data
        
        return await self._safe_redis_operation('get_cached_user_session', operation)
    
    # Narrative Progress Caching
    async def cache_narrative_progress(
        self,
        user_id: int,
        progress_data: Dict[str, Any]
    ) -> bool:
        """Cache user narrative progress for fast retrieval.
        
        Args:
            user_id: User identifier
            progress_data: Narrative progress data
            
        Returns:
            True if cached successfully
        """
        async def operation():
            cache_key = self._build_cache_key('narrative_progress', str(user_id))
            
            # Enhance with caching metadata
            cached_data = {
                **progress_data,
                'cached_at': datetime.utcnow().isoformat(),
                'diana_personality_preserved': True,
                'cache_version': '1.0'
            }
            
            serialized_data = json.dumps(cached_data, default=str)
            await self.redis.setex(
                cache_key,
                self.ttl_settings['narrative_progress'],
                serialized_data
            )
            
            self.cache_stats['sets'] += 1
            logger.debug(f"🔄 Cached narrative progress for user {user_id}")
            return True
        
        result = await self._safe_redis_operation('cache_narrative_progress', operation)
        return result is True
    
    async def get_cached_narrative_progress(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve cached narrative progress.
        
        Args:
            user_id: User identifier
            
        Returns:
            Cached progress data or None
        """
        async def operation():
            cache_key = self._build_cache_key('narrative_progress', str(user_id))
            
            cached_data = await self.redis.get(cache_key)
            if not cached_data:
                self.cache_stats['misses'] += 1
                return None
            
            self.cache_stats['hits'] += 1
            progress_data = json.loads(cached_data)
            
            logger.debug(f"✅ Retrieved cached narrative progress for user {user_id}")
            return progress_data
        
        return await self._safe_redis_operation('get_cached_narrative_progress', operation)
    
    # Mission Progress Caching
    async def cache_mission_progress(
        self,
        user_id: int,
        mission_data: Dict[str, Any]
    ) -> bool:
        """Cache user mission progress for gamification system.
        
        Args:
            user_id: User identifier
            mission_data: Mission progress data
            
        Returns:
            True if cached successfully
        """
        async def operation():
            cache_key = self._build_cache_key('mission_progress', str(user_id))
            
            cached_data = {
                **mission_data,
                'cached_at': datetime.utcnow().isoformat(),
                'gamification_data_valid': True
            }
            
            serialized_data = json.dumps(cached_data, default=str)
            await self.redis.setex(
                cache_key,
                self.ttl_settings['mission_progress'],
                serialized_data
            )
            
            self.cache_stats['sets'] += 1
            logger.debug(f"🔄 Cached mission progress for user {user_id}")
            return True
        
        result = await self._safe_redis_operation('cache_mission_progress', operation)
        return result is True
    
    async def get_cached_mission_progress(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve cached mission progress.
        
        Args:
            user_id: User identifier
            
        Returns:
            Cached mission data or None
        """
        async def operation():
            cache_key = self._build_cache_key('mission_progress', str(user_id))
            
            cached_data = await self.redis.get(cache_key)
            if not cached_data:
                self.cache_stats['misses'] += 1
                return None
            
            self.cache_stats['hits'] += 1
            mission_data = json.loads(cached_data)
            
            logger.debug(f"✅ Retrieved cached mission progress for user {user_id}")
            return mission_data
        
        return await self._safe_redis_operation('get_cached_mission_progress', operation)
    
    # Character Validation Caching
    async def cache_character_validation(
        self,
        validation_key: str,
        validation_data: Dict[str, Any]
    ) -> bool:
        """Cache character validation results for Diana consistency.
        
        Args:
            validation_key: Unique key for validation (fragment_id or user_context)
            validation_data: Validation results
            
        Returns:
            True if cached successfully
        """
        async def operation():
            cache_key = self._build_cache_key('character_validation', validation_key)
            
            cached_data = {
                **validation_data,
                'cached_at': datetime.utcnow().isoformat(),
                'validation_preserved': True
            }
            
            serialized_data = json.dumps(cached_data, default=str)
            await self.redis.setex(
                cache_key,
                self.ttl_settings['character_validation'],
                serialized_data
            )
            
            self.cache_stats['sets'] += 1
            logger.debug(f"🔄 Cached character validation for {validation_key}")
            return True
        
        result = await self._safe_redis_operation('cache_character_validation', operation)
        return result is True
    
    async def get_cached_character_validation(self, validation_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached character validation results.
        
        Args:
            validation_key: Validation key
            
        Returns:
            Cached validation data or None
        """
        async def operation():
            cache_key = self._build_cache_key('character_validation', validation_key)
            
            cached_data = await self.redis.get(cache_key)
            if not cached_data:
                self.cache_stats['misses'] += 1
                return None
            
            self.cache_stats['hits'] += 1
            validation_data = json.loads(cached_data)
            
            logger.debug(f"✅ Retrieved cached character validation for {validation_key}")
            return validation_data
        
        return await self._safe_redis_operation('get_cached_character_validation', operation)
    
    # Query Result Caching
    async def cache_query_result(
        self,
        query_key: str,
        result_data: Any,
        custom_ttl: Optional[int] = None
    ) -> bool:
        """Cache database query results for performance optimization.
        
        Args:
            query_key: Unique query identifier
            result_data: Query result data
            custom_ttl: Custom TTL in seconds
            
        Returns:
            True if cached successfully
        """
        async def operation():
            cache_key = self._build_cache_key('query_result', query_key)
            ttl = custom_ttl or self.ttl_settings['query_result']
            
            # Use pickle for complex data structures
            try:
                if isinstance(result_data, (dict, list)):
                    serialized_data = json.dumps(result_data, default=str)
                else:
                    serialized_data = pickle.dumps(result_data)
                    
            except (TypeError, pickle.PickleError):
                # Fallback to JSON for non-pickleable objects
                serialized_data = json.dumps(str(result_data))
            
            await self.redis.setex(cache_key, ttl, serialized_data)
            
            self.cache_stats['sets'] += 1
            logger.debug(f"🔄 Cached query result for {query_key}")
            return True
        
        result = await self._safe_redis_operation('cache_query_result', operation)
        return result is True
    
    async def get_cached_query_result(self, query_key: str) -> Any:
        """Retrieve cached query result.
        
        Args:
            query_key: Query identifier
            
        Returns:
            Cached query result or None
        """
        async def operation():
            cache_key = self._build_cache_key('query_result', query_key)
            
            cached_data = await self.redis.get(cache_key)
            if not cached_data:
                self.cache_stats['misses'] += 1
                return None
            
            self.cache_stats['hits'] += 1
            
            # Try JSON first, then pickle
            try:
                result_data = json.loads(cached_data)
            except json.JSONDecodeError:
                try:
                    result_data = pickle.loads(cached_data)
                except pickle.PickleError:
                    result_data = str(cached_data)
            
            logger.debug(f"✅ Retrieved cached query result for {query_key}")
            return result_data
        
        return await self._safe_redis_operation('get_cached_query_result', operation)
    
    # Cache Invalidation
    async def invalidate_user_cache(self, user_id: int, cache_types: Optional[List[str]] = None) -> int:
        """Invalidate all cache entries for a specific user.
        
        Args:
            user_id: User identifier
            cache_types: Specific cache types to invalidate, or None for all
            
        Returns:
            Number of keys invalidated
        """
        async def operation():
            if cache_types is None:
                cache_types_to_clear = ['user_session', 'narrative_progress', 'mission_progress', 'user_archetype', 'user_achievements']
            else:
                cache_types_to_clear = cache_types
            
            keys_to_delete = []
            for cache_type in cache_types_to_clear:
                cache_key = self._build_cache_key(cache_type, str(user_id))
                keys_to_delete.append(cache_key)
            
            if keys_to_delete:
                deleted_count = await self.redis.delete(*keys_to_delete)
                self.cache_stats['deletes'] += deleted_count
                
                logger.info(f"🧹 Invalidated {deleted_count} cache entries for user {user_id}")
                return deleted_count
            
            return 0
        
        result = await self._safe_redis_operation('invalidate_user_cache', operation)
        return result or 0
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching a pattern.
        
        Args:
            pattern: Redis key pattern (e.g., 'diana:narrative:*')
            
        Returns:
            Number of keys invalidated
        """
        async def operation():
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted_count = await self.redis.delete(*keys)
                self.cache_stats['deletes'] += deleted_count
                
                logger.info(f"🧹 Invalidated {deleted_count} cache entries matching pattern: {pattern}")
                return deleted_count
            
            return 0
        
        result = await self._safe_redis_operation('invalidate_pattern', operation)
        return result or 0
    
    # Cache Health and Monitoring
    async def get_cache_health(self) -> Dict[str, Any]:
        """Get cache health status and statistics.
        
        Returns:
            Cache health information
        """
        async def operation():
            info = await self.redis.info()
            memory_info = await self.redis.info('memory')
            
            # Calculate hit rate
            total_operations = self.cache_stats['hits'] + self.cache_stats['misses']
            hit_rate = round(
                (self.cache_stats['hits'] / max(1, total_operations)) * 100, 2
            )
            
            health_data = {
                'redis_connected': True,
                'cache_stats': {
                    **self.cache_stats,
                    'hit_rate_percentage': hit_rate,
                    'total_operations': total_operations
                },
                'redis_info': {
                    'connected_clients': info.get('connected_clients', 0),
                    'used_memory': memory_info.get('used_memory_human', '0B'),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                }
            }
            
            return health_data
        
        result = await self._safe_redis_operation('get_cache_health', operation)
        
        if result is None:
            return {
                'redis_connected': False,
                'cache_stats': self.cache_stats,
                'redis_info': {}
            }
        
        return result
    
    async def warm_up_cache(self, session: AsyncSession, user_id: int):
        """Pre-warm cache with frequently accessed user data.
        
        Args:
            session: Database session
            user_id: User to warm up cache for
        """
        logger.info(f"🔥 Warming up cache for user {user_id}")
        
        try:
            # Import here to avoid circular dependencies
            from services.database_optimization_service import database_optimization_service
            
            # Warm up narrative progress
            narrative_progress = await database_optimization_service.get_optimized_user_narrative_progress(
                session, user_id
            )
            if narrative_progress:
                await self.cache_narrative_progress(user_id, narrative_progress)
            
            # Warm up mission progress
            mission_progress = await database_optimization_service.get_optimized_mission_progress_aggregation(
                session, user_id
            )
            if mission_progress:
                await self.cache_mission_progress(user_id, mission_progress)
            
            logger.info(f"✅ Cache warmed up for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Cache warm-up failed for user {user_id}: {e}")


# Global Redis caching service instance
redis_caching_service = RedisCachingService()