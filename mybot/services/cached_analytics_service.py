"""
Cached analytics service that adds caching layer to existing analytics functionality.
Implements requirement for analytics data caching layer.
"""
import logging
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from services.analytics_service import AnalyticsService
from services.cache_service import CacheService

logger = logging.getLogger(__name__)

class CachedAnalyticsService:
    """
    A wrapper around AnalyticsService that adds caching functionality.
    Implements requirement for analytics data caching layer.
    """
    
    def __init__(self, session: AsyncSession, cache_service: CacheService):
        """
        Initialize the cached analytics service.
        
        Args:
            session: Database session
            cache_service: Cache service instance
        """
        self.analytics_service = AnalyticsService(session)
        self.cache_service = cache_service
    
    async def get_fragment_engagement_metrics(self, fragment_key: str) -> Dict[str, Any]:
        """
        Retrieves detailed engagement metrics for a specific story fragment with caching.
        Cache key: fragment_metrics:{fragment_key}
        TTL: 300 seconds (5 minutes)
        """
        cache_key = f"fragment_{fragment_key}"
        
        # Try to get from cache first
        cached_result = await self.cache_service.get("fragment_metrics", cache_key)
        if cached_result:
            logger.debug(f"Cache hit for fragment metrics: {fragment_key}")
            return cached_result
        
        # If not in cache, get from database
        logger.debug(f"Cache miss for fragment metrics: {fragment_key}")
        result = await self.analytics_service.get_fragment_engagement_metrics(fragment_key)
        
        # Cache the result
        await self.cache_service.set("fragment_metrics", cache_key, result, ttl=300)
        
        return result
    
    async def analyze_choice_distribution_patterns(self) -> Dict[str, Any]:
        """
        Analyzes the distribution of choices across the entire narrative with caching.
        Cache key: choice_patterns:global
        TTL: 600 seconds (10 minutes)
        """
        cache_key = "global"
        
        # Try to get from cache first
        cached_result = await self.cache_service.get("choice_patterns", cache_key)
        if cached_result:
            logger.debug("Cache hit for choice distribution patterns")
            return cached_result
        
        # If not in cache, get from database
        logger.debug("Cache miss for choice distribution patterns")
        result = await self.analytics_service.analyze_choice_distribution_patterns()
        
        # Cache the result
        await self.cache_service.set("choice_patterns", cache_key, result, ttl=600)
        
        return result
    
    async def identify_narrative_bottlenecks(self) -> Dict[str, Any]:
        """
        Identifies fragments where users frequently drop off or get stuck with caching.
        Cache key: bottlenecks:global
        TTL: 600 seconds (10 minutes)
        """
        cache_key = "global"
        
        # Try to get from cache first
        cached_result = await self.cache_service.get("bottlenecks", cache_key)
        if cached_result:
            logger.debug("Cache hit for narrative bottlenecks")
            return cached_result
        
        # If not in cache, get from database
        logger.debug("Cache miss for narrative bottlenecks")
        result = await self.analytics_service.identify_narrative_bottlenecks()
        
        # Cache the result
        await self.cache_service.set("bottlenecks", cache_key, result, ttl=600)
        
        return result
    
    async def generate_user_segment_analysis(self) -> Dict[str, Any]:
        """
        Generates an analysis of user segments based on their behavior with caching.
        Cache key: user_segments:global
        TTL: 900 seconds (15 minutes)
        """
        cache_key = "global"
        
        # Try to get from cache first
        cached_result = await self.cache_service.get("user_segments", cache_key)
        if cached_result:
            logger.debug("Cache hit for user segment analysis")
            return cached_result
        
        # If not in cache, get from database
        logger.debug("Cache miss for user segment analysis")
        result = await self.analytics_service.generate_user_segment_analysis()
        
        # Cache the result
        await self.cache_service.set("user_segments", cache_key, result, ttl=900)
        
        return result
    
    async def track_conversion_funnel_metrics(self) -> Dict[str, Any]:
        """
        Tracks metrics related to user conversion funnels with caching.
        Cache key: conversion_funnel:global
        TTL: 900 seconds (15 minutes)
        """
        cache_key = "global"
        
        # Try to get from cache first
        cached_result = await self.cache_service.get("conversion_funnel", cache_key)
        if cached_result:
            logger.debug("Cache hit for conversion funnel metrics")
            return cached_result
        
        # If not in cache, get from database
        logger.debug("Cache miss for conversion funnel metrics")
        result = await self.analytics_service.track_conversion_funnel_metrics()
        
        # Cache the result
        await self.cache_service.set("conversion_funnel", cache_key, result, ttl=900)
        
        return result
    
    async def get_character_voice_analytics(self) -> Dict[str, Any]:
        """
        Monitor character response effectiveness and emotional progression analytics with caching.
        Cache key: character_voice:global
        TTL: 600 seconds (10 minutes)
        """
        cache_key = "global"
        
        # Try to get from cache first
        cached_result = await self.cache_service.get("character_voice", cache_key)
        if cached_result:
            logger.debug("Cache hit for character voice analytics")
            return cached_result
        
        # If not in cache, get from database
        logger.debug("Cache miss for character voice analytics")
        result = await self.analytics_service.get_character_voice_analytics()
        
        # Cache the result
        await self.cache_service.set("character_voice", cache_key, result, ttl=600)
        
        return result
    
    async def get_comprehensive_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive analytics data for the admin dashboard with caching.
        Cache key: dashboard:global
        TTL: 300 seconds (5 minutes)
        """
        cache_key = "global"
        
        # Try to get from cache first
        cached_result = await self.cache_service.get("dashboard", cache_key)
        if cached_result:
            logger.debug("Cache hit for comprehensive dashboard data")
            return cached_result
        
        # If not in cache, get from database
        logger.debug("Cache miss for comprehensive dashboard data")
        result = await self.analytics_service.get_comprehensive_dashboard_data()
        
        # Cache the result
        await self.cache_service.set("dashboard", cache_key, result, ttl=300)
        
        return result
    
    async def invalidate_fragment_cache(self, fragment_key: str) -> bool:
        """
        Invalidate cache for a specific fragment.
        
        Args:
            fragment_key: Fragment key to invalidate
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = f"fragment_{fragment_key}"
        return await self.cache_service.delete("fragment_metrics", cache_key)
    
    async def invalidate_all_analytics_cache(self) -> bool:
        """
        Invalidate all analytics-related cache entries.
        
        Returns:
            True if successful, False otherwise
        """
        prefixes = [
            "fragment_metrics",
            "choice_patterns", 
            "bottlenecks",
            "user_segments",
            "conversion_funnel",
            "character_voice",
            "dashboard"
        ]
        
        success = True
        for prefix in prefixes:
            if not await self.cache_service.clear_prefix(prefix):
                success = False
                
        return success
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return self.cache_service.get_stats()