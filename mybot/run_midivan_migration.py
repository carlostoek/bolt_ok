#!/usr/bin/env python3
"""
Script to run the Mi Diván VIP features migration.
Run this script to add all Mi Diván tables to the database.
"""

import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from database.migrations.add_midivan_features import MiDivanFeaturesMigration
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Run the Mi Diván features migration"""

    # Import database URL from existing setup
    import os
    try:
        # Set a dummy BOT_TOKEN for migration purposes
        if not os.environ.get("BOT_TOKEN"):
            os.environ["BOT_TOKEN"] = "MIGRATION_DUMMY_TOKEN"

        from database.setup import DATABASE_URL
    except ImportError:
        logger.error("Could not import DATABASE_URL from database.setup")
        logger.info("Using default DATABASE_URL")
        DATABASE_URL = "sqlite+aiosqlite:///bot.db"

    logger.info(f"Connecting to database...")

    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # Run migration
        migration = MiDivanFeaturesMigration(session)

        logger.info("=" * 60)
        logger.info("Starting Mi Diván VIP Features Migration")
        logger.info("=" * 60)

        success = await migration.run_migration()

        if success:
            logger.info("=" * 60)
            logger.info("Migration completed successfully!")
            logger.info("=" * 60)

            # Verify migration
            logger.info("\nVerifying tables...")
            verification = await migration.verify_migration()

            all_created = all(verification.values())

            if all_created:
                logger.info("✅ All tables verified successfully!")
                for table_name, exists in verification.items():
                    logger.info(f"  ✓ {table_name}: {'EXISTS' if exists else 'MISSING'}")
            else:
                logger.warning("⚠️  Some tables were not created:")
                for table_name, exists in verification.items():
                    status = "✓" if exists else "✗"
                    logger.info(f"  {status} {table_name}: {'EXISTS' if exists else 'MISSING'}")

            logger.info("\n" + "=" * 60)
            logger.info("Mi Diván Features Created:")
            logger.info("=" * 60)
            logger.info("💘 Compatibility Quiz System")
            logger.info("  • Create quizzes with multiple questions")
            logger.info("  • Track user attempts and scores")
            logger.info("  • Award besitos based on completion")
            logger.info("")
            logger.info("✉️  Anonymous Messaging System")
            logger.info("  • Users send anonymous messages to Diana")
            logger.info("  • Diana responds through admin panel")
            logger.info("  • Full conversation history")
            logger.info("")
            logger.info("📊 Activity Tracking")
            logger.info("  • Monitor user engagement")
            logger.info("  • Analytics and statistics")
            logger.info("")
            logger.info("=" * 60)
            logger.info("Next Steps:")
            logger.info("=" * 60)
            logger.info("1. Register handlers in main bot file")
            logger.info("2. Create initial compatibility quiz")
            logger.info("3. Add admin menu option for Mi Diván")
            logger.info("4. Test VIP user experience")

            return 0 if all_created else 1
        else:
            logger.error("=" * 60)
            logger.error("Migration failed!")
            logger.error("=" * 60)
            return 1

    await engine.dispose()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
