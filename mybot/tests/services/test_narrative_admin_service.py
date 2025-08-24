import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.narrative_unified import NarrativeFragment, UserNarrativeState
from services.narrative_admin_service import NarrativeAdminService


@pytest.fixture
def mock_session():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def narrative_admin_service(mock_session):
    return NarrativeAdminService(mock_session)


@pytest.mark.asyncio
async def test_get_all_fragments(narrative_admin_service, mock_session):
    """Test getting all fragments with pagination and filtering."""
    # Setup mock fragments
    mock_fragment1 = Mock(spec=NarrativeFragment)
    mock_fragment1.id = "frag1"
    mock_fragment1.title = "Fragment 1"
    mock_fragment1.fragment_type = "STORY"
    mock_fragment1.created_at = None
    mock_fragment1.updated_at = None
    mock_fragment1.is_active = True
    mock_fragment1.choices = []
    mock_fragment1.triggers = {}
    mock_fragment1.required_clues = []

    mock_fragment2 = Mock(spec=NarrativeFragment)
    mock_fragment2.id = "frag2"
    mock_fragment2.title = "Fragment 2"
    mock_fragment2.fragment_type = "DECISION"
    mock_fragment2.created_at = None
    mock_fragment2.updated_at = None
    mock_fragment2.is_active = True
    mock_fragment2.choices = ["choice1"]
    mock_fragment2.triggers = {}
    mock_fragment2.required_clues = []

    # Mock session execute
    mock_result = AsyncMock()
    mock_result.scalars().all.return_value = [mock_fragment1, mock_fragment2]
    mock_session.execute.return_value = mock_result

    # Mock count query
    mock_count_result = AsyncMock()
    mock_count_result.scalar.return_value = 2
    mock_session.execute.side_effect = [mock_count_result, mock_result]

    # Call the method
    result = await narrative_admin_service.get_all_fragments(page=1, limit=10, filter_type="STORY")

    # Verify results
    assert result["total"] == 2
    assert len(result["items"]) == 2
    assert result["items"][0]["id"] == "frag1"
    assert result["items"][0]["type"] == "STORY"
    assert result["items"][1]["id"] == "frag2"
    assert result["items"][1]["type"] == "DECISION"


@pytest.mark.asyncio
async def test_get_fragment_details(narrative_admin_service, mock_session):
    """Test getting fragment details with statistics."""
    # Setup mock fragment
    mock_fragment = Mock(spec=NarrativeFragment)
    mock_fragment.id = "frag1"
    mock_fragment.title = "Fragment 1"
    mock_fragment.content = "Content of fragment 1"
    mock_fragment.fragment_type = "STORY"
    mock_fragment.created_at = None
    mock_fragment.updated_at = None
    mock_fragment.is_active = True
    mock_fragment.choices = []
    mock_fragment.triggers = {"points": 10}
    mock_fragment.required_clues = ["clue1"]

    # Mock session execute for fragment
    mock_fragment_result = AsyncMock()
    mock_fragment_result.scalar_one_or_none.return_value = mock_fragment
    mock_session.execute.return_value = mock_fragment_result

    # Mock user statistics queries
    mock_active_users_result = AsyncMock()
    mock_active_users_result.scalar.return_value = 5
    mock_visited_users_result = AsyncMock()
    mock_visited_users_result.scalar.return_value = 10
    mock_completed_users_result = AsyncMock()
    mock_completed_users_result.scalar.return_value = 3

    # Setup side effects for multiple queries
    mock_session.execute.side_effect = [
        mock_fragment_result,
        mock_active_users_result,
        mock_visited_users_result,
        mock_completed_users_result
    ]

    # Call the method
    result = await narrative_admin_service.get_fragment_details("frag1")

    # Verify results
    assert result["id"] == "frag1"
    assert result["title"] == "Fragment 1"
    assert result["content"] == "Content of fragment 1"
    assert result["type"] == "STORY"
    assert result["triggers"]["points"] == 10
    assert result["required_clues"] == ["clue1"]
    assert result["statistics"]["active_users"] == 5
    assert result["statistics"]["visited_users"] == 10
    assert result["statistics"]["completed_users"] == 3


@pytest.mark.asyncio
async def test_create_fragment(narrative_admin_service, mock_session):
    """Test creating a new fragment."""
    # Setup fragment data
    fragment_data = {
        "title": "New Fragment",
        "content": "Content of new fragment",
        "fragment_type": "STORY",
        "is_active": True,
        "choices": [],
        "triggers": {},
        "required_clues": []
    }

    # Mock the created fragment
    mock_fragment = Mock(spec=NarrativeFragment)
    mock_fragment.id = "newfrag"
    mock_fragment.title = "New Fragment"
    mock_fragment.content = "Content of new fragment"
    mock_fragment.fragment_type = "STORY"
    mock_fragment.created_at = None
    mock_fragment.updated_at = None
    mock_fragment.is_active = True
    mock_fragment.choices = []
    mock_fragment.triggers = {}
    mock_fragment.required_clues = []

    # Mock session refresh
    mock_session.refresh = AsyncMock()

    # Call the method
    result = await narrative_admin_service.create_fragment(fragment_data)

    # Verify fragment was added
    assert mock_session.add.called
    assert mock_session.commit.called
    assert result["title"] == "New Fragment"
    assert result["type"] == "STORY"


