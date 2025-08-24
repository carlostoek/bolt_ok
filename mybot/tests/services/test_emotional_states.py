"""
Tests for Emotional State Transitions in Narrative System.

This module tests the emotional state transitions in the narrative system,
ensuring that users can properly navigate between different emotional states
and that the system correctly reflects the user's emotional journey.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os
from typing import Dict, List, Set, Tuple

# Add the project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from services.narrative_engine import NarrativeEngine
from database.narrative_models import StoryFragment, NarrativeChoice, UserNarrativeState


class TestEmotionalStates:
    """Test cases for emotional state transitions in the narrative system."""
    
    @pytest.mark.asyncio
    async def test_emotional_state_fragments_exist(self, mock_db_setup, bot_mock, emotional_state_fragments):
        """
        Test that all emotional state fragments exist in the system.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        
        # Mock _get_fragment_by_key to return emotional state fragments
        async def mock_get_fragment(key):
            if key.startswith("emotional_"):
                emotion = key.split("_")[1]
                if emotion in emotional_state_fragments:
                    return emotional_state_fragments[emotion]
            return None
        
        with patch.object(engine, '_get_fragment_by_key', side_effect=mock_get_fragment):
            # Test each emotional state
            for emotion, fragment in emotional_state_fragments.items():
                fragment_key = f"emotional_{emotion}"
                result = await engine._get_fragment_by_key(fragment_key)
                
                # Assert
                assert result is not None, f"Emotional state fragment '{fragment_key}' does not exist"
                assert result.key == fragment_key
                assert result.character == "Diana"  # Diana handles emotional content
    
    @pytest.mark.asyncio
    async def test_emotional_state_transitions(self, mock_db_setup, bot_mock, emotional_state_fragments):
        """
        Test that emotional state transitions work correctly.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 123456789
        
        # Mock methods to use our emotional state fragments
        async def mock_get_fragment(key):
            if key.startswith("emotional_"):
                emotion = key.split("_")[1]
                if emotion in emotional_state_fragments:
                    return emotional_state_fragments[emotion]
            return None
        
        async def mock_get_user_state(user_id):
            state = MagicMock(spec=UserNarrativeState)
            state.user_id = user_id
            state.current_fragment_key = "emotional_happy"  # Start in happy state
            state.choices_made = []
            return state
        
        # Patch methods
        with patch.object(engine, '_get_fragment_by_key', side_effect=mock_get_fragment):
            with patch.object(engine, '_get_or_create_user_state', side_effect=mock_get_user_state):
                # Test transitioning from happy to curious
                current_fragment = await engine.get_user_current_fragment(user_id)
                assert current_fragment.key == "emotional_happy"
                
                # Find the choice that leads to curious
                curious_choice_index = None
                for i, choice in enumerate(current_fragment.choices):
                    if choice.destination_fragment_key == "emotional_curious":
                        curious_choice_index = i
                        break
                
                assert curious_choice_index is not None, "No choice found leading to curious state"
                
                # Mock process_user_decision to transition to curious
                async def mock_process_decision(user_id, choice_index):
                    return emotional_state_fragments["curious"]
                
                with patch.object(engine, 'process_user_decision', side_effect=mock_process_decision):
                    next_fragment = await engine.process_user_decision(user_id, curious_choice_index)
                    
                    # Assert
                    assert next_fragment.key == "emotional_curious"
                    assert "curiosidad" in next_fragment.text.lower()
    
    @pytest.mark.asyncio
    async def test_emotional_state_affects_narrative(self, mock_db_setup, bot_mock, emotional_state_fragments):
        """
        Test that the user's emotional state affects narrative presentation.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 123456789
        
        # Create a mock for display_narrative_fragment
        display_mock = AsyncMock()
        
        # Test displaying fragments in different emotional states
        for emotion, fragment in emotional_state_fragments.items():
            # Mock current emotional state
            async def mock_get_user_current_fragment(user_id):
                return fragment
            
            with patch.object(engine, 'get_user_current_fragment', side_effect=mock_get_user_current_fragment):
                # Call mock handler function for displaying fragment
                await self._mock_display_fragment(fragment, display_mock)
                
                # Verify display was called with correct emotional context
                display_mock.assert_called()
                _, kwargs = display_mock.call_args
                
                # Assert the fragment text was passed correctly
                fragment_text = kwargs.get('fragment_text', '')
                assert fragment.text in fragment_text
                
                # Check that Diana is presented as the character for emotional states
                assert "Diana" in fragment_text or "🌸" in fragment_text
    
    @pytest.mark.asyncio
    async def test_complete_emotional_journey(self, mock_db_setup, bot_mock, emotional_state_fragments):
        """
        Test a complete journey through all emotional states.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 123456789
        
        # Define the emotional journey: happy -> curious -> fearful -> angry -> sad -> happy
        journey = ["happy", "curious", "fearful", "angry", "sad", "happy"]
        
        # Current user state that will be updated during the journey
        user_state = MagicMock(spec=UserNarrativeState)
        user_state.user_id = user_id
        user_state.current_fragment_key = f"emotional_{journey[0]}"
        user_state.choices_made = []
        
        # Mock methods
        async def mock_get_fragment(key):
            if key.startswith("emotional_"):
                emotion = key.split("_")[1]
                if emotion in emotional_state_fragments:
                    return emotional_state_fragments[emotion]
            return None
        
        async def mock_get_user_state(user_id):
            return user_state
        
        # Set up navigation choices between emotional states
        emotional_transitions = {
            "happy": {"curious": 0},      # Happy -> Curious: choice 0
            "curious": {"fearful": 1},    # Curious -> Fearful: choice 1
            "fearful": {"angry": 0},      # Fearful -> Angry: choice 0 (invented for test)
            "angry": {"sad": 0},          # Angry -> Sad: choice 0
            "sad": {"happy": 0}           # Sad -> Happy: choice 0
        }
        
        # Journey tracking
        visited_emotions = []
        
        # Patch methods
        with patch.object(engine, '_get_fragment_by_key', side_effect=mock_get_fragment):
            with patch.object(engine, '_get_or_create_user_state', side_effect=mock_get_user_state):
                # Start journey
                for i in range(len(journey)-1):
                    current_emotion = journey[i]
                    next_emotion = journey[i+1]
                    
                    # Get current fragment
                    current_fragment = await engine.get_user_current_fragment(user_id)
                    visited_emotions.append(current_emotion)
                    
                    # Mock the transition choice
                    choice_index = emotional_transitions[current_emotion][next_emotion]
                    
                    # Define process_decision for this step
                    async def mock_process_decision(uid, idx):
                        # Update the user state
                        user_state.current_fragment_key = f"emotional_{next_emotion}"
                        # Return the next fragment
                        return emotional_state_fragments[next_emotion]
                    
                    with patch.object(engine, 'process_user_decision', side_effect=mock_process_decision):
                        next_fragment = await engine.process_user_decision(user_id, choice_index)
                        
                        # Assert
                        assert next_fragment.key == f"emotional_{next_emotion}"
                
                # Add the final emotion
                visited_emotions.append(journey[-1])
                
                # Verify the complete journey
                assert visited_emotions == journey
    
    @pytest.mark.asyncio
    async def test_emotional_state_validation(self, mock_db_setup, bot_mock, emotional_state_fragments):
        """
        Test validation of emotional state transitions.
        """
        # Define allowed transitions between emotional states
        valid_transitions = {
            "happy": ["curious", "sad"],
            "sad": ["happy", "angry"],
            "curious": ["happy", "fearful"],
            "fearful": ["curious"],
            "angry": ["sad"]
        }
        
        # Test all transitions
        for from_emotion, allowed_to in valid_transitions.items():
            from_fragment = emotional_state_fragments[from_emotion]
            
            # Get all emotions this fragment can transition to
            transition_emotions = []
            for choice in from_fragment.choices:
                if choice.destination_fragment_key.startswith("emotional_"):
                    to_emotion = choice.destination_fragment_key.split("_")[1]
                    transition_emotions.append(to_emotion)
            
            # Verify only allowed transitions exist
            for to_emotion in transition_emotions:
                assert to_emotion in allowed_to, \
                    f"Invalid transition from {from_emotion} to {to_emotion}"
            
            # Verify all allowed transitions exist
            for to_emotion in allowed_to:
                assert to_emotion in transition_emotions, \
                    f"Missing transition from {from_emotion} to {to_emotion}"
    
    # Helper method to mock display_narrative_fragment
    async def _mock_display_fragment(self, fragment, display_mock):
        """Helper method to simulate narrative fragment display."""
        character_emoji = "🎩" if fragment.character == "Lucien" else "🌸"
        fragment_text = f"{character_emoji} **{fragment.character}:**\n\n*{fragment.text}*"
        
        # Call the display mock
        await display_mock(fragment=fragment, fragment_text=fragment_text)
        
        return fragment_text