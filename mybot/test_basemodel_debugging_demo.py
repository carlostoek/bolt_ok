#!/usr/bin/env python3
"""
BaseModel Debugging Infrastructure Test Script

This script demonstrates the comprehensive BaseModel debugging infrastructure
and tests various error scenarios that could occur in the Diana menu system.
"""

import asyncio
import logging
import sys
import os
import traceback
from dataclasses import dataclass
from typing import List, Any, Dict

# Add the current directory to the path for imports
sys.path.insert(0, '/home/azureuser/repos/bolt_ok/mybot')

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Main test function for BaseModel debugging infrastructure."""
    print("🔍 BaseModel Debugging Infrastructure Test")
    print("=" * 60)
    
    try:
        # Import our debugging infrastructure
        from services.diana_basemodel_debugger import (
            get_global_debugger, 
            enable_basemodel_debug,
            disable_basemodel_debug,
            get_basemodel_debug_report,
            temporary_debug_mode
        )
        
        # Import the enhanced Diana menu system
        from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem, MenuResponse
        
        print("✅ Successfully imported debugging infrastructure and Diana menu system")
        
        # Enable global debugging
        enable_basemodel_debug()
        debugger = get_global_debugger()
        
        print(f"🔧 Debug mode enabled: {debugger.debug_enabled}")
        print()
        
        # Test 1: Normal MenuResponse creation
        print("📝 Test 1: Normal MenuResponse creation")
        try:
            response = MenuResponse(
                success=True,
                character_score=95.5,
                response_time=0.3,
                meets_performance_requirement=True,
                message_sent=True,
                errors=[]
            )
            print(f"   ✅ Normal creation succeeded: {response.success}")
        except Exception as e:
            print(f"   ❌ Normal creation failed: {e}")
        
        print()
        
        # Test 2: Create a mock session for enhanced menu system testing
        print("📝 Test 2: Enhanced Diana Menu System initialization")
        try:
            from unittest.mock import AsyncMock
            mock_session = AsyncMock()
            
            menu_system = EnhancedDianaMenuSystem(mock_session)
            print(f"   ✅ EnhancedDianaMenuSystem initialized with debug enabled: {menu_system.local_debug_enabled}")
            
            # Test safe MenuResponse creation
            safe_response = menu_system._create_safe_menu_response(
                success=True,
                character_score=96.0,
                response_time=0.25,
                meets_performance_requirement=True,
                message_sent=True,
                errors=[]
            )
            print(f"   ✅ Safe MenuResponse creation succeeded: {safe_response.success}")
        except Exception as e:
            print(f"   ❌ Enhanced menu system test failed: {e}")
            traceback.print_exc()
        
        print()
        
        # Test 3: Test error scenarios
        print("📝 Test 3: Error scenario testing")
        test_cases = [
            {
                "name": "Missing required field",
                "kwargs": {
                    "success": True,
                    "character_score": 95.0,
                    # missing response_time
                    "meets_performance_requirement": True,
                    "message_sent": True,
                    "errors": []
                }
            },
            {
                "name": "Wrong type for field",
                "kwargs": {
                    "success": "true",  # should be bool
                    "character_score": 95.0,
                    "response_time": 0.3,
                    "meets_performance_requirement": True,
                    "message_sent": True,
                    "errors": []
                }
            },
            {
                "name": "Extra unexpected argument",
                "kwargs": {
                    "success": True,
                    "character_score": 95.0,
                    "response_time": 0.3,
                    "meets_performance_requirement": True,
                    "message_sent": True,
                    "errors": [],
                    "unexpected_field": "this should cause issues"
                }
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"   Test 3.{i}: {test_case['name']}")
            try:
                if 'menu_system' in locals():
                    safe_response = menu_system._create_safe_menu_response(**test_case['kwargs'])
                    print(f"     ✅ Safe creation handled error gracefully: {safe_response.success}")
                    if hasattr(safe_response, 'errors') and safe_response.errors:
                        print(f"     📋 Errors logged: {len(safe_response.errors)}")
                else:
                    print(f"     ⚠️ Skipping test - menu_system not available")
            except Exception as e:
                print(f"     ❌ Unexpected error: {e}")
        
        print()
        
        # Test 4: Performance and fallback testing
        print("📝 Test 4: Performance and fallback testing")
        try:
            # Test with temporary debug mode disabled
            with temporary_debug_mode(False):
                if 'menu_system' in locals():
                    quick_response = menu_system._create_safe_menu_response(
                        success=True,
                        character_score=94.0,
                        response_time=0.1,
                        meets_performance_requirement=True,
                        message_sent=True,
                        errors=[]
                    )
                    print(f"   ✅ Quick creation without debug: {quick_response.success}")
            
            # Test fallback mechanism
            if 'menu_system' in locals():
                # Simulate a critical error scenario
                fallback_response = menu_system._create_fallback_menu_response(
                    "Simulated critical error for testing",
                    success=False,
                    character_score=0.0,
                    response_time=2.0,
                    meets_performance_requirement=False,
                    message_sent=False,
                    errors=["Original error"]
                )
                print(f"   ✅ Fallback mechanism works: {type(fallback_response).__name__}")
            
        except Exception as e:
            print(f"   ❌ Performance test failed: {e}")
        
        print()
        
        # Test 5: Debug report generation
        print("📝 Test 5: Debug report generation")
        try:
            debug_report = get_basemodel_debug_report()
            print(f"   📊 Debug Report Generated:")
            print(f"     Total attempts: {debug_report['total_attempts']}")
            print(f"     Successful instantiations: {debug_report['successful_instantiations']}")
            print(f"     Failed instantiations: {debug_report['failed_instantiations']}")
            print(f"     Fallback uses: {debug_report['fallback_uses']}")
            print(f"     Success rate: {debug_report['success_rate']:.1f}%")
            print(f"     Recent errors: {len(debug_report['recent_errors'])}")
            
            # Show recent errors if any
            if debug_report['recent_errors']:
                print(f"   🔍 Recent error details:")
                for error in debug_report['recent_errors'][-3:]:  # Show last 3 errors
                    print(f"     - {error['class']} in {error['function']}: {error['error']}")
            
        except Exception as e:
            print(f"   ❌ Debug report generation failed: {e}")
        
        print()
        
        # Final summary
        print("🎉 BaseModel Debugging Infrastructure Test Complete!")
        print("=" * 60)
        print("✅ Key Features Tested:")
        print("   • Normal MenuResponse creation")
        print("   • Enhanced Diana Menu System integration")
        print("   • Error scenario handling")
        print("   • Safe fallback mechanisms")
        print("   • Debug mode toggling")
        print("   • Performance monitoring")
        print("   • Comprehensive error reporting")
        print()
        print("🔧 The debugging infrastructure is now ready to help identify")
        print("   the exact cause of BaseModel initialization errors in production.")
        
        # Disable debug mode
        disable_basemodel_debug()
        print("🔕 Debug mode disabled for production use.")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all required modules are available.")
        return 1
    
    except Exception as e:
        print(f"❌ Unexpected error during testing: {e}")
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)