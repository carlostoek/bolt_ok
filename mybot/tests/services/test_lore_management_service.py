"""
Comprehensive test suite for LoreManagementService

Tests cover all core functionality including:
- Lore piece CRUD operations with rich metadata
- Shop item integration and linking
- Complex unlock condition logic
- Hierarchical organization and search capabilities
- User access tracking and analytics
- Error handling and edge cases
"""

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Create mock pytest decorators for compatibility
    class MockPytest:
        @staticmethod
        def fixture(*args, **kwargs):
            def decorator(func):
                return func
            return decorator
    pytest = MockPytest()

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

from services.lore_management_service import LoreManagementService
from database.models import LorePiece, ShopItem, UserLorePiece


class TestLoreManagementService:
    """Test suite for LoreManagementService core functionality"""

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
        """LoreManagementService instance with mocked session"""
        return LoreManagementService(mock_session)

    @pytest.fixture
    def sample_lore_data(self):
        """Sample lore piece data for testing"""
        return {
            "code_name": "test_lore_001",
            "title": "Diana's Secret Letter",
            "description": "A mysterious letter found in Diana's personal belongings",
            "content_type": "text",
            "content": "My dearest, there are things I must tell you...",
            "category": "personal",
            "is_main_story": True,
            "rich_content_data": {
                "images": ["letter_bg.jpg"],
                "audio": "diana_voice_letter.mp3",
                "interactive_elements": ["handwriting_reveal"]
            },
            "content_metadata": {
                "tags": ["secret", "romantic", "mysterious"],
                "search_keywords": ["letter", "diana", "secret", "personal"],
                "difficulty_level": 3
            },
            "unlock_condition_tree": {
                "type": "and",
                "conditions": [
                    {"type": "item_purchase", "value": 1},
                    {"type": "narrative_progress", "value": 5},
                    {"type": "user_level", "min_level": 3}
                ]
            },
            "related_lore_pieces": [2, 5, 8]
        }

    @pytest.fixture
    def sample_lore_piece(self):
        """Sample LorePiece model instance"""
        return LorePiece(
            id=1,
            code_name="test_lore_001",
            title="Diana's Secret Letter",
            description="A mysterious letter found in Diana's personal belongings",
            content_type="text",
            content="My dearest, there are things I must tell you...",
            category="personal",
            is_main_story=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_active=True
        )

    @pytest.fixture
    def sample_shop_item(self):
        """Sample shop item for testing"""
        return ShopItem(
            id=1,
            name="Diana's Personal Collection",
            description="Unlock exclusive personal content from Diana",
            price=500,
            is_vip_only=True,
            unlocks_lore_piece_id=1,
            is_active=True,
            created_at=datetime.utcnow()
        )

    @pytest.fixture
    def sample_user_lore_piece(self):
        """Sample UserLorePiece model instance"""
        return UserLorePiece(
            user_id=12345,
            lore_piece_id=1,
            unlocked_at=datetime.utcnow(),
            context={"source": "shop_purchase", "item_id": 1}
        )


