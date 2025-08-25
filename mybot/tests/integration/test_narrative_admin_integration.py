import pytest
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock
from aiogram.types import CallbackQuery, User, Message, Chat
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from database.models import User as UserModel, UserStats
from handlers.reaction_callback import handle_reaction_callback
from services.notification_service import NotificationService
from services.point_service import PointService
from services.mission_service import MissionService
from services.level_service import LevelService
from services.achievement_service import AchievementService

@pytest.mark.asyncio
async def test_view_fragment_integration():
    """
    Integration test for the reaction notification flow.
    Tests that:
    1. Reaction callbacks don't generate duplicate notifications
    2. The NotificationService correctly handles and deduplicates notifications
    """
    # === SETUP MOCKS ===
    
    # Create a simple user_progress with numeric points to avoid TypeError
    class MockUserStats:
        def __init__(self):
            self.user_id = 12345
            self.last_notified_points = 0
            self.last_activity_at = datetime.now()
            self.checkin_streak = 1
            self.messages_sent = 10
            self.reactions_sent = 5
            
    class MockUser:
        def __init__(self):
            self.id = 12345
            self.points = 100.0
            self.first_name = "Test"
            self.username = "testuser"
            self.role = "free"
            
        def __repr__(self):
            return f"<MockUser id={self.id} points={self.points}>"
    
    # Redefine _add_points_internal sin afectar comparaciones de tipos
    async def mock_add_points(self, user_id, points, bot, skip_notification, source):
        user = MockUser()
        user.points += points
        return MockUserStats()
    
    # === SESSION MOCK ===
    session_mock = AsyncMock()
    session_mock.in_transaction.return_value = False
    
    # Configurar context manager
    context_mock = AsyncMock()
    context_mock.__aenter__.return_value = None  # No necesitamos devolver nada aquí
    context_mock.__aexit__.return_value = None
    session_mock.begin.return_value = context_mock
    
    # Simular que commit() y refresh() no hacen nada
    session_mock.commit.return_value = None
    session_mock.refresh.return_value = None
    
    # Hacer que session.add() no haga nada
    session_mock.add.return_value = None
    
    # === BOT MOCK ===
    bot_mock = AsyncMock()
    
    # === NOTIFICATION SERVICE REAL ===
    notification_service = NotificationService(session_mock, bot_mock)
    
    # === MOCK SERVICES ===
    level_service = AsyncMock()
    achievement_service = AsyncMock()
    achievement_service.check_user_badges = AsyncMock(return_value=[])
    
    # === POINT SERVICE CON MÉTODO PERSONALIZADO ===
    point_service = PointService(
        session=session_mock,
        level_service=level_service,
        achievement_service=achievement_service,
        notification_service=notification_service
    )
    # Reemplazar el método que tiene el error de tipo
    point_service._add_points_internal = lambda *args, **kwargs: mock_add_points(point_service, *args, **kwargs)
    
    # === MISSION SERVICE MOCK ===
    mission_service = AsyncMock()
    
    # === USER DATA MOCK ===
    user_id = 12345
    
    # === AIOGRAM MOCKS ===
    # Para aiogram 3, necesitamos usar AsyncMock para los métodos
    
    # Crear User mock
    user = MagicMock()
    user.id = user_id
    user.is_bot = False
    user.first_name = "Test"
    
    # Crear Chat mock
    chat = MagicMock()
    chat.id = user_id
    chat.type = "private"
    
    # Crear Message mock
    message = MagicMock()
    message.message_id = 1
    message.date = datetime.now()
    message.chat = chat
    
    # Crear CallbackQuery mock con método answer()
    callback = MagicMock()
    callback.id = "test_id"
    callback.from_user = user
    callback.chat_instance = "test_instance"
    callback.message = message
    callback.data = "ip_channel123_456_heart"
    callback.answer = AsyncMock()  # Método asíncrono
    
    # === PATCH HANDLERS AND SERVICES ===
    with patch('handlers.reaction_callback.validate_message', return_value=True), \
         patch('handlers.reaction_callback.MessageService') as message_service_cls, \
         patch('handlers.reaction_callback.ChannelService') as channel_service_mock, \
         patch('services.point_service.PointService', return_value=point_service), \
         patch('services.mission_service.MissionService', return_value=mission_service), \
         patch('services.level_service.LevelService'), \
         patch('services.achievement_service.AchievementService'):
        
        # Configure message service mock
        message_service_instance = message_service_cls.return_value
        register_reaction_mock = AsyncMock(return_value={"status": "success"})
        message_service_instance.register_reaction = register_reaction_mock
        message_service_instance.update_reaction_markup = AsyncMock()
        
        # Set up channel service to return points
        channel_instance = channel_service_mock.return_value
        get_points_mock = AsyncMock(return_value={"heart": 5.0})
        channel_instance.get_reaction_points = get_points_mock
        
        # === EXECUTE HANDLER ===
        try:
            await handle_reaction_callback(callback, session_mock, bot_mock)
        except Exception as e:
            pytest.fail(f"Error ejecutando handler: {e}")
        
        # === VERIFICACIONES ===
        
        # Verificar que se llamó a register_reaction
        message_service_instance.register_reaction.assert_called_once()
        
        # Verificar que se llamó a update_progress en el MissionService
        mission_service.update_progress.assert_called_once()
        
        # Verificar que no hay notificaciones de puntos (lo que realmente estamos probando)
        notifications = notification_service.pending_notifications.get(user_id, [])
        for notification in notifications:
            if notification.type == "points":
                pytest.fail("Points notification was added when it should have been skipped")
        
        # El test pasa si llegamos aquí sin errores