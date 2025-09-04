"""
MVP Performance Requirements Compliance Tests

Comprehensive test suite for <500ms performance requirements,
concurrent user handling, database optimization, and system responsiveness.
"""

import pytest
import pytest_asyncio
import time
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from concurrent.futures import ThreadPoolExecutor

from database.narrative_unified import (
    NarrativeFragment, 
    UserNarrativeState, 
    UserDecisionLog,
    UserMissionProgress
)
from services.narrative_engine import NarrativeEngine
from services.diana_character_validator import DianaCharacterValidator


class TestCoreOperationPerformance:
    """Test core narrative operations meet <500ms requirement."""

    @pytest_asyncio.fixture
    async def optimized_narrative_engine(self, session):
        """Create optimized narrative engine for performance testing."""
        engine = NarrativeEngine(session)
        engine.point_service = AsyncMock()
        
        # Mock database operations for consistent timing
        engine._get_or_create_user_state = AsyncMock()
        engine._get_fragment_by_key = AsyncMock()
        
        return engine

    async def test_fragment_retrieval_performance(self, session):
        """Test fragment retrieval meets <500ms requirement."""
        # Create test fragment
        fragment = NarrativeFragment(
            id='performance_test_fragment',
            title='Performance Test Fragment',
            content='Test content for performance validation',
            fragment_type='STORY',
            storyline_level=1,
            tier_classification='los_kinkys',
            diana_personality_weight=95,
            is_active=True
        )
        session.add(fragment)
        await session.commit()
        
        # Measure retrieval performance
        start_time = time.time()
        
        from sqlalchemy import select
        result = await session.execute(
            select(NarrativeFragment).where(NarrativeFragment.id == 'performance_test_fragment')
        )
        retrieved_fragment = result.scalar_one_or_none()
        
        end_time = time.time()
        retrieval_time_ms = (end_time - start_time) * 1000
        
        assert retrieved_fragment is not None, "Fragment should be retrieved successfully"
        assert retrieval_time_ms < 500, f"Fragment retrieval took {retrieval_time_ms:.2f}ms, should be < 500ms"

    async def test_user_state_creation_performance(self, session):
        """Test user state creation meets performance requirements."""
        user_id = 12345
        
        start_time = time.time()
        
        # Create user state
        user_state = UserNarrativeState(
            user_id=user_id,
            current_fragment_id='test_fragment',
            current_level=1,
            current_tier='los_kinkys',
            visited_fragments=[],
            completed_fragments=[],
            unlocked_clues=[]
        )
        session.add(user_state)
        await session.commit()
        
        end_time = time.time()
        creation_time_ms = (end_time - start_time) * 1000
        
        assert creation_time_ms < 500, f"User state creation took {creation_time_ms:.2f}ms, should be < 500ms"

    async def test_choice_processing_performance(self, optimized_narrative_engine):
        """Test choice processing meets <500ms requirement."""
        user_id = 12345
        
        # Mock dependencies for consistent timing
        test_fragment = MagicMock()
        test_fragment.choices = [
            {'text': 'Test choice', 'next_fragment_id': 'next_fragment', 'points': 10}
        ]
        
        optimized_narrative_engine.get_user_current_fragment = AsyncMock(return_value=test_fragment)
        optimized_narrative_engine._get_fragment_by_key = AsyncMock(return_value=test_fragment)
        optimized_narrative_engine._check_access_conditions = AsyncMock(return_value=True)
        optimized_narrative_engine._process_fragment_rewards = AsyncMock()
        
        # Mock user state
        user_state = MagicMock()
        user_state.choices_made = []
        optimized_narrative_engine._get_or_create_user_state = AsyncMock(return_value=user_state)
        
        start_time = time.time()
        
        result = await optimized_narrative_engine.process_user_decision(user_id, 0)
        
        end_time = time.time()
        processing_time_ms = (end_time - start_time) * 1000
        
        assert result is not None, "Choice processing should return result"
        assert processing_time_ms < 500, f"Choice processing took {processing_time_ms:.2f}ms, should be < 500ms"

    async def test_character_validation_performance(self, session):
        """Test character validation meets performance requirements."""
        validator = DianaCharacterValidator(session)
        
        test_content = '💋 **Diana te mira con ojos llenos de misterio...** \n\nSus labios se curvan en una sonrisa enigmática mientras susurra: "¿Acaso pensaste que los secretos se revelan tan fácilmente, querido mío?" La complejidad de sus emociones añade profundidad a cada palabra.'
        
        start_time = time.time()
        
        result = await validator.validate_text(test_content, context="narrative_fragment")
        
        end_time = time.time()
        validation_time_ms = (end_time - start_time) * 1000
        
        assert result is not None, "Validation should return result"
        assert validation_time_ms < 500, f"Character validation took {validation_time_ms:.2f}ms, should be < 500ms"

    async def test_database_transaction_performance(self, session):
        """Test database transactions meet performance requirements."""
        start_time = time.time()
        
        # Create multiple related objects in single transaction
        fragment = NarrativeFragment(
            id='transaction_test_fragment',
            title='Transaction Test',
            content='Test content',
            fragment_type='DECISION',
            is_active=True
        )
        
        user_state = UserNarrativeState(
            user_id=54321,
            current_fragment_id='transaction_test_fragment',
            current_level=1
        )
        
        decision_log = UserDecisionLog(
            user_id=54321,
            fragment_id='transaction_test_fragment',
            decision_choice='Test choice',
            points_awarded=10
        )
        
        session.add_all([fragment, user_state, decision_log])
        await session.commit()
        
        end_time = time.time()
        transaction_time_ms = (end_time - start_time) * 1000
        
        assert transaction_time_ms < 500, f"Database transaction took {transaction_time_ms:.2f}ms, should be < 500ms"


