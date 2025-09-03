"""
MVP Narrative Progression Service
Handles user progression through Diana Bot's narrative system with performance optimization.
Manages Level 1-3 progression: Los Kinkys → Observadores → Comprensores.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update
from database.narrative_unified import (
    NarrativeFragment, 
    UserNarrativeState, 
    UserDecisionLog,
    UserMissionProgress,
    UserArchetype
)
from services.mvp_narrative_fragment_service import MVPNarrativeFragmentService
from services.point_service import PointService
from services.level_service import LevelService
from services.achievement_service import AchievementService

logger = logging.getLogger(__name__)

class MVPNarrativeProgressionService:
    """
    MVP service for narrative progression management.
    
    Features:
    - Fast progression processing <500ms
    - Level advancement tracking (1-3)
    - Basic archetyping data collection
    - Besitos/points integration
    - Character consistency preservation
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.fragment_service = MVPNarrativeFragmentService(session)
        
        # Initialize dependency services for PointService
        level_service = LevelService(session)
        achievement_service = AchievementService(session)
        self.point_service = PointService(session, level_service, achievement_service)
        
        # Performance optimization
        self._progression_cache = {}
        self._cache_ttl = 180  # 3 minutes for progression data
    
    async def start_user_narrative(self, user_id: int) -> Dict[str, Any]:
        """
        Start narrative experience for a new user.
        Initializes state and returns first fragment.
        """
        try:
            logger.info(f"Starting narrative for user {user_id}")
            
            # Get or create user state
            user_state = await self.fragment_service._get_or_create_user_state(user_id)
            mission_progress = await self.fragment_service._get_or_create_mission_progress(user_id)
            
            # Get starting fragment (Level 1, Fragment 1)
            start_fragment = await self.fragment_service._get_fragment_cached('diana_l1_f1_umbral')
            if not start_fragment:
                logger.error("Starting fragment 'diana_l1_f1_umbral' not found")
                return {
                    'success': False,
                    'error': 'Starting fragment not available',
                    'fragment': None
                }
            
            # Set current fragment
            user_state.current_fragment_id = start_fragment.id
            
            # Initialize archetype tracking
            await self._initialize_user_archetype(user_id)
            
            await self.session.commit()
            
            return {
                'success': True,
                'fragment': start_fragment,
                'user_level': user_state.current_level,
                'user_tier': user_state.current_tier,
                'progress_percentage': 0
            }
            
        except Exception as e:
            logger.error(f"Error starting narrative for user {user_id}: {e}")
            await self.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'fragment': None
            }
    
    async def process_user_choice_advanced(
        self, 
        user_id: int, 
        choice_index: int,
        response_time_ms: Optional[int] = None,
        additional_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Advanced choice processing with archetyping and performance tracking.
        """
        start_time = datetime.utcnow()
        
        try:
            # Get current fragment and validate choice
            current_fragment = await self.fragment_service.get_user_current_fragment(user_id)
            if not current_fragment or not current_fragment.is_decision:
                return {
                    'success': False,
                    'error': 'No valid decision fragment found',
                    'performance_ms': self._calculate_performance_ms(start_time)
                }
            
            if choice_index < 0 or choice_index >= len(current_fragment.choices):
                return {
                    'success': False,
                    'error': 'Invalid choice index',
                    'performance_ms': self._calculate_performance_ms(start_time)
                }
            
            selected_choice = current_fragment.choices[choice_index]
            
            # Process the choice using the fragment service
            choice_result = await self.fragment_service.process_user_choice(
                user_id, 
                choice_index, 
                additional_context
            )
            
            if not choice_result['success']:
                return {
                    'success': False,
                    'error': choice_result['error'],
                    'performance_ms': self._calculate_performance_ms(start_time)
                }
            
            # Enhanced processing: Update archetype data
            await self._update_user_archetype(
                user_id, 
                selected_choice, 
                response_time_ms,
                current_fragment
            )
            
            # Track interaction patterns
            await self._track_interaction_patterns(
                user_id,
                current_fragment,
                selected_choice,
                response_time_ms
            )
            
            # Get enhanced progress summary
            progress_summary = await self.get_comprehensive_progress(user_id)
            
            # Build comprehensive response
            result = {
                'success': True,
                'current_fragment': choice_result['next_fragment'],
                'choice_processed': selected_choice,
                'points_awarded': choice_result['points_awarded'],
                'level_progression': choice_result.get('level_progression', {}),
                'progress_summary': progress_summary,
                'performance_ms': self._calculate_performance_ms(start_time),
                'meets_performance_target': self._calculate_performance_ms(start_time) < 500
            }
            
            await self.session.commit()
            
            logger.info(
                f"Choice processed for user {user_id}: Fragment {current_fragment.id} -> "
                f"{choice_result['next_fragment'].id if choice_result['next_fragment'] else 'None'} "
                f"({self._calculate_performance_ms(start_time)}ms)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing advanced choice for user {user_id}: {e}")
            await self.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'performance_ms': self._calculate_performance_ms(start_time)
            }
    
    async def get_comprehensive_progress(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive user progress with archetyping insights.
        """
        try:
            # Get basic progress
            basic_progress = await self.fragment_service.get_user_progress_summary(user_id)
            
            # Get archetype data
            archetype_data = await self._get_user_archetype_summary(user_id)
            
            # Get interaction patterns
            interaction_patterns = await self._get_interaction_patterns(user_id)
            
            # Calculate estimated completion time for current level
            estimated_completion = await self._estimate_level_completion_time(user_id)
            
            return {
                **basic_progress,
                'archetype_profile': archetype_data,
                'interaction_patterns': interaction_patterns,
                'estimated_completion_time': estimated_completion,
                'mvp_completion_percentage': self._calculate_mvp_completion(basic_progress)
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive progress for user {user_id}: {e}")
            return {
                'error': str(e),
                'current_level': 1,
                'progress_percentage': 0
            }
    
    async def get_next_recommended_action(self, user_id: int) -> Dict[str, Any]:
        """
        Get personalized next action recommendation based on user's archetype and progress.
        """
        try:
            current_fragment = await self.fragment_service.get_user_current_fragment(user_id)
            archetype_data = await self._get_user_archetype_summary(user_id)
            
            if not current_fragment:
                return {
                    'action': 'start_narrative',
                    'message': '💋 Comienza tu viaje con Diana...',
                    'fragment': None
                }
            
            # Personalized messages based on dominant archetype
            dominant_archetype = archetype_data.get('dominant_archetype', 'explorer')
            
            personalized_messages = {
                'explorer': '🔍 Un nuevo misterio te espera. ¿Explorarás sus secretos?',
                'direct': '🎯 Diana tiene algo importante que revelarte. ¿Continuamos?',
                'romantic': '💕 Los secretos del corazón aguardan tu atención...',
                'analytical': '📚 Un enigma complejo espera tu comprensión profunda...',
                'persistent': '💪 Has llegado lejos. ¿Seguirás adelante con determinación?',
                'patient': '🧘 Tómate tu tiempo para absorber cada detalle...'
            }
            
            message = personalized_messages.get(
                dominant_archetype, 
                '✨ Diana te espera con nuevos secretos...'
            )
            
            return {
                'action': 'continue_narrative',
                'message': message,
                'fragment': current_fragment,
                'personalized_for_archetype': dominant_archetype
            }
            
        except Exception as e:
            logger.error(f"Error getting next action for user {user_id}: {e}")
            return {
                'action': 'error',
                'message': '😔 Algo interrumpe nuestra conexión... Inténtalo de nuevo.',
                'error': str(e)
            }
    
    # Private helper methods
    
    async def _initialize_user_archetype(self, user_id: int):
        """Initialize user archetype tracking."""
        try:
            stmt = select(UserArchetype).where(UserArchetype.user_id == user_id)
            result = await self.session.execute(stmt)
            existing_archetype = result.scalar_one_or_none()
            
            if not existing_archetype:
                new_archetype = UserArchetype(
                    user_id=user_id,
                    explorer_score=0,
                    direct_score=0,
                    romantic_score=0,
                    analytical_score=0,
                    persistent_score=0,
                    patient_score=0
                )
                self.session.add(new_archetype)
                await self.session.flush()
                
        except Exception as e:
            logger.error(f"Error initializing archetype for user {user_id}: {e}")
    
    async def _update_user_archetype(
        self, 
        user_id: int, 
        selected_choice: Dict[str, Any], 
        response_time_ms: Optional[int],
        fragment: NarrativeFragment
    ):
        """Update user archetype based on choice and behavior."""
        try:
            stmt = select(UserArchetype).where(UserArchetype.user_id == user_id)
            result = await self.session.execute(stmt)
            archetype = result.scalar_one_or_none()
            
            if not archetype:
                await self._initialize_user_archetype(user_id)
                stmt = select(UserArchetype).where(UserArchetype.user_id == user_id)
                result = await self.session.execute(stmt)
                archetype = result.scalar_one_or_none()
            
            if archetype:
                # Extract archetyping data from choice
                archetype_data = selected_choice.get('archetyping_data', {})
                
                # Update scores based on choice data
                for archetype_type, score_increase in archetype_data.items():
                    if hasattr(archetype, f"{archetype_type}"):
                        current_score = getattr(archetype, f"{archetype_type}")
                        setattr(archetype, f"{archetype_type}", current_score + score_increase)
                
                # Update response time tracking
                if response_time_ms:
                    current_avg = archetype.avg_response_time
                    if current_avg == 0:
                        archetype.avg_response_time = response_time_ms
                    else:
                        # Moving average
                        archetype.avg_response_time = int((current_avg * 0.8) + (response_time_ms * 0.2))
                    
                    # Classify response speed
                    if response_time_ms > 30000:  # > 30 seconds
                        archetype.patient_score += 2
                    elif response_time_ms < 5000:  # < 5 seconds
                        archetype.direct_score += 1
                
                # Calculate dominant archetype
                archetype.calculate_dominant_archetype()
                
        except Exception as e:
            logger.error(f"Error updating archetype for user {user_id}: {e}")
    
    async def _track_interaction_patterns(
        self, 
        user_id: int, 
        fragment: NarrativeFragment, 
        choice: Dict[str, Any],
        response_time_ms: Optional[int]
    ):
        """Track detailed interaction patterns for future behavioral analysis."""
        try:
            user_state = await self.fragment_service._get_or_create_user_state(user_id)
            
            # Update interaction patterns
            if not user_state.interaction_patterns:
                user_state.interaction_patterns = {}
            
            patterns = user_state.interaction_patterns
            
            # Track choice patterns
            choice_pattern_key = f"choice_pattern_{fragment.storyline_level}"
            if choice_pattern_key not in patterns:
                patterns[choice_pattern_key] = []
            
            patterns[choice_pattern_key].append({
                'fragment_id': fragment.id,
                'choice_index': choice.get('index', 0),
                'choice_text': choice.get('text', ''),
                'points_awarded': choice.get('points', 0),
                'response_time_ms': response_time_ms,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Keep only last 10 choices per level
            patterns[choice_pattern_key] = patterns[choice_pattern_key][-10:]
            
            # Track response time patterns
            if response_time_ms and 'response_times' not in patterns:
                patterns['response_times'] = []
            
            if response_time_ms:
                patterns['response_times'].append({
                    'fragment_level': fragment.storyline_level,
                    'response_time_ms': response_time_ms,
                    'timestamp': datetime.utcnow().isoformat()
                })
                patterns['response_times'] = patterns['response_times'][-20:]  # Keep last 20
            
            user_state.interaction_patterns = patterns
            
        except Exception as e:
            logger.error(f"Error tracking interaction patterns for user {user_id}: {e}")
    
    async def _get_user_archetype_summary(self, user_id: int) -> Dict[str, Any]:
        """Get user archetype summary with distribution."""
        try:
            stmt = select(UserArchetype).where(UserArchetype.user_id == user_id)
            result = await self.session.execute(stmt)
            archetype = result.scalar_one_or_none()
            
            if not archetype:
                return {
                    'dominant_archetype': 'explorer',
                    'distribution': {},
                    'behavioral_indicators': {}
                }
            
            distribution = archetype.get_archetype_distribution()
            
            behavioral_indicators = {
                'avg_response_time_seconds': archetype.avg_response_time // 1000 if archetype.avg_response_time else 0,
                'content_revisit_tendency': archetype.content_revisit_count,
                'deep_exploration_sessions': archetype.deep_exploration_sessions,
                'emotional_vocabulary_richness': archetype.emotional_vocabulary_usage
            }
            
            return {
                'dominant_archetype': archetype.dominant_archetype,
                'distribution': distribution,
                'behavioral_indicators': behavioral_indicators
            }
            
        except Exception as e:
            logger.error(f"Error getting archetype summary for user {user_id}: {e}")
            return {
                'dominant_archetype': 'explorer',
                'distribution': {},
                'error': str(e)
            }
    
    async def _get_interaction_patterns(self, user_id: int) -> Dict[str, Any]:
        """Get user interaction patterns analysis."""
        try:
            user_state = await self.fragment_service._get_or_create_user_state(user_id)
            
            if not user_state.interaction_patterns:
                return {
                    'avg_response_time_ms': 0,
                    'choice_consistency': 0,
                    'engagement_depth': 'new_user'
                }
            
            patterns = user_state.interaction_patterns
            
            # Calculate average response time
            response_times = patterns.get('response_times', [])
            if response_times:
                avg_response_time = sum(rt['response_time_ms'] for rt in response_times) / len(response_times)
            else:
                avg_response_time = 0
            
            # Calculate engagement depth
            total_interactions = sum(
                len(patterns.get(f"choice_pattern_{level}", [])) for level in range(1, 4)
            )
            
            if total_interactions >= 5:
                engagement_depth = 'highly_engaged'
            elif total_interactions >= 2:
                engagement_depth = 'moderately_engaged'
            else:
                engagement_depth = 'exploring'
            
            return {
                'avg_response_time_ms': int(avg_response_time),
                'total_interactions': total_interactions,
                'engagement_depth': engagement_depth,
                'pattern_consistency': self._calculate_pattern_consistency(patterns)
            }
            
        except Exception as e:
            logger.error(f"Error getting interaction patterns for user {user_id}: {e}")
            return {'error': str(e)}
    
    async def _estimate_level_completion_time(self, user_id: int) -> Dict[str, Any]:
        """Estimate time to complete current level based on user patterns."""
        try:
            user_state = await self.fragment_service._get_or_create_user_state(user_id)
            current_level = user_state.current_level
            
            # Fragment count per level
            fragments_per_level = {1: 3, 2: 3, 3: 2}
            remaining_fragments = fragments_per_level.get(current_level, 3) - len(user_state.completed_fragments)
            
            # Get user's average response time
            archetype = await self._get_user_archetype_summary(user_id)
            avg_response_time = archetype['behavioral_indicators'].get('avg_response_time_seconds', 30)
            
            # Estimate completion time (response time + reading time)
            estimated_time_per_fragment = avg_response_time + 120  # 2 minutes reading time
            total_estimated_seconds = remaining_fragments * estimated_time_per_fragment
            
            return {
                'remaining_fragments': remaining_fragments,
                'estimated_minutes': total_estimated_seconds // 60,
                'estimated_seconds': total_estimated_seconds % 60,
                'based_on_avg_response_time': avg_response_time
            }
            
        except Exception as e:
            logger.error(f"Error estimating completion time for user {user_id}: {e}")
            return {'estimated_minutes': 10, 'error': str(e)}
    
    def _calculate_mvp_completion(self, progress_data: Dict[str, Any]) -> float:
        """Calculate MVP completion percentage."""
        try:
            current_level = progress_data.get('current_level', 1)
            completed_count = progress_data.get('fragments_completed', 0)
            
            # MVP has 8 total fragments (3+3+2)
            mvp_total = 8
            
            return min((completed_count / mvp_total) * 100, 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating MVP completion: {e}")
            return 0.0
    
    def _calculate_pattern_consistency(self, patterns: Dict[str, Any]) -> float:
        """Calculate how consistent user's choice patterns are."""
        try:
            # Simple consistency metric based on response time variance
            response_times = patterns.get('response_times', [])
            if len(response_times) < 2:
                return 0.5  # Neutral consistency for new users
            
            times = [rt['response_time_ms'] for rt in response_times]
            avg_time = sum(times) / len(times)
            variance = sum((t - avg_time) ** 2 for t in times) / len(times)
            
            # Lower variance = higher consistency
            consistency_score = max(0, 1 - (variance / (avg_time ** 2)))
            return round(consistency_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating pattern consistency: {e}")
            return 0.5
    
    def _calculate_performance_ms(self, start_time: datetime) -> int:
        """Calculate performance in milliseconds."""
        return int((datetime.utcnow() - start_time).total_seconds() * 1000)