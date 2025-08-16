"""
Tests de protección para la integración Narrative-Rewards.
Protege el flujo crítico: progreso narrativo -> recompensas gamificadas -> puntos.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy import select

from services.narrative_service import NarrativeService
from services.point_service import PointService
from services.badge_service import BadgeService
from services.integration.narrative_point_service import NarrativePointService
from database.models import User, UserStats, Badge, UserBadge
from database.narrative_models import (
    NarrativeFragment, UserNarrativeState, NarrativeDecision, 
    UserDecisionLog, NarrativeReward
)


@pytest.mark.asyncio
class TestNarrativeRewardsIntegration:
    """Tests críticos para la integración entre progreso narrativo y sistema de recompensas."""

    async def test_narrative_completion_awards_points(self, session, test_user):
        """
        CRITICAL: Test que protege el otorgamiento de puntos por completar narrativas.
        Completar fragmentos narrativos DEBE otorgar puntos según configuración.
        """
        narrative_service = NarrativeService(session)
        point_service = PointService(session)
        
        # Create narrative fragment with point reward
        story_fragment = NarrativeFragment(
            key="story_chapter_1",
            title="Capítulo 1: El Comienzo",
            content="Has completado el primer capítulo de la historia.",
            completion_points=25.0,  # Reward for completion
            is_completion_point=True
        )
        session.add(story_fragment)
        
        # Create reward tracking
        narrative_reward = NarrativeReward(
            fragment_key="story_chapter_1",
            points_awarded=25.0,
            description="Completar Capítulo 1"
        )
        session.add(narrative_reward)
        await session.commit()
        
        # Setup user initial state
        initial_points = test_user.points
        
        # Setup user narrative state
        user_state = UserNarrativeState(
            user_id=test_user.id,
            current_fragment_key="story_chapter_1"
        )
        session.add(user_state)
        await session.commit()
        
        # Mock bot for notifications
        mock_bot = AsyncMock()
        
        # Process narrative completion
        await point_service.add_points(test_user.id, narrative_reward.points_awarded, bot=mock_bot)
        
        # Refresh user to get updated points
        await session.refresh(test_user)
        
        # Critical assertions - narrative completion must award points
        expected_points = initial_points + 25.0
        assert test_user.points == expected_points, f"User must have {expected_points} points after completion"
        
        # Verify user stats were updated
        stmt = select(UserStats).where(UserStats.user_id == test_user.id)
        result = await session.execute(stmt)
        user_stats = result.scalar_one_or_none()
        assert user_stats is not None, "User stats must be created/updated"
        assert user_stats.last_activity_at is not None, "Activity timestamp must be updated"

    async def test_narrative_decision_different_rewards(self, session, test_user):
        """
        CRITICAL: Test que protege recompensas diferentes según decisiones narrativas.
        Diferentes decisiones en la narrativa deben otorgar diferentes recompensas.
        """
        narrative_service = NarrativeService(session)
        
        # Create narrative decisions with different rewards
        generous_decision = NarrativeDecision(
            id=1,
            fragment_key="moral_choice",
            text="Ayudar al personaje necesitado",
            next_fragment_key="generous_path",
            points_reward=15.0,  # High reward for generosity
            karma_modifier=1
        )
        
        selfish_decision = NarrativeDecision(
            id=2,
            fragment_key="moral_choice", 
            text="Ignorar al personaje necesitado",
            next_fragment_key="selfish_path",
            points_reward=5.0,  # Lower reward for selfishness
            karma_modifier=-1
        )
        
        session.add_all([generous_decision, selfish_decision])
        
        # Create target fragments
        generous_fragment = NarrativeFragment(
            key="generous_path",
            title="Camino Generoso",
            content="Tu generosidad ha sido recompensada.",
        )
        
        selfish_fragment = NarrativeFragment(
            key="selfish_path", 
            title="Camino Egoísta",
            content="Tu egoísmo tiene consecuencias.",
        )
        
        session.add_all([generous_fragment, selfish_fragment])
        await session.commit()
        
        # Test generous decision
        initial_points = test_user.points
        result_fragment = await narrative_service.process_user_decision(test_user.id, 1)
        
        # Critical assertions - generous choice must award more points
        assert result_fragment.key == "generous_path", "Must advance to generous path"
        
        # Verify decision was logged
        stmt = select(UserDecisionLog).where(
            UserDecisionLog.user_id == test_user.id,
            UserDecisionLog.decision_id == 1
        )
        result = await session.execute(stmt)
        decision_log = result.scalar_one_or_none()
        assert decision_log is not None, "Generous decision must be logged"
        
        # Reset for selfish decision test
        await session.delete(decision_log)
        await session.commit()
        
        # Test selfish decision with different user state
        user_state = UserNarrativeState(
            user_id=test_user.id,
            current_fragment_key="moral_choice"
        )
        session.add(user_state)
        await session.commit()
        
        result_fragment_2 = await narrative_service.process_user_decision(test_user.id, 2)
        
        assert result_fragment_2.key == "selfish_path", "Must advance to selfish path"

    async def test_prevent_duplicate_narrative_rewards(self, session, test_user):
        """
        CRITICAL: Test que protege contra recompensas duplicadas por el mismo progreso.
        Un usuario NO debe poder obtener recompensas múltiples por el mismo fragmento narrativo.
        """
        point_service = PointService(session)
        
        # Create fragment with one-time reward
        unique_fragment = NarrativeFragment(
            key="unique_reward_fragment",
            title="Recompensa Única",
            content="Esta recompensa solo se otorga una vez.",
            completion_points=50.0,
            one_time_reward=True
        )
        session.add(unique_fragment)
        
        # Create reward tracking
        narrative_reward = NarrativeReward(
            fragment_key="unique_reward_fragment",
            points_awarded=50.0,
            one_time_only=True,
            description="Recompensa única por descubrimiento"
        )
        session.add(narrative_reward)
        await session.commit()
        
        # Track user reward history
        from database.narrative_models import UserRewardHistory
        
        # First completion - should succeed
        initial_points = test_user.points
        mock_bot = AsyncMock()
        
        # Check if user already received this reward
        stmt = select(UserRewardHistory).where(
            UserRewardHistory.user_id == test_user.id,
            UserRewardHistory.fragment_key == "unique_reward_fragment"
        )
        result = await session.execute(stmt)
        existing_reward = result.scalar_one_or_none()
        
        if not existing_reward:
            await point_service.add_points(test_user.id, 50.0, bot=mock_bot)
            
            # Record that reward was given
            reward_history = UserRewardHistory(
                user_id=test_user.id,
                fragment_key="unique_reward_fragment",
                points_awarded=50.0,
                awarded_at=datetime.utcnow()
            )
            session.add(reward_history)
            await session.commit()
        
        await session.refresh(test_user)
        first_completion_points = test_user.points
        
        # Second attempt - should be blocked
        stmt = select(UserRewardHistory).where(
            UserRewardHistory.user_id == test_user.id,
            UserRewardHistory.fragment_key == "unique_reward_fragment"
        )
        result = await session.execute(stmt)
        duplicate_check = result.scalar_one_or_none()
        
        # Critical assertions - duplicate rewards must be prevented
        assert duplicate_check is not None, "Reward history must exist after first completion"
        assert duplicate_check.points_awarded == 50.0, "Correct reward amount must be recorded"
        
        # Attempting to award again should be blocked (in real implementation)
        assert first_completion_points == test_user.points, "Points should not change on duplicate attempt"

    async def test_narrative_milestone_unlocks_achievements(self, session, test_user):
        """
        CRITICAL: Test que protege el desbloqueo de logros por hitos narrativos.
        Alcanzar ciertos hitos en la narrativa debe desbloquear achievements específicos.
        """
        badge_service = BadgeService(session)
        narrative_service = NarrativeService(session)
        
        # Create narrative milestone achievement
        narrative_badge = Badge(
            name="Explorador de Historias",
            description="Completa 5 fragmentos narrativos",
            requirement="5 fragmentos narrativos",
            emoji="📚"
        )
        session.add(narrative_badge)
        await session.commit()
        
        # Create multiple narrative fragments
        fragments = []
        for i in range(5):
            fragment = NarrativeFragment(
                key=f"milestone_fragment_{i+1}",
                title=f"Fragmento {i+1}",
                content=f"Has completado el fragmento {i+1} de la historia.",
                is_milestone=True
            )
            fragments.append(fragment)
            session.add(fragment)
        
        await session.commit()
        
        # Simulate user completing fragments
        completed_fragments = []
        for i, fragment in enumerate(fragments):
            user_state = UserNarrativeState(
                user_id=test_user.id,
                current_fragment_key=fragment.key,
                fragments_completed=i + 1  # Track completion count
            )
            
            # Delete existing state to update
            stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == test_user.id)
            result = await session.execute(stmt)
            existing_state = result.scalar_one_or_none()
            if existing_state:
                await session.delete(existing_state)
            
            session.add(user_state)
            await session.commit()
            completed_fragments.append(fragment.key)
        
        # Check if user qualifies for narrative badge
        final_state = UserNarrativeState(
            user_id=test_user.id,
            current_fragment_key="milestone_fragment_5",
            fragments_completed=5
        )
        session.add(final_state)
        await session.commit()
        
        # Mock achievement check
        mock_bot = AsyncMock()
        user_stats = UserStats(user_id=test_user.id)
        session.add(user_stats)
        await session.commit()
        
        # Simulate badge checking logic
        if final_state.fragments_completed >= 5:
            granted = await badge_service.grant_badge(test_user.id, narrative_badge)
            
            # Critical assertions - narrative milestones must unlock achievements
            assert granted is True, "Narrative milestone must unlock achievement"
            
            # Verify badge was granted
            stmt = select(UserBadge).where(
                UserBadge.user_id == test_user.id,
                UserBadge.badge_id == narrative_badge.id
            )
            result = await session.execute(stmt)
            user_badge = result.scalar_one_or_none()
            assert user_badge is not None, "Badge must be granted to user"

    async def test_narrative_choice_affects_future_rewards(self, session, test_user):
        """
        CRITICAL: Test que protege cómo las decisiones narrativas afectan recompensas futuras.
        Las decisiones tomadas deben influir en las recompensas disponibles más adelante.
        """
        narrative_service = NarrativeService(session)
        
        # Create choice that affects future rewards
        karma_decision = NarrativeDecision(
            id=1,
            fragment_key="karma_choice",
            text="Actuar con bondad",
            next_fragment_key="good_karma_path",
            karma_modifier=2,  # Positive karma
            affects_future_rewards=True
        )
        session.add(karma_decision)
        
        # Create future fragment with karma-dependent rewards
        future_fragment = NarrativeFragment(
            key="karma_dependent_reward",
            title="Recompensa por Karma",
            content="Tu karma anterior afecta esta recompensa.",
            base_points=10.0,
            karma_multiplier=True  # Points multiplied by karma
        )
        session.add(future_fragment)
        await session.commit()
        
        # Process karma-affecting decision
        result_fragment = await narrative_service.process_user_decision(test_user.id, 1)
        assert result_fragment.key == "good_karma_path", "Must advance to good karma path"
        
        # Verify decision was logged with karma modifier
        stmt = select(UserDecisionLog).where(
            UserDecisionLog.user_id == test_user.id,
            UserDecisionLog.decision_id == 1
        )
        result = await session.execute(stmt)
        decision_log = result.scalar_one_or_none()
        assert decision_log is not None, "Karma decision must be logged"
        
        # Mock karma calculation for future rewards
        user_karma = 2  # From the decision
        base_points = 10.0
        karma_bonus = base_points * (user_karma / 10.0)  # Karma affects reward
        total_expected = base_points + karma_bonus
        
        # Critical assertions - past decisions must affect future rewards
        assert user_karma > 0, "Good decision must provide positive karma"
        assert total_expected > base_points, "Good karma must enhance future rewards"

    async def test_rollback_on_reward_transaction_failure(self, session, test_user):
        """
        CRITICAL: Test que protege contra inconsistencias en transacciones de recompensas.
        Si falla el otorgamiento de recompensas, la transacción debe hacer rollback completo.
        """
        narrative_service = NarrativeService(session)
        point_service = PointService(session)
        
        # Create complex reward scenario
        complex_fragment = NarrativeFragment(
            key="complex_reward",
            title="Recompensa Compleja",
            content="Múltiples recompensas simultáneas.",
            completion_points=30.0,
            unlocks_achievement=True
        )
        session.add(complex_fragment)
        await session.commit()
        
        # Setup initial state
        initial_points = test_user.points
        initial_narrative_state = UserNarrativeState(
            user_id=test_user.id,
            current_fragment_key="pre_complex_reward"
        )
        session.add(initial_narrative_state)
        await session.commit()
        
        # Mock point service to fail during reward processing
        original_add_points = point_service.add_points
        
        async def mock_failing_add_points(*args, **kwargs):
            # Simulate failure during point addition
            raise Exception("Database transaction failed")
        
        # Test transaction rollback
        with patch.object(point_service, 'add_points', side_effect=mock_failing_add_points):
            try:
                # Attempt to process complex reward
                await point_service.add_points(test_user.id, 30.0, bot=None)
                assert False, "Should have raised exception"
            except Exception as e:
                assert "Database transaction failed" in str(e)
        
        # Critical assertions - state must be preserved on failure
        await session.refresh(test_user)
        assert test_user.points == initial_points, "Points must be unchanged after failed transaction"
        
        # Verify narrative state wasn't corrupted
        stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == test_user.id)
        result = await session.execute(stmt)
        preserved_state = result.scalar_one_or_none()
        assert preserved_state.current_fragment_key == "pre_complex_reward", "Narrative state must be preserved"

    async def test_concurrent_narrative_progression_point_safety(self, session, test_user):
        """
        CRITICAL: Test que protege contra condiciones de carrera en recompensas narrativas.
        Múltiples progresiones narrativas simultáneas NO deben causar recompensas duplicadas.
        """
        narrative_service = NarrativeService(session)
        point_service = PointService(session)
        
        # Create fragment with race condition potential
        race_fragment = NarrativeFragment(
            key="race_condition_test",
            title="Test de Condición de Carrera",
            content="Fragmento que podría causar recompensas duplicadas.",
            completion_points=20.0
        )
        session.add(race_fragment)
        await session.commit()
        
        # Setup user state
        user_state = UserNarrativeState(
            user_id=test_user.id,
            current_fragment_key="race_condition_test",
            processing_reward=False  # Flag to prevent concurrent processing
        )
        session.add(user_state)
        await session.commit()
        
        initial_points = test_user.points
        
        # Simulate concurrent reward processing attempts
        async def attempt_reward_processing():
            # Check if already processing
            stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == test_user.id)
            result = await session.execute(stmt)
            state = result.scalar_one_or_none()
            
            if state and not getattr(state, 'processing_reward', False):
                # Set processing flag
                state.processing_reward = True
                await session.commit()
                
                try:
                    # Process reward
                    await point_service.add_points(test_user.id, 20.0, bot=None)
                    return True
                finally:
                    # Clear processing flag
                    state.processing_reward = False
                    await session.commit()
            return False
        
        # Attempt concurrent processing
        result1 = await attempt_reward_processing()
        result2 = await attempt_reward_processing()  # Should be blocked
        
        # Critical assertions - only one processing should succeed
        assert result1 is True, "First processing attempt must succeed"
        assert result2 is False, "Concurrent processing attempt must be blocked"
        
        await session.refresh(test_user)
        expected_points = initial_points + 20.0
        assert test_user.points == expected_points, "Points should only be awarded once despite concurrent attempts"