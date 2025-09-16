#!/usr/bin/env python3
"""
Validation script for analytics service tests
Verifies test structure and coverage without running actual tests
"""

import ast
import os
from typing import Dict, List, Set

def analyze_test_file(file_path: str) -> Dict[str, any]:
    """Analyze the test file structure and coverage"""

    with open(file_path, 'r') as f:
        content = f.read()

    # Parse the AST
    tree = ast.parse(content)

    analysis = {
        'classes': [],
        'test_methods': [],
        'fixtures': [],
        'imports': [],
        'test_categories': {
            'fragment_analytics': [],
            'choice_distribution': [],
            'bottlenecks': [],
            'user_segments': [],
            'conversion_funnel': [],
            'character_voice': [],
            'data_export': [],
            'performance': [],
            'error_handling': [],
            'integration': []
        }
    }

    # Analyze the AST
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            analysis['classes'].append(node.name)

        elif isinstance(node, ast.FunctionDef):
            if node.name.startswith('test_'):
                analysis['test_methods'].append(node.name)

                # Categorize tests
                method_name = node.name.lower()
                if 'fragment' in method_name and 'engagement' in method_name:
                    analysis['test_categories']['fragment_analytics'].append(node.name)
                elif 'choice' in method_name and 'distribution' in method_name:
                    analysis['test_categories']['choice_distribution'].append(node.name)
                elif 'bottleneck' in method_name:
                    analysis['test_categories']['bottlenecks'].append(node.name)
                elif 'segment' in method_name:
                    analysis['test_categories']['user_segments'].append(node.name)
                elif 'funnel' in method_name or 'conversion' in method_name:
                    analysis['test_categories']['conversion_funnel'].append(node.name)
                elif 'character' in method_name or 'voice' in method_name:
                    analysis['test_categories']['character_voice'].append(node.name)
                elif 'export' in method_name:
                    analysis['test_categories']['data_export'].append(node.name)
                elif 'performance' in method_name or 'large' in method_name or 'concurrent' in method_name:
                    analysis['test_categories']['performance'].append(node.name)
                elif 'error' in method_name or 'invalid' in method_name or 'exception' in method_name or 'edge' in method_name:
                    analysis['test_categories']['error_handling'].append(node.name)
                elif 'integration' in method_name or 'realistic' in method_name:
                    analysis['test_categories']['integration'].append(node.name)

            elif hasattr(node, 'decorator_list') and any(
                hasattr(d, 'id') and d.id == 'fixture' for d in node.decorator_list
                if hasattr(d, 'id')
            ) or any(
                hasattr(d, 'attr') and d.attr == 'fixture' for d in node.decorator_list
                if hasattr(d, 'attr')
            ):
                analysis['fixtures'].append(node.name)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                analysis['imports'].append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                analysis['imports'].append(f"{module}.{alias.name}")

    return analysis

def validate_test_coverage(analysis: Dict[str, any]) -> Dict[str, any]:
    """Validate test coverage against requirements"""

    validation = {
        'total_tests': len(analysis['test_methods']),
        'total_fixtures': len(analysis['fixtures']),
        'coverage_by_category': {},
        'missing_coverage': [],
        'recommendations': []
    }

    # Required test categories and minimum test counts
    requirements = {
        'fragment_analytics': 3,  # At least 3 tests for fragment analytics
        'choice_distribution': 2,  # At least 2 tests for choice analysis
        'bottlenecks': 2,  # At least 2 tests for bottleneck detection
        'user_segments': 1,  # At least 1 test for user segmentation
        'conversion_funnel': 1,  # At least 1 test for funnel tracking
        'character_voice': 3,  # At least 3 tests for character analytics (key requirement)
        'data_export': 4,  # At least 4 tests for export functionality
        'performance': 2,  # At least 2 performance tests
        'error_handling': 4,  # At least 4 error handling tests
        'integration': 1   # At least 1 integration test
    }

    # Check coverage
    for category, min_tests in requirements.items():
        actual_tests = len(analysis['test_categories'][category])
        validation['coverage_by_category'][category] = {
            'required': min_tests,
            'actual': actual_tests,
            'meets_requirement': actual_tests >= min_tests,
            'tests': analysis['test_categories'][category]
        }

        if actual_tests < min_tests:
            validation['missing_coverage'].append(f"{category}: {actual_tests}/{min_tests} tests")

    # Generate recommendations
    if validation['total_tests'] >= 30:
        validation['recommendations'].append("✓ Excellent test coverage with 30+ test methods")
    elif validation['total_tests'] >= 20:
        validation['recommendations'].append("✓ Good test coverage with 20+ test methods")
    else:
        validation['recommendations'].append("⚠ Consider adding more test methods for comprehensive coverage")

    if validation['total_fixtures'] >= 5:
        validation['recommendations'].append("✓ Good fixture coverage for test setup")

    # Check for essential fixtures
    essential_fixtures = ['mock_session', 'analytics_service', 'sample_fragment_analytics', 'sample_user_journey_analytics']
    missing_fixtures = [f for f in essential_fixtures if f not in analysis['fixtures']]
    if not missing_fixtures:
        validation['recommendations'].append("✓ All essential fixtures are present")
    else:
        validation['recommendations'].append(f"⚠ Missing fixtures: {missing_fixtures}")

    return validation

