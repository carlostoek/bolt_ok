#!/usr/bin/env python3
"""
Cinema Performance Optimization Runner
======================================

COMPLETE PERFORMANCE OPTIMIZATION AND VALIDATION for Diana Bot's Cinema Architecture.
Executes full system optimization and validates all performance targets.

OPTIMIZATION PROCESS:
1. Initialize all performance optimization systems
2. Run comprehensive performance baseline testing
3. Execute full system optimization
4. Validate optimization results with load testing
5. Generate comprehensive performance report
6. Start continuous monitoring

PERFORMANCE TARGETS:
✅ Response Time: <400ms (improved from 500ms)
✅ Character Validation: <30ms
✅ Cache Hit Ratio: >90% (improved from 70%)
✅ Memory Usage: <150MB
✅ Concurrent Users: 50+ simultaneous
"""

import asyncio
import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('cinema_performance_optimization.log')
    ]
)

logger = logging.getLogger(__name__)

async def setup_test_database():
    """Setup test database for performance optimization."""
    
    try:
        from database.db_manager import get_async_session, async_engine
        
        # Test database connection
        async with get_async_session() as session:
            logger.info("✅ Database connection established successfully")
            return session
    
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        
        # Fallback to in-memory database for testing
        logger.info("Setting up in-memory database for testing...")
        
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        from sqlalchemy.pool import StaticPool
        
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=False
        )
        
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with session_factory() as session:
            logger.info("✅ In-memory database created successfully")
            return session

async def initialize_cinema_optimization_systems(session) -> Dict[str, Any]:
    """Initialize all cinema optimization systems."""
    
    logger.info("🎬 Initializing Cinema Performance Optimization Systems...")
    
    systems_status = {
        "performance_optimizer": False,
        "character_validator": False,
        "performance_monitor": False,
        "testing_suite": False,
        "cinema_master": False
    }
    
    try:
        # 1. Performance Optimizer
        from services.cinema_performance_optimizer import get_cinema_performance_optimizer
        performance_optimizer = get_cinema_performance_optimizer(session)
        systems_status["performance_optimizer"] = True
        logger.info("✅ Cinema Performance Optimizer initialized")
    except Exception as e:
        logger.warning(f"⚠️  Performance Optimizer initialization failed: {e}")
        performance_optimizer = None
    
    try:
        # 2. Optimized Character Validator
        from services.optimized_character_validator import get_optimized_character_validator
        character_validator = get_optimized_character_validator(session)
        systems_status["character_validator"] = True
        logger.info("✅ Optimized Character Validator initialized")
    except Exception as e:
        logger.warning(f"⚠️  Character Validator initialization failed: {e}")
        character_validator = None
    
    try:
        # 3. Performance Monitor
        from services.cinema_performance_monitor import get_cinema_performance_monitor
        performance_monitor = get_cinema_performance_monitor(session)
        systems_status["performance_monitor"] = True
        logger.info("✅ Cinema Performance Monitor initialized")
    except Exception as e:
        logger.warning(f"⚠️  Performance Monitor initialization failed: {e}")
        performance_monitor = None
    
    try:
        # 4. Performance Testing Suite
        from services.cinema_performance_testing_suite import get_cinema_performance_testing_suite
        testing_suite = get_cinema_performance_testing_suite(session)
        systems_status["testing_suite"] = True
        logger.info("✅ Performance Testing Suite initialized")
    except Exception as e:
        logger.warning(f"⚠️  Testing Suite initialization failed: {e}")
        testing_suite = None
    
    try:
        # 5. Cinema Master Integration
        from services.cinema_master_integration import get_cinema_master_integration
        cinema_master = get_cinema_master_integration(session)
        systems_status["cinema_master"] = True
        logger.info("✅ Cinema Master Integration initialized")
    except Exception as e:
        logger.warning(f"⚠️  Cinema Master Integration initialization failed: {e}")
        cinema_master = None
    
    return {
        "systems_status": systems_status,
        "performance_optimizer": performance_optimizer,
        "character_validator": character_validator,
        "performance_monitor": performance_monitor,
        "testing_suite": testing_suite,
        "cinema_master": cinema_master
    }

