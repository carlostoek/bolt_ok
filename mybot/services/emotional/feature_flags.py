"""
Feature Flag System for Emotional Evaluation System
Enables gradual rollout and instant rollback capabilities
"""
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib

from database.models import ConfigEntry
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

logger = logging.getLogger(__name__)


@dataclass
class FeatureFlagConfig:
    """Configuration for a feature flag"""
    name: str
    enabled: bool
    rollout_percentage: int  # 0-100
    user_whitelist: list = None
    user_blacklist: list = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    dependencies: list = None


class EmotionalFeatureFlags:
    """
    Feature flag system for emotional evaluation features.
    
    Supports:
    - Global enable/disable
    - Gradual percentage rollouts
    - User whitelisting/blacklisting  
    - Time-based activation
    - Feature dependencies
    - Instant rollback capabilities
    """
    
    # Core emotional system flags
    EMOTIONAL_SYSTEM_ENABLED = "emotional_system_enabled"
    EMOTIONAL_ANALYSIS_ENABLED = "emotional_analysis_enabled"
    ARCHETYPE_SYSTEM_ENABLED = "archetype_system_enabled"
    NARRATIVE_ADAPTATION_ENABLED = "narrative_adaptation_enabled"
    
    # Feature-specific flags
    EMOTIONAL_REACTIONS_ENABLED = "emotional_reactions_enabled"
    EMOTIONAL_NARRATIVE_ENABLED = "emotional_narrative_enabled"
    EMOTIONAL_ENGAGEMENT_ENABLED = "emotional_engagement_enabled"
    EMOTIONAL_DAILY_ENABLED = "emotional_daily_enabled"
    
    # Advanced features
    DEEP_PERSONALIZATION_ENABLED = "deep_personalization_enabled"
    EMOTIONAL_MEMORY_ENABLED = "emotional_memory_enabled"
    ADAPTIVE_RESPONSES_ENABLED = "adaptive_responses_enabled"
    
    _cache: Dict[str, Any] = {}
    _cache_expiry: Dict[str, datetime] = {}
    _cache_ttl = timedelta(minutes=5)  # Cache for 5 minutes
    
    @classmethod
    async def is_enabled(cls, flag_name: str, user_id: Optional[int] = None, session: Optional[AsyncSession] = None) -> bool:
        """
        Check if a feature flag is enabled for a user.
        
        Args:
            flag_name: Name of the feature flag
            user_id: Optional user ID for user-specific checks
            session: Database session (if not provided, will use cached values)
            
        Returns:
            True if feature is enabled for the user
        """
        try:
            # Check cache first
            if cls._is_cache_valid(flag_name):
                config = cls._cache[flag_name]
            else:
                # Load from database
                config = await cls._load_flag_config(flag_name, session)
                cls._cache_flag(flag_name, config)
            
            # Check if globally disabled
            if not config.enabled:
                return False
            
            # Check time-based activation
            if not cls._is_time_valid(config):
                return False
            
            # Check dependencies
            if not await cls._check_dependencies(config.dependencies, user_id, session):
                return False
            
            # Check user-specific rules
            if user_id:
                return await cls._is_user_enabled(config, user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking feature flag {flag_name}: {e}")
            # Fail safely - return False for new features
            return False

    @classmethod
    async def is_user_in_rollout(cls, flag_name: str, user_id: int, session: Optional[AsyncSession] = None) -> bool:
        """
        Check if a user is included in the rollout for a feature.
        
        Uses consistent hashing to ensure users get same result across calls.
        """
        try:
            # Check if globally enabled first
            if not await cls.is_enabled(flag_name, session=session):
                return False
            
            config = await cls._get_flag_config(flag_name, session)
            
            # Check whitelist
            if config.user_whitelist and user_id in config.user_whitelist:
                return True
            
            # Check blacklist
            if config.user_blacklist and user_id in config.user_blacklist:
                return False
            
            # Use consistent hashing for rollout percentage
            user_hash = hashlib.md5(f"{flag_name}:{user_id}".encode()).hexdigest()
            hash_value = int(user_hash[:8], 16)  # Use first 8 hex chars
            user_percentage = hash_value % 100
            
            return user_percentage < config.rollout_percentage
            
        except Exception as e:
            logger.error(f"Error checking user rollout for {flag_name}, user {user_id}: {e}")
            return False

    @classmethod
    async def get_flag_value(cls, flag_name: str, default: Any = None, session: Optional[AsyncSession] = None) -> Any:
        """Get arbitrary value for a feature flag (for configuration flags)"""
        try:
            if session:
                result = await session.execute(
                    select(ConfigEntry).where(ConfigEntry.key == flag_name)
                )
                config_entry = result.scalar_one_or_none()
                
                if config_entry and config_entry.value:
                    # Try to parse as JSON for complex values
                    import json
                    try:
                        return json.loads(config_entry.value)
                    except json.JSONDecodeError:
                        return config_entry.value
            
            return default
            
        except Exception as e:
            logger.error(f"Error getting flag value {flag_name}: {e}")
            return default

    @classmethod
    async def set_flag(
        cls, 
        flag_name: str, 
        enabled: bool, 
        rollout_percentage: int = 100,
        user_whitelist: list = None,
        user_blacklist: list = None,
        session: Optional[AsyncSession] = None
    ):
        """
        Set a feature flag configuration.
        
        For admin/deployment use.
        """
        try:
            if not session:
                logger.error("Session required to set feature flags")
                return False
            
            config = FeatureFlagConfig(
                name=flag_name,
                enabled=enabled,
                rollout_percentage=rollout_percentage,
                user_whitelist=user_whitelist or [],
                user_blacklist=user_blacklist or []
            )
            
            await cls._save_flag_config(config, session)
            cls._invalidate_cache(flag_name)
            
            logger.info(f"Feature flag {flag_name} set to enabled={enabled}, rollout={rollout_percentage}%")
            return True
            
        except Exception as e:
            logger.error(f"Error setting feature flag {flag_name}: {e}")
            return False

    @classmethod
    async def emergency_disable(cls, flag_name: str, session: Optional[AsyncSession] = None) -> bool:
        """
        Emergency disable a feature flag.
        
        This is for immediate rollback scenarios.
        """
        try:
            success = await cls.set_flag(flag_name, enabled=False, rollout_percentage=0, session=session)
            
            if success:
                logger.warning(f"EMERGENCY DISABLE: Feature flag {flag_name} has been disabled")
                # Also clear cache immediately
                cls._invalidate_cache(flag_name)
                
            return success
            
        except Exception as e:
            logger.error(f"Error in emergency disable of {flag_name}: {e}")
            return False

    @classmethod
    async def disable_all_emotional_features(cls, session: Optional[AsyncSession] = None):
        """Emergency disable of all emotional features"""
        emotional_flags = [
            cls.EMOTIONAL_SYSTEM_ENABLED,
            cls.EMOTIONAL_ANALYSIS_ENABLED,
            cls.ARCHETYPE_SYSTEM_ENABLED,
            cls.NARRATIVE_ADAPTATION_ENABLED,
            cls.EMOTIONAL_REACTIONS_ENABLED,
            cls.EMOTIONAL_NARRATIVE_ENABLED,
            cls.EMOTIONAL_ENGAGEMENT_ENABLED,
            cls.EMOTIONAL_DAILY_ENABLED,
            cls.DEEP_PERSONALIZATION_ENABLED,
            cls.EMOTIONAL_MEMORY_ENABLED,
            cls.ADAPTIVE_RESPONSES_ENABLED
        ]
        
        logger.warning("EMERGENCY SHUTDOWN: Disabling all emotional features")
        
        for flag in emotional_flags:
            await cls.emergency_disable(flag, session)

    # Private methods
    @classmethod
    def _is_cache_valid(cls, flag_name: str) -> bool:
        """Check if cached flag config is still valid"""
        if flag_name not in cls._cache:
            return False
        
        if flag_name not in cls._cache_expiry:
            return False
        
        return datetime.now() < cls._cache_expiry[flag_name]

    @classmethod
    def _cache_flag(cls, flag_name: str, config: FeatureFlagConfig):
        """Cache flag configuration"""
        cls._cache[flag_name] = config
        cls._cache_expiry[flag_name] = datetime.now() + cls._cache_ttl

    @classmethod
    def _invalidate_cache(cls, flag_name: str):
        """Invalidate cache for a flag"""
        cls._cache.pop(flag_name, None)
        cls._cache_expiry.pop(flag_name, None)

    @classmethod
    async def _load_flag_config(cls, flag_name: str, session: Optional[AsyncSession] = None) -> FeatureFlagConfig:
        """Load flag configuration from database"""
        default_config = cls._get_default_config(flag_name)
        
        if not session:
            return default_config
        
        try:
            # Load basic enabled/disabled state
            result = await session.execute(
                select(ConfigEntry).where(ConfigEntry.key == flag_name)
            )
            config_entry = result.scalar_one_or_none()
            
            if config_entry:
                # Parse configuration
                import json
                try:
                    config_data = json.loads(config_entry.value)
                    return FeatureFlagConfig(
                        name=flag_name,
                        enabled=config_data.get('enabled', False),
                        rollout_percentage=config_data.get('rollout_percentage', 0),
                        user_whitelist=config_data.get('user_whitelist', []),
                        user_blacklist=config_data.get('user_blacklist', []),
                        start_date=cls._parse_datetime(config_data.get('start_date')),
                        end_date=cls._parse_datetime(config_data.get('end_date')),
                        dependencies=config_data.get('dependencies', [])
                    )
                except json.JSONDecodeError:
                    # Simple boolean value
                    enabled = config_entry.value.lower() in ('true', '1', 'yes', 'on')
                    default_config.enabled = enabled
                    return default_config
            
            return default_config
            
        except Exception as e:
            logger.error(f"Error loading flag config {flag_name}: {e}")
            return default_config

    @classmethod
    async def _save_flag_config(cls, config: FeatureFlagConfig, session: AsyncSession):
        """Save flag configuration to database"""
        import json
        
        config_data = {
            'enabled': config.enabled,
            'rollout_percentage': config.rollout_percentage,
            'user_whitelist': config.user_whitelist or [],
            'user_blacklist': config.user_blacklist or [],
            'dependencies': config.dependencies or []
        }
        
        if config.start_date:
            config_data['start_date'] = config.start_date.isoformat()
        if config.end_date:
            config_data['end_date'] = config.end_date.isoformat()
        
        # Upsert config entry
        result = await session.execute(
            select(ConfigEntry).where(ConfigEntry.key == config.name)
        )
        config_entry = result.scalar_one_or_none()
        
        if config_entry:
            config_entry.value = json.dumps(config_data)
        else:
            config_entry = ConfigEntry(
                key=config.name,
                value=json.dumps(config_data)
            )
            session.add(config_entry)
        
        await session.commit()

    @classmethod
    def _get_default_config(cls, flag_name: str) -> FeatureFlagConfig:
        """Get default configuration for a flag"""
        # All emotional features start disabled for safety
        return FeatureFlagConfig(
            name=flag_name,
            enabled=False,
            rollout_percentage=0
        )

    @classmethod
    async def _get_flag_config(cls, flag_name: str, session: Optional[AsyncSession] = None) -> FeatureFlagConfig:
        """Get flag configuration with caching"""
        if cls._is_cache_valid(flag_name):
            return cls._cache[flag_name]
        
        config = await cls._load_flag_config(flag_name, session)
        cls._cache_flag(flag_name, config)
        return config

    @classmethod
    def _is_time_valid(cls, config: FeatureFlagConfig) -> bool:
        """Check if current time is within flag's active period"""
        now = datetime.now()
        
        if config.start_date and now < config.start_date:
            return False
        
        if config.end_date and now > config.end_date:
            return False
        
        return True

    @classmethod
    async def _check_dependencies(cls, dependencies: list, user_id: Optional[int], session: Optional[AsyncSession]) -> bool:
        """Check if all dependency flags are enabled"""
        if not dependencies:
            return True
        
        for dep_flag in dependencies:
            if not await cls.is_enabled(dep_flag, user_id, session):
                return False
        
        return True

    @classmethod
    async def _is_user_enabled(cls, config: FeatureFlagConfig, user_id: int) -> bool:
        """Check if feature is enabled for specific user"""
        # Check whitelist first
        if config.user_whitelist and user_id in config.user_whitelist:
            return True
        
        # Check blacklist
        if config.user_blacklist and user_id in config.user_blacklist:
            return False
        
        # Check rollout percentage
        if config.rollout_percentage >= 100:
            return True
        
        if config.rollout_percentage <= 0:
            return False
        
        # Use consistent hashing
        user_hash = hashlib.md5(f"{config.name}:{user_id}".encode()).hexdigest()
        hash_value = int(user_hash[:8], 16)
        user_percentage = hash_value % 100
        
        return user_percentage < config.rollout_percentage

    @classmethod
    def _parse_datetime(cls, date_string: str) -> Optional[datetime]:
        """Parse datetime string"""
        if not date_string:
            return None
        
        try:
            return datetime.fromisoformat(date_string)
        except (ValueError, TypeError):
            return None


# Convenience functions for common checks
async def emotional_system_enabled(user_id: int = None, session: AsyncSession = None) -> bool:
    """Check if emotional system is enabled"""
    return await EmotionalFeatureFlags.is_enabled(
        EmotionalFeatureFlags.EMOTIONAL_SYSTEM_ENABLED, user_id, session
    )


async def narrative_adaptation_enabled(user_id: int = None, session: AsyncSession = None) -> bool:
    """Check if narrative adaptation is enabled"""
    return await EmotionalFeatureFlags.is_enabled(
        EmotionalFeatureFlags.NARRATIVE_ADAPTATION_ENABLED, user_id, session
    )


async def archetype_system_enabled(user_id: int = None, session: AsyncSession = None) -> bool:
    """Check if archetype system is enabled"""
    return await EmotionalFeatureFlags.is_enabled(
        EmotionalFeatureFlags.ARCHETYPE_SYSTEM_ENABLED, user_id, session
    )