@pytest.mark.asyncio
async def test_update_fragment(narrative_admin_service, mock_session):
    """Test updating an existing fragment."""
    # Setup mock fragment
    mock_fragment = Mock(spec=NarrativeFragment)
    mock_fragment.id = "frag1"
    mock_fragment.title = "Old Title"
    mock_fragment.content = "Old content"
    mock_fragment.fragment_type = "STORY"
    mock_fragment.created_at = None
    mock_fragment.updated_at = None
    mock_fragment.is_active = True
    mock_fragment.choices = []
    mock_fragment.triggers = {}
    mock_fragment.required_clues = []

    # Mock session execute for getting fragment
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = mock_fragment
    mock_session.execute.return_value = mock_result

    # Setup update data
    update_data = {
        "title": "Updated Title",
        "content": "Updated content"
    }

    # Mock session refresh
    mock_session.refresh = AsyncMock()

    # Call the method
    result = await narrative_admin_service.update_fragment("frag1", update_data)

    # Verify fragment was updated
    assert mock_session.commit.called
    assert mock_fragment.title == "Updated Title"
    assert mock_fragment.content == "Updated content"
    assert result["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_delete_fragment(narrative_admin_service, mock_session):
    """Test deleting (marking inactive) a fragment."""
    # Setup mock fragment
    mock_fragment = Mock(spec=NarrativeFragment)
    mock_fragment.id = "frag1"
    mock_fragment.is_active = True

    # Mock session execute for getting fragment
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = mock_fragment
    mock_session.execute.return_value = mock_result

    # Call the method
    result = await narrative_admin_service.delete_fragment("frag1")

    # Verify fragment was marked as inactive
    assert mock_session.commit.called
    assert mock_fragment.is_active is False
    assert result is True


@pytest.mark.asyncio
async def test_get_fragment_connections(narrative_admin_service, mock_session):
    """Test getting fragment connections."""
    # Setup mock fragment
    mock_fragment = Mock(spec=NarrativeFragment)
    mock_fragment.id = "frag1"
    mock_fragment.title = "Fragment 1"
    mock_fragment.fragment_type = "DECISION"
    mock_fragment.choices = [
        {"text": "Choice 1", "next_fragment": "frag2"},
        {"text": "Choice 2", "next_fragment": "frag3"}
    ]

    # Setup mock target fragments
    mock_target1 = Mock(spec=NarrativeFragment)
    mock_target1.id = "frag2"
    mock_target1.title = "Fragment 2"
    mock_target1.fragment_type = "STORY"
    mock_target1.is_active = True

    mock_target2 = Mock(spec=NarrativeFragment)
    mock_target2.id = "frag3"
    mock_target2.title = "Fragment 3"
    mock_target2.fragment_type = "INFO"
    mock_target2.is_active = True

    # Setup mock incoming fragment
    mock_incoming = Mock(spec=NarrativeFragment)
    mock_incoming.id = "frag0"
    mock_incoming.title = "Fragment 0"
    mock_incoming.fragment_type = "STORY"
    mock_incoming.is_active = True
    mock_incoming.choices = [
        {"text": "Previous choice", "next_fragment": "frag1"}
    ]

    # Mock queries
    mock_fragment_result = AsyncMock()
    mock_fragment_result.scalar_one_or_none.return_value = mock_fragment

    mock_target1_result = AsyncMock()
    mock_target1_result.scalar_one_or_none.return_value = mock_target1

    mock_target2_result = AsyncMock()
    mock_target2_result.scalar_one_or_none.return_value = mock_target2

    mock_all_fragments_result = AsyncMock()
    mock_all_fragments_result.scalars().all.return_value = [mock_incoming]

    # Setup side effects for multiple queries
    mock_session.execute.side_effect = [
        mock_fragment_result,
        mock_target1_result,
        mock_target2_result,
        mock_all_fragments_result
    ]

    # Call the method
    result = await narrative_admin_service.get_fragment_connections("frag1")

    # Verify results
    assert result["fragment_id"] == "frag1"
    assert len(result["outgoing_connections"]) == 2
    assert len(result["incoming_connections"]) == 1
    assert result["outgoing_connections"][0]["id"] == "frag2"
    assert result["outgoing_connections"][1]["id"] == "frag3"
    assert result["incoming_connections"][0]["id"] == "frag0"


@pytest.mark.asyncio
async def test_get_narrative_stats(narrative_admin_service, mock_session):
    """Test getting narrative statistics."""
    # Mock statistics queries
    mock_total_result = AsyncMock()
    mock_total_result.scalar.return_value = 10

    mock_by_type_result = AsyncMock()
    mock_by_type_result.all.return_value = [("STORY", 5), ("DECISION", 3), ("INFO", 2)]

    mock_active_result = AsyncMock()
    mock_active_result.scalar.return_value = 8

    mock_connections_result = AsyncMock()
    mock_connections_result.scalar.return_value = 6

    mock_users_result = AsyncMock()
    mock_users_result.scalar.return_value = 50

    mock_completion_result = AsyncMock()
    mock_completion_result.scalar.return_value = 3.5

    # Setup side effects for multiple queries
    mock_session.execute.side_effect = [
        mock_total_result,
        mock_by_type_result,
        mock_active_result,
        mock_connections_result,
        mock_users_result,
        mock_completion_result
    ]

    # Call the method
    result = await narrative_admin_service.get_narrative_stats()

    # Verify results
    assert result["total_fragments"] == 10
    assert result["active_fragments"] == 8
    assert result["inactive_fragments"] == 2
    assert result["fragments_by_type"]["STORY"] == 5
    assert result["fragments_by_type"]["DECISION"] == 3
    assert result["fragments_by_type"]["INFO"] == 2
    assert result["fragments_with_connections"] == 6
    assert result["users_in_narrative"] == 50
    assert result["avg_fragments_completed"] == 3.5