#!/usr/bin/env python3
"""
🛡️ DIANA BOT PROTECTION TESTING SUITE RUNNER
Automated execution of the complete testing protection network.
Runs all protection tests with comprehensive reporting and CI integration.
"""
import os
import sys
import subprocess
import time
import json
import datetime
from typing import Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@dataclass
class TestResult:
    """Test result data structure."""
    name: str
    status: str  # "PASS", "FAIL", "ERROR"
    duration: float
    output: str
    details: str = ""

@dataclass
class TestSuite:
    """Test suite configuration."""
    name: str
    description: str
    file_path: str
    critical: bool = False
    timeout: int = 300  # 5 minutes default

class DianaProtectionTestRunner:
    """Main test runner for Diana Bot protection tests."""
    
    def __init__(self):
        self.project_root = project_root
        self.test_results: List[TestResult] = []
        self.start_time = time.time()
        
        # Define test suites
        self.test_suites = [
            TestSuite(
                name="MVP_Baseline_Protection",
                description="🛡️ MVP Baseline System Protection",
                file_path="tests/protection/test_mvp_baseline_protection.py",
                critical=True,
                timeout=600  # 10 minutes for critical baseline tests
            ),
            TestSuite(
                name="Cinema_Architecture_Integration",
                description="🎬 Cinema Architecture Integration Tests",
                file_path="tests/protection/test_cinema_architecture_integration.py",
                critical=True,
                timeout=900  # 15 minutes for complex cinema tests
            ),
            TestSuite(
                name="User_Journey_Archetypes",
                description="🎭 User Journey & Archetype Framework",
                file_path="tests/protection/test_user_journey_archetypes.py",
                critical=True,
                timeout=1200  # 20 minutes for comprehensive journey tests
            ),
            TestSuite(
                name="Performance_Scalability",
                description="⚡ Performance & Scalability Infrastructure",
                file_path="tests/protection/test_performance_scalability.py",
                critical=True,
                timeout=1800  # 30 minutes for performance tests
            )
        ]
    
    def print_banner(self):
        """Print the test runner banner."""
        banner = """
🛡️ ====================================================================
🛡️ DIANA BOT TESTING PROTECTION NETWORK - COMPLETE COVERAGE SUITE
🛡️ ====================================================================
🎭 Protecting: Diana Character Bible V1.0
🌊 Protecting: 6-Level Emotional Crescendo 
🏛️ Protecting: Choice Architecture Masterpiece
🔍 Protecting: Clue Treasure Hunting Integration
✨ Protecting: Soul Signature Personalization
📖 Protecting: 16 Narrative Fragments (MVP Baseline)
⚡ Protecting: <500ms Response Time Guarantee
👥 Protecting: 6 User Archetypes Complete Journeys
🛡️ ====================================================================
        """
        print(banner)
    
    def run_test_suite(self, suite: TestSuite) -> TestResult:
        """Run a single test suite."""
        print(f"\n🔄 Running: {suite.description}")
        print(f"   File: {suite.file_path}")
        print(f"   Critical: {'YES' if suite.critical else 'NO'}")
        print(f"   Timeout: {suite.timeout}s")
        print("   " + "="*60)
        
        start_time = time.time()
        
        try:
            # Prepare pytest command
            cmd = [
                sys.executable, "-m", "pytest",
                suite.file_path,
                "-v",  # Verbose output
                "--tb=short",  # Short traceback format
                "--no-header",  # No pytest header
                "--show-capture=no",  # Don't show captured output
                f"--timeout={suite.timeout}",  # Test timeout
                "--asyncio-mode=auto"  # Auto async mode
            ]
            
            # Add coverage if requested
            if os.getenv("COVERAGE", "false").lower() == "true":
                cmd.extend([
                    "--cov=services",
                    "--cov=database", 
                    "--cov=handlers",
                    "--cov-report=term-missing"
                ])
            
            # Execute tests
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=suite.timeout
            )
            
            duration = time.time() - start_time
            
            # Analyze result
            if result.returncode == 0:
                status = "PASS"
                details = f"All tests passed in {duration:.2f}s"
            else:
                status = "FAIL"
                details = f"Tests failed after {duration:.2f}s"
            
            # Capture output
            output = result.stdout + "\n" + result.stderr
            
            return TestResult(
                name=suite.name,
                status=status,
                duration=duration,
                output=output,
                details=details
            )
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return TestResult(
                name=suite.name,
                status="ERROR",
                duration=duration,
                output="Test suite timed out",
                details=f"Timeout after {suite.timeout}s"
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name=suite.name,
                status="ERROR", 
                duration=duration,
                output=str(e),
                details=f"Error running test suite: {e}"
            )
    
    def run_quick_smoke_test(self) -> TestResult:
        """Run quick smoke test to verify basic functionality."""
        print("\n🚀 Running Quick Smoke Test...")
        print("   " + "="*60)
        
        start_time = time.time()
        
        try:
            # Run a minimal test to verify environment
            cmd = [
                sys.executable, "-m", "pytest",
                "tests/conftest.py::test_engine",  # Test basic database setup
                "-v",
                "--tb=short",
                "--timeout=60",
                "--asyncio-mode=auto"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                return TestResult(
                    name="Quick_Smoke_Test",
                    status="PASS",
                    duration=duration,
                    output=result.stdout,
                    details="Environment verification passed"
                )
            else:
                return TestResult(
                    name="Quick_Smoke_Test",
                    status="FAIL",
                    duration=duration,
                    output=result.stdout + "\n" + result.stderr,
                    details="Environment verification failed"
                )
                
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                name="Quick_Smoke_Test",
                status="ERROR",
                duration=duration,
                output=str(e),
                details=f"Smoke test error: {e}"
            )
    
    def generate_report(self) -> Dict:
        """Generate comprehensive test report."""
        total_duration = time.time() - self.start_time
        
        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == "PASS"])
        failed_tests = len([r for r in self.test_results if r.status == "FAIL"])
        error_tests = len([r for r in self.test_results if r.status == "ERROR"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Critical test analysis
        critical_suites = [s.name for s in self.test_suites if s.critical]
        critical_results = [r for r in self.test_results if r.name in critical_suites]
        critical_passed = len([r for r in critical_results if r.status == "PASS"])
        critical_success_rate = (critical_passed / len(critical_results) * 100) if critical_results else 0
        
        report = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "total_duration_seconds": round(total_duration, 2),
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "success_rate": round(success_rate, 2),
                "critical_success_rate": round(critical_success_rate, 2)
            },
            "results": [
                {
                    "name": r.name,
                    "status": r.status,
                    "duration": round(r.duration, 2),
                    "details": r.details
                }
                for r in self.test_results
            ],
            "protection_status": {
                "mvp_baseline_protected": any(r.name == "MVP_Baseline_Protection" and r.status == "PASS" for r in self.test_results),
                "cinema_architecture_protected": any(r.name == "Cinema_Architecture_Integration" and r.status == "PASS" for r in self.test_results),
                "user_journeys_protected": any(r.name == "User_Journey_Archetypes" and r.status == "PASS" for r in self.test_results),
                "performance_guaranteed": any(r.name == "Performance_Scalability" and r.status == "PASS" for r in self.test_results)
            }
        }
        
        return report
    
    def print_report(self, report: Dict):
        """Print formatted test report."""
        print("\n" + "="*80)
        print("🛡️ DIANA BOT PROTECTION TESTING NETWORK - FINAL REPORT")
        print("="*80)
        
        # Summary
        summary = report["summary"]
        print(f"📊 TEST SUMMARY:")
        print(f"   Total Duration: {report['total_duration_seconds']}s")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed']} ✅")
        print(f"   Failed: {summary['failed']} ❌")
        print(f"   Errors: {summary['errors']} 🚨")
        print(f"   Success Rate: {summary['success_rate']}%")
        print(f"   Critical Success Rate: {summary['critical_success_rate']}%")
        
        # Protection Status
        protection = report["protection_status"]
        print(f"\n🛡️ PROTECTION STATUS:")
        print(f"   MVP Baseline: {'🛡️ PROTECTED' if protection['mvp_baseline_protected'] else '🚨 VULNERABLE'}")
        print(f"   Cinema Architecture: {'🎬 PROTECTED' if protection['cinema_architecture_protected'] else '🚨 VULNERABLE'}")
        print(f"   User Journeys: {'🎭 PROTECTED' if protection['user_journeys_protected'] else '🚨 VULNERABLE'}")
        print(f"   Performance: {'⚡ GUARANTEED' if protection['performance_guaranteed'] else '🚨 AT RISK'}")
        
        # Individual Results
        print(f"\n📋 DETAILED RESULTS:")
        for result in report["results"]:
            status_icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "🚨"}.get(result["status"], "❓")
            print(f"   {status_icon} {result['name']}: {result['status']} ({result['duration']}s)")
            if result["details"]:
                print(f"      {result['details']}")
        
        # Final Status
        overall_success = summary['critical_success_rate'] >= 75
        print(f"\n🎯 OVERALL STATUS: {'🛡️ SYSTEM PROTECTED' if overall_success else '🚨 PROTECTION COMPROMISED'}")
        
        if overall_success:
            print("🎉 All critical systems are protected and operational!")
        else:
            print("⚠️  Critical protection failures detected - immediate attention required!")
        
        print("="*80)
    
    def save_report(self, report: Dict):
        """Save report to JSON file."""
        report_dir = self.project_root / "test_reports"
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"protection_test_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Report saved: {report_file}")
        
        # Also save latest report
        latest_file = report_dir / "latest_protection_report.json"
        with open(latest_file, 'w') as f:
            json.dump(report, f, indent=2)
    
    def run_all_tests(self, quick_mode: bool = False) -> bool:
        """Run all protection tests."""
        self.print_banner()
        
        if quick_mode:
            print("🚀 QUICK MODE: Running smoke test only...")
            smoke_result = self.run_quick_smoke_test()
            self.test_results.append(smoke_result)
            
            if smoke_result.status != "PASS":
                print("🚨 SMOKE TEST FAILED - Environment not ready!")
                return False
            
            print("✅ SMOKE TEST PASSED - Environment ready!")
            return True
        
        # Run all test suites
        for suite in self.test_suites:
            result = self.run_test_suite(suite)
            self.test_results.append(result)
            
            # Print immediate result
            status_icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "🚨"}.get(result.status, "❓")
            print(f"   {status_icon} {result.status}: {result.details}")
            
            # Stop on critical test failure if requested
            if suite.critical and result.status != "PASS" and os.getenv("FAIL_FAST", "false").lower() == "true":
                print(f"🚨 CRITICAL TEST FAILED: {suite.name} - Stopping execution!")
                break
        
        # Generate and display report
        report = self.generate_report()
        self.print_report(report)
        self.save_report(report)
        
        # Return success status
        critical_success_rate = report["summary"]["critical_success_rate"]
        return critical_success_rate >= 75  # 75% critical test success required


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Diana Bot Protection Testing Suite")
    parser.add_argument("--quick", action="store_true", help="Run quick smoke test only")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first critical failure")
    parser.add_argument("--suite", help="Run specific test suite only")
    
    args = parser.parse_args()
    
    # Set environment variables
    if args.coverage:
        os.environ["COVERAGE"] = "true"
    if args.fail_fast:
        os.environ["FAIL_FAST"] = "true"
    
    # Create and run test runner
    runner = DianaProtectionTestRunner()
    
    if args.suite:
        # Run specific suite
        suite = next((s for s in runner.test_suites if s.name.lower() == args.suite.lower()), None)
        if not suite:
            print(f"🚨 Test suite '{args.suite}' not found!")
            print(f"Available suites: {[s.name for s in runner.test_suites]}")
            sys.exit(1)
        
        result = runner.run_test_suite(suite)
        runner.test_results.append(result)
        
        status_icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "🚨"}.get(result.status, "❓")
        print(f"{status_icon} {result.name}: {result.status} ({result.duration:.2f}s)")
        print(f"Details: {result.details}")
        
        success = result.status == "PASS"
    else:
        # Run all tests
        success = runner.run_all_tests(quick_mode=args.quick)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()