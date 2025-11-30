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
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'sqlite:///../bot.db'  # Asume que bot.db está en raíz
    )
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