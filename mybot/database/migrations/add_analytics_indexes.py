"""
Database migration to add performance indexes for analytics queries.
Task 30: Optimize database queries for analytics performance.

This migration adds strategic indexes to improve the performance of:
- Fragment analytics queries by fragment_key, view_count, engagement metrics
- User journey analytics queries by user_id, engagement_level, date ranges
- User narrative state queries for real-time progress tracking
- General user queries with points and activity filters
"""

from sqlalchemy import Index, text
from database.base import Base
from database.models import User, UserStats
from database.narrative_models import (
    FragmentAnalytics,
    UserJourneyAnalytics,
    UserNarrativeState,
    StoryFragment,
    NarrativeChoice
)

# Define strategic indexes for analytics performance optimization
ANALYTICS_INDEXES = [
    # FragmentAnalytics indexes for performance
    Index('idx_fragment_analytics_key', FragmentAnalytics.fragment_key),
    Index('idx_fragment_analytics_view_count', FragmentAnalytics.view_count),
    Index('idx_fragment_analytics_engagement', FragmentAnalytics.view_count, FragmentAnalytics.completion_count),
    Index('idx_fragment_analytics_updated', FragmentAnalytics.updated_at),
    Index('idx_fragment_analytics_compound', FragmentAnalytics.fragment_key, FragmentAnalytics.view_count),

    # UserJourneyAnalytics indexes for user behavior tracking
    Index('idx_user_journey_user_id', UserJourneyAnalytics.user_id),
    Index('idx_user_journey_engagement', UserJourneyAnalytics.engagement_level),
    Index('idx_user_journey_activity', UserJourneyAnalytics.last_activity_at),
    Index('idx_user_journey_completion', UserJourneyAnalytics.narrative_completion_percentage),
    Index('idx_user_journey_compound', UserJourneyAnalytics.user_id, UserJourneyAnalytics.engagement_level),
    Index('idx_user_journey_created', UserJourneyAnalytics.created_at),
    Index('idx_user_journey_fragments', UserJourneyAnalytics.fragments_completed),

    # UserNarrativeState indexes for real-time progress tracking
    Index('idx_user_narrative_fragment', UserNarrativeState.current_fragment_key),
    Index('idx_user_narrative_activity', UserNarrativeState.last_activity_at),
    Index('idx_user_narrative_fragments_visited', UserNarrativeState.fragments_visited),

    # User model indexes for analytics segmentation
    Index('idx_users_points', User.points),
    Index('idx_users_level', User.level),
    Index('idx_users_role', User.role),
    Index('idx_users_created', User.created_at),
    Index('idx_users_updated', User.updated_at),
    Index('idx_users_vip_expires', User.vip_expires_at),
    Index('idx_users_analytics_compound', User.points, User.level, User.role),

    # UserStats indexes for activity analysis
    Index('idx_user_stats_activity', UserStats.last_activity_at),
    Index('idx_user_stats_checkin', UserStats.last_checkin_at),
    Index('idx_user_stats_messages', UserStats.messages_sent),
    Index('idx_user_stats_compound', UserStats.user_id, UserStats.last_activity_at),

    # StoryFragment indexes for narrative analysis
    Index('idx_story_fragments_key', StoryFragment.key),
    Index('idx_story_fragments_level', StoryFragment.level),
    Index('idx_story_fragments_role', StoryFragment.required_role),
    Index('idx_story_fragments_besitos', StoryFragment.min_besitos),
    Index('idx_story_fragments_updated', StoryFragment.updated_at),

    # NarrativeChoice indexes for choice analysis
    Index('idx_narrative_choices_source', NarrativeChoice.source_fragment_id),
    Index('idx_narrative_choices_destination', NarrativeChoice.destination_fragment_key),
    Index('idx_narrative_choices_besitos', NarrativeChoice.required_besitos),
]

async def upgrade_database_indexes(engine):
    """
    Add all analytics performance indexes to the database.

    Args:
        engine: SQLAlchemy async engine
    """
    async with engine.begin() as conn:
        # Add all indexes
        for index in ANALYTICS_INDEXES:
            try:
                await conn.execute(text(f"CREATE INDEX IF NOT EXISTS {index.name} ON {index.table.name} ({', '.join([col.name for col in index.columns])})"))
                print(f"✓ Created index: {index.name}")
            except Exception as e:
                print(f"⚠ Failed to create index {index.name}: {e}")

        print(f"✓ Analytics indexes migration completed. Added {len(ANALYTICS_INDEXES)} indexes.")

async def downgrade_database_indexes(engine):
    """
    Remove all analytics performance indexes from the database.

    Args:
        engine: SQLAlchemy async engine
    """
    async with engine.begin() as conn:
        # Remove all indexes
        for index in ANALYTICS_INDEXES:
            try:
                await conn.execute(text(f"DROP INDEX IF EXISTS {index.name}"))
                print(f"✓ Dropped index: {index.name}")
            except Exception as e:
                print(f"⚠ Failed to drop index {index.name}: {e}")

        print(f"✓ Analytics indexes rollback completed. Removed {len(ANALYTICS_INDEXES)} indexes.")

# Export functions for migration system
upgrade = upgrade_database_indexes
downgrade = downgrade_database_indexes