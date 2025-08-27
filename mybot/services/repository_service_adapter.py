"""Service adapter to integrate repository pattern with existing services."""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.implementations.user_repository import SqlUserRepository
from repositories.implementations.point_repository import SqlPointRepository  
from repositories.implementations.mission_repository import SqlMissionRepository
from repositories.implementations.narrative_repository import SqlNarrativeRepository
from repositories.caching import create_memory_cache, create_redis_cache, CacheLayer
from repositories.query_optimization import query_optimizer, index_recommender, query_profiler

logger = logging.getLogger(__name__)


class RepositoryServiceAdapter:
    """Adapter to integrate repository pattern with existing service architecture."""
    
    def __init__(self, session: AsyncSession, cache_config: Optional[Dict[str, Any]] = None):
        self.session = session
        self._cache_layer = self._create_cache_layer(cache_config or {})
        self._repositories = {}
        self._initialize_repositories()
    
    def _create_cache_layer(self, config: Dict[str, Any]) -> Optional[CacheLayer]:
        """Create cache layer based on configuration."""
        cache_type = config.get('type', 'memory')
        
        try:
            if cache_type == 'memory':
                max_size = config.get('max_size', 10000)
                default_ttl = config.get('default_ttl', 300)
                return create_memory_cache(max_size=max_size, default_ttl=default_ttl)
            
            elif cache_type == 'redis':
                redis_url = config.get('redis_url', 'redis://localhost:6379')
                key_prefix = config.get('key_prefix', 'bot_cache')
                default_ttl = config.get('default_ttl', 300)
                return create_redis_cache(redis_url=redis_url, key_prefix=key_prefix, default_ttl=default_ttl)
            
            elif cache_type == 'disabled':
                return None
            
            else:
                logger.warning(f"Unknown cache type: {cache_type}, falling back to memory cache")
                return create_memory_cache()
        
        except Exception as e:
            logger.error(f"Failed to create cache layer: {e}")
            logger.info("Falling back to memory cache")
            return create_memory_cache()
    
    def _initialize_repositories(self):
        """Initialize all repositories with shared cache layer."""
        # User repository
        user_repo = SqlUserRepository(self.session)
        if self._cache_layer:
            user_repo._cache_layer = self._cache_layer
        self._repositories['user'] = user_repo
        
        # Point repository  
        point_repo = SqlPointRepository(self.session)
        if self._cache_layer:
            point_repo._cache_layer = self._cache_layer
        self._repositories['point'] = point_repo
        
        # Mission repository
        mission_repo = SqlMissionRepository(self.session)
        if self._cache_layer:
            mission_repo._cache_layer = self._cache_layer
        self._repositories['mission'] = mission_repo
        
        # Narrative repository
        narrative_repo = SqlNarrativeRepository(self.session)
        if self._cache_layer:
            narrative_repo._cache_layer = self._cache_layer
        self._repositories['narrative'] = narrative_repo
        
        logger.info(f"Initialized {len(self._repositories)} repositories with caching: {self._cache_layer is not None}")
    
    def get_user_repository(self) -> SqlUserRepository:
        """Get user repository instance."""
        return self._repositories['user']
    
    def get_point_repository(self) -> SqlPointRepository:
        """Get point repository instance."""
        return self._repositories['point']
    
    def get_mission_repository(self) -> SqlMissionRepository:
        """Get mission repository instance."""
        return self._repositories['mission']
    
    def get_narrative_repository(self) -> SqlNarrativeRepository:
        """Get narrative repository instance."""
        return self._repositories['narrative']
    
    def get_all_repositories(self) -> Dict[str, Any]:
        """Get all repositories."""
        return self._repositories.copy()
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get health status of all repositories and cache."""
        health = {
            'repositories': {},
            'cache': None,
            'query_optimizer': {},
            'overall_status': 'unknown'
        }
        
        # Check repository health
        repository_statuses = []
        for name, repo in self._repositories.items():
            try:
                if hasattr(repo, 'cache_health_check'):
                    repo_health = await repo.cache_health_check()
                    health['repositories'][name] = repo_health
                    repository_statuses.append(repo_health.get('status', 'unknown'))
                else:
                    health['repositories'][name] = {'status': 'no_health_check', 'message': 'Health check not implemented'}
                    repository_statuses.append('no_health_check')
            except Exception as e:
                health['repositories'][name] = {'status': 'error', 'message': f'Health check failed: {e}'}
                repository_statuses.append('error')
        
        # Check cache health
        if self._cache_layer:
            try:
                health['cache'] = self._cache_layer.get_stats()
                health['cache']['status'] = 'healthy'
            except Exception as e:
                health['cache'] = {'status': 'error', 'message': f'Cache error: {e}'}
        else:
            health['cache'] = {'status': 'disabled', 'message': 'No cache layer configured'}
        
        # Check query optimizer health
        health['query_optimizer'] = {
            'cache_stats': query_optimizer.get_cache_stats(),
            'profiler_stats': query_profiler.get_performance_report().get('overview', {}),
            'status': 'healthy'
        }
        
        # Determine overall status
        if all(status in ['healthy', 'no_health_check'] for status in repository_statuses):
            if health['cache']['status'] in ['healthy', 'disabled']:
                health['overall_status'] = 'healthy'
            else:
                health['overall_status'] = 'degraded'
        else:
            health['overall_status'] = 'unhealthy'
        
        return health
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        metrics = {
            'cache': {},
            'query_optimizer': {},
            'repositories': {},
            'recommendations': {}
        }
        
        # Cache metrics
        if self._cache_layer:
            metrics['cache'] = self._cache_layer.get_stats()
        
        # Query optimizer metrics
        metrics['query_optimizer'] = {
            'cache_stats': query_optimizer.get_cache_stats(),
            'performance_report': query_profiler.get_performance_report(),
            'optimization_suggestions': query_profiler.get_optimization_suggestions()
        }
        
        # Repository-specific metrics
        for name, repo in self._repositories.items():
            try:
                repo_metrics = {}
                
                # Basic repository stats
                if hasattr(repo, 'count'):
                    repo_metrics['total_entities'] = await repo.count()
                
                # Cache-specific stats for this repository
                if hasattr(repo, '_cache_layer') and repo._cache_layer:
                    repo_metrics['cache_enabled'] = True
                else:
                    repo_metrics['cache_enabled'] = False
                
                metrics['repositories'][name] = repo_metrics
            
            except Exception as e:
                metrics['repositories'][name] = {'error': str(e)}
        
        # Index recommendations
        recommendations = index_recommender.get_index_recommendations()
        metrics['recommendations'] = {
            'index_recommendations': recommendations,
            'total_recommendations': len(recommendations),
            'high_priority_count': len([r for r in recommendations if r.get('priority', 0) > 50])
        }
        
        return metrics
    
    async def optimize_system(self, auto_create_indexes: bool = False) -> Dict[str, Any]:
        """Optimize the repository system based on usage patterns."""
        optimization_results = {
            'cache_optimizations': {},
            'query_optimizations': {},
            'index_recommendations': {},
            'performance_improvements': {}
        }
        
        # Cache optimization
        if self._cache_layer:
            # Clear expired entries
            # This would be implementation-specific
            cache_stats = self._cache_layer.get_stats()
            optimization_results['cache_optimizations'] = {
                'cleared_expired': 0,  # Would implement actual clearing
                'current_utilization': cache_stats.get('utilization', 0),
                'recommended_action': 'monitor' if cache_stats.get('hit_rate', 0) > 70 else 'tune'
            }
        
        # Query optimization
        performance_report = query_profiler.get_performance_report()
        slow_queries_count = len(performance_report.get('recent_slow_queries', []))
        
        optimization_results['query_optimizations'] = {
            'slow_queries_identified': slow_queries_count,
            'optimization_suggestions': query_profiler.get_optimization_suggestions(),
            'cache_efficiency': query_optimizer.get_cache_stats()
        }
        
        # Index recommendations
        recommendations = index_recommender.get_index_recommendations()
        high_priority_recs = [r for r in recommendations if r.get('priority', 0) > 50]
        
        optimization_results['index_recommendations'] = {
            'total_recommendations': len(recommendations),
            'high_priority_recommendations': len(high_priority_recs),
            'recommendations': high_priority_recs[:5],  # Top 5
            'auto_create_indexes': auto_create_indexes
        }
        
        # Create indexes if requested (would need careful implementation in production)
        if auto_create_indexes and high_priority_recs:
            logger.warning("Auto-index creation requested but not implemented for safety")
            optimization_results['index_recommendations']['auto_creation_status'] = 'skipped_for_safety'
        
        # Performance improvement estimates
        cache_hit_rate = self._cache_layer.get_stats().get('hit_rate', 0) if self._cache_layer else 0
        optimization_results['performance_improvements'] = {
            'estimated_query_speedup': f"{min(cache_hit_rate * 2, 50)}%",
            'cache_efficiency': 'good' if cache_hit_rate > 70 else 'needs_improvement',
            'recommended_actions': [
                'Monitor slow queries',
                'Consider index optimization',
                'Tune cache settings' if cache_hit_rate < 70 else 'Cache performing well'
            ]
        }
        
        logger.info("System optimization analysis completed")
        return optimization_results
    
    async def clear_caches(self, pattern: Optional[str] = None) -> Dict[str, Any]:
        """Clear caches across the system."""
        if not self._cache_layer:
            return {'status': 'no_cache', 'message': 'No cache layer configured'}
        
        try:
            if pattern:
                cleared_count = await self._cache_layer.invalidate_pattern(pattern)
                message = f"Cleared {cleared_count} cache entries matching pattern: {pattern}"
            else:
                await self._cache_layer.backend.clear()
                message = "Cleared all cache entries"
                cleared_count = "all"
            
            # Also clear query optimizer cache
            query_optimizer.clear_cache()
            
            return {
                'status': 'success',
                'message': message,
                'cleared_count': cleared_count
            }
        
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return {
                'status': 'error',
                'message': f"Failed to clear cache: {e}"
            }
    
    async def warm_up_caches(self) -> Dict[str, Any]:
        """Warm up caches with commonly accessed data."""
        if not self._cache_layer:
            return {'status': 'no_cache', 'message': 'No cache layer configured'}
        
        warmup_results = {}
        
        try:
            # Warm up each repository
            for name, repo in self._repositories.items():
                if hasattr(repo, 'cache_warm_up'):
                    await repo.cache_warm_up()
                    warmup_results[name] = 'completed'
                else:
                    warmup_results[name] = 'not_supported'
            
            return {
                'status': 'success',
                'message': 'Cache warmup completed',
                'repositories': warmup_results
            }
        
        except Exception as e:
            logger.error(f"Cache warmup failed: {e}")
            return {
                'status': 'error',
                'message': f"Cache warmup failed: {e}",
                'repositories': warmup_results
            }


class LegacyServiceMigrationHelper:
    """Helper to gradually migrate existing services to use repository pattern."""
    
    def __init__(self, session: AsyncSession, repository_adapter: RepositoryServiceAdapter):
        self.session = session
        self.repository_adapter = repository_adapter
        self.migration_log = []
    
    async def migrate_user_operations(self, legacy_user_service):
        """Migrate user operations from legacy service to repository pattern."""
        user_repo = self.repository_adapter.get_user_repository()
        
        # Create wrapper methods that delegate to repository
        original_get_user = getattr(legacy_user_service, 'get_user', None)
        if original_get_user:
            async def new_get_user(user_id):
                self.migration_log.append(f"Migrated get_user call for user {user_id}")
                return await user_repo.get_by_id(user_id)
            
            legacy_user_service.get_user = new_get_user
        
        original_create_user = getattr(legacy_user_service, 'create_user', None)
        if original_create_user:
            async def new_create_user(user_id, **kwargs):
                self.migration_log.append(f"Migrated create_user call for user {user_id}")
                user_data = {'id': user_id, **kwargs}
                return await user_repo.create(user_data)
            
            legacy_user_service.create_user = new_create_user
        
        logger.info(f"Migrated user operations for {legacy_user_service.__class__.__name__}")
    
    async def migrate_point_operations(self, legacy_point_service):
        """Migrate point operations from legacy service to repository pattern."""
        point_repo = self.repository_adapter.get_point_repository()
        
        # Similar pattern for point operations
        if hasattr(legacy_point_service, 'add_points'):
            original_add_points = legacy_point_service.add_points
            
            async def new_add_points(user_id, amount, **kwargs):
                self.migration_log.append(f"Migrated add_points call for user {user_id}, amount {amount}")
                source = kwargs.get('source', 'legacy_migration')
                description = kwargs.get('description', '')
                return await point_repo.add_points(user_id, amount, source, description)
            
            legacy_point_service.add_points = new_add_points
        
        logger.info(f"Migrated point operations for {legacy_point_service.__class__.__name__}")
    
    def get_migration_log(self) -> List[str]:
        """Get migration activity log."""
        return self.migration_log.copy()
    
    def clear_migration_log(self):
        """Clear migration activity log."""
        self.migration_log.clear()


# Factory function for easy integration
def create_repository_adapter(session: AsyncSession, 
                            cache_config: Optional[Dict[str, Any]] = None) -> RepositoryServiceAdapter:
    """Create repository service adapter with default configuration."""
    default_cache_config = {
        'type': 'memory',
        'max_size': 10000,
        'default_ttl': 300
    }
    
    if cache_config:
        default_cache_config.update(cache_config)
    
    return RepositoryServiceAdapter(session, default_cache_config)


# Global instance for application-wide use
_global_repository_adapter: Optional[RepositoryServiceAdapter] = None


def get_repository_adapter() -> Optional[RepositoryServiceAdapter]:
    """Get the global repository adapter instance."""
    return _global_repository_adapter


def set_repository_adapter(adapter: RepositoryServiceAdapter):
    """Set the global repository adapter instance."""
    global _global_repository_adapter
    _global_repository_adapter = adapter


# Example integration with existing service
class EnhancedUserService:
    """Example of existing service enhanced with repository pattern."""
    
    def __init__(self, session: AsyncSession, repository_adapter: Optional[RepositoryServiceAdapter] = None):
        self.session = session
        
        # Use repository if available, fallback to direct database access
        if repository_adapter:
            self.user_repository = repository_adapter.get_user_repository()
            self.point_repository = repository_adapter.get_point_repository()
            self.use_repository = True
        else:
            self.user_repository = None
            self.point_repository = None
            self.use_repository = False
    
    async def get_user(self, user_id: int):
        """Get user using repository pattern if available."""
        if self.use_repository:
            return await self.user_repository.get_by_id(user_id)
        else:
            # Fallback to legacy database access
            return await self.session.get(User, user_id)
    
    async def get_user_with_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user with comprehensive statistics using repository pattern."""
        if self.use_repository:
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return {}
            
            # Use repository for enhanced metrics
            engagement_metrics = await self.user_repository.get_user_engagement_metrics(user_id)
            balance = await self.point_repository.get_user_balance(user_id)
            rank = await self.user_repository.get_user_rank_by_points(user_id)
            
            return {
                'user': user,
                'balance': balance,
                'rank': rank,
                'engagement': engagement_metrics
            }
        else:
            # Fallback to basic data
            user = await self.session.get(User, user_id)
            return {'user': user} if user else {}