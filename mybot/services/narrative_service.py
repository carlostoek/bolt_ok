from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.models import User
from database.narrative_unified import NarrativeFragment, UserNarrativeState, UserDecisionLog

class NarrativeService:
    def __init__(self, session: AsyncSession, user_service=None, point_service=None, backpack_service=None):
        self.session = session
        self.user_service = user_service
        self.point_service = point_service
        self.backpack_service = backpack_service

    async def get_user_current_fragment(self, user_id: int):
        """
        Gets the current story fragment for a user.
        If they haven't started, returns the initial fragment.
        Updated for unified narrative system.
        """
        user_state = await self.session.execute(
            select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        )
        user_state = user_state.scalar_one_or_none()

        fragment_id = None
        if user_state and user_state.current_fragment_id:
            fragment_id = user_state.current_fragment_id
        
        if fragment_id:
            fragment = await self.session.execute(
                select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
            )
            fragment = fragment.scalar_one_or_none()
        else:
            fragment = None

        # Fallback: get first active fragment if no current fragment
        if not fragment:
            fragment = await self.session.execute(
                select(NarrativeFragment).where(
                    NarrativeFragment.is_active == True
                ).order_by(NarrativeFragment.created_at).limit(1)
            )
            fragment = fragment.scalar_one_or_none()
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
            
        return fragment

    # TODO: Update for unified narrative system - decisions are now stored in fragment choices JSON
    async def process_user_choice(self, user_id: int, fragment_id: str, choice_index: int):
        """
        Processes a choice from a fragment's choices JSON, checks conditions, and advances the story.
        Updated for unified narrative system.
        """
        # Get the fragment
        fragment = await self.session.execute(
            select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
        )
        fragment = fragment.scalar_one_or_none()

        if not fragment or choice_index >= len(fragment.choices):
            return None  # Fragment not found or invalid choice

        choice = fragment.choices[choice_index]
        
        # Log the decision with unified approach
        user_decision_log = UserDecisionLog(
            user_id=user_id, 
            fragment_id=fragment_id,
            decision_choice=choice.get('text', f'Choice {choice_index}'),
            points_awarded=choice.get('points', 0),
            clues_unlocked=choice.get('unlocks_clues', [])
        )
        self.session.add(user_decision_log)

        # Update user's narrative state
        user_state = await self.session.execute(
            select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        )
        user_state = user_state.scalar_one_or_none()

        next_fragment_id = choice.get('next_fragment_id')
        if user_state:
            user_state.current_fragment_id = next_fragment_id
            if fragment_id not in user_state.visited_fragments:
                user_state.visited_fragments.append(fragment_id)
            if fragment_id not in user_state.completed_fragments:
                user_state.completed_fragments.append(fragment_id)
            # Add unlocked clues
            for clue in choice.get('unlocks_clues', []):
                if clue not in user_state.unlocked_clues:
                    user_state.unlocked_clues.append(clue)
        else:
            user_state = UserNarrativeState(
                user_id=user_id, 
                current_fragment_id=next_fragment_id,
                visited_fragments=[fragment_id],
                completed_fragments=[fragment_id],
                unlocked_clues=choice.get('unlocks_clues', [])
            )
            self.session.add(user_state)
        
        await self.session.commit()
        await self.session.refresh(user_state)

        # Fetch and return the new fragment if specified
        if next_fragment_id:
            new_fragment = await self.session.execute(
                select(NarrativeFragment).where(NarrativeFragment.id == next_fragment_id)
            )
            return new_fragment.scalar_one_or_none()
        return None

    async def check_fragment_requirements(self, user_id: int, fragment: NarrativeFragment) -> bool:
        """
        Helper function to check if user meets requirements for accessing a fragment.
        Checks required clues in the unified system.
        """
        if not fragment.required_clues:
            return True  # No requirements
            
        # Get user's narrative state
        user_state = await self.session.execute(
            select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        )
        user_state = user_state.scalar_one_or_none()
        
        if not user_state:
            return False  # User hasn't started narrative
            
        # Check if user has all required clues
        user_clues = set(user_state.unlocked_clues)
        required_clues = set(fragment.required_clues)
        
        return required_clues.issubset(user_clues)
