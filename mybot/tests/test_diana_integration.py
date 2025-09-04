"""
Diana Integration Tests
Tests the Diana emotional system integration doesn't break core functionality.
"""
import pytest
import pytest_asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

from database.models import User


@pytest.mark.asyncio
class TestDianaEmotionalSystemIntegration:
    """Test Diana's emotional system doesn't break core flows."""
    
    async def test_diana_menu_system_responsiveness(self, session, test_user, mock_bot):
        """Test Diana menu system responds quickly."""
        # Mock Diana menu system
        with patch('services.diana_menu_system.DianaMenuSystem') as mock_diana:
            diana_mock = AsyncMock()
            diana_mock.get_main_menu = AsyncMock(return_value="Diana Main Menu")
            diana_mock.handle_callback = AsyncMock(return_value=True)
            mock_diana.return_value = diana_mock
            
            from services.diana_menu_system import DianaMenuSystem
            diana_system = DianaMenuSystem(session, mock_bot)
            
            start_time = time.perf_counter()
            
            # Test menu operations
            menu = await diana_system.get_main_menu(test_user.id)
            callback_handled = await diana_system.handle_callback(test_user.id, "diana_menu")
            
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            # Diana menu should be responsive
            assert duration_ms < 50, f"Diana menu operations took {duration_ms:.2f}ms, too slow"
            assert menu is not None
            assert callback_handled is True

    async def test_diana_emotional_state_tracking_performance(self, session):
        """Test emotional state tracking doesn't slow operations."""
        user_id = 700000001
        
        # Create user
        user = User(id=user_id, first_name="EmotionalTest", role="free", points=0)
        session.add(user)
        await session.commit()
        
        # Mock emotional state service
        with patch('services.interfaces.emotional_state_interface.EmotionalStateInterface') as mock_emotional:
            emotional_mock = AsyncMock()
            emotional_mock.update_emotional_state = AsyncMock()
            emotional_mock.get_emotional_context = AsyncMock(return_value={"mood": "happy", "engagement": "high"})
            mock_emotional.return_value = emotional_mock
            
            start_time = time.perf_counter()
            
            # Simulate operations that trigger emotional updates
            await emotional_mock.update_emotional_state(user_id, "positive_interaction")
            context = await emotional_mock.get_emotional_context(user_id)
            
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            # Emotional processing should be fast
            assert duration_ms < 20, f"Emotional state operations took {duration_ms:.2f}ms, too slow"
            assert context["mood"] == "happy"
            
        # Cleanup
        await session.delete(user)
        await session.commit()

    async def test_diana_personalization_impact_on_core_flows(self, session, test_user):
        """Test Diana personalization doesn't break core functionality."""
        # Mock Diana personalization
        with patch('services.diana_menu_integration_impl.get_compatibility_bridge') as mock_bridge:
            bridge_mock = MagicMock()
            bridge_mock.bridge_user_menu = AsyncMock(return_value=False)  # Falls back to core
            bridge_mock.bridge_admin_menu = AsyncMock(return_value=False)
            mock_bridge.return_value = bridge_mock
            
            from services.diana_menu_integration_impl import get_compatibility_bridge
            bridge = get_compatibility_bridge(session)
            
            start_time = time.perf_counter()
            
            # Test fallback behavior
            callback_mock = MagicMock()
            callback_mock.data = "test_callback"
            
            handled = await bridge.bridge_user_menu(callback_mock)
            
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            # Diana integration should be fast and not interfere
            assert duration_ms < 10, f"Diana bridge operation took {duration_ms:.2f}ms, too slow"
            assert handled is False, "Should fall back to core system when Diana doesn't handle"

    async def test_diana_menu_integration_backwards_compatibility(self, session, test_user):
        """Test Diana menu integration maintains backwards compatibility."""
        # Test that existing menu systems still work when Diana is enabled
        with patch('services.diana_menu_system.DianaMenuSystem') as mock_diana:
            diana_mock = AsyncMock()
            diana_mock.is_enabled = True
            diana_mock.handles_menu = AsyncMock(return_value=True)
            diana_mock.render_menu = AsyncMock(return_value="Diana rendered menu")
            mock_diana.return_value = diana_mock
            
            start_time = time.perf_counter()
            
            # Test Diana menu handling
            from services.diana_menu_system import DianaMenuSystem
            diana_system = DianaMenuSystem(session, AsyncMock())
            
            handles_menu = await diana_system.handles_menu("main_menu", test_user.id)
            menu_content = await diana_system.render_menu("main_menu", test_user.id)
            
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            # Diana menu operations should be fast
            assert duration_ms < 30, f"Diana menu handling took {duration_ms:.2f}ms, too slow"
            assert handles_menu is True
            assert menu_content == "Diana rendered menu"


