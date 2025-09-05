"""
Diana Menu System Instrumentation

Comprehensive instrumentation system for tracking errors, performance,
and other metrics in the Diana menu system.
"""

import asyncio
import logging
import time
import uuid
from functools import wraps
from typing import Dict, Any, Optional, Callable, Set
from contextlib import asynccontextmanager
from dataclasses import dataclass

from services.diana_menu_error_tracker import (
    get_error_tracker, ErrorContext, PerformanceMetrics,
    track_diana_menu_errors
)
from services.diana_error_dashboard import get_error_dashboard

logger = logging.getLogger(__name__)

@dataclass
class OperationContext:
    """Context for a Diana menu operation."""
    operation_id: str
    operation_name: str
    user_id: Optional[int] = None
    menu_type: Optional[str] = None
    callback_data: Optional[str] = None
    start_time: float = 0.0
    correlation_id: Optional[str] = None

class DianaMenuInstrumentation:
    """
    Instrumentation system for Diana menu operations.
    
    Provides decorators, context managers, and utilities for tracking
    errors, performance, and other metrics in the Diana menu system.
    """
    
    def __init__(self):
        self.error_tracker = get_error_tracker()
        self.dashboard = get_error_dashboard()
        self.active_operations = {}
        
        logger.info("Diana Menu Instrumentation initialized")
    
    @asynccontextmanager
    async def operation_context(
        self,
        operation_name: str,
        user_id: Optional[int] = None,
        menu_type: Optional[str] = None,
        callback_data: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """Context manager for tracking Diana menu operations."""
        operation_id = str(uuid.uuid4())
        
        context = OperationContext(
            operation_id=operation_id,
            operation_name=operation_name,
            user_id=user_id,
            menu_type=menu_type,
            callback_data=callback_data,
            start_time=time.time(),
            correlation_id=correlation_id
        )
        
        self.active_operations[operation_id] = context
        
        try:
            yield context
            
            # Track successful operation
            duration = time.time() - context.start_time
            error_context = ErrorContext(
                user_id=user_id,
                menu_type=menu_type,
                operation=operation_name,
                callback_data=callback_data
            )
            
            self.error_tracker.track_performance(
                operation_name, duration, error_context,
                {'operation_id': operation_id, 'success': True}
            )
            
        except Exception as e:
            # Track failed operation
            duration = time.time() - context.start_time
            error_context = ErrorContext(
                user_id=user_id,
                menu_type=menu_type,
                operation=operation_name,
                callback_data=callback_data
            )
            
            performance = PerformanceMetrics()
            performance.start_time = context.start_time
            performance.complete()
            
            await self.error_tracker.track_error(
                e, error_context, performance, correlation_id, 
                {'operation_id', 'menu_operation'}
            )
            
            raise
        
        finally:
            self.active_operations.pop(operation_id, None)
    
    def track_menu_operation(
        self,
        operation_name: Optional[str] = None,
        menu_type: Optional[str] = None,
        track_performance: bool = True,
        correlation_id_key: Optional[str] = None
    ):
        """
        Decorator for tracking Diana menu operations.
        
        Args:
            operation_name: Name of the operation (defaults to function name)
            menu_type: Type of menu (admin, user, vip, etc.)
            track_performance: Whether to track performance metrics
            correlation_id_key: Key to extract correlation ID from function arguments
        """
        def decorator(func: Callable) -> Callable:
            op_name = operation_name or func.__name__
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Extract user context
                user_id = self._extract_user_id(args, kwargs)
                callback_data = self._extract_callback_data(args, kwargs)
                correlation_id = kwargs.get(correlation_id_key) if correlation_id_key else None
                
                async with self.operation_context(
                    op_name, user_id, menu_type, callback_data, correlation_id
                ) as context:
                    return await func(*args, **kwargs)
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # For sync functions, use the error tracking decorator
                return track_diana_menu_errors(
                    operation=op_name,
                    correlation_id_key=correlation_id_key,
                    context_keys=['user_id', 'menu_type'],
                    tags={'menu_operation', menu_type or 'unknown'}
                )(func)(*args, **kwargs)
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def track_basemodel_operation(
        self,
        model_name: Optional[str] = None,
        operation_type: str = "initialization"
    ):
        """
        Decorator specifically for tracking BaseModel operations.
        """
        def decorator(func: Callable) -> Callable:
            model = model_name or "BaseModel"
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                operation_name = f"{model}_{operation_type}"
                
                try:
                    start_time = time.time()
                    result = await func(*args, **kwargs)
                    
                    # Track successful BaseModel operation
                    duration = time.time() - start_time
                    context = ErrorContext(operation=operation_name)
                    self.error_tracker.track_performance(
                        operation_name, duration, context,
                        {'model': model, 'operation_type': operation_type, 'success': True}
                    )
                    
                    return result
                
                except Exception as e:
                    # Track BaseModel error with specific context
                    duration = time.time() - start_time
                    context = ErrorContext(operation=operation_name)
                    performance = PerformanceMetrics()
                    performance.start_time = start_time
                    performance.complete()
                    
                    await self.error_tracker.track_error(
                        e, context, performance, None,
                        {'basemodel_operation', model, operation_type}
                    )
                    
                    raise
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                operation_name = f"{model}_{operation_type}"
                
                try:
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    
                    # Track successful operation
                    duration = time.time() - start_time
                    context = ErrorContext(operation=operation_name)
                    self.error_tracker.track_performance(
                        operation_name, duration, context,
                        {'model': model, 'operation_type': operation_type, 'success': True}
                    )
                    
                    return result
                
                except Exception as e:
                    # Track error synchronously
                    context = ErrorContext(operation=operation_name)
                    
                    # Use asyncio to track the error
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(self.error_tracker.track_error(
                                e, context, None, None,
                                {'basemodel_operation', model, operation_type}
                            ))
                        else:
                            loop.run_until_complete(self.error_tracker.track_error(
                                e, context, None, None,
                                {'basemodel_operation', model, operation_type}
                            ))
                    except Exception:
                        logger.error(f"Failed to track BaseModel error: {e}")
                    
                    raise
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def track_database_operation(
        self,
        operation_type: str = "query",
        table_name: Optional[str] = None
    ):
        """
        Decorator for tracking database operations.
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                operation_name = f"db_{operation_type}"
                if table_name:
                    operation_name += f"_{table_name}"
                
                try:
                    start_time = time.time()
                    result = await func(*args, **kwargs)
                    
                    # Track successful database operation
                    duration = time.time() - start_time
                    context = ErrorContext(operation=operation_name)
                    self.error_tracker.track_performance(
                        operation_name, duration, context,
                        {'operation_type': operation_type, 'table': table_name, 'success': True}
                    )
                    
                    return result
                
                except Exception as e:
                    # Track database error
                    duration = time.time() - start_time
                    context = ErrorContext(operation=operation_name)
                    performance = PerformanceMetrics()
                    performance.start_time = start_time
                    performance.complete()
                    
                    await self.error_tracker.track_error(
                        e, context, performance, None,
                        {'database_operation', operation_type, table_name or 'unknown'}
                    )
                    
                    raise
            
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                # For sync database operations, similar pattern
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    operation_name = f"db_{operation_type}"
                    if table_name:
                        operation_name += f"_{table_name}"
                    
                    try:
                        start_time = time.time()
                        result = func(*args, **kwargs)
                        
                        duration = time.time() - start_time
                        context = ErrorContext(operation=operation_name)
                        self.error_tracker.track_performance(
                            operation_name, duration, context,
                            {'operation_type': operation_type, 'table': table_name, 'success': True}
                        )
                        
                        return result
                    
                    except Exception as e:
                        context = ErrorContext(operation=operation_name)
                        
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                asyncio.create_task(self.error_tracker.track_error(
                                    e, context, None, None,
                                    {'database_operation', operation_type, table_name or 'unknown'}
                                ))
                        except Exception:
                            logger.error(f"Failed to track database error: {e}")
                        
                        raise
                
                return sync_wrapper
        
        return decorator
    
    def _extract_user_id(self, args, kwargs) -> Optional[int]:
        """Extract user ID from function arguments."""
        # Check kwargs first
        if 'user_id' in kwargs:
            return kwargs['user_id']
        
        # Check for common parameter names
        for param_name in ['callback', 'message', 'update']:
            if param_name in kwargs:
                param = kwargs[param_name]
                if hasattr(param, 'from_user') and hasattr(param.from_user, 'id'):
                    return param.from_user.id
        
        # Check positional arguments
        for arg in args:
            if hasattr(arg, 'from_user') and hasattr(arg.from_user, 'id'):
                return arg.from_user.id
            elif hasattr(arg, 'user_id'):
                return getattr(arg, 'user_id', None)
        
        return None
    
    def _extract_callback_data(self, args, kwargs) -> Optional[str]:
        """Extract callback data from function arguments."""
        # Check for CallbackQuery in arguments
        for arg in list(args) + list(kwargs.values()):
            if hasattr(arg, 'data'):
                return getattr(arg, 'data', None)
        
        return kwargs.get('callback_data')
    
    async def get_operation_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get statistics about tracked operations."""
        active_ops = len(self.active_operations)
        
        # Get error and performance stats from dashboard
        metrics = await self.dashboard.get_dashboard_metrics(hours)
        performance_reports = await self.dashboard.get_performance_report(hours)
        
        return {
            'active_operations': active_ops,
            'total_errors': metrics.total_errors,
            'error_rate_per_hour': metrics.error_rate_per_hour,
            'performance_violations': metrics.performance_violations,
            'top_slow_operations': [
                {
                    'operation': p.operation,
                    'average_duration': p.average_duration,
                    'p95_duration': p.p95_duration,
                    'error_rate': p.error_rate
                }
                for p in performance_reports[:5]
            ]
        }

# Global instrumentation instance
_global_instrumentation = None

def get_diana_instrumentation() -> DianaMenuInstrumentation:
    """Get the global Diana menu instrumentation instance."""
    global _global_instrumentation
    if _global_instrumentation is None:
        _global_instrumentation = DianaMenuInstrumentation()
    return _global_instrumentation

# Convenience decorators
def track_menu_operation(
    operation_name: Optional[str] = None,
    menu_type: Optional[str] = None,
    track_performance: bool = True
):
    """Convenience decorator for tracking menu operations."""
    instrumentation = get_diana_instrumentation()
    return instrumentation.track_menu_operation(
        operation_name, menu_type, track_performance
    )

def track_basemodel_init(model_name: Optional[str] = None):
    """Convenience decorator for tracking BaseModel initialization."""
    instrumentation = get_diana_instrumentation()
    return instrumentation.track_basemodel_operation(model_name, "initialization")

def track_database_query(table_name: Optional[str] = None):
    """Convenience decorator for tracking database queries."""
    instrumentation = get_diana_instrumentation()
    return instrumentation.track_database_operation("query", table_name)

def track_database_insert(table_name: Optional[str] = None):
    """Convenience decorator for tracking database inserts."""
    instrumentation = get_diana_instrumentation()
    return instrumentation.track_database_operation("insert", table_name)

def track_database_update(table_name: Optional[str] = None):
    """Convenience decorator for tracking database updates."""
    instrumentation = get_diana_instrumentation()
    return instrumentation.track_database_operation("update", table_name)