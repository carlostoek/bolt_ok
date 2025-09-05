"""
MVP Choice System and Archetyping Tests

Comprehensive test suite for choice validation, points awarding,
archetyping data collection, and user behavioral analysis.
"""

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from database.narrative_unified import (
    NarrativeFragment, 
    UserNarrativeState, 
    UserDecisionLog,
    UserArchetype,
    UserMissionProgress
)


class TestChoiceSystemValidation:
    """Test choice system validation and processing."""

    def create_decision_fragment(self, fragment_id: str, choices: list):
        """Helper to create decision fragment with choices."""
        return NarrativeFragment(
            id=fragment_id,
            title=f'Decision Fragment {fragment_id}',
            content='Make your choice carefully...',
            fragment_type='DECISION',
            storyline_level=1,
            tier_classification='los_kinkys',
            choices=choices,
            diana_personality_weight=95,
            character_validation_required=True,
            is_active=True
        )

    async def test_choice_structure_validation(self):
        """Test choice options have correct structure."""
        valid_choices = [
            {
                'text': '💫 Follow the mysterious path',
                'next_fragment_id': 'next_fragment_1',
                'points': 10,
                'archetyping_data': {'explorer_score': 5, 'mysterious_score': 3}
            },
            {
                'text': '🌙 Whisper a question to the night',
                'next_fragment_id': 'next_fragment_2', 
                'points': 15,
                'archetyping_data': {'romantic_score': 7, 'patient_score': 2}
            }
        ]
        
        fragment = self.create_decision_fragment('test_fragment', valid_choices)
        
        # Validate choice structure
        for i, choice in enumerate(fragment.choices):
            assert 'text' in choice, f"Choice {i} missing text"
            assert 'next_fragment_id' in choice, f"Choice {i} missing next_fragment_id"
            assert 'points' in choice, f"Choice {i} missing points"
            assert isinstance(choice['points'], int), f"Choice {i} points must be integer"
            assert choice['points'] >= 0, f"Choice {i} points must be non-negative"
            
            if 'archetyping_data' in choice:
                assert isinstance(choice['archetyping_data'], dict), f"Choice {i} archetyping_data must be dict"

    async def test_invalid_choice_handling(self, session):
        """Test system handles invalid choice selections gracefully."""
        choices = [
            {'text': 'Valid choice', 'next_fragment_id': 'valid_next', 'points': 10}
        ]
        fragment = self.create_decision_fragment('test_fragment', choices)
        session.add(fragment)
        
        user_state = UserNarrativeState(
            user_id=12345,
            current_fragment_id='test_fragment'
        )
        session.add(user_state)
        await session.commit()
        
        # Test valid choice index (0)
        assert self.is_valid_choice_index(fragment, 0), "Index 0 should be valid"
        
        # Test invalid choice indices
        assert not self.is_valid_choice_index(fragment, -1), "Negative index should be invalid"
        assert not self.is_valid_choice_index(fragment, 1), "Index 1 should be invalid (only 0 exists)"
        assert not self.is_valid_choice_index(fragment, 99), "Large index should be invalid"

    def is_valid_choice_index(self, fragment: NarrativeFragment, choice_index: int) -> bool:
        """Helper to validate choice index."""
        return 0 <= choice_index < len(fragment.choices)

    async def test_choice_points_awarding(self, session):
        """Test points are correctly awarded for choices."""
        choices = [
            {'text': 'Low points choice', 'next_fragment_id': 'next_1', 'points': 5},
            {'text': 'Medium points choice', 'next_fragment_id': 'next_2', 'points': 15},
            {'text': 'High points choice', 'next_fragment_id': 'next_3', 'points': 25}
        ]
        fragment = self.create_decision_fragment('points_test', choices)
        session.add(fragment)
        
        user_id = 12345
        
        # Test each choice's point awarding
        for choice_index, choice in enumerate(choices):
            decision_log = UserDecisionLog(
                user_id=user_id,
                fragment_id='points_test',
                decision_choice=choice['text'],
                points_awarded=choice['points'],
                made_at=datetime.utcnow() - timedelta(minutes=choice_index)
            )
            session.add(decision_log)
        
        await session.commit()
        
        # Verify point awards
        from sqlalchemy import select, func
        result = await session.execute(
            select(func.sum(UserDecisionLog.points_awarded))
            .where(UserDecisionLog.user_id == user_id)
        )
        total_points = result.scalar()
        
        expected_total = sum(choice['points'] for choice in choices)
        assert total_points == expected_total, f"Expected {expected_total} points, got {total_points}"

    async def test_choice_text_character_consistency(self):
        """Test choice text maintains Diana's character consistency."""
        good_choices = [
            '💫 Seguir el sendero misterioso...',
            '🌙 Susurrar una pregunta al viento',
            '✨ Explorar las sombras con curiosidad',
            '🔮 Aceptar el desafío con valentía'
        ]
        
        bad_choices = [
            'Click here to continue',  # Too technical
            'Yes',  # Too simple
            'Go to next level',  # Too direct
            'OK'  # Too casual
        ]
        
        # Good choices should have character elements
        for choice_text in good_choices:
            assert self.has_character_elements(choice_text), f"Choice '{choice_text}' lacks character elements"
        
        # Bad choices should lack character elements  
        for choice_text in bad_choices:
            assert not self.has_character_elements(choice_text), f"Choice '{choice_text}' should lack character elements"

    def has_character_elements(self, text: str) -> bool:
        """Helper to check if text has Diana character elements."""
        character_indicators = ['💫', '🌙', '✨', '🔮', 'misterio', 'susurra', 'secreto', 'sombra', 'curiosidad']
        return any(indicator in text.lower() for indicator in character_indicators)


