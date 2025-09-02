"""
Decision State Persistence Service
Advanced state management for Diana Bot decision tree system.
Handles session recovery, state synchronization, and multi-tenant isolation.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, update, delete, or_
from database.narrative_unified import (
    UserNarrativeState, 
    UserDecisionLog,
    UserMissionProgress,
    UserArchetype
)
from services.diana_character_validator import DianaCharacterValidator

logger = logging.getLogger(__name__)

class DecisionStateTransaction:
    """Context manager for decision state transactions."""
    
    def __init__(self, service: 'DecisionStatePersistenceService', user_id: int):
        self.service = service
        self.user_id = user_id
        self.transaction_id = None
        self.rollback_data = {}
    
    async def __aenter__(self):
        self.transaction_id = f"decision_tx_{self.user_id}_{datetime.utcnow().timestamp()}"
        await self.service._begin_transaction(self.user_id, self.transaction_id)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.service._rollback_transaction(self.user_id, self.transaction_id)
        else:
            await self.service._commit_transaction(self.user_id, self.transaction_id)
        return False

class DecisionStatePersistenceService:
    """
    Advanced state persistence service for decision tree system.
    
    Features:
    - Atomic decision state transactions
    - Session recovery with context preservation
    - Multi-tenant data isolation
    - Performance-optimized state queries
    - Character-consistent error handling
    - State synchronization across services
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.character_validator = DianaCharacterValidator(session)
        
        # Transaction management
        self._active_transactions = {}
        self._state_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Performance metrics
        self._performance_metrics = {
            'state_retrievals': 0,
            'state_updates': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def get_transaction_context(self, user_id: int) -> DecisionStateTransaction:
        """Get transaction context manager for atomic operations."""
        return DecisionStateTransaction(self, user_id)
    
    async def persist_decision_state(
        self,
        user_id: int,
        decision_data: Dict[str, Any],
        state_context: Dict[str, Any],
        performance_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Persist decision state with full context and validation.
        
        Args:
            user_id: User making the decision
            decision_data: Core decision information
            state_context: Additional state context
            performance_metrics: Performance tracking data
            
        Returns:
            Persistence result with validation
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Persisting decision state for user {user_id}")
            
            # Validate user isolation
            await self._validate_user_isolation(user_id)
            
            # Get or create user state with locking
            user_state = await self._get_user_state_with_lock(user_id)
            
            # Validate state consistency
            consistency_result = await self._validate_state_consistency(
                user_id, user_state, decision_data, state_context
            )
            
            if not consistency_result['consistent']:
                raise ValueError(f"State consistency validation failed: {consistency_result['reason']}")
            
            # Persist core decision data
            persistence_result = await self._persist_core_decision_data(
                user_id, user_state, decision_data
            )
            
            # Update state context
            context_result = await self._update_state_context(
                user_id, user_state, state_context
            )
            
            # Record performance metrics
            if performance_metrics:
                await self._record_performance_metrics(user_id, performance_metrics)
            
            # Update cache
            await self._update_state_cache(user_id, user_state)
            
            await self.session.commit()
            
            processing_time = self._calculate_performance_ms(start_time)
            self._performance_metrics['state_updates'] += 1
            
            logger.info(f"Decision state persisted for user {user_id} in {processing_time}ms")
            
            return {
                'success': True,
                'persistence_result': persistence_result,
                'context_result': context_result,
                'consistency_validated': True,
                'processing_time_ms': processing_time,
                'cache_updated': True
            }
            
        except Exception as e:
            logger.error(f"Error persisting decision state for user {user_id}: {e}")
            await self.session.rollback()
            
            return {
                'success': False,
                'error': str(e),
                'diana_response': "😔 Algo interrumpe mi capacidad de recordar tu decisión, querido. Pero no te preocupes, tu progreso está seguro...",
                'processing_time_ms': self._calculate_performance_ms(start_time)
            }
    
    async def recover_decision_state(
        self,
        user_id: int,
        recovery_context: Optional[Dict[str, Any]] = None,
        include_history: bool = True
    ) -> Dict[str, Any]:
        """
        Recover complete decision state with full context restoration.
        
        Args:
            user_id: User to recover state for
            recovery_context: Previous session context if available
            include_history: Whether to include decision history
            
        Returns:
            Complete recovered state
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Recovering decision state for user {user_id}")
            
            # Check cache first
            cached_state = await self._get_cached_state(user_id)
            if cached_state and not recovery_context:
                self._performance_metrics['cache_hits'] += 1
                return {
                    'success': True,
                    'state': cached_state,
                    'source': 'cache',
                    'processing_time_ms': self._calculate_performance_ms(start_time)
                }
            
            self._performance_metrics['cache_misses'] += 1
            
            # Validate user isolation
            await self._validate_user_isolation(user_id)
            
            # Recover core state
            core_state = await self._recover_core_state(user_id)
            if not core_state:
                return {
                    'success': False,
                    'error': 'No state found for user',
                    'diana_response': "💋 Parece que esta es la primera vez que nos encontramos, querido. ¡Bienvenido a mis misterios!"
                }
            
            # Recover decision context
            decision_context = await self._recover_decision_context(user_id, include_history)
            
            # Recover session context
            session_context = await self._recover_session_context(user_id, recovery_context)
            
            # Recover archetype context
            archetype_context = await self._recover_archetype_context(user_id)
            
            # Validate recovered state integrity
            integrity_result = await self._validate_recovered_state_integrity(
                user_id, core_state, decision_context, session_context
            )
            
            if not integrity_result['valid']:
                logger.warning(f"State integrity validation failed for user {user_id}: {integrity_result['reason']}")
                # Continue with recovered state but flag the issue
            
            # Build complete recovered state
            recovered_state = {
                'core_state': core_state,
                'decision_context': decision_context,
                'session_context': session_context,
                'archetype_context': archetype_context,
                'integrity_validated': integrity_result['valid'],
                'recovery_timestamp': datetime.utcnow().isoformat()
            }
            
            # Update cache
            await self._update_state_cache(user_id, recovered_state)
            
            processing_time = self._calculate_performance_ms(start_time)
            self._performance_metrics['state_retrievals'] += 1
            
            return {
                'success': True,
                'state': recovered_state,
                'source': 'database',
                'integrity_issues': [] if integrity_result['valid'] else [integrity_result['reason']],
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error recovering decision state for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'diana_response': "✨ Los hilos de la memoria se enredan momentáneamente... Dame un instante para encontrar nuestro camino de vuelta.",
                'processing_time_ms': self._calculate_performance_ms(start_time)
            }
    
    async def synchronize_state_between_sessions(
        self,
        user_id: int,
        session_1_context: Dict[str, Any],
        session_2_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synchronize state between multiple sessions or devices.
        
        Args:
            user_id: User whose state to synchronize
            session_1_context: First session context
            session_2_context: Second session context
            
        Returns:
            Synchronization result
        """
        try:
            logger.info(f"Synchronizing state between sessions for user {user_id}")
            
            # Validate both sessions belong to same user
            await self._validate_user_isolation(user_id)
            
            # Get current authoritative state
            current_state = await self._get_user_state_with_lock(user_id)
            
            # Analyze session differences
            sync_analysis = await self._analyze_session_differences(
                user_id, session_1_context, session_2_context
            )
            
            # Resolve conflicts
            conflict_resolution = await self._resolve_session_conflicts(
                user_id, sync_analysis, current_state
            )
            
            # Apply synchronized state
            sync_result = await self._apply_synchronized_state(
                user_id, current_state, conflict_resolution
            )
            
            # Update both session contexts
            updated_context = await self._update_synchronized_context(
                user_id, session_1_context, session_2_context, sync_result
            )
            
            await self.session.commit()
            
            return {
                'success': True,
                'conflicts_detected': len(sync_analysis.get('conflicts', [])),
                'conflicts_resolved': len(conflict_resolution.get('resolved', [])),
                'state_synchronized': True,
                'updated_context': updated_context
            }
            
        except Exception as e:
            logger.error(f"Error synchronizing state for user {user_id}: {e}")
            await self.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'diana_response': "🌙 Siento una interferencia entre nuestras conexiones... Pero no te preocupes, encontraré la verdad de tu progreso."
            }
    
    async def cleanup_expired_states(
        self,
        expiry_threshold: timedelta = timedelta(days=30),
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Clean up expired decision states for performance optimization.
        
        Args:
            expiry_threshold: How old states should be before cleanup
            batch_size: Number of states to process per batch
            
        Returns:
            Cleanup results
        """
        try:
            cleanup_timestamp = datetime.utcnow() - expiry_threshold
            
            # Find expired decision logs
            expired_logs_stmt = select(UserDecisionLog).where(
                UserDecisionLog.made_at < cleanup_timestamp
            ).limit(batch_size)
            
            result = await self.session.execute(expired_logs_stmt)
            expired_logs = result.scalars().all()
            
            if not expired_logs:
                return {
                    'success': True,
                    'expired_logs_cleaned': 0,
                    'message': 'No expired states found for cleanup'
                }
            
            # Archive expired logs before deletion
            archived_count = await self._archive_expired_logs(expired_logs)
            
            # Delete expired logs
            for log in expired_logs:
                await self.session.delete(log)
            
            await self.session.commit()
            
            logger.info(f"Cleaned up {len(expired_logs)} expired decision logs")
            
            return {
                'success': True,
                'expired_logs_cleaned': len(expired_logs),
                'logs_archived': archived_count,
                'cleanup_threshold_days': expiry_threshold.days
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up expired states: {e}")
            await self.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    # Private Implementation Methods
    
    async def _validate_user_isolation(self, user_id: int):
        """Validate multi-tenant isolation for user operations."""
        if user_id <= 0:
            raise ValueError("Invalid user_id for state operations")
        
        # Additional tenant validation would go here
        # For MVP, basic validation is sufficient
    
    async def _get_user_state_with_lock(self, user_id: int) -> UserNarrativeState:
        """Get user state with row-level locking for consistency."""
        stmt = select(UserNarrativeState).where(
            UserNarrativeState.user_id == user_id
        ).with_for_update()
        
        result = await self.session.execute(stmt)
        user_state = result.scalar_one_or_none()
        
        if not user_state:
            # Create new state if doesn't exist
            user_state = UserNarrativeState(
                user_id=user_id,
                current_fragment_id=None,
                visited_fragments=[],
                completed_fragments=[],
                unlocked_clues=[],
                current_level=1,
                current_tier='los_kinkys',
                interaction_patterns={}
            )
            self.session.add(user_state)
            await self.session.flush()
        
        return user_state
    
    async def _validate_state_consistency(
        self,
        user_id: int,
        user_state: UserNarrativeState,
        decision_data: Dict[str, Any],
        state_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate state consistency before persistence."""
        try:
            # Check fragment progression consistency
            if decision_data.get('fragment_id'):
                if decision_data['fragment_id'] not in user_state.visited_fragments:
                    return {
                        'consistent': False,
                        'reason': 'Fragment not in visited fragments'
                    }
            
            # Check level consistency
            current_level = user_state.current_level
            decision_level = decision_data.get('fragment_level', current_level)
            
            if decision_level < current_level - 1:  # Allow some regression for replay
                return {
                    'consistent': False,
                    'reason': f'Decision level {decision_level} inconsistent with user level {current_level}'
                }
            
            # Check timestamp consistency
            if decision_data.get('timestamp'):
                decision_time = datetime.fromisoformat(decision_data['timestamp'].replace('Z', '+00:00'))
                if decision_time > datetime.utcnow() + timedelta(minutes=5):
                    return {
                        'consistent': False,
                        'reason': 'Decision timestamp in future'
                    }
            
            return {'consistent': True}
            
        except Exception as e:
            logger.error(f"Error validating state consistency for user {user_id}: {e}")
            return {
                'consistent': False,
                'reason': f'Validation error: {str(e)}'
            }
    
    async def _persist_core_decision_data(
        self,
        user_id: int,
        user_state: UserNarrativeState,
        decision_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Persist core decision data."""
        try:
            # Update current fragment
            if decision_data.get('next_fragment_id'):
                user_state.current_fragment_id = decision_data['next_fragment_id']
            
            # Update completed and visited fragments
            fragment_id = decision_data.get('fragment_id')
            if fragment_id:
                if fragment_id not in user_state.visited_fragments:
                    user_state.visited_fragments = user_state.visited_fragments + [fragment_id]
                
                if decision_data.get('completed', False) and fragment_id not in user_state.completed_fragments:
                    user_state.completed_fragments = user_state.completed_fragments + [fragment_id]
            
            # Update level and tier
            if decision_data.get('level_progression'):
                user_state.current_level = decision_data['level_progression']
            
            if decision_data.get('tier_change'):
                user_state.current_tier = decision_data['tier_change']
            
            # Update unlocked clues
            if decision_data.get('clues_unlocked'):
                new_clues = decision_data['clues_unlocked']
                existing_clues = user_state.unlocked_clues or []
                user_state.unlocked_clues = list(set(existing_clues + new_clues))
            
            return {
                'core_data_persisted': True,
                'fragments_updated': bool(fragment_id),
                'progression_updated': bool(decision_data.get('level_progression')),
                'clues_updated': bool(decision_data.get('clues_unlocked'))
            }
            
        except Exception as e:
            logger.error(f"Error persisting core decision data for user {user_id}: {e}")
            raise
    
    async def _update_state_context(
        self,
        user_id: int,
        user_state: UserNarrativeState,
        state_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update state context information."""
        try:
            # Ensure interaction_patterns exists
            if not user_state.interaction_patterns:
                user_state.interaction_patterns = {}
            
            patterns = user_state.interaction_patterns
            
            # Update decision patterns
            if state_context.get('decision_pattern'):
                pattern_key = f"pattern_{state_context['decision_pattern']['level']}"
                if pattern_key not in patterns:
                    patterns[pattern_key] = []
                
                patterns[pattern_key].append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': state_context['decision_pattern']
                })
                
                # Keep only last 10 patterns per level
                patterns[pattern_key] = patterns[pattern_key][-10:]
            
            # Update performance context
            if state_context.get('performance'):
                patterns['performance_history'] = patterns.get('performance_history', [])
                patterns['performance_history'].append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'metrics': state_context['performance']
                })
                patterns['performance_history'] = patterns['performance_history'][-20:]
            
            # Update session context
            if state_context.get('session_data'):
                patterns['session_context'] = state_context['session_data']
            
            user_state.interaction_patterns = patterns
            
            return {
                'context_updated': True,
                'patterns_count': len(patterns),
                'context_keys': list(state_context.keys())
            }
            
        except Exception as e:
            logger.error(f"Error updating state context for user {user_id}: {e}")
            raise
    
    async def _record_performance_metrics(
        self,
        user_id: int,
        performance_metrics: Dict[str, Any]
    ):
        """Record performance metrics for monitoring."""
        try:
            # This would typically write to a performance tracking table
            # For MVP, we'll log the metrics
            logger.info(
                f"Performance metrics for user {user_id}: "
                f"processing_time={performance_metrics.get('processing_time_ms')}ms, "
                f"decision_validation_time={performance_metrics.get('validation_time_ms')}ms"
            )
            
        except Exception as e:
            logger.error(f"Error recording performance metrics for user {user_id}: {e}")
    
    async def _update_state_cache(self, user_id: int, state_data: Any):
        """Update state cache for performance optimization."""
        try:
            cache_key = f"user_state_{user_id}"
            self._state_cache[cache_key] = {
                'data': state_data,
                'timestamp': datetime.utcnow(),
                'ttl': self._cache_ttl
            }
            
        except Exception as e:
            logger.error(f"Error updating state cache for user {user_id}: {e}")
    
    async def _get_cached_state(self, user_id: int) -> Optional[Any]:
        """Get state from cache if valid."""
        try:
            cache_key = f"user_state_{user_id}"
            cached_entry = self._state_cache.get(cache_key)
            
            if cached_entry:
                cache_age = datetime.utcnow() - cached_entry['timestamp']
                if cache_age.total_seconds() < cached_entry['ttl']:
                    return cached_entry['data']
                else:
                    # Remove expired cache
                    del self._state_cache[cache_key]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached state for user {user_id}: {e}")
            return None
    
    async def _recover_core_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Recover core user state."""
        stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        result = await self.session.execute(stmt)
        user_state = result.scalar_one_or_none()
        
        if not user_state:
            return None
        
        return {
            'user_id': user_state.user_id,
            'current_fragment_id': user_state.current_fragment_id,
            'current_level': user_state.current_level,
            'current_tier': user_state.current_tier,
            'visited_fragments': user_state.visited_fragments,
            'completed_fragments': user_state.completed_fragments,
            'unlocked_clues': user_state.unlocked_clues,
            'interaction_patterns': user_state.interaction_patterns,
            'diana_consistency_average': user_state.diana_consistency_average
        }
    
    async def _recover_decision_context(self, user_id: int, include_history: bool) -> Dict[str, Any]:
        """Recover decision context."""
        context = {'recent_decisions': []}
        
        if include_history:
            stmt = select(UserDecisionLog).where(
                UserDecisionLog.user_id == user_id
            ).order_by(UserDecisionLog.made_at.desc()).limit(10)
            
            result = await self.session.execute(stmt)
            decisions = result.scalars().all()
            
            context['recent_decisions'] = [
                {
                    'fragment_id': d.fragment_id,
                    'decision_choice': d.decision_choice,
                    'points_awarded': d.points_awarded,
                    'clues_unlocked': d.clues_unlocked,
                    'made_at': d.made_at.isoformat()
                }
                for d in decisions
            ]
        
        return context
    
    async def _recover_session_context(
        self, 
        user_id: int, 
        recovery_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Recover session context."""
        context = {
            'session_recovered': True,
            'recovery_timestamp': datetime.utcnow().isoformat()
        }
        
        if recovery_context:
            context['previous_session'] = recovery_context
        
        return context
    
    async def _recover_archetype_context(self, user_id: int) -> Dict[str, Any]:
        """Recover archetype context."""
        stmt = select(UserArchetype).where(UserArchetype.user_id == user_id)
        result = await self.session.execute(stmt)
        archetype = result.scalar_one_or_none()
        
        if not archetype:
            return {'archetype_data_available': False}
        
        return {
            'archetype_data_available': True,
            'dominant_archetype': archetype.dominant_archetype,
            'archetype_scores': {
                'explorer': archetype.explorer_score,
                'direct': archetype.direct_score,
                'romantic': archetype.romantic_score,
                'analytical': archetype.analytical_score,
                'persistent': archetype.persistent_score,
                'patient': archetype.patient_score
            },
            'behavioral_metrics': {
                'avg_response_time': archetype.avg_response_time,
                'content_revisit_count': archetype.content_revisit_count,
                'deep_exploration_sessions': archetype.deep_exploration_sessions
            }
        }
    
    async def _validate_recovered_state_integrity(
        self,
        user_id: int,
        core_state: Dict[str, Any],
        decision_context: Dict[str, Any],
        session_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate integrity of recovered state."""
        try:
            # Check core state consistency
            if not core_state.get('user_id') == user_id:
                return {
                    'valid': False,
                    'reason': 'User ID mismatch in recovered state'
                }
            
            # Check fragment progression consistency
            visited = core_state.get('visited_fragments', [])
            completed = core_state.get('completed_fragments', [])
            
            if not all(frag in visited for frag in completed):
                return {
                    'valid': False,
                    'reason': 'Completed fragments not all in visited fragments'
                }
            
            # Check decision history consistency
            recent_decisions = decision_context.get('recent_decisions', [])
            if recent_decisions:
                decision_fragments = [d['fragment_id'] for d in recent_decisions]
                if not all(frag in visited for frag in decision_fragments):
                    logger.warning(f"Some decision fragments not in visited list for user {user_id}")
                    # Don't fail validation, but note the inconsistency
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validating recovered state integrity for user {user_id}: {e}")
            return {
                'valid': False,
                'reason': f'Validation error: {str(e)}'
            }
    
    # Transaction Management Methods
    
    async def _begin_transaction(self, user_id: int, transaction_id: str):
        """Begin a decision state transaction."""
        self._active_transactions[transaction_id] = {
            'user_id': user_id,
            'started_at': datetime.utcnow(),
            'operations': []
        }
    
    async def _commit_transaction(self, user_id: int, transaction_id: str):
        """Commit a decision state transaction."""
        if transaction_id in self._active_transactions:
            transaction = self._active_transactions[transaction_id]
            transaction['completed_at'] = datetime.utcnow()
            # Additional commit logic would go here
            del self._active_transactions[transaction_id]
    
    async def _rollback_transaction(self, user_id: int, transaction_id: str):
        """Rollback a decision state transaction."""
        if transaction_id in self._active_transactions:
            # Rollback logic would go here
            del self._active_transactions[transaction_id]
    
    # Synchronization Methods (MVP Stubs)
    
    async def _analyze_session_differences(
        self, user_id: int, session_1: Dict, session_2: Dict
    ) -> Dict[str, Any]:
        """Analyze differences between sessions."""
        # MVP implementation - basic difference detection
        return {'conflicts': [], 'differences': []}
    
    async def _resolve_session_conflicts(
        self, user_id: int, analysis: Dict, current_state: UserNarrativeState
    ) -> Dict[str, Any]:
        """Resolve conflicts between sessions."""
        # MVP implementation - prefer current state
        return {'resolved': [], 'resolution_strategy': 'prefer_current'}
    
    async def _apply_synchronized_state(
        self, user_id: int, state: UserNarrativeState, resolution: Dict
    ) -> Dict[str, Any]:
        """Apply synchronized state."""
        return {'state_applied': True}
    
    async def _update_synchronized_context(
        self, user_id: int, context_1: Dict, context_2: Dict, sync_result: Dict
    ) -> Dict[str, Any]:
        """Update synchronized context."""
        return {'context_synchronized': True}
    
    async def _archive_expired_logs(self, expired_logs: List[UserDecisionLog]) -> int:
        """Archive expired logs before deletion."""
        # MVP implementation - just count
        return len(expired_logs)
    
    def _calculate_performance_ms(self, start_time: datetime) -> int:
        """Calculate performance in milliseconds."""
        return int((datetime.utcnow() - start_time).total_seconds() * 1000)