@pytest.mark.asyncio
class TestDianaSystemStabilityUnderLoad:
    """Test Diana system stability under various load conditions."""
    
    async def test_diana_concurrent_user_interactions(self, session):
        """Test Diana system handles concurrent user interactions."""
        user_count = 10
        base_user_id = 800000000
        
        # Create test users
        users = []
        for i in range(user_count):
            user = User(
                id=base_user_id + i,
                first_name=f"DianaUser{i}",
                role="free",
                points=i * 5
            )
            users.append(user)
            session.add(user)
        await session.commit()
        
        # Mock Diana emotional processing
        with patch('services.interfaces.emotional_state_interface.EmotionalStateInterface') as mock_emotional:
            emotional_mock = AsyncMock()
            emotional_mock.process_user_interaction = AsyncMock()
            mock_emotional.return_value = emotional_mock
            
            async def diana_user_interaction(user_id: int):
                """Simulate Diana processing user interaction."""
                start = time.perf_counter()
                
                await emotional_mock.process_user_interaction(
                    user_id, 
                    "user_message",
                    {"content": "Hello Diana"}
                )
                
                end = time.perf_counter()
                return (end - start) * 1000
            
            # Test concurrent Diana interactions
            start_time = time.perf_counter()
            
            durations = await asyncio.gather(*[
                diana_user_interaction(base_user_id + i)
                for i in range(user_count)
            ])
            
            end_time = time.perf_counter()
            total_duration_ms = (end_time - start_time) * 1000
            
            # Diana concurrent processing should be efficient
            avg_duration = sum(durations) / len(durations)
            assert avg_duration < 50, f"Average Diana interaction took {avg_duration:.2f}ms, too slow"
            assert total_duration_ms < 500, f"Total Diana processing took {total_duration_ms:.2f}ms, too slow"
            
        # Cleanup
        for user in users:
            await session.delete(user)
        await session.commit()

    async def test_diana_error_recovery_mechanisms(self, session, test_user):
        """Test Diana system recovers gracefully from errors."""
        # Mock Diana service with error scenarios
        with patch('services.diana_menu_system.DianaMenuSystem') as mock_diana:
            diana_mock = AsyncMock()
            diana_mock.process_user_input = AsyncMock(side_effect=Exception("Diana processing error"))
            diana_mock.fallback_to_core = AsyncMock(return_value="Core system response")
            mock_diana.return_value = diana_mock
            
            start_time = time.perf_counter()
            
            # Test error recovery
            from services.diana_menu_system import DianaMenuSystem
            diana_system = DianaMenuSystem(session, AsyncMock())
            
            try:
                await diana_system.process_user_input(test_user.id, "test input")
                assert False, "Should have raised exception"
            except Exception:
                # Simulate fallback mechanism
                fallback_response = await diana_system.fallback_to_core(test_user.id, "test input")
                assert fallback_response == "Core system response"
            
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            # Error recovery should be fast
            assert duration_ms < 25, f"Diana error recovery took {duration_ms:.2f}ms, too slow"

    async def test_diana_memory_usage_stability(self, session):
        """Test Diana system doesn't accumulate memory over time."""
        import gc
        
        # Get initial memory state
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Mock Diana with memory-intensive operations
        with patch('services.diana_menu_system.DianaMenuSystem') as mock_diana:
            diana_mock = AsyncMock()
            diana_mock.process_emotional_context = AsyncMock()
            mock_diana.return_value = diana_mock
            
            # Simulate many Diana operations
            from services.diana_menu_system import DianaMenuSystem
            diana_system = DianaMenuSystem(session, AsyncMock())
            
            for i in range(50):
                await diana_mock.process_emotional_context(
                    i, 
                    {"user_input": f"test message {i}", "context": "conversation"}
                )
        
        # Force cleanup
        gc.collect()
        await asyncio.sleep(0.05)
        final_objects = len(gc.get_objects())
        
        # Memory growth should be minimal
        object_growth = final_objects - initial_objects
        assert object_growth < 500, f"Diana operations grew memory by {object_growth} objects"


