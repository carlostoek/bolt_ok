#!/usr/bin/env python3
"""
Script para cargar fragmentos narrativos con variantes por arquetipo.

Carga los fragmentos de archetype_variants.json a la base de datos.
Esto permite la ramificación narrativa basada en el arquetipo del usuario.

Uso:
    python scripts/load_archetype_fragments.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.setup import init_db, get_session_factory
from services.narrative_loader import NarrativeLoader
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def load_archetype_fragments():
    """Carga los fragmentos de variantes por arquetipo."""
    try:
        # Inicializar base de datos
        logger.info("Inicializando base de datos...")
        await init_db()

        # Obtener session
        session_factory = get_session_factory()
        async with session_factory() as session:
            logger.info("Cargando fragmentos con variantes por arquetipo...")

            loader = NarrativeLoader(session)

            # Cargar el archivo de variantes
            variants_file = Path(__file__).parent.parent / "narrative_fragments" / "archetype_variants.json"

            if not variants_file.exists():
                logger.error(f"Archivo no encontrado: {variants_file}")
                return False

            await loader.load_fragment_from_file(str(variants_file))

            logger.info("✅ Fragmentos de arquetipos cargados exitosamente")
            logger.info("")
            logger.info("Fragmentos cargados:")
            logger.info("  - diana_direct_adventurer")
            logger.info("  - diana_slow_romantic")
            logger.info("  - diana_multi_explorer")
            logger.info("  - vip_fast_track_adventurer")
            logger.info("  - vip_emotional_romantic")
            logger.info("  - diana_wild_explorer")
            logger.info("  - diana_vulnerable_explorer")
            logger.info("  - diana_mystery_explorer")
            logger.info("  - + 12 fragmentos más")
            logger.info("")
            logger.info("🎭 Sistema de ramificación por arquetipos activado")

            return True

    except Exception as e:
        logger.error(f"Error al cargar fragmentos: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = asyncio.run(load_archetype_fragments())
    sys.exit(0 if success else 1)
