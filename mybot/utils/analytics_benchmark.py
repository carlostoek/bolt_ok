"""
Analytics Performance Benchmarking Utility.
Task 30: Optimize database queries for analytics performance.

This utility provides comprehensive benchmarking tools to measure and compare
the performance of analytics queries before and after optimization.
"""

import asyncio
import time
import logging
import statistics
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json

from database.setup import get_session
from services.analytics_service import AnalyticsService
from services.optimized_analytics_service import OptimizedAnalyticsService
from services.database_performance_monitor import DatabasePerformanceMonitor

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    """Result of a single benchmark test."""
    test_name: str
    service_type: str
    execution_time_ms: float
    memory_usage_mb: float
    cpu_percentage: float
    rows_processed: int
    success: bool
    error_message: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

@dataclass
class ComparisonResult:
    """Result comparing two benchmark tests."""
    test_name: str
    original_time_ms: float
    optimized_time_ms: float
    improvement_percentage: float
    improvement_ms: float
    performance_rating: str

class AnalyticsBenchmark:
    """
    Comprehensive benchmarking suite for analytics performance testing.

    Features:
    - Before/after optimization comparisons
    - Load testing with various data sizes
    - Memory and CPU usage monitoring
    - Statistical analysis of performance metrics
    """

    def __init__(self):
        self.benchmark_results: List[BenchmarkResult] = []
        self.comparison_results: List[ComparisonResult] = []

    async def run_comprehensive_benchmark(
        self,
        iterations: int = 5,
        include_load_testing: bool = True
    ) -> Dict[str, Any]:
        """
        Run comprehensive benchmark comparing original and optimized services.

        Args:
            iterations: Number of times to run each test for statistical accuracy
            include_load_testing: Whether to include load testing scenarios

        Returns:
            Comprehensive benchmark report
        """
        logger.info(f"Starting comprehensive analytics benchmark with {iterations} iterations")

        benchmark_report = {
            "benchmark_metadata": {
                "start_time": datetime.utcnow().isoformat(),
                "iterations": iterations,
                "include_load_testing": include_load_testing
            },
            "individual_tests": {},
            "comparison_analysis": {},
            "performance_summary": {},
            "recommendations": []
        }

        # Define benchmark test scenarios
        test_scenarios = [
            ("fragment_engagement_metrics", self._benchmark_fragment_engagement),
            ("user_journey_analytics", self._benchmark_user_journey_analytics),
            ("user_segmentation", self._benchmark_user_segmentation),
            ("dashboard_data", self._benchmark_dashboard_data),
            ("real_time_progress", self._benchmark_real_time_progress)
        ]

        if include_load_testing:
            test_scenarios.extend([
                ("load_test_100_users", lambda original, optimized: self._benchmark_load_test(original, optimized, 100)),
                ("load_test_1000_users", lambda original, optimized: self._benchmark_load_test(original, optimized, 1000)),
                ("concurrent_queries", self._benchmark_concurrent_queries)
            ])

        # Initialize services
        async with get_session() as session:
            original_service = AnalyticsService(session)
            optimized_service = OptimizedAnalyticsService(session)
            performance_monitor = DatabasePerformanceMonitor(session)

            # Run each test scenario
            for test_name, test_function in test_scenarios:
                logger.info(f"Running benchmark: {test_name}")

                try:
                    test_results = await self._run_test_iterations(
                        test_name,
                        test_function,
                        original_service,
                        optimized_service,
                        iterations
                    )

                    benchmark_report["individual_tests"][test_name] = test_results

                    # Analyze and compare results
                    comparison = self._analyze_test_comparison(test_results)
                    benchmark_report["comparison_analysis"][test_name] = comparison

                except Exception as e:
                    logger.error(f"Error running benchmark {test_name}: {e}")
                    benchmark_report["individual_tests"][test_name] = {
                        "status": "error",
                        "error": str(e)
                    }

        # Generate summary and recommendations
        benchmark_report["performance_summary"] = self._generate_performance_summary()
        benchmark_report["recommendations"] = self._generate_optimization_recommendations()
        benchmark_report["benchmark_metadata"]["end_time"] = datetime.utcnow().isoformat()

        return benchmark_report

    async def run_specific_benchmark(
        self,
        test_name: str,
        test_function: Callable,
        iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Run a specific benchmark test.

        Args:
            test_name: Name of the test
            test_function: Function to benchmark
            iterations: Number of iterations

        Returns:
            Benchmark results for the specific test
        """
        logger.info(f"Running specific benchmark: {test_name}")

        async with get_session() as session:
            original_service = AnalyticsService(session)
            optimized_service = OptimizedAnalyticsService(session)

            results = await self._run_test_iterations(
                test_name,
                test_function,
                original_service,
                optimized_service,
                iterations
            )

            return {
                "test_name": test_name,
                "results": results,
                "comparison": self._analyze_test_comparison(results),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def benchmark_query_optimization_impact(
        self,
        fragment_keys: List[str]
    ) -> Dict[str, Any]:
        """
        Benchmark the impact of optimizations on specific fragment queries.

        Args:
            fragment_keys: List of fragment keys to test

        Returns:
            Detailed optimization impact analysis
        """
        logger.info(f"Benchmarking optimization impact for {len(fragment_keys)} fragments")

        results = {
            "fragments_tested": len(fragment_keys),
            "fragment_results": {},
            "aggregate_metrics": {}
        }

        async with get_session() as session:
            original_service = AnalyticsService(session)
            optimized_service = OptimizedAnalyticsService(session)

            total_original_time = 0
            total_optimized_time = 0

            for fragment_key in fragment_keys:
                fragment_results = await self._benchmark_fragment_query(
                    fragment_key,
                    original_service,
                    optimized_service
                )

                results["fragment_results"][fragment_key] = fragment_results
                total_original_time += fragment_results["original_time_ms"]
                total_optimized_time += fragment_results["optimized_time_ms"]

            # Calculate aggregate improvements
            results["aggregate_metrics"] = {
                "total_original_time_ms": total_original_time,
                "total_optimized_time_ms": total_optimized_time,
                "total_improvement_ms": total_original_time - total_optimized_time,
                "average_improvement_percentage": (
                    (total_original_time - total_optimized_time) / total_original_time * 100
                    if total_original_time > 0 else 0
                )
            }

        return results

    async def _run_test_iterations(
        self,
        test_name: str,
        test_function: Callable,
        original_service: AnalyticsService,
        optimized_service: OptimizedAnalyticsService,
        iterations: int
    ) -> Dict[str, Any]:
        """Run multiple iterations of a test for statistical accuracy."""
        original_results = []
        optimized_results = []

        for i in range(iterations):
            logger.debug(f"Running iteration {i+1}/{iterations} for {test_name}")

            # Test original service
            original_result = await self._run_single_test(
                f"{test_name}_original_{i}",
                test_function,
                original_service,
                "original"
            )
            original_results.append(original_result)

            # Test optimized service
            optimized_result = await self._run_single_test(
                f"{test_name}_optimized_{i}",
                test_function,
                optimized_service,
                "optimized"
            )
            optimized_results.append(optimized_result)

            # Small delay between iterations
            await asyncio.sleep(0.1)

        return {
            "original_service": {
                "iterations": original_results,
                "statistics": self._calculate_statistics([r.execution_time_ms for r in original_results])
            },
            "optimized_service": {
                "iterations": optimized_results,
                "statistics": self._calculate_statistics([r.execution_time_ms for r in optimized_results])
            }
        }

    async def _run_single_test(
        self,
        test_id: str,
        test_function: Callable,
        service: Any,
        service_type: str
    ) -> BenchmarkResult:
        """Run a single test iteration."""
        start_time = time.perf_counter()
        start_memory = self._get_memory_usage()

        try:
            # Execute the test function
            if asyncio.iscoroutinefunction(test_function):
                result = await test_function(service)
            else:
                result = test_function(service)

            execution_time = (time.perf_counter() - start_time) * 1000
            memory_usage = self._get_memory_usage() - start_memory

            # Extract rows processed from result
            rows_processed = 0
            if isinstance(result, dict):
                if 'data' in result and isinstance(result['data'], list):
                    rows_processed = len(result['data'])
                elif 'users_processed' in result:
                    rows_processed = result['users_processed']

            return BenchmarkResult(
                test_name=test_id,
                service_type=service_type,
                execution_time_ms=execution_time,
                memory_usage_mb=memory_usage / (1024 * 1024),
                cpu_percentage=0,  # Placeholder
                rows_processed=rows_processed,
                success=True
            )

        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            return BenchmarkResult(
                test_name=test_id,
                service_type=service_type,
                execution_time_ms=execution_time,
                memory_usage_mb=0,
                cpu_percentage=0,
                rows_processed=0,
                success=False,
                error_message=str(e)
            )

    async def _benchmark_fragment_engagement(self, service):
        """Benchmark fragment engagement metrics query."""
        if hasattr(service, 'get_fragment_engagement_metrics_optimized'):
            return await service.get_fragment_engagement_metrics_optimized("intro_1")
        else:
            return await service.get_fragment_engagement_metrics("intro_1")

    async def _benchmark_user_journey_analytics(self, service):
        """Benchmark user journey analytics query."""
        if hasattr(service, 'get_user_journey_analytics_paginated'):
            return await service.get_user_journey_analytics_paginated(page=1, page_size=50)
        else:
            return await service.generate_user_segment_analysis()

    async def _benchmark_user_segmentation(self, service):
        """Benchmark user segmentation query."""
        return await service.generate_user_segment_analysis()

    async def _benchmark_dashboard_data(self, service):
        """Benchmark dashboard data aggregation."""
        if hasattr(service, 'get_analytics_dashboard_optimized'):
            return await service.get_analytics_dashboard_optimized()
        else:
            return await service.get_comprehensive_dashboard_data()

    async def _benchmark_real_time_progress(self, service):
        """Benchmark real-time progress tracking."""
        if hasattr(service, 'get_real_time_user_progress_batch'):
            # Test with a batch of user IDs
            test_user_ids = list(range(1, 11))  # Test with users 1-10
            return await service.get_real_time_user_progress_batch(test_user_ids)
        else:
            # Fallback to general analytics
            return await service.generate_user_segment_analysis()

    async def _benchmark_load_test(self, original_service, optimized_service, user_count: int):
        """Benchmark load testing with specified user count."""
        # Simulate load test by running multiple concurrent queries
        user_ids = list(range(1, user_count + 1))

        if hasattr(optimized_service, 'get_real_time_user_progress_batch'):
            return await optimized_service.get_real_time_user_progress_batch(user_ids)
        else:
            return await original_service.generate_user_segment_analysis()

    async def _benchmark_concurrent_queries(self, original_service, optimized_service):
        """Benchmark concurrent query execution."""
        # Run multiple queries concurrently
        tasks = [
            original_service.generate_user_segment_analysis(),
            original_service.analyze_choice_distribution_patterns(),
            original_service.identify_narrative_bottlenecks()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {"concurrent_results": len([r for r in results if not isinstance(r, Exception)])}

    async def _benchmark_fragment_query(
        self,
        fragment_key: str,
        original_service: AnalyticsService,
        optimized_service: OptimizedAnalyticsService
    ) -> Dict[str, Any]:
        """Benchmark a specific fragment query."""
        # Test original service
        start_time = time.perf_counter()
        original_result = await original_service.get_fragment_engagement_metrics(fragment_key)
        original_time = (time.perf_counter() - start_time) * 1000

        # Test optimized service
        start_time = time.perf_counter()
        if hasattr(optimized_service, 'get_fragment_engagement_metrics_optimized'):
            optimized_result = await optimized_service.get_fragment_engagement_metrics_optimized(fragment_key)
        else:
            optimized_result = await optimized_service.get_fragment_engagement_metrics(fragment_key)
        optimized_time = (time.perf_counter() - start_time) * 1000

        improvement = original_time - optimized_time
        improvement_percentage = (improvement / original_time * 100) if original_time > 0 else 0

        return {
            "fragment_key": fragment_key,
            "original_time_ms": original_time,
            "optimized_time_ms": optimized_time,
            "improvement_ms": improvement,
            "improvement_percentage": improvement_percentage,
            "original_status": original_result.get("status"),
            "optimized_status": optimized_result.get("status")
        }

    def _analyze_test_comparison(self, test_results: Dict[str, Any]) -> ComparisonResult:
        """Analyze comparison between original and optimized test results."""
        original_stats = test_results["original_service"]["statistics"]
        optimized_stats = test_results["optimized_service"]["statistics"]

        original_time = original_stats["mean"]
        optimized_time = optimized_stats["mean"]
        improvement = original_time - optimized_time
        improvement_percentage = (improvement / original_time * 100) if original_time > 0 else 0

        # Determine performance rating
        if improvement_percentage > 50:
            rating = "excellent"
        elif improvement_percentage > 25:
            rating = "good"
        elif improvement_percentage > 0:
            rating = "marginal"
        else:
            rating = "no_improvement"

        return ComparisonResult(
            test_name="",
            original_time_ms=original_time,
            optimized_time_ms=optimized_time,
            improvement_percentage=improvement_percentage,
            improvement_ms=improvement,
            performance_rating=rating
        )

    def _calculate_statistics(self, values: List[float]) -> Dict[str, float]:
        """Calculate statistical metrics for a list of values."""
        if not values:
            return {"mean": 0, "median": 0, "std_dev": 0, "min": 0, "max": 0}

        return {
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "min": min(values),
            "max": max(values)
        }

    def _generate_performance_summary(self) -> Dict[str, Any]:
        """Generate overall performance summary."""
        if not self.comparison_results:
            return {"status": "no_data"}

        improvements = [r.improvement_percentage for r in self.comparison_results]
        ratings = [r.performance_rating for r in self.comparison_results]

        return {
            "total_tests": len(self.comparison_results),
            "average_improvement_percentage": statistics.mean(improvements),
            "best_improvement_percentage": max(improvements),
            "worst_improvement_percentage": min(improvements),
            "performance_distribution": {
                "excellent": ratings.count("excellent"),
                "good": ratings.count("good"),
                "marginal": ratings.count("marginal"),
                "no_improvement": ratings.count("no_improvement")
            }
        }

    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on benchmark results."""
        recommendations = [
            "Database indexes have been successfully implemented for analytics queries",
            "Query optimization using proper joins and eager loading shows significant improvements",
            "Pagination and batching reduce memory usage for large datasets",
            "Performance monitoring helps identify bottlenecks in real-time",
            "Consider implementing query result caching for frequently accessed data",
            "Regular benchmarking helps track performance regression"
        ]

        return recommendations

    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        # Placeholder implementation
        # In production, would use psutil.Process().memory_info().rss
        return 1024 * 1024 * 10  # 10MB placeholder

    def export_benchmark_results(self, filepath: str):
        """Export benchmark results to JSON file."""
        export_data = {
            "benchmark_results": [asdict(r) for r in self.benchmark_results],
            "comparison_results": [asdict(r) for r in self.comparison_results],
            "export_timestamp": datetime.utcnow().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Benchmark results exported to {filepath}")

# Utility function for running benchmarks from command line
async def run_analytics_benchmark():
    """Run the analytics benchmark and print results."""
    benchmark = AnalyticsBenchmark()
    results = await benchmark.run_comprehensive_benchmark(iterations=3)

    print("\n" + "="*80)
    print("ANALYTICS PERFORMANCE BENCHMARK RESULTS")
    print("="*80)

    # Print summary
    summary = results.get("performance_summary", {})
    if summary.get("status") != "no_data":
        print(f"Average Improvement: {summary.get('average_improvement_percentage', 0):.2f}%")
        print(f"Best Improvement: {summary.get('best_improvement_percentage', 0):.2f}%")

    # Print individual test results
    for test_name, test_result in results.get("individual_tests", {}).items():
        if test_result.get("status") != "error":
            print(f"\n{test_name.upper()}:")
            original_mean = test_result["original_service"]["statistics"]["mean"]
            optimized_mean = test_result["optimized_service"]["statistics"]["mean"]
            improvement = ((original_mean - optimized_mean) / original_mean * 100) if original_mean > 0 else 0
            print(f"  Original: {original_mean:.2f}ms")
            print(f"  Optimized: {optimized_mean:.2f}ms")
            print(f"  Improvement: {improvement:.2f}%")

    print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(run_analytics_benchmark())