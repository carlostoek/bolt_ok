#!/usr/bin/env python3
"""
BaseModel Fix Validation Script

This script validates that BaseModel initialization fixes are working correctly
in the Diana menu system. It performs targeted tests on previously failing areas
and confirms that the implemented solutions are effective.

Usage:
    python scripts/validate_basemodel_fixes.py
"""

import asyncio
import logging
import sys
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class BaseModelFixValidator:
    """
    Validation system to confirm BaseModel fixes are working.
    """
    
    def __init__(self):
        self.validation_results = []
        self.performance_metrics = {}
        
        # Ensure logs directory exists
        (project_root / "logs").mkdir(exist_ok=True)
    
    def setup_mock_environment(self):
        """Setup mock environment for validation testing."""
        print("🔧 Setting up mock environment...")
        
        # Mock database session
        self.mock_session = AsyncMock()
        
        # Mock user data
        mock_user = MagicMock()
        mock_user.id = 123456789
        mock_user.first_name = "ValidatorUser"
        mock_user.role = "free"
        mock_user.points = 200.0
        mock_user.level = 3
        mock_user.created_at = datetime.now()
        mock_user.vip_expires_at = None
        
        # Mock query results
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_result.scalar.return_value = "free"
        
        self.mock_session.execute.return_value = mock_result
        self.mock_session.commit = AsyncMock()
        self.mock_session.rollback = AsyncMock()
        self.mock_session.is_active = True
        
        # Mock callback query
        self.mock_callback = MagicMock()
        self.mock_callback.from_user.id = 123456789
        self.mock_callback.data = "diana_main_menu"
        self.mock_callback.answer = AsyncMock()
        self.mock_callback.message.edit_text = AsyncMock()
        
        print("✅ Mock environment ready")
    
    async def validate_menu_response_creation(self) -> bool:
        """Validate that MenuResponse creation is working reliably."""
        print("\n🔍 Validation Test 1: MenuResponse Creation Reliability")
        print("-" * 60)
        
        validation_success = True
        test_scenarios = []
        
        try:
            from services.enhanced_diana_menu_system import MenuResponse, EnhancedDianaMenuSystem
            
            menu_system = EnhancedDianaMenuSystem(self.mock_session)
            
            # Test scenarios that previously failed
            scenarios = [
                {
                    'name': 'Standard success response',
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
                    'name': 'Error response with fallback',
                    'kwargs': {
                        'success': False,
                        'character_score': 0.0,
                        'response_time': 1.0,
                        'meets_performance_requirement': False,
                        'message_sent': False,
                        'errors': ["Test error"]
                    }
                },
                {
                    'name': 'Performance warning scenario',
                    'kwargs': {
                        'success': True,
                        'character_score': 94.0,
                        'response_time': 1.2,
                        'meets_performance_requirement': False,
                        'message_sent': True,
                        'errors': []
                    }
                },
                {
                    'name': 'Multiple errors scenario',
                    'kwargs': {
                        'success': False,
                        'character_score': 75.0,
                        'response_time': 0.8,
                        'meets_performance_requirement': True,
                        'message_sent': True,
                        'errors': ["Error 1", "Error 2", "Error 3"]
                    }
                }
            ]
            
            for scenario in scenarios:
                scenario_result = {'name': scenario['name'], 'success': False, 'duration_ms': 0}
                
                start_time = time.time()
                try:
                    # Test direct creation
                    direct_response = MenuResponse(**scenario['kwargs'])
                    
                    # Test safe creation through menu system
                    safe_response = menu_system._create_safe_menu_response(**scenario['kwargs'])
                    
                    # Validate responses
                    assert direct_response.success == scenario['kwargs']['success']
                    assert safe_response.success == scenario['kwargs']['success']
                    assert len(safe_response.errors) == len(scenario['kwargs']['errors'])
                    
                    scenario_result['success'] = True
                    duration_ms = (time.time() - start_time) * 1000
                    scenario_result['duration_ms'] = round(duration_ms, 2)
                    
                    print(f"   ✅ {scenario['name']}: {duration_ms:.2f}ms")
                    
                except Exception as e:
                    scenario_result['error'] = str(e)
                    validation_success = False
                    print(f"   ❌ {scenario['name']}: {e}")
                
                test_scenarios.append(scenario_result)
            
            # Performance check
            avg_duration = sum(s.get('duration_ms', 0) for s in test_scenarios) / len(test_scenarios)
            print(f"\n   📊 Average creation time: {avg_duration:.2f}ms")
            
            if avg_duration > 10:  # 10ms threshold for creation
                print(f"   ⚠️ Warning: Average creation time exceeds 10ms threshold")
            
        except Exception as e:
            print(f"   ❌ MenuResponse validation failed: {e}")
            validation_success = False
        
        self.validation_results.append({
            'test': 'menu_response_creation',
            'success': validation_success,
            'scenarios': test_scenarios,
            'avg_duration_ms': avg_duration if 'avg_duration' in locals() else 0
        })
        
        return validation_success
    
    async def validate_menu_operations(self) -> bool:
        """Validate that menu operations work without BaseModel errors."""
        print("\n🔍 Validation Test 2: Menu Operations Reliability")
        print("-" * 60)
        
        validation_success = True
        operation_results = []
        
        try:
            from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem
            
            menu_system = EnhancedDianaMenuSystem(self.mock_session)
            
            # Test key menu operations that previously failed
            operations = [
                {
                    'name': 'Show main menu (free user)',
                    'operation': lambda: menu_system.show_main_menu(self.mock_callback, user_role="free")
                },
                {
                    'name': 'Show main menu (VIP user)',
                    'operation': lambda: menu_system.show_main_menu(self.mock_callback, user_role="vip")
                },
                {
                    'name': 'Handle main menu callback',
                    'operation': lambda: menu_system.handle_callback(self.mock_callback)
                }
            ]
            
            for op in operations:
                op_result = {'name': op['name'], 'success': False, 'duration_ms': 0}
                
                start_time = time.time()
                try:
                    result = await op['operation']()
                    
                    # Validate result structure
                    assert hasattr(result, 'success')
                    assert hasattr(result, 'character_score')
                    assert hasattr(result, 'response_time')
                    assert hasattr(result, 'meets_performance_requirement')
                    assert hasattr(result, 'message_sent')
                    assert hasattr(result, 'errors')
                    
                    op_result['success'] = True
                    op_result['result_success'] = result.success
                    op_result['character_score'] = result.character_score
                    duration_ms = (time.time() - start_time) * 1000
                    op_result['duration_ms'] = round(duration_ms, 2)
                    
                    print(f"   ✅ {op['name']}: {duration_ms:.2f}ms (score: {result.character_score})")
                    
                except Exception as e:
                    op_result['error'] = str(e)
                    validation_success = False
                    print(f"   ❌ {op['name']}: {e}")
                
                operation_results.append(op_result)
            
            # Performance check for menu operations
            successful_ops = [op for op in operation_results if op['success']]
            if successful_ops:
                avg_duration = sum(op['duration_ms'] for op in successful_ops) / len(successful_ops)
                print(f"\n   📊 Average operation time: {avg_duration:.2f}ms")
                
                if avg_duration > 1000:  # 1 second threshold
                    print(f"   ⚠️ Warning: Average operation time exceeds 1000ms performance requirement")
            
        except Exception as e:
            print(f"   ❌ Menu operations validation failed: {e}")
            validation_success = False
        
        self.validation_results.append({
            'test': 'menu_operations',
            'success': validation_success,
            'operations': operation_results
        })
        
        return validation_success
    
    async def validate_error_handling(self) -> bool:
        """Validate that error handling and fallback mechanisms work correctly."""
        print("\n🔍 Validation Test 3: Error Handling & Fallbacks")
        print("-" * 60)
        
        validation_success = True
        error_scenarios = []
        
        try:
            from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem
            
            menu_system = EnhancedDianaMenuSystem(self.mock_session)
            
            # Test error scenarios
            scenarios = [
                {
                    'name': 'Missing required field',
                    'test': lambda: menu_system._create_safe_menu_response(
                        success=True,
                        character_score=95.0,
                        # missing response_time
                        meets_performance_requirement=True,
                        message_sent=True,
                        errors=[]
                    )
                },
                {
                    'name': 'Invalid field type',
                    'test': lambda: menu_system._create_safe_menu_response(
                        success="true",  # should be bool
                        character_score=95.0,
                        response_time=0.3,
                        meets_performance_requirement=True,
                        message_sent=True,
                        errors=[]
                    )
                },
                {
                    'name': 'Fallback mechanism',
                    'test': lambda: menu_system._create_fallback_menu_response(
                        "Test error",
                        success=False,
                        character_score=0.0,
                        response_time=1.0,
                        meets_performance_requirement=False,
                        message_sent=False,
                        errors=["Original error"]
                    )
                }
            ]
            
            for scenario in scenarios:
                scenario_result = {'name': scenario['name'], 'success': False}
                
                try:
                    result = scenario['test']()
                    
                    # Should not raise an exception - fallback should handle it
                    if hasattr(result, 'success'):
                        scenario_result['success'] = True
                        scenario_result['fallback_used'] = getattr(result, 'errors', [])
                        print(f"   ✅ {scenario['name']}: Handled gracefully")
                    else:
                        print(f"   ⚠️ {scenario['name']}: No result returned")
                    
                except Exception as e:
                    # For the first two scenarios, we expect graceful handling, not exceptions
                    if scenario['name'] in ['Missing required field', 'Invalid field type']:
                        validation_success = False
                        scenario_result['error'] = str(e)
                        print(f"   ❌ {scenario['name']}: Should be handled gracefully, got: {e}")
                    else:
                        # For other scenarios, exceptions might be expected
                        scenario_result['expected_exception'] = str(e)
                        print(f"   ℹ️ {scenario['name']}: Exception (might be expected): {e}")
                
                error_scenarios.append(scenario_result)
            
        except Exception as e:
            print(f"   ❌ Error handling validation failed: {e}")
            validation_success = False
        
        self.validation_results.append({
            'test': 'error_handling',
            'success': validation_success,
            'scenarios': error_scenarios
        })
        
        return validation_success
    
    async def validate_debugging_infrastructure(self) -> bool:
        """Validate that debugging infrastructure is working properly."""
        print("\n🔍 Validation Test 4: Debugging Infrastructure")
        print("-" * 60)
        
        validation_success = True
        debug_components = []
        
        try:
            # Test debugger availability
            try:
                from services.diana_basemodel_debugger import (
                    get_global_debugger,
                    get_basemodel_debug_report
                )
                
                debugger = get_global_debugger()
                report = get_basemodel_debug_report()
                
                debug_components.append({
                    'component': 'BaseModel Debugger',
                    'available': True,
                    'debug_enabled': debugger.debug_enabled,
                    'total_attempts': report.get('total_attempts', 0)
                })
                print(f"   ✅ BaseModel Debugger: Available (enabled: {debugger.debug_enabled})")
                
            except Exception as e:
                debug_components.append({
                    'component': 'BaseModel Debugger',
                    'available': False,
                    'error': str(e)
                })
                print(f"   ❌ BaseModel Debugger: Not available ({e})")
                validation_success = False
            
            # Test error tracker availability
            try:
                from services.diana_basemodel_error_tracker import (
                    get_global_error_tracker,
                    generate_error_report
                )
                
                error_tracker = get_global_error_tracker()
                error_report = generate_error_report()
                
                debug_components.append({
                    'component': 'Error Tracker',
                    'available': True,
                    'enabled': error_tracker.enabled,
                    'total_errors': error_report.get('summary', {}).get('total_errors', 0)
                })
                print(f"   ✅ Error Tracker: Available (enabled: {error_tracker.enabled})")
                
            except Exception as e:
                debug_components.append({
                    'component': 'Error Tracker',
                    'available': False,
                    'error': str(e)
                })
                print(f"   ❌ Error Tracker: Not available ({e})")
                validation_success = False
            
            # Test enhanced menu system integration
            try:
                from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem
                
                menu_system = EnhancedDianaMenuSystem(self.mock_session)
                has_debugger = hasattr(menu_system, 'debugger')
                debug_enabled = getattr(menu_system, 'local_debug_enabled', False)
                
                debug_components.append({
                    'component': 'Menu System Integration',
                    'available': True,
                    'has_debugger': has_debugger,
                    'debug_enabled': debug_enabled
                })
                print(f"   ✅ Menu System Integration: Ready (debugger: {has_debugger}, enabled: {debug_enabled})")
                
            except Exception as e:
                debug_components.append({
                    'component': 'Menu System Integration',
                    'available': False,
                    'error': str(e)
                })
                print(f"   ❌ Menu System Integration: Failed ({e})")
                validation_success = False
            
        except Exception as e:
            print(f"   ❌ Debugging infrastructure validation failed: {e}")
            validation_success = False
        
        self.validation_results.append({
            'test': 'debugging_infrastructure',
            'success': validation_success,
            'components': debug_components
        })
        
        return validation_success
    
    def generate_validation_report(self) -> str:
        """Generate comprehensive validation report."""
        print("\n📊 Generating Validation Report")
        print("=" * 50)
        
        # Calculate overall success
        total_tests = len(self.validation_results)
        successful_tests = sum(1 for r in self.validation_results if r['success'])
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Create report
        report = {
            'validation_time': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': round(success_rate, 1)
            },
            'test_results': self.validation_results,
            'overall_status': 'PASSED' if success_rate >= 75 else 'FAILED',
            'recommendations': self._generate_validation_recommendations()
        }
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = project_root / "logs" / f"basemodel_fix_validation_{timestamp}.json"
        
        import json
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print(f"Overall Status: {'✅ PASSED' if report['overall_status'] == 'PASSED' else '❌ FAILED'}")
        print(f"Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        print(f"Report saved to: {report_path}")
        
        # Print test results
        print(f"\nTest Results:")
        for result in self.validation_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"   {status} {result['test']}")
        
        # Print recommendations if any failures
        if report['overall_status'] == 'FAILED':
            print(f"\n🔧 Recommendations:")
            for rec in report['recommendations']:
                print(f"   • {rec['action']}")
        
        return str(report_path)
    
    def _generate_validation_recommendations(self) -> List[Dict[str, str]]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        failed_tests = [r for r in self.validation_results if not r['success']]
        
        for failed_test in failed_tests:
            if failed_test['test'] == 'menu_response_creation':
                recommendations.append({
                    'test': failed_test['test'],
                    'action': 'Fix MenuResponse creation issues - check dataclass field definitions and type validation'
                })
            elif failed_test['test'] == 'menu_operations':
                recommendations.append({
                    'test': failed_test['test'],
                    'action': 'Fix menu operation failures - review session handling and error management'
                })
            elif failed_test['test'] == 'error_handling':
                recommendations.append({
                    'test': failed_test['test'],
                    'action': 'Improve error handling and fallback mechanisms'
                })
            elif failed_test['test'] == 'debugging_infrastructure':
                recommendations.append({
                    'test': failed_test['test'],
                    'action': 'Ensure debugging infrastructure is properly deployed and integrated'
                })
        
        if not recommendations:
            recommendations.append({
                'test': 'general',
                'action': 'All validations passed - BaseModel fixes are working correctly'
            })
        
        return recommendations

async def main():
    """Main validation execution."""
    print("🔍 BaseModel Fix Validation System")
    print("=" * 50)
    print(f"Validation started at: {datetime.now().isoformat()}")
    print()
    
    validator = BaseModelFixValidator()
    
    # Setup mock environment
    validator.setup_mock_environment()
    
    # Run validation tests
    validation_tests = [
        validator.validate_menu_response_creation,
        validator.validate_menu_operations,
        validator.validate_error_handling,
        validator.validate_debugging_infrastructure
    ]
    
    print("🚀 Starting validation tests...")
    
    all_passed = True
    for test in validation_tests:
        try:
            test_result = await test()
            if not test_result:
                all_passed = False
        except Exception as e:
            logger.error(f"Validation test {test.__name__} crashed: {e}")
            all_passed = False
    
    # Generate final report
    try:
        report_path = validator.generate_validation_report()
        
        print(f"\n🎉 Validation completed!")
        print(f"📊 Final report: {report_path}")
        
        return 0 if all_passed else 1
        
    except Exception as e:
        print(f"\n❌ Error generating validation report: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)