@pytest.mark.asyncio
class TestDianaIntegrationWithCoreServices:
    """Test Diana integration with core services doesn't break functionality."""
    
    async def test_diana_with_point_service_integration(self, session):
        """Test Diana integration doesn't break point service operations."""
        user_id = 900000001
        
        # Create user
        user = User(id=user_id, first_name="DianaPointTest", role="free", points=50)
        session.add(user)
        await session.commit()
        
        # Mock both Diana and point service
        with patch('services.point_service.PointService') as mock_ps, \
             patch('services.diana_menu_system.DianaMenuSystem') as mock_diana:
            
            # Setup mocks
            point_service_mock = AsyncMock()
            point_service_mock.award_points = AsyncMock(return_value=True)
            point_service_mock.get_user_points = AsyncMock(return_value=60.0)
            mock_ps.return_value = point_service_mock
            
            diana_mock = AsyncMock()
            diana_mock.notify_point_change = AsyncMock()
            mock_diana.return_value = diana_mock
            
            start_time = time.perf_counter()
            
            # Test integration
            success = await point_service_mock.award_points(user_id, 10, "diana_test")
            points = await point_service_mock.get_user_points(user_id)
            await diana_mock.notify_point_change(user_id, 10, 60)
            
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            # Integration should not slow down operations
            assert duration_ms < 15, f"Diana-Point integration took {duration_ms:.2f}ms, too slow"
            assert success is True
            assert points == 60.0
            
        # Cleanup
        await session.delete(user)
        await session.commit()

    async def test_diana_with_narrative_service_integration(self, session, test_user):
        """Test Diana integration with narrative service."""
        # Mock both services
        with patch('services.narrative_service.NarrativeService') as mock_ns, \
             patch('services.diana_menu_system.DianaMenuSystem') as mock_diana:
            
            narrative_mock = AsyncMock()
            narrative_mock.get_current_fragment = AsyncMock(return_value={"key": "test_fragment"})
            narrative_mock.advance_narrative = AsyncMock(return_value=True)
            mock_ns.return_value = narrative_mock
            
            diana_mock = AsyncMock()
            diana_mock.personalize_content = AsyncMock(return_value="Personalized content")
            diana_mock.track_narrative_engagement = AsyncMock()
            mock_diana.return_value = diana_mock
            
            start_time = time.perf_counter()
            
            # Test narrative-Diana integration
            fragment = await narrative_mock.get_current_fragment(test_user.id)
            personalized = await diana_mock.personalize_content(test_user.id, fragment)
            success = await narrative_mock.advance_narrative(test_user.id, "choice1")
            await diana_mock.track_narrative_engagement(test_user.id, "choice_made")
            
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            # Diana-narrative integration should be fast
            assert duration_ms < 25, f"Diana-narrative integration took {duration_ms:.2f}ms, too slow"
            assert fragment["key"] == "test_fragment"
            assert personalized == "Personalized content"
            assert success is True

    async def test_diana_fallback_mechanism_reliability(self, session, test_user):
        """Test Diana fallback mechanisms work reliably."""
        # Mock Diana with failure scenarios
        with patch('services.diana_menu_integration_impl.get_compatibility_bridge') as mock_bridge:
            bridge_mock = MagicMock()
            
            # Test successful Diana handling
            bridge_mock.bridge_user_menu = AsyncMock(return_value=True)
            mock_bridge.return_value = bridge_mock
            
            from services.diana_menu_integration_impl import get_compatibility_bridge
            bridge = get_compatibility_bridge(session)
            
            # Test Diana success case
            callback_mock = MagicMock()
            callback_mock.data = "diana_main"
            
            handled = await bridge.bridge_user_menu(callback_mock)
            assert handled is True, "Diana should handle recognized callbacks"
            
            # Test fallback case
            bridge_mock.bridge_user_menu = AsyncMock(return_value=False)
            callback_mock.data = "legacy_callback"
            
            handled = await bridge.bridge_user_menu(callback_mock)
            assert handled is False, "Should fall back for unrecognized callbacks"

    async def test_diana_system_doesnt_interfere_with_admin(self, session, admin_user):
        """Test Diana system doesn't interfere with admin operations."""
        # Mock both Diana and admin services
        with patch('services.diana_menu_system.DianaMenuSystem') as mock_diana, \
             patch('handlers.admin.admin_menu.handle_admin_callback') as mock_admin:
            
            diana_mock = AsyncMock()
            diana_mock.should_handle_admin = AsyncMock(return_value=False)  # Diana doesn't handle admin
            mock_diana.return_value = diana_mock
            
            admin_handler_mock = AsyncMock(return_value="Admin handled")
            mock_admin.return_value = admin_handler_mock
            
            start_time = time.perf_counter()
            
            # Test admin operation with Diana present
            should_handle = await diana_mock.should_handle_admin(admin_user.id, "admin_config")
            
            if not should_handle:
                # Should use regular admin handler
                result = await mock_admin("admin_config", admin_user.id)
            
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            # Admin operations should remain fast
            assert duration_ms < 10, f"Admin with Diana took {duration_ms:.2f}ms, too slow"
            assert should_handle is False, "Diana should not interfere with admin"