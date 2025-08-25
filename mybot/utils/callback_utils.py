"""
Utilidades para procesamiento y análisis de datos de callback.
Proporciona funciones para extraer y validar parámetros de callbacks.
"""

from typing import Dict, Any, Optional


def parse_callback_data(callback_data: str) -> Dict[str, Any]:
    """
    Analiza una string de callback para extraer parámetros.
    
    Args:
        callback_data (str): Datos del callback, típicamente en formato "action?param1=value1&param2=value2"
    
    Returns:
        Dict[str, Any]: Diccionario con los parámetros extraídos
    
    Ejemplo:
        >>> parse_callback_data("admin_view_fragment?id=123&page=2")
        {'action': 'admin_view_fragment', 'id': '123', 'page': '2'}
    """
    params = {}
    
    # Dividir en acción y parámetros
    if "?" in callback_data:
        action, param_string = callback_data.split("?", 1)
        params["action"] = action
        
        # Extraer parámetros
        for param in param_string.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[key] = value
            else:
                # Para parámetros sin valor
                params[param] = True
    else:
        # Si no hay parámetros, la acción es todo el callback
        params["action"] = callback_data
    
    return params


def build_callback_data(action: str, **kwargs) -> str:
    """
    Construye una string de callback con acción y parámetros.
    
    Args:
        action (str): Acción principal del callback
        **kwargs: Parámetros adicionales como pares clave-valor
    
    Returns:
        str: String de callback formateada
    
    Ejemplo:
        >>> build_callback_data("admin_view_fragment", id="123", page="2")
        'admin_view_fragment?id=123&page=2'
    """
    if not kwargs:
        return action
    
    param_strings = []
    for key, value in kwargs.items():
        if value is not None:
            param_strings.append(f"{key}={value}")
    
    return f"{action}?{'&'.join(param_strings)}"