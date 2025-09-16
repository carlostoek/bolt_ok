"""
Example usage of optimized analytics services for performance.
Task 30: Optimize database queries for analytics performance.

This example demonstrates how to use the optimized analytics components
to achieve high-performance analytics operations.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta

from database.setup import get_session
from services.optimized_analytics_service import OptimizedAnalyticsService
from services.database_performance_monitor import DatabasePerformanceMonitor
from utils.analytics_benchmark import AnalyticsBenchmark

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def demonstrate_optimized_analytics():
    """Demonstrate optimized analytics functionality."""
    print("🚀 Starting Optimized Analytics Demonstration")
    print("=" * 60)

    async with get_session() as session:
        # Initialize services
        analytics = OptimizedAnalyticsService(session)
        monitor = DatabasePerformanceMonitor(session, slow_query_threshold_ms=500)

        # Example 1: Optimized Fragment Metrics
        print("\n📊 Example 1: Optimized Fragment Engagement Metrics")
        print("-" * 50)

        async with monitor.monitor_query("fragment_metrics_demo") as metrics:
            fragment_metrics = await analytics.get_fragment_engagement_metrics_optimized(
                fragment_key="intro_1",
                use_cache=True
            )

        print(f"✅ Fragment metrics retrieved in {metrics.execution_time_ms:.2f}ms")
        print(f"   Status: {fragment_metrics.get('status', 'unknown')}")
        if fragment_metrics.get('status') == 'success':
            print(f"   Engagement Rate: {fragment_metrics['metrics'].get('engagement_rate', 0)}%")
            print(f"   View Count: {fragment_metrics['metrics'].get('view_count', 0)}")

        # Example 2: Paginated User Journey Analytics
        print("\n👥 Example 2: Paginated User Journey Analytics")
        print("-" * 50)

        async with monitor.monitor_query("journey_analytics_demo") as metrics:
            journey_data = await analytics.get_user_journey_analytics_paginated(
                page=1,
                page_size=20,
                engagement_level="highly_engaged"
            )

        print(f"✅ Journey analytics retrieved in {metrics.execution_time_ms:.2f}ms")
        if journey_data.get('status') == 'success':
            pagination = journey_data.get('pagination', {})
            print(f"   Users processed: {len(journey_data.get('data', []))}")
            print(f"   Total count: {pagination.get('total_count', 0)}")
            print(f"   Has next page: {pagination.get('has_next', False)}")

        # Example 3: Batch User Progress Tracking
        print("\n⚡ Example 3: Batch User Progress Tracking")
        print("-" * 50)

        test_user_ids = list(range(1, 21))  # Test with users 1-20
        async with monitor.monitor_query("batch_progress_demo") as metrics:
            progress_data = await analytics.get_real_time_user_progress_batch(test_user_ids)

        print(f"✅ Batch progress retrieved in {metrics.execution_time_ms:.2f}ms")
        if progress_data.get('status') == 'success':
            print(f"   Users processed: {progress_data.get('users_processed', 0)}")
            print(f"   Users with narrative data: {progress_data.get('users_with_narrative_data', 0)}")

        # Example 4: Optimized Dashboard Data
        print("\n📈 Example 4: Optimized Dashboard Data")
        print("-" * 50)

        async with monitor.monitor_query("dashboard_demo") as metrics:
            dashboard_data = await analytics.get_analytics_dashboard_optimized(cache_duration=300)

        print(f"✅ Dashboard data retrieved in {metrics.execution_time_ms:.2f}ms")
        if dashboard_data.get('status') == 'success':
            summary = dashboard_data.get('summary', {})
            availability = summary.get('data_availability', {})
            print(f"   Data components available: {sum(availability.values())}/{len(availability)}")

        # Example 5: Performance Monitoring Report
        print("\n🔍 Example 5: Performance Monitoring Report")
        print("-" * 50)

        performance_summary = await monitor.get_performance_summary()
        if performance_summary.get('status') != 'no_data':
            stats = performance_summary.get('performance_stats', {})
            print(f"   Queries monitored: {performance_summary.get('total_queries_monitored', 0)}")
            print(f"   Average execution time: {stats.get('average_execution_time_ms', 0):.2f}ms")
            print(f"   Slow queries: {stats.get('slow_queries_count', 0)}")

        # Cache Statistics
        cache_stats = await analytics.get_cache_stats()
        print(f"\n💾 Cache Statistics:")
        print(f"   Cache entries: {cache_stats.get('cache_entries', 0)}")

async def demonstrate_performance_comparison():
    """Demonstrate performance comparison between services."""
    print("\n🏃‍♂️ Performance Comparison Demonstration")
    print("=" * 60)

    benchmark = AnalyticsBenchmark()

    # Run a quick benchmark comparison
    print("Running performance benchmark (this may take a few moments)...")

    benchmark_results = await benchmark.run_specific_benchmark(
        test_name="fragment_engagement",
        test_function=benchmark._benchmark_fragment_engagement,
        iterations=3
    )

    print(f"\n📊 Benchmark Results:")
    comparison = benchmark_results.get('comparison', {})
    print(f"   Original service: {comparison.original_time_ms:.2f}ms")
    print(f"   Optimized service: {comparison.optimized_time_ms:.2f}ms")
    print(f"   Improvement: {comparison.improvement_percentage:.2f}%")
    print(f"   Performance rating: {comparison.performance_rating}")

async def demonstrate_real_time_monitoring():
    """Demonstrate real-time performance monitoring."""
    print("\n📡 Real-Time Performance Monitoring")
    print("=" * 60)

    async with get_session() as session:
        monitor = DatabasePerformanceMonitor(session, slow_query_threshold_ms=200)
        analytics = OptimizedAnalyticsService(session)

        print("Monitoring several analytics operations...")

        # Monitor multiple operations
        operations = [
            ("Fragment Metrics", "intro_1"),
            ("Fragment Metrics", "chapter_1"),
            ("Fragment Metrics", "decision_point_1")
        ]

        for operation_name, fragment_key in operations:
            async with monitor.monitor_query(f"monitor_demo_{fragment_key}") as metrics:
                result = await analytics.get_fragment_engagement_metrics_optimized(fragment_key)

            status = "✅" if metrics.execution_time_ms < 200 else "⚠️"
            print(f"   {status} {operation_name} ({fragment_key}): {metrics.execution_time_ms:.2f}ms")

        # Get slow query report
        slow_query_report = await monitor.get_slow_query_report(limit=5)
        slow_count = slow_query_report.get('total_slow_queries', 0)

        if slow_count > 0:
            print(f"\n⚠️  Detected {slow_count} slow queries")
            recommendations = slow_query_report.get('recommendations', [])
            for rec in recommendations[:3]:
                print(f"   💡 {rec}")
        else:
            print("\n✅ No slow queries detected - performance is optimal!")

async def main():
    """Main demonstration function."""
    print("🔥 Analytics Performance Optimization Demo")
    print("Task 30: Optimize database queries for analytics performance")
    print("=" * 80)

    try:
        # Run demonstrations
        await demonstrate_optimized_analytics()
        await demonstrate_performance_comparison()
        await demonstrate_real_time_monitoring()

        print("\n" + "=" * 80)
        print("✅ Demonstration completed successfully!")
        print("\n💡 Key Benefits Demonstrated:")
        print("   • Indexed queries for O(log n) performance")
        print("   • Eager loading prevents N+1 query problems")
        print("   • Pagination handles large datasets efficiently")
        print("   • Batch operations reduce database round trips")
        print("   • Real-time monitoring tracks performance")
        print("   • Query caching improves response times")

    except Exception as e:
        logger.error(f"❌ Error during demonstration: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())