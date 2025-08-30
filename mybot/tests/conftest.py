"""
Configuración global de pytest para tests de protección.
"""
import pytest
import pytest_asyncio
import asyncio
import logging
import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from database.base import Base
from database.models import User, Channel, UserStats, Badge, UserBadge, NarrativeReward, UserRewardHistory
from database.narrative_models import UserNarrativeState, StoryFragment, NarrativeFragment, NarrativeDecision, UserDecisionLog
from database.narrative_unified import NarrativeFragment as UnifiedNarrativeFragment
from services.coordinador_central import CoordinadorCentral
from services.point_service import PointService
from services.user_service import UserService
from middlewares.user_middleware import UserRegistrationMiddleware
from middlewares.points_middleware import PointsMiddleware

# Suprimir logs durante tests
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

@pytest.fixture(scope="session")
def event_loop():
    """Crear loop de eventos para tests async."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Crear engine de test con SQLite en memoria."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    async with engine.begin() as conn:
        # Create all tables including our new unified narrative fragment table
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="session")
async def session_factory(test_engine):
    """Factory para crear sesiones de test."""
    # Crear y devolver la fábrica de sesiones
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    return factory

@pytest_asyncio.fixture
async def session(session_factory):
    """Sesión de base de datos para test individual."""
    # Crear una sesión nueva para cada test
    async with session_factory() as session:
        yield session

@pytest_asyncio.fixture
async def mock_bot():
    """Mock del bot de Telegram."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.get_chat_member = AsyncMock()
    return bot

# === FIXTURES DE DATOS DE PRUEBA ===

