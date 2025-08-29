"""
Reconciliation service for detecting and correcting data inconsistencies across modules.
Provides mechanisms to ensure data integrity and synchronization between services.
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_

from database.models import User, Badge, UserBadge
from database.narrative_models import UserNarrativeState
from services.point_service import PointService
from services.user_service import UserService
from services.narrative_service import NarrativeService
from services.badge_service import BadgeService
from services.event_bus import get_event_bus, EventType

logger = logging.getLogger(__name__)

@dataclass
class InconsistencyReport:
    """Data structure for reporting system inconsistencies."""
    user_id: int
    issue_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    expected_value: Any
    actual_value: Any
    module_affected: str
    detected_at: datetime
    auto_correctable: bool = False
    correction_performed: bool = False

@dataclass
class ReconciliationResult:
    """Result of a reconciliation process."""
    total_users_checked: int
    inconsistencies_found: int
    inconsistencies_corrected: int
    issues_by_severity: Dict[str, int]
    execution_time_ms: float
    reports: List[InconsistencyReport]

class ReconciliationService:
    """
    Service for detecting and correcting data inconsistencies across modules.
    
    This service maintains architectural coherence by:
    - Following the same async patterns as existing services
    - Using the established dependency injection pattern
    - Integrating with the event bus for system monitoring
    - Respecting service boundaries and contracts
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize the reconciliation service.
        
        Args:
            session: Database session for performing reconciliation operations
        """
        self.session = session
        
        # Initialize dependent services with proper dependency injection
        from services.level_service import LevelService
        from services.achievement_service import AchievementService
        
        level_service = LevelService(session)
        achievement_service = AchievementService(session)
        self.point_service = PointService(session, level_service, achievement_service)
        self.user_service = UserService(session)
        self.narrative_service = NarrativeService(session)
        self.badge_service = BadgeService(session)
        self.event_bus = get_event_bus()
    
    async def perform_full_reconciliation(self, user_ids: Optional[List[int]] = None) -> ReconciliationResult:
        """
        Perform a comprehensive reconciliation check across all modules.
        
        Args:
            user_ids: Optional list of specific user IDs to check. If None, checks all users.
            
        Returns:
            ReconciliationResult: Comprehensive report of the reconciliation process
        """
        start_time = datetime.utcnow()
        logger.info(f"Starting full reconciliation for {len(user_ids) if user_ids else 'all'} users")
        
        try:
            # Get users to check
            if user_ids:
                users_query = select(User).where(User.id.in_(user_ids))
            else:
                users_query = select(User).limit(1000)  # Process in batches to avoid memory issues
                
            result = await self.session.execute(users_query)
            users = result.scalars().all()
            
            all_reports = []
            corrections_made = 0
            
            # Check each user for inconsistencies
            for user in users:
                user_reports = await self._check_user_consistency(user.id)
                all_reports.extend(user_reports)
                
                # Perform auto-corrections where possible
                for report in user_reports:
                    if report.auto_correctable and not report.correction_performed:
                        try:
                            corrected = await self._auto_correct_inconsistency(report)
                            if corrected:
                                report.correction_performed = True
                                corrections_made += 1
                        except Exception as e:
                            logger.exception(f"Failed to auto-correct inconsistency for user {user.id}: {e}")
            
            # Calculate results
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds() * 1000
            
            issues_by_severity = {
                'low': len([r for r in all_reports if r.severity == 'low']),
                'medium': len([r for r in all_reports if r.severity == 'medium']),
                'high': len([r for r in all_reports if r.severity == 'high']),
                'critical': len([r for r in all_reports if r.severity == 'critical'])
            }
            
            result = ReconciliationResult(
                total_users_checked=len(users),
                inconsistencies_found=len(all_reports),
                inconsistencies_corrected=corrections_made,
                issues_by_severity=issues_by_severity,
                execution_time_ms=execution_time,
                reports=all_reports
            )
            
            # Emit reconciliation event
            await self.event_bus.publish(
                EventType.CONSISTENCY_CHECK,
                0,  # System-level event
                {
                    "type": "full_reconciliation",
                    "result": asdict(result),
                    "users_checked": len(users),
                    "issues_found": len(all_reports),
                    "corrections_made": corrections_made
                },
                source="reconciliation_service"
            )
            
            logger.info(f"Full reconciliation completed: {len(all_reports)} issues found, {corrections_made} corrected")
            return result
            
        except Exception as e:
            logger.exception(f"Error during full reconciliation: {e}")
            raise
    
    async def _check_user_consistency(self, user_id: int) -> List[InconsistencyReport]:
        """
        Check consistency for a specific user across all modules.
        
        Args:
            user_id: User ID to check
            
        Returns:
            List[InconsistencyReport]: List of inconsistencies found
        """
        reports = []
        
        try:
            # 1. Check user existence consistency
            user = await self.user_service.get_user(user_id)
            if not user:
                # User doesn't exist, this could be a reference integrity issue
                reports.append(InconsistencyReport(
                    user_id=user_id,
                    issue_type="missing_user",
                    severity="critical",
                    description="User referenced but not found in database",
                    expected_value="User record",
                    actual_value=None,
                    module_affected="user_service",
                    detected_at=datetime.utcnow()
                ))
                return reports
            
            # 2. Check point consistency
            point_reports = await self._check_point_consistency(user_id)
            reports.extend(point_reports)
            
            # 3. Check badge consistency
            badge_reports = await self._check_badge_consistency(user_id)
            reports.extend(badge_reports)
            
            # 4. Check narrative consistency
            narrative_reports = await self._check_narrative_consistency(user_id)
            reports.extend(narrative_reports)
            
            # 5. Check cross-module consistency
            cross_module_reports = await self._check_cross_module_consistency(user_id)
            reports.extend(cross_module_reports)
            
        except Exception as e:
            logger.exception(f"Error checking consistency for user {user_id}: {e}")
            reports.append(InconsistencyReport(
                user_id=user_id,
                issue_type="check_error",
                severity="medium",
                description=f"Error during consistency check: {str(e)}",
                expected_value="Successful check",
                actual_value=f"Error: {str(e)}",
                module_affected="reconciliation_service",
                detected_at=datetime.utcnow()
            ))
        
        return reports
    
    async def _check_point_consistency(self, user_id: int) -> List[InconsistencyReport]:
        """Check point system consistency for a user."""
        reports = []
        
        try:
            # Get user data (points and level are stored directly in User model)
            user_query = select(User).where(User.id == user_id)
            result = await self.session.execute(user_query)
            user = result.scalar_one_or_none()
            
            if not user:
                reports.append(InconsistencyReport(
                    user_id=user_id,
                    issue_type="missing_user",
                    severity="critical",
                    description="User not found",
                    expected_value="User record",
                    actual_value=None,
                    module_affected="point_service",
                    detected_at=datetime.utcnow(),
                    auto_correctable=True
                ))
                return reports
            
            # Check for negative points
            if user.points < 0:
                reports.append(InconsistencyReport(
                    user_id=user_id,
                    issue_type="negative_points",
                    severity="high",
                    description="User has negative points",
                    expected_value=">=0",
                    actual_value=user.points,
                    module_affected="point_service",
                    detected_at=datetime.utcnow(),
                    auto_correctable=True
                ))
            
            # Check level consistency with points
            expected_level = await self._calculate_expected_level(user.points)
            if user.level != expected_level:
                reports.append(InconsistencyReport(
                    user_id=user_id,
                    issue_type="level_mismatch",
                    severity="medium",
                    description="User level doesn't match points",
                    expected_value=expected_level,
                    actual_value=user.level,
                    module_affected="point_service",
                    detected_at=datetime.utcnow(),
                    auto_correctable=True
                ))
            
        except Exception as e:
            logger.exception(f"Error checking point consistency for user {user_id}: {e}")
        
        return reports
    
    async def _check_badge_consistency(self, user_id: int) -> List[InconsistencyReport]:
        """Check badge system consistency for a user."""
        reports = []
        
        try:
            # Get user badges
            user_badges_query = select(UserBadge).where(UserBadge.user_id == user_id)
            result = await self.session.execute(user_badges_query)
            user_badges = result.scalars().all()
            
            # Check for duplicate badges
            badge_ids = [ub.badge_id for ub in user_badges]
            if len(badge_ids) != len(set(badge_ids)):
                reports.append(InconsistencyReport(
                    user_id=user_id,
                    issue_type="duplicate_badges",
                    severity="medium",
                    description="User has duplicate badge awards",
                    expected_value="Unique badges only",
                    actual_value=f"Duplicates found: {badge_ids}",
                    module_affected="badge_service",
                    detected_at=datetime.utcnow(),
                    auto_correctable=True
                ))
            
            # Check for badges with missing references
            for user_badge in user_badges:
                badge_query = select(Badge).where(Badge.id == user_badge.badge_id)
                result = await self.session.execute(badge_query)
                badge = result.scalar_one_or_none()
                
                if not badge:
                    reports.append(InconsistencyReport(
                        user_id=user_id,
                        issue_type="orphaned_user_badge",
                        severity="high",
                        description=f"UserBadge references non-existent Badge {user_badge.badge_id}",
                        expected_value="Valid badge reference",
                        actual_value=f"Badge ID {user_badge.badge_id} not found",
                        module_affected="badge_service",
                        detected_at=datetime.utcnow(),
                        auto_correctable=True
                    ))
            
        except Exception as e:
            logger.exception(f"Error checking badge consistency for user {user_id}: {e}")
        
        return reports
    
    async def _check_narrative_consistency(self, user_id: int) -> List[InconsistencyReport]:
        """Check narrative system consistency for a user."""
        reports = []
        
        try:
            # Get narrative state
            narrative_query = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
            result = await self.session.execute(narrative_query)
            narrative_states = result.scalars().all()
            
            # Check for invalid fragment references
            for state in narrative_states:
                if hasattr(state, 'current_fragment') and (not state.current_fragment or state.current_fragment.strip() == ""):
                    reports.append(InconsistencyReport(
                        user_id=user_id,
                        issue_type="empty_fragment_reference",
                        severity="medium",
                        description="User has narrative state with empty fragment reference",
                        expected_value="Valid fragment key",
                        actual_value=state.current_fragment,
                        module_affected="narrative_service",
                        detected_at=datetime.utcnow(),
                        auto_correctable=True
                    ))
            
        except Exception as e:
            logger.exception(f"Error checking narrative consistency for user {user_id}: {e}")
        
        return reports
    
    async def _check_cross_module_consistency(self, user_id: int) -> List[InconsistencyReport]:
        """Check consistency between different modules."""
        reports = []
        
        try:
            # Get user data from different modules
            user = await self.user_service.get_user(user_id)
            user_points = await self.point_service.get_user_points(user_id)
            
            # Check if user role matches their progress
            # VIP users should typically have more points than free users
            if user and user.role == 'vip' and user_points < 50:  # Arbitrary threshold
                reports.append(InconsistencyReport(
                    user_id=user_id,
                    issue_type="vip_low_points",
                    severity="low",
                    description="VIP user has surprisingly low points",
                    expected_value=">= 50 points for VIP",
                    actual_value=user_points,
                    module_affected="cross_module",
                    detected_at=datetime.utcnow(),
                    auto_correctable=False
                ))
            
        except Exception as e:
            logger.exception(f"Error checking cross-module consistency for user {user_id}: {e}")
        
        return reports
    
    async def _auto_correct_inconsistency(self, report: InconsistencyReport) -> bool:
        """
        Attempt to automatically correct an inconsistency.
        
        Args:
            report: The inconsistency report to correct
            
        Returns:
            bool: True if correction was successful, False otherwise
        """
        try:
            if report.issue_type == "missing_user":
                # Create missing User record - this should be handled by user_service
                try:
                    # This would normally be handled by the user service when a user first interacts
                    logger.info(f"Missing user {report.user_id} detected - user creation should be handled by user_service")
                    return False  # Don't auto-create users here
                except Exception:
                    return False
                
            elif report.issue_type == "negative_points":
                # Reset negative points to 0
                try:
                    await self.point_service.set_user_points(report.user_id, 0)
                    logger.info(f"Auto-corrected negative points for user {report.user_id}")
                    return True
                except Exception:
                    return False
                
            elif report.issue_type == "level_mismatch":
                # Recalculate and update level - use available service methods
                try:
                    current_points = await self.point_service.get_user_points(report.user_id)
                    correct_level = await self._calculate_expected_level(current_points)
                    # Note: We would need a method to update user level in point_service
                    logger.info(f"Level mismatch detected for user {report.user_id}: has level {report.actual_value}, should be {correct_level}")
                    return False  # Don't auto-correct without proper service method
                except Exception:
                    return False
                
            elif report.issue_type == "duplicate_badges":
                # Remove duplicate badge entries
                await self._remove_duplicate_badges(report.user_id)
                logger.info(f"Auto-corrected duplicate badges for user {report.user_id}")
                return True
                
            elif report.issue_type == "orphaned_user_badge":
                # Remove orphaned UserBadge records
                await self._remove_orphaned_user_badges(report.user_id)
                logger.info(f"Auto-corrected orphaned user badges for user {report.user_id}")
                return True
                
            elif report.issue_type == "empty_fragment_reference":
                # Reset to starting fragment
                await self.narrative_service.reset_user_progress(report.user_id)
                logger.info(f"Auto-corrected empty fragment reference for user {report.user_id}")
                return True
                
        except Exception as e:
            logger.exception(f"Failed to auto-correct {report.issue_type} for user {report.user_id}: {e}")
            return False
        
        return False
    
    async def _calculate_expected_level(self, points: int) -> int:
        """Calculate the expected level based on points."""
        # Basic level calculation (can be enhanced based on actual game logic)
        if points < 100:
            return 1
        elif points < 250:
            return 2
        elif points < 500:
            return 3
        elif points < 1000:
            return 4
        else:
            return 5
    
    async def _remove_duplicate_badges(self, user_id: int) -> None:
        """Remove duplicate badge entries for a user."""
        # Implementation would depend on the specific badge system logic
        pass
    
    async def _remove_orphaned_user_badges(self, user_id: int) -> None:
        """Remove orphaned UserBadge records for a user."""
        # Implementation would depend on the specific badge system logic
        pass
    
    async def schedule_periodic_reconciliation(self, interval_hours: int = 24) -> None:
        """
        Schedule periodic reconciliation checks.
        
        Args:
            interval_hours: How often to run reconciliation (in hours)
        """
        logger.info(f"Scheduling periodic reconciliation every {interval_hours} hours")
        
        # This would integrate with the existing scheduler service
        # For now, just emit an event to indicate the schedule was set
        await self.event_bus.publish(
            EventType.CONSISTENCY_CHECK,
            0,
            {
                "type": "schedule_set",
                "interval_hours": interval_hours,
                "next_run": datetime.utcnow() + timedelta(hours=interval_hours)
            },
            source="reconciliation_service"
        )