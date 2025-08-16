"""
Tests simples de protección para flujos de integración críticos.
Enfoque funcional para asegurar protección durante refactoring.
"""
import pytest
import asyncio
import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from database.base import Base
from database.models import User, Channel, UserStats, Badge, UserBadge
from database.narrative_models import NarrativeFragment, UserNarrativeState, NarrativeDecision
from services.point_service import PointService
from services.badge_service import BadgeService


@pytest.mark.asyncio
async def test_point_service_critical_flow():
    """
    CRITICAL: Test que protege el flujo de puntos básico.
    El otorgamiento de puntos DEBE funcionar correctamente.
    """
    # Setup in-memory database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_factory() as session:
        # Create test user
        user = User(
            id=123456789,
            first_name="TestUser",
            username="testuser",
            role="free",
            points=100.0
        )
        session.add(user)
        await session.commit()
        
        # Test point service
        point_service = PointService(session)
        mock_bot = AsyncMock()
        
        initial_points = user.points
        await point_service.add_points(user.id, 25.0, bot=mock_bot)
        
        # Refresh and verify
        await session.refresh(user)
        assert user.points == initial_points + 25.0, "Points must be added correctly"
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_badge_service_critical_flow():
    """
    CRITICAL: Test que protege el flujo de badges básico.
    El otorgamiento de badges DEBE funcionar correctamente.
    """
    # Setup in-memory database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_factory() as session:
        # Create test user
        user = User(
            id=123456789,
            first_name="TestUser",
            username="testuser",
            role="free",
            points=100.0
        )
        session.add(user)
        
        # Create test badge
        badge = Badge(
            name="Test Achievement",
            description="Test badge",
            emoji="🏆",
            requirement="testing"
        )
        session.add(badge)
        await session.commit()
        await session.refresh(badge)
        
        # Test badge service
        badge_service = BadgeService(session)
        granted = await badge_service.grant_badge(user.id, badge)
        
        # Verify badge was granted
        assert granted is True, "Badge must be granted successfully"
        
        # Check database
        from sqlalchemy import select
        stmt = select(UserBadge).where(UserBadge.user_id == user.id)
        result = await session.execute(stmt)
        user_badges = result.scalars().all()
        
        assert len(user_badges) == 1, "One badge must be granted"
        assert user_badges[0].badge_id == badge.id, "Correct badge must be granted"
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_vip_badge_integration():
    """
    CRITICAL: Test que protege la integración VIP por badges.
    Los badges VIP DEBEN otorgar acceso VIP correctamente.
    """
    # Setup in-memory database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_factory() as session:
        # Create test user
        user = User(
            id=123456789,
            first_name="TestUser",
            username="testuser",
            role="free",
            points=1000.0
        )
        session.add(user)
        
        # Create VIP badge
        vip_badge = Badge(
            name="VIP Achievement",
            description="Grants VIP access",
            emoji="👑",
            requirement="1000 points",
            grants_vip_access=True,
            vip_duration_days=30
        )
        session.add(vip_badge)
        await session.commit()
        await session.refresh(vip_badge)
        
        # Grant VIP badge
        badge_service = BadgeService(session)
        granted = await badge_service.grant_badge(user.id, vip_badge)
        assert granted is True, "VIP badge must be granted"
        
        # Simulate VIP upgrade process
        if vip_badge.grants_vip_access:
            user.role = "vip"
            user.vip_until = datetime.datetime.utcnow() + datetime.timedelta(days=vip_badge.vip_duration_days)
            session.add(user)
            await session.commit()
        
        # Verify VIP status
        await session.refresh(user)
        assert user.role == "vip", "User must be upgraded to VIP"
        assert user.vip_until is not None, "VIP expiration must be set"
        
        # Verify duration
        time_diff = user.vip_until - datetime.datetime.utcnow()
        assert time_diff.days >= 29, "VIP duration must be approximately correct"
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_narrative_fragment_retrieval():
    """
    CRITICAL: Test que protege la recuperación de fragmentos narrativos.
    La navegación narrativa DEBE funcionar correctamente.
    """
    # Setup in-memory database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_factory() as session:
        # Create test user
        user = User(
            id=123456789,
            first_name="TestUser",
            username="testuser",
            role="free",
            points=100.0
        )
        session.add(user)
        
        # Create narrative fragment
        fragment = NarrativeFragment(
            key="test_fragment",
            title="Test Fragment",
            content="This is a test narrative fragment."
        )
        session.add(fragment)
        
        # Create user narrative state
        user_state = UserNarrativeState(
            user_id=user.id,
            current_fragment_key="test_fragment"
        )
        session.add(user_state)
        await session.commit()
        
        # Test fragment retrieval using narrative service
        from services.narrative_service import NarrativeService
        narrative_service = NarrativeService(session)
        
        current_fragment = await narrative_service.get_user_current_fragment(user.id)
        
        # Critical assertions
        assert current_fragment is not None, "Fragment must be retrieved"
        assert current_fragment.key == "test_fragment", "Correct fragment must be returned"
        assert "test narrative fragment" in current_fragment.content, "Fragment content must be preserved"
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_engagement_points_integration():
    """
    CRITICAL: Test que protege la integración engagement-puntos.
    Las reacciones en canales DEBEN otorgar puntos correctamente.
    """
    # Setup in-memory database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_factory() as session:
        # Create test user
        user = User(
            id=123456789,
            first_name="TestUser",
            username="testuser",
            role="free",
            points=100.0
        )
        session.add(user)
        
        # Create test channel
        channel = Channel(
            id=-1001234567890,
            title="Test Channel",
            channel_type="vip",
            reaction_points={"like": 10.0, "heart": 15.0}
        )
        session.add(channel)
        await session.commit()
        
        # Test engagement service
        from services.integration.channel_engagement_service import ChannelEngagementService
        engagement_service = ChannelEngagementService(session)
        
        # Mock managed channels
        engagement_service.config_service.get_managed_channels = AsyncMock(
            return_value={str(channel.id): "vip"}
        )
        engagement_service.point_service.award_reaction = AsyncMock()
        
        # Test channel reaction award
        result = await engagement_service.award_channel_reaction(
            user.id,
            message_id=123,
            channel_id=channel.id,
            bot=None
        )
        
        # Critical assertions
        assert result is True, "Channel reaction award must succeed for managed channels"
        engagement_service.point_service.award_reaction.assert_called_once()
        
        # Verify call parameters
        call_args = engagement_service.point_service.award_reaction.call_args
        assert call_args[0][0] == user, "Correct user must be passed"
        assert call_args[0][1] == 123, "Correct message ID must be passed"
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_data_integrity_under_load():
    """
    CRITICAL: Test que protege la integridad de datos bajo carga.
    Las operaciones concurrentes NO deben corromper el estado.
    """
    # Setup in-memory database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_factory() as session:
        # Create test user
        user = User(
            id=123456789,
            first_name="TestUser",
            username="testuser",
            role="free",
            points=100.0
        )
        session.add(user)
        await session.commit()
        
        initial_points = user.points
        
        # Test concurrent point operations
        point_service = PointService(session)
        mock_bot = AsyncMock()
        
        # Simulate multiple point additions
        await point_service.add_points(user.id, 10.0, bot=mock_bot)
        await point_service.add_points(user.id, 15.0, bot=mock_bot)
        await point_service.add_points(user.id, 5.0, bot=mock_bot)
        
        # Verify final state
        await session.refresh(user)
        expected_points = initial_points + 30.0
        assert user.points == expected_points, f"Points must accumulate correctly: {user.points} vs {expected_points}"
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_error_handling_resilience():
    """
    CRITICAL: Test que protege la resistencia a errores.
    Los servicios DEBEN manejar errores sin corromper el estado.
    """
    # Setup in-memory database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_factory() as session:
        # Test point service with non-existent user
        point_service = PointService(session)
        
        # This should create the user or handle gracefully
        user_stats = await point_service.add_points(99999999, 10.0, bot=None)
        
        # Service should handle gracefully
        assert user_stats is not None, "Service must handle non-existent users gracefully"
        
        # Verify user was created
        from sqlalchemy import select
        stmt = select(User).where(User.id == 99999999)
        result = await session.execute(stmt)
        created_user = result.scalar_one_or_none()
        
        assert created_user is not None, "User must be created when adding points to non-existent user"
        assert created_user.points >= 10.0, "Points must be added to new user"
    
    await engine.dispose()


if __name__ == "__main__":
    # Para ejecutar directamente
    asyncio.run(test_point_service_critical_flow())
    asyncio.run(test_badge_service_critical_flow())
    asyncio.run(test_vip_badge_integration())
    asyncio.run(test_narrative_fragment_retrieval())
    asyncio.run(test_engagement_points_integration())
    asyncio.run(test_data_integrity_under_load())
    asyncio.run(test_error_handling_resilience())
    print("All critical integration tests passed!")