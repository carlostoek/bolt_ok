"""
Diana Service Registry - High-Performance Service Instance Management

Implements service registry pattern with singleton instances to eliminate
service instantiation overhead (40% response time improvement expected).

Key Features:
- Service singleton instances with proper lifecycle management
- Lazy loading for non-critical services
- Shared service instances across operations
- Memory-efficient service caching
- Performance monitoring and optimization
"""

import asyncio
import logging
import time
import weakref
from typing import Dict, Any, Optional, Type, TypeVar, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

# Service type variable for type hints
T = TypeVar('T')

logger = logging.getLogger(__name__)

@dataclass
class ServiceMetrics:
    """Performance metrics for service instances."""
    instantiation_count: int = 0
    total_instantiation_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_instantiation_time: float = 0.0
    last_access: datetime = field(default_factory=datetime.now)
    
    def update_instantiation(self, duration: float):
        """Update instantiation metrics."""
        self.instantiation_count += 1
        self.total_instantiation_time += duration
        self.avg_instantiation_time = self.total_instantiation_time / self.instantiation_count
        self.last_access = datetime.now()
    
    def record_cache_hit(self):
        """Record cache hit."""
        self.cache_hits += 1
        self.last_access = datetime.now()
    
    def record_cache_miss(self):
        """Record cache miss."""
        self.cache_misses += 1
        self.last_access = datetime.now()

@dataclass
class ServiceInstance:
    """Container for service instances with metadata."""
    instance: Any
    created_at: datetime
    last_accessed: datetime
    session_id: str
    access_count: int = 0
    
    def touch(self):
        """Update access timestamp."""
        self.last_accessed = datetime.now()
        self.access_count += 1

class ServiceRegistry:
    """
    High-performance service registry with singleton pattern and caching.
    
    Provides:
    - Service instance caching to eliminate instantiation overhead
    - Lazy loading for performance-critical operations
    - Memory management and cleanup
    - Performance monitoring and metrics
    """
    
    def __init__(self):
        # Service instances cache (session_id -> service_name -> ServiceInstance)
        self._service_instances: Dict[str, Dict[str, ServiceInstance]] = {}
        
        # Service factory functions
        self._service_factories: Dict[str, Callable[[AsyncSession], Any]] = {}
        
        # Performance metrics
        self._metrics: Dict[str, ServiceMetrics] = {}
        
        # Configuration
        self.cache_ttl = timedelta(minutes=30)  # Services expire after 30 minutes
        self.max_sessions = 100  # Maximum concurrent sessions
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
        
        logger.info("Diana Service Registry initialized with high-performance caching")
    
    def register_service(self, name: str, factory: Callable[[AsyncSession], Any]):
        """Register a service factory function."""
        self._service_factories[name] = factory
        self._metrics[name] = ServiceMetrics()
        logger.debug(f"Registered service factory: {name}")
    
    async def get_service(self, name: str, session: AsyncSession) -> Optional[Any]:
        """
        Get service instance with caching for optimal performance.
        
        Returns cached instance if available, otherwise creates new one.
        """
        session_id = str(id(session))
        
        # Check cache first
        if session_id in self._service_instances:
            if name in self._service_instances[session_id]:
                service_instance = self._service_instances[session_id][name]
                
                # Check if instance is still valid
                if datetime.now() - service_instance.created_at < self.cache_ttl:
                    service_instance.touch()
                    self._metrics[name].record_cache_hit()
                    return service_instance.instance
        
        # Cache miss - create new instance
        return await self._create_service_instance(name, session, session_id)
    
    async def _create_service_instance(self, name: str, session: AsyncSession, session_id: str) -> Optional[Any]:
        """Create new service instance with performance tracking."""
        if name not in self._service_factories:
            logger.error(f"Service factory not found: {name}")
            return None
        
        start_time = time.time()
        
        try:
            # Create service instance
            factory = self._service_factories[name]
            instance = factory(session)
            
            # If factory returns a coroutine, await it
            if asyncio.iscoroutine(instance):
                instance = await instance
            
            # Cache the instance
            if session_id not in self._service_instances:
                self._service_instances[session_id] = {}
            
            service_instance = ServiceInstance(
                instance=instance,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                session_id=session_id
            )
            
            self._service_instances[session_id][name] = service_instance
            
            # Update metrics
            instantiation_time = time.time() - start_time
            self._metrics[name].update_instantiation(instantiation_time)
            self._metrics[name].record_cache_miss()
            
            logger.debug(f"Created service instance: {name} in {instantiation_time:.3f}s")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create service instance {name}: {e}")
            return None
    
    def get_service_sync(self, name: str, session: AsyncSession) -> Optional[Any]:
        """
        Get service instance synchronously for cached instances only.
        Returns None if not cached (to avoid blocking).
        """
        session_id = str(id(session))
        
        if session_id in self._service_instances:
            if name in self._service_instances[session_id]:
                service_instance = self._service_instances[session_id][name]
                
                if datetime.now() - service_instance.created_at < self.cache_ttl:
                    service_instance.touch()
                    self._metrics[name].record_cache_hit()
                    return service_instance.instance
        
        return None
    
    def invalidate_session(self, session: AsyncSession):
        """Invalidate all services for a session."""
        session_id = str(id(session))
        
        if session_id in self._service_instances:
            del self._service_instances[session_id]
            logger.debug(f"Invalidated service cache for session: {session_id}")
    
    def get_metrics(self) -> Dict[str, ServiceMetrics]:
        """Get performance metrics for all services."""
        return self._metrics.copy()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_instances = sum(len(services) for services in self._service_instances.values())
        total_sessions = len(self._service_instances)
        
        cache_efficiency = {}
        for name, metrics in self._metrics.items():
            total_requests = metrics.cache_hits + metrics.cache_misses
            efficiency = (metrics.cache_hits / total_requests * 100) if total_requests > 0 else 0
            cache_efficiency[name] = efficiency
        
        return {
            "total_cached_instances": total_instances,
            "active_sessions": total_sessions,
            "cache_efficiency": cache_efficiency,
            "metrics": {name: metrics.__dict__ for name, metrics in self._metrics.items()}
        }
    
    def _start_cleanup_task(self):
        """Start background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_services())
    
    async def _cleanup_expired_services(self):
        """Background task to cleanup expired services."""
        while True:
            try:
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                await self._perform_cleanup()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in service cleanup task: {e}")
    
    async def _perform_cleanup(self):
        """Perform cleanup of expired services and sessions."""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, services in self._service_instances.items():
            expired_services = []
            
            for service_name, service_instance in services.items():
                if now - service_instance.created_at > self.cache_ttl:
                    expired_services.append(service_name)
            
            # Remove expired services
            for service_name in expired_services:
                del services[service_name]
            
            # Mark empty sessions for removal
            if not services:
                expired_sessions.append(session_id)
        
        # Remove empty sessions
        for session_id in expired_sessions:
            del self._service_instances[session_id]
        
        if expired_sessions or any(self._service_instances.values()):
            logger.debug(f"Cleanup: removed {len(expired_sessions)} expired sessions")
    
    async def shutdown(self):
        """Shutdown service registry and cleanup resources."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self._service_instances.clear()
        self._metrics.clear()
        logger.info("Diana Service Registry shutdown complete")

