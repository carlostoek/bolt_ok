"""Advanced caching layer for repository pattern with multiple backend support."""

import logging
import json
import pickle
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """Clear cache entries matching pattern. Returns count of deleted keys."""
        pass


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend with TTL support."""
    
    def __init__(self, max_size: int = 10000):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
        self._access_order: List[str] = []  # For LRU eviction
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if entry.get("expires_at") and datetime.utcnow() > entry["expires_at"]:
            await self.delete(key)
            return None
        
        # Update access order for LRU
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        
        return entry["value"]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in memory cache."""
        try:
            # Calculate expiration time
            expires_at = None
            if ttl:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            
            # Evict if at max size
            if len(self._cache) >= self._max_size and key not in self._cache:
                await self._evict_lru()
            
            self._cache[key] = {
                "value": value,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at
            }
            
            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            return True
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from memory cache."""
        if key in self._cache:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return await self.get(key) is not None
    
    async def clear(self) -> bool:
        """Clear all cache entries."""
        self._cache.clear()
        self._access_order.clear()
        return True
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear cache entries matching pattern."""
        matching_keys = [key for key in self._cache.keys() if pattern in key]
        count = 0
        for key in matching_keys:
            if await self.delete(key):
                count += 1
        return count
    
    async def _evict_lru(self):
        """Evict least recently used entry."""
        if self._access_order:
            lru_key = self._access_order[0]
            await self.delete(lru_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_size = len(self._cache)
        expired_count = 0
        
        now = datetime.utcnow()
        for entry in self._cache.values():
            if entry.get("expires_at") and now > entry["expires_at"]:
                expired_count += 1
        
        return {
            "total_entries": total_size,
            "max_size": self._max_size,
            "expired_entries": expired_count,
            "utilization": (total_size / self._max_size) * 100 if self._max_size > 0 else 0
        }


class RedisCacheBackend(CacheBackend):
    """Redis cache backend (requires aioredis)."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", key_prefix: str = "bot_cache"):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self._redis = None
        self._connected = False
    
    async def _connect(self):
        """Connect to Redis."""
        if self._connected:
            return
        
        try:
            import aioredis
            self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            await self._redis.ping()
            self._connected = True
            logger.info("Connected to Redis cache backend")
        except ImportError:
            raise ImportError("aioredis package required for Redis cache backend")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _make_key(self, key: str) -> str:
        """Create prefixed key."""
        return f"{self.key_prefix}:{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        await self._connect()
        try:
            data = await self._redis.get(self._make_key(key))
            if data is None:
                return None
            return pickle.loads(data.encode('latin1'))
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache."""
        await self._connect()
        try:
            serialized_value = pickle.dumps(value).decode('latin1')
            if ttl:
                await self._redis.setex(self._make_key(key), ttl, serialized_value)
            else:
                await self._redis.set(self._make_key(key), serialized_value)
            return True
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache."""
        await self._connect()
        try:
            result = await self._redis.delete(self._make_key(key))
            return result > 0
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        await self._connect()
        try:
            result = await self._redis.exists(self._make_key(key))
            return result > 0
        except Exception as e:
            logger.error(f"Failed to check cache key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all cache entries with our prefix."""
        await self._connect()
        try:
            keys = await self._redis.keys(f"{self.key_prefix}:*")
            if keys:
                await self._redis.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear cache entries matching pattern."""
        await self._connect()
        try:
            keys = await self._redis.keys(f"{self.key_prefix}:*{pattern}*")
            if keys:
                await self._redis.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            logger.error(f"Failed to clear cache pattern {pattern}: {e}")
            return 0


class CacheLayer:
    """Main cache layer with multiple backend support and advanced features."""
    
    def __init__(self, backend: CacheBackend, default_ttl: int = 300):
        self.backend = backend
        self.default_ttl = default_ttl
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments."""
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (int, str)):
                key_parts.append(str(arg))
            else:
                # Hash complex objects
                key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])
        
        # Add keyword arguments
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            kwargs_str = json.dumps(sorted_kwargs, sort_keys=True)
            key_parts.append(hashlib.md5(kwargs_str.encode()).hexdigest()[:8])
        
        return ":".join(key_parts)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            result = await self.backend.get(key)
            if result is not None:
                self._stats["hits"] += 1
            else:
                self._stats["misses"] += 1
            return result
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self._stats["errors"] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            ttl = ttl or self.default_ttl
            result = await self.backend.set(key, value, ttl)
            if result:
                self._stats["sets"] += 1
            return result
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self._stats["errors"] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            result = await self.backend.delete(key)
            if result:
                self._stats["deletes"] += 1
            return result
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            self._stats["errors"] += 1
            return False
    
    async def get_or_set(self, key: str, factory: Callable, ttl: Optional[int] = None) -> Any:
        """Get value from cache or set it using factory function."""
        value = await self.get(key)
        if value is not None:
            return value
        
        # Generate value using factory
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()
        
        # Cache the value
        await self.set(key, value, ttl)
        return value
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache keys matching pattern."""
        try:
            count = await self.backend.clear_pattern(pattern)
            self._stats["deletes"] += count
            return count
        except Exception as e:
            logger.error(f"Cache invalidate pattern error for {pattern}: {e}")
            self._stats["errors"] += 1
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "sets": self._stats["sets"],
            "deletes": self._stats["deletes"],
            "errors": self._stats["errors"],
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests
        }
        
        # Add backend-specific stats if available
        if hasattr(self.backend, 'get_stats'):
            stats["backend"] = self.backend.get_stats()
        
        return stats
    
    def reset_stats(self):
        """Reset cache statistics."""
        self._stats = {key: 0 for key in self._stats}
    
    @asynccontextmanager
    async def batch_operations(self):
        """Context manager for batch cache operations."""
        # Could be enhanced to support true batch operations in Redis
        yield self


def cache_result(ttl: int = 300, key_prefix: str = None, skip_args: List[int] = None):
    """Decorator to cache method results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Skip if no cache layer available
            if not hasattr(self, '_cache_layer') or self._cache_layer is None:
                return await func(self, *args, **kwargs)
            
            # Generate cache key
            prefix = key_prefix or f"{self.__class__.__name__}.{func.__name__}"
            
            # Filter out arguments to skip
            filtered_args = args
            if skip_args:
                filtered_args = tuple(
                    arg for i, arg in enumerate(args) 
                    if i not in skip_args
                )
            
            cache_key = self._cache_layer._generate_key(prefix, *filtered_args, **kwargs)
            
            # Try to get from cache
            result = await self._cache_layer.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result
            
            # Execute function and cache result
            result = await func(self, *args, **kwargs)
            await self._cache_layer.set(cache_key, result, ttl)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern_template: str):
    """Decorator to invalidate cache patterns after method execution."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            result = await func(self, *args, **kwargs)
            
            # Invalidate cache if cache layer is available
            if hasattr(self, '_cache_layer') and self._cache_layer is not None:
                # Replace placeholders in pattern with actual values
                pattern = pattern_template
                if "{class}" in pattern:
                    pattern = pattern.replace("{class}", self.__class__.__name__)
                if "{method}" in pattern:
                    pattern = pattern.replace("{method}", func.__name__)
                
                count = await self._cache_layer.invalidate_pattern(pattern)
                if count > 0:
                    logger.debug(f"Invalidated {count} cache entries matching pattern: {pattern}")
            
            return result
        return wrapper
    return decorator


# Enhanced cache mixin for repositories
class CacheableMixin:
    """Mixin to add caching capabilities to repository classes."""
    
    def __init__(self, *args, cache_layer: Optional[CacheLayer] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache_layer = cache_layer
    
    def set_cache_layer(self, cache_layer: CacheLayer):
        """Set the cache layer for this repository."""
        self._cache_layer = cache_layer
    
    async def cache_warm_up(self, patterns: List[str] = None):
        """Warm up cache with commonly accessed data."""
        if not self._cache_layer:
            return
        
        logger.info(f"Warming up cache for {self.__class__.__name__}")
        
        # Default warm-up patterns for common queries
        if patterns is None:
            patterns = ["get_active_", "get_all_", "count_"]
        
        # This could be enhanced to actually call common methods
        # For now, it's a placeholder for future implementation
        pass
    
    async def cache_health_check(self) -> Dict[str, Any]:
        """Check cache health and performance."""
        if not self._cache_layer:
            return {"status": "no_cache", "message": "No cache layer configured"}
        
        try:
            # Test basic cache operations
            test_key = f"health_check_{self.__class__.__name__}"
            test_value = {"timestamp": datetime.utcnow().isoformat()}
            
            # Test set
            set_result = await self._cache_layer.set(test_key, test_value, 60)
            if not set_result:
                return {"status": "error", "message": "Failed to set test value"}
            
            # Test get
            get_result = await self._cache_layer.get(test_key)
            if get_result != test_value:
                return {"status": "error", "message": "Failed to retrieve test value"}
            
            # Test delete
            delete_result = await self._cache_layer.delete(test_key)
            if not delete_result:
                return {"status": "warning", "message": "Failed to delete test value"}
            
            stats = self._cache_layer.get_stats()
            return {
                "status": "healthy",
                "message": "Cache is working properly",
                "stats": stats
            }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Cache health check failed: {e}"
            }


# Global cache layer instance
_global_cache_layer: Optional[CacheLayer] = None


def get_cache_layer() -> Optional[CacheLayer]:
    """Get the global cache layer instance."""
    return _global_cache_layer


def set_cache_layer(cache_layer: CacheLayer):
    """Set the global cache layer instance."""
    global _global_cache_layer
    _global_cache_layer = cache_layer


def create_memory_cache(max_size: int = 10000, default_ttl: int = 300) -> CacheLayer:
    """Create memory cache layer."""
    backend = MemoryCacheBackend(max_size=max_size)
    return CacheLayer(backend=backend, default_ttl=default_ttl)


def create_redis_cache(redis_url: str = "redis://localhost:6379", 
                      key_prefix: str = "bot_cache", 
                      default_ttl: int = 300) -> CacheLayer:
    """Create Redis cache layer."""
    backend = RedisCacheBackend(redis_url=redis_url, key_prefix=key_prefix)
    return CacheLayer(backend=backend, default_ttl=default_ttl)