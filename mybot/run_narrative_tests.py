#!/usr/bin/env python
"""
Script to run narrative system tests for Diana Bot.

This script provides a way to run all narrative tests or specific test categories.
It handles setting up the test environment and generating test reports.
"""
import argparse
import sys
import os
import time
from datetime import datetime
from pathlib import Path
import pytest

# Test categories
TEST_CATEGORIES = {
    "all": "Run all narrative tests",
    "basic": "Basic NarrativeEngine functionality tests",
    "flow": "Narrative flow validation tests",
    "emotional": "Emotional state transition tests",
    "rewards": "Integration tests for points and rewards",
    "journey": "User journey flow tests",
    "demo": "Demo tests to verify test infrastructure",
    "integrity": "Test infrastructure integrity verification",
}

def get_test_path(category):
    """Get the test path for the specified category."""
    base_path = "tests/services/"
    
    if category == "all":
        return base_path + "test_*.py"
    elif category == "basic":
        return base_path + "test_narrative_engine.py"
    elif category == "flow":
        return base_path + "test_narrative_flow.py"
    elif category == "emotional":
        return base_path + "test_emotional_states.py"
    elif category == "rewards":
        return base_path + "test_narrative_rewards.py"
    elif category == "journey":
        return base_path + "test_user_journey.py"
    elif category == "demo":
        return base_path + "test_demo.py"
    elif category == "integrity":
        return base_path + "test_infrastructure_integrity.py"
    else:
        return base_path + "test_*.py"

def generate_report(result, category, start_time, end_time):
    """Generate a test report based on the test results."""
    report_dir = Path("test_reports")
    report_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = report_dir / f"narrative_test_report_{category}_{timestamp}.txt"
    
    with open(report_file, "w") as f:
        f.write("=== Diana Narrative System Test Report ===\n\n")
        f.write(f"Test Category: {category}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Duration: {end_time - start_time:.2f} seconds\n\n")
        
        f.write(f"Result Code: {result}\n")
        
        if result == 0:
            f.write("Status: All tests passed successfully!\n")
        else:
            f.write(f"Status: Tests completed with failures or errors (code {result}).\n")
    
    print(f"Test report generated: {report_file}")
    return report_file

def run_tests(category="all", verbosity=2, generate_report_file=True):
    """Run the specified tests and optionally generate a report."""
    if category not in TEST_CATEGORIES:
        print(f"Error: Unknown test category '{category}'")
        print("Available categories:")
        for cat, desc in TEST_CATEGORIES.items():
            print(f"  {cat}: {desc}")
        return 1
    
    print(f"Running {category} narrative tests...")
    
    # Get test path
    test_path = get_test_path(category)
    
    # Set up pytest arguments
    pytest_args = [
        test_path,
        "-v" if verbosity >= 1 else "",
        "--no-header" if verbosity < 2 else "",
    ]
    
    # Run tests
    start_time = time.time()
    result = pytest.main(pytest_args)
    end_time = time.time()
    
    # Generate report if requested
    if generate_report_file:
        report_file = generate_report(result, category, start_time, end_time)
    
    # Return exit code based on test results
    if result == 0:
        print("All tests passed successfully!")
    else:
        print(f"Tests completed with failures or errors (code {result}).")
    
    return result

def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(description="Run Diana narrative system tests")
    
    parser.add_argument(
        "-c", "--category",
        choices=TEST_CATEGORIES.keys(),
        default="all",
        help="Test category to run (default: all)"
    )
    
    parser.add_argument(
        "-v", "--verbosity",
        type=int,
        choices=[0, 1, 2],
        default=2,
        help="Test output verbosity (0-2, default: 2)"
    )
    
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Disable test report generation"
    )
    
    args = parser.parse_args()
    
    return run_tests(
        category=args.category,
        verbosity=args.verbosity,
        generate_report_file=not args.no_report
    )

if __name__ == "__main__":
    sys.exit(main())