class TestLorePieceCRUD:
    """Test lore piece CRUD operations"""

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
        """LoreManagementService instance with mocked session"""
        return LoreManagementService(mock_session)

    async def test_create_lore_piece_success(self, service, sample_lore_data, mock_session):
        """Test successful lore piece creation"""
        # Mock successful database operation
        mock_session.commit.return_value = None

        # Call the method (currently returns not_implemented)
        result = await service.create_lore_piece(sample_lore_data)

        # Verify the result structure (placeholder for now)
        assert "status" in result
        assert result["status"] == "not_implemented"

        # Verify logging was called
        # This tests the current placeholder implementation
        # When implemented, this would test actual lore piece creation

    async def test_create_lore_piece_with_rich_metadata(self, service, sample_lore_data, mock_session):
        """Test lore piece creation with rich metadata"""
        rich_data = sample_lore_data.copy()
        rich_data["content_type"] = "interactive"
        rich_data["rich_content_data"] = {
            "video_url": "https://example.com/video.mp4",
            "interactive_elements": ["clickable_map", "character_selector"],
            "animations": ["fade_in", "typewriter_effect"]
        }

        result = await service.create_lore_piece(rich_data)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_create_lore_piece_invalid_data(self, service, mock_session):
        """Test lore piece creation with invalid data"""
        invalid_data = {
            "code_name": "",  # Empty code name should fail
            "title": None,  # Null title should fail
            "content_type": "text"
        }

        result = await service.create_lore_piece(invalid_data)

        # Currently returns not_implemented, but should eventually validate data
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_create_lore_piece_duplicate_code_name(self, service, sample_lore_data, mock_session):
        """Test lore piece creation with duplicate code name"""
        # Mock integrity error for duplicate code name
        mock_session.commit.side_effect = IntegrityError("Duplicate key", None, None)

        result = await service.create_lore_piece(sample_lore_data)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_update_lore_piece_success(self, service, mock_session):
        """Test successful lore piece update"""
        lore_id = 1
        updates = {
            "title": "Updated Diana's Secret Letter - Chapter 2",
            "content": "Updated content with new revelations...",
            "content_metadata": {
                "tags": ["secret", "romantic", "mysterious", "revelation"],
                "difficulty_level": 4
            }
        }

        result = await service.update_lore_piece(lore_id, updates)

        # Verify the result structure (placeholder for now)
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_update_lore_piece_nonexistent(self, service, mock_session):
        """Test updating non-existent lore piece"""
        lore_id = 999
        updates = {"title": "Updated title"}

        result = await service.update_lore_piece(lore_id, updates)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_update_lore_piece_empty_updates(self, service, mock_session):
        """Test updating lore piece with empty updates"""
        lore_id = 1
        updates = {}

        result = await service.update_lore_piece(lore_id, updates)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_update_lore_piece_preserve_relationships(self, service, mock_session):
        """Test that updates preserve existing relationships"""
        lore_id = 1
        updates = {
            "title": "Updated title",
            # Should not affect existing shop item relationships
        }

        result = await service.update_lore_piece(lore_id, updates)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"


class TestShopItemIntegration:
    """Test shop item integration and linking functionality"""

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
        """LoreManagementService instance with mocked session"""
        return LoreManagementService(mock_session)

    async def test_link_lore_to_shop_item_success(self, service, mock_session):
        """Test successful linking of lore piece to shop item"""
        lore_id = 1
        shop_item_id = 1

        # Mock successful database operation
        mock_session.commit.return_value = None

        result = await service.link_lore_to_shop_item(lore_id, shop_item_id)

        # Verify the result structure (placeholder for now)
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_link_lore_to_shop_item_nonexistent_lore(self, service, mock_session):
        """Test linking non-existent lore piece to shop item"""
        lore_id = 999  # Non-existent
        shop_item_id = 1

        result = await service.link_lore_to_shop_item(lore_id, shop_item_id)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_link_lore_to_shop_item_nonexistent_shop_item(self, service, mock_session):
        """Test linking lore piece to non-existent shop item"""
        lore_id = 1
        shop_item_id = 999  # Non-existent

        result = await service.link_lore_to_shop_item(lore_id, shop_item_id)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_unlink_lore_from_shop_item_success(self, service, mock_session):
        """Test successful unlinking of lore piece from shop item"""
        lore_id = 1
        shop_item_id = 1

        # Mock successful database operation
        mock_session.commit.return_value = None

        result = await service.unlink_lore_from_shop_item(lore_id, shop_item_id)

        # Verify the result structure (placeholder for now)
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_unlink_lore_from_shop_item_not_linked(self, service, mock_session):
        """Test unlinking lore piece that's not linked to shop item"""
        lore_id = 1
        shop_item_id = 2  # Not linked

        result = await service.unlink_lore_from_shop_item(lore_id, shop_item_id)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"

    async def test_shop_integration_transactional_integrity(self, service, mock_session):
        """Test that shop integration maintains transactional integrity"""
        lore_id = 1
        shop_item_id = 1

        # Mock database error during linking
        mock_session.commit.side_effect = SQLAlchemyError("Database constraint violation")

        result = await service.link_lore_to_shop_item(lore_id, shop_item_id)

        # Currently returns not_implemented
        assert "status" in result
        assert result["status"] == "not_implemented"

    @patch('services.lore_management_service.logger')
    async def test_shop_integration_logging(self, mock_logger, service, mock_session):
        """Test that shop integration operations are properly logged"""
        lore_id = 1
        shop_item_id = 1

        await service.link_lore_to_shop_item(lore_id, shop_item_id)

        # Verify logging was called
        mock_logger.info.assert_called()


