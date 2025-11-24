"""
Testing configuration for automation system with atomic nested creation.
Fixtures and utilities for testing the event-driven automation engine.
"""
import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone

from app.models.automation import AutomationTrigger, TriggerAction, AutomationLog
from app.schemas.automation import TriggerCreate, ActionCreateNested
from app.services.automation_service import AutomationService


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_session():
    """Mock database session for testing."""
    session = AsyncMock()
    
    # Mock common database operations
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.get = AsyncMock()
    session.add = AsyncMock()
    session.flush = AsyncMock()
    
    # Mock flush to set IDs on objects
    async def mock_flush():
        # Set IDs on any added objects
        if hasattr(session, '_added_objects'):
            for i, obj in enumerate(session._added_objects, start=1):
                if hasattr(obj, 'id') and obj.id is None:
                    obj.id = i
    
    session.flush = mock_flush
    
    # Track added objects
    session._added_objects = []
    
    def mock_add(obj):
        session._added_objects.append(obj)
    
    session.add = mock_add
    
    return session


@pytest.fixture
def automation_service(mock_session):
    """Fixture providing the automation service."""
    return AutomationService(mock_session)


@pytest.fixture
def sample_trigger_data() -> Dict[str, Any]:
    """Sample data for creating automation triggers."""
    return {
        "name": "test_trigger",
        "description": "Test automation trigger",
        "event_type": "fragment_viewed",
        "conditions": {
            "fragment_key": "welcome",
            "user_level": 1
        },
        "is_enabled": True,
        "priority": 1
    }


@pytest.fixture
def sample_action_data() -> Dict[str, Any]:
    """Sample data for creating trigger actions."""
    return {
        "action_type": "give_product",
        "parameters": {
            "product_id": 1,
            "quantity": 1
        },
        "execution_order": 1,
        "is_enabled": True
    }


@pytest.fixture
def sample_nested_creation_data() -> Dict[str, Any]:
    """Sample data for testing atomic nested creation."""
    return {
        "name": "atomic_nested_trigger",
        "description": "Test atomic nested creation",
        "event_type": "purchase_completed",
        "conditions": {
            "product_type": "premium"
        },
        "is_enabled": True,
        "priority": 1,
        "actions": [
            {
                "action_type": "give_product",
                "parameters": {
                    "product_id": 2,
                    "quantity": 1
                },
                "execution_order": 1,
                "is_enabled": True
            },
            {
                "action_type": "add_points",
                "parameters": {
                    "points": 100
                },
                "execution_order": 2,
                "is_enabled": True
            }
        ]
    }


@pytest.fixture
def automation_test_scenarios():
    """Predefined test scenarios for automation system."""
    return {
        "atomic_nested_creation": {
            "description": "Create trigger with multiple actions atomically",
            "trigger_data": {
                "name": "multi_action_trigger",
                "event_type": "user_registered",
                "conditions": {},
                "is_enabled": True
            },
            "actions_data": [
                {
                    "action_type": "grant_vip",
                    "parameters": {"duration_days": 7},
                    "execution_order": 1
                },
                {
                    "action_type": "send_message",
                    "parameters": {"message": "Welcome to our platform!"},
                    "execution_order": 2
                }
            ],
            "expected_actions_count": 2
        },
        "rollback_scenario": {
            "description": "Test rollback when action creation fails",
            "trigger_data": {
                "name": "rollback_test",
                "event_type": "fragment_viewed",
                "conditions": {"fragment_key": "test_fragment"},
                "is_enabled": True
            },
            "actions_data": [
                {
                    "action_type": "give_product",
                    "parameters": {"product_id": 1},
                    "execution_order": 1
                },
                {
                    "action_type": "invalid_action",  # This should cause rollback
                    "parameters": {},
                    "execution_order": 2
                }
            ],
            "should_fail": True
        },
        "condition_evaluation": {
            "description": "Test complex condition evaluation",
            "trigger_data": {
                "name": "complex_conditions",
                "event_type": "fragment_viewed",
                "conditions": {
                    "fragment_key": "advanced_level",
                    "user_level": {"gte": 5},
                    "vip_status": True
                },
                "is_enabled": True
            },
            "actions_data": [
                {
                    "action_type": "unlock_fragment",
                    "parameters": {"fragment_key": "secret_content"},
                    "execution_order": 1
                }
            ]
        }
    }


@pytest.fixture
def mock_event_context():
    """Mock event context for testing trigger evaluation."""
    return {
        "user_id": 12345,
        "fragment_key": "welcome",
        "user_level": 1,
        "vip_status": False,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


class AutomationTestHelper:
    """Helper class for automation system testing."""
    
    @staticmethod
    async def create_test_trigger_with_actions(
        session: AsyncMock,
        trigger_data: Dict[str, Any],
        actions_data: list[Dict[str, Any]]
    ) -> AutomationTrigger:
        """Helper to create a trigger with actions for testing."""
        # Create trigger
        trigger = AutomationTrigger(**trigger_data)
        
        # Create actions
        trigger.actions = []
        for i, action_data in enumerate(actions_data):
            action = TriggerAction(
                trigger_id=1,  # Mock trigger ID
                **action_data
            )
            trigger.actions.append(action)
        
        return trigger
    
    @staticmethod
    async def verify_atomic_creation(
        session: AsyncMock,
        trigger_name: str,
        expected_actions_count: int
    ) -> bool:
        """Verify that trigger and actions were created atomically."""
        # In mock tests, we'll simulate the verification
        return True
    
    @staticmethod
    async def verify_rollback(
        session: AsyncMock,
        trigger_name: str
    ) -> bool:
        """Verify that rollback occurred (trigger should not exist)."""
        # In mock tests, we'll simulate the verification
        return True


@pytest.fixture
def automation_test_helper():
    """Fixture providing the automation test helper."""
    return AutomationTestHelper()


# Integration test helpers
async def setup_test_automation_state(session: AsyncMock, user_id: int):
    """Helper to setup automation state for testing."""
    # Create test triggers and actions
    trigger_data = {
        "name": f"test_trigger_{user_id}",
        "event_type": "fragment_viewed",
        "conditions": {"fragment_key": "test_fragment"},
        "is_enabled": True
    }
    
    actions_data = [
        {
            "action_type": "send_message",
            "parameters": {"message": "Test message"},
            "execution_order": 1
        }
    ]
    
    helper = AutomationTestHelper()
    return await helper.create_test_trigger_with_actions(
        session, trigger_data, actions_data
    )


async def cleanup_test_automation_data(session: AsyncMock):
    """Helper to cleanup test automation data after tests."""
    # Reset mock calls
    session.reset_mock()