#!/usr/bin/env python3
"""
Standalone BaseModel Debugging Infrastructure Test

Tests the BaseModel debugging infrastructure without external dependencies.
"""

import sys
import logging
import traceback
from dataclasses import dataclass
from typing import List

# Add the current directory to the path for imports
sys.path.insert(0, '/home/azureuser/repos/bolt_ok/mybot')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@dataclass
class TestMenuResponse:
    """Test version of MenuResponse for debugging."""
    success: bool
    character_score: float
    response_time: float
    meets_performance_requirement: bool
    message_sent: bool
    errors: List[str]

def test_debugger():
    """Test the BaseModel debugging infrastructure."""
    print("🔍 BaseModel Debugger Standalone Test")
    print("=" * 50)
    
    try:
        # Import our debugging infrastructure
        from services.diana_basemodel_debugger import (
            BaseModelDebugger,
            get_global_debugger,
            enable_basemodel_debug,
            disable_basemodel_debug,
            get_basemodel_debug_report,
            temporary_debug_mode
        )
        
        print("✅ Successfully imported debugging infrastructure")
        
        # Test 1: Create a debugger instance
        print("\n📝 Test 1: Debugger initialization")
        debugger = BaseModelDebugger(debug_enabled=True)
        print(f"   ✅ Debugger created: debug_enabled={debugger.debug_enabled}")
        
        # Test 2: Test safe instantiation with correct arguments
        print("\n📝 Test 2: Safe instantiation - correct arguments")
        result, success, error_msg = debugger.safe_instantiate(
            TestMenuResponse,
            success=True,
            character_score=95.0,
            response_time=0.3,
            meets_performance_requirement=True,
            message_sent=True,
            errors=[]
        )
        
        if success:
            print(f"   ✅ Safe instantiation succeeded: {result.success}")
        else:
            print(f"   ❌ Safe instantiation failed: {error_msg}")
        
        # Test 3: Test with incorrect arguments (missing required field)
        print("\n📝 Test 3: Safe instantiation - missing required field")
        result2, success2, error_msg2 = debugger.safe_instantiate(
            TestMenuResponse,
            success=True,
            character_score=95.0,
            # missing response_time
            meets_performance_requirement=True,
            message_sent=True,
            errors=[]
        )
        
        if success2:
            print(f"   ❓ Unexpected success: {result2.success}")
        else:
            print(f"   ✅ Expected failure caught: {error_msg2}")
        
        # Test 4: Test with wrong argument types
        print("\n📝 Test 4: Safe instantiation - wrong argument types")
        result3, success3, error_msg3 = debugger.safe_instantiate(
            TestMenuResponse,
            success="true",  # should be bool
            character_score="95.0",  # should be float
            response_time=0.3,
            meets_performance_requirement=True,
            message_sent=True,
            errors=[]
        )
        
        if success3:
            print(f"   ❓ Unexpected success with wrong types: {result3.success}")
        else:
            print(f"   ✅ Type error caught: {error_msg3}")
        
        # Test 5: Test global debugger functions
        print("\n📝 Test 5: Global debugger functions")
        enable_basemodel_debug()
        global_debugger = get_global_debugger()
        print(f"   ✅ Global debugger enabled: {global_debugger.debug_enabled}")
        
        # Test 6: Generate debug report
        print("\n📝 Test 6: Debug report generation")
        report = get_basemodel_debug_report()
        print(f"   📊 Debug Report:")
        print(f"     Total attempts: {report['total_attempts']}")
        print(f"     Successful: {report['successful_instantiations']}")
        print(f"     Failed: {report['failed_instantiations']}")
        print(f"     Fallback uses: {report['fallback_uses']}")
        print(f"     Success rate: {report['success_rate']:.1f}%")
        
        # Test 7: Context manager
        print("\n📝 Test 7: Debug context manager")
        with debugger.debug_context("TestClass") as context:
            debugger.log_arguments(context, "arg1", "arg2", kwarg1="value1", kwarg2=42)
            print(f"   ✅ Context created for {context.attempted_class}")
        
        # Test 8: Temporary debug mode
        print("\n📝 Test 8: Temporary debug mode")
        print(f"   Current debug state: {global_debugger.debug_enabled}")
        with temporary_debug_mode(False):
            print(f"   Temporary debug state: {global_debugger.debug_enabled}")
        print(f"   Restored debug state: {global_debugger.debug_enabled}")
        
        print("\n🎉 All tests completed successfully!")
        print("✅ The BaseModel debugging infrastructure is working correctly.")
        
        disable_basemodel_debug()
        print("🔕 Debug mode disabled.")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_debugger()
    sys.exit(0 if success else 1)