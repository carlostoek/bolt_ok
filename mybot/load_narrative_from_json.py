#!/usr/bin/env python3
"""
Script para cargar narrativa desde archivo JSON a la base de datos.
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database.setup import get_session, init_db
from services.narrative_loader import NarrativeLoader
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def load_narrative_from_json(json_file_path: str):
    """
    Carga narrativa desde un archivo JSON usando NarrativeLoader.

    Args:
        json_file_path: Ruta al archivo JSON con la narrativa
    """
    logger.info("🔄 Inicializando base de datos...")
    await init_db()

    logger.info("📂 Obteniendo sesión de base de datos...")
    Session = await get_session()

    async with Session() as session:
        logger.info(f"📖 Cargando narrativa desde: {json_file_path}")
        loader = NarrativeLoader(session)

        try:
            await loader.load_fragment_from_file(json_file_path)
            logger.info("✅ ¡Narrativa cargada exitosamente!")
            logger.info("🎯 Próximo paso: Prueba con /historia en el bot")

        except Exception as e:
            logger.error(f"❌ Error cargando narrativa: {e}", exc_info=True)
            raise


async def main():
    # Usar el archivo JSON corregido
    json_file = "/home/azureuser/repos/bolt_ok/mybot/narrative_fixed.json"

    if not os.path.exists(json_file):
        logger.error(f"❌ Archivo no encontrado: {json_file}")
        sys.exit(1)

    await load_narrative_from_json(json_file)


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 CARGANDO NARRATIVA DESDE JSON")
    print("=" * 60)
    asyncio.run(main())
    print("=" * 60)
