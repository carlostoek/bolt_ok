import logging
import os
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Union
from urllib.parse import urlparse

from sqlalchemy import NullPool, event, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import DeclarativeMeta, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql import Select

# Configure logging for database operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Detect database type from URL
def get_database_config(url: str):
    parsed = urlparse(url)
    return {
        'is_sqlite': parsed.scheme == 'sqlite',
        'is_postgresql': parsed.scheme in ['postgresql', 'postgres']
    }


# Global engine and session variables
engine: Optional[AsyncEngine] = None
SessionLocal = None


class TimestampMixin:
    """Mixin que agrega campos created_at y updated_at a los modelos."""
    created_at = None  # Will be set in declarative base
    updated_at = None  # Will be set in declarative base


class SoftDeleteMixin:
    """Mixin que agrega funcionalidad de borrado lógico a los modelos."""
    deleted_at = None  # Will be set in declarative base


@as_declarative()
class Base:
    """Clase base para todos los modelos SQLAlchemy."""
    
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()  # type: ignore
    
    # Define common columns with type hints
    created_at = None
    updated_at = None
    deleted_at = None
    
    # Initialize common columns in __init_subclass__
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        
        # Add timestamp columns if TimestampMixin is in the MRO
        if TimestampMixin in cls.__mro__:
            from sqlalchemy import DateTime
            from datetime import datetime
            cls.created_at = cls.created_at or DateTime(timezone=True)
            cls.updated_at = cls.updated_at or DateTime(timezone=True)
            
        # Add soft delete column if SoftDeleteMixin is in the MRO
        if SoftDeleteMixin in cls.__mro__:
            from sqlalchemy import DateTime
            cls.deleted_at = cls.deleted_at or DateTime(timezone=True)

    def to_dict(self) -> dict:
        """Serialize model instance to dictionary."""
        result = {}
        # Access the table through the mapped class
        for column in self.__table__.columns:  # type: ignore
            value = getattr(self, column.name)
            if hasattr(value, 'isoformat'):  # datetime objects
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result


def configure_engine(database_url: Optional[str] = None) -> None:
    """
    Configura el engine de SQLAlchemy basado en la URL de la base de datos.
    
    Args:
        database_url: URL de la base de datos (default: DATABASE_URL del entorno)
    """
    global engine, SessionLocal
    
    if database_url is None:
        database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./db.sqlite3")
    
    db_config = get_database_config(database_url)
    
    # Engine configuration options
    engine_kwargs = {}
    
    if db_config['is_sqlite']:
        # SQLite-specific configuration
        engine_kwargs = {
            'poolclass': StaticPool,
            'connect_args': {
                'check_same_thread': False,
                'timeout': 30,
            },
            'echo': os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",
        }
        
        engine = create_async_engine(database_url, **engine_kwargs)
        
        # Configure SQLite PRAGMAs
        @event.listens_for(engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys=ON")
            # Set cache size (default 2000 pages of 4KB each = 8MB)
            cursor.execute("PRAGMA cache_size=2000")
            # Enable synchronous NORMAL for better performance
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
    
    elif db_config['is_postgresql']:
        # PostgreSQL-specific configuration
        pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        
        engine_kwargs = {
            'pool_size': pool_size,
            'max_overflow': max_overflow,
            'pool_timeout': pool_timeout,
            'pool_recycle': 300,
            'echo': os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true",
        }
        
        engine = create_async_engine(
            database_url.replace("postgresql://", "postgresql+asyncpg://"),
            **engine_kwargs
        )
    
    else:
        # Default configuration
        engine = create_async_engine(database_url, echo=False)
    
    # Create configured "SessionLocal" class
    global SessionLocal
    SessionLocal = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )  # type: ignore


# Initialize the engine with the default URL
configure_engine()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Generator para obtener una sesión de base de datos para FastAPI Depends().
    Implementa retry automático con máximo 3 intentos.
    """
    if SessionLocal is None:
        configure_engine()
    
    # At this point, SessionLocal should not be None anymore
    if SessionLocal is None:
        raise RuntimeError("SessionLocal is still None after configuration")
    
    max_retries = int(os.getenv("DB_MAX_RETRIES", "3"))
    retry_count = 0
    
    while retry_count < max_retries:
        async with SessionLocal() as session:
            try:
                yield session
                break  # Exit loop if successful
            except Exception as e:
                retry_count += 1
                logger.error(f"Database session error (attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count >= max_retries:
                    raise e
                else:
                    # Wait before retrying (exponential backoff)
                    import asyncio
                    wait_time = 2 ** retry_count
                    await asyncio.sleep(wait_time)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager para obtener una sesión de base de datos.
    Maneja automáticamente el rollback en errores.
    """
    if SessionLocal is None:
        configure_engine()
    
    # At this point, SessionLocal should not be None anymore
    if SessionLocal is None:
        raise RuntimeError("SessionLocal is still None after configuration")
        
    async with SessionLocal() as session:
        try:
            start_time = time.time()
            yield session
            
            # Log slow queries (>500ms)
            execution_time = time.time() - start_time
            if execution_time > 0.5:
                logger.warning(f"Slow database query: {execution_time:.2f} seconds")
                
        except Exception as e:
            # Log the error and rollback
            logger.error(f"Database session rollback due to error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def execute_with_retry(query_func, max_retries=3):
    """
    Ejecuta una función de consulta con retry automático.
    
    Args:
        query_func: Función asincrónica que devuelve un resultado
        max_retries: Número máximo de reintentos
        
    Returns:
        Resultado de la función de consulta
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return await query_func()
        except Exception as e:
            last_error = e
            logger.warning(f"Query attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                import asyncio
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"Query failed after {max_retries} attempts")
                raise last_error
    
    raise last_error


# Initialize the engine if not already done
if engine is None:
    configure_engine()


__all__ = [
    "engine", 
    "SessionLocal", 
    "Base", 
    "TimestampMixin", 
    "SoftDeleteMixin", 
    "get_db", 
    "get_db_session", 
    "execute_with_retry",
    "configure_engine"
]