@pytest_asyncio.fixture
async def test_user(session, request):
    """Usuario de prueba básico."""
    # Generar un ID único para cada test
    import time
    unique_id = int(time.time() * 1000000) % (10**9)  # ID único basado en timestamp
    
    user = User(
        id=unique_id,
        first_name="TestUser",
        username="testuser",
        role="free",
        points=100.0,
        created_at=datetime.datetime.utcnow()
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@pytest_asyncio.fixture
async def vip_user(session, request):
    """Usuario VIP de prueba."""
    # Generar un ID único para cada test
    import time
    unique_id = (int(time.time() * 1000000) % (10**9)) + 1  # ID único basado en timestamp
    
    user = User(
        id=unique_id,
        first_name="VIPUser", 
        username="vipuser",
        role="vip",
        points=500.0,
        vip_expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=30),  # 30 días
        created_at=datetime.datetime.utcnow()
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@pytest_asyncio.fixture
async def admin_user(session, request):
    """Usuario administrador de prueba."""
    # Generar un ID único para cada test
    import time
    unique_id = (int(time.time() * 1000000) % (10**9)) + 2  # ID único basado en timestamp
    
    user = User(
        id=unique_id,
        first_name="AdminUser",
        username="adminuser", 
        role="admin",
        points=1000.0,
        created_at=datetime.datetime.utcnow()
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_channel(session):
    """Canal de prueba."""
    channel = Channel(
        id=-1001234567890,
        title="Test Channel",
        channel_type="vip",
        reaction_points={"like": 10.0, "heart": 15.0}
    )
    session.add(channel)
    await session.commit()
    await session.refresh(channel)
    return channel

@pytest_asyncio.fixture
async def user_progress(session, test_user):
    """Progreso de usuario de prueba."""
    progress = UserStats(
        user_id=test_user.id,
        checkin_streak=5,
        last_checkin_at=datetime.datetime.utcnow() - datetime.timedelta(days=1)  # Ayer
    )
    session.add(progress)
    await session.commit()
    await session.refresh(progress)
    return progress

# === FIXTURES DE SERVICIOS ===

@pytest_asyncio.fixture
async def coordinador_central(session, level_service, achievement_service):
    """Coordinador central para tests con dependencias correctas."""
    from services.coordinador_central import CoordinadorCentral
    from services.notification_service import NotificationService
    from unittest.mock import AsyncMock
    
    # Mock bot for notification service
    mock_bot = AsyncMock()
    notification_service = NotificationService(session, mock_bot)
    
    # Create coordinador with proper dependencies
    coordinador = CoordinadorCentral(session)
    
    # Override internal services with properly initialized ones
    coordinador.point_service = PointService(session, level_service, achievement_service, notification_service)
    
    return coordinador

@pytest_asyncio.fixture
async def level_service(session):
    """Servicio de niveles para tests."""
    from services.level_service import LevelService
    from unittest.mock import AsyncMock
    
    # Crear un mock del servicio de niveles para evitar problemas de transacciones
    mock_level_service = AsyncMock(spec=LevelService)
    mock_level_service.session = session
    mock_level_service.check_for_level_up = AsyncMock(return_value=None)
    mock_level_service.get_level_for_points = AsyncMock(return_value=1)
    mock_level_service.get_user_level = AsyncMock(return_value=1)
    return mock_level_service

@pytest_asyncio.fixture
async def achievement_service(session):
    """Servicio de logros para tests."""
    from services.achievement_service import AchievementService
    from unittest.mock import AsyncMock
    
    # Crear un mock del servicio de logros para evitar problemas de transacciones
    mock_achievement_service = AsyncMock(spec=AchievementService)
    mock_achievement_service.session = session
    mock_achievement_service.check_achievements = AsyncMock(return_value=[])
    mock_achievement_service.unlock_achievement = AsyncMock(return_value=True)
    return mock_achievement_service

@pytest_asyncio.fixture
async def point_service(session, level_service, achievement_service):
    """Servicio de puntos para tests."""
    from services.point_service import PointService
    from services.notification_service import NotificationService
    from unittest.mock import AsyncMock
    
    # Mock bot for notification service
    mock_bot = AsyncMock()
    notification_service = NotificationService(session, mock_bot)
    
    return PointService(session, level_service, achievement_service, notification_service)

@pytest_asyncio.fixture
async def user_service(session):
    """Servicio de usuarios para tests."""
    return UserService(session)

# === FIXTURES DE MIDDLEWARE ===

@pytest_asyncio.fixture
async def user_middleware(session_factory):
    """Middleware de registro de usuarios."""
    return UserRegistrationMiddleware()

@pytest_asyncio.fixture
async def points_middleware():
    """Middleware de puntos."""
    return PointsMiddleware()

# === FIXTURES DE EVENTOS TELEGRAM ===

@pytest.fixture
def mock_message():
    """Mock de mensaje de Telegram."""
    message = MagicMock()
    message.from_user.id = 123456789
    message.from_user.first_name = "TestUser"
    message.from_user.username = "testuser"
    message.from_user.is_bot = False
    message.chat.id = 123456789
    message.text = "Test message"
    message.message_id = 1
    return message

@pytest.fixture
def mock_callback_query():
    """Mock de callback query de Telegram."""
    callback = MagicMock()
    callback.from_user.id = 123456789
    callback.from_user.first_name = "TestUser"
    callback.from_user.username = "testuser"
    callback.data = "ip_-1001234567890_1_like"
    callback.message.chat.id = 123456789
    callback.message.message_id = 1
    callback.answer = AsyncMock()
    return callback

@pytest.fixture
def mock_update():
    """Mock de update de Telegram."""
    update = MagicMock()
    update.message = None
    update.callback_query = None
    update.from_user = None
    return update

# === HELPERS PARA TESTS ===

@pytest.fixture
def assert_database_state():
    """Helper para verificar estado de base de datos."""
    async def _assert_db_state(session: AsyncSession, model, **filters):
        from sqlalchemy import select
        stmt = select(model)
        for attr, value in filters.items():
            stmt = stmt.where(getattr(model, attr) == value)
        result = await session.execute(stmt)
        return result.scalars().all()
    return _assert_db_state

@pytest.fixture
def simulate_telegram_error():
    """Helper para simular errores de Telegram API."""
    def _simulate_error(error_type="BadRequest", message="Test error"):
        from aiogram.exceptions import TelegramBadRequest
        if error_type == "BadRequest":
            return TelegramBadRequest(method="test", message=message)
        # Agregar más tipos según necesidad
        return Exception(message)
    return _simulate_error