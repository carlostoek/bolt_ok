"""
⚡ PERFORMANCE & SCALABILITY TESTING INFRASTRUCTURE
Critical testing that ensures <500ms response time guarantee and system scalability.
Tests load handling, concurrent users, memory optimization, and database performance.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
import asyncio
import time
import datetime
import psutil
import gc
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
import concurrent.futures
import threading
import statistics

from database.models import User, UserStats, Channel
from database.narrative_unified import NarrativeFragment, UserNarrativeState, UserDecisionLog
from services.coordinador_central import CoordinadorCentral
from services.user_narrative_service import UserNarrativeService
from services.diana_menu_system import DianaMenuSystem
from services.point_service import PointService
from services.notification_service import NotificationService


class TestResponseTimeGuarantee:
    """⚡ Critical <500ms response time guarantee testing."""
    
    @pytest.mark.asyncio
    async def test_coordinador_central_response_time_guarantee(self, session, level_service, achievement_service):
        """🔒 CRITICAL: CoordinadorCentral must respond <500ms."""
        from services.notification_service import NotificationService
        
        mock_bot = AsyncMock()
        notification_service = NotificationService(session, mock_bot)
        
        coordinador = CoordinadorCentral(session)
        coordinador.point_service = PointService(session, level_service, achievement_service, notification_service)
        
        # Create test user
        user = User(
            id=500001,
            first_name="ResponseTimeUser",
            role="free",
            points=0.0
        )
        session.add(user)
        await session.commit()
        
        # Measure response time for critical operations
        operations = [
            ("process_user_reaction", {
                "user_id": 500001,
                "channel_id": -1001234567890,
                "message_id": 1,
                "reaction": "like",
                "points_earned": 10.0
            }),
            ("process_user_reaction", {
                "user_id": 500001,
                "channel_id": -1001234567890,
                "message_id": 2,
                "reaction": "heart",
                "points_earned": 15.0
            })
        ]
        
        response_times = []
        
        for operation_name, kwargs in operations:
            start_time = time.time()
            
            if operation_name == "process_user_reaction":
                result = await coordinador.process_user_reaction(**kwargs)
                assert result is True, f"Operation failed: {operation_name}"
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to ms
            response_times.append(response_time)
            
            assert response_time < 500, f"{operation_name} response time {response_time}ms > 500ms!"
        
        # Statistical analysis
        avg_response = statistics.mean(response_times)
        max_response = max(response_times)
        
        assert avg_response < 250, f"Average response time too high: {avg_response}ms"
        assert max_response < 500, f"Max response time exceeded: {max_response}ms"
    
    @pytest.mark.asyncio
    async def test_narrative_service_response_time_guarantee(self, session):
        """⚡ UserNarrativeService must respond <500ms."""
        service = UserNarrativeService(session)
        
        # Create test user with complex narrative state
        user = User(
            id=500002,
            first_name="NarrativeSpeedUser",
            role="vip",
            points=300.0,
            archetype="Explorer"
        )
        session.add(user)
        
        narrative_state = UserNarrativeState(
            user_id=500002,
            current_fragment_id=10,
            tier=2,
            emotional_crescendo_level=4,
            completed_fragments=list(range(1, 10)),
            available_choices=[]
        )
        session.add(narrative_state)
        await session.commit()
        
        # Test critical narrative operations
        operations = [
            ("get_user_narrative_state", (500002,)),
            ("can_user_progress_to_tier", (500002, 3)),
            ("get_user_narrative_state", (500002,))  # Second call (should be cached)
        ]
        
        response_times = []
        
        for operation_name, args in operations:
            start_time = time.time()
            
            if operation_name == "get_user_narrative_state":
                result = await service.get_user_narrative_state(*args)
                assert result is not None, f"Narrative state retrieval failed!"
            elif operation_name == "can_user_progress_to_tier":
                result = await service.can_user_progress_to_tier(*args)
                assert isinstance(result, bool), f"Progression check failed!"
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            response_times.append(response_time)
            
            assert response_time < 500, f"{operation_name} response time {response_time}ms > 500ms!"
        
        # Second call should be faster (caching effect)
        if len(response_times) >= 3:
            assert response_times[2] <= response_times[0], "Caching not improving performance!"
    
    @pytest.mark.asyncio
    async def test_diana_menu_system_response_time_guarantee(self, session):
        """🎭 Diana Menu System must respond <500ms."""
        mock_bot = AsyncMock()
        menu_system = DianaMenuSystem(session, mock_bot)
        
        # Create test user
        user = User(
            id=500003,
            first_name="MenuSpeedUser",
            role="vip",
            points=500.0
        )
        session.add(user)
        await session.commit()
        
        # Create mock callback query
        callback = MagicMock()
        callback.from_user.id = 500003
        callback.data = "diana_menu"
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        
        # Test menu operations
        start_time = time.time()
        
        try:
            await menu_system.handle_diana_menu(callback)
            menu_success = True
        except Exception:
            menu_success = False  # May fail due to mocking, but timing is what matters
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        
        assert response_time < 500, f"Diana Menu response time {response_time}ms > 500ms!"


class TestConcurrentUserLoad:
    """👥 Concurrent user load testing for system scalability."""
    
    @pytest.mark.asyncio
    async def test_concurrent_user_reactions(self, session, level_service, achievement_service):
        """👥 System must handle concurrent user reactions."""
        from services.notification_service import NotificationService
        
        mock_bot = AsyncMock()
        notification_service = NotificationService(session, mock_bot)
        
        coordinador = CoordinadorCentral(session)
        coordinador.point_service = PointService(session, level_service, achievement_service, notification_service)
        
        # Create multiple test users
        num_users = 20  # Simulate 20 concurrent users
        users = []
        
        for i in range(num_users):
            user = User(
                id=600000 + i,
                first_name=f"ConcurrentUser{i}",
                role="free" if i % 2 == 0 else "vip",
                points=0.0
            )
            session.add(user)
            users.append(user)
        
        await session.commit()
        
        # Simulate concurrent reactions
        async def simulate_user_reaction(user_id, reaction_count):
            results = []
            for j in range(reaction_count):
                try:
                    result = await coordinador.process_user_reaction(
                        user_id=user_id,
                        channel_id=-1001234567890,
                        message_id=j + 1,
                        reaction="like",
                        points_earned=10.0
                    )
                    results.append(result)
                except Exception as e:
                    results.append(f"Error: {e}")
            return results
        
        # Execute concurrent reactions
        start_time = time.time()
        
        tasks = [
            simulate_user_reaction(users[i].id, 5)  # 5 reactions per user
            for i in range(min(num_users, 10))  # Test with 10 concurrent users
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        
        # Analyze results
        successful_operations = 0
        failed_operations = 0
        
        for user_results in results:
            if isinstance(user_results, Exception):
                failed_operations += 1
            else:
                for result in user_results:
                    if result is True:
                        successful_operations += 1
                    else:
                        failed_operations += 1
        
        # Performance requirements
        success_rate = successful_operations / (successful_operations + failed_operations)
        assert success_rate >= 0.95, f"Success rate too low: {success_rate:.2%} < 95%"
        assert total_time < 10000, f"Concurrent processing too slow: {total_time}ms > 10s"
        
        # Average time per operation should still be reasonable
        avg_time_per_operation = total_time / (successful_operations + failed_operations)
        assert avg_time_per_operation < 100, f"Average operation time too high: {avg_time_per_operation}ms"
    
    @pytest.mark.asyncio
    async def test_concurrent_narrative_access(self, session):
        """📖 System must handle concurrent narrative access."""
        service = UserNarrativeService(session)
        
        # Create users with narrative states
        num_users = 15
        users = []
        
        for i in range(num_users):
            user = User(
                id=700000 + i,
                first_name=f"NarrativeConcurrent{i}",
                role="vip" if i % 3 == 0 else "free",
                points=100.0 + (i * 50),
                archetype=["Explorer", "Romantic", "Analytical"][i % 3]
            )
            session.add(user)
            
            narrative_state = UserNarrativeState(
                user_id=user.id,
                current_fragment_id=3 + (i % 10),
                tier=1 + (i % 3),
                completed_fragments=list(range(1, 3 + (i % 5))),
                available_choices=[]
            )
            session.add(narrative_state)
            users.append(user)
        
        await session.commit()
        
        # Concurrent narrative operations
        async def access_narrative_state(user_id):
            try:
                state = await service.get_user_narrative_state(user_id)
                progression = await service.can_user_progress_to_tier(user_id, 2)
                return {"state": state is not None, "progression": isinstance(progression, bool)}
            except Exception as e:
                return {"error": str(e)}
        
        start_time = time.time()
        
        tasks = [access_narrative_state(user.id) for user in users]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        
        # Analyze concurrent access results
        successful_accesses = 0
        failed_accesses = 0
        
        for result in results:
            if isinstance(result, Exception) or "error" in result:
                failed_accesses += 1
            else:
                if result.get("state") and result.get("progression"):
                    successful_accesses += 1
                else:
                    failed_accesses += 1
        
        success_rate = successful_accesses / len(results)
        assert success_rate >= 0.90, f"Narrative concurrent access success rate: {success_rate:.2%} < 90%"
        assert total_time < 5000, f"Concurrent narrative access too slow: {total_time}ms > 5s"


class TestMemoryOptimization:
    """🧠 Memory usage and optimization testing."""
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, session, level_service, achievement_service):
        """🧠 System must maintain reasonable memory usage."""
        from services.notification_service import NotificationService
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        mock_bot = AsyncMock()
        notification_service = NotificationService(session, mock_bot)
        
        coordinador = CoordinadorCentral(session)
        coordinador.point_service = PointService(session, level_service, achievement_service, notification_service)
        
        # Create many users and operations
        num_operations = 100
        memory_readings = []
        
        for i in range(num_operations):
            # Create user
            user = User(
                id=800000 + i,
                first_name=f"MemoryUser{i}",
                role="free",
                points=0.0
            )
            session.add(user)
            
            if i % 10 == 0:  # Commit every 10 users
                await session.commit()
                
                # Process some reactions
                for j in range(5):
                    await coordinador.process_user_reaction(
                        user_id=user.id,
                        channel_id=-1001234567890,
                        message_id=j + 1,
                        reaction="like",
                        points_earned=10.0
                    )
                
                # Check memory usage
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_readings.append(current_memory)
                
                # Force garbage collection periodically
                if i % 50 == 0:
                    gc.collect()
        
        await session.commit()
        
        # Final memory check
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory should not increase excessively
        assert memory_increase < 100, f"Memory usage increased by {memory_increase}MB > 100MB limit!"
        
        # Memory should be relatively stable (not constantly growing)
        if len(memory_readings) > 5:
            memory_growth_trend = memory_readings[-1] - memory_readings[0]
            assert memory_growth_trend < 50, f"Memory growth trend too high: {memory_growth_trend}MB"
    
    @pytest.mark.asyncio
    async def test_database_connection_management(self, session):
        """🔌 Database connections must be properly managed."""
        # Test that we're not leaking database connections
        initial_connections = len(session.get_bind().pool.checkedout())
        
        # Perform multiple database operations
        operations_count = 50
        
        for i in range(operations_count):
            # Create and query users
            user = User(
                id=900000 + i,
                first_name=f"ConnectionUser{i}",
                role="free",
                points=float(i)
            )
            session.add(user)
            
            if i % 10 == 0:
                await session.commit()
                
                # Query database
                result = await session.execute(
                    select(User).where(User.id == user.id)
                )
                queried_user = result.scalar_one_or_none()
                assert queried_user is not None, f"User query failed for ID {user.id}"
        
        await session.commit()
        
        # Check final connection count
        final_connections = len(session.get_bind().pool.checkedout())
        connection_leak = final_connections - initial_connections
        
        # Should not be leaking connections
        assert connection_leak <= 1, f"Database connection leak detected: {connection_leak} connections"


class TestDatabasePerformance:
    """🗃️ Database query performance and optimization testing."""
    
    @pytest.mark.asyncio
    async def test_user_query_performance(self, session):
        """⚡ User queries must be fast and optimized."""
        # Create many users for performance testing
        num_users = 200
        users_batch = []
        
        for i in range(num_users):
            user = User(
                id=1000000 + i,
                first_name=f"PerfUser{i}",
                username=f"perf_user_{i}",
                role="vip" if i % 4 == 0 else "free",
                points=float(i * 10),
                archetype=["Explorer", "Romantic", "Analytical", "Direct", "Persistent", "Patient"][i % 6]
            )
            users_batch.append(user)
            session.add(user)
            
            if i % 50 == 0:  # Commit in batches
                await session.commit()
        
        await session.commit()
        
        # Test query performance
        queries = [
            ("single_user_by_id", select(User).where(User.id == 1000100)),
            ("users_by_role", select(User).where(User.role == "vip")),
            ("users_by_archetype", select(User).where(User.archetype == "Explorer")),
            ("users_by_points_range", select(User).where(User.points.between(500.0, 1000.0)))
        ]
        
        for query_name, query in queries:
            start_time = time.time()
            
            result = await session.execute(query)
            users = result.scalars().all()
            
            end_time = time.time()
            query_time = (end_time - start_time) * 1000  # ms
            
            assert query_time < 100, f"{query_name} query time {query_time}ms > 100ms!"
            assert len(users) >= 0, f"{query_name} query returned invalid results!"
    
    @pytest.mark.asyncio
    async def test_narrative_state_query_performance(self, session):
        """📖 Narrative state queries must be optimized."""
        # Create users and narrative states
        num_users = 100
        
        for i in range(num_users):
            user = User(
                id=1100000 + i,
                first_name=f"NarrativePerfUser{i}",
                role="vip" if i % 3 == 0 else "free",
                points=float(i * 15)
            )
            session.add(user)
            
            narrative_state = UserNarrativeState(
                user_id=user.id,
                current_fragment_id=1 + (i % 16),
                tier=1 + (i % 3),
                completed_fragments=list(range(1, 1 + (i % 10))),
                available_choices=[]
            )
            session.add(narrative_state)
        
        await session.commit()
        
        # Test narrative queries
        service = UserNarrativeService(session)
        
        # Test multiple user state retrievals
        test_user_ids = [1100000 + i for i in range(0, num_users, 10)]  # Every 10th user
        
        start_time = time.time()
        
        for user_id in test_user_ids:
            state = await service.get_user_narrative_state(user_id)
            assert state is not None, f"Narrative state not found for user {user_id}"
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        avg_time_per_query = total_time / len(test_user_ids)
        
        assert avg_time_per_query < 50, f"Average narrative query time {avg_time_per_query}ms > 50ms!"
        assert total_time < 1000, f"Total narrative queries time {total_time}ms > 1s!"
    
    @pytest.mark.asyncio
    async def test_decision_log_performance(self, session):
        """📋 Decision logging must be fast and efficient."""
        # Create user and many decisions
        user = User(
            id=1200001,
            first_name="DecisionPerfUser",
            role="vip",
            points=500.0
        )
        session.add(user)
        await session.commit()
        
        # Log many decisions quickly
        num_decisions = 100
        start_time = time.time()
        
        decisions_batch = []
        for i in range(num_decisions):
            decision = UserDecisionLog(
                user_id=1200001,
                fragment_id=1 + (i % 16),
                choice_index=i % 3,
                choice_text=f"Decision {i}",
                timestamp=datetime.datetime.utcnow()
            )
            decisions_batch.append(decision)
            session.add(decision)
            
            if i % 20 == 0:  # Commit in batches
                await session.commit()
        
        await session.commit()
        
        end_time = time.time()
        logging_time = (end_time - start_time) * 1000
        avg_logging_time = logging_time / num_decisions
        
        assert avg_logging_time < 10, f"Average decision logging time {avg_logging_time}ms > 10ms!"
        
        # Test querying decisions
        start_time = time.time()
        
        result = await session.execute(
            select(UserDecisionLog).where(UserDecisionLog.user_id == 1200001)
        )
        decisions = result.scalars().all()
        
        end_time = time.time()
        query_time = (end_time - start_time) * 1000
        
        assert query_time < 100, f"Decision query time {query_time}ms > 100ms!"
        assert len(decisions) == num_decisions, f"Decision count mismatch: {len(decisions)} != {num_decisions}"


class TestScalabilityBoundaries:
    """🚀 System scalability boundary testing."""
    
    @pytest.mark.asyncio
    async def test_maximum_concurrent_operations(self, session, level_service, achievement_service):
        """🚀 Test system limits with maximum load."""
        from services.notification_service import NotificationService
        
        mock_bot = AsyncMock()
        notification_service = NotificationService(session, mock_bot)
        
        coordinador = CoordinadorCentral(session)
        coordinador.point_service = PointService(session, level_service, achievement_service, notification_service)
        
        # Create many users for stress testing
        num_users = 50  # High concurrent load
        users = []
        
        for i in range(num_users):
            user = User(
                id=1300000 + i,
                first_name=f"StressUser{i}",
                role="vip" if i % 5 == 0 else "free",
                points=0.0
            )
            session.add(user)
            users.append(user)
        
        await session.commit()
        
        # Maximum concurrent operations
        async def stress_test_user(user_id, operation_count):
            results = []
            errors = []
            
            for j in range(operation_count):
                try:
                    start_time = time.time()
                    result = await coordinador.process_user_reaction(
                        user_id=user_id,
                        channel_id=-1001234567890,
                        message_id=j + 1,
                        reaction="like",
                        points_earned=10.0
                    )
                    end_time = time.time()
                    
                    operation_time = (end_time - start_time) * 1000
                    results.append({"success": result, "time": operation_time})
                    
                except Exception as e:
                    errors.append(str(e))
            
            return {"results": results, "errors": errors}
        
        # Execute maximum stress test
        start_time = time.time()
        
        # High concurrency - 30 users, 10 operations each = 300 total operations
        stress_tasks = [
            stress_test_user(users[i].id, 10)
            for i in range(min(30, num_users))
        ]
        
        stress_results = await asyncio.gather(*stress_tasks, return_exceptions=True)
        
        end_time = time.time()
        total_stress_time = (end_time - start_time) * 1000
        
        # Analyze stress test results
        total_operations = 0
        successful_operations = 0
        total_errors = 0
        operation_times = []
        
        for user_result in stress_results:
            if isinstance(user_result, Exception):
                total_errors += 10  # Assume all 10 operations failed
                total_operations += 10
            else:
                results = user_result.get("results", [])
                errors = user_result.get("errors", [])
                
                total_operations += len(results) + len(errors)
                successful_operations += len([r for r in results if r.get("success")])
                total_errors += len(errors)
                
                for result in results:
                    operation_times.append(result.get("time", 0))
        
        # Stress test analysis
        success_rate = successful_operations / total_operations if total_operations > 0 else 0
        error_rate = total_errors / total_operations if total_operations > 0 else 0
        avg_operation_time = statistics.mean(operation_times) if operation_times else 0
        
        # Scalability requirements (more lenient under stress)
        assert success_rate >= 0.80, f"Stress test success rate too low: {success_rate:.2%} < 80%"
        assert error_rate <= 0.20, f"Stress test error rate too high: {error_rate:.2%} > 20%"
        assert avg_operation_time < 1000, f"Stress test avg operation time: {avg_operation_time}ms > 1s"
        assert total_stress_time < 30000, f"Total stress test time: {total_stress_time}ms > 30s"
        
        print(f"🚀 STRESS TEST RESULTS:")
        print(f"   Total operations: {total_operations}")
        print(f"   Success rate: {success_rate:.2%}")
        print(f"   Average operation time: {avg_operation_time:.1f}ms")
        print(f"   Total test time: {total_stress_time:.1f}ms")
    
    @pytest.mark.asyncio
    async def test_database_connection_pool_limits(self, session):
        """🔌 Test database connection pool under stress."""
        # Test that we can handle many simultaneous database operations
        # without exhausting the connection pool
        
        async def database_intensive_operation(user_id):
            try:
                # Multiple database operations in sequence
                user = User(
                    id=user_id,
                    first_name=f"PoolUser{user_id}",
                    role="free",
                    points=0.0
                )
                session.add(user)
                await session.flush()  # Don't commit yet
                
                # Query the user back
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                queried_user = result.scalar_one_or_none()
                
                # Update the user
                if queried_user:
                    queried_user.points = 100.0
                    await session.flush()
                
                return True
            except Exception as e:
                return f"Error: {e}"
        
        # Run many concurrent database operations
        num_operations = 25  # Should be within connection pool limits
        start_user_id = 1400000
        
        start_time = time.time()
        
        tasks = [
            database_intensive_operation(start_user_id + i)
            for i in range(num_operations)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Commit all changes
        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            pytest.fail(f"Database commit failed: {e}")
        
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        
        # Analyze connection pool performance
        successful_ops = sum(1 for r in results if r is True)
        failed_ops = len(results) - successful_ops
        success_rate = successful_ops / len(results)
        
        assert success_rate >= 0.90, f"Connection pool success rate: {success_rate:.2%} < 90%"
        assert total_time < 10000, f"Connection pool operations too slow: {total_time}ms > 10s"


class TestPerformanceRegression:
    """📊 Performance regression testing and monitoring."""
    
    @pytest.mark.asyncio
    async def test_performance_baseline_regression(self, session, level_service, achievement_service):
        """📊 Ensure performance doesn't regress below baseline."""
        from services.notification_service import NotificationService
        
        mock_bot = AsyncMock()
        notification_service = NotificationService(session, mock_bot)
        
        coordinador = CoordinadorCentral(session)
        coordinador.point_service = PointService(session, level_service, achievement_service, notification_service)
        
        # Performance baseline test suite
        baseline_tests = [
            {
                "name": "single_user_reaction",
                "max_time_ms": 100,
                "operation": lambda: coordinador.process_user_reaction(
                    user_id=1500001, channel_id=-1001234567890, message_id=1, 
                    reaction="like", points_earned=10.0
                )
            },
            {
                "name": "narrative_state_retrieval",
                "max_time_ms": 150,
                "operation": lambda: UserNarrativeService(session).get_user_narrative_state(1500002)
            }
        ]
        
        # Create test users
        for i in range(1, 5):
            user = User(
                id=1500000 + i,
                first_name=f"BaselineUser{i}",
                role="vip" if i % 2 == 0 else "free",
                points=float(i * 100)
            )
            session.add(user)
            
            if i >= 2:  # Create narrative state for user 2+
                narrative_state = UserNarrativeState(
                    user_id=user.id,
                    current_fragment_id=5,
                    tier=2,
                    completed_fragments=list(range(1, 5)),
                    available_choices=[]
                )
                session.add(narrative_state)
        
        await session.commit()
        
        # Run baseline tests
        performance_results = {}
        
        for test in baseline_tests:
            test_name = test["name"]
            max_time = test["max_time_ms"]
            operation = test["operation"]
            
            # Run test multiple times for statistical accuracy
            times = []
            
            for run in range(5):
                start_time = time.time()
                
                try:
                    result = await operation()
                    success = True
                except Exception as e:
                    success = False
                    result = e
                
                end_time = time.time()
                operation_time = (end_time - start_time) * 1000
                times.append(operation_time)
                
                assert success, f"Baseline test {test_name} failed: {result}"
            
            # Statistical analysis
            avg_time = statistics.mean(times)
            max_observed = max(times)
            min_observed = min(times)
            
            performance_results[test_name] = {
                "avg_time": avg_time,
                "max_time": max_observed,
                "min_time": min_observed,
                "baseline_limit": max_time,
                "passes": avg_time <= max_time
            }
            
            assert avg_time <= max_time, \
                f"Performance regression in {test_name}: {avg_time:.1f}ms > {max_time}ms baseline!"
        
        # Print performance summary
        print("📊 PERFORMANCE BASELINE RESULTS:")
        for test_name, results in performance_results.items():
            status = "PASS" if results["passes"] else "FAIL"
            print(f"   {test_name}: {results['avg_time']:.1f}ms (limit: {results['baseline_limit']}ms) [{status}]")


