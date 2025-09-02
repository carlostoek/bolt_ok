"""Query optimization utilities for performance-critical database operations.

This module provides pre-compiled and optimized queries for the most frequent
database operations, ensuring <2s response time while maintaining Diana's
character consistency delivery.
"""
from sqlalchemy import text
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class OptimizedQueries:
    """Pre-compiled optimized queries for performance-critical operations."""
    
    # User narrative progress - The most frequent query
    USER_NARRATIVE_PROGRESS = text("""
        SELECT 
            nf.id as fragment_id,
            nf.title,
            nf.content,
            nf.fragment_type,
            nf.tier_classification,
            nf.requires_vip,
            nf.diana_personality_weight,
            nf.choices,
            nf.triggers,
            nf.required_clues,
            uns.current_level,
            uns.current_tier,
            uns.visited_fragments,
            uns.completed_fragments,
            uns.unlocked_clues,
            u.points,
            u.level,
            u.role,
            u.vip_expires_at,
            us.character_consistency_score
        FROM narrative_fragments_unified nf
        LEFT JOIN user_narrative_states_unified uns ON uns.user_id = :user_id
        LEFT JOIN users u ON u.id = :user_id
        LEFT JOIN user_sessions us ON us.user_id = :user_id
        WHERE nf.is_active = true
        AND nf.storyline_level <= COALESCE(uns.current_level, 1) + 1
        AND (
            nf.requires_vip = false 
            OR (nf.requires_vip = true AND u.vip_expires_at > NOW())
        )
        ORDER BY nf.storyline_level, nf.fragment_sequence
        LIMIT 50
    """)
    
    # Mission progress aggregation - Critical for gamification
    MISSION_PROGRESS_AGGREGATION = text("""
        SELECT 
            m.id as mission_id,
            m.name,
            m.description,
            m.reward_points,
            m.type as mission_type,
            m.target_value,
            m.is_active,
            m.unlocks_lore_piece_code,
            COALESCE(ume.progress_value, 0) as progress_value,
            COALESCE(ume.completed, false) as completed,
            ume.completed_at,
            -- Aggregate stats
            (
                SELECT COUNT(*) 
                FROM missions m2 
                WHERE m2.is_active = true
            ) as total_active_missions,
            (
                SELECT COUNT(*) 
                FROM user_mission_entries ume2 
                JOIN missions m2 ON m2.id = ume2.mission_id
                WHERE ume2.user_id = :user_id AND ume2.completed = true AND m2.is_active = true
            ) as total_completed_missions
        FROM missions m
        LEFT JOIN user_mission_entries ume ON (
            ume.mission_id = m.id AND ume.user_id = :user_id
        )
        WHERE m.is_active = true
        ORDER BY 
            ume.completed ASC,
            m.type,
            m.reward_points DESC
    """)
    
    # Character validation check - Critical for Diana consistency  
    CHARACTER_VALIDATION_CHECK = text("""
        SELECT 
            id,
            fragment_id,
            user_id,
            consistency_score,
            mysterious_score,
            seductive_score,
            emotional_complexity_score,
            intellectual_engagement_score,
            meets_threshold,
            violations_detected,
            recommendations,
            validated_at
        FROM narrative_character_validation_unified
        WHERE (:fragment_id IS NULL OR fragment_id = :fragment_id)
        AND (:user_id IS NULL OR user_id = :user_id)
        AND consistency_score >= :min_score
        ORDER BY validated_at DESC, consistency_score DESC
        LIMIT :limit_count
    """)
    
    # User session state - For Diana menu system
    USER_SESSION_STATE = text("""
        SELECT 
            us.user_id,
            us.session_state,
            us.menu_position,
            us.preferences,
            us.last_interaction,
            us.character_consistency_score,
            u.role,
            u.vip_expires_at,
            u.points,
            u.level,
            uns.current_level as narrative_level,
            uns.current_tier as narrative_tier
        FROM user_sessions us
        JOIN users u ON u.id = us.user_id
        LEFT JOIN user_narrative_states_unified uns ON uns.user_id = us.user_id
        WHERE us.user_id = :user_id
    """)
    
    # User achievements and badges - For gamification integration
    USER_ACHIEVEMENTS_BADGES = text("""
        SELECT 
            'achievement' as reward_type,
            a.id,
            a.name,
            a.condition_type,
            a.condition_value,
            a.reward_text,
            ua.unlocked_at,
            NULL as icon,
            NULL as emoji
        FROM user_achievements ua
        JOIN achievements a ON a.id = ua.achievement_id
        WHERE ua.user_id = :user_id
        
        UNION ALL
        
        SELECT 
            'badge' as reward_type,
            CAST(b.id AS TEXT),
            b.name,
            b.condition_type,
            b.condition_value,
            b.description as reward_text,
            ub.awarded_at as unlocked_at,
            b.icon,
            b.emoji
        FROM user_badges ub
        JOIN badges b ON b.id = ub.badge_id
        WHERE ub.user_id = :user_id
        
        ORDER BY unlocked_at DESC
    """)
    
    # User decision history - For duplicate prevention
    USER_DECISION_HISTORY = text("""
        SELECT 
            udl.fragment_id,
            udl.decision_choice,
            udl.points_awarded,
            udl.clues_unlocked,
            udl.made_at,
            nf.title as fragment_title,
            nf.fragment_type
        FROM user_decision_log_unified udl
        JOIN narrative_fragments_unified nf ON nf.id = udl.fragment_id
        WHERE udl.user_id = :user_id
        AND (:fragment_id IS NULL OR udl.fragment_id = :fragment_id)
        ORDER BY udl.made_at DESC
        LIMIT :limit_count
    """)
    
    # Lucien coordination state - For character coordination
    LUCIEN_COORDINATION_STATE = text("""
        SELECT 
            lc.user_id,
            lc.is_active,
            lc.coordination_mode,
            lc.current_role,
            lc.trigger_conditions,
            lc.appearance_context,
            lc.user_emotional_state,
            lc.narrative_phase,
            lc.diana_availability,
            lc.coordination_effectiveness,
            lc.activated_at,
            lc.last_coordination_at
        FROM lucien_coordination_unified lc
        WHERE lc.user_id = :user_id
        AND (:is_active IS NULL OR lc.is_active = :is_active)
    """)
    
    # User archetype information - For personality customization
    USER_ARCHETYPE_INFO = text("""
        SELECT 
            user_id,
            explorer_score,
            direct_score,
            romantic_score,
            analytical_score,
            persistent_score,
            patient_score,
            dominant_archetype,
            avg_response_time,
            content_revisit_count,
            deep_exploration_sessions,
            question_engagement_rate,
            emotional_vocabulary_usage,
            updated_at
        FROM user_archetypes_unified
        WHERE user_id = :user_id
    """)
    
    # Database health check - For monitoring
    DATABASE_HEALTH_CHECK = text("""
        SELECT 
            (
                SELECT COUNT(*) 
                FROM pg_stat_activity 
                WHERE datname = current_database()
            ) as total_connections,
            (
                SELECT COUNT(*) 
                FROM pg_stat_activity 
                WHERE datname = current_database() AND state = 'active'
            ) as active_connections,
            (
                SELECT COUNT(*) 
                FROM pg_stat_activity 
                WHERE datname = current_database() AND state = 'idle'
            ) as idle_connections,
            (
                SELECT COALESCE(SUM(n_tup_ins + n_tup_upd + n_tup_del), 0)
                FROM pg_stat_user_tables 
                WHERE schemaname = 'public'
            ) as total_operations,
            NOW() as check_time
    """)


