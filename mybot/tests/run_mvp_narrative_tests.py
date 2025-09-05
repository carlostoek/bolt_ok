#!/usr/bin/env python3
"""
MVP Narrative System Test Runner

Comprehensive test runner for all MVP narrative system tests with detailed reporting,
performance metrics, and validation compliance checking.
"""

import os
import sys
import time
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import json

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class MVPTestRunner:
    """Comprehensive test runner for MVP narrative system."""
    
    def __init__(self):
        self.test_files = [
            'test_mvp_narrative_fragment_validation.py',
            'test_mvp_narrative_progression.py', 
            'test_mvp_choice_system_archetyping.py',
            'test_mvp_diana_menu_integration.py',
            'test_mvp_character_consistency.py',
            'test_mvp_performance_requirements.py',
            'test_mvp_error_handling_recovery.py',
            'test_mvp_e2e_user_journeys.py'
        ]
        
        self.test_categories = {
            'fragment_validation': ['test_mvp_narrative_fragment_validation.py'],
            'progression_logic': ['test_mvp_narrative_progression.py'],
            'choice_archetyping': ['test_mvp_choice_system_archetyping.py'],
            'diana_menu': ['test_mvp_diana_menu_integration.py'],
            'character_consistency': ['test_mvp_character_consistency.py'],
            'performance': ['test_mvp_performance_requirements.py'],
            'error_handling': ['test_mvp_error_handling_recovery.py'],
            'e2e_journeys': ['test_mvp_e2e_user_journeys.py']
        }
        
        self.results = {}
        
    def print_banner(self):
        """Print test runner banner."""
        print("=" * 80)
        print("🎭 DIANA BOT MVP NARRATIVE SYSTEM TEST SUITE")
        print("=" * 80)
        print("Testing Levels 1→2→3 progression, character consistency >95%,")
        print("performance <500ms, and complete user journey validation.")
        print("-" * 80)
        
    def run_test_category(self, category: str, verbose: bool = False) -> Dict[str, Any]:
        """Run a specific test category."""
        if category not in self.test_categories:
            print(f"❌ Unknown test category: {category}")
            return {'success': False, 'error': f'Unknown category: {category}'}
        
        print(f"\n🔍 Running {category.upper()} tests...")
        
        category_results = {
            'category': category,
            'files': [],
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'duration': 0,
            'success': True
        }
        
        start_time = time.time()
        
        for test_file in self.test_categories[category]:
            file_result = self.run_test_file(test_file, verbose)
            category_results['files'].append(file_result)
            category_results['total_tests'] += file_result.get('total_tests', 0)
            category_results['passed_tests'] += file_result.get('passed_tests', 0)
            category_results['failed_tests'] += file_result.get('failed_tests', 0)
            
            if not file_result.get('success', False):
                category_results['success'] = False
        
        category_results['duration'] = time.time() - start_time
        
        # Print category summary
        status = "✅ PASSED" if category_results['success'] else "❌ FAILED"
        print(f"{status} {category.upper()}: {category_results['passed_tests']}/{category_results['total_tests']} tests passed in {category_results['duration']:.2f}s")
        
        return category_results
        
    def run_test_file(self, test_file: str, verbose: bool = False) -> Dict[str, Any]:
        """Run a specific test file."""
        test_path = PROJECT_ROOT / 'tests' / test_file
        
        if not test_path.exists():
            return {
                'file': test_file,
                'success': False,
                'error': f'Test file not found: {test_path}',
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0
            }
        
        # Prepare pytest command
        cmd = [
            sys.executable, '-m', 'pytest',
            str(test_path),
            '--tb=short',
            '--disable-warnings'
        ]
        
        if verbose:
            cmd.append('-v')
        else:
            cmd.append('-q')
        
        # Add coverage if requested
        if os.environ.get('MVP_TEST_COVERAGE'):
            cmd.extend(['--cov=services', '--cov=database', '--cov-report=term-missing'])
        
        try:
            # Run the test
            result = subprocess.run(
                cmd,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per file
            )
            
            # Parse results
            file_result = self.parse_pytest_output(test_file, result.stdout, result.stderr, result.returncode)
            
            if verbose and result.returncode != 0:
                print(f"   STDOUT: {result.stdout}")
                print(f"   STDERR: {result.stderr}")
            
            return file_result
            
        except subprocess.TimeoutExpired:
            return {
                'file': test_file,
                'success': False,
                'error': 'Test timeout (300s exceeded)',
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0
            }
        except Exception as e:
            return {
                'file': test_file,
                'success': False,
                'error': f'Test execution error: {str(e)}',
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0
            }
    
    def parse_pytest_output(self, test_file: str, stdout: str, stderr: str, return_code: int) -> Dict[str, Any]:
        """Parse pytest output to extract test results."""
        result = {
            'file': test_file,
            'success': return_code == 0,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'errors': []
        }
        
        # Parse test counts from output
        lines = stdout.split('\n') + stderr.split('\n')
        
        for line in lines:
            # Look for pytest summary line
            if 'failed' in line and 'passed' in line:
                # Format: "2 failed, 8 passed in 1.23s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'failed,' and i > 0:
                        result['failed_tests'] = int(parts[i-1])
                    elif part == 'passed' and i > 0:
                        result['passed_tests'] = int(parts[i-1])
            elif 'passed in' in line and 'failed' not in line:
                # Format: "8 passed in 1.23s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'passed' and i > 0:
                        result['passed_tests'] = int(parts[i-1])
            elif line.strip().startswith('FAILED'):
                result['errors'].append(line.strip())
        
        result['total_tests'] = result['passed_tests'] + result['failed_tests']
        
        return result
    
    def run_all_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run all MVP narrative tests."""
        self.print_banner()
        
        overall_results = {
            'start_time': time.time(),
            'categories': {},
            'total_duration': 0,
            'overall_success': True,
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'categories_passed': 0,
                'categories_failed': 0
            }
        }
        
        # Run each test category
        for category in self.test_categories.keys():
            category_result = self.run_test_category(category, verbose)
            overall_results['categories'][category] = category_result
            
            # Update summary
            overall_results['summary']['total_tests'] += category_result.get('total_tests', 0)
            overall_results['summary']['passed_tests'] += category_result.get('passed_tests', 0)
            overall_results['summary']['failed_tests'] += category_result.get('failed_tests', 0)
            
            if category_result.get('success', False):
                overall_results['summary']['categories_passed'] += 1
            else:
                overall_results['summary']['categories_failed'] += 1
                overall_results['overall_success'] = False
        
        overall_results['total_duration'] = time.time() - overall_results['start_time']
        
        # Print final summary
        self.print_final_summary(overall_results)
        
        return overall_results
    
    def print_final_summary(self, results: Dict[str, Any]):
        """Print final test summary."""
        summary = results['summary']
        
        print("\n" + "=" * 80)
        print("📊 FINAL TEST RESULTS SUMMARY")
        print("=" * 80)
        
        # Overall status
        status = "🎉 ALL TESTS PASSED" if results['overall_success'] else "❌ SOME TESTS FAILED"
        print(f"Status: {status}")
        print(f"Duration: {results['total_duration']:.2f} seconds")
        print()
        
        # Test statistics
        print("📈 Test Statistics:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed_tests']} ({(summary['passed_tests']/max(summary['total_tests'],1)*100):.1f}%)")
        print(f"   Failed: {summary['failed_tests']}")
        print(f"   Categories Passed: {summary['categories_passed']}/{len(self.test_categories)}")
        print()
        
        # Category breakdown
        print("📋 Category Breakdown:")
        for category, result in results['categories'].items():
            status_icon = "✅" if result.get('success', False) else "❌"
            print(f"   {status_icon} {category.upper()}: {result.get('passed_tests', 0)}/{result.get('total_tests', 0)} tests")
        
        # MVP compliance check
        self.check_mvp_compliance(results)
        
        print("=" * 80)
    
    def check_mvp_compliance(self, results: Dict[str, Any]):
        """Check MVP compliance requirements."""
        print("\n🎯 MVP COMPLIANCE CHECK:")
        
        compliance_checks = {
            'character_consistency': "Character consistency >95% validated",
            'performance': "Performance <500ms requirements met", 
            'fragment_validation': "All 8 fragments validated and loaded",
            'progression_logic': "Level 1→2→3 progression working",
            'choice_archetyping': "Choice system and archetyping functional",
            'diana_menu': "Diana Menu System integrated",
            'error_handling': "Error handling maintains character",
            'e2e_journeys': "Complete user journeys tested"
        }
        
        for category, description in compliance_checks.items():
            category_result = results['categories'].get(category, {})
            if category_result.get('success', False):
                print(f"   ✅ {description}")
            else:
                print(f"   ❌ {description}")
        
        # Overall MVP readiness
        mvp_ready = results['overall_success']
        if mvp_ready:
            print("\n🚀 MVP READY: All narrative system requirements validated!")
        else:
            print("\n⚠️  MVP NOT READY: Some requirements need attention.")
    
    def run_quick_tests(self) -> Dict[str, Any]:
        """Run quick subset of tests for development."""
        print("🚀 Running QUICK MVP tests...")
        
        quick_categories = [
            'fragment_validation',
            'character_consistency', 
            'performance'
        ]
        
        results = {'categories': {}, 'overall_success': True}
        
        for category in quick_categories:
            result = self.run_test_category(category, verbose=False)
            results['categories'][category] = result
            if not result.get('success', False):
                results['overall_success'] = False
        
        status = "✅ QUICK TESTS PASSED" if results['overall_success'] else "❌ QUICK TESTS FAILED"
        print(f"\n{status}")
        
        return results
    
    def run_performance_only(self) -> Dict[str, Any]:
        """Run only performance tests."""
        print("⚡ Running PERFORMANCE tests only...")
        return self.run_test_category('performance', verbose=True)
    
    def run_character_only(self) -> Dict[str, Any]:
        """Run only character consistency tests."""
        print("🎭 Running CHARACTER CONSISTENCY tests only...")
        return self.run_test_category('character_consistency', verbose=True)


def main():
    """Main test runner function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='MVP Narrative System Test Runner')
    parser.add_argument('--category', '-c', choices=list(MVPTestRunner().test_categories.keys()),
                       help='Run specific test category only')
    parser.add_argument('--quick', '-q', action='store_true',
                       help='Run quick subset of tests for development')
    parser.add_argument('--performance', '-p', action='store_true',
                       help='Run only performance tests')
    parser.add_argument('--character', '-ch', action='store_true',
                       help='Run only character consistency tests')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--coverage', action='store_true',
                       help='Include test coverage reporting')
    
    args = parser.parse_args()
    
    # Set environment variables
    if args.coverage:
        os.environ['MVP_TEST_COVERAGE'] = '1'
    
    runner = MVPTestRunner()
    
    try:
        if args.quick:
            results = runner.run_quick_tests()
        elif args.performance:
            results = runner.run_performance_only()
        elif args.character:
            results = runner.run_character_only()
        elif args.category:
            results = runner.run_test_category(args.category, args.verbose)
            print(f"\nCategory {args.category.upper()} completed.")
        else:
            results = runner.run_all_tests(args.verbose)
        
        # Return appropriate exit code
        exit_code = 0 if results.get('overall_success', True) else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()