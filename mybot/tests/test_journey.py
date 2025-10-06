"""
Tests para el User Journey System

Verifica:
1. Inicialización de milestones para nuevos usuarios
2. Obtención de usuarios para cada milestone
3. Marcado de milestones como completados
4. Procesamiento de milestones individuales (mock bot)
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from database.models import User, UserMilestone, ContentSet, Base
from services.user_journey_service import UserJourneyService
from services.content_service import ContentService


# Configuración de BD de prueba
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def session():
    """Crea una sesión de BD en memoria para tests"""
    engine = create_async_engine(TEST_DB_URL, echo=False)

    # Crear todas las tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Crear session factory
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    # Crear sesión
    async with session_factory() as session:
        yield session

    # Limpiar
    await engine.dispose()


@pytest.mark.asyncio
async def test_initialize_user_milestones(session):
    """Test: Inicializar milestones para un nuevo usuario"""
    # Crear usuario de prueba
    user = User(
        id=123,
        username="testuser",
        first_name="Test",
        role="free",
        created_at=datetime.utcnow()
    )
    session.add(user)
    await session.commit()

    # Inicializar milestones
    journey_service = UserJourneyService(session)
    await journey_service.initialize_user_milestones(user.id)

    # Verificar que se crearon los 3 milestones
    stmt = select(UserMilestone).where(UserMilestone.user_id == user.id)
    result = await session.execute(stmt)
    milestones = result.scalars().all()

    assert len(milestones) == 3

    milestone_types = {m.milestone_type for m in milestones}
    assert milestone_types == {"day_1", "day_7", "day_30"}

    # Todos deberían estar pendientes
    for milestone in milestones:
        assert milestone.completed is False


@pytest.mark.asyncio
async def test_get_users_for_day_1_milestone(session):
    """Test: Obtener usuarios que alcanzaron el milestone day_1"""
    # Crear usuarios de prueba
    # Usuario 1: Registrado hace 2 días (debería aparecer)
    user1 = User(
        id=1,
        username="user1",
        role="free",
        created_at=datetime.utcnow() - timedelta(days=2)
    )

    # Usuario 2: Registrado hoy (NO debería aparecer)
    user2 = User(
        id=2,
        username="user2",
        role="free",
        created_at=datetime.utcnow()
    )

    # Usuario 3: Registrado hace 1 día exacto (debería aparecer)
    user3 = User(
        id=3,
        username="user3",
        role="free",
        created_at=datetime.utcnow() - timedelta(days=1)
    )

    session.add_all([user1, user2, user3])
    await session.commit()

    # Inicializar milestones
    journey_service = UserJourneyService(session)
    await journey_service.initialize_user_milestones(1)
    await journey_service.initialize_user_milestones(2)
    await journey_service.initialize_user_milestones(3)

    # Obtener usuarios para day_1
    users = await journey_service.get_users_for_milestone("day_1")

    # Solo user1 y user3 deberían aparecer
    user_ids = {u.id for u in users}
    assert 1 in user_ids
    assert 3 in user_ids
    assert 2 not in user_ids  # Muy reciente


@pytest.mark.asyncio
async def test_mark_milestone_completed(session):
    """Test: Marcar un milestone como completado"""
    # Crear usuario
    user = User(
        id=456,
        username="testuser2",
        role="free",
        created_at=datetime.utcnow()
    )
    session.add(user)
    await session.commit()

    # Inicializar milestones
    journey_service = UserJourneyService(session)
    await journey_service.initialize_user_milestones(user.id)

    # Marcar day_1 como completado
    success = await journey_service.mark_milestone_completed(
        user_id=user.id,
        milestone_type="day_1",
        data={"test": "data"}
    )

    assert success is True

    # Verificar que se marcó
    stmt = select(UserMilestone).where(
        UserMilestone.user_id == user.id,
        UserMilestone.milestone_type == "day_1"
    )
    result = await session.execute(stmt)
    milestone = result.scalar_one()

    assert milestone.completed is True
    assert milestone.completed_at is not None
    assert milestone.data == {"test": "data"}


@pytest.mark.asyncio
async def test_is_milestone_completed(session):
    """Test: Verificar si un milestone está completado"""
    # Crear usuario
    user = User(
        id=789,
        username="testuser3",
        role="free",
        created_at=datetime.utcnow()
    )
    session.add(user)
    await session.commit()

    # Inicializar milestones
    journey_service = UserJourneyService(session)
    await journey_service.initialize_user_milestones(user.id)

    # Verificar que no está completado inicialmente
    is_completed = await journey_service.is_milestone_completed(user.id, "day_1")
    assert is_completed is False

    # Marcar como completado
    await journey_service.mark_milestone_completed(user.id, "day_1")

    # Verificar que ahora sí está completado
    is_completed = await journey_service.is_milestone_completed(user.id, "day_1")
    assert is_completed is True


@pytest.mark.asyncio
async def test_skip_day_7_for_vip_users(session):
    """Test: Day 7 milestone se salta para usuarios VIP"""
    # Crear usuario VIP
    user = User(
        id=999,
        username="vipuser",
        role="vip",
        created_at=datetime.utcnow() - timedelta(days=7)
    )
    session.add(user)
    await session.commit()

    # Inicializar milestones
    journey_service = UserJourneyService(session)
    await journey_service.initialize_user_milestones(user.id)

    # Mock bot (no podemos testear el envío real)
    class MockBot:
        async def send_message(self, *args, **kwargs):
            pass

    bot = MockBot()

    # Procesar day_7 (debería saltarse)
    success = await journey_service.process_day_7_milestone(user, bot)

    assert success is True

    # Verificar que se marcó como completado con skip
    stmt = select(UserMilestone).where(
        UserMilestone.user_id == user.id,
        UserMilestone.milestone_type == "day_7"
    )
    result = await session.execute(stmt)
    milestone = result.scalar_one()

    assert milestone.completed is True
    assert milestone.data.get("skipped") == "already_vip"


if __name__ == "__main__":
    # Ejecutar tests manualmente
    async def run_tests():
        print("🧪 Ejecutando tests del Journey System...")

        # Crear engine y session
        engine = create_async_engine(TEST_DB_URL, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async with session_factory() as session:
            # Test 1
            print("✓ Test: Inicializar milestones")
            await test_initialize_user_milestones(session)

            # Test 2
            print("✓ Test: Obtener usuarios para day_1")
            await test_get_users_for_day_1_milestone(session)

            # Test 3
            print("✓ Test: Marcar milestone completado")
            await test_mark_milestone_completed(session)

            # Test 4
            print("✓ Test: Verificar milestone completado")
            await test_is_milestone_completed(session)

            # Test 5
            print("✓ Test: Skip day_7 para VIP")
            await test_skip_day_7_for_vip_users(session)

        await engine.dispose()
        print("\n✅ Todos los tests del journey pasaron exitosamente!")

    asyncio.run(run_tests())
