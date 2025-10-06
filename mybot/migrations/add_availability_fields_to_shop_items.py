#!/usr/bin/env python3
"""
Database migration script to add availability date fields to shop_items table.

This migration adds temporal availability scheduling for shop products.

Usage:
    python migrations/add_availability_fields_to_shop_items.py

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
from database.setup import get_session_factory, init_db

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


async def add_availability_fields():
    """Add available_from and available_until columns to shop_items table."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            # Check if available_from column already exists
            from_exists = await check_column_exists(session, "shop_items", "available_from")
            # Check if available_until column already exists
            until_exists = await check_column_exists(session, "shop_items", "available_until")

            changes_made = False

            if not from_exists:
                logger.info("Adding 'available_from' column to 'shop_items' table...")
                await session.execute(
                    text("""
                        ALTER TABLE shop_items
                        ADD COLUMN available_from DATETIME
                    """)
                )
                changes_made = True
                logger.info("✅ Successfully added 'available_from' column")
            else:
                logger.info("✅ Column 'available_from' already exists")

            if not until_exists:
                logger.info("Adding 'available_until' column to 'shop_items' table...")
                await session.execute(
                    text("""
                        ALTER TABLE shop_items
                        ADD COLUMN available_until DATETIME
                    """)
                )
                changes_made = True
                logger.info("✅ Successfully added 'available_until' column")
            else:
                logger.info("✅ Column 'available_until' already exists")

            if changes_made:
                await session.commit()
                logger.info("✅ Migration completed successfully")
            else:
                logger.info("✅ No changes needed - columns already exist")

            return True

        except Exception as e:
            logger.error(f"❌ Error adding columns: {e}")
            await session.rollback()
            return False


async def verify_migration():
    """Verify that the migration was successful."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            # Try to query the new columns
            result = await session.execute(
                text("SELECT id, name, available_from, available_until FROM shop_items LIMIT 1")
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
    logger.info("Starting migration: Add availability fields to shop_items")
    logger.info("=" * 60)

    # Initialize database first
    logger.info("Initializing database...")
    await init_db()

    # Run migration
    success = await add_availability_fields()

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
    logger.info("  2. Products can now have temporal availability")
    logger.info("  3. Use Admin → Tienda → Create/Edit to configure dates")
    logger.info("")
    logger.info("Features:")
    logger.info("  • available_from (NULL = available immediately)")
    logger.info("  • available_until (NULL = available forever)")
    logger.info("")
    logger.info("Examples:")
    logger.info("  • Event item: 01/12/2025 - 31/12/2025")
    logger.info("  • Pre-order: available from 15/01/2026")
    logger.info("  • Limited time: available until 28/02/2026")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
