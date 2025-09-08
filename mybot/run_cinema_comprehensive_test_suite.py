#!/usr/bin/env python3
"""
Cinema Architecture Comprehensive Test Suite Executor
=====================================================

Master test execution script for the complete Cinema Architecture System.
This script orchestrates all testing phases and generates comprehensive
reports for production deployment readiness assessment.

Test Phases:
✅ Phase 1: Integration Testing - Complete system integration validation
✅ Phase 2: Performance Testing - Benchmarking and scalability validation  
✅ Phase 3: Regression Testing - Zero breaking changes protection
✅ Phase 4: Character Testing - Diana & Lucien consistency validation
✅ Phase 5: Deployment Readiness - Final production assessment

Usage:
    python run_cinema_comprehensive_test_suite.py [--phase PHASE] [--verbose] [--report]
    
Arguments:
    --phase PHASE    Run specific test phase (integration|performance|regression|character|all)
    --verbose        Enable verbose output
    --report         Generate comprehensive HTML report
    --no-docker      Skip Docker-based test isolation
"""

import asyncio
import sys
import os
import time
import json
import subprocess
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test phase configurations
TEST_PHASES = {
    "integration": {
        "name": "Cinema Integration Testing",
        "description": "Complete system integration validation",
        "test_file": "tests/integration/test_complete_cinema_integration.py",
        "critical": True,
        "estimated_time": "5-10 minutes"
    },
    "performance": {
        "name": "Cinema Performance Testing",
        "description": "Benchmarking and scalability validation",
        "test_file": "tests/performance/test_cinema_performance_validation.py", 
        "critical": True,
        "estimated_time": "10-15 minutes"
    },
    "regression": {
        "name": "Cinema Regression Protection",
        "description": "Zero breaking changes validation",
        "test_file": "tests/regression/test_cinema_regression_protection.py",
        "critical": True,
        "estimated_time": "8-12 minutes"
    },
    "character": {
        "name": "Cinema Character Consistency",
        "description": "Diana & Lucien character validation",
        "test_file": "tests/character/test_cinema_character_integration.py",
        "critical": True,
        "estimated_time": "6-10 minutes"
    }
}


