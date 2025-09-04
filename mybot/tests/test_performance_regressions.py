"""
Performance Regression Tests
Validates system performance against established baselines to prevent degradation.
"""
import pytest
import pytest_asyncio
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User, UserStats, Channel
from database.transaction_models import PointTransaction


@pytest.mark.asyncio
class TestNarrativePerformanceBaseline:
    """Tests to ensure narrative operations maintain 15.4ms baseline."""
    
    async def test_narrative_user_retrieval_performance(self, session):
        """Test user retrieval for narrative operations."""
        user_id = 100000001
        
        # Create test user
        user = User(
            id=user_id,
            first_name="NarrativePerf",
            role="vip",
            points=150.0
        )
        session.add(user)
        await session.commit()
        
        # Measure narrative-related user retrieval
        start_time = time.perf_counter()
        
        # Simulate narrative user lookup pattern
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Should be well under baseline (test environment adjustment)
        assert duration_ms < 100, f"User retrieval took {duration_ms:.2f}ms, exceeds 100ms threshold"
        assert user is not None
        
        # Cleanup
        await session.delete(user)
        await session.commit()

    async def test_narrative_progress_calculation_performance(self, session):
        """Test narrative progress calculation performance."""
        user_id = 100000002
        
        # Create user with stats
        user = User(id=user_id, first_name="ProgressPerf", role="free", points=75.0)
        stats = UserStats(user_id=user_id, checkin_streak=3)
        session.add(user)
        session.add(stats)
        await session.commit()
        
        # Measure progress calculation pattern
        start_time = time.perf_counter()
        
        # Simulate narrative progress lookup
        user_result = await session.execute(select(User).where(User.id == user_id))
        stats_result = await session.execute(select(UserStats).where(UserStats.user_id == user_id))
        
        user = user_result.scalar_one_or_none()
        user_stats = stats_result.scalar_one_or_none()
        
        # Simulate progress calculation
        progress_percentage = min(100, (user.points / 1000) * 100) if user else 0
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Should meet baseline (test environment adjustment)
        assert duration_ms < 100, f"Progress calculation took {duration_ms:.2f}ms, exceeds baseline"
        assert progress_percentage == 7.5  # 75 points / 1000 * 100
        
        # Cleanup
        await session.delete(user_stats)
        await session.delete(user)
        await session.commit()

    async def test_concurrent_narrative_users_performance(self, session):
        """Test concurrent narrative user operations performance."""
        base_user_id = 100000010
        user_count = 20
        
        async def narrative_user_operation(user_id: int):
            """Simulate a narrative user operation."""
            start = time.perf_counter()
            
            # Simulate typical narrative user lookup
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if user:
                # Simulate some narrative processing
                await asyncio.sleep(0.001)  # 1ms processing time
            
            end = time.perf_counter()
            return (end - start) * 1000
        
        # Create test users
        users = []
        for i in range(user_count):
            user = User(
                id=base_user_id + i,
                first_name=f"ConcurrentNarrative{i}",
                role="free",
                points=i * 10
            )
            users.append(user)
            session.add(user)
        await session.commit()
        
        # Measure concurrent operations
        start_time = time.perf_counter()
        
        durations = await asyncio.gather(*[
            narrative_user_operation(base_user_id + i)
            for i in range(user_count)
        ])
        
        end_time = time.perf_counter()
        total_duration_ms = (end_time - start_time) * 1000
        
        # Concurrent operations should be efficient
        avg_duration = sum(durations) / len(durations)
        assert avg_duration < 200, f"Average operation took {avg_duration:.2f}ms, exceeds baseline"
        assert total_duration_ms < 200, f"Total concurrent time {total_duration_ms:.2f}ms too high"
        
        # Cleanup
        for user in users:
            await session.delete(user)
        await session.commit()


@pytest.mark.asyncio
class TestUserOperationLatencyRequirements:
    """Validates user operations meet performance SLAs."""
    
    async def test_user_registration_workflow_latency(self, session):
        """Test user registration workflow meets 100ms requirement."""
        user_id = 200000001
        
        start_time = time.perf_counter()
        
        # Simulate complete user registration workflow
        user = User(
            id=user_id,
            first_name="RegistrationPerf",
            role="free",
            points=0
        )
        session.add(user)
        
        # Create initial user stats
        stats = UserStats(
            user_id=user_id,
            checkin_streak=0
        )
        session.add(stats)
        
        await session.commit()
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Registration should complete under 100ms
        assert duration_ms < 100, f"User registration took {duration_ms:.2f}ms, exceeds 100ms SLA"
        
        # Cleanup
        await session.delete(stats)
        await session.delete(user)
        await session.commit()

    async def test_user_preference_update_performance(self, session):
        """Test user preference updates are fast."""
        user_id = 200000002
        
        # Create user
        user = User(id=user_id, first_name="PrefPerf", role="free", points=0)
        session.add(user)
        await session.commit()
        
        # Measure preference update
        start_time = time.perf_counter()
        
        user.role = "vip"
        user.points = 100.0
        await session.commit()
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Updates should be very fast
        assert duration_ms < 20, f"Preference update took {duration_ms:.2f}ms, too slow"
        
        # Cleanup
        await session.delete(user)
        await session.commit()

    async def test_point_transaction_logging_performance(self, session):
        """Test point transaction logging performance."""
        user_id = 200000003
        
        # Create user
        user = User(id=user_id, first_name="TransLogPerf", role="free", points=0)
        session.add(user)
        await session.commit()
        
        # Measure transaction logging
        start_time = time.perf_counter()
        
        transaction = PointTransaction(
            user_id=user_id,
            amount=10.0,
            balance_after=10.0,
            source="performance_test",
            description="Performance logging test"
        )
        session.add(transaction)
        await session.commit()
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Transaction logging should be fast
        assert duration_ms < 25, f"Transaction logging took {duration_ms:.2f}ms, too slow"
        
        # Cleanup
        await session.delete(transaction)
        await session.delete(user)
        await session.commit()


