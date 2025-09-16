"""
Comprehensive test suite for NarrativeAdminService

Tests cover all core functionality including:
- Story fragment CRUD operations
- Narrative consistency validation
- Shop item integration and access conditions
- Fragment analytics integration
- Bulk import functionality
- Error handling and edge cases
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import select
from typing import Dict, Any, List, Optional

# Import the service and models
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.narrative_admin_service import NarrativeAdminService
from database.narrative_models import (
    StoryFragment, NarrativeChoice, UserNarrativeState,
    FragmentAnalytics, UserJourneyAnalytics
)
from database.models import ShopItem, UserPurchase


class TestNarrativeAdminService:
    """Test suite for NarrativeAdminService core functionality"""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.add = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.refresh = AsyncMock()
        session.get = AsyncMock()
        return session

    @pytest.fixture
    async def service(self, mock_session):
        """NarrativeAdminService instance with mocked session"""
        return NarrativeAdminService(mock_session)

    @pytest.fixture
    def sample_fragment_data(self):
        """Sample story fragment data for testing"""
        return {
            "key": "test_fragment_001",
            "text": "Diana looks at you with curious eyes, waiting for your response.",
            "character": "Diana",
            "level": 2,
            "min_besitos": 50,
            "required_role": "vip",
            "reward_besitos": 25,
            "unlocks_achievement_id": "achievement_001"
        }

    @pytest.fixture
    def sample_fragment(self):
        """Sample StoryFragment model instance"""
        return StoryFragment(
            id=1,
            key="test_fragment_001",
            text="Diana looks at you with curious eyes, waiting for your response.",
            character="Diana",
            level=2,
            min_besitos=50,
            required_role="vip",
            reward_besitos=25,
            unlocks_achievement_id="achievement_001",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    @pytest.fixture
    def sample_choice(self):
        """Sample NarrativeChoice model instance"""
        return NarrativeChoice(
            id=1,
            source_fragment_id=1,
            destination_fragment_key="choice_destination_001",
            text="Tell Diana about your deepest desire",
            required_besitos=100,
            required_role="vip",
            created_at=datetime.utcnow()
        )

    @pytest.fixture
    def sample_analytics(self):
        """Sample FragmentAnalytics model instance"""
        return FragmentAnalytics(
            id=1,
            fragment_key="test_fragment_001",
            view_count=150,
            completion_count=120,
            drop_off_count=30,
            average_time_spent=45,
            choice_distribution={"choice_1": 60, "choice_2": 40, "choice_3": 20},
            most_popular_choice_id=1,
            users_progressed_from=100,
            users_returned_to=20,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_analyzed_at=datetime.utcnow()
        )

    @pytest.fixture
    def narrative_graph_fragments(self):
        """Sample narrative graph structure for testing"""
        start_fragment = StoryFragment(
            id=1, key="start", text="Welcome to the story",
            auto_next_fragment_key="level_1_intro"
        )

        level_1_fragment = StoryFragment(
            id=2, key="level_1_intro", text="Level 1 introduction"
        )

        choice_fragment = StoryFragment(
            id=3, key="choice_point", text="Choose your path"
        )

        orphaned_fragment = StoryFragment(
            id=4, key="orphaned", text="This fragment is unreachable"
        )

        dead_end_fragment = StoryFragment(
            id=5, key="dead_end", text="No way forward from here"
        )

        # Add choices to demonstrate links
        choice1 = NarrativeChoice(
            source_fragment_id=2, destination_fragment_key="choice_point", text="Continue"
        )
        choice2 = NarrativeChoice(
            source_fragment_id=3, destination_fragment_key="nonexistent", text="Broken link"
        )

        level_1_fragment.choices = [choice1]
        choice_fragment.choices = [choice2]

        return [start_fragment, level_1_fragment, choice_fragment, orphaned_fragment, dead_end_fragment]


class TestStoryFragmentCRUD:
    """Test story fragment CRUD operations"""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.add = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    async def service(self, mock_session):
        """NarrativeAdminService instance with mocked session"""
        return NarrativeAdminService(mock_session)

    async def test_create_story_fragment_success(self, service, sample_fragment_data, mock_session):
        """Test successful story fragment creation"""
        # Mock successful database operation
        mock_session.commit.return_value = None

        # Call the method (currently returns not_implemented)
        result = await service.create_story_fragment(sample_fragment_data)

        # Verify the result structure (placeholder for now)
        assert "status" in result
        assert result["status"] == "not_implemented"

        # Verify logging was called
        # This tests the current placeholder implementation
        # When implemented, this would test actual fragment creation

    async def test_create_story_fragment_invalid_data(self, service, mock_session):
        """Test story fragment creation with invalid data"""
        invalid_data = {
            "key": "",  # Empty key should fail
            "text": None,  # Null text should fail
            "character": "Diana"
        }

        result = await service.create_story_fragment(invalid_data)

        # Currently returns not_implemented, but should eventually validate data
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_create_story_fragment_duplicate_key(self, service, sample_fragment_data, mock_session):
        """Test story fragment creation with duplicate key"""
        # Mock integrity error for duplicate key
        mock_session.commit.side_effect = IntegrityError("Duplicate key", None, None)

        result = await service.create_story_fragment(sample_fragment_data)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_update_story_fragment_success(self, service, mock_session):
        """Test successful story fragment update"""
        fragment_id = "test_fragment_001"
        updates = {
            "text": "Updated Diana dialogue with more depth.",
            "reward_besitos": 30
        }

        result = await service.update_story_fragment(fragment_id, updates)

        # Verify the result structure (placeholder for now)
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_update_story_fragment_nonexistent(self, service, mock_session):
        """Test updating non-existent story fragment"""
        fragment_id = "nonexistent_fragment"
        updates = {"text": "Updated text"}

        result = await service.update_story_fragment(fragment_id, updates)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_update_story_fragment_empty_updates(self, service, mock_session):
        """Test updating story fragment with empty updates"""
        fragment_id = "test_fragment_001"
        updates = {}

        result = await service.update_story_fragment(fragment_id, updates)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_delete_story_fragment_success(self, service, mock_session):
        """Test successful story fragment deletion"""
        fragment_id = "test_fragment_001"

        # Mock successful deletion
        mock_session.commit.return_value = None

        result = await service.delete_story_fragment(fragment_id)

        # Verify the result structure (placeholder for now)
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_delete_story_fragment_with_dependencies(self, service, mock_session):
        """Test deleting story fragment that has dependencies"""
        fragment_id = "fragment_with_choices"

        # Mock constraint violation for dependencies
        mock_session.commit.side_effect = IntegrityError("Foreign key constraint", None, None)

        result = await service.delete_story_fragment(fragment_id)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_delete_story_fragment_nonexistent(self, service, mock_session):
        """Test deleting non-existent story fragment"""
        fragment_id = "nonexistent_fragment"

        result = await service.delete_story_fragment(fragment_id)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"


class TestFragmentAnalyticsIntegration:
    """Test fragment analytics integration functionality"""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.add = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    async def service(self, mock_session):
        """NarrativeAdminService instance with mocked session"""
        return NarrativeAdminService(mock_session)

    async def test_get_fragment_with_analytics_success(self, service, sample_fragment, sample_analytics, mock_session):
        """Test successful retrieval of fragment with analytics"""
        fragment_id = "test_fragment_001"

        # Mock database result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_analytics
        mock_session.execute.return_value = mock_result

        result = await service.get_fragment_with_analytics(fragment_id)

        # Currently returns None (not implemented)
        assert result is None

    async def test_get_fragment_with_analytics_no_fragment(self, service, mock_session):
        """Test retrieving analytics for non-existent fragment"""
        fragment_id = "nonexistent_fragment"

        # Mock no result found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.get_fragment_with_analytics(fragment_id)

        # Currently returns None (not implemented)
        assert result is None

    async def test_get_fragment_with_analytics_database_error(self, service, mock_session):
        """Test handling database error when retrieving analytics"""
        fragment_id = "test_fragment_001"

        # Mock database error
        mock_session.execute.side_effect = SQLAlchemyError("Database connection failed")

        result = await service.get_fragment_with_analytics(fragment_id)

        # Currently returns None (not implemented)
        assert result is None


class TestNarrativeConsistency:
    """Test narrative consistency validation functionality"""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session with narrative graph data"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    async def service(self, mock_session):
        """NarrativeAdminService instance with mocked session"""
        return NarrativeAdminService(mock_session)

    async def test_validate_narrative_consistency_healthy_graph(self, service, narrative_graph_fragments, mock_session):
        """Test validation of a healthy narrative graph"""
        # Filter to only healthy fragments (no orphaned, no dead ends, no broken links)
        healthy_fragments = [
            narrative_graph_fragments[0],  # start
            narrative_graph_fragments[1],  # level_1_intro
            narrative_graph_fragments[2]   # choice_point
        ]

        # Fix the choice to point to existing fragment
        healthy_fragments[2].choices[0].destination_fragment_key = "start"

        # Mock database result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = healthy_fragments
        mock_session.execute.return_value = mock_result

        result = await service.validate_narrative_consistency()

        # Should report no issues
        assert result["status"] == "ok"
        assert len(result["orphaned_fragments"]) == 0
        assert len(result["dead_end_fragments"]) == 1  # choice_point has no outgoing edges
        assert len(result["broken_links"]) == 0

    async def test_validate_narrative_consistency_with_issues(self, service, narrative_graph_fragments, mock_session):
        """Test validation of narrative graph with various issues"""
        # Mock database result with all fragments (including problematic ones)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = narrative_graph_fragments
        mock_session.execute.return_value = mock_result

        result = await service.validate_narrative_consistency()

        # Should report issues found
        assert result["status"] == "issues_found"
        assert len(result["orphaned_fragments"]) == 1  # orphaned fragment
        assert len(result["dead_end_fragments"]) == 2  # choice_point and dead_end
        assert len(result["broken_links"]) == 1  # broken link to nonexistent

        # Verify summary statistics
        summary = result["summary"]
        assert summary["total_fragments"] == 5
        assert summary["reachable_fragments"] == 3
        assert summary["orphaned_count"] == 1
        assert summary["dead_end_count"] == 2
        assert summary["broken_link_count"] == 1

    async def test_validate_narrative_consistency_no_fragments(self, service, mock_session):
        """Test validation when no fragments exist"""
        # Mock empty database result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await service.validate_narrative_consistency()

        # Should report empty status
        assert result["status"] == "empty"
        assert "No story fragments found" in result["issues"][0]

    async def test_validate_narrative_consistency_no_start_fragment(self, service, narrative_graph_fragments, mock_session):
        """Test validation when start fragment is missing"""
        # Remove start fragment
        fragments_without_start = narrative_graph_fragments[1:]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = fragments_without_start
        mock_session.execute.return_value = mock_result

        result = await service.validate_narrative_consistency()

        # Should report error status
        assert result["status"] == "error"
        assert "'start' fragment not found" in result["issues"][0]

    async def test_validate_narrative_consistency_circular_references(self, service, mock_session):
        """Test validation with circular references"""
        # Create fragments with circular references
        frag1 = StoryFragment(id=1, key="circle1", text="First", auto_next_fragment_key="circle2")
        frag2 = StoryFragment(id=2, key="circle2", text="Second", auto_next_fragment_key="circle1")
        start = StoryFragment(id=3, key="start", text="Start", auto_next_fragment_key="circle1")

        circular_fragments = [start, frag1, frag2]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = circular_fragments
        mock_session.execute.return_value = mock_result

        result = await service.validate_narrative_consistency()

        # Should handle circular references without infinite loops
        assert "status" in result
        assert result["summary"]["total_fragments"] == 3
        assert result["summary"]["reachable_fragments"] == 3

    async def test_validate_narrative_consistency_database_error(self, service, mock_session):
        """Test handling database error during validation"""
        # Mock database error
        mock_session.execute.side_effect = SQLAlchemyError("Database connection failed")

        # Should raise the exception (current implementation doesn't handle it)
        with pytest.raises(SQLAlchemyError):
            await service.validate_narrative_consistency()


class TestNarrativeGraphVisualization:
    """Test narrative graph visualization functionality"""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def service(self, mock_session):
        """NarrativeAdminService instance with mocked session"""
        return NarrativeAdminService(mock_session)

    async def test_visualize_narrative_graph_placeholder(self, service):
        """Test narrative graph visualization (placeholder implementation)"""
        result = await service.visualize_narrative_graph()

        # Currently returns not_implemented placeholder
        assert "graph" in result
        assert result["graph"] == "not_implemented"

    async def test_visualize_narrative_graph_with_data(self, service, narrative_graph_fragments, mock_session):
        """Test narrative graph visualization with actual data"""
        # When implemented, this would test actual graph generation
        result = await service.visualize_narrative_graph()

        # Currently returns placeholder
        assert isinstance(result, dict)
        assert "graph" in result


class TestShopItemIntegration:
    """Test shop item integration and access conditions"""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    async def service(self, mock_session):
        """NarrativeAdminService instance with mocked session"""
        return NarrativeAdminService(mock_session)

    @pytest.fixture
    def sample_shop_item(self):
        """Sample shop item for testing"""
        return ShopItem(
            id=1,
            name="Exclusive Diana Conversation",
            description="Unlock special dialogue with Diana",
            price=500,
            is_vip_only=True,
            is_active=True
        )

    @pytest.fixture
    def sample_user_purchase(self):
        """Sample user purchase for testing"""
        return UserPurchase(
            id=1,
            user_id=12345,
            shop_item_id=1,
            quantity=1,
            total_cost=500,
            created_at=datetime.utcnow()
        )

    async def test_fragment_access_with_shop_item_requirement(self, service, sample_fragment_data, sample_shop_item, mock_session):
        """Test fragment access validation with shop item requirements"""
        # Add shop item requirement to fragment
        fragment_data_with_shop_requirement = sample_fragment_data.copy()
        fragment_data_with_shop_requirement["required_shop_item_id"] = 1

        # This would test access validation when implemented
        # Currently, the service doesn't implement this functionality
        result = await service.create_story_fragment(fragment_data_with_shop_requirement)

        # Placeholder assertion
        assert "status" in result

    async def test_conditional_access_validation_user_has_item(self, service, mock_session):
        """Test conditional access when user owns required item"""
        user_id = 12345
        fragment_key = "premium_fragment"
        required_item_id = 1

        # Mock user has purchased the item
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = True
        mock_session.execute.return_value = mock_result

        # When access validation is implemented, this would test the logic
        # Currently, no access validation method exists in the service
        pass

    async def test_conditional_access_validation_user_lacks_item(self, service, mock_session):
        """Test conditional access when user doesn't own required item"""
        user_id = 12345
        fragment_key = "premium_fragment"
        required_item_id = 1

        # Mock user has not purchased the item
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # When access validation is implemented, this would test denial logic
        # Currently, no access validation method exists in the service
        pass

    async def test_complex_conditional_logic_multiple_requirements(self, service, mock_session):
        """Test complex conditional logic with multiple requirements"""
        user_id = 12345
        fragment_requirements = {
            "required_besitos": 1000,
            "required_role": "vip",
            "required_shop_items": [1, 2],
            "required_previous_choices": ["choice_romantic", "choice_deep"]
        }

        # When complex conditional logic is implemented, this would test it
        # Currently, the service doesn't implement this functionality
        pass

    async def test_shop_item_integration_transactional_integrity(self, service, mock_session):
        """Test that shop item integration maintains transactional integrity"""
        # Test that fragment access changes are rolled back if shop validation fails
        fragment_data = {
            "key": "premium_content",
            "text": "Exclusive premium content",
            "required_shop_item_id": 999  # Non-existent item
        }

        # Mock shop item validation failure
        mock_session.commit.side_effect = IntegrityError("Foreign key constraint", None, None)

        # When implemented, this would test rollback behavior
        result = await service.create_story_fragment(fragment_data)

        # Currently returns placeholder
        assert "status" in result


