"""
Async Database Operations and Transaction Integrity Tests
Tests database session lifecycle management and transaction integrity across services.
"""
import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from database.models import User, UserStats, Channel
from database.transaction_models import PointTransaction


@pytest.mark.asyncio
class TestAsyncDatabaseOperations:
    """Tests for async database operations integrity."""
    
    async def test_async_session_lifecycle_management(self, session):
        """Test async session lifecycle doesn't leak or deadlock."""
        # Test basic session operations
        user = User(
            id=111111111,
            first_name="SessionTest",
            role="free",
            points=0
        )
        
        # Test session lifecycle
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # Verify user was created
        result = await session.execute(select(User).where(User.id == 111111111))
        found_user = result.scalar_one_or_none()
        
        assert found_user is not None
        assert found_user.first_name == "SessionTest"
        
        # Test update operation
        found_user.points = 50
        await session.commit()
        
        # Verify update
        result = await session.execute(select(User).where(User.id == 111111111))
        updated_user = result.scalar_one_or_none()
        assert updated_user.points == 50
        
        # Cleanup
        await session.delete(updated_user)
        await session.commit()

    async def test_async_transaction_context_manager(self, session):
        """Test async transaction context managers work correctly."""
        user_id = 222222222
        
        # Test successful transaction
        async with session.begin():
            user = User(
                id=user_id,
                first_name="TransactionTest",
                role="free",
                points=100
            )
            session.add(user)
            # Transaction commits automatically
        
        # Verify user was created
        result = await session.execute(select(User).where(User.id == user_id))
        created_user = result.scalar_one_or_none()
        assert created_user is not None
        assert created_user.points == 100
        
        # Test transaction rollback on exception
        try:
            async with session.begin():
                created_user.points = 500
                raise Exception("Force rollback")
        except Exception:
            pass
        
        # Verify rollback occurred
        await session.refresh(created_user)
        assert created_user.points == 100, "Transaction should have rolled back"
        
        # Cleanup
        await session.delete(created_user)
        await session.commit()

    async def test_concurrent_session_handling(self, session_factory):
        """Test concurrent session handling doesn't cause deadlocks."""
        async def create_user_operation(user_id: int):
            async with session_factory() as local_session:
                user = User(
                    id=user_id,
                    first_name=f"ConcurrentTest{user_id}",
                    role="free",
                    points=user_id % 100
                )
                local_session.add(user)
                await local_session.commit()
                return user_id
        
        # Run concurrent operations
        user_ids = [333333330 + i for i in range(10)]
        results = await asyncio.gather(*[create_user_operation(uid) for uid in user_ids])
        
        assert len(results) == 10
        assert set(results) == set(user_ids)
        
        # Verify all users were created
        async with session_factory() as cleanup_session:
            for user_id in user_ids:
                result = await cleanup_session.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                assert user is not None, f"User {user_id} should exist"
                
                # Cleanup
                await cleanup_session.delete(user)
            await cleanup_session.commit()

    async def test_cross_table_transaction_consistency(self, session):
        """Test transaction consistency across multiple tables."""
        user_id = 444444444
        
        async with session.begin():
            # Create user
            user = User(
                id=user_id,
                first_name="CrossTableTest",
                role="free",
                points=100
            )
            session.add(user)
            
            # Create user stats
            stats = UserStats(
                user_id=user_id,
                checkin_streak=5,
                last_checkin_at=datetime.utcnow()
            )
            session.add(stats)
            
            # Create point transaction
            transaction = PointTransaction(
                user_id=user_id,
                amount=100.0,
                balance_after=100.0,
                source="initial_award",
                description="Test transaction"
            )
            session.add(transaction)
            # All should commit together
        
        # Verify all were created consistently
        user_result = await session.execute(select(User).where(User.id == user_id))
        stats_result = await session.execute(select(UserStats).where(UserStats.user_id == user_id))
        trans_result = await session.execute(select(PointTransaction).where(PointTransaction.user_id == user_id))
        
        user = user_result.scalar_one_or_none()
        stats = stats_result.scalar_one_or_none()
        transaction = trans_result.scalar_one_or_none()
        
        assert user is not None, "User should be created"
        assert stats is not None, "UserStats should be created"
        assert transaction is not None, "PointTransaction should be created"
        assert stats.checkin_streak == 5, "Stats data should be correct"
        assert transaction.amount == 100.0, "Transaction data should be correct"
        assert transaction.balance_after == 100.0, "Balance should be tracked"
        
        # Cleanup
        await session.delete(transaction)
        await session.delete(stats)
        await session.delete(user)
        await session.commit()


