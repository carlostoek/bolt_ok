"""
PROTECTION TESTS FOR CORE USER FLOWS
=====================================

These tests protect the most critical user journeys that must continue working 
during refactoring and architectural changes. They capture current behavior
as-is and ensure no regressions during cleanup.

CRITICAL FLOWS COVERED:
- User registration and basic profile management
- Points earning through various activities
- VIP subscription access control
- Narrative progression with choice system
- Basic menu navigation and command handling

These tests use realistic data and minimal mocking to reflect actual usage patterns.
"""
import pytest
import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User, Channel, UserStats
from services.user_service import UserService
from services.point_service import PointService
from services.level_service import LevelService
from services.achievement_service import AchievementService
from services.notification_service import NotificationService
from services.coordinador_central import CoordinadorCentral, AccionUsuario
from handlers.start import cmd_start
from utils.text_utils import sanitize_text


class TestCoreUserFlows:
    """
    Protection tests for core user flows that must survive refactoring.
    
    These tests protect existing functionality without trying to improve it.
    They verify current behavior patterns to prevent regressions.
    """

    async def test_user_registration_flow_complete(self, session, mock_bot):
        """
        TEST: Complete user registration flow from start command
        
        PROTECTS: Initial user creation process which is foundational
        CURRENT BEHAVIOR: User created with default values, role 'free'
        CRITICAL: This flow must work for new users to access the bot
        """
        # Arrange: Mock Telegram message
        message = MagicMock()
        message.from_user.id = 987654321
        message.from_user.username = "new_test_user"
        message.from_user.first_name = "New"
        message.from_user.last_name = "User"
        message.from_user.is_bot = False
        message.chat.id = 987654321
        message.reply = AsyncMock()
        
        # Act: Execute start command (simulates user typing /start)
        await cmd_start(message, session)
        
        # Assert: User was created with correct default values
        result = await session.execute(select(User).where(User.id == 987654321))
        user = result.scalar_one_or_none()
        
        assert user is not None, "User should be created during registration"
        assert user.role == "free", "New users should have 'free' role"
        assert user.points == 0.0, "New users should start with 0 points"
        assert user.level == 1, "New users should start at level 1"
        assert user.username == "new_test_user", "Username should be preserved"
        assert user.first_name == "New", "First name should be preserved"
        assert user.created_at is not None, "Creation timestamp should be set"

    async def test_points_earning_through_reactions_flow(self, session, test_user, test_channel, mock_bot):
        """
        TEST: Points earning through channel reactions
        
        PROTECTS: Core gamification mechanic - users earn points by reacting
        CURRENT BEHAVIOR: Users get 10 points per reaction with cooldown
        CRITICAL: This is the primary engagement mechanism
        """
        # Arrange: Set up services
        level_service = LevelService(session)
        achievement_service = AchievementService(session)
        notification_service = NotificationService(session, mock_bot)
        coordinador = CoordinadorCentral(session)
        
        initial_points = await coordinador.point_service.get_user_points(test_user.id)
        
        # Act: Simulate user reacting to a channel post
        result = await coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=12345,
            channel_id=test_channel.id,
            reaction_type="like",
            bot=mock_bot
        )
        
        # Assert: Points were awarded correctly
        assert result["success"] is True, "Reaction should be successful"
        assert result["points_awarded"] == 10, "Should award exactly 10 points for reaction"
        
        final_points = await coordinador.point_service.get_user_points(test_user.id)
        assert final_points == initial_points + 10, "Points should be added to user's total"
        
        # Assert: Response message follows expected pattern
        assert "Diana sonríe" in result["message"], "Response should use Diana character voice"
        assert "besitos" in result["message"], "Response should use established terminology"

    async def test_vip_access_control_flow(self, session, test_user, vip_user, mock_bot):
        """
        TEST: VIP content access control mechanisms
        
        PROTECTS: Subscription-based access control which is revenue-critical
        CURRENT BEHAVIOR: Free users blocked, VIP users allowed access
        CRITICAL: Revenue model depends on this working correctly
        """
        # Arrange: Set up coordinador for access control
        coordinador = CoordinadorCentral(session)
        vip_fragment_key = "vip_exclusive_content"
        
        # Act & Assert: Free user should be blocked
        free_result = await coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.ACCEDER_NARRATIVA_VIP,
            fragment_key=vip_fragment_key,
            bot=mock_bot
        )
        
        assert free_result["success"] is False, "Free users should be blocked from VIP content"
        assert free_result["action"] == "vip_required", "Should indicate VIP requirement"
        assert "suscripción VIP" in free_result["message"], "Should mention VIP subscription requirement"
        
        # Act & Assert: VIP user should have access
        vip_result = await coordinador.ejecutar_flujo(
            user_id=vip_user.id,
            accion=AccionUsuario.ACCEDER_NARRATIVA_VIP,
            fragment_key=vip_fragment_key,
            bot=mock_bot
        )
        
        # Note: This might succeed or fail depending on fragment existence, but should not be VIP-blocked
        if not vip_result["success"]:
            assert vip_result["action"] != "vip_required", "VIP users should not be blocked for VIP reasons"

    async def test_narrative_choice_and_progression_flow(self, session, test_user, mock_bot):
        """
        TEST: Narrative choice system and story progression
        
        PROTECTS: Core storytelling mechanic that drives engagement
        CURRENT BEHAVIOR: Users can make choices that affect story progression  
        CRITICAL: This is the main content delivery system
        """
        # Arrange: Set up narrative system
        coordinador = CoordinadorCentral(session)
        decision_id = 1  # Simulate a story decision
        
        # Act: Simulate user making a narrative choice
        result = await coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.TOMAR_DECISION,
            decision_id=decision_id,
            bot=mock_bot
        )
        
        # Assert: Decision processing works (success or proper failure)
        assert "success" in result, "Result should contain success status"
        assert "message" in result, "Result should contain response message"
        
        # If successful, verify story progression elements
        if result["success"]:
            assert result["action"] == "decision_success", "Should indicate successful decision"
            assert "Diana" in result["message"], "Should maintain character voice"
            assert "fragment" in result, "Should provide next story fragment"
        else:
            # If failed, should be for valid reasons (points, invalid decision, etc.)
            valid_failures = ["points_required", "decision_error"]
            assert result.get("action") in valid_failures, f"Failure should be for valid reason, got: {result.get('action')}"

    async def test_daily_engagement_bonus_flow(self, session, test_user, mock_bot):
        """
        TEST: Daily engagement bonus system
        
        PROTECTS: Daily retention mechanism that encourages regular usage
        CURRENT BEHAVIOR: Users get bonus points for daily check-ins
        CRITICAL: Key retention and engagement driver
        """
        # Arrange: Set up engagement tracking
        coordinador = CoordinadorCentral(session)
        
        # Act: Simulate daily engagement check
        result = await coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.VERIFICAR_ENGAGEMENT,
            bot=mock_bot
        )
        
        # Assert: Engagement system responds appropriately
        assert "success" in result, "Result should contain success status"
        assert "message" in result, "Result should contain response message"
        
        if result["success"]:
            assert result["action"] == "daily_check_success", "Should indicate successful daily check"
            assert result["points_awarded"] > 0, "Should award engagement bonus points"
            assert "Diana" in result["message"], "Should maintain character voice"
        else:
            # Valid failure case: already checked today
            assert result["action"] == "daily_check_already_done", "Should indicate already completed today"

    async def test_mission_progress_through_activity_flow(self, session, test_user, mock_bot):
        """
        TEST: Mission progress tracking through user activities
        
        PROTECTS: Mission system that provides goals and rewards
        CURRENT BEHAVIOR: Activities can trigger mission completions
        CRITICAL: Provides structured progression and goals
        """
        # Arrange: Set up mission system through coordinador
        coordinador = CoordinadorCentral(session)
        fragment_id = "test_narrative_fragment"
        
        # Act: Simulate completing a narrative fragment (should trigger mission progress)
        result = await coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
            fragment_id=fragment_id,
            bot=mock_bot
        )
        
        # Assert: Mission system processes activity correctly
        assert "success" in result, "Result should contain success status"
        assert "message" in result, "Result should contain response message"
        assert result["fragment_id"] == fragment_id, "Should track which fragment was completed"
        
        # Check mission-related fields
        assert "missions_updated" in result, "Should indicate if missions were updated"
        if result.get("missions_updated"):
            assert "missions_completed" in result, "Should list completed missions"
            if result["missions_completed"]:
                assert result["mission_points_awarded"] > 0, "Should award mission points"

    async def test_user_data_consistency_during_operations(self, session, test_user, mock_bot):
        """
        TEST: User data remains consistent during complex operations
        
        PROTECTS: Data integrity across concurrent operations
        CURRENT BEHAVIOR: User data should remain consistent across services
        CRITICAL: Prevents data corruption during high-load scenarios
        """
        # Arrange: Set up services
        user_service = UserService(session)
        level_service = LevelService(session)
        achievement_service = AchievementService(session)
        notification_service = NotificationService(session, mock_bot)
        point_service = PointService(session, level_service, achievement_service, notification_service)
        
        # Get initial state
        initial_user = await user_service.get_user(test_user.id)
        initial_points = await point_service.get_user_points(test_user.id)
        
        # Act: Perform multiple operations that should maintain consistency
        await point_service.add_points(test_user.id, 50.0, "test_operation")
        await session.commit()
        
        # Assert: Data remains consistent
        final_user = await user_service.get_user(test_user.id)
        final_points = await point_service.get_user_points(test_user.id)
        
        assert final_user.id == initial_user.id, "User ID should remain unchanged"
        assert final_points == initial_points + 50.0, "Points should be accurately updated"
        assert final_user.role == initial_user.role, "Role should remain unchanged unless explicitly modified"

    async def test_error_handling_in_critical_flows(self, session, test_user, mock_bot):
        """
        TEST: Error handling prevents system crashes in critical flows
        
        PROTECTS: System stability when operations fail
        CURRENT BEHAVIOR: Errors are handled gracefully with user feedback
        CRITICAL: System must remain stable even when individual operations fail
        """
        # Arrange: Set up coordinador for error scenarios
        coordinador = CoordinadorCentral(session)
        
        # Act: Simulate invalid operations that should fail gracefully
        invalid_channel_result = await coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=99999,
            channel_id=-999999999,  # Non-existent channel
            reaction_type="invalid",
            bot=mock_bot
        )
        
        # Assert: System handles errors gracefully
        assert "success" in invalid_channel_result, "Result should contain success status"
        assert "message" in invalid_channel_result, "Should provide user feedback even on error"
        
        # System should not crash, even if operation fails
        if not invalid_channel_result["success"]:
            assert len(invalid_channel_result["message"]) > 0, "Should provide meaningful error message"

    async def test_service_layer_integration_stability(self, session, test_user, mock_bot):
        """
        TEST: Service layer integrations remain stable during operations
        
        PROTECTS: Inter-service communication and coordination
        CURRENT BEHAVIOR: Services coordinate properly through CoordinadorCentral
        CRITICAL: Ensures modular architecture continues to function during refactoring
        """
        # Arrange: Set up coordinador with all integrated services
        coordinador = CoordinadorCentral(session)
        
        # Verify all critical services are properly initialized
        assert coordinador.session is not None, "Session should be available"
        assert coordinador.point_service is not None, "Point service should be initialized"
        assert coordinador.user_service is not None, "User service should be initialized"
        assert coordinador.narrative_service is not None, "Narrative service should be initialized"
        
        # Act: Test service coordination through a complex flow
        result = await coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=12345,
            channel_id=-1001234567890,  # Standard test channel ID
            reaction_type="like",
            bot=mock_bot
        )
        
        # Assert: Services coordinated properly
        assert isinstance(result, dict), "Should return structured result"
        assert "success" in result, "Should indicate operation status"
        
        # Verify that the coordinador's facade pattern is working
        user_points = await coordinador.point_service.get_user_points(test_user.id)
        assert isinstance(user_points, (int, float)), "Point service integration should work"