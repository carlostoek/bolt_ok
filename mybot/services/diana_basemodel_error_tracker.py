#!/usr/bin/env python3
"""
Diana BaseModel Comprehensive Error Tracking System

Advanced error tracking system designed specifically to identify, reproduce,
and analyze BaseModel initialization failures in the Diana menu system.
This module provides real-time error capture, dependency injection analysis,
and actionable diagnostic reports.
"""

import asyncio
import logging
import inspect
import traceback
import functools
import json
import time
from typing import Dict, Any, Optional, List, Type, Union, Callable, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
import sys

logger = logging.getLogger(__name__)

@dataclass
class ErrorContext:
    """Comprehensive error context for BaseModel failures."""
    timestamp: datetime = field(default_factory=datetime.now)
    error_id: str = ""
    error_type: str = ""
    error_message: str = ""
    stack_trace: List[str] = field(default_factory=list)
    
    # Function context
    function_name: str = ""
    file_name: str = ""
    line_number: int = 0
    module_name: str = ""
    
    # BaseModel context  
    attempted_class: str = ""
    constructor_args: List[str] = field(default_factory=list)
    constructor_kwargs: Dict[str, Any] = field(default_factory=dict)
    argument_types: Dict[str, str] = field(default_factory=dict)
    
    # Dependency injection context
    session_state: Dict[str, Any] = field(default_factory=dict)
    service_dependencies: List[str] = field(default_factory=list)
    lazy_loaded_services: Dict[str, bool] = field(default_factory=dict)
    
    # Diana-specific context
    menu_operation: str = ""
    user_id: Optional[int] = None
    user_role: Optional[str] = None
    callback_data: Optional[str] = None
    
    # Resolution attempts
    fallback_attempts: List[str] = field(default_factory=list)
    fallback_success: bool = False
    resolution_strategy: Optional[str] = None
    
    # Performance data
    execution_time_ms: float = 0.0
    memory_usage_mb: float = 0.0

@dataclass
class DiagnosticResult:
    """Result of diagnostic analysis."""
    error_id: str
    root_cause: str
    confidence_level: float  # 0.0 to 1.0
    recommended_actions: List[str] = field(default_factory=list)
    related_errors: List[str] = field(default_factory=list)
    reproduction_steps: List[str] = field(default_factory=list)

