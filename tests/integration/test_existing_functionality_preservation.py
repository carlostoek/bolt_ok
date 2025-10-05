"""
Comprehensive integration tests to ensure existing functionality is preserved
during emotional evaluation system integration.

These tests verify that ALL existing features work exactly as before.
"""
import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from services.coordinador_central import CoordinadorCentral, AccionUsuario
from services.integration.emotional_coordinator import EmotionalCoordinator
from services.emotional.emotional_analysis_service import EmotionalAnalysisService
from database.models import User, ButtonReaction, UserStats, NarrativeFragment
from tests.conftest import create_test_session, create_test_user


class TestExistingFunctionalityPreservation:
    """Test suite ensuring existing functionality remains unchanged"""
    
    async def test_reaction_flow_preservation(self):
        """Verify reaction handling works identically with and without emotional system"""
        async with create_test_session() as session:
            # Setup test data
            user = await create_test_user(session, user_id=12345)
            
            # Test original reaction flow
            coordinador = CoordinadorCentral(session)
            original_result = await coordinador.ejecutar_flujo(
                user.id,
                AccionUsuario.REACCIONAR_PUBLICACION,
                message_id=123,
                channel_id=456,
                reaction_type="❤️",
                bot=AsyncMock()
            )
            
            # Test with emotional system enabled
            emotional_coordinator = EmotionalCoordinator(coordinador)
            enhanced_result = await emotional_coordinator.execute_emotional_flow(
                user.id,
                AccionUsuario.REACCIONAR_PUBLICACION,
                message_id=123,
                channel_id=456,
                reaction_type="❤️",
                bot=AsyncMock()
            )
            
            # Core functionality MUST be identical
            assert original_result["success"] == enhanced_result["success"]
            assert original_result["points_awarded"] == enhanced_result["points_awarded"]
            assert original_result["action"] == enhanced_result["action"]
            
            # Verify database state is consistent
            user_reactions_count = await self._count_user_reactions(session, user.id)
            assert user_reactions_count == 1  # Should be same regardless of emotional system

    async def test_narrative_progression_integrity(self):
        """Ensure narrative progression works exactly as before"""
        async with create_test_session() as session:
            user = await create_test_user(session, user_id=67890)
            
            # Test original narrative decision flow
            coordinador = CoordinadorCentral(session)
            original_result = await coordinador.ejecutar_flujo(
                user.id,
                AccionUsuario.TOMAR_DECISION,
                choice_index=0,
                bot=AsyncMock()
            )
            
            # Reset user state for second test
            await self._reset_user_narrative_state(session, user.id)
            
            # Test with emotional enhancement
            emotional_coordinator = EmotionalCoordinator(coordinador)
            enhanced_result = await emotional_coordinator.execute_emotional_flow(
                user.id,
                AccionUsuario.TOMAR_DECISION,
                choice_index=0,
                bot=AsyncMock()
            )
            
            # Narrative progression must be identical
            if original_result["success"]:
                assert enhanced_result["success"] == True
                # Fragment progression should be the same
                assert original_result["fragment"]["id"] == enhanced_result["fragment"]["id"]
            else:
                # If original failed, enhanced should fail in same way
                assert enhanced_result["success"] == False
                assert enhanced_result["action"] == original_result["action"]

    async def test_vip_access_control_unchanged(self):
        """Verify VIP access control works identically"""
        async with create_test_session() as session:
            # Test with non-VIP user
            user = await create_test_user(session, user_id=11111, role="free")
            
            coordinador = CoordinadorCentral(session)
            original_result = await coordinador.ejecutar_flujo(
                user.id,
                AccionUsuario.ACCEDER_NARRATIVA_VIP,
                fragment_key="level4_secreto",
                bot=AsyncMock()
            )
            
            emotional_coordinator = EmotionalCoordinator(coordinador)
            enhanced_result = await emotional_coordinator.execute_emotional_flow(
                user.id,
                AccionUsuario.ACCEDER_NARRATIVA_VIP,
                fragment_key="level4_secreto",
                bot=AsyncMock()
            )
            
            # Access control must be identical
            assert original_result["success"] == enhanced_result["success"]
            assert original_result["action"] == enhanced_result["action"]
            
            # Both should deny access
            assert original_result["success"] == False
            assert enhanced_result["success"] == False
            assert "vip_required" in enhanced_result["action"]

    async def test_points_system_integrity(self):
        """Ensure points are awarded consistently"""
        async with create_test_session() as session:
            user = await create_test_user(session, user_id=22222)
            initial_points = user.points
            
            # Test channel participation points
            coordinador = CoordinadorCentral(session)
            original_result = await coordinador.ejecutar_flujo(
                user.id,
                AccionUsuario.PARTICIPAR_CANAL,
                channel_id=789,
                action_type="post",
                bot=AsyncMock()
            )
            
            # Get points after original flow
            await session.refresh(user)
            points_after_original = user.points
            points_gained_original = points_after_original - initial_points
            
            # Reset points for second test
            user.points = initial_points
            await session.commit()
            
            # Test with emotional system
            emotional_coordinator = EmotionalCoordinator(coordinador)
            enhanced_result = await emotional_coordinator.execute_emotional_flow(
                user.id,
                AccionUsuario.PARTICIPAR_CANAL,
                channel_id=789,
                action_type="post",
                bot=AsyncMock()
            )
            
            await session.refresh(user)
            points_after_enhanced = user.points
            points_gained_enhanced = points_after_enhanced - initial_points
            
            # Points system must be identical
            assert points_gained_original == points_gained_enhanced
            assert original_result["points_awarded"] == enhanced_result["points_awarded"]

    async def test_error_handling_consistency(self):
        """Verify error handling behaves identically"""
        async with create_test_session() as session:
            user = await create_test_user(session, user_id=33333)
            
            # Test with invalid decision (should fail)
            coordinador = CoordinadorCentral(session)
            
            try:
                original_result = await coordinador.ejecutar_flujo(
                    user.id,
                    AccionUsuario.TOMAR_DECISION,
                    choice_index=999,  # Invalid choice
                    bot=AsyncMock()
                )
            except Exception as e:
                original_error = str(e)
                original_result = {"success": False, "error": original_error}
            
            # Test same error with emotional system
            emotional_coordinator = EmotionalCoordinator(coordinador)
            
            try:
                enhanced_result = await emotional_coordinator.execute_emotional_flow(
                    user.id,
                    AccionUsuario.TOMAR_DECISION,
                    choice_index=999,  # Invalid choice
                    bot=AsyncMock()
                )
            except Exception as e:
                enhanced_error = str(e)
                enhanced_result = {"success": False, "error": enhanced_error}
            
            # Error handling should be consistent
            assert original_result["success"] == enhanced_result["success"]
            assert original_result["success"] == False

    async def test_daily_engagement_flow_preservation(self):
        """Verify daily engagement checking works identically"""
        async with create_test_session() as session:
            user = await create_test_user(session, user_id=44444)
            
            # Test original daily engagement
            coordinador = CoordinadorCentral(session)
            original_result = await coordinador.ejecutar_flujo(
                user.id,
                AccionUsuario.VERIFICAR_ENGAGEMENT,
                bot=AsyncMock()
            )
            
            # Get user stats after original flow
            user_stats = await self._get_user_stats(session, user.id)
            original_checkin_time = user_stats.last_checkin_at if user_stats else None
            
            # Reset for second test (simulate different day)
            if user_stats:
                user_stats.last_checkin_at = datetime.now() - timedelta(days=1)
                await session.commit()
            
            # Test with emotional system
            emotional_coordinator = EmotionalCoordinator(coordinador)
            enhanced_result = await emotional_coordinator.execute_emotional_flow(
                user.id,
                AccionUsuario.VERIFICAR_ENGAGEMENT,
                bot=AsyncMock()
            )
            
            # Daily engagement behavior must be identical
            if original_result["success"]:
                assert enhanced_result["success"] == True
                assert enhanced_result["points_awarded"] == original_result["points_awarded"]
            else:
                assert enhanced_result["success"] == False
                assert enhanced_result["action"] == original_result["action"]

    # Helper methods
    async def _count_user_reactions(self, session: AsyncSession, user_id: int) -> int:
        """Count user reactions in database"""
        from sqlalchemy import select, func
        result = await session.execute(
            select(func.count(ButtonReaction.id)).where(ButtonReaction.user_id == user_id)
        )
        return result.scalar() or 0

    async def _reset_user_narrative_state(self, session: AsyncSession, user_id: int):
        """Reset user narrative state for testing"""
        from database.models.narrative import UserStoryState
        from sqlalchemy import select, delete
        
        # Remove existing state
        await session.execute(
            delete(UserStoryState).where(UserStoryState.user_id == user_id)
        )
        await session.commit()

    async def _get_user_stats(self, session: AsyncSession, user_id: int):
        """Get user stats from database"""
        return await session.get(UserStats, user_id)