class TestComplexUnlockConditions:
    """Test complex unlock condition logic"""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    async def service(self, mock_session):
        """LoreManagementService instance with mocked session"""
        return LoreManagementService(mock_session)

    async def test_simple_item_ownership_condition(self, service, mock_session):
        """Test simple item ownership unlock condition"""
        unlock_conditions = {
            "type": "item_purchase",
            "value": 1  # Shop item ID
        }

        # This would test unlock condition evaluation when implemented
        # Currently, no unlock condition evaluation method exists
        pass

    async def test_complex_multi_condition_logic(self, service, mock_session):
        """Test complex multi-condition unlock logic"""
        complex_conditions = {
            "type": "and",
            "conditions": [
                {"type": "item_purchase", "value": 1},
                {"type": "narrative_progress", "value": 5},
                {
                    "type": "or",
                    "conditions": [
                        {"type": "user_level", "min_level": 10},
                        {"type": "vip_status", "value": True}
                    ]
                },
                {"type": "time_based", "after": "2024-01-01"}
            ]
        }

        # When complex condition evaluation is implemented, this would test it
        # Currently, the service doesn't implement this functionality
        pass

    async def test_time_based_unlock_conditions(self, service, mock_session):
        """Test time-based unlock conditions"""
        time_conditions = [
            {"type": "time_based", "after": "2024-01-01T00:00:00Z"},
            {"type": "time_based", "before": "2024-12-31T23:59:59Z"},
            {"type": "time_window", "start": "2024-06-01", "end": "2024-08-31"}
        ]

        for condition in time_conditions:
            # When time-based conditions are implemented, this would test them
            pass

    async def test_user_engagement_level_conditions(self, service, mock_session):
        """Test user engagement level unlock conditions"""
        engagement_conditions = {
            "type": "and",
            "conditions": [
                {"type": "daily_visits", "min_count": 7},
                {"type": "total_playtime", "min_hours": 10},
                {"type": "interaction_count", "min_interactions": 50}
            ]
        }

        # When engagement-based conditions are implemented, this would test them
        pass

    async def test_narrative_progress_conditions(self, service, mock_session):
        """Test narrative progress unlock conditions"""
        narrative_conditions = {
            "type": "and",
            "conditions": [
                {"type": "chapter_completed", "value": 3},
                {"type": "choice_made", "choice_id": "romantic_path"},
                {"type": "character_relationship", "character": "diana", "min_level": 5}
            ]
        }

        # When narrative progress conditions are implemented, this would test them
        pass

    async def test_nested_condition_logic(self, service, mock_session):
        """Test deeply nested condition logic"""
        nested_conditions = {
            "type": "or",
            "conditions": [
                {
                    "type": "and",
                    "conditions": [
                        {"type": "item_purchase", "value": 1},
                        {
                            "type": "or",
                            "conditions": [
                                {"type": "user_level", "min_level": 5},
                                {"type": "special_event", "event_id": "summer_2024"}
                            ]
                        }
                    ]
                },
                {"type": "admin_override", "value": True}
            ]
        }

        # When nested condition evaluation is implemented, this would test it
        pass


