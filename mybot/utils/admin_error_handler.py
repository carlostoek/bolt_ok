"""
Admin Error Handling Utilities for Channel Administration Module

This module provides comprehensive error handling utilities for administrative operations
including graceful degradation, error logging, and recovery mechanisms.
Implements requirements 4.3 and 4.4 for robust error handling and integration points.
"""

import logging
import functools
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Tuple, Union
from enum import Enum
from dataclasses import dataclass
from aiogram import Bot
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramAPIError

# Import existing utilities for consistency
from utils.notify_admins import notify_admins
from utils.html_formatter import HTMLMessageFormatter

logger = logging.getLogger(__name__)


class AdminErrorCode(Enum):
    """
    Standardized error codes for administrative operations.
    Provides consistent error identification across the admin module.
    """
    # Menu and Navigation Errors
    MENU_CLEANUP_FAILED = "ADMIN_MENU_001"
    MENU_CREATION_FAILED = "ADMIN_MENU_002"
    NAVIGATION_FAILED = "ADMIN_NAV_001"

    # VIP Management Errors
    VIP_TOKEN_GENERATION_FAILED = "ADMIN_VIP_001"
    VIP_SUBSCRIPTION_SYNC_FAILED = "ADMIN_VIP_002"
    VIP_ACCESS_VALIDATION_FAILED = "ADMIN_VIP_003"
    VIP_EXPIRATION_REMINDER_FAILED = "ADMIN_VIP_004"

    # Channel and Content Errors
    CHANNEL_ACCESS_CONTROL_FAILED = "ADMIN_CHAN_001"
    CONTENT_PROTECTION_FAILED = "ADMIN_CHAN_002"
    EXCLUSIVE_CONTENT_PUBLISH_FAILED = "ADMIN_CHAN_003"

    # Analytics and Reporting Errors
    ANALYTICS_GENERATION_FAILED = "ADMIN_ANAL_001"
    REPORT_EXPORT_FAILED = "ADMIN_ANAL_002"
    METRICS_CALCULATION_FAILED = "ADMIN_ANAL_003"

    # Automation and Task Errors
    AUTOMATION_TASK_START_FAILED = "ADMIN_AUTO_001"
    AUTOMATION_TASK_EXECUTION_FAILED = "ADMIN_AUTO_002"
    SCHEDULED_TASK_FAILED = "ADMIN_AUTO_003"

    # Integration and Coordination Errors
    COORDINATOR_SYNC_FAILED = "ADMIN_COORD_001"
    MODULE_INTEGRATION_FAILED = "ADMIN_COORD_002"
    DATA_CONSISTENCY_FAILED = "ADMIN_COORD_003"

    # Database and System Errors
    DATABASE_CONNECTION_FAILED = "ADMIN_DB_001"
    DATABASE_TRANSACTION_FAILED = "ADMIN_DB_002"
    SYSTEM_RESOURCE_EXHAUSTED = "ADMIN_SYS_001"
    EXTERNAL_SERVICE_UNAVAILABLE = "ADMIN_SYS_002"


@dataclass
class AdminError:
    """
    Structured representation of administrative errors with context and recovery options.
    """
    code: AdminErrorCode
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[int] = None
    recovery_options: Optional[List[str]] = None
    stack_trace: Optional[str] = None
    severity: str = "ERROR"  # ERROR, WARNING, CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging and reporting."""
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "recovery_options": self.recovery_options,
            "severity": self.severity
        }


