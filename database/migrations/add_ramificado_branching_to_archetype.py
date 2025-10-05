# database/migrations/add_ramificado_branching_to_archetype.py
"""
Database Migration: Add Ramificado Branching Fields to ArchetypeClassification

This migration adds the necessary fields to the `archetype_classifications` table
to support the activation of the branched narrative system (Sistema Ramificado).
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)

class RamificadoBranchingMigration:
    """
    Handles the addition of ramificado branching fields to the archetype_classifications table.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upgrade(self):
        """
        Applies the migration, adding the new columns.
        """
        logger.info("Starting ramificado branching migration...")
        try:
            await self._add_ramificado_columns()
            await self.session.commit()
            logger.info("Ramificado branching migration completed successfully.")
        except Exception as e:
            logger.error(f"Error during ramificado branching migration: {e}")
            await self.session.rollback()
            raise

    async def _add_ramificado_columns(self):
        """
        Adds `ramificado_enabled` and `activation_timestamp` to the `archetype_classifications` table.
        """
        async with self.session.begin_nested():
            await self.session.execute(text(
                "ALTER TABLE archetype_classifications ADD COLUMN ramificado_enabled BOOLEAN DEFAULT FALSE NOT NULL;"
            ))
            await self.session.execute(text(
                "ALTER TABLE archetype_classifications ADD COLUMN activation_timestamp TIMESTAMP WITHOUT TIME ZONE;"
            ))
        logger.info("Added ramificado_enabled and activation_timestamp columns to archetype_classifications.")

    async def downgrade(self):
        """
        Reverts the migration, removing the new columns.
        """
        logger.warning("Rolling back ramificado branching migration - COLUMN DATA WILL BE LOST")
        try:
            await self._remove_ramificado_columns()
            await self.session.commit()
            logger.info("Ramificado branching migration rolled back successfully.")
        except Exception as e:
            logger.error(f"Error during ramificado branching migration rollback: {e}")
            await self.session.rollback()
            raise

    async def _remove_ramificado_columns(self):
        """
        Removes `ramificado_enabled` and `activation_timestamp` from the `archetype_classifications` table.
        """
        async with self.session.begin_nested():
            await self.session.execute(text(
                """
                ALTER TABLE archetype_classifications
                DROP COLUMN IF EXISTS ramificado_enabled,
                DROP COLUMN IF EXISTS activation_timestamp;
                """
            ))
        logger.info("Removed ramificado_enabled and activation_timestamp columns from archetype_classifications.")

async def run_ramificado_branching_migration(session: AsyncSession):
    """
    Convenience function to run the ramificado branching migration.
    """
    migration = RamificadoBranchingMigration(session)
    await migration.upgrade()
