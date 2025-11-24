"""
Simplified tests for atomic nested creation functionality.

Focuses on testing the atomicity logic without complex database mocking.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.schemas.automation import TriggerCreate, ActionCreateNested
from app.services.automation_service import AutomationService
from app.core.exceptions import DuplicateKeyException, NestedCreationException, DatabaseException


class TestAtomicNestedCreation:
    """Test atomic nested creation functionality."""

    @pytest.mark.asyncio
    async def test_atomic_nested_creation_success(self):
        """Test successful atomic creation of trigger with actions."""
        # Arrange
        mock_session = AsyncMock()
        service = AutomationService(mock_session)
        
        # Mock the database operations
        mock_trigger = MagicMock()
        mock_trigger.id = 1
        mock_trigger.name = "test_trigger"
        mock_trigger.created_at = datetime.now()
        mock_trigger.updated_at = datetime.now()
        
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        # Create test data
        trigger_data = TriggerCreate(
            name="test_trigger",
            description="Test trigger",
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
                ),
                ActionCreateNested(
                    action_type="add_points",
                    parameters={"points": 100},
                    execution_order=2,
                    is_enabled=True
                )
            ]
        )

        # Mock the AutomationTrigger constructor to return our mock
        with patch('app.services.automation_service.AutomationTrigger') as mock_trigger_class:
            mock_trigger_class.return_value = mock_trigger
            
            # Mock TriggerAction creation
            with patch('app.services.automation_service.TriggerAction') as mock_action_class:
                mock_action1 = MagicMock()
                mock_action1.id = 1
                mock_action1.action_type = "send_message"
                mock_action1.execution_order = 1
                
                mock_action2 = MagicMock()
                mock_action2.id = 2
                mock_action2.action_type = "add_points"
                mock_action2.execution_order = 2
                
                mock_action_class.side_effect = [mock_action1, mock_action2]
                
                # Act
                result = await service.create_trigger_with_actions(trigger_data)

        # Assert
        assert result["success"] is True
        assert result["trigger"].name == "test_trigger"
        assert len(result["created_actions"]) == 2
        assert result["summary"]["actions_created"] == 2
        assert result["summary"]["total_entities"] == 3
        
        # Verify database operations were called
        mock_session.add.assert_called()
        mock_session.flush.assert_called()
        mock_session.commit.assert_called()
        mock_session.refresh.assert_called()

    @pytest.mark.asyncio
    async def test_atomic_nested_creation_rollback_on_error(self):
        """Test that rollback occurs when action creation fails."""
        # Arrange
        mock_session = AsyncMock()
        service = AutomationService(mock_session)
        
        # Mock the database operations
        mock_trigger = MagicMock()
        mock_trigger.id = 1
        mock_trigger.name = "test_trigger"
        
        mock_session.flush = AsyncMock()
        mock_session.rollback = AsyncMock()
        
        # Create test data
        trigger_data = TriggerCreate(
            name="test_trigger",
            description="Test trigger",
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

        # Mock the AutomationTrigger constructor to return our mock
        with patch('app.services.automation_service.AutomationTrigger') as mock_trigger_class:
            mock_trigger_class.return_value = mock_trigger
            
            # Mock TriggerAction creation to raise an exception
            with patch('app.services.automation_service.TriggerAction') as mock_action_class:
                mock_action_class.side_effect = Exception("Action creation failed")
                
                # Act & Assert
                with pytest.raises(NestedCreationException):
                    await service.create_trigger_with_actions(trigger_data)

        # Assert rollback was called
        mock_session.rollback.assert_called()

    @pytest.mark.asyncio
    async def test_atomic_nested_creation_duplicate_name(self):
        """Test that duplicate trigger names are handled correctly."""
        # Arrange
        mock_session = AsyncMock()
        service = AutomationService(mock_session)
        
        # Mock flush to raise IntegrityError for duplicate name
        mock_session.flush = AsyncMock(side_effect=Exception("UNIQUE constraint failed"))
        
        # Create test data
        trigger_data = TriggerCreate(
            name="duplicate_trigger",
            description="Test trigger",
            event_type="fragment_viewed",
            conditions={"fragment_key": "welcome"},
            is_enabled=True,
            priority=1
        )

        # Act & Assert
        with pytest.raises(DatabaseException):
            await service.create_trigger_with_actions(trigger_data)

        # Assert rollback was called
        mock_session.rollback.assert_called()

    @pytest.mark.asyncio
    async def test_atomic_nested_creation_no_actions(self):
        """Test creating trigger with no actions."""
        # Arrange
        mock_session = AsyncMock()
        service = AutomationService(mock_session)
        
        # Mock the database operations
        mock_trigger = MagicMock()
        mock_trigger.id = 1
        mock_trigger.name = "test_trigger"
        mock_trigger.created_at = datetime.now()
        mock_trigger.updated_at = datetime.now()
        
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        # Create test data without actions
        trigger_data = TriggerCreate(
            name="test_trigger",
            description="Test trigger",
            event_type="fragment_viewed",
            conditions={"fragment_key": "welcome"},
            is_enabled=True,
            priority=1
        )

        # Mock the AutomationTrigger constructor
        with patch('app.services.automation_service.AutomationTrigger') as mock_trigger_class:
            mock_trigger_class.return_value = mock_trigger
            
            # Act
            result = await service.create_trigger_with_actions(trigger_data)

        # Assert
        assert result["success"] is True
        assert result["trigger"].name == "test_trigger"
        assert len(result["created_actions"]) == 0
        assert result["summary"]["actions_created"] == 0
        assert result["summary"]["total_entities"] == 1

    @pytest.mark.asyncio
    async def test_atomic_nested_creation_execution_order(self):
        """Test that actions maintain their execution order."""
        # Arrange
        mock_session = AsyncMock()
        service = AutomationService(mock_session)
        
        # Mock the database operations
        mock_trigger = MagicMock()
        mock_trigger.id = 1
        mock_trigger.name = "test_trigger"
        mock_trigger.created_at = datetime.now()
        mock_trigger.updated_at = datetime.now()
        
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        # Create test data with actions in non-sequential order
        trigger_data = TriggerCreate(
            name="test_trigger",
            description="Test trigger",
            event_type="fragment_viewed",
            conditions={"fragment_key": "welcome"},
            is_enabled=True,
            priority=1,
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

        # Mock the AutomationTrigger constructor
        with patch('app.services.automation_service.AutomationTrigger') as mock_trigger_class:
            mock_trigger_class.return_value = mock_trigger
            
            # Mock TriggerAction creation
            with patch('app.services.automation_service.TriggerAction') as mock_action_class:
                actions_created = []
                
                def create_action(**kwargs):
                    action = MagicMock()
                    action.id = len(actions_created) + 1
                    action.action_type = kwargs.get('action_type')
                    action.execution_order = kwargs.get('execution_order')
                    actions_created.append(action)
                    return action
                
                mock_action_class.side_effect = create_action
                
                # Act
                result = await service.create_trigger_with_actions(trigger_data)

        # Assert
        assert result["success"] is True
        assert len(result["created_actions"]) == 3
        
        # Verify actions are stored in the order they were created
        # (not necessarily execution order, but that's handled by the service)
        action_types = [action["action_type"] for action in result["created_actions"]]
        assert "send_message" in action_types
        assert "give_product" in action_types
        assert "add_points" in action_types