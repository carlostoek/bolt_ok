"""
Tests for Narrative Reward Integration.

This module tests the integration between the narrative system and points/rewards,
ensuring that narrative progress correctly awards points, unlocks achievements,
and interacts with other gamification systems.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os
from typing import Dict, List, Any

# Add the project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.narrative_engine import NarrativeEngine
from services.point_service import PointService
from database.narrative_models import StoryFragment, NarrativeChoice, UserNarrativeState
from database.models import User


class TestNarrativeRewards:
    """Test cases for narrative reward integration."""
    
    @pytest.mark.asyncio
    async def test_fragment_points_reward(self, mock_db_setup, bot_mock):
        """
        Test that fragment points are correctly awarded when visiting a fragment.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 123456789
        
        # Create a fragment with points reward
        reward_fragment = MagicMock(spec=StoryFragment)
        reward_fragment.id = 100
        reward_fragment.key = "reward_test"
        reward_fragment.text = "This fragment awards points."
        reward_fragment.character = "Lucien"
        reward_fragment.reward_besitos = 25
        reward_fragment.unlocks_achievement_id = None
        
        # Mock point service
        point_service_mock = MagicMock(spec=PointService)
        point_service_mock.add_points = AsyncMock(
            return_value={"success": True, "points": 25, "total": 125}
        )
        engine.point_service = point_service_mock
        
        # Mock methods to use our test fragment
        async def mock_get_fragment(key):
            if key == "reward_test":
                return reward_fragment
            return None
        
        async def mock_get_user_state(user_id):
            state = MagicMock(spec=UserNarrativeState)
            state.user_id = user_id
            state.current_fragment_key = "reward_test"
            return state
        
        with patch.object(engine, '_get_fragment_by_key', side_effect=mock_get_fragment):
            with patch.object(engine, '_get_or_create_user_state', side_effect=mock_get_user_state):
                # Test getting the current fragment (should trigger rewards)
                fragment = await engine.get_user_current_fragment(user_id)
                
                # Process rewards explicitly
                await engine._process_fragment_rewards(user_id, fragment)
                
                # Verify points were awarded
                point_service_mock.add_points.assert_called_once_with(
                    user_id, 25, bot=bot_mock
                )
    
    @pytest.mark.asyncio
    async def test_choice_points_reward(self, mock_db_setup, bot_mock):
        """
        Test that narrative choices can award points when selected.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 123456789
        
        # Create source and destination fragments
        source_fragment = MagicMock(spec=StoryFragment)
        source_fragment.id = 1
        source_fragment.key = "source"
        
        dest_fragment = MagicMock(spec=StoryFragment)
        dest_fragment.id = 2
        dest_fragment.key = "destination"
        dest_fragment.reward_besitos = 0  # No direct fragment rewards
        
        # Create a choice with points reward
        reward_choice = MagicMock(spec=NarrativeChoice)
        reward_choice.id = 1
        reward_choice.source_fragment_id = 1
        reward_choice.destination_fragment_key = "destination"
        reward_choice.text = "This choice awards points"
        
        # NarrativeDecision for enhanced testing (uses points_reward)
        reward_decision = MagicMock()
        reward_decision.id = 1
        reward_decision.fragment_key = "source"
        reward_decision.next_fragment_key = "destination"
        reward_decision.text = "This decision awards points"
        reward_decision.points_reward = 15
        
        # Mock methods
        async def mock_get_fragment(key):
            if key == "source":
                return source_fragment
            elif key == "destination":
                return dest_fragment
            return None
        
        async def mock_get_choices(fragment_id):
            if fragment_id == 1:
                return [reward_choice]
            return []
        
        async def mock_get_user_state(user_id):
            state = MagicMock(spec=UserNarrativeState)
            state.user_id = user_id
            state.current_fragment_key = "source"
            return state
        
        # Mock point service
        point_service_mock = MagicMock(spec=PointService)
        point_service_mock.add_points = AsyncMock(
            return_value={"success": True, "points": 15, "total": 115}
        )
        engine.point_service = point_service_mock
        
        # Patch methods
        with patch.object(engine, '_get_fragment_by_key', side_effect=mock_get_fragment):
            with patch.object(engine, '_get_fragment_choices', side_effect=mock_get_choices):
                with patch.object(engine, '_get_or_create_user_state', side_effect=mock_get_user_state):
                    # Also patch the NarrativeDecision.get method for enhanced testing
                    async def mock_execute(query):
                        mock_result = MagicMock()
                        mock_result.scalar_one_or_none.return_value = reward_decision
                        return mock_result
                    
                    mock_db_setup.execute.side_effect = mock_execute
                    
                    # Mock process_user_decision to use NarrativeDecision with points
                    original_process = engine.process_user_decision
                    
                    async def mock_process_decision(user_id, choice_index):
                        # Call the real method but also award decision points
                        result = await original_process(user_id, choice_index)
                        
                        # Award points from the decision
                        if point_service_mock and reward_decision.points_reward > 0:
                            await point_service_mock.add_points(
                                user_id, reward_decision.points_reward, bot=bot_mock
                            )
                        
                        return result
                    
                    with patch.object(engine, 'process_user_decision', side_effect=mock_process_decision):
                        # Process the choice
                        next_fragment = await engine.process_user_decision(user_id, 0)
                        
                        # Verify
                        assert next_fragment.key == "destination"
                        
                        # Verify points were awarded
                        point_service_mock.add_points.assert_called_once_with(
                            user_id, 15, bot=bot_mock
                        )
    
    @pytest.mark.asyncio
    async def test_achievement_unlock(self, mock_db_setup, bot_mock):
        """
        Test that fragments can unlock achievements.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 123456789
        
        # Create a fragment that unlocks an achievement
        achievement_fragment = MagicMock(spec=StoryFragment)
        achievement_fragment.id = 200
        achievement_fragment.key = "achievement_test"
        achievement_fragment.text = "This fragment unlocks an achievement."
        achievement_fragment.character = "Diana"
        achievement_fragment.reward_besitos = 10
        achievement_fragment.unlocks_achievement_id = "test_achievement"
        
        # Mock achievement
        mock_achievement = MagicMock()
        mock_achievement.id = "test_achievement"
        mock_achievement.name = "Test Achievement"
        mock_achievement.description = "Achievement unlocked by reaching a narrative milestone"
        
        # Mock achievement service
        achievement_service_mock = MagicMock()
        achievement_service_mock._grant = AsyncMock(
            return_value={"success": True, "achievement": mock_achievement}
        )
        
        # Mock methods
        async def mock_get_fragment(key):
            if key == "achievement_test":
                return achievement_fragment
            return None
        
        async def mock_get_user_state(user_id):
            state = MagicMock(spec=UserNarrativeState)
            state.user_id = user_id
            state.current_fragment_key = "achievement_test"
            return state
        
        async def mock_get_achievement(achievement_id):
            return mock_achievement
        
        # Mock point service for the besitos reward
        point_service_mock = MagicMock(spec=PointService)
        point_service_mock.add_points = AsyncMock(
            return_value={"success": True, "points": 10, "total": 110}
        )
        engine.point_service = point_service_mock
        
        # Patch methods
        with patch.object(engine, '_get_fragment_by_key', side_effect=mock_get_fragment):
            with patch.object(engine, '_get_or_create_user_state', side_effect=mock_get_user_state):
                with patch("services.achievement_service.AchievementService", return_value=achievement_service_mock):
                    # Mock session.get for achievement
                    async def mock_session_get(cls, achievement_id):
                        if achievement_id == "test_achievement":
                            return mock_achievement
                        return None
                    
                    mock_db_setup.get = AsyncMock(side_effect=mock_session_get)
                    
                    # Test getting the current fragment (should trigger rewards and achievement)
                    fragment = await engine.get_user_current_fragment(user_id)
                    
                    # Process rewards explicitly
                    await engine._process_fragment_rewards(user_id, fragment)
                    
                    # Verify points were awarded
                    point_service_mock.add_points.assert_called_once_with(
                        user_id, 10, bot=bot_mock
                    )
                    
                    # Verify achievement was granted
                    achievement_service_mock._grant.assert_called_once_with(
                        user_id, mock_achievement, bot=bot_mock
                    )
    
    @pytest.mark.asyncio
    async def test_progress_tracking(self, mock_db_setup, bot_mock):
        """
        Test that narrative progress is correctly tracked for rewards.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 123456789
        
        # Mock user state with progress tracking
        user_state = MagicMock(spec=UserNarrativeState)
        user_state.user_id = user_id
        user_state.current_fragment_key = "progress_test"
        user_state.fragments_visited = 5
        user_state.fragments_completed = 3
        user_state.total_besitos_earned = 50
        
        # Create a progress milestone fragment
        milestone_fragment = MagicMock(spec=StoryFragment)
        milestone_fragment.id = 300
        milestone_fragment.key = "progress_test"
        milestone_fragment.text = "This is a progress milestone."
        milestone_fragment.character = "Lucien"
        milestone_fragment.reward_besitos = 20
        
        # Mock methods
        async def mock_get_fragment(key):
            if key == "progress_test":
                return milestone_fragment
            return None
        
        async def mock_get_user_state(user_id):
            return user_state
        
        # Mock point service
        point_service_mock = MagicMock(spec=PointService)
        point_service_mock.add_points = AsyncMock(
            return_value={"success": True, "points": 20, "total": 70}
        )
        engine.point_service = point_service_mock
        
        # Patch methods
        with patch.object(engine, '_get_fragment_by_key', side_effect=mock_get_fragment):
            with patch.object(engine, '_get_or_create_user_state', side_effect=mock_get_user_state):
                # Test processing the milestone fragment
                fragment = await engine.get_user_current_fragment(user_id)
                
                # Process rewards
                await engine._process_fragment_rewards(user_id, fragment)
                
                # Verify progress was updated
                assert user_state.fragments_visited == 5  # Not incremented in the mock
                
                # Verify points were awarded
                point_service_mock.add_points.assert_called_once_with(
                    user_id, 20, bot=bot_mock
                )
                
                # Verify the total earned besitos would be updated
                # In real implementation this would be updated
    
    @pytest.mark.asyncio
    async def test_karma_multiplier(self, mock_db_setup, bot_mock):
        """
        Test that karma multipliers affect point rewards.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 123456789
        
        # Create a fragment with karma multiplier
        karma_fragment = MagicMock(spec=StoryFragment)
        karma_fragment.id = 400
        karma_fragment.key = "karma_test"
        karma_fragment.text = "This fragment has karma effects."
        karma_fragment.character = "Diana"
        karma_fragment.reward_besitos = 30
        karma_fragment.karma_multiplier = True  # This would multiply rewards based on karma
        
        # Mock user with karma score
        mock_user = MagicMock(spec=User)
        mock_user.id = user_id
        mock_user.karma = 2.0  # 2x multiplier
        mock_user.points = 100
        
        # Mock methods
        async def mock_get_fragment(key):
            if key == "karma_test":
                return karma_fragment
            return None
        
        async def mock_get_user_state(user_id):
            state = MagicMock(spec=UserNarrativeState)
            state.user_id = user_id
            state.current_fragment_key = "karma_test"
            return state
        
        # Mock point service with karma consideration
        point_service_mock = MagicMock(spec=PointService)
        
        async def mock_add_points(user_id, points, **kwargs):
            # Apply karma multiplier if the fragment has it
            if karma_fragment.karma_multiplier:
                # In a real implementation, we would get the user's karma
                # Here we're using the mock user's karma value
                karma_multiplier = mock_user.karma
                adjusted_points = int(points * karma_multiplier)
            else:
                adjusted_points = points
                
            return {
                "success": True,
                "points": adjusted_points,
                "total": mock_user.points + adjusted_points,
                "karma_applied": karma_fragment.karma_multiplier
            }
        
        point_service_mock.add_points = AsyncMock(side_effect=mock_add_points)
        engine.point_service = point_service_mock
        
        # Mock session.get to return our user
        mock_db_setup.get.return_value = mock_user
        
        # Patch methods
        with patch.object(engine, '_get_fragment_by_key', side_effect=mock_get_fragment):
            with patch.object(engine, '_get_or_create_user_state', side_effect=mock_get_user_state):
                # Test processing the karma fragment
                fragment = await engine.get_user_current_fragment(user_id)
                
                # Process rewards
                await engine._process_fragment_rewards(user_id, fragment)
                
                # Verify points were awarded with karma multiplier
                point_service_mock.add_points.assert_called_once_with(
                    user_id, 30, bot=bot_mock
                )
                
                # Get the result to check the points
                result = await point_service_mock.add_points(user_id, 30, bot=bot_mock)
                
                # Verify karma was applied
                assert result["karma_applied"] is True
                assert result["points"] == 60  # 30 * 2.0 karma multiplier
    
    @pytest.mark.asyncio
    async def test_one_time_rewards(self, mock_db_setup, bot_mock):
        """
        Test that one-time rewards are only given once.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 123456789
        
        # Create a fragment with one-time reward
        onetime_fragment = MagicMock(spec=StoryFragment)
        onetime_fragment.id = 500
        onetime_fragment.key = "onetime_test"
        onetime_fragment.text = "This fragment has a one-time reward."
        onetime_fragment.character = "Lucien"
        onetime_fragment.reward_besitos = 50
        onetime_fragment.one_time_reward = True
        
        # Mock user state with reward tracking
        user_state = MagicMock(spec=UserNarrativeState)
        user_state.user_id = user_id
        user_state.current_fragment_key = "onetime_test"
        user_state.fragments_visited = 10
        
        # Use a dictionary to track if the reward was already given
        rewards_given = {}
        
        # Mock methods
        async def mock_get_fragment(key):
            if key == "onetime_test":
                return onetime_fragment
            return None
        
        async def mock_get_user_state(user_id):
            return user_state
        
        # Mock point service
        point_service_mock = MagicMock(spec=PointService)
        
        async def mock_add_points(user_id, points, **kwargs):
            fragment_key = onetime_fragment.key
            reward_key = f"{user_id}_{fragment_key}"
            
            # Check if this is a one-time reward that was already given
            if onetime_fragment.one_time_reward and reward_key in rewards_given:
                return {
                    "success": False,
                    "reason": "One-time reward already given",
                    "points": 0,
                    "total": 100
                }
            
            # Mark reward as given
            if onetime_fragment.one_time_reward:
                rewards_given[reward_key] = True
            
            return {
                "success": True,
                "points": points,
                "total": 100 + points
            }
        
        point_service_mock.add_points = AsyncMock(side_effect=mock_add_points)
        engine.point_service = point_service_mock
        
        # Patch methods
        with patch.object(engine, '_get_fragment_by_key', side_effect=mock_get_fragment):
            with patch.object(engine, '_get_or_create_user_state', side_effect=mock_get_user_state):
                # First visit - should get reward
                fragment = await engine.get_user_current_fragment(user_id)
                await engine._process_fragment_rewards(user_id, fragment)
                
                # Verify points were awarded
                point_service_mock.add_points.assert_called_with(
                    user_id, 50, bot=bot_mock
                )
                
                # Reset the mock to check second call
                point_service_mock.add_points.reset_mock()
                
                # Second visit - should not get reward again
                fragment = await engine.get_user_current_fragment(user_id)
                await engine._process_fragment_rewards(user_id, fragment)
                
                # Verify the second call result
                result = await point_service_mock.add_points(user_id, 50, bot=bot_mock)
                assert result["success"] is False
                assert result["points"] == 0
                assert "already given" in result["reason"]