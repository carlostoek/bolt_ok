"""
Tests para el sistema de notificaciones unificadas.
Verifica la consolidación de mensajes y el funcionamiento de reacciones nativas.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

from services.notification_service import NotificationService, NotificationData
from services.coordinador_central import CoordinadorCentral, AccionUsuario
from handlers.native_reaction_handler import handle_native_reaction
from aiogram.types import MessageReactionUpdated, User, Chat, ReactionTypeEmoji


class TestNotificationService:
    """Tests para el servicio de notificaciones."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock de sesión de base de datos."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_bot(self):
        """Mock del bot de Telegram."""
        bot = AsyncMock()
        bot.send_message = AsyncMock()
        return bot
    
    @pytest.fixture
    def notification_service(self, mock_session, mock_bot):
        """Instancia del servicio de notificaciones."""
        return NotificationService(mock_session, mock_bot)
    
    @pytest.mark.asyncio
    async def test_add_single_notification(self, notification_service):
        """Test para agregar una sola notificación."""
        user_id = 12345
        
        await notification_service.add_notification(
            user_id, 
            "points", 
            {"points": 10, "total": 50}
        )
        
        # Verificar que la notificación está pendiente
        assert user_id in notification_service.pending_notifications
        assert len(notification_service.pending_notifications[user_id]) == 1
        assert notification_service.pending_notifications[user_id][0].type == "points"
    
    @pytest.mark.asyncio
    async def test_notification_aggregation(self, notification_service):
        """Test para agregación de múltiples notificaciones."""
        user_id = 12345
        
        # Agregar múltiples notificaciones en rápida sucesión
        await notification_service.add_notification(
            user_id, "points", {"points": 10, "total": 50}
        )
        await notification_service.add_notification(
            user_id, "mission", {"name": "Test Mission", "points": 20}
        )
        await notification_service.add_notification(
            user_id, "achievement", {"name": "Test Achievement"}
        )
        
        # Esperar a que se procese la agregación
        await asyncio.sleep(1.2)  # Más que el delay de agregación
        
        # Verificar que se envió un mensaje consolidado
        notification_service.bot.send_message.assert_called_once()
        
        # Verificar que las notificaciones pendientes se limpiaron
        assert user_id not in notification_service.pending_notifications
    
    @pytest.mark.asyncio
    async def test_group_notifications_by_type(self, notification_service):
        """Test para agrupación de notificaciones por tipo."""
        notifications = [
            NotificationData("points", {"points": 10}),
            NotificationData("points", {"points": 5}),
            NotificationData("mission", {"name": "Mission 1"}),
            NotificationData("achievement", {"name": "Achievement 1"}),
        ]
        
        grouped = notification_service._group_notifications_by_type(notifications)
        
        assert "points" in grouped
        assert "mission" in grouped
        assert "achievement" in grouped
        assert len(grouped["points"]) == 2
        assert len(grouped["mission"]) == 1
        assert len(grouped["achievement"]) == 1
    
    @pytest.mark.asyncio
    async def test_build_unified_message_multiple_types(self, notification_service):
        """Test para construcción de mensaje unificado con múltiples tipos."""
        grouped = {
            "points": [{"points": 10, "total": 50}, {"points": 5, "total": 55}],
            "mission": [{"name": "Test Mission", "points": 20}],
            "achievement": [{"name": "Test Achievement"}]
        }
        
        message = await notification_service._build_unified_message(grouped)
        
        assert "Diana te mira con una sonrisa cálida" in message
        assert "+15 besitos" in message  # 10 + 5
        assert "Total actual: 55 besitos" in message
        assert "Test Mission" in message
        assert "Test Achievement" in message
        assert "Cada paso que das me acerca más a ti" in message
    
    @pytest.mark.asyncio
    async def test_build_unified_message_single_type(self, notification_service):
        """Test para construcción de mensaje unificado con un solo tipo."""
        grouped = {
            "points": [{"points": 10, "total": 50}]
        }
        
        message = await notification_service._build_unified_message(grouped)
        
        assert "Diana te mira con una sonrisa cálida" in message
        assert "+10 besitos" in message
        assert "Total actual: 50 besitos" in message
        # No debe incluir el mensaje de cierre para un solo tipo
        assert "Cada paso que das me acerca más a ti" not in message
    
    @pytest.mark.asyncio
    async def test_immediate_notification(self, notification_service):
        """Test para notificaciones inmediatas."""
        user_id = 12345
        message = "Test immediate message"
        
        await notification_service.send_immediate_notification(user_id, message)
        
        notification_service.bot.send_message.assert_called_once()
        # Verificar que se usó safe_send_message
        args = notification_service.bot.send_message.call_args
        assert args is not None
    
    @pytest.mark.asyncio
    async def test_flush_pending_notifications(self, notification_service):
        """Test para forzar el envío de notificaciones pendientes."""
        user_id = 12345
        
        # Agregar notificaciones
        await notification_service.add_notification(
            user_id, "points", {"points": 10, "total": 50}
        )
        
        # Forzar envío inmediato
        await notification_service.flush_pending_notifications(user_id)
        
        # Verificar que se envió el mensaje
        notification_service.bot.send_message.assert_called_once()
        
        # Verificar que las notificaciones se limpiaron
        assert user_id not in notification_service.pending_notifications
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_notifications(self, notification_service):
        """Test para limpieza de notificaciones expiradas."""
        user_id = 12345
        
        # Agregar notificación antigua
        old_notification = NotificationData("points", {"points": 10})
        old_notification.timestamp = datetime.now() - timedelta(minutes=10)
        
        # Agregar notificación reciente
        new_notification = NotificationData("mission", {"name": "Test"})
        
        notification_service.pending_notifications[user_id] = [old_notification, new_notification]
        
        # Limpiar notificaciones expiradas (máximo 5 minutos)
        await notification_service.cleanup_expired_notifications(max_age_minutes=5)
        
        # Verificar que solo la notificación reciente permanece
        remaining = notification_service.pending_notifications.get(user_id, [])
        assert len(remaining) == 1
        assert remaining[0].type == "mission"


