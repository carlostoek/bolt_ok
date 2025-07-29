"""
Emotional response service for managing character emotional states and user interactions.
This service tracks and manages emotional states within the narrative system.
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.future import select

from database.models import User
from database.narrative_models import StoryFragment, NarrativeChoice, UserNarrativeState

logger = logging.getLogger(__name__)

# Emotional state constants
EMOTION_STATES = {
    "joy": {
        "intensity_range": (0, 100),
        "default": 50,
        "decay_rate": 0.05,  # 5% decay per interaction
        "icon": "😊",
        "description": "Felicidad y alegría"
    },
    "trust": {
        "intensity_range": (0, 100),
        "default": 30,
        "decay_rate": 0.02,  # 2% decay per interaction
        "icon": "🤝",
        "description": "Confianza y seguridad"
    },
    "fear": {
        "intensity_range": (0, 100),
        "default": 20,
        "decay_rate": 0.08,  # 8% decay per interaction
        "icon": "😨",
        "description": "Miedo e inseguridad"
    },
    "sadness": {
        "intensity_range": (0, 100),
        "default": 15,
        "decay_rate": 0.03,  # 3% decay per interaction
        "icon": "😢",
        "description": "Tristeza y melancolía"
    },
    "anger": {
        "intensity_range": (0, 100),
        "default": 10,
        "decay_rate": 0.10,  # 10% decay per interaction
        "icon": "😠",
        "description": "Enfado e irritación"
    },
    "surprise": {
        "intensity_range": (0, 100),
        "default": 25,
        "decay_rate": 0.15,  # 15% decay per interaction
        "icon": "😲",
        "description": "Sorpresa y asombro"
    },
    "anticipation": {
        "intensity_range": (0, 100),
        "default": 40,
        "decay_rate": 0.04,  # 4% decay per interaction
        "icon": "🔮",
        "description": "Anticipación y expectativa"
    },
    "disgust": {
        "intensity_range": (0, 100),
        "default": 5,
        "decay_rate": 0.07,  # 7% decay per interaction
        "icon": "🤢",
        "description": "Disgusto y repulsión"
    }
}

# Character baseline emotional profiles
CHARACTER_BASELINES = {
    "Diana": {
        "joy": 60,
        "trust": 40,
        "fear": 15,
        "sadness": 20,
        "anger": 25,
        "surprise": 30,
        "anticipation": 65,
        "disgust": 10
    },
    "Lucien": {
        "joy": 50,
        "trust": 70,
        "fear": 10,
        "sadness": 15,
        "anger": 5,
        "surprise": 20,
        "anticipation": 45,
        "disgust": 5
    }
}


class EmotionalService:
    """Service for managing emotional responses in the narrative system."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_character_emotional_state(
        self, 
        user_id: int, 
        character_name: str
    ) -> Dict[str, Any]:
        """
        Get the current emotional state of a character for a specific user.
        This reflects how the character feels toward the user based on their interactions.
        
        Args:
            user_id: The user's ID
            character_name: The character's name (e.g., "Diana", "Lucien")
            
        Returns:
            Dictionary with emotional state information
        """
        try:
            # Get user's narrative state
            stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            result = await self.session.execute(stmt)
            user_state = result.scalar_one_or_none()
            
            if not user_state:
                # Return default emotional state if user hasn't started narrative
                return self._get_default_emotional_state(character_name)
            
            # Extract emotional state from user_state.choices_made
            # If not present, initialize with default values
            emotional_data = {}
            
            if user_state.choices_made and isinstance(user_state.choices_made, list):
                # Process historical choices to determine emotional state
                emotional_data = await self._calculate_emotional_state(
                    user_id, 
                    character_name, 
                    user_state.choices_made
                )
            else:
                emotional_data = self._get_default_emotional_state(character_name)
            
            # Add metadata to the response
            emotional_data["character"] = character_name
            emotional_data["user_id"] = user_id
            emotional_data["fragments_visited"] = user_state.fragments_visited
            emotional_data["dominant_emotion"] = self._get_dominant_emotion(emotional_data)
            
            return emotional_data
            
        except Exception as e:
            logger.error(f"Error getting emotional state for user {user_id} and character {character_name}: {e}")
            return self._get_default_emotional_state(character_name)
    
    async def update_emotional_state(
        self, 
        user_id: int,
        character_name: str,
        emotion_changes: Dict[str, int],
        interaction_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a character's emotional state based on a user interaction.
        
        Args:
            user_id: The user's ID
            character_name: The character's name
            emotion_changes: Dictionary of emotions to change and by how much
            interaction_context: Optional context for the interaction
            
        Returns:
            Updated emotional state
        """
        try:
            # Get current emotional state
            current_state = await self.get_character_emotional_state(user_id, character_name)
            
            # Update the state with new emotion values
            for emotion, change in emotion_changes.items():
                if emotion not in EMOTION_STATES:
                    continue
                
                # Get current value or default
                current_value = current_state.get(emotion, EMOTION_STATES[emotion]["default"])
                
                # Apply change and keep within range
                new_value = max(
                    min(
                        current_value + change,
                        EMOTION_STATES[emotion]["intensity_range"][1]
                    ),
                    EMOTION_STATES[emotion]["intensity_range"][0]
                )
                
                # Update the value
                current_state[emotion] = new_value
            
            # Store the updated state in the user's narrative state
            await self._store_emotional_state(user_id, character_name, current_state, interaction_context)
            
            # Recalculate dominant emotion
            current_state["dominant_emotion"] = self._get_dominant_emotion(current_state)
            
            return current_state
            
        except Exception as e:
            logger.error(f"Error updating emotional state for user {user_id} and character {character_name}: {e}")
            return await self.get_character_emotional_state(user_id, character_name)
    
    async def get_emotional_response(
        self, 
        user_id: int,
        character_name: str,
        context: str,
        intensity: Optional[float] = 1.0
    ) -> Dict[str, Any]:
        """
        Generate an emotional response based on the current emotional state.
        
        Args:
            user_id: The user's ID
            character_name: The character's name
            context: The context in which the response is generated
            intensity: Intensity multiplier for the emotional response
            
        Returns:
            Dictionary with response data including text modifications and suggestions
        """
        try:
            # Get current emotional state
            emotional_state = await self.get_character_emotional_state(user_id, character_name)
            
            # Determine dominant emotion and its intensity
            dominant_emotion = emotional_state["dominant_emotion"]
            
            # Generate response modifiers based on dominant emotion and intensity
            modifiers = self._generate_response_modifiers(
                dominant_emotion, 
                emotional_state[dominant_emotion], 
                intensity
            )
            
            # Get secondary emotions (next 2 highest)
            secondary_emotions = self._get_secondary_emotions(emotional_state, dominant_emotion)
            
            # Build response with all relevant emotional data
            response = {
                "character": character_name,
                "dominant_emotion": dominant_emotion,
                "dominant_intensity": emotional_state[dominant_emotion],
                "secondary_emotions": secondary_emotions,
                "context": context,
                "modifiers": modifiers,
                "emotional_state": {
                    emotion: value for emotion, value in emotional_state.items()
                    if emotion in EMOTION_STATES
                }
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating emotional response for user {user_id} and character {character_name}: {e}")
            return {
                "character": character_name,
                "dominant_emotion": "neutral",
                "dominant_intensity": 50,
                "secondary_emotions": [],
                "context": context,
                "modifiers": {
                    "text_prefixes": [],
                    "text_suffixes": [],
                    "style_suggestions": [],
                    "emoji_suggestions": []
                }
            }
    
    async def analyze_narrative_choice(
        self, 
        user_id: int,
        choice_id: int
    ) -> Dict[str, Any]:
        """
        Analyze the emotional impact of a narrative choice.
        
        Args:
            user_id: The user's ID
            choice_id: The ID of the choice being made
            
        Returns:
            Dictionary with emotional impact analysis
        """
        try:
            # Get the choice and related data
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
            
            # Get current emotional state
            emotional_state = await self.get_character_emotional_state(user_id, character_name)
            
            # Calculate emotional impact (placeholder for more sophisticated logic)
            # This would use NLP or predefined tags in a real implementation
            impact = self._calculate_choice_emotional_impact(choice, emotional_state)
            
            return {
                "choice_id": choice_id,
                "character": character_name,
                "choice_text": choice.text,
                "current_emotional_state": {
                    emotion: value for emotion, value in emotional_state.items()
                    if emotion in EMOTION_STATES
                },
                "emotional_impact": impact
            }
            
        except Exception as e:
            logger.error(f"Error analyzing narrative choice {choice_id} for user {user_id}: {e}")
            return {"error": str(e)}
    
    async def get_character_relationship(
        self, 
        user_id: int,
        character_name: str
    ) -> Dict[str, Any]:
        """
        Get the relationship status between a user and character.
        
        Args:
            user_id: The user's ID
            character_name: The character's name
            
        Returns:
            Dictionary with relationship data
        """
        try:
            # Get emotional state
            emotional_state = await self.get_character_emotional_state(user_id, character_name)
            
            # Calculate relationship metrics
            relationship = self._calculate_relationship_metrics(emotional_state)
            
            return {
                "user_id": user_id,
                "character": character_name,
                "relationship_status": relationship["status"],
                "relationship_level": relationship["level"],
                "description": relationship["description"],
                "positive_traits": relationship["positive_traits"],
                "challenging_traits": relationship["challenging_traits"],
                "trust_level": emotional_state.get("trust", 0),
                "joy_level": emotional_state.get("joy", 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting relationship data for user {user_id} and character {character_name}: {e}")
            return {
                "user_id": user_id,
                "character": character_name,
                "relationship_status": "neutral",
                "relationship_level": 1,
                "description": "Relación neutral",
                "positive_traits": [],
                "challenging_traits": [],
                "trust_level": 30,
                "joy_level": 30
            }
    
    # ----- Helper methods -----
    
    def _get_default_emotional_state(self, character_name: str) -> Dict[str, float]:
        """Get the default emotional state for a character."""
        if character_name in CHARACTER_BASELINES:
            state = CHARACTER_BASELINES[character_name].copy()
        else:
            # Generic default state if character not defined
            state = {emotion: config["default"] for emotion, config in EMOTION_STATES.items()}
        
        return state
    
    async def _calculate_emotional_state(
        self, 
        user_id: int,
        character_name: str,
        choices_made: List[Dict]
    ) -> Dict[str, float]:
        """
        Calculate emotional state based on historical choices.
        
        In a real implementation, this would analyze all choices and their
        emotional impacts to derive the current state.
        """
        # Start with baseline emotional profile
        state = self._get_default_emotional_state(character_name)
        
        # Process each choice to update emotional state
        # This is simplified logic - real implementation would be more sophisticated
        for choice_data in choices_made:
            choice_id = choice_data.get("choice_id")
            if not choice_id:
                continue
                
            # Get choice data
            stmt = select(NarrativeChoice).where(NarrativeChoice.id == choice_id)
            result = await self.session.execute(stmt)
            choice = result.scalar_one_or_none()
            
            if not choice:
                continue
                
            # Apply emotional impact of choice
            # This is simplified - would use NLP or predefined tags in real implementation
            choice_text_lower = choice.text.lower()
            
            # Very basic sentiment analysis as example
            if any(word in choice_text_lower for word in ["ayuda", "apoyar", "proteger", "confiar"]):
                state["trust"] = min(state["trust"] + 5, 100)
            elif any(word in choice_text_lower for word in ["miedo", "temer", "huir", "escapar"]):
                state["fear"] = min(state["fear"] + 5, 100)
            elif any(word in choice_text_lower for word in ["feliz", "alegre", "sonreír", "celebrar"]):
                state["joy"] = min(state["joy"] + 5, 100)
            elif any(word in choice_text_lower for word in ["triste", "llorar", "lamentar"]):
                state["sadness"] = min(state["sadness"] + 5, 100)
            elif any(word in choice_text_lower for word in ["enfad", "molest", "irritar", "frustrar"]):
                state["anger"] = min(state["anger"] + 5, 100)
            
            # Apply natural decay to all emotions
            for emotion in state:
                if emotion in EMOTION_STATES:
                    decay_rate = EMOTION_STATES[emotion]["decay_rate"]
                    baseline = CHARACTER_BASELINES.get(character_name, {}).get(emotion, EMOTION_STATES[emotion]["default"])
                    
                    # Move slightly toward baseline
                    if state[emotion] > baseline:
                        state[emotion] = max(state[emotion] - decay_rate * abs(state[emotion] - baseline), baseline)
                    elif state[emotion] < baseline:
                        state[emotion] = min(state[emotion] + decay_rate * abs(state[emotion] - baseline), baseline)
        
        return state
    
    async def _store_emotional_state(
        self, 
        user_id: int,
        character_name: str,
        emotional_state: Dict[str, float],
        interaction_context: Optional[str] = None
    ) -> None:
        """
        Store the updated emotional state in the user's narrative state.
        
        In a production implementation, this would likely be a separate database table.
        For now, we store it in the UserNarrativeState.choices_made field as extra metadata.
        """
        try:
            # Get user's narrative state
            stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            result = await self.session.execute(stmt)
            user_state = result.scalar_one_or_none()
            
            if not user_state:
                # Create new user state if it doesn't exist
                user_state = UserNarrativeState(
                    user_id=user_id,
                    current_fragment_key="start",
                    choices_made=[]
                )
                self.session.add(user_state)
            
            # Ensure choices_made exists and is a list
            if not user_state.choices_made or not isinstance(user_state.choices_made, list):
                user_state.choices_made = []
            
            # Add emotional state update record
            emotional_update = {
                "type": "emotional_update",
                "character": character_name,
                "timestamp": str(func.now()),
                "emotional_state": {
                    emotion: value for emotion, value in emotional_state.items()
                    if emotion in EMOTION_STATES
                },
                "context": interaction_context
            }
            
            # Append to choices_made
            user_state.choices_made.append(emotional_update)
            
            # Commit changes
            await self.session.commit()
            
        except Exception as e:
            logger.error(f"Error storing emotional state for user {user_id} and character {character_name}: {e}")
            # Roll back session in case of error
            await self.session.rollback()
    
    def _get_dominant_emotion(self, emotional_state: Dict[str, Any]) -> str:
        """Determine the dominant emotion from an emotional state."""
        # Filter out non-emotion keys
        emotions = {k: v for k, v in emotional_state.items() if k in EMOTION_STATES}
        
        if not emotions:
            return "neutral"
            
        # Return the emotion with the highest value
        return max(emotions.items(), key=lambda x: x[1])[0]
    
    def _get_secondary_emotions(
        self, 
        emotional_state: Dict[str, Any], 
        dominant_emotion: str
    ) -> List[Dict[str, Any]]:
        """Get the next two highest emotions after the dominant one."""
        # Filter out non-emotion keys and the dominant emotion
        emotions = {
            k: v for k, v in emotional_state.items() 
            if k in EMOTION_STATES and k != dominant_emotion
        }
        
        # Sort by intensity and take top 2
        sorted_emotions = sorted(emotions.items(), key=lambda x: x[1], reverse=True)[:2]
        
        # Format the response
        return [
            {"name": emotion, "intensity": intensity, "icon": EMOTION_STATES[emotion]["icon"]}
            for emotion, intensity in sorted_emotions
        ]
    
    def _generate_response_modifiers(
        self, 
        emotion: str, 
        intensity: float, 
        intensity_multiplier: float = 1.0
    ) -> Dict[str, Any]:
        """
        Generate text modifiers based on emotion and intensity.
        These suggestions help create emotionally appropriate responses.
        """
        # Adjust intensity with multiplier
        adjusted_intensity = min(intensity * intensity_multiplier, 100)
        
        # Default modifiers
        modifiers = {
            "text_prefixes": [],
            "text_suffixes": [],
            "style_suggestions": [],
            "emoji_suggestions": []
        }
        
        # Intensity level categorization
        if adjusted_intensity < 30:
            intensity_level = "low"
        elif adjusted_intensity < 70:
            intensity_level = "medium"
        else:
            intensity_level = "high"
        
        # Emotion-specific modifiers
        if emotion == "joy":
            modifiers["text_prefixes"] = ["¡", "Oh, "] if intensity_level in ["medium", "high"] else []
            modifiers["text_suffixes"] = ["!"] if intensity_level in ["medium", "high"] else ["."]
            modifiers["style_suggestions"] = ["tono alegre", "palabras positivas"]
            modifiers["emoji_suggestions"] = ["😊", "😄"] if intensity_level == "medium" else ["😁", "🥰", "✨"] if intensity_level == "high" else ["🙂"]
            
        elif emotion == "trust":
            modifiers["text_prefixes"] = ["Confío en que ", "Creo que "] if intensity_level in ["medium", "high"] else []
            modifiers["style_suggestions"] = ["tono confiado", "palabras reconfortantes"]
            modifiers["emoji_suggestions"] = ["🤝", "👍"] if intensity_level == "medium" else ["❤️", "🫂"] if intensity_level == "high" else ["👋"]
            
        elif emotion == "fear":
            modifiers["text_prefixes"] = ["Uhm... ", "Oh... "] if intensity_level in ["medium", "high"] else []
            modifiers["style_suggestions"] = ["tono nervioso", "palabras de preocupación"]
            modifiers["emoji_suggestions"] = ["😨", "😧"] if intensity_level == "medium" else ["😱", "🫣"] if intensity_level == "high" else ["😟"]
            
        elif emotion == "sadness":
            modifiers["text_prefixes"] = ["Ah... ", "Oh... "] if intensity_level in ["medium", "high"] else []
            modifiers["style_suggestions"] = ["tono melancólico", "palabras reflexivas"]
            modifiers["emoji_suggestions"] = ["😢", "😔"] if intensity_level == "medium" else ["😭", "💔"] if intensity_level == "high" else ["🙁"]
            
        elif emotion == "anger":
            modifiers["text_prefixes"] = ["Hmph. ", "¡"] if intensity_level in ["medium", "high"] else []
            modifiers["text_suffixes"] = ["!"] if intensity_level in ["medium", "high"] else ["."]
            modifiers["style_suggestions"] = ["tono firme", "palabras directas"]
            modifiers["emoji_suggestions"] = ["😠", "😤"] if intensity_level == "medium" else ["😡", "💢"] if intensity_level == "high" else ["😑"]
            
        elif emotion == "surprise":
            modifiers["text_prefixes"] = ["¡", "Wow, "] if intensity_level in ["medium", "high"] else []
            modifiers["text_suffixes"] = ["!"] if intensity_level in ["medium", "high"] else ["."]
            modifiers["style_suggestions"] = ["tono asombrado", "palabras de sorpresa"]
            modifiers["emoji_suggestions"] = ["😲", "😮"] if intensity_level == "medium" else ["😱", "🤯"] if intensity_level == "high" else ["😯"]
            
        elif emotion == "anticipation":
            modifiers["text_prefixes"] = ["Hmm... ", "Oh, "] if intensity_level in ["medium", "high"] else []
            modifiers["style_suggestions"] = ["tono expectante", "palabras de anticipación"]
            modifiers["emoji_suggestions"] = ["🔮", "👀"] if intensity_level == "medium" else ["✨", "🌟"] if intensity_level == "high" else ["🤔"]
            
        elif emotion == "disgust":
            modifiers["text_prefixes"] = ["Ugh... ", "Hmm... "] if intensity_level in ["medium", "high"] else []
            modifiers["style_suggestions"] = ["tono desagradado", "palabras de rechazo"]
            modifiers["emoji_suggestions"] = ["🤢", "😖"] if intensity_level == "medium" else ["🤮", "😫"] if intensity_level == "high" else ["😒"]
            
        else:  # neutral
            modifiers["style_suggestions"] = ["tono neutral", "palabras equilibradas"]
            modifiers["emoji_suggestions"] = ["🙂", "👋"]
        
        return modifiers
    
    def _calculate_choice_emotional_impact(
        self, 
        choice: NarrativeChoice,
        current_state: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Calculate the emotional impact of a choice.
        This is a simplified implementation and would be more sophisticated in production.
        """
        # Simplified impact calculation based on choice text
        impact = {}
        choice_text_lower = choice.text.lower()
        
        # Very basic sentiment analysis
        if any(word in choice_text_lower for word in ["ayuda", "apoyar", "proteger", "confiar"]):
            impact["trust"] = 5
            impact["joy"] = 3
        elif any(word in choice_text_lower for word in ["miedo", "temer", "huir", "escapar"]):
            impact["fear"] = 5
            impact["trust"] = -2
        elif any(word in choice_text_lower for word in ["feliz", "alegre", "sonreír", "celebrar"]):
            impact["joy"] = 5
            impact["sadness"] = -3
        elif any(word in choice_text_lower for word in ["triste", "llorar", "lamentar"]):
            impact["sadness"] = 5
            impact["joy"] = -3
        elif any(word in choice_text_lower for word in ["enfad", "molest", "irritar", "frustrar"]):
            impact["anger"] = 5
            impact["trust"] = -2
        
        # Default minimal impact if no keywords matched
        if not impact:
            # Small random variations
            import random
            impact = {
                emotion: random.uniform(-1, 1) for emotion in EMOTION_STATES
            }
        
        # Format the response
        formatted_impact = {
            "primary_changes": [
                {"emotion": emotion, "change": change, "icon": EMOTION_STATES[emotion]["icon"]}
                for emotion, change in impact.items() if abs(change) >= 2
            ],
            "secondary_changes": [
                {"emotion": emotion, "change": change, "icon": EMOTION_STATES[emotion]["icon"]}
                for emotion, change in impact.items() if 0 < abs(change) < 2
            ],
            "predicted_state": {
                emotion: min(max(current_state.get(emotion, EMOTION_STATES[emotion]["default"]) + impact.get(emotion, 0), 0), 100)
                for emotion in EMOTION_STATES
            }
        }
        
        return formatted_impact
    
    def _calculate_relationship_metrics(self, emotional_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate relationship metrics based on emotional state.
        """
        # Extract relevant emotions
        trust = emotional_state.get("trust", 30)
        joy = emotional_state.get("joy", 30)
        anger = emotional_state.get("anger", 10)
        fear = emotional_state.get("fear", 20)
        
        # Calculate relationship level (1-5)
        level_base = (trust + joy) / 2
        level_penalty = (anger + fear) / 4
        relationship_score = level_base - level_penalty
        
        if relationship_score < 20:
            level = 1
            status = "distante"
            description = "Relación tensa y distante"
        elif relationship_score < 40:
            level = 2
            status = "cautelosa"
            description = "Relación cautelosa con momentos de tensión"
        elif relationship_score < 60:
            level = 3
            status = "neutral"
            description = "Relación neutral y cordial"
        elif relationship_score < 80:
            level = 4
            status = "amistosa"
            description = "Relación amistosa y cercana"
        else:
            level = 5
            status = "íntima"
            description = "Relación íntima y de profunda confianza"
        
        # Determine relationship traits
        positive_traits = []
        challenging_traits = []
        
        # Assign traits based on emotional values
        if trust > 70:
            positive_traits.append("confianza profunda")
        elif trust > 50:
            positive_traits.append("honestidad")
        elif trust < 30:
            challenging_traits.append("desconfianza")
            
        if joy > 70:
            positive_traits.append("alegría compartida")
        elif joy > 50:
            positive_traits.append("momentos felices")
        elif joy < 30:
            challenging_traits.append("falta de alegría")
            
        if anger > 50:
            challenging_traits.append("tensión")
        elif anger > 30:
            challenging_traits.append("momentos de irritación")
            
        if fear > 50:
            challenging_traits.append("inseguridad")
        elif fear > 30:
            challenging_traits.append("cautela")
        
        return {
            "status": status,
            "level": level,
            "description": description,
            "positive_traits": positive_traits,
            "challenging_traits": challenging_traits
        }