"""
LUCIEN MYSTERY AMPLIFICATION SYSTEM
===================================

Transforms Lucien's clue distribution into magical coincidences that feel like destiny,
perfectly synchronized with your Choice Architecture Masterpiece and emotional crescendo.

This system enhances Lucien's existing coordination capabilities with:
1. Destiny Timing Psychology: Deliveries feel perfectly timed, never random
2. Emotional Synchronization: Clues arrive exactly when emotionally needed
3. Mystical Coincidence Creation: Admin-granted clues become "magical discoveries"
4. Progressive Mystery Building: Each delivery builds toward greater revelations
5. Emotional Dependency Amplification: Makes users crave Lucien's appearances

PHILOSOPHY: Transform functional clue distribution into mystical experiences
that make users believe Lucien truly understands their deepest needs.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import uuid
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy import and_, func, desc

# Your existing system imports
from database.narrative_unified import (
    UserNarrativeState,
    LucienCoordination,
    UserArchetype,
    UserDecisionLog
)
from database.models import User, LorePiece
from services.clue_treasure_hunting_cinema_integration import TreasureHuntingBlueprint, ClueEmotionalWeight

logger = logging.getLogger(__name__)


class LucienMysteryStyle(Enum):
    """Different styles of mysterious clue delivery"""
    CASUAL_DISCOVERY = "casual"          # "Oh, encontré esto..."  
    URGENT_REVELATION = "urgent"         # "Necesitas ver esto ahora"
    PROTECTIVE_CONCERN = "protective"    # "Esto te ayudará..."
    MYSTICAL_COINCIDENCE = "mystical"    # "¿Qué casualidad...?"
    PROFOUND_TIMING = "profound"         # "El momento perfecto..."
    GUARDIAN_GUIDANCE = "guardian"       # "Diana quiere que tengas esto"


class EmotionalSynchronizationLevel(Enum):
    """How perfectly timed Lucien's appearances feel"""
    BASIC_TIMING = "basic"               # Good timing
    PERFECT_TIMING = "perfect"           # Uncannily perfect
    DESTINY_TIMING = "destiny"           # Feels like fate
    TRANSCENDENT_TIMING = "transcendent" # Magical, impossible timing


@dataclass
class MysteryDeliveryBlueprint:
    """Blueprint for creating mystical clue delivery experiences"""
    clue_code: str
    user_id: int
    mystery_style: LucienMysteryStyle
    synchronization_level: EmotionalSynchronizationLevel
    emotional_context: Dict[str, Any] = field(default_factory=dict)
    delivery_timing: datetime = field(default_factory=datetime.utcnow)
    coincidence_setup: Dict[str, Any] = field(default_factory=dict)
    mystery_buildup_messages: List[str] = field(default_factory=list)
    revelation_ceremony: Dict[str, Any] = field(default_factory=dict)
    treasure_significance: str = ""
    user_readiness_score: float = 0.0


@dataclass
class EmotionalSynchronizationData:
    """Data for creating perfectly timed emotional synchronization"""
    user_current_state: str  # curious, confused, seeking, frustrated, breakthrough
    recent_interactions: List[Dict[str, Any]]
    choice_patterns: Dict[str, Any]
    emotional_trajectory: str  # building, peak, valley, transition
    optimal_intervention_window: datetime
    synchronization_opportunities: List[str]


