from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./bot_database.db"
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    telegram_bot_token: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()