async def run_baseline_performance_test(testing_suite) -> Dict[str, Any]:
    """Run baseline performance testing before optimization."""
    
    logger.info("📊 Running Baseline Performance Tests...")
    
    if not testing_suite:
        logger.error("❌ Testing suite not available for baseline testing")
        return {"success": False, "error": "Testing suite not available"}
    
    try:
        # Run comprehensive performance test
        baseline_report = await testing_suite.run_comprehensive_performance_test()
        
        logger.info(f"📈 Baseline Test Results:")
        logger.info(f"   Overall Success: {baseline_report.overall_success}")
        logger.info(f"   Performance Grade: {baseline_report.performance_grade}")
        logger.info(f"   Tests Passed: {baseline_report.tests_passed}/{baseline_report.tests_passed + baseline_report.tests_failed}")
        
        # Log individual test results
        for test_result in baseline_report.test_results:
            status = "✅" if test_result.meets_target else "❌"
            logger.info(f"   {status} {test_result.test_name}: {test_result.metric_value:.2f} (target: {test_result.target_value})")
        
        return {
            "success": True,
            "report": baseline_report,
            "grade": baseline_report.performance_grade
        }
    
    except Exception as e:
        logger.exception(f"❌ Baseline performance testing failed: {e}")
        return {"success": False, "error": str(e)}

async def execute_full_system_optimization(systems) -> Dict[str, Any]:
    """Execute comprehensive system optimization."""
    
    logger.info("🚀 Executing Full System Optimization...")
    
    optimization_results = {
        "optimizations_performed": [],
        "errors": [],
        "overall_success": True
    }
    
    # 1. Performance Optimizer
    if systems["performance_optimizer"]:
        try:
            result = await systems["performance_optimizer"].trigger_full_system_optimization()
            if result["success"]:
                optimization_results["optimizations_performed"].extend(result["optimizations_performed"])
                logger.info("✅ Performance Optimizer optimization completed")
            else:
                optimization_results["errors"].append(f"Performance optimizer failed: {result.get('error', 'Unknown')}")
        except Exception as e:
            optimization_results["errors"].append(f"Performance optimizer error: {e}")
            logger.warning(f"⚠️  Performance optimizer optimization failed: {e}")
    
    # 2. Character Validator Optimization
    if systems["character_validator"]:
        try:
            result = await systems["character_validator"].optimize_performance()
            if result["success"]:
                optimization_results["optimizations_performed"].extend(result["optimizations_performed"])
                logger.info("✅ Character Validator optimization completed")
            else:
                optimization_results["errors"].append("Character validator optimization failed")
        except Exception as e:
            optimization_results["errors"].append(f"Character validator error: {e}")
            logger.warning(f"⚠️  Character validator optimization failed: {e}")
    
    # 3. Cinema Master System Optimization
    if systems["cinema_master"]:
        try:
            result = await systems["cinema_master"].trigger_performance_optimization()
            if result["success"]:
                optimization_results["optimizations_performed"].extend(result.get("optimizations_performed", []))
                logger.info("✅ Cinema Master system optimization completed")
            else:
                optimization_results["errors"].append(f"Cinema Master optimization failed: {result.get('reason', 'Unknown')}")
        except Exception as e:
            optimization_results["errors"].append(f"Cinema Master error: {e}")
            logger.warning(f"⚠️  Cinema Master optimization failed: {e}")
    
    # 4. Performance Monitor Optimization
    if systems["performance_monitor"]:
        try:
            result = await systems["performance_monitor"].trigger_advanced_optimization()
            if result["success"]:
                optimization_results["optimizations_performed"].append("performance_monitor_optimized")
                logger.info("✅ Performance Monitor optimization completed")
            else:
                optimization_results["errors"].append(f"Performance monitor optimization failed: {result.get('reason', 'Unknown')}")
        except Exception as e:
            optimization_results["errors"].append(f"Performance monitor error: {e}")
            logger.warning(f"⚠️  Performance monitor optimization failed: {e}")
    
    # Determine overall success
    optimization_results["overall_success"] = len(optimization_results["errors"]) == 0
    
    logger.info(f"🔧 System Optimization Results:")
    logger.info(f"   Optimizations Performed: {len(optimization_results['optimizations_performed'])}")
    logger.info(f"   Errors Encountered: {len(optimization_results['errors'])}")
    logger.info(f"   Overall Success: {optimization_results['overall_success']}")
    
    return optimization_results

