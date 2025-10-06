"""
Script para ejecutar migración de VIP Grants.
Crea la tabla vip_grants y agrega campo vip_days a rewards.
"""
import asyncio
import logging
from database.setup import get_session_factory
from database.base import Base
from database.models import VipGrant, Reward  # Import models to register them

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_migration():
    """Ejecuta la migración de VIP Grants."""
    logger.info("Iniciando migración de VIP Grants...")

    # Initialize database (this creates all tables including vip_grants)
    from database.setup import init_db
    engine = await init_db()

    logger.info("✓ Tabla vip_grants creada/verificada")

    # Add vip_days column to rewards using a new session
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            from sqlalchemy import text
            await session.execute(text("ALTER TABLE rewards ADD COLUMN IF NOT EXISTS vip_days INT"))
            await session.commit()
            logger.info("✓ Campo vip_days agregado a tabla rewards")
        except Exception as e:
            logger.warning(f"Campo vip_days probablemente ya existe: {e}")
            await session.rollback()

    logger.info("✅ Migración completada exitosamente")


if __name__ == "__main__":
    asyncio.run(run_migration())