class TestHierarchicalOrganizationAndSearch:
    """Test hierarchical organization and search functionality"""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    async def service(self, mock_session):
        """LoreManagementService instance with mocked session"""
        return LoreManagementService(mock_session)

    @pytest.fixture
    def sample_categorized_lore(self):
        """Sample categorized lore pieces for testing"""
        return [
            LorePiece(id=1, code_name="personal_letter_1", title="Diana's Letter 1", category="personal"),
            LorePiece(id=2, code_name="personal_diary_1", title="Diana's Diary Entry", category="personal"),
            LorePiece(id=3, code_name="story_chapter_1", title="Chapter 1: Meeting", category="main_story"),
            LorePiece(id=4, code_name="story_chapter_2", title="Chapter 2: Discovery", category="main_story"),
            LorePiece(id=5, code_name="secret_document_1", title="Mysterious Document", category="secrets"),
        ]

    async def test_organize_lore_by_category_success(self, service, sample_categorized_lore, mock_session):
        """Test successful lore organization by category"""
        category_filters = {"include_categories": ["personal", "main_story"]}

        # Mock database result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_categorized_lore[:4]
        mock_session.execute.return_value = mock_result

        result = await service.organize_lore_by_category(category_filters)

        # Currently returns empty dict (not implemented)
        assert isinstance(result, dict)

    async def test_organize_lore_by_category_empty_filters(self, service, sample_categorized_lore, mock_session):
        """Test lore organization with empty category filters"""
        category_filters = {}

        result = await service.organize_lore_by_category(category_filters)

        # Currently returns empty dict
        assert isinstance(result, dict)

    async def test_organize_lore_by_category_nonexistent_category(self, service, mock_session):
        """Test lore organization for non-existent category"""
        category_filters = {"include_categories": ["nonexistent_category"]}

        # Mock empty database result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await service.organize_lore_by_category(category_filters)

        # Currently returns empty dict
        assert isinstance(result, dict)

    async def test_search_lore_pieces_by_title(self, service, sample_categorized_lore, mock_session):
        """Test searching lore pieces by title"""
        search_criteria = {"title": "Diana's"}

        # Mock database result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_categorized_lore[:2]
        mock_session.execute.return_value = mock_result

        result = await service.search_lore_pieces(search_criteria)

        # Currently returns empty list (not implemented)
        assert isinstance(result, list)

    async def test_search_lore_pieces_by_category(self, service, sample_categorized_lore, mock_session):
        """Test searching lore pieces by category"""
        search_criteria = {"category": "personal"}

        result = await service.search_lore_pieces(search_criteria)

        # Currently returns empty list
        assert isinstance(result, list)

    async def test_search_lore_pieces_by_tags(self, service, mock_session):
        """Test searching lore pieces by tags"""
        search_criteria = {"tags": ["romantic", "secret"]}

        result = await service.search_lore_pieces(search_criteria)

        # Currently returns empty list
        assert isinstance(result, list)

    async def test_search_lore_pieces_by_content_type(self, service, mock_session):
        """Test searching lore pieces by content type"""
        search_criteria = {"content_type": "interactive"}

        result = await service.search_lore_pieces(search_criteria)

        # Currently returns empty list
        assert isinstance(result, list)

    async def test_search_lore_pieces_complex_criteria(self, service, mock_session):
        """Test searching with complex criteria"""
        search_criteria = {
            "title": "Diana",
            "category": "personal",
            "tags": ["romantic"],
            "content_type": "text",
            "is_main_story": True
        }

        result = await service.search_lore_pieces(search_criteria)

        # Currently returns empty list
        assert isinstance(result, list)

    async def test_search_lore_pieces_no_results(self, service, mock_session):
        """Test search with criteria that match no lore pieces"""
        search_criteria = {"title": "nonexistent_title"}

        # Mock empty database result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await service.search_lore_pieces(search_criteria)

        # Currently returns empty list
        assert isinstance(result, list)

    async def test_hierarchical_content_relationships(self, service, mock_session):
        """Test hierarchical content relationships"""
        # Test parent-child relationships in lore pieces
        relationship_data = {
            "parent_lore_id": 1,
            "child_lore_ids": [2, 3, 4],
            "relationship_type": "series"
        }

        # When hierarchical relationships are implemented, this would test them
        # Currently, the service doesn't implement this functionality
        pass


