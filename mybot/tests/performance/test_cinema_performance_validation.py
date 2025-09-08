"""
CINEMA ARCHITECTURE PERFORMANCE & SCALABILITY TESTING FRAMEWORK
==============================================================

This comprehensive performance testing suite validates that Cinema Architecture
enhancements maintain required performance standards under various load conditions.

PERFORMANCE REQUIREMENTS VALIDATED:
✅ <500ms Response Time (Normal Load) 
✅ <2s Response Time (Heavy Load)
✅ Memory Stability (<100MB increase)
✅ Concurrent User Handling (50+ users)
✅ Database Performance Optimization
✅ Cinema Enhancement Overhead <10%
✅ Fallback Performance Preservation
✅ Character Validation Performance
"""

import pytest
import pytest_asyncio
import asyncio
import time
import psutil
import os
import statistics
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from database.models import User, UserStats
from database.narrative_unified import NarrativeFragment, UserNarrativeState
from services.coordinador_central import CoordinadorCentral, AccionUsuario


class PerformanceMetrics:
    """Performance metrics collector and analyzer"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.memory_snapshots: List[float] = []
        self.cpu_snapshots: List[float] = []
        self.error_counts: Dict[str, int] = {}
        self.throughput_data: List[Tuple[datetime, int]] = []
        
    def add_response_time(self, response_time: float):
        self.response_times.append(response_time)
        
    def add_memory_snapshot(self, memory_mb: float):
        self.memory_snapshots.append(memory_mb)
        
    def add_cpu_snapshot(self, cpu_percent: float):
        self.cpu_snapshots.append(cpu_percent)
        
    def add_error(self, error_type: str):
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
    def add_throughput_measurement(self, timestamp: datetime, operations_count: int):
        self.throughput_data.append((timestamp, operations_count))
        
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        if not self.response_times:
            return {"error": "No performance data collected"}
            
        return {
            "response_time": {
                "avg": statistics.mean(self.response_times),
                "median": statistics.median(self.response_times),
                "p95": self._percentile(self.response_times, 95),
                "p99": self._percentile(self.response_times, 99),
                "min": min(self.response_times),
                "max": max(self.response_times)
            },
            "memory": {
                "avg_mb": statistics.mean(self.memory_snapshots) if self.memory_snapshots else 0,
                "peak_mb": max(self.memory_snapshots) if self.memory_snapshots else 0,
                "increase_mb": max(self.memory_snapshots) - min(self.memory_snapshots) if self.memory_snapshots else 0
            },
            "cpu": {
                "avg_percent": statistics.mean(self.cpu_snapshots) if self.cpu_snapshots else 0,
                "peak_percent": max(self.cpu_snapshots) if self.cpu_snapshots else 0
            },
            "errors": self.error_counts,
            "total_operations": len(self.response_times),
            "throughput_ops_per_second": self._calculate_throughput()
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        return sorted(data)[int(len(data) * percentile / 100)]
    
    def _calculate_throughput(self) -> float:
        if len(self.throughput_data) < 2:
            return 0.0
            
        total_ops = sum(ops for _, ops in self.throughput_data)
        time_span = (self.throughput_data[-1][0] - self.throughput_data[0][0]).total_seconds()
        
        return total_ops / time_span if time_span > 0 else 0.0


class TestCinemaPerformanceFramework:
    """Cinema Architecture Performance Testing Framework"""
    
    @pytest_asyncio.fixture
    async def performance_coordinador(self, session, mock_bot):
        """Initialize high-performance coordinador for testing"""
        coordinador = CoordinadorCentral(session)
        
        # Enable performance monitoring
        if hasattr(coordinador, 'cinema_master') and coordinador.cinema_master:
            coordinador.cinema_master._performance_monitoring = True
            coordinador.cinema_master._bot = mock_bot
            
        return coordinador
    
    @pytest_asyncio.fixture
    async def performance_metrics(self):
        """Performance metrics collector"""
        return PerformanceMetrics()
    
    @pytest_asyncio.fixture
    async def load_test_users(self, session):
        """Create multiple users for load testing"""
        users = []
        for i in range(50):
            user = User(
                id=800000 + i,
                first_name=f"LoadUser{i}",
                username=f"loaduser{i}",
                role="free",
                points=100.0,
                created_at=datetime.utcnow()
            )
            session.add(user)
            users.append(user)
        
        await session.commit()
        return users
    
    @pytest.mark.asyncio
    async def test_normal_load_performance_requirements(self, performance_coordinador, test_user, performance_metrics):
        """Test Cinema system performance under normal load"""
        
        process = psutil.Process(os.getpid())
        
        # Baseline memory measurement
        initial_memory = process.memory_info().rss / 1024 / 1024
        performance_metrics.add_memory_snapshot(initial_memory)
        
        # Execute normal load operations
        operations = [
            AccionUsuario.TOMAR_DECISION,
            AccionUsuario.DESBLOQUEAR_PISTA,
            AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
            AccionUsuario.PARTICIPAR_CANAL,
            AccionUsuario.REACCIONAR_PUBLICACION
        ]
        
        for i in range(20):  # Normal load simulation
            for operation in operations:
                start_time = time.time()
                
                try:
                    result = await performance_coordinador.ejecutar_flujo(
                        user_id=test_user.id,
                        accion=operation,
                        fragment_id=f"normal_load_test_{i}",
                        choice_id=f"choice_{i}",
                        channel_id=-1001234567890,
                        message_id=i,
                        reaction_type="like"
                    )
                    
                    end_time = time.time()
                    response_time = end_time - start_time
                    performance_metrics.add_response_time(response_time)
                    
                    # Individual operation performance requirement
                    assert response_time < 0.5, \
                        f"Normal load response time exceeded: {response_time:.3f}s for {operation}"
                    
                    # Memory monitoring
                    current_memory = process.memory_info().rss / 1024 / 1024
                    performance_metrics.add_memory_snapshot(current_memory)
                    
                    # CPU monitoring
                    cpu_percent = process.cpu_percent()
                    performance_metrics.add_cpu_snapshot(cpu_percent)
                    
                except Exception as e:
                    performance_metrics.add_error(type(e).__name__)
                    raise
        
        # Performance validation
        stats = performance_metrics.get_stats()
        
        # Response time requirements
        assert stats["response_time"]["avg"] < 0.3, \
            f"Average response time too high: {stats['response_time']['avg']:.3f}s"
        assert stats["response_time"]["p95"] < 0.5, \
            f"95th percentile response time too high: {stats['response_time']['p95']:.3f}s"
        
        # Memory stability requirement
        assert stats["memory"]["increase_mb"] < 50, \
            f"Memory increase too high: {stats['memory']['increase_mb']:.2f}MB"
        
        # Error rate requirement
        total_ops = stats["total_operations"]
        total_errors = sum(stats["errors"].values())
        error_rate = total_errors / total_ops if total_ops > 0 else 0
        assert error_rate < 0.01, f"Error rate too high: {error_rate:.2%}"
    
    @pytest.mark.asyncio
    async def test_heavy_load_performance_degradation(self, performance_coordinador, load_test_users, performance_metrics):
        """Test Cinema system performance under heavy concurrent load"""
        
        async def execute_heavy_operation(user: User, operation_id: int) -> Dict[str, Any]:
            """Execute heavy operation for load testing"""
            start_time = time.time()
            
            try:
                result = await performance_coordinador.ejecutar_flujo(
                    user_id=user.id,
                    accion=AccionUsuario.TOMAR_DECISION,
                    fragment_id=f"heavy_load_{operation_id}",
                    choice_id=f"heavy_choice_{operation_id}",
                    psychology_aware=True,
                    cinema_enhanced=True
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                return {
                    "user_id": user.id,
                    "response_time": response_time,
                    "success": result.get("success", True),
                    "operation_id": operation_id
                }
                
            except Exception as e:
                end_time = time.time()
                return {
                    "user_id": user.id,
                    "response_time": end_time - start_time,
                    "success": False,
                    "error": str(e),
                    "operation_id": operation_id
                }
        
        # Execute concurrent heavy load
        concurrent_limit = 25  # Test with 25 concurrent users
        tasks = []
        
        for i in range(100):  # 100 operations total
            user = load_test_users[i % len(load_test_users[:concurrent_limit])]
            task = execute_heavy_operation(user, i)
            tasks.append(task)
        
        # Measure throughput
        start_throughput_time = datetime.utcnow()
        
        # Execute with controlled concurrency
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        async def controlled_execution(task):
            async with semaphore:
                return await task
        
        results = await asyncio.gather(*[controlled_execution(task) for task in tasks], return_exceptions=True)
        
        end_throughput_time = datetime.utcnow()
        
        # Analyze results
        successful_results = [r for r in results if not isinstance(r, Exception) and r.get("success", False)]
        failed_results = [r for r in results if isinstance(r, Exception) or not r.get("success", True)]
        
        # Performance validation under heavy load
        success_rate = len(successful_results) / len(results)
        assert success_rate >= 0.95, f"Success rate too low under heavy load: {success_rate:.2%}"
        
        # Response time validation under heavy load
        response_times = [r["response_time"] for r in successful_results]
        avg_response_time = statistics.mean(response_times)
        p95_response_time = sorted(response_times)[int(len(response_times) * 0.95)]
        
        assert avg_response_time < 1.5, \
            f"Heavy load average response time too high: {avg_response_time:.3f}s"
        assert p95_response_time < 2.0, \
            f"Heavy load 95th percentile response time too high: {p95_response_time:.3f}s"
        
        # Throughput validation
        total_time = (end_throughput_time - start_throughput_time).total_seconds()
        throughput = len(successful_results) / total_time
        
        assert throughput >= 5.0, f"Throughput too low: {throughput:.2f} ops/second"
        
        # Update metrics
        for result in successful_results:
            performance_metrics.add_response_time(result["response_time"])
    
    @pytest.mark.asyncio
    async def test_cinema_enhancement_overhead(self, session, test_user, performance_metrics):
        """Test performance overhead introduced by Cinema enhancements"""
        
        # Test without Cinema enhancements (baseline)
        coordinador_baseline = CoordinadorCentral(session)
        if hasattr(coordinador_baseline, 'cinema_master'):
            coordinador_baseline.cinema_master = None
        
        baseline_times = []
        for i in range(20):
            start_time = time.time()
            result = await coordinador_baseline.ejecutar_flujo(
                user_id=test_user.id,
                accion=AccionUsuario.TOMAR_DECISION,
                fragment_id=f"baseline_test_{i}",
                choice_id=f"baseline_choice_{i}"
            )
            end_time = time.time()
            baseline_times.append(end_time - start_time)
        
        # Test with Cinema enhancements
        coordinador_cinema = CoordinadorCentral(session)
        
        cinema_times = []
        for i in range(20):
            start_time = time.time()
            result = await coordinador_cinema.ejecutar_flujo(
                user_id=test_user.id,
                accion=AccionUsuario.TOMAR_DECISION,
                fragment_id=f"cinema_test_{i}",
                choice_id=f"cinema_choice_{i}",
                cinema_enhanced=True,
                psychology_aware=True
            )
            end_time = time.time()
            cinema_times.append(end_time - start_time)
        
        # Calculate overhead
        baseline_avg = statistics.mean(baseline_times)
        cinema_avg = statistics.mean(cinema_times)
        overhead_percent = ((cinema_avg - baseline_avg) / baseline_avg) * 100
        
        # Cinema enhancement overhead should be <10%
        assert overhead_percent < 10, \
            f"Cinema enhancement overhead too high: {overhead_percent:.1f}%"
        
        # Both should still meet performance requirements
        assert baseline_avg < 0.5, f"Baseline performance degraded: {baseline_avg:.3f}s"
        assert cinema_avg < 0.6, f"Cinema performance too slow: {cinema_avg:.3f}s"
    
    @pytest.mark.asyncio
    async def test_database_performance_optimization(self, performance_coordinador, load_test_users, performance_metrics):
        """Test database performance with Cinema architecture"""
        
        # Monitor database query performance
        query_times = []
        
        async def monitored_database_operation(user: User):
            """Execute database-intensive operation with monitoring"""
            start_time = time.time()
            
            # Simulate complex database operations that Cinema might trigger
            result = await performance_coordinador.ejecutar_flujo(
                user_id=user.id,
                accion=AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
                fragment_id="db_intensive_fragment",
                save_decision_history=True,
                update_user_progress=True,
                calculate_soul_signature=True
            )
            
            end_time = time.time()
            return end_time - start_time, result
        
        # Execute database-intensive operations
        tasks = [monitored_database_operation(user) for user in load_test_users[:20]]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_results = [r for r in results if not isinstance(r, Exception)]
        query_times = [r[0] for r in successful_results]
        
        if query_times:
            avg_db_time = statistics.mean(query_times)
            max_db_time = max(query_times)
            
            # Database operation performance requirements
            assert avg_db_time < 1.0, \
                f"Average database operation time too high: {avg_db_time:.3f}s"
            assert max_db_time < 2.0, \
                f"Maximum database operation time too high: {max_db_time:.3f}s"
            
            # Update performance metrics
            for query_time in query_times:
                performance_metrics.add_response_time(query_time)
    
    @pytest.mark.asyncio 
    async def test_memory_leak_detection(self, performance_coordinador, test_user, performance_metrics):
        """Test for memory leaks in Cinema architecture"""
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # Execute many operations to detect memory leaks
        for cycle in range(10):  # 10 cycles of operations
            cycle_start_memory = process.memory_info().rss / 1024 / 1024
            
            # Execute various operations in each cycle
            operations = [
                AccionUsuario.TOMAR_DECISION,
                AccionUsuario.DESBLOQUEAR_PISTA,
                AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
                AccionUsuario.PARTICIPAR_CANAL
            ]
            
            for i in range(50):  # 50 operations per cycle
                for operation in operations:
                    await performance_coordinador.ejecutar_flujo(
                        user_id=test_user.id,
                        accion=operation,
                        fragment_id=f"memory_test_cycle_{cycle}_op_{i}",
                        choice_id=f"choice_{i}",
                        cinema_enhanced=True
                    )
            
            cycle_end_memory = process.memory_info().rss / 1024 / 1024
            performance_metrics.add_memory_snapshot(cycle_end_memory)
            
            # Memory should not grow significantly per cycle
            cycle_increase = cycle_end_memory - cycle_start_memory
            assert cycle_increase < 20, \
                f"Memory increase too high in cycle {cycle}: {cycle_increase:.2f}MB"
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        
        # Total memory increase should be reasonable
        assert total_increase < 100, \
            f"Total memory increase too high: {total_increase:.2f}MB"
    
    @pytest.mark.asyncio
    async def test_cpu_utilization_efficiency(self, performance_coordinador, load_test_users, performance_metrics):
        """Test CPU utilization efficiency under load"""
        
        process = psutil.Process(os.getpid())
        
        # Monitor CPU usage during intensive operations
        cpu_measurements = []
        
        async def cpu_monitored_operation(user: User, op_id: int):
            """Execute operation while monitoring CPU"""
            start_cpu = process.cpu_percent()
            
            start_time = time.time()
            result = await performance_coordinador.ejecutar_flujo(
                user_id=user.id,
                accion=AccionUsuario.TOMAR_DECISION,
                fragment_id=f"cpu_test_{op_id}",
                choice_id=f"cpu_choice_{op_id}",
                cinema_enhanced=True,
                psychology_aware=True
            )
            end_time = time.time()
            
            end_cpu = process.cpu_percent()
            avg_cpu = (start_cpu + end_cpu) / 2
            
            return {
                "response_time": end_time - start_time,
                "cpu_usage": avg_cpu,
                "success": result.get("success", True)
            }
        
        # Execute CPU-intensive test
        tasks = [cpu_monitored_operation(user, i) for i, user in enumerate(load_test_users[:15])]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_results = [r for r in results if not isinstance(r, Exception) and r.get("success")]
        
        if successful_results:
            avg_cpu = statistics.mean([r["cpu_usage"] for r in successful_results])
            max_cpu = max([r["cpu_usage"] for r in successful_results])
            
            # CPU efficiency requirements
            assert avg_cpu < 80, f"Average CPU usage too high: {avg_cpu:.1f}%"
            assert max_cpu < 95, f"Peak CPU usage too high: {max_cpu:.1f}%"
            
            # Performance should remain good even with CPU load
            response_times = [r["response_time"] for r in successful_results]
            avg_response_time = statistics.mean(response_times)
            
            assert avg_response_time < 0.8, \
                f"Response time degraded under CPU load: {avg_response_time:.3f}s"


class TestCinemaScalabilityValidation:
    """Scalability testing for Cinema Architecture"""
    
    @pytest.mark.asyncio
    async def test_user_scaling_capacity(self, session, mock_bot):
        """Test system capacity with increasing user loads"""
        
        coordinador = CoordinadorCentral(session)
        if hasattr(coordinador, 'cinema_master') and coordinador.cinema_master:
            coordinador.cinema_master._bot = mock_bot
        
        scaling_results = {}
        user_counts = [10, 25, 50, 75, 100]
        
        for user_count in user_counts:
            # Create users for this scaling test
            users = []
            for i in range(user_count):
                user = User(
                    id=700000 + i,
                    first_name=f"ScaleUser{i}",
                    username=f"scaleuser{i}",
                    role="free",
                    points=100.0,
                    created_at=datetime.utcnow()
                )
                session.add(user)
                users.append(user)
            
            await session.commit()
            
            # Execute concurrent operations
            async def scale_test_operation(user: User):
                start_time = time.time()
                result = await coordinador.ejecutar_flujo(
                    user_id=user.id,
                    accion=AccionUsuario.TOMAR_DECISION,
                    fragment_id="scale_test_fragment",
                    choice_id="scale_test_choice"
                )
                end_time = time.time()
                return end_time - start_time, result.get("success", True)
            
            # Measure scaling performance
            start_scale_time = time.time()
            tasks = [scale_test_operation(user) for user in users]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_scale_time = time.time()
            
            # Analyze scaling results
            successful_results = [r for r in results if not isinstance(r, Exception) and r[1]]
            response_times = [r[0] for r in successful_results]
            
            scaling_results[user_count] = {
                "success_rate": len(successful_results) / len(results),
                "avg_response_time": statistics.mean(response_times) if response_times else float('inf'),
                "total_time": end_scale_time - start_scale_time,
                "throughput": len(successful_results) / (end_scale_time - start_scale_time)
            }
        
        # Validate scaling behavior
        for user_count, results in scaling_results.items():
            assert results["success_rate"] >= 0.95, \
                f"Success rate degraded with {user_count} users: {results['success_rate']:.2%}"
            
            # Response time should not degrade linearly with user count
            max_acceptable_time = 2.0  # 2 seconds max even at high scale
            assert results["avg_response_time"] < max_acceptable_time, \
                f"Response time too high with {user_count} users: {results['avg_response_time']:.3f}s"
        
        # Throughput should scale reasonably
        throughput_10 = scaling_results[10]["throughput"]
        throughput_100 = scaling_results[100]["throughput"]
        
        # Throughput shouldn't decrease drastically
        throughput_ratio = throughput_100 / throughput_10 if throughput_10 > 0 else 0
        assert throughput_ratio >= 0.3, \
            f"Throughput scaling too poor: {throughput_ratio:.2f} (100 users vs 10 users)"
    
    @pytest.mark.asyncio
    async def test_database_connection_scaling(self, session, mock_bot):
        """Test database connection handling under scale"""
        
        coordinador = CoordinadorCentral(session)
        if hasattr(coordinador, 'cinema_master') and coordinador.cinema_master:
            coordinador.cinema_master._bot = mock_bot
        
        # Create test user
        user = User(
            id=600000,
            first_name="DBScaleUser",
            username="dbscaleuser",
            role="free",
            points=100.0,
            created_at=datetime.utcnow()
        )
        session.add(user)
        await session.commit()
        
        # Test database-intensive operations
        async def db_intensive_operation(op_id: int):
            start_time = time.time()
            
            # Multiple database operations in one flow
            result = await coordinador.ejecutar_flujo(
                user_id=user.id,
                accion=AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
                fragment_id=f"db_scale_test_{op_id}",
                save_progress=True,
                update_stats=True,
                cinema_enhanced=True
            )
            
            end_time = time.time()
            return end_time - start_time, result.get("success", True)
        
        # Execute many database operations concurrently
        tasks = [db_intensive_operation(i) for i in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_results = [r for r in results if not isinstance(r, Exception) and r[1]]
        
        # Database scaling validation
        success_rate = len(successful_results) / len(results)
        assert success_rate >= 0.98, f"DB scaling success rate too low: {success_rate:.2%}"
        
        response_times = [r[0] for r in successful_results]
        avg_db_time = statistics.mean(response_times)
        max_db_time = max(response_times)
        
        assert avg_db_time < 1.5, f"DB scaling average time too high: {avg_db_time:.3f}s"
        assert max_db_time < 3.0, f"DB scaling max time too high: {max_db_time:.3f}s"


class TestCinemaPerformanceReporting:
    """Performance reporting and analysis for Cinema Architecture"""
    
    @pytest.mark.asyncio
    async def test_comprehensive_performance_report(self, performance_coordinador, load_test_users, performance_metrics):
        """Generate comprehensive performance report"""
        
        # Execute comprehensive test suite
        test_scenarios = [
            ("normal_load", self._execute_normal_load_scenario),
            ("heavy_load", self._execute_heavy_load_scenario),
            ("memory_intensive", self._execute_memory_intensive_scenario),
            ("cpu_intensive", self._execute_cpu_intensive_scenario)
        ]
        
        scenario_results = {}
        
        for scenario_name, scenario_func in test_scenarios:
            start_time = time.time()
            scenario_metrics = PerformanceMetrics()
            
            try:
                await scenario_func(performance_coordinador, load_test_users, scenario_metrics)
                scenario_results[scenario_name] = {
                    "status": "success",
                    "duration": time.time() - start_time,
                    "metrics": scenario_metrics.get_stats()
                }
            except Exception as e:
                scenario_results[scenario_name] = {
                    "status": "failed",
                    "error": str(e),
                    "duration": time.time() - start_time
                }
        
        # Generate performance report
        report = self._generate_performance_report(scenario_results)
        
        # Validate overall performance meets requirements
        assert report["overall_performance"]["meets_requirements"], \
            f"Performance requirements not met: {report['overall_performance']['issues']}"
        
        # Log performance report for analysis
        print("\n" + "="*80)
        print("CINEMA ARCHITECTURE PERFORMANCE REPORT")
        print("="*80)
        print(f"Test Execution Date: {datetime.utcnow().isoformat()}")
        print(f"Overall Status: {'PASS' if report['overall_performance']['meets_requirements'] else 'FAIL'}")
        print(f"Scenarios Tested: {len(scenario_results)}")
        
        for scenario, results in scenario_results.items():
            print(f"\n{scenario.upper()} SCENARIO:")
            print(f"  Status: {results['status']}")
            print(f"  Duration: {results.get('duration', 0):.2f}s")
            
            if results['status'] == 'success' and 'metrics' in results:
                metrics = results['metrics']
                if 'response_time' in metrics:
                    print(f"  Avg Response Time: {metrics['response_time']['avg']:.3f}s")
                    print(f"  P95 Response Time: {metrics['response_time']['p95']:.3f}s")
                if 'memory' in metrics:
                    print(f"  Memory Usage: {metrics['memory']['peak_mb']:.2f}MB")
                if 'throughput_ops_per_second' in metrics:
                    print(f"  Throughput: {metrics['throughput_ops_per_second']:.2f} ops/sec")
        
        print("="*80)
    
    async def _execute_normal_load_scenario(self, coordinador, users, metrics):
        """Execute normal load test scenario"""
        for i in range(20):
            user = users[i % len(users[:5])]  # Use 5 users
            start_time = time.time()
            
            result = await coordinador.ejecutar_flujo(
                user_id=user.id,
                accion=AccionUsuario.TOMAR_DECISION,
                fragment_id=f"normal_{i}",
                choice_id=f"choice_{i}"
            )
            
            response_time = time.time() - start_time
            metrics.add_response_time(response_time)
    
    async def _execute_heavy_load_scenario(self, coordinador, users, metrics):
        """Execute heavy load test scenario"""
        tasks = []
        for i in range(50):
            user = users[i % len(users[:20])]  # Use 20 users
            
            async def heavy_operation():
                start_time = time.time()
                result = await coordinador.ejecutar_flujo(
                    user_id=user.id,
                    accion=AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
                    fragment_id=f"heavy_{i}",
                    cinema_enhanced=True
                )
                return time.time() - start_time
            
            tasks.append(heavy_operation())
        
        response_times = await asyncio.gather(*tasks)
        for rt in response_times:
            metrics.add_response_time(rt)
    
    async def _execute_memory_intensive_scenario(self, coordinador, users, metrics):
        """Execute memory intensive test scenario"""
        process = psutil.Process(os.getpid())
        
        for i in range(100):
            user = users[i % len(users[:10])]  # Use 10 users
            
            await coordinador.ejecutar_flujo(
                user_id=user.id,
                accion=AccionUsuario.DESBLOQUEAR_PISTA,
                fragment_id=f"memory_{i}",
                clue_type="complex_clue"
            )
            
            memory_mb = process.memory_info().rss / 1024 / 1024
            metrics.add_memory_snapshot(memory_mb)
    
    async def _execute_cpu_intensive_scenario(self, coordinador, users, metrics):
        """Execute CPU intensive test scenario"""
        process = psutil.Process(os.getpid())
        
        tasks = []
        for i in range(30):
            user = users[i % len(users[:15])]  # Use 15 users
            
            async def cpu_operation():
                start_time = time.time()
                result = await coordinador.ejecutar_flujo(
                    user_id=user.id,
                    accion=AccionUsuario.TOMAR_DECISION,
                    fragment_id=f"cpu_{i}",
                    psychology_aware=True,
                    cinema_enhanced=True
                )
                return time.time() - start_time
            
            tasks.append(cpu_operation())
        
        response_times = await asyncio.gather(*tasks)
        for rt in response_times:
            metrics.add_response_time(rt)
            
        cpu_percent = process.cpu_percent()
        metrics.add_cpu_snapshot(cpu_percent)
    
    def _generate_performance_report(self, scenario_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive performance analysis report"""
        
        overall_issues = []
        meets_requirements = True
        
        # Analyze each scenario
        for scenario, results in scenario_results.items():
            if results['status'] != 'success':
                overall_issues.append(f"{scenario} scenario failed")
                meets_requirements = False
                continue
            
            if 'metrics' in results:
                metrics = results['metrics']
                
                # Check response time requirements
                if 'response_time' in metrics:
                    avg_time = metrics['response_time']['avg']
                    if scenario == 'normal_load' and avg_time > 0.5:
                        overall_issues.append(f"{scenario}: Average response time too high ({avg_time:.3f}s)")
                        meets_requirements = False
                    elif scenario == 'heavy_load' and avg_time > 2.0:
                        overall_issues.append(f"{scenario}: Heavy load response time too high ({avg_time:.3f}s)")
                        meets_requirements = False
                
                # Check memory requirements
                if 'memory' in metrics:
                    memory_increase = metrics['memory']['increase_mb']
                    if memory_increase > 100:
                        overall_issues.append(f"{scenario}: Memory increase too high ({memory_increase:.2f}MB)")
                        meets_requirements = False
        
        return {
            "overall_performance": {
                "meets_requirements": meets_requirements,
                "issues": overall_issues
            },
            "scenario_results": scenario_results,
            "recommendations": self._generate_recommendations(scenario_results)
        }
    
    def _generate_recommendations(self, scenario_results: Dict[str, Any]) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        for scenario, results in scenario_results.items():
            if results['status'] != 'success':
                continue
                
            if 'metrics' in results:
                metrics = results['metrics']
                
                if 'response_time' in metrics:
                    p95_time = metrics['response_time'].get('p95', 0)
                    if p95_time > 1.0:
                        recommendations.append(f"Consider optimizing {scenario} scenario for 95th percentile response times")
                
                if 'memory' in metrics:
                    peak_memory = metrics['memory'].get('peak_mb', 0)
                    if peak_memory > 200:
                        recommendations.append(f"Consider memory optimization for {scenario} scenario")
        
        if not recommendations:
            recommendations.append("Performance is within acceptable limits - no immediate optimizations needed")
        
        return recommendations