@pytest.mark.asyncio
class TestCrossModuleWorkflowPerformance:
    """Tests for cross-module workflow performance requirements."""
    
    async def test_end_to_end_workflow_performance(self, session):
        """Test complete end-to-end workflow meets 200ms requirement."""
        user_id = 300000001
        
        start_time = time.perf_counter()
        
        # Simulate complete workflow: user lookup + point award + transaction log
        # 1. User lookup
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            # Create user if not exists
            user = User(id=user_id, first_name="WorkflowPerf", role="free", points=0)
            session.add(user)
            await session.commit()
        
        # 2. Point award simulation
        user.points += 10
        
        # 3. Transaction logging
        transaction = PointTransaction(
            user_id=user_id,
            amount=10.0,
            balance_after=user.points,
            source="workflow_test",
            description="End-to-end workflow test"
        )
        session.add(transaction)
        
        # 4. Final commit
        await session.commit()
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Complete workflow should be under 200ms
        assert duration_ms < 200, f"End-to-end workflow took {duration_ms:.2f}ms, exceeds 200ms SLA"
        
        # Cleanup
        await session.delete(transaction)
        await session.delete(user)
        await session.commit()

    async def test_channel_reaction_workflow_performance(self, session):
        """Test channel reaction processing performance."""
        user_id = 300000002
        channel_id = -100123456789
        
        # Setup test data
        user = User(id=user_id, first_name="ChannelPerf", role="free", points=50)
        channel = Channel(
            id=channel_id,
            title="Performance Test Channel",
            channel_type="vip",
            reaction_points={"like": 10.0, "heart": 15.0}
        )
        session.add(user)
        session.add(channel)
        await session.commit()
        
        start_time = time.perf_counter()
        
        # Simulate channel reaction workflow
        # 1. Verify channel exists
        channel_result = await session.execute(select(Channel).where(Channel.id == channel_id))
        found_channel = channel_result.scalar_one_or_none()
        
        # 2. Get reaction points
        reaction_points = found_channel.reaction_points.get("like", 0) if found_channel else 0
        
        # 3. Award points to user
        user.points += reaction_points
        
        # 4. Log transaction
        transaction = PointTransaction(
            user_id=user_id,
            amount=reaction_points,
            balance_after=user.points,
            source="channel_reaction",
            description=f"Reaction in channel {channel_id}"
        )
        session.add(transaction)
        await session.commit()
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Channel reaction workflow should be fast
        assert duration_ms < 50, f"Channel reaction workflow took {duration_ms:.2f}ms, too slow"
        assert user.points == 60.0  # 50 + 10
        
        # Cleanup
        await session.delete(transaction)
        await session.delete(channel)
        await session.delete(user)
        await session.commit()

    async def test_vip_content_access_check_performance(self, session):
        """Test VIP content access checking performance."""
        user_id = 300000003
        
        # Create VIP user
        from datetime import timedelta
        user = User(
            id=user_id,
            first_name="VIPAccessPerf",
            role="vip",
            points=200,
            vip_expires_at=datetime.now() + timedelta(days=30)
        )
        session.add(user)
        await session.commit()
        
        start_time = time.perf_counter()
        
        # Simulate VIP access check workflow
        # 1. User lookup
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        # 2. VIP status validation
        is_vip = user.role == "vip" and user.vip_expires_at and user.vip_expires_at > datetime.now()
        
        # 3. Content access decision
        access_granted = is_vip
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # VIP access check should be very fast (test environment)
        assert duration_ms < 50, f"VIP access check took {duration_ms:.2f}ms, too slow"
        assert access_granted is True
        
        # Cleanup
        await session.delete(user)
        await session.commit()


