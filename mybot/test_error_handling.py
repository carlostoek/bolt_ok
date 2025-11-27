"""
Test file to validate error handling and logging functionality
"""
import asyncio
import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import (
    engine, 
    get_db, 
    get_db_session, 
    execute_with_retry,
    Base,
    configure_engine
)
from app.core.sqlite_optimizations import (
    enable_wal_mode, 
    optimize_sqlite_pragmas, 
    integrity_check,
    optimize_sqlite_for_termux
)

# Set up logging to see output
logging.basicConfig(level=logging.INFO)


async def test_basic_connection():
    """Test basic database connection"""
    print("Testing basic database connection...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✓ Basic connection successful")
            return True
    except Exception as e:
        print(f"✗ Basic connection failed: {e}")
        return False


async def test_session_with_error_handling():
    """Test session with error handling"""
    print("Testing session with error handling...")
    try:
        async for db in get_db():
            # Simulate a normal operation
            result = await db.execute(text("SELECT 1"))
            print("✓ Session with get_db() works")
            break
    except Exception as e:
        print(f"✗ Session with get_db() failed: {e}")
        return False

    try:
        async with get_db_session() as db:
            # Simulate a normal operation
            result = await db.execute(text("SELECT 1"))
            print("✓ Session with get_db_session() works")
    except Exception as e:
        print(f"✗ Session with get_db_session() failed: {e}")
        return False
    
    return True


async def test_retry_mechanism():
    """Test the retry mechanism"""
    print("Testing retry mechanism...")
    
    attempt_count = 0
    max_attempts = 2
    
    async def failing_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < max_attempts:
            raise Exception("Simulated failure")
        return "success"
    
    try:
        result = await execute_with_retry(failing_function, max_retries=3)
        if result == "success" and attempt_count == max_attempts:
            print("✓ Retry mechanism works correctly")
        else:
            print(f"✗ Retry mechanism issue: result={result}, attempts={attempt_count}")
            return False
    except Exception as e:
        print(f"✗ Retry mechanism failed: {e}")
        return False
    
    return True


async def test_sqlite_optimizations():
    """Test SQLite optimization functions"""
    print("Testing SQLite optimizations...")
    
    try:
        # Test WAL mode
        wal_result = await enable_wal_mode(engine)
        if wal_result:
            print("✓ WAL mode enabled successfully")
        else:
            print("✗ WAL mode failed")
            return False
        
        # Test PRAGMA optimizations
        pragma_result = await optimize_sqlite_pragmas(engine)
        if pragma_result:
            print("✓ PRAGMA optimizations successful")
        else:
            print("✗ PRAGMA optimizations failed")
            return False
        
        # Test integrity check
        integrity_result = await integrity_check(engine)
        if integrity_result is not None:  # Could be True or False, but not None
            print("✓ Integrity check completed")
        else:
            print("✗ Integrity check failed to execute")
            return False
        
        # Test full optimization
        full_opt_result = await optimize_sqlite_for_termux(engine)
        if full_opt_result:
            print("✓ Full SQLite optimization completed")
        else:
            print("✗ Full SQLite optimization failed")
            return False
            
        return True
    except Exception as e:
        print(f"✗ SQLite optimization test failed: {e}")
        return False


async def test_model_creation():
    """Test that models can be created properly with mixins"""
    print("Testing model creation with mixins...")
    
    # Check that Base has the expected methods
    if hasattr(Base, 'to_dict'):
        print("✓ Base model has to_dict method")
    else:
        print("✗ Base model missing to_dict method")
        return False
    
    return True


async def run_all_tests():
    """Run all tests"""
    print("Starting error handling and logging tests...\n")
    
    tests = [
        test_basic_connection,
        test_session_with_error_handling,
        test_retry_mechanism,
        test_sqlite_optimizations,
        test_model_creation
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
            print()  # Add spacing between tests
        except Exception as e:
            print(f"✗ Test {test.__name__} threw an exception: {e}")
            results.append(False)
            print()
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests completed: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed!")
        return True
    else:
        print("✗ Some tests failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)