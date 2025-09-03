#!/usr/bin/env python3
"""
Diana Menu Performance Validation Script
Tests the optimized Enhanced Diana Menu System performance improvements.

Target: Reduce response time from 3.10s to <2.0s (ideally <1.5s)
"""

import asyncio
import time
import logging
import statistics
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class PerformanceResult:
    """Performance test result."""
    operation: str
    response_time: float
    meets_target: bool
    character_score: float
    success: bool
    errors: List[str]

class DianaMenuPerformanceTester:
    """Performance tester for Diana Menu System optimizations."""
    
    TARGET_RESPONSE_TIME = 2.0  # seconds
    IDEAL_RESPONSE_TIME = 1.5   # seconds
    MIN_CHARACTER_SCORE = 95.0
    
    def __init__(self):
        self.results: List[PerformanceResult] = []
        self.session_mock = self._create_session_mock()
    
    def _create_session_mock(self):
        """Create optimized session mock for testing."""
        session = AsyncMock()
        
        # Mock database queries to return fast
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.begin = AsyncMock().__aenter__
        
        # Mock query results
        mock_user = MagicMock()
        mock_user.id = 123456789
        mock_user.first_name = "TestUser"
        mock_user.role = "free"
        mock_user.points = 100.0
        mock_user.level = 1
        mock_user.created_at = time.time()
        
        mock_session = MagicMock()
        mock_session.session_state = "main_menu"
        mock_session.character_consistency_score = 96.5
        mock_session.last_interaction = time.time()
        
        mock_user.session = mock_session
        
        # Configure query results
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        session.execute.return_value = mock_result
        
        return session
    
    async def test_main_menu_performance(self) -> PerformanceResult:
        """Test main menu display performance."""
        try:
            from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem
            from aiogram.types import CallbackQuery
            
            # Create menu system
            menu_system = EnhancedDianaMenuSystem(self.session_mock)
            
            # Create mock callback
            callback = MagicMock(spec=CallbackQuery)
            callback.from_user.id = 123456789
            callback.answer = AsyncMock()
            callback.message.edit_text = AsyncMock()
            
            # Measure performance
            start_time = time.time()
            
            result = await menu_system.show_main_menu(callback)
            
            response_time = time.time() - start_time
            
            return PerformanceResult(
                operation="main_menu_display",
                response_time=response_time,
                meets_target=response_time < self.TARGET_RESPONSE_TIME,
                character_score=result.character_score,
                success=result.success,
                errors=result.errors
            )
            
        except Exception as e:
            logger.error(f"Error testing main menu performance: {e}")
            return PerformanceResult(
                operation="main_menu_display",
                response_time=999.0,
                meets_target=False,
                character_score=0.0,
                success=False,
                errors=[str(e)]
            )
    
    async def test_character_validation_performance(self) -> PerformanceResult:
        """Test character validation performance with caching."""
        try:
            from services.diana_character_validator import DianaCharacterValidator
            
            validator = DianaCharacterValidator(self.session_mock)
            
            # Test text for validation
            test_text = "💋 **Los Dominios de Diana**\\n\\nSusurra mi nombre, querido... ¿Qué secretos deseas explorar conmigo hoy?"
            
            # First validation (cold cache)
            start_time = time.time()
            result1 = await validator.validate_text(test_text, context="menu_response")
            cold_time = time.time() - start_time
            
            # Second validation (warm cache)
            start_time = time.time()
            result2 = await validator.validate_text(test_text, context="menu_response")
            warm_time = time.time() - start_time
            
            # Should use cached result
            cache_performance_improvement = (cold_time - warm_time) / cold_time * 100
            
            logger.info(f"Character validation - Cold: {cold_time:.3f}s, Warm: {warm_time:.3f}s, Cache improvement: {cache_performance_improvement:.1f}%")
            
            return PerformanceResult(
                operation="character_validation",
                response_time=cold_time,  # Report cold cache time
                meets_target=cold_time < 0.1,  # Character validation should be <100ms
                character_score=result1.overall_score,
                success=result1.meets_threshold,
                errors=result1.violations
            )
            
        except Exception as e:
            logger.error(f"Error testing character validation performance: {e}")
            return PerformanceResult(
                operation="character_validation",
                response_time=999.0,
                meets_target=False,
                character_score=0.0,
                success=False,
                errors=[str(e)]
            )
    
    async def test_user_service_performance(self) -> PerformanceResult:
        """Test user service performance with caching."""
        try:
            from services.enhanced_user_service import EnhancedUserService
            
            user_service = EnhancedUserService(self.session_mock)
            user_id = 123456789
            
            # Test user data retrieval
            start_time = time.time()
            user_data = await user_service.get_user_with_character_score(user_id)
            response_time = time.time() - start_time
            
            return PerformanceResult(
                operation="user_data_retrieval",
                response_time=response_time,
                meets_target=response_time < 0.05,  # Should be <50ms
                character_score=user_data["character_score"] if user_data else 0.0,
                success=user_data is not None,
                errors=[] if user_data else ["User data not found"]
            )
            
        except Exception as e:
            logger.error(f"Error testing user service performance: {e}")
            return PerformanceResult(
                operation="user_data_retrieval",
                response_time=999.0,
                meets_target=False,
                character_score=0.0,
                success=False,
                errors=[str(e)]
            )
    
    async def test_callback_handling_performance(self) -> PerformanceResult:
        """Test callback handling performance."""
        try:
            from services.enhanced_diana_menu_system import EnhancedDianaMenuSystem
            from aiogram.types import CallbackQuery
            
            menu_system = EnhancedDianaMenuSystem(self.session_mock)
            
            # Create mock callback for VIP preview
            callback = MagicMock(spec=CallbackQuery)
            callback.from_user.id = 123456789
            callback.data = "diana_vip_preview"
            callback.answer = AsyncMock()
            callback.message.edit_text = AsyncMock()
            
            # Measure performance
            start_time = time.time()
            result = await menu_system.handle_callback(callback)
            response_time = time.time() - start_time
            
            return PerformanceResult(
                operation="callback_handling",
                response_time=response_time,
                meets_target=response_time < self.TARGET_RESPONSE_TIME,
                character_score=result.character_score,
                success=result.success,
                errors=result.errors
            )
            
        except Exception as e:
            logger.error(f"Error testing callback handling performance: {e}")
            return PerformanceResult(
                operation="callback_handling",
                response_time=999.0,
                meets_target=False,
                character_score=0.0,
                success=False,
                errors=[str(e)]
            )
    
    async def run_comprehensive_performance_test(self) -> Dict[str, Any]:
        """Run comprehensive performance test suite."""
        logger.info("🚀 Starting Diana Menu Performance Validation")
        logger.info(f"Target: <{self.TARGET_RESPONSE_TIME}s response time")
        logger.info(f"Ideal: <{self.IDEAL_RESPONSE_TIME}s response time")
        
        # Run all performance tests
        tests = [
            self.test_main_menu_performance(),
            self.test_character_validation_performance(), 
            self.test_user_service_performance(),
            self.test_callback_handling_performance()
        ]
        
        results = await asyncio.gather(*tests, return_exceptions=True)
        
        # Process results
        successful_results = []
        failed_tests = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_tests.append(f"Test {i+1} failed: {result}")
                continue
            
            successful_results.append(result)
            self.results.append(result)
        
        # Generate performance report
        return self._generate_performance_report(successful_results, failed_tests)
    
    def _generate_performance_report(self, results: List[PerformanceResult], failed_tests: List[str]) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        if not results:
            return {
                "status": "FAILED",
                "message": "No successful test results",
                "failed_tests": failed_tests
            }
        
        # Calculate statistics
        response_times = [r.response_time for r in results]
        character_scores = [r.character_score for r in results]
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        avg_character_score = statistics.mean(character_scores)
        
        # Check if targets are met
        meets_target = avg_response_time < self.TARGET_RESPONSE_TIME
        meets_ideal = avg_response_time < self.IDEAL_RESPONSE_TIME
        character_consistent = avg_character_score >= self.MIN_CHARACTER_SCORE
        
        # Calculate improvement metrics
        original_time = 3.10  # Original reported time
        improvement_percentage = ((original_time - avg_response_time) / original_time) * 100
        
        # Detailed results by operation
        operation_details = {}
        for result in results:
            operation_details[result.operation] = {
                "response_time": result.response_time,
                "meets_target": result.meets_target,
                "character_score": result.character_score,
                "success": result.success,
                "errors": result.errors
            }
        
        report = {
            "status": "SUCCESS" if meets_target and character_consistent else "NEEDS_IMPROVEMENT",
            "performance_metrics": {
                "average_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "min_response_time": min_response_time,
                "improvement_vs_original": improvement_percentage,
                "meets_2s_target": meets_target,
                "meets_1_5s_ideal": meets_ideal,
                "original_time": original_time
            },
            "character_consistency": {
                "average_score": avg_character_score,
                "meets_95_threshold": character_consistent,
                "min_required": self.MIN_CHARACTER_SCORE
            },
            "operation_details": operation_details,
            "failed_tests": failed_tests,
            "recommendations": self._generate_recommendations(meets_target, meets_ideal, character_consistent)
        }
        
        return report
    
    def _generate_recommendations(self, meets_target: bool, meets_ideal: bool, character_consistent: bool) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        if not meets_target:
            recommendations.append("🚨 CRITICAL: Response time still exceeds 2s target")
            recommendations.append("Consider additional database query optimization")
            recommendations.append("Implement more aggressive caching strategies")
        elif not meets_ideal:
            recommendations.append("⚠️ Consider further optimization to reach <1.5s ideal time")
            recommendations.append("Look into async operation improvements")
        else:
            recommendations.append("✅ Excellent performance - targets exceeded!")
        
        if not character_consistent:
            recommendations.append("🎭 Character consistency below 95% - review validation logic")
        else:
            recommendations.append("✅ Character consistency maintained")
        
        return recommendations
    
    def print_performance_report(self, report: Dict[str, Any]):
        """Print formatted performance report."""
        print("\n" + "="*60)
        print("🎭 DIANA MENU PERFORMANCE VALIDATION REPORT")
        print("="*60)
        
        status = report["status"]
        status_icon = "✅" if status == "SUCCESS" else "⚠️" if status == "NEEDS_IMPROVEMENT" else "❌"
        print(f"\n{status_icon} OVERALL STATUS: {status}\n")
        
        # Performance metrics
        metrics = report["performance_metrics"]
        print("📊 PERFORMANCE METRICS:")
        print(f"   • Average Response Time: {metrics['average_response_time']:.3f}s")
        print(f"   • Improvement vs Original: {metrics['improvement_vs_original']:.1f}%")
        print(f"   • Meets 2.0s Target: {'✅' if metrics['meets_2s_target'] else '❌'}")
        print(f"   • Meets 1.5s Ideal: {'✅' if metrics['meets_1_5s_ideal'] else '⚠️'}")
        
        # Character consistency
        character = report["character_consistency"]
        print(f"\n🎭 CHARACTER CONSISTENCY:")
        print(f"   • Average Score: {character['average_score']:.1f}/100")
        print(f"   • Meets 95% Threshold: {'✅' if character['meets_95_threshold'] else '❌'}")
        
        # Operation details
        print(f"\n🔍 OPERATION BREAKDOWN:")
        for op, details in report["operation_details"].items():
            status_icon = "✅" if details["meets_target"] else "⚠️"
            print(f"   {status_icon} {op}: {details['response_time']:.3f}s (Score: {details['character_score']:.1f})")
        
        # Recommendations
        if report["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in report["recommendations"]:
                print(f"   {rec}")
        
        # Failed tests
        if report["failed_tests"]:
            print(f"\n❌ FAILED TESTS:")
            for test in report["failed_tests"]:
                print(f"   {test}")
        
        print("\n" + "="*60)

async def main():
    """Run performance validation."""
    tester = DianaMenuPerformanceTester()
    
    try:
        report = await tester.run_comprehensive_performance_test()
        tester.print_performance_report(report)
        
        # Return success code based on results
        if report["status"] == "SUCCESS":
            print("🎉 Performance optimization SUCCESSFUL!")
            return 0
        elif report["status"] == "NEEDS_IMPROVEMENT":
            print("⚠️ Performance optimization needs additional work")
            return 1
        else:
            print("❌ Performance optimization FAILED")
            return 2
            
    except Exception as e:
        logger.error(f"Performance validation failed: {e}")
        print(f"❌ Performance validation error: {e}")
        return 3

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)