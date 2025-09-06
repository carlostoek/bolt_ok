"""
Emotional State Machine - 6-Level Emotional Crescendo System
Tracks and manages user emotional progression with Diana across 6 distinct levels.
Preserves emotional essence while maintaining technical precision.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, desc
from sqlalchemy.orm import selectinload

from database.models import User
from database.narrative_unified import UserNarrativeState
from .event_bus import get_event_bus, EventType
from .user_service import UserService

logger = logging.getLogger(__name__)

class EmotionalLevel(Enum):
    """
    Six levels of emotional progression with Diana.
    Each level represents deeper emotional intimacy and character development.
    """
    CURIOSITY = 1        # Initial attraction and mystery
    INTRIGUE = 2         # Growing interest and light flirtation  
    TENSION = 3          # Sexual tension and deeper conversation
    VULNERABILITY = 4    # Sharing secrets and emotional openness
    PASSION = 5          # Intense emotional and physical connection
    SOUL_BOND = 6        # Complete emotional and spiritual unity

class EmotionalTransitionType(Enum):
    """Types of emotional transitions between levels."""
    GRADUAL = "gradual"           # Natural progression over time
    BREAKTHROUGH = "breakthrough"  # Sudden leap forward
    REVELATION = "revelation"      # Triggered by character revelation
    CHOICE_IMPACT = "choice_impact"  # Triggered by significant choice
    VULNERABILITY_MOMENT = "vulnerability_moment"  # Sharing deep truth

@dataclass
class EmotionalStateData:
    """Complete emotional state information for a user."""
    user_id: int
    current_level: EmotionalLevel
    level_progress: float  # 0.0 to 1.0 within current level
    trust_score: float     # Overall trust in Diana (0-100)
    vulnerability_capacity: float  # Ability to handle emotional depth (0-100)
    authenticity_score: float     # How genuine user appears (0-100)
    
    # Progression tracking
    time_in_current_level: timedelta
    total_interactions: int
    breakthrough_moments: int
    
    # Recent emotional indicators
    recent_response_patterns: Dict[str, float]
    emotional_stability: float  # How consistent emotional responses are
    
    # Level-specific metrics
    level_specific_data: Dict[str, Any]
    
    # Timing and transitions
    last_level_advancement: Optional[datetime]
    next_transition_probability: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/transmission."""
        return asdict(self)

