"""
Emotional Analysis Service - Advanced emotional intelligence for narrative personalization.

This service provides sophisticated emotional analysis capabilities including:
- Real-time sentiment analysis from user interactions
- Emotional pattern recognition across user sessions
- Emotional state prediction and triggers identification  
- Contextual emotional memory with temporal patterns
- Emotional compatibility scoring for content adaptation

The service integrates seamlessly with the Narrative Adaptation Engine to provide
emotionally intelligent responses that feel genuinely attuned to each user.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from collections import deque, Counter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc, func

# Import our emotional state definitions
from .narrative_adaptation_engine import EmotionalState, EmotionalContext

logger = logging.getLogger(__name__)

class EmotionalIntensity(Enum):
    """Intensity levels for emotional states."""
    SUBTLE = 0.2
    MILD = 0.4
    MODERATE = 0.6
    STRONG = 0.8
    INTENSE = 1.0

class EmotionalTrigger(Enum):
    """Types of triggers that can cause emotional state changes."""
    NARRATIVE_CHOICE = "narrative_choice"
    CHARACTER_INTERACTION = "character_interaction"
    CONTENT_RESPONSE = "content_response"
    PROGRESSION_MILESTONE = "progression_milestone"
    SOCIAL_INTERACTION = "social_interaction"
    ACHIEVEMENT_UNLOCK = "achievement_unlock"
    TIME_PRESSURE = "time_pressure"
    SURPRISE_ELEMENT = "surprise_element"

@dataclass
class EmotionalSignal:
    """Individual emotional signal from user interaction."""
    signal_type: str
    intensity: float
    confidence: float
    timestamp: datetime
    source: str
    context: Dict[str, Any]

@dataclass
class EmotionalPattern:
    """Recognized pattern in user's emotional responses."""
    pattern_type: str
    frequency: float
    strength: float
    triggers: List[EmotionalTrigger]
    typical_duration: timedelta
    recovery_pattern: Optional[str]
    contextual_factors: Dict[str, Any]

@dataclass
class EmotionalProfile:
    """Comprehensive emotional profile for a user."""
    user_id: int
    baseline_state: EmotionalState
    emotional_volatility: float  # How quickly emotions change
    emotional_depth: float  # How deeply emotions are felt
    emotional_patterns: List[EmotionalPattern]
    trigger_sensitivity: Dict[EmotionalTrigger, float]
    recovery_speed: float  # How quickly user returns to baseline
    emotional_memory: List[Dict[str, Any]]  # Significant emotional moments
    last_analysis: datetime
    confidence_score: float

