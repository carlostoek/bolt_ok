"""
Lucien Coordination Service

Manages Lucien's dynamic appearance and coordination role in the master storyline system.
Provides intelligent timing for when Lucien should appear/disappear based on user state,
narrative context, and Diana's availability.

Key Features:
- Context-aware appearance logic based on user needs
- Dynamic role adaptation (guide, coordinator, messenger, support)
- Seamless integration with Diana's personality system
- Real-time coordination with narrative flow
- User emotional state monitoring for optimal timing
- Performance-optimized coordination decisions
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func, desc

from database.narrative_unified import (
    LucienCoordination,
    UserNarrativeState,
    UserMissionProgress,
    UserArchetype,
    NarrativeFragment
)

logger = logging.getLogger(__name__)

class LucienRole(Enum):
    """Lucien's possible roles in coordination."""
    GUIDE = "guide"                     # Guiding user through narrative
    COORDINATOR = "coordinator"         # Coordinating between Diana and user
    MESSENGER = "messenger"            # Delivering Diana's messages
    SUPPORT = "support"                # Supporting user during difficulties
    GUARDIAN = "guardian"              # Protecting narrative integrity
    FACILITATOR = "facilitator"        # Facilitating VIP transitions

class CoordinationMode(Enum):
    """Modes of Lucien's coordination behavior."""
    HIDDEN = "hidden"                  # Not actively coordinating
    OBSERVING = "observing"           # Watching but not interfering
    GUIDING = "guiding"               # Actively guiding user
    TRANSITIONING = "transitioning"    # Managing narrative transitions
    EMERGENCY = "emergency"           # Handling system issues

class UserEmotionalState(Enum):
    """User emotional states that influence coordination."""
    CURIOUS = "curious"               # Engaged and exploring
    CONFUSED = "confused"             # Lost or uncertain
    FRUSTRATED = "frustrated"        # Experiencing difficulties
    ENGAGED = "engaged"               # Deeply involved in narrative
    IMPATIENT = "impatient"          # Wanting faster progression
    CONTEMPLATIVE = "contemplative"   # Processing deeply

@dataclass
class CoordinationTrigger:
    """Trigger conditions for Lucien coordination."""
    trigger_type: str
    conditions: Dict[str, Any]
    priority: int  # 1-10, higher is more urgent
    context: str
    user_state_requirements: Optional[Dict[str, Any]] = None

@dataclass
class CoordinationAction:
    """Action for Lucien to take."""
    action_type: str  # appear, disappear, message, redirect
    role: LucienRole
    message: str
    duration_estimate: int  # Estimated duration in seconds
    follow_up_actions: List[str] = None

