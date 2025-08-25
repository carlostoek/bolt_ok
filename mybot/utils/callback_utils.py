"""
Utilidades para el manejo de datos de callback en los handlers de Telegram.
Simplifica la extracción y análisis de parámetros en callback_data.
"""
from typing import Dict, Any, Optional
from urllib.parse import parse_qs


def parse_callback_data(callback_data: str) -> Dict[str, Any]:
    """
    Parsea los datos de callback que incluyen parámetros en formato de URL.
    
    Args:
        callback_data: String con los datos del callback (ej: "command?param1=value1&param2=value2")
        
    Returns:
        Dict con el comando base y los parámetros parseados
    
    Ejemplo:
        >>> parse_callback_data("admin_fragments_list?page=2&filter=active")
        {'command': 'admin_fragments_list', 'params': {'page': '2', 'filter': 'active'}}
    """
    result = {
        "command": callback_data,
        "params": {}
    }
    
    # Verificar si hay parámetros
    if "?" in callback_data:
        # Dividir en comando y parámetros
        parts = callback_data.split("?", 1)
        result["command"] = parts[0]
        
        # Parsear parámetros si existen
        if len(parts) > 1 and parts[1]:
            # Convertir a diccionario
            params_dict = parse_qs(parts[1])
            
            # Simplificar los valores únicos (convertir listas de un elemento a valores simples)
            for key, value in params_dict.items():
                if isinstance(value, list) and len(value) == 1:
                    result["params"][key] = value[0]
                else:
                    result["params"][key] = value
    
    return result


def get_callback_parameter(callback_data: str, param_name: str, default: Any = None) -> Any:
    """
    Extrae un parámetro específico de los datos de callback.
    
    Args:
        callback_data: String con los datos del callback
        param_name: Nombre del parámetro a extraer
        default: Valor por defecto si el parámetro no existe
        
    Returns:
        Valor del parámetro o el valor por defecto
    """
    parsed = parse_callback_data(callback_data)
    return parsed["params"].get(param_name, default)


def build_callback_data(command: str, params: Optional[Dict[str, Any]] = None) -> str:
    """
    Construye un string de callback_data con comando y parámetros.
    
    Args:
        command: Comando base
        params: Diccionario de parámetros a incluir
        
    Returns:
        String formateado para callback_data
    
    Ejemplo:
        >>> build_callback_data("admin_fragments_list", {"page": 2, "filter": "active"})
        "admin_fragments_list?page=2&filter=active"
    """
    if not params:
        return command
    
    # Construir string de parámetros
    params_str = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{command}?{params_str}"