class EmotionalAnalysisService:
    """
    Advanced emotional analysis service for narrative personalization.
    
    This service provides the emotional intelligence backbone for the
    narrative adaptation engine, enabling truly empathetic responses.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Emotional analysis components
        self.sentiment_patterns = self._initialize_sentiment_patterns()
        self.emotional_lexicon = self._initialize_emotional_lexicon()
        self.context_analyzers = self._initialize_context_analyzers()
        
        # Temporal emotion tracking
        self.emotion_history: Dict[int, deque] = {}  # user_id -> recent emotions
        self.pattern_cache: Dict[int, List[EmotionalPattern]] = {}
        
        # Analysis confidence thresholds
        self.MIN_CONFIDENCE = 0.3
        self.PATTERN_MIN_OCCURRENCES = 3
        self.EMOTION_HISTORY_SIZE = 50
        
        logger.info("EmotionalAnalysisService initialized with advanced analysis capabilities")
    
    async def analyze_current_emotional_state(
        self, 
        user_id: int,
        interaction_data: Dict[str, Any],
        narrative_context: Dict[str, Any]
    ) -> EmotionalContext:
        """
        Analyze user's current emotional state from interaction data.
        
        This is the primary method for real-time emotional analysis that considers:
        - Text sentiment (if available)
        - Choice patterns and timing
        - Interaction frequency and intensity
        - Narrative context and progression
        - Historical emotional patterns
        """
        try:
            # Extract emotional signals from interaction
            signals = await self._extract_emotional_signals(interaction_data, narrative_context)
            
            # Get user's emotional profile
            profile = await self._get_emotional_profile(user_id)
            
            # Analyze current state based on signals and profile
            current_state = await self._determine_emotional_state(signals, profile)
            intensity = await self._calculate_emotional_intensity(signals, profile)
            
            # Identify triggers for this emotional state
            triggers = await self._identify_emotional_triggers(signals, interaction_data)
            
            # Predict emotional duration and volatility
            duration = await self._predict_emotional_duration(current_state, profile, signals)
            volatility = await self._calculate_emotional_volatility(profile, signals)
            
            # Build comprehensive emotional context
            context = EmotionalContext(
                current_state=current_state,
                intensity=intensity,
                previous_states=await self._get_recent_emotional_history(user_id),
                triggers=triggers,
                duration=duration,
                volatility=volatility
            )
            
            # Update user's emotional history
            await self._update_emotional_history(user_id, current_state, intensity, triggers)
            
            return context
            
        except Exception as e:
            logger.exception(f"Error analyzing emotional state for user {user_id}: {e}")
            # Return neutral emotional context as fallback
            return EmotionalContext(
                current_state=EmotionalState.CONTEMPLATIVE,
                intensity=0.5,
                previous_states=[],
                triggers={},
                duration=timedelta(minutes=5),
                volatility=0.3
            )
    
    async def predict_emotional_response(
        self,
        user_id: int,
        content_type: str,
        content_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict how a user will emotionally respond to specific content.
        
        This enables proactive content adaptation before showing content to the user.
        """
        profile = await self._get_emotional_profile(user_id)
        
        # Analyze content emotional signature
        content_emotional_profile = await self._analyze_content_emotional_signature(
            content_type, content_context
        )
        
        # Calculate emotional compatibility
        compatibility = await self._calculate_emotional_compatibility(
            profile, content_emotional_profile
        )
        
        # Predict likely emotional response
        predicted_state = await self._predict_response_state(
            profile, content_emotional_profile, compatibility
        )
        
        # Calculate confidence in prediction
        prediction_confidence = await self._calculate_prediction_confidence(
            profile, compatibility, content_context
        )
        
        return {
            "predicted_state": predicted_state.value,
            "predicted_intensity": compatibility.get("intensity", 0.5),
            "confidence": prediction_confidence,
            "compatibility_score": compatibility.get("score", 0.5),
            "recommended_adaptations": await self._recommend_emotional_adaptations(
                profile, predicted_state, compatibility
            )
        }
    
    async def identify_emotional_patterns(
        self, 
        user_id: int,
        lookback_days: int = 30
    ) -> List[EmotionalPattern]:
        """
        Identify recurring emotional patterns in user's interaction history.
        
        This provides insights into user's emotional rhythms and triggers
        that can be used for long-term personalization.
        """
        # Check cache first
        if user_id in self.pattern_cache:
            cached_patterns = self.pattern_cache[user_id]
            # Return cached patterns if recent enough
            if cached_patterns and any(
                datetime.now() - pattern.contextual_factors.get("last_updated", datetime.min) 
                < timedelta(hours=6) for pattern in cached_patterns
            ):
                return cached_patterns
        
        # Analyze emotional history for patterns
        emotional_history = await self._get_emotional_history(user_id, lookback_days)
        
        if not emotional_history:
            return []
        
        patterns = []
        
        # Identify state transition patterns
        transition_patterns = await self._find_transition_patterns(emotional_history)
        patterns.extend(transition_patterns)
        
        # Identify trigger-response patterns
        trigger_patterns = await self._find_trigger_patterns(emotional_history)
        patterns.extend(trigger_patterns)
        
        # Identify temporal patterns (time-based emotional rhythms)
        temporal_patterns = await self._find_temporal_patterns(emotional_history)
        patterns.extend(temporal_patterns)
        
        # Identify recovery patterns (how user returns to baseline)
        recovery_patterns = await self._find_recovery_patterns(emotional_history)
        patterns.extend(recovery_patterns)
        
        # Cache the patterns
        self.pattern_cache[user_id] = patterns
        
        return patterns
    
    async def calculate_emotional_compatibility(
        self,
        user_id: int,
        content_options: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Calculate emotional compatibility scores for multiple content options.
        
        This helps select the most emotionally appropriate content for the user.
        """
        profile = await self._get_emotional_profile(user_id)
        compatibility_scores = []
        
        for content in content_options:
            content_emotional_sig = await self._analyze_content_emotional_signature(
                content.get("type", "narrative"),
                content
            )
            
            compatibility = await self._calculate_emotional_compatibility(
                profile, content_emotional_sig
            )
            
            compatibility_scores.append((content, compatibility.get("score", 0.0)))
        
        # Sort by compatibility score (highest first)
        compatibility_scores.sort(key=lambda x: x[1], reverse=True)
        
        return compatibility_scores
    
    async def _extract_emotional_signals(
        self,
        interaction_data: Dict[str, Any],
        narrative_context: Dict[str, Any]
    ) -> List[EmotionalSignal]:
        """Extract emotional signals from various interaction sources."""
        signals = []
        
        # Analyze text input if available
        if "user_message" in interaction_data:
            text_signals = await self._analyze_text_sentiment(
                interaction_data["user_message"]
            )
            signals.extend(text_signals)
        
        # Analyze choice patterns
        if "choice_made" in interaction_data:
            choice_signals = await self._analyze_choice_emotional_signature(
                interaction_data["choice_made"], narrative_context
            )
            signals.extend(choice_signals)
        
        # Analyze timing patterns
        if "response_time" in interaction_data:
            timing_signals = await self._analyze_response_timing(
                interaction_data["response_time"]
            )
            signals.extend(timing_signals)
        
        # Analyze interaction frequency
        if "session_data" in interaction_data:
            frequency_signals = await self._analyze_interaction_frequency(
                interaction_data["session_data"]
            )
            signals.extend(frequency_signals)
        
        return signals
    
    async def _analyze_text_sentiment(self, text: str) -> List[EmotionalSignal]:
        """Analyze emotional content of text input."""
        signals = []
        
        # Use emotional lexicon for sentiment analysis
        emotional_scores = {}
        words = re.findall(r'\b\w+\b', text.lower())
        
        for word in words:
            if word in self.emotional_lexicon:
                emotion_data = self.emotional_lexicon[word]
                for emotion, score in emotion_data.items():
                    emotional_scores[emotion] = emotional_scores.get(emotion, 0) + score
        
        # Convert scores to signals
        for emotion, score in emotional_scores.items():
            if score > 0.1:  # Threshold for significance
                try:
                    emotional_state = EmotionalState(emotion)
                    signals.append(EmotionalSignal(
                        signal_type="text_sentiment",
                        intensity=min(score, 1.0),
                        confidence=0.7,
                        timestamp=datetime.now(),
                        source="user_text",
                        context={"word_count": len(words), "text_length": len(text)}
                    ))
                except ValueError:
                    # Skip invalid emotional states
                    continue
        
        return signals
    
    async def _analyze_choice_emotional_signature(
        self,
        choice_data: Dict[str, Any],
        narrative_context: Dict[str, Any]
    ) -> List[EmotionalSignal]:
        """Analyze the emotional signature of user choices."""
        signals = []
        
        choice_text = choice_data.get("text", "")
        choice_index = choice_data.get("index", 0)
        
        # Analyze choice content for emotional indicators
        emotional_keywords = {
            "passionate": ["passionate", "intense", "burning", "desire", "lust"],
            "romantic": ["love", "heart", "tender", "sweet", "gentle"],
            "playful": ["tease", "play", "fun", "laugh", "mischief"],
            "mysterious": ["secret", "hidden", "mystery", "unknown", "shadow"],
            "vulnerable": ["vulnerable", "open", "trust", "fear", "worry"],
            "confident": ["confident", "bold", "strong", "power", "control"]
        }
        
        choice_lower = choice_text.lower()
        for emotion, keywords in emotional_keywords.items():
            if any(keyword in choice_lower for keyword in keywords):
                try:
                    emotional_state = EmotionalState(emotion)
                    signals.append(EmotionalSignal(
                        signal_type="choice_content",
                        intensity=0.6,
                        confidence=0.8,
                        timestamp=datetime.now(),
                        source="user_choice",
                        context={
                            "choice_index": choice_index,
                            "choice_text": choice_text,
                            "narrative_level": narrative_context.get("level", 1)
                        }
                    ))
                except ValueError:
                    continue
        
        # Analyze choice timing and position
        if choice_index == 0:
            # First choice might indicate eagerness or default selection
            signals.append(EmotionalSignal(
                signal_type="choice_position",
                intensity=0.4,
                confidence=0.5,
                timestamp=datetime.now(),
                source="choice_pattern",
                context={"position": "first", "possible_meaning": "eager_or_default"}
            ))
        
        return signals
    
    async def _analyze_response_timing(self, response_time: float) -> List[EmotionalSignal]:
        """Analyze emotional implications of response timing."""
        signals = []
        
        # Very fast responses might indicate excitement or impulsiveness
        if response_time < 2.0:
            signals.append(EmotionalSignal(
                signal_type="response_timing",
                intensity=0.7,
                confidence=0.6,
                timestamp=datetime.now(),
                source="timing_analysis",
                context={
                    "response_time": response_time,
                    "interpretation": "quick_response",
                    "possible_emotions": ["excited", "eager", "impulsive"]
                }
            ))
        
        # Very slow responses might indicate contemplation or hesitation
        elif response_time > 30.0:
            signals.append(EmotionalSignal(
                signal_type="response_timing",
                intensity=0.5,
                confidence=0.7,
                timestamp=datetime.now(),
                source="timing_analysis",
                context={
                    "response_time": response_time,
                    "interpretation": "slow_response",
                    "possible_emotions": ["contemplative", "hesitant", "careful"]
                }
            ))
        
        return signals
    
    async def _get_emotional_profile(self, user_id: int) -> EmotionalProfile:
        """Get or create emotional profile for user."""
        # In full implementation, this would load from database
        # For now, create a default profile
        return EmotionalProfile(
            user_id=user_id,
            baseline_state=EmotionalState.CONTEMPLATIVE,
            emotional_volatility=0.3,
            emotional_depth=0.6,
            emotional_patterns=[],
            trigger_sensitivity={},
            recovery_speed=0.5,
            emotional_memory=[],
            last_analysis=datetime.now(),
            confidence_score=0.3
        )
    
    async def _determine_emotional_state(
        self,
        signals: List[EmotionalSignal],
        profile: EmotionalProfile
    ) -> EmotionalState:
        """Determine current emotional state from signals and profile."""
        if not signals:
            return profile.baseline_state
        
        # Weight signals by confidence and recency
        emotion_weights = Counter()
        
        for signal in signals:
            weight = signal.confidence * signal.intensity
            
            # Extract emotional implications from signal context
            if signal.signal_type == "choice_content":
                # Direct emotional indicator from choice content
                emotion_weights[signal.context.get("detected_emotion", "contemplative")] += weight
            elif signal.signal_type == "text_sentiment":
                # Extract from text analysis context
                emotion_weights["excited"] += weight * 0.8  # Text input often indicates engagement
            elif signal.signal_type == "response_timing":
                # Interpret timing signals
                possible_emotions = signal.context.get("possible_emotions", [])
                for emotion in possible_emotions:
                    if hasattr(EmotionalState, emotion.upper()):
                        emotion_weights[emotion] += weight * 0.6
        
        # Return most weighted emotion or baseline
        if emotion_weights:
            most_likely_emotion = emotion_weights.most_common(1)[0][0]
            try:
                return EmotionalState(most_likely_emotion)
            except ValueError:
                return profile.baseline_state
        
        return profile.baseline_state
    
    async def _calculate_emotional_intensity(
        self,
        signals: List[EmotionalSignal],
        profile: EmotionalProfile
    ) -> float:
        """Calculate emotional intensity from signals."""
        if not signals:
            return 0.3  # Low baseline intensity
        
        # Combine signal intensities with user's emotional depth profile
        total_intensity = sum(signal.intensity * signal.confidence for signal in signals)
        avg_intensity = total_intensity / len(signals) if signals else 0.3
        
        # Apply user's emotional depth factor
        adjusted_intensity = avg_intensity * profile.emotional_depth
        
        return min(adjusted_intensity, 1.0)
    
    async def _identify_emotional_triggers(
        self,
        signals: List[EmotionalSignal],
        interaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify what triggered the current emotional state."""
        triggers = {}
        
        for signal in signals:
            if signal.signal_type == "choice_content":
                triggers["narrative_choice"] = {
                    "choice_text": signal.context.get("choice_text"),
                    "choice_index": signal.context.get("choice_index"),
                    "emotional_weight": signal.intensity
                }
            elif signal.signal_type == "text_sentiment":
                triggers["user_expression"] = {
                    "word_count": signal.context.get("word_count"),
                    "emotional_weight": signal.intensity
                }
            elif signal.signal_type == "response_timing":
                triggers["timing_pattern"] = {
                    "response_time": signal.context.get("response_time"),
                    "interpretation": signal.context.get("interpretation"),
                    "emotional_weight": signal.intensity
                }
        
        return triggers
    
    # Additional helper methods (shortened for brevity)
    
    def _initialize_sentiment_patterns(self) -> Dict[str, Any]:
        """Initialize sentiment analysis patterns."""
        return {
            "excitement_patterns": [r"\b(wow|amazing|incredible|exciting)\b"],
            "romantic_patterns": [r"\b(love|heart|romantic|sweet)\b"],
            "playful_patterns": [r"\b(fun|play|tease|laugh)\b"]
        }
    
    def _initialize_emotional_lexicon(self) -> Dict[str, Dict[str, float]]:
        """Initialize emotional word lexicon."""
        return {
            "love": {"romantic": 0.9, "passionate": 0.7},
            "excited": {"excited": 1.0, "playful": 0.3},
            "mysterious": {"mysterious": 1.0, "contemplative": 0.5},
            "intense": {"passionate": 0.9, "intense": 1.0},
            "gentle": {"romantic": 0.6, "contemplative": 0.4},
            "bold": {"confident": 0.8, "excited": 0.4},
            "vulnerable": {"vulnerable": 1.0, "romantic": 0.3},
            "playful": {"playful": 1.0, "excited": 0.5}
        }
    
    def _initialize_context_analyzers(self) -> Dict[str, Any]:
        """Initialize contextual analysis components."""
        return {
            "narrative_context": {},
            "user_history": {},
            "interaction_patterns": {}
        }
    
    # Placeholder implementations for advanced methods
    async def _predict_emotional_duration(self, state: EmotionalState, profile: EmotionalProfile, signals: List[EmotionalSignal]) -> timedelta:
        return timedelta(minutes=10)  # Default duration
    
    async def _calculate_emotional_volatility(self, profile: EmotionalProfile, signals: List[EmotionalSignal]) -> float:
        return profile.emotional_volatility
    
    async def _get_recent_emotional_history(self, user_id: int) -> List[Tuple[EmotionalState, datetime]]:
        return []  # Would load from database
    
    async def _update_emotional_history(self, user_id: int, state: EmotionalState, intensity: float, triggers: Dict[str, Any]):
        pass  # Would update database
    
    async def _get_emotional_history(self, user_id: int, days: int) -> List[Dict[str, Any]]:
        return []  # Would load from database
    
    async def _find_transition_patterns(self, history: List[Dict[str, Any]]) -> List[EmotionalPattern]:
        return []  # Would analyze transition patterns
    
    async def _find_trigger_patterns(self, history: List[Dict[str, Any]]) -> List[EmotionalPattern]:
        return []  # Would analyze trigger patterns
    
    async def _find_temporal_patterns(self, history: List[Dict[str, Any]]) -> List[EmotionalPattern]:
        return []  # Would analyze temporal patterns
    
    async def _find_recovery_patterns(self, history: List[Dict[str, Any]]) -> List[EmotionalPattern]:
        return []  # Would analyze recovery patterns
    
    async def _analyze_content_emotional_signature(self, content_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"emotional_tone": "neutral", "intensity": 0.5}
    
    async def _calculate_emotional_compatibility(self, profile: EmotionalProfile, content_sig: Dict[str, Any]) -> Dict[str, Any]:
        return {"score": 0.7, "intensity": 0.6}
    
    async def _predict_response_state(self, profile: EmotionalProfile, content_sig: Dict[str, Any], compatibility: Dict[str, Any]) -> EmotionalState:
        return profile.baseline_state
    
    async def _calculate_prediction_confidence(self, profile: EmotionalProfile, compatibility: Dict[str, Any], context: Dict[str, Any]) -> float:
        return 0.7
    
    async def _recommend_emotional_adaptations(self, profile: EmotionalProfile, predicted_state: EmotionalState, compatibility: Dict[str, Any]) -> List[str]:
        return ["increase_emotional_intensity", "add_romantic_undertones"]
    
    async def _analyze_interaction_frequency(self, session_data: Dict[str, Any]) -> List[EmotionalSignal]:
        return []  # Would analyze frequency patterns