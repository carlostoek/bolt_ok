"""
Diana Menu Error Tracking System

Comprehensive error tracking and analysis system for Diana menu operations.
Provides centralized error collection, pattern analysis, performance monitoring,
and detailed debugging information for all menu-related errors.
"""

import asyncio
import json
import logging
import time
import traceback
import inspect
from collections import defaultdict, deque
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
from functools import wraps
from typing import Dict, Any, Optional, List, Callable, Union, Set
from pathlib import Path

logger = logging.getLogger(__name__)

class ErrorCategory(Enum):
    """Categories of Diana menu errors."""
    BASEMODEL = "basemodel"
    DATABASE = "database"
    SERVICE = "service"
    MENU_NAVIGATION = "menu_navigation"
    CALLBACK_PROCESSING = "callback_processing"
    CHARACTER_VALIDATION = "character_validation"
    PERFORMANCE = "performance"
    TELEGRAM_API = "telegram_api"
    DEPENDENCY_INJECTION = "dependency_injection"
    UNKNOWN = "unknown"

class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class ErrorContext:
    """Context information for an error."""
    user_id: Optional[int] = None
    menu_type: Optional[str] = None
    operation: Optional[str] = None
    callback_data: Optional[str] = None
    session_active: bool = False
    user_role: Optional[str] = None
    request_params: Dict[str, Any] = field(default_factory=dict)
    system_state: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceMetrics:
    """Performance metrics for an operation."""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_usage: Optional[float] = None
    database_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    def complete(self):
        """Mark the operation as complete and calculate duration."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

@dataclass
class ErrorEvent:
    """Represents a single error event in the Diana menu system."""
    id: str = field(default_factory=lambda: f"err_{int(time.time() * 1000)}")
    timestamp: datetime = field(default_factory=datetime.now)
    category: ErrorCategory = ErrorCategory.UNKNOWN
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    message: str = ""
    exception_type: str = ""
    stack_trace: str = ""
    function_name: str = ""
    file_name: str = ""
    line_number: int = 0
    context: ErrorContext = field(default_factory=ErrorContext)
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    correlation_id: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    resolved: bool = False
    resolution_notes: str = ""

class ErrorPattern:
    """Represents a pattern of errors for correlation analysis."""
    def __init__(self, pattern_id: str):
        self.pattern_id = pattern_id
        self.first_seen = datetime.now()
        self.last_seen = datetime.now()
        self.count = 0
        self.error_ids = []
        self.common_attributes = {}
        self.severity_distribution = defaultdict(int)
        
    def add_error(self, error: ErrorEvent):
        """Add an error to this pattern."""
        self.count += 1
        self.last_seen = error.timestamp
        self.error_ids.append(error.id)
        self.severity_distribution[error.severity.value] += 1
        
        # Keep only last 100 error IDs to prevent memory bloat
        if len(self.error_ids) > 100:
            self.error_ids = self.error_ids[-100:]

class DianaMenuErrorTracker:
    """
    Centralized error tracking system for Diana menu operations.
    
    Features:
    - Comprehensive error collection and categorization
    - Pattern analysis and correlation
    - Performance monitoring
    - Error reporting and analytics
    - Real-time error alerting
    """
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self.errors = deque(maxlen=10000)  # Keep last 10,000 errors
        self.error_patterns = {}
        self.performance_history = deque(maxlen=1000)
        self.active_operations = {}
        
        # Error categorization rules
        self.categorization_rules = self._build_categorization_rules()
        
        # Performance thresholds
        self.performance_thresholds = {
            'menu_response': 1.0,  # 1 second
            'database_query': 0.5,  # 500ms
            'character_validation': 0.3,  # 300ms
            'callback_processing': 0.8,  # 800ms
        }
        
        # Error rate thresholds
        self.error_rate_thresholds = {
            'critical': 1,  # 1 critical error per minute
            'high': 5,      # 5 high severity errors per minute
            'medium': 20,   # 20 medium severity errors per minute
        }
        
        # Statistics
        self.stats = {
            'total_errors': 0,
            'errors_by_category': defaultdict(int),
            'errors_by_severity': defaultdict(int),
            'errors_by_hour': defaultdict(int),
            'performance_violations': 0,
            'resolved_errors': 0,
        }
        
        logger.info("Diana Menu Error Tracker initialized")
    
    def _build_categorization_rules(self) -> Dict[str, ErrorCategory]:
        """Build rules for automatic error categorization."""
        return {
            # BaseModel errors
            r"BaseModel.*__init__": ErrorCategory.BASEMODEL,
            r"takes 1 positional argument": ErrorCategory.BASEMODEL,
            r"pydantic.*ValidationError": ErrorCategory.BASEMODEL,
            r"MenuResponse.*initialization": ErrorCategory.BASEMODEL,
            
            # Database errors
            r"Cannot operate on a closed database": ErrorCategory.DATABASE,
            r"sqlalchemy.*IntegrityError": ErrorCategory.DATABASE,
            r"sqlalchemy.*OperationalError": ErrorCategory.DATABASE,
            r"AsyncSession.*closed": ErrorCategory.DATABASE,
            r"connection.*closed": ErrorCategory.DATABASE,
            
            # Service errors
            r"EnhancedUserService": ErrorCategory.SERVICE,
            r"DianaCharacterValidator": ErrorCategory.SERVICE,
            r"NotificationService": ErrorCategory.SERVICE,
            r"dependency injection": ErrorCategory.DEPENDENCY_INJECTION,
            
            # Menu navigation errors
            r"menu.*navigation": ErrorCategory.MENU_NAVIGATION,
            r"keyboard.*generation": ErrorCategory.MENU_NAVIGATION,
            r"menu.*template": ErrorCategory.MENU_NAVIGATION,
            
            # Callback processing
            r"callback.*query": ErrorCategory.CALLBACK_PROCESSING,
            r"CallbackQuery.*processing": ErrorCategory.CALLBACK_PROCESSING,
            r"callback.*data": ErrorCategory.CALLBACK_PROCESSING,
            
            # Character validation
            r"character.*consistency": ErrorCategory.CHARACTER_VALIDATION,
            r"CharacterValidationResult": ErrorCategory.CHARACTER_VALIDATION,
            r"Diana.*personality": ErrorCategory.CHARACTER_VALIDATION,
            
            # Telegram API errors
            r"TelegramAPIError": ErrorCategory.TELEGRAM_API,
            r"aiogram.*exception": ErrorCategory.TELEGRAM_API,
            r"telegram.*timeout": ErrorCategory.TELEGRAM_API,
        }
    
    def _categorize_error(self, exception: Exception, message: str, stack_trace: str) -> ErrorCategory:
        """Automatically categorize an error based on its characteristics."""
        import re
        
        # Check exception type first
        exception_name = type(exception).__name__
        
        # Check all text content
        search_text = f"{exception_name} {message} {stack_trace}".lower()
        
        for pattern, category in self.categorization_rules.items():
            if re.search(pattern.lower(), search_text):
                return category
                
        return ErrorCategory.UNKNOWN
    
    def _determine_severity(self, category: ErrorCategory, exception: Exception) -> ErrorSeverity:
        """Determine error severity based on category and exception type."""
        severity_map = {
            ErrorCategory.DATABASE: {
                'IntegrityError': ErrorSeverity.HIGH,
                'OperationalError': ErrorSeverity.CRITICAL,
                'TimeoutError': ErrorSeverity.HIGH,
                'default': ErrorSeverity.MEDIUM
            },
            ErrorCategory.BASEMODEL: {
                'TypeError': ErrorSeverity.HIGH,
                'ValidationError': ErrorSeverity.MEDIUM,
                'default': ErrorSeverity.MEDIUM
            },
            ErrorCategory.SERVICE: {
                'AttributeError': ErrorSeverity.HIGH,
                'ImportError': ErrorSeverity.CRITICAL,
                'default': ErrorSeverity.MEDIUM
            },
            ErrorCategory.TELEGRAM_API: {
                'TelegramAPIError': ErrorSeverity.HIGH,
                'NetworkError': ErrorSeverity.MEDIUM,
                'default': ErrorSeverity.MEDIUM
            },
            ErrorCategory.PERFORMANCE: {
                'default': ErrorSeverity.LOW
            },
        }
        
        exception_name = type(exception).__name__
        category_rules = severity_map.get(category, {'default': ErrorSeverity.MEDIUM})
        
        return category_rules.get(exception_name, category_rules['default'])
    
    async def track_error(
        self,
        exception: Exception,
        context: ErrorContext,
        performance: Optional[PerformanceMetrics] = None,
        correlation_id: Optional[str] = None,
        tags: Optional[Set[str]] = None
    ) -> ErrorEvent:
        """Track a new error event."""
        async with self._lock:
            # Extract error information
            stack_trace = traceback.format_exc()
            frame = inspect.currentframe().f_back
            
            error = ErrorEvent(
                category=self._categorize_error(exception, str(exception), stack_trace),
                severity=self._determine_severity(
                    self._categorize_error(exception, str(exception), stack_trace), 
                    exception
                ),
                message=str(exception),
                exception_type=type(exception).__name__,
                stack_trace=stack_trace,
                function_name=frame.f_code.co_name if frame else "",
                file_name=frame.f_code.co_filename if frame else "",
                line_number=frame.f_lineno if frame else 0,
                context=context,
                performance=performance or PerformanceMetrics(),
                correlation_id=correlation_id,
                tags=tags or set()
            )
            
            # Add to error collection
            self.errors.append(error)
            
            # Update statistics
            self.stats['total_errors'] += 1
            self.stats['errors_by_category'][error.category.value] += 1
            self.stats['errors_by_severity'][error.severity.value] += 1
            self.stats['errors_by_hour'][datetime.now().hour] += 1
            
            # Check for patterns
            await self._analyze_error_patterns(error)
            
            # Log the error
            log_level = self._get_log_level(error.severity)
            logger.log(log_level, 
                f"Diana Menu Error [{error.category.value}]: {error.message} "
                f"(User: {context.user_id}, Operation: {context.operation})"
            )
            
            return error
    
    def _get_log_level(self, severity: ErrorSeverity) -> int:
        """Get appropriate log level for error severity."""
        level_map = {
            ErrorSeverity.CRITICAL: logging.CRITICAL,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.INFO: logging.DEBUG,
        }
        return level_map.get(severity, logging.WARNING)
    
    async def _analyze_error_patterns(self, error: ErrorEvent):
        """Analyze error for patterns and correlations."""
        # Generate pattern signature
        signature = f"{error.category.value}_{error.exception_type}_{error.function_name}"
        
        if signature not in self.error_patterns:
            self.error_patterns[signature] = ErrorPattern(signature)
        
        pattern = self.error_patterns[signature]
        pattern.add_error(error)
        
        # Check if this is a recurring pattern that needs attention
        if pattern.count >= 5:  # 5 or more occurrences
            time_window = timedelta(minutes=10)
            if pattern.last_seen - pattern.first_seen < time_window:
                logger.warning(
                    f"Diana Menu Error Pattern Detected: {signature} "
                    f"occurred {pattern.count} times in {time_window}"
                )
    
    def track_performance(
        self,
        operation: str,
        duration: float,
        context: ErrorContext,
        metrics: Dict[str, Any] = None
    ):
        """Track performance metrics for an operation."""
        performance = PerformanceMetrics(
            duration=duration,
            **metrics or {}
        )
        
        self.performance_history.append({
            'timestamp': datetime.now(),
            'operation': operation,
            'duration': duration,
            'context': context,
            'metrics': metrics or {}
        })
        
        # Check for performance violations
        threshold = self.performance_thresholds.get(operation)
        if threshold and duration > threshold:
            self.stats['performance_violations'] += 1
            logger.warning(
                f"Diana Menu Performance Violation: {operation} took {duration:.3f}s "
                f"(threshold: {threshold}s, User: {context.user_id})"
            )
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.errors if e.timestamp >= cutoff]
        
        summary = {
            'total_errors': len(recent_errors),
            'time_period_hours': hours,
            'categories': defaultdict(int),
            'severities': defaultdict(int),
            'top_patterns': [],
            'performance_issues': 0,
            'resolved_count': 0,
            'error_rate': len(recent_errors) / max(hours, 1)  # errors per hour
        }
        
        for error in recent_errors:
            summary['categories'][error.category.value] += 1
            summary['severities'][error.severity.value] += 1
            if error.resolved:
                summary['resolved_count'] += 1
            if error.performance.duration and error.performance.duration > 1.0:
                summary['performance_issues'] += 1
        
        # Get top error patterns
        pattern_counts = [
            (pattern_id, pattern.count)
            for pattern_id, pattern in self.error_patterns.items()
            if pattern.last_seen >= cutoff
        ]
        pattern_counts.sort(key=lambda x: x[1], reverse=True)
        summary['top_patterns'] = pattern_counts[:10]
        
        return summary
    
    def get_error_details(self, error_id: str) -> Optional[ErrorEvent]:
        """Get detailed information about a specific error."""
        for error in self.errors:
            if error.id == error_id:
                return error
        return None
    
    def get_correlation_analysis(self, correlation_id: str) -> List[ErrorEvent]:
        """Get all errors with the same correlation ID."""
        return [error for error in self.errors if error.correlation_id == correlation_id]
    
    def resolve_error(self, error_id: str, resolution_notes: str):
        """Mark an error as resolved with notes."""
        for error in self.errors:
            if error.id == error_id:
                error.resolved = True
                error.resolution_notes = resolution_notes
                self.stats['resolved_errors'] += 1
                logger.info(f"Diana Menu Error {error_id} resolved: {resolution_notes}")
                break
    
    def export_errors(self, hours: int = 24, format: str = 'json') -> str:
        """Export error data for analysis."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.errors if e.timestamp >= cutoff]
        
        if format == 'json':
            # Convert to serializable format
            serializable_errors = []
            for error in recent_errors:
                error_dict = asdict(error)
                error_dict['timestamp'] = error.timestamp.isoformat()
                error_dict['category'] = error.category.value
                error_dict['severity'] = error.severity.value
                error_dict['tags'] = list(error.tags)
                serializable_errors.append(error_dict)
            
            return json.dumps(serializable_errors, indent=2, ensure_ascii=False)
        
        return str(recent_errors)
    
    def clear_old_errors(self, days: int = 7):
        """Clear errors older than specified days."""
        cutoff = datetime.now() - timedelta(days=days)
        
        # Filter out old errors
        current_count = len(self.errors)
        self.errors = deque(
            [error for error in self.errors if error.timestamp >= cutoff],
            maxlen=self.errors.maxlen
        )
        
        cleared_count = current_count - len(self.errors)
        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} Diana menu errors older than {days} days")

