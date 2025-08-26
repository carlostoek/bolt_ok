"""
Patrones de manejo de errores unificados para el ecosistema narrativo Diana.
Proporciona consistencia en el manejo de errores a través de todas las interfaces.
"""
from abc import ABC
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


class ErrorSeverity(Enum):
    """Severidad de errores en el sistema narrativo."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"


class ErrorCategory(Enum):
    """Categorías de errores en el ecosistema narrativo."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    BUSINESS_LOGIC = "business_logic"
    DATA_INTEGRITY = "data_integrity"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM = "system"
    NETWORK = "network"
    PERFORMANCE = "performance"


@dataclass
class ErrorContext:
    """Contexto detallado de un error."""
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    operation_id: Optional[str] = None
    request_data: Optional[Dict[str, Any]] = None
    system_state: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()


@dataclass
class ErrorDetail:
    """Detalle completo de un error del sistema."""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    technical_message: str
    context: ErrorContext
    recovery_suggestions: List[str]
    user_message: Optional[str] = None
    error_data: Optional[Dict[str, Any]] = None


class NarrativeException(Exception):
    """Excepción base para el ecosistema narrativo."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[ErrorContext] = None,
        error_data: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[List[str]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.context = context or ErrorContext()
        self.error_data = error_data or {}
        self.recovery_suggestions = recovery_suggestions or []
        self.user_message = user_message
        self.error_id = self._generate_error_id()
    
    def _generate_error_id(self) -> str:
        """Genera un ID único para el error."""
        import uuid
        return f"{self.category.value}_{uuid.uuid4().hex[:8]}"
    
    def to_error_detail(self) -> ErrorDetail:
        """Convierte la excepción en un ErrorDetail."""
        return ErrorDetail(
            error_id=self.error_id,
            category=self.category,
            severity=self.severity,
            message=str(self),
            technical_message=str(self),
            context=self.context,
            recovery_suggestions=self.recovery_suggestions,
            user_message=self.user_message,
            error_data=self.error_data
        )


class ValidationError(NarrativeException):
    """Error de validación de datos."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.WARNING,
            **kwargs
        )
        if field:
            self.error_data["field"] = field


class BusinessLogicError(NarrativeException):
    """Error de lógica de negocio."""
    
    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.ERROR,
            **kwargs
        )
        if operation:
            self.error_data["operation"] = operation


class DataIntegrityError(NarrativeException):
    """Error de integridad de datos."""
    
    def __init__(self, message: str, table: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.DATA_INTEGRITY,
            severity=ErrorSeverity.CRITICAL,
            **kwargs
        )
        if table:
            self.error_data["table"] = table


class ExternalServiceError(NarrativeException):
    """Error de servicios externos."""
    
    def __init__(self, message: str, service: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.ERROR,
            **kwargs
        )
        if service:
            self.error_data["service"] = service


class SystemError(NarrativeException):
    """Error del sistema."""
    
    def __init__(self, message: str, component: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            **kwargs
        )
        if component:
            self.error_data["component"] = component


class IErrorHandler(ABC):
    """
    Interfaz para el manejo centralizado de errores.
    Define las operaciones necesarias para un manejo consistente de errores.
    """
    
    async def handle_error(self, error: Union[Exception, ErrorDetail]) -> ErrorDetail:
        """
        Maneja un error de forma centralizada.
        
        Args:
            error: Excepción o detalle de error
            
        Returns:
            ErrorDetail: Detalle completo del error procesado
        """
        raise NotImplementedError
    
    async def log_error(self, error_detail: ErrorDetail) -> None:
        """
        Registra un error en el sistema de logging.
        
        Args:
            error_detail: Detalle completo del error
        """
        raise NotImplementedError
    
    async def notify_error(self, error_detail: ErrorDetail) -> None:
        """
        Notifica un error crítico al sistema de alertas.
        
        Args:
            error_detail: Detalle del error a notificar
        """
        raise NotImplementedError
    
    async def get_recovery_actions(self, error_detail: ErrorDetail) -> List[str]:
        """
        Obtiene acciones de recuperación sugeridas para un error.
        
        Args:
            error_detail: Detalle del error
            
        Returns:
            List[str]: Lista de acciones de recuperación
        """
        raise NotImplementedError


def create_error_context(
    user_id: Optional[int] = None,
    operation_id: Optional[str] = None,
    request_data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> ErrorContext:
    """
    Función utilitaria para crear contexto de error.
    
    Args:
        user_id: ID del usuario relacionado
        operation_id: ID de la operación
        request_data: Datos de la petición
        **kwargs: Datos adicionales del contexto
        
    Returns:
        ErrorContext: Contexto completo del error
    """
    return ErrorContext(
        user_id=user_id,
        operation_id=operation_id,
        request_data=request_data,
        system_state=kwargs
    )


def handle_exceptions(
    default_category: ErrorCategory = ErrorCategory.SYSTEM,
    default_severity: ErrorSeverity = ErrorSeverity.ERROR
):
    """
    Decorador para manejo automático de excepciones en métodos de interface.
    
    Args:
        default_category: Categoría por defecto para excepciones no controladas
        default_severity: Severidad por defecto para excepciones no controladas
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except NarrativeException:
                raise  # Re-lanza excepciones narrativas sin modificar
            except Exception as e:
                # Convierte excepciones generales en NarrativeException
                raise SystemError(
                    message=f"Error no controlado en {func.__name__}: {str(e)}",
                    component=func.__qualname__,
                    severity=default_severity,
                    error_data={"original_exception": type(e).__name__}
                )
        return wrapper
    return decorator


# Funciones utilitarias para manejo común de errores

def validate_user_id(user_id: Optional[int]) -> None:
    """
    Valida que el user_id sea válido.
    
    Args:
        user_id: ID del usuario a validar
        
    Raises:
        ValidationError: Si el user_id es inválido
    """
    if user_id is None or user_id <= 0:
        raise ValidationError(
            "User ID debe ser un entero positivo",
            field="user_id",
            user_message="Error de validación de usuario"
        )


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Valida que todos los campos requeridos estén presentes.
    
    Args:
        data: Datos a validar
        required_fields: Lista de campos requeridos
        
    Raises:
        ValidationError: Si faltan campos requeridos
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        raise ValidationError(
            f"Campos requeridos faltantes: {', '.join(missing_fields)}",
            error_data={"missing_fields": missing_fields},
            user_message="Faltan datos requeridos"
        )


def create_business_logic_error(operation: str, reason: str, user_message: str = None) -> BusinessLogicError:
    """
    Crea un error de lógica de negocio estandarizado.
    
    Args:
        operation: Operación que falló
        reason: Razón técnica del fallo
        user_message: Mensaje amigable para el usuario
        
    Returns:
        BusinessLogicError: Error de lógica de negocio
    """
    return BusinessLogicError(
        message=f"Error en {operation}: {reason}",
        operation=operation,
        user_message=user_message or f"No se pudo completar la operación {operation}"
    )