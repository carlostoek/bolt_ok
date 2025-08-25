import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from database.narrative_unified import NarrativeFragment
from services.narrative_fragment_service import NarrativeFragmentService

# Test data
TEST_STORY_FRAGMENT = {
    "title": "Introducción al Misterio",
    "content": "En una noche oscura, un misterio inquietante esperaba ser resuelto.",
    "fragment_type": "STORY",
    "choices": [],
    "triggers": {},
    "required_clues": []
}

TEST_DECISION_FRAGMENT = {
    "title": "Cruce en el Bosque",
    "content": "Llegas a un cruce en el bosque. ¿Qué camino tomas?",
    "fragment_type": "DECISION",
    "choices": [
        {"text": "Camino de la izquierda", "next_fragment_id": "fragment-2"},
        {"text": "Camino de la derecha", "next_fragment_id": "fragment-3"}
    ],
    "triggers": {"reward_points": 5},
    "required_clues": ["pista-bosque"]
}

TEST_INFO_FRAGMENT = {
    "title": "Historia del Castillo",
    "content": "El castillo fue construido en el siglo XV por el rey Alonso.",
    "fragment_type": "INFO",
    "choices": [],
    "triggers": {"unlock_lore": "historia-castillo"},
    "required_clues": []
}


@pytest.mark.asyncio
async def test_create_fragment(session: AsyncSession):
    """Test creating a narrative fragment."""
    service = NarrativeFragmentService(session)
    
    # Test creating a story fragment
    fragment = await service.create_fragment(**TEST_STORY_FRAGMENT)
    
    assert fragment.title == TEST_STORY_FRAGMENT["title"]
    assert fragment.content == TEST_STORY_FRAGMENT["content"]
    assert fragment.fragment_type == TEST_STORY_FRAGMENT["fragment_type"]
    assert fragment.is_active is True
    assert fragment.id is not None


@pytest.mark.asyncio
async def test_get_fragment(session: AsyncSession):
    """Test retrieving a narrative fragment."""
    service = NarrativeFragmentService(session)
    
    # Create a fragment first
    created_fragment = await service.create_fragment(**TEST_DECISION_FRAGMENT)
    
    # Retrieve the fragment
    retrieved_fragment = await service.get_fragment(created_fragment.id)
    
    assert retrieved_fragment is not None
    assert retrieved_fragment.id == created_fragment.id
    assert retrieved_fragment.title == TEST_DECISION_FRAGMENT["title"]


@pytest.mark.asyncio
async def test_get_fragments_by_type(session: AsyncSession):
    """Test retrieving fragments by type."""
    service = NarrativeFragmentService(session)
    
    # Create fragments of different types
    await service.create_fragment(**TEST_STORY_FRAGMENT)
    await service.create_fragment(**TEST_DECISION_FRAGMENT)
    await service.create_fragment(**TEST_INFO_FRAGMENT)
    
    # Get story fragments
    story_fragments = await service.get_story_fragments()
    assert len(story_fragments) >= 1
    
    # Get decision fragments
    decision_fragments = await service.get_decision_fragments()
    assert len(decision_fragments) >= 1
    
    # Get info fragments
    info_fragments = await service.get_info_fragments()
    assert len(info_fragments) >= 1


@pytest.mark.asyncio
async def test_update_fragment(session: AsyncSession):
    """Test updating a narrative fragment."""
    service = NarrativeFragmentService(session)
    
    # Create a fragment
    fragment = await service.create_fragment(**TEST_STORY_FRAGMENT)
    
    # Update the fragment
    updated_fragment = await service.update_fragment(
        fragment_id=fragment.id,
        title="Introducción Actualizada",
        content="En una noche aún más oscura..."
    )
    
    assert updated_fragment is not None
    assert updated_fragment.title == "Introducción Actualizada"
    assert updated_fragment.content == "En una noche aún más oscura..."


@pytest.mark.asyncio
async def test_delete_fragment(session: AsyncSession):
    """Test deleting a narrative fragment."""
    service = NarrativeFragmentService(session)
    
    # Create a fragment
    fragment = await service.create_fragment(**TEST_INFO_FRAGMENT)
    
    # Delete the fragment (soft delete)
    result = await service.delete_fragment(fragment.id)
    assert result is True
    
    # Try to retrieve the fragment (should not be found as active)
    retrieved_fragment = await service.get_fragment(fragment.id)
    assert retrieved_fragment is None


@pytest.mark.asyncio
async def test_check_user_access(session: AsyncSession):
    """Test checking user access to fragments."""
    service = NarrativeFragmentService(session)
    
    # Create a fragment with required clues
    fragment = await service.create_fragment(**TEST_DECISION_FRAGMENT)
    
    # Test access with required clues
    user_clues = ["pista-bosque", "pista-castillo"]
    has_access = await service.check_user_access(fragment.id, user_clues)
    assert has_access is True
    
    # Test access without required clues
    user_clues = ["pista-castillo"]
    has_access = await service.check_user_access(fragment.id, user_clues)
    assert has_access is False
    
    # Test access with no required clues
    fragment_no_clues = await service.create_fragment(**TEST_STORY_FRAGMENT)
    has_access = await service.check_user_access(fragment_no_clues.id, [])
    assert has_access is True