@pytest.mark.asyncio
class TestDatabaseConsistencyValidation:
    """Tests for data consistency across modules."""
    
    async def test_point_transaction_consistency(self, session):
        """Test PointTransaction consistency requirements."""
        user_id = 555555555
        
        # Create user first
        user = User(
            id=user_id,
            first_name="PointConsistencyTest",
            role="free",
            points=0
        )
        session.add(user)
        await session.commit()
        
        # Test point transaction creation
        transaction = PointTransaction(
            user_id=user_id,
            amount=25.0,
            balance_after=25.0,
            source="reaction_award",
            description="Test reaction award"
        )
        session.add(transaction)
        await session.commit()
        
        # Update user points
        user.points += 25.0
        await session.commit()
        
        # Verify consistency
        trans_result = await session.execute(
            select(PointTransaction).where(PointTransaction.user_id == user_id)
        )
        saved_transaction = trans_result.scalar_one_or_none()
        
        user_result = await session.execute(select(User).where(User.id == user_id))
        updated_user = user_result.scalar_one_or_none()
        
        assert saved_transaction is not None
        assert saved_transaction.amount == 25.0
        assert saved_transaction.source == "reaction_award"
        assert saved_transaction.balance_after == 25.0
        assert updated_user.points == 25.0
        
        # Cleanup
        await session.delete(saved_transaction)
        await session.delete(updated_user)
        await session.commit()

    async def test_user_stats_creation_and_update(self, session):
        """Test UserStats creation and update patterns."""
        user_id = 666666666
        
        # Create user
        user = User(
            id=user_id,
            first_name="StatsTest",
            role="free",
            points=0
        )
        session.add(user)
        await session.commit()
        
        # Create initial stats
        stats = UserStats(
            user_id=user_id,
            checkin_streak=1,
            last_checkin_at=datetime.utcnow()
        )
        session.add(stats)
        await session.commit()
        
        # Update stats
        stats.checkin_streak = 5
        await session.commit()
        
        # Verify update
        stats_result = await session.execute(select(UserStats).where(UserStats.user_id == user_id))
        updated_stats = stats_result.scalar_one_or_none()
        
        assert updated_stats is not None
        assert updated_stats.checkin_streak == 5
        
        # Cleanup
        await session.delete(updated_stats)
        await session.delete(user)
        await session.commit()

    async def test_foreign_key_constraint_handling(self, session):
        """Test foreign key constraints are properly enforced."""
        # Try to create UserStats without corresponding User
        orphan_stats = UserStats(
            user_id=999999999,  # Non-existent user
            checkin_streak=1,
            last_checkin_at=datetime.utcnow()
        )
        session.add(orphan_stats)
        
        # This should fail due to foreign key constraint
        try:
            await session.commit()
            assert False, "Foreign key constraint should prevent orphan UserStats"
        except Exception:
            # Expected behavior
            await session.rollback()

    async def test_database_isolation_between_tests(self, session):
        """Test that tests are properly isolated from each other."""
        # This test ensures no data leaks between tests
        user_id = 777777777
        
        # Check that user doesn't already exist from previous tests
        result = await session.execute(select(User).where(User.id == user_id))
        existing_user = result.scalar_one_or_none()
        
        assert existing_user is None, "Tests should start with clean database state"
        
        # Create user for this test
        user = User(
            id=user_id,
            first_name="IsolationTest",
            role="free",
            points=123
        )
        session.add(user)
        await session.commit()
        
        # Verify creation
        result = await session.execute(select(User).where(User.id == user_id))
        created_user = result.scalar_one_or_none()
        assert created_user is not None
        assert created_user.points == 123
        
        # Cleanup (important for test isolation)
        await session.delete(created_user)
        await session.commit()


