#!/usr/bin/env python3
"""
Complete Character Consistency Validation Suite Runner

Executes the complete character consistency validation test suite for
Diana and Lucien across all Cinema Architecture systems.

This script runs all character validation tests and generates a 
comprehensive report to ensure Diana and Lucien maintain their
core personalities through all system enhancements.

Usage:
    python run_complete_character_validation_suite.py [--export-report] [--stress-test]
    
Options:
    --export-report    Export detailed JSON report
    --stress-test      Include stress testing scenarios  
    --performance      Include performance testing
    --quiet           Suppress detailed output
"""

import asyncio
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import test modules
import pytest
from services.comprehensive_character_validation_report import (
    generate_character_validation_report,
    ComprehensiveCharacterValidationReportSystem
)

# Database setup
from database.database import get_async_session


async def run_complete_validation_suite(
    export_json: bool = False,
    include_stress_testing: bool = False,
    include_performance_testing: bool = True,
    quiet_mode: bool = False
):
    """
    Run the complete character consistency validation suite.
    
    Args:
        export_json: Export detailed JSON report
        include_stress_testing: Include stress testing scenarios
        include_performance_testing: Include performance testing
        quiet_mode: Suppress detailed output
    """
    start_time = datetime.utcnow()
    
    if not quiet_mode:
        print("\n" + "="*80)
        print("CINEMA ARCHITECTURE CHARACTER CONSISTENCY VALIDATION SUITE")
        print("="*80)
        print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("\nValidating Diana and Lucien character integrity across:")
        print("• Soul Signature Personalization")
        print("• Choice Architecture Masterpiece")
        print("• Clue Treasure Hunting")
        print("• Fallback Character Preservation")
        print("• Integration Testing")
        if include_performance_testing:
            print("• Performance Under Load Testing")
        if include_stress_testing:
            print("• Stress Testing Scenarios")
        print("\n" + "-"*80)
    
    try:
        # Step 1: Run pytest test suites
        if not quiet_mode:
            print("\n🧪 PHASE 1: RUNNING CHARACTER CONSISTENCY TEST SUITES")
            print("-"*60)
        
        test_results = await run_pytest_character_tests(quiet_mode)
        
        # Step 2: Generate comprehensive validation report
        if not quiet_mode:
            print("\n📈 PHASE 2: GENERATING COMPREHENSIVE CHARACTER REPORT")
            print("-"*60)
        
        async with get_async_session() as session:
            export_path = None
            if export_json:
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                export_path = f"character_validation_report_{timestamp}.json"
            
            comprehensive_report = await generate_character_validation_report(
                session=session,
                include_performance_testing=include_performance_testing,
                include_stress_testing=include_stress_testing,
                export_json_path=export_path
            )
        
        # Step 3: Final validation summary
        if not quiet_mode:
            print("\n🏆 PHASE 3: FINAL CHARACTER VALIDATION SUMMARY")
            print("-"*60)
        
        await print_final_validation_summary(
            test_results, comprehensive_report, start_time, quiet_mode
        )
        
        # Step 4: Exit with appropriate code
        exit_code = determine_exit_code(test_results, comprehensive_report)
        
        if not quiet_mode:
            print(f"\nValidation suite completed in {(datetime.utcnow() - start_time).total_seconds():.1f} seconds")
            if exit_code == 0:
                print("🎉 CHARACTER CONSISTENCY VALIDATION: SUCCESS!")
            else:
                print("⚠️ CHARACTER CONSISTENCY VALIDATION: ISSUES DETECTED")
        
        return exit_code
        
    except Exception as e:
        logger.error(f"Critical error in character validation suite: {e}")
        if not quiet_mode:
            print(f"\n🚨 CRITICAL ERROR: {e}")
            print("Character validation suite failed to complete!")
        return 1


async def run_pytest_character_tests(quiet_mode: bool = False) -> dict:
    """
    Run all pytest character consistency test suites.
    
    Args:
        quiet_mode: Suppress detailed pytest output
        
    Returns:
        Dictionary with test results summary
    """
    test_files = [
        "tests/test_cinema_character_consistency_validation.py",
        "tests/test_choice_architecture_character_preservation.py", 
        "tests/test_treasure_hunting_character_integrity.py",
        "tests/test_fallback_character_preservation.py"
    ]
    
    test_results = {
        'total_files': len(test_files),
        'passed_files': 0,
        'failed_files': 0,
        'total_tests': 0,
        'passed_tests': 0,
        'failed_tests': 0,
        'file_results': {}
    }
    
    for test_file in test_files:
        if not quiet_mode:
            print(f"\n🧪 Running {test_file}...")
        
        # Configure pytest arguments
        pytest_args = [test_file, "-v"]
        if quiet_mode:
            pytest_args.extend(["-q", "--tb=no"])
        
        # Run pytest programmatically
        try:
            exit_code = pytest.main(pytest_args)
            
            if exit_code == 0:
                test_results['passed_files'] += 1
                test_results['file_results'][test_file] = 'PASSED'
                if not quiet_mode:
                    print(f"✅ {test_file} - ALL TESTS PASSED")
            else:
                test_results['failed_files'] += 1
                test_results['file_results'][test_file] = 'FAILED'
                if not quiet_mode:
                    print(f"❌ {test_file} - TESTS FAILED")
                    
        except Exception as e:
            logger.error(f"Error running {test_file}: {e}")
            test_results['failed_files'] += 1
            test_results['file_results'][test_file] = f'ERROR: {str(e)}'
            if not quiet_mode:
                print(f"❌ {test_file} - ERROR: {e}")
    
    return test_results


