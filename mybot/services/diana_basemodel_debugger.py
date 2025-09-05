"""
Diana BaseModel Debugging Infrastructure

Comprehensive debugging system to identify and track BaseModel initialization errors
in the Diana menu system. This module provides detailed logging, type inspection,
error context tracking, and safe fallbacks for BaseModel-related issues.
"""

import logging
import traceback
import inspect
import functools
import time
from typing import Dict, Any, Optional, List, Type, Union, Callable
from datetime import datetime
from dataclasses import dataclass, field
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class BaseModelDebugContext:
    """Context information for BaseModel debugging."""
    timestamp: datetime = field(default_factory=datetime.now)
    function_name: str = ""
    line_number: int = 0
    file_name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    argument_types: Dict[str, str] = field(default_factory=dict)
    stack_trace: List[str] = field(default_factory=list)
    error_message: str = ""
    attempted_class: str = ""
    success: bool = False
    fallback_used: bool = False

class BaseModelDebugger:
    """
    Comprehensive BaseModel debugging system.
    
    Features:
    - Detailed argument logging before instantiation
    - Type inspection and validation
    - Error context tracking with stack traces
    - Safe fallback mechanisms
    - Debug mode activation/deactivation
    - Performance impact monitoring
    """
    
    def __init__(self, debug_enabled: bool = True):
        self.debug_enabled = debug_enabled
        self.debug_contexts: List[BaseModelDebugContext] = []
        self.error_count = 0
        self.success_count = 0
        self.fallback_count = 0
        
        # Configure enhanced logging
        if debug_enabled:
            self._setup_enhanced_logging()
    
    def _setup_enhanced_logging(self):
        """Setup enhanced logging for BaseModel debugging."""
        debug_logger = logging.getLogger("diana.basemodel.debug")
        debug_logger.setLevel(logging.DEBUG)
        
        # Create detailed formatter
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s [BaseModel Debug] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add handler if not already exists
        if not debug_logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            debug_logger.addHandler(handler)
    
    @contextmanager
    def debug_context(self, class_name: str, caller_info: Optional[Dict[str, Any]] = None):
        """Context manager for tracking BaseModel instantiation."""
        context = BaseModelDebugContext()
        context.attempted_class = class_name
        context.timestamp = datetime.now()
        
        # Capture caller information
        if caller_info:
            context.function_name = caller_info.get('function_name', '')
            context.file_name = caller_info.get('file_name', '')
            context.line_number = caller_info.get('line_number', 0)
        else:
            # Auto-capture from stack
            frame = inspect.currentframe().f_back
            if frame:
                context.function_name = frame.f_code.co_name
                context.file_name = frame.f_code.co_filename
                context.line_number = frame.f_lineno
        
        # Capture stack trace
        context.stack_trace = traceback.format_stack()
        
        start_time = time.time()
        
        try:
            yield context
            context.success = True
            self.success_count += 1
            
            if self.debug_enabled:
                logger.info(f"✅ BaseModel {class_name} instantiated successfully in {context.function_name}")
                
        except Exception as e:
            context.success = False
            context.error_message = str(e)
            self.error_count += 1
            
            if self.debug_enabled:
                logger.error(f"❌ BaseModel {class_name} instantiation failed in {context.function_name}: {e}")
                logger.debug(f"Debug context: {self._format_debug_context(context)}")
            
            raise
        
        finally:
            context.execution_time = time.time() - start_time
            self.debug_contexts.append(context)
            
            # Keep only last 100 contexts to avoid memory issues
            if len(self.debug_contexts) > 100:
                self.debug_contexts = self.debug_contexts[-100:]
    
    def log_arguments(self, context: BaseModelDebugContext, *args, **kwargs):
        """Log detailed information about arguments passed to BaseModel constructor."""
        if not self.debug_enabled:
            return
        
        # Log positional arguments
        context.arguments['args'] = []
        context.argument_types['args'] = []
        
        for i, arg in enumerate(args):
            arg_info = self._analyze_argument(arg, f"arg_{i}")
            context.arguments['args'].append(arg_info['value'])
            context.argument_types['args'].append(arg_info['type'])
            
            logger.debug(f"  ARG[{i}]: {arg_info['type']} = {arg_info['preview']}")
        
        # Log keyword arguments
        context.arguments['kwargs'] = {}
        context.argument_types['kwargs'] = {}
        
        for key, value in kwargs.items():
            arg_info = self._analyze_argument(value, key)
            context.arguments['kwargs'][key] = arg_info['value']
            context.argument_types['kwargs'][key] = arg_info['type']
            
            logger.debug(f"  KWARG[{key}]: {arg_info['type']} = {arg_info['preview']}")
        
        # Check for common error patterns
        self._check_common_patterns(context, args, kwargs)
    
    def _analyze_argument(self, value: Any, name: str) -> Dict[str, Any]:
        """Analyze a single argument for debugging."""
        arg_type = type(value).__name__
        
        # Create safe preview of the value
        try:
            if isinstance(value, str):
                preview = f"'{value[:50]}{'...' if len(value) > 50 else ''}'"
            elif isinstance(value, (list, tuple)):
                preview = f"{arg_type}(len={len(value)})"
            elif isinstance(value, dict):
                preview = f"dict(keys={list(value.keys())[:5]})"
            else:
                preview = str(value)[:50]
        except:
            preview = f"<{arg_type} - preview failed>"
        
        return {
            'type': arg_type,
            'value': str(value)[:200],  # Truncate for storage
            'preview': preview,
            'is_none': value is None,
            'is_callable': callable(value)
        }
    
    def _check_common_patterns(self, context: BaseModelDebugContext, args, kwargs):
        """Check for common error patterns in BaseModel instantiation."""
        warnings = []
        
        # Check for too many positional arguments
        if len(args) > 1:
            warnings.append(f"⚠️ Multiple positional arguments detected: {len(args)} args")
        
        # Check for mixed args and kwargs that might conflict
        if args and kwargs:
            warnings.append("⚠️ Both positional and keyword arguments provided")
        
        # Check for None values that might cause issues
        none_args = [i for i, arg in enumerate(args) if arg is None]
        none_kwargs = [k for k, v in kwargs.items() if v is None]
        
        if none_args:
            warnings.append(f"⚠️ None values in positional args: {none_args}")
        if none_kwargs:
            warnings.append(f"⚠️ None values in kwargs: {none_kwargs}")
        
        # Check for unexpected types
        for i, arg in enumerate(args):
            if callable(arg) and not inspect.isclass(arg):
                warnings.append(f"⚠️ Callable in args[{i}]: {type(arg)}")
        
        if warnings:
            context.warnings = warnings
            for warning in warnings:
                logger.warning(warning)
    
    def _format_debug_context(self, context: BaseModelDebugContext) -> str:
        """Format debug context for logging."""
        return f"""
BaseModel Debug Context:
  Class: {context.attempted_class}
  Function: {context.function_name}
  File: {context.file_name}:{context.line_number}
  Arguments: {context.arguments}
  Argument Types: {context.argument_types}
  Error: {context.error_message}
  Success: {context.success}
  Fallback Used: {context.fallback_used}
  Timestamp: {context.timestamp}
        """.strip()
    
    def safe_instantiate(self, class_type: Type, *args, **kwargs):
        """
        Safely instantiate a BaseModel with comprehensive debugging.
        
        Args:
            class_type: The class to instantiate
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Tuple of (instance, success, error_message)
        """
        class_name = class_type.__name__
        caller_info = self._get_caller_info()
        
        with self.debug_context(class_name, caller_info) as context:
            # Log arguments before instantiation
            self.log_arguments(context, *args, **kwargs)
            
            try:
                # Attempt normal instantiation
                instance = class_type(*args, **kwargs)
                return instance, True, None
                
            except TypeError as e:
                if "takes 1 positional argument but" in str(e):
                    # This is the specific error we're debugging
                    logger.error(f"🔍 Detected BaseModel.__init__() argument error in {class_name}")
                    logger.error(f"   Error: {e}")
                    logger.error(f"   Args provided: {len(args)} positional, {len(kwargs)} keyword")
                    
                    # Try fallback strategies
                    fallback_result = self._try_fallback_instantiation(class_type, context, *args, **kwargs)
                    if fallback_result:
                        return fallback_result
                
                raise
    
    def _get_caller_info(self) -> Dict[str, Any]:
        """Get information about the calling function."""
        frame = inspect.currentframe()
        try:
            # Go up the stack to find the actual caller (skip our internal methods)
            for _ in range(3):
                frame = frame.f_back
                if frame is None:
                    break
            
            if frame:
                return {
                    'function_name': frame.f_code.co_name,
                    'file_name': frame.f_code.co_filename,
                    'line_number': frame.f_lineno
                }
        finally:
            del frame
        
        return {}
    
    def _try_fallback_instantiation(self, class_type: Type, context: BaseModelDebugContext, *args, **kwargs):
        """Try various fallback strategies for BaseModel instantiation."""
        fallback_strategies = [
            ("kwargs_only", lambda: class_type(**kwargs) if kwargs else None),
            ("args_only", lambda: class_type(*args) if args else None),
            ("empty", lambda: class_type()),
            ("first_arg_only", lambda: class_type(args[0]) if args else None)
        ]
        
        for strategy_name, strategy_func in fallback_strategies:
            try:
                logger.debug(f"🔄 Trying fallback strategy '{strategy_name}' for {class_type.__name__}")
                result = strategy_func()
                if result is not None:
                    context.fallback_used = True
                    self.fallback_count += 1
                    logger.warning(f"✅ Fallback strategy '{strategy_name}' succeeded for {class_type.__name__}")
                    return result, True, f"Used fallback strategy: {strategy_name}"
            except Exception as fallback_error:
                logger.debug(f"❌ Fallback strategy '{strategy_name}' failed: {fallback_error}")
                continue
        
        logger.error(f"🚨 All fallback strategies failed for {class_type.__name__}")
        return None
    
    def get_debug_report(self) -> Dict[str, Any]:
        """Generate a comprehensive debug report."""
        return {
            'total_attempts': len(self.debug_contexts),
            'successful_instantiations': self.success_count,
            'failed_instantiations': self.error_count,
            'fallback_uses': self.fallback_count,
            'success_rate': self.success_count / max(1, len(self.debug_contexts)) * 100,
            'recent_errors': [
                {
                    'class': ctx.attempted_class,
                    'function': ctx.function_name,
                    'error': ctx.error_message,
                    'timestamp': ctx.timestamp.isoformat(),
                    'arguments': ctx.arguments,
                    'argument_types': ctx.argument_types
                }
                for ctx in self.debug_contexts
                if not ctx.success
            ][-10:],  # Last 10 errors
            'debug_enabled': self.debug_enabled
        }
    
    def enable_debug_mode(self):
        """Enable debug mode."""
        self.debug_enabled = True
        self._setup_enhanced_logging()
        logger.info("🔧 BaseModel debug mode enabled")
    
    def disable_debug_mode(self):
        """Disable debug mode."""
        self.debug_enabled = False
        logger.info("🔧 BaseModel debug mode disabled")

