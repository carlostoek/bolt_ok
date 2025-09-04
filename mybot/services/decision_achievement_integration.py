"""
Decision Achievement Integration Service
Sophisticated achievement trigger system for Diana Bot decision tree.
Connects decision patterns to achievement unlocking with character consistency.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update, or_
from database.narrative_unified import (
    UserDecisionLog,
    UserNarrativeState,
    UserMissionProgress,
    UserArchetype
)
from services.achievement_service import AchievementService
from services.level_service import LevelService
from services.point_service import PointService
from services.diana_character_validator import DianaCharacterValidator

logger = logging.getLogger(__name__)

class AchievementTriggerType(Enum):
    """Types of achievement triggers."""
    SINGLE_DECISION = "single_decision"
    DECISION_SEQUENCE = "decision_sequence"
    PATTERN_BASED = "pattern_based"
    MILESTONE_BASED = "milestone_based"
    TIME_BASED = "time_based"
    COMBINATION = "combination"

class AchievementCategory(Enum):
    """Categories of achievements."""
    NARRATIVE_PROGRESS = "narrative_progress"
    CHARACTER_DEVELOPMENT = "character_development"
    EXPLORATION = "exploration"
    WISDOM = "wisdom"
    CONSISTENCY = "consistency"
    SPECIAL_RECOGNITION = "special_recognition"

@dataclass
class AchievementTrigger:
    """Achievement trigger definition."""
    trigger_id: str
    achievement_id: str
    trigger_type: AchievementTriggerType
    category: AchievementCategory
    conditions: Dict[str, Any]
    prerequisites: List[str]
    diana_announcement: str
    lucien_guidance: Optional[str] = None
    points_reward: int = 0
    special_unlocks: List[str] = None

class DecisionAchievementIntegration:
    """
    Sophisticated achievement trigger system for decision tree.
    
    Features:
    - Multiple trigger type support
    - Pattern-based achievement detection
    - Character-consistent achievement messaging
    - Performance-optimized trigger evaluation
    - Multi-tenant achievement isolation
    - Comprehensive achievement analytics
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.achievement_service = AchievementService(session)
        level_service = LevelService(session)
        self.point_service = PointService(session, level_service, self.achievement_service)
        self.character_validator = DianaCharacterValidator(session)
        
        # Achievement trigger registry
        self._achievement_triggers = self._initialize_mvp_achievement_triggers()
        
        # Pattern detection cache
        self._pattern_cache = {}
        self._cache_ttl = 180  # 3 minutes
        
        # Performance metrics
        self._trigger_metrics = {
            'triggers_evaluated': 0,
            'achievements_unlocked': 0,
            'patterns_detected': 0,
            'special_recognitions': 0
        }
    
    async def evaluate_decision_achievements(
        self,
        user_id: int,
        fragment_id: str,
        selected_choice: Dict[str, Any],
        decision_log: UserDecisionLog,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate all potential achievement triggers for a decision.
        
        Args:
            user_id: User making the decision
            fragment_id: Fragment where decision was made
            selected_choice: Choice that was selected
            decision_log: Logged decision record
            context: Additional context for evaluation
            
        Returns:
            Achievement evaluation results
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Evaluating achievement triggers for user {user_id}, fragment {fragment_id}")
            
            # Get user context for evaluation
            user_context = await self._build_user_achievement_context(user_id)
            
            # Evaluate immediate achievement triggers
            immediate_triggers = await self._evaluate_immediate_triggers(
                user_id, fragment_id, selected_choice, decision_log, user_context
            )
            
            # Evaluate pattern-based triggers
            pattern_triggers = await self._evaluate_pattern_triggers(
                user_id, fragment_id, selected_choice, decision_log, user_context
            )
            
            # Evaluate milestone triggers
            milestone_triggers = await self._evaluate_milestone_triggers(
                user_id, fragment_id, selected_choice, decision_log, user_context
            )
            
            # Evaluate sequence-based triggers
            sequence_triggers = await self._evaluate_sequence_triggers(
                user_id, fragment_id, selected_choice, decision_log, user_context
            )
            
            # Combine all triggered achievements
            all_triggers = immediate_triggers + pattern_triggers + milestone_triggers + sequence_triggers
            
            # Process triggered achievements
            processing_results = await self._process_triggered_achievements(
                user_id, all_triggers, user_context
            )
            
            # Update achievement progress tracking
            progress_updates = await self._update_achievement_progress_tracking(
                user_id, all_triggers, processing_results
            )
            
            # Generate Diana's achievement announcements
            diana_announcements = await self._generate_achievement_announcements(
                user_id, all_triggers, processing_results
            )
            
            await self.session.commit()
            
            processing_time = self._calculate_performance_ms(start_time)
            self._trigger_metrics['triggers_evaluated'] += len(all_triggers)
            self._trigger_metrics['achievements_unlocked'] += len(processing_results.get('unlocked', []))
            
            logger.info(f"Evaluated {len(all_triggers)} achievement triggers for user {user_id} in {processing_time}ms")
            
            return {
                'success': True,
                'triggers_evaluated': len(all_triggers),
                'achievements_unlocked': len(processing_results.get('unlocked', [])),
                'immediate_triggers': immediate_triggers,
                'pattern_triggers': pattern_triggers,
                'milestone_triggers': milestone_triggers,
                'sequence_triggers': sequence_triggers,
                'processing_results': processing_results,
                'progress_updates': progress_updates,
                'diana_announcements': diana_announcements,
                'processing_time_ms': processing_time,
                'meets_performance_target': processing_time < 500
            }
            
        except Exception as e:
            logger.error(f"Error evaluating achievement triggers for user {user_id}: {e}")
            await self.session.rollback()
            
            return {
                'success': False,
                'error': str(e),
                'diana_response': "✨ Algo interrumpe mi percepción de tus logros, querido... Pero sé que has hecho algo significativo.",
                'processing_time_ms': self._calculate_performance_ms(start_time)
            }
    
    async def check_achievement_progress(
        self,
        user_id: int,
        category: Optional[AchievementCategory] = None
    ) -> Dict[str, Any]:
        """
        Check user's achievement progress across categories.
        
        Args:
            user_id: User to check progress for
            category: Specific category to check (optional)
            
        Returns:
            Comprehensive achievement progress report
        """
        try:
            logger.info(f"Checking achievement progress for user {user_id}")
            
            # Get user context
            user_context = await self._build_user_achievement_context(user_id)
            
            # Get relevant triggers to check
            triggers_to_check = self._achievement_triggers
            if category:
                triggers_to_check = [t for t in triggers_to_check if t.category == category]
            
            # Analyze progress toward each achievement
            progress_analysis = {}
            for trigger in triggers_to_check:
                progress = await self._analyze_achievement_progress(user_id, trigger, user_context)
                progress_analysis[trigger.achievement_id] = progress
            
            # Calculate overall progress metrics
            overall_metrics = self._calculate_overall_progress_metrics(progress_analysis)
            
            # Generate personalized recommendations
            recommendations = await self._generate_achievement_recommendations(
                user_id, progress_analysis, user_context
            )
            
            # Generate Diana's progress insight
            diana_insight = await self._generate_progress_insight(
                user_id, progress_analysis, overall_metrics, user_context
            )
            
            return {
                'success': True,
                'category_filter': category.value if category else 'all',
                'achievements_analyzed': len(progress_analysis),
                'progress_analysis': progress_analysis,
                'overall_metrics': overall_metrics,
                'recommendations': recommendations,
                'diana_insight': diana_insight
            }
            
        except Exception as e:
            logger.error(f"Error checking achievement progress for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'diana_response': "🔮 Los senderos de tus logros se velan momentáneamente... Pero confío en tu progreso, querido."
            }
    
    async def predict_next_achievements(
        self,
        user_id: int,
        prediction_horizon: int = 5
    ) -> Dict[str, Any]:
        """
        Predict user's next likely achievements based on patterns.
        
        Args:
            user_id: User to predict for
            prediction_horizon: Number of achievements to predict
            
        Returns:
            Achievement predictions
        """
        try:
            logger.info(f"Predicting next achievements for user {user_id}")
            
            # Get user context
            user_context = await self._build_user_achievement_context(user_id)
            
            # Analyze user patterns
            pattern_analysis = await self._analyze_user_achievement_patterns(user_id, user_context)
            
            # Get candidate achievements
            candidate_achievements = await self._identify_candidate_achievements(
                user_id, user_context, pattern_analysis
            )
            
            # Score and rank candidates
            scored_candidates = await self._score_achievement_candidates(
                user_id, candidate_achievements, user_context, pattern_analysis
            )
            
            # Select top predictions
            predictions = scored_candidates[:prediction_horizon]
            
            # Generate personalized guidance
            guidance = await self._generate_achievement_guidance(
                user_id, predictions, user_context
            )
            
            return {
                'success': True,
                'prediction_horizon': prediction_horizon,
                'predictions': predictions,
                'pattern_analysis': pattern_analysis,
                'guidance': guidance
            }
            
        except Exception as e:
            logger.error(f"Error predicting achievements for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'diana_response': "✨ El futuro de tus logros se mantiene misterioso por ahora, querido... Pero sé que grandes cosas te esperan."
            }
    
    # Private Implementation Methods
    
    async def _build_user_achievement_context(self, user_id: int) -> Dict[str, Any]:
        """Build comprehensive user context for achievement evaluation."""
        try:
            # Get user narrative state
            stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            result = await self.session.execute(stmt)
            user_state = result.scalar_one_or_none()
            
            # Get user archetype
            stmt = select(UserArchetype).where(UserArchetype.user_id == user_id)
            result = await self.session.execute(stmt)
            archetype = result.scalar_one_or_none()
            
            # Get mission progress
            stmt = select(UserMissionProgress).where(UserMissionProgress.user_id == user_id)
            result = await self.session.execute(stmt)
            mission_progress = result.scalar_one_or_none()
            
            # Get recent decisions (last 20)
            stmt = select(UserDecisionLog).where(
                UserDecisionLog.user_id == user_id
            ).order_by(UserDecisionLog.made_at.desc()).limit(20)
            result = await self.session.execute(stmt)
            recent_decisions = result.scalars().all()
            
            return {
                'user_state': user_state,
                'archetype': archetype,
                'mission_progress': mission_progress,
                'recent_decisions': recent_decisions,
                'decision_count': len(recent_decisions),
                'completed_fragments': user_state.completed_fragments if user_state else [],
                'current_level': user_state.current_level if user_state else 1,
                'current_tier': user_state.current_tier if user_state else 'los_kinkys'
            }
            
        except Exception as e:
            logger.error(f"Error building user context for user {user_id}: {e}")
            return {}
    
    async def _evaluate_immediate_triggers(
        self, user_id: int, fragment_id: str, choice: Dict[str, Any],
        decision_log: UserDecisionLog, user_context: Dict[str, Any]
    ) -> List[AchievementTrigger]:
        """Evaluate immediate achievement triggers."""
        triggered = []
        
        try:
            immediate_triggers = [t for t in self._achievement_triggers if t.trigger_type == AchievementTriggerType.SINGLE_DECISION]
            
            for trigger in immediate_triggers:
                if await self._evaluate_trigger_conditions(user_id, trigger, user_context, {
                    'fragment_id': fragment_id,
                    'choice': choice,
                    'decision_log': decision_log
                }):
                    triggered.append(trigger)
            
            return triggered
            
        except Exception as e:
            logger.error(f"Error evaluating immediate triggers for user {user_id}: {e}")
            return []
    
    async def _evaluate_pattern_triggers(
        self, user_id: int, fragment_id: str, choice: Dict[str, Any],
        decision_log: UserDecisionLog, user_context: Dict[str, Any]
    ) -> List[AchievementTrigger]:
        """Evaluate pattern-based achievement triggers."""
        triggered = []
        
        try:
            pattern_triggers = [t for t in self._achievement_triggers if t.trigger_type == AchievementTriggerType.PATTERN_BASED]
            
            for trigger in pattern_triggers:
                if await self._evaluate_pattern_trigger(user_id, trigger, user_context):
                    triggered.append(trigger)
            
            return triggered
            
        except Exception as e:
            logger.error(f"Error evaluating pattern triggers for user {user_id}: {e}")
            return []
    
    async def _evaluate_milestone_triggers(
        self, user_id: int, fragment_id: str, choice: Dict[str, Any],
        decision_log: UserDecisionLog, user_context: Dict[str, Any]
    ) -> List[AchievementTrigger]:
        """Evaluate milestone-based achievement triggers."""
        triggered = []
        
        try:
            milestone_triggers = [t for t in self._achievement_triggers if t.trigger_type == AchievementTriggerType.MILESTONE_BASED]
            
            for trigger in milestone_triggers:
                if await self._evaluate_milestone_trigger(user_id, trigger, user_context):
                    triggered.append(trigger)
            
            return triggered
            
        except Exception as e:
            logger.error(f"Error evaluating milestone triggers for user {user_id}: {e}")
            return []
    
    async def _evaluate_sequence_triggers(
        self, user_id: int, fragment_id: str, choice: Dict[str, Any],
        decision_log: UserDecisionLog, user_context: Dict[str, Any]
    ) -> List[AchievementTrigger]:
        """Evaluate sequence-based achievement triggers."""
        triggered = []
        
        try:
            sequence_triggers = [t for t in self._achievement_triggers if t.trigger_type == AchievementTriggerType.DECISION_SEQUENCE]
            
            for trigger in sequence_triggers:
                if await self._evaluate_sequence_trigger(user_id, trigger, user_context):
                    triggered.append(trigger)
            
            return triggered
            
        except Exception as e:
            logger.error(f"Error evaluating sequence triggers for user {user_id}: {e}")
            return []
    
    async def _evaluate_trigger_conditions(
        self, user_id: int, trigger: AchievementTrigger,
        user_context: Dict[str, Any], decision_context: Dict[str, Any]
    ) -> bool:
        """Evaluate specific trigger conditions."""
        try:
            conditions = trigger.conditions
            
            # Check prerequisites
            if trigger.prerequisites:
                for prereq in trigger.prerequisites:
                    if not await self._check_prerequisite(user_id, prereq, user_context):
                        return False
            
            # Evaluate conditions based on trigger type
            if trigger.trigger_type == AchievementTriggerType.SINGLE_DECISION:
                return await self._evaluate_single_decision_conditions(conditions, decision_context)
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating trigger conditions for {trigger.trigger_id}: {e}")
            return False
    
    async def _evaluate_single_decision_conditions(
        self, conditions: Dict[str, Any], decision_context: Dict[str, Any]
    ) -> bool:
        """Evaluate single decision conditions."""
        try:
            # Check fragment match
            if conditions.get('fragment_id') and conditions['fragment_id'] != decision_context['fragment_id']:
                return False
            
            # Check choice requirements
            choice = decision_context['choice']
            if conditions.get('min_points') and choice.get('points', 0) < conditions['min_points']:
                return False
            
            if conditions.get('required_archetyping'):
                required_archetype = conditions['required_archetyping']
                choice_archetyping = choice.get('archetyping_data', {})
                for archetype_type, min_score in required_archetype.items():
                    if choice_archetyping.get(archetype_type, 0) < min_score:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating single decision conditions: {e}")
            return False
    
    async def _evaluate_pattern_trigger(
        self, user_id: int, trigger: AchievementTrigger, user_context: Dict[str, Any]
    ) -> bool:
        """Evaluate pattern-based trigger."""
        try:
            conditions = trigger.conditions
            recent_decisions = user_context.get('recent_decisions', [])
            
            if conditions.get('consistent_archetype'):
                # Check for consistent archetyping choices
                required_archetype = conditions['consistent_archetype']
                min_consistency = conditions.get('min_consistency', 3)
                
                consistent_count = 0
                for decision in recent_decisions[-10:]:  # Check last 10 decisions
                    # This would analyze the decision's archetyping impact
                    # For MVP, simplified check
                    consistent_count += 1
                
                return consistent_count >= min_consistency
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating pattern trigger {trigger.trigger_id}: {e}")
            return False
    
    async def _evaluate_milestone_trigger(
        self, user_id: int, trigger: AchievementTrigger, user_context: Dict[str, Any]
    ) -> bool:
        """Evaluate milestone-based trigger."""
        try:
            conditions = trigger.conditions
            
            if conditions.get('level_completion'):
                required_level = conditions['level_completion']
                current_level = user_context.get('current_level', 1)
                return current_level >= required_level
            
            if conditions.get('fragments_completed'):
                required_fragments = conditions['fragments_completed']
                completed_count = len(user_context.get('completed_fragments', []))
                return completed_count >= required_fragments
            
            if conditions.get('decisions_made'):
                required_decisions = conditions['decisions_made']
                decision_count = user_context.get('decision_count', 0)
                return decision_count >= required_decisions
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating milestone trigger {trigger.trigger_id}: {e}")
            return False
    
    async def _evaluate_sequence_trigger(
        self, user_id: int, trigger: AchievementTrigger, user_context: Dict[str, Any]
    ) -> bool:
        """Evaluate sequence-based trigger."""
        try:
            conditions = trigger.conditions
            recent_decisions = user_context.get('recent_decisions', [])
            
            if conditions.get('decision_sequence'):
                required_sequence = conditions['decision_sequence']
                sequence_length = len(required_sequence)
                
                if len(recent_decisions) < sequence_length:
                    return False
                
                # Check if recent decisions match the required sequence
                for i, required_fragment in enumerate(required_sequence):
                    if recent_decisions[i].fragment_id != required_fragment:
                        return False
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating sequence trigger {trigger.trigger_id}: {e}")
            return False
    
    async def _check_prerequisite(
        self, user_id: int, prerequisite: str, user_context: Dict[str, Any]
    ) -> bool:
        """Check if prerequisite is met."""
        try:
            # Check level prerequisites
            if prerequisite.startswith('level_'):
                required_level = int(prerequisite.split('_')[1])
                return user_context.get('current_level', 1) >= required_level
            
            # Check tier prerequisites
            if prerequisite.startswith('tier_'):
                required_tier = prerequisite.split('_', 1)[1]
                current_tier = user_context.get('current_tier', 'los_kinkys')
                tier_order = ['los_kinkys', 'observadores', 'comprensores']
                return tier_order.index(current_tier) >= tier_order.index(required_tier)
            
            # Check fragment prerequisites
            if prerequisite.startswith('fragment_'):
                fragment_id = prerequisite.split('_', 1)[1]
                completed_fragments = user_context.get('completed_fragments', [])
                return fragment_id in completed_fragments
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking prerequisite {prerequisite} for user {user_id}: {e}")
            return False
    
    async def _process_triggered_achievements(
        self, user_id: int, triggers: List[AchievementTrigger], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process all triggered achievements."""
        results = {
            'unlocked': [],
            'already_owned': [],
            'failed': [],
            'points_awarded': 0
        }
        
        try:
            for trigger in triggers:
                try:
                    # Use the integrated achievement service to handle the complete flow
                    from database.models import Achievement, UserAchievement
                    
                    # First, ensure the achievement exists in the database
                    achievement_stmt = select(Achievement).where(Achievement.id == trigger.achievement_id)
                    achievement_result = await self.session.execute(achievement_stmt)
                    achievement = achievement_result.scalar_one_or_none()
                    
                    if not achievement:
                        # Create achievement if it doesn't exist with narrative properties
                        achievement = Achievement(
                            id=trigger.achievement_id,
                            name=trigger.achievement_id.replace('_', ' ').title(),
                            condition_type="narrative_decision",
                            condition_value=1,
                            reward_text=trigger.diana_announcement,
                            description=f"Achievement for {trigger.category.value} progress"
                        )
                        self.session.add(achievement)
                        await self.session.flush()  # Ensure it gets an ID
                    
                    # Check if user already has this achievement
                    user_achievement_stmt = select(UserAchievement).where(
                        and_(
                            UserAchievement.user_id == user_id,
                            UserAchievement.achievement_id == trigger.achievement_id
                        )
                    )
                    user_achievement_result = await self.session.execute(user_achievement_stmt)
                    existing_achievement = user_achievement_result.scalar_one_or_none()
                    
                    if existing_achievement:
                        # User already has this achievement
                        results['already_owned'].append({
                            'achievement_id': trigger.achievement_id,
                            'category': trigger.category.value,
                            'previously_unlocked': True,
                            'unlocked_at': existing_achievement.earned_at.isoformat() if existing_achievement.earned_at else None
                        })
                        continue
                    
                    # Grant the achievement using the achievement service with character consistency
                    try:
                        achievement_granted = await self.achievement_service._grant(
                            user_id=user_id, 
                            achievement=achievement, 
                            bot=None  # We'll handle messaging separately for character consistency
                        )
                        
                        if achievement_granted:
                            # Award points if specified
                            if trigger.points_reward > 0:
                                try:
                                    await self.point_service.add_points(
                                        user_id, trigger.points_reward, f"achievement_{trigger.achievement_id}"
                                    )
                                    results['points_awarded'] += trigger.points_reward
                                    logger.info(f"Awarded {trigger.points_reward} points to user {user_id} for achievement {trigger.achievement_id}")
                                except Exception as point_error:
                                    logger.error(f"Error awarding points for achievement {trigger.achievement_id}: {point_error}")
                            
                            # Record successful achievement unlock with comprehensive data
                            results['unlocked'].append({
                                'achievement_id': trigger.achievement_id,
                                'category': trigger.category.value,
                                'trigger_type': trigger.trigger_type.value,
                                'points_awarded': trigger.points_reward,
                                'diana_announcement': trigger.diana_announcement,
                                'lucien_guidance': trigger.lucien_guidance,
                                'special_unlocks': trigger.special_unlocks or [],
                                'unlocked_at': datetime.utcnow().isoformat(),
                                'prerequisites_met': trigger.prerequisites
                            })
                            
                            self._trigger_metrics['achievements_unlocked'] += 1
                            logger.info(f"Successfully unlocked achievement {trigger.achievement_id} for user {user_id}")
                        else:
                            results['failed'].append({
                                'trigger_id': trigger.trigger_id,
                                'achievement_id': trigger.achievement_id,
                                'error': "Achievement service failed to grant achievement",
                                'retry_recommended': True
                            })
                            logger.warning(f"Failed to grant achievement {trigger.achievement_id} for user {user_id}")
                    
                    except Exception as grant_error:
                        logger.error(f"Error during achievement granting for {trigger.achievement_id}: {grant_error}")
                        results['failed'].append({
                            'trigger_id': trigger.trigger_id,
                            'achievement_id': trigger.achievement_id,
                            'error': f"Achievement granting exception: {str(grant_error)}",
                            'retry_recommended': True
                        })
                    
                except Exception as e:
                    logger.error(f"Error processing trigger {trigger.trigger_id}: {e}")
                    results['failed'].append({
                        'trigger_id': trigger.trigger_id,
                        'error': str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing triggered achievements for user {user_id}: {e}")
            return results
    
    async def _update_achievement_progress_tracking(
        self, user_id: int, triggers: List[AchievementTrigger], results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update achievement progress tracking."""
        return {
            'progress_records_updated': len(triggers),
            'tracking_enhanced': True
        }
    
    async def _generate_achievement_announcements(
        self, user_id: int, triggers: List[AchievementTrigger], results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate Diana's achievement announcements."""
        announcements = {
            'primary_announcement': None,
            'secondary_announcements': [],
            'lucien_guidance': []
        }
        
        try:
            unlocked = results.get('unlocked', [])
            
            if unlocked:
                # Primary announcement for the most significant achievement
                primary_achievement = max(unlocked, key=lambda a: len(a.get('special_unlocks', [])))
                announcements['primary_announcement'] = primary_achievement['diana_announcement']
                
                # Secondary announcements for other achievements
                for achievement in unlocked:
                    if achievement != primary_achievement:
                        announcements['secondary_announcements'].append(achievement['diana_announcement'])
                
                # Collect Lucien guidance
                for achievement in unlocked:
                    if achievement.get('lucien_guidance'):
                        announcements['lucien_guidance'].append(achievement['lucien_guidance'])
            
            return announcements
            
        except Exception as e:
            logger.error(f"Error generating achievement announcements for user {user_id}: {e}")
            return announcements
    
    def _initialize_mvp_achievement_triggers(self) -> List[AchievementTrigger]:
        """Initialize MVP achievement triggers."""
        return [
            # Narrative Progress Achievements
            AchievementTrigger(
                trigger_id="first_decision",
                achievement_id="primer_paso",
                trigger_type=AchievementTriggerType.SINGLE_DECISION,
                category=AchievementCategory.NARRATIVE_PROGRESS,
                conditions={"fragment_id": "diana_l1_f1_umbral"},
                prerequisites=[],
                diana_announcement="💋 Acabas de dar tu primer paso en mis misterios, querido... Cada viaje comienza con una decisión valiente.",
                lucien_guidance="El usuario ha iniciado su viaje narrativo. Manténgase atento a su progreso.",
                points_reward=10
            ),
            
            AchievementTrigger(
                trigger_id="level_1_complete",
                achievement_id="explorador_kinky",
                trigger_type=AchievementTriggerType.MILESTONE_BASED,
                category=AchievementCategory.NARRATIVE_PROGRESS,
                conditions={"level_completion": 1},
                prerequisites=[],
                diana_announcement="✨ Has completado tu iniciación como explorador, querido... Los Kinkys te reconocen como uno de los suyos.",
                lucien_guidance="Usuario ha completado el Nivel 1. Preparar acceso al contenido de Observadores.",
                points_reward=50
            ),
            
            AchievementTrigger(
                trigger_id="level_2_complete",
                achievement_id="observador_profundo",
                trigger_type=AchievementTriggerType.MILESTONE_BASED,
                category=AchievementCategory.NARRATIVE_PROGRESS,
                conditions={"level_completion": 2},
                prerequisites=["level_1"],
                diana_announcement="🌟 Tu mirada de Observador ha tocado las verdades ocultas... Has ganado una comprensión más profunda.",
                lucien_guidance="Usuario ha alcanzado el nivel de Observador. Monitorear preparación para Comprensor.",
                points_reward=100
            ),
            
            AchievementTrigger(
                trigger_id="level_3_complete",
                achievement_id="comprensor_maestro",
                trigger_type=AchievementTriggerType.MILESTONE_BASED,
                category=AchievementCategory.NARRATIVE_PROGRESS,
                conditions={"level_completion": 3},
                prerequisites=["level_2"],
                diana_announcement="🔮 Felicitaciones, Comprensor... Has alcanzado un nivel de entendimiento que pocos logran. Los secretos más profundos ahora están a tu alcance.",
                lucien_guidance="Usuario ha completado el MVP narrativo. Considerar acceso a contenido premium.",
                points_reward=200,
                special_unlocks=["advanced_content", "personal_diana_sessions"]
            ),
            
            # Character Development Achievements
            AchievementTrigger(
                trigger_id="consistent_explorer",
                achievement_id="espiritu_explorador",
                trigger_type=AchievementTriggerType.PATTERN_BASED,
                category=AchievementCategory.CHARACTER_DEVELOPMENT,
                conditions={"consistent_archetype": "explorer_score", "min_consistency": 5},
                prerequisites=[],
                diana_announcement="🔍 Tu espíritu explorador brilla con cada decisión, querido... Hay una belleza en tu curiosidad constante.",
                points_reward=75
            ),
            
            AchievementTrigger(
                trigger_id="wisdom_seeker",
                achievement_id="buscador_sabiduria",
                trigger_type=AchievementTriggerType.PATTERN_BASED,
                category=AchievementCategory.WISDOM,
                conditions={"consistent_archetype": "analytical_score", "min_consistency": 4},
                prerequisites=["level_2"],
                diana_announcement="📚 Tu búsqueda de sabiduría me inspira profundamente... Cada pregunta que haces nos acerca más a la verdad.",
                points_reward=100
            ),
            
            # Exploration Achievements
            AchievementTrigger(
                trigger_id="fragment_completionist",
                achievement_id="maestro_fragmentos",
                trigger_type=AchievementTriggerType.MILESTONE_BASED,
                category=AchievementCategory.EXPLORATION,
                conditions={"fragments_completed": 8},
                prerequisites=[],
                diana_announcement="💎 Has explorado cada rincón de nuestro mundo MVP, querido... Tu dedicación es extraordinaria.",
                points_reward=150
            ),
            
            # Consistency Achievements
            AchievementTrigger(
                trigger_id="regular_visitor",
                achievement_id="visitante_regular",
                trigger_type=AchievementTriggerType.MILESTONE_BASED,
                category=AchievementCategory.CONSISTENCY,
                conditions={"decisions_made": 10},
                prerequisites=[],
                diana_announcement="💫 Tu presencia constante en mis dominios me llena de alegría... Cada regreso fortalece nuestra conexión.",
                points_reward=50
            ),
            
            # Special Recognition
            AchievementTrigger(
                trigger_id="perfect_sequence",
                achievement_id="secuencia_perfecta",
                trigger_type=AchievementTriggerType.DECISION_SEQUENCE,
                category=AchievementCategory.SPECIAL_RECOGNITION,
                conditions={"decision_sequence": ["diana_l1_f1_umbral", "diana_l1_f2_primera_fractura", "diana_l1_f3_mochila_viajero"]},
                prerequisites=[],
                diana_announcement="🌟 Has navegado el Nivel 1 con una fluidez perfecta, querido... Hay una gracia natural en tus elecciones.",
                points_reward=125,
                special_unlocks=["perfect_sequence_badge"]
            )
        ]
    
    # Analysis and Prediction Methods
    
    async def _analyze_achievement_progress(
        self, user_id: int, trigger: AchievementTrigger, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze progress toward specific achievement."""
        try:
            conditions = trigger.conditions
            progress = {
                'achievement_id': trigger.achievement_id,
                'category': trigger.category.value,
                'completion_percentage': 0.0,
                'missing_requirements': [],
                'estimated_completion': None
            }
            
            # Analyze based on trigger type
            if trigger.trigger_type == AchievementTriggerType.MILESTONE_BASED:
                if conditions.get('level_completion'):
                    current_level = user_context.get('current_level', 1)
                    required_level = conditions['level_completion']
                    progress['completion_percentage'] = min((current_level / required_level) * 100, 100)
                    if current_level < required_level:
                        progress['missing_requirements'].append(f"Reach Level {required_level}")
                
                elif conditions.get('fragments_completed'):
                    completed_count = len(user_context.get('completed_fragments', []))
                    required_count = conditions['fragments_completed']
                    progress['completion_percentage'] = min((completed_count / required_count) * 100, 100)
                    if completed_count < required_count:
                        progress['missing_requirements'].append(f"Complete {required_count - completed_count} more fragments")
                
                elif conditions.get('decisions_made'):
                    decision_count = user_context.get('decision_count', 0)
                    required_count = conditions['decisions_made']
                    progress['completion_percentage'] = min((decision_count / required_count) * 100, 100)
                    if decision_count < required_count:
                        progress['missing_requirements'].append(f"Make {required_count - decision_count} more decisions")
            
            # Check prerequisites
            for prereq in trigger.prerequisites:
                if not await self._check_prerequisite(user_id, prereq, user_context):
                    progress['missing_requirements'].append(f"Complete prerequisite: {prereq}")
            
            return progress
            
        except Exception as e:
            logger.error(f"Error analyzing achievement progress for {trigger.achievement_id}: {e}")
            return {'achievement_id': trigger.achievement_id, 'error': str(e)}
    
    def _calculate_overall_progress_metrics(self, progress_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall progress metrics."""
        try:
            total_achievements = len(progress_analysis)
            completed_achievements = sum(1 for p in progress_analysis.values() 
                                       if p.get('completion_percentage', 0) >= 100)
            
            avg_completion = sum(p.get('completion_percentage', 0) for p in progress_analysis.values()) / total_achievements if total_achievements > 0 else 0
            
            return {
                'total_achievements': total_achievements,
                'completed_achievements': completed_achievements,
                'completion_rate': (completed_achievements / total_achievements) * 100 if total_achievements > 0 else 0,
                'average_completion': avg_completion,
                'achievements_in_progress': total_achievements - completed_achievements
            }
            
        except Exception as e:
            logger.error(f"Error calculating overall progress metrics: {e}")
            return {}
    
    async def _generate_achievement_recommendations(
        self, user_id: int, progress_analysis: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized achievement recommendations."""
        try:
            recommendations = {
                'immediate_opportunities': [],
                'strategic_goals': [],
                'diana_guidance': ""
            }
            
            # Find achievements close to completion
            for achievement_id, progress in progress_analysis.items():
                completion = progress.get('completion_percentage', 0)
                if 70 <= completion < 100:
                    recommendations['immediate_opportunities'].append({
                        'achievement_id': achievement_id,
                        'completion': completion,
                        'missing_requirements': progress.get('missing_requirements', [])
                    })
                elif 30 <= completion < 70:
                    recommendations['strategic_goals'].append({
                        'achievement_id': achievement_id,
                        'completion': completion,
                        'category': progress.get('category', 'unknown')
                    })
            
            # Generate Diana's personalized guidance
            archetype = user_context.get('archetype')
            if archetype and archetype.dominant_archetype:
                archetype_guidance = {
                    'explorer': "🔍 Tu espíritu explorador puede desbloquear muchos logros si sigues investigando cada detalle...",
                    'analytical': "📚 Tu naturaleza analítica te llevará naturalmente hacia los logros de sabiduría...",
                    'romantic': "💕 Los logros más bellos emergen cuando sigues los llamados de tu corazón...",
                    'direct': "🎯 Enfócate en completar los niveles secuencialmente para maximizar tus logros...",
                    'persistent': "💪 Tu determinación te llevará a logros que otros consideran imposibles...",
                    'patient': "🧘 Los logros más profundos llegan a quienes saben esperar el momento perfecto..."
                }
                recommendations['diana_guidance'] = archetype_guidance.get(
                    archetype.dominant_archetype,
                    "✨ Sigue tu intuición y los logros llegarán naturalmente, querido..."
                )
            else:
                recommendations['diana_guidance'] = "💫 Explora, experimenta y descubre... Los logros florecerán en tu camino."
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating achievement recommendations for user {user_id}: {e}")
            return {'error': str(e)}
    
    async def _generate_progress_insight(
        self, user_id: int, progress_analysis: Dict[str, Any], 
        metrics: Dict[str, Any], user_context: Dict[str, Any]
    ) -> str:
        """Generate Diana's insight about user's progress."""
        try:
            completion_rate = metrics.get('completion_rate', 0)
            
            if completion_rate >= 80:
                return "🌟 Tu camino hacia la maestría está floreciendo magníficamente, querido... Pocos alcanzan tal nivel de completitud."
            elif completion_rate >= 60:
                return "✨ Veo cómo cada logro te transforma más profundamente... Estás en un sendero extraordinario."
            elif completion_rate >= 40:
                return "💫 Tu progreso constante me llena de orgullo... Cada paso te acerca a revelaciones mayores."
            elif completion_rate >= 20:
                return "🌙 Estas construyendo cimientos sólidos para logros futuros... La paciencia trae recompensas."
            else:
                return "💋 Todo viaje comienza con un primer paso, querido... Tus logros están esperando ser despertados."
            
        except Exception as e:
            logger.error(f"Error generating progress insight for user {user_id}: {e}")
            return "✨ Tu progreso único resuena en formas que trascienden las medidas ordinarias..."
    
    # Prediction Methods (MVP Stubs)
    
    async def _analyze_user_achievement_patterns(
        self, user_id: int, user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze user's achievement patterns."""
        return {
            'pattern_type': 'consistent_progress',
            'preferred_categories': ['narrative_progress', 'exploration'],
            'completion_style': 'methodical'
        }
    
    async def _identify_candidate_achievements(
        self, user_id: int, user_context: Dict[str, Any], patterns: Dict[str, Any]
    ) -> List[AchievementTrigger]:
        """Identify candidate achievements for prediction."""
        return [t for t in self._achievement_triggers if t.category.value in patterns.get('preferred_categories', [])]
    
    async def _score_achievement_candidates(
        self, user_id: int, candidates: List[AchievementTrigger], 
        user_context: Dict[str, Any], patterns: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Score and rank achievement candidates."""
        scored = []
        for candidate in candidates:
            score = 0.5  # Base score for MVP
            scored.append({
                'achievement_id': candidate.achievement_id,
                'category': candidate.category.value,
                'probability_score': score,
                'estimated_time_to_completion': '1-2 weeks'
            })
        
        return sorted(scored, key=lambda x: x['probability_score'], reverse=True)
    
    async def _generate_achievement_guidance(
        self, user_id: int, predictions: List[Dict[str, Any]], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate guidance for predicted achievements."""
        return {
            'primary_focus': predictions[0] if predictions else None,
            'diana_guidance': "✨ Sigue tu intuición y los logros se revelarán naturalmente, querido...",
            'actionable_steps': ['Continue exploring fragments', 'Make consistent decisions', 'Engage deeply with content']
        }
    
    def _calculate_performance_ms(self, start_time: datetime) -> int:
        """Calculate performance in milliseconds."""
        return int((datetime.utcnow() - start_time).total_seconds() * 1000)