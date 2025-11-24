"""
Excepciones personalizadas para el panel de administración.
"""


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

    def __init__(self, message: str, nested_entity: str = None):
        full_message = f"Error en creación anidada"
        if nested_entity:
            full_message += f" de {nested_entity}"
        full_message += f": {message}"
        super().__init__(full_message, status_code=500)
