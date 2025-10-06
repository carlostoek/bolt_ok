import json
from pathlib import Path

_translations = {}
_default_lang = 'es'

def load_translations(lang: str):
    """Carga un archivo de idioma en el caché _translations."""
    p = Path(__file__).parent.parent / 'locales' / f'{lang}.json'
    if not p.exists():
        # En un caso real, podríamos querer loggear este error
        print(f"Error: Language file not found for '{lang}'")
        _translations[lang] = {}
        return

    with open(p, 'r', encoding='utf-8') as f:
        _translations[lang] = json.load(f)

def get_text(key: str, lang: str = _default_lang, **kwargs) -> str:
    """
    Obtiene un texto desde el archivo de idioma.

    Args:
        key: La clave del texto, usando puntos para anidación (ej. 'start.welcome').
        lang: El código de idioma (ej. 'es').
        **kwargs: Valores para reemplazar en el texto (ej. user_name='John').

    Returns:
        El texto traducido y formateado, o la clave si no se encuentra.
    """
    if lang not in _translations:
        load_translations(lang)

    # Navegar por la clave anidada (ej. 'main_menu.button_profile')
    keys = key.split('.')
    value = _translations.get(lang, {})
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            value = None
            break

    if value is None:
        # Si no se encuentra la clave, devolver la clave misma como fallback.
        # Esto ayuda a identificar textos faltantes durante el desarrollo.
        return key

    if isinstance(value, str) and kwargs:
        try:
            return value.format(**kwargs)
        except KeyError as e:
            # Si falta una variable en los kwargs, se loggea y devuelve el texto sin formato
            print(f"Warning: Missing placeholder {e} in key '{key}'")
            return value
    
    return value

# Cargar el idioma por defecto al iniciar el módulo
load_translations(_default_lang)

# Alias corto para get_text (útil para imports: from utils.localization import L)
L = get_text
