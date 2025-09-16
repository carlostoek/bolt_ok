"""
Pytest configuration for integration tests.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_session():
    """Mock database session for integration tests."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.get = AsyncMock()
    session.add = AsyncMock()
    return session

@pytest.fixture
def test_user_data():
    """Test user data for integration tests."""
    return {
        "user_id": 12345,
        "username": "test_user",
        "current_fragment": "TEST_START",
        "archetype": "explorer_deep"
    }

@pytest.fixture
def test_narrative_fragments():
    """Test narrative fragments for integration tests."""
    return {
        "TEST_START": {
            "key": "TEST_START",
            "text": "Welcome to the test narrative journey",
            "character": "Lucien",
            "choices": [
                {"text": "Begin exploration", "destination": "EXPLORE_PATH"},
                {"text": "Seek answers directly", "destination": "DIRECT_PATH"}
            ]
        },
        "EXPLORE_PATH": {
            "key": "EXPLORE_PATH",
            "text": "You chose to explore...",
            "character": "Diana",
            "required_item": "EXPLORER_KEY",
            "choices": [{"text": "Continue exploring", "destination": "DEEPER_EXPLORE"}]
        },
        "DIRECT_PATH": {
            "key": "DIRECT_PATH", 
            "text": "You seek direct answers...",
            "character": "Lucien",
            "choices": [{"text": "Ask more questions", "destination": "DEEPER_QUESTIONS"}]
        }
    }

@pytest.fixture
def test_shop_items():
    """Test shop items for integration tests."""
    return {
        "EXPLORER_KEY": {
            "id": 1,
            "name": "Explorer's Key",
            "code_name": "EXPLORER_KEY",
            "price": 150,
            "description": "Unlocks exploratory narrative paths"
        },
        "DIRECT_ACCESS": {
            "id": 2,
            "name": "Direct Access Pass",
            "code_name": "DIRECT_ACCESS", 
            "price": 100,
            "description": "Grants direct access to answers"
        }
    }
