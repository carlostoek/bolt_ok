"""
Handler decorators for consistent Telegram bot handler behavior.
Provides standardized error handling, role validation, state management, and transactions.
"""

import logging
from functools import wraps
from typing import List, Union, Callable, Any, Optional
from aiogram import Bot
from aiogram.types import Message, CallbackQuery, Update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from utils.message_safety import safe_answer, safe_send_message, DEFAULT_SAFE_MESSAGE
from utils.user_roles import get_user_role, is_admin, is_vip_member
from database.models import User

logger = logging.getLogger(__name__)

# Type hints for handler functions
HandlerFunction = Callable[..., Any]


def safe_handler(error_message: str = "Ha ocurrido un error. Inténtalo de nuevo más tarde."):
    """
    Decorator for uniform exception handling with proper logging and user-friendly error messages.
    
    Args:
        error_message: Custom error message to show users when an exception occurs
    """
    def decorator(func: HandlerFunction) -> HandlerFunction:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in handler {func.__name__}: {e}", exc_info=True)
                
                # Try to find the message/callback and session from args
                message_obj = None
                session = None
                
                for arg in args:
                    if isinstance(arg, (Message, CallbackQuery)):
                        message_obj = arg
                    elif isinstance(arg, AsyncSession):
                        session = arg
                
                # Also check kwargs
                if not message_obj:
                    message_obj = kwargs.get('message') or kwargs.get('callback')
                if not session:
                    session = kwargs.get('session')
                
                # Send error message to user if possible
                if message_obj:
                    try:
                        if isinstance(message_obj, Message):
                            await safe_answer(message_obj, error_message)
                        elif isinstance(message_obj, CallbackQuery):
                            await message_obj.answer(error_message, show_alert=True)
                    except Exception as send_error:
                        logger.error(f"Failed to send error message: {send_error}")
                
                # Rollback transaction if session exists
                if session:
                    try:
                        await session.rollback()
                    except Exception as rollback_error:
                        logger.error(f"Failed to rollback session: {rollback_error}")
                
                return None
        
        return wrapper
    return decorator


