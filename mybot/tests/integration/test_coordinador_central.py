"""
Tests de protección para CoordinadorCentral - Critical Business Flows.
Estos tests protegen la funcionalidad existente durante refactoring.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from services.coordinador_central import CoordinadorCentral, AccionUsuario


@pytest.mark.asyncio
class TestCoordinadorCentralCriticalFlows:
    """Tests críticos para el Coordinador Central que maneja los flujos principales del bot."""

    async def test_flujo_reaccion_publicacion_completo_con_pista(self, coordinador_central, test_user, test_channel, mock_bot):
        """
        CRITICAL: Test que protege el flujo completo de reacciones a publicaciones.
        Este es uno de los flujos más importantes - genera puntos y desbloquea contenido.
        """
        # Setup - Mock services for complete flow simulation
        coordinador_central.channel_engagement.award_channel_reaction = AsyncMock(return_value=True)
        coordinador_central.point_service.get_user_points = AsyncMock(return_value=65)  # Points that trigger hint
        
        # Mock narrative fragment to trigger hint unlock
        fragment_mock = MagicMock()
        fragment_mock.key = "level2_romantic_encounter"
        coordinador_central.narrative_service.get_user_current_fragment = AsyncMock(return_value=fragment_mock)
        
        # Execute critical flow
        result = await coordinador_central.ejecutar_flujo(
            test_user.id,
            AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=456,
            channel_id=test_channel.id,
            reaction_type="like",
            bot=mock_bot
        )
        
        # Critical assertions - these behaviors MUST be preserved
        assert result["success"] is True, "Reaction flow must succeed for valid users"
        assert result["points_awarded"] == 10, "Points award amount must remain consistent"
        assert result["total_points"] == 65, "Total points must be correctly retrieved"
        assert result["action"] == "reaction_success", "Action type must be correctly identified"
        assert "Diana sonríe" in result["message"], "Character messaging must be preserved"
        assert "hint_unlocked" in result, "Hint unlock mechanism must be preserved"
        assert result["hint_unlocked"] is not None, "Hint should unlock at this point level"
        
        # Verify service calls happen in correct order
        coordinador_central.channel_engagement.award_channel_reaction.assert_called_once_with(
            test_user.id, 456, test_channel.id, bot=mock_bot
        )
        coordinador_central.point_service.get_user_points.assert_called_once_with(test_user.id)

    async def test_flujo_reaccion_publicacion_fallo_award(self, coordinador_central, test_user, test_channel, mock_bot):
        """
        CRITICAL: Test que protege el manejo de errores en reacciones.
        Fallos aquí pueden romper la experiencia del usuario.
        """
        # Setup failure scenario
        coordinador_central.channel_engagement.award_channel_reaction = AsyncMock(return_value=False)
        
        result = await coordinador_central.ejecutar_flujo(
            test_user.id,
            AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=456,
            channel_id=test_channel.id,
            reaction_type="like",
            bot=mock_bot
        )
        
        # Critical failure handling - must maintain user-friendly messaging
        assert result["success"] is False, "Failed reactions must be properly handled"
        assert result["action"] == "reaction_failed", "Failure action must be identified"
        assert "Diana observa" in result["message"], "Failure message must maintain character voice"
        assert "más tarde" in result["message"], "User should be encouraged to try again"

    async def test_flujo_acceso_narrativa_vip_proteccion_contenido(self, coordinador_central, test_user):
        """
        CRITICAL: Test que protege el sistema de control de acceso VIP.
        Este es el core del modelo de negocio - DEBE funcionar correctamente.
        """
        # Setup VIP protection scenario
        coordinador_central.narrative_access.get_accessible_fragment = AsyncMock(return_value={
            "type": "subscription_required",
            "message": "Este contenido requiere una suscripción VIP activa.",
            "requested_fragment": "level4_intimate_scene"
        })
        
        result = await coordinador_central.ejecutar_flujo(
            test_user.id,
            AccionUsuario.ACCEDER_NARRATIVA_VIP,
            fragment_key="level4_intimate_scene"
        )
        
        # Critical business logic - VIP protection must work
        assert result["success"] is False, "Non-VIP users must be blocked from VIP content"
        assert result["action"] == "vip_required", "VIP requirement must be clearly identified"
        assert "/vip" in result["message"], "VIP subscription path must be provided"
        assert "Diana te mira con deseo" in result["message"], "Character interaction must be preserved"
        assert result["fragment_key"] == "level4_intimate_scene", "Fragment tracking must be preserved"

    async def test_flujo_acceso_narrativa_vip_usuario_autorizado(self, coordinador_central, vip_user):
        """
        CRITICAL: Test que protege el acceso exitoso de usuarios VIP.
        Los usuarios VIP DEBEN poder acceder a su contenido pagado.
        """
        # Setup successful VIP access
        fragment_data = {
            "key": "level4_intimate_scene",
            "content": "Diana te lleva hacia...",
            "choices": [{"text": "Seguir", "points_cost": 0}]
        }
        coordinador_central.narrative_access.get_accessible_fragment = AsyncMock(return_value=fragment_data)
        
        result = await coordinador_central.ejecutar_flujo(
            vip_user.id,
            AccionUsuario.ACCEDER_NARRATIVA_VIP,
            fragment_key="level4_intimate_scene"
        )
        
        # Critical VIP access - paid users must get their content
        assert result["success"] is True, "VIP users must access VIP content successfully"
        assert result["action"] == "fragment_accessed", "Access action must be identified"
        assert "fragment" in result, "Fragment data must be provided"
        assert result["fragment"] == fragment_data, "Correct fragment must be returned"

    async def test_flujo_tomar_decision_puntos_insuficientes(self, coordinador_central, test_user):
        """
        CRITICAL: Test que protege el sistema de costos por decisiones.
        Usuarios sin puntos suficientes NO deben acceder a decisiones costosas.
        """
        coordinador_central.narrative_point.process_decision_with_points = AsyncMock(return_value={
            "type": "points_required",
            "message": "No tienes suficientes puntos para esta decisión.",
            "decision_id": 456,
            "points_needed": 25,
            "user_points": 10
        })
        
        result = await coordinador_central.ejecutar_flujo(
            test_user.id,
            AccionUsuario.TOMAR_DECISION,
            decision_id=456
        )
        
        # Critical points system - must prevent access without sufficient points
        assert result["success"] is False, "Insufficient points must prevent decision access"
        assert result["action"] == "points_required", "Points requirement must be identified"
        assert "más besitos" in result["message"], "Point requirement must be explained to user"
        assert result["decision_id"] == 456, "Decision tracking must be preserved"

    async def test_flujo_tomar_decision_exitoso(self, coordinador_central, vip_user, mock_bot):
        """
        CRITICAL: Test que protege el flujo exitoso de toma de decisiones.
        Usuarios con puntos suficientes DEBEN poder tomar decisiones.
        """
        fragment_data = {
            "key": "choice_result_romantic",
            "content": "Diana sonríe al ver tu elección...",
            "choices": []
        }
        coordinador_central.narrative_point.process_decision_with_points = AsyncMock(return_value={
            "type": "success",
            "fragment": fragment_data,
            "points_deducted": 15
        })
        
        result = await coordinador_central.ejecutar_flujo(
            vip_user.id,
            AccionUsuario.TOMAR_DECISION,
            decision_id=456,
            bot=mock_bot
        )
        
        # Critical decision flow - must work for valid scenarios
        assert result["success"] is True, "Valid decisions must succeed"
        assert result["action"] == "decision_success", "Success action must be identified"
        assert "fragment" in result, "Result fragment must be provided"
        assert result["fragment"] == fragment_data, "Correct fragment must be returned"

    async def test_flujo_participacion_canal_mensaje(self, coordinador_central, test_user, test_channel, mock_bot):
        """
        CRITICAL: Test que protege el sistema de participación en canales.
        La participación debe otorgar puntos y mantener engagement.
        """
        coordinador_central.channel_engagement.award_channel_participation = AsyncMock(return_value=True)
        
        result = await coordinador_central.ejecutar_flujo(
            test_user.id,
            AccionUsuario.PARTICIPAR_CANAL,
            channel_id=test_channel.id,
            action_type="post",
            bot=mock_bot
        )
        
        # Critical participation rewards - must maintain user engagement
        assert result["success"] is True, "Valid participation must succeed"
        assert result["action"] == "participation_success", "Success action must be identified"
        assert result["points_awarded"] == 5, "Post participation must award 5 points"
        assert result["action_type"] == "post", "Action type must be tracked"
        assert "Diana lee con interés" in result["message"], "Character response must be preserved"

    async def test_flujo_verificar_engagement_racha_semanal(self, coordinador_central, test_user, mock_bot):
        """
        CRITICAL: Test que protege el sistema de rachas de engagement.
        Las rachas semanales deben dar bonificaciones especiales.
        """
        coordinador_central.channel_engagement.check_daily_engagement = AsyncMock(return_value=True)
        
        # Mock 7-day streak for weekly bonus
        progress_mock = MagicMock()
        progress_mock.checkin_streak = 7
        coordinador_central.point_service.get_user_progress = AsyncMock(return_value=progress_mock)
        
        result = await coordinador_central.ejecutar_flujo(
            test_user.id,
            AccionUsuario.VERIFICAR_ENGAGEMENT,
            bot=mock_bot
        )
        
        # Critical streak system - weekly bonuses must work
        assert result["success"] is True, "Valid engagement check must succeed"
        assert result["streak"] == 7, "Streak must be correctly tracked"
        assert result["points_awarded"] == 25, "Weekly bonus must be 25 points"
        assert result["action"] == "daily_check_success", "Success action must be identified"
        assert "abrazo apasionado" in result["message"], "Weekly bonus message must be special"

    async def test_flujo_verificar_engagement_ya_realizado(self, coordinador_central, test_user, mock_bot):
        """
        CRITICAL: Test que protege contra doble check-in diario.
        Los usuarios NO deben poder hacer check-in múltiple el mismo día.
        """
        coordinador_central.channel_engagement.check_daily_engagement = AsyncMock(return_value=False)
        
        result = await coordinador_central.ejecutar_flujo(
            test_user.id,
            AccionUsuario.VERIFICAR_ENGAGEMENT,
            bot=mock_bot
        )
        
        # Critical daily check prevention - must prevent abuse
        assert result["success"] is False, "Duplicate daily check must be prevented"
        assert result["action"] == "daily_check_already_done", "Duplicate check must be identified"
        assert "Ya nos hemos visto hoy" in result["message"], "Clear explanation must be provided"

    async def test_flujo_error_handling_accion_invalida(self, coordinador_central, test_user):
        """
        CRITICAL: Test que protege el manejo de errores por acciones inválidas.
        El sistema debe responder correctamente a acciones no implementadas.
        """
        # Test with invalid action
        class AccionInvalida:
            pass
        
        result = await coordinador_central.ejecutar_flujo(
            test_user.id,
            AccionInvalida(),
            some_param="test"
        )
        
        # Critical error handling - must handle unknown actions gracefully
        assert result["success"] is False, "Invalid actions must be rejected"
        assert "Acción no reconocida" in result["message"], "Clear error message must be provided"

    async def test_flujo_error_handling_exception_en_servicio(self, coordinador_central, test_user):
        """
        CRITICAL: Test que protege el manejo de errores por excepciones en servicios.
        Las excepciones NO deben romper la experiencia del usuario.
        """
        # Setup service to raise exception
        coordinador_central.channel_engagement.award_channel_reaction = AsyncMock(
            side_effect=Exception("Database connection error")
        )
        
        result = await coordinador_central.ejecutar_flujo(
            test_user.id,
            AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=456,
            channel_id=-123456,
            reaction_type="like"
        )
        
        # Critical exception handling - must provide user-friendly error
        assert result["success"] is False, "Service exceptions must be handled"
        assert "error inesperado" in result["message"], "User-friendly error message must be provided"
        assert "error" in result, "Error details must be logged for debugging"
