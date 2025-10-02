#!/usr/bin/env python3
"""
Fix Mi Diván tables to use SQLite-compatible auto-increment.
"""

import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def fix_tables():
    """Drop and recreate tables with SQLite-compatible syntax"""

    # Set dummy BOT_TOKEN
    if not os.environ.get("BOT_TOKEN"):
        os.environ["BOT_TOKEN"] = "MIGRATION_DUMMY_TOKEN"

    try:
        from utils.config import Config
        DATABASE_URL = Config.DATABASE_URL
    except Exception:
        DATABASE_URL = "sqlite+aiosqlite:///bot.db"

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        try:
            logger.info("Dropping old tables...")

            # Drop tables in reverse order (respect foreign keys)
            drop_statements = [
                "DROP TABLE IF EXISTS divan_activities",
                "DROP TABLE IF EXISTS anonymous_messages",
                "DROP TABLE IF EXISTS quiz_attempts",
                "DROP TABLE IF EXISTS quiz_options",
                "DROP TABLE IF EXISTS quiz_questions",
                "DROP TABLE IF EXISTS compatibility_quizzes"
            ]

            for stmt in drop_statements:
                await session.execute(text(stmt))

            await session.commit()
            logger.info("✓ Old tables dropped")

            logger.info("Creating tables with SQLite-compatible syntax...")

            # Compatibility Quizzes
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS compatibility_quizzes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    besitos_reward INTEGER NOT NULL DEFAULT 50,
                    total_questions INTEGER NOT NULL DEFAULT 0,
                    average_completion_time INTEGER
                )
            """))
            logger.info("✓ Created compatibility_quizzes")

            # Quiz Questions
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS quiz_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quiz_id INTEGER NOT NULL REFERENCES compatibility_quizzes(id) ON DELETE CASCADE,
                    question_number INTEGER NOT NULL,
                    question_text TEXT NOT NULL,
                    category VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    UNIQUE(quiz_id, question_number)
                )
            """))
            logger.info("✓ Created quiz_questions")

            # Quiz Options
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS quiz_options (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL REFERENCES quiz_questions(id) ON DELETE CASCADE,
                    option_number INTEGER NOT NULL,
                    option_text TEXT NOT NULL,
                    compatibility_score INTEGER NOT NULL DEFAULT 50,
                    diana_response TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    UNIQUE(question_id, option_number),
                    CHECK (compatibility_score >= 0 AND compatibility_score <= 100)
                )
            """))
            logger.info("✓ Created quiz_options")

            # Quiz Attempts
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS quiz_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id BIGINT NOT NULL,
                    quiz_id INTEGER NOT NULL REFERENCES compatibility_quizzes(id) ON DELETE CASCADE,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    is_completed BOOLEAN NOT NULL DEFAULT 0,
                    current_question_number INTEGER DEFAULT 1,
                    total_score REAL DEFAULT 0.0,
                    compatibility_level VARCHAR(50),
                    answers JSON,
                    besitos_awarded INTEGER DEFAULT 0
                )
            """))
            logger.info("✓ Created quiz_attempts")

            # Anonymous Messages
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS anonymous_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id BIGINT NOT NULL,
                    message_text TEXT NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    is_read BOOLEAN NOT NULL DEFAULT 0,
                    read_at TIMESTAMP,
                    is_responded BOOLEAN NOT NULL DEFAULT 0,
                    response_text TEXT,
                    responded_at TIMESTAMP,
                    user_notified BOOLEAN NOT NULL DEFAULT 0
                )
            """))
            logger.info("✓ Created anonymous_messages")

            # Divan Activities
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS divan_activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id BIGINT NOT NULL,
                    activity_type VARCHAR(50) NOT NULL,
                    activity_data JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
                )
            """))
            logger.info("✓ Created divan_activities")

            # Create indexes
            logger.info("Creating indexes...")

            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user ON quiz_attempts(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_quiz_attempts_quiz ON quiz_attempts(quiz_id)",
                "CREATE INDEX IF NOT EXISTS idx_quiz_attempts_completed ON quiz_attempts(is_completed, completed_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_quiz_questions_quiz ON quiz_questions(quiz_id)",
                "CREATE INDEX IF NOT EXISTS idx_quiz_options_question ON quiz_options(question_id)",
                "CREATE INDEX IF NOT EXISTS idx_anonymous_messages_user ON anonymous_messages(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_anonymous_messages_read ON anonymous_messages(is_read, sent_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_anonymous_messages_responded ON anonymous_messages(is_responded)",
                "CREATE INDEX IF NOT EXISTS idx_divan_activities_user ON divan_activities(user_id, created_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_divan_activities_type ON divan_activities(activity_type)",
                "CREATE INDEX IF NOT EXISTS idx_compatibility_quizzes_active ON compatibility_quizzes(is_active, created_at DESC)"
            ]

            for index_sql in indexes:
                await session.execute(text(index_sql))

            logger.info("✓ Created all indexes")

            await session.commit()
            logger.info("=" * 60)
            logger.info("✅ All Mi Diván tables fixed successfully!")
            logger.info("=" * 60)
            return True

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            await session.rollback()
            return False

    await engine.dispose()


if __name__ == "__main__":
    success = asyncio.run(fix_tables())
    sys.exit(0 if success else 1)
