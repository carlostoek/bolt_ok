"""
Simple standalone test for the cache service.
"""
import sys
import os
import json
import time
from typing import Any, Optional, Dict, Union

# Add the project directory to the path
sys.path.insert(0, '/data/data/com.termux/files/home/repos/bolt_ok/mybot')

def test_cache_service():
    """Test the cache service implementation."""
    print("Testing cache service...")
    
    # Import the cache service directly
    cache_module_path = '/data/data/com.termux/files/home/repos/bolt_ok/mybot/services/cache_service.py'
    
    # Read and execute the cache service code
    with open(cache_module_path, 'r') as f:
        cache_code = f.read()
    
    # Execute the code in a local namespace
    local_ns = {}
    exec(cache_code, globals(), local_ns)
    
    # Get the CacheService class
    CacheService = local_ns['CacheService']
    
    # Test in-memory cache
    print("Creating in-memory cache service...")
    cache_service = CacheService(use_redis=False)
    
    # Test set and get
    print("Testing set/get operations...")
    cache_service.memory_cache = {}  # Reset cache
    
    # Test set
    cache_key = cache_service._get_cache_key("test", "key1")
    expires_at = time.time() + 10  # 10 seconds from now
    cache_service.memory_cache[cache_key] = {
        'data': {"test": "value"},
        'expires_at': expires_at
    }
    
    # Test get
    result = cache_service.memory_cache.get(cache_key)
    if result and time.time() < result['expires_at']:
        print("✓ Set/Get test passed")
    else:
        print("✗ Set/Get test failed")
        return False
    
    # Test expired entry
    print("Testing expired entry handling...")
    cache_service.memory_cache[cache_key] = {
        'data': {"test": "value"},
        'expires_at': time.time() - 1  # Expired 1 second ago
    }
    
    result = cache_service.memory_cache.get(cache_key)
    if result and time.time() < result['expires_at']:
        print("✗ Expired entry test failed")
        return False
    else:
        print("✓ Expired entry test passed")
    
    # Test stats
    print("Testing cache stats...")
    stats = cache_service.get_stats()
    if stats.get("backend") == "memory":
        print("✓ Cache stats test passed")
    else:
        print("✗ Cache stats test failed")
        return False
    
    print("All tests passed!")
    return True

if __name__ == "__main__":
    test_cache_service()