def check_requirements_compliance(analysis: Dict[str, any]) -> Dict[str, any]:
    """Check compliance with specific requirements"""

    compliance = {
        'requirement_4_1': {
            'description': 'Comprehensive Analytics and User Journey Tracking',
            'tests': [],
            'compliant': False
        },
        'requirement_4_3': {
            'description': 'Character Voice Analytics',
            'tests': [],
            'compliant': False
        }
    }

    # Check requirement 4.1 compliance
    req_4_1_tests = (
        analysis['test_categories']['fragment_analytics'] +
        analysis['test_categories']['user_segments'] +
        analysis['test_categories']['conversion_funnel'] +
        analysis['test_categories']['data_export']
    )
    compliance['requirement_4_1']['tests'] = req_4_1_tests
    compliance['requirement_4_1']['compliant'] = len(req_4_1_tests) >= 8

    # Check requirement 4.3 compliance
    req_4_3_tests = analysis['test_categories']['character_voice']
    compliance['requirement_4_3']['tests'] = req_4_3_tests
    compliance['requirement_4_3']['compliant'] = len(req_4_3_tests) >= 3

    return compliance

def main():
    """Main validation function"""

    test_file_path = 'tests/services/test_analytics_service.py'

    if not os.path.exists(test_file_path):
        print(f"❌ Test file not found: {test_file_path}")
        return

    print("🔍 Analyzing Analytics Service Test Coverage")
    print("=" * 50)

    # Analyze the test file
    analysis = analyze_test_file(test_file_path)

    print(f"📊 Test File Analysis:")
    print(f"  • Classes: {len(analysis['classes'])}")
    print(f"  • Test Methods: {len(analysis['test_methods'])}")
    print(f"  • Fixtures: {len(analysis['fixtures'])}")
    print()

    # Validate coverage
    validation = validate_test_coverage(analysis)

    print("📈 Test Coverage by Category:")
    for category, data in validation['coverage_by_category'].items():
        status = "✅" if data['meets_requirement'] else "❌"
        print(f"  {status} {category.replace('_', ' ').title()}: {data['actual']}/{data['required']} tests")

    print()

    # Check requirements compliance
    compliance = check_requirements_compliance(analysis)

    print("📋 Requirements Compliance:")
    for req, data in compliance.items():
        status = "✅" if data['compliant'] else "❌"
        print(f"  {status} {req.upper()}: {data['description']}")
        print(f"     Tests: {len(data['tests'])}")

    print()

    print("💡 Recommendations:")
    for rec in validation['recommendations']:
        print(f"  {rec}")

    if validation['missing_coverage']:
        print("\n⚠️  Missing Coverage:")
        for missing in validation['missing_coverage']:
            print(f"  • {missing}")

    print()

    # Summary
    total_coverage = sum(1 for data in validation['coverage_by_category'].values() if data['meets_requirement'])
    total_requirements = len(validation['coverage_by_category'])
    coverage_percentage = (total_coverage / total_requirements) * 100

    if coverage_percentage >= 90:
        print(f"🎉 Excellent! Coverage: {coverage_percentage:.1f}% ({total_coverage}/{total_requirements} categories)")
    elif coverage_percentage >= 70:
        print(f"👍 Good coverage: {coverage_percentage:.1f}% ({total_coverage}/{total_requirements} categories)")
    else:
        print(f"⚠️  Needs improvement: {coverage_percentage:.1f}% ({total_coverage}/{total_requirements} categories)")

    print("\n✅ Test file validation completed!")

if __name__ == "__main__":
    main()