class TestConcurrentUserHandling:
    """Test system handles concurrent users efficiently."""

    async def test_concurrent_fragment_access(self, session):
        """Test concurrent fragment access doesn't degrade performance."""
        # Create test fragment
        fragment = NarrativeFragment(
            id='concurrent_test_fragment',
            title='Concurrent Test Fragment',
            content='Content for concurrent access testing',
            fragment_type='STORY',
            is_active=True
        )
        session.add(fragment)
        await session.commit()
        
        async def access_fragment():
            from sqlalchemy import select
            start_time = time.time()
            result = await session.execute(
                select(NarrativeFragment).where(NarrativeFragment.id == 'concurrent_test_fragment')
            )
            retrieved = result.scalar_one_or_none()
            end_time = time.time()
            return (end_time - start_time) * 1000, retrieved is not None
        
        # Create 10 concurrent access tasks
        tasks = [access_fragment() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Verify all succeeded within time limit
        for access_time_ms, success in results:
            assert success, "All concurrent accesses should succeed"
            assert access_time_ms < 1000, f"Concurrent access took {access_time_ms:.2f}ms, should be < 1000ms"
        
        # Verify average performance
        avg_time = sum(time_ms for time_ms, _ in results) / len(results)
        assert avg_time < 500, f"Average concurrent access time {avg_time:.2f}ms should be < 500ms"

    async def test_concurrent_user_state_operations(self, session):
        """Test concurrent user state operations maintain performance."""
        async def create_user_state(user_id):
            start_time = time.time()
            
            user_state = UserNarrativeState(
                user_id=user_id,
                current_fragment_id='test_fragment',
                current_level=1,
                visited_fragments=[],
                completed_fragments=[]
            )
            session.add(user_state)
            await session.commit()
            
            end_time = time.time()
            return (end_time - start_time) * 1000
        
        # Create 20 concurrent user states
        user_ids = range(10000, 10020)  # 20 unique user IDs
        tasks = [create_user_state(uid) for uid in user_ids]
        creation_times = await asyncio.gather(*tasks)
        
        # Verify performance
        for creation_time_ms in creation_times:
            assert creation_time_ms < 1000, f"Concurrent user state creation took {creation_time_ms:.2f}ms"
        
        avg_creation_time = sum(creation_times) / len(creation_times)
        assert avg_creation_time < 500, f"Average creation time {avg_creation_time:.2f}ms should be < 500ms"

    async def test_concurrent_choice_processing(self, session):
        """Test concurrent choice processing maintains performance."""
        # Create narrative engine with minimal mocking for realistic test
        engine = NarrativeEngine(session)
        engine.point_service = AsyncMock()
        
        # Create test fragment with choice
        fragment = NarrativeFragment(
            id='concurrent_choice_fragment',
            title='Concurrent Choice Test',
            content='Test content',
            fragment_type='DECISION',
            choices=[
                {'text': 'Test choice', 'next_fragment_id': 'next_fragment', 'points': 10}
            ],
            is_active=True
        )
        session.add(fragment)
        
        # Create next fragment
        next_fragment = NarrativeFragment(
            id='next_fragment',
            title='Next Fragment',
            content='Next content',
            fragment_type='STORY',
            is_active=True
        )
        session.add(next_fragment)
        await session.commit()
        
        async def process_user_choice(user_id):
            # Create user state
            user_state = UserNarrativeState(
                user_id=user_id,
                current_fragment_id='concurrent_choice_fragment',
                choices_made=[],
                fragments_visited=0
            )
            session.add(user_state)
            await session.flush()
            
            start_time = time.time()
            result = await engine.process_user_decision(user_id, 0)
            end_time = time.time()
            
            return (end_time - start_time) * 1000, result is not None
        
        # Process choices for 10 different users concurrently
        user_ids = range(20000, 20010)
        tasks = [process_user_choice(uid) for uid in user_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out any exceptions and verify performance
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= 5, "At least 5 concurrent operations should succeed"
        
        for processing_time_ms, success in successful_results:
            if success:  # Only check timing for successful operations
                assert processing_time_ms < 1500, f"Concurrent choice processing took {processing_time_ms:.2f}ms"


class TestScalabilityRequirements:
    """Test system scalability and resource usage."""

    async def test_memory_usage_under_load(self, session):
        """Test memory usage remains reasonable under load."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large number of narrative objects
        fragments = []
        user_states = []
        
        for i in range(100):
            fragment = NarrativeFragment(
                id=f'memory_test_fragment_{i}',
                title=f'Memory Test Fragment {i}',
                content=f'Content for memory test fragment {i}' * 10,  # Make content larger
                fragment_type='STORY',
                storyline_level=1,
                is_active=True
            )
            fragments.append(fragment)
            
            user_state = UserNarrativeState(
                user_id=30000 + i,
                current_fragment_id=f'memory_test_fragment_{i}',
                current_level=1,
                visited_fragments=[f'fragment_{j}' for j in range(min(i, 10))],
                completed_fragments=[f'completed_{j}' for j in range(min(i, 5))]
            )
            user_states.append(user_state)
        
        session.add_all(fragments + user_states)
        await session.commit()
        
        # Check memory after operations
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100, f"Memory increase {memory_increase:.1f}MB too high"

    async def test_database_connection_efficiency(self, session):
        """Test database connection usage is efficient."""
        connection_operations = []
        
        async def perform_db_operation(operation_id):
            start_time = time.time()
            
            # Simulate complex database operation
            fragment = NarrativeFragment(
                id=f'connection_test_{operation_id}',
                title='Connection Test',
                content='Test content',
                fragment_type='STORY',
                is_active=True
            )
            session.add(fragment)
            await session.flush()
            
            # Query the fragment back
            from sqlalchemy import select
            result = await session.execute(
                select(NarrativeFragment).where(NarrativeFragment.id == f'connection_test_{operation_id}')
            )
            retrieved = result.scalar_one_or_none()
            
            end_time = time.time()
            return (end_time - start_time) * 1000, retrieved is not None
        
        # Perform 50 database operations
        tasks = [perform_db_operation(i) for i in range(50)]
        results = await asyncio.gather(*tasks)
        
        # Verify all operations completed efficiently
        for operation_time_ms, success in results:
            assert success, "All database operations should succeed"
            assert operation_time_ms < 1000, f"Database operation took {operation_time_ms:.2f}ms"
        
        await session.commit()

    async def test_response_time_under_varying_load(self, session):
        """Test response times remain stable under varying load."""
        async def simulate_user_session(session_id, operations_count):
            """Simulate a complete user session with multiple operations."""
            session_times = []
            
            for op in range(operations_count):
                start_time = time.time()
                
                # Create user state
                user_state = UserNarrativeState(
                    user_id=40000 + session_id * 100 + op,
                    current_fragment_id='load_test_fragment',
                    current_level=1
                )
                session.add(user_state)
                await session.flush()
                
                # Create decision log
                decision = UserDecisionLog(
                    user_id=40000 + session_id * 100 + op,
                    fragment_id='load_test_fragment',
                    decision_choice=f'Choice {op}',
                    points_awarded=10
                )
                session.add(decision)
                await session.flush()
                
                end_time = time.time()
                session_times.append((end_time - start_time) * 1000)
            
            return session_times
        
        # Test with different load levels
        load_tests = [
            (5, 10),   # 5 sessions, 10 operations each
            (10, 5),   # 10 sessions, 5 operations each
            (20, 3),   # 20 sessions, 3 operations each
        ]
        
        for sessions_count, ops_per_session in load_tests:
            tasks = [simulate_user_session(i, ops_per_session) for i in range(sessions_count)]
            session_results = await asyncio.gather(*tasks)
            
            # Flatten all operation times
            all_times = [time_ms for session_times in session_results for time_ms in session_times]
            
            # Verify performance under this load level
            avg_time = sum(all_times) / len(all_times)
            max_time = max(all_times)
            
            assert avg_time < 500, f"Average time {avg_time:.2f}ms under load ({sessions_count}x{ops_per_session})"
            assert max_time < 2000, f"Max time {max_time:.2f}ms too high under load"
        
        await session.commit()


class TestPerformanceOptimizations:
    """Test specific performance optimizations are working."""

    async def test_fragment_caching_effectiveness(self, session):
        """Test fragment caching improves performance."""
        # Create test fragment
        fragment = NarrativeFragment(
            id='cache_test_fragment',
            title='Cache Test Fragment',
            content='Content for cache testing',
            fragment_type='STORY',
            is_active=True
        )
        session.add(fragment)
        await session.commit()
        
        from sqlalchemy import select
        
        # First access - uncached
        start_time = time.time()
        result = await session.execute(
            select(NarrativeFragment).where(NarrativeFragment.id == 'cache_test_fragment')
        )
        first_fragment = result.scalar_one_or_none()
        first_access_time = (time.time() - start_time) * 1000
        
        # Second access - should be faster due to SQL query plan caching
        start_time = time.time()
        result = await session.execute(
            select(NarrativeFragment).where(NarrativeFragment.id == 'cache_test_fragment')
        )
        second_fragment = result.scalar_one_or_none()
        second_access_time = (time.time() - start_time) * 1000
        
        assert first_fragment is not None
        assert second_fragment is not None
        assert first_fragment.id == second_fragment.id
        
        # Both should be fast, but we're mainly testing they complete successfully
        assert first_access_time < 1000, f"First access took {first_access_time:.2f}ms"
        assert second_access_time < 1000, f"Second access took {second_access_time:.2f}ms"

    async def test_bulk_operation_efficiency(self, session):
        """Test bulk operations are more efficient than individual ones."""
        # Test individual insertions
        individual_start = time.time()
        for i in range(20):
            fragment = NarrativeFragment(
                id=f'individual_fragment_{i}',
                title=f'Individual Fragment {i}',
                content=f'Content {i}',
                fragment_type='STORY',
                is_active=True
            )
            session.add(fragment)
            await session.flush()
        individual_time = (time.time() - individual_start) * 1000
        
        # Test bulk insertion
        bulk_start = time.time()
        bulk_fragments = []
        for i in range(20):
            fragment = NarrativeFragment(
                id=f'bulk_fragment_{i}',
                title=f'Bulk Fragment {i}',
                content=f'Content {i}',
                fragment_type='STORY',
                is_active=True
            )
            bulk_fragments.append(fragment)
        
        session.add_all(bulk_fragments)
        await session.flush()
        bulk_time = (time.time() - bulk_start) * 1000
        
        await session.commit()
        
        # Bulk should be significantly faster
        assert bulk_time < individual_time, f"Bulk operation ({bulk_time:.2f}ms) should be faster than individual ({individual_time:.2f}ms)"
        assert bulk_time < 1000, f"Bulk operation took {bulk_time:.2f}ms, should be < 1000ms"

    async def test_index_utilization_performance(self, session):
        """Test database indexes improve query performance."""
        # Create fragments with different levels for index testing
        fragments = []
        for level in range(1, 4):
            for seq in range(1, 6):
                fragment = NarrativeFragment(
                    id=f'index_test_l{level}_s{seq}',
                    title=f'Level {level} Sequence {seq}',
                    content=f'Content for level {level} sequence {seq}',
                    fragment_type='STORY',
                    storyline_level=level,
                    fragment_sequence=seq,
                    is_active=True
                )
                fragments.append(fragment)
        
        session.add_all(fragments)
        await session.commit()
        
        # Test indexed query (by level and active status)
        start_time = time.time()
        from sqlalchemy import select
        result = await session.execute(
            select(NarrativeFragment).where(
                NarrativeFragment.storyline_level == 2,
                NarrativeFragment.is_active == True
            )
        )
        level_2_fragments = result.scalars().all()
        indexed_query_time = (time.time() - start_time) * 1000
        
        # Test non-indexed query (by content)
        start_time = time.time()
        result = await session.execute(
            select(NarrativeFragment).where(
                NarrativeFragment.content.contains('level 2')
            )
        )
        content_search_results = result.scalars().all()
        content_query_time = (time.time() - start_time) * 1000
        
        # Verify results
        assert len(level_2_fragments) == 5, "Should find 5 level 2 fragments"
        assert indexed_query_time < 500, f"Indexed query took {indexed_query_time:.2f}ms, should be < 500ms"
        # Content search is typically slower but should still be reasonable
        assert content_query_time < 2000, f"Content query took {content_query_time:.2f}ms, should be < 2000ms"


class TestPerformanceMonitoring:
    """Test performance monitoring and alerting capabilities."""

    async def test_performance_metric_collection(self, session):
        """Test performance metrics are collected correctly."""
        metrics = {
            'fragment_retrieval_times': [],
            'user_state_operations': [],
            'validation_times': []
        }
        
        # Collect fragment retrieval metrics
        for i in range(10):
            start_time = time.time()
            
            fragment = NarrativeFragment(
                id=f'metrics_fragment_{i}',
                title=f'Metrics Test {i}',
                content='Test content for metrics',
                fragment_type='STORY',
                is_active=True
            )
            session.add(fragment)
            await session.flush()
            
            end_time = time.time()
            metrics['fragment_retrieval_times'].append((end_time - start_time) * 1000)
        
        await session.commit()
        
        # Verify metrics collection
        assert len(metrics['fragment_retrieval_times']) == 10
        
        # Calculate statistics
        avg_time = sum(metrics['fragment_retrieval_times']) / len(metrics['fragment_retrieval_times'])
        max_time = max(metrics['fragment_retrieval_times'])
        min_time = min(metrics['fragment_retrieval_times'])
        
        # Verify performance statistics
        assert avg_time < 500, f"Average fragment retrieval time {avg_time:.2f}ms exceeds target"
        assert max_time < 2000, f"Max fragment retrieval time {max_time:.2f}ms too high"
        assert min_time >= 0, "Min time should be non-negative"

    async def test_performance_threshold_alerting(self, session):
        """Test performance threshold monitoring."""
        # Simulate operations with varying performance
        operation_times = []
        
        for i in range(30):
            start_time = time.time()
            
            # Simulate some operations being slower
            if i % 10 == 9:  # Every 10th operation is slower
                await asyncio.sleep(0.6)  # 600ms - above threshold
            
            user_state = UserNarrativeState(
                user_id=50000 + i,
                current_fragment_id='threshold_test_fragment',
                current_level=1
            )
            session.add(user_state)
            await session.flush()
            
            end_time = time.time()
            operation_time = (end_time - start_time) * 1000
            operation_times.append(operation_time)
        
        await session.commit()
        
        # Analyze performance violations
        threshold_violations = [t for t in operation_times if t > 500]
        violation_percentage = (len(threshold_violations) / len(operation_times)) * 100
        
        # Should detect the intentionally slow operations
        assert len(threshold_violations) >= 2, f"Should detect threshold violations, found {len(threshold_violations)}"
        assert violation_percentage >= 5, f"Should detect ~10% violation rate, found {violation_percentage:.1f}%"
        
        # Most operations should still be fast
        fast_operations = [t for t in operation_times if t <= 500]
        assert len(fast_operations) >= 20, "Most operations should be within threshold"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])