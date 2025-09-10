#!/usr/bin/env python3
"""
Migration script to add daily_gift_streak column to user_stats table.
"""

import asyncio
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

async def add_daily_gift_streak_column():
    """Add the daily_gift_streak column to user_stats table."""
    try:
        from database.setup import init_db, get_session_factory
        
        logger.info("🔧 Initializing database...")
        await init_db()
        
        session_factory = get_session_factory()
        async with session_factory() as session:
            # Check if column already exists
            try:
                result = await session.execute(text("PRAGMA table_info(user_stats)"))
                columns = result.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'daily_gift_streak' in column_names:
                    logger.info("✅ Column daily_gift_streak already exists")
                    return
                
                # Add the column
                logger.info("🔨 Adding daily_gift_streak column to user_stats table...")
                await session.execute(text("ALTER TABLE user_stats ADD COLUMN daily_gift_streak INTEGER DEFAULT 0"))
                await session.commit()
                
                logger.info("✅ Successfully added daily_gift_streak column")
                
                # Verify the column was added
                result = await session.execute(text("PRAGMA table_info(user_stats)"))
                columns = result.fetchall()
                column_names = [col[1] for col in columns]
                
                if 'daily_gift_streak' in column_names:
                    logger.info("✅ Column verification successful")
                else:
                    logger.error("❌ Column verification failed")
                
            except Exception as e:
                logger.error(f"❌ Error adding column: {e}")
                await session.rollback()
                raise
                
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(add_daily_gift_streak_column())