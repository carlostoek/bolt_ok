"""Database optimization service for performance improvements.

This service handles:
- Database connection pooling optimization
- Query performance monitoring  
- Critical query optimization
- Connection lifecycle management
- Character consistency preservation during performance optimization

Key Requirements:
- Maintain <2s response time target
- Preserve Diana personality delivery speed
- Support multi-tenant architecture
- Ensure data integrity during optimization
"""
import asyncio
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from sqlalchemy import text, func, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine.events import event

from database.models import (
    User, UserNarrativeState, Mission, UserMissionEntry, 
    UserStats, ButtonReaction, Achievement, UserAchievement
)
from database.narrative_unified import (
    NarrativeFragment, UserNarrativeState as UnifiedUserNarrativeState,
    UserDecisionLog, NarrativeCharacterValidation, UserMissionProgress
)

logger = logging.getLogger(__name__)


class DatabaseOptimizationService:
    """Service for database performance optimization and monitoring."""
    
    def __init__(self):
        self.connection_pool_stats = {}
        self.query_performance_cache = {}
        self.optimization_metrics = {
            'slow_queries': [],
            'connection_issues': [],
            'cache_hits': 0,
            'cache_misses': 0
        }
        
    async def optimize_connection_pool(self, engine_config: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize database connection pool settings for production load.
        
        Args:
            engine_config: Current engine configuration
            
        Returns:
            Optimized engine configuration
        """
        logger.info("🏗️ Optimizing database connection pool configuration")
        
        # Production-optimized pool settings
        optimized_config = {
            **engine_config,
            'poolclass': QueuePool,
            'pool_size': 20,  # Increased from default 5
            'max_overflow': 30,  # Allow burst connections  
            'pool_timeout': 30,  # Connection timeout
            'pool_recycle': 3600,  # Recycle connections every hour
            'pool_pre_ping': True,  # Verify connections before use
            'connect_args': {
                'command_timeout': 30,
                'server_settings': {
                    'application_name': 'diana_bot_optimized',
                    'tcp_keepalives_idle': '600',
                    'tcp_keepalives_interval': '30',
                    'tcp_keepalives_count': '3',
                }
            }
        }
        
        logger.info(f"✅ Connection pool optimized - pool_size: {optimized_config['pool_size']}, max_overflow: {optimized_config['max_overflow']}")
        return optimized_config
    
    async def get_optimized_user_narrative_progress(
        self, 
        session: AsyncSession, 
        user_id: int
    ) -> Dict[str, Any]:
        """Optimized query for user narrative progress (most frequent query).
        
        This query is optimized with proper indexes and joins to minimize response time
        while preserving Diana's narrative flow delivery.
        """
        start_time = time.time()
        
        try:
            # Single optimized query with proper joins and indexes
            query = text("""
                SELECT 
                    nf.id as fragment_id,
                    nf.title,
                    nf.content,
                    nf.fragment_type,
                    nf.tier_classification,
                    nf.requires_vip,
                    nf.diana_personality_weight,
                    uns.current_level,
                    uns.current_tier,
                    uns.visited_fragments,
                    uns.completed_fragments,
                    uns.unlocked_clues,
                    u.points,
                    u.level,
                    u.role,
                    u.vip_expires_at
                FROM narrative_fragments_unified nf
                LEFT JOIN user_narrative_states_unified uns ON uns.user_id = :user_id
                LEFT JOIN users u ON u.id = :user_id
                WHERE nf.is_active = true
                AND (
                    nf.requires_vip = false 
                    OR (nf.requires_vip = true AND u.vip_expires_at > NOW())
                )
                ORDER BY nf.storyline_level, nf.fragment_sequence
            """)
            
            result = await session.execute(query, {"user_id": user_id})
            rows = result.fetchall()
            
            query_time = time.time() - start_time
            
            # Log slow queries for monitoring
            if query_time > 1.0:  # Log queries over 1 second
                logger.warning(f"⚠️ Slow narrative progress query: {query_time:.2f}s for user {user_id}")
                self.optimization_metrics['slow_queries'].append({
                    'query': 'user_narrative_progress',
                    'duration': query_time,
                    'user_id': user_id,
                    'timestamp': datetime.utcnow()
                })
            
            # Convert to structured format
            progress_data = {
                'fragments': [],
                'user_state': None,
                'user_info': None,
                'query_time': query_time
            }
            
            for row in rows:
                fragment_data = {
                    'id': row.fragment_id,
                    'title': row.title,
                    'content': row.content,
                    'fragment_type': row.fragment_type,
                    'tier_classification': row.tier_classification,
                    'requires_vip': row.requires_vip,
                    'diana_personality_weight': row.diana_personality_weight
                }
                progress_data['fragments'].append(fragment_data)
                
                # Set user state and info from first row
                if progress_data['user_state'] is None and row.current_level:
                    progress_data['user_state'] = {
                        'current_level': row.current_level,
                        'current_tier': row.current_tier,
                        'visited_fragments': row.visited_fragments or [],
                        'completed_fragments': row.completed_fragments or [],
                        'unlocked_clues': row.unlocked_clues or []
                    }
                    
                if progress_data['user_info'] is None and row.points is not None:
                    progress_data['user_info'] = {
                        'points': row.points,
                        'level': row.level,
                        'role': row.role,
                        'is_vip': row.vip_expires_at and row.vip_expires_at > datetime.utcnow()
                    }
            
            logger.info(f"✅ User narrative progress query completed in {query_time:.3f}s for user {user_id}")
            return progress_data
            
        except Exception as e:
            query_time = time.time() - start_time
            logger.error(f"❌ User narrative progress query failed in {query_time:.3f}s: {e}")
            raise
    
    async def get_optimized_mission_progress_aggregation(
        self, 
        session: AsyncSession, 
        user_id: int
    ) -> Dict[str, Any]:
        """Optimized mission progress aggregation query.
        
        Aggregates mission completion data efficiently to support gamification
        without affecting Diana's response timing.
        """
        start_time = time.time()
        
        try:
            # Optimized mission progress query with proper indexing
            query = text("""
                WITH mission_stats AS (
                    SELECT 
                        m.id as mission_id,
                        m.name,
                        m.description,
                        m.reward_points,
                        m.type as mission_type,
                        m.target_value,
                        m.is_active,
                        COALESCE(ume.progress_value, 0) as progress_value,
                        COALESCE(ume.completed, false) as completed,
                        ume.completed_at
                    FROM missions m
                    LEFT JOIN user_mission_entries ume ON (
                        ume.mission_id = m.id AND ume.user_id = :user_id
                    )
                    WHERE m.is_active = true
                ),
                progress_summary AS (
                    SELECT
                        COUNT(*) as total_missions,
                        COUNT(CASE WHEN completed = true THEN 1 END) as completed_missions,
                        SUM(CASE WHEN completed = true THEN reward_points ELSE 0 END) as total_rewards_earned,
                        SUM(CASE WHEN completed = false THEN reward_points ELSE 0 END) as potential_rewards
                    FROM mission_stats
                )
                SELECT 
                    ms.*,
                    ps.total_missions,
                    ps.completed_missions, 
                    ps.total_rewards_earned,
                    ps.potential_rewards
                FROM mission_stats ms
                CROSS JOIN progress_summary ps
                ORDER BY ms.completed ASC, ms.mission_type, ms.reward_points DESC
            """)
            
            result = await session.execute(query, {"user_id": user_id})
            rows = result.fetchall()
            
            query_time = time.time() - start_time
            
            # Log slow queries
            if query_time > 0.5:  # Mission queries should be very fast
                logger.warning(f"⚠️ Slow mission progress query: {query_time:.2f}s for user {user_id}")
                self.optimization_metrics['slow_queries'].append({
                    'query': 'mission_progress_aggregation',
                    'duration': query_time,
                    'user_id': user_id,
                    'timestamp': datetime.utcnow()
                })
            
            # Structure the response
            if not rows:
                return {'missions': [], 'summary': {}, 'query_time': query_time}
            
            missions = []
            summary = {}
            
            for row in rows:
                mission_data = {
                    'id': row.mission_id,
                    'name': row.name,
                    'description': row.description,
                    'reward_points': row.reward_points,
                    'mission_type': row.mission_type,
                    'target_value': row.target_value,
                    'progress_value': row.progress_value,
                    'completed': row.completed,
                    'completed_at': row.completed_at
                }
                missions.append(mission_data)
                
                # Set summary from first row (all rows have same summary data)
                if not summary:
                    summary = {
                        'total_missions': row.total_missions,
                        'completed_missions': row.completed_missions,
                        'total_rewards_earned': row.total_rewards_earned,
                        'potential_rewards': row.potential_rewards,
                        'completion_percentage': round(
                            (row.completed_missions / row.total_missions) * 100, 1
                        ) if row.total_missions > 0 else 0
                    }
            
            logger.info(f"✅ Mission progress aggregation completed in {query_time:.3f}s for user {user_id}")
            return {
                'missions': missions,
                'summary': summary,
                'query_time': query_time
            }
            
        except Exception as e:
            query_time = time.time() - start_time
            logger.error(f"❌ Mission progress aggregation failed in {query_time:.3f}s: {e}")
            raise
    
    async def get_optimized_character_validation_check(
        self,
        session: AsyncSession,
        fragment_id: Optional[str] = None,
        user_id: Optional[int] = None,
        consistency_threshold: int = 95
    ) -> Dict[str, Any]:
        """Optimized character validation check for Diana consistency.
        
        Ensures Diana's personality consistency is maintained while optimizing
        for performance to meet <2s response requirements.
        """
        start_time = time.time()
        
        try:
            # Build dynamic query based on parameters
            conditions = ["meets_threshold = true"]
            params = {"threshold": consistency_threshold}
            
            if fragment_id:
                conditions.append("fragment_id = :fragment_id")
                params["fragment_id"] = fragment_id
                
            if user_id:
                conditions.append("user_id = :user_id")
                params["user_id"] = user_id
            
            query = text(f"""
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
                    validated_at
                FROM narrative_character_validation_unified
                WHERE {' AND '.join(conditions)}
                ORDER BY validated_at DESC, consistency_score DESC
                LIMIT 10
            """)
            
            result = await session.execute(query, params)
            rows = result.fetchall()
            
            query_time = time.time() - start_time
            
            # Character validation queries must be very fast to preserve user experience
            if query_time > 0.3:
                logger.warning(f"⚠️ Slow character validation query: {query_time:.2f}s")
                self.optimization_metrics['slow_queries'].append({
                    'query': 'character_validation_check',
                    'duration': query_time,
                    'fragment_id': fragment_id,
                    'user_id': user_id,
                    'timestamp': datetime.utcnow()
                })
            
            # Calculate aggregate metrics
            validations = []
            total_score = 0
            trait_averages = {
                'mysterious': 0,
                'seductive': 0,
                'emotional_complexity': 0,
                'intellectual_engagement': 0
            }
            
            for row in rows:
                validation_data = {
                    'id': row.id,
                    'fragment_id': row.fragment_id,
                    'user_id': row.user_id,
                    'consistency_score': row.consistency_score,
                    'trait_scores': {
                        'mysterious': row.mysterious_score,
                        'seductive': row.seductive_score,
                        'emotional_complexity': row.emotional_complexity_score,
                        'intellectual_engagement': row.intellectual_engagement_score
                    },
                    'meets_threshold': row.meets_threshold,
                    'validated_at': row.validated_at
                }
                validations.append(validation_data)
                
                total_score += row.consistency_score
                trait_averages['mysterious'] += row.mysterious_score
                trait_averages['seductive'] += row.seductive_score
                trait_averages['emotional_complexity'] += row.emotional_complexity_score
                trait_averages['intellectual_engagement'] += row.intellectual_engagement_score
            
            # Calculate averages
            count = len(validations)
            if count > 0:
                avg_consistency = round(total_score / count, 1)
                for trait in trait_averages:
                    trait_averages[trait] = round(trait_averages[trait] / count, 1)
            else:
                avg_consistency = 0
            
            result_data = {
                'validations': validations,
                'summary': {
                    'total_validations': count,
                    'average_consistency_score': avg_consistency,
                    'meets_requirement': avg_consistency >= consistency_threshold,
                    'trait_averages': trait_averages
                },
                'query_time': query_time
            }
            
            logger.info(f"✅ Character validation check completed in {query_time:.3f}s - avg score: {avg_consistency}")
            return result_data
            
        except Exception as e:
            query_time = time.time() - start_time
            logger.error(f"❌ Character validation check failed in {query_time:.3f}s: {e}")
            raise
    
    async def monitor_query_performance(self, session: AsyncSession) -> Dict[str, Any]:
        """Monitor overall database query performance and connection health."""
        start_time = time.time()
        
        try:
            # Check active connections
            connection_query = text("""
                SELECT 
                    COUNT(*) as active_connections,
                    COUNT(CASE WHEN state = 'active' THEN 1 END) as running_queries,
                    COUNT(CASE WHEN state = 'idle' THEN 1 END) as idle_connections
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """)
            
            result = await session.execute(connection_query)
            connection_stats = result.fetchone()
            
            # Check slow queries from metrics
            recent_slow_queries = [
                q for q in self.optimization_metrics['slow_queries']
                if q['timestamp'] > datetime.utcnow() - timedelta(minutes=5)
            ]
            
            monitoring_data = {
                'database_health': {
                    'active_connections': connection_stats.active_connections if connection_stats else 0,
                    'running_queries': connection_stats.running_queries if connection_stats else 0,
                    'idle_connections': connection_stats.idle_connections if connection_stats else 0
                },
                'performance_metrics': {
                    'recent_slow_queries': len(recent_slow_queries),
                    'cache_hit_rate': round(
                        (self.optimization_metrics['cache_hits'] / 
                         max(1, self.optimization_metrics['cache_hits'] + self.optimization_metrics['cache_misses'])) * 100, 1
                    ),
                    'avg_query_time': round(
                        sum(q['duration'] for q in recent_slow_queries) / max(1, len(recent_slow_queries)), 3
                    )
                },
                'query_time': time.time() - start_time
            }
            
            logger.info(f"✅ Database performance monitoring completed - {monitoring_data['database_health']['active_connections']} active connections")
            return monitoring_data
            
        except Exception as e:
            logger.error(f"❌ Database performance monitoring failed: {e}")
            raise
    
    def get_optimization_metrics(self) -> Dict[str, Any]:
        """Get current optimization metrics and statistics."""
        return {
            'metrics': self.optimization_metrics,
            'connection_pool_stats': self.connection_pool_stats,
            'query_cache_size': len(self.query_performance_cache)
        }
    
    async def clear_old_performance_data(self, days_to_keep: int = 7):
        """Clear old performance monitoring data to prevent memory bloat."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Clean slow queries
        self.optimization_metrics['slow_queries'] = [
            q for q in self.optimization_metrics['slow_queries']
            if q['timestamp'] > cutoff_date
        ]
        
        # Clear old cache entries
        self.query_performance_cache.clear()
        
        logger.info(f"🧹 Cleaned performance data older than {days_to_keep} days")


# Global database optimization service instance
database_optimization_service = DatabaseOptimizationService()