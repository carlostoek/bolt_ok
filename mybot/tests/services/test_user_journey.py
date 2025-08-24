"""
Tests for User Journey Flows.

This module tests complete user journeys through the narrative system,
simulating various user paths from registration to advanced content.
It ensures that the entire narrative experience works correctly for
different user types.
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
from services.point_service import PointService
from database.narrative_models import StoryFragment, NarrativeChoice, UserNarrativeState
from database.models import User


class TestUserJourney:
    """Test cases for complete user journeys through the narrative system."""
    
    @pytest.mark.asyncio
    async def test_new_user_onboarding_journey(self, mock_db_setup, bot_mock):
        """
        Test the complete onboarding journey for a new user.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 123456789
        
        # Mock a new user
        new_user = MagicMock(spec=User)
        new_user.id = user_id
        new_user.username = "new_user"
        new_user.points = 0
        new_user.is_vip = False
        
        # Define the onboarding journey fragments
        onboarding_fragments = {
            "start": MagicMock(spec=StoryFragment, 
                              key="start",
                              text="Bienvenido a la mansión. ¿Qué deseas hacer?",
                              character="Lucien",
                              reward_besitos=5),
            "tutorial": MagicMock(spec=StoryFragment,
                                 key="tutorial",
                                 text="Este es un tutorial sobre cómo funciona el sistema.",
                                 character="Lucien",
                                 reward_besitos=5),
            "first_choice": MagicMock(spec=StoryFragment,
                                    key="first_choice",
                                    text="Tu primera decisión importante.",
                                    character="Lucien",
                                    reward_besitos=10),
            "conclusion": MagicMock(spec=StoryFragment,
                                   key="conclusion",
                                   text="Has completado la introducción.",
                                   character="Diana",
                                   reward_besitos=15)
        }
        
        # Define choices for each fragment
        onboarding_choices = {
            "start": [
                MagicMock(spec=NarrativeChoice,
                        id=1,
                        source_fragment_id=1,
                        destination_fragment_key="tutorial",
                        text="Aprender cómo funciona")
            ],
            "tutorial": [
                MagicMock(spec=NarrativeChoice,
                        id=2,
                        source_fragment_id=2,
                        destination_fragment_key="first_choice",
                        text="Continuar")
            ],
            "first_choice": [
                MagicMock(spec=NarrativeChoice,
                        id=3,
                        source_fragment_id=3,
                        destination_fragment_key="conclusion",
                        text="Opción A"),
                MagicMock(spec=NarrativeChoice,
                        id=4,
                        source_fragment_id=3,
                        destination_fragment_key="conclusion",
                        text="Opción B")
            ]
        }
        
        # Add choices to fragments
        for key, fragment in onboarding_fragments.items():
            fragment.choices = onboarding_choices.get(key, [])
        
        # User state that will be updated
        user_state = MagicMock(spec=UserNarrativeState)
        user_state.user_id = user_id
        user_state.current_fragment_key = None
        user_state.choices_made = []
        user_state.fragments_visited = 0
        user_state.total_besitos_earned = 0
        
        # Points accumulator to track points through the journey
        total_points = 0
        
        # Mock methods
        async def mock_get_fragment(key):
            return onboarding_fragments.get(key)
        
        async def mock_get_user_state(user_id):
            return user_state
        
        async def mock_get_choices(fragment_id):
            # Map fragment IDs to keys
            id_to_key = {1: "start", 2: "tutorial", 3: "first_choice", 4: "conclusion"}
            key = id_to_key.get(fragment_id)
            return onboarding_choices.get(key, [])
        
        # Mock point service
        point_service_mock = MagicMock(spec=PointService)
        
        async def mock_add_points(user_id, points, **kwargs):
            nonlocal total_points
            total_points += points
            return {
                "success": True,
                "points": points,
                "total": total_points
            }
        
        point_service_mock.add_points = AsyncMock(side_effect=mock_add_points)
        engine.point_service = point_service_mock
        
        # Journey tracking
        visited_fragments = []
        
        # Patch methods
        with patch.object(engine, '_get_fragment_by_key', side_effect=mock_get_fragment):
            with patch.object(engine, '_get_or_create_user_state', side_effect=mock_get_user_state):
                with patch.object(engine, '_get_fragment_choices', side_effect=mock_get_choices):
                    # Start journey - should create user state and return start fragment
                    start_fragment = await engine.start_narrative(user_id)
                    visited_fragments.append(start_fragment.key)
                    
                    # Process rewards for start fragment
                    await engine._process_fragment_rewards(user_id, start_fragment)
                    
                    # Update user state
                    user_state.current_fragment_key = start_fragment.key
                    user_state.fragments_visited += 1
                    
                    # Follow the tutorial
                    next_fragment = await engine.process_user_decision(user_id, 0)
                    visited_fragments.append(next_fragment.key)
                    
                    # Update user state
                    user_state.current_fragment_key = next_fragment.key
                    user_state.fragments_visited += 1
                    
                    # Process tutorial rewards
                    await engine._process_fragment_rewards(user_id, next_fragment)
                    
                    # Continue to first choice
                    next_fragment = await engine.process_user_decision(user_id, 0)
                    visited_fragments.append(next_fragment.key)
                    
                    # Update user state
                    user_state.current_fragment_key = next_fragment.key
                    user_state.fragments_visited += 1
                    
                    # Process first choice rewards
                    await engine._process_fragment_rewards(user_id, next_fragment)
                    
                    # Make first important choice (choose option A)
                    next_fragment = await engine.process_user_decision(user_id, 0)
                    visited_fragments.append(next_fragment.key)
                    
                    # Update user state
                    user_state.current_fragment_key = next_fragment.key
                    user_state.fragments_visited += 1
                    
                    # Process conclusion rewards
                    await engine._process_fragment_rewards(user_id, next_fragment)
                    
                    # Verify the journey
                    assert visited_fragments == ["start", "tutorial", "first_choice", "conclusion"]
                    assert total_points == 35  # Sum of all fragment rewards
                    assert user_state.fragments_visited == 4
    
    @pytest.mark.asyncio
    async def test_vip_content_journey(self, mock_db_setup, bot_mock):
        """
        Test a journey that includes VIP content access.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 987654321  # VIP user ID
        
        # Mock a VIP user
        vip_user = MagicMock(spec=User)
        vip_user.id = user_id
        vip_user.username = "vip_user"
        vip_user.points = 200
        vip_user.is_vip = True
        
        # Define the VIP journey fragments
        vip_fragments = {
            "mansion_entrance": MagicMock(spec=StoryFragment, 
                                        key="mansion_entrance",
                                        text="Estás en la entrada de la mansión.",
                                        character="Lucien",
                                        reward_besitos=0),
            "secret_passage": MagicMock(spec=StoryFragment,
                                       key="secret_passage",
                                       text="Has descubierto un pasaje secreto.",
                                       character="Lucien",
                                       reward_besitos=10,
                                       min_besitos=100),
            "vip_lounge": MagicMock(spec=StoryFragment,
                                   key="vip_lounge",
                                   text="Bienvenido al salón VIP.",
                                   character="Diana",
                                   reward_besitos=20,
                                   required_role="vip"),
            "exclusive_content": MagicMock(spec=StoryFragment,
                                         key="exclusive_content",
                                         text="Este contenido es exclusivo para miembros VIP.",
                                         character="Diana",
                                         reward_besitos=30,
                                         required_role="vip")
        }
        
        # Define choices for each fragment
        vip_choices = {
            "mansion_entrance": [
                MagicMock(spec=NarrativeChoice,
                        id=1,
                        source_fragment_id=1,
                        destination_fragment_key="secret_passage",
                        text="Investigar el muro")
            ],
            "secret_passage": [
                MagicMock(spec=NarrativeChoice,
                        id=2,
                        source_fragment_id=2,
                        destination_fragment_key="vip_lounge",
                        text="Continuar por el pasaje",
                        required_role="vip")
            ],
            "vip_lounge": [
                MagicMock(spec=NarrativeChoice,
                        id=3,
                        source_fragment_id=3,
                        destination_fragment_key="exclusive_content",
                        text="Explorar contenido exclusivo",
                        required_role="vip")
            ]
        }
        
        # Add choices to fragments
        for key, fragment in vip_fragments.items():
            fragment.choices = vip_choices.get(key, [])
        
        # User state that will be updated
        user_state = MagicMock(spec=UserNarrativeState)
        user_state.user_id = user_id
        user_state.current_fragment_key = "mansion_entrance"
        user_state.choices_made = []
        user_state.fragments_visited = 1
        user_state.total_besitos_earned = 0
        
        # Points accumulator
        total_points = 200  # Starting points
        
        # Mock methods
        async def mock_get_fragment(key):
            return vip_fragments.get(key)
        
        async def mock_get_user_state(user_id):
            return user_state
        
        async def mock_get_choices(fragment_id):
            # Map fragment IDs to keys
            id_to_key = {1: "mansion_entrance", 2: "secret_passage", 3: "vip_lounge", 4: "exclusive_content"}
            key = id_to_key.get(fragment_id)
            return vip_choices.get(key, [])
        
        # Mock point service
        point_service_mock = MagicMock(spec=PointService)
        
        async def mock_add_points(user_id, points, **kwargs):
            nonlocal total_points
            total_points += points
            return {
                "success": True,
                "points": points,
                "total": total_points
            }
        
        point_service_mock.add_points = AsyncMock(side_effect=mock_add_points)
        engine.point_service = point_service_mock
        
        # Mock user role check
        async def mock_get_user_role(bot, user_id, session=None):
            return "vip"  # User is VIP
        
        # Mock session.get to return our VIP user
        mock_db_setup.get.return_value = vip_user
        
        # Journey tracking
        visited_fragments = ["mansion_entrance"]  # Already at mansion entrance
        
        # Patch methods
        with patch.object(engine, '_get_fragment_by_key', side_effect=mock_get_fragment):
            with patch.object(engine, '_get_or_create_user_state', side_effect=mock_get_user_state):
                with patch.object(engine, '_get_fragment_choices', side_effect=mock_get_choices):
                    with patch("utils.user_roles.get_user_role", mock_get_user_role):
                        # Get current fragment
                        current_fragment = await engine.get_user_current_fragment(user_id)
                        assert current_fragment.key == "mansion_entrance"
                        
                        # Discover secret passage
                        next_fragment = await engine.process_user_decision(user_id, 0)
                        visited_fragments.append(next_fragment.key)
                        
                        # Update user state
                        user_state.current_fragment_key = next_fragment.key
                        user_state.fragments_visited += 1
                        
                        # Process rewards
                        await engine._process_fragment_rewards(user_id, next_fragment)
                        
                        # Enter VIP lounge
                        next_fragment = await engine.process_user_decision(user_id, 0)
                        visited_fragments.append(next_fragment.key)
                        
                        # Update user state
                        user_state.current_fragment_key = next_fragment.key
                        user_state.fragments_visited += 1
                        
                        # Process rewards
                        await engine._process_fragment_rewards(user_id, next_fragment)
                        
                        # Access exclusive content
                        next_fragment = await engine.process_user_decision(user_id, 0)
                        visited_fragments.append(next_fragment.key)
                        
                        # Update user state
                        user_state.current_fragment_key = next_fragment.key
                        user_state.fragments_visited += 1
                        
                        # Process rewards
                        await engine._process_fragment_rewards(user_id, next_fragment)
                        
                        # Verify the journey
                        assert visited_fragments == ["mansion_entrance", "secret_passage", "vip_lounge", "exclusive_content"]
                        assert total_points == 260  # Starting 200 + 10 + 20 + 30 from fragments
                        assert user_state.fragments_visited == 4
    
    @pytest.mark.asyncio
    async def test_upgrade_to_vip_journey(self, mock_db_setup, bot_mock):
        """
        Test a journey where a free user upgrades to VIP mid-story.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 555777999
        
        # Define the journey fragments
        journey_fragments = {
            "free_content": MagicMock(spec=StoryFragment, 
                                     key="free_content",
                                     text="Este contenido es para todos los usuarios.",
                                     character="Lucien",
                                     reward_besitos=10),
            "teaser": MagicMock(spec=StoryFragment,
                              key="teaser",
                              text="Un vistazo a lo que hay detrás de la puerta VIP.",
                              character="Diana",
                              reward_besitos=5),
            "vip_gate": MagicMock(spec=StoryFragment,
                                key="vip_gate",
                                text="Esta puerta solo se abre para miembros VIP.",
                                character="Diana",
                                reward_besitos=0),
            "vip_area": MagicMock(spec=StoryFragment,
                                key="vip_area",
                                text="¡Bienvenido al área exclusiva!",
                                character="Diana",
                                reward_besitos=50,
                                required_role="vip")
        }
        
        # Define choices for each fragment
        journey_choices = {
            "free_content": [
                MagicMock(spec=NarrativeChoice,
                        id=1,
                        source_fragment_id=1,
                        destination_fragment_key="teaser",
                        text="Continuar")
            ],
            "teaser": [
                MagicMock(spec=NarrativeChoice,
                        id=2,
                        source_fragment_id=2,
                        destination_fragment_key="vip_gate",
                        text="Seguir explorando")
            ],
            "vip_gate": [
                MagicMock(spec=NarrativeChoice,
                        id=3,
                        source_fragment_id=3,
                        destination_fragment_key="vip_area",
                        text="Entrar al área VIP",
                        required_role="vip")
            ]
        }
        
        # Add choices to fragments
        for key, fragment in journey_fragments.items():
            fragment.choices = journey_choices.get(key, [])
        
        # User state that will be updated
        user_state = MagicMock(spec=UserNarrativeState)
        user_state.user_id = user_id
        user_state.current_fragment_key = "free_content"
        user_state.choices_made = []
        user_state.fragments_visited = 1
        user_state.total_besitos_earned = 0
        
        # Mock user that changes from free to VIP
        user = MagicMock(spec=User)
        user.id = user_id
        user.username = "upgrading_user"
        user.points = 100
        user.is_vip = False  # Starts as free
        
        # Mock methods
        async def mock_get_fragment(key):
            return journey_fragments.get(key)
        
        async def mock_get_user_state(user_id):
            return user_state
        
        async def mock_get_choices(fragment_id):
            # Map fragment IDs to keys
            id_to_key = {1: "free_content", 2: "teaser", 3: "vip_gate", 4: "vip_area"}
            key = id_to_key.get(fragment_id)
            return journey_choices.get(key, [])
        
        # Mock user role check that changes mid-test
        user_role_state = {"current": "free"}
        
        async def mock_get_user_role(bot, user_id, session=None):
            return user_role_state["current"]
        
        # Mock session.get to return our user
        mock_db_setup.get.return_value = user
        
        # Journey tracking
        visited_fragments = ["free_content"]  # Already at free content
        
        # Patch methods
        with patch.object(engine, '_get_fragment_by_key', side_effect=mock_get_fragment):
            with patch.object(engine, '_get_or_create_user_state', side_effect=mock_get_user_state):
                with patch.object(engine, '_get_fragment_choices', side_effect=mock_get_choices):
                    with patch("utils.user_roles.get_user_role", mock_get_user_role):
                        # Get current fragment
                        current_fragment = await engine.get_user_current_fragment(user_id)
                        assert current_fragment.key == "free_content"
                        
                        # Continue to teaser
                        next_fragment = await engine.process_user_decision(user_id, 0)
                        visited_fragments.append(next_fragment.key)
                        
                        # Update user state
                        user_state.current_fragment_key = next_fragment.key
                        user_state.fragments_visited += 1
                        
                        # Continue to VIP gate
                        next_fragment = await engine.process_user_decision(user_id, 0)
                        visited_fragments.append(next_fragment.key)
                        
                        # Update user state
                        user_state.current_fragment_key = next_fragment.key
                        user_state.fragments_visited += 1
                        
                        # Try to enter VIP area as free user - should fail
                        with pytest.raises(Exception):  # Should fail due to VIP check
                            await engine.process_user_decision(user_id, 0)
                        
                        # Now upgrade to VIP
                        user.is_vip = True
                        user_role_state["current"] = "vip"
                        
                        # Try again to enter VIP area - should succeed now
                        next_fragment = await engine.process_user_decision(user_id, 0)
                        visited_fragments.append(next_fragment.key)
                        
                        # Update user state
                        user_state.current_fragment_key = next_fragment.key
                        user_state.fragments_visited += 1
                        
                        # Verify the journey
                        assert visited_fragments == ["free_content", "teaser", "vip_gate", "vip_area"]
                        assert user_state.fragments_visited == 4
    
    @pytest.mark.asyncio
    async def test_user_journey_with_handlers(self, mock_db_setup, bot_mock, message_mock, callback_query_mock):
        """
        Test a user journey through the handler functions.
        """
        # Setup engine
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        
        # Mock fragments for the journey
        journey_fragments = {
            "start": MagicMock(spec=StoryFragment, 
                             key="start",
                             text="Bienvenido a la mansión.",
                             character="Lucien",
                             reward_besitos=5),
            "explore": MagicMock(spec=StoryFragment,
                               key="explore",
                               text="Exploras la mansión.",
                               character="Lucien",
                               reward_besitos=10)
        }
        
        # Define choices for each fragment
        journey_choices = {
            "start": [
                MagicMock(spec=NarrativeChoice,
                        id=1,
                        source_fragment_id=1,
                        destination_fragment_key="explore",
                        text="Explorar la mansión")
            ]
        }
        
        # Add choices to fragments
        for key, fragment in journey_fragments.items():
            fragment.choices = journey_choices.get(key, [])
        
        # Import handler functions
        from handlers.narrative_handler import start_narrative_command, handle_narrative_choice
        
        # Mock the NarrativeEngine instantiation in handlers
        original_narrative_engine = __import__('services.narrative_engine').narrative_engine.NarrativeEngine
        
        # Mock _display_narrative_fragment to track calls
        display_calls = []
        
        async def mock_display_fragment(message, fragment, session, is_callback=False):
            display_calls.append({
                "fragment_key": fragment.key,
                "is_callback": is_callback
            })
            
            # Simulate displaying the fragment
            text = f"{fragment.character}: {fragment.text}"
            if is_callback:
                await message.edit_text(text)
            else:
                await message.answer(text)
        
        # Patch methods
        with patch('services.narrative_engine.NarrativeEngine', return_value=engine):
            with patch('handlers.narrative_handler._display_narrative_fragment', side_effect=mock_display_fragment):
                with patch.object(engine, 'get_user_current_fragment', return_value=journey_fragments["start"]):
                    with patch.object(engine, 'start_narrative', return_value=journey_fragments["start"]):
                        # Start the narrative
                        await start_narrative_command(message_mock, mock_db_setup)
                        
                        # Verify the start fragment was displayed
                        assert len(display_calls) == 1
                        assert display_calls[0]["fragment_key"] == "start"
                        assert display_calls[0]["is_callback"] is False
                        
                        # Setup for the next step - choice selection
                        callback_query_mock.data = "narrative_choice:0"  # Select first choice
                        
                        with patch.object(engine, 'process_user_decision', return_value=journey_fragments["explore"]):
                            # Process the choice
                            await handle_narrative_choice(callback_query_mock, mock_db_setup)
                            
                            # Verify the explore fragment was displayed
                            assert len(display_calls) == 2
                            assert display_calls[1]["fragment_key"] == "explore"
                            assert display_calls[1]["is_callback"] is True
                            
                            # Verify message.answer and edit_text were called
                            message_mock.answer.assert_called_once()
                            callback_query_mock.message.edit_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_user_stats_journey(self, mock_db_setup, bot_mock, message_mock):
        """
        Test a journey focusing on narrative statistics.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        user_id = 123456789
        
        # Mock user state with statistics
        user_state = MagicMock(spec=UserNarrativeState)
        user_state.user_id = user_id
        user_state.current_fragment_key = "current_fragment"
        user_state.choices_made = [
            {"fragment_key": "start", "choice_index": 0, "choice_text": "First choice", "timestamp": "2023-01-01T12:00:00"},
            {"fragment_key": "second", "choice_index": 1, "choice_text": "Second choice", "timestamp": "2023-01-01T12:05:00"}
        ]
        user_state.fragments_visited = 10
        user_state.fragments_completed = 8
        user_state.total_besitos_earned = 120
        
        # Mock methods
        async def mock_get_user_state(user_id):
            return user_state
        
        async def mock_count_fragments(user_id):
            return 20  # Total accessible fragments
        
        # Mock the get_user_narrative_stats method
        async def mock_get_stats(user_id):
            return {
                "current_fragment": "current_fragment",
                "fragments_visited": 10,
                "total_accessible": 20,
                "progress_percentage": 50.0,
                "choices_made": user_state.choices_made
            }
        
        # Import handler function for stats
        from handlers.narrative_handler import show_narrative_stats
        
        # Patch methods
        with patch('services.narrative_engine.NarrativeEngine', return_value=engine):
            with patch.object(engine, '_get_or_create_user_state', side_effect=mock_get_user_state):
                with patch.object(engine, '_count_accessible_fragments', side_effect=mock_count_fragments):
                    with patch.object(engine, 'get_user_narrative_stats', side_effect=mock_get_stats):
                        # Get narrative stats
                        await show_narrative_stats(message_mock, mock_db_setup)
                        
                        # Verify the stats were displayed
                        message_mock.answer.assert_called_once()
                        
                        # Verify stats content
                        call_args = message_mock.answer.call_args[0][0]
                        assert "Tu Historia Personal" in call_args
                        assert "Progreso: 50.0%" in call_args
                        assert "Fragmentos Visitados: 10" in call_args
                        assert "Total Accesible: 20" in call_args
                        assert "Decisiones Tomadas: 2" in call_args