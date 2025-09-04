"""
Enhanced Unified Narrative Service for Master Storyline System

Handles the complete 6-level master storyline with 16 fragments, user archetyping,
mission validation, VIP tier management, and real-time character consistency validation.

Master Storyline Structure:
- Level 1-3: Los Kinkys (Free) - Fragments 1-8
- Level 4-5: El Diván (VIP) - Fragments 9-12  
- Level 6: Elite (Premium VIP) - Fragments 13-16

Integrated Systems:
- Mission validation (observation, comprehension, synthesis)
- User archetyping and behavioral analysis
- VIP tier management and access control
- Diana character consistency validation >95%
- Lucien coordination system
- Performance optimization <500ms
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from database.models import User
from database.narrative_unified import (
    UserNarrativeState,
    NarrativeFragment as UnifiedNarrativeFragment,
    UserMissionProgress,
    UserArchetype,
    NarrativeCharacterValidation,
    LucienCoordination,
    UserDecisionLog
)
from services.narrative_fragment_service import NarrativeFragmentService
from services.point_service import PointService
from services.master_storyline_mission_service import MasterStorylineMissionService, MissionType
from services.user_archetyping_service import UserArchetypingService
from services.vip_tier_management_service import VIPTierManagementService
from services.diana_character_validator import DianaCharacterValidator
from datetime import datetime
import asyncio
import time

logger = logging.getLogger(__name__)

class EnhancedUnifiedNarrativeService:
    """Enhanced unified narrative service with complete master storyline support."""
    
    def __init__(self, session: AsyncSession, bot=None):
        self.session = session
        self.bot = bot
        
        # Core services
        self.point_service = PointService(session) if session else None
        self.fragment_service = NarrativeFragmentService(session)
        
        # Master storyline services
        self.mission_service = MasterStorylineMissionService(session)
        self.archetyping_service = UserArchetypingService(session)
        self.vip_service = VIPTierManagementService(session)
        self.character_validator = DianaCharacterValidator(session)
        
        # Performance tracking
        self._operation_start_time = None
        self._performance_threshold_ms = 500
    
    async def start_master_storyline(self, user_id: int) -> Dict[str, Any]:
        """Initialize user in the master storyline system."""
        self._start_performance_tracking()
        
        try:
            # Get or create user progress
            mission_progress = await self.mission_service._get_user_mission_progress(user_id)
            narrative_state = await self._get_or_create_user_state(user_id)
            archetype = await self.archetyping_service._get_user_archetype(user_id)
            
            # Initialize with first fragment based on master storyline
            start_fragment = await self._get_master_storyline_start_fragment()
            if not start_fragment:
                logger.error("Master storyline start fragment not found")
                return {'success': False, 'error': 'Start fragment not available'}
            
            # Validate access
            access_result = await self.vip_service.check_content_access(user_id, start_fragment.id)
            if not access_result.has_access:
                return {
                    'success': False,
                    'error': 'Access denied',
                    'access_result': access_result.__dict__
                }
            
            # Set initial state
            narrative_state.current_fragment_id = start_fragment.id
            narrative_state.current_level = 1
            narrative_state.current_tier = 'los_kinkys'
            
            # Initialize Lucien coordination if needed
            await self._initialize_lucien_coordination(user_id, start_fragment)
            
            await self.session.commit()
            
            # Track performance
            elapsed = self._end_performance_tracking()
            
            return {
                'success': True,
                'start_fragment': {
                    'id': start_fragment.id,
                    'title': start_fragment.title,
                    'content': start_fragment.content,
                    'type': start_fragment.fragment_type,
                    'level': start_fragment.storyline_level,
                    'tier': start_fragment.tier_classification
                },
                'user_status': {
                    'level': narrative_state.current_level,
                    'tier': narrative_state.current_tier,
                    'archetype': archetype.dominant_archetype if archetype else None
                },
                'performance': {'response_time_ms': elapsed}
            }
            
        except Exception as e:
            logger.error(f"Error starting master storyline for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def process_fragment_interaction(
        self, 
        user_id: int, 
        fragment_id: str,
        interaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process user interaction with a narrative fragment."""
        self._start_performance_tracking()
        
        try:
            # Get current state
            fragment = await self._get_unified_fragment_by_id(fragment_id)
            if not fragment:
                return {'success': False, 'error': 'Fragment not found'}
            
            # Validate access
            access_result = await self.vip_service.check_content_access(user_id, fragment_id)
            if not access_result.has_access:
                return {
                    'success': False,
                    'error': 'Access denied',
                    'access_result': access_result.__dict__
                }
            
            # Track real-time behavior for archetyping
            behavior_insights = await self.archetyping_service.track_real_time_behavior(
                user_id, 
                interaction_data.get('interaction_type', 'fragment_view'),
                interaction_data
            )
            
            # Validate character consistency
            character_validation = await self._validate_fragment_character_consistency(
                fragment, user_id
            )
            
            # Process mission if fragment has mission components
            mission_result = None
            if fragment.mission_type:
                mission_result = await self._process_fragment_mission(
                    user_id, fragment, interaction_data
                )
            
            # Update user state
            narrative_state = await self._get_or_create_user_state(user_id)
            if fragment_id not in narrative_state.visited_fragments:
                narrative_state.visited_fragments.append(fragment_id)
            
            # Check for Lucien coordination needs
            lucien_action = await self._check_lucien_coordination_needs(
                user_id, fragment, interaction_data
            )
            
            await self.session.commit()
            
            elapsed = self._end_performance_tracking()
            
            return {
                'success': True,
                'fragment': {
                    'id': fragment.id,
                    'title': fragment.title,
                    'content': fragment.content,
                    'mission_type': fragment.mission_type,
                    'tier': fragment.tier_classification
                },
                'mission_result': mission_result.__dict__ if mission_result else None,
                'character_validation': character_validation.__dict__ if character_validation else None,
                'behavior_insights': behavior_insights,
                'lucien_action': lucien_action,
                'performance': {'response_time_ms': elapsed}
            }
            
        except Exception as e:
            logger.error(f"Error processing fragment interaction for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def process_user_decision_enhanced(
        self, 
        user_id: int, 
        fragment_id: str,
        decision_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhanced decision processing with master storyline integration."""
        self._start_performance_tracking()
        
        try:
            # Get current fragment
            current_fragment = await self._get_unified_fragment_by_id(fragment_id)
            if not current_fragment or not current_fragment.is_decision:
                return {'success': False, 'error': 'Invalid decision fragment'}
            
            # Validate access
            access_result = await self.vip_service.check_content_access(user_id, fragment_id)
            if not access_result.has_access:
                return {'success': False, 'error': 'Access denied'}
            
            # Process decision with archetyping
            choice_index = decision_data.get('choice_index', 0)
            if choice_index >= len(current_fragment.choices):
                return {'success': False, 'error': 'Invalid choice index'}
            
            selected_choice = current_fragment.choices[choice_index]
            
            # Track decision for archetyping
            decision_insights = await self.archetyping_service.track_real_time_behavior(
                user_id,
                'decision',
                {
                    'fragment_id': fragment_id,
                    'choice_index': choice_index,
                    'choice_text': selected_choice.get('text', ''),
                    'response_time_seconds': decision_data.get('response_time_seconds', 30)
                }
            )
            
            # Get next fragment
            next_fragment_id = selected_choice.get('next_fragment_id')
            next_fragment = await self._get_unified_fragment_by_id(next_fragment_id) if next_fragment_id else None
            
            if not next_fragment:
                return {'success': False, 'error': 'Next fragment not found'}
            
            # Validate access to next fragment
            next_access = await self.vip_service.check_content_access(user_id, next_fragment.id)
            
            # Update user state
            narrative_state = await self._get_or_create_user_state(user_id)
            narrative_state.current_fragment_id = next_fragment.id
            
            # Mark current fragment as completed
            if fragment_id not in narrative_state.completed_fragments:
                narrative_state.completed_fragments.append(fragment_id)
            
            # Process level progression if needed
            progression_result = await self._check_level_progression(user_id, next_fragment)
            
            # Record decision
            decision_log = UserDecisionLog(
                user_id=user_id,
                fragment_id=fragment_id,
                decision_choice=selected_choice.get('text', 'Unknown choice'),
                points_awarded=selected_choice.get('points_reward', 0),
                clues_unlocked=selected_choice.get('clues_unlocked', [])
            )
            self.session.add(decision_log)
            
            await self.session.commit()
            
            elapsed = self._end_performance_tracking()
            
            result = {
                'success': True,
                'current_fragment_completed': fragment_id,
                'next_fragment': {
                    'id': next_fragment.id,
                    'title': next_fragment.title,
                    'content': next_fragment.content,
                    'tier': next_fragment.tier_classification,
                    'has_access': next_access.has_access
                } if next_access.has_access else None,
                'access_denied_info': next_access.__dict__ if not next_access.has_access else None,
                'decision_insights': decision_insights,
                'progression_result': progression_result,
                'performance': {'response_time_ms': elapsed}
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing decision for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_user_master_storyline_status(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user status in master storyline."""
        self._start_performance_tracking()
        
        try:
            # Get all user states
            narrative_state = await self._get_or_create_user_state(user_id)
            mission_progress = await self.mission_service._get_user_mission_progress(user_id)
            archetype = await self.archetyping_service._get_user_archetype(user_id)
            
            # Get archetype analysis
            archetype_analysis = await self.archetyping_service.get_user_archetype_analysis(user_id)
            
            # Get Diana adaptation strategy
            diana_strategy = await self.archetyping_service.get_diana_adaptation_strategy(user_id)
            
            # Get VIP analytics
            vip_analytics = await self.vip_service.get_tier_analytics(user_id)
            
            # Calculate overall progress
            progress_stats = {
                'current_level': narrative_state.current_level,
                'current_tier': narrative_state.current_tier,
                'overall_progress_percentage': mission_progress.get_overall_progress_percentage(),
                'fragments_completed_by_tier': {
                    'los_kinkys': len(mission_progress.los_kinkys_fragments_completed),
                    'el_divan': len(mission_progress.el_divan_fragments_completed),
                    'elite': len(mission_progress.elite_fragments_completed)
                },
                'mission_completion': {
                    'observation': len(mission_progress.observation_missions_completed),
                    'comprehension': len(mission_progress.comprehension_tests_passed),
                    'synthesis': len(mission_progress.synthesis_challenges_completed)
                }
            }
            
            # Get next recommendations
            next_recommendations = await self._generate_next_storyline_recommendations(user_id)
            
            elapsed = self._end_performance_tracking()
            
            return {
                'success': True,
                'progress_stats': progress_stats,
                'archetype_analysis': archetype_analysis,
                'diana_adaptation_strategy': diana_strategy,
                'vip_analytics': vip_analytics,
                'next_recommendations': next_recommendations,
                'performance': {'response_time_ms': elapsed}
            }
            
        except Exception as e:
            logger.error(f"Error getting master storyline status for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def generate_personalized_content(
        self, 
        user_id: int, 
        content_type: str = "next_fragment"
    ) -> Dict[str, Any]:
        """Generate personalized content based on user archetype and progress."""
        self._start_performance_tracking()
        
        try:
            # Get user archetype and adaptation strategy
            diana_strategy = await self.archetyping_service.get_diana_adaptation_strategy(user_id, content_type)
            archetype_analysis = await self.archetyping_service.get_user_archetype_analysis(user_id)
            
            # Get current narrative state
            narrative_state = await self._get_or_create_user_state(user_id)
            mission_progress = await self.mission_service._get_user_mission_progress(user_id)
            
            # Generate content based on type
            if content_type == "next_fragment":
                content = await self._generate_next_fragment_content(user_id, diana_strategy)
            elif content_type == "vip_offer":
                content = await self._generate_personalized_vip_offer(user_id)
            elif content_type == "mission_challenge":
                content = await self._generate_mission_challenge(user_id, diana_strategy)
            else:
                content = await self._generate_generic_personalized_content(user_id, diana_strategy)
            
            elapsed = self._end_performance_tracking()
            
            return {
                'success': True,
                'content': content,
                'personalization_data': {
                    'archetype': archetype_analysis.get('dominant_archetype'),
                    'adaptation_strategy': diana_strategy,
                    'confidence': diana_strategy.get('adaptation_confidence', 0.5)
                },
                'performance': {'response_time_ms': elapsed}
            }
            
        except Exception as e:
            logger.error(f"Error generating personalized content for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    # Performance tracking methods
    def _start_performance_tracking(self):
        """Start performance tracking for current operation."""
        self._operation_start_time = time.time()
    
    def _end_performance_tracking(self) -> int:
        """End performance tracking and return elapsed time in milliseconds."""
        if self._operation_start_time is None:
            return 0
        
        elapsed_ms = int((time.time() - self._operation_start_time) * 1000)
        
        if elapsed_ms > self._performance_threshold_ms:
            logger.warning(f"Narrative operation exceeded performance threshold: {elapsed_ms}ms > {self._performance_threshold_ms}ms")
        
        self._operation_start_time = None
        return elapsed_ms
    
    # Private helper methods
    async def _get_or_create_user_state(self, user_id: int) -> UserNarrativeState:
        """Get or create user narrative state."""
        stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        result = await self.session.execute(stmt)
        user_state = result.scalar_one_or_none()
        
        if not user_state:
            user_state = UserNarrativeState(
                user_id=user_id,
                current_fragment_id=None,
                visited_fragments=[],
                completed_fragments=[],
                unlocked_clues=[]
            )
            self.session.add(user_state)
            await self.session.commit()
            await self.session.refresh(user_state)
        
        return user_state
    
    async def _get_unified_fragment_by_id(self, fragment_id: str) -> Optional[UnifiedNarrativeFragment]:
        """Get unified fragment by ID."""
        return await self.fragment_service.get_fragment(fragment_id)
    
    async def _get_master_storyline_start_fragment(self) -> Optional[UnifiedNarrativeFragment]:
        """Get the master storyline start fragment."""
        stmt = select(UnifiedNarrativeFragment).where(
            and_(
                UnifiedNarrativeFragment.storyline_level == 1,
                UnifiedNarrativeFragment.fragment_sequence == 1,
                UnifiedNarrativeFragment.tier_classification == 'los_kinkys',
                UnifiedNarrativeFragment.is_active == True
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _initialize_lucien_coordination(self, user_id: int, fragment: UnifiedNarrativeFragment):
        """Initialize Lucien coordination for new user."""
        if not fragment.lucien_appearance_logic:
            return
        
        coordination = LucienCoordination(
            user_id=user_id,
            coordination_mode='introduction',
            current_role='guide',
            trigger_conditions=fragment.lucien_appearance_logic,
            narrative_phase='introduction'
        )
        self.session.add(coordination)
    
    async def _validate_fragment_character_consistency(
        self, 
        fragment: UnifiedNarrativeFragment, 
        user_id: int
    ) -> Optional[NarrativeCharacterValidation]:
        """Validate character consistency for fragment."""
        if not fragment.requires_character_validation():
            return None
        
        # Validate fragment content
        validation_result = await self.character_validator.validate_narrative_fragment(fragment)
        
        # Store validation result
        validation_record = NarrativeCharacterValidation(
            fragment_id=fragment.id,
            user_id=user_id,
            validated_content=f"{fragment.title}\n{fragment.content}",
            content_type="narrative_fragment",
            consistency_score=int(validation_result.overall_score),
            mysterious_score=int(validation_result.trait_scores.get('mysterious', 0) * 4),  # Convert to 0-100
            seductive_score=int(validation_result.trait_scores.get('seductive', 0) * 4),
            emotional_complexity_score=int(validation_result.trait_scores.get('emotionally_complex', 0) * 4),
            intellectual_engagement_score=int(validation_result.trait_scores.get('intellectually_engaging', 0) * 4),
            meets_threshold=validation_result.meets_threshold,
            violations_detected=validation_result.violations,
            recommendations=validation_result.recommendations
        )
        
        self.session.add(validation_record)
        return validation_record
    
    async def _process_fragment_mission(
        self, 
        user_id: int, 
        fragment: UnifiedNarrativeFragment, 
        interaction_data: Dict[str, Any]
    ) -> Any:
        """Process mission component of fragment."""
        mission_type = MissionType(fragment.mission_type)
        
        if mission_type == MissionType.OBSERVATION:
            return await self.mission_service.validate_observation_mission(
                user_id, fragment.id, interaction_data
            )
        elif mission_type == MissionType.COMPREHENSION:
            return await self.mission_service.validate_comprehension_test(
                user_id, fragment.id, interaction_data
            )
        elif mission_type == MissionType.SYNTHESIS:
            return await self.mission_service.validate_synthesis_challenge(
                user_id, fragment.id, interaction_data
            )
        
        return None
    
    async def _check_lucien_coordination_needs(
        self, 
        user_id: int, 
        fragment: UnifiedNarrativeFragment, 
        interaction_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if Lucien coordination is needed."""
        # Get current coordination state
        stmt = select(LucienCoordination).where(LucienCoordination.user_id == user_id)
        result = await self.session.execute(stmt)
        coordination = result.scalar_one_or_none()
        
        if not coordination:
            return None
        
        # Check if Lucien should appear based on context
        user_state = {
            'current_fragment': fragment.id,
            'interaction_type': interaction_data.get('interaction_type'),
            'consecutive_errors': interaction_data.get('consecutive_errors', 0)
        }
        
        should_appear = coordination.should_appear('fragment_interaction', user_state)
        
        if should_appear and not coordination.is_active:
            coordination.record_appearance(
                'fragment_interaction', 
                f"User needs guidance in {fragment.id}"
            )
            return {
                'action': 'appear',
                'role': coordination.current_role,
                'message': self._generate_lucien_appearance_message(fragment, coordination)
            }
        
        return None
    
    def _generate_lucien_appearance_message(
        self, 
        fragment: UnifiedNarrativeFragment, 
        coordination: LucienCoordination
    ) -> str:
        """Generate Lucien appearance message."""
        role_messages = {
            'guide': f"Lucien aparece discretamente... 'Veo que {fragment.title} requiere algo de contexto. Permíteme ayudarte a navegar esta parte del viaje.'",
            'coordinator': f"Lucien se materializa... 'Diana está preparando algo especial. Mientras tanto, asegúrate de que comprendes completamente {fragment.title}.'",
            'messenger': f"Lucien emerge de las sombras... 'Diana me ha pedido que te transmita algo importante sobre {fragment.title}.'"
        }
        
        return role_messages.get(coordination.current_role, "Lucien aparece para ayudarte...")
    
    async def _check_level_progression(self, user_id: int, next_fragment: UnifiedNarrativeFragment) -> Optional[Dict[str, Any]]:
        """Check if user should progress to next level."""
        mission_progress = await self.mission_service._get_user_mission_progress(user_id)
        
        # Check if next fragment requires higher level
        if next_fragment.storyline_level and next_fragment.storyline_level > mission_progress.current_level:
            # Check if user meets requirements for level progression
            progression_ready = await self.mission_service._check_level_progression_readiness(
                mission_progress, mission_progress.current_level
            )
            
            if progression_ready:
                # Progress user to next level
                mission_progress.record_level_progression(
                    next_fragment.storyline_level,
                    f"fragment_progression_{next_fragment.id}"
                )
                
                return {
                    'level_progressed': True,
                    'new_level': next_fragment.storyline_level,
                    'trigger': 'fragment_progression'
                }
        
        return None
    
    async def _generate_next_storyline_recommendations(self, user_id: int) -> List[str]:
        """Generate next storyline recommendations for user."""
        mission_progress = await self.mission_service._get_user_mission_progress(user_id)
        narrative_state = await self._get_or_create_user_state(user_id)
        
        recommendations = []
        
        # Level-based recommendations
        current_level = mission_progress.current_level
        if current_level < 3:
            recommendations.append(f"Continúa explorando Los Kinkys para alcanzar el nivel {current_level + 1}")
        elif current_level == 3 and mission_progress.current_tier == 'los_kinkys':
            recommendations.append("Considera actualizar a VIP para acceder a El Diván")
        elif current_level < 6:
            recommendations.append(f"Progresa hacia el nivel {current_level + 1} completando más misiones")
        
        # Mission-specific recommendations
        if len(mission_progress.observation_missions_completed) < current_level:
            recommendations.append("Completa más misiones de observación")
        if len(mission_progress.comprehension_tests_passed) < current_level:
            recommendations.append("Participa en pruebas de comprensión")
        if current_level >= 3 and len(mission_progress.synthesis_challenges_completed) == 0:
            recommendations.append("Intenta los desafíos de síntesis")
        
        return recommendations
    
    async def _generate_next_fragment_content(
        self, 
        user_id: int, 
        diana_strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate next fragment content personalized for user."""
        narrative_state = await self._get_or_create_user_state(user_id)
        
        # Find next appropriate fragment
        current_fragment_id = narrative_state.current_fragment_id
        if current_fragment_id:
            current_fragment = await self._get_unified_fragment_by_id(current_fragment_id)
            if current_fragment and current_fragment.is_decision and current_fragment.choices:
                # Suggest continuing with first available choice
                first_choice = current_fragment.choices[0]
                next_fragment_id = first_choice.get('next_fragment_id')
                if next_fragment_id:
                    next_fragment = await self._get_unified_fragment_by_id(next_fragment_id)
                    if next_fragment:
                        return {
                            'type': 'next_fragment_suggestion',
                            'fragment': {
                                'id': next_fragment.id,
                                'title': next_fragment.title,
                                'content': self._adapt_content_to_archetype(next_fragment.content, diana_strategy),
                                'tier': next_fragment.tier_classification
                            }
                        }
        
        return {
            'type': 'exploration_suggestion',
            'message': 'Continúa explorando el mundo de Diana para descubrir más secretos.'
        }
    
    async def _generate_personalized_vip_offer(self, user_id: int) -> Dict[str, Any]:
        """Generate personalized VIP offer."""
        offer = await self.vip_service.generate_upgrade_opportunity(user_id, 'content_request')
        
        if offer:
            return {
                'type': 'vip_offer',
                'offer': offer.to_dict()
            }
        
        return {
            'type': 'no_offer',
            'message': 'Continúa explorando para desbloquear oportunidades VIP personalizadas.'
        }
    
    async def _generate_mission_challenge(self, user_id: int, diana_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized mission challenge."""
        mission_progress = await self.mission_service._get_user_mission_progress(user_id)
        
        # Determine appropriate challenge type
        current_level = mission_progress.current_level
        
        if current_level <= 2:
            challenge_type = 'observation'
        elif current_level <= 4:
            challenge_type = 'comprehension'
        else:
            challenge_type = 'synthesis'
        
        return {
            'type': 'mission_challenge',
            'challenge_type': challenge_type,
            'description': f"Desafío de {challenge_type} personalizado para tu nivel {current_level}",
            'adapted_for_archetype': diana_strategy.get('interaction_style', 'balanced')
        }
    
    async def _generate_generic_personalized_content(self, user_id: int, diana_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Generate generic personalized content."""
        return {
            'type': 'personalized_message',
            'message': self._create_personalized_diana_message(diana_strategy),
            'adaptation_style': diana_strategy.get('interaction_style', 'balanced')
        }
    
    def _adapt_content_to_archetype(self, content: str, diana_strategy: Dict[str, Any]) -> str:
        """Adapt content based on user archetype strategy."""
        interaction_style = diana_strategy.get('interaction_style', 'balanced')
        
        if interaction_style == 'mysterious_revealing':
            # Add more mystery and hints
            return f"{content}\n\n*[Diana deja caer una pista sutil, invitándote a explorar más profundo...]*"
        elif interaction_style == 'emotionally_intimate':
            # Add emotional connection
            return f"{content}\n\n*[Puedes sentir una conexión emocional más profunda en las palabras de Diana...]*"
        elif interaction_style == 'intellectually_challenging':
            # Add intellectual depth
            return f"{content}\n\n*[Las palabras de Diana contienen capas de significado esperando ser analizadas...]*"
        
        return content
    
    def _create_personalized_diana_message(self, diana_strategy: Dict[str, Any]) -> str:
        """Create personalized Diana message based on strategy."""
        interaction_style = diana_strategy.get('interaction_style', 'balanced')
        confidence = diana_strategy.get('adaptation_confidence', 0.5)
        
        if confidence > 0.7:
            confidence_modifier = "perfectamente"
        elif confidence > 0.5:
            confidence_modifier = "bien"
        else:
            confidence_modifier = "gradualmente"
        
        messages = {
            'mysterious_revealing': f"Diana sonríe enigmáticamente... 'Te conozco {confidence_modifier}, explorador de secretos. Hay misterios aquí que solo tú podrías apreciar.'",
            'emotionally_intimate': f"Diana te mira con calidez genuina... 'Siento una conexión especial contigo. Comprendo {confidence_modifier} lo que tu corazón busca.'",
            'intellectually_challenging': f"Diana inclina la cabeza pensativamente... 'Tu mente me fascina. Te entiendo {confidence_modifier} y tengo desafíos que estimularán tu intelecto.'",
            'progressively_challenging': f"Diana reconoce tu determinación... 'Tu persistencia es admirable. He preparado {confidence_modifier} desafíos que pondrán a prueba tu resolución.'",
            'contemplative': f"Diana pausa reflexivamente... 'Aprecio cómo procesas las cosas profundamente. Entiendo {confidence_modifier} tu necesidad de tiempo para reflexionar.'"
        }
        
        return messages.get(interaction_style, f"Diana te reconoce... 'Te estoy conociendo {confidence_modifier}, y cada interacción revela algo nuevo sobre ti.'")