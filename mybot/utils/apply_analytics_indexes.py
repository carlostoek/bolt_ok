"""
Utility to apply analytics performance indexes to the database.
Task 30: Optimize database queries for analytics performance.

This script applies the performance optimization indexes to improve
analytics query performance.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.setup import init_db
from database.migrations.add_analytics_indexes import upgrade_database_indexes, downgrade_database_indexes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def apply_indexes():
    """Apply analytics performance indexes to the database."""
    try:
        logger.info("Initializing database connection...")
        engine = await init_db()

        logger.info("Applying analytics performance indexes...")
        await upgrade_database_indexes(engine)

        logger.info("✅ Analytics indexes applied successfully!")
        logger.info("Performance optimization is now active.")

    except Exception as e:
        logger.error(f"❌ Error applying indexes: {e}")
        raise

async def remove_indexes():
    """Remove analytics performance indexes from the database."""
    try:
        logger.info("Initializing database connection...")
        engine = await init_db()

        logger.info("Removing analytics performance indexes...")
        await downgrade_database_indexes(engine)

        logger.info("✅ Analytics indexes removed successfully!")

    except Exception as e:
        logger.error(f"❌ Error removing indexes: {e}")
        raise

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "remove" or command == "downgrade":
            asyncio.run(remove_indexes())
        elif command == "apply" or command == "upgrade":
            asyncio.run(apply_indexes())
        else:
            print("Usage: python apply_analytics_indexes.py [apply|remove]")
            print("  apply  - Apply analytics performance indexes (default)")
            print("  remove - Remove analytics performance indexes")
    else:
        # Default action is to apply indexes
        asyncio.run(apply_indexes())

if __name__ == "__main__":
    main()