# Global debugger instance
_global_debugger = BaseModelDebugger(debug_enabled=True)

def debug_basemodel_instantiation(class_type: Type):
    """
    Decorator to automatically debug BaseModel instantiation.
    
    Usage:
        @debug_basemodel_instantiation
        class MyModel(BaseModel):
            pass
    """
    original_init = class_type.__init__
    
    @functools.wraps(original_init)
    def wrapped_init(self, *args, **kwargs):
        global _global_debugger
        
        if _global_debugger.debug_enabled:
            # Use the debugger for instantiation
            with _global_debugger.debug_context(class_type.__name__) as context:
                _global_debugger.log_arguments(context, *args, **kwargs)
                return original_init(self, *args, **kwargs)
        else:
            return original_init(self, *args, **kwargs)
    
    class_type.__init__ = wrapped_init
    return class_type

def safe_menu_response(*args, **kwargs):
    """
    Safe wrapper for MenuResponse instantiation with debugging.
    
    This function should be used instead of direct MenuResponse() calls
    in areas where BaseModel errors are occurring.
    """
    global _global_debugger
    
    # Import here to avoid circular imports
    from dataclasses import dataclass
    
    # Try to determine what class we're actually instantiating
    class_name = "MenuResponse"
    
    try:
        # Import the actual MenuResponse class
        from services.enhanced_diana_menu_system import MenuResponse
        
        result, success, error_msg = _global_debugger.safe_instantiate(MenuResponse, *args, **kwargs)
        
        if success:
            return result
        else:
            # Create fallback MenuResponse with safe defaults
            logger.error(f"Creating fallback MenuResponse due to instantiation error: {error_msg}")
            return MenuResponse(
                success=False,
                character_score=0.0,
                response_time=1.0,
                meets_performance_requirement=False,
                message_sent=False,
                errors=[f"MenuResponse instantiation error: {error_msg or 'Unknown error'}"]
            )
    
    except Exception as e:
        logger.error(f"Critical error in safe_menu_response: {e}")
        # Return a minimal fallback object
        class FallbackMenuResponse:
            def __init__(self):
                self.success = False
                self.character_score = 0.0
                self.response_time = 1.0
                self.meets_performance_requirement = False
                self.message_sent = False
                self.errors = [f"Critical MenuResponse error: {e}"]
        
        return FallbackMenuResponse()

def get_global_debugger() -> BaseModelDebugger:
    """Get the global BaseModel debugger instance."""
    return _global_debugger

def enable_basemodel_debug():
    """Enable global BaseModel debugging."""
    _global_debugger.enable_debug_mode()

def disable_basemodel_debug():
    """Disable global BaseModel debugging."""
    _global_debugger.disable_debug_mode()

def get_basemodel_debug_report():
    """Get a comprehensive BaseModel debug report."""
    return _global_debugger.get_debug_report()

# Context manager for temporary debug mode
@contextmanager
def temporary_debug_mode(enabled: bool = True):
    """Temporarily enable/disable debug mode."""
    old_state = _global_debugger.debug_enabled
    try:
        if enabled:
            _global_debugger.enable_debug_mode()
        else:
            _global_debugger.disable_debug_mode()
        yield _global_debugger
    finally:
        _global_debugger.debug_enabled = old_state