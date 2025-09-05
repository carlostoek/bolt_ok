#!/usr/bin/env python3
"""
Focused BaseModel Error Test

This script focuses specifically on the BaseModel initialization issues
in the Diana menu system without requiring full bot dependencies.
"""

import sys
import traceback
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_basemodel_creation():
    """Test BaseModel creation patterns that are failing."""
    print("🔍 Testing BaseModel Creation Patterns")
    print("=" * 50)
    
    results = []
    
    # Test 1: Basic dataclass creation
    print("\n📝 Test 1: Basic dataclass creation")
    try:
        @dataclass
        class TestMenuResponse:
            success: bool
            character_score: float
            response_time: float
            meets_performance_requirement: bool
            message_sent: bool
            errors: List[str]
            
            def __post_init__(self):
                """Post-initialization validation."""
                if not isinstance(self.errors, list):
                    self.errors = []
        
        # Test normal creation
        response1 = TestMenuResponse(
            success=True,
            character_score=95.5,
            response_time=0.3,
            meets_performance_requirement=True,
            message_sent=True,
            errors=[]
        )
        
        print(f"   ✅ Normal creation successful: {response1.success}")
        results.append({'test': 'normal_creation', 'success': True})
        
        # Test creation with potential issues
        response2 = TestMenuResponse(
            success=False,
            character_score=0.0,
            response_time=1.0,
            meets_performance_requirement=False,
            message_sent=False,
            errors=["Test error"]
        )
        
        print(f"   ✅ Error scenario creation successful: {response2.success}")
        results.append({'test': 'error_scenario', 'success': True})
        
    except Exception as e:
        print(f"   ❌ Basic dataclass test failed: {e}")
        traceback.print_exc()
        results.append({'test': 'basic_dataclass', 'success': False, 'error': str(e)})
    
    # Test 2: Test with the actual MenuResponse if available
    print("\n📝 Test 2: Actual MenuResponse testing")
    try:
        # Try to import the actual MenuResponse
        try:
            from services.enhanced_diana_menu_system import MenuResponse
            print("   ℹ️ MenuResponse class imported successfully")
            
            # Test creation patterns
            test_cases = [
                {
                    'name': 'Standard success',
                    'kwargs': {
                        'success': True,
                        'character_score': 95.5,
                        'response_time': 0.3,
                        'meets_performance_requirement': True,
                        'message_sent': True,
                        'errors': []
                    }
                },
                {
                    'name': 'Standard failure',
                    'kwargs': {
                        'success': False,
                        'character_score': 0.0,
                        'response_time': 1.0,
                        'meets_performance_requirement': False,
                        'message_sent': False,
                        'errors': ["Test error"]
                    }
                }
            ]
            
            for case in test_cases:
                try:
                    response = MenuResponse(**case['kwargs'])
                    print(f"   ✅ {case['name']}: Success={response.success}")
                    results.append({'test': f"menuresponse_{case['name'].lower()}", 'success': True})
                except Exception as e:
                    print(f"   ❌ {case['name']}: {e}")
                    results.append({'test': f"menuresponse_{case['name'].lower()}", 'success': False, 'error': str(e)})
                    
                    # Analyze the error
                    print(f"      Error type: {type(e).__name__}")
                    print(f"      Error message: {str(e)}")
                    if "takes 1 positional argument but" in str(e):
                        print("      🔍 This is the specific BaseModel initialization error!")
        
        except ImportError as ie:
            print(f"   ⚠️ Could not import MenuResponse: {ie}")
            results.append({'test': 'menuresponse_import', 'success': False, 'error': str(ie)})
        
    except Exception as e:
        print(f"   ❌ MenuResponse testing failed: {e}")
        results.append({'test': 'menuresponse_testing', 'success': False, 'error': str(e)})
    
    # Test 3: Check the debugger infrastructure
    print("\n📝 Test 3: Debugger infrastructure")
    try:
        from services.diana_basemodel_debugger import (
            get_global_debugger,
            BaseModelDebugger,
            safe_menu_response
        )
        
        debugger = get_global_debugger()
        print(f"   ✅ Debugger available: enabled={debugger.debug_enabled}")
        
        # Test safe instantiation
        try:
            from services.enhanced_diana_menu_system import MenuResponse
            
            result, success, error_msg = debugger.safe_instantiate(
                MenuResponse,
                success=True,
                character_score=95.0,
                response_time=0.3,
                meets_performance_requirement=True,
                message_sent=True,
                errors=[]
            )
            
            if success:
                print(f"   ✅ Safe instantiation successful: {result.success}")
                results.append({'test': 'safe_instantiation', 'success': True})
            else:
                print(f"   ❌ Safe instantiation failed: {error_msg}")
                results.append({'test': 'safe_instantiation', 'success': False, 'error': error_msg})
        
        except Exception as e:
            print(f"   ⚠️ Safe instantiation test failed: {e}")
            results.append({'test': 'safe_instantiation', 'success': False, 'error': str(e)})
        
    except ImportError as ie:
        print(f"   ⚠️ Could not import debugger: {ie}")
        results.append({'test': 'debugger_import', 'success': False, 'error': str(ie)})
    
    # Test 4: Mock session test
    print("\n📝 Test 4: Mock session dependency test")
    try:
        from unittest.mock import AsyncMock
        
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()
        mock_session.is_active = True
        
        # Try to create enhanced menu system
        try:
            from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem
            
            menu_system = EnhancedDianaMenuSystem(mock_session)
            print(f"   ✅ EnhancedDianaMenuSystem created with mock session")
            
            # Test safe menu response creation
            safe_response = menu_system._create_safe_menu_response(
                success=True,
                character_score=95.0,
                response_time=0.3,
                meets_performance_requirement=True,
                message_sent=True,
                errors=[]
            )
            
            print(f"   ✅ Safe menu response created: {safe_response.success}")
            results.append({'test': 'mock_session', 'success': True})
            
        except Exception as e:
            print(f"   ❌ Mock session test failed: {e}")
            traceback.print_exc()
            results.append({'test': 'mock_session', 'success': False, 'error': str(e)})
    
    except Exception as e:
        print(f"   ❌ Mock session setup failed: {e}")
        results.append({'test': 'mock_session_setup', 'success': False, 'error': str(e)})
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 30)
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    
    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {total_tests - successful_tests}")
    
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"  {status} {result['test']}")
        if 'error' in result:
            print(f"    Error: {result['error']}")
    
    return successful_tests == total_tests