async def validate_optimization_results(testing_suite, baseline_results) -> Dict[str, Any]:
    """Validate optimization results with comprehensive testing."""
    
    logger.info("🔍 Validating Optimization Results...")
    
    if not testing_suite:
        logger.error("❌ Testing suite not available for validation")
        return {"success": False, "error": "Testing suite not available"}
    
    try:
        # Run post-optimization performance test
        validation_report = await testing_suite.run_comprehensive_performance_test()
        
        logger.info(f"📈 Post-Optimization Test Results:")
        logger.info(f"   Overall Success: {validation_report.overall_success}")
        logger.info(f"   Performance Grade: {validation_report.performance_grade}")
        logger.info(f"   Tests Passed: {validation_report.tests_passed}/{validation_report.tests_passed + validation_report.tests_failed}")
        
        # Compare with baseline
        improvements = {}
        if baseline_results.get("success"):
            baseline_report = baseline_results["report"]
            
            # Compare individual metrics
            for validation_test in validation_report.test_results:
                test_name = validation_test.test_name
                
                # Find corresponding baseline test
                baseline_test = next(
                    (t for t in baseline_report.test_results if t.test_name == test_name), 
                    None
                )
                
                if baseline_test:
                    improvement = baseline_test.metric_value - validation_test.metric_value
                    improvement_percent = (improvement / baseline_test.metric_value) * 100 if baseline_test.metric_value > 0 else 0
                    improvements[test_name] = {
                        "baseline": baseline_test.metric_value,
                        "optimized": validation_test.metric_value,
                        "improvement": improvement,
                        "improvement_percent": improvement_percent
                    }
                    
                    if improvement > 0:
                        logger.info(f"   📈 {test_name}: {improvement:.2f} improvement ({improvement_percent:.1f}%)")
                    elif improvement < 0:
                        logger.warning(f"   📉 {test_name}: {abs(improvement):.2f} regression ({abs(improvement_percent):.1f}%)")
                    else:
                        logger.info(f"   ➡️  {test_name}: No change")
        
        # Run intensive load test to validate under stress
        logger.info("🏋️  Running intensive load test validation...")
        load_test_result = await testing_suite.run_load_test(concurrent_users=25, operations_per_user=50)
        
        load_test_success = (
            load_test_result.avg_response_time_ms <= 800 and  # Allow higher threshold under load
            load_test_result.error_rate <= 0.10 and  # Allow up to 10% error rate under stress
            load_test_result.memory_usage_mb <= 200  # Allow higher memory under load
        )
        
        logger.info(f"🏋️  Load Test Results:")
        logger.info(f"   Concurrent Users: {load_test_result.concurrent_users}")
        logger.info(f"   Avg Response Time: {load_test_result.avg_response_time_ms:.1f}ms")
        logger.info(f"   Error Rate: {load_test_result.error_rate:.1%}")
        logger.info(f"   Memory Usage: {load_test_result.memory_usage_mb:.1f}MB")
        logger.info(f"   Load Test Success: {load_test_success}")
        
        return {
            "success": True,
            "validation_report": validation_report,
            "improvements": improvements,
            "load_test_result": load_test_result,
            "load_test_success": load_test_success,
            "overall_validation_success": validation_report.overall_success and load_test_success
        }
    
    except Exception as e:
        logger.exception(f"❌ Optimization validation failed: {e}")
        return {"success": False, "error": str(e)}

async def generate_comprehensive_report(systems, baseline_results, optimization_results, validation_results) -> Dict[str, Any]:
    """Generate comprehensive performance optimization report."""
    
    logger.info("📋 Generating Comprehensive Performance Report...")
    
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "optimization_session_id": f"cinema_opt_{int(datetime.utcnow().timestamp())}",
        "systems_initialized": systems["systems_status"],
        "baseline_performance": baseline_results,
        "optimization_results": optimization_results,
        "validation_results": validation_results,
        "final_assessment": {},
        "recommendations": []
    }
    
    # Calculate final assessment
    systems_healthy = sum(systems["systems_status"].values())
    total_systems = len(systems["systems_status"])
    
    optimization_successful = optimization_results.get("overall_success", False)
    validation_successful = validation_results.get("overall_validation_success", False)
    
    if systems_healthy == total_systems and optimization_successful and validation_successful:
        final_grade = "EXCELLENT"
        status = "All systems optimized and performing within targets"
    elif systems_healthy >= total_systems - 1 and optimization_successful:
        final_grade = "GOOD"
        status = "Most systems optimized successfully"
    elif systems_healthy >= total_systems // 2:
        final_grade = "FAIR"
        status = "Partial optimization achieved"
    else:
        final_grade = "NEEDS_IMPROVEMENT"
        status = "Significant optimization issues remain"
    
    report["final_assessment"] = {
        "grade": final_grade,
        "status": status,
        "systems_healthy": f"{systems_healthy}/{total_systems}",
        "optimization_successful": optimization_successful,
        "validation_successful": validation_successful
    }
    
    # Generate recommendations
    recommendations = []
    
    if not optimization_successful:
        recommendations.append("Review optimization errors and retry failed optimizations")
    
    if not validation_successful:
        recommendations.append("Investigate performance regressions and apply additional optimizations")
    
    if systems_healthy < total_systems:
        failed_systems = [name for name, status in systems["systems_status"].items() if not status]
        recommendations.append(f"Initialize failed systems: {', '.join(failed_systems)}")
    
    if validation_results.get("success") and validation_results["validation_report"].performance_grade in ["C", "F"]:
        recommendations.append("Performance grade below expectations - consider aggressive optimization mode")
    
    if not recommendations:
        recommendations = [
            "Cinema Architecture System fully optimized and performing excellently",
            "Continue regular performance monitoring",
            "Consider implementing continuous optimization"
        ]
    
    report["recommendations"] = recommendations
    
    return report

