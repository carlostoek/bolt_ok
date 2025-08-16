"""
Tests de protección para Channel Engagement Service - Critical Point/Besitos System.
Estos tests protegen el sistema de gamificación durante refactoring.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.integration.channel_engagement_service import ChannelEngagementService
from database.models import User, UserStats

@pytest.mark.asyncio
class TestChannelEngagementProtection:
    """Tests críticos para el servicio de engagement que maneja puntos y gamificación."""

    async def test_award_channel_reaction_usuario_valido_canal_gestionado(self, session, test_user, test_channel):
        """
        CRITICAL: Test que protege el otorgamiento de puntos por reacciones.
        Las reacciones en canales gestionados DEBEN otorgar puntos.
        """
        service = ChannelEngagementService(session)
        
        # Mock managed channels to include test channel
        service.config_service.get_managed_channels = AsyncMock(return_value={str(test_channel.id): "vip"})
        service.point_service.award_reaction = AsyncMock()
        
        mock_bot = AsyncMock()
        
        # Execute critical flow
        result = await service.award_channel_reaction(
            test_user.id,
            message_id=123,
            channel_id=test_channel.id,
            bot=mock_bot
        )
        
        # Critical assertions - reactions must award points in managed channels
        assert result is True, "Reactions in managed channels must succeed"
        service.point_service.award_reaction.assert_called_once_with(test_user, 123, mock_bot)
        
    async def test_award_channel_reaction_canal_no_gestionado(self, session, test_user):
        """
        CRITICAL: Test que protege contra otorgar puntos en canales no gestionados.
        Las reacciones en canales no gestionados NO deben otorgar puntos.
        """
        service = ChannelEngagementService(session)
        
        # Mock empty managed channels
        service.config_service.get_managed_channels = AsyncMock(return_value={})
        service.point_service.award_reaction = AsyncMock()
        
        # Execute with unmanaged channel
        result = await service.award_channel_reaction(
            test_user.id,
            message_id=123,
            channel_id=-9999999999,  # Unmanaged channel
            bot=None
        )
        
        # Critical assertions - unmanaged channels must not award points
        assert result is False, "Unmanaged channels must not award points"
        service.point_service.award_reaction.assert_not_called()
        
    async def test_award_channel_participation_tipos_accion(self, session, test_user):
        """
        CRITICAL: Test que protege los diferentes tipos de participación.
        Cada tipo de acción debe otorgar la cantidad correcta de puntos.
        """
        service = ChannelEngagementService(session)
        
        # Mock managed channel
        service.config_service.get_managed_channels = AsyncMock(return_value={"-123456": "vip"})
        service.point_service.add_points = AsyncMock()
        service.point_service.award_poll = AsyncMock()
        service.point_service.award_message = AsyncMock()
        
        mock_bot = AsyncMock()
        
        # Test different action types and their point values
        test_cases = [
            ("post", 5, "add_points"),
            ("comment", 2, "add_points"),
            ("poll_vote", None, "award_poll"),
            ("message", None, "award_message"),
            ("other", 1, "add_points")
        ]
        
        for action_type, expected_points, expected_method in test_cases:
            # Reset mocks
            service.point_service.add_points.reset_mock()
            service.point_service.award_poll.reset_mock()
            service.point_service.award_message.reset_mock()
            
            result = await service.award_channel_participation(
                test_user.id,
                channel_id=-123456,
                action_type=action_type,
                bot=mock_bot
            )
            
            # Critical assertions - each action type must award correct points
            assert result is True, f"Participation type '{action_type}' must succeed"
            
            if expected_method == "add_points":
                service.point_service.add_points.assert_called_once_with(test_user.id, expected_points, bot=mock_bot)
            elif expected_method == "award_poll":
                service.point_service.award_poll.assert_called_once_with(test_user.id, mock_bot)
            elif expected_method == "award_message":
                service.point_service.award_message.assert_called_once_with(test_user.id, mock_bot)
                
    async def test_check_daily_engagement_bonus_semanal(self, session, test_user):
        """
        CRITICAL: Test que protege el bonus semanal por racha.
        Las rachas semanales (7, 14, 21 días) deben otorgar bonus adicional.
        """
        service = ChannelEngagementService(session)
        
        # Mock successful daily checkin with 7-day streak (weekly bonus)
        progress_mock = MagicMock()
        progress_mock.checkin_streak = 7
        service.point_service.daily_checkin = AsyncMock(return_value=(True, progress_mock))
        service.point_service.add_points = AsyncMock()
        
        mock_bot = AsyncMock()
        mock_bot.send_message = AsyncMock()
        
        result = await service.check_daily_engagement(test_user.id, mock_bot)
        
        # Critical assertions - weekly bonus must be awarded
        assert result is True, "Weekly streak checkin must succeed"
        service.point_service.daily_checkin.assert_called_once_with(test_user.id, mock_bot)
        service.point_service.add_points.assert_called_once_with(test_user.id, 25, bot=mock_bot)
        
        # Verify congratulatory message is sent
        mock_bot.send_message.assert_called_once()
        sent_message = mock_bot.send_message.call_args[0][1]
        assert "Felicidades" in sent_message, "Weekly bonus message must be congratulatory"
        assert "7 días" in sent_message, "Message must mention the streak length"
        assert "+25 puntos" in sent_message, "Message must mention bonus amount"
        
    async def test_check_daily_engagement_ya_realizado(self, session, test_user):
        """
        CRITICAL: Test que protege contra check-ins duplicados.
        Los usuarios NO deben poder hacer check-in múltiple el mismo día.
        """
        service = ChannelEngagementService(session)
        
        # Mock failed daily checkin (already done today)
        service.point_service.daily_checkin = AsyncMock(return_value=(False, None))
        service.point_service.add_points = AsyncMock()
        
        result = await service.check_daily_engagement(test_user.id, None)
        
        # Critical assertions - duplicate checkin must be prevented
        assert result is False, "Duplicate daily checkin must be prevented"
        service.point_service.daily_checkin.assert_called_once_with(test_user.id, None)
        service.point_service.add_points.assert_not_called()
        
    async def test_error_handling_service_exception(self, session, test_user):
        """
        CRITICAL: Test que protege el manejo de errores en servicios.
        Las excepciones en servicios NO deben romper el flujo.
        """
        service = ChannelEngagementService(session)
        
        # Mock service to raise exception
        service.point_service.award_reaction = AsyncMock(side_effect=Exception("Database error"))
        service.config_service.get_managed_channels = AsyncMock(return_value={"-123": "vip"})
        
        result = await service.award_channel_reaction(
            test_user.id,
            message_id=123,
            channel_id=-123,
            bot=None
        )
        
        # Critical assertions - service errors must be handled gracefully
        assert result is False, "Service exceptions must be handled gracefully"
        
    async def test_integration_flujo_completo_engagement(self, session, test_user, test_channel):
        """
        CRITICAL: Test de integración que simula un flujo completo de engagement.
        Simula: reacción -> participación -> check-in diario en secuencia.
        """
        service = ChannelEngagementService(session)
        
        # Mock all services for complete flow
        service.config_service.get_managed_channels = AsyncMock(return_value={str(test_channel.id): "vip"})
        service.point_service.award_reaction = AsyncMock()
        service.point_service.add_points = AsyncMock()
        
        progress_mock = MagicMock()
        progress_mock.checkin_streak = 3
        service.point_service.daily_checkin = AsyncMock(return_value=(True, progress_mock))
        
        mock_bot = AsyncMock()
        
        # 1. User reacts to a message
        reaction_result = await service.award_channel_reaction(
            test_user.id,
            message_id=456,
            channel_id=test_channel.id,
            bot=mock_bot
        )
        
        # 2. User participates with a post
        participation_result = await service.award_channel_participation(
            test_user.id,
            channel_id=test_channel.id,
            action_type="post",
            bot=mock_bot
        )
        
        # 3. User does daily check-in
        checkin_result = await service.check_daily_engagement(test_user.id, mock_bot)
        
        # Critical assertions - complete engagement flow must work
        assert reaction_result is True, "Reaction step must succeed"
        assert participation_result is True, "Participation step must succeed"
        assert checkin_result is True, "Daily checkin step must succeed"
        
        # Verify all services were called correctly
        service.point_service.award_reaction.assert_called_once_with(test_user, 456, mock_bot)
        service.point_service.add_points.assert_called_once_with(test_user.id, 5, bot=mock_bot)  # Post = 5 points
        service.point_service.daily_checkin.assert_called_once_with(test_user.id, mock_bot)