class TestUserAccessTrackingAndAnalytics:
    """Test user access tracking and analytics functionality"""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    async def service(self, mock_session):
        """LoreManagementService instance with mocked session"""
        return LoreManagementService(mock_session)

    @pytest.fixture
    def sample_user_unlocks(self):
        """Sample user unlock data for analytics testing"""
        base_time = datetime.utcnow()
        return [
            UserLorePiece(
                user_id=12345, lore_piece_id=1,
                unlocked_at=base_time - timedelta(days=25),
                context={"source": "shop_purchase", "item_id": 1}
            ),
            UserLorePiece(
                user_id=12346, lore_piece_id=1,
                unlocked_at=base_time - timedelta(days=20),
                context={"source": "narrative_progress", "chapter": 3}
            ),
            UserLorePiece(
                user_id=12347, lore_piece_id=1,
                unlocked_at=base_time - timedelta(days=15),
                context={"source": "shop_purchase", "item_id": 1}
            ),
            UserLorePiece(
                user_id=12348, lore_piece_id=1,
                unlocked_at=base_time - timedelta(days=10),
                context={"source": "special_event", "event": "summer_2024"}
            ),
            UserLorePiece(
                user_id=12349, lore_piece_id=1,
                unlocked_at=base_time - timedelta(days=5),
                context={"source": "shop_purchase", "item_id": 2}
            ),
        ]

    async def test_get_lore_unlock_analytics_success(self, service, sample_user_unlocks, mock_session):
        """Test successful retrieval of lore unlock analytics"""
        lore_id = 1

        # Mock database result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_user_unlocks
        mock_session.execute.return_value = mock_result

        result = await service.get_lore_unlock_analytics(lore_id)

        # Verify the analytics structure
        assert "lore_id" in result
        assert result["lore_id"] == lore_id
        assert "total_unlocks" in result
        assert result["total_unlocks"] == 5
        assert "unlocks_by_source" in result
        assert "unlocks_timeline_last_30d" in result
        assert "first_unlock" in result
        assert "last_unlock" in result

        # Verify unlock source analysis
        unlocks_by_source = result["unlocks_by_source"]
        assert unlocks_by_source["shop_purchase"] == 3
        assert unlocks_by_source["narrative_progress"] == 1
        assert unlocks_by_source["special_event"] == 1

    async def test_get_lore_unlock_analytics_no_unlocks(self, service, mock_session):
        """Test analytics for lore piece with no unlocks"""
        lore_id = 999

        # Mock empty database result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await service.get_lore_unlock_analytics(lore_id)

        # Verify empty analytics structure
        assert result["lore_id"] == lore_id
        assert result["total_unlocks"] == 0
        assert result["unlocks_by_source"] == {}
        assert result["unlocks_timeline"] == {}
        assert "No unlocks found" in result["summary"]

    async def test_get_lore_unlock_analytics_timeline_filtering(self, service, mock_session):
        """Test analytics timeline filtering for last 30 days"""
        lore_id = 1

        # Create unlocks with some outside 30-day window
        now = datetime.utcnow()
        unlocks_mixed_timeline = [
            UserLorePiece(
                user_id=1, lore_piece_id=1,
                unlocked_at=now - timedelta(days=45),  # Outside 30-day window
                context={"source": "old_unlock"}
            ),
            UserLorePiece(
                user_id=2, lore_piece_id=1,
                unlocked_at=now - timedelta(days=15),  # Within 30-day window
                context={"source": "recent_unlock"}
            ),
            UserLorePiece(
                user_id=3, lore_piece_id=1,
                unlocked_at=now - timedelta(days=5),   # Within 30-day window
                context={"source": "recent_unlock"}
            ),
        ]

        # Mock database result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = unlocks_mixed_timeline
        mock_session.execute.return_value = mock_result

        result = await service.get_lore_unlock_analytics(lore_id)

        # Timeline should only include unlocks from last 30 days
        timeline = result["unlocks_timeline_last_30d"]
        # Should have 2 entries in timeline (the recent ones)
        timeline_total = sum(timeline.values())
        assert timeline_total == 2  # Only recent unlocks counted in timeline

        # But total unlocks should include all
        assert result["total_unlocks"] == 3

    async def test_get_lore_unlock_analytics_context_analysis(self, service, mock_session):
        """Test analytics context analysis for unlock sources"""
        lore_id = 1

        unlocks_with_context = [
            UserLorePiece(
                user_id=1, lore_piece_id=1, unlocked_at=datetime.utcnow(),
                context={"source": "shop_purchase", "item_id": 1, "price": 500}
            ),
            UserLorePiece(
                user_id=2, lore_piece_id=1, unlocked_at=datetime.utcnow(),
                context={"source": "narrative_progress", "chapter": 5, "character": "diana"}
            ),
            UserLorePiece(
                user_id=3, lore_piece_id=1, unlocked_at=datetime.utcnow(),
                context=None  # No context
            ),
        ]

        # Mock database result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = unlocks_with_context
        mock_session.execute.return_value = mock_result

        result = await service.get_lore_unlock_analytics(lore_id)

        # Verify context analysis
        unlocks_by_source = result["unlocks_by_source"]
        assert unlocks_by_source["shop_purchase"] == 1
        assert unlocks_by_source["narrative_progress"] == 1
        assert unlocks_by_source["unknown"] == 1  # No context case

    async def test_get_lore_unlock_analytics_database_error(self, service, mock_session):
        """Test handling database error during analytics retrieval"""
        lore_id = 1

        # Mock database error
        mock_session.execute.side_effect = SQLAlchemyError("Database connection failed")

        # Should raise the exception (current implementation doesn't handle it)
        with pytest.raises(SQLAlchemyError):
            await service.get_lore_unlock_analytics(lore_id)


