"""
Automation Service for modulo-admon - Administrative Task Automation

This service handles automated administrative tasks including subscription reminders,
message cleanup, and coordination with CoordinadorCentral for cross-module operations.

Implements requirements:
- 6.1: Subscription reminder automation
- 6.2: Message cleanup automation
- Cross-module coordination through CoordinadorCentral
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete

try:
    from .coordinador_central import CoordinadorCentral, AccionUsuario
    from .subscription_service import SubscriptionService
    from .config_service import ConfigService
    from ..database.models import (
        User, VipSubscription, AdminActionLog, MessageCleanupLog,
        InviteToken, SubscriptionToken, Token, PendingChannelRequest,
        UserStats
    )
    from ..utils.menu_manager import MenuManager
except ImportError:
    # Fallback to absolute imports for standalone usage
    from services.coordinador_central import CoordinadorCentral, AccionUsuario
    from services.subscription_service import SubscriptionService
    from services.config_service import ConfigService
    from database.models import (
        User, VipSubscription, AdminActionLog, MessageCleanupLog,
        InviteToken, SubscriptionToken, Token, PendingChannelRequest,
        UserStats
    )
    from utils.menu_manager import MenuManager

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AutomationTask:
    """Represents an automation task with metadata and execution details."""
    task_id: str
    name: str
    description: str
    task_function: Callable
    schedule_interval: int  # seconds
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    max_retries: int = 3
    retry_count: int = 0
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    kwargs: Dict[str, Any] = field(default_factory=dict)


class AutomationService:
    """
    Comprehensive automation service for administrative tasks.

    Handles:
    - Subscription reminder automation (Requirement 6.1)
    - Message cleanup automation (Requirement 6.2)
    - Task scheduling and management
    - Cross-module coordination through CoordinadorCentral
    - Retry mechanisms and error handling
    """

    def __init__(self, session: AsyncSession, bot: Optional[Bot] = None):
        """
        Initialize the automation service.

        Args:
            session: Database session for operations
            bot: Telegram bot instance for sending messages (optional)
        """
        self.session = session
        self.bot = bot
        self.subscription_service = SubscriptionService(session)
        self.config_service = ConfigService(session)

        # Initialize CoordinadorCentral for cross-module coordination
        self.coordinator = CoordinadorCentral(session)

        # Task management
        self._tasks: Dict[str, AutomationTask] = {}
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None

        # Services
        self._menu_manager = MenuManager()

        # Metrics
        self._metrics = {
            "tasks_executed": 0,
            "tasks_failed": 0,
            "reminders_sent": 0,
            "messages_cleaned": 0,
            "last_execution": None,
            "start_time": datetime.utcnow()
        }

        # Configuration defaults
        self._default_config = {
            "reminder_days_before": [3, 1],  # Days before expiration to send reminders
            "message_cleanup_interval": 3600,  # 1 hour in seconds
            "inactive_user_threshold": 7,  # Days to consider user inactive
            "cleanup_batch_size": 50,  # Messages to clean per batch
            "retry_delay": 300  # 5 minutes between retries
        }

        # Initialize default tasks
        self._initialize_default_tasks()

    def _initialize_default_tasks(self):
        """Initialize default automation tasks based on requirements."""
        # Requirement 6.1: Subscription reminder automation
        self.register_task(
            task_id="subscription_reminders",
            name="VIP Subscription Reminders",
            description="Send personalized automatic reminders with renewal links for expiring subscriptions",
            task_function=self._handle_subscription_reminders,
            schedule_interval=3600,  # Every hour
            priority=TaskPriority.HIGH,
            max_retries=3
        )

        # Requirement 6.2: Message cleanup automation
        self.register_task(
            task_id="temporary_message_cleanup",
            name="Temporary Message Cleanup",
            description="Clean old temporary messages according to configuration",
            task_function=self._handle_message_cleanup,
            schedule_interval=1800,  # Every 30 minutes
            priority=TaskPriority.NORMAL,
            max_retries=2
        )

        # Additional administrative tasks
        self.register_task(
            task_id="expired_subscription_cleanup",
            name="Expired Subscription Cleanup",
            description="Process and clean up fully expired subscriptions",
            task_function=self._handle_expired_subscriptions,
            schedule_interval=7200,  # Every 2 hours
            priority=TaskPriority.NORMAL,
            max_retries=2
        )

        self.register_task(
            task_id="automation_health_check",
            name="Automation Health Check",
            description="Monitor automation service health and performance",
            task_function=self._handle_health_check,
            schedule_interval=900,  # Every 15 minutes
            priority=TaskPriority.LOW,
            max_retries=1
        )

        # Additional cleanup automation tasks
        self.register_task(
            task_id="cleanup_old_messages_extended",
            name="Extended Old Messages Cleanup",
            description="Clean up expired temporary messages and tracking data",
            task_function=self._handle_extended_message_cleanup,
            schedule_interval=3600,  # Every hour
            priority=TaskPriority.NORMAL,
            max_retries=2
        )

        self.register_task(
            task_id="remove_expired_tokens",
            name="Expired Token Removal",
            description="Remove expired and used tokens from database",
            task_function=self._handle_token_cleanup,
            schedule_interval=7200,  # Every 2 hours
            priority=TaskPriority.NORMAL,
            max_retries=2
        )

        self.register_task(
            task_id="archive_old_analytics",
            name="Analytics Data Archival",
            description="Archive old analytics data and clean up logs",
            task_function=self._handle_analytics_archival,
            schedule_interval=86400,  # Every 24 hours
            priority=TaskPriority.LOW,
            max_retries=2
        )

        self.register_task(
            task_id="inactive_vip_detection",
            name="Inactive VIP User Detection",
            description="Detect inactive VIP users and notify administrators (Requirement 6.4)",
            task_function=self._handle_inactive_vip_detection,
            schedule_interval=21600,  # Every 6 hours
            priority=TaskPriority.HIGH,
            max_retries=3
        )

    def register_task(
        self,
        task_id: str,
        name: str,
        description: str,
        task_function: Callable,
        schedule_interval: int,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        **kwargs
    ) -> bool:
        """
        Register a new automation task.

        Args:
            task_id: Unique identifier for the task
            name: Human-readable task name
            description: Task description
            task_function: Function to execute for the task
            schedule_interval: Execution interval in seconds
            priority: Task priority level
            max_retries: Maximum retry attempts
            **kwargs: Additional task parameters

        Returns:
            bool: True if task was registered successfully
        """
        try:
            if task_id in self._tasks:
                logger.warning(f"Task {task_id} already exists, updating configuration")

            task = AutomationTask(
                task_id=task_id,
                name=name,
                description=description,
                task_function=task_function,
                schedule_interval=schedule_interval,
                priority=priority,
                max_retries=max_retries,
                next_run=datetime.utcnow() + timedelta(seconds=schedule_interval),
                kwargs=kwargs
            )

            self._tasks[task_id] = task
            logger.info(f"Registered automation task: {name} ({task_id})")
            return True

        except Exception as e:
            logger.exception(f"Failed to register task {task_id}: {str(e)}")
            return False

    async def start_automation(self) -> bool:
        """
        Start the automation scheduler.

        Returns:
            bool: True if started successfully
        """
        try:
            if self._running:
                logger.warning("Automation service is already running")
                return True

            self._running = True
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())
            logger.info("Automation service started successfully")
            return True

        except Exception as e:
            logger.exception(f"Failed to start automation service: {str(e)}")
            self._running = False
            return False

    async def stop_automation(self) -> bool:
        """
        Stop the automation scheduler.

        Returns:
            bool: True if stopped successfully
        """
        try:
            self._running = False

            if self._scheduler_task and not self._scheduler_task.done():
                self._scheduler_task.cancel()
                try:
                    await self._scheduler_task
                except asyncio.CancelledError:
                    pass

            logger.info("Automation service stopped successfully")
            return True

        except Exception as e:
            logger.exception(f"Failed to stop automation service: {str(e)}")
            return False

    async def _scheduler_loop(self):
        """Main scheduler loop that manages task execution."""
        logger.info("Automation scheduler loop started")

        try:
            while self._running:
                await self._process_scheduled_tasks()
                await asyncio.sleep(60)  # Check every minute

        except asyncio.CancelledError:
            logger.info("Automation scheduler loop cancelled")
            raise
        except Exception as e:
            logger.exception(f"Error in scheduler loop: {str(e)}")
            # Continue running despite errors
            if self._running:
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

        logger.info("Automation scheduler loop ended")

    async def _process_scheduled_tasks(self):
        """Process all scheduled tasks that are due for execution."""
        now = datetime.utcnow()

        # Get tasks sorted by priority and next run time
        due_tasks = [
            task for task in self._tasks.values()
            if task.next_run and task.next_run <= now and task.status != TaskStatus.RUNNING
        ]

        # Sort by priority (highest first), then by next_run time
        due_tasks.sort(key=lambda t: (-t.priority.value, t.next_run or now))

        for task in due_tasks:
            try:
                await self._execute_task(task)
            except Exception as e:
                logger.exception(f"Error executing task {task.task_id}: {str(e)}")
                await self._handle_task_failure(task, str(e))

    async def _execute_task(self, task: AutomationTask):
        """
        Execute a single automation task with error handling and retry logic.

        Args:
            task: The automation task to execute
        """
        start_time = datetime.utcnow()
        task.status = TaskStatus.RUNNING
        task.last_run = start_time

        try:
            logger.debug(f"Executing task: {task.name} ({task.task_id})")

            # Execute the task function
            if asyncio.iscoroutinefunction(task.task_function):
                await task.task_function(**task.kwargs)
            else:
                task.task_function(**task.kwargs)

            # Task completed successfully
            task.status = TaskStatus.COMPLETED
            task.retry_count = 0
            task.error_message = None
            task.execution_time = (datetime.utcnow() - start_time).total_seconds()
            task.next_run = start_time + timedelta(seconds=task.schedule_interval)

            self._metrics["tasks_executed"] += 1
            self._metrics["last_execution"] = start_time

            logger.debug(f"Task {task.name} completed successfully in {task.execution_time:.2f}s")

        except Exception as e:
            await self._handle_task_failure(task, str(e))

    async def _handle_task_failure(self, task: AutomationTask, error_message: str):
        """
        Handle task execution failure with retry logic.

        Args:
            task: The failed automation task
            error_message: Error message from the failure
        """
        task.error_message = error_message
        task.retry_count += 1
        self._metrics["tasks_failed"] += 1

        if task.retry_count <= task.max_retries:
            # Schedule retry with exponential backoff
            retry_delay = min(300, 60 * (2 ** (task.retry_count - 1)))  # Max 5 minutes
            task.status = TaskStatus.RETRYING
            task.next_run = datetime.utcnow() + timedelta(seconds=retry_delay)

            logger.warning(
                f"Task {task.name} failed (attempt {task.retry_count}/{task.max_retries}), "
                f"retrying in {retry_delay}s: {error_message}"
            )
        else:
            # Max retries exceeded
            task.status = TaskStatus.FAILED
            task.next_run = datetime.utcnow() + timedelta(seconds=task.schedule_interval)

            logger.error(
                f"Task {task.name} failed permanently after {task.max_retries} retries: {error_message}"
            )

    # Task Implementation Methods

    async def _handle_extended_message_cleanup(self, **kwargs):
        """Handle extended message cleanup automation task."""
        try:
            retention_hours = kwargs.get("retention_hours", 24)
            batch_size = kwargs.get("batch_size", 50)

            result = await self.cleanup_old_messages(
                retention_hours=retention_hours,
                batch_size=batch_size
            )

            if not result.get("success"):
                raise Exception(result.get("message", "Cleanup failed"))

            logger.info(f"Extended message cleanup completed: {result.get('cleaned_count', 0)} messages cleaned")

        except Exception as e:
            logger.exception(f"Error in extended message cleanup: {str(e)}")
            raise

    async def _handle_token_cleanup(self, **kwargs):
        """Handle token cleanup automation task."""
        try:
            retention_days = kwargs.get("retention_days", 30)

            result = await self.remove_expired_tokens(retention_days=retention_days)

            if not result.get("success"):
                raise Exception(result.get("message", "Token cleanup failed"))

            logger.info(f"Token cleanup completed: {result.get('removed_count', 0)} tokens removed")

        except Exception as e:
            logger.exception(f"Error in token cleanup: {str(e)}")
            raise

    async def _handle_analytics_archival(self, **kwargs):
        """Handle analytics archival automation task."""
        try:
            retention_days = kwargs.get("retention_days", 90)

            result = await self.archive_old_analytics(retention_days=retention_days)

            if not result.get("success"):
                raise Exception(result.get("message", "Analytics archival failed"))

            logger.info(f"Analytics archival completed: {result.get('archived_count', 0)} entries archived")

        except Exception as e:
            logger.exception(f"Error in analytics archival: {str(e)}")
            raise

    async def _handle_inactive_vip_detection(self, **kwargs):
        """Handle inactive VIP user detection automation task (Requirement 6.4)."""
        try:
            threshold_days = kwargs.get("inactivity_threshold_days", 7)

            result = await self.detect_inactive_vip_users(inactivity_threshold_days=threshold_days)

            if not result.get("success"):
                raise Exception(result.get("message", "Inactive VIP detection failed"))

            # Notify administrators if inactive users found
            inactive_count = len(result.get("inactive_users", []))
            if inactive_count > 0:
                # Send notification through CoordinadorCentral
                await self.coordinator.ejecutar_flujo(
                    user_id=1,  # System user for admin notifications
                    accion=AccionUsuario.ADMIN_NARRATIVE_OPERATION,
                    operation_type="admin_notification",
                    notification_type="inactive_vip_users",
                    inactive_users_data=result.get("admin_notifications", []),
                    count=inactive_count
                )

            logger.info(f"Inactive VIP detection completed: {inactive_count} inactive users detected")

        except Exception as e:
            logger.exception(f"Error in inactive VIP detection: {str(e)}")
            raise

    async def _handle_subscription_reminders(self, **kwargs):
        """
        Handle subscription reminder automation (Requirement 6.1).
        Sends personalized automatic reminders with renewal links for expiring subscriptions.
        """
        try:
            now = datetime.utcnow()
            days_before = self._default_config["reminder_days_before"]

            # Query VIP subscriptions that need reminders
            reminders_sent = 0

            for days in days_before:
                remind_date = now + timedelta(days=days)

                # Find subscriptions expiring in X days
                stmt = select(VipSubscription).where(
                    and_(
                        VipSubscription.is_active == True,
                        VipSubscription.expiration_date >= remind_date,
                        VipSubscription.expiration_date <= remind_date + timedelta(hours=24)
                    )
                )

                result = await self.session.execute(stmt)
                subscriptions = result.scalars().all()

                for subscription in subscriptions:
                    try:
                        # Use CoordinadorCentral to send personalized reminder
                        reminder_result = await self.coordinator.ejecutar_flujo(
                            user_id=subscription.user_id,
                            accion=AccionUsuario.ADMIN_NARRATIVE_OPERATION,
                            operation_type="send_reminder",
                            reminder_type="subscription_expiration",
                            days_before=days,
                            expiration_date=subscription.expiration_date.isoformat(),
                            subscription_id=subscription.id
                        )

                        if reminder_result.get("success"):
                            reminders_sent += 1
                            logger.info(f"Sent {days}-day reminder to user {subscription.user_id}")
                        else:
                            logger.warning(f"Failed to send reminder to user {subscription.user_id}: {reminder_result.get('message')}")

                    except Exception as e:
                        logger.exception(f"Failed to send reminder to user {subscription.user_id}: {str(e)}")

            self._metrics["reminders_sent"] += reminders_sent
            logger.info(f"Subscription reminder automation completed: {reminders_sent} reminders sent")

        except Exception as e:
            logger.exception(f"Error in subscription reminder automation: {str(e)}")
            raise

    async def _handle_message_cleanup(self, **kwargs):
        """
        Handle temporary message cleanup automation (Requirement 6.2).
        Cleans old temporary messages according to configuration.
        """
        try:
            # Get cleanup configuration
            max_age_hours = kwargs.get("max_age_hours", 24)
            batch_size = self._default_config["cleanup_batch_size"]

            messages_cleaned = 0

            # Use MenuManager's cleanup capabilities with retry mechanism
            cleanup_results = await self._menu_manager.cleanup_old_messages(
                cutoff_time=datetime.utcnow() - timedelta(hours=max_age_hours),
                batch_size=batch_size
            )

            messages_cleaned = cleanup_results.get("cleaned_count", 0)

            # Log cleanup operation for auditing
            await self._log_cleanup_operation(
                user_id=None,  # System-wide cleanup
                messages_cleaned=messages_cleaned,
                max_age_hours=max_age_hours
            )

            # Additional cleanup for MenuManager internal state
            if hasattr(self._menu_manager, '_temp_messages'):
                current_time = time.time()
                expired_messages = []

                for user_id, (chat_id, message_id, expire_time) in self._menu_manager._temp_messages.items():
                    if current_time >= expire_time:
                        expired_messages.append(user_id)

                # Remove expired message tracking
                for user_id in expired_messages:
                    self._menu_manager._temp_messages.pop(user_id, None)

                messages_cleaned += len(expired_messages)

            self._metrics["messages_cleaned"] += messages_cleaned
            logger.info(f"Message cleanup automation completed: {messages_cleaned} messages processed")

        except Exception as e:
            logger.exception(f"Error in message cleanup automation: {str(e)}")
            raise

    async def _handle_expired_subscriptions(self, **kwargs):
        """
        Handle cleanup of fully expired subscriptions.
        Updates user roles and cleans up subscription data.
        """
        try:
            now = datetime.utcnow()

            # Find users with expired subscriptions
            stmt = select(User).where(
                and_(
                    User.role == "vip",
                    User.vip_expires_at.is_not(None),
                    User.vip_expires_at <= now
                )
            )

            result = await self.session.execute(stmt)
            expired_users = result.scalars().all()

            processed_count = 0
            for user in expired_users:
                try:
                    # Update user role to free
                    user.role = "free"

                    # Get farewell message
                    farewell_msg = await self.config_service.get_value("vip_farewell_message")
                    if not farewell_msg:
                        farewell_msg = (
                            "💔 *Tu suscripción VIP ha expirado*\n\n"
                            "Diana susurra: 'Ha sido un placer compartir estos momentos contigo...'\n\n"
                            "💫 Usa /vip para renovar tu acceso exclusivo"
                        )

                    # Send farewell message
                    await self.bot.send_message(
                        chat_id=user.id,
                        text=farewell_msg,
                        parse_mode="Markdown"
                    )

                    processed_count += 1
                    logger.info(f"Processed expired subscription for user {user.id}")

                except Exception as e:
                    logger.exception(f"Failed to process expired subscription for user {user.id}: {str(e)}")

            # Commit changes
            await self.session.commit()

            logger.info(f"Expired subscription cleanup completed: {processed_count} users processed")

        except Exception as e:
            logger.exception(f"Error in expired subscription cleanup: {str(e)}")
            raise

    async def _handle_health_check(self, **kwargs):
        """
        Perform health check on the automation service.
        Monitors task execution and service performance.
        """
        try:
            # Check task status distribution
            status_counts = {}
            total_tasks = len(self._tasks)

            for task in self._tasks.values():
                status = task.status.value
                status_counts[status] = status_counts.get(status, 0) + 1

            # Calculate health metrics
            failed_tasks = status_counts.get(TaskStatus.FAILED.value, 0)
            health_score = max(0, 100 - (failed_tasks * 100 / max(total_tasks, 1)))

            # Log health status
            if health_score >= 90:
                log_level = logging.INFO
                status_msg = "HEALTHY"
            elif health_score >= 70:
                log_level = logging.WARNING
                status_msg = "DEGRADED"
            else:
                log_level = logging.ERROR
                status_msg = "UNHEALTHY"

            logger.log(
                log_level,
                f"Automation service health check: {status_msg} "
                f"(score: {health_score:.1f}%, tasks: {total_tasks}, failed: {failed_tasks})"
            )

            # Update metrics
            self._metrics["health_score"] = health_score
            self._metrics["total_tasks"] = total_tasks

        except Exception as e:
            logger.exception(f"Error in health check: {str(e)}")
            raise

    # Public API Methods

    async def get_task_status(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get status information for tasks.

        Args:
            task_id: Specific task ID or None for all tasks

        Returns:
            Dict containing task status information
        """
        try:
            if task_id and task_id in self._tasks:
                task = self._tasks[task_id]
                return {
                    "task_id": task.task_id,
                    "name": task.name,
                    "status": task.status.value,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "next_run": task.next_run.isoformat() if task.next_run else None,
                    "retry_count": task.retry_count,
                    "max_retries": task.max_retries,
                    "execution_time": task.execution_time,
                    "error_message": task.error_message
                }
            else:
                return {
                    "total_tasks": len(self._tasks),
                    "running": self._running,
                    "metrics": self._metrics.copy(),
                    "tasks": [
                        {
                            "task_id": task.task_id,
                            "name": task.name,
                            "status": task.status.value,
                            "priority": task.priority.value,
                            "last_run": task.last_run.isoformat() if task.last_run else None,
                            "next_run": task.next_run.isoformat() if task.next_run else None
                        }
                        for task in self._tasks.values()
                    ]
                }
        except Exception as e:
            logger.exception(f"Error getting task status: {str(e)}")
            return {"error": str(e)}

    async def trigger_task_execution(self, task_id: str) -> Dict[str, Any]:
        """
        Manually trigger execution of a specific task.

        Args:
            task_id: ID of the task to trigger

        Returns:
            Dict containing execution result
        """
        try:
            if task_id not in self._tasks:
                return {"success": False, "error": f"Task {task_id} not found"}

            task = self._tasks[task_id]
            if task.status == TaskStatus.RUNNING:
                return {"success": False, "error": "Task is already running"}

            # Execute the task
            await self._execute_task(task)

            return {
                "success": True,
                "task_id": task_id,
                "status": task.status.value,
                "execution_time": task.execution_time
            }

        except Exception as e:
            logger.exception(f"Error triggering task {task_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def update_task_schedule(self, task_id: str, new_interval: int) -> Dict[str, Any]:
        """
        Update the schedule interval for a task.

        Args:
            task_id: ID of the task to update
            new_interval: New interval in seconds

        Returns:
            Dict containing update result
        """
        try:
            if task_id not in self._tasks:
                return {"success": False, "error": f"Task {task_id} not found"}

            task = self._tasks[task_id]
            old_interval = task.schedule_interval
            task.schedule_interval = new_interval

            # Update next run time
            if task.last_run:
                task.next_run = task.last_run + timedelta(seconds=new_interval)
            else:
                task.next_run = datetime.utcnow() + timedelta(seconds=new_interval)

            logger.info(f"Updated task {task_id} interval from {old_interval}s to {new_interval}s")

            return {
                "success": True,
                "task_id": task_id,
                "old_interval": old_interval,
                "new_interval": new_interval
            }

        except Exception as e:
            logger.exception(f"Error updating task schedule {task_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_service_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive service metrics.

        Returns:
            Dict containing service metrics and statistics
        """
        return {
            "automation_service": {
                "running": self._running,
                "total_tasks": len(self._tasks),
                "metrics": self._metrics.copy(),
                "uptime": (datetime.utcnow() - self._metrics.get("start_time", datetime.utcnow())).total_seconds()
                if "start_time" in self._metrics else 0
            }
        }

    async def coordinate_with_central(self, coordinador_central) -> Dict[str, Any]:
        """
        Coordinate automation tasks with CoordinadorCentral for cross-module integration.

        Args:
            coordinador_central: Instance of CoordinadorCentral

        Returns:
            Dict containing coordination result
        """
        try:
            # This method provides integration point with CoordinadorCentral
            # for cross-module automation coordination

            coordination_result = {
                "success": True,
                "automation_status": self._running,
                "active_tasks": len([t for t in self._tasks.values() if t.status == TaskStatus.RUNNING]),
                "integration": "automation_service_ready"
            }

            logger.info("Automation service coordinated with CoordinadorCentral")
            return coordination_result

        except Exception as e:
            logger.exception(f"Error coordinating with CoordinadorCentral: {str(e)}")
            return {"success": False, "error": str(e)}

    async def handle_user_departure_external(self, user_id: int, chat_id: int) -> Dict[str, Any]:
        """
        External API for handling user departure from free channel (Requirement 6.3).
        This method can be called from message handlers when user leaves.

        Args:
            user_id: ID of the user who left
            chat_id: ID of the chat they left

        Returns:
            Dict with departure handling results
        """
        try:
            # Schedule immediate execution of user departure handling
            result = await self.handle_user_departure(user_id=user_id, chat_id=chat_id)

            return result

        except Exception as e:
            logger.exception(f"Error in external user departure handling: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to handle user departure: {str(e)}",
                "error": str(e)
            }

    async def coordinate_narrative_events(self, event_schedule: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coordinate narrative events through CoordinadorCentral.

        Args:
            event_schedule: Schedule data for narrative events

        Returns:
            Dict with coordination results
        """
        try:
            event_type = event_schedule.get("event_type")
            target_users = event_schedule.get("target_users", [])
            event_data = event_schedule.get("event_data", {})

            coordination_results = []

            for user_id in target_users:
                try:
                    # Use CoordinadorCentral to coordinate with narrative module
                    result = await self.coordinator.ejecutar_flujo(
                        user_id=user_id,
                        accion=AccionUsuario.ADMIN_NARRATIVE_OPERATION,
                        operation_type="schedule_event",
                        event_type=event_type,
                        event_data=event_data
                    )

                    coordination_results.append({
                        "user_id": user_id,
                        "result": result
                    })

                except Exception as user_error:
                    logger.warning(f"Failed to coordinate event for user {user_id}: {str(user_error)}")
                    coordination_results.append({
                        "user_id": user_id,
                        "result": {"success": False, "error": str(user_error)}
                    })

            successful_coords = sum(1 for r in coordination_results if r["result"].get("success"))

            return {
                "success": True,
                "message": f"Coordinated events for {successful_coords}/{len(target_users)} users",
                "coordination_results": coordination_results,
                "action": "narrative_events_coordinated"
            }

        except Exception as e:
            logger.exception(f"Error coordinating narrative events: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to coordinate narrative events: {str(e)}",
                "error": str(e)
            }

    async def detect_inactive_vip_users(self, inactivity_threshold_days: int = 7) -> Dict[str, Any]:
        """
        Detect inactive VIP users and notify administrators (Requirement 6.4).

        Args:
            inactivity_threshold_days: Days without activity to consider inactive

        Returns:
            Dict with detection results
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=inactivity_threshold_days)
            current_time = datetime.utcnow()

            # Query for VIP users with active subscriptions who haven't been active recently
            # Using proper joins with UserStats for last_activity_at
            query = select(User, VipSubscription, UserStats).join(
                VipSubscription, User.id == VipSubscription.user_id
            ).outerjoin(
                UserStats, User.id == UserStats.user_id
            ).where(
                and_(
                    User.role == "vip",
                    VipSubscription.expires_at > current_time,
                    or_(
                        UserStats.last_activity_at < cutoff_date,
                        UserStats.last_activity_at.is_(None)
                    )
                )
            )

            result = await self.session.execute(query)
            inactive_records = result.all()

            # Prepare notification data for administrators
            inactive_users_data = []
            admin_notifications = []

            for user, subscription, stats in inactive_records:
                last_activity = stats.last_activity_at if stats else None
                days_inactive = (current_time - (last_activity or subscription.created_at)).days

                user_data = {
                    "user_id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "subscription_expires": subscription.expires_at.isoformat(),
                    "last_activity": last_activity.isoformat() if last_activity else None,
                    "days_inactive": days_inactive,
                    "points": user.points,
                    "level": user.level
                }

                inactive_users_data.append(user_data)

                # Create admin notification for each inactive VIP user
                admin_notification = {
                    "notification_type": "inactive_vip_user",
                    "user_id": user.id,
                    "user_info": user_data,
                    "suggested_actions": [
                        "Send engagement message",
                        "Offer personalized content",
                        "Check subscription satisfaction",
                        "Send retention offer"
                    ]
                }
                admin_notifications.append(admin_notification)

            # Log admin action for inactive user detection
            if inactive_users_data:
                detection_log = AdminActionLog(
                    admin_user_id=1,  # System user ID for automated actions
                    action_type="inactive_vip_detection",
                    action_details={
                        "threshold_days": inactivity_threshold_days,
                        "users_detected": len(inactive_users_data),
                        "detection_time": current_time.isoformat()
                    },
                    status="completed"
                )
                self.session.add(detection_log)
                await self.session.commit()

            logger.info(f"Detected {len(inactive_users_data)} inactive VIP users (threshold: {inactivity_threshold_days} days)")

            return {
                "success": True,
                "message": f"Detected {len(inactive_users_data)} inactive VIP users",
                "inactive_users": inactive_users_data,
                "admin_notifications": admin_notifications,
                "threshold_days": inactivity_threshold_days,
                "action": "inactive_users_detected"
            }

        except Exception as e:
            logger.exception(f"Error detecting inactive VIP users: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to detect inactive users: {str(e)}",
                "error": str(e)
            }

    async def _log_cleanup_operation(
        self,
        user_id: Optional[int],
        cleanup_type: str,
        messages_cleaned: int,
        max_age_hours: Optional[int] = None,
        batch_size: Optional[int] = None,
        execution_time: Optional[float] = None
    ):
        """Log message cleanup operation for auditing."""
        try:
            # Create cleanup log entry
            cleanup_log = MessageCleanupLog(
                user_id=user_id,
                cleanup_type=cleanup_type,
                messages_cleaned=messages_cleaned,
                max_age_hours=max_age_hours,
                batch_size=batch_size,
                execution_time_seconds=execution_time,
                status="completed"
            )

            self.session.add(cleanup_log)
            await self.session.commit()

        except Exception as e:
            logger.warning(f"Failed to log cleanup operation: {str(e)}")

    async def cleanup_old_messages(self, retention_hours: int = 24, batch_size: int = 50) -> Dict[str, Any]:
        """
        Clean up old temporary messages and expired message tracking.

        Args:
            retention_hours: Hours after which messages are considered old
            batch_size: Number of messages to process in each batch

        Returns:
            Dict with cleanup results
        """
        try:
            start_time = datetime.utcnow()
            cutoff_time = start_time - timedelta(hours=retention_hours)
            total_cleaned = 0

            # Clean up MenuManager temporary messages if available
            if hasattr(self._menu_manager, '_temp_messages'):
                current_time = time.time()
                expired_messages = []

                for user_id, (chat_id, message_id, expire_time) in self._menu_manager._temp_messages.items():
                    if current_time >= expire_time:
                        expired_messages.append(user_id)
                        try:
                            # Try to delete the actual message if bot is available
                            if self.bot:
                                await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
                        except Exception as e:
                            logger.debug(f"Could not delete message {message_id} in chat {chat_id}: {e}")

                # Remove expired message tracking
                for user_id in expired_messages:
                    self._menu_manager._temp_messages.pop(user_id, None)

                total_cleaned += len(expired_messages)

            # Use MenuManager's cleanup capabilities if available
            if hasattr(self._menu_manager, 'cleanup_old_messages'):
                cleanup_results = await self._menu_manager.cleanup_old_messages(
                    cutoff_time=cutoff_time,
                    batch_size=batch_size
                )
                total_cleaned += cleanup_results.get("cleaned_count", 0)

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            # Log cleanup operation
            await self._log_cleanup_operation(
                user_id=None,  # System-wide cleanup
                cleanup_type="old_messages",
                messages_cleaned=total_cleaned,
                max_age_hours=retention_hours,
                batch_size=batch_size,
                execution_time=execution_time
            )

            logger.info(f"Cleaned up {total_cleaned} old messages in {execution_time:.2f}s")

            return {
                "success": True,
                "message": f"Cleaned up {total_cleaned} old messages",
                "cleaned_count": total_cleaned,
                "execution_time": execution_time
            }

        except Exception as e:
            logger.exception(f"Error cleaning up old messages: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to cleanup old messages: {str(e)}",
                "error": str(e)
            }

    async def remove_expired_tokens(self, retention_days: int = 30) -> Dict[str, Any]:
        """
        Remove expired and used tokens from the database.

        Args:
            retention_days: Days after which used tokens are considered for cleanup

        Returns:
            Dict with cleanup results
        """
        try:
            start_time = datetime.utcnow()
            cutoff_date = start_time - timedelta(days=retention_days)
            total_removed = 0

            # Clean up expired invite tokens
            invite_token_delete = delete(InviteToken).where(
                or_(
                    and_(
                        InviteToken.expires_at.is_not(None),
                        InviteToken.expires_at < start_time
                    ),
                    and_(
                        InviteToken.used_at.is_not(None),
                        InviteToken.used_at < cutoff_date
                    )
                )
            )
            invite_result = await self.session.execute(invite_token_delete)
            invite_cleaned = invite_result.rowcount

            # Clean up expired subscription tokens
            sub_token_delete = delete(SubscriptionToken).where(
                and_(
                    SubscriptionToken.used_at.is_not(None),
                    SubscriptionToken.used_at < cutoff_date
                )
            )
            sub_result = await self.session.execute(sub_token_delete)
            sub_cleaned = sub_result.rowcount

            # Clean up expired VIP activation tokens
            vip_token_delete = delete(Token).where(
                or_(
                    and_(
                        Token.is_used == True,
                        Token.activated_at.is_not(None),
                        Token.activated_at < cutoff_date
                    ),
                    # Remove very old unused tokens (90 days)
                    Token.generated_at < start_time - timedelta(days=90)
                )
            )
            vip_result = await self.session.execute(vip_token_delete)
            vip_cleaned = vip_result.rowcount

            await self.session.commit()
            total_removed = invite_cleaned + sub_cleaned + vip_cleaned

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            logger.info(f"Removed {total_removed} expired tokens: {invite_cleaned} invite, {sub_cleaned} subscription, {vip_cleaned} VIP tokens")

            return {
                "success": True,
                "message": f"Removed {total_removed} expired tokens",
                "removed_count": total_removed,
                "breakdown": {
                    "invite_tokens": invite_cleaned,
                    "subscription_tokens": sub_cleaned,
                    "vip_tokens": vip_cleaned
                },
                "execution_time": execution_time
            }

        except Exception as e:
            logger.exception(f"Error removing expired tokens: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to remove expired tokens: {str(e)}",
                "error": str(e)
            }

    async def archive_old_analytics(self, retention_days: int = 90) -> Dict[str, Any]:
        """
        Archive old analytics data by cleaning up outdated entries.

        Args:
            retention_days: Days after which analytics entries are considered for cleanup

        Returns:
            Dict with archival results
        """
        try:
            start_time = datetime.utcnow()
            cutoff_date = start_time - timedelta(days=retention_days)
            total_archived = 0

            # Import analytics models conditionally
            try:
                from ..database.narrative_models import FragmentAnalytics, UserJourneyAnalytics
                analytics_available = True
            except ImportError:
                logger.warning("Analytics models not available for cleanup")
                analytics_available = False

            if analytics_available:
                # Archive old fragment analytics that haven't been updated recently
                fragment_stmt = select(FragmentAnalytics).where(
                    FragmentAnalytics.last_analyzed_at < cutoff_date
                )
                fragment_result = await self.session.execute(fragment_stmt)
                old_fragments = fragment_result.scalars().all()

                # Instead of deleting, we could move to archive table or compress data
                # For now, we'll update the last_analyzed_at to mark as processed
                for fragment in old_fragments:
                    fragment.last_analyzed_at = start_time

                # Clean up very old user journey analytics (6+ months)
                very_old_date = start_time - timedelta(days=180)
                old_journeys_delete = delete(UserJourneyAnalytics).where(
                    UserJourneyAnalytics.created_at < very_old_date
                )
                journey_result = await self.session.execute(old_journeys_delete)
                journey_cleaned = journey_result.rowcount

                await self.session.commit()
                total_archived = len(old_fragments) + journey_cleaned

                logger.info(f"Archived {len(old_fragments)} fragment analytics and removed {journey_cleaned} old user journeys")

            # Clean up old admin action logs
            admin_log_delete = delete(AdminActionLog).where(
                AdminActionLog.timestamp < cutoff_date
            )
            admin_result = await self.session.execute(admin_log_delete)
            admin_cleaned = admin_result.rowcount

            # Clean up old message cleanup logs
            cleanup_log_delete = delete(MessageCleanupLog).where(
                MessageCleanupLog.timestamp < cutoff_date
            )
            cleanup_result = await self.session.execute(cleanup_log_delete)
            cleanup_cleaned = cleanup_result.rowcount

            await self.session.commit()

            total_archived += admin_cleaned + cleanup_cleaned
            execution_time = (datetime.utcnow() - start_time).total_seconds()

            return {
                "success": True,
                "message": f"Archived {total_archived} analytics and log entries",
                "archived_count": total_archived,
                "breakdown": {
                    "fragment_analytics": len(old_fragments) if analytics_available else 0,
                    "user_journeys": journey_cleaned if analytics_available else 0,
                    "admin_logs": admin_cleaned,
                    "cleanup_logs": cleanup_cleaned
                },
                "execution_time": execution_time
            }

        except Exception as e:
            logger.exception(f"Error archiving old analytics: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to archive old analytics: {str(e)}",
                "error": str(e)
            }

    async def handle_user_departure(self, user_id: int, chat_id: int) -> Dict[str, Any]:
        """
        Handle user departure from free channel within 5 minutes (Requirement 6.3).

        Args:
            user_id: ID of the user who left
            chat_id: ID of the chat they left

        Returns:
            Dict with departure handling results
        """
        try:
            start_time = datetime.utcnow()

            # Get user information
            user_stmt = select(User).where(User.id == user_id)
            user_result = await self.session.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if not user:
                return {
                    "success": False,
                    "message": f"User {user_id} not found",
                    "action": "user_departure_failed"
                }

            # Log the departure action
            departure_log = AdminActionLog(
                admin_user_id=user_id,  # Self-initiated departure
                action_type="user_departure",
                action_details={
                    "chat_id": chat_id,
                    "user_role": user.role,
                    "departure_time": start_time.isoformat()
                },
                target_user_id=user_id,
                target_entity_type="chat",
                target_entity_id=str(chat_id),
                status="completed"
            )
            self.session.add(departure_log)

            # Check if user has active VIP subscription
            vip_stmt = select(VipSubscription).where(VipSubscription.user_id == user_id)
            vip_result = await self.session.execute(vip_stmt)
            vip_subscription = vip_result.scalar_one_or_none()

            actions_taken = []

            # If VIP user, send retention message
            if vip_subscription and vip_subscription.expires_at and vip_subscription.expires_at > start_time:
                try:
                    # Use CoordinadorCentral to send retention message
                    retention_result = await self.coordinator.ejecutar_flujo(
                        user_id=user_id,
                        accion=AccionUsuario.ADMIN_NARRATIVE_OPERATION,
                        operation_type="retention_message",
                        departure_type="vip_user_departure",
                        chat_id=chat_id
                    )

                    if retention_result.get("success"):
                        actions_taken.append("retention_message_sent")
                    else:
                        logger.warning(f"Failed to send retention message to VIP user {user_id}")

                except Exception as e:
                    logger.exception(f"Error sending retention message to user {user_id}: {str(e)}")

            # Remove pending channel requests if any
            pending_delete = delete(PendingChannelRequest).where(
                and_(
                    PendingChannelRequest.user_id == user_id,
                    PendingChannelRequest.chat_id == chat_id
                )
            )
            pending_result = await self.session.execute(pending_delete)
            if pending_result.rowcount > 0:
                actions_taken.append("pending_requests_cleaned")

            await self.session.commit()

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            logger.info(f"Handled user departure for user {user_id} from chat {chat_id}: {actions_taken}")

            return {
                "success": True,
                "message": f"Handled user departure for user {user_id}",
                "user_id": user_id,
                "chat_id": chat_id,
                "actions_taken": actions_taken,
                "execution_time": execution_time,
                "action": "user_departure_handled"
            }

        except Exception as e:
            logger.exception(f"Error handling user departure for user {user_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to handle user departure: {str(e)}",
                "error": str(e)
            }

    async def _cleanup_old_logs(self, retention_days: int) -> Dict[str, Any]:
        """Clean up old log entries."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

            # Clean up old admin action logs
            admin_log_delete = delete(AdminActionLog).where(
                AdminActionLog.timestamp < cutoff_date
            )
            admin_result = await self.session.execute(admin_log_delete)

            # Clean up old message cleanup logs
            cleanup_log_delete = delete(MessageCleanupLog).where(
                MessageCleanupLog.timestamp < cutoff_date
            )
            cleanup_result = await self.session.execute(cleanup_log_delete)

            await self.session.commit()

            total_cleaned = admin_result.rowcount + cleanup_result.rowcount

            return {
                "success": True,
                "message": f"Cleaned up {total_cleaned} old log entries",
                "cleaned_count": total_cleaned
            }

        except Exception as e:
            logger.exception(f"Error cleaning up old logs: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to cleanup old logs: {str(e)}",
                "error": str(e)
            }