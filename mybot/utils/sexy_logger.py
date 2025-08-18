# sexy_logger.py
"""
Sistema de Logging Sexy y Detallado para Bot Diana
¡Logs que dan ganas de ver! 🎬
"""

import logging
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import json
import asyncio
from contextlib import contextmanager

class LogLevel(Enum):
    DEBUG = "🔍 DEBUG"
    INFO = "ℹ️  INFO"
    SUCCESS = "✅ SUCCESS"
    WARNING = "⚠️  WARNING"
    ERROR = "❌ ERROR"
    CRITICAL = "🚨 CRITICAL"
    STARTUP = "🚀 STARTUP"
    VALIDATION = "🎯 VALIDATION"
    GAMIFICATION = "🎮 GAMIFICATION"
    NARRATIVE = "📚 NARRATIVE"
    USER_ACTION = "👤 USER"
    PERFORMANCE = "⚡ PERFORMANCE"
    DATABASE = "🗄️  DATABASE"
    API = "🌐 API"

class SexyLogger:
    """
    Logger que hace que tus deployments se vean INCREÍBLES
    ¡Logs con estilo y sustancia!
    """
    
    def __init__(self, name: str = "DianaBot", enable_colors: bool = True):
        self.name = name
        self.enable_colors = enable_colors
        self.start_time = time.time()
        self.setup_logger()
        
        # Contadores para métricas
        self.metrics = {
            'validations_success': 0,
            'validations_failed': 0,
            'points_awarded': 0,
            'users_processed': set(),
            'events_tracked': 0,
            'errors_count': 0
        }
    
    def setup_logger(self):
        """Configurar logger base"""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        
        # Limpiar handlers existentes
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Handler para consola con formato sexy
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        # Formato personalizado
        formatter = SexyFormatter(enable_colors=self.enable_colors)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
    
    # ============================================
    # MÉTODOS DE LOGGING PRINCIPALES
    # ============================================
    
    def startup(self, message: str, **kwargs):
        """Log de inicio con estilo"""
        self._log(LogLevel.STARTUP, message, **kwargs)
    
    def success(self, message: str, **kwargs):
        """Log de éxito"""
        self._log(LogLevel.SUCCESS, message, **kwargs)
    
    def validation(self, message: str, user_id: int = None, level: str = None, score: float = None, **kwargs):
        """Log específico para validaciones Diana"""
        extra_data = {}
        if user_id:
            extra_data['user_id'] = user_id
        if level:
            extra_data['level'] = level
        if score is not None:
            extra_data['score'] = f"{score:.2f}"
        
        self._log(LogLevel.VALIDATION, message, extra_data=extra_data, **kwargs)
    
    def gamification(self, message: str, user_id: int = None, points: int = None, **kwargs):
        """Log específico para gamificación"""
        extra_data = {}
        if user_id:
            extra_data['user_id'] = user_id
        if points:
            extra_data['points'] = points
            self.metrics['points_awarded'] += points
        
        self._log(LogLevel.GAMIFICATION, message, extra_data=extra_data, **kwargs)
    
    def narrative(self, message: str, user_id: int = None, fragment: str = None, **kwargs):
        """Log específico para narrativa"""
        extra_data = {}
        if user_id:
            extra_data['user_id'] = user_id
        if fragment:
            extra_data['fragment'] = fragment
        
        self._log(LogLevel.NARRATIVE, message, extra_data=extra_data, **kwargs)
    
    def user_action(self, message: str, user_id: int, action: str = None, **kwargs):
        """Log de acciones de usuario"""
        self.metrics['users_processed'].add(user_id)
        extra_data = {'user_id': user_id}
        if action:
            extra_data['action'] = action
        
        self._log(LogLevel.USER_ACTION, message, extra_data=extra_data, **kwargs)
    
    def performance(self, message: str, duration: float = None, **kwargs):
        """Log de performance"""
        extra_data = {}
        if duration:
            extra_data['duration'] = f"{duration:.3f}s"
        
        self._log(LogLevel.PERFORMANCE, message, extra_data=extra_data, **kwargs)
    
    def database(self, message: str, operation: str = None, **kwargs):
        """Log de operaciones de BD"""
        extra_data = {}
        if operation:
            extra_data['operation'] = operation
        
        self._log(LogLevel.DATABASE, message, extra_data=extra_data, **kwargs)
    
    def api(self, message: str, endpoint: str = None, status: int = None, **kwargs):
        """Log de API calls"""
        extra_data = {}
        if endpoint:
            extra_data['endpoint'] = endpoint
        if status:
            extra_data['status'] = status
        
        self._log(LogLevel.API, message, extra_data=extra_data, **kwargs)
    
    def error(self, message: str, error: Exception = None, **kwargs):
        """Log de errores con detalles"""
        self.metrics['errors_count'] += 1
        extra_data = {}
        if error:
            extra_data['error_type'] = type(error).__name__
            extra_data['error_msg'] = str(error)
        
        self._log(LogLevel.ERROR, message, extra_data=extra_data, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log de warnings"""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log de información general"""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log de debug"""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    # ============================================
    # MÉTODOS ESPECIALES PARA DIANA
    # ============================================
    
    def diana_validation_success(self, user_id: int, level: str, score: float, archetype: str = None, points_awarded: int = 0):
        """Log específico para validaciones exitosas de Diana"""
        self.metrics['validations_success'] += 1
        if points_awarded:
            self.metrics['points_awarded'] += points_awarded
        
        archetype_text = f" | Arquetipo: {archetype}" if archetype else ""
        points_text = f" | +{points_awarded} puntos" if points_awarded else ""
        
        self.validation(
            f"✨ Validación EXITOSA: {level} | Score: {score:.2f}{archetype_text}{points_text}",
            user_id=user_id,
            level=level,
            score=score
        )
    
    def diana_validation_failed(self, user_id: int, level: str, score: float, reason: str = None):
        """Log específico para validaciones fallidas de Diana"""
        self.metrics['validations_failed'] += 1
        
        reason_text = f" | Razón: {reason}" if reason else ""
        
        self.validation(
            f"💔 Validación FALLIDA: {level} | Score: {score:.2f}{reason_text}",
            user_id=user_id,
            level=level,
            score=score
        )
    
    def diana_archetype_detected(self, user_id: int, archetype: str, confidence: float = None):
        """Log cuando se detecta un arquetipo"""
        confidence_text = f" (Confianza: {confidence:.2f})" if confidence else ""
        
        self.user_action(
            f"🎭 Arquetipo detectado: {archetype.upper()}{confidence_text}",
            user_id=user_id,
            action='archetype_detection'
        )
    
    def diana_reward_delivered(self, user_id: int, reward_type: str, items: list = None):
        """Log cuando se entregan recompensas"""
        items_text = f" | Items: {', '.join(items)}" if items else ""
        
        self.gamification(
            f"🎁 Recompensa entregada: {reward_type}{items_text}",
            user_id=user_id
        )
    
    # ============================================
    # CONTEXTOS Y SECCIONES
    # ============================================
    
    @contextmanager
    def section(self, title: str, emoji: str = "📋"):
        """Contexto para crear secciones visuales"""
        self.section_start(title, emoji)
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.section_end(title, duration)
    
    def section_start(self, title: str, emoji: str = "📋"):
        """Iniciar una sección"""
        separator = "=" * 60
        self.info(f"\n{separator}")
        self.info(f"{emoji} {title.upper()}")
        self.info(separator)
    
    def section_end(self, title: str, duration: float):
        """Terminar una sección"""
        self.performance(f"⏱️  Sección '{title}' completada", duration=duration)
        self.info("=" * 60 + "\n")
    
    def banner(self, title: str, subtitle: str = None):
        """Banner de inicio sexy"""
        lines = [
            "",
            "🎭" + "=" * 58 + "🎭",
            f"🎪  {title.center(54)}  🎪",
            "🎭" + "=" * 58 + "🎭"
        ]
        
        if subtitle:
            lines.insert(-1, f"✨  {subtitle.center(54)}  ✨")
            lines.insert(-1, "🎭" + "=" * 58 + "🎭")
        
        lines.append("")
        
        for line in lines:
            self.startup(line)
    
    def summary(self, title: str = "RESUMEN DE EJECUCIÓN"):
        """Resumen final con métricas"""
        uptime = time.time() - self.start_time
        
        self.section_start(title, "📊")
        
        # Métricas principales
        self.success(f"⏰ Tiempo de ejecución: {uptime:.2f}s")
        self.success(f"👥 Usuarios únicos procesados: {len(self.metrics['users_processed'])}")
        
        # Validaciones
        total_validations = self.metrics['validations_success'] + self.metrics['validations_failed']
        if total_validations > 0:
            success_rate = (self.metrics['validations_success'] / total_validations) * 100
            self.success(f"🎯 Validaciones exitosas: {self.metrics['validations_success']}/{total_validations} ({success_rate:.1f}%)")
        
        # Gamificación
        if self.metrics['points_awarded'] > 0:
            self.success(f"💰 Puntos otorgados: {self.metrics['points_awarded']}")
        
        # Errores
        if self.metrics['errors_count'] > 0:
            self.warning(f"⚠️  Errores registrados: {self.metrics['errors_count']}")
        else:
            self.success("✅ Ejecución sin errores")
        
        self.section_end("RESUMEN", 0)
    
    # ============================================
    # MÉTODO INTERNO
    # ============================================
    
    def _log(self, level: LogLevel, message: str, extra_data: Dict = None, **kwargs):
        """Método interno de logging"""
        # Preparar mensaje
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Añadir datos extra si existen
        if extra_data:
            extra_str = " | ".join([f"{k}: {v}" for k, v in extra_data.items()])
            message = f"{message} | {extra_str}"
        
        # Log usando el logger base
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            self.logger.error(f"{level.value} {message}")
        elif level == LogLevel.WARNING:
            self.logger.warning(f"{level.value} {message}")
        else:
            self.logger.info(f"{level.value} {message}")


class SexyFormatter(logging.Formatter):
    """Formatter personalizado para logs sexy"""
    
    # Colores ANSI
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[37m',      # White
        'SUCCESS': '\033[92m',   # Bright Green
        'WARNING': '\033[93m',   # Yellow
        'ERROR': '\033[91m',     # Red
        'CRITICAL': '\033[95m',  # Magenta
        'STARTUP': '\033[94m',   # Blue
        'VALIDATION': '\033[35m', # Purple
        'GAMIFICATION': '\033[33m', # Orange
        'NARRATIVE': '\033[96m',  # Light Cyan
        'USER_ACTION': '\033[92m', # Light Green
        'PERFORMANCE': '\033[93m', # Light Yellow
        'DATABASE': '\033[90m',   # Dark Gray
        'API': '\033[34m',       # Dark Blue
        'RESET': '\033[0m'       # Reset
    }
    
    def __init__(self, enable_colors: bool = True):
        super().__init__()
        self.enable_colors = enable_colors
    
    def format(self, record):
        if not self.enable_colors:
            return record.getMessage()
        
        # Detectar tipo de log por el mensaje
        message = record.getMessage()
        color = self.COLORS.get('INFO', '')
        
        for log_type, ansi_color in self.COLORS.items():
            if log_type in message:
                color = ansi_color
                break
        
        # Formatear con color
        return f"{color}{message}{self.COLORS['RESET']}"


# ============================================
# DECORADOR PARA TIMING AUTOMÁTICO
# ============================================

def log_execution_time(logger, description: str = None):
    """Decorador para loggear tiempo de ejecución automáticamente"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = description or f"{func.__name__}"
            
            logger.performance(f"⏳ Iniciando: {func_name}")
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.performance(f"✅ Completado: {func_name}", duration=duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"❌ Error en {func_name}: {str(e)}", error=e)
                logger.performance(f"⏹️  Terminado con error: {func_name}", duration=duration)
                raise
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            func_name = description or f"{func.__name__}"
            
            logger.performance(f"⏳ Iniciando: {func_name}")
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.performance(f"✅ Completado: {func_name}", duration=duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"❌ Error en {func_name}: {str(e)}", error=e)
                logger.performance(f"⏹️  Terminado con error: {func_name}", duration=duration)
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# ============================================
# LOGGER GLOBAL PARA EASY ACCESS
# ============================================

# Instancia global del logger
sexy_logger = SexyLogger("DianaBot")

# Shortcuts para acceso fácil
log = sexy_logger
logger = sexy_logger  # Para compatibilidad

# Funciones directas para uso rápido
def startup(message: str, **kwargs):
    sexy_logger.startup(message, **kwargs)

def success(message: str, **kwargs):
    sexy_logger.success(message, **kwargs)

def validation(message: str, **kwargs):
    sexy_logger.validation(message, **kwargs)

def gamification(message: str, **kwargs):
    sexy_logger.gamification(message, **kwargs)

def narrative(message: str, **kwargs):
    sexy_logger.narrative(message, **kwargs)

def user_action(message: str, **kwargs):
    sexy_logger.user_action(message, **kwargs)

def performance(message: str, **kwargs):
    sexy_logger.performance(message, **kwargs)

def error(message: str, **kwargs):
    sexy_logger.error(message, **kwargs)

def info(message: str, **kwargs):
    sexy_logger.info(message, **kwargs)
