#!/usr/bin/env python3
"""
Database migration script to add unlocks_fragment_key column to shop_items table.

This migration allows shop products to unlock narrative fragments directly.

Usage:
    python migrations/add_unlocks_fragment_key_to_shop_items.py

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
from database.setup import get_session_factory

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


async def add_unlocks_fragment_key_column():
    """Add unlocks_fragment_key column to shop_items table."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            # Check if column already exists
            exists = await check_column_exists(session, "shop_items", "unlocks_fragment_key")

            if exists:
                logger.info("✅ Column 'unlocks_fragment_key' already exists in 'shop_items' table")
                return True

            logger.info("Adding 'unlocks_fragment_key' column to 'shop_items' table...")

            # Add the column
            await session.execute(
                text("""
                    ALTER TABLE shop_items
                    ADD COLUMN unlocks_fragment_key VARCHAR(50)
                """)
            )

            await session.commit()
            logger.info("✅ Successfully added 'unlocks_fragment_key' column to 'shop_items' table")
            return True

        except Exception as e:
            logger.error(f"❌ Error adding column: {e}")
            await session.rollback()
            return False


async def verify_migration():
    """Verify that the migration was successful."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            # Try to query the new column
            result = await session.execute(
                text("SELECT id, name, unlocks_fragment_key FROM shop_items LIMIT 1")
            )
            result.fetchone()
            logger.info("✅ Migration verified successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Migration verification failed: {e}")
            return False


async def main():
    """Run the migration."""
    # Initialize database first
    from database.setup import init_db
    await init_db()

    logger.info("=" * 60)
    logger.info("Starting migration: Add unlocks_fragment_key to shop_items")
    logger.info("=" * 60)

    # Run migration
    success = await add_unlocks_fragment_key_column()

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
    logger.info("  2. Products can now unlock narrative fragments")
    logger.info("  3. Use Admin → Tienda → Create/Edit to configure fragment unlocks")
    logger.info("  4. Set unlocks_fragment_key to the fragment key (e.g., 'start', 'chapter_2')")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
