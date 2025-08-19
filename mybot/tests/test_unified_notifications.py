import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, call
from datetime import datetime

from services.notification_service import (
    NotificationService, 
    NotificationData, 
    NotificationPriority
)

@pytest.fixture
async def notification_service():
    """Fixture para crear servicio de notificaciones mock."""
    mock_session = Mock()
    mock_bot = AsyncMock()
    mock_bot.send_message = AsyncMock()
    
    service = NotificationService(mock_session, mock_bot)
    return service, mock_bot

class TestNotificationAggregation:
    """Tests para el sistema de agregación de notificaciones."""
    
    @pytest.mark.asyncio
    async def test_single_notification_delayed_send(self, notification_service):
        """Verifica que una sola notificación se envíe después del delay."""
        service, mock_bot = notification_service
        user_id = 12345
        
        # Añadir notificación
        await service.add_notification(
            user_id,
            "points",
            {"points": 10, "total": 100},
            priority=NotificationPriority.MEDIUM
        )
        
        # Verificar que no se envía inmediatamente
        assert mock_bot.send_message.call_count == 0
        
        # Esperar el delay de agregación
        await asyncio.sleep(1.2)
        
        # Verificar que se envió
        assert mock_bot.send_message.call_count == 1
        call_args = mock_bot.send_message.call_args
        assert call_args[0][0] == user_id
        assert "10 besitos" in call_args[0][1]
    
    @pytest.mark.asyncio
    async def test_multiple_notifications_aggregated(self, notification_service):
        """Verifica que múltiples notificaciones se agreguen en un mensaje."""
        service, mock_bot = notification_service
        user_id = 12345
        
        # Añadir múltiples notificaciones rápidamente
        await service.add_notification(
            user_id, "points", 
            {"points": 10, "total": 100}
        )
        await service.add_notification(
            user_id, "mission",
            {"name": "Primera Reacción", "points": 20}
        )
        await service.add_notification(
            user_id, "achievement",
            {"name": "Explorador Novato"}
        )
        
        # Esperar el delay
        await asyncio.sleep(1.2)
        
        # Verificar un solo mensaje enviado
        assert mock_bot.send_message.call_count == 1
        
        # Verificar que el mensaje contiene toda la información
        message = mock_bot.send_message.call_args[0][1]
        assert "10 besitos" in message
        assert "Primera Reacción" in message
        assert "Explorador Novato" in message
    
    @pytest.mark.asyncio
    async def test_critical_priority_immediate_send(self, notification_service):
        """Verifica que notificaciones críticas se envíen inmediatamente."""
        service, mock_bot = notification_service
        user_id = 12345
        
        # Añadir notificación crítica
        await service.add_notification(
            user_id,
            "error",
            {"message": "Error crítico"},
            priority=NotificationPriority.CRITICAL
        )
        
        # Pequeña espera para procesar
        await asyncio.sleep(0.2)
        
        # Debe enviarse inmediatamente
        assert mock_bot.send_message.call_count == 1
    
    @pytest.mark.asyncio
    async def test_duplicate_detection(self, notification_service):
        """Verifica que se detecten y filtren duplicados."""
        service, mock_bot = notification_service
        user_id = 12345
        
        # Añadir la misma notificación múltiples veces
        for _ in range(3):
            await service.add_notification(
                user_id,
                "points",
                {"points": 10, "total": 100}
            )
        
        await asyncio.sleep(1.2)
        
        # Solo debe enviarse una vez
        assert mock_bot.send_message.call_count == 1
        message = mock_bot.send_message.call_args[0][1]
        # Verificar que solo aparece una vez la cantidad
        assert message.count("10 besitos") == 1
    
    @pytest.mark.asyncio
    async def test_max_queue_force_send(self, notification_service):
        """Verifica que se fuerce envío cuando la cola está llena."""
        service, mock_bot = notification_service
        service.max_queue_size = 5
        user_id = 12345
        
        # Añadir notificaciones hasta llenar la cola
        for i in range(5):
            await service.add_notification(
                user_id,
                "points",
                {"points": i+1, "total": (i+1)*10},
                priority=NotificationPriority.LOW
            )
        
        # Pequeña espera para procesar
        await asyncio.sleep(0.2)
        
        # Debe haberse enviado al alcanzar el límite
        assert mock_bot.send_message.call_count == 1
    
    @pytest.mark.asyncio
    async def test_flush_pending_notifications(self, notification_service):
        """Verifica el flush manual de notificaciones."""
        service, mock_bot = notification_service
        user_id = 12345
        
        # Añadir notificaciones
        await service.add_notification(
            user_id, "points", {"points": 10, "total": 100}
        )
        await service.add_notification(
            user_id, "mission", {"name": "Test Mission", "points": 20}
        )
        
        # Flush inmediato
        await service.flush_pending_notifications(user_id)
        
        # Debe enviarse inmediatamente
        await asyncio.sleep(0.1)
        assert mock_bot.send_message.call_count == 1
    
    @pytest.mark.asyncio
    async def test_message_formatting_diana_personality(self, notification_service):
        """Verifica que los mensajes mantengan la personalidad de Diana."""
        service, mock_bot = notification_service
        user_id = 12345
        
        # Añadir varias notificaciones
        await service.add_notification(
            user_id, "points", {"points": 50, "total": 500}
        )
        await service.add_notification(
            user_id, "achievement", 
            {"name": "Amante Dedicado", "description": "Has demostrado tu devoción"}
        )
        await service.add_notification(
            user_id, "hint",
            {"text": "El jardín esconde más secretos de los que imaginas..."}
        )
        
        await asyncio.sleep(1.2)
        
        message = mock_bot.send_message.call_args[0][1]
        
        # Verificar elementos de personalidad de Diana
        assert "Diana" in message
        assert "💋" in message
        assert any(word in message for word in ["amor", "cariño", "querido", "mi"])
        assert "━━━" in message  # Separadores visuales