def analyze_specific_lines():
    """Analyze the specific lines mentioned in the error tracking requirements."""
    print("\n🔍 Analyzing Specific Problem Lines")
    print("=" * 40)
    
    try:
        # Read the enhanced_diana_menu_system.py file
        from pathlib import Path
        
        menu_file = Path("services/enhanced_diana_menu_system.py")
        if not menu_file.exists():
            print("❌ Enhanced Diana menu system file not found")
            return
        
        print("📖 Reading enhanced_diana_menu_system.py...")
        
        with open(menu_file, 'r') as f:
            lines = f.readlines()
        
        # Check the problematic lines: 567, 626, 681, 751
        problematic_lines = [567, 626, 681, 751]
        
        for line_num in problematic_lines:
            if line_num <= len(lines):
                line_content = lines[line_num - 1].strip()
                print(f"\n🔍 Line {line_num}:")
                print(f"   Content: {line_content}")
                
                # Look for BaseModel instantiation patterns
                if any(keyword in line_content.lower() for keyword in ['menuresponse', '__init__', 'response', 'create']):
                    print(f"   🎯 Potential BaseModel instantiation detected")
                
                # Look for context around the line
                context_start = max(0, line_num - 3)
                context_end = min(len(lines), line_num + 2)
                
                print(f"   Context (lines {context_start + 1}-{context_end}):")
                for i in range(context_start, context_end):
                    marker = " ➤ " if i == line_num - 1 else "   "
                    print(f"   {marker}{i + 1}: {lines[i].rstrip()}")
            else:
                print(f"\n🔍 Line {line_num}: Beyond file length ({len(lines)} lines)")
    
    except Exception as e:
        print(f"❌ Error analyzing specific lines: {e}")
        traceback.print_exc()

def main():
    """Main test execution."""
    print("🚀 Focused BaseModel Error Analysis")
    print("=" * 50)
    print(f"Started at: {datetime.now().isoformat()}")
    
    try:
        # Run basic tests
        success = test_basemodel_creation()
        
        # Analyze specific problem lines
        analyze_specific_lines()
        
        print(f"\n🎯 Analysis complete at: {datetime.now().isoformat()}")
        
        if success:
            print("✅ Basic tests passed - BaseModel creation is working")
        else:
            print("❌ Some tests failed - BaseModel issues detected")
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())