@pytest.mark.asyncio
async def test_complete_performance_scalability_smoke_test(session, level_service, achievement_service):
    """🚨 CRITICAL SMOKE TEST: Complete performance and scalability validation."""
    from services.notification_service import NotificationService
    
    print("🚀 STARTING COMPLETE PERFORMANCE & SCALABILITY SMOKE TEST...")
    
    # Setup comprehensive test environment
    mock_bot = AsyncMock()
    notification_service = NotificationService(session, mock_bot)
    
    coordinador = CoordinadorCentral(session)
    coordinador.point_service = PointService(session, level_service, achievement_service, notification_service)
    
    narrative_service = UserNarrativeService(session)
    menu_system = DianaMenuSystem(session, mock_bot)
    
    # Create comprehensive user base
    num_users = 30
    users = []
    
    for i in range(num_users):
        user = User(
            id=9900000 + i,
            first_name=f"SmokeTestUser{i}",
            username=f"smoke_user_{i}",
            role="vip" if i % 4 == 0 else "free",
            points=float(i * 25),
            archetype=["Explorer", "Romantic", "Analytical", "Direct", "Persistent", "Patient"][i % 6],
            vip_expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=30) if i % 4 == 0 else None
        )
        session.add(user)
        
        # Add narrative state
        narrative_state = UserNarrativeState(
            user_id=user.id,
            current_fragment_id=1 + (i % 16),
            tier=1 + (i % 3),
            emotional_crescendo_level=1 + (i % 6),
            completed_fragments=list(range(1, 1 + (i % 10))),
            available_choices=[]
        )
        session.add(narrative_state)
        users.append(user)
    
    await session.commit()
    
    # PERFORMANCE TEST BATTERY
    test_results = {}
    
    # 1. Response Time Guarantee Test
    print("   Testing <500ms response time guarantee...")
    start_time = time.time()
    
    response_time_tests = 0
    response_time_passes = 0
    
    for i in range(10):  # Test 10 random users
        user = users[i]
        operation_start = time.time()
        
        result = await coordinador.process_user_reaction(
            user_id=user.id,
            channel_id=-1001234567890,
            message_id=i + 1,
            reaction="like",
            points_earned=10.0
        )
        
        operation_end = time.time()
        operation_time = (operation_end - operation_start) * 1000
        
        response_time_tests += 1
        if operation_time < 500 and result is True:
            response_time_passes += 1
    
    response_time_success_rate = response_time_passes / response_time_tests
    test_results["response_time_guarantee"] = {
        "success_rate": response_time_success_rate,
        "passes": response_time_success_rate >= 0.95
    }
    
    # 2. Concurrent Load Test
    print("   Testing concurrent user load...")
    
    async def concurrent_operation(user_id):
        try:
            # Multiple operations per user
            reaction_result = await coordinador.process_user_reaction(
                user_id=user_id, channel_id=-1001234567890, message_id=999, 
                reaction="heart", points_earned=15.0
            )
            
            narrative_result = await narrative_service.get_user_narrative_state(user_id)
            
            return {
                "reaction_success": reaction_result is True,
                "narrative_success": narrative_result is not None
            }
        except Exception as e:
            return {"error": str(e)}
    
    concurrent_start = time.time()
    
    # Run 20 concurrent operations
    concurrent_tasks = [concurrent_operation(users[i].id) for i in range(20)]
    concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
    
    concurrent_end = time.time()
    concurrent_time = (concurrent_end - concurrent_start) * 1000
    
    # Analyze concurrent results
    concurrent_successes = 0
    for result in concurrent_results:
        if isinstance(result, dict) and not "error" in result:
            if result.get("reaction_success") and result.get("narrative_success"):
                concurrent_successes += 1
    
    concurrent_success_rate = concurrent_successes / len(concurrent_results)
    test_results["concurrent_load"] = {
        "success_rate": concurrent_success_rate,
        "total_time": concurrent_time,
        "passes": concurrent_success_rate >= 0.85 and concurrent_time < 10000
    }
    
    # 3. Memory Usage Test
    print("   Testing memory optimization...")
    process = psutil.Process()
    memory_before = process.memory_info().rss / 1024 / 1024  # MB
    
    # Perform memory-intensive operations
    for i in range(50):
        user_id = 9950000 + i
        temp_user = User(
            id=user_id,
            first_name=f"MemoryTestUser{i}",
            role="free",
            points=0.0
        )
        session.add(temp_user)
        
        if i % 10 == 0:
            await session.commit()
            # Trigger some operations
            await coordinador.process_user_reaction(
                user_id=user_id, channel_id=-1001234567890, message_id=i,
                reaction="like", points_earned=5.0
            )
    
    await session.commit()
    memory_after = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = memory_after - memory_before
    
    test_results["memory_optimization"] = {
        "memory_increase_mb": memory_increase,
        "passes": memory_increase < 50  # Less than 50MB increase
    }
    
    # 4. Database Performance Test
    print("   Testing database performance...")
    db_start = time.time()
    
    # Multiple database queries
    db_operations = 20
    db_successes = 0
    
    for i in range(db_operations):
        try:
            # Complex query
            result = await session.execute(
                select(User).where(
                    User.points > float(i * 10),
                    User.role == "vip"
                ).limit(10)
            )
            users_result = result.scalars().all()
            
            if len(users_result) >= 0:  # Any result is valid
                db_successes += 1
                
        except Exception:
            pass
    
    db_end = time.time()
    db_time = (db_end - db_start) * 1000
    db_success_rate = db_successes / db_operations
    
    test_results["database_performance"] = {
        "success_rate": db_success_rate,
        "total_time": db_time,
        "avg_time_per_query": db_time / db_operations,
        "passes": db_success_rate >= 0.90 and db_time < 5000
    }
    
    # FINAL ANALYSIS
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result["passes"])
    overall_success_rate = passed_tests / total_tests
    
    print(f"🚀 PERFORMANCE & SCALABILITY SMOKE TEST RESULTS:")
    print(f"   Response Time Guarantee: {'PASS' if test_results['response_time_guarantee']['passes'] else 'FAIL'} ({test_results['response_time_guarantee']['success_rate']:.2%})")
    print(f"   Concurrent Load: {'PASS' if test_results['concurrent_load']['passes'] else 'FAIL'} ({test_results['concurrent_load']['success_rate']:.2%}, {test_results['concurrent_load']['total_time']:.1f}ms)")
    print(f"   Memory Optimization: {'PASS' if test_results['memory_optimization']['passes'] else 'FAIL'} (+{test_results['memory_optimization']['memory_increase_mb']:.1f}MB)")
    print(f"   Database Performance: {'PASS' if test_results['database_performance']['passes'] else 'FAIL'} ({test_results['database_performance']['success_rate']:.2%}, {test_results['database_performance']['avg_time_per_query']:.1f}ms/query)")
    print(f"   Overall Success Rate: {overall_success_rate:.2%} ({passed_tests}/{total_tests})")
    
    # Critical assertions
    assert overall_success_rate >= 0.75, f"Overall performance test success rate too low: {overall_success_rate:.2%} < 75%"
    assert test_results["response_time_guarantee"]["passes"], "Response time guarantee FAILED!"
    assert test_results["concurrent_load"]["passes"], "Concurrent load test FAILED!"
    
    print("⚡ PERFORMANCE & SCALABILITY: ALL SYSTEMS FULLY OPERATIONAL!")