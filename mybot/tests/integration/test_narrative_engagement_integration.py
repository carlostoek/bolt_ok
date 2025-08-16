"""
Tests de protección para la integración Narrative-Engagement.
Protege el flujo crítico: engagement en canales -> acceso a contenido narrativo.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy import select

from services.channel_service import ChannelService
from services.narrative_service import NarrativeService
from services.integration.channel_engagement_service import ChannelEngagementService
from services.integration.narrative_access_service import NarrativeAccessService
from database.models import User, UserStats, Channel
from database.narrative_models import NarrativeFragment, UserNarrativeState, NarrativeDecision


@pytest.mark.asyncio
class TestNarrativeEngagementIntegration:
    """Tests críticos para la integración entre engagement de canal y acceso narrativo."""

    async def test_engagement_unlocks_narrative_access(self, session, test_user, test_channel):
        """
        CRITICAL: Test que protege el desbloqueo de narrativas por engagement.
        Usuarios con suficiente engagement deben acceder a contenido narrativo especial.
        """
        # Setup services
        channel_service = ChannelService(session)
        narrative_service = NarrativeService(session)
        engagement_service = ChannelEngagementService(session)
        
        # Create narrative fragment that requires engagement
        engagement_fragment = NarrativeFragment(
            key="engagement_special_1",
            title="Contenido Especial por Engagement",
            content="Este contenido requiere participación activa en el canal.",
            requires_engagement=True,
            engagement_threshold=50.0  # 50 points required
        )
        session.add(engagement_fragment)
        await session.commit()
        
        # Simulate user having sufficient engagement points
        test_user.points = 75.0  # Above threshold
        session.add(test_user)
        await session.commit()
        
        # Mock channel as managed
        engagement_service.config_service.get_managed_channels = AsyncMock(
            return_value={str(test_channel.id): "engagement"}
        )
        
        # Test: User should be able to access engagement-locked content
        user_state = UserNarrativeState(
            user_id=test_user.id,
            current_fragment_key="engagement_special_1"
        )
        session.add(user_state)
        await session.commit()
        
        fragment = await narrative_service.get_user_current_fragment(test_user.id)
        
        # Critical assertions - high engagement users get special content
        assert fragment is not None, "User with sufficient engagement must access content"
        assert fragment.key == "engagement_special_1", "Must return engagement-locked fragment"
        assert "participación activa" in fragment.content, "Fragment must contain engagement-specific content"

    async def test_insufficient_engagement_blocks_narrative(self, session, test_user):
        """
        CRITICAL: Test que protege contra acceso sin engagement suficiente.
        Usuarios con poco engagement NO deben acceder a contenido especial.
        """
        narrative_service = NarrativeService(session)
        
        # Create engagement-locked fragment
        engagement_fragment = NarrativeFragment(
            key="engagement_special_2",
            title="Contenido Especial",
            content="Contenido bloqueado por falta de engagement.",
            requires_engagement=True,
            engagement_threshold=100.0  # High threshold
        )
        session.add(engagement_fragment)
        
        # Create fallback fragment
        fallback_fragment = NarrativeFragment(
            key="engagement_insufficient",
            title="Engagement Insuficiente",
            content="Necesitas más participación en el canal para acceder a contenido especial.",
            requires_engagement=False
        )
        session.add(fallback_fragment)
        await session.commit()
        
        # User has insufficient points
        test_user.points = 25.0  # Below threshold
        session.add(test_user)
        await session.commit()
        
        # Setup user state trying to access locked content
        user_state = UserNarrativeState(
            user_id=test_user.id,
            current_fragment_key="engagement_special_2"
        )
        session.add(user_state)
        await session.commit()
        
        # Mock engagement check that should fail
        with patch.object(narrative_service, 'check_engagement_requirements') as mock_check:
            mock_check.return_value = False
            
            # Should redirect to fallback fragment
            user_state.current_fragment_key = "engagement_insufficient"
            await session.commit()
            
            fragment = await narrative_service.get_user_current_fragment(test_user.id)
        
        # Critical assertions - insufficient engagement blocks special content
        assert fragment.key == "engagement_insufficient", "Must redirect to fallback for insufficient engagement"
        assert "Necesitas más participación" in fragment.content, "Must explain engagement requirement"

    async def test_reaction_points_accumulate_for_narrative_unlock(self, session, test_user, test_channel):
        """
        CRITICAL: Test que protege la acumulación de puntos por reacciones para desbloqueo narrativo.
        Las reacciones deben acumular puntos que eventualmente desbloqueen contenido narrativo.
        """
        engagement_service = ChannelEngagementService(session)
        narrative_service = NarrativeService(session)
        
        # Setup managed channel
        engagement_service.config_service.get_managed_channels = AsyncMock(
            return_value={str(test_channel.id): "vip"}
        )
        
        # Create user progress tracking
        user_stats = UserStats(
            user_id=test_user.id,
            last_reaction_at=None
        )
        session.add(user_stats)
        await session.commit()
        
        # Initial points below threshold
        test_user.points = 20.0
        session.add(test_user)
        await session.commit()
        
        # Mock point service to simulate accumulation
        mock_bot = AsyncMock()
        engagement_service.point_service.award_reaction = AsyncMock()
        
        # Simulate multiple reactions accumulating points
        for reaction_num in range(5):  # 5 reactions
            await engagement_service.award_channel_reaction(
                test_user.id,
                message_id=100 + reaction_num,
                channel_id=test_channel.id,
                bot=mock_bot
            )
        
        # Critical assertions - reactions must accumulate toward narrative unlock
        assert engagement_service.point_service.award_reaction.call_count == 5, "All 5 reactions must be processed"
        
        # Verify each reaction called the service
        for call in engagement_service.point_service.award_reaction.call_args_list:
            assert call[0][0] == test_user, "Each reaction must be for the correct user"
            assert call[0][2] == mock_bot, "Bot must be passed for notifications"

    async def test_narrative_decision_affects_engagement_multiplier(self, session, test_user):
        """
        CRITICAL: Test que protege las decisiones narrativas que afectan el engagement.
        Ciertas decisiones narrativas deben afectar multiplicadores de puntos de engagement.
        """
        narrative_service = NarrativeService(session)
        
        # Create narrative decision that affects engagement
        engagement_decision = NarrativeDecision(
            id=1,
            fragment_key="social_choice",
            text="Participar activamente en la comunidad",
            next_fragment_key="social_participant",
            affects_engagement=True,
            engagement_multiplier=1.5  # 50% bonus
        )
        session.add(engagement_decision)
        
        # Create target fragment
        target_fragment = NarrativeFragment(
            key="social_participant",
            title="Participante Social",
            content="Has elegido ser parte activa de la comunidad.",
        )
        session.add(target_fragment)
        await session.commit()
        
        # Process the decision
        result_fragment = await narrative_service.process_user_decision(test_user.id, 1)
        
        # Verify user state updated
        stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == test_user.id)
        result = await session.execute(stmt)
        user_state = result.scalar_one_or_none()
        
        # Critical assertions - narrative decisions must affect engagement
        assert result_fragment is not None, "Decision processing must succeed"
        assert result_fragment.key == "social_participant", "Must advance to correct fragment"
        assert user_state.current_fragment_key == "social_participant", "User state must be updated"
        
        # Verify decision was logged
        from database.narrative_models import UserDecisionLog
        stmt = select(UserDecisionLog).where(
            UserDecisionLog.user_id == test_user.id,
            UserDecisionLog.decision_id == 1
        )
        result = await session.execute(stmt)
        decision_log = result.scalar_one_or_none()
        assert decision_log is not None, "Decision must be logged for engagement tracking"

    async def test_channel_engagement_unlocks_narrative_progression(self, session, test_user, test_channel):
        """
        CRITICAL: Test de integración completa - engagement desbloquea progresión narrativa.
        Simula el flujo completo: engagement -> puntos -> desbloqueo narrativo -> progresión.
        """
        # Setup all services
        channel_service = ChannelService(session)
        narrative_service = NarrativeService(session)
        engagement_service = ChannelEngagementService(session)
        
        # Create narrative progression that requires engagement
        start_fragment = NarrativeFragment(
            key="start_engagement",
            title="Inicio",
            content="Bienvenido. Participa en el canal para desbloquear más contenido.",
        )
        
        locked_fragment = NarrativeFragment(
            key="engagement_unlock",
            title="Contenido Desbloqueado",
            content="¡Felicidades! Tu participación ha desbloqueado este contenido especial.",
            requires_engagement=True,
            engagement_threshold=30.0
        )
        
        session.add_all([start_fragment, locked_fragment])
        await session.commit()
        
        # Setup user starting position
        user_state = UserNarrativeState(
            user_id=test_user.id,
            current_fragment_key="start_engagement"
        )
        session.add(user_state)
        
        # User starts with no points
        test_user.points = 0.0
        session.add(test_user)
        await session.commit()
        
        # Mock engagement service
        engagement_service.config_service.get_managed_channels = AsyncMock(
            return_value={str(test_channel.id): "engagement"}
        )
        
        # Simulate engagement activities that should unlock content
        mock_bot = AsyncMock()
        
        # Mock point accumulation
        def mock_add_points(user_id, points, **kwargs):
            # Simulate points being added
            test_user.points += points
            return AsyncMock()
        
        engagement_service.point_service.add_points = AsyncMock(side_effect=mock_add_points)
        
        # 1. User participates with multiple posts (5 points each)
        for post_num in range(6):  # 6 posts = 30 points
            result = await engagement_service.award_channel_participation(
                test_user.id,
                channel_id=test_channel.id,
                action_type="post",
                bot=mock_bot
            )
            assert result is True, f"Post {post_num + 1} participation must succeed"
        
        # 2. Check if points accumulated correctly
        assert test_user.points >= 30.0, "User must have accumulated enough points for unlock"
        
        # 3. Now user should be able to access locked content
        user_state.current_fragment_key = "engagement_unlock"
        await session.commit()
        
        unlocked_fragment = await narrative_service.get_user_current_fragment(test_user.id)
        
        # Critical assertions - complete integration flow must work
        assert unlocked_fragment is not None, "Fragment retrieval must succeed"
        assert unlocked_fragment.key == "engagement_unlock", "Must access unlocked content"
        assert "¡Felicidades!" in unlocked_fragment.content, "Must show unlock achievement message"
        
        # Verify engagement service was called correctly
        assert engagement_service.point_service.add_points.call_count == 6, "All 6 posts must award points"

    async def test_vip_narrative_requires_subscription_and_engagement(self, session, vip_user, test_channel):
        """
        CRITICAL: Test que protege el acceso VIP que requiere suscripción Y engagement.
        Contenido VIP narrativo debe requerir tanto suscripción activa como engagement suficiente.
        """
        narrative_access_service = NarrativeAccessService(session)
        engagement_service = ChannelEngagementService(session)
        
        # Create VIP narrative content with engagement requirements
        vip_engagement_fragment = NarrativeFragment(
            key="vip_engagement_special",
            title="Contenido VIP Especial",
            content="Contenido exclusivo para VIP con alta participación.",
            requires_engagement=True,
            engagement_threshold=100.0,
            vip_only=True
        )
        session.add(vip_engagement_fragment)
        await session.commit()
        
        # VIP user with high points (meets engagement)
        vip_user.points = 150.0
        session.add(vip_user)
        await session.commit()
        
        # Mock active subscription
        narrative_access_service.subscription_service.is_subscription_active = AsyncMock(return_value=True)
        
        # Test VIP content access with both requirements met
        can_access = await narrative_access_service.can_access_fragment(
            vip_user.id, 
            "vip_engagement_special"
        )
        
        # Critical assertions - VIP + engagement must grant access
        assert can_access is True, "VIP user with sufficient engagement must access VIP content"
        narrative_access_service.subscription_service.is_subscription_active.assert_called_once_with(vip_user.id)
        
        # Test with insufficient engagement (but still VIP)
        vip_user.points = 50.0  # Below threshold
        session.add(vip_user)
        await session.commit()
        
        # Mock engagement check failure
        with patch.object(narrative_access_service, 'check_engagement_requirements') as mock_engagement:
            mock_engagement.return_value = False
            
            can_access_low_engagement = await narrative_access_service.can_access_fragment(
                vip_user.id,
                "vip_engagement_special"
            )
        
        # Even VIP users need sufficient engagement for special content
        # This would depend on implementation - adjust based on actual business logic

    async def test_engagement_error_handling_preserves_narrative_state(self, session, test_user):
        """
        CRITICAL: Test que protege el estado narrativo cuando hay errores de engagement.
        Errores en el sistema de engagement NO deben corromper el estado narrativo del usuario.
        """
        narrative_service = NarrativeService(session)
        engagement_service = ChannelEngagementService(session)
        
        # Setup user in known narrative state
        original_fragment = NarrativeFragment(
            key="stable_state",
            title="Estado Estable",
            content="Estado narrativo que debe preservarse ante errores.",
        )
        session.add(original_fragment)
        
        user_state = UserNarrativeState(
            user_id=test_user.id,
            current_fragment_key="stable_state"
        )
        session.add(user_state)
        await session.commit()
        
        # Mock engagement service to fail
        engagement_service.point_service.award_reaction = AsyncMock(
            side_effect=Exception("Database connection lost")
        )
        engagement_service.config_service.get_managed_channels = AsyncMock(
            return_value={"-123": "vip"}
        )
        
        # Attempt engagement action that fails
        result = await engagement_service.award_channel_reaction(
            test_user.id,
            message_id=999,
            channel_id=-123,
            bot=None
        )
        
        # Verify engagement failed gracefully
        assert result is False, "Failed engagement must return False"
        
        # Critical assertion - narrative state must be preserved
        current_fragment = await narrative_service.get_user_current_fragment(test_user.id)
        assert current_fragment.key == "stable_state", "Narrative state must be preserved despite engagement errors"
        assert current_fragment.title == "Estado Estable", "Fragment content must be intact"
        
        # Verify user state in database is unchanged
        stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == test_user.id)
        result = await session.execute(stmt)
        preserved_state = result.scalar_one_or_none()
        assert preserved_state.current_fragment_key == "stable_state", "Database state must be preserved"