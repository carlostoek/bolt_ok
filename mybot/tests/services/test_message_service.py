import pytest
from unittest.mock import AsyncMock, Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from services.message_service import MessageService
from database.models import ButtonReaction


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    return AsyncMock()


@pytest.fixture
def message_service(mock_session, mock_bot):
    """Create a MessageService instance with mocked dependencies."""
    return MessageService(mock_session, mock_bot)


@pytest.mark.asyncio
async def test_register_reaction_duplicate_reaction(message_service, mock_session):
    """Test registering a duplicate reaction (should return None)."""
    user_id = 123456789
    message_id = 123456
    reaction_type = "👍"
    
    # Mock the database query to return an existing reaction
    mock_result = AsyncMock()
    mock_result.scalar = AsyncMock(return_value=Mock(spec=ButtonReaction))
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    # Call the method
    result = await message_service.register_reaction(user_id, message_id, reaction_type)
    
    # Verify that no new reaction was added to session
    assert not mock_session.add.called
    
    # Verify that None was returned
    assert result is None