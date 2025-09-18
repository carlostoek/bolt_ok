import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from database.models import Token, Tariff, VipSubscription, User, UserStats
from services.token_service import TokenService
from services.subscription_service import SubscriptionService
from utils.message_safety import safe_send_message

logger = logging.getLogger(__name__)


class EnhancedVIPService:
    """
    Service for enhanced VIP management, including batch operations and orchestration.
    """

    def __init__(self, session: AsyncSession, bot=None):
        self.session = session
        self.token_service = TokenService(session)
        self.subscription_service = SubscriptionService(session)
        self.bot = bot
        self._reminder_tracking: Set[Tuple[int, str]] = set()  # (user_id, reminder_type)
        self._automation_running = False

    async def generate_token(self, tariff_id: int, admin_id: int) -> Token:
        """
        Generates a single VIP token.

        Args:
            tariff_id: The ID of the tariff for the token.
            admin_id: The ID of the admin generating the token (for auditing).

        Returns:
            The generated Token object.
        """
        # Note: admin_id is for future audit log integration.
        # The current Token model does not store the creator.
        logger.info(f"Admin {admin_id} generating a VIP token for tariff {tariff_id}.")
        
        tariff = await self.session.get(Tariff, tariff_id)
        if not tariff:
            raise ValueError(f"Tariff with id {tariff_id} not found.")

        token = await self.token_service.create_vip_token(tariff_id=tariff_id)
        return token

    async def generate_batch_tokens(self, tariff_id: int, admin_id: int, count: int) -> List[Token]:
        """
        Generates a batch of VIP tokens.

        Args:
            tariff_id: The ID of the tariff for the tokens.
            admin_id: The ID of the admin generating the tokens.
            count: The number of tokens to generate.

        Returns:
            A list of generated Token objects.
        """
        if not 1 <= count <= 50:
            raise ValueError("Batch size must be between 1 and 50.")

        tariff = await self.session.get(Tariff, tariff_id)
        if not tariff:
            raise ValueError(f"Tariff with id {tariff_id} not found.")

        logger.info(f"Admin {admin_id} generating a batch of {count} VIP tokens for tariff {tariff_id}.")

        tokens = []
        for _ in range(count):
            token = await self.token_service.create_vip_token(tariff_id=tariff_id)
            tokens.append(token)
        
        return tokens

    async def redeem_token(self, token_string: str, user_id: int) -> VipSubscription:
        """
        Redeems a VIP token to grant or extend a subscription.

        Args:
            token_string: The VIP token string.
            user_id: The ID of the user redeeming the token.

        Returns:
            The user's updated VipSubscription object.
        
        Raises:
            ValueError: If the token is invalid or the associated tariff is not found.
        """
        logger.info(f"User {user_id} attempting to redeem VIP token {token_string[:8]}...")

        try:
            # 1. Activate the token and get the duration
            duration_days = await self.token_service.activate_token(token_string, user_id)
            
            # 2. Extend the user's subscription
            subscription = await self.subscription_service.extend_subscription(user_id, duration_days)
            
            logger.info(f"Successfully redeemed token {token_string[:8]} for user {user_id}. Subscription extended by {duration_days} days.")
            
            return subscription
        except ValueError as e:
            logger.warning(f"Failed to redeem token for user {user_id}: {e}")
            raise e

    async def calculate_revenue_metrics(self, date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """
        Calculate revenue metrics from used tokens with projections.

        Args:
            date_range: Optional tuple of (start_date, end_date) for filtering

        Returns:
            Dictionary containing revenue metrics and projections
        """
        logger.info("Calculating VIP revenue metrics")

        try:
            # Set default date range to last 30 days if not provided
            if not date_range:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
            else:
                start_date, end_date = date_range

            # Calculate total revenue from used tokens
            total_revenue_stmt = (
                select(func.sum(Tariff.price))
                .select_from(Token)
                .join(Tariff, Token.tariff_id == Tariff.id)
                .where(Token.is_used.is_(True))
            )
            total_revenue_result = await self.session.execute(total_revenue_stmt)
            total_revenue = total_revenue_result.scalar() or 0

            # Calculate revenue in date range
            period_revenue_stmt = (
                select(func.sum(Tariff.price))
                .select_from(Token)
                .join(Tariff, Token.tariff_id == Tariff.id)
                .where(
                    and_(
                        Token.is_used.is_(True),
                        Token.activated_at >= start_date,
                        Token.activated_at <= end_date
                    )
                )
            )
            period_revenue_result = await self.session.execute(period_revenue_stmt)
            period_revenue = period_revenue_result.scalar() or 0

            # Calculate average revenue per token
            avg_revenue_stmt = (
                select(func.avg(Tariff.price))
                .select_from(Token)
                .join(Tariff, Token.tariff_id == Tariff.id)
                .where(Token.is_used.is_(True))
            )
            avg_revenue_result = await self.session.execute(avg_revenue_stmt)
            avg_revenue_per_token = avg_revenue_result.scalar() or 0

            # Count total tokens generated vs used
            total_tokens_stmt = select(func.count(Token.id))
            total_tokens_result = await self.session.execute(total_tokens_stmt)
            total_tokens = total_tokens_result.scalar() or 0

            used_tokens_stmt = select(func.count(Token.id)).where(Token.is_used.is_(True))
            used_tokens_result = await self.session.execute(used_tokens_stmt)
            used_tokens = used_tokens_result.scalar() or 0

            # Calculate conversion rate
            conversion_rate = (used_tokens / total_tokens * 100) if total_tokens > 0 else 0

            # Revenue by tariff breakdown
            revenue_by_tariff_stmt = (
                select(Tariff.name, Tariff.price, func.count(Token.id).label('tokens_used'),
                       func.sum(Tariff.price).label('tariff_revenue'))
                .select_from(Token)
                .join(Tariff, Token.tariff_id == Tariff.id)
                .where(Token.is_used.is_(True))
                .group_by(Tariff.id, Tariff.name, Tariff.price)
                .order_by(desc('tariff_revenue'))
            )
            revenue_by_tariff_result = await self.session.execute(revenue_by_tariff_stmt)
            revenue_by_tariff = [
                {
                    "tariff_name": row.name,
                    "price": row.price,
                    "tokens_used": row.tokens_used,
                    "total_revenue": row.tariff_revenue
                }
                for row in revenue_by_tariff_result
            ]

            # Calculate monthly projection based on period data
            days_in_period = (end_date - start_date).days or 1
            monthly_projection = (period_revenue / days_in_period) * 30 if period_revenue > 0 else 0

            # Unused tokens value (potential revenue)
            unused_tokens_stmt = (
                select(func.sum(Tariff.price))
                .select_from(Token)
                .join(Tariff, Token.tariff_id == Tariff.id)
                .where(Token.is_used.is_(False))
            )
            unused_tokens_result = await self.session.execute(unused_tokens_stmt)
            potential_revenue = unused_tokens_result.scalar() or 0

            return {
                "status": "success",
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days_in_period
                },
                "revenue_metrics": {
                    "total_revenue": total_revenue,
                    "period_revenue": period_revenue,
                    "average_revenue_per_token": round(float(avg_revenue_per_token), 2),
                    "monthly_projection": round(monthly_projection, 2),
                    "potential_revenue": potential_revenue
                },
                "token_metrics": {
                    "total_tokens_generated": total_tokens,
                    "tokens_used": used_tokens,
                    "tokens_unused": total_tokens - used_tokens,
                    "conversion_rate": round(conversion_rate, 2)
                },
                "revenue_breakdown": revenue_by_tariff,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error calculating revenue metrics: {e}")
            return {"status": "error", "message": str(e)}

    async def get_subscription_trends(self, date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """
        Analyze subscription patterns and trends over time.

        Args:
            date_range: Optional tuple of (start_date, end_date) for filtering

        Returns:
            Dictionary containing subscription trend analysis
        """
        logger.info("Analyzing VIP subscription trends")

        try:
            # Set default date range to last 90 days if not provided
            if not date_range:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=90)
            else:
                start_date, end_date = date_range

            # Get current subscription statistics
            total_subs, active_subs, expired_subs = await self.subscription_service.get_statistics()

            # Subscription creation trends (new subscriptions over time)
            new_subs_stmt = (
                select(
                    func.date(VipSubscription.created_at).label('date'),
                    func.count(VipSubscription.user_id).label('new_subscriptions')
                )
                .where(
                    and_(
                        VipSubscription.created_at >= start_date,
                        VipSubscription.created_at <= end_date
                    )
                )
                .group_by(func.date(VipSubscription.created_at))
                .order_by('date')
            )
            new_subs_result = await self.session.execute(new_subs_stmt)
            new_subscriptions_trend = [
                {
                    "date": row.date.isoformat(),
                    "new_subscriptions": row.new_subscriptions
                }
                for row in new_subs_result
            ]

            # Subscription expiration trends
            now = datetime.utcnow()

            # Expiring soon (within 7 days)
            expiring_soon_stmt = (
                select(func.count(VipSubscription.user_id))
                .where(
                    and_(
                        VipSubscription.expires_at.is_not(None),
                        VipSubscription.expires_at > now,
                        VipSubscription.expires_at <= now + timedelta(days=7)
                    )
                )
            )
            expiring_soon_result = await self.session.execute(expiring_soon_stmt)
            expiring_soon = expiring_soon_result.scalar() or 0

            # Expiring this month
            expiring_month_stmt = (
                select(func.count(VipSubscription.user_id))
                .where(
                    and_(
                        VipSubscription.expires_at.is_not(None),
                        VipSubscription.expires_at > now,
                        VipSubscription.expires_at <= now + timedelta(days=30)
                    )
                )
            )
            expiring_month_result = await self.session.execute(expiring_month_stmt)
            expiring_month = expiring_month_result.scalar() or 0

            # Renewal patterns - users who have extended subscriptions
            renewal_stmt = (
                select(
                    func.count(Token.user_id).label('renewals'),
                    func.count(func.distinct(Token.user_id)).label('unique_renewers')
                )
                .where(
                    and_(
                        Token.is_used.is_(True),
                        Token.activated_at >= start_date,
                        Token.activated_at <= end_date,
                        Token.user_id.in_(
                            select(VipSubscription.user_id)
                            .where(VipSubscription.created_at < Token.activated_at)
                        )
                    )
                )
            )
            renewal_result = await self.session.execute(renewal_stmt)
            renewal_data = renewal_result.first()
            renewals = renewal_data.renewals if renewal_data else 0
            unique_renewers = renewal_data.unique_renewers if renewal_data else 0

            # Average subscription duration from used tokens
            avg_duration_stmt = (
                select(func.avg(Tariff.duration_days))
                .select_from(Token)
                .join(Tariff, Token.tariff_id == Tariff.id)
                .where(
                    and_(
                        Token.is_used.is_(True),
                        Token.activated_at >= start_date,
                        Token.activated_at <= end_date
                    )
                )
            )
            avg_duration_result = await self.session.execute(avg_duration_stmt)
            avg_subscription_duration = avg_duration_result.scalar() or 0

            # User lifecycle analysis
            lifecycle_stmt = (
                select(
                    User.id,
                    User.created_at,
                    VipSubscription.created_at.label('first_vip'),
                    VipSubscription.expires_at,
                    func.count(Token.id).label('tokens_used')
                )
                .select_from(User)
                .outerjoin(VipSubscription, User.id == VipSubscription.user_id)
                .outerjoin(Token, User.id == Token.user_id)
                .where(VipSubscription.user_id.is_not(None))
                .group_by(User.id, User.created_at, VipSubscription.created_at, VipSubscription.expires_at)
                .limit(100)  # Sample for performance
            )
            lifecycle_result = await self.session.execute(lifecycle_stmt)

            # Calculate time to VIP conversion and renewal rates
            conversion_times = []
            renewal_counts = []

            for row in lifecycle_result:
                if row.first_vip and row.created_at:
                    time_to_vip = (row.first_vip - row.created_at).days
                    conversion_times.append(time_to_vip)
                renewal_counts.append(row.tokens_used or 0)

            avg_time_to_conversion = sum(conversion_times) / len(conversion_times) if conversion_times else 0
            avg_renewals_per_user = sum(renewal_counts) / len(renewal_counts) if renewal_counts else 0

            # Calculate retention rate
            retention_rate = (unique_renewers / active_subs * 100) if active_subs > 0 else 0

            return {
                "status": "success",
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": (end_date - start_date).days
                },
                "current_metrics": {
                    "total_subscriptions": total_subs,
                    "active_subscriptions": active_subs,
                    "expired_subscriptions": expired_subs,
                    "expiring_soon_7_days": expiring_soon,
                    "expiring_this_month": expiring_month
                },
                "trend_analysis": {
                    "new_subscriptions_daily": new_subscriptions_trend,
                    "total_renewals": renewals,
                    "unique_renewers": unique_renewers,
                    "retention_rate": round(retention_rate, 2),
                    "average_subscription_duration_days": round(float(avg_subscription_duration), 1)
                },
                "user_behavior": {
                    "average_time_to_vip_conversion_days": round(avg_time_to_conversion, 1),
                    "average_renewals_per_user": round(avg_renewals_per_user, 2)
                },
                "insights": {
                    "churn_risk": "high" if expiring_soon > active_subs * 0.2 else "low",
                    "growth_trend": "positive" if len(new_subscriptions_trend) > 0 and
                                  sum(d["new_subscriptions"] for d in new_subscriptions_trend[-7:]) >
                                  sum(d["new_subscriptions"] for d in new_subscriptions_trend[:7]) else "stable"
                },
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing subscription trends: {e}")
            return {"status": "error", "message": str(e)}

    async def get_user_engagement_stats(self, date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """
        Track user engagement and activity metrics for VIP users.

        Args:
            date_range: Optional tuple of (start_date, end_date) for filtering

        Returns:
            Dictionary containing user engagement statistics
        """
        logger.info("Analyzing VIP user engagement statistics")

        try:
            # Set default date range to last 30 days if not provided
            if not date_range:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
            else:
                start_date, end_date = date_range

            # Get VIP users and their stats
            vip_users_stmt = (
                select(User, UserStats, VipSubscription)
                .outerjoin(UserStats, User.id == UserStats.user_id)
                .join(VipSubscription, User.id == VipSubscription.user_id)
                .where(
                    or_(
                        VipSubscription.expires_at.is_(None),
                        VipSubscription.expires_at > datetime.utcnow()
                    )
                )
            )
            vip_users_result = await self.session.execute(vip_users_stmt)
            vip_users_data = vip_users_result.all()

            if not vip_users_data:
                return {
                    "status": "no_data",
                    "message": "No active VIP users found"
                }

            # Analyze engagement metrics
            total_vip_users = len(vip_users_data)
            active_users = 0
            total_messages = 0
            total_points = 0
            checkin_streaks = []
            last_activity_times = []

            engagement_levels = {
                "highly_engaged": 0,  # Active in last 3 days
                "moderately_engaged": 0,  # Active in last 7 days
                "low_engagement": 0,  # Active in last 30 days
                "inactive": 0  # No activity in 30+ days
            }

            now = datetime.utcnow()

            for user, user_stats, vip_sub in vip_users_data:
                # Count points
                total_points += user.points or 0

                if user_stats:
                    # Count messages
                    total_messages += user_stats.messages_sent or 0

                    # Analyze checkin streaks
                    if user_stats.checkin_streak:
                        checkin_streaks.append(user_stats.checkin_streak)

                    # Analyze last activity
                    last_activity = user_stats.last_activity_at
                    if last_activity:
                        last_activity_times.append(last_activity)
                        days_inactive = (now - last_activity).days

                        if days_inactive <= 3:
                            engagement_levels["highly_engaged"] += 1
                            active_users += 1
                        elif days_inactive <= 7:
                            engagement_levels["moderately_engaged"] += 1
                            active_users += 1
                        elif days_inactive <= 30:
                            engagement_levels["low_engagement"] += 1
                        else:
                            engagement_levels["inactive"] += 1
                    else:
                        engagement_levels["inactive"] += 1
                else:
                    engagement_levels["inactive"] += 1

            # Calculate averages
            avg_points = total_points / total_vip_users if total_vip_users > 0 else 0
            avg_messages = total_messages / total_vip_users if total_vip_users > 0 else 0
            avg_checkin_streak = sum(checkin_streaks) / len(checkin_streaks) if checkin_streaks else 0

            # Engagement rate
            engagement_rate = (active_users / total_vip_users * 100) if total_vip_users > 0 else 0

            # Activity distribution by time periods
            recent_activity = {
                "last_24h": 0,
                "last_week": 0,
                "last_month": 0
            }

            for activity_time in last_activity_times:
                hours_since = (now - activity_time).total_seconds() / 3600
                if hours_since <= 24:
                    recent_activity["last_24h"] += 1
                if hours_since <= 168:  # 7 days
                    recent_activity["last_week"] += 1
                if hours_since <= 720:  # 30 days
                    recent_activity["last_month"] += 1

            # VIP vs Free user comparison (sample)
            free_users_sample_stmt = (
                select(User, UserStats)
                .outerjoin(UserStats, User.id == UserStats.user_id)
                .outerjoin(VipSubscription, User.id == VipSubscription.user_id)
                .where(
                    or_(
                        VipSubscription.user_id.is_(None),
                        and_(
                            VipSubscription.expires_at.is_not(None),
                            VipSubscription.expires_at <= datetime.utcnow()
                        )
                    )
                )
                .limit(total_vip_users)  # Sample same size for comparison
            )
            free_users_result = await self.session.execute(free_users_sample_stmt)
            free_users_data = free_users_result.all()

            # Calculate free user averages for comparison
            free_total_points = sum(user.points or 0 for user, _ in free_users_data)
            free_total_messages = sum(stats.messages_sent or 0 for _, stats in free_users_data if stats)
            free_avg_points = free_total_points / len(free_users_data) if free_users_data else 0
            free_avg_messages = free_total_messages / len(free_users_data) if free_users_data else 0

            # Token usage analysis for VIP users
            token_usage_stmt = (
                select(
                    func.count(Token.id).label('tokens_used'),
                    func.count(func.distinct(Token.user_id)).label('users_with_tokens')
                )
                .where(
                    and_(
                        Token.is_used.is_(True),
                        Token.activated_at >= start_date,
                        Token.activated_at <= end_date,
                        Token.user_id.in_([user.id for user, _, _ in vip_users_data])
                    )
                )
            )
            token_usage_result = await self.session.execute(token_usage_stmt)
            token_data = token_usage_result.first()
            tokens_used = token_data.tokens_used if token_data else 0
            users_with_tokens = token_data.users_with_tokens if token_data else 0

            return {
                "status": "success",
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": (end_date - start_date).days
                },
                "vip_user_metrics": {
                    "total_vip_users": total_vip_users,
                    "active_users": active_users,
                    "engagement_rate": round(engagement_rate, 2),
                    "average_points": round(avg_points, 2),
                    "average_messages_sent": round(avg_messages, 2),
                    "average_checkin_streak": round(avg_checkin_streak, 1)
                },
                "engagement_distribution": {
                    "highly_engaged": engagement_levels["highly_engaged"],
                    "moderately_engaged": engagement_levels["moderately_engaged"],
                    "low_engagement": engagement_levels["low_engagement"],
                    "inactive": engagement_levels["inactive"]
                },
                "activity_breakdown": recent_activity,
                "vip_vs_free_comparison": {
                    "vip_avg_points": round(avg_points, 2),
                    "free_avg_points": round(free_avg_points, 2),
                    "points_multiplier": round(avg_points / free_avg_points, 2) if free_avg_points > 0 else 0,
                    "vip_avg_messages": round(avg_messages, 2),
                    "free_avg_messages": round(free_avg_messages, 2),
                    "message_multiplier": round(avg_messages / free_avg_messages, 2) if free_avg_messages > 0 else 0
                },
                "token_engagement": {
                    "tokens_used_in_period": tokens_used,
                    "users_with_token_activity": users_with_tokens,
                    "token_usage_rate": round((users_with_tokens / total_vip_users * 100), 2) if total_vip_users > 0 else 0
                },
                "insights": {
                    "engagement_health": "excellent" if engagement_rate > 70 else "good" if engagement_rate > 50 else "needs_attention",
                    "most_common_engagement_level": max(engagement_levels.items(), key=lambda x: x[1])[0],
                    "vip_value_indicator": "high" if avg_points > free_avg_points * 2 else "moderate"
                },
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing user engagement stats: {e}")
            return {"status": "error", "message": str(e)}

    async def schedule_vip_reminders(self, days_before: List[int] = [3, 1]) -> Dict[str, Any]:
        """
        Schedule reminder notifications for expiring VIP subscriptions.

        Args:
            days_before: List of days before expiration to send reminders

        Returns:
            Dictionary with scheduling results
        """
        logger.info(f"Scheduling VIP reminders for {days_before} days before expiration")

        try:
            if self._automation_running:
                return {"status": "already_running", "message": "VIP automation is already running"}

            self._automation_running = True

            now = datetime.utcnow()
            scheduled_count = 0

            for days in days_before:
                # Find subscriptions expiring in the specified number of days
                target_date = now + timedelta(days=days)
                date_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
                date_end = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

                expiring_subs_stmt = (
                    select(VipSubscription, User)
                    .join(User, VipSubscription.user_id == User.id)
                    .where(
                        and_(
                            VipSubscription.expires_at.is_not(None),
                            VipSubscription.expires_at >= date_start,
                            VipSubscription.expires_at <= date_end
                        )
                    )
                )

                result = await self.session.execute(expiring_subs_stmt)
                expiring_subscriptions = result.all()

                for vip_sub, user in expiring_subscriptions:
                    reminder_key = (user.id, f"{days}_day_warning")

                    # Check if reminder already sent
                    if reminder_key not in self._reminder_tracking:
                        # Schedule the reminder
                        delay_seconds = max(0, (target_date - now).total_seconds())
                        asyncio.create_task(
                            self._delayed_reminder(user.id, days, delay_seconds)
                        )
                        self._reminder_tracking.add(reminder_key)
                        scheduled_count += 1

                        logger.info(f"Scheduled {days}-day reminder for user {user.id} (expires: {vip_sub.expires_at})")

            return {
                "status": "success",
                "scheduled_reminders": scheduled_count,
                "days_before": days_before,
                "scheduled_at": now.isoformat()
            }

        except Exception as e:
            logger.error(f"Error scheduling VIP reminders: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            self._automation_running = False

    async def _delayed_reminder(self, user_id: int, days_before: int, delay_seconds: float):
        """
        Internal method to send a delayed reminder with retry logic.

        Args:
            user_id: ID of the user to remind
            days_before: Number of days before expiration
            delay_seconds: Seconds to wait before sending
        """
        try:
            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)

            # Send the reminder with retry logic
            for attempt in range(3):
                try:
                    await self.send_expiration_warning(user_id, days_before)
                    logger.info(f"Successfully sent {days_before}-day reminder to user {user_id}")
                    break
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed for user {user_id} reminder: {e}")
                    if attempt == 2:  # Last attempt
                        logger.error(f"Failed to send reminder to user {user_id} after 3 attempts")
                        # TODO: Alert administrator about failed reminder
                    else:
                        await asyncio.sleep(5 * (attempt + 1))  # Exponential backoff

        except Exception as e:
            logger.error(f"Critical error in delayed reminder for user {user_id}: {e}")

    async def send_expiration_warning(self, user_id: int, days_before: int) -> bool:
        """
        Send personalized expiration warning message to a user.

        Args:
            user_id: ID of the user to notify
            days_before: Number of days before expiration

        Returns:
            True if message sent successfully, False otherwise
        """
        logger.info(f"Sending {days_before}-day expiration warning to user {user_id}")

        try:
            if not self.bot:
                logger.error("Bot instance not available for sending messages")
                return False

            # Get user subscription details
            user_stmt = (
                select(User, VipSubscription)
                .outerjoin(VipSubscription, User.id == VipSubscription.user_id)
                .where(User.id == user_id)
            )
            result = await self.session.execute(user_stmt)
            user_data = result.first()

            if not user_data or not user_data.VipSubscription:
                logger.warning(f"No VIP subscription found for user {user_id}")
                return False

            user, vip_sub = user_data

            # Create personalized message
            if days_before == 1:
                message = (
                    f"⚠️ ¡Atención {user.username or 'Usuario'}!\n\n"
                    f"Tu suscripción VIP expira MAÑANA ({vip_sub.expires_at.strftime('%d/%m/%Y')}).\n\n"
                    f"💎 No pierdas tus beneficios VIP:\n"
                    f"• Acceso a contenido exclusivo\n"
                    f"• Puntos adicionales\n"
                    f"• Funciones premium\n\n"
                    f"🔄 Renueva ahora para continuar disfrutando de todos los beneficios."
                )
            elif days_before == 3:
                message = (
                    f"📅 Hola {user.username or 'Usuario'},\n\n"
                    f"Tu suscripción VIP expira en {days_before} días ({vip_sub.expires_at.strftime('%d/%m/%Y')}).\n\n"
                    f"🌟 Recuerda renovar tu suscripción para seguir disfrutando de:\n"
                    f"• Contenido exclusivo premium\n"
                    f"• Beneficios especiales\n"
                    f"• Acceso prioritario\n\n"
                    f"💡 Tip: Renueva antes de que expire para no perder tu progreso."
                )
            else:
                message = (
                    f"🔔 Recordatorio VIP para {user.username or 'Usuario'}\n\n"
                    f"Tu suscripción expira en {days_before} días ({vip_sub.expires_at.strftime('%d/%m/%Y')}).\n\n"
                    f"¡No olvides renovar para mantener tus beneficios VIP!"
                )

            # Send the message using safe_send_message
            await safe_send_message(self.bot, user_id, message)

            logger.info(f"Expiration warning sent successfully to user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending expiration warning to user {user_id}: {e}")
            return False

    async def process_auto_renewals(self, auto_renewal_enabled: bool = False) -> Dict[str, Any]:
        """
        Process automatic renewals for eligible subscriptions.

        Args:
            auto_renewal_enabled: Whether automatic renewals are enabled (future feature)

        Returns:
            Dictionary with renewal processing results
        """
        logger.info("Processing VIP auto-renewals")

        try:
            now = datetime.utcnow()
            processed_count = 0
            failed_count = 0

            if not auto_renewal_enabled:
                logger.info("Auto-renewal is disabled, skipping processing")
                return {
                    "status": "disabled",
                    "message": "Auto-renewal feature is not enabled",
                    "processed_count": 0
                }

            # Find expired subscriptions (for future auto-renewal implementation)
            expired_subs_stmt = (
                select(VipSubscription, User)
                .join(User, VipSubscription.user_id == User.id)
                .where(
                    and_(
                        VipSubscription.expires_at.is_not(None),
                        VipSubscription.expires_at <= now,
                        VipSubscription.expires_at >= now - timedelta(hours=1)  # Within last hour
                    )
                )
            )

            result = await self.session.execute(expired_subs_stmt)
            expired_subscriptions = result.all()

            for vip_sub, user in expired_subscriptions:
                try:
                    # TODO: Implement auto-renewal logic here
                    # This would typically involve:
                    # 1. Check if user has auto-renewal enabled
                    # 2. Check payment method availability
                    # 3. Process payment
                    # 4. Extend subscription

                    logger.info(f"Auto-renewal processing for user {user.id} (expired: {vip_sub.expires_at})")

                    # For now, just log and notify about expiration
                    await self._notify_subscription_expired(user.id)
                    processed_count += 1

                except Exception as e:
                    logger.error(f"Failed to process auto-renewal for user {user.id}: {e}")
                    failed_count += 1

            return {
                "status": "success",
                "processed_count": processed_count,
                "failed_count": failed_count,
                "total_expired": len(expired_subscriptions),
                "processed_at": now.isoformat()
            }

        except Exception as e:
            logger.error(f"Error processing auto-renewals: {e}")
            return {"status": "error", "message": str(e)}

    async def _notify_subscription_expired(self, user_id: int):
        """
        Notify user that their subscription has expired.

        Args:
            user_id: ID of the user to notify
        """
        try:
            if not self.bot:
                return

            user = await self.session.get(User, user_id)
            if not user:
                return

            message = (
                f"⏰ Hola {user.username or 'Usuario'},\n\n"
                f"Tu suscripción VIP ha expirado.\n\n"
                f"💎 Renueva ahora para recuperar:\n"
                f"• Acceso a contenido exclusivo\n"
                f"• Beneficios premium\n"
                f"• Funciones especiales\n\n"
                f"¡Esperamos verte de vuelta pronto!"
            )

            await safe_send_message(self.bot, user_id, message)
            logger.info(f"Expiration notification sent to user {user_id}")

        except Exception as e:
            logger.error(f"Error notifying user {user_id} about expiration: {e}")

    async def start_reminder_automation(self, check_interval_minutes: int = 60) -> Dict[str, Any]:
        """
        Start the continuous VIP reminder automation process.

        Args:
            check_interval_minutes: How often to check for expiring subscriptions

        Returns:
            Dictionary with automation start results
        """
        logger.info(f"Starting VIP reminder automation with {check_interval_minutes}-minute intervals")

        try:
            if self._automation_running:
                return {"status": "already_running", "message": "Automation is already active"}

            # Start the background automation task
            asyncio.create_task(self._automation_loop(check_interval_minutes))

            return {
                "status": "started",
                "check_interval_minutes": check_interval_minutes,
                "started_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error starting reminder automation: {e}")
            return {"status": "error", "message": str(e)}

    async def _automation_loop(self, check_interval_minutes: int):
        """
        Continuous loop for checking and scheduling reminders.

        Args:
            check_interval_minutes: Minutes between checks
        """
        self._automation_running = True
        logger.info("VIP reminder automation loop started")

        try:
            while self._automation_running:
                try:
                    # Schedule reminders for upcoming expirations
                    await self.schedule_vip_reminders([3, 1])

                    # Process auto-renewals (if enabled in future)
                    await self.process_auto_renewals(auto_renewal_enabled=False)

                    # Wait for next check
                    await asyncio.sleep(check_interval_minutes * 60)

                except Exception as e:
                    logger.error(f"Error in automation loop iteration: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute before retrying

        except asyncio.CancelledError:
            logger.info("VIP reminder automation loop cancelled")
        except Exception as e:
            logger.error(f"Critical error in automation loop: {e}")
        finally:
            self._automation_running = False
            logger.info("VIP reminder automation loop stopped")

    async def stop_reminder_automation(self) -> Dict[str, Any]:
        """
        Stop the VIP reminder automation process.

        Returns:
            Dictionary with stop results
        """
        logger.info("Stopping VIP reminder automation")

        try:
            if not self._automation_running:
                return {"status": "not_running", "message": "Automation is not currently active"}

            self._automation_running = False

            return {
                "status": "stopped",
                "stopped_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error stopping reminder automation: {e}")
            return {"status": "error", "message": str(e)}

    async def get_reminder_status(self) -> Dict[str, Any]:
        """
        Get the current status of the reminder automation system.

        Returns:
            Dictionary with current automation status
        """
        try:
            return {
                "status": "running" if self._automation_running else "stopped",
                "tracked_reminders": len(self._reminder_tracking),
                "automation_active": self._automation_running,
                "checked_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting reminder status: {e}")
            return {"status": "error", "message": str(e)}

    async def get_vip_analytics(self, date_range: Optional[Tuple[datetime, datetime]] = None,
                              metrics_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Get comprehensive VIP analytics combining all metrics.

        Args:
            date_range: Optional tuple of (start_date, end_date) for filtering
            metrics_type: Type of metrics to return ('revenue', 'subscriptions', 'engagement', 'comprehensive')

        Returns:
            Dictionary containing requested VIP analytics
        """
        logger.info(f"Getting VIP analytics - type: {metrics_type}")

        try:
            # Set default date range if not provided
            if not date_range:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
            else:
                start_date, end_date = date_range

            analytics_data = {
                "status": "success",
                "analytics_type": metrics_type,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": (end_date - start_date).days
                },
                "generated_at": datetime.utcnow().isoformat()
            }

            if metrics_type in ["revenue", "comprehensive"]:
                revenue_metrics = await self.calculate_revenue_metrics(date_range)
                analytics_data["revenue_analytics"] = revenue_metrics

            if metrics_type in ["subscriptions", "comprehensive"]:
                subscription_trends = await self.get_subscription_trends(date_range)
                analytics_data["subscription_analytics"] = subscription_trends

            if metrics_type in ["engagement", "comprehensive"]:
                engagement_stats = await self.get_user_engagement_stats(date_range)
                analytics_data["engagement_analytics"] = engagement_stats

            # Add summary insights for comprehensive analytics
            if metrics_type == "comprehensive":
                analytics_data["summary_insights"] = self._generate_analytics_summary(
                    analytics_data.get("revenue_analytics", {}),
                    analytics_data.get("subscription_analytics", {}),
                    analytics_data.get("engagement_analytics", {})
                )

            return analytics_data

        except Exception as e:
            logger.error(f"Error getting VIP analytics: {e}")
            return {"status": "error", "message": str(e)}

    def _generate_analytics_summary(self, revenue_data: Dict, subscription_data: Dict,
                                  engagement_data: Dict) -> Dict[str, Any]:
        """
        Generate summary insights from all analytics data.
        """
        insights = {
            "overall_health": "good",
            "key_metrics": {},
            "recommendations": [],
            "alerts": []
        }

        try:
            # Revenue insights
            if revenue_data.get("status") == "success":
                revenue_metrics = revenue_data.get("revenue_metrics", {})
                conversion_rate = revenue_data.get("token_metrics", {}).get("conversion_rate", 0)

                insights["key_metrics"]["total_revenue"] = revenue_metrics.get("total_revenue", 0)
                insights["key_metrics"]["conversion_rate"] = conversion_rate

                if conversion_rate < 50:
                    insights["recommendations"].append("Consider improving token marketing or pricing strategy")
                    insights["alerts"].append("Low token conversion rate detected")

            # Subscription insights
            if subscription_data.get("status") == "success":
                current_metrics = subscription_data.get("current_metrics", {})
                trend_analysis = subscription_data.get("trend_analysis", {})

                insights["key_metrics"]["active_subscriptions"] = current_metrics.get("active_subscriptions", 0)
                insights["key_metrics"]["retention_rate"] = trend_analysis.get("retention_rate", 0)

                churn_risk = subscription_data.get("insights", {}).get("churn_risk", "low")
                if churn_risk == "high":
                    insights["alerts"].append("High churn risk - many subscriptions expiring soon")
                    insights["recommendations"].append("Implement retention campaigns for expiring users")

            # Engagement insights
            if engagement_data.get("status") == "success":
                vip_metrics = engagement_data.get("vip_user_metrics", {})
                engagement_health = engagement_data.get("insights", {}).get("engagement_health", "good")

                insights["key_metrics"]["engagement_rate"] = vip_metrics.get("engagement_rate", 0)
                insights["key_metrics"]["total_vip_users"] = vip_metrics.get("total_vip_users", 0)

                if engagement_health == "needs_attention":
                    insights["alerts"].append("VIP user engagement below optimal levels")
                    insights["recommendations"].append("Consider VIP-exclusive content or events")

            # Overall health assessment
            alert_count = len(insights["alerts"])
            if alert_count == 0:
                insights["overall_health"] = "excellent"
            elif alert_count <= 2:
                insights["overall_health"] = "good"
            else:
                insights["overall_health"] = "needs_attention"

        except Exception as e:
            logger.warning(f"Error generating analytics summary: {e}")
            insights["summary_error"] = str(e)

        return insights