class BaseModelErrorTracker:
    """
    Comprehensive error tracking system for BaseModel failures.
    
    This system provides:
    - Real-time error capture with full context
    - Dependency injection pattern analysis
    - Session management error detection
    - Automatic error correlation and root cause analysis
    - Actionable diagnostic reports
    - Error reproduction assistance
    """
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.error_contexts: List[ErrorContext] = []
        self.error_patterns: Dict[str, int] = {}
        self.session_issues: List[Dict[str, Any]] = []
        self.dependency_failures: List[Dict[str, Any]] = []
        
        # Analysis cache
        self.diagnostic_cache: Dict[str, DiagnosticResult] = {}
        
        # Setup logging
        if enabled:
            self._setup_error_logging()
    
    def _setup_error_logging(self):
        """Setup specialized error logging for tracking."""
        error_logger = logging.getLogger("diana.basemodel.error_tracker")
        error_logger.setLevel(logging.DEBUG)
        
        # File handler for persistent error logs
        log_file = Path("logs/diana_basemodel_errors.log")
        log_file.parent.mkdir(exist_ok=True)
        
        if not error_logger.handlers:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(
                '[%(asctime)s] %(levelname)s [ERROR_TRACKER] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            error_logger.addHandler(file_handler)
            
            # Also add console handler for immediate feedback
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '🚨 [ERROR_TRACKER] %(message)s'
            ))
            error_logger.addHandler(console_handler)
    
    def capture_error(
        self,
        error: Exception,
        attempted_class: Optional[str] = None,
        constructor_args: List[Any] = None,
        constructor_kwargs: Dict[str, Any] = None,
        additional_context: Dict[str, Any] = None
    ) -> str:
        """
        Capture comprehensive error context for analysis.
        
        Returns:
            Error ID for tracking and correlation
        """
        if not self.enabled:
            return ""
        
        # Generate unique error ID
        error_id = f"BME_{int(time.time() * 1000)}_{len(self.error_contexts)}"
        
        # Create error context
        context = ErrorContext()
        context.error_id = error_id
        context.error_type = type(error).__name__
        context.error_message = str(error)
        context.stack_trace = traceback.format_exception(type(error), error, error.__traceback__)
        
        # Capture caller information
        frame = inspect.currentframe()
        try:
            # Go up the stack to find the actual caller
            for _ in range(3):
                frame = frame.f_back
                if frame is None:
                    break
            
            if frame:
                context.function_name = frame.f_code.co_name
                context.file_name = frame.f_code.co_filename
                context.line_number = frame.f_lineno
                context.module_name = inspect.getmodule(frame).__name__ if inspect.getmodule(frame) else ""
        finally:
            del frame
        
        # BaseModel context
        if attempted_class:
            context.attempted_class = attempted_class
        
        if constructor_args:
            context.constructor_args = [self._safe_repr(arg) for arg in constructor_args]
        
        if constructor_kwargs:
            context.constructor_kwargs = {k: self._safe_repr(v) for k, v in constructor_kwargs.items()}
            context.argument_types = {k: type(v).__name__ for k, v in constructor_kwargs.items()}
        
        # Additional context
        if additional_context:
            if 'session_state' in additional_context:
                context.session_state = additional_context['session_state']
            if 'service_dependencies' in additional_context:
                context.service_dependencies = additional_context['service_dependencies']
            if 'menu_operation' in additional_context:
                context.menu_operation = additional_context['menu_operation']
            if 'user_id' in additional_context:
                context.user_id = additional_context['user_id']
            if 'user_role' in additional_context:
                context.user_role = additional_context['user_role']
            if 'callback_data' in additional_context:
                context.callback_data = additional_context['callback_data']
        
        # Store context
        self.error_contexts.append(context)
        
        # Update error patterns
        pattern_key = f"{context.error_type}:{context.function_name}:{context.attempted_class}"
        self.error_patterns[pattern_key] = self.error_patterns.get(pattern_key, 0) + 1
        
        # Log error
        logger.error(f"BaseModel Error Captured: {error_id}")
        logger.debug(f"Error Details: {context.error_message}")
        logger.debug(f"Function: {context.function_name} in {context.file_name}:{context.line_number}")
        
        return error_id
    
    def track_session_error(
        self,
        error_type: str,
        description: str,
        session_details: Dict[str, Any],
        user_id: Optional[int] = None
    ):
        """Track session-related errors that may cause BaseModel failures."""
        if not self.enabled:
            return
        
        session_error = {
            'timestamp': datetime.now(),
            'error_type': error_type,
            'description': description,
            'session_details': session_details,
            'user_id': user_id
        }
        
        self.session_issues.append(session_error)
        logger.warning(f"Session Error Tracked: {error_type} - {description}")
    
    def track_dependency_failure(
        self,
        service_name: str,
        failure_reason: str,
        context: Dict[str, Any]
    ):
        """Track service dependency injection failures."""
        if not self.enabled:
            return
        
        dependency_failure = {
            'timestamp': datetime.now(),
            'service_name': service_name,
            'failure_reason': failure_reason,
            'context': context
        }
        
        self.dependency_failures.append(dependency_failure)
        logger.warning(f"Dependency Failure Tracked: {service_name} - {failure_reason}")
    
    def analyze_error_patterns(self) -> Dict[str, Any]:
        """Analyze captured errors to identify patterns and root causes."""
        if not self.error_contexts:
            return {'status': 'no_errors', 'message': 'No errors captured yet'}
        
        # Pattern analysis
        pattern_analysis = {
            'most_common_errors': sorted(
                [(pattern, count) for pattern, count in self.error_patterns.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10],
            'error_frequency_by_function': {},
            'error_frequency_by_class': {},
            'common_failure_points': []
        }
        
        # Function-based analysis
        function_errors = {}
        class_errors = {}
        
        for context in self.error_contexts:
            # By function
            func_key = f"{context.function_name}:{context.line_number}"
            function_errors[func_key] = function_errors.get(func_key, 0) + 1
            
            # By class
            if context.attempted_class:
                class_errors[context.attempted_class] = class_errors.get(context.attempted_class, 0) + 1
        
        pattern_analysis['error_frequency_by_function'] = dict(
            sorted(function_errors.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        pattern_analysis['error_frequency_by_class'] = dict(
            sorted(class_errors.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        # Identify failure points in enhanced_diana_menu_system.py
        diana_menu_errors = [
            ctx for ctx in self.error_contexts
            if 'enhanced_diana_menu_system.py' in ctx.file_name
        ]
        
        if diana_menu_errors:
            failure_points = {}
            for ctx in diana_menu_errors:
                point = f"Line {ctx.line_number}: {ctx.function_name}"
                failure_points[point] = failure_points.get(point, 0) + 1
            
            pattern_analysis['diana_menu_failure_points'] = dict(
                sorted(failure_points.items(), key=lambda x: x[1], reverse=True)
            )
        
        return pattern_analysis
    
    def generate_diagnostic_report(self) -> Dict[str, Any]:
        """Generate comprehensive diagnostic report with actionable recommendations."""
        report = {
            'generation_time': datetime.now().isoformat(),
            'summary': {
                'total_errors': len(self.error_contexts),
                'unique_error_patterns': len(self.error_patterns),
                'session_issues': len(self.session_issues),
                'dependency_failures': len(self.dependency_failures)
            },
            'pattern_analysis': self.analyze_error_patterns(),
            'critical_issues': [],
            'recommended_actions': [],
            'reproduction_guides': []
        }
        
        # Identify critical issues
        critical_issues = []
        
        # Check for lines 567, 626, 681, 751 specifically mentioned
        problematic_lines = [567, 626, 681, 751]
        for context in self.error_contexts:
            if any(context.line_number == line for line in problematic_lines):
                critical_issues.append({
                    'issue': f"BaseModel error at line {context.line_number}",
                    'function': context.function_name,
                    'error_type': context.error_type,
                    'frequency': self.error_patterns.get(
                        f"{context.error_type}:{context.function_name}:{context.attempted_class}", 0
                    )
                })
        
        report['critical_issues'] = critical_issues
        
        # Generate recommendations based on analysis
        recommendations = []
        
        if any('MenuResponse' in pattern for pattern in self.error_patterns.keys()):
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'MenuResponse instantiation failures',
                'action': 'Review MenuResponse dataclass definition and ensure all required fields have proper defaults',
                'implementation': 'Check dataclass field definitions and add proper type hints and default values'
            })
        
        if self.session_issues:
            recommendations.append({
                'priority': 'HIGH',
                'issue': 'Database session management errors',
                'action': 'Implement proper session lifecycle management with proper error handling',
                'implementation': 'Add session state validation and error recovery mechanisms'
            })
        
        if self.dependency_failures:
            recommendations.append({
                'priority': 'MEDIUM',
                'issue': 'Service dependency injection failures',
                'action': 'Review lazy loading patterns and service initialization order',
                'implementation': 'Add defensive programming for service dependencies'
            })
        
        report['recommended_actions'] = recommendations
        
        # Create reproduction guides
        reproduction_guides = []
        
        for context in self.error_contexts[-5:]:  # Last 5 errors
            guide = {
                'error_id': context.error_id,
                'reproduction_steps': [
                    f"1. Call {context.function_name}() with arguments:",
                    f"   - Args: {context.constructor_args}",
                    f"   - Kwargs: {list(context.constructor_kwargs.keys()) if context.constructor_kwargs else 'None'}",
                    f"2. Expected error: {context.error_type}: {context.error_message}",
                    f"3. Location: {context.file_name}:{context.line_number}"
                ],
                'context': {
                    'menu_operation': context.menu_operation,
                    'user_role': context.user_role,
                    'callback_data': context.callback_data
                }
            }
            reproduction_guides.append(guide)
        
        report['reproduction_guides'] = reproduction_guides
        
        return report
    
    def save_diagnostic_report(self, filepath: Optional[str] = None) -> str:
        """Save diagnostic report to file."""
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"logs/diana_basemodel_diagnostic_report_{timestamp}.json"
        
        Path(filepath).parent.mkdir(exist_ok=True)
        
        report = self.generate_diagnostic_report()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Diagnostic report saved to: {filepath}")
        return filepath
    
    def _safe_repr(self, value: Any, max_length: int = 100) -> str:
        """Create safe representation of a value for logging."""
        try:
            repr_str = repr(value)
            if len(repr_str) > max_length:
                return repr_str[:max_length] + "..."
            return repr_str
        except:
            return f"<{type(value).__name__} - repr failed>"
    
    def get_error_by_id(self, error_id: str) -> Optional[ErrorContext]:
        """Get specific error context by ID."""
        for context in self.error_contexts:
            if context.error_id == error_id:
                return context
        return None
    
    def clear_errors(self):
        """Clear all captured errors (use with caution)."""
        self.error_contexts.clear()
        self.error_patterns.clear()
        self.session_issues.clear()
        self.dependency_failures.clear()
        self.diagnostic_cache.clear()
        logger.info("All error tracking data cleared")

# Global error tracker instance
_global_error_tracker = BaseModelErrorTracker(enabled=True)

def track_basemodel_error(
    error: Exception,
    attempted_class: Optional[str] = None,
    constructor_args: List[Any] = None,
    constructor_kwargs: Dict[str, Any] = None,
    **additional_context
) -> str:
    """Global function to track BaseModel errors."""
    return _global_error_tracker.capture_error(
        error=error,
        attempted_class=attempted_class,
        constructor_args=constructor_args or [],
        constructor_kwargs=constructor_kwargs or {},
        additional_context=additional_context
    )

def track_session_error(error_type: str, description: str, session_details: Dict[str, Any], user_id: Optional[int] = None):
    """Global function to track session errors."""
    _global_error_tracker.track_session_error(error_type, description, session_details, user_id)

def track_dependency_failure(service_name: str, failure_reason: str, context: Dict[str, Any]):
    """Global function to track dependency failures."""
    _global_error_tracker.track_dependency_failure(service_name, failure_reason, context)

def get_global_error_tracker() -> BaseModelErrorTracker:
    """Get the global error tracker instance."""
    return _global_error_tracker

def generate_error_report() -> Dict[str, Any]:
    """Generate diagnostic report from global tracker."""
    return _global_error_tracker.generate_diagnostic_report()

def save_error_report(filepath: Optional[str] = None) -> str:
    """Save diagnostic report to file."""
    return _global_error_tracker.save_diagnostic_report(filepath)

# Instrumentation decorators
def track_menu_operation(operation_name: str):
    """Decorator to track menu operations for error correlation."""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                # Extract context from function arguments
                context = {'menu_operation': operation_name}
                
                # Try to extract user context
                if args:
                    for arg in args:
                        if hasattr(arg, 'from_user') and hasattr(arg.from_user, 'id'):
                            context['user_id'] = arg.from_user.id
                        if hasattr(arg, 'data'):
                            context['callback_data'] = arg.data
                
                track_basemodel_error(
                    error=e,
                    attempted_class=None,
                    constructor_args=list(args),
                    constructor_kwargs=kwargs,
                    **context
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                context = {'menu_operation': operation_name}
                
                track_basemodel_error(
                    error=e,
                    attempted_class=None,
                    constructor_args=list(args),
                    constructor_kwargs=kwargs,
                    **context
                )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def track_service_dependency(service_name: str):
    """Decorator to track service dependency issues."""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                track_dependency_failure(
                    service_name=service_name,
                    failure_reason=str(e),
                    context={
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys())
                    }
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                track_dependency_failure(
                    service_name=service_name,
                    failure_reason=str(e),
                    context={
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys())
                    }
                )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

if __name__ == "__main__":
    # Self-test
    print("🔍 Diana BaseModel Error Tracking System")
    print("Initializing error tracker...")
    
    tracker = get_global_error_tracker()
    print(f"✅ Error tracker initialized: {tracker.enabled}")
    
    # Simulate an error for testing
    try:
        raise ValueError("Test error for error tracking system")
    except Exception as e:
        error_id = track_basemodel_error(
            error=e,
            attempted_class="TestClass",
            constructor_kwargs={"test_param": "test_value"},
            menu_operation="test_operation"
        )
        print(f"✅ Test error tracked with ID: {error_id}")
    
    # Generate report
    report_path = save_error_report()
    print(f"✅ Diagnostic report saved to: {report_path}")