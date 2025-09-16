import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from database.models import User
from database.narrative_models import FragmentAnalytics, UserJourneyAnalytics, UserNarrativeState, StoryFragment, NarrativeChoice
import json
import csv
import io

# Placeholder types for return values
EngagementMetrics = Dict[str, Any]
ChoiceDistribution = Dict[str, Any]
BottleneckReport = Dict[str, Any]
SegmentAnalysis = Dict[str, Any]
ConversionFunnel = Dict[str, Any]
ExportData = Any

logger = logging.getLogger(__name__)

class AnalyticsService:
    """
    Service for providing comprehensive analytics on narrative engagement.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_fragment_engagement_metrics(self, fragment_key: str) -> EngagementMetrics:
        """
        Retrieves detailed engagement metrics for a specific story fragment.
        """
        logger.info(f"Getting engagement metrics for fragment {fragment_key}")

        try:
            # Get fragment analytics
            stmt = select(FragmentAnalytics).where(FragmentAnalytics.fragment_key == fragment_key)
            result = await self.session.execute(stmt)
            analytics = result.scalar_one_or_none()

            if not analytics:
                return {
                    "status": "no_data",
                    "fragment_key": fragment_key,
                    "message": "No analytics data found for this fragment"
                }

            # Calculate engagement rate
            engagement_rate = 0
            if analytics.view_count > 0:
                engagement_rate = (analytics.completion_count / analytics.view_count) * 100

            # Calculate drop-off rate
            drop_off_rate = 0
            if analytics.view_count > 0:
                drop_off_rate = (analytics.drop_off_count / analytics.view_count) * 100

            return {
                "status": "success",
                "fragment_key": fragment_key,
                "metrics": {
                    "view_count": analytics.view_count,
                    "completion_count": analytics.completion_count,
                    "drop_off_count": analytics.drop_off_count,
                    "engagement_rate": round(engagement_rate, 2),
                    "drop_off_rate": round(drop_off_rate, 2),
                    "average_time_spent": analytics.average_time_spent,
                    "choice_distribution": analytics.choice_distribution,
                    "most_popular_choice_id": analytics.most_popular_choice_id,
                    "users_progressed_from": analytics.users_progressed_from,
                    "users_returned_to": analytics.users_returned_to
                },
                "last_analyzed": analytics.last_analyzed_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting fragment engagement metrics: {e}")
            return {"status": "error", "message": str(e)}

    async def analyze_choice_distribution_patterns(self) -> ChoiceDistribution:
        """
        Analyzes the distribution of choices across the entire narrative.
        """
        logger.info("Analyzing choice distribution patterns")

        try:
            # Get all fragment analytics with choice distribution data
            stmt = select(FragmentAnalytics).where(FragmentAnalytics.choice_distribution.isnot(None))
            result = await self.session.execute(stmt)
            fragment_analytics = result.scalars().all()

            if not fragment_analytics:
                return {
                    "status": "no_data",
                    "message": "No choice distribution data available"
                }

            # Aggregate choice patterns
            total_choices_made = 0
            choice_popularity = {}
            fragment_choice_stats = {}

            for analytics in fragment_analytics:
                fragment_key = analytics.fragment_key
                choice_dist = analytics.choice_distribution or {}

                fragment_total = sum(choice_dist.values())
                total_choices_made += fragment_total

                fragment_choice_stats[fragment_key] = {
                    "total_choices": fragment_total,
                    "choice_breakdown": choice_dist,
                    "most_popular": analytics.most_popular_choice_id
                }

                # Aggregate global choice popularity
                for choice_id, count in choice_dist.items():
                    choice_popularity[choice_id] = choice_popularity.get(choice_id, 0) + count

            # Find global most popular choices
            most_popular_choices = sorted(
                choice_popularity.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]  # Top 10

            # Calculate choice diversity (how evenly distributed choices are)
            diversity_scores = {}
            for fragment_key, stats in fragment_choice_stats.items():
                if stats["total_choices"] > 0:
                    choices = list(stats["choice_breakdown"].values())
                    if len(choices) > 1:
                        # Calculate entropy-like diversity score
                        proportions = [c / stats["total_choices"] for c in choices]
                        diversity = -sum(p * (p.bit_length() - 1) for p in proportions if p > 0)
                        diversity_scores[fragment_key] = round(diversity, 2)

            return {
                "status": "success",
                "summary": {
                    "total_choices_made": total_choices_made,
                    "fragments_analyzed": len(fragment_analytics),
                    "unique_choices": len(choice_popularity)
                },
                "most_popular_choices": most_popular_choices,
                "fragment_stats": fragment_choice_stats,
                "diversity_scores": diversity_scores,
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error analyzing choice distribution: {e}")
            return {"status": "error", "message": str(e)}

    async def identify_narrative_bottlenecks(self) -> BottleneckReport:
        """
        Identifies fragments where users frequently drop off or get stuck.
        """
        logger.info("Identifying narrative bottlenecks")

        try:
            # Get fragment analytics ordered by drop-off rate
            stmt = select(FragmentAnalytics).where(FragmentAnalytics.view_count > 0)
            result = await self.session.execute(stmt)
            fragment_analytics = result.scalars().all()

            if not fragment_analytics:
                return {
                    "status": "no_data",
                    "message": "No fragment analytics data available"
                }

            # Calculate bottleneck metrics
            bottlenecks = []
            potential_issues = []

            for analytics in fragment_analytics:
                fragment_key = analytics.fragment_key
                view_count = analytics.view_count
                completion_count = analytics.completion_count
                drop_off_count = analytics.drop_off_count

                # Calculate drop-off rate
                drop_off_rate = (drop_off_count / view_count) * 100 if view_count > 0 else 0

                # Calculate completion rate
                completion_rate = (completion_count / view_count) * 100 if view_count > 0 else 0

                fragment_data = {
                    "fragment_key": fragment_key,
                    "view_count": view_count,
                    "completion_count": completion_count,
                    "drop_off_count": drop_off_count,
                    "drop_off_rate": round(drop_off_rate, 2),
                    "completion_rate": round(completion_rate, 2),
                    "average_time_spent": analytics.average_time_spent
                }

                # Identify bottlenecks (high drop-off rate or low completion rate)
                if drop_off_rate > 30 or completion_rate < 50:  # Configurable thresholds
                    severity = "critical" if drop_off_rate > 50 else "warning"
                    bottlenecks.append({
                        **fragment_data,
                        "severity": severity,
                        "issue_type": "high_drop_off" if drop_off_rate > 30 else "low_completion"
                    })

                # Identify potential navigation issues
                if analytics.users_returned_to > (view_count * 0.2):  # 20% return rate might indicate confusion
                    potential_issues.append({
                        **fragment_data,
                        "issue_type": "high_return_rate",
                        "return_count": analytics.users_returned_to,
                        "return_rate": round((analytics.users_returned_to / view_count) * 100, 2)
                    })

            # Sort bottlenecks by severity
            bottlenecks.sort(key=lambda x: x["drop_off_rate"], reverse=True)

            # Get user journey patterns for additional insights
            journey_stmt = select(UserJourneyAnalytics).where(UserJourneyAnalytics.engagement_level == "stalled")
            journey_result = await self.session.execute(journey_stmt)
            stalled_users = journey_result.scalars().all()

            # Find common last fragments for stalled users
            last_fragments = {}
            for user_journey in stalled_users:
                if user_journey.last_fragment_key:
                    key = user_journey.last_fragment_key
                    last_fragments[key] = last_fragments.get(key, 0) + 1

            stalled_hotspots = sorted(last_fragments.items(), key=lambda x: x[1], reverse=True)[:5]

            return {
                "status": "success",
                "summary": {
                    "total_fragments_analyzed": len(fragment_analytics),
                    "critical_bottlenecks": len([b for b in bottlenecks if b.get("severity") == "critical"]),
                    "warning_bottlenecks": len([b for b in bottlenecks if b.get("severity") == "warning"]),
                    "potential_navigation_issues": len(potential_issues),
                    "stalled_users_count": len(stalled_users)
                },
                "bottlenecks": bottlenecks[:10],  # Top 10 bottlenecks
                "potential_issues": potential_issues[:5],  # Top 5 potential issues
                "stalled_user_hotspots": stalled_hotspots,
                "recommendations": self._generate_bottleneck_recommendations(bottlenecks, potential_issues),
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error identifying narrative bottlenecks: {e}")
            return {"status": "error", "message": str(e)}

    def _generate_bottleneck_recommendations(self, bottlenecks: List[Dict], potential_issues: List[Dict]) -> List[str]:
        """Generate actionable recommendations based on bottleneck analysis."""
        recommendations = []

        critical_bottlenecks = [b for b in bottlenecks if b.get("severity") == "critical"]
        if critical_bottlenecks:
            recommendations.append(f"Review {len(critical_bottlenecks)} critical fragments with >50% drop-off rate")

        high_return_issues = [i for i in potential_issues if i.get("issue_type") == "high_return_rate"]
        if high_return_issues:
            recommendations.append(f"Investigate {len(high_return_issues)} fragments with high return rates - may indicate user confusion")

        low_completion_fragments = [b for b in bottlenecks if b.get("completion_rate", 0) < 30]
        if low_completion_fragments:
            recommendations.append(f"Optimize {len(low_completion_fragments)} fragments with very low completion rates")

        if not recommendations:
            recommendations.append("No critical issues detected - narrative flow appears healthy")

        return recommendations

    async def generate_user_segment_analysis(self) -> SegmentAnalysis:
        """
        Generates an analysis of user segments based on their behavior.
        Segments include: Whales, Explorers, Engaged, Stalled, and New Users.
        """
        logger.info("Generating user segment analysis...")

        users_stmt = select(User).options(selectinload(User.narrative_state))
        result = await self.session.execute(users_stmt)
        all_users = result.scalars().all()

        segments = {
            "whales": [],
            "explorers": [],
            "highly_engaged": [],
            "stalled": [],
            "new_users": [],
            "inactive": [],
        }

        now = datetime.utcnow()
        one_week_ago = now - timedelta(days=7)
        three_days_ago = now - timedelta(days=3)

        for user in all_users:
            # New Users segment
            if user.created_at > one_week_ago:
                segments["new_users"].append(user.id)

            narrative_state = user.narrative_state
            if narrative_state:
                # Whales segment (top 10% by points)
                if user.points > 1000: # Arbitrary threshold for now
                    segments["whales"].append(user.id)

                # Explorers segment
                if narrative_state.fragments_visited > 50: # Arbitrary threshold
                    segments["explorers"].append(user.id)
                
                # Highly Engaged segment
                if narrative_state.last_activity_at > three_days_ago:
                    segments["highly_engaged"].append(user.id)
                
                # Stalled segment
                elif narrative_state.last_activity_at < one_week_ago:
                    segments["stalled"].append(user.id)
            else:
                # Inactive in narrative
                segments["inactive"].append(user.id)

        # Prepare summary report
        report = {
            "segment_counts": {name: len(users) for name, users in segments.items()},
            "segments": segments,
            "generated_at": now.isoformat()
        }
        
        logger.info(f"User segmentation analysis complete: {report['segment_counts']}")
        return report

    async def track_conversion_funnel_metrics(self) -> ConversionFunnel:
        """
        Tracks metrics related to user conversion funnels (e.g., item purchase to access content).
        """
        logger.info("Tracking conversion funnel metrics")

        try:
            # Get user journey data for funnel analysis
            journey_stmt = select(UserJourneyAnalytics).options(selectinload(UserJourneyAnalytics.user))
            journey_result = await self.session.execute(journey_stmt)
            user_journeys = journey_result.scalars().all()

            if not user_journeys:
                return {
                    "status": "no_data",
                    "message": "No user journey data available for funnel analysis"
                }

            # Define funnel stages
            funnel_stages = {
                "initial_visit": {"count": 0, "description": "Users who started narrative"},
                "engaged": {"count": 0, "description": "Users who visited 3+ fragments"},
                "highly_engaged": {"count": 0, "description": "Users who visited 10+ fragments"},
                "purchaser": {"count": 0, "description": "Users who made shop purchases"},
                "retained": {"count": 0, "description": "Users active in last 7 days"}
            }

            # Analyze each user journey
            now = datetime.utcnow()
            week_ago = now - timedelta(days=7)

            for journey in user_journeys:
                user = journey.user

                # Stage 1: Initial visit (all users in journey analytics)
                funnel_stages["initial_visit"]["count"] += 1

                # Stage 2: Engaged (3+ fragments visited)
                if journey.fragments_completed >= 3:
                    funnel_stages["engaged"]["count"] += 1

                # Stage 3: Highly engaged (10+ fragments visited)
                if journey.fragments_completed >= 10:
                    funnel_stages["highly_engaged"]["count"] += 1

                # Stage 4: Purchaser (has made purchases)
                if user and user.points < journey.total_besitos_earned:  # Basic heuristic for purchase activity
                    funnel_stages["purchaser"]["count"] += 1

                # Stage 5: Retained (active in last 7 days)
                if journey.last_activity_at > week_ago:
                    funnel_stages["retained"]["count"] += 1

            # Calculate conversion rates
            total_users = funnel_stages["initial_visit"]["count"]
            conversion_rates = {}

            for stage, data in funnel_stages.items():
                if total_users > 0:
                    conversion_rates[stage] = round((data["count"] / total_users) * 100, 2)
                else:
                    conversion_rates[stage] = 0

            # Calculate drop-off rates between stages
            stage_names = list(funnel_stages.keys())
            drop_off_rates = {}

            for i in range(len(stage_names) - 1):
                current_stage = stage_names[i]
                next_stage = stage_names[i + 1]
                current_count = funnel_stages[current_stage]["count"]
                next_count = funnel_stages[next_stage]["count"]

                if current_count > 0:
                    drop_off_rate = round(((current_count - next_count) / current_count) * 100, 2)
                    drop_off_rates[f"{current_stage}_to_{next_stage}"] = drop_off_rate

            # Identify cohorts by registration time
            cohort_analysis = {}
            for journey in user_journeys:
                if journey.user:
                    # Group by month of registration
                    cohort_month = journey.journey_started_at.strftime("%Y-%m")
                    if cohort_month not in cohort_analysis:
                        cohort_analysis[cohort_month] = {
                            "total_users": 0,
                            "engaged_users": 0,
                            "retained_users": 0
                        }

                    cohort_analysis[cohort_month]["total_users"] += 1
                    if journey.fragments_completed >= 3:
                        cohort_analysis[cohort_month]["engaged_users"] += 1
                    if journey.last_activity_at > week_ago:
                        cohort_analysis[cohort_month]["retained_users"] += 1

            return {
                "status": "success",
                "funnel_stages": funnel_stages,
                "conversion_rates": conversion_rates,
                "drop_off_rates": drop_off_rates,
                "cohort_analysis": cohort_analysis,
                "insights": {
                    "strongest_conversion": max(conversion_rates.items(), key=lambda x: x[1]) if conversion_rates else None,
                    "biggest_drop_off": max(drop_off_rates.items(), key=lambda x: x[1]) if drop_off_rates else None,
                    "total_conversion_rate": conversion_rates.get("retained", 0)
                },
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error tracking conversion funnel metrics: {e}")
            return {"status": "error", "message": str(e)}

    async def export_analytics_data(self, date_range: Tuple[str, str], format: str, export_type: str = "full") -> ExportData:
        """
        Exports analytics data in a specified format (e.g., CSV, JSON).
        """
        logger.info(f"Exporting analytics data from {date_range[0]} to {date_range[1]} in {format} format")

        try:
            start_date = datetime.fromisoformat(date_range[0])
            end_date = datetime.fromisoformat(date_range[1])

            # Gather all analytics data for the date range
            export_data = {
                "metadata": {
                    "export_date": datetime.utcnow().isoformat(),
                    "date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    },
                    "format": format
                }
            }

            # Get fragment analytics
            fragment_stmt = select(FragmentAnalytics).where(
                and_(
                    FragmentAnalytics.created_at >= start_date,
                    FragmentAnalytics.created_at <= end_date
                )
            )
            fragment_result = await self.session.execute(fragment_stmt)
            fragment_analytics = fragment_result.scalars().all()

            # Get user journey analytics
            journey_stmt = select(UserJourneyAnalytics).where(
                and_(
                    UserJourneyAnalytics.created_at >= start_date,
                    UserJourneyAnalytics.created_at <= end_date
                )
            )
            journey_result = await self.session.execute(journey_stmt)
            journey_analytics = journey_result.scalars().all()

            # Format data based on requested format
            if format.lower() == "json":
                export_data["fragment_analytics"] = [
                    {
                        "fragment_key": fa.fragment_key,
                        "view_count": fa.view_count,
                        "completion_count": fa.completion_count,
                        "drop_off_count": fa.drop_off_count,
                        "average_time_spent": fa.average_time_spent,
                        "choice_distribution": fa.choice_distribution,
                        "most_popular_choice_id": fa.most_popular_choice_id,
                        "users_progressed_from": fa.users_progressed_from,
                        "users_returned_to": fa.users_returned_to,
                        "created_at": fa.created_at.isoformat(),
                        "updated_at": fa.updated_at.isoformat()
                    }
                    for fa in fragment_analytics
                ]

                export_data["user_journey_analytics"] = [
                    {
                        "user_id": ja.user_id,
                        "fragments_visited": ja.fragments_visited,
                        "choices_made": ja.choices_made,
                        "progression_path": ja.progression_path,
                        "total_time_spent": ja.total_time_spent,
                        "session_count": ja.session_count,
                        "average_session_duration": ja.average_session_duration,
                        "backtrack_count": ja.backtrack_count,
                        "exploration_score": ja.exploration_score,
                        "engagement_level": ja.engagement_level,
                        "fragments_completed": ja.fragments_completed,
                        "narrative_completion_percentage": ja.narrative_completion_percentage,
                        "emotional_states": ja.emotional_states,
                        "character_interaction_count": ja.character_interaction_count,
                        "journey_started_at": ja.journey_started_at.isoformat(),
                        "last_activity_at": ja.last_activity_at.isoformat()
                    }
                    for ja in journey_analytics
                ]

                return json.dumps(export_data, indent=2, ensure_ascii=False)

            elif format.lower() == "csv":
                # Create CSV for fragment analytics
                fragment_csv = io.StringIO()
                fragment_writer = csv.writer(fragment_csv)

                # Write headers
                fragment_writer.writerow([
                    "fragment_key", "view_count", "completion_count", "drop_off_count",
                    "average_time_spent", "users_progressed_from", "users_returned_to",
                    "engagement_rate", "drop_off_rate", "created_at", "updated_at"
                ])

                # Write data
                for fa in fragment_analytics:
                    engagement_rate = (fa.completion_count / fa.view_count * 100) if fa.view_count > 0 else 0
                    drop_off_rate = (fa.drop_off_count / fa.view_count * 100) if fa.view_count > 0 else 0

                    fragment_writer.writerow([
                        fa.fragment_key, fa.view_count, fa.completion_count, fa.drop_off_count,
                        fa.average_time_spent, fa.users_progressed_from, fa.users_returned_to,
                        round(engagement_rate, 2), round(drop_off_rate, 2),
                        fa.created_at.isoformat(), fa.updated_at.isoformat()
                    ])

                # Create CSV for user journey analytics
                journey_csv = io.StringIO()
                journey_writer = csv.writer(journey_csv)

                journey_writer.writerow([
                    "user_id", "total_time_spent", "session_count", "average_session_duration",
                    "backtrack_count", "exploration_score", "engagement_level",
                    "fragments_completed", "narrative_completion_percentage",
                    "journey_started_at", "last_activity_at"
                ])

                for ja in journey_analytics:
                    journey_writer.writerow([
                        ja.user_id, ja.total_time_spent, ja.session_count, ja.average_session_duration,
                        ja.backtrack_count, ja.exploration_score, ja.engagement_level,
                        ja.fragments_completed, ja.narrative_completion_percentage,
                        ja.journey_started_at.isoformat(), ja.last_activity_at.isoformat()
                    ])

                return {
                    "fragment_analytics.csv": fragment_csv.getvalue(),
                    "user_journey_analytics.csv": journey_csv.getvalue(),
                    "metadata": export_data["metadata"]
                }

            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            logger.error(f"Error exporting analytics data: {e}")
            return {"status": "error", "message": str(e)}

    async def export_character_analytics_data(self, character_name: str = None, date_range: Tuple[str, str] = None, format: str = "json") -> ExportData:
        """
        Export character-specific analytics data.
        Implements requirement 4.3 - Character Voice Analytics Export.
        """
        logger.info(f"Exporting character analytics for {character_name or 'all characters'} in {format} format")

        try:
            # Get character voice analytics
            character_data = await self.get_character_voice_analytics()

            if character_data.get("status") != "success":
                return {"status": "error", "message": "No character analytics data available"}

            # Filter by character if specified
            character_analytics = character_data.get("character_analytics", {})
            emotional_progressions = character_data.get("emotional_progressions", {})

            if character_name and character_name.lower() in ["diana", "lucien"]:
                # Filter data for specific character
                filtered_analytics = {
                    char: stats for char, stats in character_analytics.items()
                    if character_name.lower() in char.lower()
                }
                character_analytics = filtered_analytics

            export_data = {
                "metadata": {
                    "export_date": datetime.utcnow().isoformat(),
                    "character_filter": character_name,
                    "date_range": date_range,
                    "format": format,
                    "export_type": "character_analytics"
                },
                "character_analytics": character_analytics,
                "emotional_progressions": emotional_progressions,
                "insights": character_data.get("insights", {})
            }

            if format.lower() == "json":
                return json.dumps(export_data, indent=2, ensure_ascii=False)
            elif format.lower() == "csv":
                # Create CSV for character analytics
                character_csv = io.StringIO()
                character_writer = csv.writer(character_csv)

                # Character analytics CSV
                character_writer.writerow([
                    "character_name", "total_interactions", "unique_users",
                    "average_interactions_per_user", "engagement_score"
                ])

                for char_name, stats in character_analytics.items():
                    character_writer.writerow([
                        char_name,
                        stats.get("total_interactions", 0),
                        stats.get("unique_users", 0),
                        stats.get("average_interactions_per_user", 0),
                        stats.get("engagement_score", 0)
                    ])

                # Emotional progressions CSV
                emotions_csv = io.StringIO()
                emotions_writer = csv.writer(emotions_csv)

                emotions_writer.writerow([
                    "emotion", "occurrences", "average_intensity", "fragments_count"
                ])

                for emotion, data in emotional_progressions.items():
                    emotions_writer.writerow([
                        emotion,
                        data.get("occurrences", 0),
                        data.get("average_intensity", 0),
                        data.get("fragments", 0)
                    ])

                return {
                    "character_analytics.csv": character_csv.getvalue(),
                    "emotional_progressions.csv": emotions_csv.getvalue(),
                    "metadata": export_data["metadata"]
                }
            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            logger.error(f"Error exporting character analytics data: {e}")
            return {"status": "error", "message": str(e)}

    async def export_user_journey_data(self, date_range: Tuple[str, str] = None, format: str = "json") -> ExportData:
        """
        Export user journey analytics data.
        Implements requirement 4.1 - User Journey Export.
        """
        logger.info(f"Exporting user journey analytics in {format} format")

        try:
            if date_range:
                start_date = datetime.fromisoformat(date_range[0])
                end_date = datetime.fromisoformat(date_range[1])
            else:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)  # Default to last 30 days

            # Get user journey data
            journey_stmt = select(UserJourneyAnalytics).where(
                and_(
                    UserJourneyAnalytics.created_at >= start_date,
                    UserJourneyAnalytics.created_at <= end_date
                )
            )
            journey_result = await self.session.execute(journey_stmt)
            journey_analytics = journey_result.scalars().all()

            if not journey_analytics:
                return {"status": "error", "message": "No user journey data found for the specified period"}

            export_data = {
                "metadata": {
                    "export_date": datetime.utcnow().isoformat(),
                    "date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat()
                    },
                    "format": format,
                    "export_type": "user_journey",
                    "total_records": len(journey_analytics)
                }
            }

            if format.lower() == "json":
                export_data["user_journeys"] = [
                    {
                        "user_id": ja.user_id,
                        "fragments_visited": ja.fragments_visited,
                        "choices_made": ja.choices_made,
                        "progression_path": ja.progression_path,
                        "total_time_spent": ja.total_time_spent,
                        "session_count": ja.session_count,
                        "average_session_duration": ja.average_session_duration,
                        "backtrack_count": ja.backtrack_count,
                        "exploration_score": ja.exploration_score,
                        "engagement_level": ja.engagement_level,
                        "fragments_completed": ja.fragments_completed,
                        "narrative_completion_percentage": ja.narrative_completion_percentage,
                        "emotional_states": ja.emotional_states,
                        "character_interaction_count": ja.character_interaction_count,
                        "journey_started_at": ja.journey_started_at.isoformat(),
                        "last_activity_at": ja.last_activity_at.isoformat() if ja.last_activity_at else None
                    }
                    for ja in journey_analytics
                ]

                return json.dumps(export_data, indent=2, ensure_ascii=False)

            elif format.lower() == "csv":
                journey_csv = io.StringIO()
                journey_writer = csv.writer(journey_csv)

                # Write headers
                journey_writer.writerow([
                    "user_id", "fragments_visited", "choices_made", "total_time_spent",
                    "session_count", "average_session_duration", "backtrack_count",
                    "exploration_score", "engagement_level", "fragments_completed",
                    "narrative_completion_percentage", "journey_started_at", "last_activity_at"
                ])

                # Write data
                for ja in journey_analytics:
                    journey_writer.writerow([
                        ja.user_id, ja.fragments_visited, ja.choices_made, ja.total_time_spent,
                        ja.session_count, ja.average_session_duration, ja.backtrack_count,
                        ja.exploration_score, ja.engagement_level, ja.fragments_completed,
                        ja.narrative_completion_percentage,
                        ja.journey_started_at.isoformat(),
                        ja.last_activity_at.isoformat() if ja.last_activity_at else None
                    ])

                return {
                    "user_journey_analytics.csv": journey_csv.getvalue(),
                    "metadata": export_data["metadata"]
                }

            else:
                raise ValueError(f"Unsupported export format: {format}")

        except Exception as e:
            logger.error(f"Error exporting user journey data: {e}")
            return {"status": "error", "message": str(e)}

    def invalidate_cache_signal(self, data_type: str, identifier: Optional[str] = None):
        """
        Signal that cache should be invalidated for specific data types.
        This method is called when underlying data changes.
        
        Args:
            data_type: Type of data that changed ('fragment', 'user_segments', etc.)
            identifier: Specific identifier that changed (e.g., fragment key)
        """
        logger.info(f"Cache invalidation signal received for {data_type} {identifier or 'all'}")
        # This is a placeholder method that would be used by other services
        # to signal when data has changed and cache should be invalidated
        pass

    async def generate_comprehensive_report(self, report_type: str = "executive", date_range: Tuple[str, str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive analytics reports.
        Implements enhanced reporting capabilities for task 18.
        """
        logger.info(f"Generating {report_type} report")

        try:
            if date_range:
                start_date = datetime.fromisoformat(date_range[0])
                end_date = datetime.fromisoformat(date_range[1])
            else:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)

            # Get comprehensive analytics data
            dashboard_data = await self.get_comprehensive_dashboard_data()
            character_data = await self.get_character_voice_analytics()

            report = {
                "report_type": report_type,
                "generated_at": datetime.utcnow().isoformat(),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "status": "success"
            }

            if report_type == "executive":
                # Executive summary with key metrics
                report["executive_summary"] = {
                    "total_users": 0,
                    "engagement_highlights": [],
                    "character_performance": {},
                    "key_insights": [],
                    "recommendations": []
                }

                # Extract key metrics from dashboard data
                if dashboard_data.get("status") == "success":
                    user_segments = dashboard_data.get("user_segments", {})
                    if user_segments.get("status") == "success":
                        segment_counts = user_segments.get("segment_counts", {})
                        report["executive_summary"]["total_users"] = sum(segment_counts.values())

                    bottlenecks = dashboard_data.get("bottlenecks", {})
                    if bottlenecks.get("status") == "success":
                        recommendations = bottlenecks.get("recommendations", [])
                        report["executive_summary"]["recommendations"] = recommendations[:3]

                # Character performance summary
                if character_data.get("status") == "success":
                    insights = character_data.get("insights", {})
                    most_effective = insights.get("most_effective_character")
                    if most_effective:
                        report["executive_summary"]["character_performance"] = {
                            "most_effective": most_effective.get("name"),
                            "engagement_score": most_effective.get("engagement_score"),
                            "total_interactions": insights.get("total_tracked_interactions", 0)
                        }

            elif report_type == "detailed":
                # Detailed report with all metrics
                report["detailed_analytics"] = {
                    "dashboard_data": dashboard_data,
                    "character_analytics": character_data,
                    "export_capabilities": {
                        "formats_supported": ["JSON", "CSV", "Excel"],
                        "data_types": ["user_journey", "character_analytics", "fragments", "choices"],
                        "date_ranges": ["week", "month", "quarter", "custom"]
                    }
                }

            elif report_type == "kpis":
                # KPI-focused report
                report["kpis"] = {
                    "engagement_metrics": {},
                    "character_effectiveness": {},
                    "user_progression": {},
                    "content_performance": {}
                }

                # Extract KPIs from various sources
                if dashboard_data.get("status") == "success":
                    choice_patterns = dashboard_data.get("choice_patterns", {})
                    if choice_patterns.get("status") == "success":
                        summary = choice_patterns.get("summary", {})
                        report["kpis"]["engagement_metrics"] = {
                            "total_choices": summary.get("total_choices_made", 0),
                            "unique_choices": summary.get("unique_choices", 0),
                            "fragments_analyzed": summary.get("fragments_analyzed", 0)
                        }

            return report

        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {"status": "error", "message": str(e)}

    async def get_character_voice_analytics(self) -> Dict[str, Any]:
        """
        Monitor character response effectiveness and emotional progression analytics.
        Addresses requirement 4.3 - Character Voice and Emotional Intelligence Analytics.
        """
        logger.info("Getting character voice analytics")

        try:
            # Get user journey data with emotional states
            journey_stmt = select(UserJourneyAnalytics).where(
                UserJourneyAnalytics.emotional_states.isnot(None)
            )
            journey_result = await self.session.execute(journey_stmt)
            user_journeys = journey_result.scalars().all()

            if not user_journeys:
                return {
                    "status": "no_data",
                    "message": "No emotional progression data available"
                }

            # Analyze character interactions
            character_stats = {}
            emotional_progressions = {}
            total_interactions = 0

            for journey in user_journeys:
                # Character interaction analysis
                char_interactions = journey.character_interaction_count or {}
                for character, count in char_interactions.items():
                    if character not in character_stats:
                        character_stats[character] = {
                            "total_interactions": 0,
                            "unique_users": set(),
                            "average_interactions_per_user": 0
                        }
                    character_stats[character]["total_interactions"] += count
                    character_stats[character]["unique_users"].add(journey.user_id)
                    total_interactions += count

                # Emotional progression analysis
                emotional_states = journey.emotional_states or []
                for emotion_data in emotional_states:
                    if isinstance(emotion_data, dict):
                        emotion = emotion_data.get("emotion")
                        intensity = emotion_data.get("intensity", 0)
                        fragment = emotion_data.get("fragment")

                        if emotion not in emotional_progressions:
                            emotional_progressions[emotion] = {
                                "occurrences": 0,
                                "total_intensity": 0,
                                "average_intensity": 0,
                                "fragments": set()
                            }

                        emotional_progressions[emotion]["occurrences"] += 1
                        emotional_progressions[emotion]["total_intensity"] += intensity
                        if fragment:
                            emotional_progressions[emotion]["fragments"].add(fragment)

            # Calculate character effectiveness scores
            for character, stats in character_stats.items():
                unique_users_count = len(stats["unique_users"])
                if unique_users_count > 0:
                    stats["average_interactions_per_user"] = round(
                        stats["total_interactions"] / unique_users_count, 2
                    )
                    stats["engagement_score"] = min(100,
                        (stats["total_interactions"] / total_interactions * 100) if total_interactions > 0 else 0
                    )
                stats["unique_users"] = unique_users_count  # Convert set to count

            # Calculate emotional progression averages
            for emotion, data in emotional_progressions.items():
                if data["occurrences"] > 0:
                    data["average_intensity"] = round(
                        data["total_intensity"] / data["occurrences"], 2
                    )
                data["fragments"] = len(data["fragments"])  # Convert set to count

            # Find most effective character and dominant emotions
            most_effective_character = max(
                character_stats.items(),
                key=lambda x: x[1]["engagement_score"]
            ) if character_stats else None

            dominant_emotion = max(
                emotional_progressions.items(),
                key=lambda x: x[1]["occurrences"]
            ) if emotional_progressions else None

            return {
                "status": "success",
                "character_analytics": character_stats,
                "emotional_progressions": emotional_progressions,
                "insights": {
                    "most_effective_character": {
                        "name": most_effective_character[0],
                        "engagement_score": most_effective_character[1]["engagement_score"]
                    } if most_effective_character else None,
                    "dominant_emotion": {
                        "emotion": dominant_emotion[0],
                        "occurrences": dominant_emotion[1]["occurrences"],
                        "average_intensity": dominant_emotion[1]["average_intensity"]
                    } if dominant_emotion else None,
                    "total_tracked_interactions": total_interactions,
                    "emotions_tracked": len(emotional_progressions)
                },
                "generated_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting character voice analytics: {e}")
            return {"status": "error", "message": str(e)}

    async def get_comprehensive_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive analytics data for the admin dashboard.
        Combines all analytics components for a complete overview.
        """
        logger.info("Getting comprehensive dashboard data")

        try:
            # Run all analytics methods in parallel for efficiency
            results = await asyncio.gather(
                self.generate_user_segment_analysis(),
                self.analyze_choice_distribution_patterns(),
                self.identify_narrative_bottlenecks(),
                self.track_conversion_funnel_metrics(),
                self.get_character_voice_analytics(),
                return_exceptions=True
            )

            # Parse results
            user_segments, choice_patterns, bottlenecks, conversion_funnel, character_voice = results

            # Create summary statistics
            summary = {
                "last_updated": datetime.utcnow().isoformat(),
                "data_availability": {
                    "user_segments": user_segments.get("status") == "success" if isinstance(user_segments, dict) else False,
                    "choice_patterns": choice_patterns.get("status") == "success" if isinstance(choice_patterns, dict) else False,
                    "bottlenecks": bottlenecks.get("status") == "success" if isinstance(bottlenecks, dict) else False,
                    "conversion_funnel": conversion_funnel.get("status") == "success" if isinstance(conversion_funnel, dict) else False,
                    "character_voice": character_voice.get("status") == "success" if isinstance(character_voice, dict) else False
                }
            }

            return {
                "status": "success",
                "summary": summary,
                "user_segments": user_segments if not isinstance(user_segments, Exception) else {"status": "error", "message": str(user_segments)},
                "choice_patterns": choice_patterns if not isinstance(choice_patterns, Exception) else {"status": "error", "message": str(choice_patterns)},
                "bottlenecks": bottlenecks if not isinstance(bottlenecks, Exception) else {"status": "error", "message": str(bottlenecks)},
                "conversion_funnel": conversion_funnel if not isinstance(conversion_funnel, Exception) else {"status": "error", "message": str(conversion_funnel)},
                "character_voice": character_voice if not isinstance(character_voice, Exception) else {"status": "error", "message": str(character_voice)}
            }
        except Exception as e:
            logger.error(f"Error getting comprehensive dashboard data: {e}")
            return {"status": "error", "message": str(e)}