class TestPerformanceImpactLimits:
    """Test that performance impact stays within acceptable limits"""
    
    async def test_response_time_impact_under_10_percent(self):
        """Verify response time increase is less than 10%"""
        async with create_test_session() as session:
            user = await create_test_user(session, user_id=55555)
            
            # Measure baseline performance
            coordinador = CoordinadorCentral(session)
            baseline_times = []
            
            for _ in range(10):  # Run multiple times for average
                start_time = time.time()
                await coordinador.ejecutar_flujo(
                    user.id,
                    AccionUsuario.REACCIONAR_PUBLICACION,
                    message_id=123,
                    channel_id=456,
                    reaction_type="👍",
                    bot=AsyncMock()
                )
                baseline_times.append(time.time() - start_time)
            
            baseline_avg = sum(baseline_times) / len(baseline_times)
            
            # Measure performance with emotional system
            emotional_coordinator = EmotionalCoordinator(coordinador)
            enhanced_times = []
            
            for _ in range(10):
                start_time = time.time()
                await emotional_coordinator.execute_emotional_flow(
                    user.id,
                    AccionUsuario.REACCIONAR_PUBLICACION,
                    message_id=123,
                    channel_id=456,
                    reaction_type="👍",
                    bot=AsyncMock()
                )
                enhanced_times.append(time.time() - start_time)
            
            enhanced_avg = sum(enhanced_times) / len(enhanced_times)
            
            # Calculate performance impact
            impact_percentage = ((enhanced_avg - baseline_avg) / baseline_avg) * 100
            
            # Performance impact must be less than 10%
            assert impact_percentage < 10, f"Performance impact {impact_percentage:.2f}% exceeds 10% limit"

    async def test_memory_usage_remains_stable(self):
        """Verify memory usage doesn't increase significantly"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        async with create_test_session() as session:
            user = await create_test_user(session, user_id=66666)
            
            # Measure baseline memory
            baseline_memory = process.memory_info().rss
            
            # Run operations with emotional system
            emotional_coordinator = EmotionalCoordinator(CoordinadorCentral(session))
            
            for _ in range(100):  # Simulate load
                await emotional_coordinator.execute_emotional_flow(
                    user.id,
                    AccionUsuario.REACCIONAR_PUBLICACION,
                    message_id=123,
                    channel_id=456,
                    reaction_type="❤️",
                    bot=AsyncMock()
                )
            
            # Measure memory after operations
            final_memory = process.memory_info().rss
            memory_increase = final_memory - baseline_memory
            memory_increase_mb = memory_increase / (1024 * 1024)
            
            # Memory increase should be reasonable (less than 50MB for this test)
            assert memory_increase_mb < 50, f"Memory increase {memory_increase_mb:.2f}MB is too high"


class TestRollbackCapabilities:
    """Test that rollback mechanisms work correctly"""
    
    async def test_feature_flag_disable_immediate_effect(self):
        """Test that disabling feature flags immediately disables emotional features"""
        async with create_test_session() as session:
            user = await create_test_user(session, user_id=77777)
            
            # Enable emotional features
            with patch('services.emotional.feature_flags.EmotionalFeatureFlags.is_enabled', return_value=True):
                emotional_coordinator = EmotionalCoordinator(CoordinadorCentral(session))
                result_enabled = await emotional_coordinator.execute_emotional_flow(
                    user.id,
                    AccionUsuario.REACCIONAR_PUBLICACION,
                    message_id=123,
                    channel_id=456,
                    reaction_type="💖",
                    bot=AsyncMock()
                )
            
            # Disable emotional features
            with patch('services.emotional.feature_flags.EmotionalFeatureFlags.is_enabled', return_value=False):
                emotional_coordinator = EmotionalCoordinator(CoordinadorCentral(session))
                result_disabled = await emotional_coordinator.execute_emotional_flow(
                    user.id,
                    AccionUsuario.REACCIONAR_PUBLICACION,
                    message_id=124,
                    channel_id=456,
                    reaction_type="💖",
                    bot=AsyncMock()
                )
            
            # With features disabled, should behave like original system
            assert result_disabled["success"] == True
            # Should not have emotional enhancements when disabled
            assert "emotional_context" not in result_disabled

    async def test_circuit_breaker_functionality(self):
        """Test that circuit breaker protects core functionality"""
        async with create_test_session() as session:
            user = await create_test_user(session, user_id=88888)
            
            # Mock emotional service to always fail
            with patch.object(EmotionalAnalysisService, 'analyze_interaction', side_effect=Exception("Service down")):
                emotional_coordinator = EmotionalCoordinator(CoordinadorCentral(session))
                
                # Even with emotional service failing, core functionality should work
                result = await emotional_coordinator.execute_emotional_flow(
                    user.id,
                    AccionUsuario.REACCIONAR_PUBLICACION,
                    message_id=125,
                    channel_id=456,
                    reaction_type="🔥",
                    bot=AsyncMock()
                )
                
                # Core functionality should still succeed
                assert result["success"] == True
                assert result["points_awarded"] == 10  # Standard points
                
                # Should have fallback behavior, not emotional enhancements
                assert "emotional_context" not in result or result["emotional_context"] is None


@pytest.mark.integration
class TestEndToEndIntegrationScenarios:
    """Test complete user journey scenarios"""
    
    async def test_complete_user_journey_unchanged(self):
        """Test that complete user journeys work identically"""
        async with create_test_session() as session:
            user = await create_test_user(session, user_id=99999)
            
            # Simulate complete user session: reaction -> narrative -> vip attempt -> daily check
            coordinador = CoordinadorCentral(session)
            emotional_coordinator = EmotionalCoordinator(coordinador)
            
            # Original journey
            original_journey_results = []
            
            # 1. React to post
            result1 = await coordinador.ejecutar_flujo(
                user.id, AccionUsuario.REACCIONAR_PUBLICACION,
                message_id=200, channel_id=500, reaction_type="❤️", bot=AsyncMock()
            )
            original_journey_results.append(result1)
            
            # 2. Make narrative decision
            result2 = await coordinador.ejecutar_flujo(
                user.id, AccionUsuario.TOMAR_DECISION,
                choice_index=0, bot=AsyncMock()
            )
            original_journey_results.append(result2)
            
            # 3. Try VIP access
            result3 = await coordinador.ejecutar_flujo(
                user.id, AccionUsuario.ACCEDER_NARRATIVA_VIP,
                fragment_key="level4_test", bot=AsyncMock()
            )
            original_journey_results.append(result3)
            
            # 4. Daily engagement check
            result4 = await coordinador.ejecutar_flujo(
                user.id, AccionUsuario.VERIFICAR_ENGAGEMENT, bot=AsyncMock()
            )
            original_journey_results.append(result4)
            
            # Reset user state for enhanced journey
            await self._reset_complete_user_state(session, user.id)
            
            # Enhanced journey with emotional system
            enhanced_journey_results = []
            
            # Same sequence with emotional enhancements
            result1e = await emotional_coordinator.execute_emotional_flow(
                user.id, AccionUsuario.REACCIONAR_PUBLICACION,
                message_id=200, channel_id=500, reaction_type="❤️", bot=AsyncMock()
            )
            enhanced_journey_results.append(result1e)
            
            result2e = await emotional_coordinator.execute_emotional_flow(
                user.id, AccionUsuario.TOMAR_DECISION,
                choice_index=0, bot=AsyncMock()
            )
            enhanced_journey_results.append(result2e)
            
            result3e = await emotional_coordinator.execute_emotional_flow(
                user.id, AccionUsuario.ACCEDER_NARRATIVA_VIP,
                fragment_key="level4_test", bot=AsyncMock()
            )
            enhanced_journey_results.append(result3e)
            
            result4e = await emotional_coordinator.execute_emotional_flow(
                user.id, AccionUsuario.VERIFICAR_ENGAGEMENT, bot=AsyncMock()
            )
            enhanced_journey_results.append(result4e)
            
            # Verify journey outcomes are identical
            for i, (original, enhanced) in enumerate(zip(original_journey_results, enhanced_journey_results)):
                assert original["success"] == enhanced["success"], f"Step {i+1} success differs"
                if original["success"] and enhanced["success"]:
                    # Core results should be identical
                    assert original.get("points_awarded", 0) == enhanced.get("points_awarded", 0), f"Step {i+1} points differ"
                    assert original["action"] == enhanced["action"], f"Step {i+1} action differs"

    async def _reset_complete_user_state(self, session: AsyncSession, user_id: int):
        """Reset all user state for testing"""
        user = await session.get(User, user_id)
        if user:
            user.points = 0
            user.menu_state = "root"
            
        # Reset narrative state
        await self._reset_user_narrative_state(session, user_id)
        
        # Reset user stats
        user_stats = await session.get(UserStats, user_id)
        if user_stats:
            user_stats.last_checkin_at = None
            user_stats.checkin_streak = 0
            
        await session.commit()

    async def _reset_user_narrative_state(self, session: AsyncSession, user_id: int):
        """Reset user narrative state"""
        from database.models.narrative import UserStoryState
        from sqlalchemy import delete
        
        await session.execute(
            delete(UserStoryState).where(UserStoryState.user_id == user_id)
        )
        await session.commit()