class TestArchetypingSystem:
    """Test user archetyping and behavioral analysis."""

    async def test_archetype_initialization(self, session):
        """Test user archetype profile initialization."""
        user_id = 12345
        
        archetype = UserArchetype(
            user_id=user_id,
            explorer_score=0,
            direct_score=0, 
            romantic_score=0,
            analytical_score=0,
            persistent_score=0,
            patient_score=0
        )
        session.add(archetype)
        await session.commit()
        
        # Verify initialization
        assert archetype.dominant_archetype is None, "Should have no dominant archetype initially"
        assert archetype.get_archetype_distribution() == {
            'explorer': 0, 'direct': 0, 'romantic': 0,
            'analytical': 0, 'persistent': 0, 'patient': 0
        }

    async def test_archetype_score_accumulation(self, session):
        """Test archetype scores accumulate correctly from choices."""
        user_id = 12345
        
        archetype = UserArchetype(user_id=user_id)
        session.add(archetype)
        await session.commit()
        
        # Simulate choices that build different archetypes
        choice_data = [
            {'explorer_score': 5, 'romantic_score': 2},  # Explorer-leaning choice
            {'analytical_score': 7, 'persistent_score': 3},  # Analytical-leaning choice
            {'romantic_score': 8, 'patient_score': 4},  # Romantic-leaning choice
            {'explorer_score': 3, 'analytical_score': 5}  # Mixed choice
        ]
        
        # Accumulate scores
        for choice_archetyping in choice_data:
            archetype.explorer_score += choice_archetyping.get('explorer_score', 0)
            archetype.direct_score += choice_archetyping.get('direct_score', 0)
            archetype.romantic_score += choice_archetyping.get('romantic_score', 0)
            archetype.analytical_score += choice_archetyping.get('analytical_score', 0)
            archetype.persistent_score += choice_archetyping.get('persistent_score', 0)
            archetype.patient_score += choice_archetyping.get('patient_score', 0)
        
        await session.commit()
        
        # Verify accumulation
        assert archetype.explorer_score == 8  # 5 + 3
        assert archetype.romantic_score == 10  # 2 + 8
        assert archetype.analytical_score == 12  # 7 + 5
        assert archetype.persistent_score == 3
        assert archetype.patient_score == 4
        assert archetype.direct_score == 0

    async def test_dominant_archetype_calculation(self, session):
        """Test dominant archetype is calculated correctly."""
        user_id = 12345
        
        # Create archetype with clear dominant trait
        archetype = UserArchetype(
            user_id=user_id,
            explorer_score=15,
            direct_score=5,
            romantic_score=8,
            analytical_score=25,  # Highest score
            persistent_score=12,
            patient_score=7
        )
        session.add(archetype)
        
        # Calculate dominant archetype
        archetype.calculate_dominant_archetype()
        await session.commit()
        
        # Verify dominant archetype
        assert archetype.dominant_archetype == 'analytical', f"Expected 'analytical', got {archetype.dominant_archetype}"

    async def test_archetype_distribution_calculation(self, session):
        """Test archetype distribution percentages."""
        user_id = 12345
        
        archetype = UserArchetype(
            user_id=user_id,
            explorer_score=20,
            direct_score=10,
            romantic_score=30,
            analytical_score=15,
            persistent_score=15,
            patient_score=10
        )
        session.add(archetype)
        await session.commit()
        
        distribution = archetype.get_archetype_distribution()
        total_percentage = sum(distribution.values())
        
        # Verify distribution
        assert abs(total_percentage - 100.0) < 0.1, f"Total should be 100%, got {total_percentage}%"
        assert distribution['romantic'] == 30.0, f"Romantic should be 30%, got {distribution['romantic']}%"
        assert distribution['explorer'] == 20.0, f"Explorer should be 20%, got {distribution['explorer']}%"

    async def test_behavioral_pattern_tracking(self, session):
        """Test behavioral patterns are tracked correctly."""
        user_id = 12345
        
        archetype = UserArchetype(
            user_id=user_id,
            avg_response_time=0,
            content_revisit_count=0,
            deep_exploration_sessions=0,
            question_engagement_rate=0
        )
        session.add(archetype)
        await session.commit()
        
        # Simulate behavioral tracking updates
        response_times = [15.5, 22.3, 18.7, 12.1, 25.9]  # Seconds
        archetype.avg_response_time = int(sum(response_times) / len(response_times))
        
        archetype.content_revisit_count = 3  # User revisited content 3 times
        archetype.deep_exploration_sessions = 2  # 2 sessions > 10 minutes
        archetype.question_engagement_rate = 85  # 85% of questions answered thoughtfully
        
        await session.commit()
        
        # Verify tracking
        assert 15 <= archetype.avg_response_time <= 25, f"Average response time should be ~19s, got {archetype.avg_response_time}s"
        assert archetype.content_revisit_count == 3
        assert archetype.deep_exploration_sessions == 2
        assert archetype.question_engagement_rate == 85

    async def test_archetype_evolution_over_time(self, session):
        """Test archetype evolves as user makes more choices."""
        user_id = 12345
        
        # Initial archetype - primarily explorer
        archetype = UserArchetype(
            user_id=user_id,
            explorer_score=20,
            romantic_score=5,
            analytical_score=3
        )
        archetype.calculate_dominant_archetype()
        initial_dominant = archetype.dominant_archetype
        session.add(archetype)
        await session.commit()
        
        assert initial_dominant == 'explorer', f"Initial dominant should be explorer, got {initial_dominant}"
        
        # Simulate user making more romantic choices over time
        romantic_choice_impacts = [8, 12, 15, 10, 18]  # Growing romantic scores
        
        for romantic_impact in romantic_choice_impacts:
            archetype.romantic_score += romantic_impact
            archetype.calculate_dominant_archetype()
        
        await session.commit()
        
        # Verify evolution
        final_dominant = archetype.dominant_archetype
        assert final_dominant == 'romantic', f"Final dominant should be romantic, got {final_dominant}"
        assert archetype.romantic_score > archetype.explorer_score, "Romantic score should exceed explorer"