# Global service registry instance
_service_registry: Optional[ServiceRegistry] = None

def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    return _service_registry

async def register_diana_services(registry: ServiceRegistry):
    """Register all Diana services with the registry."""
    from services.enhanced_user_service import EnhancedUserService
    from services.diana_character_validator import DianaCharacterValidator
    from services.point_service import PointService
    
    # Register service factories
    registry.register_service("user_service", lambda session: EnhancedUserService(session))
    registry.register_service("character_validator", lambda session: DianaCharacterValidator())
    registry.register_service("point_service", lambda session: PointService(session))
    
    logger.info("Diana services registered with service registry")

# Convenience functions for service access
async def get_user_service(session: AsyncSession) -> Optional['EnhancedUserService']:
    """Get EnhancedUserService instance with caching."""
    registry = get_service_registry()
    return await registry.get_service("user_service", session)

async def get_character_validator(session: AsyncSession) -> Optional['DianaCharacterValidator']:
    """Get DianaCharacterValidator instance with caching."""
    registry = get_service_registry()
    return await registry.get_service("character_validator", session)

async def get_point_service(session: AsyncSession) -> Optional['PointService']:
    """Get PointService instance with caching."""
    registry = get_service_registry()
    return await registry.get_service("point_service", session)

def get_user_service_sync(session: AsyncSession) -> Optional['EnhancedUserService']:
    """Get cached EnhancedUserService instance synchronously."""
    registry = get_service_registry()
    return registry.get_service_sync("user_service", session)

def get_character_validator_sync(session: AsyncSession) -> Optional['DianaCharacterValidator']:
    """Get cached DianaCharacterValidator instance synchronously."""
    registry = get_service_registry()
    return registry.get_service_sync("character_validator", session)

def get_point_service_sync(session: AsyncSession) -> Optional['PointService']:
    """Get cached PointService instance synchronously."""
    registry = get_service_registry()
    return registry.get_service_sync("point_service", session)

@asynccontextmanager
async def service_context(session: AsyncSession):
    """Context manager for service lifecycle management."""
    registry = get_service_registry()
    try:
        yield registry
    finally:
        # Optional: cleanup session services on context exit
        pass

# Initialize services when module is imported
async def initialize_diana_service_registry():
    """Initialize the Diana service registry with all services."""
    registry = get_service_registry()
    await register_diana_services(registry)
    return registry

# Performance monitoring utilities
def get_service_performance_report() -> Dict[str, Any]:
    """Get comprehensive performance report for all services."""
    registry = get_service_registry()
    cache_stats = registry.get_cache_stats()
    
    return {
        "timestamp": datetime.now().isoformat(),
        "registry_stats": cache_stats,
        "performance_summary": {
            "total_instantiation_overhead_saved": sum(
                metrics.cache_hits * metrics.avg_instantiation_time
                for metrics in registry.get_metrics().values()
            ),
            "cache_hit_rate_average": sum(
                stats for stats in cache_stats["cache_efficiency"].values()
            ) / len(cache_stats["cache_efficiency"]) if cache_stats["cache_efficiency"] else 0
        }
    }

logger.info("Diana Service Registry module loaded")