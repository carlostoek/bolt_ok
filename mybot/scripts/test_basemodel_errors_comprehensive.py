#!/usr/bin/env python3
"""
Comprehensive BaseModel Error Diagnostic Test Script

This script reproduces BaseModel initialization failures in the Diana menu system
and provides detailed analysis of the exact causes. It can be run alongside the bot
to capture real-world error scenarios with full debugging context.

Usage:
    python scripts/test_basemodel_errors_comprehensive.py

Features:
- Reproduces specific BaseModel errors from lines 567, 626, 681, 751
- Tests database session management issues
- Analyzes service dependency injection patterns
- Captures detailed error logs with full stack traces
- Generates actionable diagnostic reports
"""

import asyncio
import logging
import sys
import os
import traceback
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
import tempfile

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / "logs" / "basemodel_diagnostic_test.log")
    ]
)

logger = logging.getLogger(__name__)

class BaseModelDiagnosticTester:
    """
    Comprehensive diagnostic tester for BaseModel errors in Diana menu system.
    """
    
    def __init__(self):
        self.test_results = []
        self.error_tracker = None
        self.debugger = None
        self.mock_session = None
        
        # Ensure logs directory exists
        (project_root / "logs").mkdir(exist_ok=True)
    
    async def initialize_systems(self):
        """Initialize all debugging and tracking systems."""
        print("🔧 Initializing BaseModel diagnostic systems...")
        
        try:
            # Import and initialize error tracking
            from services.diana_basemodel_error_tracker import (
                get_global_error_tracker,
                track_basemodel_error,
                track_session_error,
                track_dependency_failure
            )
            
            self.error_tracker = get_global_error_tracker()
            print(f"✅ Error tracker initialized: {self.error_tracker.enabled}")
            
            # Import and initialize debugger
            from services.diana_basemodel_debugger import (
                get_global_debugger,
                enable_basemodel_debug
            )
            
            enable_basemodel_debug()
            self.debugger = get_global_debugger()
            print(f"✅ BaseModel debugger enabled: {self.debugger.debug_enabled}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize systems: {e}")
            traceback.print_exc()
            return False
    
    def setup_mock_session(self):
        """Setup comprehensive mock database session."""
        print("🔧 Setting up mock database session...")
        
        self.mock_session = AsyncMock()
        
        # Mock session methods that might cause "Cannot operate on a closed database" errors
        self.mock_session.execute = AsyncMock()
        self.mock_session.commit = AsyncMock()
        self.mock_session.rollback = AsyncMock()
        self.mock_session.close = AsyncMock()
        self.mock_session.is_active = True
        
        # Mock query results
        mock_user = MagicMock()
        mock_user.id = 123456789
        mock_user.first_name = "TestUser"
        mock_user.role = "free"
        mock_user.points = 150.0
        mock_user.level = 2
        mock_user.created_at = datetime.now()
        
        # Setup various query scenarios
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_result.scalar.return_value = "free"
        
        self.mock_session.execute.return_value = mock_result
        
        print("✅ Mock session configured with test data")
        return self.mock_session
    
    async def test_enhanced_diana_menu_initialization(self):
        """Test 1: Enhanced Diana Menu System initialization."""
        print("\n📝 Test 1: Enhanced Diana Menu System Initialization")
        print("-" * 60)
        
        test_result = {
            'test_name': 'enhanced_diana_menu_initialization',
            'success': False,
            'errors': [],
            'details': {}
        }
        
        try:
            from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem
            
            # Test with mock session
            menu_system = EnhancedDianaMenuSystem(self.mock_session)
            
            print(f"✅ EnhancedDianaMenuSystem initialized successfully")
            print(f"   Debug enabled: {menu_system.local_debug_enabled}")
            print(f"   Debugger available: {hasattr(menu_system, 'debugger')}")
            
            test_result['success'] = True
            test_result['details'] = {
                'debug_enabled': menu_system.local_debug_enabled,
                'has_debugger': hasattr(menu_system, 'debugger')
            }
            
        except Exception as e:
            error_msg = f"Enhanced Diana Menu System initialization failed: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            traceback.print_exc()
            
            test_result['errors'].append(error_msg)
            
            # Track the error
            if self.error_tracker:
                error_id = self.error_tracker.capture_error(
                    error=e,
                    attempted_class="EnhancedDianaMenuSystem",
                    constructor_args=[self.mock_session],
                    additional_context={
                        'test_name': 'enhanced_diana_menu_initialization',
                        'menu_operation': 'initialization'
                    }
                )
                print(f"🔍 Error tracked with ID: {error_id}")
        
        self.test_results.append(test_result)
        return test_result['success']
    
    async def test_menu_response_creation_patterns(self):
        """Test 2: MenuResponse creation patterns (lines 567, 626, 681, 751)."""
        print("\n📝 Test 2: MenuResponse Creation Patterns")
        print("-" * 60)
        
        test_result = {
            'test_name': 'menu_response_creation_patterns',
            'success': True,
            'errors': [],
            'details': {'tested_patterns': []}
        }
        
        try:
            from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem, MenuResponse
            
            menu_system = EnhancedDianaMenuSystem(self.mock_session)
            
            # Test various MenuResponse creation patterns that might fail
            test_patterns = [
                {
                    'name': 'Normal creation (baseline)',
                    'line_reference': 'N/A',
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
                    'name': 'Failure scenario (similar to line 567)',
                    'line_reference': '~567',
                    'kwargs': {
                        'success': False,
                        'character_score': 0.0,
                        'response_time': 1.0,
                        'meets_performance_requirement': False,
                        'message_sent': False,
                        'errors': ["Simulated error for line 567 scenario"]
                    }
                },
                {
                    'name': 'Performance warning (similar to line 626)',
                    'line_reference': '~626',
                    'kwargs': {
                        'success': True,
                        'character_score': 94.5,
                        'response_time': 1.2,
                        'meets_performance_requirement': False,
                        'message_sent': True,
                        'errors': []
                    }
                },
                {
                    'name': 'Character validation failure (similar to line 681)',
                    'line_reference': '~681',
                    'kwargs': {
                        'success': False,
                        'character_score': 72.3,
                        'response_time': 0.8,
                        'meets_performance_requirement': True,
                        'message_sent': False,
                        'errors': ["Character validation failed"]
                    }
                },
                {
                    'name': 'Critical system error (similar to line 751)',
                    'line_reference': '~751',
                    'kwargs': {
                        'success': False,
                        'character_score': 0.0,
                        'response_time': 2.5,
                        'meets_performance_requirement': False,
                        'message_sent': False,
                        'errors': ["Critical system error", "Database connection lost"]
                    }
                }
            ]
            
            for pattern in test_patterns:
                print(f"\n   Testing: {pattern['name']} (line {pattern['line_reference']})")
                
                pattern_result = {'name': pattern['name'], 'success': False, 'error': None}
                
                try:
                    # Test direct MenuResponse creation
                    direct_response = MenuResponse(**pattern['kwargs'])
                    print(f"     ✅ Direct MenuResponse creation: Success={direct_response.success}")
                    pattern_result['direct_creation'] = True
                    
                    # Test safe creation through menu system
                    safe_response = menu_system._create_safe_menu_response(**pattern['kwargs'])
                    print(f"     ✅ Safe MenuResponse creation: Success={safe_response.success}")
                    pattern_result['safe_creation'] = True
                    pattern_result['success'] = True
                    
                except Exception as e:
                    error_msg = f"MenuResponse creation failed for {pattern['name']}: {e}"
                    print(f"     ❌ {error_msg}")
                    pattern_result['error'] = str(e)
                    test_result['errors'].append(error_msg)
                    
                    # Track the specific error
                    if self.error_tracker:
                        error_id = self.error_tracker.capture_error(
                            error=e,
                            attempted_class="MenuResponse",
                            constructor_kwargs=pattern['kwargs'],
                            additional_context={
                                'test_pattern': pattern['name'],
                                'line_reference': pattern['line_reference'],
                                'menu_operation': 'menu_response_creation'
                            }
                        )
                        print(f"     🔍 Error tracked with ID: {error_id}")
                
                test_result['details']['tested_patterns'].append(pattern_result)
            
            # Overall success if no errors
            test_result['success'] = len(test_result['errors']) == 0
            
        except Exception as e:
            error_msg = f"MenuResponse pattern testing failed: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            traceback.print_exc()
            test_result['errors'].append(error_msg)
            test_result['success'] = False
        
        self.test_results.append(test_result)
        return test_result['success']
    
    async def test_database_session_scenarios(self):
        """Test 3: Database session management scenarios."""
        print("\n📝 Test 3: Database Session Management Scenarios")
        print("-" * 60)
        
        test_result = {
            'test_name': 'database_session_scenarios',
            'success': True,
            'errors': [],
            'details': {'scenarios': []}
        }
        
        try:
            from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem
            
            # Test scenarios that might cause "Cannot operate on a closed database" errors
            scenarios = [
                {
                    'name': 'Normal session',
                    'setup': lambda: self.setup_mock_session()
                },
                {
                    'name': 'Closed session',
                    'setup': lambda: self._setup_closed_session()
                },
                {
                    'name': 'Session with connection error',
                    'setup': lambda: self._setup_error_session()
                }
            ]
            
            for scenario in scenarios:
                print(f"\n   Testing scenario: {scenario['name']}")
                scenario_result = {'name': scenario['name'], 'success': False, 'error': None}
                
                try:
                    session = scenario['setup']()
                    menu_system = EnhancedDianaMenuSystem(session)
                    
                    # Try to use the menu system
                    await self._simulate_menu_operations(menu_system)
                    
                    print(f"     ✅ Scenario completed successfully")
                    scenario_result['success'] = True
                    
                except Exception as e:
                    error_msg = f"Session scenario '{scenario['name']}' failed: {e}"
                    print(f"     ❌ {error_msg}")
                    scenario_result['error'] = str(e)
                    
                    # Track session error
                    if self.error_tracker:
                        self.error_tracker.track_session_error(
                            error_type='session_management_error',
                            description=error_msg,
                            session_details={'scenario': scenario['name']},
                            user_id=123456789
                        )
                
                test_result['details']['scenarios'].append(scenario_result)
            
            # Overall success if at least normal session works
            normal_session_success = any(
                s['name'] == 'Normal session' and s['success']
                for s in test_result['details']['scenarios']
            )
            test_result['success'] = normal_session_success
            
        except Exception as e:
            error_msg = f"Database session testing failed: {e}"
            print(f"❌ {error_msg}")
            test_result['errors'].append(error_msg)
            test_result['success'] = False
        
        self.test_results.append(test_result)
        return test_result['success']
    
    async def test_service_dependency_injection(self):
        """Test 4: Service dependency injection patterns."""
        print("\n📝 Test 4: Service Dependency Injection Patterns")
        print("-" * 60)
        
        test_result = {
            'test_name': 'service_dependency_injection',
            'success': True,
            'errors': [],
            'details': {'services': []}
        }
        
        try:
            from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem
            
            menu_system = EnhancedDianaMenuSystem(self.mock_session)
            
            # Test lazy-loaded service dependencies
            services_to_test = [
                ('user_service', '_get_user_service'),
                ('character_validator', '_get_character_validator'),
                ('base_menu_system', '_get_base_menu_system')
            ]
            
            for service_name, getter_method in services_to_test:
                print(f"\n   Testing service: {service_name}")
                service_result = {'name': service_name, 'success': False, 'error': None}
                
                try:
                    # Test lazy loading
                    if hasattr(menu_system, getter_method):
                        service = getattr(menu_system, getter_method)()
                        print(f"     ✅ Service {service_name} loaded: {type(service).__name__}")
                        service_result['success'] = True
                        service_result['type'] = type(service).__name__
                    else:
                        print(f"     ⚠️ Getter method {getter_method} not found")
                        service_result['error'] = f"Getter method {getter_method} not found"
                    
                    # Test property access
                    if hasattr(menu_system, service_name):
                        prop_service = getattr(menu_system, service_name)
                        print(f"     ✅ Property access works: {type(prop_service).__name__}")
                        service_result['property_access'] = True
                    
                except Exception as e:
                    error_msg = f"Service {service_name} dependency injection failed: {e}"
                    print(f"     ❌ {error_msg}")
                    service_result['error'] = str(e)
                    
                    # Track dependency failure
                    if self.error_tracker:
                        self.error_tracker.track_dependency_failure(
                            service_name=service_name,
                            failure_reason=str(e),
                            context={
                                'getter_method': getter_method,
                                'menu_system_type': type(menu_system).__name__
                            }
                        )
                
                test_result['details']['services'].append(service_result)
            
            # Check overall success
            all_services_ok = all(s['success'] for s in test_result['details']['services'])
            test_result['success'] = all_services_ok
            
        except Exception as e:
            error_msg = f"Service dependency testing failed: {e}"
            print(f"❌ {error_msg}")
            test_result['errors'].append(error_msg)
            test_result['success'] = False
        
        self.test_results.append(test_result)
        return test_result['success']
    
    async def test_character_validation_integration(self):
        """Test 5: Character validation integration."""
        print("\n📝 Test 5: Character Validation Integration")
        print("-" * 60)
        
        test_result = {
            'test_name': 'character_validation_integration',
            'success': True,
            'errors': [],
            'details': {}
        }
        
        try:
            from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem
            
            menu_system = EnhancedDianaMenuSystem(self.mock_session)
            
            # Test character validator initialization
            try:
                validator = menu_system.character_validator
                print(f"   ✅ Character validator loaded: {type(validator).__name__}")
                test_result['details']['validator_loaded'] = True
            except Exception as e:
                print(f"   ❌ Character validator loading failed: {e}")
                test_result['errors'].append(f"Character validator loading failed: {e}")
                test_result['details']['validator_loaded'] = False
            
            # Test validation functionality (mock it since we may not have the full system)
            try:
                # This might fail, but we want to see how it fails
                test_text = "💋 Los Dominios de Diana... Un susurro seductor en la noche..."
                # validation_result = await validator.validate_text(test_text, context="test")
                print(f"   ⚠️ Character validation test skipped (requires full system)")
                test_result['details']['validation_test'] = 'skipped'
            except Exception as e:
                print(f"   ❌ Character validation test failed: {e}")
                test_result['details']['validation_test'] = f"failed: {e}"
        
        except Exception as e:
            error_msg = f"Character validation integration test failed: {e}"
            print(f"❌ {error_msg}")
            test_result['errors'].append(error_msg)
            test_result['success'] = False
        
        self.test_results.append(test_result)
        return test_result['success']
    
    def _setup_closed_session(self):
        """Setup a mock closed session to test error scenarios."""
        closed_session = AsyncMock()
        closed_session.execute.side_effect = Exception("Cannot operate on a closed database")
        closed_session.is_active = False
        return closed_session
    
    def _setup_error_session(self):
        """Setup a mock session that raises connection errors."""
        error_session = AsyncMock()
        error_session.execute.side_effect = Exception("Database connection lost")
        error_session.is_active = True
        return error_session
    
    async def _simulate_menu_operations(self, menu_system):
        """Simulate basic menu operations to test session usage."""
        # Try to get user role (involves session)
        try:
            role = await menu_system._get_user_role_fast(123456789)
            print(f"       User role retrieved: {role}")
        except Exception as e:
            print(f"       User role retrieval failed: {e}")
            raise
        
        # Try to create a simple response
        try:
            response = menu_system._create_safe_menu_response(
                success=True,
                character_score=95.0,
                response_time=0.3,
                meets_performance_requirement=True,
                message_sent=True,
                errors=[]
            )
            print(f"       Safe response created: {response.success}")
        except Exception as e:
            print(f"       Safe response creation failed: {e}")
            raise
    
    async def generate_comprehensive_report(self):
        """Generate comprehensive diagnostic report."""
        print("\n📊 Generating Comprehensive Diagnostic Report")
        print("=" * 60)
        
        # Generate error tracker report
        if self.error_tracker:
            error_report = self.error_tracker.generate_diagnostic_report()
            error_report_path = self.error_tracker.save_diagnostic_report()
            print(f"✅ Error tracker report saved to: {error_report_path}")
        else:
            error_report = {'status': 'error_tracker_not_available'}
        
        # Generate debugger report
        if self.debugger:
            from services.diana_basemodel_debugger import get_basemodel_debug_report
            debugger_report = get_basemodel_debug_report()
        else:
            debugger_report = {'status': 'debugger_not_available'}
        
        # Compile comprehensive report
        comprehensive_report = {
            'generation_time': datetime.now().isoformat(),
            'test_summary': {
                'total_tests': len(self.test_results),
                'successful_tests': sum(1 for t in self.test_results if t['success']),
                'failed_tests': sum(1 for t in self.test_results if not t['success'])
            },
            'test_results': self.test_results,
            'error_tracker_report': error_report,
            'debugger_report': debugger_report,
            'recommendations': self._generate_recommendations()
        }
        
        # Save comprehensive report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = project_root / "logs" / f"comprehensive_basemodel_diagnostic_{timestamp}.json"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, indent=2, default=str)
        
        print(f"✅ Comprehensive diagnostic report saved to: {report_path}")
        
        # Print summary
        print(f"\n📋 Test Summary:")
        print(f"   Total tests: {comprehensive_report['test_summary']['total_tests']}")
        print(f"   Successful: {comprehensive_report['test_summary']['successful_tests']}")
        print(f"   Failed: {comprehensive_report['test_summary']['failed_tests']}")
        
        if error_report.get('summary'):
            print(f"\n🔍 Error Analysis:")
            summary = error_report['summary']
            print(f"   Total errors captured: {summary.get('total_errors', 0)}")
            print(f"   Unique error patterns: {summary.get('unique_error_patterns', 0)}")
            print(f"   Session issues: {summary.get('session_issues', 0)}")
            print(f"   Dependency failures: {summary.get('dependency_failures', 0)}")
        
        return report_path
    
    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on test results."""
        recommendations = []
        
        # Check test results for patterns
        failed_tests = [t for t in self.test_results if not t['success']]
        
        if any(t['test_name'] == 'menu_response_creation_patterns' for t in failed_tests):
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'MenuResponse creation failures detected',
                'action': 'Review MenuResponse dataclass definition and ensure proper field validation',
                'implementation': 'Add type checking and default value validation in MenuResponse.__post_init__()'
            })
        
        if any(t['test_name'] == 'database_session_scenarios' for t in failed_tests):
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'Database session management issues detected',
                'action': 'Implement proper session lifecycle management and error handling',
                'implementation': 'Add session state validation before database operations'
            })
        
        if any(t['test_name'] == 'service_dependency_injection' for t in failed_tests):
            recommendations.append({
                'priority': 'MEDIUM',
                'issue': 'Service dependency injection failures detected',
                'action': 'Review lazy loading patterns and add defensive programming',
                'implementation': 'Add null checks and proper error handling in service getters'
            })
        
        # Add general recommendations
        recommendations.append({
            'priority': 'MEDIUM',
            'issue': 'BaseModel debugging infrastructure',
            'action': 'Keep BaseModel debugging enabled in development',
            'implementation': 'Use the deployed error tracking system to monitor production issues'
        })
        
        return recommendations

async def main():
    """Main test execution."""
    print("🔍 Diana BaseModel Comprehensive Error Diagnostic Test")
    print("=" * 70)
    print(f"Test started at: {datetime.now().isoformat()}")
    print()
    
    tester = BaseModelDiagnosticTester()
    
    # Initialize systems
    if not await tester.initialize_systems():
        print("❌ Failed to initialize diagnostic systems")
        return 1
    
    # Setup mock session
    tester.setup_mock_session()
    
    # Run comprehensive tests
    tests = [
        tester.test_enhanced_diana_menu_initialization,
        tester.test_menu_response_creation_patterns,
        tester.test_database_session_scenarios,
        tester.test_service_dependency_injection,
        tester.test_character_validation_integration
    ]
    
    print("🚀 Starting comprehensive diagnostic tests...")
    print()
    
    for test in tests:
        try:
            await test()
        except Exception as e:
            logger.error(f"Test {test.__name__} crashed: {e}")
            traceback.print_exc()
    
    # Generate comprehensive report
    try:
        report_path = await tester.generate_comprehensive_report()
        print(f"\n🎉 All tests completed!")
        print(f"📊 Comprehensive report available at: {report_path}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error generating final report: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)