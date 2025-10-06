# database/migrations/enhance_store_system.py
"""
Database Migration: Enhance Store System with Stock Management
Adds stock management fields to existing StoreProduct table.
Safe to run multiple times - checks for existing columns.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, inspect
import logging

logger = logging.getLogger(__name__)


class StoreSystemEnhancementMigration:
    """
    Handles enhancement of store system with stock management.
    Safe to run multiple times - checks for existing columns.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def run_migration(self) -> bool:
        """
        Executes the store system enhancement migration.
        Returns True if successful, False if any errors.
        """
        try:
            logger.info("Starting store system enhancement migration...")

            # Add stock management columns to StoreProduct
            await self._add_stock_management_columns()

            # Update existing products with default values
            await self._update_existing_products()

            # Add indexes for performance
            await self._create_indexes()

            await self.session.commit()
            logger.info("Store system enhancement migration completed successfully")
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            await self.session.rollback()
            return False

    async def _column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table."""
        try:
            result = await self.session.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_name = :table_name
                AND column_name = :column_name
            """), {"table_name": table_name, "column_name": column_name})
            return result.scalar() > 0
        except Exception:
            return False

    async def _add_stock_management_columns(self):
        """Add stock management columns to StoreProduct table."""
        logger.info("Adding stock management columns to store_products...")

        columns_to_add = [
            ("current_stock", "INTEGER"),
            ("max_stock", "INTEGER"),
            ("is_limited_edition", "BOOLEAN DEFAULT FALSE"),
            ("stock_alert_threshold", "INTEGER DEFAULT 5")
        ]

        for column_name, column_definition in columns_to_add:
            if not await self._column_exists("store_products", column_name):
                await self.session.execute(text(f"""
                    ALTER TABLE store_products
                    ADD COLUMN {column_name} {column_definition}
                """))
                logger.info(f"Added column: {column_name}")
            else:
                logger.info(f"Column {column_name} already exists, skipping...")

    async def _update_existing_products(self):
        """Update existing products with sensible defaults."""
        logger.info("Updating existing products with default values...")

        # Set default price to 2 for products that might have NULL or 0 price
        await self.session.execute(text("""
            UPDATE store_products
            SET price = 2
            WHERE price IS NULL OR price = 0
        """))

        # Set unlimited stock for existing products (NULL = unlimited)
        # This is intentionally left as NULL to maintain unlimited stock
        logger.info("Existing products will have unlimited stock (current_stock = NULL)")

    async def _create_indexes(self):
        """Create performance indexes for store system."""
        logger.info("Creating performance indexes...")

        indexes_to_create = [
            "idx_store_products_active_stock",
            "idx_store_products_vip_only",
            "idx_store_products_category_active"
        ]

        for index_name in indexes_to_create:
            try:
                if index_name == "idx_store_products_active_stock":
                    await self.session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_store_products_active_stock
                        ON store_products(is_active, current_stock)
                        WHERE is_active = true
                    """))
                elif index_name == "idx_store_products_vip_only":
                    await self.session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_store_products_vip_only
                        ON store_products(vip_only, is_active)
                    """))
                elif index_name == "idx_store_products_category_active":
                    await self.session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_store_products_category_active
                        ON store_products(category_id, is_active, sort_order)
                    """))

                logger.info(f"Created index: {index_name}")
            except Exception as e:
                logger.warning(f"Index {index_name} might already exist: {e}")

    async def rollback_migration(self) -> bool:
        """
        Rollback the migration if needed.
        WARNING: This will remove the added columns and their data!
        """
        try:
            logger.info("Rolling back store system enhancement migration...")

            columns_to_remove = [
                "current_stock",
                "max_stock",
                "is_limited_edition",
                "stock_alert_threshold"
            ]

            for column_name in columns_to_remove:
                if await self._column_exists("store_products", column_name):
                    await self.session.execute(text(f"""
                        ALTER TABLE store_products DROP COLUMN {column_name}
                    """))
                    logger.info(f"Removed column: {column_name}")

            await self.session.commit()
            logger.info("Rollback completed successfully")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            await self.session.rollback()
            return False


# Usage example:
# async def run_store_migration(session: AsyncSession):
#     migration = StoreSystemEnhancementMigration(session)
#     success = await migration.run_migration()
#     return success