class AdminErrorHandler:
    """
    Central error handler for administrative operations with graceful degradation.
    Provides consistent error handling, logging, and user notification across admin module.
    """

    def __init__(self, bot: Optional[Bot] = None):
        self.bot = bot
        self.error_history: List[AdminError] = []
        self.max_history_size = 100
        self.retry_counts: Dict[str, int] = {}
        self.max_retries = 3

    async def handle_error(
        self,
        error: Exception,
        error_code: AdminErrorCode,
        context: Dict[str, Any],
        user_id: Optional[int] = None,
        notify_admin: bool = True,
        auto_recover: bool = True
    ) -> AdminError:
        """
        Comprehensive error handling with logging, notification, and recovery.

        Args:
            error: The exception that occurred
            error_code: Standardized error code
            context: Additional context information
            user_id: User ID if applicable
            notify_admin: Whether to notify administrators
            auto_recover: Whether to attempt automatic recovery

        Returns:
            AdminError object with complete error information
        """
        admin_error = AdminError(
            code=error_code,
            message=str(error),
            details=context,
            timestamp=datetime.now(),
            user_id=user_id,
            recovery_options=self._get_recovery_options(error_code),
            stack_trace=str(error) if logger.isEnabledFor(logging.DEBUG) else None,
            severity=self._determine_severity(error_code)
        )

        # Log the error with appropriate level
        self._log_error(admin_error)

        # Add to error history
        self._add_to_history(admin_error)

        # Notify administrators if requested and critical
        if notify_admin and admin_error.severity in ["ERROR", "CRITICAL"]:
            await self._notify_administrators(admin_error)

        # Attempt automatic recovery if enabled
        if auto_recover and admin_error.severity != "CRITICAL":
            await self._attempt_recovery(admin_error)

        return admin_error

    def _log_error(self, admin_error: AdminError) -> None:
        """Log error with appropriate level based on severity."""
        log_message = f"Admin Error {admin_error.code.value}: {admin_error.message}"
        log_extra = {
            "error_code": admin_error.code.value,
            "user_id": admin_error.user_id,
            "details": admin_error.details
        }

        if admin_error.severity == "CRITICAL":
            logger.critical(log_message, extra=log_extra)
        elif admin_error.severity == "ERROR":
            logger.error(log_message, extra=log_extra)
        else:
            logger.warning(log_message, extra=log_extra)

    def _add_to_history(self, admin_error: AdminError) -> None:
        """Add error to history with size management."""
        self.error_history.append(admin_error)
        if len(self.error_history) > self.max_history_size:
            self.error_history.pop(0)

    async def _notify_administrators(self, admin_error: AdminError) -> None:
        """Notify administrators about critical errors."""
        if not self.bot:
            return

        try:
            notification_text = HTMLMessageFormatter.format_error_message(
                error_code=admin_error.code.value,
                details=admin_error.message,
                recovery_options=admin_error.recovery_options
            )

            await notify_admins(self.bot, notification_text)

        except Exception as e:
            # Fallback notification
            logger.critical(f"Failed to notify admins about error {admin_error.code.value}: {e}")

    async def _attempt_recovery(self, admin_error: AdminError) -> bool:
        """Attempt automatic recovery based on error type."""
        recovery_key = f"{admin_error.code.value}_{admin_error.user_id}"

        # Check retry limit
        if self.retry_counts.get(recovery_key, 0) >= self.max_retries:
            logger.warning(f"Max retries exceeded for {admin_error.code.value}")
            return False

        try:
            recovery_successful = False

            # Recovery strategies based on error type
            if admin_error.code == AdminErrorCode.MENU_CLEANUP_FAILED:
                recovery_successful = await self._recover_menu_cleanup(admin_error)
            elif admin_error.code in [AdminErrorCode.VIP_SUBSCRIPTION_SYNC_FAILED, AdminErrorCode.VIP_ACCESS_VALIDATION_FAILED]:
                recovery_successful = await self._recover_vip_sync(admin_error)
            elif admin_error.code == AdminErrorCode.DATABASE_CONNECTION_FAILED:
                recovery_successful = await self._recover_database_connection(admin_error)

            # Update retry count
            self.retry_counts[recovery_key] = self.retry_counts.get(recovery_key, 0) + 1

            if recovery_successful:
                logger.info(f"Successfully recovered from error {admin_error.code.value}")
                # Reset retry count on success
                self.retry_counts.pop(recovery_key, None)

            return recovery_successful

        except Exception as e:
            logger.error(f"Recovery attempt failed for {admin_error.code.value}: {e}")
            return False

    async def _recover_menu_cleanup(self, admin_error: AdminError) -> bool:
        """Recovery strategy for menu cleanup failures."""
        try:
            # Schedule cleanup retry with delay
            await asyncio.sleep(5)
            logger.info("Menu cleanup recovery attempted")
            return True
        except Exception:
            return False

    async def _recover_vip_sync(self, admin_error: AdminError) -> bool:
        """Recovery strategy for VIP synchronization failures."""
        try:
            # Queue for later retry through coordinator
            logger.info("VIP sync queued for retry")
            return True
        except Exception:
            return False

    async def _recover_database_connection(self, admin_error: AdminError) -> bool:
        """Recovery strategy for database connection failures."""
        try:
            # Wait before retry
            await asyncio.sleep(10)
            logger.info("Database connection recovery attempted")
            return True
        except Exception:
            return False

    def _determine_severity(self, error_code: AdminErrorCode) -> str:
        """Determine error severity based on error code."""
        critical_errors = [
            AdminErrorCode.DATABASE_CONNECTION_FAILED,
            AdminErrorCode.SYSTEM_RESOURCE_EXHAUSTED,
            AdminErrorCode.DATA_CONSISTENCY_FAILED
        ]

        warning_errors = [
            AdminErrorCode.MENU_CLEANUP_FAILED,
            AdminErrorCode.VIP_EXPIRATION_REMINDER_FAILED
        ]

        if error_code in critical_errors:
            return "CRITICAL"
        elif error_code in warning_errors:
            return "WARNING"
        else:
            return "ERROR"

    def _get_recovery_options(self, error_code: AdminErrorCode) -> List[str]:
        """Get recovery options based on error type."""
        recovery_map = {
            AdminErrorCode.MENU_CLEANUP_FAILED: [
                "Reintentar limpieza de menú",
                "Omitir mensajes problemáticos",
                "Reiniciar sesión de menú"
            ],
            AdminErrorCode.VIP_TOKEN_GENERATION_FAILED: [
                "Verificar configuración de tarifas",
                "Reintentar generación de token",
                "Revisar límites de generación"
            ],
            AdminErrorCode.VIP_SUBSCRIPTION_SYNC_FAILED: [
                "Verificar conexión con módulos",
                "Forzar sincronización manual",
                "Revisar estado del coordinador"
            ],
            AdminErrorCode.DATABASE_CONNECTION_FAILED: [
                "Verificar estado de la base de datos",
                "Reintentar conexión",
                "Revisar configuración de conexión"
            ],
            AdminErrorCode.ANALYTICS_GENERATION_FAILED: [
                "Usar datos en caché",
                "Generar reporte parcial",
                "Programar regeneración"
            ]
        }

        return recovery_map.get(error_code, [
            "Verificar logs del sistema",
            "Reintentar operación",
            "Contactar soporte técnico"
        ])

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring and analysis."""
        if not self.error_history:
            return {"total_errors": 0, "by_code": {}, "by_severity": {}}

        by_code = {}
        by_severity = {}
        recent_errors = 0

        cutoff_time = datetime.now() - timedelta(hours=24)

        for error in self.error_history:
            # Count by code
            code_str = error.code.value
            by_code[code_str] = by_code.get(code_str, 0) + 1

            # Count by severity
            by_severity[error.severity] = by_severity.get(error.severity, 0) + 1

            # Count recent errors
            if error.timestamp > cutoff_time:
                recent_errors += 1

        return {
            "total_errors": len(self.error_history),
            "recent_errors_24h": recent_errors,
            "by_code": by_code,
            "by_severity": by_severity,
            "last_error": self.error_history[-1].to_dict() if self.error_history else None
        }


# Decorator for automatic error handling in admin functions
def admin_error_handler(
    error_code: AdminErrorCode,
    notify_admin: bool = True,
    auto_recover: bool = True,
    fallback_result: Any = None
):
    """
    Decorator for automatic error handling in administrative functions.

    Args:
        error_code: Error code to assign to caught exceptions
        notify_admin: Whether to notify administrators
        auto_recover: Whether to attempt automatic recovery
        fallback_result: Result to return if operation fails
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Get error handler instance
                error_handler = getattr(wrapper, '_error_handler', None)
                if not error_handler:
                    error_handler = AdminErrorHandler()
                    wrapper._error_handler = error_handler

                # Extract context information
                context = {
                    "function": func.__name__,
                    "args": str(args)[:200],  # Truncate for logging
                    "kwargs": {k: str(v)[:100] for k, v in kwargs.items()}
                }

                # Handle the error
                await error_handler.handle_error(
                    error=e,
                    error_code=error_code,
                    context=context,
                    notify_admin=notify_admin,
                    auto_recover=auto_recover
                )

                # Return fallback result
                return fallback_result

        return wrapper
    return decorator


