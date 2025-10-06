"""
Migración: Crear tablas para Content Journey System

Tablas creadas:
- content_sets: Sets de contenido multimedia
- gift_records: Registro de regalos enviados
- user_milestones: Tracking de milestones del usuario
"""
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def run_migration():
    """Ejecuta la migración de base de datos"""
    db_url = 'sqlite+aiosqlite:///bot.db'
    engine = create_async_engine(db_url, echo=False)

    async with engine.begin() as conn:
        print("🔄 Iniciando migración: create_content_journey_tables...")

        # Crear tabla content_sets
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS content_sets (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                type VARCHAR NOT NULL,
                tier VARCHAR NOT NULL DEFAULT 'free',
                file_ids TEXT DEFAULT '[]',
                description TEXT,
                category VARCHAR,
                for_archetype VARCHAR DEFAULT 'all',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """))
        print("✅ Tabla content_sets creada")

        # Crear tabla gift_records
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gift_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT NOT NULL,
                content_set_id VARCHAR NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                context VARCHAR,
                trigger_type VARCHAR,
                sent_by_admin BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (content_set_id) REFERENCES content_sets(id)
            )
        """))
        print("✅ Tabla gift_records creada")

        # Crear tabla user_milestones
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id BIGINT NOT NULL,
                milestone_type VARCHAR NOT NULL,
                completed BOOLEAN DEFAULT 0,
                completed_at TIMESTAMP,
                data TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, milestone_type)
            )
        """))
        print("✅ Tabla user_milestones creada")

        # Crear índices para optimizar queries
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_gift_records_user
            ON gift_records(user_id)
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_user_milestones_user
            ON user_milestones(user_id)
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_content_sets_tier
            ON content_sets(tier)
        """))

        print("✅ Índices creados")
        print("\n🎉 Migración completada exitosamente!")

    await engine.dispose()


if __name__ == "__main__":
    import sys
    import os

    # Agregar variable de entorno temporal para evitar error
    if not os.environ.get('BOT_TOKEN'):
        os.environ['BOT_TOKEN'] = 'migration_token'

    asyncio.run(run_migration())
