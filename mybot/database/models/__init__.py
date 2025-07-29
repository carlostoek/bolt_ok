# database/models/__init__.py

# Importamos directamente User desde database.models (ubicado en el paquete padre)
import sys
import importlib.util
import os

# Primero exportamos los modelos emocionales y narrativos
from .emotional import CharacterEmotionalState, EmotionalHistoryEntry, EmotionalResponseTemplate
from .narrative import NarrativeFragment, UserStoryState

# Vamos a crear un alias para User
# Ubicación del archivo models.py en la carpeta padre
models_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models.py')

# Cargar el módulo models.py explícitamente
spec = importlib.util.spec_from_file_location('database.models_main', models_path)
models_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models_module)

# Obtener la clase User y exponerla desde este módulo
User = models_module.User

__all__ = [
    'User',  # Importante: exponemos User para que sea importado
    'CharacterEmotionalState',
    'EmotionalHistoryEntry',
    'EmotionalResponseTemplate',
    'NarrativeFragment',
    'UserStoryState'
]