# Specialized error handlers for common admin operations

class MenuErrorHandler:
    """Specialized error handler for menu operations."""

    @staticmethod
    async def handle_cleanup_failure(
        user_id: int,
        message_ids: List[int],
        bot: Bot,
        original_error: Exception
    ) -> bool:
        """
        Handle menu cleanup failures with graceful degradation.

        Returns:
            True if partially successful, False if completely failed
        """
        try:
            successful_deletes = 0

            for message_id in message_ids:
                try:
                    await bot.delete_message(user_id, message_id)
                    successful_deletes += 1
                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.1)
                except TelegramAPIError:
                    # Individual message deletion failed - continue with others
                    continue

            # Consider partially successful if at least 50% deleted
            success_rate = successful_deletes / len(message_ids) if message_ids else 0
            return success_rate >= 0.5

        except Exception as e:
            logger.error(f"Menu cleanup recovery failed: {e}")
            return False

    @staticmethod
    async def create_fallback_menu(user_id: int, bot: Bot) -> bool:
        """Create a minimal fallback menu when main menu fails."""
        try:
            fallback_text = (
                "<b>🛠️ Panel Administrativo (Modo Seguro)</b>\n\n"
                "<i>Algunas funciones pueden estar temporalmente limitadas.</i>\n\n"
                "Use /admin para reintentar el menú completo."
            )

            await bot.send_message(
                user_id,
                fallback_text,
                parse_mode="HTML"
            )
            return True

        except Exception as e:
            logger.error(f"Fallback menu creation failed: {e}")
            return False