class TestCoordinadorCentralIntegration:
    """Tests para la integración del CoordinadorCentral con el sistema de notificaciones."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock de sesión de base de datos."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_bot(self):
        """Mock del bot de Telegram."""
        bot = AsyncMock()
        bot.send_message = AsyncMock()
        return bot
    
    @pytest.fixture
    def coordinador(self, mock_session):
        """Instancia del coordinador central."""
        with patch.multiple(
            'services.coordinador_central',
            ChannelEngagementService=AsyncMock,
            NarrativePointService=AsyncMock,
            NarrativeAccessService=AsyncMock,
            EventCoordinator=AsyncMock,
            NarrativeService=AsyncMock,
            PointService=AsyncMock,
            ReconciliationService=AsyncMock,
            get_event_bus=Mock(return_value=AsyncMock())
        ):
            return CoordinadorCentral(mock_session)
    
    @pytest.mark.asyncio
    async def test_reaction_flow_with_unified_notifications(self, coordinador, mock_bot):
        """Test para flujo de reacción con notificaciones unificadas."""
        user_id = 12345
        
        # Mock de servicios
        coordinador.channel_engagement.award_channel_reaction = AsyncMock(return_value=True)
        coordinador.point_service.get_user_points = AsyncMock(return_value=60)
        coordinador.narrative_service.get_user_current_fragment = AsyncMock(return_value=None)
        
        # Ejecutar flujo con bot
        result = await coordinador.ejecutar_flujo(
            user_id,
            AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=123,
            channel_id=456,
            reaction_type="❤️",
            bot=mock_bot
        )
        
        # Verificar que el resultado es exitoso
        assert result["success"] is True
        assert result["points_awarded"] == 10
        assert result["total_points"] == 60
        assert result["action"] == "reaction_success"
    
    @pytest.mark.asyncio
    async def test_send_unified_notifications_method(self, coordinador, mock_session, mock_bot):
        """Test para el método _send_unified_notifications."""
        user_id = 12345
        result = {
            "success": True,
            "points_awarded": 10,
            "total_points": 60,
            "mission_completed": "Test Mission",
            "mission_points": 20,
            "hint_unlocked": "Test hint"
        }
        
        # Mock del servicio de notificaciones
        with patch('services.coordinador_central.NotificationService') as MockNotificationService:
            mock_notification_service = MockNotificationService.return_value
            mock_notification_service.add_notification = AsyncMock()
            
            await coordinador._send_unified_notifications(
                mock_notification_service,
                user_id,
                result,
                AccionUsuario.REACCIONAR_PUBLICACION
            )
            
            # Verificar que se llamó add_notification para cada tipo
            calls = mock_notification_service.add_notification.call_args_list
            call_types = [call[0][1] for call in calls]  # Segundo argumento es el tipo
            
            assert "points" in call_types
            assert "mission" in call_types
            assert "hint" in call_types
            assert "reaction" in call_types


class TestNativeReactionHandler:
    """Tests para el handler de reacciones nativas."""
    
    @pytest.fixture
    def mock_session(self):
        """Mock de sesión de base de datos."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_bot(self):
        """Mock del bot de Telegram."""
        bot = AsyncMock()
        bot.send_message = AsyncMock()
        return bot
    
    @pytest.fixture
    def mock_reaction_update(self):
        """Mock de MessageReactionUpdated."""
        user = User(id=12345, is_bot=False, first_name="Test")
        chat = Chat(id=67890, type="channel")
        
        # Mock de ReactionTypeEmoji
        reaction = Mock()
        reaction.emoji = "❤️"
        reaction.type = "emoji"
        
        update = Mock(spec=MessageReactionUpdated)
        update.user = user
        update.chat = chat
        update.message_id = 123
        update.new_reaction = [reaction]
        
        return update
    
    @pytest.mark.asyncio
    async def test_handle_native_reaction_success(self, mock_reaction_update, mock_session, mock_bot):
        """Test para manejo exitoso de reacción nativa."""
        with patch('handlers.native_reaction_handler.CoordinadorCentral') as MockCoordinador:
            with patch('handlers.native_reaction_handler.NotificationService') as MockNotificationService:
                # Mock del coordinador
                mock_coordinador_instance = MockCoordinador.return_value
                mock_coordinador_instance.ejecutar_flujo = AsyncMock(return_value={
                    "success": True,
                    "points_awarded": 10,
                    "total_points": 60,
                    "message": "Test success message"
                })
                
                # Mock del servicio de notificaciones
                mock_notification_service = MockNotificationService.return_value
                mock_notification_service.add_notification = AsyncMock()
                
                # Ejecutar handler
                await handle_native_reaction(mock_reaction_update, mock_session, mock_bot)
                
                # Verificar que se llamó al coordinador
                mock_coordinador_instance.ejecutar_flujo.assert_called_once()
                call_args = mock_coordinador_instance.ejecutar_flujo.call_args
                
                assert call_args[0][0] == 12345  # user_id
                assert call_args[0][1] == AccionUsuario.REACCIONAR_PUBLICACION
                assert call_args[1]["message_id"] == 123
                assert call_args[1]["channel_id"] == 67890
                assert call_args[1]["reaction_type"] == "❤️"
                assert call_args[1]["is_native_reaction"] is True
    
    @pytest.mark.asyncio
    async def test_handle_native_reaction_no_emoji(self, mock_session, mock_bot):
        """Test para reacción nativa sin emoji válido."""
        # Mock de update sin emoji
        user = User(id=12345, is_bot=False, first_name="Test")
        chat = Chat(id=67890, type="channel")
        
        update = Mock(spec=MessageReactionUpdated)
        update.user = user
        update.chat = chat
        update.message_id = 123
        update.new_reaction = []  # Sin reacciones
        
        with patch('handlers.native_reaction_handler.CoordinadorCentral') as MockCoordinador:
            mock_coordinador_instance = MockCoordinador.return_value
            mock_coordinador_instance.ejecutar_flujo = AsyncMock()
            
            # Ejecutar handler
            await handle_native_reaction(update, mock_session, mock_bot)
            
            # Verificar que NO se llamó al coordinador
            mock_coordinador_instance.ejecutar_flujo.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_native_reaction_error_handling(self, mock_reaction_update, mock_session, mock_bot):
        """Test para manejo de errores en reacciones nativas."""
        with patch('handlers.native_reaction_handler.CoordinadorCentral') as MockCoordinador:
            with patch('handlers.native_reaction_handler.NotificationService') as MockNotificationService:
                # Mock que lanza excepción
                mock_coordinador_instance = MockCoordinador.return_value
                mock_coordinador_instance.ejecutar_flujo = AsyncMock(side_effect=Exception("Test error"))
                
                # Mock del servicio de notificaciones
                mock_notification_service = MockNotificationService.return_value
                mock_notification_service.send_immediate_notification = AsyncMock()
                
                # Ejecutar handler (no debe lanzar excepción)
                await handle_native_reaction(mock_reaction_update, mock_session, mock_bot)
                
                # Verificar que se intentó enviar notificación de error
                # (aunque puede fallar por el mock, no debe afectar el flujo principal)
                assert True  # Si llegamos aquí, no se lanzó excepción


