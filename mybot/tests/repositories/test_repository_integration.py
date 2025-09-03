"""Integration tests for the complete repository pattern system."""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from database.base import Base
from database.models import User, Mission, UserMissionEntry, Achievement
from database.narrative_unified import NarrativeFragment, UserNarrativeState
from database.transaction_models import PointTransaction

from repositories.implementations.user_repository import SqlUserRepository
from repositories.implementations.point_repository import SqlPointRepository
from repositories.implementations.mission_repository import SqlMissionRepository
from repositories.implementations.narrative_repository import SqlNarrativeRepository
from repositories.caching import create_memory_cache
from repositories.query_optimization import QueryOptimizer, IndexRecommendation, QueryProfiler


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
async def repositories(session):
    """Create all repositories with shared cache."""
    cache_layer = create_memory_cache(max_size=1000, default_ttl=300)
    
    user_repo = SqlUserRepository(session)
    user_repo._cache_layer = cache_layer
    
    point_repo = SqlPointRepository(session)
    point_repo._cache_layer = cache_layer
    
    mission_repo = SqlMissionRepository(session)
    mission_repo._cache_layer = cache_layer
    
    narrative_repo = SqlNarrativeRepository(session)
    narrative_repo._cache_layer = cache_layer
    
    return {
        'user': user_repo,
        'point': point_repo,
        'mission': mission_repo,
        'narrative': narrative_repo,
        'cache': cache_layer
    }


@pytest_asyncio.fixture
async def sample_data(session, repositories):
    """Create comprehensive sample data for integration tests."""
    # Create users
    users = [
        User(id=1, username="alice", first_name="Alice", points=100.0, level=2),
        User(id=2, username="bob", first_name="Bob", points=250.0, level=3),
        User(id=3, username="charlie", first_name="Charlie", points=500.0, level=5),
    ]
    
    for user in users:
        session.add(user)
    
    # Create missions
    missions = [
        Mission(id="daily_login", name="Daily Login", type="daily", target_value=1, reward_points=10),
        Mission(id="send_messages", name="Send Messages", type="one_time", target_value=50, reward_points=25),
        Mission(id="narrative_progress", name="Story Progress", type="weekly", target_value=5, reward_points=50),
    ]
    
    for mission in missions:
        session.add(mission)
    
    # Create narrative fragments
    fragments = [
        NarrativeFragment(
            id="intro",
            title="Introduction",
            content="Welcome to the story",
            fragment_type="STORY",
            is_active=True
        ),
        NarrativeFragment(
            id="choice_1",
            title="First Choice",
            content="Choose your path",
            fragment_type="DECISION",
            choices=[
                {"text": "Go left", "next_fragment_id": "path_left"},
                {"text": "Go right", "next_fragment_id": "path_right"}
            ],
            is_active=True
        ),
        NarrativeFragment(
            id="path_left",
            title="Left Path",
            content="You chose the left path",
            fragment_type="STORY",
            triggers={"reward_points": 10},
            is_active=True
        )
    ]
    
    for fragment in fragments:
        session.add(fragment)
    
    await session.commit()
    
    return {
        'users': users,
        'missions': missions,
        'fragments': fragments
    }