class LucienCoordinationService:
    """
    Service for managing Lucien's coordination and appearance logic.
    Ensures seamless integration between Diana, user, and system operations.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Coordination triggers and their priorities
        self.coordination_triggers = {
            'user_confusion': CoordinationTrigger(
                trigger_type='user_confusion',
                conditions={'consecutive_errors': 2, 'time_without_progress': 300},
                priority=8,
                context='user_needs_help',
                user_state_requirements={'emotional_state': 'confused'}
            ),
            'narrative_transition': CoordinationTrigger(
                trigger_type='narrative_transition',
                conditions={'tier_change': True, 'level_progression': True},
                priority=7,
                context='system_transition',
                user_state_requirements={'progression_event': True}
            ),
            'vip_opportunity': CoordinationTrigger(
                trigger_type='vip_opportunity',
                conditions={'vip_readiness_score': 0.7, 'completed_tier_percentage': 0.8},
                priority=6,
                context='upgrade_opportunity'
            ),
            'mission_introduction': CoordinationTrigger(
                trigger_type='mission_introduction',
                conditions={'new_mission_available': True, 'mission_complexity': 'high'},
                priority=5,
                context='mission_guidance'
            ),
            'character_consistency_issue': CoordinationTrigger(
                trigger_type='character_consistency_issue',
                conditions={'consistency_score': 90, 'fallback_triggered': True},
                priority=9,
                context='system_recovery',
                user_state_requirements={'needs_explanation': True}
            ),
            'achievement_recognition': CoordinationTrigger(
                trigger_type='achievement_recognition',
                conditions={'major_achievement': True, 'archetype': 'persistent'},
                priority=4,
                context='celebration'
            )
        }
        
        # Role-specific message templates
        self.role_messages = {
            LucienRole.GUIDE: {
                'appearance': "Lucien aparece discretamente, con la elegancia de quien comprende los momentos precisos...",
                'guidance': "Permíteme ofrecerte algo de contexto sobre lo que Diana está compartiendo contigo.",
                'transition': "Te acompañaré durante esta transición para asegurarme de que todo fluya perfectamente."
            },
            LucienRole.COORDINATOR: {
                'appearance': "Lucien se materializa con la autoridad serena de quien orquesta experiencias únicas...",
                'coordination': "Diana está preparando algo especial. Mientras tanto, permíteme coordinar los detalles.",
                'system_message': "Hay algunos elementos del sistema que requieren coordinación. Mantengo todo en orden."
            },
            LucienRole.MESSENGER: {
                'appearance': "Lucien emerge de las sombras, portando un mensaje que Diana no puede entregar personalmente...",
                'delivery': "Diana me ha confiado un mensaje específicamente para ti:",
                'clarification': "Diana quiere asegurarme de que comprendas completamente sus intenciones."
            },
            LucienRole.SUPPORT: {
                'appearance': "Lucien aparece con una presencia tranquilizadora, reconociendo tu situación...",
                'encouragement': "Veo que estás navegando por aguas complejas. Permíteme ofrecerte apoyo.",
                'problem_solving': "Entiendo la dificultad que estás experimentando. Trabajemos juntos para resolverla."
            },
            LucienRole.GUARDIAN: {
                'appearance': "Lucien se presenta con la solemnidad de quien protege algo valioso...",
                'protection': "Hay aspectos de esta experiencia que requieren protección especial.",
                'boundary_setting': "Permíteme establecer algunos límites para preservar la integridad de tu viaje."
            },
            LucienRole.FACILITATOR: {
                'appearance': "Lucien aparece con la sofisticación de quien facilita transiciones importantes...",
                'facilitation': "Estás a punto de acceder a un nivel completamente nuevo de experiencia.",
                'vip_transition': "Diana me ha pedido que facilite tu transición a una experiencia más exclusiva."
            }
        }
        
        # Archetype-specific coordination styles
        self.archetype_coordination_styles = {
            'explorer': {
                'approach': 'mysterious_hints',
                'communication_style': 'suggestive',
                'information_level': 'partial',
                'independence_level': 'high'
            },
            'direct': {
                'approach': 'clear_guidance',
                'communication_style': 'straightforward',
                'information_level': 'complete',
                'independence_level': 'medium'
            },
            'romantic': {
                'approach': 'emotional_support',
                'communication_style': 'warm',
                'information_level': 'contextual',
                'independence_level': 'supportive'
            },
            'analytical': {
                'approach': 'detailed_explanation',
                'communication_style': 'informative',
                'information_level': 'comprehensive',
                'independence_level': 'consultative'
            },
            'persistent': {
                'approach': 'challenge_acknowledgment',
                'communication_style': 'respectful',
                'information_level': 'progressive',
                'independence_level': 'high'
            },
            'patient': {
                'approach': 'thoughtful_guidance',
                'communication_style': 'contemplative',
                'information_level': 'layered',
                'independence_level': 'gentle'
            }
        }
    
    async def evaluate_coordination_needs(
        self, 
        user_id: int, 
        context: Dict[str, Any]
    ) -> Optional[CoordinationAction]:
        """
        Evaluate if Lucien coordination is needed and what action to take.
        
        Args:
            user_id: User ID to evaluate
            context: Current context and user state information
            
        Returns:
            CoordinationAction if coordination is needed, None otherwise
        """
        try:
            # Get user's current coordination state
            coordination_state = await self._get_user_coordination_state(user_id)
            
            # If Lucien is already active, check if he should continue or step back
            if coordination_state and coordination_state.is_active:
                return await self._evaluate_active_coordination(coordination_state, context)
            
            # Evaluate triggers for new coordination
            triggered_actions = []
            
            for trigger_name, trigger_config in self.coordination_triggers.items():
                if await self._should_trigger_coordination(trigger_config, context, user_id):
                    action = await self._create_coordination_action(
                        trigger_config, context, user_id
                    )
                    if action:
                        triggered_actions.append((trigger_config.priority, action))
            
            # Return highest priority action
            if triggered_actions:
                triggered_actions.sort(key=lambda x: x[0], reverse=True)
                return triggered_actions[0][1]
            
            return None
            
        except Exception as e:
            logger.error(f"Error evaluating coordination needs for user {user_id}: {e}")
            return None
    
    async def execute_coordination_action(
        self, 
        user_id: int, 
        action: CoordinationAction
    ) -> Dict[str, Any]:
        """
        Execute a coordination action for Lucien.
        
        Args:
            user_id: User ID
            action: Coordination action to execute
            
        Returns:
            Dictionary with execution result and next steps
        """
        try:
            coordination_state = await self._get_user_coordination_state(user_id)
            
            if action.action_type == 'appear':
                result = await self._execute_appearance_action(user_id, action, coordination_state)
            elif action.action_type == 'disappear':
                result = await self._execute_disappearance_action(user_id, action, coordination_state)
            elif action.action_type == 'message':
                result = await self._execute_message_action(user_id, action, coordination_state)
            elif action.action_type == 'redirect':
                result = await self._execute_redirect_action(user_id, action, coordination_state)
            else:
                result = {'success': False, 'error': f'Unknown action type: {action.action_type}'}
            
            # Record coordination event
            await self._record_coordination_event(user_id, action, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing coordination action for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_coordination_analytics(self, user_id: int, days_back: int = 7) -> Dict[str, Any]:
        """
        Get analytics on Lucien's coordination effectiveness for a user.
        
        Args:
            user_id: User ID
            days_back: Number of days to analyze
            
        Returns:
            Dictionary with coordination analytics
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Get coordination history
            coordination_state = await self._get_user_coordination_state(user_id)
            
            if not coordination_state or not coordination_state.appearance_history:
                return {
                    'total_appearances': 0,
                    'average_effectiveness': 0,
                    'most_common_role': None,
                    'coordination_frequency': 0,
                    'user_satisfaction_proxy': 0
                }
            
            # Analyze appearance history
            recent_appearances = [
                appearance for appearance in coordination_state.appearance_history
                if datetime.fromisoformat(appearance['appeared_at']) >= since_date
            ]
            
            # Calculate metrics
            total_appearances = len(recent_appearances)
            
            # Effectiveness scores
            effectiveness_scores = [
                appearance.get('effectiveness_score', 50)
                for appearance in recent_appearances
                if 'effectiveness_score' in appearance
            ]
            average_effectiveness = sum(effectiveness_scores) / len(effectiveness_scores) if effectiveness_scores else 0
            
            # Role frequency
            role_counts = {}
            for appearance in recent_appearances:
                role = appearance.get('coordination_mode', 'unknown')
                role_counts[role] = role_counts.get(role, 0) + 1
            
            most_common_role = max(role_counts, key=role_counts.get) if role_counts else None
            
            # Coordination frequency (appearances per day)
            coordination_frequency = total_appearances / max(days_back, 1)
            
            # User satisfaction proxy (based on continued engagement after coordination)
            satisfaction_proxy = average_effectiveness * 0.7 + (1 / max(coordination_frequency, 0.1)) * 0.3 * 100
            
            return {
                'analysis_period_days': days_back,
                'total_appearances': total_appearances,
                'average_effectiveness': round(average_effectiveness, 1),
                'most_common_role': most_common_role,
                'role_distribution': role_counts,
                'coordination_frequency': round(coordination_frequency, 2),
                'user_satisfaction_proxy': round(min(satisfaction_proxy, 100), 1),
                'recent_coordination_events': len(recent_appearances),
                'coordination_trends': self._analyze_coordination_trends(recent_appearances)
            }
            
        except Exception as e:
            logger.error(f"Error getting coordination analytics for user {user_id}: {e}")
            return {'error': str(e)}
    
    async def optimize_coordination_timing(self, user_id: int, user_archetype: str) -> Dict[str, Any]:
        """
        Optimize coordination timing based on user archetype and behavior patterns.
        
        Args:
            user_id: User ID
            user_archetype: User's dominant archetype
            
        Returns:
            Dictionary with optimized coordination settings
        """
        try:
            coordination_style = self.archetype_coordination_styles.get(user_archetype, {})
            coordination_state = await self._get_user_coordination_state(user_id)
            
            # Default optimization settings
            optimization_settings = {
                'appearance_threshold': 0.6,  # How readily Lucien should appear (0-1)
                'independence_level': coordination_style.get('independence_level', 'medium'),
                'communication_preference': coordination_style.get('communication_style', 'balanced'),
                'information_depth': coordination_style.get('information_level', 'moderate'),
                'proactive_guidance': coordination_style.get('approach', 'balanced')
            }
            
            # Adjust based on archetype
            if user_archetype == 'explorer':
                optimization_settings['appearance_threshold'] = 0.8  # Let them explore more
                optimization_settings['hint_density'] = 'sparse'
                optimization_settings['mystery_preservation'] = 'high'
                
            elif user_archetype == 'direct':
                optimization_settings['appearance_threshold'] = 0.4  # More readily available
                optimization_settings['explanation_completeness'] = 'full'
                optimization_settings['efficiency_focus'] = 'high'
                
            elif user_archetype == 'romantic':
                optimization_settings['appearance_threshold'] = 0.5
                optimization_settings['emotional_support_level'] = 'high'
                optimization_settings['narrative_context_emphasis'] = 'emotional'
                
            elif user_archetype == 'analytical':
                optimization_settings['appearance_threshold'] = 0.6
                optimization_settings['detail_level'] = 'comprehensive'
                optimization_settings['reasoning_transparency'] = 'high'
                
            elif user_archetype == 'persistent':
                optimization_settings['appearance_threshold'] = 0.7  # Respect their determination
                optimization_settings['challenge_acknowledgment'] = 'high'
                optimization_settings['achievement_recognition'] = 'prominent'
                
            elif user_archetype == 'patient':
                optimization_settings['appearance_threshold'] = 0.5
                optimization_settings['pacing'] = 'thoughtful'
                optimization_settings['reflection_time'] = 'extended'
            
            # Apply historical effectiveness adjustments
            if coordination_state and coordination_state.coordination_effectiveness:
                effectiveness = coordination_state.coordination_effectiveness
                if effectiveness > 80:
                    # High effectiveness - maintain current approach
                    optimization_settings['confidence_multiplier'] = 1.0
                elif effectiveness < 60:
                    # Low effectiveness - adjust approach
                    optimization_settings['appearance_threshold'] *= 1.2  # Be more selective
                    optimization_settings['adaptation_needed'] = True
                    optimization_settings['confidence_multiplier'] = 0.8
            
            # Update coordination state with optimized settings
            if coordination_state:
                coordination_state.trigger_conditions = optimization_settings
                await self.session.commit()
            
            return {
                'user_archetype': user_archetype,
                'optimization_settings': optimization_settings,
                'coordination_effectiveness': coordination_state.coordination_effectiveness if coordination_state else 50,
                'recommendations': self._generate_coordination_recommendations(user_archetype, optimization_settings)
            }
            
        except Exception as e:
            logger.error(f"Error optimizing coordination timing for user {user_id}: {e}")
            return {'error': str(e)}
    
    # Private helper methods
    
    async def _get_user_coordination_state(self, user_id: int) -> Optional[LucienCoordination]:
        """Get user's coordination state."""
        stmt = select(LucienCoordination).where(LucienCoordination.user_id == user_id)
        result = await self.session.execute(stmt)
        coordination_state = result.scalar_one_or_none()
        
        if not coordination_state:
            # Create initial coordination state
            coordination_state = LucienCoordination(
                user_id=user_id,
                coordination_mode='hidden',
                current_role='guide',
                trigger_conditions={},
                narrative_phase='introduction',
                is_active=False
            )
            self.session.add(coordination_state)
            await self.session.commit()
            await self.session.refresh(coordination_state)
        
        return coordination_state
    
    async def _should_trigger_coordination(
        self, 
        trigger_config: CoordinationTrigger, 
        context: Dict[str, Any], 
        user_id: int
    ) -> bool:
        """Check if coordination should be triggered based on conditions."""
        # Check basic conditions
        for condition_key, expected_value in trigger_config.conditions.items():
            actual_value = context.get(condition_key)
            
            if isinstance(expected_value, (int, float)):
                if isinstance(actual_value, (int, float)):
                    if condition_key.endswith('_score') or condition_key.endswith('_rate'):
                        if actual_value < expected_value:  # Score thresholds
                            continue
                    else:
                        if actual_value < expected_value:  # Count thresholds
                            return False
                else:
                    return False
            elif isinstance(expected_value, bool):
                if actual_value != expected_value:
                    return False
            elif isinstance(expected_value, str):
                if actual_value != expected_value:
                    return False
        
        # Check user state requirements if specified
        if trigger_config.user_state_requirements:
            for requirement_key, required_value in trigger_config.user_state_requirements.items():
                if context.get(requirement_key) != required_value:
                    return False
        
        return True
    
    async def _create_coordination_action(
        self, 
        trigger_config: CoordinationTrigger, 
        context: Dict[str, Any], 
        user_id: int
    ) -> Optional[CoordinationAction]:
        """Create coordination action based on trigger."""
        # Get user archetype for personalization
        stmt = select(UserArchetype).where(UserArchetype.user_id == user_id)
        result = await self.session.execute(stmt)
        user_archetype = result.scalar_one_or_none()
        
        archetype_name = user_archetype.dominant_archetype if user_archetype else 'balanced'
        
        # Determine appropriate role based on trigger
        role_mapping = {
            'user_confusion': LucienRole.SUPPORT,
            'narrative_transition': LucienRole.COORDINATOR,
            'vip_opportunity': LucienRole.FACILITATOR,
            'mission_introduction': LucienRole.GUIDE,
            'character_consistency_issue': LucienRole.GUARDIAN,
            'achievement_recognition': LucienRole.MESSENGER
        }
        
        role = role_mapping.get(trigger_config.trigger_type, LucienRole.GUIDE)
        
        # Generate personalized message
        message = self._generate_personalized_message(
            role, trigger_config, context, archetype_name
        )
        
        # Estimate coordination duration
        duration_estimate = self._estimate_coordination_duration(trigger_config.trigger_type, archetype_name)
        
        return CoordinationAction(
            action_type='appear',
            role=role,
            message=message,
            duration_estimate=duration_estimate,
            follow_up_actions=self._determine_follow_up_actions(trigger_config.trigger_type)
        )
    
    def _generate_personalized_message(
        self, 
        role: LucienRole, 
        trigger_config: CoordinationTrigger, 
        context: Dict[str, Any],
        archetype: str
    ) -> str:
        """Generate personalized message based on role and context."""
        base_messages = self.role_messages.get(role, {})
        coordination_style = self.archetype_coordination_styles.get(archetype, {})
        
        # Start with role-appropriate appearance
        appearance_message = base_messages.get('appearance', "Lucien aparece...")
        
        # Add context-specific content
        if trigger_config.trigger_type == 'user_confusion':
            context_message = f"Veo que has encontrado algunos desafíos. {base_messages.get('encouragement', 'Permíteme ayudarte.')}"
            
        elif trigger_config.trigger_type == 'narrative_transition':
            tier_change = context.get('tier_change', False)
            level_change = context.get('level_progression', False)
            
            if tier_change:
                context_message = f"Estás entrando en un nuevo nivel de experiencia. {base_messages.get('coordination', 'Permíteme coordinar esta transición.')}"
            elif level_change:
                context_message = f"Tu progreso te ha llevado a un nuevo nivel. {base_messages.get('transition', 'Te acompañaré en este avance.')}"
            else:
                context_message = base_messages.get('coordination', 'Hay cambios en el horizonte que requieren coordinación.')
                
        elif trigger_config.trigger_type == 'vip_opportunity':
            context_message = f"Diana ha notado tu progreso excepcional. {base_messages.get('facilitation', 'Permíteme facilitar el siguiente paso.')}"
            
        elif trigger_config.trigger_type == 'character_consistency_issue':
            context_message = f"Ha ocurrido una pequeña interrupción en la experiencia. {base_messages.get('system_message', 'Permíteme restaurar la continuidad.')}"
            
        else:
            context_message = base_messages.get('guidance', 'Permíteme ofrecerte orientación.')
        
        # Adapt message style to archetype
        if coordination_style.get('communication_style') == 'straightforward':
            # More direct communication
            full_message = f"{appearance_message}\n\n{context_message}"
        elif coordination_style.get('communication_style') == 'warm':
            # More emotional and supportive
            full_message = f"{appearance_message}\n\n*[Con una sonrisa comprensiva]* {context_message}"
        elif coordination_style.get('communication_style') == 'contemplative':
            # More thoughtful and reflective
            full_message = f"{appearance_message}\n\n*[Después de una pausa reflexiva]* {context_message}"
        else:
            # Balanced approach
            full_message = f"{appearance_message}\n\n{context_message}"
        
        return full_message
    
    def _estimate_coordination_duration(self, trigger_type: str, archetype: str) -> int:
        """Estimate how long coordination should last."""
        base_durations = {
            'user_confusion': 180,      # 3 minutes
            'narrative_transition': 120, # 2 minutes
            'vip_opportunity': 300,     # 5 minutes
            'mission_introduction': 90,  # 1.5 minutes
            'character_consistency_issue': 60,  # 1 minute
            'achievement_recognition': 45  # 45 seconds
        }
        
        base_duration = base_durations.get(trigger_type, 120)
        
        # Adjust based on archetype
        archetype_multipliers = {
            'patient': 1.5,      # Patient users need more time
            'analytical': 1.3,   # Analytical users want more explanation
            'direct': 0.7,       # Direct users want quick resolution
            'persistent': 0.8,   # Persistent users are self-sufficient
            'explorer': 0.9,     # Explorers prefer minimal guidance
            'romantic': 1.2      # Romantic users appreciate deeper interaction
        }
        
        multiplier = archetype_multipliers.get(archetype, 1.0)
        return int(base_duration * multiplier)
    
    def _determine_follow_up_actions(self, trigger_type: str) -> List[str]:
        """Determine what follow-up actions might be needed."""
        follow_up_mapping = {
            'user_confusion': ['check_understanding', 'monitor_progress'],
            'narrative_transition': ['confirm_transition', 'update_user_state'],
            'vip_opportunity': ['present_upgrade_options', 'track_decision'],
            'mission_introduction': ['provide_mission_briefing', 'track_completion'],
            'character_consistency_issue': ['restore_narrative_flow', 'monitor_consistency'],
            'achievement_recognition': ['celebrate_achievement', 'suggest_next_goals']
        }
        
        return follow_up_mapping.get(trigger_type, ['monitor_user_response'])
    
    async def _evaluate_active_coordination(
        self, 
        coordination_state: LucienCoordination, 
        context: Dict[str, Any]
    ) -> Optional[CoordinationAction]:
        """Evaluate whether active coordination should continue."""
        # Check if Lucien should step back
        current_time = datetime.utcnow()
        
        # If coordination has been active for too long, consider stepping back
        if coordination_state.activated_at:
            active_duration = (current_time - coordination_state.activated_at).total_seconds()
            max_duration = 600  # 10 minutes maximum
            
            if active_duration > max_duration:
                return CoordinationAction(
                    action_type='disappear',
                    role=LucienRole(coordination_state.current_role),
                    message="Lucien asiente con satisfacción y se retira discretamente, dejando que continúes tu viaje...",
                    duration_estimate=0
                )
        
        # Check if the issue has been resolved
        if coordination_state.coordination_mode == 'guiding':
            # If user shows signs of understanding, Lucien can step back
            if context.get('user_progress_made', False) or context.get('confusion_resolved', False):
                return CoordinationAction(
                    action_type='disappear',
                    role=LucienRole(coordination_state.current_role),
                    message="Lucien observa tu progreso con aprobación y se desvanece silenciosamente...",
                    duration_estimate=0
                )
        
        return None
    
    async def _execute_appearance_action(
        self, 
        user_id: int, 
        action: CoordinationAction, 
        coordination_state: LucienCoordination
    ) -> Dict[str, Any]:
        """Execute Lucien appearance action."""
        # Record appearance
        coordination_state.record_appearance(
            'system_triggered',
            f"Appeared as {action.role.value} for coordination"
        )
        
        # Set coordination state
        coordination_state.current_role = action.role.value
        coordination_state.coordination_mode = 'guiding'
        coordination_state.is_active = True
        
        # Set planned disappearance time
        if action.duration_estimate > 0:
            coordination_state.planned_disappearance_at = datetime.utcnow() + timedelta(seconds=action.duration_estimate)
        
        await self.session.commit()
        
        return {
            'success': True,
            'action': 'lucien_appeared',
            'role': action.role.value,
            'message': action.message,
            'estimated_duration': action.duration_estimate,
            'follow_up_actions': action.follow_up_actions
        }
    
    async def _execute_disappearance_action(
        self, 
        user_id: int, 
        action: CoordinationAction, 
        coordination_state: LucienCoordination
    ) -> Dict[str, Any]:
        """Execute Lucien disappearance action."""
        # Record disappearance with effectiveness score
        effectiveness_score = self._calculate_coordination_effectiveness(coordination_state)
        coordination_state.record_disappearance('task_completed', effectiveness_score)
        
        await self.session.commit()
        
        return {
            'success': True,
            'action': 'lucien_disappeared',
            'message': action.message,
            'effectiveness_score': effectiveness_score
        }
    
    async def _execute_message_action(
        self, 
        user_id: int, 
        action: CoordinationAction, 
        coordination_state: LucienCoordination
    ) -> Dict[str, Any]:
        """Execute Lucien message action."""
        # Update coordination state
        coordination_state.last_coordination_at = datetime.utcnow()
        await self.session.commit()
        
        return {
            'success': True,
            'action': 'lucien_message',
            'role': action.role.value,
            'message': action.message
        }
    
    async def _execute_redirect_action(
        self, 
        user_id: int, 
        action: CoordinationAction, 
        coordination_state: LucienCoordination
    ) -> Dict[str, Any]:
        """Execute Lucien redirect action."""
        return {
            'success': True,
            'action': 'lucien_redirect',
            'role': action.role.value,
            'message': action.message,
            'redirect_guidance': action.follow_up_actions
        }
    
    def _calculate_coordination_effectiveness(self, coordination_state: LucienCoordination) -> int:
        """Calculate effectiveness score for coordination session."""
        if not coordination_state.activated_at:
            return 50  # Default score
        
        # Base score
        score = 50
        
        # Duration appropriateness (not too short, not too long)
        duration = (datetime.utcnow() - coordination_state.activated_at).total_seconds()
        if 30 <= duration <= 300:  # 30 seconds to 5 minutes is good
            score += 20
        elif duration < 30:
            score += 5  # Too brief
        elif duration > 600:
            score -= 10  # Too long
        
        # Role appropriateness (would need more context to evaluate)
        score += 15  # Assume appropriate role selection
        
        # User response (would need user feedback to evaluate)
        score += 15  # Assume positive user response
        
        return max(0, min(score, 100))
    
    async def _record_coordination_event(
        self, 
        user_id: int, 
        action: CoordinationAction, 
        result: Dict[str, Any]
    ):
        """Record coordination event for analytics."""
        # This would typically record to an analytics system
        logger.info(
            f"Coordination event: User {user_id}, Action {action.action_type}, "
            f"Role {action.role.value}, Success {result.get('success', False)}"
        )
    
    def _analyze_coordination_trends(self, recent_appearances: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in coordination appearances."""
        if not recent_appearances:
            return {'trend': 'no_data'}
        
        # Analyze frequency trend
        appearance_times = [
            datetime.fromisoformat(app['appeared_at'])
            for app in recent_appearances
        ]
        appearance_times.sort()
        
        if len(appearance_times) >= 2:
            # Calculate time intervals between appearances
            intervals = [
                (appearance_times[i] - appearance_times[i-1]).total_seconds()
                for i in range(1, len(appearance_times))
            ]
            
            avg_interval = sum(intervals) / len(intervals)
            
            # Determine trend
            if len(intervals) >= 3:
                recent_avg = sum(intervals[-2:]) / 2
                early_avg = sum(intervals[:2]) / 2
                
                if recent_avg < early_avg * 0.8:
                    trend = 'increasing_frequency'
                elif recent_avg > early_avg * 1.2:
                    trend = 'decreasing_frequency'
                else:
                    trend = 'stable_frequency'
            else:
                trend = 'stable_frequency'
            
            return {
                'trend': trend,
                'average_interval_minutes': avg_interval / 60,
                'total_appearances': len(recent_appearances),
                'frequency_analysis': 'available'
            }
        
        return {
            'trend': 'insufficient_data',
            'total_appearances': len(recent_appearances)
        }
    
    def _generate_coordination_recommendations(
        self, 
        user_archetype: str, 
        optimization_settings: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for coordination optimization."""
        recommendations = []
        
        # Archetype-specific recommendations
        if user_archetype == 'explorer':
            recommendations.append("Minimize interruptions - let user explore independently")
            recommendations.append("Use subtle hints rather than direct guidance")
        elif user_archetype == 'direct':
            recommendations.append("Provide clear, actionable guidance when coordinating")
            recommendations.append("Be concise and focus on immediate solutions")
        elif user_archetype == 'romantic':
            recommendations.append("Emphasize emotional context and connection")
            recommendations.append("Use warm, supportive communication style")
        elif user_archetype == 'analytical':
            recommendations.append("Provide detailed explanations and reasoning")
            recommendations.append("Offer comprehensive context for coordination actions")
        elif user_archetype == 'persistent':
            recommendations.append("Acknowledge user's determination before offering help")
            recommendations.append("Focus on celebrating achievements and progress")
        elif user_archetype == 'patient':
            recommendations.append("Allow time for processing between guidance steps")
            recommendations.append("Use thoughtful, contemplative communication style")
        
        # Settings-based recommendations
        if optimization_settings.get('adaptation_needed', False):
            recommendations.append("Monitor coordination effectiveness and adjust approach")
        
        if optimization_settings.get('appearance_threshold', 0.5) > 0.7:
            recommendations.append("User prefers independence - coordinate only when necessary")
        elif optimization_settings.get('appearance_threshold', 0.5) < 0.4:
            recommendations.append("User appreciates guidance - be more proactive in coordination")
        
        return recommendations[:5]  # Top 5 recommendations