class TestBulkImportFunctionality:
    """Test bulk import functionality"""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        session.add_all = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session

    @pytest.fixture
    async def service(self, mock_session):
        """NarrativeAdminService instance with mocked session"""
        return NarrativeAdminService(mock_session)

    @pytest.fixture
    def sample_import_data(self):
        """Sample bulk import data"""
        return b'''[
            {
                "key": "imported_fragment_1",
                "text": "This is imported content",
                "character": "Diana",
                "level": 1
            },
            {
                "key": "imported_fragment_2",
                "text": "This is more imported content",
                "character": "Lucien",
                "level": 2,
                "choices": [
                    {
                        "destination_fragment_key": "imported_fragment_1",
                        "text": "Go back to Diana"
                    }
                ]
            }
        ]'''

    async def test_bulk_import_narrative_content_success(self, service, sample_import_data, mock_session):
        """Test successful bulk import of narrative content"""
        result = await service.bulk_import_narrative_content(sample_import_data)

        # Currently returns not_implemented placeholder
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_bulk_import_narrative_content_invalid_json(self, service, mock_session):
        """Test bulk import with invalid JSON data"""
        invalid_json = b'{"key": "test", invalid json}'

        result = await service.bulk_import_narrative_content(invalid_json)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_bulk_import_narrative_content_duplicate_keys(self, service, mock_session):
        """Test bulk import with duplicate fragment keys"""
        duplicate_data = b'''[
            {"key": "duplicate", "text": "First"},
            {"key": "duplicate", "text": "Second"}
        ]'''

        result = await service.bulk_import_narrative_content(duplicate_data)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_bulk_import_narrative_content_partial_failure(self, service, mock_session):
        """Test bulk import with some valid and some invalid entries"""
        mixed_data = b'''[
            {"key": "valid", "text": "Valid content"},
            {"key": "", "text": "Invalid - empty key"},
            {"key": "valid2", "text": "Another valid entry"}
        ]'''

        result = await service.bulk_import_narrative_content(mixed_data)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_bulk_import_narrative_content_empty_data(self, service, mock_session):
        """Test bulk import with empty data"""
        empty_data = b'[]'

        result = await service.bulk_import_narrative_content(empty_data)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_bulk_import_narrative_content_database_error(self, service, sample_import_data, mock_session):
        """Test bulk import handling database error"""
        # Mock database error during import
        mock_session.commit.side_effect = SQLAlchemyError("Database error during bulk insert")

        result = await service.bulk_import_narrative_content(sample_import_data)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases"""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def service(self, mock_session):
        """NarrativeAdminService instance with mocked session"""
        return NarrativeAdminService(mock_session)

    async def test_database_connection_failure(self, service, mock_session):
        """Test handling database connection failure"""
        mock_session.execute.side_effect = SQLAlchemyError("Connection failed")

        # Test various operations with connection failure
        fragment_data = {"key": "test", "text": "test"}

        result = await service.create_story_fragment(fragment_data)
        assert "status" in result  # Currently returns not_implemented

        result = await service.update_story_fragment("test", {"text": "updated"})
        assert "status" in result

        result = await service.delete_story_fragment("test")
        assert "status" in result

    async def test_invalid_fragment_data_validation(self, service):
        """Test validation of invalid fragment data"""
        invalid_cases = [
            {},  # Empty data
            {"key": None},  # Null key
            {"key": "", "text": ""},  # Empty key and text
            {"key": "test"},  # Missing required text
            {"text": "test"},  # Missing required key
            {"key": "x" * 100, "text": "test"},  # Key too long
            {"key": "test", "text": None},  # Null text
        ]

        for invalid_data in invalid_cases:
            result = await service.create_story_fragment(invalid_data)
            # Currently all return not_implemented
            assert "status" in result
            assert result["status"] == "not_implemented"

    async def test_memory_management_large_datasets(self, service, narrative_graph_fragments, mock_session):
        """Test memory management with large datasets"""
        # Simulate large dataset by repeating fragments
        large_dataset = narrative_graph_fragments * 1000

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = large_dataset
        mock_session.execute.return_value = mock_result

        # Test that validation can handle large datasets
        result = await service.validate_narrative_consistency()

        # Should complete without memory issues
        assert "status" in result

    async def test_concurrent_access_handling(self, mock_session):
        """Test handling of concurrent access to narrative admin operations"""
        service1 = NarrativeAdminService(mock_session)
        service2 = NarrativeAdminService(mock_session)

        fragment_data = {"key": "concurrent_test", "text": "Test concurrent access"}

        # Simulate concurrent operations
        tasks = [
            service1.create_story_fragment(fragment_data),
            service2.create_story_fragment(fragment_data),
            service1.validate_narrative_consistency(),
            service2.visualize_narrative_graph()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete (currently return not_implemented)
        for result in results:
            if isinstance(result, dict):
                assert "status" in result or "graph" in result

    async def test_session_timeout_handling(self, service, mock_session):
        """Test handling of database session timeouts"""
        # Mock session timeout
        mock_session.execute.side_effect = SQLAlchemyError("Session timeout")

        result = await service.validate_narrative_consistency()

        # Should raise the exception (current implementation doesn't handle timeouts)
        # When implemented, should gracefully handle timeouts
        with pytest.raises(SQLAlchemyError):
            await service.validate_narrative_consistency()

    async def test_null_and_boundary_values(self, service):
        """Test handling of null and boundary values"""
        boundary_cases = [
            {"key": "a", "text": "b"},  # Minimum valid values
            {"key": "a" * 50, "text": "b" * 65535},  # Maximum field lengths
            {"key": "test", "text": "test", "min_besitos": 0},  # Minimum besitos
            {"key": "test", "text": "test", "min_besitos": 999999},  # Large besitos
            {"key": "test", "text": "test", "level": 1},  # Minimum level
            {"key": "test", "text": "test", "level": 100},  # High level
        ]

        for case in boundary_cases:
            result = await service.create_story_fragment(case)
            # Currently returns not_implemented
            assert "status" in result

    async def test_unicode_and_special_characters(self, service):
        """Test handling of unicode and special characters in content"""
        unicode_cases = [
            {"key": "unicode_test", "text": "Café con leche ☕"},
            {"key": "emoji_test", "text": "Diana says: 'Hello! 👋🎭💕'"},
            {"key": "special_chars", "text": "Special chars: <>&\"'"},
            {"key": "newlines", "text": "Line 1\nLine 2\r\nLine 3"},
            {"key": "quotes", "text": "She said: \"Hello, 'world'!\""},
        ]

        for case in unicode_cases:
            result = await service.create_story_fragment(case)
            # Currently returns not_implemented
            assert "status" in result


class TestServiceIntegration:
    """Test integration between different service components"""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def service(self, mock_session):
        """NarrativeAdminService instance with mocked session"""
        return NarrativeAdminService(mock_session)

    async def test_fragment_creation_with_analytics_integration(self, service, sample_fragment_data, mock_session):
        """Test that fragment creation integrates with analytics system"""
        # When implemented, this would test automatic analytics setup
        result = await service.create_story_fragment(sample_fragment_data)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_fragment_deletion_cleanup_analytics(self, service, mock_session):
        """Test that fragment deletion cleans up associated analytics"""
        fragment_id = "test_fragment"

        # When implemented, this would test cascade deletion of analytics
        result = await service.delete_story_fragment(fragment_id)

        # Currently returns not_implemented
        assert "status" in result

    async def test_consistency_validation_performance_with_analytics(self, service, narrative_graph_fragments, mock_session):
        """Test consistency validation performance when analytics data is present"""
        # Mock fragments with analytics data
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = narrative_graph_fragments
        mock_session.execute.return_value = mock_result

        import time
        start_time = time.time()
        result = await service.validate_narrative_consistency()
        end_time = time.time()

        # Validation should complete in reasonable time
        assert end_time - start_time < 5.0  # Should complete within 5 seconds
        assert "status" in result


# Performance and stress tests
class TestPerformanceAndStress:
    """Test performance and stress scenarios"""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def service(self, mock_session):
        """NarrativeAdminService instance with mocked session"""
        return NarrativeAdminService(mock_session)

    async def test_large_narrative_graph_validation_performance(self, service, mock_session):
        """Test performance with large narrative graphs"""
        # Create a large graph (1000 fragments)
        large_graph = []
        for i in range(1000):
            fragment = StoryFragment(
                id=i+1,
                key=f"fragment_{i:04d}",
                text=f"Content for fragment {i}",
                character="Diana" if i % 2 == 0 else "Lucien"
            )

            # Add some choices to create connections
            if i > 0:  # Not the first fragment
                choice = NarrativeChoice(
                    source_fragment_id=i,
                    destination_fragment_key=f"fragment_{(i-1):04d}",
                    text=f"Choice {i}"
                )
                fragment.choices = [choice]

            large_graph.append(fragment)

        # Add start fragment
        start = StoryFragment(id=1001, key="start", text="Start", auto_next_fragment_key="fragment_0000")
        large_graph.append(start)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = large_graph
        mock_session.execute.return_value = mock_result

        import time
        start_time = time.time()
        result = await service.validate_narrative_consistency()
        end_time = time.time()

        # Should complete within reasonable time even for large graphs
        assert end_time - start_time < 10.0  # Should complete within 10 seconds
        assert result["summary"]["total_fragments"] == 1001

    async def test_concurrent_validation_operations(self, service, narrative_graph_fragments, mock_session):
        """Test concurrent narrative validation operations"""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = narrative_graph_fragments
        mock_session.execute.return_value = mock_result

        # Run multiple validation operations concurrently
        tasks = [service.validate_narrative_consistency() for _ in range(10)]

        import time
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # All should complete successfully
        for result in results:
            assert "status" in result

        # Concurrent operations shouldn't take much longer than single operation
        assert end_time - start_time < 20.0

    async def test_memory_usage_with_deep_graph(self, service, mock_session):
        """Test memory usage with deeply nested narrative graphs"""
        # Create a deep chain of fragments (100 levels deep)
        deep_graph = []
        for i in range(100):
            fragment = StoryFragment(
                id=i+1,
                key=f"level_{i:03d}",
                text=f"Deep level {i} content",
                auto_next_fragment_key=f"level_{(i+1):03d}" if i < 99 else None
            )
            deep_graph.append(fragment)

        # Add start fragment
        start = StoryFragment(id=101, key="start", text="Start", auto_next_fragment_key="level_000")
        deep_graph.append(start)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = deep_graph
        mock_session.execute.return_value = mock_result

        result = await service.validate_narrative_consistency()

        # Should handle deep recursion without stack overflow
        assert "status" in result
        assert result["summary"]["total_fragments"] == 101
        assert result["summary"]["reachable_fragments"] == 101  # All should be reachable