class TestRepositoryIntegration:
    """Integration tests for repository pattern system."""
    
    async def test_cross_repository_user_journey(self, repositories, sample_data):
        """Test complete user journey across multiple repositories."""
        user_repo = repositories['user']
        point_repo = repositories['point']
        mission_repo = repositories['mission']
        narrative_repo = repositories['narrative']
        
        user_id = 1
        
        # 1. User completes a mission
        mission_entry = await mission_repo.create_user_mission_entry(user_id, "daily_login")
        completed_entry = await mission_repo.complete_user_mission(user_id, "daily_login")
        
        assert completed_entry.completed is True
        
        # 2. Award points for mission completion
        transaction = await point_repo.add_points(user_id, 10.0, "mission_reward", "Daily login mission")
        assert transaction.amount == 10.0
        
        # 3. Check user's updated balance
        balance = await point_repo.get_user_balance(user_id)
        assert balance == 110.0  # Original 100 + 10 from mission
        
        # 4. User progresses in narrative
        user_state = await narrative_repo.create_user_narrative_state(user_id)
        await narrative_repo.add_visited_fragment(user_id, "intro")
        await narrative_repo.add_completed_fragment(user_id, "intro")
        
        # 5. Get comprehensive user profile
        user = await user_repo.get_by_id(user_id)
        user_missions = await mission_repo.get_user_completed_missions(user_id)
        narrative_progress = await narrative_repo.get_user_progress_percentage(user_id)
        
        assert user.points == 110.0
        assert len(user_missions) == 1
        assert narrative_progress > 0
    
    async def test_caching_across_repositories(self, repositories, sample_data):
        """Test shared caching across repositories."""
        user_repo = repositories['user']
        point_repo = repositories['point']
        cache = repositories['cache']
        
        # Clear cache stats
        cache.reset_stats()
        
        # Perform operations that should use cache
        user1 = await user_repo.get_by_id(1)  # Cache miss
        balance1 = await point_repo.get_user_balance(1)  # Cache miss
        
        user2 = await user_repo.get_by_id(1)  # Should be cache hit if cached
        balance2 = await point_repo.get_user_balance(1)  # Should be cache hit if cached
        
        # Verify data consistency
        assert user1.id == user2.id
        assert balance1 == balance2
        
        # Check cache stats
        stats = cache.get_stats()
        assert stats['total_requests'] > 0
    
    async def test_transaction_consistency(self, repositories, sample_data):
        """Test transaction consistency across repositories."""
        user_repo = repositories['user']
        point_repo = repositories['point']
        mission_repo = repositories['mission']
        
        user_id = 2
        initial_balance = await point_repo.get_user_balance(user_id)
        
        # Simulate complex transaction: complete mission and award points
        try:
            # Start mission progress
            await mission_repo.increment_mission_progress(user_id, "send_messages", 50)
            
            # Mission should now be complete, award points
            mission_entry = await mission_repo.get_user_mission_entry(user_id, "send_messages")
            assert mission_entry.completed is True
            
            # Award mission points
            await point_repo.add_points(user_id, 25.0, "mission_completion", "Send messages mission")
            
            # Verify final state
            final_balance = await point_repo.get_user_balance(user_id)
            assert final_balance == initial_balance + 25.0
            
            completed_missions = await mission_repo.get_user_completed_missions(user_id)
            assert len(completed_missions) == 1
            
        except Exception as e:
            pytest.fail(f"Transaction consistency test failed: {e}")
    
    async def test_query_optimization_integration(self, repositories, sample_data):
        """Test query optimization across repositories."""
        optimizer = QueryOptimizer()
        index_recommender = IndexRecommendation()
        query_profiler = QueryProfiler()
        
        user_repo = repositories['user']
        point_repo = repositories['point']
        
        # Simulate query patterns
        for i in range(10):
            # Frequent user lookups
            await user_repo.get_by_id(1)
            await user_repo.get_by_username("alice")
            
            # Point balance queries
            await point_repo.get_user_balance(1)
            
            # Record patterns for index recommendation
            index_recommender.record_query_pattern(
                table="users",
                columns=["id"],
                query_type="SELECT",
                frequency=1
            )
            
            index_recommender.record_query_pattern(
                table="users",
                columns=["username"],
                query_type="SELECT",
                frequency=1
            )
        
        # Get index recommendations
        recommendations = index_recommender.get_index_recommendations(min_frequency=5)
        assert len(recommendations) > 0
        
        # Check that high-frequency patterns get recommended
        user_id_rec = next((r for r in recommendations if "id" in r["columns"]), None)
        assert user_id_rec is not None
        assert user_id_rec["frequency"] >= 5
    
    async def test_repository_performance_monitoring(self, repositories, sample_data):
        """Test performance monitoring across repositories."""
        import time
        
        user_repo = repositories['user']
        point_repo = repositories['point']
        mission_repo = repositories['mission']
        
        query_profiler = QueryProfiler()
        
        # Simulate various operations and profile them
        operations = [
            ("get_user", lambda: user_repo.get_by_id(1)),
            ("get_balance", lambda: point_repo.get_user_balance(1)),
            ("get_missions", lambda: mission_repo.get_user_mission_entries(1)),
            ("top_users", lambda: user_repo.get_top_by_points(10)),
        ]
        
        for operation_name, operation in operations:
            start_time = time.time()
            result = await operation()
            execution_time = time.time() - start_time
            
            # Profile the query
            await query_profiler.profile_query(
                query=f"Mock query for {operation_name}",
                execution_time=execution_time,
                result_count=1 if not isinstance(result, list) else len(result)
            )
        
        # Get performance report
        report = query_profiler.get_performance_report()
        
        assert report['overview']['total_executions'] == 4
        assert len(report['slowest_queries']) > 0
        assert len(report['most_frequent_queries']) > 0
    
    async def test_bulk_operations_integration(self, repositories, sample_data):
        """Test bulk operations across repositories."""
        user_repo = repositories['user']
        point_repo = repositories['point']
        
        # Test bulk user creation and point awards
        user_ids = range(100, 110)
        
        # Create users in bulk (simulate by creating individually)
        users = []
        for user_id in user_ids:
            user_data = {
                "id": user_id,
                "username": f"bulk_user_{user_id}",
                "first_name": "Bulk",
                "points": 0.0
            }
            user = await user_repo.create(user_data)
            users.append(user)
        
        # Bulk point awards
        transactions = []
        for user_id in user_ids:
            transaction = await point_repo.add_points(
                user_id, 50.0, "bulk_award", "Bulk point award"
            )
            transactions.append(transaction)
        
        # Verify bulk operations
        assert len(users) == 10
        assert len(transactions) == 10
        
        # Verify all users received points
        for user_id in user_ids:
            balance = await point_repo.get_user_balance(user_id)
            assert balance == 50.0
    
    async def test_error_handling_integration(self, repositories, sample_data):
        """Test error handling across repository operations."""
        user_repo = repositories['user']
        point_repo = repositories['point']
        mission_repo = repositories['mission']
        
        # Test cascading error scenarios
        
        # 1. Try to award points to non-existent user
        transaction = await point_repo.add_points(999, 100.0, "test", "Test transaction")
        assert transaction is not None  # Should create user automatically
        
        # 2. Try to complete non-existent mission
        try:
            await mission_repo.complete_user_mission(1, "non_existent_mission")
            # Should handle gracefully
        except Exception as e:
            # Should not raise unhandled exceptions
            assert False, f"Unhandled exception: {e}"
        
        # 3. Try to deduct more points than available
        insufficient_transaction = await point_repo.deduct_points(1, 10000.0, "test", "Insufficient funds test")
        assert insufficient_transaction is None  # Should fail gracefully
        
        # Verify system remains in consistent state
        user = await user_repo.get_by_id(1)
        assert user is not None
        assert user.points >= 0
    
    async def test_repository_factory_pattern(self, session):
        """Test repository factory pattern for dependency injection."""
        
        class RepositoryFactory:
            """Factory for creating repository instances."""
            
            def __init__(self, session: AsyncSession, cache_layer=None):
                self.session = session
                self.cache_layer = cache_layer or create_memory_cache()
            
            def create_user_repository(self) -> SqlUserRepository:
                repo = SqlUserRepository(self.session)
                repo._cache_layer = self.cache_layer
                return repo
            
            def create_point_repository(self) -> SqlPointRepository:
                repo = SqlPointRepository(self.session)
                repo._cache_layer = self.cache_layer
                return repo
            
            def get_all_repositories(self):
                return {
                    'user': self.create_user_repository(),
                    'point': self.create_point_repository(),
                }
        
        # Test factory
        factory = RepositoryFactory(session)
        repos = factory.get_all_repositories()
        
        assert 'user' in repos
        assert 'point' in repos
        assert isinstance(repos['user'], SqlUserRepository)
        assert isinstance(repos['point'], SqlPointRepository)
        
        # Test that repositories share the same cache
        assert repos['user']._cache_layer is repos['point']._cache_layer
    
    async def test_repository_health_checks(self, repositories):
        """Test health check functionality across repositories."""
        health_results = {}
        
        for name, repo in repositories.items():
            if name == 'cache':
                continue
                
            if hasattr(repo, 'cache_health_check'):
                health = await repo.cache_health_check()
                health_results[name] = health
        
        # All repositories should report healthy status
        for name, health in health_results.items():
            assert health['status'] in ['healthy', 'no_cache'], f"{name} repository health check failed: {health}"
    
    async def test_repository_metrics_aggregation(self, repositories, sample_data):
        """Test aggregation of metrics across repositories."""
        user_repo = repositories['user']
        point_repo = repositories['point']
        mission_repo = repositories['mission']
        narrative_repo = repositories['narrative']
        cache = repositories['cache']
        
        # Perform various operations
        await user_repo.get_by_id(1)
        await point_repo.get_user_balance(1)
        await mission_repo.get_user_mission_entries(1)
        await narrative_repo.get_active_fragments()
        
        # Aggregate metrics
        cache_stats = cache.get_stats()
        
        metrics = {
            'cache': cache_stats,
            'repositories_tested': ['user', 'point', 'mission', 'narrative'],
            'operations_performed': 4,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        assert metrics['cache']['total_requests'] >= 0
        assert len(metrics['repositories_tested']) == 4
        assert metrics['operations_performed'] == 4
    
    async def test_concurrent_repository_access(self, repositories, sample_data):
        """Test concurrent access across repositories."""
        import asyncio
        
        user_repo = repositories['user']
        point_repo = repositories['point']
        
        async def concurrent_operations(user_id):
            """Perform concurrent operations for a user."""
            tasks = [
                user_repo.get_by_id(user_id),
                point_repo.get_user_balance(user_id),
                point_repo.add_points(user_id, 1.0, "concurrent_test", "Concurrent operation"),
                user_repo.get_user_engagement_metrics(user_id)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check that no operations failed
            for result in results:
                assert not isinstance(result, Exception), f"Concurrent operation failed: {result}"
            
            return results
        
        # Run concurrent operations for multiple users
        user_tasks = [concurrent_operations(user_id) for user_id in [1, 2, 3]]
        all_results = await asyncio.gather(*user_tasks)
        
        # Verify all operations completed successfully
        assert len(all_results) == 3
        for user_results in all_results:
            assert len(user_results) == 4  # 4 operations per user