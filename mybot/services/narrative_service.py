from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from database.models import User
from database.narrative_unified import NarrativeFragment, UserNarrativeState, UserDecisionLog

class NarrativeService:
    def __init__(self, session: AsyncSession, user_service=None, point_service=None, backpack_service=None):
        self.session = session
        self.user_service = user_service
        self.point_service = point_service
        self.backpack_service = backpack_service
        
        # Optional Cinema System Integration
        self.cinema_master = None
        try:
            from .cinema_master_integration import get_cinema_master_integration
            self.cinema_master = get_cinema_master_integration(session)
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Cinema Master Integration available for NarrativeService")
        except ImportError:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Cinema Master Integration not available for NarrativeService")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to initialize Cinema Master Integration: {e}")

    async def get_user_current_fragment(self, user_id: int):
        """
        Gets the current story fragment for a user with optimized loading.
        If they haven't started, returns the initial fragment.
        Updated for unified narrative system with performance optimizations.
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
            # Use already loaded fragment from user_state if available
            if user_state and user_state.current_fragment:
                fragment = user_state.current_fragment
            else:
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
        Updated for unified narrative system with performance optimizations.
        """
        # Get the fragment (optimized query)
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

        # Update user's narrative state (optimized query)
        user_state = await self.session.execute(
            select(UserNarrativeState)
            .options(selectinload(UserNarrativeState.user))
            .where(UserNarrativeState.user_id == user_id)
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

    # ==================== CINEMA ENHANCED METHODS ====================
    
    async def get_fragment_with_choice_architecture(self, fragment_key: str, user_id: int, **kwargs) -> Dict[str, Any]:
        """
        Enhanced fragment retrieval with choice architecture integration.
        Falls back to standard functionality if cinema systems unavailable.
        
        Args:
            fragment_key: Fragment key
            user_id: User ID
            **kwargs: Additional parameters for choice architecture
            
        Returns:
            Enhanced fragment data with choice architecture if available
        """
        try:
            # Get standard fragment
            fragment = await self.get_fragment_by_key(fragment_key)
            
            result = {
                "fragment": fragment,
                "enhanced": False,
                "choices_enhanced": False
            }
            
            if not fragment:
                return result
            
            # Try choice architecture enhancement
            if (self.cinema_master and 
                self.cinema_master.is_choice_architecture_available() and 
                fragment.choices):
                
                try:
                    choice_architecture = getattr(self.cinema_master, 'choice_architecture', None)
                    if choice_architecture and hasattr(choice_architecture, 'enhance_fragment_choices'):
                        enhanced_choices = await choice_architecture.enhance_fragment_choices(
                            user_id, fragment, **kwargs
                        )
                        if enhanced_choices:
                            result.update({
                                "enhanced_choices": enhanced_choices,
                                "choices_enhanced": True,
                                "enhanced": True,
                                "enhancement_type": "choice_architecture"
                            })
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Choice architecture enhancement failed for fragment {fragment_key}: {e}")
            
            return result
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Error in get_fragment_with_choice_architecture for {fragment_key}: {e}")
            # Fallback to standard fragment
            fragment = await self.get_fragment_by_key(fragment_key)
            return {
                "fragment": fragment,
                "enhanced": False,
                "fallback_used": True,
                "error": str(e)
            }
    
    async def process_user_choice_enhanced(self, user_id: int, fragment_id: str, choice_text: str, **kwargs) -> Dict[str, Any]:
        """
        Enhanced choice processing with decision consequence tracking and personalization.
        
        Args:
            user_id: User ID
            fragment_id: Current fragment ID
            choice_text: Chosen text
            **kwargs: Additional parameters for enhancement
            
        Returns:
            Enhanced choice processing result
        """
        try:
            # Execute standard choice processing
            standard_result = await self.process_user_choice(user_id, fragment_id, choice_text)
            
            result = {
                "success": bool(standard_result),
                "next_fragment": standard_result,
                "enhanced": False
            }
            
            # Try cinema enhancements
            if self.cinema_master and self.cinema_master.cinema_active:
                try:
                    # Create decision data for enhancement
                    decision_data = {
                        "fragment_id": fragment_id,
                        "choice_text": choice_text,
                        "next_fragment": standard_result,
                        "user_id": user_id
                    }
                    
                    enhanced_result = await self.cinema_master.enhance_decision_experience(
                        user_id, fragment_id, decision_data
                    )
                    
                    if enhanced_result:
                        result.update(enhanced_result)
                        result["enhanced"] = True
                        
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Cinema enhancement failed for choice processing: {e}")
            
            return result
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Error in process_user_choice_enhanced: {e}")
            return {
                "success": False,
                "error": str(e),
                "enhanced": False,
                "fallback_available": True
            }
    
    async def get_narrative_recommendations(self, user_id: int, fragment_id: str = None) -> List[Dict[str, Any]]:
        """
        Get personalized narrative recommendations based on user's soul signature.
        
        Args:
            user_id: User ID
            fragment_id: Current fragment ID (optional)
            
        Returns:
            List of recommended fragments with personalization data
        """
        try:
            # Get all available fragments as base recommendations
            available_fragments = []
            
            # Get fragments user can access
            if fragment_id:
                current_fragment = await self.get_fragment_by_key(fragment_id)
                if current_fragment and current_fragment.choices:
                    # Get next fragments from choices
                    for choice in current_fragment.choices:
                        next_fragment_id = choice.get('next_fragment')
                        if next_fragment_id:
                            next_fragment = await self.get_fragment_by_key(next_fragment_id)
                            if next_fragment and await self.check_fragment_requirements(user_id, next_fragment):
                                available_fragments.append(next_fragment)
            
            recommendations = []
            
            # If no cinema enhancement, return basic recommendations
            if not self.cinema_master or not self.cinema_master.is_soul_signature_available():
                return [{"fragment": f, "personalized": False, "recommendation_score": 0.5} for f in available_fragments]
            
            # Apply soul signature personalization to recommendations
            soul_signature = getattr(self.cinema_master, 'soul_signature', None)
            if soul_signature and hasattr(soul_signature, 'get_narrative_recommendations'):
                try:
                    personalized_recommendations = await soul_signature.get_narrative_recommendations(
                        user_id, available_fragments, fragment_id
                    )
                    recommendations.extend(personalized_recommendations)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Personalized recommendations failed for user {user_id}: {e}")
                    # Fallback to basic recommendations
                    recommendations = [{"fragment": f, "personalized": False, "recommendation_score": 0.5} for f in available_fragments]
            else:
                recommendations = [{"fragment": f, "personalized": False, "recommendation_score": 0.5} for f in available_fragments]
            
            return recommendations
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f"Error in get_narrative_recommendations for user {user_id}: {e}")
            return []
