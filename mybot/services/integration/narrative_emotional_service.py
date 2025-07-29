"""
Integration service connecting narrative and emotional systems.
Manages the emotional context of narrative interactions.
"""
import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..narrative_service import NarrativeService
from ..emotional_service import EmotionalService
from ..point_service import PointService
from database.narrative_models import NarrativeChoice, StoryFragment

logger = logging.getLogger(__name__)

class NarrativeEmotionalService:
    """
    Integration service that connects the narrative system with emotional state.
    Allows narrative choices to affect emotional states and vice versa.
    """
    
    def __init__(self, session: AsyncSession, bot=None):
        self.session = session
        self.bot = bot
        self.narrative_service = NarrativeService(session)
        self.emotional_service = EmotionalService(session)
        self.point_service = PointService(session)
    
    async def get_emotionally_enhanced_fragment(
        self, 
        user_id: int, 
        fragment_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a narrative fragment with emotional context.
        If fragment_key is not provided, gets the user's current fragment.
        
        Args:
            user_id: The user's ID
            fragment_key: Optional specific fragment key to retrieve
            
        Returns:
            Dictionary with fragment data and emotional context
        """
        try:
            # Get the fragment
            if fragment_key:
                # Get specific fragment
                stmt = select(StoryFragment).where(StoryFragment.key == fragment_key)
                result = await self.session.execute(stmt)
                fragment = result.scalar_one_or_none()
                
                if not fragment:
                    return {"error": "Fragment not found"}
            else:
                # Get user's current fragment
                user_state = await self.narrative_service.get_user_current_fragment(user_id)
                
                if not user_state:
                    return {"error": "User has no current fragment"}
                    
                fragment = user_state
            
            # Get character's emotional state
            character_name = fragment.character
            emotional_state = await self.emotional_service.get_character_emotional_state(
                user_id, 
                character_name
            )
            
            # Get emotional response modifiers
            emotional_response = await self.emotional_service.get_emotional_response(
                user_id,
                character_name,
                fragment.text
            )
            
            # Enhance choices with emotional preview if available
            enhanced_choices = []
            for choice in fragment.choices:
                choice_impact = await self.emotional_service.analyze_narrative_choice(
                    user_id, 
                    choice.id
                )
                
                enhanced_choice = {
                    "id": choice.id,
                    "text": choice.text,
                    "required_besitos": choice.required_besitos,
                    "required_role": choice.required_role,
                    "emotional_impact": choice_impact.get("emotional_impact", {})
                }
                
                enhanced_choices.append(enhanced_choice)
            
            # Build the enhanced fragment
            enhanced_fragment = {
                "fragment": {
                    "key": fragment.key,
                    "text": fragment.text,
                    "character": fragment.character,
                    "level": fragment.level,
                    "min_besitos": fragment.min_besitos,
                    "required_role": fragment.required_role,
                    "reward_besitos": fragment.reward_besitos,
                    "auto_next_fragment_key": getattr(fragment, "auto_next_fragment_key", None)
                },
                "emotional_context": {
                    "character": character_name,
                    "dominant_emotion": emotional_state["dominant_emotion"],
                    "emotional_state": {
                        emotion: value for emotion, value in emotional_state.items()
                        if emotion in ["joy", "trust", "fear", "sadness", "anger", "surprise", "anticipation", "disgust"]
                    },
                    "response_modifiers": emotional_response["modifiers"]
                },
                "choices": enhanced_choices
            }
            
            return enhanced_fragment
            
        except Exception as e:
            logger.error(f"Error getting emotionally enhanced fragment for user {user_id}: {e}")
            return {"error": str(e)}
    
    async def process_narrative_choice_with_emotions(
        self, 
        user_id: int, 
        choice_id: int
    ) -> Dict[str, Any]:
        """
        Process a narrative choice with emotional state updates.
        
        Args:
            user_id: The user's ID
            choice_id: The choice ID being made
            
        Returns:
            Dict with next fragment and emotional changes
        """
        try:
            # Get the choice
            stmt = select(NarrativeChoice).where(NarrativeChoice.id == choice_id)
            result = await self.session.execute(stmt)
            choice = result.scalar_one_or_none()
            
            if not choice:
                return {"error": "Choice not found"}
            
            # Get source fragment for character information
            source_fragment = await self.session.get(StoryFragment, choice.source_fragment_id)
            
            if not source_fragment:
                return {"error": "Source fragment not found"}
            
            character_name = source_fragment.character
            
            # Analyze the emotional impact of the choice
            emotional_impact = await self.emotional_service.analyze_narrative_choice(
                user_id, 
                choice_id
            )
            
            # Update the emotional state based on the choice
            primary_changes = emotional_impact.get("emotional_impact", {}).get("primary_changes", [])
            emotion_changes = {
                item["emotion"]: item["change"] 
                for item in primary_changes
            }
            
            # Process the choice in the narrative system
            next_fragment = await self.narrative_service.process_user_decision(user_id, choice_id)
            
            if not next_fragment:
                return {"error": "Failed to process narrative choice"}
            
            # Apply emotional state changes
            if emotion_changes:
                await self.emotional_service.update_emotional_state(
                    user_id,
                    character_name,
                    emotion_changes,
                    f"Choice: {choice.text}"
                )
            
            # Get the emotionally enhanced next fragment
            enhanced_fragment = await self.get_emotionally_enhanced_fragment(
                user_id,
                next_fragment.key
            )
            
            # Process any besitos rewards from the fragment
            if next_fragment.reward_besitos > 0:
                await self.point_service.add_points(
                    user_id,
                    next_fragment.reward_besitos,
                    reason="narrative_progress",
                    bot=self.bot
                )
            
            # Add emotional changes information
            enhanced_fragment["emotional_changes"] = {
                "changes": primary_changes,
                "previous_dominant": emotional_impact.get("current_emotional_state", {}).get("dominant_emotion", "neutral"),
                "new_dominant": enhanced_fragment.get("emotional_context", {}).get("dominant_emotion", "neutral")
            }
            
            return enhanced_fragment
            
        except Exception as e:
            logger.error(f"Error processing narrative choice with emotions for user {user_id}, choice {choice_id}: {e}")
            return {"error": str(e)}
    
    async def get_character_relationship_status(
        self, 
        user_id: int,
        character_name: str
    ) -> Dict[str, Any]:
        """
        Get the relationship status between user and character.
        
        Args:
            user_id: The user's ID
            character_name: The character's name
            
        Returns:
            Dict with relationship information
        """
        try:
            # Get relationship data
            relationship = await self.emotional_service.get_character_relationship(
                user_id,
                character_name
            )
            
            # Get narrative progress data
            user_state = await self.session.execute(
                select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            )
            user_state = user_state.scalar_one_or_none()
            
            # Combine data
            relationship_data = {
                "user_id": user_id,
                "character": character_name,
                "relationship_status": relationship["relationship_status"],
                "relationship_level": relationship["relationship_level"],
                "description": relationship["description"],
                "positive_traits": relationship["positive_traits"],
                "challenging_traits": relationship["challenging_traits"],
                "narrative_progress": {
                    "fragments_visited": user_state.fragments_visited if user_state else 0,
                    "current_fragment": user_state.current_fragment_key if user_state else None,
                    "choices_made": len(user_state.choices_made) if user_state and user_state.choices_made else 0
                }
            }
            
            return relationship_data
            
        except Exception as e:
            logger.error(f"Error getting character relationship for user {user_id}, character {character_name}: {e}")
            return {"error": str(e)}
    
    async def generate_emotionally_consistent_responses(
        self,
        user_id: int,
        character_name: str,
        context: str,
        options_count: int = 3
    ) -> Dict[str, Any]:
        """
        Generate multiple response options consistent with emotional state.
        
        Args:
            user_id: The user's ID
            character_name: The character name
            context: The conversation context
            options_count: Number of options to generate
            
        Returns:
            Dict with response options
        """
        try:
            # Get emotional state
            emotional_response = await self.emotional_service.get_emotional_response(
                user_id,
                character_name,
                context
            )
            
            # Generate response options based on emotional modifiers
            # In a real implementation, this might use a more sophisticated 
            # text generation system or templates
            
            # For now, return suggested modifiers for manual implementation
            response_options = {
                "character": character_name,
                "context": context,
                "dominant_emotion": emotional_response["dominant_emotion"],
                "dominant_intensity": emotional_response["dominant_intensity"],
                "modifiers": emotional_response["modifiers"],
                "secondary_emotions": emotional_response["secondary_emotions"],
                "implementation_note": "This would return generated text options in a real implementation"
            }
            
            return response_options
            
        except Exception as e:
            logger.error(f"Error generating emotional responses for user {user_id}, character {character_name}: {e}")
            return {"error": str(e)}