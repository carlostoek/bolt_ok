#!/usr/bin/env python3
"""
Script para limpiar quizzes duplicados y dejar solo uno activo.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, func
from database.midivan_models import CompatibilityQuiz
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Clean duplicate quizzes"""
    import os
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
            # Get all quizzes
            stmt = select(CompatibilityQuiz).order_by(CompatibilityQuiz.created_at.desc())
            result = await session.execute(stmt)
            quizzes = result.scalars().all()

            logger.info(f"Found {len(quizzes)} total quizzes")

            if len(quizzes) == 0:
                logger.info("No quizzes found. Nothing to clean.")
                return

            # Keep the most recent one active, deactivate the rest
            for idx, quiz in enumerate(quizzes):
                if idx == 0:
                    # Keep first (most recent) active
                    quiz.is_active = True
                    logger.info(f"✅ Keeping active: {quiz.title} (ID: {quiz.id})")
                else:
                    # Deactivate older duplicates
                    quiz.is_active = False
                    logger.info(f"⏸️ Deactivating: {quiz.title} (ID: {quiz.id})")

            await session.commit()

            logger.info("=" * 60)
            logger.info("✅ Cleanup completed!")
            logger.info(f"Active quizzes: 1")
            logger.info(f"Inactive quizzes: {len(quizzes) - 1}")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Error: {e}")
            await session.rollback()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
