# database/migrations/add_midivan_features.py
"""
Database Migration: Add Mi Diván VIP Features

Creates tables for:
- Compatibility quizzes with Diana
- Anonymous messages to Diana
- Quiz attempts and results
- Activity tracking

VIP exclusive features to enhance engagement.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class MiDivanFeaturesMigration:
    """
    Handles creation of Mi Diván feature tables.
    Safe to run multiple times - checks for existing tables.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def run_migration(self) -> bool:
        """
        Executes the complete Mi Diván features migration.
        Returns True if successful, False if any errors.
        """
        try:
            logger.info("Starting Mi Diván features database migration...")

            # Create all tables
            await self._create_compatibility_quizzes_table()
            await self._create_quiz_questions_table()
            await self._create_quiz_options_table()
            await self._create_quiz_attempts_table()
            await self._create_anonymous_messages_table()
            await self._create_divan_activities_table()

            # Add indexes for performance
            await self._create_indexes()

            await self.session.commit()
            logger.info("Mi Diván features migration completed successfully")
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            await self.session.rollback()
            return False

    async def _create_compatibility_quizzes_table(self):
        """Create compatibility quizzes table"""

        sql = """
        CREATE TABLE IF NOT EXISTS compatibility_quizzes (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            besitos_reward INTEGER NOT NULL DEFAULT 50,
            total_questions INTEGER NOT NULL DEFAULT 0,
            average_completion_time INTEGER
        );
        """

        await self.session.execute(text(sql))
        logger.info("Created compatibility_quizzes table")

    async def _create_quiz_questions_table(self):
        """Create quiz questions table"""

        sql = """
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id SERIAL PRIMARY KEY,
            quiz_id INTEGER NOT NULL REFERENCES compatibility_quizzes(id) ON DELETE CASCADE,
            question_number INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            category VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            UNIQUE(quiz_id, question_number)
        );
        """

        await self.session.execute(text(sql))
        logger.info("Created quiz_questions table")

    async def _create_quiz_options_table(self):
        """Create quiz options table"""

        sql = """
        CREATE TABLE IF NOT EXISTS quiz_options (
            id SERIAL PRIMARY KEY,
            question_id INTEGER NOT NULL REFERENCES quiz_questions(id) ON DELETE CASCADE,
            option_number INTEGER NOT NULL,
            option_text TEXT NOT NULL,
            compatibility_score INTEGER NOT NULL DEFAULT 50,
            diana_response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            UNIQUE(question_id, option_number),
            CHECK (compatibility_score >= 0 AND compatibility_score <= 100)
        );
        """

        await self.session.execute(text(sql))
        logger.info("Created quiz_options table")

    async def _create_quiz_attempts_table(self):
        """Create quiz attempts table"""

        sql = """
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            quiz_id INTEGER NOT NULL REFERENCES compatibility_quizzes(id) ON DELETE CASCADE,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            completed_at TIMESTAMP,
            is_completed BOOLEAN NOT NULL DEFAULT FALSE,
            current_question_number INTEGER NOT NULL DEFAULT 1,
            total_score REAL NOT NULL DEFAULT 0.0,
            compatibility_level VARCHAR(50),
            answers JSONB NOT NULL DEFAULT '{}',
            besitos_earned INTEGER NOT NULL DEFAULT 0,
            reward_claimed BOOLEAN NOT NULL DEFAULT FALSE,
            completion_time_seconds INTEGER,
            CHECK (total_score >= 0 AND total_score <= 100)
        );
        """

        await self.session.execute(text(sql))
        logger.info("Created quiz_attempts table")

    async def _create_anonymous_messages_table(self):
        """Create anonymous messages table"""

        sql = """
        CREATE TABLE IF NOT EXISTS anonymous_messages (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            message_text TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            is_read BOOLEAN NOT NULL DEFAULT FALSE,
            read_at TIMESTAMP,
            is_responded BOOLEAN NOT NULL DEFAULT FALSE,
            responded_at TIMESTAMP,
            response_text TEXT,
            response_sent_to_user BOOLEAN NOT NULL DEFAULT FALSE,
            response_sent_at TIMESTAMP,
            message_length INTEGER NOT NULL,
            sentiment VARCHAR(20),
            admin_notes TEXT,
            flagged_for_review BOOLEAN NOT NULL DEFAULT FALSE
        );
        """

        await self.session.execute(text(sql))
        logger.info("Created anonymous_messages table")

    async def _create_divan_activities_table(self):
        """Create divan activities table"""

        sql = """
        CREATE TABLE IF NOT EXISTS divan_activities (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            activity_type VARCHAR(50) NOT NULL,
            activity_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            activity_data JSONB NOT NULL DEFAULT '{}'
        );
        """

        await self.session.execute(text(sql))
        logger.info("Created divan_activities table")

    async def _create_indexes(self):
        """Create performance indexes on Mi Diván tables"""

        indexes = [
            # Quiz lookups
            "CREATE INDEX IF NOT EXISTS idx_compatibility_quizzes_active ON compatibility_quizzes(is_active, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_questions_quiz_id ON quiz_questions(quiz_id, question_number)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_options_question_id ON quiz_options(question_id, option_number)",

            # Quiz attempts (hot path - frequent queries)
            "CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user_id ON quiz_attempts(user_id, started_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_attempts_quiz_user ON quiz_attempts(quiz_id, user_id)",
            "CREATE INDEX IF NOT EXISTS idx_quiz_attempts_incomplete ON quiz_attempts(user_id, quiz_id, is_completed) WHERE is_completed = FALSE",
            "CREATE INDEX IF NOT EXISTS idx_quiz_attempts_completed ON quiz_attempts(user_id, total_score DESC) WHERE is_completed = TRUE",

            # Anonymous messages (admin view - frequent admin queries)
            "CREATE INDEX IF NOT EXISTS idx_anonymous_messages_user_id ON anonymous_messages(user_id, sent_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_anonymous_messages_unread ON anonymous_messages(is_read, sent_at DESC) WHERE is_read = FALSE",
            "CREATE INDEX IF NOT EXISTS idx_anonymous_messages_pending ON anonymous_messages(is_read, is_responded, sent_at DESC) WHERE is_responded = FALSE",
            "CREATE INDEX IF NOT EXISTS idx_anonymous_messages_flagged ON anonymous_messages(flagged_for_review, sent_at DESC) WHERE flagged_for_review = TRUE",

            # Activity tracking
            "CREATE INDEX IF NOT EXISTS idx_divan_activities_user_id ON divan_activities(user_id, activity_timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_divan_activities_type ON divan_activities(activity_type, activity_timestamp DESC)"
        ]

        for index_sql in indexes:
            await self.session.execute(text(index_sql))

        logger.info("Created performance indexes for Mi Diván tables")

    async def verify_migration(self) -> Dict[str, bool]:
        """
        Verifies that all Mi Diván tables were created successfully.
        Returns dict with table names and their existence status.
        """
        tables_to_check = [
            'compatibility_quizzes',
            'quiz_questions',
            'quiz_options',
            'quiz_attempts',
            'anonymous_messages',
            'divan_activities'
        ]

        verification_results = {}

        for table_name in tables_to_check:
            try:
                result = await self.session.execute(
                    text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')")
                )
                exists = result.scalar()
                verification_results[table_name] = exists

            except Exception as e:
                logger.error(f"Error checking table {table_name}: {e}")
                verification_results[table_name] = False

        return verification_results

    async def rollback_migration(self) -> bool:
        """
        CAUTION: Completely removes all Mi Diván tables and data.
        Only use during development or if migration needs to be completely undone.
        """
        try:
            logger.warning("ROLLING BACK Mi Diván migration - ALL DATA WILL BE LOST")

            # Drop tables in reverse dependency order
            drop_statements = [
                "DROP TABLE IF EXISTS divan_activities CASCADE",
                "DROP TABLE IF EXISTS anonymous_messages CASCADE",
                "DROP TABLE IF EXISTS quiz_attempts CASCADE",
                "DROP TABLE IF EXISTS quiz_options CASCADE",
                "DROP TABLE IF EXISTS quiz_questions CASCADE",
                "DROP TABLE IF EXISTS compatibility_quizzes CASCADE"
            ]

            for statement in drop_statements:
                await self.session.execute(text(statement))

            await self.session.commit()
            logger.info("Mi Diván migration rolled back successfully")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            await self.session.rollback()
            return False


async def run_midivan_migration(session: AsyncSession) -> bool:
    """
    Convenience function to run the Mi Diván features migration.
    Can be called from existing database setup scripts.
    """
    migration = MiDivanFeaturesMigration(session)
    return await migration.run_migration()


async def verify_midivan_migration(session: AsyncSession) -> Dict[str, bool]:
    """
    Convenience function to verify the Mi Diván migration.
    """
    migration = MiDivanFeaturesMigration(session)
    return await migration.verify_migration()
