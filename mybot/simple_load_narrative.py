#!/usr/bin/env python3
"""
Script simple para cargar narrativa sin depender de config del bot.
"""
import asyncio
import sys
import os
import json
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def load_narrative_simple(json_file_path: str):
    """
    Carga narrativa directamente usando SQLAlchemy sin config del bot.
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy import select
    from database.narrative_models import StoryFragment, NarrativeChoice, Base

    # Usar la base de datos del bot
    DATABASE_URL = "sqlite+aiosqlite:///./bot.db"

    logger.info(f"🔗 Conectando a: {DATABASE_URL}")

    engine = create_async_engine(DATABASE_URL, echo=False)

    # Crear tablas si no existen
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Crear session factory
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    logger.info(f"📖 Cargando JSON desde: {json_file_path}")

    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    fragments = data.get('fragments', [])
    logger.info(f"✅ Encontrados {len(fragments)} fragmentos en el JSON")

    async with Session() as session:
        # Limpiar choices existentes
        logger.info("🧹 Limpiando decisiones existentes...")
        await session.execute(NarrativeChoice.__table__.delete())
        await session.commit()

        # Procesar fragmentos
        logger.info("📝 Procesando fragmentos...")
        for fragment_data in fragments:
            key = fragment_data.get('fragment_id') or fragment_data.get('key')
            if not key:
                logger.warning(f"⚠️  Fragmento sin ID, saltando: {fragment_data}")
                continue

            # Buscar si existe
            stmt = select(StoryFragment).where(StoryFragment.key == key)
            result = await session.execute(stmt)
            fragment = result.scalar_one_or_none()

            content = fragment_data.get('content') or fragment_data.get('text', '')
            character = fragment_data.get('character', 'Lucien')
            level = fragment_data.get('level', 1)
            required_besitos = fragment_data.get('required_besitos', 0)
            required_role = fragment_data.get('required_role')
            reward_besitos = fragment_data.get('reward_besitos', 0)
            archetype_variant = fragment_data.get('archetype_variant')

            if fragment:
                # Actualizar
                logger.info(f"  🔄 Actualizando: {key}")
                fragment.text = content
                fragment.character = character
                fragment.level = level
                fragment.min_besitos = required_besitos
                fragment.required_role = required_role
                fragment.reward_besitos = reward_besitos
                fragment.archetype_variant = archetype_variant
            else:
                # Crear nuevo
                logger.info(f"  ✨ Creando: {key}")
                fragment = StoryFragment(
                    key=key,
                    text=content,
                    character=character,
                    level=level,
                    min_besitos=required_besitos,
                    required_role=required_role,
                    reward_besitos=reward_besitos,
                    archetype_variant=archetype_variant
                )
                session.add(fragment)

        # Commit fragmentos
        await session.commit()
        logger.info("✅ Fragmentos guardados")

        # Re-cargar fragmentos para obtener IDs
        result = await session.execute(select(StoryFragment))
        fragments_map = {f.key: f for f in result.scalars().all()}

        # Procesar decisiones
        logger.info("🔀 Procesando decisiones...")
        decisions_count = 0
        for fragment_data in fragments:
            source_key = fragment_data.get('fragment_id') or fragment_data.get('key')
            if not source_key:
                continue

            source_fragment = fragments_map.get(source_key)
            if not source_fragment:
                logger.warning(f"  ⚠️  Fragmento origen no encontrado: {source_key}")
                continue

            for decision in fragment_data.get('decisions', []):
                dest_key = decision.get('next_fragment') or decision.get('destination_key')
                if not dest_key:
                    logger.warning(f"    ⚠️  Decisión sin destino en {source_key}")
                    continue

                text = decision.get('text', '')
                required_besitos_choice = decision.get('required_besitos', 0)
                required_role_choice = decision.get('required_role')

                choice = NarrativeChoice(
                    source_fragment_id=source_fragment.id,
                    destination_fragment_key=dest_key,
                    text=text,
                    required_besitos=required_besitos_choice,
                    required_role=required_role_choice
                )
                session.add(choice)
                decisions_count += 1

        await session.commit()
        logger.info(f"✅ Guardadas {decisions_count} decisiones")

    logger.info("\n🎉 ¡NARRATIVA CARGADA EXITOSAMENTE!")
    logger.info(f"   📊 {len(fragments_map)} fragmentos")
    logger.info(f"   🔀 {decisions_count} decisiones")
    logger.info("\n📌 Próximo paso: Prueba con /historia en el bot")


async def main():
    json_file = "/home/azureuser/repos/bolt_ok/mybot/narrative_fixed.json"

    if not os.path.exists(json_file):
        logger.error(f"❌ Archivo no encontrado: {json_file}")
        sys.exit(1)

    await load_narrative_simple(json_file)


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 CARGANDO NARRATIVA DESDE JSON (Modo Directo)")
    print("=" * 60)
    asyncio.run(main())
    print("=" * 60)
