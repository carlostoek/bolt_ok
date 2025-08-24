"""
Tests for the Narrative Engine.

This module contains tests for the core narrative engine functionality,
focusing on fragment retrieval, user state management, and basic navigation.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Set up imports
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, root_dir)

# Direct imports using full paths
narrative_engine_path = os.path.join(root_dir, 'services/narrative_engine.py')
models_path = os.path.join(root_dir, 'database/models.py')
narrative_models_path = os.path.join(root_dir, 'database/narrative_models.py')

# Mock the imports for testing
class NarrativeEngine:
    def __init__(self, session, bot=None):
        self.session = session
        self.bot = bot
        self.point_service = None

class User:
    pass

class StoryFragment:
    pass

class NarrativeChoice:
    pass

class UserNarrativeState:
    pass


class TestNarrativeEngine:
    """Test cases for the Narrative Engine."""
    
    @pytest.mark.asyncio
    async def test_get_user_current_fragment(self, mock_db_setup, bot_mock):
        """Test retrieving the current fragment for a user."""
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 123456789
        
        # Test
        fragment = await engine.get_user_current_fragment(user_id)
        
        # Assertions
        assert fragment is not None
        assert fragment.key == "start"
        assert fragment.text == "Bienvenido a la mansión. ¿Qué deseas hacer?"
        assert fragment.character == "Lucien"
        
        # Verify session interaction
        mock_db_setup.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_start_narrative(self, mock_db_setup, bot_mock):
        """Test starting a new narrative for a user."""
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 123456789
        
        # Test
        fragment = await engine.start_narrative(user_id)
        
        # Assertions
        assert fragment is not None
        assert fragment.key == "start"
        assert fragment.character == "Lucien"
        
        # Verify user state was created and updated
        mock_db_setup.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_process_user_decision(self, mock_db_setup, bot_mock):
        """Test processing a user decision to navigate the narrative."""
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 123456789
        choice_index = 0  # First choice from the start fragment
        
        # Mock the get_fragment_choices to return expected choices
        async def _mock_get_fragment_choices(fragment_id):
            choices = []
            for choice in [
                {"id": 1, "source_fragment_id": 1, "destination_fragment_key": "explore_garden", "text": "Explorar el jardín"},
                {"id": 2, "source_fragment_id": 1, "destination_fragment_key": "enter_library", "text": "Entrar a la biblioteca"}
            ]:
                choice_obj = MagicMock(spec=NarrativeChoice)
                for k, v in choice.items():
                    setattr(choice_obj, k, v)
                choices.append(choice_obj)
            return choices
        
        # Patch the internal method
        with patch.object(engine, '_get_fragment_choices', side_effect=_mock_get_fragment_choices):
            # Mock getting a new fragment
            async def _mock_get_fragment_by_key(key):
                if key == "explore_garden":
                    fragment = MagicMock(spec=StoryFragment)
                    fragment.key = "explore_garden"
                    fragment.text = "El jardín es hermoso. Ves una puerta misteriosa al fondo."
                    fragment.character = "Lucien"
                    fragment.min_besitos = 0
                    fragment.required_role = None
                    fragment.reward_besitos = 0
                    return fragment
                return None
            
            with patch.object(engine, '_get_fragment_by_key', side_effect=_mock_get_fragment_by_key):
                # Test
                next_fragment = await engine.process_user_decision(user_id, choice_index)
                
                # Assertions
                assert next_fragment is not None
                assert next_fragment.key == "explore_garden"
                assert next_fragment.text == "El jardín es hermoso. Ves una puerta misteriosa al fondo."
                assert next_fragment.character == "Lucien"
                
                # Verify user state was updated
                mock_db_setup.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_user_narrative_stats(self, mock_db_setup, bot_mock):
        """Test retrieving narrative statistics for a user."""
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 123456789
        
        # Mock internal methods for stats calculation
        async def _mock_count_accessible_fragments(user_id):
            return 10  # Mock 10 accessible fragments
        
        with patch.object(engine, '_count_accessible_fragments', side_effect=_mock_count_accessible_fragments):
            # Test
            stats = await engine.get_user_narrative_stats(user_id)
            
            # Assertions
            assert stats is not None
            assert "current_fragment" in stats
            assert "fragments_visited" in stats
            assert "total_accessible" in stats
            assert "progress_percentage" in stats
            assert "choices_made" in stats
            
            # Verify the stats values
            assert stats["total_accessible"] == 10
            assert stats["progress_percentage"] <= 100  # Should not exceed 100%
    
    @pytest.mark.asyncio
    async def test_check_access_conditions(self, mock_db_setup, bot_mock, mock_user):
        """Test checking access conditions for a fragment."""
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 123456789
        
        # Create test fragments with different access requirements
        free_fragment = MagicMock(spec=StoryFragment)
        free_fragment.min_besitos = 0
        free_fragment.required_role = None
        
        points_fragment = MagicMock(spec=StoryFragment)
        points_fragment.min_besitos = 200  # More than mock user has
        points_fragment.required_role = None
        
        vip_fragment = MagicMock(spec=StoryFragment)
        vip_fragment.min_besitos = 0
        vip_fragment.required_role = "vip"
        
        # Mock the session.get to return our mock user
        mock_db_setup.get.return_value = mock_user
        
        # Mock user_role function
        async def mock_get_user_role(bot, user_id, session=None):
            return "free"  # Mock user is not VIP
        
        with patch("utils.user_roles.get_user_role", mock_get_user_role):
            # Test
            free_access = await engine._check_access_conditions(user_id, free_fragment)
            points_access = await engine._check_access_conditions(user_id, points_fragment)
            vip_access = await engine._check_access_conditions(user_id, vip_fragment)
            
            # Assertions
            assert free_access is True  # Should have access to free fragment
            assert points_access is False  # Not enough points
            assert vip_access is False  # Not a VIP user
    
    @pytest.mark.asyncio
    async def test_process_fragment_rewards(self, mock_db_setup, bot_mock):
        """Test processing rewards from a fragment."""
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 123456789
        
        # Create a fragment with rewards
        reward_fragment = MagicMock(spec=StoryFragment)
        reward_fragment.reward_besitos = 25
        reward_fragment.key = "reward_test"
        reward_fragment.unlocks_achievement_id = None
        
        # Mock point service
        point_service_mock = MagicMock()
        point_service_mock.add_points = AsyncMock(return_value={"success": True})
        engine.point_service = point_service_mock
        
        # Test
        await engine._process_fragment_rewards(user_id, reward_fragment)
        
        # Assertions - verify points were awarded
        point_service_mock.add_points.assert_called_once_with(
            user_id, 25, bot=bot_mock
        )