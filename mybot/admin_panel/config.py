"""
Configuración de Flask
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración base"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    # Base de Datos
    # El panel web necesita usar un driver SYNC, no ASYNC
    # Aunque el .env tenga sqlite+aiosqlite para el bot, aquí usamos sqlite:// para Flask
    _db_url = os.getenv('DATABASE_URL', 'sqlite:///../bot.db')
    if _db_url.startswith('sqlite+aiosqlite://'):
        # Convertir de async a sync para Flask
        # sqlite+aiosqlite:///bot.db -> sqlite:///bot.db
        # Usar path absoluto: sqlite:////absolute/path/to/bot.db
        from pathlib import Path
        # bot.db está en el mismo directorio que app.py padre (mybot/)
        # config.py -> admin_panel -> config.py, así que parent.parent es /mybot/
        project_root = Path(__file__).parent.parent  # admin_panel/config.py -> admin_panel -> mybot
        db_path = project_root / 'bot.db'
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    else:
        SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG  # Log SQL queries en debug
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Seguridad
    ADMIN_IPS = os.getenv('ADMIN_IPS', '127.0.0.1,::1').split(',')
    
    # Paginación
    ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', '20'))

class DevelopmentConfig(Config):
    """Configuración de desarrollo"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Configuración de producción"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    # En producción, SECRET_KEY debe venir de variable de entorno
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    @classmethod
    def init_app(cls, app):
        """Validaciones específicas de producción"""
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY must be set in production")

# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}