"""
Tests de protección para la cadena de middleware - Critical Infrastructure.
Estos tests protegen el orden y funcionamiento de los middlewares durante refactoring.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Update, Message, User as TelegramUser, Chat, MessageReactionUpdated, PollAnswer
from sqlalchemy.ext.asyncio import AsyncSession

from middlewares.user_middleware import UserRegistrationMiddleware
from middlewares.points_middleware import PointsMiddleware
from database.models import User


@pytest.mark.asyncio
class TestMiddlewareChainProtection:
    """Tests críticos para la cadena de middleware que procesa todos los eventos."""

    async def test_user_middleware_registro_nuevo_usuario(self, session_factory):
        """
        CRITICAL: Test que protege el registro automático de usuarios nuevos.
        Todo usuario que interactúe debe ser registrado automáticamente.
        """
        async with session_factory() as session:
            middleware = UserRegistrationMiddleware()
            
            # Setup mock handler
            handler = AsyncMock()
            
            # Create realistic Telegram update
            telegram_user = TelegramUser(
                id=999888777,
                is_bot=False,
                first_name="NewUser",
                last_name="TestLast",
                username="newuser123"
            )
            
            message = MagicMock()
            message.from_user = telegram_user
            
            update = MagicMock()
            update.message = message
            
            data = {"session": session}
            
            # Execute middleware
            await middleware(handler, update, data)
            
            # Critical assertions - new user must be created and tracked
            assert "user" in data, "User must be added to data context"
            created_user = data["user"]
            assert created_user.id == 999888777, "User ID must match Telegram ID"
            assert created_user.first_name == "NewUser", "First name must be preserved"
            assert created_user.last_name == "TestLast", "Last name must be preserved"
            assert created_user.username == "newuser123", "Username must be preserved"
            assert created_user.role == "free", "New users must default to 'free' role"
            
            # Verify handler was called with enriched data
            handler.assert_called_once_with(update, data)

    async def test_user_middleware_usuario_existente(self, session, test_user):
        """
        CRITICAL: Test que protege el manejo de usuarios existentes.
        Usuarios existentes deben ser recuperados sin duplicación.
        """
        middleware = UserRegistrationMiddleware()
        handler = AsyncMock()
        
        telegram_user = TelegramUser(
            id=test_user.id,
            is_bot=False,
            first_name="UpdatedName",
            username="updatedusername"
        )
        
        message = MagicMock()
        message.from_user = telegram_user
        
        update = MagicMock()
        update.message = message
        
        data = {"session": session}
        
        # Execute middleware
        await middleware(handler, update, data)
        
        # Critical assertions - existing user must be retrieved
        assert "user" in data, "Existing user must be added to data context"
        retrieved_user = data["user"]
        assert retrieved_user.id == test_user.id, "Correct user must be retrieved"
        # Note: middleware should not update existing user data automatically
        
        handler.assert_called_once_with(update, data)

    async def test_user_middleware_callback_query_handling(self, session_factory):
        """
        CRITICAL: Test que protege el manejo de callback queries.
        Los callback queries también deben registrar/recuperar usuarios.
        """
        async with session_factory() as session:
            middleware = UserRegistrationMiddleware()
            handler = AsyncMock()
            
            telegram_user = TelegramUser(
                id=777666555,
                is_bot=False,
                first_name="CallbackUser",
                username="callbackuser"
            )
            
            callback_query = MagicMock()
            callback_query.from_user = telegram_user
            
            update = MagicMock()
            update.message = None
            update.callback_query = callback_query
            
            data = {"session": session}
            
            await middleware(handler, update, data)
            
            # Critical assertions - callback queries must also register users
            assert "user" in data, "User must be registered from callback query"
            created_user = data["user"]
            assert created_user.id == 777666555, "User ID must match from callback"
            
            handler.assert_called_once_with(update, data)

    async def test_user_middleware_error_handling_sin_session(self):
        """
        CRITICAL: Test que protege el comportamiento sin sesión de BD.
        El middleware NO debe fallar si no hay sesión disponible.
        """
        middleware = UserRegistrationMiddleware()
        handler = AsyncMock()
        
        update = MagicMock()
        data = {}  # No session provided
        
        # Execute middleware
        await middleware(handler, update, data)
        
        # Critical assertions - must not crash without session
        handler.assert_called_once_with(update, data)
        assert "user" not in data, "No user should be added without session"

    @patch('middlewares.user_middleware.logger')
    async def test_user_middleware_error_handling_excepcion_bd(self, mock_logger, session):
        """
        CRITICAL: Test que protege el manejo de errores de BD.
        Errores de BD NO deben romper el flujo del middleware.
        """
        middleware = UserRegistrationMiddleware()
        handler = AsyncMock()
        
        # Mock session to raise exception
        session.get = AsyncMock(side_effect=Exception("Database error"))
        
        telegram_user = TelegramUser(id=123, is_bot=False, first_name="Test")
        message = MagicMock()
        message.from_user = telegram_user
        
        update = MagicMock()
        update.message = message
        
        data = {"session": session}
        
        # Execute middleware - should not raise exception
        await middleware(handler, update, data)
        
        # Critical assertions - must handle errors gracefully
        handler.assert_called_once_with(update, data)
        mock_logger.error.assert_called_once()
        # Should continue even if user registration fails

    async def test_points_middleware_award_message_points(self, session, test_user, mock_bot):
        """
        CRITICAL: Test que protege el otorgamiento de puntos por mensajes.
        Los mensajes de usuarios deben otorgar puntos automáticamente.
        """
        middleware = PointsMiddleware()
        handler = AsyncMock()
        
        telegram_user = TelegramUser(
            id=test_user.id,
            is_bot=False,
            first_name="TestUser"
        )
        
        message = Message(
            message_id=123,
            from_user=telegram_user,
            date=1234567890,
            chat=Chat(id=test_user.id, type="private"),
            content_type="text",
            options={}
        )
        message.text = "Hello Diana!"  # Non-command message
        
        data = {"session": session, "bot": mock_bot}
        
        with patch('middlewares.points_middleware.PointService') as mock_point_service, \
             patch('middlewares.points_middleware.MissionService') as mock_mission_service, \
             patch('middlewares.points_middleware.is_admin', return_value=False):
            
            mock_service_instance = AsyncMock()
            mock_point_service.return_value = mock_service_instance
            
            mock_mission_instance = AsyncMock()
            mock_mission_instance.increment_challenge_progress.return_value = []
            mock_mission_service.return_value = mock_mission_instance
            
            await middleware(handler, message, data)
            
            # Critical assertions - message points must be awarded
            mock_service_instance.award_message.assert_called_once_with(test_user.id, mock_bot)
            mock_mission_instance.update_progress.assert_called_once_with(test_user.id, "messages", bot=mock_bot)
            handler.assert_called_once_with(message, data)

    async def test_points_middleware_ignore_commands(self, session, test_user, mock_bot):
        """
        CRITICAL: Test que protege el ignorado de comandos para puntos.
        Los comandos (/start, /help, etc.) NO deben otorgar puntos.
        """
        middleware = PointsMiddleware()
        handler = AsyncMock()
        
        telegram_user = TelegramUser(
            id=test_user.id,
            is_bot=False,
            first_name="TestUser"
        )
        
        message = Message(
            message_id=123,
            from_user=telegram_user,
            date=1234567890,
            chat=Chat(id=test_user.id, type="private"),
            content_type="text",
            options={}
        )
        message.text = "/start"  # Command message
        
        data = {"session": session, "bot": mock_bot}
        
        with patch('middlewares.points_middleware.PointService') as mock_point_service, \
             patch('middlewares.points_middleware.is_admin', return_value=False):
            
            mock_service_instance = AsyncMock()
            mock_point_service.return_value = mock_service_instance
            
            await middleware(handler, message, data)
            
            # Critical assertions - commands must not award points
            mock_service_instance.award_message.assert_not_called()
            handler.assert_called_once_with(message, data)

    async def test_points_middleware_ignore_admin_users(self, session, admin_user, mock_bot):
        """
        CRITICAL: Test que protege el ignorado de usuarios admin para puntos.
        Los usuarios admin NO deben recibir puntos por sus acciones.
        """
        middleware = PointsMiddleware()
        handler = AsyncMock()
        
        telegram_user = TelegramUser(
            id=admin_user.id,
            is_bot=False,
            first_name="AdminUser"
        )
        
        message = Message(
            message_id=123,
            from_user=telegram_user,
            date=1234567890,
            chat=Chat(id=admin_user.id, type="private"),
            content_type="text",
            options={}
        )
        message.text = "Admin message"
        
        data = {"session": session, "bot": mock_bot}
        
        with patch('middlewares.points_middleware.PointService') as mock_point_service, \
             patch('middlewares.points_middleware.is_admin', return_value=True):
            
            mock_service_instance = AsyncMock()
            mock_point_service.return_value = mock_service_instance
            
            await middleware(handler, message, data)
            
            # Critical assertions - admin users must not get points
            mock_service_instance.award_message.assert_not_called()
            handler.assert_called_once_with(message, data)

    async def test_points_middleware_reaction_handling(self, session, test_user, mock_bot):
        """
        CRITICAL: Test que protege el manejo de reacciones para puntos.
        Las reacciones deben otorgar puntos y registrar actividad.
        """
        middleware = PointsMiddleware()
        handler = AsyncMock()
        
        # Mock MessageReactionUpdated event
        reaction_event = MagicMock()
        reaction_event.user = MagicMock()
        reaction_event.user.id = test_user.id
        reaction_event.message_id = 456
        
        # Simulate the isinstance check
        reaction_event.__class__.__name__ = 'MessageReactionUpdated'
        
        data = {"session": session, "bot": mock_bot}
        
        with patch('middlewares.points_middleware.PointService') as mock_point_service, \
             patch('middlewares.points_middleware.MissionService') as mock_mission_service, \
             patch('middlewares.points_middleware.isinstance') as mock_isinstance, \
             patch('middlewares.points_middleware.is_admin', return_value=False):
            
            # Configure isinstance to return True for MessageReactionUpdated
            def isinstance_side_effect(obj, cls):
                if hasattr(cls, '__name__') and cls.__name__ == 'MessageReactionUpdated':
                    return True
                return False
            mock_isinstance.side_effect = isinstance_side_effect
            
            mock_service_instance = AsyncMock()
            mock_point_service.return_value = mock_service_instance
            
            mock_mission_instance = AsyncMock()
            mock_mission_instance.increment_challenge_progress.return_value = []
            mock_mission_service.return_value = mock_mission_instance
            
            # Mock user creation for reaction
            session.get.return_value = test_user
            
            await middleware(handler, reaction_event, data)
            
            # Critical assertions - reactions must award points
            mock_service_instance.award_reaction.assert_called_once()
            mock_mission_instance.update_progress.assert_called_once_with(test_user.id, "reaction", bot=mock_bot)
            handler.assert_called_once_with(reaction_event, data)

    async def test_points_middleware_poll_answer_handling(self, session, test_user, mock_bot):
        """
        CRITICAL: Test que protege el manejo de respuestas a encuestas.
        Las respuestas a polls deben otorgar puntos.
        """
        middleware = PointsMiddleware()
        handler = AsyncMock()
        
        poll_answer = PollAnswer(
            poll_id="poll123",
            user=TelegramUser(id=test_user.id, is_bot=False, first_name="Test"),
            option_ids=[0]
        )
        
        data = {"session": session, "bot": mock_bot}
        
        with patch('middlewares.points_middleware.PointService') as mock_point_service, \
             patch('middlewares.points_middleware.is_admin', return_value=False):
            
            mock_service_instance = AsyncMock()
            mock_point_service.return_value = mock_service_instance
            
            await middleware(handler, poll_answer, data)
            
            # Critical assertions - poll answers must award points
            mock_service_instance.award_poll.assert_called_once_with(test_user.id, mock_bot)
            handler.assert_called_once_with(poll_answer, data)

    @patch('middlewares.points_middleware.logger')
    async def test_points_middleware_error_handling(self, mock_logger, session, test_user, mock_bot):
        """
        CRITICAL: Test que protege el manejo de errores en points middleware.
        Los errores de puntos NO deben romper el flujo del handler.
        """
        middleware = PointsMiddleware()
        handler = AsyncMock()
        
        telegram_user = TelegramUser(
            id=test_user.id,
            is_bot=False,
            first_name="TestUser"
        )
        
        message = Message(
            message_id=123,
            from_user=telegram_user,
            date=1234567890,
            chat=Chat(id=test_user.id, type="private"),
            content_type="text",
            options={}
        )
        message.text = "Test message"
        
        data = {"session": session, "bot": mock_bot}
        
        with patch('middlewares.points_middleware.PointService') as mock_point_service, \
             patch('middlewares.points_middleware.is_admin', return_value=False):
            
            # Make service raise exception
            mock_service_instance = AsyncMock()
            mock_service_instance.award_message.side_effect = Exception("Points service error")
            mock_point_service.return_value = mock_service_instance
            
            # Execute middleware - should not raise exception
            await middleware(handler, message, data)
            
            # Critical assertions - must handle errors gracefully
            handler.assert_called_once_with(message, data)
            mock_logger.exception.assert_called_once()

    async def test_middleware_chain_order_integration(self, session_factory, mock_bot):
        """
        CRITICAL: Test de integración que protege el orden de la cadena de middleware.
        El orden debe ser: UserRegistration -> Points -> Handler.
        """
        async with session_factory() as session:
            user_middleware = UserRegistrationMiddleware()
            points_middleware = PointsMiddleware()
            
            final_handler = AsyncMock()
            
            # Create chain: final_handler -> points_middleware -> user_middleware
            def create_chain():
                async def combined_handler(event, data):
                    # First: user middleware
                    async def points_handler(event, data):
                        # Second: points middleware  
                        return await points_middleware(final_handler, event, data)
                    return await user_middleware(points_handler, event, data)
                return combined_handler
            
            chain_handler = create_chain()
            
            # Create test event
            telegram_user = TelegramUser(
                id=555444333,
                is_bot=False,
                first_name="ChainTest",
                username="chaintest"
            )
            
            message = Message(
                message_id=123,
                from_user=telegram_user,
                date=1234567890,
                chat=Chat(id=555444333, type="private"),
                content_type="text",
                options={}
            )
            message.text = "Chain test message"
            
            data = {"session": session, "bot": mock_bot}
            
            with patch('middlewares.points_middleware.PointService') as mock_point_service, \
                 patch('middlewares.points_middleware.MissionService') as mock_mission_service, \
                 patch('middlewares.points_middleware.is_admin', return_value=False):
                
                mock_service_instance = AsyncMock()
                mock_point_service.return_value = mock_service_instance
                
                mock_mission_instance = AsyncMock()
                mock_mission_instance.increment_challenge_progress.return_value = []
                mock_mission_service.return_value = mock_mission_instance
                
                # Execute chain
                await chain_handler(message, data)
                
                # Critical assertions - chain must work correctly
                assert "user" in data, "User middleware must have added user to context"
                created_user = data["user"]
                assert created_user.id == 555444333, "Correct user must be created"
                
                # Points middleware should have run after user middleware
                mock_service_instance.award_message.assert_called_once_with(555444333, mock_bot)
                
                # Final handler should receive enriched data
                final_handler.assert_called_once_with(message, data)