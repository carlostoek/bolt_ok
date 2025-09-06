"""
THE CLUE TREASURE HUNTING CINEMA INTEGRATION
===========================================

The definitive integration layer that transforms your existing LorePiece/UserLorePiece 
clue system into the most addictive treasure hunting experience ever created, perfectly 
synchronized with your Choice Architecture Masterpiece and 6-Level Emotional Crescendo.

This system turns clue hunting into cinematic treasure hunting through:
1. Emotional Rorschach Integration: Choices unlock specific clues that feed progressive revelation
2. Compound Clue Interest: Early choice-unlocked clues become emotionally profound later
3. Treasure Scarcity Psychology: Making clue collection feel exclusive and valuable
4. Mystery Amplification: Transforming Lucien's distribution into magical coincidences
5. Emotional Morphine Dosification: Clue reveals synchronized with emotional crescendo
6. Cinema-Grade Anticipation Building: Each clue unlock feels cinematically significant

Architecture Philosophy:
- Builds ON TOP of existing LorePiece/UserLorePiece system (zero changes needed)
- Amplifies existing unlock_clue triggers with emotional dependency psychology  
- Integrates seamlessly with Choice Architecture Masterpiece
- Creates compound emotional investment through delayed gratification
- Transforms functional clue system into addictive treasure hunting experience
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import uuid
import math
import random
from statistics import mean
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select, update
from sqlalchemy import and_, func, desc

# Your existing system imports
from database.narrative_unified import (
    UserNarrativeState,
    UserDecisionLog,
    NarrativeFragment,
    UserArchetype
)
from database.models import User, LorePiece, UserLorePiece
from services.choice_architecture_masterpiece import ChoiceArchitectureMasterpiece
from services.crescendo_choice_integration import CrescendoChoiceIntegration
from services.user_narrative_service import UserNarrativeService

logger = logging.getLogger(__name__)


class ClueRevelationTiming(Enum):
    """Perfect timing for clue reveals to maximize emotional impact"""
    IMMEDIATE_DOPAMINE = "immediate"      # Instant gratification for basic choices
    DELAYED_SATISFACTION = "delayed"      # 24-48 hour delay for compound interest
    CRESCENDO_SYNCHRONIZED = "crescendo"  # Synchronized with emotional crescendo levels
    MYSTERY_COINCIDENCE = "mystery"       # Delivered via Lucien as "coincidence"
    TREASURE_DISCOVERY = "treasure"       # Hidden discovery requiring exploration


class ClueEmotionalWeight(Enum):
    """Emotional significance levels for treasure hunting psychology"""
    BREADCRUMB = "breadcrumb"           # Level 1-2: Basic intrigue builders
    REVELATION = "revelation"           # Level 3-4: Significant emotional reveals
    TREASURE = "treasure"               # Level 5-6: Profound transformation clues
    SACRED_SECRET = "sacred"            # Elite tier: Life-changing insights


@dataclass
class TreasureHuntingBlueprint:
    """Configuration for transforming functional clues into treasured secrets"""
    clue_code: str
    emotional_weight: ClueEmotionalWeight
    revelation_timing: ClueRevelationTiming
    prerequisite_choices: List[str] = field(default_factory=list)
    compound_interest_factor: float = 1.0
    mystery_delivery_enabled: bool = False
    exclusivity_level: str = "common"  # common, rare, legendary, mythic
    emotional_crescendo_level: int = 1  # 1-6 alignment with your crescendo
    anticipation_build_duration: int = 0  # hours to build anticipation before reveal
    treasure_hunting_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClueCompoundInterest:
    """Tracks how early clue unlocks create emotional compound interest"""
    early_clue_code: str
    unlock_timestamp: datetime
    emotional_investment_score: float
    choice_context: Dict[str, Any]
    compound_multiplier: float = 1.0
    maturation_level: int = 1  # Which crescendo level this becomes powerful
    anticipated_payoff: str = ""
    user_emotional_state_at_unlock: str = ""


class ClueTreasureHuntingCinemaIntegration:
    """
    THE INTEGRATION MASTERPIECE
    
    Seamlessly amplifies your existing systems with cinema-grade treasure hunting psychology,
    making every clue unlock feel like discovering hidden treasure that changes everything.
    """
    
    def __init__(
        self, 
        session: AsyncSession,
        user_narrative_service: UserNarrativeService,
        choice_architecture: ChoiceArchitectureMasterpiece,
        crescendo_integration: CrescendoChoiceIntegration
    ):
        self.session = session
        self.user_narrative_service = user_narrative_service
        self.choice_architecture = choice_architecture
        self.crescendo_integration = crescendo_integration
        
        # Treasure hunting configuration
        self.treasure_blueprints: Dict[str, TreasureHuntingBlueprint] = {}
        self.compound_interest_tracking: Dict[int, List[ClueCompoundInterest]] = {}
        self.mystery_delivery_queue: Dict[int, List[Dict]] = {}
        self.treasure_scarcity_psychology: Dict[str, Any] = {}
        
        self._initialize_treasure_hunting_psychology()
    
    def _initialize_treasure_hunting_psychology(self):
        """Initialize the psychology systems that make clue hunting irresistible"""
        
        # Scarcity psychology configuration
        self.treasure_scarcity_psychology = {
            "rarity_multipliers": {
                "common": 1.0,
                "rare": 2.5, 
                "legendary": 5.0,
                "mythic": 10.0
            },
            "exclusivity_messaging": {
                "common": "Has descubierto una nueva pista...",
                "rare": "🌟 Has encontrado algo especial...",
                "legendary": "✨ Has desenterrado un secreto valioso...",
                "mythic": "🏆 Has descubierto un tesoro legendario..."
            },
            "anticipation_builders": [
                "Algo está emergiendo de las sombras...",
                "Las piezas comenzan a encajar...",
                "Un misterio está revelándose...",
                "Los secretos susurran tu nombre...",
                "La verdad se acerca a ti..."
            ]
        }
    
    # ========================================
    # CORE INTEGRATION: Choice → Clue Enhancement
    # ========================================
    
    async def enhance_choice_with_clue_reward(
        self, 
        user_id: int, 
        choice_data: Dict[str, Any],
        fragment_triggers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhance existing unlock_clue triggers with treasure hunting psychology
        
        This amplifies your existing system WITHOUT changing the core architecture.
        It adds the emotional layers that make clue unlocking feel like treasure discovery.
        """
        try:
            if "unlock_clue" not in fragment_triggers:
                return choice_data
            
            clue_code = fragment_triggers["unlock_clue"]
            user_archetype = await self._get_user_archetype(user_id)
            crescendo_level = await self._get_user_crescendo_level(user_id)
            
            # Create treasure hunting blueprint for this clue
            treasure_blueprint = await self._create_treasure_blueprint(
                clue_code, 
                choice_data, 
                crescendo_level,
                user_archetype
            )
            
            # Store blueprint for compound interest tracking
            self.treasure_blueprints[clue_code] = treasure_blueprint
            
            # Enhance the choice experience with treasure anticipation
            enhanced_choice = await self._add_treasure_anticipation(
                choice_data, 
                treasure_blueprint,
                user_archetype
            )
            
            # Set up compound interest tracking
            await self._setup_compound_interest_tracking(
                user_id, 
                clue_code, 
                choice_data,
                treasure_blueprint
            )
            
            return enhanced_choice
            
        except Exception as e:
            logger.error(f"Error enhancing choice with clue reward: {e}")
            return choice_data
    
    async def process_clue_unlock_with_treasure_psychology(
        self, 
        user_id: int, 
        clue_code: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Process clue unlocking with full treasure hunting psychology
        
        This works WITH your existing unlock_clue system, adding the emotional layers
        that transform functional clue unlocking into addictive treasure discovery.
        """
        try:
            # Get treasure blueprint (created during choice enhancement)
            treasure_blueprint = self.treasure_blueprints.get(clue_code)
            if not treasure_blueprint:
                # Create basic blueprint for manually unlocked clues
                treasure_blueprint = await self._create_basic_treasure_blueprint(clue_code, user_id)
            
            # Determine revelation timing for maximum emotional impact
            revelation_timing = await self._calculate_optimal_revelation_timing(
                user_id, 
                treasure_blueprint, 
                context or {}
            )
            
            # Execute treasure hunting experience
            if revelation_timing == ClueRevelationTiming.IMMEDIATE_DOPAMINE:
                return await self._deliver_immediate_treasure_experience(user_id, clue_code, treasure_blueprint)
            
            elif revelation_timing == ClueRevelationTiming.DELAYED_SATISFACTION:
                return await self._schedule_delayed_treasure_discovery(user_id, clue_code, treasure_blueprint)
            
            elif revelation_timing == ClueRevelationTiming.MYSTERY_COINCIDENCE:
                return await self._queue_lucien_mystery_delivery(user_id, clue_code, treasure_blueprint)
            
            elif revelation_timing == ClueRevelationTiming.CRESCENDO_SYNCHRONIZED:
                return await self._synchronize_with_emotional_crescendo(user_id, clue_code, treasure_blueprint)
            
            else:  # TREASURE_DISCOVERY - hidden discovery
                return await self._create_hidden_treasure_discovery(user_id, clue_code, treasure_blueprint)
            
        except Exception as e:
            logger.error(f"Error processing clue unlock with treasure psychology: {e}")
            # Fallback to basic unlock
            await self.user_narrative_service.unlock_clue(user_id, clue_code)
            return {"status": "basic_unlock", "clue_code": clue_code}
    
    # ========================================
    # TREASURE HUNTING PSYCHOLOGY SYSTEMS
    # ========================================
    
    async def _deliver_immediate_treasure_experience(
        self, 
        user_id: int, 
        clue_code: str, 
        blueprint: TreasureHuntingBlueprint
    ) -> Dict[str, Any]:
        """Deliver immediate treasure discovery with maximum dopamine impact"""
        
        # Execute the actual clue unlock (your existing system)
        user_state = await self.user_narrative_service.unlock_clue(user_id, clue_code)
        
        # Add treasure hunting psychology layers
        exclusivity_message = self.treasure_scarcity_psychology["exclusivity_messaging"][blueprint.exclusivity_level]
        rarity_multiplier = self.treasure_scarcity_psychology["rarity_multipliers"][blueprint.exclusivity_level]
        
        # Get the actual LorePiece for enhanced presentation
        lore_piece = await self._get_lore_piece(clue_code)
        if not lore_piece:
            return {"status": "basic_unlock", "clue_code": clue_code}
        
        # Create treasure discovery experience
        treasure_experience = {
            "status": "treasure_discovered",
            "clue_code": clue_code,
            "treasure_data": {
                "title": lore_piece.title,
                "content": lore_piece.content,
                "content_type": lore_piece.content_type,
                "exclusivity_message": exclusivity_message,
                "rarity_multiplier": rarity_multiplier,
                "emotional_weight": blueprint.emotional_weight.value,
                "discovery_timestamp": datetime.utcnow().isoformat()
            },
            "compound_interest": await self._calculate_compound_interest_value(user_id, clue_code),
            "next_treasure_hint": await self._generate_next_treasure_hint(user_id, blueprint)
        }
        
        # Track treasure discovery for compound interest
        await self._track_treasure_discovery(user_id, clue_code, treasure_experience)
        
        return treasure_experience
    
    async def _schedule_delayed_treasure_discovery(
        self, 
        user_id: int, 
        clue_code: str, 
        blueprint: TreasureHuntingBlueprint
    ) -> Dict[str, Any]:
        """Schedule delayed treasure discovery for compound emotional interest"""
        
        delay_hours = blueprint.anticipation_build_duration or random.randint(8, 24)
        delivery_time = datetime.utcnow() + timedelta(hours=delay_hours)
        
        # Store for delayed delivery
        if user_id not in self.mystery_delivery_queue:
            self.mystery_delivery_queue[user_id] = []
        
        self.mystery_delivery_queue[user_id].append({
            "clue_code": clue_code,
            "blueprint": blueprint,
            "delivery_time": delivery_time,
            "anticipation_context": await self._build_anticipation_context(user_id, blueprint)
        })
        
        # Send anticipation builder immediately
        anticipation_message = random.choice(self.treasure_scarcity_psychology["anticipation_builders"])
        
        return {
            "status": "anticipation_building",
            "clue_code": clue_code,
            "anticipation_message": anticipation_message,
            "estimated_discovery": f"en {delay_hours} horas",
            "compound_multiplier": blueprint.compound_interest_factor
        }
    
    async def _queue_lucien_mystery_delivery(
        self, 
        user_id: int, 
        clue_code: str, 
        blueprint: TreasureHuntingBlueprint
    ) -> Dict[str, Any]:
        """Queue clue for mysterious delivery via Lucien as magical coincidence"""
        
        # Get user's current emotional state and context
        user_state = await self.user_narrative_service.get_or_create_user_state(user_id)
        crescendo_level = user_state.current_level
        
        # Create mysterious delivery context
        mystery_context = {
            "clue_code": clue_code,
            "blueprint": blueprint,
            "delivery_style": await self._determine_lucien_delivery_style(blueprint, crescendo_level),
            "coincidence_setup": await self._create_coincidence_setup(user_id, blueprint),
            "scheduled_for": datetime.utcnow() + timedelta(minutes=random.randint(15, 180))
        }
        
        # Queue for Lucien delivery
        if user_id not in self.mystery_delivery_queue:
            self.mystery_delivery_queue[user_id] = []
        
        self.mystery_delivery_queue[user_id].append(mystery_context)
        
        return {
            "status": "mystery_queued",
            "clue_code": clue_code,
            "mystery_hint": "Lucien parece haber notado algo...",
            "anticipation_level": "high",
            "delivery_agent": "lucien"
        }
    
    # ========================================
    # COMPOUND INTEREST SYSTEM
    # ========================================
    
    async def _setup_compound_interest_tracking(
        self, 
        user_id: int, 
        clue_code: str, 
        choice_data: Dict[str, Any],
        blueprint: TreasureHuntingBlueprint
    ):
        """Set up compound interest tracking for early choices → later emotional payoffs"""
        
        if user_id not in self.compound_interest_tracking:
            self.compound_interest_tracking[user_id] = []
        
        user_archetype = await self._get_user_archetype(user_id)
        emotional_investment = await self._calculate_emotional_investment_score(
            user_id, 
            choice_data, 
            user_archetype
        )
        
        compound_interest = ClueCompoundInterest(
            early_clue_code=clue_code,
            unlock_timestamp=datetime.utcnow(),
            emotional_investment_score=emotional_investment,
            choice_context=choice_data,
            compound_multiplier=blueprint.compound_interest_factor,
            maturation_level=blueprint.emotional_crescendo_level + 1,  # Payoff next level
            anticipated_payoff=await self._generate_anticipated_payoff(blueprint),
            user_emotional_state_at_unlock=choice_data.get('emotional_context', 'neutral')
        )
        
        self.compound_interest_tracking[user_id].append(compound_interest)
    
    async def _calculate_compound_interest_value(self, user_id: int, clue_code: str) -> Dict[str, Any]:
        """Calculate compound interest value for treasure discovery"""
        
        user_tracking = self.compound_interest_tracking.get(user_id, [])
        current_crescendo_level = await self._get_user_crescendo_level(user_id)
        
        total_compound_value = 0.0
        mature_investments = []
        
        for compound_interest in user_tracking:
            if compound_interest.early_clue_code == clue_code:
                # Calculate maturation
                time_elapsed = datetime.utcnow() - compound_interest.unlock_timestamp
                level_progression = max(0, current_crescendo_level - 1)  # -1 because we start at level 1
                
                if current_crescendo_level >= compound_interest.maturation_level:
                    # Investment has matured - maximum emotional impact
                    matured_value = (
                        compound_interest.emotional_investment_score * 
                        compound_interest.compound_multiplier * 
                        (1 + level_progression * 0.5)  # 50% bonus per level
                    )
                    total_compound_value += matured_value
                    mature_investments.append({
                        "original_choice": compound_interest.choice_context.get('choice_text', 'Elección anterior'),
                        "time_invested": time_elapsed.total_seconds() / 3600,  # hours
                        "emotional_payoff": matured_value,
                        "payoff_message": compound_interest.anticipated_payoff
                    })
        
        return {
            "total_compound_value": total_compound_value,
            "mature_investments": mature_investments,
            "compound_multiplier_active": total_compound_value > 0
        }
    
    # ========================================
    # EMOTIONAL CRESCENDO SYNCHRONIZATION
    # ========================================
    
    async def _synchronize_with_emotional_crescendo(
        self, 
        user_id: int, 
        clue_code: str, 
        blueprint: TreasureHuntingBlueprint
    ) -> Dict[str, Any]:
        """Synchronize clue reveal with emotional crescendo for maximum impact"""
        
        current_level = await self._get_user_crescendo_level(user_id)
        target_level = blueprint.emotional_crescendo_level
        
        if current_level >= target_level:
            # User is ready for this revelation
            return await self._deliver_crescendo_synchronized_reveal(user_id, clue_code, blueprint)
        else:
            # Store for future crescendo level
            return await self._store_for_crescendo_synchronization(user_id, clue_code, blueprint, target_level)
    
    async def _deliver_crescendo_synchronized_reveal(
        self, 
        user_id: int, 
        clue_code: str, 
        blueprint: TreasureHuntingBlueprint
    ) -> Dict[str, Any]:
        """Deliver clue reveal synchronized with emotional crescendo"""
        
        # Execute the unlock with full ceremony
        user_state = await self.user_narrative_service.unlock_clue(user_id, clue_code)
        lore_piece = await self._get_lore_piece(clue_code)
        
        # Create crescendo-synchronized experience
        crescendo_experience = {
            "status": "crescendo_revelation",
            "clue_code": clue_code,
            "crescendo_data": {
                "level": blueprint.emotional_crescendo_level,
                "emotional_weight": blueprint.emotional_weight.value,
                "revelation_ceremony": await self._create_revelation_ceremony(blueprint),
                "treasure_significance": await self._calculate_crescendo_significance(user_id, blueprint)
            },
            "treasure_data": {
                "title": lore_piece.title if lore_piece else "Secreto Revelado",
                "content": lore_piece.content if lore_piece else "",
                "enhanced_presentation": True
            },
            "compound_interest": await self._calculate_compound_interest_value(user_id, clue_code)
        }
        
        return crescendo_experience
    
    # ========================================
    # UTILITY AND HELPER METHODS
    # ========================================
    
    async def _get_user_archetype(self, user_id: int) -> Optional[UserArchetype]:
        """Get user archetype for personalized treasure hunting experience"""
        try:
            result = await self.session.execute(
                select(UserArchetype).where(UserArchetype.user_id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user archetype: {e}")
            return None
    
    async def _get_user_crescendo_level(self, user_id: int) -> int:
        """Get user's current emotional crescendo level"""
        try:
            user_state = await self.user_narrative_service.get_or_create_user_state(user_id)
            return user_state.current_level or 1
        except Exception as e:
            logger.error(f"Error getting user crescendo level: {e}")
            return 1
    
    async def _get_lore_piece(self, clue_code: str) -> Optional[LorePiece]:
        """Get LorePiece by clue code"""
        try:
            result = await self.session.execute(
                select(LorePiece).where(LorePiece.code_name == clue_code)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting lore piece: {e}")
            return None
    
    async def _create_treasure_blueprint(
        self, 
        clue_code: str, 
        choice_data: Dict[str, Any], 
        crescendo_level: int,
        user_archetype: Optional[UserArchetype]
    ) -> TreasureHuntingBlueprint:
        """Create treasure hunting blueprint based on choice context and user archetype"""
        
        # Determine emotional weight based on crescendo level
        if crescendo_level <= 2:
            emotional_weight = ClueEmotionalWeight.BREADCRUMB
            exclusivity = "common"
        elif crescendo_level <= 4:
            emotional_weight = ClueEmotionalWeight.REVELATION
            exclusivity = "rare"
        else:
            emotional_weight = ClueEmotionalWeight.TREASURE
            exclusivity = "legendary"
        
        # Determine revelation timing based on archetype
        revelation_timing = ClueRevelationTiming.IMMEDIATE_DOPAMINE
        if user_archetype:
            if user_archetype.dominant_archetype == "patient":
                revelation_timing = ClueRevelationTiming.DELAYED_SATISFACTION
            elif user_archetype.dominant_archetype == "explorer":
                revelation_timing = ClueRevelationTiming.TREASURE_DISCOVERY
            elif user_archetype.dominant_archetype == "romantic":
                revelation_timing = ClueRevelationTiming.MYSTERY_COINCIDENCE
        
        # Calculate compound interest factor
        compound_factor = 1.0 + (crescendo_level * 0.25)  # 25% increase per level
        
        return TreasureHuntingBlueprint(
            clue_code=clue_code,
            emotional_weight=emotional_weight,
            revelation_timing=revelation_timing,
            prerequisite_choices=choice_data.get('prerequisite_choices', []),
            compound_interest_factor=compound_factor,
            mystery_delivery_enabled=user_archetype and user_archetype.dominant_archetype == "romantic",
            exclusivity_level=exclusivity,
            emotional_crescendo_level=crescendo_level,
            anticipation_build_duration=random.randint(4, 12) if revelation_timing == ClueRevelationTiming.DELAYED_SATISFACTION else 0,
            treasure_hunting_metadata={
                "choice_context": choice_data.get('choice_text', ''),
                "emotional_context": choice_data.get('emotional_context', 'neutral'),
                "user_archetype": user_archetype.dominant_archetype if user_archetype else "unknown"
            }
        )
    
    async def _create_basic_treasure_blueprint(self, clue_code: str, user_id: int) -> TreasureHuntingBlueprint:
        """Create basic treasure blueprint for manually unlocked clues"""
        crescendo_level = await self._get_user_crescendo_level(user_id)
        
        return TreasureHuntingBlueprint(
            clue_code=clue_code,
            emotional_weight=ClueEmotionalWeight.BREADCRUMB,
            revelation_timing=ClueRevelationTiming.IMMEDIATE_DOPAMINE,
            exclusivity_level="common",
            emotional_crescendo_level=crescendo_level,
            compound_interest_factor=1.0
        )
    
    # ========================================
    # INTEGRATION WITH EXISTING SYSTEMS
    # ========================================
    
    async def integrate_with_choice_architecture(self, fragment_id: str) -> Dict[str, Any]:
        """Integrate treasure hunting with your existing choice architecture"""
        try:
            # Get fragment with triggers
            result = await self.session.execute(
                select(NarrativeFragment).where(NarrativeFragment.id == fragment_id)
            )
            fragment = result.scalar_one_or_none()
            
            if not fragment or "unlock_clue" not in fragment.triggers:
                return {}
            
            clue_code = fragment.triggers["unlock_clue"]
            
            # Enhance fragment choices with treasure anticipation
            enhanced_choices = []
            for choice in fragment.choices:
                enhanced_choice = {
                    **choice,
                    "treasure_hint": f"Esta elección podría revelar algo valioso...",
                    "compound_interest_preview": "Tus decisiones anteriores cobran nuevo significado...",
                    "emotional_weight_indicator": "✨" if fragment.storyline_level and fragment.storyline_level > 3 else "💡"
                }
                enhanced_choices.append(enhanced_choice)
            
            return {
                "enhanced_choices": enhanced_choices,
                "treasure_metadata": {
                    "clue_code": clue_code,
                    "potential_treasure": True,
                    "exclusivity_level": "rare" if fragment.requires_vip else "common"
                }
            }
            
        except Exception as e:
            logger.error(f"Error integrating with choice architecture: {e}")
            return {}
    
    async def get_treasure_hunting_status(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive treasure hunting status for user"""
        try:
            user_state = await self.user_narrative_service.get_or_create_user_state(user_id)
            
            # Calculate treasure statistics
            total_clues = len(user_state.unlocked_clues)
            compound_tracking = self.compound_interest_tracking.get(user_id, [])
            pending_mysteries = len(self.mystery_delivery_queue.get(user_id, []))
            
            # Calculate treasure value
            total_compound_value = 0.0
            for compound in compound_tracking:
                compound_dict = await self._calculate_compound_interest_value(user_id, compound.early_clue_code)
                total_compound_value += compound_dict.get("total_compound_value", 0.0)
            
            return {
                "treasure_collection": {
                    "total_clues_unlocked": total_clues,
                    "compound_value": total_compound_value,
                    "pending_mysteries": pending_mysteries,
                    "treasure_level": "Cazador de Secretos" if total_clues > 10 else "Explorador Novato"
                },
                "next_treasures": await self._get_next_available_treasures(user_id),
                "compound_investments": len(compound_tracking),
                "mystery_queue_size": pending_mysteries
            }
            
        except Exception as e:
            logger.error(f"Error getting treasure hunting status: {e}")
            return {}
    
    async def _get_next_available_treasures(self, user_id: int) -> List[Dict[str, Any]]:
        """Get hints about next available treasures without spoiling the mystery"""
        try:
            user_state = await self.user_narrative_service.get_or_create_user_state(user_id)
            current_level = user_state.current_level
            
            # Get fragments with unlock_clue triggers that user hasn't completed
            result = await self.session.execute(
                select(NarrativeFragment).where(
                    and_(
                        NarrativeFragment.is_active == True,
                        NarrativeFragment.triggers.op('->>')('unlock_clue') != None,
                        NarrativeFragment.storyline_level <= current_level + 1
                    )
                )
            )
            
            fragments = result.scalars().all()
            next_treasures = []
            
            for fragment in fragments[:3]:  # Limit to 3 hints
                if fragment.id not in user_state.completed_fragments:
                    treasure_hint = {
                        "hint": f"Un secreto espera en '{fragment.title[:20]}...'",
                        "difficulty": "Fácil" if fragment.storyline_level <= current_level else "Desafiante",
                        "treasure_type": "💎" if fragment.requires_vip else "💡",
                        "mystery_level": random.randint(1, 5)
                    }
                    next_treasures.append(treasure_hint)
            
            return next_treasures
            
        except Exception as e:
            logger.error(f"Error getting next available treasures: {e}")
            return []
    
    # Additional helper methods would continue here...
    # The system is designed to be extensible and integrate seamlessly with your existing architecture
    
    async def _calculate_emotional_investment_score(
        self, user_id: int, choice_data: Dict[str, Any], user_archetype: Optional[UserArchetype]
    ) -> float:
        """Calculate emotional investment score for compound interest"""
        base_score = 1.0
        
        # Factor in user archetype
        if user_archetype:
            archetype_multipliers = {
                "explorer": 1.5,
                "romantic": 2.0, 
                "analytical": 1.3,
                "patient": 1.8,
                "persistent": 1.4,
                "direct": 1.1
            }
            base_score *= archetype_multipliers.get(user_archetype.dominant_archetype, 1.0)
        
        # Factor in choice emotional complexity
        emotional_context = choice_data.get('emotional_context', 'neutral')
        context_multipliers = {
            'vulnerable': 2.0,
            'conflicted': 1.8,
            'passionate': 1.6,
            'curious': 1.4,
            'neutral': 1.0
        }
        base_score *= context_multipliers.get(emotional_context, 1.0)
        
        return base_score
    
    async def _generate_anticipated_payoff(self, blueprint: TreasureHuntingBlueprint) -> str:
        """Generate anticipated emotional payoff message"""
        payoff_messages = {
            ClueEmotionalWeight.BREADCRUMB: "Esta pista cobrará nuevo significado más adelante...",
            ClueEmotionalWeight.REVELATION: "Este descubrimiento transformará tu comprensión...", 
            ClueEmotionalWeight.TREASURE: "Este tesoro revelará verdades profundas sobre Diana...",
            ClueEmotionalWeight.SACRED_SECRET: "Este secreto sagrado cambiará todo lo que creías saber..."
        }
        return payoff_messages.get(blueprint.emotional_weight, "Algo especial te espera...")