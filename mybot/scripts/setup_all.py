#!/usr/bin/env python3
"""
Setup Master Script - Configuración Completa del Bot
====================================================

Este script ejecuta todos los módulos de setup en el orden correcto:
1. Tienda (Shop Items + Lore Pieces)
2. Misiones (Missions + Lore Pieces)
3. Journey/Regalos (Content Sets)

Uso:
    python scripts/setup_all.py

Opciones:
    --reset    Borra toda la data existente antes de poblar (CUIDADO!)
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import logging

# Import setup functions from individual scripts
from scripts.setup_shop import setup_shop
from scripts.setup_missions import setup_missions
from scripts.setup_journey import setup_journey_module

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# RESET FUNCTIONS (OPCIONAL)
# ═══════════════════════════════════════════════════════════════════════════════

async def reset_database(session: AsyncSession):
    """
    ADVERTENCIA: Borra toda la data de los módulos de gamificación
    Útil solo para desarrollo/testing
    """
    logger.warning("\n⚠️  RESETTING DATABASE - BORRANDO TODA LA DATA...")
    logger.warning("─" * 50)

    # Orden correcto: borrar tablas dependientes primero
    tables_to_clear = [
        "gift_records",           # Depende de content_sets
        "user_milestones",        # Depende de users
        "user_mission_progress",  # Depende de missions
        "user_shop_purchases",    # Depende de shop_items
        "content_sets",
        "missions",
        "shop_items",
        "lore_pieces"
    ]

    for table in tables_to_clear:
        try:
            await session.execute(text(f"DELETE FROM {table}"))
            logger.info(f"  ✓ Tabla '{table}' limpiada")
        except Exception as e:
            logger.warning(f"  ⚠ No se pudo limpiar '{table}': {e}")

    await session.commit()
    logger.info("─" * 50)
    logger.info("✓ Reset completado\n")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN SETUP ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════════════

async def main(reset: bool = False):
    """Ejecuta todos los módulos de setup en orden"""

    logger.info("\n" + "═" * 80)
    logger.info("║")
    logger.info("║  🤖 SETUP MAESTRO - SEÑORITA KINKY BOT")
    logger.info("║")
    logger.info("║  Configuración completa de todos los módulos")
    logger.info("║")
    logger.info("═" * 80)

    # Configurar conexión a BD
    DATABASE_URL = "sqlite+aiosqlite:///bot.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # Reset opcional
            if reset:
                confirm = input("\n⚠️  ¿ESTÁS SEGURO de borrar toda la data? (escribe 'SI' para confirmar): ")
                if confirm == "SI":
                    await reset_database(session)
                else:
                    logger.info("Reset cancelado. Continuando con setup normal...\n")

            # ─────────────────────────────────────────────────────────────
            # MÓDULO 1: TIENDA
            # ─────────────────────────────────────────────────────────────
            logger.info("\n" + "▼" * 80)
            logger.info("  MÓDULO 1/3: TIENDA")
            logger.info("▼" * 80 + "\n")

            await setup_shop(session)

            logger.info("✅ Módulo Tienda completado\n")

            # ─────────────────────────────────────────────────────────────
            # MÓDULO 2: MISIONES
            # ─────────────────────────────────────────────────────────────
            logger.info("\n" + "▼" * 80)
            logger.info("  MÓDULO 2/3: MISIONES")
            logger.info("▼" * 80 + "\n")

            await setup_missions(session)

            logger.info("✅ Módulo Misiones completado\n")

            # ─────────────────────────────────────────────────────────────
            # MÓDULO 3: JOURNEY/REGALOS
            # ─────────────────────────────────────────────────────────────
            logger.info("\n" + "▼" * 80)
            logger.info("  MÓDULO 3/3: JOURNEY/REGALOS")
            logger.info("▼" * 80 + "\n")

            await setup_journey_module(session)

            logger.info("✅ Módulo Journey/Regalos completado\n")

            # ─────────────────────────────────────────────────────────────
            # RESUMEN FINAL
            # ─────────────────────────────────────────────────────────────
            logger.info("\n" + "═" * 80)
            logger.info("║")
            logger.info("║  🎉 ¡SETUP MAESTRO COMPLETADO EXITOSAMENTE!")
            logger.info("║")
            logger.info("═" * 80)
            logger.info("║")
            logger.info("║  📊 RESUMEN:")
            logger.info("║")
            logger.info("║  ✓ Tienda configurada (10 productos + lore pieces)")
            logger.info("║  ✓ Misiones creadas (19 misiones + lore pieces)")
            logger.info("║  ✓ Content Sets listos (16 sets de regalos)")
            logger.info("║")
            logger.info("═" * 80)
            logger.info("\n💡 PRÓXIMOS PASOS:")
            logger.info("─" * 80)
            logger.info("\n  1. Configurar variables de entorno (BOT_TOKEN, etc)")
            logger.info("  2. Subir contenido multimedia real para los ContentSets")
            logger.info("  3. Actualizar file_ids de los ContentSets con IDs reales")
            logger.info("  4. (Opcional) Desarrollar módulo narrativo por separado")
            logger.info("  5. Iniciar el bot: python main.py")
            logger.info("\n─" * 80)
            logger.info("\n🚀 El bot está listo para funcionar!\n")

        except Exception as e:
            logger.error(f"\n❌ ERROR DURANTE EL SETUP: {e}")
            logger.error("Revirtiendo cambios...\n")
            await session.rollback()
            raise


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Setup maestro para Señorita Kinky Bot"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="⚠️  Borra toda la data existente antes de poblar (CUIDADO!)"
    )

    args = parser.parse_args()

    asyncio.run(main(reset=args.reset))
