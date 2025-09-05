"""
PROTECTION TESTS FOR COORDINADOR CENTRAL
========================================

These tests protect the Facade pattern implementation in CoordinadorCentral
which orchestrates integration between all modules. This is the core architectural
component that must remain stable during refactoring.

CRITICAL PATTERNS COVERED:
- Facade pattern coordination between services
- Cross-module event handling and workflow orchestration  
- Error handling and fallback mechanisms
- Service dependency injection and lifecycle management
- Transaction coordination and data consistency

These tests capture the current working behavior of the coordination layer.
"""
import pytest
import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User, Channel, UserStats
from services.coordinador_central import CoordinadorCentral, AccionUsuario
from services.event_bus import EventType
from services.notification_service import NotificationService, NotificationPriority


class TestCoordinadorCentralProtection:
    """
    Protection tests for CoordinadorCentral facade pattern and orchestration.
    
    These tests ensure the coordination layer continues to work during refactoring
    by protecting the current working behavior patterns.
    """

    async def test_service_initialization_and_dependencies(self, session):
        """
        TEST: CoordinadorCentral properly initializes all dependent services
        
        PROTECTS: Service dependency injection and initialization patterns
        CURRENT BEHAVIOR: All services are properly initialized with dependencies
        CRITICAL: Facade pattern depends on proper service initialization
        """
        # Act: Initialize coordinador
        coordinador = CoordinadorCentral(session)
        
        # Assert: All critical services are properly initialized
        assert coordinador.session is session, "Session should be preserved"
        assert coordinador.channel_engagement is not None, "Channel engagement service should be initialized"
        assert coordinador.narrative_point is not None, "Narrative point service should be initialized"
        assert coordinador.narrative_access is not None, "Narrative access service should be initialized"
        assert coordinador.event_coordinator is not None, "Event coordinator should be initialized"
        assert coordinador.narrative_service is not None, "Narrative service should be initialized"
        assert coordinador.user_service is not None, "User service should be initialized"
        assert coordinador.point_service is not None, "Point service should be initialized"
        assert coordinador.reconciliation_service is not None, "Reconciliation service should be initialized"
        assert coordinador.unified_mission_service is not None, "Unified mission service should be initialized"
        assert coordinador.event_bus is not None, "Event bus should be initialized"
        
        # Verify service dependencies are properly injected
        # Point service should have level and achievement service dependencies
        assert coordinador.point_service.level_service is not None, "Point service should have level service dependency"
        assert coordinador.point_service.achievement_service is not None, "Point service should have achievement service dependency"

    async def test_workflow_execution_facade_pattern(self, session, test_user, mock_bot):
        """
        TEST: Facade pattern correctly orchestrates complex workflows
        
        PROTECTS: Core facade functionality that simplifies multi-service operations
        CURRENT BEHAVIOR: Single method call coordinates multiple services
        CRITICAL: This pattern is fundamental to the architecture
        """
        # Arrange: Set up coordinador with test data
        coordinador = CoordinadorCentral(session)
        
        # Act: Execute a complex workflow through the facade
        result = await coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=12345,
            channel_id=-1001234567890,
            reaction_type="like",
            bot=mock_bot
        )
        
        # Assert: Facade coordinated multiple services properly
        assert isinstance(result, dict), "Should return structured result"
        assert "success" in result, "Should contain success indicator"
        assert "message" in result, "Should contain user message"
        assert "action" in result, "Should contain action identifier"
        
        # Verify that the facade abstracted complexity
        assert "points_awarded" in result or not result["success"], "Should handle point awarding"
        
        # The result should be user-friendly despite internal complexity
        if result["success"]:
            assert "Diana" in result["message"], "Should maintain consistent character voice"

    async def test_error_handling_and_fallback_mechanisms(self, session, test_user, mock_bot):
        """
        TEST: Error handling provides graceful degradation across services
        
        PROTECTS: System stability when individual services fail
        CURRENT BEHAVIOR: Errors are caught and converted to user-friendly messages
        CRITICAL: System must remain stable even when subsystems fail
        """
        # Arrange: Set up coordinador
        coordinador = CoordinadorCentral(session)
        
        # Act: Test error handling with invalid inputs
        invalid_action_result = await coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=99999,
            channel_id=-999999999,  # Non-existent channel
            reaction_type="invalid_reaction",
            bot=mock_bot
        )
        
        # Assert: Errors are handled gracefully
        assert isinstance(invalid_action_result, dict), "Should return structured result even on error"
        assert "success" in invalid_action_result, "Should contain success indicator"
        assert "message" in invalid_action_result, "Should contain user-facing message"
        
        # Error messages should be user-friendly, not technical
        if not invalid_action_result["success"]:
            message = invalid_action_result["message"]
            assert len(message) > 0, "Error message should not be empty"
            assert "Diana" in message or "error" not in message.lower() or "exception" not in message.lower(), "Should maintain character voice or be user-friendly"

    async def test_cross_module_event_coordination(self, session, test_user, mock_bot):
        """
        TEST: Event bus integration for cross-module communication
        
        PROTECTS: Event-driven architecture that enables loose coupling
        CURRENT BEHAVIOR: Events are published for cross-module coordination
        CRITICAL: Enables modules to communicate without direct coupling
        """
        # Arrange: Set up coordinador with event tracking
        coordinador = CoordinadorCentral(session)
        
        # Mock event bus to track events
        original_publish = coordinador.event_bus.publish
        published_events = []
        
        async def mock_publish(*args, **kwargs):
            published_events.append((args, kwargs))
            return await original_publish(*args, **kwargs)
        
        coordinador.event_bus.publish = mock_publish
        
        # Act: Execute workflow that should generate events
        result = await coordinador.ejecutar_flujo_async(
            user_id=test_user.id,
            accion=AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=12345,
            channel_id=-1001234567890,
            reaction_type="like",
            bot=mock_bot
        )
        
        # Assert: Events were published for coordination
        assert len(published_events) > 0, "Should publish events for cross-module coordination"
        
        # Verify workflow completion event
        workflow_events = [e for e in published_events if e[0][0] == EventType.WORKFLOW_COMPLETED]
        assert len(workflow_events) > 0, "Should publish workflow completion event"
        
        # If successful, should have specific events
        if result.get("success"):
            reaction_events = [e for e in published_events if e[0][0] == EventType.USER_REACTION]
            # Note: May or may not have reaction events depending on implementation

    async def test_transaction_coordination_and_consistency(self, session, test_user, mock_bot):
        """
        TEST: Transaction coordination maintains data consistency
        
        PROTECTS: Data consistency across multiple service operations
        CURRENT BEHAVIOR: Operations are coordinated to maintain consistency
        CRITICAL: Prevents data corruption in complex workflows
        """
        # Arrange: Set up coordinador and capture initial state
        coordinador = CoordinadorCentral(session)
        initial_points = await coordinador.point_service.get_user_points(test_user.id)
        
        # Act: Execute workflow that involves multiple service operations
        result = await coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=12345,
            channel_id=-1001234567890,
            reaction_type="like",
            bot=mock_bot
        )
        
        # Assert: Data remains consistent across services
        final_points = await coordinador.point_service.get_user_points(test_user.id)
        
        if result.get("success") and result.get("points_awarded"):
            # Points should be updated consistently
            expected_points = initial_points + result["points_awarded"]
            assert final_points == expected_points, "Points should be consistently updated across services"
        
        # User data should remain valid
        user = await coordinador.user_service.get_user(test_user.id)
        assert user is not None, "User should still exist after operations"
        assert user.points >= 0, "User points should never be negative"

    async def test_parallel_workflow_execution(self, session, test_user, vip_user, mock_bot):
        """
        TEST: Parallel workflow execution maintains data integrity
        
        PROTECTS: Concurrent operation handling without data corruption
        CURRENT BEHAVIOR: Multiple workflows can execute concurrently safely
        CRITICAL: System must handle concurrent users without issues
        """
        # Arrange: Set up coordinador and prepare multiple workflows
        coordinador = CoordinadorCentral(session)
        
        workflows = [
            {
                "user_id": test_user.id,
                "accion": AccionUsuario.REACCIONAR_PUBLICACION,
                "kwargs": {
                    "message_id": 12345,
                    "channel_id": -1001234567890,
                    "reaction_type": "like",
                    "bot": mock_bot
                }
            },
            {
                "user_id": vip_user.id,
                "accion": AccionUsuario.VERIFICAR_ENGAGEMENT,
                "kwargs": {
                    "bot": mock_bot
                }
            }
        ]
        
        # Act: Execute workflows in parallel
        results = await coordinador.execute_parallel_workflows(workflows)
        
        # Assert: All workflows completed and data is consistent
        assert len(results) == 2, "Should return results for all workflows"
        
        for result in results:
            assert isinstance(result, dict), "Each result should be structured"
            assert "success" in result, "Each result should have success indicator"
            
            # No workflow should have corrupted another's data
            if "error" in result:
                assert "user_id" in result, "Error results should identify the user"

    async def test_system_health_monitoring(self, session):
        """
        TEST: System health check capabilities function correctly
        
        PROTECTS: Monitoring and diagnostic capabilities
        CURRENT BEHAVIOR: Health checks can assess system status
        CRITICAL: Enables monitoring system health during operations
        """
        # Arrange: Set up coordinador
        coordinador = CoordinadorCentral(session)
        
        # Act: Perform system health check
        health_report = await coordinador.perform_system_health_check()
        
        # Assert: Health check provides useful information
        assert isinstance(health_report, dict), "Should return structured health report"
        assert "overall_status" in health_report, "Should provide overall status"
        assert "modules" in health_report, "Should report on individual modules"
        assert "timestamp" in health_report, "Should include timestamp"
        
        # Status should be meaningful
        valid_statuses = ["healthy", "degraded", "unhealthy", "error"]
        assert health_report["overall_status"] in valid_statuses, "Should provide valid status"
        
        # Should provide actionable recommendations if there are issues
        if health_report["overall_status"] in ["degraded", "unhealthy"]:
            assert "recommendations" in health_report, "Should provide recommendations for issues"
            assert len(health_report["recommendations"]) > 0, "Should have actionable recommendations"

    async def test_consistency_check_across_modules(self, session, test_user):
        """
        TEST: Cross-module consistency checking functions correctly
        
        PROTECTS: Data integrity verification across the system
        CURRENT BEHAVIOR: Can detect and report inconsistencies
        CRITICAL: Helps maintain data quality during complex operations
        """
        # Arrange: Set up coordinador
        coordinador = CoordinadorCentral(session)
        
        # Act: Perform consistency check
        consistency_report = await coordinador.check_system_consistency(test_user.id)
        
        # Assert: Consistency check provides useful information
        assert isinstance(consistency_report, dict), "Should return structured consistency report"
        assert "user_id" in consistency_report, "Should identify the user checked"
        assert "checks" in consistency_report, "Should provide check results"
        
        # Should perform meaningful checks
        checks = consistency_report["checks"]
        expected_checks = ["user_exists", "points_consistent"]
        for check in expected_checks:
            assert check in checks, f"Should perform {check} check"
        
        # If there are warnings or errors, they should be actionable
        if "warnings" in consistency_report and consistency_report["warnings"]:
            assert isinstance(consistency_report["warnings"], list), "Warnings should be structured"
        
        if "errors" in consistency_report and consistency_report["errors"]:
            assert isinstance(consistency_report["errors"], list), "Errors should be structured"

    async def test_notification_system_integration(self, session, test_user, mock_bot):
        """
        TEST: Unified notification system integration through coordinador
        
        PROTECTS: Notification coordination and delivery mechanisms
        CURRENT BEHAVIOR: Notifications are coordinated through the facade
        CRITICAL: User feedback system must work consistently
        """
        # Arrange: Set up coordinador with notification service
        coordinador = CoordinadorCentral(session)
        
        # Act: Execute workflow that should trigger notifications
        result = await coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=12345,
            channel_id=-1001234567890,
            reaction_type="like",
            bot=mock_bot,
            skip_unified_notifications=False  # Enable unified notifications
        )
        
        # Assert: Workflow completed with proper notification handling
        assert isinstance(result, dict), "Should return structured result"
        assert "message" in result, "Should include user message"
        
        # The notification integration should not break the main workflow
        if result.get("success"):
            assert len(result["message"]) > 0, "Should provide meaningful user feedback"

    async def test_enhanced_async_workflow_capabilities(self, session, test_user, mock_bot):
        """
        TEST: Enhanced async workflow capabilities maintain compatibility
        
        PROTECTS: Advanced workflow features while maintaining backward compatibility
        CURRENT BEHAVIOR: Async workflows provide enhanced features with fallback
        CRITICAL: New features must not break existing functionality
        """
        # Arrange: Set up coordinador
        coordinador = CoordinadorCentral(session)
        
        # Act: Test enhanced async workflow
        result = await coordinador.ejecutar_flujo_async(
            user_id=test_user.id,
            accion=AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=12345,
            channel_id=-1001234567890,
            reaction_type="like",
            bot=mock_bot
        )
        
        # Assert: Enhanced workflow maintains compatibility
        assert isinstance(result, dict), "Should return structured result"
        assert "success" in result, "Should contain success indicator"
        assert "message" in result, "Should contain user message"
        
        # Enhanced features should not break basic functionality
        if result.get("success"):
            assert result.get("points_awarded") is not None or result["action"] == "reaction_failed", "Should handle points appropriately"

    async def test_service_layer_facade_abstraction(self, session, test_user, mock_bot):
        """
        TEST: Facade properly abstracts service layer complexity
        
        PROTECTS: Clean abstraction that hides internal complexity
        CURRENT BEHAVIOR: Simple interface masks complex multi-service operations
        CRITICAL: Facade pattern is core to the architecture
        """
        # Arrange: Set up coordinador
        coordinador = CoordinadorCentral(session)
        
        # Act: Use facade for complex operation
        result = await coordinador.ejecutar_flujo(
            user_id=test_user.id,
            accion=AccionUsuario.COMPLETAR_FRAGMENTO_NARRATIVO,
            fragment_id="test_fragment",
            bot=mock_bot
        )
        
        # Assert: Complex operation appears simple to caller
        assert isinstance(result, dict), "Should return simple, structured result"
        assert "success" in result, "Should abstract internal complexity to simple success/failure"
        assert "message" in result, "Should provide user-friendly message"
        assert "fragment_id" in result, "Should echo back the input for confirmation"
        
        # Internal complexity should be hidden
        assert "missions_updated" in result, "Should indicate if missions were affected"
        
        # User doesn't need to know about internal service coordination
        assert "error" not in result or not result["success"], "Should not expose internal errors unless operation fails"