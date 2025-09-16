"""
Optimized analytics service with improved database query performance.
Task 30: Optimize database queries for analytics performance.

This service provides performance-optimized queries for analytics operations
with proper indexing, eager loading, pagination, and query batching.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, text
from sqlalchemy.orm import selectinload, joinedload
from datetime import datetime, timedelta
from database.models import User, UserStats
from database.narrative_models import (
    FragmentAnalytics,
    UserJourneyAnalytics,
    UserNarrativeState,
    StoryFragment,
    NarrativeChoice
)
import json

logger = logging.getLogger(__name__)

class OptimizedAnalyticsService:
    """
    Performance-optimized analytics service implementing best practices for
    database query optimization, caching, and real-time analytics.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.query_cache = {}  # Simple in-memory cache for repeated queries
        self.batch_size = 1000  # Default batch size for large queries

    async def get_fragment_engagement_metrics_optimized(
        self,
        fragment_key: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Optimized version of fragment engagement metrics with indexed queries.

        Performance optimizations:
        - Uses index on fragment_key for O(log n) lookup
        - Leverages compound index for view_count calculations
        - Includes query execution time tracking
        """
        start_time = datetime.utcnow()
        logger.info(f"Getting optimized engagement metrics for fragment {fragment_key}")

        try:
            # Check cache first
            cache_key = f"fragment_metrics_{fragment_key}"
            if use_cache and cache_key in self.query_cache:
                cached_result = self.query_cache[cache_key]
                if (datetime.utcnow() - cached_result['cached_at']).seconds < 300:  # 5 min cache
                    logger.debug(f"Cache hit for fragment metrics: {fragment_key}")
                    return cached_result['data']

            # Optimized query using proper indexes
            stmt = (
                select(FragmentAnalytics)
                .where(FragmentAnalytics.fragment_key == fragment_key)
                .order_by(desc(FragmentAnalytics.updated_at))
                .limit(1)  # Get most recent analytics
            )

            result = await self.session.execute(stmt)
            analytics = result.scalar_one_or_none()

            if not analytics:
                return {
                    "status": "no_data",
                    "fragment_key": fragment_key,
                    "message": "No analytics data found for this fragment",
                    "query_time_ms": self._get_query_time_ms(start_time)
                }

            # Calculate engagement metrics efficiently
            engagement_rate = (analytics.completion_count / analytics.view_count * 100) if analytics.view_count > 0 else 0
            drop_off_rate = (analytics.drop_off_count / analytics.view_count * 100) if analytics.view_count > 0 else 0

            result_data = {
                "status": "success",
                "fragment_key": fragment_key,
                "metrics": {
                    "view_count": analytics.view_count,
                    "completion_count": analytics.completion_count,
                    "drop_off_count": analytics.drop_off_count,
                    "engagement_rate": round(engagement_rate, 2),
                    "drop_off_rate": round(drop_off_rate, 2),
                    "average_time_spent": analytics.average_time_spent,
                    "choice_distribution": analytics.choice_distribution or {},
                    "most_popular_choice_id": analytics.most_popular_choice_id,
                    "users_progressed_from": analytics.users_progressed_from,
                    "users_returned_to": analytics.users_returned_to
                },
                "last_analyzed": analytics.last_analyzed_at.isoformat(),
                "query_time_ms": self._get_query_time_ms(start_time)
            }

            # Cache the result
            if use_cache:
                self.query_cache[cache_key] = {
                    'data': result_data,
                    'cached_at': datetime.utcnow()
                }

            return result_data

        except Exception as e:
            logger.error(f"Error getting optimized fragment engagement metrics: {e}")
            return {
                "status": "error",
                "message": str(e),
                "query_time_ms": self._get_query_time_ms(start_time)
            }

    async def get_user_journey_analytics_paginated(
        self,
        page: int = 1,
        page_size: int = 100,
        engagement_level: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Paginated user journey analytics with optimized queries.

        Performance optimizations:
        - Uses indexed pagination for efficient large dataset handling
        - Implements compound indexes for filtered queries
        - Eager loads related user data to avoid N+1 queries
        """
        start_time = datetime.utcnow()
        logger.info(f"Getting paginated user journey analytics (page {page}, size {page_size})")

        try:
            # Build optimized query with proper indexes
            base_query = select(UserJourneyAnalytics).options(
                joinedload(UserJourneyAnalytics.user)  # Eager load to avoid N+1
            )

            # Apply filters using indexed columns
            conditions = []
            if engagement_level:
                conditions.append(UserJourneyAnalytics.engagement_level == engagement_level)
            if date_from:
                conditions.append(UserJourneyAnalytics.created_at >= date_from)
            if date_to:
                conditions.append(UserJourneyAnalytics.created_at <= date_to)

            if conditions:
                base_query = base_query.where(and_(*conditions))

            # Count total records for pagination
            count_query = select(func.count(UserJourneyAnalytics.id))
            if conditions:
                count_query = count_query.where(and_(*conditions))

            total_count_result = await self.session.execute(count_query)
            total_count = total_count_result.scalar()

            # Apply pagination with indexed ordering
            offset = (page - 1) * page_size
            paginated_query = (
                base_query
                .order_by(desc(UserJourneyAnalytics.last_activity_at))  # Use indexed column
                .offset(offset)
                .limit(page_size)
            )

            result = await self.session.execute(paginated_query)
            journey_analytics = result.scalars().all()

            # Calculate pagination metadata
            total_pages = (total_count + page_size - 1) // page_size
            has_next = page < total_pages
            has_prev = page > 1

            return {
                "status": "success",
                "data": [
                    {
                        "user_id": ja.user_id,
                        "user_points": ja.user.points if ja.user else 0,
                        "user_level": ja.user.level if ja.user else 0,
                        "fragments_completed": ja.fragments_completed,
                        "engagement_level": ja.engagement_level,
                        "total_time_spent": ja.total_time_spent,
                        "exploration_score": ja.exploration_score,
                        "narrative_completion_percentage": ja.narrative_completion_percentage,
                        "last_activity_at": ja.last_activity_at.isoformat() if ja.last_activity_at else None
                    }
                    for ja in journey_analytics
                ],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev
                },
                "query_time_ms": self._get_query_time_ms(start_time)
            }

        except Exception as e:
            logger.error(f"Error getting paginated user journey analytics: {e}")
            return {
                "status": "error",
                "message": str(e),
                "query_time_ms": self._get_query_time_ms(start_time)
            }

    async def get_real_time_user_progress_batch(
        self,
        user_ids: List[int]
    ) -> Dict[str, Any]:
        """
        Batch query for real-time user progress tracking.

        Performance optimizations:
        - Batches multiple user queries into single database call
        - Uses indexed user_id lookups for O(log n) performance
        - Eager loads narrative state to avoid additional queries
        """
        start_time = datetime.utcnow()
        logger.info(f"Getting real-time progress for {len(user_ids)} users")

        try:
            if not user_ids:
                return {
                    "status": "success",
                    "data": {},
                    "query_time_ms": self._get_query_time_ms(start_time)
                }

            # Batch query for user narrative states
            narrative_stmt = (
                select(UserNarrativeState)
                .options(joinedload(UserNarrativeState.user))
                .where(UserNarrativeState.user_id.in_(user_ids))
            )

            narrative_result = await self.session.execute(narrative_stmt)
            narrative_states = narrative_result.scalars().all()

            # Create progress data mapping
            progress_data = {}
            for state in narrative_states:
                progress_data[state.user_id] = {
                    "current_fragment": state.current_fragment_key,
                    "fragments_visited": state.fragments_visited,
                    "total_besitos_earned": state.total_besitos_earned,
                    "last_activity": state.last_activity_at.isoformat() if state.last_activity_at else None,
                    "choices_made_count": len(state.choices_made) if state.choices_made else 0,
                    "user_points": state.user.points if state.user else 0,
                    "user_level": state.user.level if state.user else 0
                }

            # Add empty entries for users without narrative state
            for user_id in user_ids:
                if user_id not in progress_data:
                    progress_data[user_id] = {
                        "current_fragment": None,
                        "fragments_visited": 0,
                        "total_besitos_earned": 0,
                        "last_activity": None,
                        "choices_made_count": 0,
                        "user_points": 0,
                        "user_level": 0
                    }

            return {
                "status": "success",
                "data": progress_data,
                "users_processed": len(user_ids),
                "users_with_narrative_data": len(narrative_states),
                "query_time_ms": self._get_query_time_ms(start_time)
            }

        except Exception as e:
            logger.error(f"Error getting batch user progress: {e}")
            return {
                "status": "error",
                "message": str(e),
                "query_time_ms": self._get_query_time_ms(start_time)
            }

    async def get_analytics_dashboard_optimized(
        self,
        cache_duration: int = 300  # 5 minutes cache
    ) -> Dict[str, Any]:
        """
        Optimized dashboard data aggregation with parallel query execution.

        Performance optimizations:
        - Executes analytics queries in parallel using asyncio.gather
        - Uses indexed aggregation queries for fast computation
        - Implements intelligent caching for expensive operations
        """
        start_time = datetime.utcnow()
        logger.info("Getting optimized analytics dashboard data")

        try:
            # Check cache for dashboard data
            cache_key = "dashboard_data"
            if cache_key in self.query_cache:
                cached_result = self.query_cache[cache_key]
                if (datetime.utcnow() - cached_result['cached_at']).seconds < cache_duration:
                    logger.debug("Cache hit for dashboard data")
                    return cached_result['data']

            # Parallel execution of optimized dashboard queries
            results = await asyncio.gather(
                self._get_user_segment_stats_optimized(),
                self._get_fragment_performance_stats_optimized(),
                self._get_engagement_trends_optimized(),
                self._get_content_effectiveness_stats_optimized(),
                return_exceptions=True
            )

            user_segments, fragment_performance, engagement_trends, content_effectiveness = results

            # Handle any exceptions in parallel queries
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error in parallel query {i}: {result}")

            dashboard_data = {
                "status": "success",
                "generated_at": datetime.utcnow().isoformat(),
                "user_segments": user_segments if not isinstance(user_segments, Exception) else {"status": "error", "message": str(user_segments)},
                "fragment_performance": fragment_performance if not isinstance(fragment_performance, Exception) else {"status": "error", "message": str(fragment_performance)},
                "engagement_trends": engagement_trends if not isinstance(engagement_trends, Exception) else {"status": "error", "message": str(engagement_trends)},
                "content_effectiveness": content_effectiveness if not isinstance(content_effectiveness, Exception) else {"status": "error", "message": str(content_effectiveness)},
                "query_time_ms": self._get_query_time_ms(start_time)
            }

            # Cache the result
            self.query_cache[cache_key] = {
                'data': dashboard_data,
                'cached_at': datetime.utcnow()
            }

            return dashboard_data

        except Exception as e:
            logger.error(f"Error getting optimized dashboard data: {e}")
            return {
                "status": "error",
                "message": str(e),
                "query_time_ms": self._get_query_time_ms(start_time)
            }

    async def _get_user_segment_stats_optimized(self) -> Dict[str, Any]:
        """Optimized user segmentation using indexed queries."""
        try:
            # Use indexed queries for user segmentation
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)

            # Parallel execution of segment queries
            segment_queries = await asyncio.gather(
                # High-value users (using points index)
                self.session.execute(
                    select(func.count(User.id)).where(User.points > 1000)
                ),
                # Recent users (using created_at index)
                self.session.execute(
                    select(func.count(User.id)).where(User.created_at > week_ago)
                ),
                # Active users (using narrative state index)
                self.session.execute(
                    select(func.count(UserNarrativeState.user_id))
                    .where(UserNarrativeState.last_activity_at > week_ago)
                ),
                # VIP users (using role index)
                self.session.execute(
                    select(func.count(User.id)).where(User.role == 'vip')
                )
            )

            high_value_count = segment_queries[0].scalar()
            recent_users_count = segment_queries[1].scalar()
            active_users_count = segment_queries[2].scalar()
            vip_users_count = segment_queries[3].scalar()

            return {
                "status": "success",
                "segments": {
                    "high_value_users": high_value_count,
                    "recent_users": recent_users_count,
                    "active_users": active_users_count,
                    "vip_users": vip_users_count
                }
            }

        except Exception as e:
            logger.error(f"Error getting user segment stats: {e}")
            return {"status": "error", "message": str(e)}

    async def _get_fragment_performance_stats_optimized(self) -> Dict[str, Any]:
        """Optimized fragment performance using compound indexes."""
        try:
            # Use compound indexes for fragment performance
            performance_query = await self.session.execute(
                select(
                    func.count(FragmentAnalytics.id).label('total_fragments'),
                    func.sum(FragmentAnalytics.view_count).label('total_views'),
                    func.sum(FragmentAnalytics.completion_count).label('total_completions'),
                    func.avg(
                        FragmentAnalytics.completion_count * 100.0 /
                        func.nullif(FragmentAnalytics.view_count, 0)
                    ).label('avg_completion_rate')
                )
                .where(FragmentAnalytics.view_count > 0)
            )

            stats = performance_query.one()

            # Get top performing fragments
            top_fragments_query = await self.session.execute(
                select(
                    FragmentAnalytics.fragment_key,
                    FragmentAnalytics.view_count,
                    FragmentAnalytics.completion_count,
                    (FragmentAnalytics.completion_count * 100.0 /
                     func.nullif(FragmentAnalytics.view_count, 0)).label('completion_rate')
                )
                .where(FragmentAnalytics.view_count > 10)
                .order_by(desc('completion_rate'))
                .limit(5)
            )

            top_fragments = [
                {
                    "fragment_key": row.fragment_key,
                    "view_count": row.view_count,
                    "completion_count": row.completion_count,
                    "completion_rate": round(row.completion_rate or 0, 2)
                }
                for row in top_fragments_query
            ]

            return {
                "status": "success",
                "overall_stats": {
                    "total_fragments": stats.total_fragments,
                    "total_views": stats.total_views,
                    "total_completions": stats.total_completions,
                    "average_completion_rate": round(stats.avg_completion_rate or 0, 2)
                },
                "top_performing_fragments": top_fragments
            }

        except Exception as e:
            logger.error(f"Error getting fragment performance stats: {e}")
            return {"status": "error", "message": str(e)}

    async def _get_engagement_trends_optimized(self) -> Dict[str, Any]:
        """Optimized engagement trends using time-based indexes."""
        try:
            # Use time-based indexes for engagement trends
            now = datetime.utcnow()
            days_back = 7

            daily_engagement = []
            for i in range(days_back):
                day_start = now - timedelta(days=i+1)
                day_end = now - timedelta(days=i)

                daily_stats = await self.session.execute(
                    select(
                        func.count(UserJourneyAnalytics.id).label('active_users'),
                        func.sum(UserJourneyAnalytics.total_time_spent).label('total_time'),
                        func.avg(UserJourneyAnalytics.exploration_score).label('avg_exploration')
                    )
                    .where(
                        and_(
                            UserJourneyAnalytics.last_activity_at >= day_start,
                            UserJourneyAnalytics.last_activity_at < day_end
                        )
                    )
                )

                stats = daily_stats.one()
                daily_engagement.append({
                    "date": day_start.date().isoformat(),
                    "active_users": stats.active_users,
                    "total_time_spent": stats.total_time or 0,
                    "average_exploration_score": round(stats.avg_exploration or 0, 2)
                })

            return {
                "status": "success",
                "daily_trends": list(reversed(daily_engagement))  # Oldest to newest
            }

        except Exception as e:
            logger.error(f"Error getting engagement trends: {e}")
            return {"status": "error", "message": str(e)}

    async def _get_content_effectiveness_stats_optimized(self) -> Dict[str, Any]:
        """Optimized content effectiveness analysis."""
        try:
            # Character effectiveness analysis using indexed queries
            character_effectiveness = await self.session.execute(
                select(
                    StoryFragment.character,
                    func.count(FragmentAnalytics.id).label('fragment_count'),
                    func.avg(FragmentAnalytics.view_count).label('avg_views'),
                    func.avg(
                        FragmentAnalytics.completion_count * 100.0 /
                        func.nullif(FragmentAnalytics.view_count, 0)
                    ).label('avg_completion_rate')
                )
                .join(FragmentAnalytics, StoryFragment.key == FragmentAnalytics.fragment_key)
                .where(FragmentAnalytics.view_count > 0)
                .group_by(StoryFragment.character)
                .order_by(desc('avg_completion_rate'))
            )

            character_stats = [
                {
                    "character": row.character,
                    "fragment_count": row.fragment_count,
                    "average_views": round(row.avg_views or 0, 2),
                    "average_completion_rate": round(row.avg_completion_rate or 0, 2)
                }
                for row in character_effectiveness
            ]

            return {
                "status": "success",
                "character_effectiveness": character_stats
            }

        except Exception as e:
            logger.error(f"Error getting content effectiveness stats: {e}")
            return {"status": "error", "message": str(e)}

    def _get_query_time_ms(self, start_time: datetime) -> int:
        """Calculate query execution time in milliseconds."""
        return int((datetime.utcnow() - start_time).total_seconds() * 1000)

    async def clear_query_cache(self):
        """Clear the in-memory query cache."""
        self.query_cache.clear()
        logger.info("Query cache cleared")

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get query cache statistics."""
        return {
            "cache_entries": len(self.query_cache),
            "cache_keys": list(self.query_cache.keys())
        }