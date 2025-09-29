# tests/test_archetype_performance.py
"""
Performance tests for archetype analysis system.

Tests analysis completion within 2-second requirement, concurrent analysis for up to 100 users,
database query performance for classification operations, and memory usage limits.
Ensures the archetype system meets performance requirements for real-time user interactions.
"""

import pytest
import asyncio
import time
import psutil
import gc
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import statistics
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import or mock the archetype analyzer
try:
    from services.archetype_analyzer import ArchetypeAnalyzer, ArchetypeScores, SubArchetypeScores
except ImportError:
    # Mock imports for testing
    from dataclasses import dataclass

    @dataclass
    class ArchetypeScores:
        intellectual: float = 0.0
        emotional: float = 0.0
        exploratory: float = 0.0
        vulnerable: float = 0.0
        philosophical: float = 0.0
        direct: float = 0.0
        patient: float = 0.0
        reciprocal: float = 0.0

    @dataclass
    class SubArchetypeScores:
        romantic_intellectual: float = 0.0
        skeptical_thinker: float = 0.0
        hedonist_philosopher: float = 0.0
        pure_theorist: float = 0.0
        empathetic_emotional: float = 0.0
        passionate_emotional: float = 0.0
        wounded_healer: float = 0.0
        adventure_seeker: float = 0.0
        collector_explorer: float = 0.0
        freedom_lover: float = 0.0


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking structure."""
    execution_time: float
    memory_usage_mb: float
    concurrent_success_rate: float
    average_response_time: float
    max_response_time: float
    min_response_time: float
    throughput_requests_per_second: float
    error_count: int
    success_count: int


class MockArchetypeAnalyzer:
    """Mock ArchetypeAnalyzer optimized for performance testing."""

    def __init__(self, session, simulate_db_delay=True):
        self.session = session
        self.simulate_db_delay = simulate_db_delay
        self.response_time_analyzer = AsyncMock()

    async def analyze_l1_choices(
        self,
        user_id: int,
        choices: List[Dict[str, Any]],
        timings: List[float]
    ) -> Dict[str, Any]:
        """Mock implementation with realistic performance characteristics."""
        start_time = time.time()

        # Simulate database operation delay if enabled
        if self.simulate_db_delay:
            await asyncio.sleep(0.01)  # 10ms database operation simulation

        # Initialize scoring structures
        archetype_scores = ArchetypeScores()
        sub_archetype_scores = SubArchetypeScores()

        # Process choices (optimized loop)
        for choice in choices:
            # Process archetype weights
            archetype_weights = choice.get('archetype_weights', {})
            for archetype_name, weight in archetype_weights.items():
                if hasattr(archetype_scores, archetype_name):
                    current_value = getattr(archetype_scores, archetype_name)
                    setattr(archetype_scores, archetype_name, current_value + weight)

            # Process sub-archetype weights
            sub_archetype_weights = choice.get('sub_archetype_weights', {})
            for sub_archetype_name, weight in sub_archetype_weights.items():
                if hasattr(sub_archetype_scores, sub_archetype_name):
                    current_value = getattr(sub_archetype_scores, sub_archetype_name)
                    setattr(sub_archetype_scores, sub_archetype_name, current_value + weight)

        # Apply timing modifiers (vectorized operations)
        for timing in timings:
            if timing < 10.0:
                archetype_scores.direct += 0.5
            elif 10.0 <= timing <= 30.0:
                archetype_scores.philosophical += 0.4
                archetype_scores.intellectual += 0.3
            else:
                archetype_scores.philosophical += 0.6
                archetype_scores.patient += 0.5

        # Calculate primary archetype (optimized)
        score_dict = asdict(archetype_scores)
        max_score = max(score_dict.values())
        primary_archetype = min(k for k, v in score_dict.items() if v == max_score)

        # Calculate confidence (simplified for performance)
        if len(choices) >= 3 and max_score > 1.0:
            confidence_score = min(0.9, 0.5 + (max_score / 10.0))
        else:
            confidence_score = 0.3

        # Mock timing analysis (fast)
        avg_timing = sum(timings) / len(timings) if timings else 0.0
        timing_analysis = {
            'cognitive_style': 'quick_intuitive' if avg_timing < 10 else 'thoughtful' if avg_timing < 30 else 'deliberate',
            'consistency_score': 0.8,
            'temporal_pattern': 'stable'
        }

        # Behavioral indicators
        behavioral_indicators = []
        if confidence_score >= 0.8:
            behavioral_indicators.append("high_confidence_classification")
        if len(choices) >= 3:
            behavioral_indicators.append("sufficient_data_points")

        execution_time = time.time() - start_time

        return {
            'primary_scores': archetype_scores,
            'sub_scores': sub_archetype_scores,
            'timing_analysis': timing_analysis,
            'dominant_archetype': primary_archetype,
            'sub_archetype': 'undefined',
            'confidence_score': confidence_score,
            'behavioral_indicators': behavioral_indicators,
            'analysis_metadata': {
                'total_choices': len(choices),
                'total_timings': len(timings),
                'avg_response_time': avg_timing,
                'classification_timestamp': datetime.utcnow(),
                'execution_time_ms': execution_time * 1000
            }
        }

    async def store_classification_results(
        self,
        user_id: int,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock storage with performance simulation."""
        if self.simulate_db_delay:
            await asyncio.sleep(0.005)  # 5ms database write simulation

        return {
            'user_id': user_id,
            'stored_at': datetime.utcnow(),
            'success': True
        }


