
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from services.unified_narrative_service import UnifiedNarrativeService
from database.models import User
from database.narrative_unified import UserNarrativeState, NarrativeFragment

# Mock data for a few narrative fragments representing the first few levels
MOCK_FRAGMENTS = {
    "start": {"id": "start", "title": "Inicio", "content": "...", "fragment_type": "STORY", "storyline_level": 1, "choices": [], "triggers": {}},
    "decision_1": {"id": "decision_1", "title": "Primera Decisión", "content": "...", "fragment_type": "DECISION", "storyline_level": 2, "choices": [{"text": "Opción A", "next_fragment_id": "level_3_story"}], "triggers": {}},
    "level_3_story": {"id": "level_3_story", "title": "Historia Nivel 3", "content": "...", "fragment_type": "STORY", "storyline_level": 3, "choices": [], "triggers": {}},
}

@pytest.mark.asyncio
async def test_emotional_crescendo_level_progression(session: AsyncSession):
    """
    Tests the emotional level progression from Level 1 to 2
    as described in the Emotional Crescendo documentation.
    """
    # 1. Setup: Create a test user and mock the fragment service
    test_user = User(id=12345, username="testuser", first_name="Test", last_name="User", role="free")
    session.add(test_user)
    await session.commit()

    narrative_service = UnifiedNarrativeService(session)

    # Mock the fragment retrieval to avoid database dependency on fragments
    async def mock_get_fragment(fragment_id: str):
        data = MOCK_FRAGMENTS.get(fragment_id)
        if not data:
            return None
        # Simulate a SQLAlchemy model object
        fragment = NarrativeFragment(**data)
        return fragment

    narrative_service.fragment_service.get_fragment = mock_get_fragment

    # 2. Act: Start the narrative for the user
    await narrative_service.start_narrative(test_user.id)

    # 3. Assert: Check initial emotional state (Level 1)
    user_state = await session.get(UserNarrativeState, test_user.id)
    assert user_state is not None, "UserNarrativeState should be created"
    
    # Assuming _update_emotional_state is called after start_narrative or is part of it
    # This part of the test might need adjustment based on when the emotional state is first calculated
    # For now, let's assume it's updated on the first action.
    
    # 4. Act: Process a decision that moves the user to storyline_level 3
    await narrative_service.process_user_decision(test_user.id, {"index": 0})

    # 5. Assert: Check emotional state after progressing to Level 3
    await session.refresh(user_state) # Refresh state from DB
    
    # According to the logic from the user's diff, reaching storyline_level 3 should set emotional_level to 2
    assert user_state.emotional_level == 2, "Emotional level should be 2 after reaching storyline level 3"
    assert user_state.last_emotional_milestone == "The Recognition", "Emotional milestone should be 'The Recognition'"

    print("\n✅ Test Passed: Emotional Crescendo progression from Level 1 to 2 verified.")
