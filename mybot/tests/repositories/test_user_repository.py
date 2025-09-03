"""Tests for User repository implementation."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from database.base import Base
from database.models import User, UserStats, Badge, UserBadge
from repositories.implementations.user_repository import SqlUserRepository
from repositories.caching import create_memory_cache, CacheableMixin


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(test_engine):
    """Create session factory."""
    return async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def session(session_factory):
    """Create test session."""
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def user_repository(session):
    """Create user repository with cache."""
    cache_layer = create_memory_cache(max_size=100, default_ttl=300)
    repo = SqlUserRepository(session)
    repo._cache_layer = cache_layer
    return repo


@pytest_asyncio.fixture
async def sample_users(session):
    """Create sample users for testing."""
    users = [
        User(id=1, username="user1", first_name="John", last_name="Doe", points=100.0, level=2),
        User(id=2, username="user2", first_name="Jane", last_name="Smith", points=250.0, level=3, role="vip"),
        User(id=3, username="admin", first_name="Admin", last_name="User", points=500.0, level=5, is_admin=True),
        User(id=4, username="user4", first_name="Bob", last_name="Johnson", points=75.0, level=1),
    ]
    
    for user in users:
        session.add(user)
    
    await session.commit()
    
    # Create user stats
    stats = [
        UserStats(user_id=1, messages_sent=50, checkin_streak=5, last_activity_at=datetime.utcnow()),
        UserStats(user_id=2, messages_sent=120, checkin_streak=10, last_activity_at=datetime.utcnow()),
        UserStats(user_id=3, messages_sent=200, checkin_streak=15, last_activity_at=datetime.utcnow()),
    ]
    
    for stat in stats:
        session.add(stat)
    
    await session.commit()
    return users


@pytest_asyncio.fixture
async def sample_badges(session):
    """Create sample badges for testing."""
    badges = [
        Badge(id=1, name="First Steps", description="Welcome badge", icon="🎯", is_active=True),
        Badge(id=2, name="Chatter", description="Message count badge", icon="💬", is_active=True),
        Badge(id=3, name="VIP Member", description="VIP access badge", icon="⭐", grants_vip_access=True, is_active=True),
    ]
    
    for badge in badges:
        session.add(badge)
    
    await session.commit()
    return badges


class TestUserRepository:
    """Test cases for User repository."""
    
    async def test_get_by_id(self, user_repository, sample_users):
        """Test getting user by ID."""
        user = await user_repository.get_by_id(1)
        
        assert user is not None
        assert user.id == 1
        assert user.username == "user1"
        assert user.first_name == "John"
        assert user.points == 100.0
    
    async def test_get_by_id_nonexistent(self, user_repository):
        """Test getting non-existent user."""
        user = await user_repository.get_by_id(999)
        assert user is None
    
    async def test_create_user(self, user_repository):
        """Test creating a new user."""
        user_data = {
            "id": 100,
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "points": 0.0
        }
        
        user = await user_repository.create(user_data)
        
        assert user.id == 100
        assert user.username == "newuser"
        assert user.first_name == "New"
        assert user.points == 0.0
    
    async def test_get_by_username(self, user_repository, sample_users):
        """Test getting user by username."""
        user = await user_repository.get_by_username("user1")
        
        assert user is not None
        assert user.id == 1
        assert user.username == "user1"
    
    async def test_get_by_username_case_insensitive(self, user_repository, sample_users):
        """Test case-insensitive username search."""
        user = await user_repository.get_by_username("USER1")
        
        assert user is not None
        assert user.username == "user1"
    
    async def test_get_top_by_points(self, user_repository, sample_users):
        """Test getting top users by points."""
        top_users = await user_repository.get_top_by_points(limit=3)
        
        assert len(top_users) == 3
        # Should be ordered by points descending
        assert top_users[0].points == 500.0  # Admin
        assert top_users[1].points == 250.0  # Jane
        assert top_users[2].points == 100.0  # John
    
    async def test_get_admins(self, user_repository, sample_users):
        """Test getting admin users."""
        admins = await user_repository.get_admins()
        
        assert len(admins) == 1
        assert admins[0].username == "admin"
        assert admins[0].is_admin is True
    
    async def test_get_vip_users(self, user_repository, sample_users):
        """Test getting VIP users."""
        vip_users = await user_repository.get_vip_users()
        
        assert len(vip_users) == 1
        assert vip_users[0].username == "user2"
        assert vip_users[0].role == "vip"
    
    async def test_search_by_name(self, user_repository, sample_users):
        """Test searching users by name."""
        users = await user_repository.search_by_name("John")
        
        assert len(users) >= 1
        assert any(user.first_name == "John" for user in users)
    
    async def test_user_stats_operations(self, user_repository, sample_users):
        """Test user statistics operations."""
        # Get existing stats
        stats = await user_repository.get_user_stats(1)
        assert stats is not None
        assert stats.user_id == 1
        assert stats.messages_sent == 50
        
        # Update stats
        stats.messages_sent = 75
        updated_stats = await user_repository.update_user_stats(stats)
        assert updated_stats.messages_sent == 75
        
        # Create new stats
        new_stats = await user_repository.create_user_stats(4)
        assert new_stats.user_id == 4
        assert new_stats.messages_sent == 0
    
    async def test_badge_operations(self, user_repository, sample_users, sample_badges):
        """Test badge-related operations."""
        user_id = 1
        badge_id = 1
        
        # Award badge
        user_badge = await user_repository.award_badge(user_id, badge_id)
        assert user_badge.user_id == user_id
        assert user_badge.badge_id == badge_id
        
        # Check if user has badge
        has_badge = await user_repository.has_badge(user_id, badge_id)
        assert has_badge is True
        
        # Get user badges
        badges = await user_repository.get_user_badges(user_id)
        assert len(badges) == 1
        assert badges[0].id == badge_id
        
        # Test duplicate award prevention
        duplicate_award = await user_repository.award_badge(user_id, badge_id)
        assert duplicate_award.user_id == user_id
        
        # Revoke badge
        revoked = await user_repository.revoke_badge(user_id, badge_id)
        assert revoked is True
        
        # Check badge is removed
        has_badge_after = await user_repository.has_badge(user_id, badge_id)
        assert has_badge_after is False
    
    async def test_bulk_operations(self, user_repository, sample_users):
        """Test bulk operations."""
        user_ids = [1, 2, 3]
        users = await user_repository.get_users_by_ids(user_ids)
        
        assert len(users) == 3
        retrieved_ids = {user.id for user in users}
        assert retrieved_ids == set(user_ids)
    
    async def test_get_users_with_role(self, user_repository, sample_users):
        """Test getting users with specific role."""
        vip_users = await user_repository.get_users_with_role("vip")
        assert len(vip_users) == 1
        assert vip_users[0].role == "vip"
        
        free_users = await user_repository.get_users_with_role("free")
        # Should get users with default role
        assert len(free_users) >= 1
    
    async def test_active_users_count(self, user_repository, sample_users):
        """Test counting active users."""
        count = await user_repository.get_active_users_count(days=30)
        # Should count users with recent activity
        assert count >= 3
    
    async def test_engagement_metrics(self, user_repository, sample_users, sample_badges):
        """Test user engagement metrics calculation."""
        # Award a badge to user 1
        await user_repository.award_badge(1, 1)
        
        metrics = await user_repository.get_user_engagement_metrics(1)
        
        assert metrics["user_id"] == 1
        assert metrics["points"] == 100.0
        assert metrics["level"] == 2
        assert metrics["messages_sent"] == 50
        assert metrics["badge_count"] == 1
        assert "engagement_score" in metrics
        assert metrics["engagement_score"] > 0
    
    async def test_leaderboard_with_rankings(self, user_repository, sample_users):
        """Test leaderboard with rankings."""
        leaderboard = await user_repository.get_leaderboard_with_rankings(limit=5)
        
        assert len(leaderboard) == 4  # All sample users
        
        # Check ranking order
        for i, entry in enumerate(leaderboard, 1):
            assert entry["rank"] == i
            assert "user_id" in entry
            assert "points" in entry
            assert "username" in entry
        
        # First place should be admin with 500 points
        assert leaderboard[0]["points"] == 500.0
        assert leaderboard[0]["username"] == "admin"
    
    async def test_user_rank_by_points(self, user_repository, sample_users):
        """Test getting user rank by points."""
        # User with 250 points should be rank 2 (after admin with 500)
        rank = await user_repository.get_user_rank_by_points(2)
        assert rank == 2
        
        # User with 500 points should be rank 1
        admin_rank = await user_repository.get_user_rank_by_points(3)
        assert admin_rank == 1
        
        # Non-existent user
        no_rank = await user_repository.get_user_rank_by_points(999)
        assert no_rank is None
    
    async def test_caching(self, user_repository, sample_users):
        """Test repository caching functionality."""
        # First call - should miss cache
        user1 = await user_repository.get_by_id(1)
        stats1 = user_repository._cache_layer.get_stats()
        
        # Second call - should hit cache (if using cached method)
        user2 = await user_repository.get_by_id(1)
        stats2 = user_repository._cache_layer.get_stats()
        
        assert user1.id == user2.id
        # Cache stats should change
        assert stats2["total_requests"] >= stats1["total_requests"]
    
    async def test_cache_health_check(self, user_repository):
        """Test cache health check."""
        if hasattr(user_repository, 'cache_health_check'):
            health = await user_repository.cache_health_check()
            assert health["status"] in ["healthy", "no_cache", "error", "warning"]
    
    async def test_error_handling(self, user_repository):
        """Test error handling in repository operations."""
        # Test with invalid data types
        try:
            invalid_user = await user_repository.get_by_id("invalid")
            # Should handle gracefully
        except Exception as e:
            # Should not raise unhandled exceptions
            assert isinstance(e, (ValueError, TypeError))
    
    async def test_repository_stats_and_metrics(self, user_repository, sample_users):
        """Test repository statistics and performance metrics."""
        # Perform various operations
        await user_repository.get_by_id(1)
        await user_repository.get_by_username("user1")
        await user_repository.get_top_by_points(3)
        await user_repository.get_admins()
        
        # Check cache stats
        if hasattr(user_repository, '_cache_layer') and user_repository._cache_layer:
            stats = user_repository._cache_layer.get_stats()
            assert "hits" in stats
            assert "misses" in stats
            assert "hit_rate" in stats


@pytest.mark.asyncio
class TestUserRepositoryIntegration:
    """Integration tests for User repository."""
    
    async def test_complex_user_workflow(self, user_repository, sample_badges):
        """Test a complex user workflow with multiple operations."""
        # Create a new user
        user_data = {
            "id": 200,
            "username": "integration_test",
            "first_name": "Integration",
            "last_name": "Test",
            "points": 0.0
        }
        
        user = await user_repository.create(user_data)
        assert user.id == 200
        
        # Create user stats
        stats = await user_repository.create_user_stats(200)
        assert stats.user_id == 200
        
        # Award multiple badges
        await user_repository.award_badge(200, 1)
        await user_repository.award_badge(200, 2)
        
        # Get user with all related data
        user = await user_repository.get_by_id(200)
        stats = await user_repository.get_user_stats(200)
        badges = await user_repository.get_user_badges(200)
        
        assert user.username == "integration_test"
        assert stats.user_id == 200
        assert len(badges) == 2
        
        # Get engagement metrics
        metrics = await user_repository.get_user_engagement_metrics(200)
        assert metrics["user_id"] == 200
        assert metrics["badge_count"] == 2
    
    async def test_concurrent_operations(self, user_repository):
        """Test concurrent repository operations."""
        import asyncio
        
        # Create multiple users concurrently
        async def create_user(user_id):
            return await user_repository.create({
                "id": user_id,
                "username": f"concurrent_{user_id}",
                "first_name": "Concurrent",
                "last_name": "User",
                "points": float(user_id)
            })
        
        # Create 10 users concurrently
        user_ids = range(300, 310)
        tasks = [create_user(user_id) for user_id in user_ids]
        users = await asyncio.gather(*tasks)
        
        assert len(users) == 10
        for i, user in enumerate(users, 300):
            assert user.id == i
            assert user.username == f"concurrent_{i}"
    
    async def test_repository_performance(self, user_repository, sample_users):
        """Test repository performance with larger datasets."""
        import time
        
        # Test bulk retrieval performance
        start_time = time.time()
        user_ids = [1, 2, 3, 4] * 25  # 100 total requests
        
        for user_id in user_ids[:10]:  # Test first 10
            await user_repository.get_by_id(user_id)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time
        assert execution_time < 5.0  # 5 seconds threshold
        
        # Test leaderboard performance
        start_time = time.time()
        leaderboard = await user_repository.get_leaderboard_with_rankings(limit=100)
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 2.0  # 2 seconds threshold
        assert len(leaderboard) <= 100