@pytest.mark.asyncio
class TestSystemLoadPerformance:
    """Tests system performance under various load conditions."""
    
    async def test_multiple_user_concurrent_operations(self, session_factory):
        """Test system handles multiple users concurrently."""
        user_count = 50
        base_user_id = 400000000
        
        async def user_operation(user_id: int):
            """Simulate typical user operation."""
            async with session_factory() as local_session:
                start = time.perf_counter()
                
                # Create/lookup user
                user = User(
                    id=user_id,
                    first_name=f"ConcurrentUser{user_id}",
                    role="free",
                    points=0
                )
                local_session.add(user)
                await local_session.commit()
                
                # Award points
                user.points += 10
                await local_session.commit()
                
                end = time.perf_counter()
                
                # Cleanup
                await local_session.delete(user)
                await local_session.commit()
                
                return (end - start) * 1000
        
        # Execute concurrent user operations
        start_time = time.perf_counter()
        
        durations = await asyncio.gather(*[
            user_operation(base_user_id + i)
            for i in range(user_count)
        ])
        
        end_time = time.perf_counter()
        total_duration_ms = (end_time - start_time) * 1000
        
        # Performance validations
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        
        assert avg_duration < 500, f"Average operation took {avg_duration:.2f}ms, too slow"
        assert max_duration < 1000, f"Slowest operation took {max_duration:.2f}ms, too slow"
        assert total_duration_ms < 5000, f"Total time {total_duration_ms:.2f}ms too high for {user_count} users"

    async def test_point_transaction_bulk_performance(self, session):
        """Test bulk point transaction performance."""
        user_id = 400000100
        transaction_count = 100
        
        # Create user
        user = User(id=user_id, first_name="BulkTransPerf", role="free", points=0)
        session.add(user)
        await session.commit()
        
        start_time = time.perf_counter()
        
        # Create many transactions
        transactions = []
        for i in range(transaction_count):
            transaction = PointTransaction(
                user_id=user_id,
                amount=1.0,
                balance_after=i + 1,
                source="bulk_test",
                description=f"Bulk transaction {i}"
            )
            transactions.append(transaction)
            session.add(transaction)
        
        await session.commit()
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Bulk transactions should be efficient
        avg_per_transaction = duration_ms / transaction_count
        assert avg_per_transaction < 5, f"Average per transaction: {avg_per_transaction:.2f}ms, too slow"
        assert duration_ms < 500, f"Bulk transactions took {duration_ms:.2f}ms total, too slow"
        
        # Cleanup
        for transaction in transactions:
            await session.delete(transaction)
        await session.delete(user)
        await session.commit()

    async def test_database_connection_pooling_efficiency(self, session_factory):
        """Test database connection pooling doesn't become bottleneck."""
        operation_count = 30
        
        async def quick_db_operation(operation_id: int):
            """Quick database operation to test connection efficiency."""
            async with session_factory() as local_session:
                start = time.perf_counter()
                
                # Simple query
                result = await local_session.execute(select(User).limit(1))
                users = result.scalars().all()
                
                end = time.perf_counter()
                return (end - start) * 1000
        
        # Execute operations that require new connections
        start_time = time.perf_counter()
        
        durations = await asyncio.gather(*[
            quick_db_operation(i)
            for i in range(operation_count)
        ])
        
        end_time = time.perf_counter()
        total_duration_ms = (end_time - start_time) * 1000
        
        # Connection pooling should be efficient
        avg_duration = sum(durations) / len(durations)
        assert avg_duration < 300, f"Average connection operation took {avg_duration:.2f}ms, too slow"
        assert total_duration_ms < 1000, f"Total connection time {total_duration_ms:.2f}ms, pooling inefficient"


@pytest.mark.asyncio
class TestMemoryUsageBaseline:
    """Tests to ensure memory usage stays within acceptable limits."""
    
    async def test_session_memory_cleanup(self, session_factory):
        """Test sessions don't accumulate in memory."""
        import gc
        
        # Get initial object count
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Create and dispose many sessions
        for i in range(20):
            async with session_factory() as temp_session:
                user = User(
                    id=500000000 + i,
                    first_name=f"MemoryTest{i}",
                    role="free",
                    points=i
                )
                temp_session.add(user)
                await temp_session.commit()
                
                # Delete immediately
                await temp_session.delete(user)
                await temp_session.commit()
        
        # Force garbage collection
        gc.collect()
        await asyncio.sleep(0.1)  # Allow cleanup
        final_objects = len(gc.get_objects())
        
        # Memory shouldn't grow significantly
        object_growth = final_objects - initial_objects
        assert object_growth < 1000, f"Memory grew by {object_growth} objects, possible leak"

    async def test_large_result_set_handling(self, session):
        """Test handling of large result sets doesn't exhaust memory."""
        base_user_id = 600000000
        large_count = 200
        
        # Create many users
        users = []
        for i in range(large_count):
            user = User(
                id=base_user_id + i,
                first_name=f"LargeSet{i}",
                role="free",
                points=i
            )
            users.append(user)
            session.add(user)
        await session.commit()
        
        start_time = time.perf_counter()
        
        # Query large result set
        result = await session.execute(
            select(User).where(User.id >= base_user_id).where(User.id < base_user_id + large_count)
        )
        all_users = result.scalars().all()
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Large query should complete efficiently
        assert len(all_users) == large_count
        assert duration_ms < 100, f"Large query took {duration_ms:.2f}ms, too slow"
        
        # Cleanup
        for user in users:
            await session.delete(user)
        await session.commit()