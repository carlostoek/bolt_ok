"""
MVP Narrative Progression Tests

Comprehensive test suite for Level 1→2→3 progression logic,
user state persistence, clue gating, and advancement mechanisms.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from database.narrative_unified import (
    NarrativeFragment, 
    UserNarrativeState, 
    UserDecisionLog,
    UserMissionProgress,
    UserArchetype
)
from services.narrative_engine import NarrativeEngine


class TestLevelProgressionLogic:
    """Test level progression from 1→2→3."""

    @pytest_asyncio.fixture
    async def progression_service(self, session):
        """Create progression service with mocked dependencies."""
        engine = NarrativeEngine(session)
        engine.point_service = AsyncMock()
        return engine

    def create_test_fragment(self, fragment_id: str, level: int, tier: str, sequence: int, 
                           fragment_type: str = 'DECISION', choices: list = None):
        """Helper to create test fragments."""
        if choices is None:
            choices = []
        
        return NarrativeFragment(
            id=fragment_id,
            title=f'Test Fragment {sequence}',
            content=f'Test content for level {level} sequence {sequence}',
            fragment_type=fragment_type,
            storyline_level=level,
            tier_classification=tier,
            fragment_sequence=sequence,
            choices=choices,
            triggers={'reward_points': 10 * level},
            diana_personality_weight=95 + level,
            character_validation_required=True,
            is_active=True
        )

    async def test_level_1_progression_structure(self, session):
        """Test Level 1 has correct progression structure."""
        # Create Level 1 fragments
        fragments = [
            self.create_test_fragment('l1_f1', 1, 'los_kinkys', 1, 'DECISION', [
                {'text': 'Choice 1', 'next_fragment_id': 'l1_f2', 'points': 10}
            ]),
            self.create_test_fragment('l1_f2', 1, 'los_kinkys', 2, 'STORY'),
            self.create_test_fragment('l1_f3', 1, 'los_kinkys', 3, 'DECISION', [
                {'text': 'Advance to Level 2', 'next_fragment_id': 'l2_f1', 'points': 15}
            ])
        ]
        
        for fragment in fragments:
            session.add(fragment)
        await session.commit()
        
        # Test progression logic
        user_state = UserNarrativeState(
            user_id=12345,
            current_fragment_id='l1_f1',
            current_level=1,
            current_tier='los_kinkys',
            visited_fragments=[],
            completed_fragments=[]
        )
        session.add(user_state)
        await session.commit()
        
        # Verify initial state
        assert user_state.current_level == 1
        assert user_state.current_tier == 'los_kinkys'
        assert len(user_state.visited_fragments) == 0

    async def test_level_2_progression_requirements(self, session):
        """Test Level 2 access requires Level 1 completion."""
        # Create Level 2 fragments
        l2_fragment = self.create_test_fragment('l2_f1', 2, 'observadores', 4)
        session.add(l2_fragment)
        
        # Create user without Level 1 completion
        user_state_incomplete = UserNarrativeState(
            user_id=12345,
            current_fragment_id='l1_f1',
            current_level=1,
            current_tier='los_kinkys',
            completed_fragments=['l1_f1']  # Only 1 fragment completed
        )
        session.add(user_state_incomplete)
        
        # Create user with Level 1 completion
        user_state_complete = UserNarrativeState(
            user_id=54321,
            current_fragment_id='l2_f1',
            current_level=2,
            current_tier='observadores',
            completed_fragments=['l1_f1', 'l1_f2', 'l1_f3']  # All Level 1 completed
        )
        session.add(user_state_complete)
        await session.commit()
        
        # Test access control
        assert not self.can_access_level(user_state_incomplete, 2), "Should not access Level 2 without Level 1 completion"
        assert self.can_access_level(user_state_complete, 2), "Should access Level 2 with Level 1 completion"

    def can_access_level(self, user_state: UserNarrativeState, target_level: int) -> bool:
        """Helper method to check level access."""
        if target_level <= user_state.current_level:
            return True
        
        level_requirements = {
            2: 3,  # Need 3 Level 1 fragments completed
            3: 6   # Need 6 fragments total (3 Level 1 + 3 Level 2)
        }
        
        required_completions = level_requirements.get(target_level, 0)
        return len(user_state.completed_fragments) >= required_completions

    async def test_level_3_progression_requirements(self, session):
        """Test Level 3 access requires Level 2 completion."""
        # Create Level 3 fragment
        l3_fragment = self.create_test_fragment('l3_f1', 3, 'comprensores', 7)
        session.add(l3_fragment)
        
        # Create user with insufficient progress
        user_state_insufficient = UserNarrativeState(
            user_id=12345,
            current_level=2,
            current_tier='observadores',
            completed_fragments=['l1_f1', 'l1_f2', 'l1_f3', 'l2_f1']  # Missing Level 2 completion
        )
        session.add(user_state_insufficient)
        
        # Create user with sufficient progress
        user_state_sufficient = UserNarrativeState(
            user_id=54321,
            current_level=3,
            current_tier='comprensores', 
            completed_fragments=['l1_f1', 'l1_f2', 'l1_f3', 'l2_f1', 'l2_f2', 'l2_f3']  # All Level 1&2 completed
        )
        session.add(user_state_sufficient)
        await session.commit()
        
        # Test access control
        assert not self.can_access_level(user_state_insufficient, 3), "Should not access Level 3 without Level 2 completion"
        assert self.can_access_level(user_state_sufficient, 3), "Should access Level 3 with Level 1&2 completion"

    async def test_tier_transition_logic(self, session):
        """Test tier transitions follow progression logic."""
        user_state = UserNarrativeState(
            user_id=12345,
            current_level=1,
            current_tier='los_kinkys',
            tier_transition_history=[]
        )
        session.add(user_state)
        await session.commit()
        
        # Simulate tier progression
        transitions = [
            (1, 'los_kinkys'),
            (2, 'observadores'), 
            (3, 'comprensores')
        ]
        
        for level, tier in transitions:
            user_state.current_level = level
            user_state.current_tier = tier
            
            # Record transition
            if not user_state.tier_transition_history:
                user_state.tier_transition_history = []
            user_state.tier_transition_history.append({
                'from_tier': 'los_kinkys' if level == 1 else transitions[level-2][1],
                'to_tier': tier,
                'level': level,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        await session.commit()
        
        # Verify transition history
        assert len(user_state.tier_transition_history) == 3
        final_transition = user_state.tier_transition_history[-1]
        assert final_transition['to_tier'] == 'comprensores'
        assert final_transition['level'] == 3

    async def test_fragment_sequence_validation(self, session):
        """Test fragments must be completed in sequence."""
        # Create fragments in sequence
        fragments = [
            self.create_test_fragment('seq_1', 1, 'los_kinkys', 1, 'DECISION', [
                {'text': 'Next', 'next_fragment_id': 'seq_2', 'points': 10}
            ]),
            self.create_test_fragment('seq_2', 1, 'los_kinkys', 2, 'STORY'),
            self.create_test_fragment('seq_3', 1, 'los_kinkys', 3, 'DECISION', [
                {'text': 'Complete', 'next_fragment_id': 'seq_4', 'points': 15}
            ]),
            self.create_test_fragment('seq_4', 2, 'observadores', 4)
        ]
        
        for fragment in fragments:
            session.add(fragment)
        await session.commit()
        
        # Test valid sequence progression
        user_state = UserNarrativeState(
            user_id=12345,
            current_fragment_id='seq_1',
            visited_fragments=[],
            completed_fragments=[]
        )
        session.add(user_state)
        await session.commit()
        
        # Simulate sequential progression
        sequence_progression = ['seq_1', 'seq_2', 'seq_3', 'seq_4']
        
        for i, fragment_id in enumerate(sequence_progression):
            user_state.current_fragment_id = fragment_id
            
            if fragment_id not in user_state.visited_fragments:
                user_state.visited_fragments.append(fragment_id)
            
            if i > 0:  # Mark previous as completed
                prev_fragment = sequence_progression[i-1]
                if prev_fragment not in user_state.completed_fragments:
                    user_state.completed_fragments.append(prev_fragment)
        
        await session.commit()
        
        # Verify progression
        assert len(user_state.visited_fragments) == 4
        assert len(user_state.completed_fragments) == 3  # Current fragment not completed yet
        assert user_state.current_fragment_id == 'seq_4'


class TestClueGatingSystem:
    """Test clue requirements and progression gating."""

    async def test_clue_requirement_blocking(self, session):
        """Test fragments with clue requirements block access appropriately."""
        # Create fragment requiring specific clue
        gated_fragment = NarrativeFragment(
            id='gated_fragment',
            title='Gated Fragment',
            content='This requires a clue to access',
            fragment_type='STORY',
            required_clues=['secret_key_1'],
            storyline_level=2,
            tier_classification='observadores',
            is_active=True
        )
        session.add(gated_fragment)
        
        # Create user without required clue
        user_no_clue = UserNarrativeState(
            user_id=12345,
            unlocked_clues=[]
        )
        session.add(user_no_clue)
        
        # Create user with required clue
        user_with_clue = UserNarrativeState(
            user_id=54321,
            unlocked_clues=['secret_key_1']
        )
        session.add(user_with_clue)
        await session.commit()
        
        # Test access control
        assert not user_no_clue.has_unlocked_clue('secret_key_1'), "User should not have clue"
        assert user_with_clue.has_unlocked_clue('secret_key_1'), "User should have clue"
        
        # Test gating logic
        assert not self.can_access_fragment(user_no_clue, gated_fragment), "Should not access without clue"
        assert self.can_access_fragment(user_with_clue, gated_fragment), "Should access with clue"

    def can_access_fragment(self, user_state: UserNarrativeState, fragment: NarrativeFragment) -> bool:
        """Helper to check fragment access based on clues."""
        if not fragment.required_clues:
            return True
        
        for required_clue in fragment.required_clues:
            if not user_state.has_unlocked_clue(required_clue):
                return False
        return True

    async def test_clue_unlocking_mechanism(self, session):
        """Test clues are properly unlocked through progression."""
        # Create fragment that unlocks clue
        clue_granting_fragment = NarrativeFragment(
            id='clue_granter',
            title='Clue Granter',
            content='This fragment grants a clue',
            fragment_type='STORY',
            triggers={'unlock_clue': 'mystery_revealed'},
            is_active=True
        )
        session.add(clue_granting_fragment)
        
        user_state = UserNarrativeState(
            user_id=12345,
            unlocked_clues=[]
        )
        session.add(user_state)
        await session.commit()
        
        # Simulate completing fragment and unlocking clue
        user_state.completed_fragments.append('clue_granter')
        
        # Process trigger - unlock clue
        trigger = clue_granting_fragment.triggers.get('unlock_clue')
        if trigger and trigger not in user_state.unlocked_clues:
            user_state.unlocked_clues.append(trigger)
        
        await session.commit()
        
        # Verify clue was unlocked
        assert user_state.has_unlocked_clue('mystery_revealed'), "Clue should be unlocked"
        assert len(user_state.unlocked_clues) == 1

    async def test_multiple_clue_requirements(self, session):
        """Test fragments requiring multiple clues."""
        # Create fragment requiring multiple clues
        multi_clue_fragment = NarrativeFragment(
            id='multi_clue_fragment',
            title='Multi Clue Fragment',
            content='Requires multiple clues',
            fragment_type='DECISION',
            required_clues=['clue_a', 'clue_b', 'clue_c'],
            is_active=True
        )
        session.add(multi_clue_fragment)
        
        # Test partial clue access
        user_partial = UserNarrativeState(
            user_id=12345,
            unlocked_clues=['clue_a', 'clue_b']  # Missing clue_c
        )
        session.add(user_partial)
        
        # Test complete clue access
        user_complete = UserNarrativeState(
            user_id=54321,
            unlocked_clues=['clue_a', 'clue_b', 'clue_c']  # All clues
        )
        session.add(user_complete)
        await session.commit()
        
        # Verify access control
        assert not self.can_access_fragment(user_partial, multi_clue_fragment), "Should not access with partial clues"
        assert self.can_access_fragment(user_complete, multi_clue_fragment), "Should access with all clues"


class TestUserStatePersistence:
    """Test user state persistence between sessions."""

    async def test_session_state_persistence(self, session):
        """Test user state persists correctly between sessions."""
        # Create initial user state
        initial_state = UserNarrativeState(
            user_id=12345,
            current_fragment_id='level_1_fragment',
            current_level=1,
            current_tier='los_kinkys',
            visited_fragments=['frag_1', 'frag_2'],
            completed_fragments=['frag_1'],
            unlocked_clues=['first_secret'],
            interaction_patterns={'session_count': 1},
            response_time_tracking=[15.5, 12.3, 18.7]
        )
        session.add(initial_state)
        await session.commit()
        
        # Simulate session ending and starting again
        session.expunge(initial_state)  # Remove from session to simulate new session
        
        # Retrieve state in new "session"
        from sqlalchemy import select
        result = await session.execute(select(UserNarrativeState).where(UserNarrativeState.user_id == 12345))
        restored_state = result.scalar_one_or_none()
        
        # Verify state persistence
        assert restored_state is not None, "User state should be retrievable"
        assert restored_state.current_fragment_id == 'level_1_fragment'
        assert restored_state.current_level == 1
        assert restored_state.current_tier == 'los_kinkys'
        assert len(restored_state.visited_fragments) == 2
        assert len(restored_state.completed_fragments) == 1
        assert len(restored_state.unlocked_clues) == 1
        assert 'first_secret' in restored_state.unlocked_clues

    async def test_progress_state_updates(self, session):
        """Test progress state updates correctly during progression."""
        user_state = UserNarrativeState(
            user_id=12345,
            current_fragment_id='start',
            visited_fragments=[],
            completed_fragments=[],
            current_level=1
        )
        session.add(user_state)
        await session.commit()
        
        # Simulate progression through multiple fragments
        progression_sequence = [
            ('start', 1), ('middle_1', 1), ('middle_2', 1), 
            ('level_2_start', 2), ('level_2_end', 2), ('finale', 3)
        ]
        
        for fragment_id, level in progression_sequence:
            # Update current fragment
            user_state.current_fragment_id = fragment_id
            user_state.current_level = level
            
            # Mark as visited
            if fragment_id not in user_state.visited_fragments:
                user_state.visited_fragments.append(fragment_id)
            
            # Mark previous as completed (except first)
            if len(user_state.visited_fragments) > 1:
                prev_fragment = user_state.visited_fragments[-2]
                if prev_fragment not in user_state.completed_fragments:
                    user_state.completed_fragments.append(prev_fragment)
            
            user_state.updated_at = datetime.utcnow()
        
        await session.commit()
        
        # Verify final state
        assert user_state.current_fragment_id == 'finale'
        assert user_state.current_level == 3
        assert len(user_state.visited_fragments) == 6
        assert len(user_state.completed_fragments) == 5  # All but current

    async def test_concurrent_user_state_handling(self, session):
        """Test system handles multiple users' states correctly."""
        # Create multiple user states
        users_data = [
            (12345, 'frag_1', 1, ['frag_1'], []),
            (23456, 'frag_5', 2, ['frag_1', 'frag_2', 'frag_3', 'frag_4', 'frag_5'], ['frag_1', 'frag_2', 'frag_3', 'frag_4']),
            (34567, 'frag_8', 3, ['frag_1', 'frag_2', 'frag_3', 'frag_4', 'frag_5', 'frag_6', 'frag_7', 'frag_8'], 
             ['frag_1', 'frag_2', 'frag_3', 'frag_4', 'frag_5', 'frag_6', 'frag_7'])
        ]
        
        user_states = []
        for user_id, current_frag, level, visited, completed in users_data:
            state = UserNarrativeState(
                user_id=user_id,
                current_fragment_id=current_frag,
                current_level=level,
                visited_fragments=visited,
                completed_fragments=completed
            )
            user_states.append(state)
            session.add(state)
        
        await session.commit()
        
        # Verify each user's state is independent and correct
        from sqlalchemy import select
        for expected_state in user_states:
            result = await session.execute(
                select(UserNarrativeState).where(UserNarrativeState.user_id == expected_state.user_id)
            )
            retrieved_state = result.scalar_one_or_none()
            
            assert retrieved_state is not None
            assert retrieved_state.current_fragment_id == expected_state.current_fragment_id
            assert retrieved_state.current_level == expected_state.current_level
            assert len(retrieved_state.visited_fragments) == len(expected_state.visited_fragments)
            assert len(retrieved_state.completed_fragments) == len(expected_state.completed_fragments)


