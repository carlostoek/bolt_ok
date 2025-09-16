"""
Cache service for analytics data caching.
Implements both in-memory caching and Redis caching (if available).
"""
import logging
import json
import time
from typing import Any, Optional, Dict, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Try to import Redis, but make it optional
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

class CacheService:
    """
    A flexible cache service that can use either in-memory storage or Redis.
    Implements requirement for analytics data caching layer.
    """
    
    def __init__(self, use_redis: bool = False, redis_host: str = 'localhost', redis_port: int = 6379, 
                 redis_db: int = 0, default_ttl: int = 300):
        """
        Initialize the cache service.
        
        Args:
            use_redis: Whether to use Redis for caching (if available)
            redis_host: Redis host
            redis_port: Redis port
            redis_db: Redis database number
            default_ttl: Default time-to-live in seconds (5 minutes)
        """
        self.default_ttl = default_ttl
        self.use_redis = use_redis and REDIS_AVAILABLE
        
        if self.use_redis:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis cache: {e}. Falling back to in-memory cache.")
                self.use_redis = False
                self.redis_client = None
        
        # In-memory cache as fallback
        if not self.use_redis:
            self.memory_cache: Dict[str, Dict[str, Any]] = {}
            logger.info("In-memory cache initialized")
    
    def _get_cache_key(self, prefix: str, key: str) -> str:
        """Generate a cache key with prefix."""
        return f"{prefix}:{key}"
    
    async def get(self, prefix: str, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            prefix: Cache key prefix (e.g., 'fragment_metrics')
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        cache_key = self._get_cache_key(prefix, key)
        
        if self.use_redis:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
                return None
            except Exception as e:
                logger.error(f"Error getting from Redis cache: {e}")
                return None
        else:
            # In-memory cache
            if cache_key in self.memory_cache:
                cached_entry = self.memory_cache[cache_key]
                if time.time() < cached_entry['expires_at']:
                    return cached_entry['data']
                else:
                    # Remove expired entry
                    del self.memory_cache[cache_key]
            return None
    
    async def set(self, prefix: str, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in cache.
        
        Args:
            prefix: Cache key prefix
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = self._get_cache_key(prefix, key)
        expires_in = ttl if ttl is not None else self.default_ttl
        
        try:
            if self.use_redis:
                # Store in Redis
                serialized_value = json.dumps(value, default=str)
                result = self.redis_client.setex(
                    cache_key, 
                    expires_in, 
                    serialized_value
                )
                return result
            else:
                # Store in memory
                expires_at = time.time() + expires_in
                self.memory_cache[cache_key] = {
                    'data': value,
                    'expires_at': expires_at
                }
                return True
        except Exception as e:
            logger.error(f"Error setting cache value: {e}")
            return False
    
    async def delete(self, prefix: str, key: str) -> bool:
        """
        Delete a value from cache.
        
        Args:
            prefix: Cache key prefix
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = self._get_cache_key(prefix, key)
        
        try:
            if self.use_redis:
                result = self.redis_client.delete(cache_key)
                return result > 0
            else:
                if cache_key in self.memory_cache:
                    del self.memory_cache[cache_key]
                return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False
    
    async def clear_prefix(self, prefix: str) -> bool:
        """
        Clear all cache entries with a specific prefix.
        
        Args:
            prefix: Cache key prefix to clear
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.use_redis:
                # Get all keys with this prefix and delete them
                pattern = f"{prefix}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                return True
            else:
                # Remove all entries with this prefix from memory
                keys_to_delete = [
                    key for key in self.memory_cache.keys() 
                    if key.startswith(f"{prefix}:")
                ]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                return True
        except Exception as e:
            logger.error(f"Error clearing cache prefix: {e}")
            return False
    
    async def clear_all(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.use_redis:
                self.redis_client.flushdb()
                return True
            else:
                self.memory_cache.clear()
                return True
        except Exception as e:
            logger.error(f"Error clearing all cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if self.use_redis:
            try:
                info = self.redis_client.info()
                return {
                    'backend': 'redis',
                    'used_memory': info.get('used_memory_human', 'N/A'),
                    'connected_clients': info.get('connected_clients', 'N/A'),
                    'total_commands_processed': info.get('total_commands_processed', 'N/A')
                }
            except Exception as e:
                logger.error(f"Error getting Redis stats: {e}")
                return {'backend': 'redis', 'error': str(e)}
        else:
            # Count non-expired entries
            valid_entries = 0
            now = time.time()
            for entry in self.memory_cache.values():
                if now < entry['expires_at']:
                    valid_entries += 1
            
            return {
                'backend': 'memory',
                'entries': valid_entries,
                'total_entries': len(self.memory_cache)
            }