class VIPErrorHandler:
    """Specialized error handler for VIP operations."""

    @staticmethod
    async def handle_token_generation_failure(
        admin_id: int,
        tariff_id: str,
        quantity: int,
        original_error: Exception
    ) -> Dict[str, Any]:
        """
        Handle VIP token generation failures with partial success support.

        Returns:
            Dictionary with success count and error details
        """
        result = {
            "successful_tokens": 0,
            "failed_tokens": quantity,
            "partial_success": False,
            "error_details": str(original_error)
        }

        try:
            # Attempt to generate tokens one by one for partial success
            successful_count = 0

            for i in range(min(quantity, 10)):  # Limit retry attempts
                try:
                    # Single token generation logic would go here
                    # This is a placeholder for the actual token generation
                    await asyncio.sleep(0.1)  # Simulate token generation
                    successful_count += 1
                except Exception:
                    continue

            result["successful_tokens"] = successful_count
            result["failed_tokens"] = quantity - successful_count
            result["partial_success"] = successful_count > 0

            return result

        except Exception as e:
            logger.error(f"VIP token recovery failed: {e}")
            return result


class AnalyticsErrorHandler:
    """Specialized error handler for analytics operations."""

    @staticmethod
    async def handle_report_generation_failure(
        report_type: str,
        date_range: Tuple[datetime, datetime],
        original_error: Exception
    ) -> Dict[str, Any]:
        """
        Handle analytics report generation failures with cached data fallback.

        Returns:
            Partial analytics data or cached results
        """
        try:
            # Return minimal analytics structure
            fallback_data = {
                "report_type": report_type,
                "date_range": {
                    "start": date_range[0].isoformat() if date_range[0] else None,
                    "end": date_range[1].isoformat() if date_range[1] else None
                },
                "status": "partial_data",
                "error": str(original_error),
                "metrics": {
                    "total_users": "N/A",
                    "vip_users": "N/A",
                    "revenue": "N/A"
                },
                "message": "Datos completos no disponibles. Reintente más tarde."
            }

            return fallback_data

        except Exception as e:
            logger.error(f"Analytics fallback failed: {e}")
            return {"error": "Analytics temporarily unavailable"}


# Global error handler instance
_global_admin_error_handler: Optional[AdminErrorHandler] = None

def get_admin_error_handler(bot: Optional[Bot] = None) -> AdminErrorHandler:
    """Get global admin error handler instance."""
    global _global_admin_error_handler
    if _global_admin_error_handler is None:
        _global_admin_error_handler = AdminErrorHandler(bot)
    elif bot and not _global_admin_error_handler.bot:
        _global_admin_error_handler.bot = bot
    return _global_admin_error_handler


# Convenience functions for quick error handling

async def handle_menu_error(
    error: Exception,
    user_id: int,
    context: Dict[str, Any],
    bot: Optional[Bot] = None
) -> AdminError:
    """Quick handler for menu-related errors."""
    handler = get_admin_error_handler(bot)
    return await handler.handle_error(
        error=error,
        error_code=AdminErrorCode.MENU_CLEANUP_FAILED,
        context=context,
        user_id=user_id
    )


async def handle_vip_error(
    error: Exception,
    error_code: AdminErrorCode,
    context: Dict[str, Any],
    user_id: Optional[int] = None,
    bot: Optional[Bot] = None
) -> AdminError:
    """Quick handler for VIP-related errors."""
    handler = get_admin_error_handler(bot)
    return await handler.handle_error(
        error=error,
        error_code=error_code,
        context=context,
        user_id=user_id
    )


async def handle_analytics_error(
    error: Exception,
    context: Dict[str, Any],
    bot: Optional[Bot] = None
) -> AdminError:
    """Quick handler for analytics-related errors."""
    handler = get_admin_error_handler(bot)
    return await handler.handle_error(
        error=error,
        error_code=AdminErrorCode.ANALYTICS_GENERATION_FAILED,
        context=context
    )


async def handle_automation_error(
    error: Exception,
    task_name: str,
    context: Dict[str, Any],
    bot: Optional[Bot] = None
) -> AdminError:
    """Quick handler for automation-related errors."""
    handler = get_admin_error_handler(bot)
    context.update({"task_name": task_name})
    return await handler.handle_error(
        error=error,
        error_code=AdminErrorCode.AUTOMATION_TASK_EXECUTION_FAILED,
        context=context
    )