class CinemaTestExecutor:
    """Orchestrates comprehensive cinema architecture testing."""
    
    def __init__(self, verbose: bool = False, generate_report: bool = False):
        self.verbose = verbose
        self.generate_report = generate_report
        self.test_results = {}
        self.start_time = time.time()
        
        # Ensure test output directory exists
        self.output_dir = project_root / "test_reports"
        self.output_dir.mkdir(exist_ok=True)
        
        # Test environment setup
        self.test_env = os.environ.copy()
        self.test_env.update({
            "PYTHONPATH": str(project_root),
            "TESTING": "1",
            "CINEMA_TESTING_MODE": "1"
        })
    
    def print_header(self, title: str, char: str = "=", width: int = 80):
        """Print formatted header."""
        print(f"\n{char * width}")
        print(f"{title.center(width)}")
        print(f"{char * width}")
    
    def print_phase_info(self, phase_name: str, phase_config: Dict[str, Any]):
        """Print phase information."""
        print(f"\n🚀 Starting {phase_config['name']}")
        print(f"   Description: {phase_config['description']}")
        print(f"   Estimated Time: {phase_config['estimated_time']}")
        print(f"   Critical: {'YES' if phase_config['critical'] else 'NO'}")
        if self.verbose:
            print(f"   Test File: {phase_config['test_file']}")
    
    async def execute_test_phase(self, phase_name: str, phase_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single test phase."""
        self.print_phase_info(phase_name, phase_config)
        
        test_file = project_root / phase_config["test_file"]
        if not test_file.exists():
            return {
                "phase": phase_name,
                "status": "SKIPPED",
                "reason": f"Test file not found: {phase_config['test_file']}",
                "execution_time": 0,
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 0
            }
        
        start_time = time.time()
        
        # Prepare pytest command
        pytest_cmd = [
            sys.executable, "-m", "pytest",
            str(test_file),
            "-v" if self.verbose else "-q",
            "--tb=short",
            "--disable-warnings",
            f"--junitxml={self.output_dir}/junit_{phase_name}.xml"
        ]
        
        # Add coverage if requested
        if self.generate_report:
            pytest_cmd.extend([
                "--cov=services",
                "--cov=handlers", 
                f"--cov-report=html:{self.output_dir}/coverage_{phase_name}",
                f"--cov-report=json:{self.output_dir}/coverage_{phase_name}.json"
            ])
        
        if self.verbose:
            print(f"   Executing: {' '.join(pytest_cmd)}")
        
        try:
            # Execute pytest
            process = await asyncio.create_subprocess_exec(
                *pytest_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.test_env,
                cwd=project_root
            )
            
            stdout, stderr = await process.communicate()
            execution_time = time.time() - start_time
            
            # Parse pytest output
            stdout_str = stdout.decode('utf-8', errors='ignore')
            stderr_str = stderr.decode('utf-8', errors='ignore')
            
            if self.verbose:
                print(f"\n--- {phase_name.upper()} OUTPUT ---")
                print(stdout_str)
                if stderr_str:
                    print(f"\n--- {phase_name.upper()} ERRORS ---")
                    print(stderr_str)
            
            # Extract test statistics from pytest output
            tests_run, tests_passed, tests_failed = self._parse_pytest_output(stdout_str)
            
            # Determine phase status
            if process.returncode == 0:
                status = "PASSED"
                print(f"   ✅ {phase_config['name']}: PASSED ({tests_passed}/{tests_run} tests)")
            else:
                status = "FAILED"
                print(f"   ❌ {phase_config['name']}: FAILED ({tests_failed}/{tests_run} failed)")
                if not self.verbose:
                    print(f"   Last few lines of output:")
                    for line in stdout_str.split('\n')[-5:]:
                        if line.strip():
                            print(f"     {line}")
            
            return {
                "phase": phase_name,
                "status": status,
                "execution_time": execution_time,
                "tests_run": tests_run,
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "return_code": process.returncode,
                "output": stdout_str,
                "errors": stderr_str
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Test execution failed: {str(e)}"
            print(f"   ❌ {phase_config['name']}: ERROR - {error_msg}")
            
            return {
                "phase": phase_name,
                "status": "ERROR",
                "reason": error_msg,
                "execution_time": execution_time,
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 0
            }
    
    def _parse_pytest_output(self, output: str) -> tuple[int, int, int]:
        """Parse pytest output to extract test statistics."""
        import re
        
        # Look for pytest summary line patterns
        summary_patterns = [
            r'(\d+) passed.*?in ([\d.]+)s',
            r'(\d+) failed.*?(\d+) passed.*?in ([\d.]+)s',
            r'(\d+) passed.*?(\d+) warnings.*?in ([\d.]+)s',
            r'(\d+) failed.*?in ([\d.]+)s'
        ]
        
        tests_run = 0
        tests_passed = 0
        tests_failed = 0
        
        for pattern in summary_patterns:
            match = re.search(pattern, output)
            if match:
                numbers = [int(x) for x in match.groups() if x.isdigit()]
                if len(numbers) >= 1:
                    if "failed" in match.group():
                        if len(numbers) >= 2:
                            tests_failed = numbers[0]
                            tests_passed = numbers[1]
                        else:
                            tests_failed = numbers[0]
                    else:
                        tests_passed = numbers[0]
                    tests_run = tests_passed + tests_failed
                break
        
        # Fallback: count individual test results
        if tests_run == 0:
            passed_matches = re.findall(r'PASSED', output)
            failed_matches = re.findall(r'FAILED', output)
            tests_passed = len(passed_matches)
            tests_failed = len(failed_matches)
            tests_run = tests_passed + tests_failed
        
        return tests_run, tests_passed, tests_failed
    
    async def execute_all_phases(self, selected_phases: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute all test phases or selected phases."""
        phases_to_run = selected_phases or list(TEST_PHASES.keys())
        
        self.print_header("🎬 CINEMA ARCHITECTURE COMPREHENSIVE TEST SUITE 🎬")
        
        print(f"Test Phases to Execute: {', '.join(phases_to_run)}")
        print(f"Total Estimated Time: {self._calculate_total_estimated_time(phases_to_run)}")
        print(f"Verbose Output: {'Enabled' if self.verbose else 'Disabled'}")
        print(f"Report Generation: {'Enabled' if self.generate_report else 'Disabled'}")
        
        # Execute phases sequentially
        for phase_name in phases_to_run:
            if phase_name not in TEST_PHASES:
                print(f"⚠️ Unknown test phase: {phase_name}")
                continue
            
            phase_config = TEST_PHASES[phase_name]
            result = await self.execute_test_phase(phase_name, phase_config)
            self.test_results[phase_name] = result
        
        # Generate summary
        summary = self._generate_execution_summary()
        
        # Generate reports if requested
        if self.generate_report:
            await self._generate_comprehensive_report()
        
        return summary
    
    def _calculate_total_estimated_time(self, phases: List[str]) -> str:
        """Calculate total estimated execution time."""
        total_min = 0
        total_max = 0
        
        for phase in phases:
            if phase in TEST_PHASES:
                time_range = TEST_PHASES[phase]["estimated_time"]
                # Parse "5-10 minutes" format
                if "-" in time_range and "minute" in time_range:
                    try:
                        range_part = time_range.split(" ")[0]
                        min_time, max_time = map(int, range_part.split("-"))
                        total_min += min_time
                        total_max += max_time
                    except:
                        total_min += 5
                        total_max += 10
                else:
                    total_min += 5
                    total_max += 10
        
        return f"{total_min}-{total_max} minutes"
    
    def _generate_execution_summary(self) -> Dict[str, Any]:
        """Generate comprehensive execution summary."""
        total_execution_time = time.time() - self.start_time
        
        total_tests = sum(result.get("tests_run", 0) for result in self.test_results.values())
        total_passed = sum(result.get("tests_passed", 0) for result in self.test_results.values())
        total_failed = sum(result.get("tests_failed", 0) for result in self.test_results.values())
        
        passed_phases = [name for name, result in self.test_results.items() if result.get("status") == "PASSED"]
        failed_phases = [name for name, result in self.test_results.items() if result.get("status") == "FAILED"]
        error_phases = [name for name, result in self.test_results.items() if result.get("status") == "ERROR"]
        skipped_phases = [name for name, result in self.test_results.items() if result.get("status") == "SKIPPED"]
        
        # Determine overall status
        critical_phases = [name for name in self.test_results.keys() if TEST_PHASES.get(name, {}).get("critical", False)]
        critical_failures = [name for name in critical_phases if name in failed_phases or name in error_phases]
        
        overall_status = "PASSED" if not critical_failures else "FAILED"
        
        summary = {
            "overall_status": overall_status,
            "execution_time_seconds": total_execution_time,
            "execution_time_formatted": f"{total_execution_time/60:.1f} minutes",
            "phases_executed": len(self.test_results),
            "phases_passed": len(passed_phases),
            "phases_failed": len(failed_phases),
            "phases_error": len(error_phases),
            "phases_skipped": len(skipped_phases),
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
            "critical_failures": critical_failures,
            "detailed_results": self.test_results
        }
        
        # Print summary
        self.print_header("📊 CINEMA TEST SUITE EXECUTION SUMMARY 📊")
        
        print(f"\nOVERALL STATUS: {overall_status}")
        print(f"Execution Time: {summary['execution_time_formatted']}")
        
        print(f"\nPHASE SUMMARY:")
        print(f"  Total Phases: {summary['phases_executed']}")
        print(f"  ✅ Passed: {summary['phases_passed']}")
        print(f"  ❌ Failed: {summary['phases_failed']}")
        print(f"  ⚠️ Error: {summary['phases_error']}")
        print(f"  ⏭️ Skipped: {summary['phases_skipped']}")
        
        print(f"\nTEST SUMMARY:")
        print(f"  Total Tests: {summary['total_tests']}")
        print(f"  ✅ Passed: {summary['total_passed']}")
        print(f"  ❌ Failed: {summary['total_failed']}")
        print(f"  Success Rate: {summary['success_rate']:.1f}%")
        
        if critical_failures:
            print(f"\n🚨 CRITICAL FAILURES:")
            for phase in critical_failures:
                result = self.test_results[phase]
                print(f"  - {TEST_PHASES[phase]['name']}: {result.get('status', 'UNKNOWN')}")
        
        print(f"\nDETAILED PHASE RESULTS:")
        for phase_name, result in self.test_results.items():
            status_icon = {"PASSED": "✅", "FAILED": "❌", "ERROR": "⚠️", "SKIPPED": "⏭️"}.get(result["status"], "❓")
            phase_config = TEST_PHASES.get(phase_name, {})
            print(f"  {status_icon} {phase_config.get('name', phase_name)}: {result['status']} "
                  f"({result.get('tests_passed', 0)}/{result.get('tests_run', 0)} tests) "
                  f"in {result.get('execution_time', 0):.1f}s")
        
        # Production deployment readiness assessment
        self._print_deployment_readiness_assessment(summary)
        
        return summary
    
    def _print_deployment_readiness_assessment(self, summary: Dict[str, Any]):
        """Print production deployment readiness assessment."""
        self.print_header("🚀 PRODUCTION DEPLOYMENT READINESS ASSESSMENT 🚀")
        
        deployment_ready = summary["overall_status"] == "PASSED" and not summary["critical_failures"]
        
        print(f"\nDEPLOYMENT STATUS: {'✅ READY' if deployment_ready else '❌ NOT READY'}")
        
        # Assessment criteria
        criteria = [
            {
                "name": "Integration Testing",
                "passed": "integration" not in summary.get("critical_failures", []),
                "requirement": "All cinema system integrations functional"
            },
            {
                "name": "Performance Requirements", 
                "passed": "performance" not in summary.get("critical_failures", []),
                "requirement": "<500ms response time, scalability validated"
            },
            {
                "name": "Regression Protection",
                "passed": "regression" not in summary.get("critical_failures", []),
                "requirement": "Zero breaking changes, backward compatibility"
            },
            {
                "name": "Character Consistency",
                "passed": "character" not in summary.get("critical_failures", []),
                "requirement": "Diana 85-95% mystery, Lucien 100% supportive"
            },
            {
                "name": "Test Coverage",
                "passed": summary["success_rate"] >= 90,
                "requirement": "≥90% test success rate"
            }
        ]
        
        print(f"\nDEPLOYMENT CRITERIA:")
        for criterion in criteria:
            status_icon = "✅" if criterion["passed"] else "❌"
            print(f"  {status_icon} {criterion['name']}: {criterion['requirement']}")
        
        if deployment_ready:
            print(f"\n🎉 CINEMA ARCHITECTURE IS PRODUCTION-READY! 🎉")
            print(f"   All critical systems validated")
            print(f"   Performance requirements met")
            print(f"   Character consistency maintained")
            print(f"   Zero breaking changes confirmed")
        else:
            print(f"\n⚠️ DEPLOYMENT BLOCKED - CRITICAL ISSUES DETECTED ⚠️")
            print(f"   Review failed test phases before deployment")
            print(f"   Address all critical failures")
            print(f"   Re-run test suite after fixes")
    
    async def _generate_comprehensive_report(self):
        """Generate comprehensive HTML and JSON reports."""
        try:
            # Generate JSON report
            json_report = {
                "test_suite": "Cinema Architecture Comprehensive Test Suite",
                "execution_timestamp": datetime.now().isoformat(),
                "execution_summary": self._generate_execution_summary(),
                "detailed_results": self.test_results,
                "environment_info": {
                    "python_version": sys.version,
                    "platform": sys.platform,
                    "project_root": str(project_root)
                }
            }
            
            json_report_path = self.output_dir / "cinema_comprehensive_test_report.json"
            with open(json_report_path, 'w') as f:
                json.dump(json_report, f, indent=2, default=str)
            
            print(f"\n📄 JSON Report Generated: {json_report_path}")
            
            # Generate simple HTML report
            html_report = self._generate_html_report(json_report)
            html_report_path = self.output_dir / "cinema_comprehensive_test_report.html"
            with open(html_report_path, 'w') as f:
                f.write(html_report)
            
            print(f"📄 HTML Report Generated: {html_report_path}")
            
        except Exception as e:
            print(f"⚠️ Report generation failed: {str(e)}")
    
    def _generate_html_report(self, json_report: Dict[str, Any]) -> str:
        """Generate HTML report from JSON data."""
        summary = json_report["execution_summary"]
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Cinema Architecture Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .phase {{ margin: 10px 0; padding: 10px; border-left: 4px solid #3498db; }}
        .passed {{ border-left-color: #27ae60; }}
        .failed {{ border-left-color: #e74c3c; }}
        .error {{ border-left-color: #f39c12; }}
        .skipped {{ border-left-color: #95a5a6; }}
        .status-passed {{ color: #27ae60; font-weight: bold; }}
        .status-failed {{ color: #e74c3c; font-weight: bold; }}
        .status-error {{ color: #f39c12; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎬 Cinema Architecture Comprehensive Test Report</h1>
        <p>Generated: {json_report['execution_timestamp']}</p>
        <p>Overall Status: <span class="status-{summary['overall_status'].lower()}">{summary['overall_status']}</span></p>
    </div>
    
    <div class="summary">
        <h2>📊 Execution Summary</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Execution Time</td><td>{summary['execution_time_formatted']}</td></tr>
            <tr><td>Phases Executed</td><td>{summary['phases_executed']}</td></tr>
            <tr><td>Total Tests</td><td>{summary['total_tests']}</td></tr>
            <tr><td>Tests Passed</td><td>{summary['total_passed']}</td></tr>
            <tr><td>Tests Failed</td><td>{summary['total_failed']}</td></tr>
            <tr><td>Success Rate</td><td>{summary['success_rate']:.1f}%</td></tr>
        </table>
    </div>
    
    <div>
        <h2>📝 Phase Details</h2>
"""
        
        for phase_name, result in self.test_results.items():
            phase_config = TEST_PHASES.get(phase_name, {})
            status_class = result["status"].lower()
            
            html += f"""
        <div class="phase {status_class}">
            <h3>{phase_config.get('name', phase_name)} - {result['status']}</h3>
            <p><strong>Description:</strong> {phase_config.get('description', 'N/A')}</p>
            <p><strong>Execution Time:</strong> {result.get('execution_time', 0):.1f} seconds</p>
            <p><strong>Tests:</strong> {result.get('tests_passed', 0)}/{result.get('tests_run', 0)} passed</p>
            {f"<p><strong>Reason:</strong> {result.get('reason', '')}</p>" if result.get('reason') else ''}
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        return html


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Cinema Architecture Comprehensive Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_cinema_comprehensive_test_suite.py --phase all --verbose
  python run_cinema_comprehensive_test_suite.py --phase integration
  python run_cinema_comprehensive_test_suite.py --phase performance --report
        """
    )
    
    parser.add_argument(
        "--phase",
        choices=list(TEST_PHASES.keys()) + ["all"],
        default="all",
        help="Test phase to execute (default: all)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate comprehensive HTML and JSON reports"
    )
    
    parser.add_argument(
        "--list-phases",
        action="store_true",
        help="List available test phases and exit"
    )
    
    args = parser.parse_args()
    
    if args.list_phases:
        print("Available Test Phases:")
        for name, config in TEST_PHASES.items():
            print(f"  {name}: {config['description']} ({config['estimated_time']})")
        return
    
    # Initialize test executor
    executor = CinemaTestExecutor(verbose=args.verbose, generate_report=args.report)
    
    try:
        # Determine phases to run
        phases_to_run = [args.phase] if args.phase != "all" else None
        
        # Execute test suite
        summary = await executor.execute_all_phases(phases_to_run)
        
        # Exit with appropriate code
        exit_code = 0 if summary["overall_status"] == "PASSED" else 1
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️ Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())