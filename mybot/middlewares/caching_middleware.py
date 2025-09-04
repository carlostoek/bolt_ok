"""Caching middleware for automatic cache integration.

This middleware automatically handles:
- Cache-first lookups for user data
- Cache invalidation on user updates
- Performance monitoring
- Fallback to database when cache unavailable
- Diana character consistency preservation

Key Features:
- Transparent cache integration
- Multi-tenant cache isolation
- Performance metrics collection
- Graceful degradation
"""
import asyncio
import time
import logging
from typing import Callable, Dict, Any, Optional, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from services.redis_caching_service import redis_caching_service
from utils.query_optimization import query_optimizer

logger = logging.getLogger(__name__)


class CachingMiddleware(BaseMiddleware):
    """Middleware for automatic cache integration and performance optimization."""
    
    def __init__(self):
        self.performance_metrics = {
            'cache_enabled_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_response_time': 0.0,
            'total_requests': 0
        }
        
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process request with caching integration."""
        
        # Extract user information
        user = None
        user_id = None
        
        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user
            user_id = user.id if user else None
        
        if not user_id:
            # No user context, skip caching
            return await handler(event, data)
        
        start_time = time.time()
        
        try:
            # Add caching utilities to handler data
            data['cache_service'] = redis_caching_service
            data['cache_enabled'] = redis_caching_service.redis is not None
            
            # Pre-populate cache data if available
            if redis_caching_service.redis:
                await self._populate_cache_data(data, user_id)
            
            # Execute handler
            result = await handler(event, data)
            
            # Post-process cache updates if needed
            if redis_caching_service.redis and 'cache_invalidation_needed' in data:
                await self._handle_cache_invalidation(data, user_id)
            
            # Update performance metrics
            request_time = time.time() - start_time
            await self._update_performance_metrics(request_time, data.get('cache_enabled', False))
            
            return result
            
        except Exception as e:
            request_time = time.time() - start_time
            logger.error(f"❌ Caching middleware error (took {request_time:.3f}s): {e}")
            
            # Still update metrics for failed requests
            await self._update_performance_metrics(request_time, False)
            raise
    
    async def _populate_cache_data(self, data: Dict[str, Any], user_id: int):
        """Pre-populate handler data with cached information.
        
        Args:
            data: Handler data dictionary
            user_id: User identifier
        """
        try:
            # Try to get cached user session
            cached_session = await redis_caching_service.get_cached_user_session(user_id)
            if cached_session:
                data['cached_user_session'] = cached_session
                data['cache_hit_session'] = True
            else:
                data['cache_hit_session'] = False
            
            # Try to get cached narrative progress
            cached_narrative = await redis_caching_service.get_cached_narrative_progress(user_id)
            if cached_narrative:
                data['cached_narrative_progress'] = cached_narrative
                data['cache_hit_narrative'] = True
            else:
                data['cache_hit_narrative'] = False
            
            # Try to get cached mission progress
            cached_missions = await redis_caching_service.get_cached_mission_progress(user_id)
            if cached_missions:
                data['cached_mission_progress'] = cached_missions
                data['cache_hit_missions'] = True
            else:
                data['cache_hit_missions'] = False
            
            # Mark cache data as available
            data['cache_data_available'] = True
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to populate cache data for user {user_id}: {e}")
            data['cache_data_available'] = False
    
    async def _handle_cache_invalidation(self, data: Dict[str, Any], user_id: int):
        """Handle cache invalidation after data updates.
        
        Args:
            data: Handler data with invalidation requirements
            user_id: User identifier
        """
        try:
            invalidation_types = data.get('cache_invalidation_types', [])
            
            if 'all' in invalidation_types:
                # Invalidate all user cache
                invalidated_count = await redis_caching_service.invalidate_user_cache(user_id)
                logger.info(f"🧹 Invalidated all cache for user {user_id}: {invalidated_count} keys")
                
            elif invalidation_types:
                # Selective invalidation
                invalidated_count = await redis_caching_service.invalidate_user_cache(
                    user_id, invalidation_types
                )
                logger.info(f"🧹 Selective cache invalidation for user {user_id}: {invalidated_count} keys")
            
        except Exception as e:
            logger.error(f"❌ Cache invalidation failed for user {user_id}: {e}")
    
    async def _update_performance_metrics(self, request_time: float, cache_enabled: bool):
        """Update performance monitoring metrics.
        
        Args:
            request_time: Request processing time in seconds
            cache_enabled: Whether caching was available
        """
        self.performance_metrics['total_requests'] += 1
        
        if cache_enabled:
            self.performance_metrics['cache_enabled_requests'] += 1
        
        # Update rolling average response time
        total_requests = self.performance_metrics['total_requests']
        current_avg = self.performance_metrics['average_response_time']
        
        self.performance_metrics['average_response_time'] = (
            (current_avg * (total_requests - 1) + request_time) / total_requests
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        total_cache_operations = (
            self.performance_metrics['cache_hits'] + 
            self.performance_metrics['cache_misses']
        )
        
        hit_rate = 0.0
        if total_cache_operations > 0:
            hit_rate = (self.performance_metrics['cache_hits'] / total_cache_operations) * 100
        
        return {
            **self.performance_metrics,
            'cache_hit_rate_percentage': round(hit_rate, 2),
            'average_response_time_ms': round(self.performance_metrics['average_response_time'] * 1000, 2)
        }


class CacheAwareDataService:
    """Service for cache-aware database operations."""
    
    def __init__(self, session: AsyncSession, user_id: int, cache_data: Dict[str, Any]):
        self.session = session
        self.user_id = user_id
        self.cache_data = cache_data
        self.cache_updates_needed = []
    
    async def get_user_narrative_progress(self) -> Dict[str, Any]:
        """Get user narrative progress with cache-first lookup.
        
        Returns:
            User narrative progress data
        """
        # Try cache first
        if self.cache_data.get('cache_hit_narrative'):
            logger.debug(f"✅ Cache hit: narrative progress for user {self.user_id}")
            return self.cache_data['cached_narrative_progress']
        
        # Fallback to database
        logger.debug(f"💿 Cache miss: loading narrative progress from database for user {self.user_id}")
        
        from services.database_optimization_service import database_optimization_service
        
        progress_data = await database_optimization_service.get_optimized_user_narrative_progress(
            self.session, self.user_id
        )
        
        # Cache the result for future requests
        if progress_data and redis_caching_service.redis:
            await redis_caching_service.cache_narrative_progress(self.user_id, progress_data)
        
        return progress_data
    
    async def get_user_mission_progress(self) -> Dict[str, Any]:
        """Get user mission progress with cache-first lookup.
        
        Returns:
            User mission progress data
        """
        # Try cache first
        if self.cache_data.get('cache_hit_missions'):
            logger.debug(f"✅ Cache hit: mission progress for user {self.user_id}")
            return self.cache_data['cached_mission_progress']
        
        # Fallback to database
        logger.debug(f"💿 Cache miss: loading mission progress from database for user {self.user_id}")
        
        from services.database_optimization_service import database_optimization_service
        
        mission_data = await database_optimization_service.get_optimized_mission_progress_aggregation(
            self.session, self.user_id
        )
        
        # Cache the result
        if mission_data and redis_caching_service.redis:
            await redis_caching_service.cache_mission_progress(self.user_id, mission_data)
        
        return mission_data
    
    async def get_user_session_state(self) -> Optional[Dict[str, Any]]:
        """Get user session state with cache-first lookup.
        
        Returns:
            User session state data
        """
        # Try cache first
        if self.cache_data.get('cache_hit_session'):
            logger.debug(f"✅ Cache hit: session state for user {self.user_id}")
            return self.cache_data['cached_user_session']
        
        # Fallback to database query
        logger.debug(f"💿 Cache miss: loading session state from database for user {self.user_id}")
        
        from utils.query_optimization import optimized_queries
        
        result = await self.session.execute(
            optimized_queries.USER_SESSION_STATE,
            {"user_id": self.user_id}
        )
        
        row = result.fetchone()
        if row:
            session_data = {
                'user_id': row.user_id,
                'session_state': row.session_state,
                'menu_position': row.menu_position,
                'preferences': row.preferences,
                'last_interaction': row.last_interaction,
                'character_consistency_score': row.character_consistency_score,
                'role': row.role,
                'vip_expires_at': row.vip_expires_at,
                'points': row.points,
                'level': row.level,
                'narrative_level': row.narrative_level,
                'narrative_tier': row.narrative_tier
            }
            
            # Cache the result
            if redis_caching_service.redis:
                await redis_caching_service.cache_user_session(self.user_id, session_data)
            
            return session_data
        
        return None
    
    def mark_cache_invalidation_needed(self, cache_types: list[str]):
        """Mark that cache invalidation is needed after this request.
        
        Args:
            cache_types: List of cache types to invalidate
        """
        self.cache_updates_needed.extend(cache_types)
    
    def get_cache_invalidation_requirements(self) -> list[str]:
        """Get cache invalidation requirements.
        
        Returns:
            List of cache types that need invalidation
        """
        return list(set(self.cache_updates_needed))


# Factory function to create cache-aware data service
def create_cache_aware_service(
    session: AsyncSession, 
    user_id: int, 
    handler_data: Dict[str, Any]
) -> CacheAwareDataService:
    """Create a cache-aware data service for handlers.
    
    Args:
        session: Database session
        user_id: User identifier
        handler_data: Handler data with cache information
        
    Returns:
        Cache-aware data service instance
    """
    cache_data = {
        'cache_hit_narrative': handler_data.get('cache_hit_narrative', False),
        'cache_hit_missions': handler_data.get('cache_hit_missions', False),
        'cache_hit_session': handler_data.get('cache_hit_session', False),
        'cached_narrative_progress': handler_data.get('cached_narrative_progress'),
        'cached_mission_progress': handler_data.get('cached_mission_progress'),
        'cached_user_session': handler_data.get('cached_user_session')
    }
    
    return CacheAwareDataService(session, user_id, cache_data)


# Global caching middleware instance
caching_middleware = CachingMiddleware()