class EmotionalStateMachine:
    """
    Advanced emotional state machine managing user progression through 6 levels.
    
    Tracks emotional development, triggers character evolution moments,
    and maintains Diana's personality consistency across all levels.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize emotional state machine.
        
        Args:
            session: Database session for state persistence
        """
        self.session = session
        self.user_service = UserService(session)
        self.event_bus = get_event_bus()
        
        # Level progression requirements
        self.level_requirements = self._initialize_level_requirements()
        
        # Character personality by level
        self.diana_personalities = self._initialize_diana_personalities()
        
        # Emotional memory cache
        self._state_cache: Dict[int, EmotionalStateData] = {}
        
        # Performance optimization
        self._cache_ttl = timedelta(minutes=5)
        self._last_cache_clear = datetime.utcnow()
    
    async def initialize(self) -> None:
        """Initialize the emotional state machine."""
        logger.info("Emotional State Machine initialized")
    
    # ==================== CORE STATE MANAGEMENT ====================
    
    async def get_user_emotional_state(self, user_id: int) -> EmotionalStateData:
        """
        Get comprehensive emotional state for user.
        
        Args:
            user_id: User ID
            
        Returns:
            Complete emotional state data
        """
        # Check cache first
        if user_id in self._state_cache:
            cached_state = self._state_cache[user_id]
            # Return cached if recent
            if datetime.utcnow() - cached_state.last_level_advancement < self._cache_ttl:
                return cached_state
        
        # Build emotional state from database
        emotional_state = await self._build_emotional_state(user_id)
        
        # Cache the state
        self._state_cache[user_id] = emotional_state
        
        return emotional_state
    
    async def _build_emotional_state(self, user_id: int) -> EmotionalStateData:
        """
        Build emotional state from database data.
        """
        try:
            # Get user data
            user = await self.user_service.get_user(user_id)
            if not user:
                return self._create_initial_emotional_state(user_id)
            
            # Get narrative state for emotional context
            narrative_state = await self._get_user_narrative_state(user_id)
            
            # Determine current emotional level from user progress
            current_level = await self._calculate_current_emotional_level(
                user, narrative_state
            )
            
            # Calculate level progress
            level_progress = await self._calculate_level_progress(
                user_id, current_level, narrative_state
            )
            
            # Calculate emotional metrics
            trust_score = await self._calculate_trust_score(user, narrative_state)
            vulnerability_capacity = await self._calculate_vulnerability_capacity(user, narrative_state)
            authenticity_score = await self._calculate_authenticity_score(user)
            
            # Get interaction statistics
            total_interactions = await self._get_total_interactions(user_id)
            breakthrough_moments = await self._get_breakthrough_moments(user_id)
            
            # Calculate time in current level
            time_in_level = await self._calculate_time_in_level(user_id, current_level)
            
            # Get recent emotional patterns
            recent_patterns = await self._analyze_recent_patterns(user_id)
            
            # Calculate emotional stability
            stability = self._calculate_emotional_stability(recent_patterns)
            
            # Level-specific data
            level_data = await self._get_level_specific_data(user_id, current_level)
            
            # Transition probability
            transition_prob = await self._calculate_transition_probability(
                current_level, level_progress, trust_score, vulnerability_capacity
            )
            
            return EmotionalStateData(
                user_id=user_id,
                current_level=current_level,
                level_progress=level_progress,
                trust_score=trust_score,
                vulnerability_capacity=vulnerability_capacity,
                authenticity_score=authenticity_score,
                time_in_current_level=time_in_level,
                total_interactions=total_interactions,
                breakthrough_moments=breakthrough_moments,
                recent_response_patterns=recent_patterns,
                emotional_stability=stability,
                level_specific_data=level_data,
                last_level_advancement=user.updated_at,
                next_transition_probability=transition_prob
            )
            
        except Exception as e:
            logger.exception(f"Error building emotional state for user {user_id}: {e}")
            return self._create_initial_emotional_state(user_id)
    
    def _create_initial_emotional_state(self, user_id: int) -> EmotionalStateData:
        """Create initial emotional state for new user."""
        return EmotionalStateData(
            user_id=user_id,
            current_level=EmotionalLevel.CURIOSITY,
            level_progress=0.0,
            trust_score=50.0,
            vulnerability_capacity=30.0,
            authenticity_score=50.0,
            time_in_current_level=timedelta(0),
            total_interactions=0,
            breakthrough_moments=0,
            recent_response_patterns={},
            emotional_stability=0.5,
            level_specific_data={},
            last_level_advancement=datetime.utcnow(),
            next_transition_probability=0.1
        )
    
    # ==================== EMOTIONAL PROGRESSION ====================
    
    async def process_user_interaction(
        self,
        user_id: int,
        interaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process user interaction and update emotional state.
        
        Args:
            user_id: User ID
            interaction_data: Data about the interaction
            
        Returns:
            Result of processing including any level changes
        """
        try:
            # Get current emotional state
            current_state = await self.get_user_emotional_state(user_id)
            
            # Analyze interaction impact
            emotional_impact = await self._analyze_interaction_impact(
                interaction_data, current_state
            )
            
            # Update emotional metrics
            updated_state = await self._update_emotional_metrics(
                current_state, emotional_impact
            )
            
            # Check for level advancement
            advancement_result = await self._check_level_advancement(
                updated_state, emotional_impact
            )
            
            # Persist state changes
            await self._persist_emotional_state(updated_state)
            
            # Update cache
            self._state_cache[user_id] = updated_state
            
            # Emit emotional evolution event
            await self.event_bus.publish(
                EventType.NARRATIVE_DECISION,  # Reusing existing event type
                user_id,
                {
                    "type": "emotional_interaction",
                    "current_level": updated_state.current_level.value,
                    "progress": updated_state.level_progress,
                    "impact": emotional_impact,
                    "advancement": advancement_result
                },
                source="emotional_state_machine"
            )
            
            result = {
                "success": True,
                "current_level": updated_state.current_level,
                "level_progress": updated_state.level_progress,
                "emotional_impact": emotional_impact,
                "trust_change": emotional_impact.get("trust_delta", 0),
                "vulnerability_change": emotional_impact.get("vulnerability_delta", 0)
            }
            
            if advancement_result.get("advanced"):
                result.update(advancement_result)
                
            return result
            
        except Exception as e:
            logger.exception(f"Error processing emotional interaction for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_interaction_impact(
        self,
        interaction_data: Dict[str, Any],
        current_state: EmotionalStateData
    ) -> Dict[str, Any]:
        """
        Analyze the emotional impact of a user interaction.
        """
        impact = {
            "trust_delta": 0.0,
            "vulnerability_delta": 0.0,
            "authenticity_delta": 0.0,
            "progress_delta": 0.0,
            "breakthrough_potential": 0.0
        }
        
        action = interaction_data.get("action", "")
        resonance = interaction_data.get("resonance", 0)
        response_time = interaction_data.get("user_response_time", 30)  # seconds
        points_earned = interaction_data.get("points_earned", 0)
        
        # Base impact from action type
        action_impacts = {
            "reaccionar_publicacion": {"trust_delta": 0.5, "progress_delta": 0.02},
            "tomar_decision": {"trust_delta": 1.0, "vulnerability_delta": 0.8, "progress_delta": 0.05},
            "completar_fragmento_narrativo": {"trust_delta": 0.8, "progress_delta": 0.04},
            "desbloquear_pista": {"trust_delta": 0.6, "authenticity_delta": 0.3, "progress_delta": 0.03}
        }
        
        if action in action_impacts:
            for key, value in action_impacts[action].items():
                impact[key] = value
        
        # Adjust based on emotional resonance
        for key in impact:
            if key.endswith("_delta"):
                impact[key] *= (1 + resonance)
        
        # Response time indicates engagement level
        if response_time < 10:  # Very quick response
            impact["authenticity_delta"] += 0.2
        elif response_time > 120:  # Slow response (thinking)
            impact["vulnerability_delta"] += 0.3
        
        # Points earned indicate success/investment
        point_multiplier = min(points_earned / 20.0, 1.5)
        impact["progress_delta"] *= point_multiplier
        
        # Level-specific adjustments
        level_adjustments = {
            EmotionalLevel.CURIOSITY: {"trust_delta": 1.2, "progress_delta": 1.5},
            EmotionalLevel.INTRIGUE: {"trust_delta": 1.1, "vulnerability_delta": 0.8},
            EmotionalLevel.TENSION: {"vulnerability_delta": 1.3, "authenticity_delta": 1.1},
            EmotionalLevel.VULNERABILITY: {"trust_delta": 0.9, "vulnerability_delta": 1.4},
            EmotionalLevel.PASSION: {"authenticity_delta": 1.3, "vulnerability_delta": 1.2},
            EmotionalLevel.SOUL_BOND: {"all_metrics": 1.1}
        }
        
        level_adj = level_adjustments.get(current_state.current_level, {})
        for key, multiplier in level_adj.items():
            if key == "all_metrics":
                for impact_key in impact:
                    if impact_key.endswith("_delta"):
                        impact[impact_key] *= multiplier
            elif key in impact:
                impact[key] *= multiplier
        
        # Calculate breakthrough potential
        if (impact["vulnerability_delta"] > 1.0 and 
            impact["trust_delta"] > 0.8 and 
            current_state.level_progress > 0.7):
            impact["breakthrough_potential"] = 0.8
        
        return impact
    
    async def _update_emotional_metrics(
        self,
        current_state: EmotionalStateData,
        emotional_impact: Dict[str, Any]
    ) -> EmotionalStateData:
        """
        Apply emotional impact to update user's emotional state.
        """
        # Create updated state
        updated_state = EmotionalStateData(**current_state.to_dict())
        
        # Apply deltas with bounds checking
        updated_state.trust_score = max(0, min(100, 
            current_state.trust_score + emotional_impact.get("trust_delta", 0)
        ))
        
        updated_state.vulnerability_capacity = max(0, min(100,
            current_state.vulnerability_capacity + emotional_impact.get("vulnerability_delta", 0)
        ))
        
        updated_state.authenticity_score = max(0, min(100,
            current_state.authenticity_score + emotional_impact.get("authenticity_delta", 0)
        ))
        
        updated_state.level_progress = max(0, min(1.0,
            current_state.level_progress + emotional_impact.get("progress_delta", 0)
        ))
        
        # Update interaction count
        updated_state.total_interactions += 1
        
        # Update breakthrough moments if significant impact
        if emotional_impact.get("breakthrough_potential", 0) > 0.7:
            updated_state.breakthrough_moments += 1
        
        # Update time in current level
        updated_state.time_in_current_level = (
            datetime.utcnow() - current_state.last_level_advancement
        )
        
        return updated_state
    
    async def check_level_advancement(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Check if user should advance to the next emotional level.
        
        Returns:
            Advancement data if level change occurred, None otherwise
        """
        current_state = await self.get_user_emotional_state(user_id)
        return await self._check_level_advancement(current_state, {})
    
    async def _check_level_advancement(
        self,
        current_state: EmotionalStateData,
        emotional_impact: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check and process potential level advancement.
        """
        advancement_result = {"advanced": False}
        
        # Can't advance from maximum level
        if current_state.current_level == EmotionalLevel.SOUL_BOND:
            return advancement_result
        
        # Get requirements for current level
        requirements = self.level_requirements[current_state.current_level]
        
        # Check if advancement criteria are met
        can_advance = (
            current_state.level_progress >= requirements["min_progress"] and
            current_state.trust_score >= requirements["min_trust"] and
            current_state.vulnerability_capacity >= requirements["min_vulnerability"] and
            current_state.time_in_current_level >= requirements["min_time"] and
            current_state.total_interactions >= requirements["min_interactions"]
        )
        
        # Check for breakthrough advancement
        breakthrough = (
            emotional_impact.get("breakthrough_potential", 0) > 0.7 and
            current_state.level_progress >= 0.6
        )
        
        if can_advance or breakthrough:
            # Advance to next level
            next_level = EmotionalLevel(current_state.current_level.value + 1)
            
            advancement_result.update({
                "advanced": True,
                "previous_level": current_state.current_level,
                "new_level": next_level,
                "advancement_type": "breakthrough" if breakthrough else "gradual",
                "celebration_message": self._get_level_advancement_message(
                    current_state.current_level, next_level
                ),
                "unlocked_content": await self._get_unlocked_content(next_level),
                "diana_personality_change": self.diana_personalities[next_level]
            })
            
            # Update state
            current_state.current_level = next_level
            current_state.level_progress = 0.0
            current_state.last_level_advancement = datetime.utcnow()
            current_state.time_in_current_level = timedelta(0)
        
        return advancement_result
    
    # ==================== DIANA PERSONALITY AND MESSAGING ====================
    
    async def enhance_message(
        self,
        base_message: str,
        emotional_state: EmotionalStateData,
        personalization_context: Dict[str, Any]
    ) -> str:
        """
        Enhance message with emotional level appropriate Diana personality.
        """
        try:
            level_personality = self.diana_personalities[emotional_state.current_level]
            
            # Get level-appropriate enhancements
            enhancements = level_personality["message_enhancements"]
            
            # Apply personality traits to message
            enhanced_message = await self._apply_personality_enhancements(
                base_message, enhancements, emotional_state, personalization_context
            )
            
            return enhanced_message
            
        except Exception as e:
            logger.exception(f"Error enhancing message: {e}")
            return base_message  # Return original on error
    
    async def _apply_personality_enhancements(
        self,
        message: str,
        enhancements: Dict[str, Any],
        emotional_state: EmotionalStateData,
        context: Dict[str, Any]
    ) -> str:
        """
        Apply Diana personality enhancements to message based on emotional level.
        """
        enhanced = message
        
        # Add level-specific emotional coloring
        emotional_prefix = enhancements.get("emotional_prefixes", [])
        if emotional_prefix and emotional_state.trust_score > 60:
            prefix = self._select_contextual_element(emotional_prefix, context)
            if prefix:
                enhanced = f"{prefix} {enhanced}"
        
        # Add vulnerability indicators for higher levels
        if emotional_state.current_level.value >= 3:
            vulnerability_hints = enhancements.get("vulnerability_hints", [])
            if vulnerability_hints and emotional_state.vulnerability_capacity > 70:
                hint = self._select_contextual_element(vulnerability_hints, context)
                if hint:
                    enhanced = f"{enhanced}\n\n{hint}"
        
        # Add intimacy markers for highest levels
        if emotional_state.current_level.value >= 5:
            intimacy_markers = enhancements.get("intimacy_markers", [])
            if intimacy_markers and emotional_state.trust_score > 80:
                marker = self._select_contextual_element(intimacy_markers, context)
                if marker:
                    enhanced = f"{enhanced}\n\n_{marker}_"
        
        return enhanced
    
    def _select_contextual_element(
        self,
        elements: List[str],
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Select appropriate element based on context.
        """
        if not elements:
            return None
        
        # For now, simple selection - could be enhanced with more context awareness
        import random
        return random.choice(elements)
    
    # ==================== CINEMATIC MOMENT GENERATION ====================
    
    async def generate_breakthrough_moment(
        self,
        emotional_state: EmotionalStateData,
        soul_signature: Any  # Will be typed properly when soul engine is implemented
    ) -> Dict[str, Any]:
        """
        Generate an emotional breakthrough moment.
        """
        level_moments = {
            EmotionalLevel.CURIOSITY: {
                "type": "first_blush",
                "message": "Diana se sonroja ligeramente cuando sus miradas se cruzan...",
                "emotional_impact": 0.3
            },
            EmotionalLevel.INTRIGUE: {
                "type": "playful_tease",
                "message": "Diana juega con un mechón de cabello mientras te observa con interés...",
                "emotional_impact": 0.4
            },
            EmotionalLevel.TENSION: {
                "type": "electric_moment",
                "message": "El aire se carga de electricidad cuando Diana se acerca lo suficiente para que sientas su respiración...",
                "emotional_impact": 0.6
            },
            EmotionalLevel.VULNERABILITY: {
                "type": "emotional_confession",
                "message": "Diana baja la mirada, sus defensas se desvanecen por un momento...",
                "emotional_impact": 0.7
            },
            EmotionalLevel.PASSION: {
                "type": "passionate_revelation",
                "message": "Diana te toma la mano, su voz tiembla con emoción contenida...",
                "emotional_impact": 0.8
            },
            EmotionalLevel.SOUL_BOND: {
                "type": "soul_recognition",
                "message": "En sus ojos ves reflejada tu propia alma, y Diana sonríe con entendimiento perfecto...",
                "emotional_impact": 0.9
            }
        }
        
        moment = level_moments.get(emotional_state.current_level, level_moments[EmotionalLevel.CURIOSITY])
        
        return {
            "success": True,
            "moment_type": moment["type"],
            "message": moment["message"],
            "emotional_impact": moment["emotional_impact"],
            "level": emotional_state.current_level.value,
            "breakthrough": True
        }
    
    async def generate_vulnerability_test(
        self,
        emotional_state: EmotionalStateData,
        soul_signature: Any
    ) -> Dict[str, Any]:
        """
        Generate a vulnerability test appropriate for current emotional level.
        """
        if emotional_state.current_level.value < 3:
            return {
                "success": False,
                "message": "Not ready for vulnerability tests at this level"
            }
        
        vulnerability_tests = {
            EmotionalLevel.TENSION: {
                "scenario": "Diana menciona casualmente algo personal sobre su pasado...",
                "test_type": "gentle_sharing",
                "expected_response": "empathy"
            },
            EmotionalLevel.VULNERABILITY: {
                "scenario": "Diana admite tener miedo de algo que nunca había confesado...",
                "test_type": "fear_confession",
                "expected_response": "support"
            },
            EmotionalLevel.PASSION: {
                "scenario": "Diana revela una inseguridad profunda sobre sí misma...",
                "test_type": "insecurity_reveal",
                "expected_response": "acceptance"
            },
            EmotionalLevel.SOUL_BOND: {
                "scenario": "Diana comparte su mayor arrepentimiento contigo...",
                "test_type": "regret_sharing",
                "expected_response": "understanding"
            }
        }
        
        test = vulnerability_tests.get(emotional_state.current_level)
        if not test:
            return {"success": False, "message": "No vulnerability test available for this level"}
        
        return {
            "success": True,
            "scenario": test["scenario"],
            "test_type": test["test_type"],
            "level": emotional_state.current_level.value,
            "vulnerability_test": True
        }
    
    # ==================== INITIALIZATION AND CONFIGURATION ====================
    
    def _initialize_level_requirements(self) -> Dict[EmotionalLevel, Dict[str, Any]]:
        """Initialize requirements for each emotional level advancement."""
        return {
            EmotionalLevel.CURIOSITY: {
                "min_progress": 0.8,
                "min_trust": 40,
                "min_vulnerability": 20,
                "min_time": timedelta(hours=2),
                "min_interactions": 5
            },
            EmotionalLevel.INTRIGUE: {
                "min_progress": 0.7,
                "min_trust": 55,
                "min_vulnerability": 35,
                "min_time": timedelta(hours=6),
                "min_interactions": 12
            },
            EmotionalLevel.TENSION: {
                "min_progress": 0.8,
                "min_trust": 65,
                "min_vulnerability": 50,
                "min_time": timedelta(hours=12),
                "min_interactions": 20
            },
            EmotionalLevel.VULNERABILITY: {
                "min_progress": 0.9,
                "min_trust": 75,
                "min_vulnerability": 70,
                "min_time": timedelta(days=1),
                "min_interactions": 30
            },
            EmotionalLevel.PASSION: {
                "min_progress": 0.9,
                "min_trust": 85,
                "min_vulnerability": 80,
                "min_time": timedelta(days=2),
                "min_interactions": 40
            },
            EmotionalLevel.SOUL_BOND: {
                # Maximum level - no advancement
                "min_progress": 1.0,
                "min_trust": 95,
                "min_vulnerability": 90,
                "min_time": timedelta(days=7),
                "min_interactions": 50
            }
        }
    
    def _initialize_diana_personalities(self) -> Dict[EmotionalLevel, Dict[str, Any]]:
        """Initialize Diana's personality traits for each emotional level."""
        return {
            EmotionalLevel.CURIOSITY: {
                "traits": ["mysterious", "playful", "intriguing"],
                "vulnerability_level": 0.2,
                "intimacy_markers": ["sonrisas enigmáticas", "miradas curiosas"],
                "message_enhancements": {
                    "emotional_prefixes": [
                        "Diana te observa con curiosidad...",
                        "Una sonrisa misteriosa cruza el rostro de Diana...",
                        "Diana inclina la cabeza, intrigada..."
                    ]
                }
            },
            EmotionalLevel.INTRIGUE: {
                "traits": ["flirtatious", "engaging", "magnetic"],
                "vulnerability_level": 0.4,
                "intimacy_markers": ["coqueteo sutil", "atención enfocada"],
                "message_enhancements": {
                    "emotional_prefixes": [
                        "Diana te mira con interés creciente...",
                        "Un brillo especial ilumina los ojos de Diana...",
                        "Diana se acerca un poco más..."
                    ]
                }
            },
            EmotionalLevel.TENSION: {
                "traits": ["seductive", "intense", "magnetic"],
                "vulnerability_level": 0.6,
                "intimacy_markers": ["tensión palpable", "cercanía física"],
                "message_enhancements": {
                    "emotional_prefixes": [
                        "Diana te mira intensamente...",
                        "El aire se carga de electricidad...",
                        "Diana muerde suavemente su labio inferior..."
                    ],
                    "vulnerability_hints": [
                        "*Su respiración se vuelve más profunda*",
                        "*Sus mejillas se tiñen de un suave rubor*"
                    ]
                }
            },
            EmotionalLevel.VULNERABILITY: {
                "traits": ["open", "trusting", "emotionally_available"],
                "vulnerability_level": 0.8,
                "intimacy_markers": ["apertura emocional", "confianza mutua"],
                "message_enhancements": {
                    "emotional_prefixes": [
                        "Diana baja sus defensas...",
                        "Con voz más suave, Diana...",
                        "Los ojos de Diana revelan emociones profundas..."
                    ],
                    "vulnerability_hints": [
                        "*Sus ojos brillan con lágrimas no derramadas*",
                        "*Su voz se quiebra ligeramente*",
                        "*Te toma la mano buscando conexión*"
                    ]
                }
            },
            EmotionalLevel.PASSION: {
                "traits": ["passionate", "intense", "devoted"],
                "vulnerability_level": 0.9,
                "intimacy_markers": ["pasión intensa", "entrega emocional"],
                "message_enhancements": {
                    "emotional_prefixes": [
                        "Diana te mira con pasión desbordante...",
                        "Con voz cargada de emoción, Diana...",
                        "Diana se acerca hasta que puedes sentir su corazón latir..."
                    ],
                    "vulnerability_hints": [
                        "*Su corazón late aceleradamente*",
                        "*Su respiración se entrecorta*",
                        "*Sus manos tiemblan ligeramente*"
                    ],
                    "intimacy_markers": [
                        "Solo tú puedes hacerme sentir así...",
                        "Contigo me siento completa...",
                        "Eres mi refugio y mi tormenta..."
                    ]
                }
            },
            EmotionalLevel.SOUL_BOND: {
                "traits": ["transcendent", "unified", "eternal"],
                "vulnerability_level": 1.0,
                "intimacy_markers": ["unión de almas", "comprensión perfecta"],
                "message_enhancements": {
                    "emotional_prefixes": [
                        "Diana te mira como si fueras parte de su alma...",
                        "Con la serenidad de quien ha encontrado su lugar, Diana...",
                        "En perfecta armonía, Diana..."
                    ],
                    "vulnerability_hints": [
                        "*En sus ojos ves reflejada tu propia alma*",
                        "*Su presencia se fusiona con la tuya*",
                        "*El tiempo parece detenerse a vuestro alrededor*"
                    ],
                    "intimacy_markers": [
                        "Somos dos almas que se reconocieron...",
                        "Contigo he encontrado mi otra mitad...",
                        "Juntos somos eternidad...",
                        "En ti veo mi hogar y mi destino..."
                    ]
                }
            }
        }
    
    # ==================== UTILITY METHODS ====================
    
    async def get_user_journey_analysis(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive analysis of user's emotional journey."""
        try:
            emotional_state = await self.get_user_emotional_state(user_id)
            
            return {
                "current_level": emotional_state.current_level.value,
                "level_name": emotional_state.current_level.name,
                "progression_rate": emotional_state.level_progress,
                "trust_development": emotional_state.trust_score,
                "vulnerability_growth": emotional_state.vulnerability_capacity,
                "authenticity_score": emotional_state.authenticity_score,
                "total_interactions": emotional_state.total_interactions,
                "breakthrough_moments": emotional_state.breakthrough_moments,
                "time_invested": emotional_state.time_in_current_level.total_seconds() / 3600,  # hours
                "emotional_stability": emotional_state.emotional_stability,
                "next_level_probability": emotional_state.next_transition_probability
            }
        except Exception as e:
            logger.exception(f"Error in user journey analysis: {e}")
            return {"error": str(e)}
    
    def _get_level_advancement_message(
        self,
        from_level: EmotionalLevel,
        to_level: EmotionalLevel
    ) -> str:
        """Get celebration message for level advancement."""
        messages = {
            (EmotionalLevel.CURIOSITY, EmotionalLevel.INTRIGUE): 
                "💋 Diana te mira con renovado interés... Algo ha cambiado entre vosotros.",
            
            (EmotionalLevel.INTRIGUE, EmotionalLevel.TENSION): 
                "⚡ El aire se carga de una nueva energía... Diana se acerca más que nunca.",
            
            (EmotionalLevel.TENSION, EmotionalLevel.VULNERABILITY): 
                "💝 Diana baja sus defensas... Su mirada revela emociones más profundas.",
            
            (EmotionalLevel.VULNERABILITY, EmotionalLevel.PASSION): 
                "🔥 La pasión arde entre vosotros... Diana se entrega por completo.",
            
            (EmotionalLevel.PASSION, EmotionalLevel.SOUL_BOND): 
                "✨ Vuestras almas se reconocen... Habéis alcanzado la unión perfecta."
        }
        
        return messages.get((from_level, to_level), 
            "🌟 Vuestra conexión con Diana ha evolucionado a un nivel más profundo.")
    
    async def _get_unlocked_content(self, level: EmotionalLevel) -> List[str]:
        """Get content unlocked at specific emotional level."""
        unlocked_content = {
            EmotionalLevel.INTRIGUE: [
                "Acceso a conversaciones más íntimas",
                "Nuevas opciones de diálogo coqueto"
            ],
            EmotionalLevel.TENSION: [
                "Escenas de tensión sexual",
                "Momentos de cercanía física",
                "Opciones de seducción avanzada"
            ],
            EmotionalLevel.VULNERABILITY: [
                "Secretos personales de Diana",
                "Momentos de vulnerabilidad emocional",
                "Conversaciones sobre el pasado"
            ],
            EmotionalLevel.PASSION: [
                "Escenas de pasión intensa",
                "Declaraciones de amor profundo",
                "Momentos íntimos exclusivos"
            ],
            EmotionalLevel.SOUL_BOND: [
                "La verdad completa sobre Diana",
                "Unión espiritual perfecta",
                "Contenido exclusivo de alma gemela"
            ]
        }
        
        return unlocked_content.get(level, [])
    
    # ==================== DATABASE INTEGRATION ====================
    
    async def _get_user_narrative_state(self, user_id: int) -> Optional[UserNarrativeState]:
        """Get user's narrative state for emotional context."""
        try:
            result = await self.session.execute(
                select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.exception(f"Error getting narrative state: {e}")
            return None
    
    async def _calculate_current_emotional_level(
        self, 
        user: User, 
        narrative_state: Optional[UserNarrativeState]
    ) -> EmotionalLevel:
        """Calculate current emotional level from user data."""
        # Simple calculation based on user level and points
        # This could be enhanced with more sophisticated logic
        user_level = getattr(user, 'level', 1)
        user_points = getattr(user, 'points', 0)
        
        if user_points < 50:
            return EmotionalLevel.CURIOSITY
        elif user_points < 150:
            return EmotionalLevel.INTRIGUE
        elif user_points < 300:
            return EmotionalLevel.TENSION
        elif user_points < 500:
            return EmotionalLevel.VULNERABILITY
        elif user_points < 800:
            return EmotionalLevel.PASSION
        else:
            return EmotionalLevel.SOUL_BOND
    
    async def _calculate_level_progress(
        self, 
        user_id: int, 
        current_level: EmotionalLevel,
        narrative_state: Optional[UserNarrativeState]
    ) -> float:
        """Calculate progress within current emotional level."""
        # This would integrate with actual user progress data
        # For now, return a placeholder
        return 0.5
    
    async def _calculate_trust_score(
        self, 
        user: User, 
        narrative_state: Optional[UserNarrativeState]
    ) -> float:
        """Calculate user's trust score with Diana."""
        # Base score from user level and engagement
        base_score = min(50 + (getattr(user, 'level', 1) * 10), 100)
        return base_score
    
    async def _calculate_vulnerability_capacity(
        self, 
        user: User, 
        narrative_state: Optional[UserNarrativeState]
    ) -> float:
        """Calculate user's capacity to handle emotional vulnerability."""
        # Based on interaction patterns and decisions made
        base_capacity = min(30 + (getattr(user, 'points', 0) / 10), 100)
        return base_capacity
    
    async def _calculate_authenticity_score(self, user: User) -> float:
        """Calculate how authentic the user appears in interactions."""
        # Would analyze response patterns, timing, etc.
        return 50.0  # Placeholder
    
    async def _get_total_interactions(self, user_id: int) -> int:
        """Get total number of interactions for user."""
        # This would query interaction history
        return 0  # Placeholder
    
    async def _get_breakthrough_moments(self, user_id: int) -> int:
        """Get number of breakthrough moments user has experienced."""
        # This would query emotional memory
        return 0  # Placeholder
    
    async def _calculate_time_in_level(
        self, 
        user_id: int, 
        current_level: EmotionalLevel
    ) -> timedelta:
        """Calculate how long user has been in current emotional level."""
        # This would track level advancement history
        return timedelta(hours=1)  # Placeholder
    
    async def _analyze_recent_patterns(self, user_id: int) -> Dict[str, float]:
        """Analyze recent emotional response patterns."""
        # This would analyze recent interactions
        return {}  # Placeholder
    
    def _calculate_emotional_stability(self, recent_patterns: Dict[str, float]) -> float:
        """Calculate emotional stability score."""
        return 0.7  # Placeholder
    
    async def _get_level_specific_data(
        self, 
        user_id: int, 
        current_level: EmotionalLevel
    ) -> Dict[str, Any]:
        """Get level-specific data for user."""
        return {}  # Placeholder
    
    async def _calculate_transition_probability(
        self,
        current_level: EmotionalLevel,
        level_progress: float,
        trust_score: float,
        vulnerability_capacity: float
    ) -> float:
        """Calculate probability of advancing to next level."""
        base_prob = level_progress * 0.5
        trust_factor = (trust_score / 100) * 0.3
        vulnerability_factor = (vulnerability_capacity / 100) * 0.2
        
        return min(base_prob + trust_factor + vulnerability_factor, 1.0)
    
    async def _persist_emotional_state(self, state: EmotionalStateData) -> None:
        """Persist emotional state to database."""
        # This would update the database with current emotional state
        # For now, we'll just update the cache
        pass