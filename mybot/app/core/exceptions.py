"""
Excepciones personalizadas para el panel de administración.
"""
from typing import Optional


class AppException(Exception):
    """Excepción base de la aplicación."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseException(AppException):
    """Excepción para errores de base de datos."""

    def __init__(self, message: str = "Error en la base de datos"):
        super().__init__(message, status_code=500)


class DuplicateKeyException(AppException):
    """Excepción cuando se intenta crear un fragmento con key duplicada."""

    def __init__(self, key: str):
        super().__init__(
            f"Ya existe un fragmento con la key '{key}'",
            status_code=409
        )


class FragmentNotFoundException(AppException):
    """Excepción cuando no se encuentra un fragmento."""

    def __init__(self, key: str):
        super().__init__(
            f"No se encontró el fragmento con key '{key}'",
            status_code=404
        )


class ValidationException(AppException):
    """Excepción para errores de validación de negocio."""

    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class NestedCreationException(AppException):
    """Excepción específica para errores en creación anidada."""

    def __init__(self, message: str, nested_entity: Optional[str] = None):
        full_message = f"Error en creación anidada"
        if nested_entity:
            full_message += f" de {nested_entity}"
        full_message += f": {message}"
        super().__init__(full_message, status_code=500)


class ProductNotFoundException(AppException):
    """Excepción cuando no se encuentra un producto."""

    def __init__(self, product_id: int):
        super().__init__(
            f"No se encontró el producto con ID '{product_id}'",
            status_code=404
        )


class TriggerNotFoundException(AppException):
    """Excepción cuando no se encuentra un trigger."""

    def __init__(self, trigger_id: int):
        super().__init__(
            f"No se encontró el trigger con ID '{trigger_id}'",
            status_code=404
        )


class NotFoundException(AppException):
    """Excepción genérica cuando no se encuentra un recurso."""

    def __init__(self, message: str):
        super().__init__(message, status_code=404)