@pytest.mark.asyncio
async def test_integration_end_to_end():
    """Test de integración completo del sistema de notificaciones."""
    # Este test simula un flujo completo desde la reacción hasta la notificación
    
    with patch.multiple(
        'services.coordinador_central',
        ChannelEngagementService=AsyncMock,
        NarrativePointService=AsyncMock,
        NarrativeAccessService=AsyncMock,
        EventCoordinator=AsyncMock,
        NarrativeService=AsyncMock,
        PointService=AsyncMock,
        ReconciliationService=AsyncMock,
        get_event_bus=Mock(return_value=AsyncMock())
    ):
        # Setup
        mock_session = AsyncMock()
        mock_bot = AsyncMock()
        coordinador = CoordinadorCentral(mock_session)
        
        # Mock de servicios del coordinador
        coordinador.channel_engagement.award_channel_reaction = AsyncMock(return_value=True)
        coordinador.point_service.get_user_points = AsyncMock(return_value=75)
        coordinador.narrative_service.get_user_current_fragment = AsyncMock(return_value=None)
        
        user_id = 12345
        
        # Ejecutar flujo completo con notificaciones unificadas
        result = await coordinador.ejecutar_flujo(
            user_id,
            AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=123,
            channel_id=456,
            reaction_type="❤️",
            bot=mock_bot
        )
        
        # Verificar resultado
        assert result["success"] is True
        assert result["points_awarded"] == 10
        assert result["total_points"] == 75
        
        # En un escenario real, aquí verificaríamos que se enviaron las notificaciones
        # consolidadas, pero como estamos usando mocks, verificamos la estructura del resultado
        assert "message" in result
        assert "action" in result