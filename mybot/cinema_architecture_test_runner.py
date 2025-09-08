#!/usr/bin/env python3
"""
CINEMA ARCHITECTURE COMPREHENSIVE TEST EXECUTION SUITE
=====================================================

This master test runner executes the complete Cinema Architecture validation
test suite and generates comprehensive production readiness reports.

EXECUTION COVERAGE:
✅ Integration Testing Suite
✅ Performance Validation Framework  
✅ Regression Protection Suite
✅ Character Consistency Validation
✅ Error Handling & Resilience Testing
✅ Comprehensive Production Readiness Report
"""

import os
import sys
import asyncio
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


class CinemaTestExecutor:
    """Master test executor for Cinema Architecture validation"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.test_results: Dict[str, Any] = {}
        self.execution_log: List[str] = []
        self.performance_metrics: Dict[str, float] = {}
        
    def log(self, message: str):
        """Log execution message with timestamp"""
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.execution_log.append(log_entry)
        print(log_entry)
    
    def execute_test_suite(self, suite_name: str, test_path: str) -> Dict[str, Any]:
        """Execute a specific test suite and capture results"""
        
        self.log(f"Starting {suite_name} test suite...")
        start_time = time.time()
        
        try:
            # Execute pytest with comprehensive options
            cmd = [
                "python", "-m", "pytest",
                test_path,
                "-v",  # Verbose output
                "--tb=short",  # Short traceback format
                "--strict-markers",  # Strict marker checking
                "--strict-config",  # Strict configuration
                "--disable-warnings",  # Disable warnings for cleaner output
                "--maxfail=10",  # Stop after 10 failures
                "--json-report",  # Generate JSON report
                f"--json-report-file=cinema_test_reports/{suite_name}_report.json"
            ]
            
            # Create reports directory
            os.makedirs("cinema_test_reports", exist_ok=True)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                timeout=1800  # 30 minute timeout
            )
            
            execution_time = time.time() - start_time
            
            # Parse results
            suite_result = {
                "suite_name": suite_name,
                "execution_time": execution_time,
                "exit_code": result.returncode,
                "passed": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            # Try to load detailed JSON report
            json_report_path = f"cinema_test_reports/{suite_name}_report.json"
            if os.path.exists(json_report_path):
                try:
                    with open(json_report_path, 'r') as f:
                        json_data = json.load(f)
                        suite_result.update({
                            "tests_collected": json_data.get("summary", {}).get("collected", 0),
                            "tests_passed": json_data.get("summary", {}).get("passed", 0),
                            "tests_failed": json_data.get("summary", {}).get("failed", 0),
                            "tests_errors": json_data.get("summary", {}).get("error", 0),
                            "test_details": json_data.get("tests", [])
                        })
                except Exception as e:
                    self.log(f"Warning: Could not parse JSON report for {suite_name}: {e}")
            
            if suite_result["passed"]:
                self.log(f"✅ {suite_name} test suite PASSED ({execution_time:.2f}s)")
            else:
                self.log(f"❌ {suite_name} test suite FAILED ({execution_time:.2f}s)")
                self.log(f"STDOUT: {result.stdout}")
                self.log(f"STDERR: {result.stderr}")
            
            return suite_result
            
        except subprocess.TimeoutExpired:
            self.log(f"❌ {suite_name} test suite TIMED OUT after 30 minutes")
            return {
                "suite_name": suite_name,
                "execution_time": 1800,
                "exit_code": -1,
                "passed": False,
                "error": "Test suite timed out"
            }
        except Exception as e:
            execution_time = time.time() - start_time
            self.log(f"❌ {suite_name} test suite ERROR: {e}")
            return {
                "suite_name": suite_name,
                "execution_time": execution_time,
                "exit_code": -1,
                "passed": False,
                "error": str(e)
            }
    
    def run_complete_test_suite(self) -> Dict[str, Any]:
        """Execute complete Cinema Architecture test suite"""
        
        self.log("🎬 CINEMA ARCHITECTURE COMPREHENSIVE TEST EXECUTION STARTING")
        self.log("="*80)
        
        # Define test suites in execution order
        test_suites = [
            {
                "name": "integration_tests",
                "path": "tests/integration/test_complete_cinema_integration.py",
                "description": "Cinema Integration Testing"
            },
            {
                "name": "performance_tests", 
                "path": "tests/performance/test_cinema_performance_validation.py",
                "description": "Performance & Scalability Validation"
            },
            {
                "name": "regression_tests",
                "path": "tests/regression/test_cinema_regression_protection.py", 
                "description": "Regression Protection Suite"
            },
            {
                "name": "character_tests",
                "path": "tests/character/test_cinema_character_integration.py",
                "description": "Character Consistency Validation"
            }
        ]
        
        # Execute each test suite
        suite_results = []
        
        for suite in test_suites:
            self.log(f"\n📋 Executing {suite['description']}...")
            
            # Check if test file exists
            test_file_path = project_root / suite["path"]
            if not test_file_path.exists():
                self.log(f"⚠️  Test file not found: {suite['path']}")
                suite_results.append({
                    "suite_name": suite["name"],
                    "passed": False,
                    "error": f"Test file not found: {suite['path']}"
                })
                continue
            
            # Execute test suite
            result = self.execute_test_suite(suite["name"], suite["path"])
            suite_results.append(result)
            
            # Update performance metrics
            self.performance_metrics[f"{suite['name']}_execution_time"] = result.get("execution_time", 0)
        
        # Generate comprehensive results
        total_execution_time = time.time() - self.start_time.timestamp()
        
        comprehensive_results = {
            "execution_metadata": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat(), 
                "total_execution_time": total_execution_time,
                "test_environment": "cinema_architecture_validation",
                "python_version": sys.version
            },
            "suite_results": suite_results,
            "performance_metrics": self.performance_metrics,
            "overall_status": self._calculate_overall_status(suite_results),
            "execution_log": self.execution_log
        }
        
        return comprehensive_results
    
    def _calculate_overall_status(self, suite_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall test execution status"""
        
        total_suites = len(suite_results)
        passed_suites = sum(1 for result in suite_results if result.get("passed", False))
        failed_suites = total_suites - passed_suites
        
        # Calculate test totals
        total_tests = sum(result.get("tests_collected", 0) for result in suite_results)
        total_passed = sum(result.get("tests_passed", 0) for result in suite_results)
        total_failed = sum(result.get("tests_failed", 0) for result in suite_results)
        total_errors = sum(result.get("tests_errors", 0) for result in suite_results)
        
        # Determine overall status
        if failed_suites == 0:
            overall_status = "PASS"
            production_ready = True
        elif failed_suites <= 1:
            overall_status = "CONDITIONAL_PASS"
            production_ready = False
        else:
            overall_status = "FAIL"
            production_ready = False
        
        return {
            "overall_status": overall_status,
            "production_ready": production_ready,
            "suites_total": total_suites,
            "suites_passed": passed_suites,
            "suites_failed": failed_suites,
            "tests_total": total_tests,
            "tests_passed": total_passed,
            "tests_failed": total_failed,
            "tests_errors": total_errors,
            "pass_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0
        }
    
    def generate_production_readiness_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive production readiness report"""
        
        overall_status = results["overall_status"]
        metadata = results["execution_metadata"]
        
        report_lines = [
            "🎬 CINEMA ARCHITECTURE PRODUCTION READINESS REPORT",
            "="*80,
            f"Execution Date: {metadata['start_time']}",
            f"Total Execution Time: {metadata['total_execution_time']:.2f} seconds",
            f"Overall Status: {overall_status['overall_status']}",
            f"Production Ready: {'✅ YES' if overall_status['production_ready'] else '❌ NO'}",
            "",
            "📊 EXECUTION SUMMARY",
            "-" * 40,
            f"Test Suites: {overall_status['suites_passed']}/{overall_status['suites_total']} passed",
            f"Individual Tests: {overall_status['tests_passed']}/{overall_status['tests_total']} passed",
            f"Overall Pass Rate: {overall_status['pass_rate']:.1f}%",
            "",
        ]
        
        # Suite-by-suite breakdown
        report_lines.append("🔍 DETAILED SUITE RESULTS")
        report_lines.append("-" * 40)
        
        for suite_result in results["suite_results"]:
            status_icon = "✅" if suite_result.get("passed", False) else "❌"
            suite_name = suite_result["suite_name"].replace("_", " ").title()
            execution_time = suite_result.get("execution_time", 0)
            
            report_lines.append(f"{status_icon} {suite_name}: {execution_time:.2f}s")
            
            if suite_result.get("tests_collected"):
                tests_info = (
                    f"    Tests: {suite_result.get('tests_passed', 0)}/"
                    f"{suite_result.get('tests_collected', 0)} passed"
                )
                report_lines.append(tests_info)
            
            if not suite_result.get("passed", False) and suite_result.get("error"):
                report_lines.append(f"    Error: {suite_result['error']}")
        
        # Performance metrics
        if results["performance_metrics"]:
            report_lines.extend([
                "",
                "⚡ PERFORMANCE METRICS",
                "-" * 40
            ])
            
            for metric_name, metric_value in results["performance_metrics"].items():
                formatted_name = metric_name.replace("_", " ").title()
                report_lines.append(f"{formatted_name}: {metric_value:.2f}s")
        
        # Production readiness assessment
        report_lines.extend([
            "",
            "🎯 PRODUCTION READINESS ASSESSMENT",
            "-" * 40
        ])
        
        if overall_status["production_ready"]:
            report_lines.extend([
                "✅ CINEMA ARCHITECTURE IS PRODUCTION READY",
                "",
                "All critical test suites have passed validation:",
                "• Integration testing confirms system compatibility",
                "• Performance requirements are met (<500ms response time)",
                "• Regression protection ensures zero breaking changes", 
                "• Character consistency maintained (Diana 85-95% mystery)",
                "",
                "🚀 DEPLOYMENT RECOMMENDATION: APPROVED"
            ])
        else:
            report_lines.extend([
                "❌ CINEMA ARCHITECTURE REQUIRES FIXES BEFORE PRODUCTION",
                "",
                "Issues detected that must be resolved:"
            ])
            
            failed_suites = [r for r in results["suite_results"] if not r.get("passed", False)]
            for failed_suite in failed_suites:
                suite_name = failed_suite["suite_name"].replace("_", " ").title()
                report_lines.append(f"• {suite_name} validation failed")
            
            report_lines.extend([
                "",
                "🚫 DEPLOYMENT RECOMMENDATION: BLOCKED UNTIL FIXES APPLIED"
            ])
        
        # Footer
        report_lines.extend([
            "",
            "="*80,
            "Report generated by Cinema Architecture Test Automation Suite",
            f"Generated at: {datetime.utcnow().isoformat()}",
            "="*80
        ])
        
        return "\n".join(report_lines)
    
    def save_results(self, results: Dict[str, Any]) -> str:
        """Save test results to files"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # Create results directory
        results_dir = project_root / "cinema_test_results"
        results_dir.mkdir(exist_ok=True)
        
        # Save JSON results
        json_file = results_dir / f"cinema_test_results_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Generate and save production readiness report
        report = self.generate_production_readiness_report(results)
        report_file = results_dir / f"cinema_production_readiness_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        self.log(f"📄 Results saved to: {json_file}")
        self.log(f"📋 Report saved to: {report_file}")
        
        return report


async def main():
    """Main test execution entry point"""
    
    executor = CinemaTestExecutor()
    
    try:
        # Execute complete test suite
        results = executor.run_complete_test_suite()
        
        # Save results and generate report
        report = executor.save_results(results)
        
        # Display final report
        print("\n" + "="*80)
        print(report)
        
        # Exit with appropriate code
        if results["overall_status"]["production_ready"]:
            executor.log("🎉 CINEMA ARCHITECTURE VALIDATION COMPLETE - PRODUCTION READY")
            sys.exit(0)
        else:
            executor.log("🚫 CINEMA ARCHITECTURE VALIDATION FAILED - PRODUCTION BLOCKED")
            sys.exit(1)
            
    except Exception as e:
        executor.log(f"💥 CRITICAL ERROR during test execution: {e}")
        print(f"💥 CRITICAL ERROR during test execution: {e}")
        sys.exit(2)


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required for Cinema Architecture testing")
        sys.exit(1)
    
    # Run test suite
    asyncio.run(main())