from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from database.models import User
from database.narrative_unified import NarrativeFragment, UserNarrativeState, UserDecisionLog, UserEmotionalJourney

class NarrativeService:
    def __init__(self, session: AsyncSession, user_service=None, point_service=None, backpack_service=None):
        self.session = session
        self.user_service = user_service
        self.point_service = point_service
        self.backpack_service = backpack_service

    async def _update_emotional_state(self, user_state: UserNarrativeState):
        """
        Analyzes user progress and updates their emotional state based on the 6-Level Crescendo.
        This is the core of the Emotional Crescendo implementation.
        """
        if not user_state:
            return

        # Foundation for Level 1-2: Curiosity -> Intrigue
        # Simple mapping for now: narrative level maps to emotional level.
        # This will be expanded with more sophisticated logic.
        if user_state.current_level <= 2:
            user_state.emotional_level = 1  # The Awakening
            user_state.last_emotional_milestone = "curiosity_awakening"
        elif user_state.current_level == 3:
            user_state.emotional_level = 2  # The Recognition
            user_state.last_emotional_milestone = "fascination_peak"
        elif user_state.current_level == 4:
            user_state.emotional_level = 3  # The Investment
            user_state.last_emotional_milestone = "investment_solidified"
        elif user_state.current_level == 5:
            user_state.emotional_level = 4  # The Attachment
            user_state.last_emotional_milestone = "attachment_crystallized"
        elif user_state.current_level >= 6:
            user_state.emotional_level = 5  # La Trascendencia
            user_state.last_emotional_milestone = "transcendence_achieved"

        # Placeholder for future, more complex logic:
        # - Analyze interaction_patterns to calculate attachment_score
        # - Detect vulnerability exchanges
        # - Manage memory_callbacks and anticipation_triggers

        await self.session.commit()
        await self.session.refresh(user_state)

    async def get_user_current_fragment(self, user_id: int):
        """
        Gets the current story fragment for a user with optimized loading.
        If they haven't started, returns the initial fragment.
        Enhanced to update emotional state.
        """
        user_state = await self.session.execute(
            select(UserNarrativeState)
            .options(
                selectinload(UserNarrativeState.user),
                selectinload(UserNarrativeState.current_fragment)
            )
            .where(UserNarrativeState.user_id == user_id)
        )
        user_state = user_state.scalar_one_or_none()

        fragment_id = None
        if user_state and user_state.current_fragment_id:
            fragment_id = user_state.current_fragment_id
        
        if fragment_id:
            if user_state and user_state.current_fragment:
                fragment = user_state.current_fragment
            else:
                fragment = await self.session.get(NarrativeFragment, fragment_id)
        else:
            fragment = None

        if not fragment:
            first_fragment_result = await self.session.execute(
                select(NarrativeFragment).where(
                    NarrativeFragment.is_active == True
                ).order_by(NarrativeFragment.fragment_sequence).limit(1)
            )
            fragment = first_fragment_result.scalar_one_or_none()
            fragment_id = fragment.id if fragment else None

        if not user_state and fragment_id:
            user_state = UserNarrativeState(user_id=user_id, current_fragment_id=fragment_id)
            self.session.add(user_state)
            await self.session.commit()
            await self.session.refresh(user_state)
        elif user_state and user_state.current_fragment_id != fragment_id:
            user_state.current_fragment_id = fragment_id
            await self.session.commit()
            await self.session.refresh(user_state)

        # Update emotional state after getting the fragment
        if user_state:
            await self._update_emotional_state(user_state)
            
        return fragment

    async def process_user_choice(self, user_id: int, fragment_id: str, choice_index: int):
        """
        Processes a choice, checks conditions, advances the story, and updates emotional state.
        """
        fragment = await self.session.get(NarrativeFragment, fragment_id)

        if not fragment or not fragment.is_decision or choice_index >= len(fragment.choices):
            return None

        choice = fragment.choices[choice_index]
        
        user_state = await self.session.execute(
            select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        )
        user_state = user_state.scalar_one_or_none()

        if not user_state:
            # This case should ideally be handled by get_user_current_fragment
            user_state = UserNarrativeState(user_id=user_id)
            self.session.add(user_state)

        # Log the decision
        log_entry = UserDecisionLog(
            user_id=user_id, 
            fragment_id=fragment_id,
            decision_choice=choice.get('text', f'Choice {choice_index}'),
            points_awarded=choice.get('points', 0),
            clues_unlocked=choice.get('unlocks_clues', [])
        )
        self.session.add(log_entry)

        # Update narrative state
        next_fragment_id = choice.get('next_fragment_id')
        user_state.current_fragment_id = next_fragment_id
        
        if fragment_id not in user_state.visited_fragments:
            user_state.visited_fragments.append(fragment_id)
        if fragment_id not in user_state.completed_fragments:
            user_state.completed_fragments.append(fragment_id)
        
        for clue in choice.get('unlocks_clues', []):
            if clue not in user_state.unlocked_clues:
                user_state.unlocked_clues.append(clue)
        
        # Update narrative level if specified in choice
        if 'sets_level' in choice:
            user_state.current_level = choice['sets_level']

        await self.session.commit()
        await self.session.refresh(user_state)

        # Update emotional state after processing the choice
        await self._update_emotional_state(user_state)

        if next_fragment_id:
            return await self.session.get(NarrativeFragment, next_fragment_id)
        return None

    async def check_fragment_requirements(self, user_id: int, fragment: NarrativeFragment) -> bool:
        """
        Checks if user meets requirements for accessing a fragment.
        """
        if not fragment.required_clues:
            return True
            
        user_state_result = await self.session.execute(
            select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        )
        user_state = user_state_result.scalar_one_or_none()
        
        if not user_state:
            return False
            
        user_clues = set(user_state.unlocked_clues)
        required_clues = set(fragment.required_clues)
        
        return required_clues.issubset(user_clues)
