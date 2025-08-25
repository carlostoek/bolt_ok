import pytest
from unittest.mock import AsyncMock, Mock, patch
from aiogram.types import CallbackQuery, Message, Chat, User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.reaction_callback import handle_reaction_callback
from services.point_service import PointService
from services.mission_service import MissionService


@pytest.fixture
def mock_callback():
    """Create a mock callback query for testing."""
    callback = Mock(spec=CallbackQuery)
    callback.data = "ip_-1001234567890_123456_👍"
    callback.from_user = Mock(spec=TelegramUser)
    callback.from_user.id = 123456789
    callback.message = Mock(spec=Message)
    callback.message.chat = Mock(spec=Chat)
    callback.message.chat.id = -1001234567890
    callback.answer = AsyncMock()
    return callback


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_complete_reaction_flow(mock_callback, mock_session, mock_bot):
    """Test the complete reaction flow from callback to point awarding."""
    # Mock the validate_message function to return True
    with patch('handlers.reaction_callback.validate_message', return_value=True):
        # Mock the MessageService methods
        with patch('handlers.reaction_callback.MessageService') as mock_service_class:
            mock_service = AsyncMock()
            mock_service.register_reaction.return_value = Mock()  # Return a reaction object
            mock_service.update_reaction_markup = AsyncMock()
            mock_service_class.return_value = mock_service
            
            # Mock the ChannelService methods
            with patch('handlers.reaction_callback.ChannelService') as mock_channel_service_class:
                mock_channel_service = AsyncMock()
                mock_channel_service.get_reaction_points.return_value = {"👍": 1.5}
                mock_channel_service_class.return_value = mock_channel_service
                
                # Mock the PointService
                with patch('services.point_service.PointService') as mock_point_service_class:
                    mock_point_service = AsyncMock()
                    mock_point_service.add_points = AsyncMock()
                    mock_point_service_class.return_value = mock_point_service
                    
                    # Mock the MissionService
                    with patch('services.mission_service.MissionService') as mock_mission_service_class:
                        mock_mission_service = AsyncMock()
                        mock_mission_service.update_progress = AsyncMock()
                        mock_mission_service_class.return_value = mock_mission_service
                        
                        # Mock BOT_MESSAGES
                        with patch('utils.messages.BOT_MESSAGES', {
                            "reaction_registered_points": "¡Has ganado {points} puntos!"
                        }):
                            # Call the handler
                            await handle_reaction_callback(mock_callback, mock_session, mock_bot)
                            
                            # Verify that register_reaction was called with correct parameters
                            mock_service.register_reaction.assert_called_once_with(
                                123456789,  # user_id
                                123456,     # message_id
                                "👍"        # reaction_type
                            )
                            
                            # Verify that point service add_points was called
                            mock_point_service.add_points.assert_called_once_with(
                                123456789,  # user_id
                                1.5,        # points
                                bot=mock_bot,
                                skip_notification=False,
                                source="reaction_👍_message_123456"
                            )
                            
                            # Verify that mission service update_progress was called
                            mock_mission_service.update_progress.assert_called_once_with(
                                123456789,  # user_id
                                "reaction",
                                bot=mock_bot,
                                message_id=123456,
                                reaction_type="👍"
                            )
                            
                            # Verify that update_reaction_markup was called
                            mock_service.update_reaction_markup.assert_called_once_with(
                                -1001234567890,  # chat_id
                                123456           # message_id
                            )
                            
                            # Verify that callback.answer was called with correct message
                            mock_callback.answer.assert_called_once_with(
                                "¡Has ganado 1.5 puntos!"
                            )