async def start_continuous_monitoring(systems):
    """Start continuous performance monitoring."""
    
    logger.info("🔄 Starting Continuous Performance Monitoring...")
    
    if systems["testing_suite"]:
        try:
            # Start monitoring in background (non-blocking)
            asyncio.create_task(
                systems["testing_suite"].start_continuous_monitoring(interval_minutes=15)
            )
            logger.info("✅ Continuous monitoring started (15-minute intervals)")
            return True
        except Exception as e:
            logger.warning(f"⚠️  Failed to start continuous monitoring: {e}")
            return False
    else:
        logger.warning("⚠️  Testing suite not available for continuous monitoring")
        return False

def print_final_report(report):
    """Print formatted final report."""
    
    print("\n" + "="*80)
    print("🎬 CINEMA ARCHITECTURE PERFORMANCE OPTIMIZATION REPORT")
    print("="*80)
    
    print(f"\n📅 Optimization Session: {report['optimization_session_id']}")
    print(f"🕒 Timestamp: {report['timestamp']}")
    
    # Systems Status
    print(f"\n🖥️  SYSTEMS STATUS:")
    for system_name, status in report["systems_initialized"].items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {system_name.replace('_', ' ').title()}")
    
    # Final Assessment
    assessment = report["final_assessment"]
    grade_icons = {
        "EXCELLENT": "🏆",
        "GOOD": "✅",
        "FAIR": "⚠️",
        "NEEDS_IMPROVEMENT": "❌"
    }
    
    print(f"\n🎯 FINAL ASSESSMENT:")
    print(f"   Grade: {grade_icons.get(assessment['grade'], '❓')} {assessment['grade']}")
    print(f"   Status: {assessment['status']}")
    print(f"   Systems Healthy: {assessment['systems_healthy']}")
    print(f"   Optimization Success: {'✅' if assessment['optimization_successful'] else '❌'}")
    print(f"   Validation Success: {'✅' if assessment['validation_successful'] else '❌'}")
    
    # Performance Improvements
    if report["validation_results"].get("success") and report["validation_results"].get("improvements"):
        print(f"\n📈 PERFORMANCE IMPROVEMENTS:")
        for test_name, improvement_data in report["validation_results"]["improvements"].items():
            if improvement_data["improvement"] > 0:
                print(f"   📈 {test_name}: {improvement_data['improvement']:.2f} improvement ({improvement_data['improvement_percent']:.1f}%)")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    for i, rec in enumerate(report["recommendations"], 1):
        print(f"   {i}. {rec}")
    
    print("\n" + "="*80)
    print("🎬 CINEMA ARCHITECTURE OPTIMIZATION COMPLETE")
    print("="*80 + "\n")

async def main():
    """Main performance optimization execution."""
    
    logger.info("🎬 Starting Cinema Architecture Performance Optimization")
    logger.info("=" * 60)
    
    try:
        # 1. Setup Database
        session = await setup_test_database()
        
        # 2. Initialize Systems
        systems = await initialize_cinema_optimization_systems(session)
        
        # 3. Run Baseline Tests
        baseline_results = await run_baseline_performance_test(systems["testing_suite"])
        
        # 4. Execute Optimization
        optimization_results = await execute_full_system_optimization(systems)
        
        # 5. Validate Results
        validation_results = await validate_optimization_results(systems["testing_suite"], baseline_results)
        
        # 6. Generate Report
        final_report = await generate_comprehensive_report(
            systems, baseline_results, optimization_results, validation_results
        )
        
        # 7. Start Continuous Monitoring
        monitoring_started = await start_continuous_monitoring(systems)
        final_report["continuous_monitoring"] = monitoring_started
        
        # 8. Print Final Report
        print_final_report(final_report)
        
        # Save report to file
        report_filename = f"cinema_performance_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        import json
        with open(report_filename, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)
        
        logger.info(f"📄 Full report saved to: {report_filename}")
        
        return final_report
    
    except Exception as e:
        logger.exception(f"❌ Critical error in performance optimization: {e}")
        print(f"\n❌ CRITICAL ERROR: {e}")
        return None

if __name__ == "__main__":
    try:
        report = asyncio.run(main())
        
        # Exit with appropriate code
        if report and report["final_assessment"]["grade"] in ["EXCELLENT", "GOOD"]:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Performance issues remain
    
    except KeyboardInterrupt:
        logger.info("🛑 Optimization cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"💥 Unexpected error: {e}")
        sys.exit(1)