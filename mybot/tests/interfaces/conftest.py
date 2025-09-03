import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

# Importar interfaces cuando estén creadas
# from services.interfaces.emotional_state_interface import EmotionalState, EmotionalContext
# from services.interfaces.content_delivery_interface import ContentType, DeliveryChannel, ContentPackage, DeliveryContext
# from services.interfaces.user_interaction_interface import InteractionType, InteractionContext, InteractionResult

@pytest_asyncio.fixture
async def mock_session():
    """Mock de sesión de base de datos async"""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    session.scalar_one_or_none = AsyncMock()
    return session

@pytest.fixture
def sample_user_id():
    """ID de usuario de prueba"""
    return 123456789

@pytest.fixture
def mock_bot():
    """Mock del bot de Telegram"""
    bot = MagicMock()
    bot.send_message = AsyncMock()
    bot.answer_callback_query = AsyncMock()
    bot.edit_message_text = AsyncMock()
    return bot

@pytest.fixture
def sample_timestamp():
    """Timestamp de prueba fijo"""
    return datetime(2024, 1, 1, 12, 0, 0)