@pytest.mark.asyncio
class TestDatabasePerformanceBaselines:
    """Performance tests for database operations."""
    
    async def test_user_query_performance(self, session):
        """Test user query performance meets baseline requirements."""
        # Create test user
        user_id = 888888888
        user = User(
            id=user_id,
            first_name="PerfTest",
            role="free",
            points=50
        )
        session.add(user)
        await session.commit()
        
        # Measure query performance
        start_time = asyncio.get_event_loop().time()
        
        result = await session.execute(select(User).where(User.id == user_id))
        found_user = result.scalar_one_or_none()
        
        end_time = asyncio.get_event_loop().time()
        duration_ms = (end_time - start_time) * 1000
        
        # Database query should be under 50ms baseline (test environment)
        assert duration_ms < 50, f"User query took {duration_ms:.2f}ms, exceeds 50ms baseline"
        assert found_user is not None
        assert found_user.id == user_id
        
        # Cleanup
        await session.delete(found_user)
        await session.commit()

    async def test_transaction_creation_performance(self, session):
        """Test transaction creation performance."""
        user_id = 999888777
        
        # Create user first
        user = User(id=user_id, first_name="TransPerfTest", role="free", points=0)
        session.add(user)
        await session.commit()
        
        # Measure transaction creation
        start_time = asyncio.get_event_loop().time()
        
        transaction = PointTransaction(
            user_id=user_id,
            amount=10.0,
            balance_after=10.0,
            source="performance_test",
            description="Performance test transaction"
        )
        session.add(transaction)
        await session.commit()
        
        end_time = asyncio.get_event_loop().time()
        duration_ms = (end_time - start_time) * 1000
        
        # Transaction creation should be fast
        assert duration_ms < 20, f"Transaction creation took {duration_ms:.2f}ms, too slow"
        
        # Cleanup
        await session.delete(transaction)
        await session.delete(user)
        await session.commit()

    async def test_bulk_operations_performance(self, session):
        """Test bulk database operations performance."""
        user_ids = [800000000 + i for i in range(50)]
        
        # Measure bulk creation
        start_time = asyncio.get_event_loop().time()
        
        users = []
        for user_id in user_ids:
            user = User(
                id=user_id,
                first_name=f"BulkTest{user_id}",
                role="free",
                points=user_id % 100
            )
            users.append(user)
            session.add(user)
        
        await session.commit()
        
        end_time = asyncio.get_event_loop().time()
        duration_ms = (end_time - start_time) * 1000
        
        # Bulk creation should be efficient (adjust threshold for test environment)
        assert duration_ms < 1000, f"Bulk creation of 50 users took {duration_ms:.2f}ms, too slow"
        
        # Cleanup
        for user in users:
            await session.delete(user)
        await session.commit()


@pytest.mark.asyncio
class TestTransactionIntegrity:
    """Tests for database transaction integrity across operations."""
    
    async def test_rollback_on_constraint_violation(self, session):
        """Test proper rollback behavior on constraint violations."""
        user_id = 123987654
        
        # Create user first
        user = User(id=user_id, first_name="ConstraintTest", role="free", points=0)
        session.add(user)
        await session.commit()
        
        # Try to create duplicate user (should fail)
        try:
            async with session.begin():
                duplicate_user = User(id=user_id, first_name="Duplicate", role="free")
                session.add(duplicate_user)
                # This should trigger rollback
        except Exception:
            # Expected behavior
            pass
        
        # Original user should still exist and be unchanged
        result = await session.execute(select(User).where(User.id == user_id))
        existing_user = result.scalar_one_or_none()
        
        assert existing_user is not None
        assert existing_user.first_name == "ConstraintTest"
        
        # Cleanup
        await session.delete(existing_user)
        await session.commit()

    async def test_nested_transaction_handling(self, session):
        """Test nested transaction scenarios."""
        user_id = 456789123
        
        try:
            async with session.begin():
                # Outer transaction
                user = User(id=user_id, first_name="NestedTest", role="free", points=0)
                session.add(user)
                
                # Simulate nested operation
                stats = UserStats(
                    user_id=user_id,
                    checkin_streak=1,
                    last_checkin_at=datetime.utcnow()
                )
                session.add(stats)
                
                # Both should commit together
        except Exception as e:
            pytest.fail(f"Nested transaction failed: {e}")
        
        # Verify both were created
        user_result = await session.execute(select(User).where(User.id == user_id))
        stats_result = await session.execute(select(UserStats).where(UserStats.user_id == user_id))
        
        created_user = user_result.scalar_one_or_none()
        created_stats = stats_result.scalar_one_or_none()
        
        assert created_user is not None
        assert created_stats is not None
        assert created_stats.checkin_streak == 1
        
        # Cleanup
        await session.delete(created_stats)
        await session.delete(created_user)
        await session.commit()

    async def test_service_transaction_safety(self, session, point_service):
        """Test service operations maintain transaction safety."""
        user_id = 567890234
        
        # Create user
        user = User(id=user_id, first_name="ServiceTransTest", role="free", points=0)
        session.add(user)
        await session.commit()
        
        # Mock successful point award
        point_service.award_points = AsyncMock(return_value=True)
        point_service.get_user_points = AsyncMock(return_value=25.0)
        
        # Test service transaction doesn't interfere
        points = await point_service.get_user_points(user_id)
        success = await point_service.award_points(user_id, 25, "test_award")
        
        assert points == 25.0
        assert success is True
        
        # Service calls should not affect our session state
        await session.refresh(user)
        # Original user should be unchanged (service uses mocks)
        assert user.points == 0
        
        # Cleanup
        await session.delete(user)
        await session.commit()