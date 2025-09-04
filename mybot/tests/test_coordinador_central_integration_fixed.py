"""
Fixed CoordinadorCentral Integration Tests
Addresses the critical 73% failure rate by fixing dependency injection issues.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from services.coordinador_central import CoordinadorCentral, AccionUsuario
from database.models import User, Channel


@pytest.mark.asyncio
class TestCoordinadorCentralIntegrationFixed:
    """Fixed integration tests for CoordinadorCentral with proper dependency injection."""
    
    @pytest_asyncio.fixture
    async def mock_coordinador(self, session):
        """Create CoordinadorCentral with all dependencies properly mocked."""
        coordinador = CoordinadorCentral(session)
        
        # Mock all services to prevent dependency injection errors
        coordinador.narrative_point = AsyncMock()
        coordinador.channel_engagement = AsyncMock()
        coordinador.narrative_access = AsyncMock()
        coordinador.event_coordinator = AsyncMock()
        
        return coordinador
    
    async def test_reaccion_publicacion_workflow_success(self, mock_coordinador, test_user, test_channel, mock_bot):
        """Test successful reaction workflow through CoordinadorCentral."""
        # Setup successful reaction award
        mock_coordinador.channel_engagement.award_channel_reaction = AsyncMock(return_value=True)
        
        # Setup point retrieval
        mock_coordinador.narrative_point.point_service.get_user_points = AsyncMock(return_value=65.0)
        
        # Setup narrative fragment for hint unlock
        fragment_mock = MagicMock()
        fragment_mock.key = "level2_romantic_encounter"
        mock_coordinador.narrative_point.narrative_service.get_user_current_fragment = AsyncMock(return_value=fragment_mock)
        
        # Execute workflow
        result = await mock_coordinador.ejecutar_flujo(
            test_user.id,
            AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=456,
            channel_id=test_channel.id,
            reaction_type="like",
            bot=mock_bot
        )
        
        # Validate critical business logic
        assert result["success"] is True, "Reaction workflow must succeed"
        assert result["points_awarded"] == 10, "Standard like must award 10 points"
        assert result["total_points"] == 65, "Point total must be retrieved correctly"
        assert result["action"] == "reaction_success", "Action must be identified correctly"
        
        # Verify service calls
        mock_coordinador.channel_engagement.award_channel_reaction.assert_called_once_with(
            test_user.id, 456, test_channel.id, bot=mock_bot
        )

    async def test_reaccion_publicacion_workflow_failure(self, mock_coordinador, test_user, test_channel, mock_bot):
        """Test failed reaction workflow handling."""
        # Setup failed reaction award
        mock_coordinador.channel_engagement.award_channel_reaction = AsyncMock(return_value=False)
        
        result = await mock_coordinador.ejecutar_flujo(
            test_user.id,
            AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=456,
            channel_id=test_channel.id,
            reaction_type="like",
            bot=mock_bot
        )
        
        # Validate error handling
        assert result["success"] is False, "Failed reactions must be handled gracefully"
        assert result["action"] == "reaction_failed", "Failure must be identified"
        assert "Diana observa" in result["message"], "Character messaging must be maintained"

    async def test_acceso_narrativa_vip_protection(self, mock_coordinador, test_user):
        """Test VIP content protection for non-VIP users."""
        # Setup VIP protection response
        mock_coordinador.narrative_access.get_accessible_fragment = AsyncMock(return_value={
            "type": "subscription_required",
            "message": "Este contenido requiere una suscripción VIP activa.",
            "requested_fragment": "level4_intimate_scene"
        })
        
        result = await mock_coordinador.ejecutar_flujo(
            test_user.id,
            AccionUsuario.ACCEDER_NARRATIVA_VIP,
            fragment_key="level4_intimate_scene"
        )
        
        # Critical VIP protection validation
        assert result["success"] is False, "Non-VIP users must be blocked from VIP content"
        assert result["action"] == "vip_required", "VIP requirement must be identified"
        assert "/vip" in result["message"], "VIP upgrade path must be provided"
        assert result["fragment_key"] == "level4_intimate_scene", "Fragment tracking must be preserved"

    async def test_acceso_narrativa_vip_authorized(self, mock_coordinador, vip_user):
        """Test successful VIP content access for authorized users."""
        # Setup successful VIP access
        fragment_data = {
            "key": "level4_intimate_scene", 
            "content": "Diana te lleva hacia...",
            "choices": [{"text": "Seguir", "points_cost": 0}]
        }
        mock_coordinador.narrative_access.get_accessible_fragment = AsyncMock(return_value=fragment_data)
        
        result = await mock_coordinador.ejecutar_flujo(
            vip_user.id,
            AccionUsuario.ACCEDER_NARRATIVA_VIP,
            fragment_key="level4_intimate_scene"
        )
        
        # Critical VIP access validation
        assert result["success"] is True, "VIP users must access VIP content successfully"
        assert result["action"] == "fragment_accessed", "Access must be identified"
        assert result["fragment"] == fragment_data, "Correct fragment must be returned"

    async def test_tomar_decision_puntos_insuficientes(self, mock_coordinador, test_user):
        """Test decision handling when user has insufficient points."""
        mock_coordinador.narrative_point.process_decision_with_points = AsyncMock(return_value={
            "type": "points_required",
            "message": "No tienes suficientes puntos para esta decisión.",
            "decision_id": 456,
            "points_needed": 25,
            "user_points": 10
        })
        
        result = await mock_coordinador.ejecutar_flujo(
            test_user.id,
            AccionUsuario.TOMAR_DECISION,
            decision_id=456
        )
        
        # Critical points validation
        assert result["success"] is False, "Insufficient points must prevent decision access"
        assert result["action"] == "points_required", "Points requirement must be identified"
        assert "más besitos" in result["message"], "Point requirement explanation must be user-friendly"
        assert result["decision_id"] == 456, "Decision tracking must be preserved"

    async def test_tomar_decision_successful(self, mock_coordinador, vip_user, mock_bot):
        """Test successful decision taking with sufficient points."""
        fragment_data = {
            "key": "choice_result_romantic",
            "content": "Diana sonríe al ver tu elección...",
            "choices": []
        }
        mock_coordinador.narrative_point.process_decision_with_points = AsyncMock(return_value={
            "type": "success",
            "fragment": fragment_data,
            "points_deducted": 15
        })
        
        result = await mock_coordinador.ejecutar_flujo(
            vip_user.id,
            AccionUsuario.TOMAR_DECISION,
            decision_id=456,
            bot=mock_bot
        )
        
        # Critical success validation
        assert result["success"] is True, "Valid decisions must succeed"
        assert result["action"] == "decision_success", "Success must be identified"
        assert result["fragment"] == fragment_data, "Result fragment must be provided"

    async def test_participacion_canal_workflow(self, mock_coordinador, test_user, test_channel, mock_bot):
        """Test channel participation workflow."""
        mock_coordinador.channel_engagement.award_channel_participation = AsyncMock(return_value=True)
        
        result = await mock_coordinador.ejecutar_flujo(
            test_user.id,
            AccionUsuario.PARTICIPAR_CANAL,
            channel_id=test_channel.id,
            action_type="post",
            bot=mock_bot
        )
        
        # Critical participation validation
        assert result["success"] is True, "Valid participation must succeed"
        assert result["action"] == "participation_success", "Success must be identified"
        assert result["points_awarded"] == 5, "Post participation must award 5 points"
        assert result["action_type"] == "post", "Action type must be tracked"

    async def test_daily_engagement_streak_bonus(self, mock_coordinador, test_user, mock_bot):
        """Test daily engagement with weekly streak bonus."""
        mock_coordinador.channel_engagement.check_daily_engagement = AsyncMock(return_value=True)
        
        # Mock 7-day streak for bonus
        progress_mock = MagicMock()
        progress_mock.checkin_streak = 7
        mock_coordinador.channel_engagement.point_service.get_user_progress = AsyncMock(return_value=progress_mock)
        
        result = await mock_coordinador.ejecutar_flujo(
            test_user.id,
            AccionUsuario.VERIFICAR_ENGAGEMENT,
            bot=mock_bot
        )
        
        # Critical streak validation
        assert result["success"] is True, "Valid engagement check must succeed"
        assert result["streak"] == 7, "Streak must be tracked correctly"
        assert result["points_awarded"] == 25, "Weekly bonus must be 25 points"
        assert "abrazo apasionado" in result["message"], "Weekly bonus message must be special"

    async def test_daily_engagement_already_done(self, mock_coordinador, test_user, mock_bot):
        """Test prevention of duplicate daily check-ins."""
        mock_coordinador.channel_engagement.check_daily_engagement = AsyncMock(return_value=False)
        
        result = await mock_coordinador.ejecutar_flujo(
            test_user.id,
            AccionUsuario.VERIFICAR_ENGAGEMENT,
            bot=mock_bot
        )
        
        # Critical duplicate check prevention
        assert result["success"] is False, "Duplicate daily check must be prevented"
        assert result["action"] == "daily_check_already_done", "Duplicate must be identified"
        assert "Ya nos hemos visto hoy" in result["message"], "Clear explanation must be provided"

    async def test_error_handling_invalid_action(self, mock_coordinador, test_user):
        """Test error handling for invalid actions."""
        class InvalidAction:
            pass
        
        result = await mock_coordinador.ejecutar_flujo(
            test_user.id,
            InvalidAction(),
            some_param="test"
        )
        
        # Critical error handling
        assert result["success"] is False, "Invalid actions must be rejected"
        assert "Acción no reconocida" in result["message"], "Clear error message must be provided"

    async def test_error_handling_service_exception(self, mock_coordinador, test_user):
        """Test error handling when services raise exceptions."""
        # Setup service to raise exception
        mock_coordinador.channel_engagement.award_channel_reaction = AsyncMock(
            side_effect=Exception("Database connection error")
        )
        
        result = await mock_coordinador.ejecutar_flujo(
            test_user.id,
            AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=456,
            channel_id=-123456,
            reaction_type="like"
        )
        
        # Critical exception handling
        assert result["success"] is False, "Service exceptions must be handled gracefully"
        assert "error inesperado" in result["message"], "User-friendly error must be provided"
        assert "error" in result, "Error details must be logged for debugging"


@pytest.mark.asyncio
class TestCoordinadorCentralPerformance:
    """Performance regression tests for CoordinadorCentral workflows."""
    
    async def test_workflow_performance_baseline(self, session):
        """Test CoordinadorCentral workflow performance stays within 15.4ms baseline."""
        import time
        
        # Create coordinador with minimal mocks
        coordinador = CoordinadorCentral(session)
        coordinador.channel_engagement = AsyncMock()
        coordinador.channel_engagement.award_channel_reaction = AsyncMock(return_value=True)
        
        # Create test user
        user = User(id=123456789, first_name="TestUser", role="free", points=100)
        
        # Measure performance
        start_time = time.perf_counter()
        
        result = await coordinador.ejecutar_flujo(
            user.id,
            AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=456,
            channel_id=-123456789,
            reaction_type="like"
        )
        
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Performance assertion (allowing 100% margin for test environment)
        assert duration_ms < 30.8, f"Workflow took {duration_ms:.2f}ms, exceeds 30.8ms threshold (2x baseline)"
        assert result is not None, "Workflow must produce result"