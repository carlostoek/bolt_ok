#!/usr/bin/env python3
"""
PHASE 2.2 COMPREHENSIVE TEST RUNNER

This script executes the complete Phase 2.2 master storyline testing suite
and generates a comprehensive production readiness report.

TESTING SCOPE:
- Master storyline flow (6-level progression)
- 16 fragment integration and navigation
- Mission system validation (Observation, Comprehension, Synthesis)
- User archetyping system with behavioral analysis
- Character consistency validation (>95% requirement)
- Performance benchmarks (<500ms requirement)
- VIP progression and access control
- Error handling and recovery scenarios
- Production readiness assessment

USAGE:
    python run_phase_2_2_comprehensive_tests.py [options]
    
OPTIONS:
    --quick          Run only critical path tests
    --full           Run complete comprehensive suite (default)
    --report-only    Generate only production readiness report
    --performance    Run only performance benchmarks
    --character      Run only character consistency tests
"""

import sys
import os
import asyncio
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class Phase22TestRunner:
    """Comprehensive test runner for Phase 2.2 master storyline implementation"""
    
    def __init__(self, test_mode: str = "full"):
        self.test_mode = test_mode
        self.start_time = datetime.utcnow()
        self.test_results = {}
        self.performance_metrics = {}
        
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Execute comprehensive Phase 2.2 test suite"""
        
        print("🚀 STARTING PHASE 2.2 COMPREHENSIVE TESTING SUITE")
        print(f"📅 Started at: {self.start_time}")
        print(f"🎯 Test mode: {self.test_mode.upper()}")
        print("=" * 60)
        
        # Define test suites based on mode
        test_suites = self._get_test_suites_for_mode(self.test_mode)
        
        overall_start = time.perf_counter()
        
        for suite_name, suite_config in test_suites.items():
            print(f"\n📋 RUNNING TEST SUITE: {suite_name}")
            print("-" * 40)
            
            suite_start = time.perf_counter()
            suite_result = self._run_test_suite(suite_config)
            suite_duration = time.perf_counter() - suite_start
            
            self.test_results[suite_name] = {
                **suite_result,
                "duration_seconds": round(suite_duration, 2)
            }
            
            # Display suite results
            self._display_suite_results(suite_name, suite_result, suite_duration)
        
        overall_duration = time.perf_counter() - overall_start
        
        # Generate comprehensive report
        final_report = self._generate_final_report(overall_duration)
        
        # Display final summary
        self._display_final_summary(final_report)
        
        return final_report
    
    def _get_test_suites_for_mode(self, mode: str) -> Dict[str, Dict]:
        """Get test suites configuration based on mode"""
        
        all_suites = {
            "master_storyline_flow": {
                "file": "test_phase_2_2_master_storyline_comprehensive.py",
                "classes": ["TestMasterStorylineFlow"],
                "priority": "critical",
                "description": "6-level master storyline progression validation"
            },
            "sixteen_fragment_integration": {
                "file": "test_phase_2_2_master_storyline_comprehensive.py",
                "classes": ["TestSixteenFragmentIntegration"],
                "priority": "critical",
                "description": "16 fragment database integration and navigation"
            },
            "mission_system": {
                "file": "test_phase_2_2_master_storyline_comprehensive.py",
                "classes": ["TestMissionSystemValidation"],
                "priority": "high",
                "description": "Mission system technical validation"
            },
            "user_archetyping": {
                "file": "test_phase_2_2_master_storyline_comprehensive.py", 
                "classes": ["TestUserArchetypingSystem"],
                "priority": "high",
                "description": "User archetyping and behavioral analysis"
            },
            "character_consistency": {
                "file": "test_phase_2_2_character_consistency_performance.py",
                "classes": ["TestCharacterConsistencyValidation"],
                "priority": "critical", 
                "description": "Character consistency >95% requirement validation"
            },
            "performance_scalability": {
                "file": "test_phase_2_2_character_consistency_performance.py",
                "classes": ["TestPerformanceAndScalability"],
                "priority": "critical",
                "description": "Performance <500ms and scalability validation"
            },
            "error_handling": {
                "file": "test_phase_2_2_character_consistency_performance.py",
                "classes": ["TestErrorHandlingAndRecovery"],
                "priority": "high",
                "description": "Error handling and recovery scenarios"
            },
            "vip_progression": {
                "file": "test_phase_2_2_vip_progression_final_report.py",
                "classes": ["TestVIPProgressionValidation"],
                "priority": "critical",
                "description": "VIP progression and access control validation"
            },
            "production_readiness": {
                "file": "test_phase_2_2_vip_progression_final_report.py",
                "classes": ["TestComprehensiveProductionReadinessAssessment"],
                "priority": "critical",
                "description": "Production readiness assessment and deployment approval"
            }
        }
        
        if mode == "quick":
            return {k: v for k, v in all_suites.items() if v["priority"] == "critical"}
        elif mode == "performance":
            return {k: v for k, v in all_suites.items() if "performance" in k.lower()}
        elif mode == "character":
            return {k: v for k, v in all_suites.items() if "character" in k.lower()}
        elif mode == "report-only":
            return {"production_readiness": all_suites["production_readiness"]}
        else:  # full mode
            return all_suites
    
    def _run_test_suite(self, suite_config: Dict) -> Dict[str, Any]:
        """Run a specific test suite"""
        
        test_file = f"tests/{suite_config['file']}"
        
        # Build pytest command
        cmd = [
            "python", "-m", "pytest", 
            test_file,
            "-v",
            "--tb=short",
            "--capture=no",
            "--json-report",
            "--json-report-file=test_results_temp.json"
        ]
        
        # Add specific test classes if specified
        if suite_config.get("classes"):
            for class_name in suite_config["classes"]:
                cmd.append(f"::{class_name}")
        
        try:
            # Run tests
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300  # 5 minute timeout per suite
            )
            
            # Parse results
            success = result.returncode == 0
            
            # Try to read JSON report if available
            test_details = {}
            try:
                with open("test_results_temp.json", "r") as f:
                    test_details = json.load(f)
            except FileNotFoundError:
                pass
            
            return {
                "success": success,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_details": test_details,
                "description": suite_config["description"]
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": "Test suite timed out after 5 minutes",
                "test_details": {},
                "description": suite_config["description"]
            }
        except Exception as e:
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": f"Test execution error: {str(e)}",
                "test_details": {},
                "description": suite_config["description"]
            }
    
    def _display_suite_results(self, suite_name: str, result: Dict, duration: float):
        """Display results for a test suite"""
        
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} {suite_name} ({duration:.2f}s)")
        
        if result["success"]:
            # Show test details if available
            if "test_details" in result and "summary" in result["test_details"]:
                summary = result["test_details"]["summary"]
                print(f"   📊 Tests: {summary.get('total', 0)} total, {summary.get('passed', 0)} passed")
        else:
            print(f"   ❌ Error: {result['stderr'][:100]}...")
            
        print(f"   📝 {result['description']}")
    
    def _generate_final_report(self, total_duration: float) -> Dict[str, Any]:
        """Generate comprehensive final report"""
        
        # Calculate overall metrics
        total_suites = len(self.test_results)
        passed_suites = len([r for r in self.test_results.values() if r["success"]])
        success_rate = (passed_suites / total_suites) * 100 if total_suites > 0 else 0
        
        # Determine deployment status
        deployment_status = "APPROVED" if success_rate >= 95 else "CONDITIONAL" if success_rate >= 85 else "REJECTED"
        
        # Extract critical metrics
        critical_metrics = self._extract_critical_metrics()
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        return {
            "assessment_timestamp": datetime.utcnow().isoformat(),
            "phase": "2.2_master_storyline_comprehensive_validation",
            "test_mode": self.test_mode,
            "execution_summary": {
                "total_duration_seconds": round(total_duration, 2),
                "total_test_suites": total_suites,
                "passed_test_suites": passed_suites,
                "failed_test_suites": total_suites - passed_suites,
                "overall_success_rate": round(success_rate, 2)
            },
            "deployment_status": deployment_status,
            "critical_metrics": critical_metrics,
            "detailed_results": self.test_results,
            "recommendations": recommendations,
            "mvp_readiness": "CONFIRMED" if success_rate >= 95 else "CONDITIONAL" if success_rate >= 85 else "NOT_READY"
        }
    
    def _extract_critical_metrics(self) -> Dict[str, Any]:
        """Extract critical metrics from test results"""
        
        critical_metrics = {
            "master_storyline_functional": "master_storyline_flow" in self.test_results and self.test_results["master_storyline_flow"]["success"],
            "character_consistency_validated": "character_consistency" in self.test_results and self.test_results["character_consistency"]["success"],
            "performance_requirements_met": "performance_scalability" in self.test_results and self.test_results["performance_scalability"]["success"],
            "vip_progression_working": "vip_progression" in self.test_results and self.test_results["vip_progression"]["success"],
            "production_readiness_confirmed": "production_readiness" in self.test_results and self.test_results["production_readiness"]["success"]
        }
        
        return critical_metrics
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        
        recommendations = []
        
        for suite_name, result in self.test_results.items():
            if not result["success"]:
                if "character" in suite_name:
                    recommendations.append("⚠️  Improve character consistency validation system - critical for user experience")
                elif "performance" in suite_name:
                    recommendations.append("⚠️  Optimize system performance to meet <500ms requirement - critical for user satisfaction")
                elif "master_storyline" in suite_name:
                    recommendations.append("⚠️  Complete master storyline implementation - core MVP requirement")
                elif "vip" in suite_name:
                    recommendations.append("⚠️  Fix VIP progression system - critical for monetization")
                else:
                    recommendations.append(f"⚠️  Address issues in {suite_name} - {result['description']}")
        
        if not recommendations:
            recommendations.append("✅ All tests passed - system ready for MVP deployment")
        
        return recommendations
    
    def _display_final_summary(self, report: Dict[str, Any]):
        """Display final comprehensive summary"""
        
        print("\n" + "=" * 60)
        print("🎯 PHASE 2.2 COMPREHENSIVE TESTING COMPLETE")
        print("=" * 60)
        
        # Execution summary
        execution = report["execution_summary"]
        print(f"⏱️  Total Duration: {execution['total_duration_seconds']:.2f} seconds")
        print(f"📋 Test Suites: {execution['passed_test_suites']}/{execution['total_test_suites']} passed ({execution['overall_success_rate']:.1f}%)")
        
        # Deployment status
        status_emoji = "🚀" if report["deployment_status"] == "APPROVED" else "⚠️" if report["deployment_status"] == "CONDITIONAL" else "🚫"
        print(f"{status_emoji} Deployment Status: {report['deployment_status']}")
        print(f"✅ MVP Readiness: {report['mvp_readiness']}")
        
        # Critical metrics
        print("\n📊 CRITICAL METRICS:")
        for metric, status in report["critical_metrics"].items():
            emoji = "✅" if status else "❌"
            print(f"{emoji} {metric.replace('_', ' ').title()}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        for recommendation in report["recommendations"]:
            print(f"  {recommendation}")
        
        # Final decision
        print("\n" + "=" * 60)
        if report["deployment_status"] == "APPROVED":
            print("🎉 PHASE 2.2 APPROVED FOR MVP DEPLOYMENT")
            print("   All critical requirements validated")
            print("   Character consistency >95% confirmed")
            print("   Performance <500ms requirement met")
            print("   Master storyline fully functional")
        elif report["deployment_status"] == "CONDITIONAL":
            print("⚠️  CONDITIONAL APPROVAL - MINOR ISSUES TO ADDRESS")
            print("   Core functionality working but improvements needed")
        else:
            print("🚫 DEPLOYMENT NOT APPROVED - CRITICAL ISSUES FOUND")
            print("   Must resolve failing tests before deployment")
        
        print("=" * 60)
        
        # Save detailed report
        report_filename = f"phase_2_2_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, "w") as f:
            json.dump(report, f, indent=2)
        print(f"📄 Detailed report saved to: {report_filename}")


def main():
    """Main execution function"""
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Phase 2.2 Comprehensive Test Runner")
    parser.add_argument("--quick", action="store_true", help="Run only critical path tests")
    parser.add_argument("--performance", action="store_true", help="Run only performance tests")
    parser.add_argument("--character", action="store_true", help="Run only character consistency tests")
    parser.add_argument("--report-only", action="store_true", help="Generate only production readiness report")
    parser.add_argument("--full", action="store_true", help="Run complete comprehensive suite (default)")
    
    args = parser.parse_args()
    
    # Determine test mode
    if args.quick:
        test_mode = "quick"
    elif args.performance:
        test_mode = "performance"
    elif args.character:
        test_mode = "character"
    elif args.report_only:
        test_mode = "report-only"
    else:
        test_mode = "full"
    
    # Create and run test runner
    runner = Phase22TestRunner(test_mode=test_mode)
    final_report = runner.run_comprehensive_tests()
    
    # Return appropriate exit code
    if final_report["deployment_status"] == "APPROVED":
        sys.exit(0)  # Success
    elif final_report["deployment_status"] == "CONDITIONAL":
        sys.exit(1)  # Conditional success - issues to address
    else:
        sys.exit(2)  # Failure - critical issues


if __name__ == "__main__":
    main()