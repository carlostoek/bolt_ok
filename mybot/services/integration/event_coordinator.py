"""
Event Coordinator for setting up cross-module event subscriptions.
Enhances module coordination by establishing event-driven communication patterns.
"""
import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from services.event_bus import get_event_bus, EventType, Event
from services.point_service import PointService
from services.badge_service import BadgeService
from services.user_service import UserService
from services.reconciliation_service import ReconciliationService

logger = logging.getLogger(__name__)

class EventCoordinator:
    """
    Coordinates event subscriptions across modules to improve integration.
    
    This service maintains architectural coherence by:
    - Setting up non-intrusive event listeners that don't break existing flows
    - Using the established service layer patterns
    - Providing loose coupling between modules through events
    - Following the same async/await patterns as existing services
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the event coordinator.
        
        Args:
            session: Database session for services that will handle events
        """
        self.session = session
        self.event_bus = get_event_bus()
        
        # Initialize services that will respond to events
        self.point_service = PointService(session)
        self.badge_service = BadgeService(session)
        self.user_service = UserService(session)
        self.reconciliation_service = ReconciliationService(session)
        
        # Track if subscriptions have been set up
        self._subscriptions_active = False
    
    async def setup_cross_module_subscriptions(self) -> Dict[str, int]:
        """
        Set up event subscriptions that enable better coordination between modules.
        
        Returns:
            Dict[str, int]: Summary of subscriptions set up by event type
        """
        if self._subscriptions_active:
            logger.warning("Event subscriptions already active")
            return {}
        
        subscription_count = {}
        
        try:
            # 1. Points and Achievement Integration
            self.event_bus.subscribe(EventType.POINTS_AWARDED, self._handle_points_awarded)
            subscription_count[EventType.POINTS_AWARDED.value] = 1
            
            # 2. Narrative Progress Monitoring
            self.event_bus.subscribe(EventType.NARRATIVE_DECISION, self._handle_narrative_decision)
            subscription_count[EventType.NARRATIVE_DECISION.value] = 1
            
            # 3. Channel Engagement Tracking
            self.event_bus.subscribe(EventType.CHANNEL_ENGAGEMENT, self._handle_channel_engagement)
            subscription_count[EventType.CHANNEL_ENGAGEMENT.value] = 1
            
            # 4. User Activity Monitoring
            self.event_bus.subscribe(EventType.USER_DAILY_CHECKIN, self._handle_daily_checkin)
            subscription_count[EventType.USER_DAILY_CHECKIN.value] = 1
            
            # 5. VIP Access Tracking
            self.event_bus.subscribe(EventType.VIP_ACCESS_REQUIRED, self._handle_vip_access_required)
            subscription_count[EventType.VIP_ACCESS_REQUIRED.value] = 1
            
            # 6. Error Monitoring and Auto-Recovery
            self.event_bus.subscribe(EventType.ERROR_OCCURRED, self._handle_error_occurred)
            subscription_count[EventType.ERROR_OCCURRED.value] = 1
            
            # 7. Consistency Check Responses
            self.event_bus.subscribe(EventType.CONSISTENCY_CHECK, self._handle_consistency_check)
            subscription_count[EventType.CONSISTENCY_CHECK.value] = 1
            
            self._subscriptions_active = True
            logger.info(f"Cross-module event subscriptions set up: {sum(subscription_count.values())} total")
            
            return subscription_count
            
        except Exception as e:
            logger.exception(f"Error setting up cross-module subscriptions: {e}")
            raise
    
    async def _handle_points_awarded(self, event: Event) -> None:
        """
        Handle points awarded events by checking for badge eligibility.
        This creates automatic badge awarding based on point milestones.
        """
        try:
            user_id = event.user_id
            points_awarded = event.data.get('points', 0)
            total_points = event.data.get('total_points', 0)
            
            logger.debug(f"Handling points awarded event for user {user_id}: +{points_awarded} (total: {total_points})")
            
            # Check for point milestone badges
            if total_points >= 1000 and points_awarded > 0:
                # Award "High Achiever" badge for 1000+ points
                await self._try_award_milestone_badge(user_id, "high_achiever", total_points)
            
            if total_points >= 500 and points_awarded > 0:
                # Award "Dedicated Player" badge for 500+ points
                await self._try_award_milestone_badge(user_id, "dedicated_player", total_points)
            
            if total_points >= 100 and points_awarded > 0:
                # Award "Getting Started" badge for 100+ points
                await self._try_award_milestone_badge(user_id, "getting_started", total_points)
            
        except Exception as e:
            logger.exception(f"Error handling points awarded event: {e}")
    
    async def _handle_narrative_decision(self, event: Event) -> None:
        """
        Handle narrative decision events by tracking user engagement patterns.
        """
        try:
            user_id = event.user_id
            decision_id = event.data.get('decision_id')
            fragment = event.data.get('fragment')
            
            logger.debug(f"Handling narrative decision event for user {user_id}: decision {decision_id}")
            
            # Award narrative engagement points
            if decision_id:
                await self.point_service.add_points(user_id, 5, "Narrative decision bonus")
                
                # Check for narrative milestone badges
                current_progress = await self.user_service.get_user(user_id)
                if current_progress:
                    # Award badges based on narrative progression
                    if fragment and 'level3_' in str(fragment):
                        await self._try_award_milestone_badge(user_id, "story_explorer", 0)
                    elif fragment and 'level5_' in str(fragment):
                        await self._try_award_milestone_badge(user_id, "narrative_master", 0)
            
        except Exception as e:
            logger.exception(f"Error handling narrative decision event: {e}")
    
    async def _handle_channel_engagement(self, event: Event) -> None:
        """
        Handle channel engagement events by tracking participation patterns.
        """
        try:
            user_id = event.user_id
            action_type = event.data.get('action_type')
            points_awarded = event.data.get('points_awarded', 0)
            
            logger.debug(f"Handling channel engagement event for user {user_id}: {action_type}")
            
            # Track engagement for social badges
            if action_type == "post" and points_awarded > 0:
                await self._try_award_milestone_badge(user_id, "content_creator", 0)
            elif action_type == "comment" and points_awarded > 0:
                await self._try_award_milestone_badge(user_id, "community_member", 0)
            
        except Exception as e:
            logger.exception(f"Error handling channel engagement event: {e}")
    
    async def _handle_daily_checkin(self, event: Event) -> None:
        """
        Handle daily check-in events by tracking user consistency.
        """
        try:
            user_id = event.user_id
            streak = event.data.get('streak', 1)
            
            logger.debug(f"Handling daily checkin event for user {user_id}: streak {streak}")
            
            # Award consistency badges
            if streak >= 30:
                await self._try_award_milestone_badge(user_id, "loyal_user", streak)
            elif streak >= 7:
                await self._try_award_milestone_badge(user_id, "consistent_visitor", streak)
            elif streak >= 3:
                await self._try_award_milestone_badge(user_id, "regular_user", streak)
            
        except Exception as e:
            logger.exception(f"Error handling daily checkin event: {e}")
    
    async def _handle_vip_access_required(self, event: Event) -> None:
        """
        Handle VIP access required events by tracking conversion opportunities.
        """
        try:
            user_id = event.user_id
            fragment_key = event.data.get('fragment_key')
            
            logger.debug(f"Handling VIP access required event for user {user_id}: {fragment_key}")
            
            # This could trigger conversion tracking or special offers
            # For now, just log the interest in VIP content
            logger.info(f"User {user_id} showed interest in VIP content: {fragment_key}")
            
        except Exception as e:
            logger.exception(f"Error handling VIP access required event: {e}")
    
    async def _handle_error_occurred(self, event: Event) -> None:
        """
        Handle error events by triggering consistency checks when appropriate.
        """
        try:
            user_id = event.user_id
            error_type = event.data.get('error_type')
            source = event.data.get('source')
            
            logger.debug(f"Handling error event for user {user_id}: {error_type} from {source}")
            
            # For certain types of errors, trigger a consistency check
            critical_error_types = ['IntegrityError', 'DataError', 'InvalidRequestError']
            if error_type in critical_error_types:
                logger.info(f"Critical error detected, scheduling consistency check for user {user_id}")
                # Schedule a consistency check (in a real system, this might be queued)
                try:
                    await self.reconciliation_service._check_user_consistency(user_id)
                except Exception as check_error:
                    logger.exception(f"Failed to perform consistency check for user {user_id}: {check_error}")
            
        except Exception as e:
            logger.exception(f"Error handling error occurred event: {e}")
    
    async def _handle_consistency_check(self, event: Event) -> None:
        """
        Handle consistency check events by logging and potentially taking action.
        """
        try:
            check_type = event.data.get('type', 'unknown')
            
            if check_type == "full_reconciliation":
                result = event.data.get('result', {})
                issues_found = result.get('inconsistencies_found', 0)
                corrections_made = result.get('inconsistencies_corrected', 0)
                
                logger.info(f"Full reconciliation completed: {issues_found} issues found, {corrections_made} corrected")
                
                # If many issues were found, this might indicate a systematic problem
                if issues_found > 10:
                    logger.warning(f"High number of inconsistencies detected ({issues_found}), system may need attention")
            
        except Exception as e:
            logger.exception(f"Error handling consistency check event: {e}")
    
    async def _try_award_milestone_badge(self, user_id: int, badge_type: str, value: int) -> bool:
        """
        Attempt to award a milestone badge to a user.
        
        Args:
            user_id: User to award badge to
            badge_type: Type of badge to award
            value: Associated value (points, streak, etc.)
            
        Returns:
            bool: True if badge was awarded, False if already owned or error occurred
        """
        try:
            # Check if user already has this badge
            existing_badges = await self.badge_service.get_user_badges(user_id)
            for badge in existing_badges:
                if badge.name == badge_type:
                    return False  # Already has this badge
            
            # Award the badge
            badge_awarded = await self.badge_service.award_badge(user_id, badge_type)
            if badge_awarded:
                logger.info(f"Awarded {badge_type} badge to user {user_id} (value: {value})")
                return True
                
        except Exception as e:
            logger.exception(f"Error awarding {badge_type} badge to user {user_id}: {e}")
        
        return False
    
    def get_subscription_status(self) -> Dict[str, Any]:
        """
        Get current status of event subscriptions.
        
        Returns:
            Dict with subscription status information
        """
        status = {
            "subscriptions_active": self._subscriptions_active,
            "total_subscribers": {}
        }
        
        # Get subscriber counts for each event type
        for event_type in EventType:
            count = self.event_bus.get_subscribers_count(event_type)
            if count > 0:
                status["total_subscribers"][event_type.value] = count
        
        return status
    
    async def teardown_subscriptions(self) -> None:
        """
        Remove all event subscriptions. Useful for cleanup and testing.
        """
        try:
            # Unsubscribe from all events
            event_handlers = [
                (EventType.POINTS_AWARDED, self._handle_points_awarded),
                (EventType.NARRATIVE_DECISION, self._handle_narrative_decision),
                (EventType.CHANNEL_ENGAGEMENT, self._handle_channel_engagement),
                (EventType.USER_DAILY_CHECKIN, self._handle_daily_checkin),
                (EventType.VIP_ACCESS_REQUIRED, self._handle_vip_access_required),
                (EventType.ERROR_OCCURRED, self._handle_error_occurred),
                (EventType.CONSISTENCY_CHECK, self._handle_consistency_check),
            ]
            
            for event_type, handler in event_handlers:
                self.event_bus.unsubscribe(event_type, handler)
            
            self._subscriptions_active = False
            logger.info("Event subscriptions torn down")
            
        except Exception as e:
            logger.exception(f"Error tearing down subscriptions: {e}")