class TestChoiceArchetypingIntegration:
    """Test integration between choice system and archetyping."""

    async def test_choice_to_archetype_data_flow(self, session):
        """Test choice archetyping data flows correctly to user archetype."""
        user_id = 12345
        
        # Create user archetype
        archetype = UserArchetype(user_id=user_id)
        session.add(archetype)
        
        # Create decision fragment with archetyping choices
        choices = [
            {
                'text': '🔍 Examine everything carefully',
                'next_fragment_id': 'analytical_path',
                'points': 10,
                'archetyping_data': {'analytical_score': 8, 'explorer_score': 3}
            },
            {
                'text': '💕 Follow your heart\'s desire',
                'next_fragment_id': 'romantic_path',
                'points': 15,
                'archetyping_data': {'romantic_score': 10, 'patient_score': 2}
            }
        ]
        
        fragment = NarrativeFragment(
            id='archetype_test_fragment',
            title='Archetyping Test',
            content='Choose your approach...',
            fragment_type='DECISION',
            choices=choices,
            is_active=True
        )
        session.add(fragment)
        await session.commit()
        
        # Simulate user making first choice (analytical)
        chosen_choice = choices[0]
        archetyping_data = chosen_choice['archetyping_data']
        
        # Apply archetyping data to user profile
        archetype.analytical_score += archetyping_data.get('analytical_score', 0)
        archetype.explorer_score += archetyping_data.get('explorer_score', 0)
        
        # Log the decision
        decision_log = UserDecisionLog(
            user_id=user_id,
            fragment_id='archetype_test_fragment',
            decision_choice=chosen_choice['text'],
            points_awarded=chosen_choice['points'],
            made_at=datetime.utcnow()
        )
        session.add(decision_log)
        
        archetype.calculate_dominant_archetype()
        await session.commit()
        
        # Verify integration
        assert archetype.analytical_score == 8
        assert archetype.explorer_score == 3
        assert archetype.romantic_score == 0
        assert archetype.dominant_archetype == 'analytical'

    async def test_multiple_choices_archetype_building(self, session):
        """Test multiple choices build comprehensive archetype profile."""
        user_id = 12345
        
        archetype = UserArchetype(user_id=user_id)
        session.add(archetype)
        
        # Simulate a series of choices that build mixed archetype
        choice_sequence = [
            {'analytical_score': 5, 'explorer_score': 2},  # Fragment 1, Choice A
            {'romantic_score': 7, 'patient_score': 3},     # Fragment 2, Choice B  
            {'persistent_score': 6, 'analytical_score': 4}, # Fragment 3, Choice A
            {'explorer_score': 8, 'direct_score': 2},      # Fragment 4, Choice C
            {'romantic_score': 9, 'patient_score': 1}      # Fragment 5, Choice B
        ]
        
        # Apply each choice's archetyping impact
        for i, archetyping_impact in enumerate(choice_sequence):
            for archetype_trait, score in archetyping_impact.items():
                current_score = getattr(archetype, archetype_trait, 0)
                setattr(archetype, archetype_trait, current_score + score)
            
            # Log decision
            decision_log = UserDecisionLog(
                user_id=user_id,
                fragment_id=f'fragment_{i+1}',
                decision_choice=f'Choice made {i+1}',
                points_awarded=10 + (i * 2),
                made_at=datetime.utcnow() - timedelta(minutes=(5-i) * 10)
            )
            session.add(decision_log)
        
        archetype.calculate_dominant_archetype()
        await session.commit()
        
        # Verify comprehensive profile
        expected_scores = {
            'analytical_score': 9,  # 5 + 4
            'explorer_score': 10,   # 2 + 8
            'romantic_score': 16,   # 7 + 9
            'patient_score': 4,     # 3 + 1
            'persistent_score': 6,
            'direct_score': 2
        }
        
        for trait, expected_score in expected_scores.items():
            actual_score = getattr(archetype, trait)
            assert actual_score == expected_score, f"{trait}: expected {expected_score}, got {actual_score}"
        
        assert archetype.dominant_archetype == 'romantic', "Should be romantic with highest score (16)"

    async def test_archetype_personalization_impact(self, session):
        """Test archetype data impacts personalized content delivery."""
        user_id = 12345
        
        # Create archetype with strong romantic tendency
        archetype = UserArchetype(
            user_id=user_id,
            explorer_score=10,
            romantic_score=35,  # Dominant
            analytical_score=8,
            patient_score=12
        )
        archetype.calculate_dominant_archetype()
        session.add(archetype)
        await session.commit()
        
        # Verify personalization data
        assert archetype.dominant_archetype == 'romantic'
        
        # Test personalization logic
        personalization_data = self.get_personalization_for_archetype(archetype.dominant_archetype)
        
        assert 'romantic' in personalization_data['theme_preferences']
        assert '💕' in personalization_data['preferred_emojis']
        assert 'emotional' in personalization_data['content_style']

    def get_personalization_for_archetype(self, dominant_archetype: str) -> dict:
        """Helper to get personalization data based on archetype."""
        personalization_map = {
            'explorer': {
                'theme_preferences': ['mysterious', 'adventure', 'discovery'],
                'preferred_emojis': ['🔍', '🗝️', '🌟'],
                'content_style': 'detailed_descriptive'
            },
            'romantic': {
                'theme_preferences': ['romantic', 'emotional', 'intimate'],
                'preferred_emojis': ['💕', '🌙', '✨'],
                'content_style': 'emotional'
            },
            'analytical': {
                'theme_preferences': ['intellectual', 'complex', 'philosophical'],
                'preferred_emojis': ['🤔', '💭', '🔮'],
                'content_style': 'thought_provoking'
            },
            'direct': {
                'theme_preferences': ['straightforward', 'action', 'decisive'],
                'preferred_emojis': ['⚡', '🎯', '✅'],
                'content_style': 'concise'
            },
            'persistent': {
                'theme_preferences': ['challenging', 'progressive', 'achievement'],
                'preferred_emojis': ['💪', '🏆', '⭐'],
                'content_style': 'motivational'
            },
            'patient': {
                'theme_preferences': ['contemplative', 'deep', 'reflective'],
                'preferred_emojis': ['🧘', '🌊', '🌸'],
                'content_style': 'meditative'
            }
        }
        
        return personalization_map.get(dominant_archetype, personalization_map['explorer'])

    async def test_archetype_consistency_validation(self, session):
        """Test archetype data maintains consistency across sessions."""
        user_id = 12345
        
        # Create initial archetype state
        initial_archetype = UserArchetype(
            user_id=user_id,
            explorer_score=20,
            romantic_score=15,
            analytical_score=25,
            created_at=datetime.utcnow() - timedelta(days=5)
        )
        initial_archetype.calculate_dominant_archetype()
        session.add(initial_archetype)
        await session.commit()
        
        initial_dominant = initial_archetype.dominant_archetype
        initial_total_score = (
            initial_archetype.explorer_score + initial_archetype.romantic_score + 
            initial_archetype.analytical_score
        )
        
        # Simulate session restart - retrieve archetype
        session.expunge(initial_archetype)
        
        from sqlalchemy import select
        result = await session.execute(select(UserArchetype).where(UserArchetype.user_id == user_id))
        retrieved_archetype = result.scalar_one_or_none()
        
        # Verify consistency
        assert retrieved_archetype is not None
        assert retrieved_archetype.dominant_archetype == initial_dominant
        
        retrieved_total = (
            retrieved_archetype.explorer_score + retrieved_archetype.romantic_score + 
            retrieved_archetype.analytical_score
        )
        assert retrieved_total == initial_total_score
        
        # Add new choice impact and verify evolution
        retrieved_archetype.romantic_score += 20  # Large romantic boost
        retrieved_archetype.calculate_dominant_archetype()
        await session.commit()
        
        # Should now be romantic dominant
        assert retrieved_archetype.dominant_archetype == 'romantic'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])