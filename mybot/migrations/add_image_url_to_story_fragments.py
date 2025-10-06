#!/usr/bin/env python3
"""
Database migration script to add image_url column to story_fragments table.

This migration adds optional image support to narrative fragments.

Usage:
    python migrations/add_image_url_to_story_fragments.py

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


async def add_image_url_column():
    """Add image_url column to story_fragments table."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            # Check if column already exists
            exists = await check_column_exists(session, "story_fragments", "image_url")

            if exists:
                logger.info("✅ Column 'image_url' already exists in 'story_fragments' table")
                return True

            logger.info("Adding 'image_url' column to 'story_fragments' table...")

            # Add the column
            await session.execute(
                text("""
                    ALTER TABLE story_fragments
                    ADD COLUMN image_url VARCHAR(500)
                """)
            )

            await session.commit()
            logger.info("✅ Successfully added 'image_url' column to 'story_fragments' table")
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
                text("SELECT id, key, text, image_url FROM story_fragments LIMIT 1")
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
    logger.info("Starting migration: Add image_url to story_fragments")
    logger.info("=" * 60)

    # Run migration
    success = await add_image_url_column()

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
    logger.info("  2. Story fragments can now have optional images")
    logger.info("  3. Set image_url when creating/editing fragments")
    logger.info("  4. Images will be displayed above fragment text")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
