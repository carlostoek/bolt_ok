"""
Performance monitoring and optimization configuration for the narrative system.
Task 33: Update system configuration for new features.

This module provides configuration for:
- Performance monitoring
- Metrics collection
- Query optimization
- Resource management
"""

import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from utils.config import Config

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Data class for performance metrics."""
    query_time: float
    memory_usage: Optional[float] = None
    cache_hits: int = 0
    cache_misses: int = 0
    database_connections: int = 0
    active_users: int = 0


class PerformanceConfig:
    """Performance configuration and monitoring utilities."""

    @staticmethod
    def get_monitoring_config() -> dict:
        """Get performance monitoring configuration."""
        return {
            "enabled": Config.MONITORING_ENABLED,
            "performance_logging": Config.PERFORMANCE_LOGGING_ENABLED,
            "error_notifications": Config.ERROR_NOTIFICATION_ENABLED,
            "metrics_interval": Config.METRICS_COLLECTION_INTERVAL,
            "analytics_processing_interval": Config.ANALYTICS_PROCESSING_INTERVAL,
        }

    @staticmethod
    def get_optimization_config() -> dict:
        """Get performance optimization configuration."""
        return {
            "cache_enabled": Config.CACHE_ENABLED,
            "cache_ttl": Config.NARRATIVE_CACHE_TTL,
            "batch_size": Config.ANALYTICS_BATCH_SIZE,
            "connection_pooling": {
                "pool_size": Config.DB_ANALYTICS_POOL_SIZE,
                "max_overflow": Config.DB_ANALYTICS_MAX_OVERFLOW,
                "timeout": Config.DB_QUERY_TIMEOUT,
            },
            "coordinator": {
                "enabled": Config.COORDINATOR_ENABLED,
                "sync_interval": Config.COORDINATOR_SYNC_INTERVAL,
                "batch_operations": Config.COORDINATOR_BATCH_OPERATIONS,
            },
        }

    @staticmethod
    def get_query_optimization_hints() -> dict:
        """Get query optimization hints for the narrative system."""
        return {
            "use_indexes": True,
            "batch_operations": True,
            "prefetch_related": True,
            "limit_large_queries": Config.ANALYTICS_BATCH_SIZE,
            "timeout_seconds": Config.DB_QUERY_TIMEOUT,
            "cache_frequent_queries": Config.CACHE_ENABLED,
        }

    @staticmethod
    def should_log_performance(query_time: float) -> bool:
        """Determine if a query should be logged for performance monitoring."""
        if not Config.PERFORMANCE_LOGGING_ENABLED:
            return False

        # Log slow queries (over 1 second)
        slow_query_threshold = 1.0
        return query_time > slow_query_threshold

    @staticmethod
    def get_cache_strategy() -> dict:
        """Get caching strategy configuration."""
        return {
            "fragments": {
                "enabled": Config.CACHE_ENABLED,
                "ttl": Config.NARRATIVE_CACHE_TTL,
                "max_size": Config.FRAGMENT_CACHE_SIZE,
                "strategy": "lru",  # Least Recently Used
            },
            "lore": {
                "enabled": Config.LORE_AUTO_UNLOCK_ENABLED,
                "ttl": Config.LORE_CACHE_DURATION,
                "preload": True,
            },
            "analytics": {
                "enabled": Config.ANALYTICS_AGGREGATION_ENABLED,
                "batch_processing": True,
                "real_time": Config.ANALYTICS_REAL_TIME_ENABLED,
            },
            "user_progress": {
                "auto_save_interval": Config.PROGRESS_AUTO_SAVE_INTERVAL,
                "validation_enabled": Config.PROGRESS_VALIDATION_ENABLED,
            },
        }


class ResourceLimits:
    """Resource limits and thresholds configuration."""

    @staticmethod
    def get_resource_limits() -> dict:
        """Get resource limits for the narrative system."""
        return {
            "memory": {
                "cache_max_size": Config.CACHE_MAX_SIZE,
                "fragment_cache_size": Config.FRAGMENT_CACHE_SIZE,
            },
            "database": {
                "max_connections": Config.DB_ANALYTICS_POOL_SIZE + Config.DB_ANALYTICS_MAX_OVERFLOW,
                "query_timeout": Config.DB_QUERY_TIMEOUT,
                "batch_size": Config.ANALYTICS_BATCH_SIZE,
            },
            "files": {
                "max_file_size_mb": Config.MAX_FILE_SIZE_MB,
                "allowed_types": Config.ALLOWED_FILE_TYPES,
                "max_content_length": Config.MAX_CONTENT_LENGTH,
            },
            "rate_limits": {
                "admin_operations_per_hour": Config.RATE_LIMIT_ADMIN_OPERATIONS,
                "user_interactions_per_hour": Config.RATE_LIMIT_USER_INTERACTIONS,
                "ai_requests_per_minute": Config.AI_RATE_LIMIT_PER_MINUTE,
            },
        }

    @staticmethod
    def check_resource_usage(metrics: PerformanceMetrics) -> dict:
        """Check if resource usage is within acceptable limits."""
        limits = ResourceLimits.get_resource_limits()
        warnings = []
        errors = []

        # Check query time
        if metrics.query_time > Config.DB_QUERY_TIMEOUT:
            errors.append(f"Query time {metrics.query_time}s exceeds timeout {Config.DB_QUERY_TIMEOUT}s")
        elif metrics.query_time > Config.DB_QUERY_TIMEOUT * 0.8:
            warnings.append(f"Query time {metrics.query_time}s approaching timeout")

        # Check cache hit ratio
        total_cache_requests = metrics.cache_hits + metrics.cache_misses
        if total_cache_requests > 0:
            hit_ratio = metrics.cache_hits / total_cache_requests
            if hit_ratio < 0.5:
                warnings.append(f"Low cache hit ratio: {hit_ratio:.2%}")

        # Check database connections
        max_connections = limits["database"]["max_connections"]
        if metrics.database_connections > max_connections * 0.9:
            warnings.append(f"High database connection usage: {metrics.database_connections}/{max_connections}")

        return {
            "status": "error" if errors else ("warning" if warnings else "ok"),
            "warnings": warnings,
            "errors": errors,
            "metrics": metrics,
        }


class PerformanceProfiler:
    """Performance profiling utilities for the narrative system."""

    def __init__(self):
        self.start_time = None
        self.metrics = {}

    def start_profiling(self, operation_name: str):
        """Start profiling an operation."""
        self.start_time = time.time()
        self.operation_name = operation_name

        if Config.PERFORMANCE_LOGGING_ENABLED:
            logger.debug(f"Starting profiling: {operation_name}")

    def end_profiling(self) -> float:
        """End profiling and return elapsed time."""
        if self.start_time is None:
            return 0.0

        elapsed_time = time.time() - self.start_time

        if Config.PERFORMANCE_LOGGING_ENABLED and PerformanceConfig.should_log_performance(elapsed_time):
            logger.warning(f"Slow operation detected: {self.operation_name} took {elapsed_time:.3f}s")

        return elapsed_time

    def add_metric(self, key: str, value: Any):
        """Add a custom metric."""
        self.metrics[key] = value

    def get_metrics(self) -> dict:
        """Get all collected metrics."""
        return self.metrics.copy()


def create_performance_context():
    """Create a performance monitoring context."""
    return PerformanceProfiler()


def validate_performance_config() -> dict:
    """Validate performance configuration settings."""
    validation_results = {}

    try:
        # Check monitoring settings
        validation_results["monitoring_enabled"] = Config.MONITORING_ENABLED
        validation_results["performance_logging"] = Config.PERFORMANCE_LOGGING_ENABLED

        # Check intervals are reasonable
        metrics_interval = Config.METRICS_COLLECTION_INTERVAL
        validation_results["metrics_interval_valid"] = 60 <= metrics_interval <= 3600

        analytics_interval = Config.ANALYTICS_PROCESSING_INTERVAL
        validation_results["analytics_interval_valid"] = 60 <= analytics_interval <= 1800

        # Check batch sizes
        batch_size = Config.ANALYTICS_BATCH_SIZE
        validation_results["batch_size_valid"] = 10 <= batch_size <= 1000

        # Check auto-save interval
        auto_save = Config.PROGRESS_AUTO_SAVE_INTERVAL
        validation_results["auto_save_valid"] = 30 <= auto_save <= 600

        # Check coordinator settings
        if Config.COORDINATOR_ENABLED:
            sync_interval = Config.COORDINATOR_SYNC_INTERVAL
            validation_results["coordinator_sync_valid"] = 30 <= sync_interval <= 300
        else:
            validation_results["coordinator_sync_valid"] = True

        validation_results["overall_valid"] = all([
            validation_results["metrics_interval_valid"],
            validation_results["analytics_interval_valid"],
            validation_results["batch_size_valid"],
            validation_results["auto_save_valid"],
            validation_results["coordinator_sync_valid"],
        ])

    except Exception as e:
        validation_results["error"] = str(e)
        validation_results["overall_valid"] = False

    return validation_results