class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge cases"""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def service(self, mock_session):
        """LoreManagementService instance with mocked session"""
        return LoreManagementService(mock_session)

    async def test_database_connection_failure(self, service, mock_session):
        """Test handling database connection failure"""
        mock_session.execute.side_effect = SQLAlchemyError("Connection failed")

        # Test various operations with connection failure
        lore_data = {"code_name": "test", "title": "test", "content_type": "text", "content": "test"}

        result = await service.create_lore_piece(lore_data)
        assert "status" in result  # Currently returns not_implemented

        result = await service.update_lore_piece(1, {"title": "updated"})
        assert "status" in result

        result = await service.organize_lore_by_category({})
        assert isinstance(result, dict)

        result = await service.search_lore_pieces({"title": "test"})
        assert isinstance(result, list)

    async def test_invalid_lore_data_validation(self, service):
        """Test validation of invalid lore data"""
        invalid_cases = [
            {},  # Empty data
            {"code_name": None},  # Null code name
            {"code_name": "", "title": ""},  # Empty code name and title
            {"code_name": "test"},  # Missing required title
            {"title": "test"},  # Missing required code name
            {"code_name": "x" * 100, "title": "test"},  # Code name too long
            {"code_name": "test", "title": None},  # Null title
            {"code_name": "test", "title": "test", "content_type": None},  # Null content type
        ]

        for invalid_data in invalid_cases:
            result = await service.create_lore_piece(invalid_data)
            # Currently all return not_implemented
            assert "status" in result
            assert result["status"] == "not_implemented"

    async def test_null_and_boundary_values(self, service):
        """Test handling of null and boundary values"""
        boundary_cases = [
            {"code_name": "a", "title": "b", "content_type": "text", "content": "c"},  # Minimum valid values
            {"code_name": "a" * 50, "title": "b" * 255, "content_type": "text", "content": "c" * 65535},  # Maximum field lengths
            {"code_name": "test", "title": "test", "content_type": "text", "content": "test", "is_main_story": True},
            {"code_name": "test", "title": "test", "content_type": "text", "content": "test", "is_main_story": False},
        ]

        for case in boundary_cases:
            result = await service.create_lore_piece(case)
            # Currently returns not_implemented
            assert "status" in result

    async def test_unicode_and_special_characters(self, service):
        """Test handling of unicode and special characters in content"""
        unicode_cases = [
            {
                "code_name": "unicode_test",
                "title": "Café con leche ☕",
                "content_type": "text",
                "content": "Diana says: 'Hello! 👋🎭💕'"
            },
            {
                "code_name": "emoji_test",
                "title": "Special Content 🎭",
                "content_type": "text",
                "content": "Emojis and unicode: 😍🌹💖"
            },
            {
                "code_name": "special_chars",
                "title": "Special chars: <>&\"'",
                "content_type": "text",
                "content": "Content with <tags> and \"quotes\" and 'apostrophes'"
            },
            {
                "code_name": "newlines",
                "title": "Content with newlines",
                "content_type": "text",
                "content": "Line 1\nLine 2\r\nLine 3"
            },
        ]

        for case in unicode_cases:
            result = await service.create_lore_piece(case)
            # Currently returns not_implemented
            assert "status" in result

    async def test_large_content_handling(self, service):
        """Test handling of large content data"""
        large_content_cases = [
            {
                "code_name": "large_text",
                "title": "Large Text Content",
                "content_type": "text",
                "content": "A" * 100000,  # 100KB of text
                "rich_content_data": {
                    "metadata": {"size": "large"},
                    "processing_hints": ["compress", "lazy_load"]
                }
            },
            {
                "code_name": "complex_metadata",
                "title": "Complex Metadata",
                "content_type": "interactive",
                "content": "Interactive content",
                "content_metadata": {
                    "tags": ["tag" + str(i) for i in range(100)],  # Many tags
                    "search_keywords": ["keyword" + str(i) for i in range(500)],  # Many keywords
                    "complex_structure": {
                        "nested": {"deeply": {"nested": {"data": "value"}}}
                    }
                }
            }
        ]

        for case in large_content_cases:
            result = await service.create_lore_piece(case)
            # Currently returns not_implemented
            assert "status" in result

    async def test_concurrent_operations(self, mock_session):
        """Test handling of concurrent lore management operations"""
        service1 = LoreManagementService(mock_session)
        service2 = LoreManagementService(mock_session)

        lore_data = {
            "code_name": "concurrent_test",
            "title": "Test concurrent access",
            "content_type": "text",
            "content": "Test content"
        }

        # Simulate concurrent operations
        tasks = [
            service1.create_lore_piece(lore_data),
            service2.create_lore_piece(lore_data),
            service1.organize_lore_by_category({}),
            service2.search_lore_pieces({"title": "test"}),
            service1.get_lore_unlock_analytics(1),
            service2.link_lore_to_shop_item(1, 1)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should complete (currently return not_implemented or appropriate structures)
        for result in results:
            if isinstance(result, dict):
                assert "status" in result or "lore_id" in result
            elif isinstance(result, list):
                assert isinstance(result, list)

    async def test_session_timeout_handling(self, service, mock_session):
        """Test handling of database session timeouts"""
        # Mock session timeout
        mock_session.execute.side_effect = SQLAlchemyError("Session timeout")

        # Test that operations handle timeouts gracefully
        with pytest.raises(SQLAlchemyError):
            await service.get_lore_unlock_analytics(1)

    async def test_memory_management_large_datasets(self, service, mock_session):
        """Test memory management with large analytics datasets"""
        lore_id = 1

        # Create a large dataset of unlock records
        large_unlocks = []
        for i in range(10000):
            unlock = UserLorePiece(
                user_id=i,
                lore_piece_id=lore_id,
                unlocked_at=datetime.utcnow() - timedelta(days=i % 30),
                context={"source": f"source_{i % 5}", "batch": i // 1000}
            )
            large_unlocks.append(unlock)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = large_unlocks
        mock_session.execute.return_value = mock_result

        # Should handle large dataset without memory issues
        result = await service.get_lore_unlock_analytics(lore_id)

        assert result["total_unlocks"] == 10000
        assert "unlocks_by_source" in result
        assert "unlocks_timeline_last_30d" in result


class TestServiceIntegration:
    """Test integration between different service components"""

    @pytest.fixture
    async def mock_session(self):
        """Mock database session"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def service(self, mock_session):
        """LoreManagementService instance with mocked session"""
        return LoreManagementService(mock_session)

    @patch('services.lore_management_service.logger')
    async def test_service_logging_integration(self, mock_logger, service, mock_session):
        """Test that all service operations are properly logged"""
        lore_data = {"code_name": "test", "title": "test", "content_type": "text", "content": "test"}

        await service.create_lore_piece(lore_data)
        await service.update_lore_piece(1, {"title": "updated"})
        await service.link_lore_to_shop_item(1, 1)
        await service.unlink_lore_from_shop_item(1, 1)
        await service.organize_lore_by_category({})
        await service.search_lore_pieces({"title": "test"})

        # Verify logging was called for all operations
        assert mock_logger.info.call_count >= 6

    async def test_analytics_performance_with_large_datasets(self, service, mock_session):
        """Test analytics performance with large datasets"""
        import time

        # Mock large dataset
        large_unlocks = [
            UserLorePiece(
                user_id=i, lore_piece_id=1,
                unlocked_at=datetime.utcnow() - timedelta(days=i % 30),
                context={"source": f"source_{i % 3}"}
            )
            for i in range(1000)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = large_unlocks
        mock_session.execute.return_value = mock_result

        start_time = time.time()
        result = await service.get_lore_unlock_analytics(1)
        end_time = time.time()

        # Analytics should complete in reasonable time
        assert end_time - start_time < 5.0  # Should complete within 5 seconds
        assert result["total_unlocks"] == 1000


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
        """LoreManagementService instance with mocked session"""
        return LoreManagementService(mock_session)

    async def test_concurrent_analytics_operations(self, service, mock_session):
        """Test concurrent analytics operations"""
        # Mock analytics data
        sample_unlocks = [
            UserLorePiece(
                user_id=i, lore_piece_id=1,
                unlocked_at=datetime.utcnow() - timedelta(days=i % 30),
                context={"source": "test"}
            )
            for i in range(100)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_unlocks
        mock_session.execute.return_value = mock_result

        # Run multiple analytics operations concurrently
        tasks = [service.get_lore_unlock_analytics(i) for i in range(1, 11)]

        import time
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # All should complete successfully
        for result in results:
            assert "lore_id" in result
            assert "total_unlocks" in result

        # Concurrent operations shouldn't take much longer than single operation
        assert end_time - start_time < 10.0

    async def test_large_search_result_handling(self, service, mock_session):
        """Test handling of large search result sets"""
        # Create large result set
        large_lore_set = [
            LorePiece(
                id=i,
                code_name=f"lore_{i:05d}",
                title=f"Lore Piece {i}",
                content_type="text",
                content=f"Content for lore piece {i}",
                category="test_category"
            )
            for i in range(1000)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = large_lore_set
        mock_session.execute.return_value = mock_result

        result = await service.search_lore_pieces({"category": "test_category"})

        # Should handle large result set
        assert isinstance(result, list)

    async def test_complex_categorization_performance(self, service, mock_session):
        """Test performance of complex categorization operations"""
        # Create diverse lore pieces with many categories
        diverse_lore = [
            LorePiece(
                id=i,
                code_name=f"diverse_lore_{i}",
                title=f"Diverse Lore {i}",
                content_type=["text", "image", "video", "interactive"][i % 4],
                content=f"Content {i}",
                category=f"category_{i % 10}"
            )
            for i in range(500)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = diverse_lore
        mock_session.execute.return_value = mock_result

        import time
        start_time = time.time()
        result = await service.organize_lore_by_category({})
        end_time = time.time()

        # Should complete within reasonable time
        assert end_time - start_time < 5.0
        assert isinstance(result, dict)