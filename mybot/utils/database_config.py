"""
Database configuration utilities for narrative system performance optimization.
Task 33: Update system configuration for new features.

This module provides enhanced database configuration for:
- Connection pooling optimization
- Analytics query performance
- Caching strategies
- Connection management
"""

from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import QueuePool, StaticPool
from utils.config import Config
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Enhanced database configuration for narrative system."""

    @staticmethod
    def get_engine_config() -> dict:
        """Get optimized engine configuration for the narrative system."""
        return {
            "pool_size": Config.DB_ANALYTICS_POOL_SIZE,
            "max_overflow": Config.DB_ANALYTICS_MAX_OVERFLOW,
            "pool_timeout": Config.DB_QUERY_TIMEOUT,
            "pool_recycle": Config.DB_CONNECTION_RECYCLE,
            "pool_pre_ping": True,  # Validate connections before use
            "pool_reset_on_return": "commit",  # Reset connections on return
            "echo": False,  # Set to True for SQL debugging
            "echo_pool": False,  # Set to True for pool debugging
        }

    @staticmethod
    def create_optimized_engine(database_url: str) -> AsyncEngine:
        """Create an optimized async engine for the narrative system."""
        engine_config = DatabaseConfig.get_engine_config()

        # Use StaticPool for SQLite, QueuePool for other databases
        if "sqlite" in database_url.lower():
            engine_config["poolclass"] = StaticPool
            engine_config["connect_args"] = {
                "check_same_thread": False,
                "timeout": 30,
                "isolation_level": None,
            }
        else:
            engine_config["poolclass"] = QueuePool

        logger.info(f"Creating optimized database engine with config: {engine_config}")

        return create_async_engine(
            database_url,
            **engine_config
        )

    @staticmethod
    def get_analytics_query_hints() -> dict:
        """Get query hints for analytics performance optimization."""
        return {
            "batch_size": Config.ANALYTICS_BATCH_SIZE,
            "prefetch_related": True,
            "use_indexes": True,
            "query_timeout": Config.DB_QUERY_TIMEOUT,
        }

    @staticmethod
    def get_connection_pool_status(engine: AsyncEngine) -> dict:
        """Get current connection pool status for monitoring."""
        pool = engine.pool
        return {
            "pool_size": pool.size() if hasattr(pool, 'size') else 'N/A',
            "checked_in": pool.checkedin() if hasattr(pool, 'checkedin') else 'N/A',
            "checked_out": pool.checkedout() if hasattr(pool, 'checkedout') else 'N/A',
            "overflow": pool.overflow() if hasattr(pool, 'overflow') else 'N/A',
            "invalid": pool.invalid() if hasattr(pool, 'invalid') else 'N/A',
        }

    @staticmethod
    def validate_database_config() -> dict:
        """Validate current database configuration."""
        validation_results = {}

        try:
            # Check pool sizes are reasonable
            pool_size = Config.DB_ANALYTICS_POOL_SIZE
            validation_results["pool_size_valid"] = 5 <= pool_size <= 50

            max_overflow = Config.DB_ANALYTICS_MAX_OVERFLOW
            validation_results["overflow_valid"] = 0 <= max_overflow <= 20

            # Check timeout settings
            query_timeout = Config.DB_QUERY_TIMEOUT
            validation_results["timeout_valid"] = 10 <= query_timeout <= 300

            connection_recycle = Config.DB_CONNECTION_RECYCLE
            validation_results["recycle_valid"] = 300 <= connection_recycle <= 7200

            # Check analytics settings
            batch_size = Config.ANALYTICS_BATCH_SIZE
            validation_results["batch_size_valid"] = 10 <= batch_size <= 1000

            validation_results["overall_valid"] = all([
                validation_results["pool_size_valid"],
                validation_results["overflow_valid"],
                validation_results["timeout_valid"],
                validation_results["recycle_valid"],
                validation_results["batch_size_valid"],
            ])

        except Exception as e:
            validation_results["error"] = str(e)
            validation_results["overall_valid"] = False

        return validation_results


class CacheConfig:
    """Cache configuration for narrative system performance."""

    @staticmethod
    def get_cache_config() -> dict:
        """Get cache configuration for the narrative system."""
        return {
            "enabled": Config.CACHE_ENABLED,
            "type": Config.CACHE_TYPE,
            "max_size": Config.CACHE_MAX_SIZE,
            "ttl_seconds": Config.NARRATIVE_CACHE_TTL,
            "redis_url": Config.REDIS_URL if Config.CACHE_TYPE == "redis" else None,
        }

    @staticmethod
    def get_fragment_cache_config() -> dict:
        """Get specific cache configuration for story fragments."""
        return {
            "max_size": Config.FRAGMENT_CACHE_SIZE,
            "ttl_seconds": Config.NARRATIVE_CACHE_TTL,
            "prefetch_enabled": True,
            "invalidation_strategy": "auto",
        }

    @staticmethod
    def get_lore_cache_config() -> dict:
        """Get specific cache configuration for lore pieces."""
        return {
            "ttl_seconds": Config.LORE_CACHE_DURATION,
            "invalidation_on_update": True,
            "preload_user_lore": True,
        }

    @staticmethod
    def validate_cache_config() -> dict:
        """Validate cache configuration."""
        validation_results = {}

        try:
            # Check cache is enabled and type is valid
            validation_results["cache_enabled"] = Config.CACHE_ENABLED
            validation_results["cache_type_valid"] = Config.CACHE_TYPE in ["memory", "redis"]

            # Check cache sizes are reasonable
            max_size = Config.CACHE_MAX_SIZE
            validation_results["max_size_valid"] = 100 <= max_size <= 100000

            fragment_size = Config.FRAGMENT_CACHE_SIZE
            validation_results["fragment_size_valid"] = 100 <= fragment_size <= 10000

            # Check TTL settings
            cache_ttl = Config.NARRATIVE_CACHE_TTL
            validation_results["cache_ttl_valid"] = 300 <= cache_ttl <= 86400

            lore_ttl = Config.LORE_CACHE_DURATION
            validation_results["lore_ttl_valid"] = 300 <= lore_ttl <= 7200

            validation_results["overall_valid"] = all([
                validation_results["cache_type_valid"],
                validation_results["max_size_valid"],
                validation_results["fragment_size_valid"],
                validation_results["cache_ttl_valid"],
                validation_results["lore_ttl_valid"],
            ])

        except Exception as e:
            validation_results["error"] = str(e)
            validation_results["overall_valid"] = False

        return validation_results


class SecurityConfig:
    """Security configuration for narrative system."""

    @staticmethod
    def get_security_config() -> dict:
        """Get security configuration for the narrative system."""
        return {
            "admin_session_timeout": Config.ADMIN_SESSION_TIMEOUT,
            "content_validation_enabled": Config.CONTENT_VALIDATION_ENABLED,
            "max_content_length": Config.MAX_CONTENT_LENGTH,
            "max_file_size_mb": Config.MAX_FILE_SIZE_MB,
            "allowed_file_types": Config.ALLOWED_FILE_TYPES,
            "rate_limit_admin": Config.RATE_LIMIT_ADMIN_OPERATIONS,
            "rate_limit_user": Config.RATE_LIMIT_USER_INTERACTIONS,
        }

    @staticmethod
    def get_rate_limit_config() -> dict:
        """Get rate limiting configuration."""
        return {
            "admin_operations_per_hour": Config.RATE_LIMIT_ADMIN_OPERATIONS,
            "user_interactions_per_hour": Config.RATE_LIMIT_USER_INTERACTIONS,
            "ai_requests_per_minute": Config.AI_RATE_LIMIT_PER_MINUTE,
            "enabled": True,
        }

    @staticmethod
    def validate_security_config() -> dict:
        """Validate security configuration."""
        validation_results = {}

        try:
            # Check session timeout is reasonable
            timeout = Config.ADMIN_SESSION_TIMEOUT
            validation_results["session_timeout_valid"] = 300 <= timeout <= 28800  # 5 min to 8 hours

            # Check content limits
            content_length = Config.MAX_CONTENT_LENGTH
            validation_results["content_length_valid"] = 100 <= content_length <= 50000

            file_size = Config.MAX_FILE_SIZE_MB
            validation_results["file_size_valid"] = 1 <= file_size <= 100

            # Check rate limits
            admin_rate = Config.RATE_LIMIT_ADMIN_OPERATIONS
            validation_results["admin_rate_valid"] = 10 <= admin_rate <= 1000

            user_rate = Config.RATE_LIMIT_USER_INTERACTIONS
            validation_results["user_rate_valid"] = 100 <= user_rate <= 10000

            # Check file types
            file_types = Config.ALLOWED_FILE_TYPES
            safe_types = {"jpg", "jpeg", "png", "gif", "mp4", "mp3", "txt", "pdf", "webp"}
            validation_results["file_types_safe"] = all(ft.lower() in safe_types for ft in file_types)

            validation_results["overall_valid"] = all([
                validation_results["session_timeout_valid"],
                validation_results["content_length_valid"],
                validation_results["file_size_valid"],
                validation_results["admin_rate_valid"],
                validation_results["user_rate_valid"],
                validation_results["file_types_safe"],
            ])

        except Exception as e:
            validation_results["error"] = str(e)
            validation_results["overall_valid"] = False

        return validation_results


def validate_all_configs() -> dict:
    """Validate all narrative system configurations."""
    return {
        "database": DatabaseConfig.validate_database_config(),
        "cache": CacheConfig.validate_cache_config(),
        "security": SecurityConfig.validate_security_config(),
        "timestamp": "2025-09-16",
    }