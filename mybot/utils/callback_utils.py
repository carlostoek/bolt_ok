"""
Utilidades para el manejo de callbacks.
Proporciona funciones para analizar y procesar datos de callbacks.
"""
from typing import Dict, Any, Optional


def parse_callback_data(callback_data: str) -> Dict[str, Any]:
    """
    Analiza los datos de una callback para extraer parámetros.
    Formato esperado: 'accion?param1=valor1&param2=valor2'
    
    Args:
        callback_data: Cadena de callback que puede contener parámetros
        
    Returns:
        Diccionario con los parámetros extraídos
    """
    params = {}
    
    if not callback_data or "?" not in callback_data:
        return params
    
    # Dividir acción y parámetros
    action, query_string = callback_data.split("?", 1)
    
    # Procesar parámetros
    for param in query_string.split("&"):
        if "=" in param:
            key, value = param.split("=", 1)
            params[key] = value
    
    return params


def build_callback_data(action: str, params: Optional[Dict[str, Any]] = None) -> str:
    """
    Construye una cadena de callback con parámetros.
    
    Args:
        action: Acción principal de la callback
        params: Diccionario de parámetros a incluir
        
    Returns:
        Cadena de callback formateada
    """
    if not params:
        return action
    
    query_parts = []
    for key, value in params.items():
        query_parts.append(f"{key}={value}")
    
    query_string = "&".join(query_parts)
    return f"{action}?{query_string}"