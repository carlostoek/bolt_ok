#!/usr/bin/env python3
"""
Database migration script to add stock and purchase limit fields to shop_items table.

This migration adds inventory control features to shop products.

Usage:
    python migrations/add_stock_fields_to_shop_items.py

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


async def add_stock_fields():
    """Add stock_limit and max_purchases_per_user columns to shop_items table."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            # Check if stock_limit column already exists
            stock_exists = await check_column_exists(session, "shop_items", "stock_limit")
            # Check if max_purchases_per_user column already exists
            max_purch_exists = await check_column_exists(session, "shop_items", "max_purchases_per_user")

            changes_made = False

            if not stock_exists:
                logger.info("Adding 'stock_limit' column to 'shop_items' table...")
                await session.execute(
                    text("""
                        ALTER TABLE shop_items
                        ADD COLUMN stock_limit INTEGER
                    """)
                )
                changes_made = True
                logger.info("✅ Successfully added 'stock_limit' column")
            else:
                logger.info("✅ Column 'stock_limit' already exists")

            if not max_purch_exists:
                logger.info("Adding 'max_purchases_per_user' column to 'shop_items' table...")
                await session.execute(
                    text("""
                        ALTER TABLE shop_items
                        ADD COLUMN max_purchases_per_user INTEGER DEFAULT 1
                    """)
                )
                changes_made = True
                logger.info("✅ Successfully added 'max_purchases_per_user' column")
            else:
                logger.info("✅ Column 'max_purchases_per_user' already exists")

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
                text("SELECT id, name, stock_limit, max_purchases_per_user FROM shop_items LIMIT 1")
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
    logger.info("Starting migration: Add stock fields to shop_items")
    logger.info("=" * 60)

    # Initialize database first
    logger.info("Initializing database...")
    await init_db()

    # Run migration
    success = await add_stock_fields()

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
    logger.info("  2. Products can now have stock limits and purchase limits")
    logger.info("  3. Use Admin → Tienda → Create/Edit to configure limits")
    logger.info("")
    logger.info("Features:")
    logger.info("  • stock_limit (NULL = unlimited)")
    logger.info("  • max_purchases_per_user (0 = unlimited, default 1)")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nMigration cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