async def print_final_validation_summary(
    test_results: dict, 
    comprehensive_report, 
    start_time: datetime,
    quiet_mode: bool = False
):
    """
    Print final character validation summary.
    
    Args:
        test_results: Pytest test results
        comprehensive_report: Comprehensive character report
        start_time: Validation start time
        quiet_mode: Suppress detailed output
    """
    if quiet_mode:
        return
    
    elapsed_time = (datetime.utcnow() - start_time).total_seconds()
    
    print("\n" + "="*80)
    print("FINAL CHARACTER CONSISTENCY VALIDATION SUMMARY")
    print("="*80)
    
    # Test Suite Results
    print(f"\n🧪 PYTEST SUITE RESULTS:")
    print(f"  Test Files: {test_results['passed_files']}/{test_results['total_files']} passed")
    print(f"  Overall Success Rate: {(test_results['passed_files'] / test_results['total_files'] * 100):.1f}%")
    
    for test_file, result in test_results['file_results'].items():
        status_emoji = "✅" if result == 'PASSED' else "❌"
        print(f"    {status_emoji} {test_file.split('/')[-1]}: {result}")
    
    # Comprehensive Report Results
    print(f"\n📈 COMPREHENSIVE CHARACTER ANALYSIS:")
    print(f"  Overall Character Integrity: {comprehensive_report.overall_character_integrity.value}")
    print(f"  Character Preservation: {comprehensive_report.character_preservation_percentage:.1f}%")
    print(f"  Diana Overall Score: {comprehensive_report.diana_overall_score:.1f}/100")
    print(f"  Lucien Overall Score: {comprehensive_report.lucien_overall_score:.1f}/100")
    print(f"  Character Bible Compliance: {'✅ CERTIFIED' if comprehensive_report.meets_character_bible_requirements else '❌ NEEDS IMPROVEMENT'}")
    print(f"  Critical Failures: {comprehensive_report.critical_failures}")
    
    # Character Trait Breakdown
    print(f"\n🎭 DIANA CHARACTER TRAITS:")
    diana_traits = comprehensive_report.diana_trait_averages
    print(f"  ✨ Mystery: {diana_traits['mystery']:.1f}/25 ({'EXCELLENT' if diana_traits['mystery'] >= 23 else 'GOOD' if diana_traits['mystery'] >= 20 else 'NEEDS IMPROVEMENT'})")
    print(f"  💋 Seductive: {diana_traits['seductive']:.1f}/25 ({'EXCELLENT' if diana_traits['seductive'] >= 23 else 'GOOD' if diana_traits['seductive'] >= 20 else 'NEEDS IMPROVEMENT'})")
    print(f"  💖 Emotional: {diana_traits['emotional']:.1f}/25 ({'EXCELLENT' if diana_traits['emotional'] >= 23 else 'GOOD' if diana_traits['emotional'] >= 20 else 'NEEDS IMPROVEMENT'})")
    print(f"  🧠 Intellectual: {diana_traits['intellectual']:.1f}/25 ({'EXCELLENT' if diana_traits['intellectual'] >= 23 else 'GOOD' if diana_traits['intellectual'] >= 20 else 'NEEDS IMPROVEMENT'})")
    
    print(f"\n🤵 LUCIEN CHARACTER TRAITS:")
    lucien_traits = comprehensive_report.lucien_trait_averages
    print(f"  🤝 Supportive: {lucien_traits['supportive']:.1f}/25 ({'EXCELLENT' if lucien_traits['supportive'] >= 20 else 'GOOD' if lucien_traits['supportive'] >= 17 else 'NEEDS IMPROVEMENT'})")
    print(f"  🙏 Non-Intrusive: {lucien_traits['non_intrusive']:.1f}/25 ({'EXCELLENT' if lucien_traits['non_intrusive'] >= 20 else 'GOOD' if lucien_traits['non_intrusive'] >= 17 else 'NEEDS IMPROVEMENT'})")
    print(f"  ✨ Mystery Amplifier: {lucien_traits['mystery_amplifier']:.1f}/25 ({'EXCELLENT' if lucien_traits['mystery_amplifier'] >= 15 else 'GOOD' if lucien_traits['mystery_amplifier'] >= 12 else 'NEEDS IMPROVEMENT'})")
    print(f"  💼 Professional: {lucien_traits['professional']:.1f}/25 ({'EXCELLENT' if lucien_traits['professional'] >= 20 else 'GOOD' if lucien_traits['professional'] >= 17 else 'NEEDS IMPROVEMENT'})")
    
    # System-Specific Results
    print(f"\n🎪 CINEMA ARCHITECTURE SYSTEMS:")
    systems = {
        'Soul Signature Personalization': comprehensive_report.soul_signature_results,
        'Choice Architecture': comprehensive_report.choice_architecture_results,
        'Treasure Hunting': comprehensive_report.treasure_hunting_results,
        'Fallback Preservation': comprehensive_report.fallback_preservation_results,
        'Integration Testing': comprehensive_report.integration_results
    }
    
    for system_name, system_results in systems.items():
        if system_results:
            rating = system_results.get('system_rating', 'UNKNOWN')
            rating_emoji = {
                'EXCELLENT': '🎆',
                'GOOD': '✅', 
                'ACCEPTABLE': '🟡',
                'NEEDS_IMPROVEMENT': '⚠️',
                'CRITICAL_FAILURE': '❌'
            }.get(rating, '❓')
            print(f"  {rating_emoji} {system_name}: {rating}")
    
    # Critical Issues
    if comprehensive_report.critical_issues:
        print(f"\n🚨 CRITICAL ISSUES:")
        for issue in comprehensive_report.critical_issues:
            print(f"  ❌ {issue}")
    
    # Recommendations
    if comprehensive_report.high_priority_recommendations:
        print(f"\n🔧 HIGH PRIORITY RECOMMENDATIONS:")
        for rec in comprehensive_report.high_priority_recommendations[:3]:
            print(f"  ➡️ {rec}")
    
    # Performance Summary
    print(f"\n⏱️ PERFORMANCE SUMMARY:")
    print(f"  Total Validation Time: {elapsed_time:.1f} seconds")
    print(f"  Report Generation Time: {comprehensive_report.test_duration_minutes:.1f} minutes")
    print(f"  Tests Executed: {comprehensive_report.total_tests_run}")
    print(f"  Certification Status: {comprehensive_report.certification_status}")
    print(f"  Next Validation Due: {comprehensive_report.next_validation_recommended.strftime('%Y-%m-%d')}")
    
    print("\n" + "="*80)
    