def require_role(allowed_roles: Union[str, List[str]], 
                 deny_message: str = "No tienes permisos para realizar esta acción."):
    """
    Decorator for consistent permission verification.
    
    Args:
        allowed_roles: Single role string or list of allowed roles ('admin', 'vip', 'free')
        deny_message: Message to show when user doesn't have required permissions
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
    
    def decorator(func: HandlerFunction) -> HandlerFunction:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id, bot, and session from arguments
            user_id = None
            bot = None
            session = None
            message_obj = None
            
            for arg in args:
                if isinstance(arg, (Message, CallbackQuery)):
                    message_obj = arg
                    user_id = arg.from_user.id
                    bot = arg.bot
                elif isinstance(arg, Bot):
                    bot = arg
                elif isinstance(arg, AsyncSession):
                    session = arg
            
            # Check kwargs as well
            if not bot:
                bot = kwargs.get('bot')
            if not session:
                session = kwargs.get('session')
            if not user_id and message_obj:
                user_id = message_obj.from_user.id
            
            if not user_id or not session:
                logger.error(f"Missing user_id or session in {func.__name__}")
                return await func(*args, **kwargs)  # Continue without role check
            
            try:
                # Get user role
                user_role = await get_user_role(bot, user_id, session)
                
                # Check if user has required role
                if user_role not in allowed_roles:
                    # Special case: if user is admin, they can access everything
                    if user_role != "admin" or "admin" not in allowed_roles:
                        logger.warning(f"User {user_id} with role {user_role} tried to access {func.__name__}")
                        
                        if message_obj:
                            if isinstance(message_obj, Message):
                                await safe_answer(message_obj, deny_message)
                            elif isinstance(message_obj, CallbackQuery):
                                await message_obj.answer(deny_message, show_alert=True)
                        
                        return None
                
                # Role check passed, continue with handler
                return await func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in role check for {func.__name__}: {e}")
                # Continue with handler if role check fails
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_state(required_states: Optional[Union[str, List[str]]] = None,
                   invalid_state_message: str = "Comando no válido en el estado actual."):
    """
    Decorator for state validation in user workflows.
    
    Args:
        required_states: Required states for this handler (if None, any state is allowed)
        invalid_state_message: Message to show when user is in invalid state
    """
    if isinstance(required_states, str):
        required_states = [required_states]
    
    def decorator(func: HandlerFunction) -> HandlerFunction:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # If no state validation required, continue
            if not required_states:
                return await func(*args, **kwargs)
            
            # Extract user_id and session
            user_id = None
            session = None
            message_obj = None
            
            for arg in args:
                if isinstance(arg, (Message, CallbackQuery)):
                    message_obj = arg
                    user_id = arg.from_user.id
                elif isinstance(arg, AsyncSession):
                    session = arg
            
            if not session:
                session = kwargs.get('session')
            
            if not user_id or not session:
                # No state validation possible, continue
                return await func(*args, **kwargs)
            
            try:
                # Get user's current state
                user = await session.get(User, user_id)
                current_state = getattr(user, 'menu_state', None) if user else None
                
                # Check if current state is valid
                if current_state not in required_states:
                    logger.debug(f"User {user_id} in state {current_state}, required: {required_states}")
                    
                    if message_obj:
                        if isinstance(message_obj, Message):
                            await safe_answer(message_obj, invalid_state_message)
                        elif isinstance(message_obj, CallbackQuery):
                            await message_obj.answer(invalid_state_message, show_alert=True)
                    
                    return None
                
                # State is valid, continue
                return await func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in state validation for {func.__name__}: {e}")
                # Continue with handler if state check fails
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def transaction(auto_commit: bool = True):
    """
    Decorator for transactional handling in handlers with automatic rollback on errors.
    
    Args:
        auto_commit: Whether to automatically commit the transaction on success
    """
    def decorator(func: HandlerFunction) -> HandlerFunction:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            session = None
            
            # Find session in arguments
            for arg in args:
                if isinstance(arg, AsyncSession):
                    session = arg
                    break
            
            if not session:
                session = kwargs.get('session')
            
            if not session:
                logger.warning(f"No session found for transaction in {func.__name__}")
                return await func(*args, **kwargs)
            
            try:
                # Execute the handler
                result = await func(*args, **kwargs)
                
                # Auto-commit if enabled
                if auto_commit:
                    await session.commit()
                    logger.debug(f"Transaction committed for {func.__name__}")
                
                return result
                
            except SQLAlchemyError as e:
                logger.error(f"Database error in {func.__name__}: {e}")
                try:
                    await session.rollback()
                    logger.debug(f"Transaction rolled back for {func.__name__}")
                except Exception as rollback_error:
                    logger.error(f"Failed to rollback transaction: {rollback_error}")
                raise
                
            except Exception as e:
                logger.error(f"Error in transactional handler {func.__name__}: {e}")
                try:
                    await session.rollback()
                    logger.debug(f"Transaction rolled back for {func.__name__}")
                except Exception as rollback_error:
                    logger.error(f"Failed to rollback transaction: {rollback_error}")
                raise
        
        return wrapper
    return decorator


def track_usage(action_name: str, log_level: int = logging.INFO):
    """
    Decorator for tracking usage and performance of handlers.
    
    Args:
        action_name: Name of the action being tracked
        log_level: Logging level for usage tracking
    """
    def decorator(func: HandlerFunction) -> HandlerFunction:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            import time
            
            start_time = time.time()
            
            # Extract user_id for tracking
            user_id = None
            for arg in args:
                if isinstance(arg, (Message, CallbackQuery)):
                    user_id = arg.from_user.id
                    break
            
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.log(
                    log_level,
                    f"Action '{action_name}' by user {user_id} completed in {execution_time:.3f}s"
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Action '{action_name}' by user {user_id} failed after {execution_time:.3f}s: {e}"
                )
                raise
        
        return wrapper
    return decorator


# Convenience decorators for common combinations
def standard_handler(allowed_roles: Union[str, List[str]] = None,
                     error_message: str = "Ha ocurrido un error. Inténtalo de nuevo más tarde.",
                     action_name: str = None):
    """
    Standard decorator combination for most handlers.
    Combines safe_handler, require_role (if specified), and track_usage (if specified).
    """
    def decorator(func: HandlerFunction) -> HandlerFunction:
        # Apply decorators in order (innermost first)
        decorated_func = func
        
        if action_name:
            decorated_func = track_usage(action_name)(decorated_func)
        
        if allowed_roles:
            decorated_func = require_role(allowed_roles)(decorated_func)
        
        decorated_func = safe_handler(error_message)(decorated_func)
        
        return decorated_func
    
    return decorator


def admin_handler(error_message: str = "Ha ocurrido un error. Inténtalo de nuevo más tarde.",
                  action_name: str = None):
    """Convenience decorator for admin-only handlers."""
    return standard_handler(
        allowed_roles="admin",
        error_message=error_message,
        action_name=action_name
    )


def vip_handler(error_message: str = "Ha ocurrido un error. Inténtalo de nuevo más tarde.",
                action_name: str = None):
    """Convenience decorator for VIP+ handlers (VIP and admin)."""
    return standard_handler(
        allowed_roles=["admin", "vip"],
        error_message=error_message,
        action_name=action_name
    )