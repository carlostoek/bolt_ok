"""
Database Performance Monitoring Service for Analytics Optimization.
Task 30: Optimize database queries for analytics performance.

This service provides comprehensive database performance monitoring,
query analysis, and optimization recommendations for the narrative module.
"""

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from sqlalchemy.pool import StaticPool
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

@dataclass
class QueryPerformanceMetrics:
    """Performance metrics for a database query."""
    query_id: str
    query_text: str
    execution_time_ms: float
    rows_examined: int
    rows_returned: int
    cpu_time_ms: Optional[float] = None
    memory_usage_bytes: Optional[int] = None
    index_usage: Optional[Dict[str, Any]] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

class DatabasePerformanceMonitor:
    """
    Comprehensive database performance monitoring service for analytics queries.

    Features:
    - Real-time query performance tracking
    - Slow query detection and logging
    - Index usage analysis
    - Query optimization recommendations
    - Performance benchmarking
    """

    def __init__(self, session: AsyncSession, slow_query_threshold_ms: float = 1000):
        """
        Initialize the performance monitor.

        Args:
            session: Database session
            slow_query_threshold_ms: Threshold for identifying slow queries
        """
        self.session = session
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.query_metrics: List[QueryPerformanceMetrics] = []
        self.slow_queries: List[QueryPerformanceMetrics] = []
        self.monitoring_enabled = True

    @asynccontextmanager
    async def monitor_query(self, query_id: str, query_text: str = ""):
        """
        Context manager for monitoring query performance.

        Usage:
            async with monitor.monitor_query("user_analytics", "SELECT ...") as metrics:
                result = await session.execute(query)
                metrics.rows_returned = len(result.scalars().all())
        """
        start_time = time.perf_counter()
        start_memory = self._get_memory_usage()

        metrics = QueryPerformanceMetrics(
            query_id=query_id,
            query_text=query_text or "Query text not provided",
            execution_time_ms=0,
            rows_examined=0,
            rows_returned=0
        )

        try:
            yield metrics
        finally:
            end_time = time.perf_counter()
            end_memory = self._get_memory_usage()

            metrics.execution_time_ms = (end_time - start_time) * 1000
            metrics.memory_usage_bytes = end_memory - start_memory

            if self.monitoring_enabled:
                await self._record_query_metrics(metrics)

    async def monitor_analytics_query_performance(
        self,
        query_function: Callable,
        query_id: str,
        *args,
        **kwargs
    ) -> Tuple[Any, QueryPerformanceMetrics]:
        """
        Monitor the performance of an analytics query function.

        Args:
            query_function: The async function to monitor
            query_id: Identifier for the query
            *args, **kwargs: Arguments to pass to the query function

        Returns:
            Tuple of (query_result, performance_metrics)
        """
        async with self.monitor_query(query_id, str(query_function.__name__)) as metrics:
            try:
                result = await query_function(*args, **kwargs)

                # Extract result metadata if available
                if isinstance(result, dict):
                    if 'data' in result and isinstance(result['data'], list):
                        metrics.rows_returned = len(result['data'])
                    elif 'metrics' in result:
                        metrics.rows_returned = 1

                return result, metrics

            except Exception as e:
                logger.error(f"Error monitoring query {query_id}: {e}")
                raise

    async def analyze_query_plan(self, query: str) -> Dict[str, Any]:
        """
        Analyze the execution plan for a SQL query.

        Args:
            query: SQL query to analyze

        Returns:
            Dictionary containing query plan analysis
        """
        try:
            # SQLite EXPLAIN QUERY PLAN
            explain_query = f"EXPLAIN QUERY PLAN {query}"
            result = await self.session.execute(text(explain_query))
            plan_rows = result.fetchall()

            plan_analysis = {
                "query": query,
                "execution_plan": [
                    {
                        "id": row[0],
                        "parent": row[1],
                        "detail": row[3] if len(row) > 3 else row[2]
                    }
                    for row in plan_rows
                ],
                "index_usage": self._analyze_index_usage(plan_rows),
                "optimization_suggestions": self._generate_optimization_suggestions(plan_rows)
            }

            return plan_analysis

        except Exception as e:
            logger.error(f"Error analyzing query plan: {e}")
            return {"error": str(e)}

    async def benchmark_analytics_operations(self) -> Dict[str, Any]:
        """
        Benchmark common analytics operations for performance assessment.

        Returns:
            Dictionary containing benchmark results for various operations
        """
        logger.info("Starting analytics operations benchmark")

        benchmark_results = {
            "benchmark_date": datetime.utcnow().isoformat(),
            "operations": {},
            "summary": {}
        }

        # Define benchmark operations
        benchmark_operations = [
            ("fragment_analytics_query", self._benchmark_fragment_analytics),
            ("user_journey_aggregation", self._benchmark_user_journey_aggregation),
            ("user_segmentation", self._benchmark_user_segmentation),
            ("choice_distribution_analysis", self._benchmark_choice_distribution),
            ("real_time_progress_tracking", self._benchmark_real_time_progress)
        ]

        # Execute benchmarks
        for operation_name, benchmark_func in benchmark_operations:
            try:
                logger.info(f"Benchmarking {operation_name}")
                operation_result = await benchmark_func()
                benchmark_results["operations"][operation_name] = operation_result

            except Exception as e:
                logger.error(f"Error benchmarking {operation_name}: {e}")
                benchmark_results["operations"][operation_name] = {
                    "status": "error",
                    "error": str(e)
                }

        # Generate summary
        benchmark_results["summary"] = self._generate_benchmark_summary(
            benchmark_results["operations"]
        )

        return benchmark_results

    async def get_slow_query_report(self, limit: int = 10) -> Dict[str, Any]:
        """
        Generate a report of slow queries identified during monitoring.

        Args:
            limit: Maximum number of slow queries to include

        Returns:
            Dictionary containing slow query analysis
        """
        slow_queries = sorted(
            self.slow_queries,
            key=lambda q: q.execution_time_ms,
            reverse=True
        )[:limit]

        return {
            "total_slow_queries": len(self.slow_queries),
            "threshold_ms": self.slow_query_threshold_ms,
            "slow_queries": [asdict(query) for query in slow_queries],
            "recommendations": self._generate_slow_query_recommendations(slow_queries)
        }

    async def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive performance summary of monitored queries.

        Returns:
            Dictionary containing performance analysis summary
        """
        if not self.query_metrics:
            return {
                "status": "no_data",
                "message": "No query metrics available"
            }

        execution_times = [m.execution_time_ms for m in self.query_metrics]

        return {
            "total_queries_monitored": len(self.query_metrics),
            "monitoring_period": {
                "start": min(m.timestamp for m in self.query_metrics),
                "end": max(m.timestamp for m in self.query_metrics)
            },
            "performance_stats": {
                "average_execution_time_ms": sum(execution_times) / len(execution_times),
                "median_execution_time_ms": sorted(execution_times)[len(execution_times) // 2],
                "max_execution_time_ms": max(execution_times),
                "min_execution_time_ms": min(execution_times),
                "slow_queries_count": len(self.slow_queries),
                "slow_queries_percentage": (len(self.slow_queries) / len(self.query_metrics)) * 100
            },
            "query_distribution": self._get_query_distribution(),
            "optimization_impact": self._calculate_optimization_impact()
        }

    async def _record_query_metrics(self, metrics: QueryPerformanceMetrics):
        """Record query metrics and identify slow queries."""
        self.query_metrics.append(metrics)

        if metrics.execution_time_ms > self.slow_query_threshold_ms:
            self.slow_queries.append(metrics)
            logger.warning(
                f"Slow query detected: {metrics.query_id} "
                f"({metrics.execution_time_ms:.2f}ms)"
            )

        # Keep only recent metrics (last 1000 queries)
        if len(self.query_metrics) > 1000:
            self.query_metrics = self.query_metrics[-1000:]

        if len(self.slow_queries) > 100:
            self.slow_queries = self.slow_queries[-100:]

    def _analyze_index_usage(self, plan_rows: List) -> Dict[str, Any]:
        """Analyze index usage from query plan."""
        index_usage = {
            "indexes_used": [],
            "table_scans": [],
            "index_recommendations": []
        }

        for row in plan_rows:
            detail = row[3] if len(row) > 3 else row[2]
            detail_lower = detail.lower()

            if "using index" in detail_lower:
                index_usage["indexes_used"].append(detail)
            elif "scan table" in detail_lower:
                index_usage["table_scans"].append(detail)

        return index_usage

    def _generate_optimization_suggestions(self, plan_rows: List) -> List[str]:
        """Generate optimization suggestions based on query plan."""
        suggestions = []

        for row in plan_rows:
            detail = row[3] if len(row) > 3 else row[2]
            detail_lower = detail.lower()

            if "scan table" in detail_lower and "using index" not in detail_lower:
                suggestions.append(f"Consider adding index for table scan: {detail}")

            if "temp b-tree" in detail_lower:
                suggestions.append("Query requires temporary sorting - consider adding appropriate index")

        if not suggestions:
            suggestions.append("Query appears to be well-optimized")

        return suggestions

    async def _benchmark_fragment_analytics(self) -> Dict[str, Any]:
        """Benchmark fragment analytics queries."""
        start_time = time.perf_counter()

        try:
            # Simulate fragment analytics query
            query = text("""
                SELECT fragment_key, view_count, completion_count,
                       (completion_count * 100.0 / NULLIF(view_count, 0)) as completion_rate
                FROM fragment_analytics
                WHERE view_count > 0
                ORDER BY view_count DESC
                LIMIT 10
            """)

            result = await self.session.execute(query)
            rows = result.fetchall()

            execution_time = (time.perf_counter() - start_time) * 1000

            return {
                "status": "success",
                "execution_time_ms": execution_time,
                "rows_processed": len(rows),
                "performance_rating": "excellent" if execution_time < 100 else "good" if execution_time < 500 else "needs_optimization"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "execution_time_ms": (time.perf_counter() - start_time) * 1000
            }

    async def _benchmark_user_journey_aggregation(self) -> Dict[str, Any]:
        """Benchmark user journey aggregation queries."""
        start_time = time.perf_counter()

        try:
            query = text("""
                SELECT engagement_level, COUNT(*) as user_count,
                       AVG(fragments_completed) as avg_fragments,
                       AVG(total_time_spent) as avg_time_spent
                FROM user_journey_analytics
                GROUP BY engagement_level
            """)

            result = await self.session.execute(query)
            rows = result.fetchall()

            execution_time = (time.perf_counter() - start_time) * 1000

            return {
                "status": "success",
                "execution_time_ms": execution_time,
                "rows_processed": len(rows),
                "performance_rating": "excellent" if execution_time < 200 else "good" if execution_time < 1000 else "needs_optimization"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "execution_time_ms": (time.perf_counter() - start_time) * 1000
            }

    async def _benchmark_user_segmentation(self) -> Dict[str, Any]:
        """Benchmark user segmentation queries."""
        start_time = time.perf_counter()

        try:
            # Simulate complex user segmentation
            one_week_ago = datetime.utcnow() - timedelta(days=7)

            query = text("""
                SELECT
                    COUNT(CASE WHEN points > 1000 THEN 1 END) as high_value_users,
                    COUNT(CASE WHEN role = 'vip' THEN 1 END) as vip_users,
                    COUNT(CASE WHEN created_at > :week_ago THEN 1 END) as recent_users
                FROM users
            """)

            result = await self.session.execute(query, {"week_ago": one_week_ago})
            rows = result.fetchall()

            execution_time = (time.perf_counter() - start_time) * 1000

            return {
                "status": "success",
                "execution_time_ms": execution_time,
                "rows_processed": len(rows),
                "performance_rating": "excellent" if execution_time < 100 else "good" if execution_time < 500 else "needs_optimization"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "execution_time_ms": (time.perf_counter() - start_time) * 1000
            }

    async def _benchmark_choice_distribution(self) -> Dict[str, Any]:
        """Benchmark choice distribution analysis."""
        start_time = time.perf_counter()

        try:
            query = text("""
                SELECT fragment_key, choice_distribution
                FROM fragment_analytics
                WHERE choice_distribution IS NOT NULL
                LIMIT 50
            """)

            result = await self.session.execute(query)
            rows = result.fetchall()

            execution_time = (time.perf_counter() - start_time) * 1000

            return {
                "status": "success",
                "execution_time_ms": execution_time,
                "rows_processed": len(rows),
                "performance_rating": "excellent" if execution_time < 50 else "good" if execution_time < 200 else "needs_optimization"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "execution_time_ms": (time.perf_counter() - start_time) * 1000
            }

    async def _benchmark_real_time_progress(self) -> Dict[str, Any]:
        """Benchmark real-time progress tracking queries."""
        start_time = time.perf_counter()

        try:
            query = text("""
                SELECT user_id, current_fragment_key, fragments_visited, last_activity_at
                FROM user_narrative_states
                WHERE last_activity_at > datetime('now', '-1 day')
                LIMIT 100
            """)

            result = await self.session.execute(query)
            rows = result.fetchall()

            execution_time = (time.perf_counter() - start_time) * 1000

            return {
                "status": "success",
                "execution_time_ms": execution_time,
                "rows_processed": len(rows),
                "performance_rating": "excellent" if execution_time < 50 else "good" if execution_time < 200 else "needs_optimization"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "execution_time_ms": (time.perf_counter() - start_time) * 1000
            }

    def _generate_benchmark_summary(self, operations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of benchmark results."""
        successful_operations = [
            op for op in operations.values()
            if op.get("status") == "success"
        ]

        if not successful_operations:
            return {"status": "no_successful_operations"}

        execution_times = [op["execution_time_ms"] for op in successful_operations]
        performance_ratings = [op["performance_rating"] for op in successful_operations]

        return {
            "total_operations": len(operations),
            "successful_operations": len(successful_operations),
            "average_execution_time_ms": sum(execution_times) / len(execution_times),
            "fastest_operation_ms": min(execution_times),
            "slowest_operation_ms": max(execution_times),
            "performance_distribution": {
                "excellent": performance_ratings.count("excellent"),
                "good": performance_ratings.count("good"),
                "needs_optimization": performance_ratings.count("needs_optimization")
            },
            "overall_rating": self._calculate_overall_rating(performance_ratings)
        }

    def _calculate_overall_rating(self, ratings: List[str]) -> str:
        """Calculate overall performance rating."""
        excellent_count = ratings.count("excellent")
        good_count = ratings.count("good")
        total = len(ratings)

        if excellent_count / total >= 0.8:
            return "excellent"
        elif (excellent_count + good_count) / total >= 0.7:
            return "good"
        else:
            return "needs_optimization"

    def _generate_slow_query_recommendations(self, slow_queries: List[QueryPerformanceMetrics]) -> List[str]:
        """Generate recommendations for slow queries."""
        recommendations = []

        if not slow_queries:
            return ["No slow queries detected - performance is optimal"]

        # Analyze common patterns in slow queries
        query_patterns = {}
        for query in slow_queries:
            query_id_base = query.query_id.split('_')[0]
            query_patterns[query_id_base] = query_patterns.get(query_id_base, 0) + 1

        # Generate specific recommendations
        for pattern, count in query_patterns.items():
            if count > 1:
                recommendations.append(
                    f"Multiple slow queries detected in {pattern} operations - "
                    f"consider adding specific indexes or query optimization"
                )

        recommendations.extend([
            "Review query execution plans for table scans",
            "Consider implementing query result caching for frequently accessed data",
            "Evaluate index coverage for common WHERE clause conditions",
            "Consider query batching for operations on multiple records"
        ])

        return recommendations

    def _get_query_distribution(self) -> Dict[str, int]:
        """Get distribution of queries by type."""
        distribution = {}
        for metrics in self.query_metrics:
            query_type = metrics.query_id.split('_')[0]
            distribution[query_type] = distribution.get(query_type, 0) + 1
        return distribution

    def _calculate_optimization_impact(self) -> Dict[str, Any]:
        """Calculate the potential impact of optimizations."""
        if len(self.query_metrics) < 10:
            return {"insufficient_data": True}

        total_time = sum(m.execution_time_ms for m in self.query_metrics)
        slow_query_time = sum(m.execution_time_ms for m in self.slow_queries)

        return {
            "total_query_time_ms": total_time,
            "slow_query_time_ms": slow_query_time,
            "slow_query_time_percentage": (slow_query_time / total_time) * 100 if total_time > 0 else 0,
            "potential_time_savings_ms": slow_query_time * 0.5,  # Assume 50% improvement
            "optimization_priority": "high" if slow_query_time / total_time > 0.3 else "medium" if slow_query_time / total_time > 0.1 else "low"
        }

    def _get_memory_usage(self) -> int:
        """Get current memory usage (placeholder implementation)."""
        # In a real implementation, this would use psutil or similar
        # For SQLite, memory monitoring is limited
        return 0

    def enable_monitoring(self):
        """Enable query performance monitoring."""
        self.monitoring_enabled = True
        logger.info("Database performance monitoring enabled")

    def disable_monitoring(self):
        """Disable query performance monitoring."""
        self.monitoring_enabled = False
        logger.info("Database performance monitoring disabled")

    def clear_metrics(self):
        """Clear all recorded metrics."""
        self.query_metrics.clear()
        self.slow_queries.clear()
        logger.info("Performance metrics cleared")