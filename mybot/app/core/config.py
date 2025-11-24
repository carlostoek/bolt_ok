"""
Configuración centralizada del panel de administración.
Usa pydantic-settings para gestionar variables de entorno.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Configuración global de la aplicación.
    Las variables se cargan automáticamente desde .env o variables de entorno.
    """

    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/botdb"

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Bot Admin Panel"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # CORS Configuration
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # SQLAlchemy Configuration
    POOL_SIZE: int = 5
    MAX_OVERFLOW: int = 10
    POOL_PRE_PING: bool = True
    ECHO_SQL: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Singleton instance
settings = Settings()
