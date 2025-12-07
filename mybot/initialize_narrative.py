#!/usr/bin/env python3
"""
Script para inicializar la narrativa por defecto en la base de datos
"""
import asyncio
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno primero
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Inicializa la narrativa por defecto"""
    from database.setup import init_db, get_session
    from services.narrative_loader import NarrativeLoader

    logger.info("🚀 Inicializando motor de base de datos...")
    engine = await init_db()

    logger.info("📖 Cargando narrativa por defecto...")
    session = await get_session()

    try:
        loader = NarrativeLoader(session)
        await loader.load_default_narrative()
        logger.info("✅ Narrativa inicializada correctamente")
    except Exception as e:
        logger.error(f"❌ Error al inicializar narrativa: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await session.close()

if __name__ == '__main__':
    asyncio.run(main())
