"""
Migración: Agregar campos avanzados al modelo Mission

Campos agregados:
- mission_category: Categoría (narrative, social, competitive, secret)
- is_hidden: Misiones secretas
- prerequisite_mission_id: Misión requerida
- unlocks_mission_id: Misión que se desbloquea
- time_limit_minutes: Timer para urgencia
- bonus_points_if_fast: Bonus por rapidez
- min_ranking_position: Para misiones competitivas
- max_completions_global: Límite global
- current_completions_global: Contador de completaciones
- repeatable: Si puede repetirse
- reset_period: Periodo de reset (daily, weekly, monthly)
- icon_emoji: Emoji visual
- difficulty_level: Nivel de dificultad (1-5)
- xp_reward: XP adicional
- tags: Tags JSON para filtrar
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text
from database.base import DATABASE_URL


async def run_migration():
    """Ejecuta la migración de base de datos"""
    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        print("🔄 Iniciando migración: add_advanced_mission_fields...")

        # Verificar si las columnas ya existen
        check_query = text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'missions' AND column_name = 'mission_category'
        """)
        result = await conn.execute(check_query)
        exists = result.fetchone() is not None

        if exists:
            print("⚠️  Las columnas ya existen. Saltando migración.")
            return

        # Agregar nuevas columnas
        await conn.execute(text("""
            ALTER TABLE missions
            ADD COLUMN IF NOT EXISTS mission_category VARCHAR,
            ADD COLUMN IF NOT EXISTS is_hidden BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS prerequisite_mission_id VARCHAR,
            ADD COLUMN IF NOT EXISTS unlocks_mission_id VARCHAR,
            ADD COLUMN IF NOT EXISTS time_limit_minutes INTEGER,
            ADD COLUMN IF NOT EXISTS bonus_points_if_fast INTEGER,
            ADD COLUMN IF NOT EXISTS min_ranking_position INTEGER,
            ADD COLUMN IF NOT EXISTS max_completions_global INTEGER,
            ADD COLUMN IF NOT EXISTS current_completions_global INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS repeatable BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS reset_period VARCHAR,
            ADD COLUMN IF NOT EXISTS icon_emoji VARCHAR,
            ADD COLUMN IF NOT EXISTS difficulty_level INTEGER DEFAULT 1,
            ADD COLUMN IF NOT EXISTS xp_reward INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS tags JSON DEFAULT '[]'::json
        """))

        # Agregar foreign keys
        await conn.execute(text("""
            ALTER TABLE missions
            ADD CONSTRAINT fk_prerequisite_mission
            FOREIGN KEY (prerequisite_mission_id) REFERENCES missions(id) ON DELETE SET NULL
        """))

        await conn.execute(text("""
            ALTER TABLE missions
            ADD CONSTRAINT fk_unlocks_mission
            FOREIGN KEY (unlocks_mission_id) REFERENCES missions(id) ON DELETE SET NULL
        """))

        print("✅ Migración completada exitosamente!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_migration())
