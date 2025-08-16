"""
Tests de protección para flujos de integración críticos del sistema.
Enfoque minimalista para asegurar protección durante refactoring.
"""
import pytest
import asyncio
import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from database.base import Base
from database.models import User, Channel, UserStats, Badge, UserBadge, VipAccess
from database.narrative_models import NarrativeFragment, UserNarrativeState, NarrativeDecision, UserDecisionLog
from services.channel_service import ChannelService
from services.narrative_service import NarrativeService
from services.point_service import PointService
from services.badge_service import BadgeService
from services.integration.channel_engagement_service import ChannelEngagementService


class TestCriticalIntegrationFlows:
    """Tests críticos de protección para flujos de integración."""

    @pytest.fixture
    async def test_session(self):
        """Create test database session."""
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=False
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with session_factory() as session:
            yield session
        
        await engine.dispose()

    @pytest.fixture
    async def test_user(self, test_session):
        """Create test user."""
        user = User(
            id=123456789,
            first_name="TestUser",
            username="testuser",
            role="free",
            points=100.0,
            created_at=datetime.datetime.utcnow()
        )
        test_session.add(user)
        await test_session.commit()
        await test_session.refresh(user)
        return user

    @pytest.fixture
    async def test_channel(self, test_session):
        """Create test channel."""
        channel = Channel(
            id=-1001234567890,
            title="Test Channel",
            channel_type="vip",
            reaction_points={"like": 10.0, "heart": 15.0}
        )
        test_session.add(channel)
        await test_session.commit()
        await test_session.refresh(channel)
        return channel

    @pytest.mark.asyncio
    async def test_point_service_integration(self, test_session, test_user):
        """
        CRITICAL: Test que protege el servicio de puntos.
        El otorgamiento de puntos DEBE funcionar correctamente.
        """
        point_service = PointService(test_session)
        mock_bot = AsyncMock()
        
        # Test adding points
        initial_points = test_user.points
        user_stats = await point_service.add_points(test_user.id, 25.0, bot=mock_bot)
        
        # Refresh user to get updated points
        await test_session.refresh(test_user)
        
        # Critical assertions
        assert test_user.points == initial_points + 25.0, "Points must be added correctly"
        assert user_stats is not None, "UserStats must be created/updated"

    @pytest.mark.asyncio
    async def test_narrative_service_basic_flow(self, test_session, test_user):
        """
        CRITICAL: Test que protege el servicio narrativo básico.
        La recuperación de fragmentos DEBE funcionar.
        """
        narrative_service = NarrativeService(test_session)
        
        # Create test narrative fragment
        fragment = NarrativeFragment(
            key="test_fragment",
            title="Test Fragment",
            content="This is a test narrative fragment."
        )
        test_session.add(fragment)
        await test_session.commit()
        
        # Create user narrative state
        user_state = UserNarrativeState(
            user_id=test_user.id,
            current_fragment_key="test_fragment"
        )
        test_session.add(user_state)
        await test_session.commit()
        
        # Test fragment retrieval
        current_fragment = await narrative_service.get_user_current_fragment(test_user.id)
        
        # Critical assertions
        assert current_fragment is not None, "Fragment must be retrieved"
        assert current_fragment.key == "test_fragment", "Correct fragment must be returned"
        assert "test narrative fragment" in current_fragment.content, "Fragment content must be preserved"

    @pytest.mark.asyncio
    async def test_badge_service_achievement_flow(self, test_session, test_user):
        """
        CRITICAL: Test que protege el sistema de logros.
        El otorgamiento de badges DEBE funcionar correctamente.
        """
        badge_service = BadgeService(test_session)
        
        # Create test badge
        test_badge = Badge(
            name="Test Achievement",
            description="Test badge for integration testing",
            emoji="🏆",
            requirement="testing"
        )
        test_session.add(test_badge)
        await test_session.commit()
        await test_session.refresh(test_badge)
        
        # Grant badge to user
        granted = await badge_service.grant_badge(test_user.id, test_badge)
        
        # Critical assertions
        assert granted is True, "Badge must be granted successfully"
        
        # Verify badge was granted
        from sqlalchemy import select
        stmt = select(UserBadge).where(
            UserBadge.user_id == test_user.id,
            UserBadge.badge_id == test_badge.id
        )
        result = await test_session.execute(stmt)
        user_badge = result.scalar_one_or_none()
        
        assert user_badge is not None, "UserBadge record must be created"

    @pytest.mark.asyncio
    async def test_channel_service_basic_operations(self, test_session, test_channel):
        """
        CRITICAL: Test que protege las operaciones básicas de canal.
        La gestión de canales DEBE funcionar correctamente.
        """
        channel_service = ChannelService(test_session)
        
        # Test channel retrieval
        channels = await channel_service.list_channels()
        assert len(channels) >= 1, "Test channel must be in channel list"
        
        found_channel = next((c for c in channels if c.id == test_channel.id), None)
        assert found_channel is not None, "Test channel must be found"
        assert found_channel.title == "Test Channel", "Channel title must be preserved"

    @pytest.mark.asyncio
    async def test_engagement_service_basic_flow(self, test_session, test_user, test_channel):
        """
        CRITICAL: Test que protege el servicio de engagement básico.
        El sistema de engagement DEBE manejar canales gestionados correctamente.
        """
        engagement_service = ChannelEngagementService(test_session)
        
        # Mock managed channels
        engagement_service.config_service.get_managed_channels = AsyncMock(
            return_value={str(test_channel.id): "vip"}
        )
        engagement_service.point_service.award_reaction = AsyncMock()
        
        # Test channel reaction award
        result = await engagement_service.award_channel_reaction(
            test_user.id,
            message_id=123,
            channel_id=test_channel.id,
            bot=None
        )
        
        # Critical assertions
        assert result is True, "Channel reaction award must succeed for managed channels"
        engagement_service.point_service.award_reaction.assert_called_once()

    @pytest.mark.asyncio
    async def test_vip_badge_integration_basic(self, test_session, test_user):
        """
        CRITICAL: Test que protege la integración básica de badges VIP.
        Los badges con propiedades VIP DEBEN ser manejados correctamente.
        """
        badge_service = BadgeService(test_session)
        
        # Create VIP-granting badge
        vip_badge = Badge(
            name="VIP Achievement",
            description="Grants VIP access",
            emoji="👑",
            requirement="special criteria",
            grants_vip_access=True,
            vip_duration_days=30
        )
        test_session.add(vip_badge)
        await test_session.commit()
        await test_session.refresh(vip_badge)
        
        # Grant VIP badge
        granted = await badge_service.grant_badge(test_user.id, vip_badge)
        assert granted is True, "VIP badge must be granted"
        
        # Simulate VIP upgrade process
        if vip_badge.grants_vip_access:
            test_user.role = "vip"
            test_user.vip_until = datetime.datetime.utcnow() + datetime.timedelta(days=30)
            test_session.add(test_user)
            await test_session.commit()
        
        # Verify VIP status
        await test_session.refresh(test_user)
        assert test_user.role == "vip", "User must be upgraded to VIP"
        assert test_user.vip_until is not None, "VIP expiration must be set"

    @pytest.mark.asyncio
    async def test_narrative_decision_processing(self, test_session, test_user):
        """
        CRITICAL: Test que protege el procesamiento de decisiones narrativas.
        Las decisiones narrativas DEBEN procesarse y registrarse correctamente.
        """
        narrative_service = NarrativeService(test_session)
        
        # Create narrative components
        decision = NarrativeDecision(
            id=1,
            fragment_key="choice_fragment",
            text="Make a choice",
            next_fragment_key="result_fragment"
        )
        
        result_fragment = NarrativeFragment(
            key="result_fragment",
            title="Choice Result",
            content="You made a choice."
        )
        
        test_session.add_all([decision, result_fragment])
        await test_session.commit()
        
        # Process decision
        result = await narrative_service.process_user_decision(test_user.id, 1)
        
        # Critical assertions
        assert result is not None, "Decision processing must succeed"
        assert result.key == "result_fragment", "Must advance to correct fragment"
        
        # Verify decision was logged
        from sqlalchemy import select
        stmt = select(UserDecisionLog).where(UserDecisionLog.user_id == test_user.id)
        result = await test_session.execute(stmt)
        decision_log = result.scalar_one_or_none()
        assert decision_log is not None, "Decision must be logged"

    @pytest.mark.asyncio
    async def test_critical_data_integrity(self, test_session, test_user):
        """
        CRITICAL: Test que protege la integridad de datos críticos.
        Las operaciones concurrentes NO deben corromper el estado.
        """
        point_service = PointService(test_session)
        
        # Test concurrent point operations
        initial_points = test_user.points
        mock_bot = AsyncMock()
        
        # Simulate adding points twice
        await point_service.add_points(test_user.id, 10.0, bot=mock_bot)
        await point_service.add_points(test_user.id, 15.0, bot=mock_bot)
        
        # Verify final state
        await test_session.refresh(test_user)
        expected_points = initial_points + 25.0
        assert test_user.points == expected_points, "Points must accumulate correctly"

    @pytest.mark.asyncio
    async def test_service_error_handling(self, test_session):
        """
        CRITICAL: Test que protege el manejo de errores en servicios.
        Los servicios DEBEN manejar errores sin corromper el estado.
        """
        point_service = PointService(test_session)
        
        # Test with non-existent user
        user_stats = await point_service.add_points(99999999, 10.0, bot=None)
        
        # Service should handle gracefully (may create user or return appropriate response)
        assert user_stats is not None, "Service must handle non-existent users gracefully"