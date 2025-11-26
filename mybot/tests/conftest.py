# tests/conftest.py
import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Assuming the Base is defined in a way that all models are registered.
# If not, we might need to import all model files here.
from database.base import Base 
from middlewares.db_middleware import DbSessionMiddleware

# Use an in-memory SQLite database for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_db_engine():
    """Fixture for creating an in-memory SQLite database engine."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(test_db_engine):
    """
    Fixture that provides a clean, isolated database session for each test function.
    Creates all tables before the test and drops them afterwards.
    """
    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSessionLocal = async_sessionmaker(
        bind=test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with TestSessionLocal() as session:
        yield session

    async with test_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def mock_bot():
    """Fixture to create a mocked Bot instance."""
    bot = MagicMock()
    bot.send_photo = AsyncMock()
    return bot

@pytest_asyncio.fixture
async def dispatcher(db_session):
    """Fixture to create and configure the Dispatcher."""
    from handlers import narrative_handler, shop_handlers # Import routers here
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # We use the session from the db_session fixture for the middleware
    dp.update.outer_middleware(DbSessionMiddleware(session_pool=db_session.get_bind().engine.pool))

    # Include routers
    dp.include_router(narrative_handler.router)
    dp.include_router(shop_handlers.router)

    yield dp

@pytest.fixture
def mock_user():
    """Fixture to create a mock user."""
    user = MagicMock()
    user.id = 12345
    user.username = "testuser"
    user.first_name = "Test"
    return user

@pytest.fixture
def mock_message(mock_user, mock_bot):
    """Fixture to create a mock message."""
    message = MagicMock()
    message.from_user = mock_user
    message.answer = AsyncMock()
    message.answer_photo = AsyncMock()
    message.edit_text = AsyncMock()
    message.bot = mock_bot
    return message

@pytest.fixture
def mock_callback_query(mock_user, mock_bot):
    """Fixture to create a mock callback query."""
    callback = MagicMock()
    callback.from_user = mock_user
    message = MagicMock()
    message.answer = AsyncMock()
    message.edit_text = AsyncMock()
    message.delete = AsyncMock()
    message.chat.id = 12345
    callback.message = message
    callback.answer = AsyncMock()
    callback.bot = mock_bot
    return callback
