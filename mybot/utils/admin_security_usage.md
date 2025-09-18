# Admin Security Module Usage Guide

## Overview

The `admin_security.py` module provides comprehensive admin permission validation and security utilities for the Channel Administration Module. It implements requirements 4.1 (Coordinator Central Integration) and 4.5 (Administrative Analysis and Reports).

## Key Features

- **Multi-level Admin Permissions**: Hierarchical permission system (Super Admin, Admin, Moderator, Viewer)
- **Category-based Access Control**: Granular permissions by functional area
- **Security Context Tracking**: Session management and audit trails
- **Action-based Validation**: Specific validation logic per action type
- **Audit Trail**: Comprehensive logging of all admin actions

## Permission Levels

### AdminPermissionLevel
- `SUPER_ADMIN`: Full system access (defined in ADMIN_IDS config)
- `ADMIN`: Standard admin operations
- `MODERATOR`: Limited moderation capabilities
- `VIEWER`: Read-only access to admin panels

### AdminPermissionCategory
- `USER_MANAGEMENT`: User operations (ban, unban, role changes)
- `VIP_MANAGEMENT`: VIP subscription management
- `CHANNEL_MANAGEMENT`: Channel administration
- `CONTENT_MANAGEMENT`: Content posting and moderation
- `FINANCIAL_MANAGEMENT`: Token generation and revenue reports
- `SYSTEM_CONFIGURATION`: System settings and configuration
- `ANALYTICS_ACCESS`: Access to reports and analytics
- `AUTOMATION_MANAGEMENT`: Automated task management

## Usage Examples

### Using the Decorator

```python
from utils.admin_security import require_admin_permission, AdminPermissionCategory
from database.admin_models import AdminActionType

@router.callback_query(F.data == "generate_vip_token")
@require_admin_permission(
    AdminPermissionCategory.VIP_MANAGEMENT,
    AdminActionType.TOKEN_GENERATED
)
async def generate_vip_token(callback: CallbackQuery, session: AsyncSession):
    # Handler implementation - permission validation is automatic
    pass
```

### Manual Permission Validation

```python
from utils.admin_security import validate_admin_permission

async def my_admin_function(user_id: int, session: AsyncSession):
    is_allowed, error_message = await validate_admin_permission(
        user_id=user_id,
        session=session,
        required_permission=AdminPermissionCategory.FINANCIAL_MANAGEMENT,
        action_type=AdminActionType.REVENUE_REPORT_GENERATED,
        additional_data={"report_type": "monthly"}
    )

    if not is_allowed:
        return error_message

    # Proceed with the operation
    pass
```

### Getting Security Context

```python
from utils.admin_security import get_security_context

async def check_admin_permissions(user_id: int, session: AsyncSession):
    context = await get_security_context(user_id, session)
    if context:
        print(f"User {user_id} has level: {context.permission_level}")
        print(f"Permissions: {context.permissions}")
        print(f"Session ID: {context.session_id}")
```

### Audit Trail Access

```python
from utils.admin_security import get_admin_audit_trail
from datetime import datetime, timedelta

async def get_recent_admin_actions(session: AsyncSession):
    # Get all admin actions from the last 24 hours
    start_date = datetime.utcnow() - timedelta(days=1)

    actions = await get_admin_audit_trail(
        session=session,
        start_date=start_date,
        limit=50
    )

    for action in actions:
        print(f"{action.timestamp}: {action.admin_user_id} - {action.action_type}")
```

## Integration with Existing Handlers

The admin security module integrates seamlessly with existing admin handlers. Simply add the decorator to any admin handler function:

```python
# Before (existing pattern)
@router.callback_query(F.data == "admin_vip")
async def vip_menu(callback: CallbackQuery, session: AsyncSession):
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer()
    # ... handler logic

# After (enhanced with admin security)
@router.callback_query(F.data == "admin_vip")
@require_admin_permission(
    AdminPermissionCategory.VIP_MANAGEMENT,
    AdminActionType.VIP_MANAGEMENT_ACCESSED
)
async def vip_menu(callback: CallbackQuery, session: AsyncSession):
    # No need for manual permission check - handled by decorator
    # ... handler logic
```

## Security Features

### Session Tracking
- Automatic session creation for admin users
- 8-hour session expiration
- Session termination logging
- Concurrent session monitoring

### Audit Trail
- All admin actions are logged with detailed context
- Security events tracking (access denied, suspicious activity)
- Performance metrics (execution time, retry counts)
- Error tracking and recovery information

### Action-Specific Validation
- Self-targeting prevention for sensitive actions
- Super admin requirement for critical operations
- Rate limiting for bulk operations
- Context-aware permission checking

## Security Context Caching

Security contexts are cached for 1 hour to improve performance. To manually clear a user's security context:

```python
from utils.admin_security import clear_security_context

await clear_security_context(user_id)
```

## Error Handling

The module provides comprehensive error handling:
- Graceful degradation on database errors
- Detailed error messages for admin users
- Security event logging for all failures
- Automatic retry mechanisms for transient errors

## Future Enhancements

- Add `admin_level` field to User model for more granular control
- Implement IP-based access restrictions
- Add two-factor authentication support
- Implement time-based access restrictions
- Add role-based permission templates