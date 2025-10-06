# database/migrations/add_expanded_archetype_fields.py
"""
Database Migration: Add Expanded Archetype Classification Fields
Extends ArchetypeClassification model with 8 primary scores, 10 sub-archetype scores,
and cognitive style tracking columns for the Sistema Narrativo Ramificado Diana.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class ExpandedArchetypeFieldsMigration:
    """
    Handles extension of archetype_classifications table with expanded scoring.
    Safe to run multiple times - checks for existing columns before adding.
    Ensures zero-downtime migration with backward compatibility.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def run_migration(self) -> bool:
        """
        Executes the complete expanded archetype fields migration.
        Returns True if successful, False if any errors.
        """
        try:
            logger.info("Starting expanded archetype fields database migration...")

            # Add primary archetype score columns
            await self._add_primary_archetype_scores()

            # Add sub-archetype score columns
            await self._add_sub_archetype_scores()

            # Add cognitive style tracking columns
            await self._add_cognitive_style_tracking()

            # Add indexes for performance
            await self._create_performance_indexes()

            await self.session.commit()
            logger.info("Expanded archetype fields migration completed successfully")
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            await self.session.rollback()
            return False

    async def _add_primary_archetype_scores(self):
        """Add 8 primary archetype score columns if they don't exist"""

        primary_score_columns = [
            ("intellectual_score", "REAL DEFAULT 0.0"),
            ("emotional_score", "REAL DEFAULT 0.0"),
            ("exploratory_score", "REAL DEFAULT 0.0"),
            ("vulnerable_score", "REAL DEFAULT 0.0"),
            ("philosophical_score", "REAL DEFAULT 0.0"),
            ("direct_score", "REAL DEFAULT 0.0"),
            ("patient_score", "REAL DEFAULT 0.0"),
            ("reciprocal_score", "REAL DEFAULT 0.0")
        ]

        for column_name, column_definition in primary_score_columns:
            await self._add_column_if_not_exists(
                table_name="archetype_classifications",
                column_name=column_name,
                column_definition=column_definition
            )

        logger.info("Added primary archetype score columns")

    async def _add_sub_archetype_scores(self):
        """Add 10 sub-archetype score columns if they don't exist"""

        sub_archetype_columns = [
            ("romantic_intellectual_score", "REAL DEFAULT 0.0"),
            ("skeptical_thinker_score", "REAL DEFAULT 0.0"),
            ("hedonist_philosopher_score", "REAL DEFAULT 0.0"),
            ("pure_theorist_score", "REAL DEFAULT 0.0"),
            ("empathetic_emotional_score", "REAL DEFAULT 0.0"),
            ("passionate_emotional_score", "REAL DEFAULT 0.0"),
            ("wounded_healer_score", "REAL DEFAULT 0.0"),
            ("adventure_seeker_score", "REAL DEFAULT 0.0"),
            ("collector_explorer_score", "REAL DEFAULT 0.0"),
            ("freedom_lover_score", "REAL DEFAULT 0.0")
        ]

        for column_name, column_definition in sub_archetype_columns:
            await self._add_column_if_not_exists(
                table_name="archetype_classifications",
                column_name=column_name,
                column_definition=column_definition
            )

        logger.info("Added sub-archetype score columns")

    async def _add_cognitive_style_tracking(self):
        """Add cognitive style tracking columns if they don't exist"""

        cognitive_style_columns = [
            ("cognitive_style", "VARCHAR(50)"),
            ("response_consistency", "REAL DEFAULT 0.5"),
            ("temporal_pattern", "VARCHAR(50)")
        ]

        for column_name, column_definition in cognitive_style_columns:
            await self._add_column_if_not_exists(
                table_name="archetype_classifications",
                column_name=column_name,
                column_definition=column_definition
            )

        logger.info("Added cognitive style tracking columns")

    async def _add_column_if_not_exists(self, table_name: str, column_name: str, column_definition: str):
        """
        Safely adds a column if it doesn't already exist.
        Uses information_schema to check column existence before attempting to add.
        """
        try:
            # Check if column already exists
            check_sql = """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = :table_name
                AND column_name = :column_name
            )
            """

            result = await self.session.execute(
                text(check_sql),
                {"table_name": table_name, "column_name": column_name}
            )
            column_exists = result.scalar()

            if not column_exists:
                # Add the column
                add_column_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
                await self.session.execute(text(add_column_sql))
                logger.info(f"Added column {column_name} to {table_name}")
            else:
                logger.info(f"Column {column_name} already exists in {table_name}, skipping")

        except Exception as e:
            logger.error(f"Error adding column {column_name} to {table_name}: {e}")
            raise

    async def _create_performance_indexes(self):
        """Create performance indexes on new archetype score columns"""

        indexes = [
            # Primary archetype score indexes for fast sorting/filtering
            "CREATE INDEX IF NOT EXISTS idx_archetype_intellectual_score ON archetype_classifications(intellectual_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_archetype_emotional_score ON archetype_classifications(emotional_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_archetype_exploratory_score ON archetype_classifications(exploratory_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_archetype_vulnerable_score ON archetype_classifications(vulnerable_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_archetype_philosophical_score ON archetype_classifications(philosophical_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_archetype_direct_score ON archetype_classifications(direct_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_archetype_patient_score ON archetype_classifications(patient_score DESC)",
            "CREATE INDEX IF NOT EXISTS idx_archetype_reciprocal_score ON archetype_classifications(reciprocal_score DESC)",

            # Cognitive style indexes for behavioral analysis
            "CREATE INDEX IF NOT EXISTS idx_archetype_cognitive_style ON archetype_classifications(cognitive_style)",
            "CREATE INDEX IF NOT EXISTS idx_archetype_temporal_pattern ON archetype_classifications(temporal_pattern)",

            # Compound indexes for advanced queries
            "CREATE INDEX IF NOT EXISTS idx_archetype_confidence_primary ON archetype_classifications(archetype_confidence DESC, primary_archetype)",
            "CREATE INDEX IF NOT EXISTS idx_archetype_user_updated ON archetype_classifications(user_id, updated_at DESC)"
        ]

        for index_sql in indexes:
            try:
                await self.session.execute(text(index_sql))
            except Exception as e:
                # Continue with other indexes even if one fails
                logger.warning(f"Could not create index: {index_sql}, error: {e}")

        logger.info("Created performance indexes for expanded archetype fields")

    async def verify_migration(self) -> dict:
        """
        Verifies that all expanded archetype columns were added successfully.
        Returns dict with column names and their existence status.
        """
        columns_to_check = [
            # Primary archetype scores
            'intellectual_score', 'emotional_score', 'exploratory_score', 'vulnerable_score',
            'philosophical_score', 'direct_score', 'patient_score', 'reciprocal_score',

            # Sub-archetype scores
            'romantic_intellectual_score', 'skeptical_thinker_score', 'hedonist_philosopher_score',
            'pure_theorist_score', 'empathetic_emotional_score', 'passionate_emotional_score',
            'wounded_healer_score', 'adventure_seeker_score', 'collector_explorer_score',
            'freedom_lover_score',

            # Cognitive style tracking
            'cognitive_style', 'response_consistency', 'temporal_pattern'
        ]

        verification_results = {}

        for column_name in columns_to_check:
            try:
                result = await self.session.execute(
                    text("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = 'archetype_classifications'
                        AND column_name = :column_name
                    )
                    """),
                    {"column_name": column_name}
                )
                exists = result.scalar()
                verification_results[column_name] = exists

            except Exception as e:
                logger.error(f"Error checking column {column_name}: {e}")
                verification_results[column_name] = False

        return verification_results

    async def rollback_migration(self) -> bool:
        """
        CAUTION: Removes all expanded archetype fields and their data.
        Only use during development or if migration needs to be completely undone.
        """
        try:
            logger.warning("ROLLING BACK expanded archetype fields migration - COLUMN DATA WILL BE LOST")

            # Drop indexes first
            drop_index_statements = [
                "DROP INDEX IF EXISTS idx_archetype_intellectual_score",
                "DROP INDEX IF EXISTS idx_archetype_emotional_score",
                "DROP INDEX IF EXISTS idx_archetype_exploratory_score",
                "DROP INDEX IF EXISTS idx_archetype_vulnerable_score",
                "DROP INDEX IF EXISTS idx_archetype_philosophical_score",
                "DROP INDEX IF EXISTS idx_archetype_direct_score",
                "DROP INDEX IF EXISTS idx_archetype_patient_score",
                "DROP INDEX IF EXISTS idx_archetype_reciprocal_score",
                "DROP INDEX IF EXISTS idx_archetype_cognitive_style",
                "DROP INDEX IF EXISTS idx_archetype_temporal_pattern",
                "DROP INDEX IF EXISTS idx_archetype_confidence_primary",
                "DROP INDEX IF EXISTS idx_archetype_user_updated"
            ]

            for statement in drop_index_statements:
                try:
                    await self.session.execute(text(statement))
                except Exception as e:
                    logger.warning(f"Could not drop index: {statement}, error: {e}")

            # Drop columns (PostgreSQL specific)
            columns_to_drop = [
                'intellectual_score', 'emotional_score', 'exploratory_score', 'vulnerable_score',
                'philosophical_score', 'direct_score', 'patient_score', 'reciprocal_score',
                'romantic_intellectual_score', 'skeptical_thinker_score', 'hedonist_philosopher_score',
                'pure_theorist_score', 'empathetic_emotional_score', 'passionate_emotional_score',
                'wounded_healer_score', 'adventure_seeker_score', 'collector_explorer_score',
                'freedom_lover_score', 'cognitive_style', 'response_consistency', 'temporal_pattern'
            ]

            for column_name in columns_to_drop:
                try:
                    drop_column_sql = f"ALTER TABLE archetype_classifications DROP COLUMN IF EXISTS {column_name}"
                    await self.session.execute(text(drop_column_sql))
                except Exception as e:
                    logger.warning(f"Could not drop column {column_name}: {e}")

            await self.session.commit()
            logger.info("Expanded archetype fields migration rolled back successfully")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            await self.session.rollback()
            return False


async def run_expanded_archetype_fields_migration(session: AsyncSession) -> bool:
    """
    Convenience function to run the expanded archetype fields migration.
    Can be called from existing database setup scripts.
    """
    migration = ExpandedArchetypeFieldsMigration(session)
    return await migration.run_migration()


async def verify_expanded_archetype_fields_migration(session: AsyncSession) -> dict:
    """
    Convenience function to verify the expanded archetype fields migration.
    """
    migration = ExpandedArchetypeFieldsMigration(session)
    return await migration.verify_migration()