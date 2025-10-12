#!/usr/bin/env python3
"""
Script para verificar que la narrativa se cargó correctamente.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

async def verify_narrative():
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy import select
    from database.narrative_models import StoryFragment, NarrativeChoice

    DATABASE_URL = "sqlite+aiosqlite:///./bot.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        # Obtener fragmento "start"
        stmt = select(StoryFragment).where(StoryFragment.key == "start")
        result = await session.execute(stmt)
        start_fragment = result.scalar_one_or_none()

        if not start_fragment:
            print("❌ No se encontró el fragmento 'start'")
            return

        print("✅ Fragmento 'start' encontrado:")
        print(f"   Key: {start_fragment.key}")
        print(f"   Character: {start_fragment.character}")
        print(f"   Level: {start_fragment.level}")
        print(f"   Reward: {start_fragment.reward_besitos} besitos")
        print(f"\n📝 Texto (primeros 200 caracteres):")
        print(f"   {start_fragment.text[:200]}...")

        # Obtener opciones del fragmento start
        stmt = select(NarrativeChoice).where(NarrativeChoice.source_fragment_id == start_fragment.id)
        result = await session.execute(stmt)
        choices = result.scalars().all()

        print(f"\n🔀 Opciones disponibles ({len(choices)}):")
        for i, choice in enumerate(choices, 1):
            print(f"   {i}. {choice.text} → {choice.destination_fragment_key}")

        # Verificar que los destinos existen
        print(f"\n🔍 Verificando destinos...")
        for choice in choices:
            stmt = select(StoryFragment).where(StoryFragment.key == choice.destination_fragment_key)
            result = await session.execute(stmt)
            dest_fragment = result.scalar_one_or_none()

            if dest_fragment:
                print(f"   ✅ {choice.destination_fragment_key} existe")
            else:
                print(f"   ❌ {choice.destination_fragment_key} NO EXISTE (fragmento huérfano)")

        # Estadísticas generales
        stmt = select(StoryFragment)
        result = await session.execute(stmt)
        total_fragments = len(result.scalars().all())

        stmt = select(NarrativeChoice)
        result = await session.execute(stmt)
        total_choices = len(result.scalars().all())

        print(f"\n📊 Estadísticas:")
        print(f"   Total fragmentos: {total_fragments}")
        print(f"   Total decisiones: {total_choices}")

        # Verificar fragmentos sin destinos (posibles finales)
        stmt = select(StoryFragment)
        result = await session.execute(stmt)
        all_fragments = result.scalars().all()

        fragments_without_choices = []
        for fragment in all_fragments:
            stmt = select(NarrativeChoice).where(NarrativeChoice.source_fragment_id == fragment.id)
            result = await session.execute(stmt)
            choices_count = len(result.scalars().all())
            if choices_count == 0:
                fragments_without_choices.append(fragment.key)

        print(f"\n🏁 Fragmentos sin opciones (posibles finales): {len(fragments_without_choices)}")
        for key in fragments_without_choices[:10]:  # Mostrar solo los primeros 10
            print(f"   - {key}")


if __name__ == "__main__":
    print("=" * 60)
    print("🔍 VERIFICANDO NARRATIVA EN BASE DE DATOS")
    print("=" * 60)
    asyncio.run(verify_narrative())
    print("=" * 60)