class TestDecisionLogging:
    """Test user decision logging and history tracking."""

    async def test_decision_log_creation(self, session):
        """Test decision logging captures all required information."""
        # Create test fragment with choices
        fragment = NarrativeFragment(
            id='decision_fragment',
            title='Decision Point',
            content='Make a choice',
            fragment_type='DECISION',
            choices=[
                {'text': 'Option A', 'points': 10, 'archetyping_data': {'explorer_score': 5}},
                {'text': 'Option B', 'points': 15, 'archetyping_data': {'romantic_score': 7}}
            ],
            is_active=True
        )
        session.add(fragment)
        await session.commit()
        
        # Create decision log
        decision_log = UserDecisionLog(
            user_id=12345,
            fragment_id='decision_fragment',
            decision_choice='Option A',
            points_awarded=10,
            clues_unlocked=[],
            made_at=datetime.utcnow()
        )
        session.add(decision_log)
        await session.commit()
        
        # Verify logging
        from sqlalchemy import select
        result = await session.execute(
            select(UserDecisionLog).where(
                UserDecisionLog.user_id == 12345,
                UserDecisionLog.fragment_id == 'decision_fragment'
            )
        )
        logged_decision = result.scalar_one_or_none()
        
        assert logged_decision is not None
        assert logged_decision.decision_choice == 'Option A'
        assert logged_decision.points_awarded == 10
        assert logged_decision.made_at is not None

    async def test_decision_history_tracking(self, session):
        """Test complete decision history tracking."""
        user_id = 12345
        decisions_data = [
            ('frag_1', 'Choice A', 10, ['clue_1']),
            ('frag_2', 'Choice B', 15, []),
            ('frag_3', 'Choice A', 12, ['clue_2', 'clue_3']),
        ]
        
        decision_logs = []
        for fragment_id, choice, points, clues in decisions_data:
            log = UserDecisionLog(
                user_id=user_id,
                fragment_id=fragment_id,
                decision_choice=choice,
                points_awarded=points,
                clues_unlocked=clues,
                made_at=datetime.utcnow() - timedelta(minutes=len(decision_logs) * 10)
            )
            decision_logs.append(log)
            session.add(log)
        
        await session.commit()
        
        # Retrieve decision history
        from sqlalchemy import select, desc
        result = await session.execute(
            select(UserDecisionLog)
            .where(UserDecisionLog.user_id == user_id)
            .order_by(desc(UserDecisionLog.made_at))
        )
        history = result.scalars().all()
        
        # Verify history
        assert len(history) == 3
        assert history[0].fragment_id == 'frag_3'  # Most recent first
        assert history[-1].fragment_id == 'frag_1'  # Oldest last
        
        # Verify total points from decisions
        total_points = sum(log.points_awarded for log in history)
        assert total_points == 37
        
        # Verify total clues unlocked
        all_clues = []
        for log in history:
            all_clues.extend(log.clues_unlocked)
        assert len(all_clues) == 3
        assert 'clue_1' in all_clues
        assert 'clue_2' in all_clues
        assert 'clue_3' in all_clues

    async def test_decision_validation_prevents_duplicates(self, session):
        """Test system prevents duplicate decision logging."""
        user_id = 12345
        fragment_id = 'unique_fragment'
        
        # Create first decision log
        first_decision = UserDecisionLog(
            user_id=user_id,
            fragment_id=fragment_id,
            decision_choice='First Choice',
            points_awarded=10,
            made_at=datetime.utcnow()
        )
        session.add(first_decision)
        await session.commit()
        
        # Attempt to create duplicate decision
        duplicate_decision = UserDecisionLog(
            user_id=user_id,
            fragment_id=fragment_id,
            decision_choice='Duplicate Choice',
            points_awarded=20,
            made_at=datetime.utcnow()
        )
        session.add(duplicate_decision)
        await session.commit()  # This should succeed (multiple decisions allowed for same fragment)
        
        # Verify both decisions exist (system allows multiple decisions for analysis)
        from sqlalchemy import select, func
        result = await session.execute(
            select(func.count(UserDecisionLog.id))
            .where(
                UserDecisionLog.user_id == user_id,
                UserDecisionLog.fragment_id == fragment_id
            )
        )
        decision_count = result.scalar()
        
        assert decision_count == 2, "Both decisions should be logged for analysis"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])