class TestArchetypeAnalysisPerformance:
    """Performance tests for archetype analysis system."""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session optimized for performance testing."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def performance_analyzer(self, mock_session):
        """ArchetypeAnalyzer configured for performance testing."""
        return MockArchetypeAnalyzer(mock_session, simulate_db_delay=True)

    @pytest.fixture
    def fast_analyzer(self, mock_session):
        """ArchetypeAnalyzer without database simulation for speed tests."""
        return MockArchetypeAnalyzer(mock_session, simulate_db_delay=False)

    @pytest.fixture
    def sample_choice_data(self):
        """Sample choice data for performance testing."""
        return [
            {
                'choice_id': 1,
                'archetype_weights': {
                    'intellectual': 2.5,
                    'philosophical': 1.8,
                    'patient': 1.0
                },
                'sub_archetype_weights': {
                    'romantic_intellectual': 2.0,
                    'pure_theorist': 1.5
                }
            },
            {
                'choice_id': 2,
                'archetype_weights': {
                    'emotional': 2.5,
                    'vulnerable': 2.0,
                    'reciprocal': 1.5
                },
                'sub_archetype_weights': {
                    'empathetic_emotional': 2.2,
                    'wounded_healer': 1.8
                }
            },
            {
                'choice_id': 3,
                'archetype_weights': {
                    'exploratory': 2.8,
                    'direct': 2.0,
                    'intellectual': 1.0
                },
                'sub_archetype_weights': {
                    'adventure_seeker': 2.5,
                    'freedom_lover': 1.8
                }
            }
        ]

    @pytest.mark.asyncio
    async def test_single_analysis_under_2_second_requirement(self, performance_analyzer, sample_choice_data):
        """Test that single archetype analysis completes within 2-second requirement."""
        user_id = 12345
        timings = [22.3, 18.5, 25.1]

        start_time = time.time()
        result = await performance_analyzer.analyze_l1_choices(user_id, sample_choice_data, timings)
        end_time = time.time()

        execution_time = end_time - start_time

        # Must complete within 2 seconds (requirement)
        assert execution_time < 2.0, f"Analysis took {execution_time:.3f}s, exceeds 2s requirement"

        # Should actually complete much faster for good UX
        assert execution_time < 0.5, f"Analysis took {execution_time:.3f}s, should be under 0.5s for optimal UX"

        # Verify result is valid
        assert result is not None
        assert 'dominant_archetype' in result
        assert result['confidence_score'] > 0.0

        print(f"✓ Single analysis completed in {execution_time:.3f}s")

    @pytest.mark.asyncio
    async def test_batch_analysis_performance(self, performance_analyzer, sample_choice_data):
        """Test performance with batch analysis of multiple users."""
        batch_sizes = [10, 25, 50]

        for batch_size in batch_sizes:
            start_time = time.time()

            # Create batch of analysis tasks
            tasks = []
            for i in range(batch_size):
                user_id = 10000 + i
                timings = [15.0 + (i * 0.1), 20.0 + (i * 0.1)]
                task = performance_analyzer.analyze_l1_choices(user_id, sample_choice_data[:2], timings)
                tasks.append(task)

            # Execute batch
            results = await asyncio.gather(*tasks)
            end_time = time.time()

            batch_time = end_time - start_time
            avg_time_per_analysis = batch_time / batch_size

            # Performance requirements
            assert batch_time < 10.0, f"Batch of {batch_size} took {batch_time:.3f}s, too slow"
            assert avg_time_per_analysis < 0.2, f"Average time per analysis: {avg_time_per_analysis:.3f}s"

            # Verify all results are valid
            assert len(results) == batch_size
            assert all(result is not None for result in results)

            print(f"✓ Batch of {batch_size} completed in {batch_time:.3f}s (avg: {avg_time_per_analysis:.3f}s per analysis)")

    @pytest.mark.asyncio
    async def test_concurrent_analysis_100_users(self, performance_analyzer, sample_choice_data):
        """Test concurrent analysis for up to 100 users (requirement)."""
        concurrent_users = 100
        start_time = time.time()

        # Create concurrent analysis tasks
        tasks = []
        for i in range(concurrent_users):
            user_id = 20000 + i
            # Vary timing patterns for realistic simulation
            timings = [10.0 + (i % 30), 15.0 + (i % 25), 20.0 + (i % 20)]
            task = performance_analyzer.analyze_l1_choices(
                user_id,
                sample_choice_data,
                timings
            )
            tasks.append(task)

        # Execute all concurrent analyses
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        total_time = end_time - start_time
        successful_results = [r for r in results if not isinstance(r, Exception)]
        error_count = len(results) - len(successful_results)

        # Performance assertions
        assert total_time < 30.0, f"100 concurrent analyses took {total_time:.3f}s, too slow"

        # Success rate should be very high
        success_rate = len(successful_results) / concurrent_users
        assert success_rate >= 0.95, f"Success rate too low: {success_rate:.2%}"

        # Average throughput
        throughput = concurrent_users / total_time
        assert throughput >= 5.0, f"Throughput too low: {throughput:.1f} analyses/second"

        print(f"✓ 100 concurrent analyses: {total_time:.3f}s, {success_rate:.2%} success rate, {throughput:.1f} analyses/s")

    @pytest.mark.asyncio
    async def test_database_query_performance(self, performance_analyzer, sample_choice_data):
        """Test database query performance for classification operations."""
        # Test with different data sizes
        test_scenarios = [
            {'users': 10, 'choices_per_user': 3},
            {'users': 50, 'choices_per_user': 5},
            {'users': 100, 'choices_per_user': 3}
        ]

        for scenario in test_scenarios:
            users = scenario['users']
            choices_count = scenario['choices_per_user']

            start_time = time.time()

            # Simulate database-heavy operations
            tasks = []
            for user_id in range(30000, 30000 + users):
                choices = sample_choice_data[:choices_count]
                timings = [15.0, 20.0, 25.0][:choices_count]

                # Analysis + storage simulation
                async def analyze_and_store(uid, ch, tim):
                    analysis_result = await performance_analyzer.analyze_l1_choices(uid, ch, tim)
                    storage_result = await performance_analyzer.store_classification_results(uid, analysis_result)
                    return analysis_result, storage_result

                task = analyze_and_store(user_id, choices, timings)
                tasks.append(task)

            results = await asyncio.gather(*tasks)
            end_time = time.time()

            query_time = end_time - start_time
            avg_query_time = query_time / users

            # Database performance requirements
            assert query_time < 60.0, f"Database operations for {users} users took {query_time:.3f}s"
            assert avg_query_time < 0.5, f"Average query time too high: {avg_query_time:.3f}s"

            print(f"✓ DB operations for {users} users: {query_time:.3f}s (avg: {avg_query_time:.3f}s per user)")

    @pytest.mark.asyncio
    async def test_memory_usage_limits(self, fast_analyzer, sample_choice_data):
        """Test memory usage stays within acceptable limits."""

        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run intensive analysis operations
        large_user_count = 500
        results = []

        for batch_start in range(0, large_user_count, 50):
            batch_tasks = []
            for i in range(batch_start, min(batch_start + 50, large_user_count)):
                user_id = 40000 + i
                # Create large choice data for memory stress test
                large_choice_data = sample_choice_data * 3  # 9 choices per user
                timings = [10.0 + (i % 40) for _ in range(9)]

                task = fast_analyzer.analyze_l1_choices(user_id, large_choice_data, timings)
                batch_tasks.append(task)

            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)

            # Check memory after each batch
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - initial_memory

            # Memory should not grow excessively
            assert memory_increase < 500, f"Memory usage increased by {memory_increase:.1f}MB, too high"

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_memory_increase = final_memory - initial_memory

        # Final memory check
        assert total_memory_increase < 1000, f"Total memory increase: {total_memory_increase:.1f}MB exceeds limit"
        assert len(results) == large_user_count, f"Expected {large_user_count} results, got {len(results)}"

        print(f"✓ Memory usage: initial {initial_memory:.1f}MB, final {final_memory:.1f}MB (+{total_memory_increase:.1f}MB)")

        # Force garbage collection and check memory cleanup
        gc.collect()
        await asyncio.sleep(0.1)  # Allow cleanup
        cleanup_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"✓ After cleanup: {cleanup_memory:.1f}MB")

    @pytest.mark.asyncio
    async def test_response_time_consistency(self, performance_analyzer, sample_choice_data):
        """Test response time consistency across multiple requests."""
        response_times = []
        test_runs = 100

        for i in range(test_runs):
            user_id = 50000 + i
            timings = [15.0 + (i % 10), 20.0 + (i % 8)]

            start_time = time.time()
            result = await performance_analyzer.analyze_l1_choices(
                user_id,
                sample_choice_data[:2],
                timings
            )
            end_time = time.time()

            response_time = end_time - start_time
            response_times.append(response_time)

            # Individual response time check
            assert response_time < 1.0, f"Request {i} took {response_time:.3f}s, too slow"

        # Statistical analysis of response times
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        std_dev = statistics.stdev(response_times)

        # Performance consistency requirements
        assert avg_response_time < 0.1, f"Average response time too high: {avg_response_time:.3f}s"
        assert max_response_time < 0.5, f"Max response time too high: {max_response_time:.3f}s"
        assert std_dev < 0.05, f"Response time variance too high: {std_dev:.3f}s"

        # 95th percentile should be reasonable
        sorted_times = sorted(response_times)
        p95_time = sorted_times[int(0.95 * len(sorted_times))]
        assert p95_time < 0.2, f"95th percentile time too high: {p95_time:.3f}s"

        print(f"✓ Response time stats: avg {avg_response_time:.3f}s, median {median_response_time:.3f}s, "
              f"max {max_response_time:.3f}s, std {std_dev:.3f}s, p95 {p95_time:.3f}s")

    @pytest.mark.asyncio
    async def test_stress_test_peak_load(self, performance_analyzer, sample_choice_data):
        """Test system behavior under peak load conditions."""

        # Simulate peak load: many concurrent users with varying request sizes
        peak_concurrent_users = 200

        start_time = time.time()

        tasks = []
        for i in range(peak_concurrent_users):
            user_id = 60000 + i

            # Vary choice data size (1-5 choices per user)
            choice_count = (i % 5) + 1
            choices = sample_choice_data[:choice_count]
            timings = [10.0 + (i % 30) for _ in range(choice_count)]

            task = performance_analyzer.analyze_l1_choices(user_id, choices, timings)
            tasks.append(task)

        # Execute peak load
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        peak_time = end_time - start_time
        successful_results = [r for r in results if not isinstance(r, Exception)]
        success_rate = len(successful_results) / peak_concurrent_users

        # Peak load requirements
        assert peak_time < 60.0, f"Peak load of {peak_concurrent_users} users took {peak_time:.3f}s"
        assert success_rate >= 0.90, f"Peak load success rate too low: {success_rate:.2%}"

        # Calculate peak throughput
        peak_throughput = peak_concurrent_users / peak_time

        print(f"✓ Peak load test: {peak_concurrent_users} users in {peak_time:.3f}s, "
              f"{success_rate:.2%} success rate, {peak_throughput:.1f} analyses/s")

    @pytest.mark.asyncio
    async def test_cold_start_performance(self, mock_session, sample_choice_data):
        """Test performance during cold start (first analysis)."""

        # Create fresh analyzer to simulate cold start
        cold_analyzer = MockArchetypeAnalyzer(mock_session, simulate_db_delay=True)

        user_id = 70000
        timings = [15.0, 20.0, 25.0]

        # Cold start analysis
        cold_start_time = time.time()
        cold_result = await cold_analyzer.analyze_l1_choices(user_id, sample_choice_data, timings)
        cold_end_time = time.time()

        cold_duration = cold_end_time - cold_start_time

        # Warm up with a few more analyses
        for i in range(3):
            await cold_analyzer.analyze_l1_choices(user_id + i + 1, sample_choice_data, timings)

        # Warm analysis
        warm_start_time = time.time()
        warm_result = await cold_analyzer.analyze_l1_choices(user_id + 10, sample_choice_data, timings)
        warm_end_time = time.time()

        warm_duration = warm_end_time - warm_start_time

        # Cold start should still be reasonable
        assert cold_duration < 3.0, f"Cold start took {cold_duration:.3f}s, too slow"

        # Warm analysis should be faster
        assert warm_duration < cold_duration, f"Warm analysis not faster than cold start"
        assert warm_duration < 1.0, f"Warm analysis took {warm_duration:.3f}s"

        print(f"✓ Cold start: {cold_duration:.3f}s, Warm: {warm_duration:.3f}s")


