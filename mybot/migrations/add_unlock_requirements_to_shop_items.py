#!/usr/bin/env python3
"""
Database migration script to add unlock_requirements JSON field to shop_items table.

This migration adds compound condition support for shop products.

Usage:
    python migrations/add_unlock_requirements_to_shop_items.py

Requirements:
    - Database must be accessible
    - BOT_TOKEN environment variable must be set (for database connection)
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_column_exists(session, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    try:
        # SQLite-specific query
        result = await session.execute(
            text(f"PRAGMA table_info({table_name})")
        )
        columns = result.fetchall()
        column_names = [col[1] for col in columns]
        return column_name in column_names
    except Exception as e:
        logger.error(f"Error checking column existence: {e}")
        return False


def get_direct_session_factory():
    """Create a session factory without models."""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'bot.db')
    db_url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(db_url, echo=False)
    return async_sessionmaker(engine, expire_on_commit=False)


async def add_unlock_requirements_field():
    """Add unlock_requirements JSON column to shop_items table."""
    session_factory = get_direct_session_factory()
    async with session_factory() as session:
        try:
            # Check if unlock_requirements column already exists
            exists = await check_column_exists(session, "shop_items", "unlock_requirements")

            if not exists:
                logger.info("Adding 'unlock_requirements' column to 'shop_items' table...")
                await session.execute(
                    text("""
                        ALTER TABLE shop_items
                        ADD COLUMN unlock_requirements JSON
                    """)
                )
                await session.commit()
                logger.info("✅ Successfully added 'unlock_requirements' column")
            else:
                logger.info("✅ Column 'unlock_requirements' already exists")

            return True

        except Exception as e:
            logger.error(f"❌ Error adding column: {e}")
            await session.rollback()
            return False


async def verify_migration():
    """Verify that the migration was successful."""
    session_factory = get_direct_session_factory()
    async with session_factory() as session:
        try:
            # Try to query the new column
            result = await session.execute(
                text("SELECT id, name, unlock_requirements FROM shop_items LIMIT 1")
            )
            result.fetchone()
            logger.info("✅ Migration verified successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Migration verification failed: {e}")
            return False


async def main():
    """Run the migration."""
    logger.info("=" * 60)
    logger.info("Starting migration: Add unlock_requirements to shop_items")
    logger.info("=" * 60)

    # Note: We don't call init_db() because it would try to create tables
    # with the new column that doesn't exist yet
    logger.info("Connecting to database...")

    # Run migration
    success = await add_unlock_requirements_field()

    if not success:
        logger.error("Migration failed!")
        sys.exit(1)

    # Verify migration
    verified = await verify_migration()

    if not verified:
        logger.error("Migration verification failed!")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("✅ Migration completed successfully!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Next steps:")
    logger.info("  1. Restart the bot")
    logger.info("  2. Products can now have compound unlock requirements")
    logger.info("  3. Use Admin → Tienda → Edit → 🔐 Requisitos")
    logger.info("")
    logger.info("Features:")
    logger.info("  • unlock_requirements (NULL = no requirements)")
    logger.info("  • JSON structure with operator (AND/OR) and conditions")
    logger.info("  • Supported condition types:")
    logger.info("    - level: User level")
    logger.info("    - vip_status: VIP subscription status")
    logger.info("    - owns_item: Owns another shop item")
    logger.info("    - points: User points (besitos)")
    logger.info("    - owns_lore_piece: Has unlocked narrative piece")
    logger.info("    - completed_mission: Has completed mission")
    logger.info("")
    logger.info("Quick Templates Available:")
    logger.info("  • 👑 Solo VIP")
    logger.info("  • ⭐ Nivel 5+")
    logger.info("  • 💎 VIP + Nivel 10")
    logger.info("  • ⚙️ Manual (JSON) - For custom requirements")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
