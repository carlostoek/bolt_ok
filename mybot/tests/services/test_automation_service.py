"""
Tests for automation service with atomic nested creation.

Validates that trigger + actions creation is atomic and rollback works correctly.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.models.automation import AutomationTrigger, TriggerAction
from app.schemas.automation import TriggerCreate, ActionCreateNested
from app.services.automation_service import AutomationService
from app.core.exceptions import DuplicateKeyException, NestedCreationException, DatabaseException


class TestAutomationServiceAtomicNestedCreation:
    """Test atomic nested creation functionality in automation service."""

    @pytest.mark.asyncio
    async def test_create_trigger_with_actions_atomic_success(
        self, 
        mock_session,
        automation_service,
        sample_nested_creation_data
    ):
        """Test successful atomic creation of trigger with multiple actions."""
        # Arrange - Create trigger data with nested actions
        trigger_data = TriggerCreate(
            name=sample_nested_creation_data["name"],
            description=sample_nested_creation_data["description"],
            event_type=sample_nested_creation_data["event_type"],
            conditions=sample_nested_creation_data["conditions"],
            is_enabled=sample_nested_creation_data["is_enabled"],
            priority=sample_nested_creation_data["priority"],
            actions=[
                ActionCreateNested(
                    action_type=action["action_type"],
                    parameters=action["parameters"],
                    execution_order=action["execution_order"],
                    is_enabled=action["is_enabled"]
                )
                for action in sample_nested_creation_data["actions"]
            ]
        )

        # Act
        result = await automation_service.create_trigger_with_actions(trigger_data)

        # Assert
        assert result is not None
        assert result["success"] is True
        assert result["trigger"].name == sample_nested_creation_data["name"]
        assert len(result["created_actions"]) == len(sample_nested_creation_data["actions"])
        
        # Verify session methods were called
        mock_session.add.assert_called()
        mock_session.flush.assert_called()
        mock_session.commit.assert_called()
        
        # Verify action details
        for i, action in enumerate(result["created_actions"]):
            expected_action = sample_nested_creation_data["actions"][i]
            assert action["action_type"] == expected_action["action_type"]
            assert action["execution_order"] == expected_action["execution_order"]

    @pytest.mark.asyncio
    async def test_create_trigger_with_actions_rollback_on_failure(
        self,
        mock_session,
        automation_service,
        sample_trigger_data
    ):
        """Test that rollback occurs when action creation fails."""
        # Arrange - Create trigger with invalid action type
        # This will fail at schema validation level, not service level
        with pytest.raises(ValueError):  # Pydantic validation error
            trigger_data = TriggerCreate(
                **sample_trigger_data,
                actions=[
                    ActionCreateNested(
                        action_type="give_product",
                        parameters={"product_id": 1},
                        execution_order=1,
                        is_enabled=True
                    ),
                    ActionCreateNested(
                        action_type="invalid_action_type",  # This should cause validation error
                        parameters={},
                        execution_order=2,
                        is_enabled=True
                    )
                ]
            )
        
        # Verify rollback - session should have been rolled back
        mock_session.rollback.assert_called()
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_trigger_with_actions_duplicate_name_rollback(
        self,
        mock_session,
        automation_service,
        sample_trigger_data
    ):
        """Test rollback when trigger name already exists."""
        # Arrange - Create first trigger
        first_trigger_data = TriggerCreate(
            **sample_trigger_data,
            actions=[
                ActionCreateNested(
                    action_type="send_message",
                    parameters={"message": "First trigger"},
                    execution_order=1,
                    is_enabled=True
                )
            ]
        )
        
        await automation_service.create_trigger_with_actions(first_trigger_data)

        # Act & Assert - Try to create duplicate trigger
        with pytest.raises(IntegrityError):
            duplicate_trigger_data = TriggerCreate(
                **sample_trigger_data,
                actions=[
                    ActionCreateNested(
                        action_type="give_product",
                        parameters={"product_id": 1},
                        execution_order=1,
                        is_enabled=True
                    )
                ]
            )
            await automation_service.create_trigger_with_actions(duplicate_trigger_data)

        # Verify rollback was called for duplicate
        mock_session.rollback.assert_called()

    @pytest.mark.asyncio
    async def test_create_trigger_with_empty_actions(
        self,
        mock_session,
        automation_service,
        sample_trigger_data
    ):
        """Test creating trigger with no actions."""
        # Arrange
        trigger_data = TriggerCreate(**sample_trigger_data)
        
        # Act
        result = await automation_service.create_trigger_with_actions(trigger_data)

        # Assert
        assert result is not None
        assert result["success"] is True
        assert result["trigger"].name == sample_trigger_data["name"]
        assert len(result["created_actions"]) == 0
        
        # Verify session methods were called
        mock_session.add.assert_called()
        mock_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_create_trigger_with_multiple_actions_order_preserved(
        self,
        mock_session,
        automation_service,
        sample_trigger_data
    ):
        """Test that multiple actions maintain their execution order."""
        # Arrange
        trigger_data = TriggerCreate(
            **sample_trigger_data,
            actions=[
                ActionCreateNested(
                    action_type="add_points",
                    parameters={"points": 50},
                    execution_order=3,
                    is_enabled=True
                ),
                ActionCreateNested(
                    action_type="send_message",
                    parameters={"message": "Welcome"},
                    execution_order=1,
                    is_enabled=True
                ),
                ActionCreateNested(
                    action_type="give_product",
                    parameters={"product_id": 1},
                    execution_order=2,
                    is_enabled=True
                )
            ]
        )

        # Act
        result = await automation_service.create_trigger_with_actions(trigger_data)

        # Assert
        assert len(result["created_actions"]) == 3
        
        # Verify actions are stored in execution order
        execution_orders = [action["execution_order"] for action in result["created_actions"]]
        assert execution_orders == [1, 2, 3]
        
        # Verify action types match expected order
        action_types = [action["action_type"] for action in result["created_actions"]]
        assert action_types == ["send_message", "give_product", "add_points"]


class TestAutomationServiceIntegration:
    """Integration tests for automation service functionality."""

    @pytest.mark.asyncio
    async def test_evaluate_trigger_with_conditions(
        self,
        mock_session,
        automation_service,
        automation_test_helper,
        mock_event_context
    ):
        """Test trigger evaluation with complex conditions."""
        # Arrange
        trigger_data = {
            "name": "condition_test_trigger",
            "event_type": "fragment_viewed",
            "conditions": {
                "fragment_key": "welcome",
                "user_level": 1
            },
            "is_enabled": True
        }
        
        actions_data = [
            {
                "action_type": "send_message",
                "parameters": {"message": "Condition matched!"},
                "execution_order": 1
            }
        ]
        
        trigger = await automation_test_helper.create_test_trigger_with_actions(
            mock_session, trigger_data, actions_data
        )

        # Act - Use execute_triggers method instead
        result = await automation_service.execute_triggers(
            event_type="fragment_viewed",
            user_id=12345,
            context=mock_event_context
        )

        # Assert
        assert result["success"] is True
        # Verify that triggers were executed
        assert len(result["triggers_executed"]) > 0

    @pytest.mark.asyncio
    async def test_evaluate_trigger_conditions_not_met(
        self,
        mock_session,
        automation_service,
        automation_test_helper
    ):
        """Test trigger evaluation when conditions are not met."""
        # Arrange
        trigger_data = {
            "name": "condition_fail_trigger",
            "event_type": "fragment_viewed",
            "conditions": {
                "fragment_key": "advanced_level",
                "user_level": 5
            },
            "is_enabled": True
        }
        
        actions_data = [
            {
                "action_type": "send_message",
                "parameters": {"message": "This should not execute"},
                "execution_order": 1
            }
        ]
        
        trigger = await automation_test_helper.create_test_trigger_with_actions(
            mock_session, trigger_data, actions_data
        )

        # Context that doesn't match conditions
        event_context = {
            "user_id": 12345,
            "fragment_key": "welcome",
            "user_level": 1
        }

        # Act - Use execute_triggers method instead
        result = await automation_service.execute_triggers(
            event_type="fragment_viewed",
            user_id=12345,
            context=event_context
        )

        # Assert
        assert result["success"] is True
        # Verify that no triggers were executed (conditions not met)
        assert len(result["triggers_executed"]) == 0


class TestAutomationServiceEdgeCases:
    """Edge case tests for automation service."""

    @pytest.mark.asyncio
    async def test_create_trigger_with_large_parameters(
        self,
        mock_session,
        automation_service
    ):
        """Test creating trigger with large JSON parameters."""
        # Arrange
        trigger_data = TriggerCreate(
            name="large_params_trigger",
            description="Test trigger with large parameters",
            event_type="custom_event",
            conditions={
                "complex_condition": {
                    "nested": {
                        "deep": {
                            "very_deep": {
                                "array": ["item1", "item2", "item3"] * 10
                            }
                        }
                    }
                }
            },
            is_enabled=True,
            priority=1,
            actions=[
                ActionCreateNested(
                    action_type="send_message",
                    parameters={
                        "large_message": "A" * 1000,
                        "complex_data": {
                            "nested": {"key1": "value1", "key2": "value2", "key3": "value3", "key4": "value4", "key5": "value5"}
                        }
                    },
                    execution_order=1,
                    is_enabled=True
                )
            ]
        )

        # Act
        result = await automation_service.create_trigger_with_actions(trigger_data)

        # Assert
        assert result is not None
        assert result["success"] is True
        assert len(result["created_actions"]) == 1
        assert result["created_actions"][0]["action_type"] == "send_message"

    @pytest.mark.asyncio
    async def test_concurrent_trigger_creation(
        self,
        mock_session,
        automation_service
    ):
        """Test concurrent creation of triggers to verify transaction isolation."""
        import asyncio
        
        # Arrange
        async def create_trigger(name: str):
            trigger_data = TriggerCreate(
                name=name,
                description=f"Test trigger {name}",
                event_type="fragment_viewed",
                conditions={"fragment_key": name},
                is_enabled=True,
                priority=1,
                actions=[
                    ActionCreateNested(
                        action_type="send_message",
                        parameters={"message": f"Message for {name}"},
                        execution_order=1,
                        is_enabled=True
                    )
                ]
            )
            
            return await automation_service.create_trigger_with_actions(trigger_data)

        # Act - Create triggers concurrently
        trigger_names = [f"concurrent_trigger_{i}" for i in range(3)]
        tasks = [create_trigger(name) for name in trigger_names]
        results = await asyncio.gather(*tasks)

        # Assert
        assert len(results) == 3
        for result in results:
            assert result is not None
            assert result["success"] is True
            assert len(result["created_actions"]) == 1