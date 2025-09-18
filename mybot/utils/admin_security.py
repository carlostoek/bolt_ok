# utils/admin_security.py
"""
Admin permission validation and security utilities for the Channel Administration Module.

This module implements comprehensive admin permission validation following requirements 4.1
(Coordinator Central Integration) and 4.5 (Administrative Analysis and Reports) from the
modulo-admon specification.

Features:
- Multi-level admin permission validation
- Action-based access control
- Security context tracking
- Audit trail integration
- Session management for administrative operations
"""

import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from enum import Enum
from functools import wraps

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from aiogram.types import CallbackQuery, Message

from .user_roles import is_admin
from .config import ADMIN_IDS
from database.admin_models import (
    AdminActionLog,
    AdminSession,
    AdminActionType,
    AdminActionStatus,
)

logger = logging.getLogger(__name__)


class AdminPermissionLevel(Enum):
    """Admin permission levels for hierarchical access control."""

    SUPER_ADMIN = "super_admin"      # Full system access
    ADMIN = "admin"                  # Standard admin operations
    MODERATOR = "moderator"          # Limited moderation capabilities
    VIEWER = "viewer"                # Read-only access to admin panels


class AdminPermissionCategory(Enum):
    """Categories of admin permissions for granular access control."""

    USER_MANAGEMENT = "user_management"
    VIP_MANAGEMENT = "vip_management"
    CHANNEL_MANAGEMENT = "channel_management"
    CONTENT_MANAGEMENT = "content_management"
    FINANCIAL_MANAGEMENT = "financial_management"
    SYSTEM_CONFIGURATION = "system_configuration"
    ANALYTICS_ACCESS = "analytics_access"
    AUTOMATION_MANAGEMENT = "automation_management"


class SecurityContext:
    """Security context for tracking admin operations."""

    def __init__(
        self,
        user_id: int,
        permission_level: AdminPermissionLevel,
        permissions: Set[AdminPermissionCategory],
        session_id: str,
        ip_address: Optional[str] = None
    ):
        self.user_id = user_id
        self.permission_level = permission_level
        self.permissions = permissions
        self.session_id = session_id
        self.ip_address = ip_address
        self.created_at = datetime.utcnow()


# Global security context cache for active admin sessions
_security_contexts: Dict[int, SecurityContext] = {}


def generate_session_id() -> str:
    """Generate a secure session ID for admin operations."""
    return secrets.token_urlsafe(32)


def generate_action_hash(user_id: int, action: str, timestamp: datetime) -> str:
    """Generate a hash for action verification and audit purposes."""
    data = f"{user_id}:{action}:{timestamp.isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()