def determine_exit_code(test_results: dict, comprehensive_report) -> int:
    """
    Determine appropriate exit code based on validation results.
    
    Args:
        test_results: Pytest results
        comprehensive_report: Comprehensive character report
        
    Returns:
        Exit code (0 = success, 1 = failure)
    """
    # Critical failure conditions
    if comprehensive_report.critical_failures > 0:
        return 1
    
    # Test suite failures
    if test_results['failed_files'] > 0:
        return 1
    
    # Character Bible compliance
    if not comprehensive_report.meets_character_bible_requirements:
        return 1
    
    # Character integrity check
    if comprehensive_report.overall_character_integrity.value in ['CRITICAL_FAILURE', 'NEEDS_IMPROVEMENT']:
        return 1
    
    # Minimum character preservation threshold
    if comprehensive_report.character_preservation_percentage < 95.0:
        return 1
    
    # Diana character score minimum
    if comprehensive_report.diana_overall_score < 90.0:
        return 1
    
    # Lucien character score minimum
    if comprehensive_report.lucien_overall_score < 85.0:
        return 1
    
    # All checks passed
    return 0


def main():
    """Main entry point for character validation suite."""
    parser = argparse.ArgumentParser(
        description='Run complete character consistency validation suite for Diana and Lucien'
    )
    parser.add_argument(
        '--export-report', 
        action='store_true',
        help='Export detailed JSON report'
    )
    parser.add_argument(
        '--stress-test',
        action='store_true', 
        help='Include stress testing scenarios'
    )
    parser.add_argument(
        '--performance',
        action='store_true',
        default=True,
        help='Include performance testing (default: True)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress detailed output'
    )
    
    args = parser.parse_args()
    
    # Run the validation suite
    try:
        exit_code = asyncio.run(run_complete_validation_suite(
            export_json=args.export_report,
            include_stress_testing=args.stress_test,
            include_performance_testing=args.performance,
            quiet_mode=args.quiet
        ))
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Character validation suite interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n🚨 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
