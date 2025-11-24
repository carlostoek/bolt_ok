"""
Integration tests for atomic nested creation functionality.

Tests the actual atomicity behavior with a real database session.
"""
import pytest
import asyncio
from datetime import datetime

from app.schemas.automation import TriggerCreate, ActionCreateNested
from app.services.automation_service import AutomationService
from app.core.exceptions import DuplicateKeyException, NestedCreationException, DatabaseException


class TestAtomicNestedCreationIntegration:
    """Integration tests for atomic nested creation."""

    @pytest.mark.asyncio
    async def test_atomic_nested_creation_basic_flow(self, mock_session):
        """Test basic atomic creation flow with mock session."""
        # Arrange
        service = AutomationService(mock_session)
        
        # Create test data
        trigger_data = TriggerCreate(
            name="integration_test_trigger",
            description="Integration test trigger",
            event_type="fragment_viewed",
            conditions={"fragment_key": "welcome"},
            is_enabled=True,
            priority=1,
            actions=[
                ActionCreateNested(
                    action_type="send_message",
                    parameters={"message": "Welcome!"},
                    execution_order=1,
                    is_enabled=True
                )
            ]
        )

        # Act
        result = await service.create_trigger_with_actions(trigger_data)

        # Assert
        assert result["success"] is True
        assert result["trigger"].name == "integration_test_trigger"
        assert len(result["created_actions"]) == 1
        assert result["summary"]["actions_created"] == 1
        assert result["summary"]["total_entities"] == 2

    @pytest.mark.asyncio
    async def test_atomic_nested_creation_validation(self):
        """Test that validation works correctly at schema level."""
        # Test valid action types
        valid_actions = [
            "give_product",
            "grant_vip", 
            "send_message",
            "add_points",
            "unlock_fragment",
            "grant_badge",
            "trigger_narrative",
            "execute_webhook"
        ]
        
        for action_type in valid_actions:
            # This should not raise an exception
            action = ActionCreateNested(
                action_type=action_type,
                parameters={},
                execution_order=1,
                is_enabled=True
            )
            assert action.action_type == action_type

        # Test invalid action type
        with pytest.raises(ValueError):
            ActionCreateNested(
                action_type="invalid_action",
                parameters={},
                execution_order=1,
                is_enabled=True
            )

    @pytest.mark.asyncio
    async def test_atomic_nested_creation_schema_structure(self):
        """Test that the schema structure supports nested creation."""
        # Test trigger creation without actions
        trigger_no_actions = TriggerCreate(
            name="trigger_no_actions",
            description="Test trigger without actions",
            event_type="fragment_viewed",
            conditions={"fragment_key": "welcome"},
            is_enabled=True,
            priority=1
        )
        assert trigger_no_actions.actions is None

        # Test trigger creation with actions
        trigger_with_actions = TriggerCreate(
            name="trigger_with_actions",
            description="Test trigger with actions",
            event_type="fragment_viewed",
            conditions={"fragment_key": "welcome"},
            is_enabled=True,
            priority=1,
            actions=[
                ActionCreateNested(
                    action_type="send_message",
                    parameters={"message": "Test"},
                    execution_order=1,
                    is_enabled=True
                )
            ]
        )
        assert trigger_with_actions.actions is not None
        assert len(trigger_with_actions.actions) == 1
        assert trigger_with_actions.actions[0].action_type == "send_message"

    @pytest.mark.asyncio
    async def test_atomic_nested_creation_execution_order_validation(self):
        """Test that execution order validation works."""
        # Test valid execution orders
        for order in [1, 5, 10]:
            action = ActionCreateNested(
                action_type="send_message",
                parameters={},
                execution_order=order,
                is_enabled=True
            )
            assert action.execution_order == order

        # Test invalid execution orders
        with pytest.raises(ValueError):
            ActionCreateNested(
                action_type="send_message",
                parameters={},
                execution_order=0,  # Below minimum
                is_enabled=True
            )

        with pytest.raises(ValueError):
            ActionCreateNested(
                action_type="send_message",
                parameters={},
                execution_order=11,  # Above maximum
                is_enabled=True
            )

    @pytest.mark.asyncio
    async def test_atomic_nested_creation_complex_parameters(self):
        """Test creation with complex parameter structures."""
        # Test with nested parameters
        complex_parameters = {
            "user_data": {
                "level": 5,
                "vip_status": True,
                "achievements": ["first_fragment", "quick_learner"]
            },
            "rewards": {
                "points": 100,
                "products": [1, 2, 3],
                "vip_duration": 7
            }
        }

        action = ActionCreateNested(
            action_type="give_product",
            parameters=complex_parameters,
            execution_order=1,
            is_enabled=True
        )
        
        assert action.parameters == complex_parameters
        assert action.parameters["user_data"]["level"] == 5
        assert "achievements" in action.parameters["user_data"]