class QueryOptimizer:
    """Query optimization utilities and helpers."""
    
    @staticmethod
    def build_dynamic_conditions(
        base_conditions: List[str],
        params: Dict[str, Any],
        optional_filters: Dict[str, Any]
    ) -> tuple[List[str], Dict[str, Any]]:
        """Build dynamic query conditions based on optional filters.
        
        Args:
            base_conditions: Base WHERE conditions
            params: Base query parameters
            optional_filters: Optional filter parameters
            
        Returns:
            Tuple of (conditions, parameters)
        """
        conditions = base_conditions.copy()
        final_params = params.copy()
        
        for key, value in optional_filters.items():
            if value is not None:
                conditions.append(f"{key} = :{key}")
                final_params[key] = value
        
        return conditions, final_params
    
    @staticmethod
    def optimize_limit_offset(limit: Optional[int], offset: Optional[int]) -> Dict[str, int]:
        """Optimize LIMIT and OFFSET values for performance.
        
        Args:
            limit: Requested limit
            offset: Requested offset
            
        Returns:
            Optimized limit and offset values
        """
        # Cap limits to prevent performance issues
        max_limit = 1000
        max_offset = 10000
        
        final_limit = min(limit or 50, max_limit)
        final_offset = min(offset or 0, max_offset)
        
        if final_offset > max_offset:
            logger.warning(f"⚠️ Large offset detected: {offset}, capped to {max_offset}")
        
        return {'limit': final_limit, 'offset': final_offset}
    
    @staticmethod
    def get_cache_key(query_name: str, params: Dict[str, Any]) -> str:
        """Generate cache key for query results.
        
        Args:
            query_name: Name of the query
            params: Query parameters
            
        Returns:
            Cache key string
        """
        # Sort params for consistent cache keys
        sorted_params = sorted(params.items())
        param_str = "_".join(f"{k}:{v}" for k, v in sorted_params)
        return f"query:{query_name}:{param_str}"
    
    @staticmethod
    def is_cache_eligible(query_name: str, params: Dict[str, Any]) -> bool:
        """Determine if query results should be cached.
        
        Args:
            query_name: Name of the query
            params: Query parameters
            
        Returns:
            True if eligible for caching
        """
        # Cache eligibility rules
        cache_eligible_queries = {
            'user_narrative_progress': True,
            'mission_progress_aggregation': True,
            'character_validation_check': True,
            'user_achievements_badges': True,
            'user_archetype_info': True
        }
        
        # Don't cache real-time queries
        no_cache_queries = {
            'database_health_check',
            'user_session_state',
            'lucien_coordination_state'
        }
        
        if query_name in no_cache_queries:
            return False
            
        return cache_eligible_queries.get(query_name, False)


# Export optimized queries and utilities
optimized_queries = OptimizedQueries()
query_optimizer = QueryOptimizer()