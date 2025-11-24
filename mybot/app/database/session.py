"""
Configuración de SQLAlchemy Async y gestión de sesiones de base de datos.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


class Base(DeclarativeBase):
    """
    Base declarativa para todos los modelos ORM.
    Todos los modelos deben heredar de esta clase.
    """
    pass


# Crear engine asíncrono
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ECHO_SQL,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    pool_pre_ping=settings.POOL_PRE_PING,
    future=True
)

# Crear session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para obtener una sesión de base de datos.

    Uso en FastAPI:
        @router.post("/endpoint")
        async def create_something(db: AsyncSession = Depends(get_db)):
            ...

    Yields:
        AsyncSession: Sesión de base de datos activa
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Inicializa la base de datos creando todas las tablas.

    NOTA: En producción, usar Alembic para migraciones.
    Esta función es útil para desarrollo y testing.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Cierra todas las conexiones de la base de datos.
    Llamar esto al apagar la aplicación.
    """
    await engine.dispose()