class LucienMysteryAmplificationSystem:
    """
    THE MYSTERY AMPLIFICATION MASTER
    
    Transforms Lucien from functional coordinator into mystical guide whose
    every appearance feels like destiny intervening at the perfect moment.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Mystery psychology configuration
        self.mystery_psychology = self._initialize_mystery_psychology()
        
        # Tracking for perfect timing
        self.emotional_synchronization_tracking: Dict[int, EmotionalSynchronizationData] = {}
        self.mystery_delivery_history: Dict[int, List[Dict[str, Any]]] = {}
        self.coincidence_probability_engine = self._initialize_coincidence_engine()
        
        # Mystical messaging templates
        self.mystical_templates = self._initialize_mystical_templates()
    
    def _initialize_mystery_psychology(self) -> Dict[str, Any]:
        """Initialize the psychology systems for mystical experiences"""
        return {
            "timing_psychology": {
                "perfect_moment_indicators": [
                    "user_just_made_vulnerable_choice",
                    "user_expressed_confusion", 
                    "user_reached_emotional_peak",
                    "user_about_to_give_up",
                    "user_having_breakthrough_moment"
                ],
                "synchronization_multipliers": {
                    EmotionalSynchronizationLevel.BASIC_TIMING: 1.0,
                    EmotionalSynchronizationLevel.PERFECT_TIMING: 2.0,
                    EmotionalSynchronizationLevel.DESTINY_TIMING: 3.5,
                    EmotionalSynchronizationLevel.TRANSCENDENT_TIMING: 5.0
                }
            },
            "mystery_building": {
                "anticipation_builders": [
                    "Lucien parece haber notado algo...",
                    "Una sombra familiar se mueve en la distancia...",
                    "El aire cambia. Lucien está cerca...",
                    "Algo está por revelar se..."
                ],
                "coincidence_enhancers": [
                    "Justo cuando lo necesitabas...",
                    "¿Qué casualidad tan extraña...?",
                    "El timing de esto es... inquietante.",
                    "Como si hubiera estado esperando el momento perfecto..."
                ]
            }
        }
    
    def _initialize_coincidence_engine(self) -> Dict[str, Any]:
        """Initialize the engine that makes deliveries feel like magical coincidences"""
        return {
            "probability_enhancers": {
                "recent_emotional_peak": 0.8,
                "user_expressed_need": 0.9, 
                "choice_vulnerability": 0.85,
                "crescendo_transition": 0.95,
                "breakthrough_moment": 1.0
            },
            "timing_windows": {
                "immediate": timedelta(minutes=5),
                "perfect": timedelta(minutes=15, seconds=random.randint(0, 300)),
                "destiny": timedelta(hours=1, minutes=random.randint(0, 60)),
                "transcendent": timedelta(hours=random.randint(2, 8))
            }
        }
    
    def _initialize_mystical_templates(self) -> Dict[str, List[str]]:
        """Initialize mystical messaging templates for different contexts"""
        return {
            LucienMysteryStyle.CASUAL_DISCOVERY.value: [
                "Encontré esto mientras... bueno, ya sabes cómo trabajo.",
                "Algo cayó en mis manos. Pensé que te interesaría.",
                "Esto estaba prácticamente pidiendo que te lo trajera.",
                "No suelo creer en coincidencias, pero..."
            ],
            LucienMysteryStyle.MYSTICAL_COINCIDENCE.value: [
                "¿No te parece extraño el timing de esto?",
                "Esto apareció exactamente cuando... ¿casualidad?",
                "El universo tiene formas curiosas de funcionar...",
                "Algunos dirían que esto es destino."
            ],
            LucienMysteryStyle.PROFOUND_TIMING.value: [
                "El momento exacto. Como si hubiera estado esperando.",
                "Perfecto timing. Demasiado perfecto para ser casual.",
                "Esto llegó justo cuando más lo necesitabas, ¿verdad?",
                "Los momentos perfectos no existen. Excepto este."
            ],
            LucienMysteryStyle.GUARDIAN_GUIDANCE.value: [
                "Diana mencionó que podrías necesitar esto...",
                "Ella quiere que tengas esto. No preguntes cómo lo sé.",
                "Esto viene con su bendición. Y su preocupación.",
                "Diana confía en que sabrás qué hacer con esto."
            ]
        }
    
    # ========================================
    # CORE MYSTERY AMPLIFICATION
    # ========================================
    
    async def create_mystical_clue_delivery(
        self, 
        user_id: int, 
        clue_code: str,
        context: Dict[str, Any] = None
    ) -> MysteryDeliveryBlueprint:
        """
        Create mystical clue delivery experience that feels like destiny
        
        This is the core function that transforms ordinary clue unlocking
        into mystical experiences that feel impossibly well-timed.
        """
        try:
            # Analyze user's current emotional state and context
            emotional_sync_data = await self._analyze_emotional_synchronization(user_id)
            
            # Determine optimal mystery style based on context
            mystery_style = await self._determine_optimal_mystery_style(
                user_id, clue_code, emotional_sync_data, context or {}
            )
            
            # Calculate synchronization level for maximum impact
            sync_level = await self._calculate_synchronization_level(
                user_id, emotional_sync_data, context or {}
            )
            
            # Calculate perfect delivery timing
            delivery_timing = await self._calculate_perfect_timing(
                user_id, sync_level, emotional_sync_data
            )
            
            # Create coincidence setup for mystical feel
            coincidence_setup = await self._create_coincidence_setup(
                user_id, clue_code, emotional_sync_data, mystery_style
            )
            
            # Generate mystery buildup messages
            buildup_messages = await self._generate_mystery_buildup(
                mystery_style, sync_level, emotional_sync_data
            )
            
            # Create revelation ceremony
            revelation_ceremony = await self._create_revelation_ceremony(
                user_id, clue_code, mystery_style, sync_level
            )
            
            # Calculate user readiness score
            readiness_score = await self._calculate_user_readiness_score(
                user_id, emotional_sync_data
            )
            
            mystery_blueprint = MysteryDeliveryBlueprint(
                clue_code=clue_code,
                user_id=user_id,
                mystery_style=mystery_style,
                synchronization_level=sync_level,
                emotional_context=emotional_sync_data.__dict__ if emotional_sync_data else {},
                delivery_timing=delivery_timing,
                coincidence_setup=coincidence_setup,
                mystery_buildup_messages=buildup_messages,
                revelation_ceremony=revelation_ceremony,
                treasure_significance=await self._assess_treasure_significance(clue_code),
                user_readiness_score=readiness_score
            )
            
            # Store for tracking and analytics
            await self._store_mystery_blueprint(mystery_blueprint)
            
            return mystery_blueprint
            
        except Exception as e:
            logger.error(f"Error creating mystical clue delivery: {e}")
            # Return basic blueprint as fallback
            return MysteryDeliveryBlueprint(
                clue_code=clue_code,
                user_id=user_id,
                mystery_style=LucienMysteryStyle.CASUAL_DISCOVERY,
                synchronization_level=EmotionalSynchronizationLevel.BASIC_TIMING
            )
    
    async def execute_mystical_delivery(
        self, 
        blueprint: MysteryDeliveryBlueprint
    ) -> Dict[str, Any]:
        """
        Execute the mystical delivery experience with full ceremony
        
        This delivers the clue with all the mystical psychology to make
        it feel like a magical, perfectly-timed revelation.
        """
        try:
            # Phase 1: Mystery Building (if appropriate timing)
            if blueprint.mystery_buildup_messages and blueprint.synchronization_level != EmotionalSynchronizationLevel.BASIC_TIMING:
                await self._execute_mystery_buildup_phase(blueprint)
            
            # Phase 2: Coincidence Setup
            coincidence_context = await self._execute_coincidence_setup(blueprint)
            
            # Phase 3: The Mystical Delivery
            delivery_result = await self._execute_mystical_delivery_ceremony(blueprint)
            
            # Phase 4: Post-Delivery Mystery Enhancement
            post_delivery_enhancement = await self._execute_post_delivery_enhancement(blueprint)
            
            # Phase 5: Future Mystery Seeding
            future_mystery_seeds = await self._plant_future_mystery_seeds(blueprint)
            
            # Compile full mystical experience
            mystical_experience = {
                "delivery_status": "mystical_success",
                "clue_code": blueprint.clue_code,
                "mystery_style": blueprint.mystery_style.value,
                "synchronization_achieved": blueprint.synchronization_level.value,
                "coincidence_context": coincidence_context,
                "delivery_ceremony": delivery_result,
                "post_delivery_enhancement": post_delivery_enhancement,
                "future_mystery_seeds": future_mystery_seeds,
                "mystical_impact_score": await self._calculate_mystical_impact_score(blueprint),
                "user_dependency_building": await self._assess_dependency_building_effect(blueprint)
            }
            
            # Track delivery for analytics and future optimization
            await self._track_mystical_delivery(blueprint, mystical_experience)
            
            return mystical_experience
            
        except Exception as e:
            logger.error(f"Error executing mystical delivery: {e}")
            return {
                "delivery_status": "basic_fallback",
                "clue_code": blueprint.clue_code,
                "error": str(e)
            }
    
    # ========================================
    # EMOTIONAL SYNCHRONIZATION SYSTEMS
    # ========================================
    
    async def _analyze_emotional_synchronization(self, user_id: int) -> EmotionalSynchronizationData:
        """Analyze user's emotional state for perfect timing synchronization"""
        try:
            # Get recent user interactions and decisions
            recent_decisions = await self._get_recent_user_decisions(user_id, limit=10)
            
            # Analyze current emotional trajectory
            emotional_trajectory = await self._analyze_emotional_trajectory(user_id, recent_decisions)
            
            # Identify current emotional state
            current_state = await self._identify_current_emotional_state(user_id, recent_decisions)
            
            # Find optimal intervention windows
            optimal_window = await self._calculate_optimal_intervention_window(
                user_id, current_state, emotional_trajectory
            )
            
            # Identify synchronization opportunities
            sync_opportunities = await self._identify_synchronization_opportunities(
                user_id, current_state, recent_decisions
            )
            
            return EmotionalSynchronizationData(
                user_current_state=current_state,
                recent_interactions=recent_decisions,
                choice_patterns=await self._analyze_choice_patterns(recent_decisions),
                emotional_trajectory=emotional_trajectory,
                optimal_intervention_window=optimal_window,
                synchronization_opportunities=sync_opportunities
            )
            
        except Exception as e:
            logger.error(f"Error analyzing emotional synchronization: {e}")
            # Return basic synchronization data
            return EmotionalSynchronizationData(
                user_current_state="neutral",
                recent_interactions=[],
                choice_patterns={},
                emotional_trajectory="stable",
                optimal_intervention_window=datetime.utcnow() + timedelta(minutes=15),
                synchronization_opportunities=["basic_timing"]
            )
    
    async def _determine_optimal_mystery_style(
        self, 
        user_id: int, 
        clue_code: str, 
        sync_data: EmotionalSynchronizationData,
        context: Dict[str, Any]
    ) -> LucienMysteryStyle:
        """Determine optimal mystery delivery style for maximum impact"""
        
        # Factor in user's emotional state
        if sync_data.user_current_state == "vulnerable":
            return LucienMysteryStyle.PROTECTIVE_CONCERN
        elif sync_data.user_current_state == "seeking":
            return LucienMysteryStyle.GUARDIAN_GUIDANCE
        elif sync_data.user_current_state == "breakthrough":
            return LucienMysteryStyle.PROFOUND_TIMING
        elif sync_data.user_current_state == "confused":
            return LucienMysteryStyle.MYSTICAL_COINCIDENCE
        
        # Factor in context
        if context.get("trigger_source") == "choice_architecture":
            return LucienMysteryStyle.MYSTICAL_COINCIDENCE
        elif context.get("admin_granted"):
            return LucienMysteryStyle.GUARDIAN_GUIDANCE
        
        # Factor in clue significance
        lore_piece = await self._get_lore_piece(clue_code)
        if lore_piece and lore_piece.is_main_story:
            return LucienMysteryStyle.PROFOUND_TIMING
        
        # Default to mystical coincidence for maximum mystery
        return LucienMysteryStyle.MYSTICAL_COINCIDENCE
    
    async def _calculate_synchronization_level(
        self, 
        user_id: int, 
        sync_data: EmotionalSynchronizationData,
        context: Dict[str, Any]
    ) -> EmotionalSynchronizationLevel:
        """Calculate synchronization level for maximum emotional impact"""
        
        synchronization_score = 0.0
        
        # Factor in emotional state alignment
        if sync_data.user_current_state in ["vulnerable", "seeking", "breakthrough"]:
            synchronization_score += 0.4
        
        # Factor in optimal timing windows
        if "perfect_moment" in sync_data.synchronization_opportunities:
            synchronization_score += 0.3
        
        # Factor in emotional trajectory
        if sync_data.emotional_trajectory == "peak":
            synchronization_score += 0.2
        elif sync_data.emotional_trajectory == "transition":
            synchronization_score += 0.3
        
        # Factor in context
        if context.get("choice_triggered") and context.get("emotional_context") == "vulnerable":
            synchronization_score += 0.4
        
        # Determine synchronization level
        if synchronization_score >= 0.8:
            return EmotionalSynchronizationLevel.TRANSCENDENT_TIMING
        elif synchronization_score >= 0.6:
            return EmotionalSynchronizationLevel.DESTINY_TIMING
        elif synchronization_score >= 0.4:
            return EmotionalSynchronizationLevel.PERFECT_TIMING
        else:
            return EmotionalSynchronizationLevel.BASIC_TIMING
    
    # ========================================
    # MYSTICAL DELIVERY EXECUTION
    # ========================================
    
    async def _execute_mystical_delivery_ceremony(
        self, blueprint: MysteryDeliveryBlueprint
    ) -> Dict[str, Any]:
        """Execute the core mystical delivery ceremony"""
        
        try:
            # Get mystical message template
            template_messages = self.mystical_templates.get(
                blueprint.mystery_style.value, 
                self.mystical_templates[LucienMysteryStyle.CASUAL_DISCOVERY.value]
            )
            
            # Select message based on synchronization level
            if blueprint.synchronization_level == EmotionalSynchronizationLevel.TRANSCENDENT_TIMING:
                message_index = -1  # Most profound message
            elif blueprint.synchronization_level == EmotionalSynchronizationLevel.DESTINY_TIMING:
                message_index = -2  # Second most profound
            else:
                message_index = random.randint(0, len(template_messages) - 3)
            
            lucien_message = template_messages[message_index]
            
            # Enhance message with coincidence context
            if blueprint.coincidence_setup:
                coincidence_enhancement = blueprint.coincidence_setup.get("timing_comment", "")
                if coincidence_enhancement:
                    lucien_message += f" {coincidence_enhancement}"
            
            # Get clue data for presentation
            lore_piece = await self._get_lore_piece(blueprint.clue_code)
            
            # Create delivery ceremony
            ceremony = {
                "lucien_appearance": {
                    "style": blueprint.mystery_style.value,
                    "timing_perfection": blueprint.synchronization_level.value,
                    "message": lucien_message,
                    "emotional_resonance": await self._calculate_emotional_resonance(blueprint)
                },
                "clue_presentation": {
                    "title": lore_piece.title if lore_piece else "Un Secreto",
                    "content_preview": self._create_content_preview(lore_piece) if lore_piece else "Algo valioso...",
                    "presentation_style": "mystical_reveal",
                    "significance_hint": blueprint.treasure_significance
                },
                "mystical_enhancements": {
                    "coincidence_probability": "Imposiblemente perfecta",
                    "emotional_synchronization": "Completa",
                    "timing_magic": f"El momento exacto que necesitabas esto",
                    "destiny_feel": "Como si hubiera sido planificado por el universo"
                }
            }
            
            return ceremony
            
        except Exception as e:
            logger.error(f"Error executing mystical delivery ceremony: {e}")
            return {"error": str(e), "fallback": True}
    
    # ========================================
    # UTILITY AND HELPER METHODS  
    # ========================================
    
    async def _get_recent_user_decisions(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent user decisions for emotional analysis"""
        try:
            result = await self.session.execute(
                select(UserDecisionLog)
                .where(UserDecisionLog.user_id == user_id)
                .order_by(desc(UserDecisionLog.made_at))
                .limit(limit)
            )
            decisions = result.scalars().all()
            
            return [
                {
                    "decision_choice": decision.decision_choice,
                    "fragment_id": decision.fragment_id,
                    "made_at": decision.made_at,
                    "points_awarded": decision.points_awarded,
                    "clues_unlocked": decision.clues_unlocked
                }
                for decision in decisions
            ]
            
        except Exception as e:
            logger.error(f"Error getting recent user decisions: {e}")
            return []
    
    async def _get_lore_piece(self, clue_code: str) -> Optional[LorePiece]:
        """Get LorePiece by clue code"""
        try:
            from database.models import LorePiece
            result = await self.session.execute(
                select(LorePiece).where(LorePiece.code_name == clue_code)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting lore piece: {e}")
            return None
    
    async def _identify_current_emotional_state(
        self, user_id: int, recent_decisions: List[Dict[str, Any]]
    ) -> str:
        """Identify user's current emotional state from recent interactions"""
        
        if not recent_decisions:
            return "neutral"
        
        # Analyze decision patterns
        recent_choices = [d["decision_choice"] for d in recent_decisions[:3]]
        
        # Simple heuristics - could be enhanced with NLP
        emotional_indicators = {
            "vulnerable": ["compartir", "confesar", "abrirme", "vulnerable", "miedo"],
            "seeking": ["buscar", "encontrar", "necesito", "quiero saber", "ayuda"],
            "curious": ["explorar", "descubrir", "interesante", "más", "continuar"],
            "confused": ["no entiendo", "confuso", "qué significa", "ayuda", "explicar"],
            "breakthrough": ["ahora entiendo", "comprendo", "claro", "por fin", "sí"]
        }
        
        # Count emotional indicators
        state_scores = {state: 0 for state in emotional_indicators.keys()}
        
        for choice in recent_choices:
            choice_lower = choice.lower()
            for state, indicators in emotional_indicators.items():
                for indicator in indicators:
                    if indicator in choice_lower:
                        state_scores[state] += 1
        
        # Return state with highest score
        if max(state_scores.values()) > 0:
            return max(state_scores, key=state_scores.get)
        
        return "neutral"
    
    def _create_content_preview(self, lore_piece: LorePiece) -> str:
        """Create mysterious content preview"""
        if not lore_piece:
            return "Un secreto te espera..."
        
        content = lore_piece.content
        if len(content) > 50:
            return content[:50] + "..."
        return content
    
    # Additional methods for complete mystical experience...
    # The system provides full mystical transformation of clue delivery
    
    async def _calculate_perfect_timing(
        self, 
        user_id: int, 
        sync_level: EmotionalSynchronizationLevel, 
        sync_data: EmotionalSynchronizationData
    ) -> datetime:
        """Calculate perfect delivery timing"""
        base_delay = self.coincidence_engine["timing_windows"][sync_level.value.split("_")[0]]
        return sync_data.optimal_intervention_window + base_delay
    
    async def _store_mystery_blueprint(self, blueprint: MysteryDeliveryBlueprint):
        """Store mystery blueprint for tracking and analytics"""
        if blueprint.user_id not in self.mystery_delivery_history:
            self.mystery_delivery_history[blueprint.user_id] = []
        
        self.mystery_delivery_history[blueprint.user_id].append({
            "clue_code": blueprint.clue_code,
            "mystery_style": blueprint.mystery_style.value,
            "synchronization_level": blueprint.synchronization_level.value,
            "delivery_timing": blueprint.delivery_timing.isoformat(),
            "readiness_score": blueprint.user_readiness_score,
            "created_at": datetime.utcnow().isoformat()
        })