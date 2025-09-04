"""
CoordinadorCentral Integration Tests with Complete Mocking
This completely avoids the dependency injection issues by mocking at the module level.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import time

from services.coordinador_central import AccionUsuario
from database.models import User, Channel


@pytest.mark.asyncio
class TestCoordinadorCentralWithMocking:
    """Complete integration tests with all dependencies mocked at import level."""
    
    async def test_coordinador_central_import_and_creation(self, session):
        """Test that CoordinadorCentral can be created with proper mocking."""
        with patch('services.integration.narrative_point_service.PointService') as mock_ps, \
             patch('services.integration.channel_engagement_service.PointService') as mock_ps2, \
             patch('services.integration.event_coordinator.PointService') as mock_ps3:
            
            # Mock PointService constructor to return proper AsyncMocks
            mock_ps.return_value = AsyncMock()
            mock_ps2.return_value = AsyncMock()
            mock_ps3.return_value = AsyncMock()
            
            # Import after mocking
            from services.coordinador_central import CoordinadorCentral
            
            # Create coordinador - should work now
            coordinador = CoordinadorCentral(session)
            
            assert coordinador is not None
            assert coordinador.session == session
    
    async def test_reaction_workflow_complete_with_mocking(self, session, test_user, test_channel, mock_bot):
        """Test complete reaction workflow with all services mocked."""
        with patch('services.integration.narrative_point_service.PointService') as mock_ps, \
             patch('services.integration.channel_engagement_service.PointService') as mock_ps2, \
             patch('services.integration.event_coordinator.PointService') as mock_ps3:
            
            # Setup point service mocks
            mock_ps.return_value = AsyncMock()
            mock_ps2.return_value = AsyncMock()  
            mock_ps3.return_value = AsyncMock()
            
            from services.coordinador_central import CoordinadorCentral
            
            coordinador = CoordinadorCentral(session)
            
            # Mock the service methods we need
            coordinador.channel_engagement.award_channel_reaction = AsyncMock(return_value=True)
            coordinador.narrative_point.point_service.get_user_points = AsyncMock(return_value=65.0)
            
            # Mock narrative fragment for hint unlock
            fragment_mock = MagicMock()
            fragment_mock.key = "level2_romantic_encounter"
            coordinador.narrative_point.narrative_service.get_user_current_fragment = AsyncMock(return_value=fragment_mock)
            
            # Execute the workflow
            result = await coordinador.ejecutar_flujo(
                test_user.id,
                AccionUsuario.REACCIONAR_PUBLICACION,
                message_id=456,
                channel_id=test_channel.id,
                reaction_type="like",
                bot=mock_bot
            )
            
            # Critical validations
            assert result["success"] is True, "Reaction workflow must succeed"
            assert result["points_awarded"] == 10, "Like must award 10 points"
            assert result["total_points"] == 65, "Total points must be retrieved correctly"
            assert result["action"] == "reaction_success", "Action must be identified"
            assert "Diana sonríe" in result["message"], "Character response must be preserved"
            
            # Verify service interactions
            coordinador.channel_engagement.award_channel_reaction.assert_called_once_with(
                test_user.id, 456, test_channel.id, bot=mock_bot
            )

    async def test_vip_content_protection_workflow(self, session, test_user):
        """Test VIP content protection workflow."""
        with patch('services.integration.narrative_point_service.PointService') as mock_ps, \
             patch('services.integration.channel_engagement_service.PointService') as mock_ps2, \
             patch('services.integration.event_coordinator.PointService') as mock_ps3:
            
            mock_ps.return_value = AsyncMock()
            mock_ps2.return_value = AsyncMock()
            mock_ps3.return_value = AsyncMock()
            
            from services.coordinador_central import CoordinadorCentral
            
            coordinador = CoordinadorCentral(session)
            
            # Mock VIP protection
            coordinador.narrative_access.get_accessible_fragment = AsyncMock(return_value={
                "type": "subscription_required",
                "message": "Este contenido requiere una suscripción VIP activa.",
                "requested_fragment": "level4_intimate_scene"
            })
            
            result = await coordinador.ejecutar_flujo(
                test_user.id,
                AccionUsuario.ACCEDER_NARRATIVA_VIP,
                fragment_key="level4_intimate_scene"
            )
            
            # Critical business logic validation
            assert result["success"] is False, "Non-VIP users must be blocked"
            assert result["action"] == "vip_required", "VIP requirement must be identified"
            assert "/vip" in result["message"], "VIP upgrade path must be provided"
            assert result["fragment_key"] == "level4_intimate_scene", "Fragment tracking preserved"

    async def test_vip_content_access_authorized(self, session, vip_user):
        """Test successful VIP content access."""
        with patch('services.integration.narrative_point_service.PointService') as mock_ps, \
             patch('services.integration.channel_engagement_service.PointService') as mock_ps2, \
             patch('services.integration.event_coordinator.PointService') as mock_ps3:
            
            mock_ps.return_value = AsyncMock()
            mock_ps2.return_value = AsyncMock()
            mock_ps3.return_value = AsyncMock()
            
            from services.coordinador_central import CoordinadorCentral
            
            coordinador = CoordinadorCentral(session)
            
            # Mock successful VIP access
            fragment_data = {
                "key": "level4_intimate_scene",
                "content": "Diana te lleva hacia...",
                "choices": [{"text": "Seguir", "points_cost": 0}]
            }
            coordinador.narrative_access.get_accessible_fragment = AsyncMock(return_value=fragment_data)
            
            result = await coordinador.ejecutar_flujo(
                vip_user.id,
                AccionUsuario.ACCEDER_NARRATIVA_VIP,
                fragment_key="level4_intimate_scene"
            )
            
            # Critical VIP access validation
            assert result["success"] is True, "VIP users must access VIP content"
            assert result["action"] == "fragment_accessed", "Access must be identified"
            assert result["fragment"] == fragment_data, "Correct fragment must be returned"

    async def test_decision_points_insufficient(self, session, test_user):
        """Test decision handling with insufficient points."""
        with patch('services.integration.narrative_point_service.PointService') as mock_ps, \
             patch('services.integration.channel_engagement_service.PointService') as mock_ps2, \
             patch('services.integration.event_coordinator.PointService') as mock_ps3:
            
            mock_ps.return_value = AsyncMock()
            mock_ps2.return_value = AsyncMock()
            mock_ps3.return_value = AsyncMock()
            
            from services.coordinador_central import CoordinadorCentral
            
            coordinador = CoordinadorCentral(session)
            
            # Mock insufficient points response
            coordinador.narrative_point.process_decision_with_points = AsyncMock(return_value={
                "type": "points_required",
                "message": "No tienes suficientes puntos para esta decisión.",
                "decision_id": 456,
                "points_needed": 25,
                "user_points": 10
            })
            
            result = await coordinador.ejecutar_flujo(
                test_user.id,
                AccionUsuario.TOMAR_DECISION,
                decision_id=456
            )
            
            # Critical points system validation
            assert result["success"] is False, "Insufficient points must prevent access"
            assert result["action"] == "points_required", "Points requirement identified"
            assert "más besitos" in result["message"], "User-friendly explanation provided"
            assert result["decision_id"] == 456, "Decision tracking preserved"

    async def test_decision_successful_with_points(self, session, vip_user, mock_bot):
        """Test successful decision taking."""
        with patch('services.integration.narrative_point_service.PointService') as mock_ps, \
             patch('services.integration.channel_engagement_service.PointService') as mock_ps2, \
             patch('services.integration.event_coordinator.PointService') as mock_ps3:
            
            mock_ps.return_value = AsyncMock()
            mock_ps2.return_value = AsyncMock()
            mock_ps3.return_value = AsyncMock()
            
            from services.coordinador_central import CoordinadorCentral
            
            coordinador = CoordinadorCentral(session)
            
            # Mock successful decision
            fragment_data = {
                "key": "choice_result_romantic",
                "content": "Diana sonríe al ver tu elección...",
                "choices": []
            }
            coordinador.narrative_point.process_decision_with_points = AsyncMock(return_value={
                "type": "success",
                "fragment": fragment_data,
                "points_deducted": 15
            })
            
            result = await coordinador.ejecutar_flujo(
                vip_user.id,
                AccionUsuario.TOMAR_DECISION,
                decision_id=456,
                bot=mock_bot
            )
            
            # Critical success validation
            assert result["success"] is True, "Valid decisions must succeed"
            assert result["action"] == "decision_success", "Success identified"
            assert result["fragment"] == fragment_data, "Result fragment provided"

    async def test_channel_participation_workflow(self, session, test_user, test_channel, mock_bot):
        """Test channel participation rewards."""
        with patch('services.integration.narrative_point_service.PointService') as mock_ps, \
             patch('services.integration.channel_engagement_service.PointService') as mock_ps2, \
             patch('services.integration.event_coordinator.PointService') as mock_ps3:
            
            mock_ps.return_value = AsyncMock()
            mock_ps2.return_value = AsyncMock()
            mock_ps3.return_value = AsyncMock()
            
            from services.coordinador_central import CoordinadorCentral
            
            coordinador = CoordinadorCentral(session)
            
            # Mock successful participation
            coordinador.channel_engagement.award_channel_participation = AsyncMock(return_value=True)
            
            result = await coordinador.ejecutar_flujo(
                test_user.id,
                AccionUsuario.PARTICIPAR_CANAL,
                channel_id=test_channel.id,
                action_type="post",
                bot=mock_bot
            )
            
            # Critical participation validation
            assert result["success"] is True, "Valid participation must succeed"
            assert result["action"] == "participation_success", "Success identified"
            assert result["points_awarded"] == 5, "Post participation awards 5 points"
            assert result["action_type"] == "post", "Action type tracked"
            assert "Diana lee con interés" in result["message"], "Character response preserved"

    async def test_daily_engagement_with_streak(self, session, test_user, mock_bot):
        """Test daily engagement with streak bonus."""
        with patch('services.integration.narrative_point_service.PointService') as mock_ps, \
             patch('services.integration.channel_engagement_service.PointService') as mock_ps2, \
             patch('services.integration.event_coordinator.PointService') as mock_ps3:
            
            mock_ps.return_value = AsyncMock()
            mock_ps2.return_value = AsyncMock()
            mock_ps3.return_value = AsyncMock()
            
            from services.coordinador_central import CoordinadorCentral
            
            coordinador = CoordinadorCentral(session)
            
            # Mock successful daily engagement
            coordinador.channel_engagement.check_daily_engagement = AsyncMock(return_value=True)
            
            # Mock 7-day streak for weekly bonus
            progress_mock = MagicMock()
            progress_mock.checkin_streak = 7
            coordinador.channel_engagement.point_service.get_user_progress = AsyncMock(return_value=progress_mock)
            
            result = await coordinador.ejecutar_flujo(
                test_user.id,
                AccionUsuario.VERIFICAR_ENGAGEMENT,
                bot=mock_bot
            )
            
            # Critical streak validation
            assert result["success"] is True, "Valid engagement check must succeed"
            assert result["streak"] == 7, "Streak tracked correctly"
            assert result["points_awarded"] == 25, "Weekly bonus is 25 points"
            assert result["action"] == "daily_check_success", "Success identified"
            assert "abrazo apasionado" in result["message"], "Special weekly message"

    async def test_error_handling_service_exception(self, session, test_user):
        """Test graceful error handling when services fail."""
        with patch('services.integration.narrative_point_service.PointService') as mock_ps, \
             patch('services.integration.channel_engagement_service.PointService') as mock_ps2, \
             patch('services.integration.event_coordinator.PointService') as mock_ps3:
            
            mock_ps.return_value = AsyncMock()
            mock_ps2.return_value = AsyncMock()
            mock_ps3.return_value = AsyncMock()
            
            from services.coordinador_central import CoordinadorCentral
            
            coordinador = CoordinadorCentral(session)
            
            # Mock service exception
            coordinador.channel_engagement.award_channel_reaction = AsyncMock(
                side_effect=Exception("Database connection error")
            )
            
            result = await coordinador.ejecutar_flujo(
                test_user.id,
                AccionUsuario.REACCIONAR_PUBLICACION,
                message_id=456,
                channel_id=-123456,
                reaction_type="like"
            )
            
            # Critical exception handling
            assert result["success"] is False, "Service exceptions handled gracefully"
            assert "error inesperado" in result["message"], "User-friendly error provided"
            assert "error" in result, "Error details logged for debugging"

    async def test_performance_regression_check(self, session):
        """Test performance stays within acceptable limits."""
        with patch('services.integration.narrative_point_service.PointService') as mock_ps, \
             patch('services.integration.channel_engagement_service.PointService') as mock_ps2, \
             patch('services.integration.event_coordinator.PointService') as mock_ps3:
            
            mock_ps.return_value = AsyncMock()
            mock_ps2.return_value = AsyncMock()
            mock_ps3.return_value = AsyncMock()
            
            from services.coordinador_central import CoordinadorCentral
            
            coordinador = CoordinadorCentral(session)
            coordinador.channel_engagement.award_channel_reaction = AsyncMock(return_value=True)
            
            # Measure workflow performance
            start_time = time.perf_counter()
            
            result = await coordinador.ejecutar_flujo(
                123456789,
                AccionUsuario.REACCIONAR_PUBLICACION,
                message_id=456,
                channel_id=-123456789,
                reaction_type="like"
            )
            
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            
            # Performance regression check (allowing 100% margin for test environment)
            assert duration_ms < 30.8, f"Workflow took {duration_ms:.2f}ms, exceeds threshold"
            assert result is not None, "Workflow must produce result"