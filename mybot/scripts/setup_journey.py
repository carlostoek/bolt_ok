"""
Setup Script - Módulo Journey/Regalos (ContentSets)

Este script crea los ContentSets predefinidos para:
- User Journey (day_1, day_7, day_30)
- Regalos por eventos (auctions, compras, niveles)
- Sorpresas y loyalty rewards

NOTA: Los file_ids son placeholders. Deberás reemplazarlos con los IDs reales
de Telegram después de subir el contenido multimedia.
"""

import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from database.models import ContentSet
from sqlalchemy import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CONTENT SETS - REGALOS Y JOURNEY
# ═══════════════════════════════════════════════════════════════════════════════

CONTENT_SETS = [
    # ─────────────────────────────────────────────────────────────────────────
    # 🌟 JOURNEY - MILESTONES AUTOMÁTICOS
    # ─────────────────────────────────────────────────────────────────────────
    {
        "id": "day_1_welcome",
        "name": "🌹 Primera Mirada - Bienvenida",
        "type": "photo_set",
        "tier": "free",
        "category": "welcome",
        "for_archetype": "all",
        "description": "Set de bienvenida para nuevos usuarios (Day 1 milestone)",
        "file_ids": [
            "PLACEHOLDER_FILE_ID_1",  # Foto sensual pero elegante
            "PLACEHOLDER_FILE_ID_2",  # Foto con teaser de contenido
            "PLACEHOLDER_FILE_ID_3"   # Foto con mensaje de bienvenida
        ]
    },
    {
        "id": "day_7_vip_teaser",
        "name": "💎 Semana Especial - Oferta VIP",
        "type": "photo_set",
        "tier": "free",
        "category": "teaser",
        "for_archetype": "all",
        "description": "Teaser VIP con cupón de descuento (Day 7 milestone)",
        "file_ids": [
            "PLACEHOLDER_FILE_ID_4",  # Foto provocativa
            "PLACEHOLDER_FILE_ID_5",  # Foto con mensaje de oferta
            "PLACEHOLDER_FILE_ID_6"   # Foto exclusiva de muestra
        ]
    },
    {
        "id": "day_30_celebration",
        "name": "🎉 Un Mes Juntos - Celebración",
        "type": "mixed",
        "tier": "free",
        "category": "milestone",
        "for_archetype": "all",
        "description": "Celebración de 30 días (Day 30 milestone)",
        "file_ids": [
            "PLACEHOLDER_FILE_ID_7",   # Video corto de agradecimiento
            "PLACEHOLDER_FILE_ID_8",   # Foto exclusiva
            "PLACEHOLDER_FILE_ID_9",   # Foto con mensaje personal
            "PLACEHOLDER_FILE_ID_10"   # Cupón u oferta especial
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 🎁 REGALOS - EVENTOS ESPECÍFICOS
    # ─────────────────────────────────────────────────────────────────────────
    {
        "id": "auction_winner_gift",
        "name": "🏆 Regalo del Ganador - Subasta",
        "type": "photo_set",
        "tier": "gift",
        "category": "surprise",
        "for_archetype": "all",
        "description": "Regalo exclusivo para ganadores de subastas",
        "file_ids": [
            "PLACEHOLDER_FILE_ID_11",  # Foto exclusiva 1
            "PLACEHOLDER_FILE_ID_12",  # Foto exclusiva 2
            "PLACEHOLDER_FILE_ID_13"   # Mensaje personalizado
        ]
    },
    {
        "id": "shop_thank_you_gift",
        "name": "💝 Gracias por tu Compra",
        "type": "photo_set",
        "tier": "gift",
        "category": "surprise",
        "for_archetype": "all",
        "description": "Regalo de agradecimiento por compra en la tienda",
        "file_ids": [
            "PLACEHOLDER_FILE_ID_14",  # Foto de agradecimiento
            "PLACEHOLDER_FILE_ID_15"   # Foto extra exclusiva
        ]
    },
    {
        "id": "level_milestone_gift",
        "name": "⭐ Nuevo Nivel Desbloqueado",
        "type": "photo_set",
        "tier": "gift",
        "category": "milestone",
        "for_archetype": "all",
        "description": "Regalo por alcanzar niveles importantes (3, 5, 7, 10)",
        "file_ids": [
            "PLACEHOLDER_FILE_ID_16",  # Foto celebración
            "PLACEHOLDER_FILE_ID_17",  # Foto exclusiva del nivel
            "PLACEHOLDER_FILE_ID_18"   # Teaser del siguiente nivel
        ]
    },
    {
        "id": "loyalty_reward_gift",
        "name": "💖 Recompensa por Lealtad",
        "type": "photo_set",
        "tier": "gift",
        "category": "surprise",
        "for_archetype": "all",
        "description": "Regalo por lealtad (30, 60, 90 días activo)",
        "file_ids": [
            "PLACEHOLDER_FILE_ID_19",  # Foto especial
            "PLACEHOLDER_FILE_ID_20"   # Mensaje personalizado
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 🌙 REGALOS VIP - PREMIUM
    # ─────────────────────────────────────────────────────────────────────────
    {
        "id": "vip_welcome_pack",
        "name": "💎 Pack de Bienvenida VIP",
        "type": "mixed",
        "tier": "vip",
        "category": "welcome",
        "for_archetype": "all",
        "description": "Pack exclusivo para nuevos VIPs",
        "file_ids": [
            "PLACEHOLDER_FILE_ID_21",  # Video de bienvenida VIP
            "PLACEHOLDER_FILE_ID_22",  # Foto exclusiva 1
            "PLACEHOLDER_FILE_ID_23",  # Foto exclusiva 2
            "PLACEHOLDER_FILE_ID_24",  # Foto exclusiva 3
            "PLACEHOLDER_FILE_ID_25"   # Audio mensaje personal
        ]
    },
    {
        "id": "first_purchase_surprise",
        "name": "🎀 Primera Compra - Sorpresa",
        "type": "photo_set",
        "tier": "gift",
        "category": "surprise",
        "for_archetype": "all",
        "description": "Sorpresa especial para la primera compra de un usuario",
        "file_ids": [
            "PLACEHOLDER_FILE_ID_26",  # Foto sorpresa
            "PLACEHOLDER_FILE_ID_27"   # Mensaje de Diana
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 🔥 SORPRESAS ESPONTÁNEAS - ADMIN
    # ─────────────────────────────────────────────────────────────────────────
    {
        "id": "diana_surprise_light",
        "name": "✨ Sorpresa de Diana (Light)",
        "type": "photo_set",
        "tier": "gift",
        "category": "surprise",
        "for_archetype": "luz",
        "description": "Sorpresa para arquetipo Luz - sensual pero tierna",
        "file_ids": [
            "PLACEHOLDER_FILE_ID_28",  # Foto romántica
            "PLACEHOLDER_FILE_ID_29"   # Mensaje personal
        ]
    },
    {
        "id": "diana_surprise_dark",
        "name": "🔥 Sorpresa de Diana (Dark)",
        "type": "photo_set",
        "tier": "gift",
        "category": "surprise",
        "for_archetype": "sombra",
        "description": "Sorpresa para arquetipo Sombra - más atrevida",
        "file_ids": [
            "PLACEHOLDER_FILE_ID_30",  # Foto provocativa
            "PLACEHOLDER_FILE_ID_31"   # Mensaje intenso
        ]
    },
    {
        "id": "midnight_whisper",
        "name": "🌙 Susurro de Medianoche",
        "type": "audio",
        "tier": "gift",
        "category": "surprise",
        "for_archetype": "all",
        "description": "Audio mensaje sensual de Diana",
        "file_ids": [
            "PLACEHOLDER_AUDIO_ID_1"   # Audio mensaje
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 🎂 EVENTOS ESPECIALES
    # ─────────────────────────────────────────────────────────────────────────
    {
        "id": "birthday_gift",
        "name": "🎂 Feliz Cumpleaños",
        "type": "photo_set",
        "tier": "gift",
        "category": "surprise",
        "for_archetype": "all",
        "description": "Regalo de cumpleaños personalizado",
        "file_ids": [
            "PLACEHOLDER_FILE_ID_32",  # Foto celebración
            "PLACEHOLDER_FILE_ID_33",  # Mensaje de cumpleaños
            "PLACEHOLDER_FILE_ID_34"   # Regalo especial
        ]
    },
    {
        "id": "valentines_gift",
        "name": "💘 San Valentín con Diana",
        "type": "mixed",
        "tier": "gift",
        "category": "surprise",
        "for_archetype": "all",
        "description": "Regalo especial de San Valentín",
        "file_ids": [
            "PLACEHOLDER_FILE_ID_35",  # Video romántico
            "PLACEHOLDER_FILE_ID_36",  # Foto exclusiva
            "PLACEHOLDER_FILE_ID_37"   # Mensaje de amor
        ]
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 🏅 LOGROS ESPECIALES
    # ─────────────────────────────────────────────────────────────────────────
    {
        "id": "all_missions_complete",
        "name": "🏆 Maestro de Misiones",
        "type": "photo_set",
        "tier": "premium",
        "category": "milestone",
        "for_archetype": "all",
        "description": "Regalo por completar todas las misiones disponibles",
        "file_ids": [
            "PLACEHOLDER_FILE_ID_38",  # Foto ultra exclusiva 1
            "PLACEHOLDER_FILE_ID_39",  # Foto ultra exclusiva 2
            "PLACEHOLDER_FILE_ID_40"   # Mensaje de felicitación
        ]
    },
    {
        "id": "top_spender_reward",
        "name": "👑 Elite Kinky",
        "type": "mixed",
        "tier": "premium",
        "category": "milestone",
        "for_archetype": "all",
        "description": "Recompensa para top 10 usuarios con más inversión",
        "file_ids": [
            "PLACEHOLDER_FILE_ID_41",  # Video exclusivo
            "PLACEHOLDER_FILE_ID_42",  # Foto premium 1
            "PLACEHOLDER_FILE_ID_43",  # Foto premium 2
            "PLACEHOLDER_FILE_ID_44",  # Audio mensaje
            "PLACEHOLDER_FILE_ID_45"   # Cupón especial
        ]
    }
]


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE SETUP
# ═══════════════════════════════════════════════════════════════════════════════

async def create_or_update_content_set(session, set_data: dict) -> ContentSet:
    """Crea o actualiza un ContentSet"""

    # Verificar si existe
    stmt = select(ContentSet).where(ContentSet.id == set_data["id"])
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        # Actualizar
        existing.name = set_data["name"]
        existing.type = set_data["type"]
        existing.tier = set_data["tier"]
        existing.file_ids = set_data["file_ids"]
        existing.description = set_data.get("description")
        existing.category = set_data.get("category")
        existing.for_archetype = set_data.get("for_archetype", "all")
        content_set = existing
        action = "actualizado"
    else:
        # Crear nuevo
        content_set = ContentSet(
            id=set_data["id"],
            name=set_data["name"],
            type=set_data["type"],
            tier=set_data["tier"],
            file_ids=set_data["file_ids"],
            description=set_data.get("description"),
            category=set_data.get("category"),
            for_archetype=set_data.get("for_archetype", "all"),
            is_active=True
        )
        session.add(content_set)
        action = "creado"

    return content_set, action


async def setup_journey_module(session: AsyncSession):
    """Setup principal del módulo Journey/Regalos"""

    logger.info("╔═══════════════════════════════════════════════")
    logger.info("║  🎁 SETUP: MÓDULO JOURNEY/REGALOS")
    logger.info("╚═══════════════════════════════════════════════\n")

    created_count = 0
    updated_count = 0

    logger.info("📦 Creando Content Sets...")
    logger.info("─" * 50)

    for set_data in CONTENT_SETS:
        content_set, action = await create_or_update_content_set(session, set_data)

        if action == "creado":
            created_count += 1
            emoji = "✨"
        else:
            updated_count += 1
            emoji = "🔄"

        logger.info(f"\n  {emoji} {content_set.name}")
        logger.info(f"     ID: {content_set.id}")
        logger.info(f"     Tipo: {content_set.type} | Tier: {content_set.tier}")
        logger.info(f"     Categoría: {content_set.category}")
        logger.info(f"     Archivos: {len(content_set.file_ids)} placeholders")

    await session.commit()

    logger.info("\n╔═══════════════════════════════════════════════")
    logger.info("║  ✅ SETUP COMPLETADO")
    logger.info("╠═══════════════════════════════════════════════")
    logger.info(f"║  📦 Content Sets creados: {created_count}")
    logger.info(f"║  🔄 Content Sets actualizados: {updated_count}")
    logger.info(f"║  📊 Total: {created_count + updated_count}")
    logger.info("╚═══════════════════════════════════════════════\n")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Punto de entrada principal"""

    # Configurar conexión a BD
    DATABASE_URL = "sqlite+aiosqlite:///bot.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        try:
            await setup_journey_module(session)
            logger.info("🎉 Content Sets configurados exitosamente!\n")
            logger.info("⚠️  IMPORTANTE - PRÓXIMOS PASOS:")
            logger.info("─" * 50)
            logger.info("  1. Los file_ids son PLACEHOLDERS")
            logger.info("  2. Sube contenido real al bot para obtener file_ids")
            logger.info("  3. Actualiza los ContentSets con los IDs reales\n")

        except Exception as e:
            logger.error(f"❌ Error durante el setup: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
