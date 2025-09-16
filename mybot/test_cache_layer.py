"""
Test script for the analytics caching layer.
Verifies that the caching implementation works correctly.
"""
import asyncio
import logging
from services.cache_service import CacheService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_caching_layer():
    """Test the analytics caching layer implementation."""
    logger.info("Testing analytics caching layer...")
    
    # Test in-memory cache service
    cache_service = CacheService(use_redis=False)
    
    # Test cache operations
    logger.info("Testing cache operations...")
    
    # Test set and get
    await cache_service.set("test", "key1", {"data": "value1"}, ttl=10)
    result = await cache_service.get("test", "key1")
    assert result == {"data": "value1"}, f"Expected {{'data': 'value1'}}, got {result}"
    logger.info("✓ Set/Get test passed")
    
    # Test cache stats
    stats = cache_service.get_stats()
    assert stats["backend"] == "memory", f"Expected 'memory', got {stats['backend']}"
    logger.info("✓ Cache stats test passed")
    
    # Test delete
    await cache_service.delete("test", "key1")
    result = await cache_service.get("test", "key1")
    assert result is None, f"Expected None, got {result}"
    logger.info("✓ Delete test passed")
    
    # Test clear prefix
    await cache_service.set("test", "key1", {"data": "value1"}, ttl=10)
    await cache_service.set("test", "key2", {"data": "value2"}, ttl=10)
    await cache_service.clear_prefix("test")
    result1 = await cache_service.get("test", "key1")
    result2 = await cache_service.get("test", "key2")
    assert result1 is None and result2 is None, "Expected None for both keys after clear_prefix"
    logger.info("✓ Clear prefix test passed")
    
    logger.info("All cache service tests passed!")

if __name__ == "__main__":
    asyncio.run(test_caching_layer())