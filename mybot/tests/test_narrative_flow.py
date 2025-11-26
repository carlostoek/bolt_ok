# tests/test_narrative_flow.py
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.narrative_service import NarrativeService
from database.models import User
from database.narrative_models import UserNarrativeState, StoryFragment

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio

async def setup_initial_fragment(db_session):
    """Helper to create the starting fragment."""
    initial_fragment = StoryFragment(
        key="START",
        text="Welcome to the story!",
        character="Narrator",
    )
    db_session.add(initial_fragment)
    await db_session.commit()
    return initial_fragment

@pytest_asyncio.fixture
async def seeded_db_session(db_session: AsyncSession):
    """Seed the database with initial data for narrative tests."""
    await setup_initial_fragment(db_session)
    
    # Create a user
    user = User(id=12345, username="testuser", points=100)
    db_session.add(user)
    await db_session.commit()
    
    return db_session

async def test_start_story_new_user(seeded_db_session: AsyncSession, mock_message):
    """
    Test case for a new user starting the narrative.
    - GIVEN a new user.
    - WHEN the user sends the /historia command.
    - THEN the user should receive the first narrative fragment.
    - AND a new UserNarrativeState should be created for the user.
    """
    from handlers.narrative_handler import start_narrative_command

    # Call the handler
    await start_narrative_command(mock_message, db=seeded_db_session)

    # ASSERT
    # 1. Check that a message was sent back (and it contains the welcome text)
    mock_message.answer.assert_called_once()
    args, kwargs = mock_message.answer.call_args
    assert "Welcome to the story!" in args[0]

    # 2. Verify user state in the database
    service = NarrativeService(seeded_db_session)
    user_state = await service.get_user_narrative_state(12345)
    
    assert user_state is not None
    assert user_state.current_fragment_key == "START"
    assert user_state.user_id == 12345