async def validate_admin_permission(
    user_id: int,
    session: AsyncSession,
    required_permission: AdminPermissionCategory,
    action_type: AdminActionType,
    target_user_id: Optional[int] = None,
    additional_data: Optional[Dict[str, Any]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Comprehensive admin permission validation.

    Args:
        user_id: ID of the user requesting the action
        session: Database session
        required_permission: Required permission category
        action_type: Type of action being performed
        target_user_id: ID of user being acted upon (if applicable)
        additional_data: Additional context data for validation

    Returns:
        Tuple of (is_allowed, error_message)
    """
    try:
        # Basic admin check
        if not await is_admin(user_id, session):
            await _log_security_event(
                session, user_id, action_type, False,
                "User is not an admin", target_user_id, additional_data
            )
            return False, "Acceso denegado: No tienes permisos de administrador"

        # Get or create security context
        security_context = await get_security_context(user_id, session)
        if not security_context:
            return False, "Error: No se pudo establecer contexto de seguridad"

        # Check permission level and category
        if not _has_permission(security_context, required_permission):
            await _log_security_event(
                session, user_id, action_type, False,
                f"Insufficient permission for {required_permission.value}",
                target_user_id, additional_data
            )
            return False, f"Acceso denegado: Permisos insuficientes para {required_permission.value}"

        # Additional validation based on action type
        validation_result = await _validate_specific_action(
            security_context, session, action_type, target_user_id, additional_data
        )

        if not validation_result[0]:
            await _log_security_event(
                session, user_id, action_type, False,
                validation_result[1], target_user_id, additional_data
            )
            return validation_result

        # Log successful validation
        await _log_security_event(
            session, user_id, action_type, True,
            "Permission validation successful", target_user_id, additional_data
        )

        return True, None

    except Exception as e:
        logger.error(f"Error validating admin permission: {e}")
        await _log_security_event(
            session, user_id, action_type, False,
            f"Validation error: {str(e)}", target_user_id, additional_data
        )
        return False, "Error interno de validación de permisos"


async def get_security_context(user_id: int, session: AsyncSession) -> Optional[SecurityContext]:
    """Get or create security context for an admin user."""
    try:
        # Check cache first
        if user_id in _security_contexts:
            context = _security_contexts[user_id]
            # Refresh if context is older than 1 hour
            if datetime.utcnow() - context.created_at < timedelta(hours=1):
                return context

        # Create new security context
        permission_level = await _determine_permission_level(user_id, session)
        permissions = await _get_user_permissions(user_id, session, permission_level)
        session_id = generate_session_id()

        context = SecurityContext(
            user_id=user_id,
            permission_level=permission_level,
            permissions=permissions,
            session_id=session_id
        )

        # Cache the context
        _security_contexts[user_id] = context

        # Log session creation
        await _create_admin_session(session, context)

        return context

    except Exception as e:
        logger.error(f"Error creating security context for user {user_id}: {e}")
        return None


async def _determine_permission_level(user_id: int, session: AsyncSession) -> AdminPermissionLevel:
    """Determine the admin permission level for a user."""
    try:
        # Super admins are defined in ADMIN_IDS config
        if user_id in ADMIN_IDS:
            return AdminPermissionLevel.SUPER_ADMIN

        # Check database for admin status
        from database.models import User
        result = await session.execute(
            select(User.is_admin).where(User.id == user_id)
        )
        is_admin_db = result.scalar_one_or_none()

        if is_admin_db:
            # For now, all database admins get standard admin level
            # TODO: Add admin_level field to User model in future migration
            return AdminPermissionLevel.ADMIN

        return AdminPermissionLevel.VIEWER

    except Exception as e:
        logger.error(f"Error determining permission level for user {user_id}: {e}")
        return AdminPermissionLevel.VIEWER


async def _get_user_permissions(
    user_id: int,
    session: AsyncSession,
    permission_level: AdminPermissionLevel
) -> Set[AdminPermissionCategory]:
    """Get the set of permissions for a user based on their level."""
    permissions = set()

    # Define permission hierarchy
    if permission_level == AdminPermissionLevel.SUPER_ADMIN:
        permissions = set(AdminPermissionCategory)
    elif permission_level == AdminPermissionLevel.ADMIN:
        permissions = {
            AdminPermissionCategory.USER_MANAGEMENT,
            AdminPermissionCategory.VIP_MANAGEMENT,
            AdminPermissionCategory.CHANNEL_MANAGEMENT,
            AdminPermissionCategory.CONTENT_MANAGEMENT,
            AdminPermissionCategory.ANALYTICS_ACCESS,
        }
    elif permission_level == AdminPermissionLevel.MODERATOR:
        permissions = {
            AdminPermissionCategory.USER_MANAGEMENT,
            AdminPermissionCategory.CONTENT_MANAGEMENT,
            AdminPermissionCategory.ANALYTICS_ACCESS,
        }
    elif permission_level == AdminPermissionLevel.VIEWER:
        permissions = {
            AdminPermissionCategory.ANALYTICS_ACCESS,
        }

    # TODO: In future, could load custom permissions from database

    return permissions


def _has_permission(
    security_context: SecurityContext,
    required_permission: AdminPermissionCategory
) -> bool:
    """Check if security context has the required permission."""
    return required_permission in security_context.permissions


async def _validate_specific_action(
    security_context: SecurityContext,
    session: AsyncSession,
    action_type: AdminActionType,
    target_user_id: Optional[int],
    additional_data: Optional[Dict[str, Any]]
) -> Tuple[bool, Optional[str]]:
    """Perform specific validation based on action type."""
    try:
        # Prevent self-targeting for certain actions
        if target_user_id and target_user_id == security_context.user_id:
            sensitive_actions = {
                AdminActionType.USER_BANNED,
                AdminActionType.USER_VIP_REVOKED,
                AdminActionType.ADMIN_PERMISSIONS_REVOKED,
            }
            if action_type in sensitive_actions:
                return False, "No puedes realizar esta acción sobre tu propia cuenta"

        # Validate super admin actions
        if action_type in {
            AdminActionType.SYSTEM_CONFIG_CHANGED,
            AdminActionType.ADMIN_PERMISSIONS_GRANTED,
            AdminActionType.ADMIN_PERMISSIONS_REVOKED,
        }:
            if security_context.permission_level != AdminPermissionLevel.SUPER_ADMIN:
                return False, "Esta acción requiere permisos de super administrador"

        # Validate financial operations
        if action_type in {
            AdminActionType.TOKEN_BATCH_GENERATED,
            AdminActionType.REVENUE_REPORT_GENERATED,
        }:
            if AdminPermissionCategory.FINANCIAL_MANAGEMENT not in security_context.permissions:
                return False, "Permisos insuficientes para operaciones financieras"

        # Rate limiting for bulk operations
        if action_type == AdminActionType.TOKEN_BATCH_GENERATED:
            if additional_data and additional_data.get("token_count", 0) > 100:
                if security_context.permission_level != AdminPermissionLevel.SUPER_ADMIN:
                    return False, "Límite de tokens excedido para tu nivel de permisos"

        return True, None

    except Exception as e:
        logger.error(f"Error in specific action validation: {e}")
        return False, f"Error de validación específica: {str(e)}"


async def _log_security_event(
    session: AsyncSession,
    user_id: int,
    action_type: AdminActionType,
    success: bool,
    message: str,
    target_user_id: Optional[int] = None,
    additional_data: Optional[Dict[str, Any]] = None
):
    """Log security events for audit trail."""
    try:
        action_hash = generate_action_hash(user_id, action_type.value, datetime.utcnow())

        log_entry = AdminActionLog(
            admin_user_id=user_id,
            action_type=action_type,
            target_user_id=target_user_id,
            action_details={
                "message": message,
                "action_hash": action_hash,
                "additional_data": additional_data or {},
            },
            success=success,
            error_message=message if not success else None,
        )

        session.add(log_entry)
        await session.commit()

    except Exception as e:
        logger.error(f"Error logging security event: {e}")


async def _create_admin_session(session: AsyncSession, security_context: SecurityContext):
    """Create an admin session record."""
    try:
        from datetime import timedelta

        # Create session with 8 hour expiration
        expires_at = security_context.created_at + timedelta(hours=8)

        admin_session = AdminSession(
            session_token=security_context.session_id,
            admin_user_id=security_context.user_id,
            authentication_method="telegram",
            created_at=security_context.created_at,
            last_activity_at=security_context.created_at,
            expires_at=expires_at,
            ip_address=security_context.ip_address,
            is_active=True,
            is_elevated=(security_context.permission_level == AdminPermissionLevel.SUPER_ADMIN),
        )

        session.add(admin_session)
        await session.commit()

    except Exception as e:
        logger.error(f"Error creating admin session: {e}")


def require_admin_permission(
    required_permission: AdminPermissionCategory,
    action_type: AdminActionType
):
    """
    Decorator to require specific admin permissions for handler functions.

    Usage:
        @require_admin_permission(AdminPermissionCategory.VIP_MANAGEMENT, AdminActionType.TOKEN_GENERATED)
        async def my_admin_handler(callback: CallbackQuery, session: AsyncSession):
            # Handler implementation
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract callback/message and session from args/kwargs
            callback_or_message = None
            session = None

            for arg in args:
                if isinstance(arg, (CallbackQuery, Message)):
                    callback_or_message = arg
                elif isinstance(arg, AsyncSession):
                    session = arg

            for value in kwargs.values():
                if isinstance(value, (CallbackQuery, Message)):
                    callback_or_message = value
                elif isinstance(value, AsyncSession):
                    session = value

            if not callback_or_message or not session:
                logger.error("Missing callback/message or session in admin permission decorator")
                return

            user_id = callback_or_message.from_user.id

            # Validate permission
            is_allowed, error_message = await validate_admin_permission(
                user_id, session, required_permission, action_type
            )

            if not is_allowed:
                if isinstance(callback_or_message, CallbackQuery):
                    await callback_or_message.answer(error_message, show_alert=True)
                else:
                    await callback_or_message.reply(error_message)
                return

            # Call the original function
            return await func(*args, **kwargs)

        return wrapper
    return decorator


async def clear_security_context(user_id: int):
    """Clear security context for a user (e.g., on logout)."""
    if user_id in _security_contexts:
        del _security_contexts[user_id]
        logger.debug(f"Cleared security context for user {user_id}")


async def get_admin_audit_trail(
    session: AsyncSession,
    user_id: Optional[int] = None,
    action_type: Optional[AdminActionType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100
) -> List[AdminActionLog]:
    """
    Retrieve admin audit trail with filtering options.

    Args:
        session: Database session
        user_id: Filter by specific admin user ID
        action_type: Filter by specific action type
        start_date: Filter actions after this date
        end_date: Filter actions before this date
        limit: Maximum number of records to return

    Returns:
        List of AdminActionLog entries
    """
    try:
        query = select(AdminActionLog)
        conditions = []

        if user_id:
            conditions.append(AdminActionLog.admin_user_id == user_id)

        if action_type:
            conditions.append(AdminActionLog.action_type == action_type)

        if start_date:
            conditions.append(AdminActionLog.timestamp >= start_date)

        if end_date:
            conditions.append(AdminActionLog.timestamp <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(AdminActionLog.timestamp.desc()).limit(limit)

        result = await session.execute(query)
        return result.scalars().all()

    except Exception as e:
        logger.error(f"Error retrieving admin audit trail: {e}")
        return []


# Export key functions and classes
__all__ = [
    "AdminPermissionLevel",
    "AdminPermissionCategory",
    "SecurityContext",
    "validate_admin_permission",
    "require_admin_permission",
    "get_security_context",
    "clear_security_context",
    "get_admin_audit_trail",
]