class TestCoordinadorIntegration:
    """Tests de integración con el CoordinadorCentral."""
    
    @pytest.mark.asyncio
    async def test_reaction_flow_unified_notifications(self):
        """Verifica el flujo completo de reacción con notificaciones unificadas."""
        from services.coordinador_central import CoordinadorCentral, AccionUsuario
        
        with patch('services.coordinador_central.NotificationService') as MockNotificationService:
            mock_notification = AsyncMock()
            MockNotificationService.return_value = mock_notification
            
            mock_session = Mock()
            coordinador = CoordinadorCentral(mock_session)
            
            # Simular resultado de reacción completa
            with patch.object(coordinador, '_flujo_reaccion_publicacion') as mock_flujo:
                mock_flujo.return_value = {
                    "success": True,
                    "points_awarded": 10,
                    "total_points": 150,
                    "missions_completed": [
                        {"name": "Primera Reacción", "points": 20}
                    ],
                    "hint_unlocked": "Un nuevo secreto se revela...",
                    "achievement_unlocked": "Explorador",
                    "level_up": True,
                    "new_level": 5
                }
                
                mock_bot = AsyncMock()
                result = await coordinador.ejecutar_flujo(
                    user_id=12345,
                    accion=AccionUsuario.REACCIONAR_PUBLICACION_NATIVA,
                    message_id=1,
                    channel_id=100,
                    reaction_type="💋",
                    bot=mock_bot
                )
                
                # Verificar que se añadieron todas las notificaciones
                assert mock_notification.add_notification.call_count >= 5
                
                # Verificar tipos de notificaciones
                call_types = [
                    call[0][1] for call in 
                    mock_notification.add_notification.call_args_list
                ]
                assert "points" in call_types
                assert "mission" in call_types
                assert "achievement" in call_types
                assert "level" in call_types
                assert "hint" in call_types

class TestNotificationConfig:
    """Tests para la configuración del sistema."""
    
    def test_config_default_values(self):
        """Verifica valores por defecto de configuración."""
        from services.notification_config import NotificationConfig
        
        config = NotificationConfig()
        
        assert config.max_queue_size == 10
        assert config.enable_aggregation == True
        assert config.aggregation_delays[NotificationPriority.CRITICAL] == 0.1
        assert config.aggregation_delays[NotificationPriority.HIGH] == 0.5
        assert config.message_format["diana_personality"] == True
    
    def test_config_from_dict(self):
        """Verifica creación de configuración desde diccionario."""
        from services.notification_config import NotificationConfig
        
        config = NotificationConfig(
            max_queue_size=20,
            enable_aggregation=False,
            aggregation_delays={0: 0.0, 1: 0.2, 2: 0.5, 3: 1.0}
        )
        
        assert config.max_queue_size == 20
        assert config.enable_aggregation == False
        assert config.aggregation_delays[0] == 0.0
    
    @pytest.mark.asyncio
    async def test_config_affects_service_behavior(self, tmp_path):
        """Verifica que la configuración afecte el comportamiento del servicio."""
        from services.notification_config import NotificationConfig, set_notification_config
        
        # Configurar para envío inmediato
        config = NotificationConfig(
            enable_aggregation=False,
            aggregation_delays={0: 0, 1: 0, 2: 0, 3: 0}
        )
        set_notification_config(config)
        
        mock_session = Mock()
        mock_bot = AsyncMock()
        
        service = NotificationService(mock_session, mock_bot)
        
        # Con agregación deshabilitada, debe enviar inmediatamente
        await service.add_notification(
            12345, "points", {"points": 10}, 
            priority=NotificationPriority.LOW
        )
        
        await asyncio.sleep(0.1)
        
        # Debe haberse enviado sin esperar
        assert mock_bot.send_message.call_count == 1