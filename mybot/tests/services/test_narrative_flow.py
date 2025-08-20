"""
Tests for Narrative Flow Validation.

This module tests the integrity of narrative flows, ensuring that all story paths
are navigable, choices lead to valid destinations, and there are no dead-ends.
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
from database.narrative_models import StoryFragment, NarrativeChoice


class TestNarrativeFlow:
    """Test cases for narrative flow validation."""
    
    @pytest.mark.asyncio
    async def test_fragment_continuity(self, mock_db_setup, bot_mock):
        """
        Test that every fragment has valid continuation paths.
        A fragment should either have choices or an auto-next fragment.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        
        # Get all fragments
        fragments = []
        result = await mock_db_setup.execute(MagicMock())
        fragments = result.scalars().all()
        
        # Test each fragment
        for fragment in fragments:
            # Skip fragments that are known end points
            if fragment.key.startswith("end_"):
                continue
                
            # Get choices for this fragment
            choices = []
            with patch.object(engine, '_get_fragment_choices') as mock_get_choices:
                # Setup the mock to return choices for this fragment
                async def mock_get_choices_impl(fragment_id):
                    choices = []
                    for choice in mock_db_setup.execute.return_value.scalars().all():
                        if choice.source_fragment_id == fragment.id:
                            choices.append(choice)
                    return choices
                
                mock_get_choices.side_effect = mock_get_choices_impl
                choices = await engine._get_fragment_choices(fragment.id)
            
            # Assert fragment has valid continuation
            has_continuation = len(choices) > 0 or fragment.auto_next_fragment_key is not None
            assert has_continuation, f"Fragment '{fragment.key}' has no continuation path"
            
            # If no choices, must have auto-next
            if len(choices) == 0:
                assert fragment.auto_next_fragment_key is not None, \
                    f"Fragment '{fragment.key}' has no choices and no auto-next"
    
    @pytest.mark.asyncio
    async def test_choice_destinations_exist(self, mock_db_setup, bot_mock):
        """
        Test that all choice destinations point to existing fragments.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        
        # Get all fragments and create a set of valid keys
        result = await mock_db_setup.execute(MagicMock())
        fragments = result.scalars().all()
        valid_keys = {fragment.key for fragment in fragments}
        
        # Get all choices
        choices = []
        for fragment in fragments:
            with patch.object(engine, '_get_fragment_choices') as mock_get_choices:
                # Setup the mock to return choices for this fragment
                async def mock_get_choices_impl(fragment_id):
                    choices = []
                    for choice in mock_db_setup.execute.return_value.scalars().all():
                        if choice.source_fragment_id == fragment.id:
                            choices.append(choice)
                    return choices
                
                mock_get_choices.side_effect = mock_get_choices_impl
                fragment_choices = await engine._get_fragment_choices(fragment.id)
                choices.extend(fragment_choices)
        
        # Test each choice destination
        for choice in choices:
            destination_key = choice.destination_fragment_key
            assert destination_key in valid_keys, \
                f"Choice destination '{destination_key}' does not exist in fragments"
    
    @pytest.mark.asyncio
    async def test_auto_next_destinations_exist(self, mock_db_setup, bot_mock):
        """
        Test that all auto-next destinations point to existing fragments.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        
        # Get all fragments and create a set of valid keys
        result = await mock_db_setup.execute(MagicMock())
        fragments = result.scalars().all()
        valid_keys = {fragment.key for fragment in fragments}
        
        # Test each fragment's auto-next
        for fragment in fragments:
            if fragment.auto_next_fragment_key:
                assert fragment.auto_next_fragment_key in valid_keys, \
                    f"Auto-next destination '{fragment.auto_next_fragment_key}' for fragment '{fragment.key}' does not exist"
    
    @pytest.mark.asyncio
    async def test_no_unreachable_fragments(self, mock_db_setup, bot_mock):
        """
        Test that all fragments are reachable from the start.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        
        # Get all fragments
        result = await mock_db_setup.execute(MagicMock())
        fragments = result.scalars().all()
        fragment_dict = {fragment.key: fragment for fragment in fragments}
        
        # Build a directed graph of fragment connections
        graph = {}
        for fragment in fragments:
            connections = []
            
            # Add connections from choices
            with patch.object(engine, '_get_fragment_choices') as mock_get_choices:
                # Setup the mock to return choices for this fragment
                async def mock_get_choices_impl(fragment_id):
                    choices = []
                    for choice in mock_db_setup.execute.return_value.scalars().all():
                        if choice.source_fragment_id == fragment.id:
                            choices.append(choice)
                    return choices
                
                mock_get_choices.side_effect = mock_get_choices_impl
                choices = await engine._get_fragment_choices(fragment.id)
                
                for choice in choices:
                    connections.append(choice.destination_fragment_key)
            
            # Add auto-next connection
            if fragment.auto_next_fragment_key:
                connections.append(fragment.auto_next_fragment_key)
            
            graph[fragment.key] = connections
        
        # Perform BFS from 'start' to find all reachable fragments
        start_key = "start"
        visited = set()
        queue = [start_key]
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
                
            visited.add(current)
            
            for neighbor in graph.get(current, []):
                if neighbor not in visited:
                    queue.append(neighbor)
        
        # Check if all fragments are reachable
        unreachable = set(fragment_dict.keys()) - visited
        assert len(unreachable) == 0, f"Unreachable fragments: {unreachable}"
    
    @pytest.mark.asyncio
    async def test_no_cycles_without_progression(self, mock_db_setup, bot_mock):
        """
        Test that there are no cycles in the narrative that don't contribute to progression.
        Simple cycles are allowed only if they involve fragments with rewards or progression.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        
        # Get all fragments
        result = await mock_db_setup.execute(MagicMock())
        fragments = result.scalars().all()
        fragment_dict = {fragment.key: fragment for fragment in fragments}
        
        # Build a directed graph of fragment connections
        graph = {}
        for fragment in fragments:
            connections = []
            
            # Add connections from choices
            with patch.object(engine, '_get_fragment_choices') as mock_get_choices:
                # Setup the mock to return choices for this fragment
                async def mock_get_choices_impl(fragment_id):
                    choices = []
                    for choice in mock_db_setup.execute.return_value.scalars().all():
                        if choice.source_fragment_id == fragment.id:
                            choices.append(choice)
                    return choices
                
                mock_get_choices.side_effect = mock_get_choices_impl
                choices = await engine._get_fragment_choices(fragment.id)
                
                for choice in choices:
                    connections.append(choice.destination_fragment_key)
            
            # Add auto-next connection
            if fragment.auto_next_fragment_key:
                connections.append(fragment.auto_next_fragment_key)
            
            graph[fragment.key] = connections
        
        # Helper function to check if a cycle has progression
        def has_progression(cycle):
            # Check if any fragment in the cycle has rewards
            for fragment_key in cycle:
                fragment = fragment_dict[fragment_key]
                if fragment.reward_besitos > 0 or fragment.unlocks_achievement_id:
                    return True
            return False
        
        # DFS to detect cycles
        def detect_cycles(start_key):
            visited = set()
            path = []
            cycles_found = []
            
            def dfs(node):
                if node in path:
                    # Found cycle, check if it has progression
                    cycle_start = path.index(node)
                    cycle = path[cycle_start:]
                    if not has_progression(cycle):
                        cycles_found.append(cycle)
                    return
                
                if node in visited:
                    return
                    
                visited.add(node)
                path.append(node)
                
                for neighbor in graph.get(node, []):
                    dfs(neighbor)
                
                path.pop()
            
            dfs(start_key)
            return cycles_found
        
        # Check for non-progression cycles starting from each fragment
        bad_cycles = []
        for fragment_key in fragment_dict.keys():
            cycles = detect_cycles(fragment_key)
            bad_cycles.extend(cycles)
        
        # Assert no non-progression cycles
        assert len(bad_cycles) == 0, f"Found cycles without progression: {bad_cycles}"
    
    @pytest.mark.asyncio
    async def test_vip_content_properly_gated(self, mock_db_setup, bot_mock):
        """
        Test that VIP content is properly access-controlled.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        
        # Get all fragments
        result = await mock_db_setup.execute(MagicMock())
        fragments = result.scalars().all()
        
        # Test each VIP fragment
        for fragment in fragments:
            if fragment.required_role == "vip":
                # Mock both free and VIP users
                mock_free_user = MagicMock(spec=User)
                mock_free_user.points = 1000  # High points to isolate role check
                
                mock_vip_user = MagicMock(spec=User)
                mock_vip_user.points = 1000
                
                # Set up session.get to return our mock users
                async def mock_session_get(cls, user_id):
                    if user_id == 123:  # Free user
                        return mock_free_user
                    elif user_id == 456:  # VIP user
                        return mock_vip_user
                    return None
                
                mock_db_setup.get = AsyncMock(side_effect=mock_session_get)
                
                # Mock user_role function
                async def mock_get_user_role(bot, user_id, session=None):
                    if user_id == 123:
                        return "free"
                    elif user_id == 456:
                        return "vip"
                    return "free"
                
                with patch("utils.user_roles.get_user_role", mock_get_user_role):
                    # Test access for free user
                    free_access = await engine._check_access_conditions(123, fragment)
                    # Test access for VIP user
                    vip_access = await engine._check_access_conditions(456, fragment)
                    
                    # Assertions
                    assert free_access is False, f"Free user should not have access to VIP fragment '{fragment.key}'"
                    assert vip_access is True, f"VIP user should have access to VIP fragment '{fragment.key}'"
    
    @pytest.mark.asyncio
    async def test_points_requirements_enforced(self, mock_db_setup, bot_mock):
        """
        Test that point requirements for fragments are properly enforced.
        """
        # Setup
        engine = NarrativeEngine(mock_db_setup, bot_mock)
        
        # Get all fragments
        result = await mock_db_setup.execute(MagicMock())
        fragments = result.scalars().all()
        
        # Test fragments with point requirements
        for fragment in fragments:
            if fragment.min_besitos > 0:
                # Create users with different point levels
                low_points_user = MagicMock(spec=User)
                low_points_user.points = fragment.min_besitos - 1
                
                exact_points_user = MagicMock(spec=User)
                exact_points_user.points = fragment.min_besitos
                
                high_points_user = MagicMock(spec=User)
                high_points_user.points = fragment.min_besitos + 100
                
                # Setup mock session.get
                async def mock_session_get(cls, user_id):
                    if user_id == 111:
                        return low_points_user
                    elif user_id == 222:
                        return exact_points_user
                    elif user_id == 333:
                        return high_points_user
                    return None
                
                mock_db_setup.get = AsyncMock(side_effect=mock_session_get)
                
                # Mock user_role function (all free users to isolate points check)
                async def mock_get_user_role(bot, user_id, session=None):
                    return "free"
                
                with patch("utils.user_roles.get_user_role", mock_get_user_role):
                    # Test access
                    low_access = await engine._check_access_conditions(111, fragment)
                    exact_access = await engine._check_access_conditions(222, fragment)
                    high_access = await engine._check_access_conditions(333, fragment)
                    
                    # Assertions
                    assert low_access is False, f"User with {low_points_user.points} points should not access fragment requiring {fragment.min_besitos}"
                    assert exact_access is True, f"User with exact {exact_points_user.points} points should access fragment requiring {fragment.min_besitos}"
                    assert high_access is True, f"User with {high_points_user.points} points should access fragment requiring {fragment.min_besitos}"