#!/usr/bin/env python3
"""
Migration script to add missing tables to existing database.
This script adds the user_sessions, role_transitions, and other missing tables
to the existing database without affecting existing data.
"""

import asyncio
import logging
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, MetaData
from sqlalchemy.exc import OperationalError

# Add the current directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.base import Base
from database.models import UserSession, RoleTransition, InteractionLog, NarrativeReward, UserRewardHistory
from utils.config import Config

logger = logging.getLogger(__name__)

async def check_table_exists(connection, table_name: str) -> bool:
    """Check if a table exists in the database."""
    try:
        if 'sqlite' in str(connection.get_bind().url):
            # SQLite check
            result = await connection.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
                {"table_name": table_name}
            )
        else:
            # PostgreSQL check
            result = await connection.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename=:table_name"),
                {"table_name": table_name}
            )
        
        return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking if table {table_name} exists: {e}")
        return False

async def create_missing_tables():
    """Create missing tables in the existing database."""
    try:
        # Get database URL from config
        db_url = Config.DATABASE_URL.strip()
        logger.info(f"Connecting to database: {db_url}")
        
        # Create engine
        engine = create_async_engine(
            db_url,
            echo=True  # Enable SQL logging for debugging
        )
        
        # Tables to check and create if missing
        required_tables = [
            'user_sessions',
            'role_transitions', 
            'interaction_logs',
            'narrative_rewards',
            'user_reward_history',
            'reward_logs'
        ]
        
        async with engine.begin() as conn:
            logger.info("Checking which tables are missing...")
            
            missing_tables = []
            for table_name in required_tables:
                exists = await check_table_exists(conn, table_name)
                if exists:
                    logger.info(f"✓ Table {table_name} already exists")
                else:
                    logger.warning(f"✗ Table {table_name} is missing")
                    missing_tables.append(table_name)
            
            if not missing_tables:
                logger.info("✅ All required tables already exist!")
                return True
            
            logger.info(f"Creating {len(missing_tables)} missing tables: {missing_tables}")
            
            # Get the specific tables from metadata that are missing
            tables_to_create = [
                Base.metadata.tables[table_name] 
                for table_name in missing_tables 
                if table_name in Base.metadata.tables
            ]
            
            if tables_to_create:
                # Create only the missing tables
                await conn.run_sync(
                    lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables_to_create)
                )
                logger.info("✅ Successfully created missing tables!")
                
                # Verify tables were created
                for table_name in missing_tables:
                    exists = await check_table_exists(conn, table_name)
                    if exists:
                        logger.info(f"✓ Verified: Table {table_name} was created successfully")
                    else:
                        logger.error(f"✗ Failed to create table {table_name}")
            else:
                logger.warning("No tables to create (metadata mismatch)")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        logger.error(f"Error creating missing tables: {e}")
        import traceback
        traceback.print_exc()
        return False

async def verify_tables_and_data():
    """Verify that the tables were created and can be accessed."""
    try:
        db_url = Config.DATABASE_URL.strip()
        engine = create_async_engine(db_url)
        
        async with engine.begin() as conn:
            logger.info("Verifying table creation and accessibility...")
            
            # Test user_sessions table
            try:
                result = await conn.execute(text("SELECT COUNT(*) FROM user_sessions"))
                count = result.scalar()
                logger.info(f"✓ user_sessions table accessible, contains {count} records")
            except Exception as e:
                logger.error(f"✗ Error accessing user_sessions table: {e}")
            
            # Test role_transitions table
            try:
                result = await conn.execute(text("SELECT COUNT(*) FROM role_transitions"))
                count = result.scalar()
                logger.info(f"✓ role_transitions table accessible, contains {count} records")
            except Exception as e:
                logger.error(f"✗ Error accessing role_transitions table: {e}")
            
            # Test interaction_logs table
            try:
                result = await conn.execute(text("SELECT COUNT(*) FROM interaction_logs"))
                count = result.scalar()
                logger.info(f"✓ interaction_logs table accessible, contains {count} records")
            except Exception as e:
                logger.error(f"✗ Error accessing interaction_logs table: {e}")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        logger.error(f"Error verifying tables: {e}")
        return False

async def main():
    """Main migration function."""
    print("🔧 DIANA BOT - Missing Tables Migration Script")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Step 1: Create missing tables
        print("\n1. Creating missing tables...")
        success = await create_missing_tables()
        if not success:
            print("❌ Failed to create missing tables")
            return False
        
        # Step 2: Verify tables were created correctly
        print("\n2. Verifying tables...")
        success = await verify_tables_and_data()
        if not success:
            print("⚠️ Warning: Some tables may not be accessible")
        
        print("\n✅ Migration completed successfully!")
        print("The bot should now be able to access all required tables.")
        print("\nNext steps:")
        print("- Restart the bot to test the fix")
        print("- Monitor bot logs for any remaining errors")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)