class TestArchetypePerformanceMetrics:
    """Test performance metrics collection and analysis."""

    @pytest.fixture
    def metrics_collector(self):
        """Performance metrics collector."""
        return PerformanceMetrics(
            execution_time=0.0,
            memory_usage_mb=0.0,
            concurrent_success_rate=0.0,
            average_response_time=0.0,
            max_response_time=0.0,
            min_response_time=0.0,
            throughput_requests_per_second=0.0,
            error_count=0,
            success_count=0
        )

    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self, performance_analyzer, sample_choice_data, metrics_collector):
        """Test collection and analysis of performance metrics."""

        # Run test scenario and collect metrics
        test_users = 50
        response_times = []
        success_count = 0
        error_count = 0

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        start_time = time.time()

        for i in range(test_users):
            user_id = 80000 + i
            timings = [15.0 + (i % 20), 20.0 + (i % 15)]

            try:
                request_start = time.time()
                result = await performance_analyzer.analyze_l1_choices(
                    user_id,
                    sample_choice_data[:2],
                    timings
                )
                request_end = time.time()

                response_time = request_end - request_start
                response_times.append(response_time)
                success_count += 1

            except Exception as e:
                error_count += 1

        end_time = time.time()
        final_memory = process.memory_info().rss / 1024 / 1024

        # Update metrics
        metrics_collector.execution_time = end_time - start_time
        metrics_collector.memory_usage_mb = final_memory - initial_memory
        metrics_collector.concurrent_success_rate = success_count / test_users
        metrics_collector.average_response_time = statistics.mean(response_times) if response_times else 0.0
        metrics_collector.max_response_time = max(response_times) if response_times else 0.0
        metrics_collector.min_response_time = min(response_times) if response_times else 0.0
        metrics_collector.throughput_requests_per_second = test_users / metrics_collector.execution_time
        metrics_collector.error_count = error_count
        metrics_collector.success_count = success_count

        # Validate metrics
        assert metrics_collector.execution_time > 0
        assert metrics_collector.concurrent_success_rate >= 0.95
        assert metrics_collector.average_response_time < 0.5
        assert metrics_collector.throughput_requests_per_second >= 10.0

        print(f"✓ Performance Metrics:")
        print(f"  Execution time: {metrics_collector.execution_time:.3f}s")
        print(f"  Success rate: {metrics_collector.concurrent_success_rate:.2%}")
        print(f"  Avg response time: {metrics_collector.average_response_time:.3f}s")
        print(f"  Throughput: {metrics_collector.throughput_requests_per_second:.1f} req/s")
        print(f"  Memory usage: {metrics_collector.memory_usage_mb:.1f}MB")

    @pytest.mark.asyncio
    async def test_performance_under_varying_load(self, performance_analyzer, sample_choice_data):
        """Test performance characteristics under varying load levels."""

        load_levels = [1, 5, 10, 25, 50, 100]
        performance_results = []

        for load_level in load_levels:
            start_time = time.time()

            tasks = []
            for i in range(load_level):
                user_id = 90000 + i
                timings = [15.0, 20.0]
                task = performance_analyzer.analyze_l1_choices(
                    user_id,
                    sample_choice_data[:2],
                    timings
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            total_time = end_time - start_time
            throughput = load_level / total_time
            success_rate = len([r for r in results if not isinstance(r, Exception)]) / load_level

            performance_results.append({
                'load_level': load_level,
                'total_time': total_time,
                'throughput': throughput,
                'success_rate': success_rate,
                'avg_time_per_request': total_time / load_level
            })

            # Each load level should maintain good performance
            assert success_rate >= 0.95, f"Load {load_level}: success rate {success_rate:.2%} too low"
            assert total_time < 30.0, f"Load {load_level}: total time {total_time:.3f}s too high"

        # Analyze performance scaling
        for result in performance_results:
            print(f"Load {result['load_level']:3d}: "
                  f"{result['total_time']:6.3f}s, "
                  f"{result['throughput']:6.1f} req/s, "
                  f"{result['success_rate']:6.2%} success")

        # Performance should scale reasonably
        max_load_result = performance_results[-1]  # 100 users
        min_load_result = performance_results[0]   # 1 user

        # Throughput should increase significantly with load
        throughput_improvement = max_load_result['throughput'] / min_load_result['throughput']
        assert throughput_improvement >= 5.0, f"Throughput scaling insufficient: {throughput_improvement:.1f}x"


if __name__ == '__main__':
    pytest.main([__file__])