# Global error tracker instance
_global_error_tracker = None

def get_error_tracker() -> DianaMenuErrorTracker:
    """Get the global Diana menu error tracker instance."""
    global _global_error_tracker
    if _global_error_tracker is None:
        _global_error_tracker = DianaMenuErrorTracker()
    return _global_error_tracker

# Decorator for tracking errors in Diana menu methods
def track_diana_menu_errors(
    operation: Optional[str] = None,
    correlation_id_key: Optional[str] = None,
    context_keys: Optional[List[str]] = None,
    tags: Optional[Set[str]] = None
):
    """
    Decorator to automatically track errors in Diana menu methods.
    
    Args:
        operation: Name of the operation (defaults to function name)
        correlation_id_key: Key to extract correlation ID from function arguments
        context_keys: Keys to extract context information from function arguments
        tags: Additional tags to attach to errors
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracker = get_error_tracker()
            start_time = time.time()
            
            # Extract context information
            context = ErrorContext()
            if context_keys:
                for key in context_keys:
                    if key in kwargs:
                        setattr(context, key, kwargs[key])
            
            # Extract correlation ID
            correlation_id = None
            if correlation_id_key and correlation_id_key in kwargs:
                correlation_id = kwargs[correlation_id_key]
            
            op_name = operation or func.__name__
            
            try:
                result = await func(*args, **kwargs)
                
                # Track performance
                duration = time.time() - start_time
                tracker.track_performance(op_name, duration, context)
                
                return result
                
            except Exception as e:
                # Track the error
                performance = PerformanceMetrics()
                performance.start_time = start_time
                performance.complete()
                
                await tracker.track_error(
                    e, context, performance, correlation_id, tags
                )
                
                # Re-raise the exception
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For synchronous functions, create a simple wrapper
            try:
                return func(*args, **kwargs)
            except Exception as e:
                tracker = get_error_tracker()
                context = ErrorContext()
                
                # Use asyncio to track the error
                loop = None
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                if loop.is_running():
                    # If loop is running, schedule the task
                    asyncio.create_task(tracker.track_error(e, context, None, None, tags))
                else:
                    # If loop is not running, run until complete
                    loop.run_until_complete(tracker.track_error(e, context, None, None, tags))
                
                raise
        
        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator