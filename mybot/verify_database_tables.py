#!/usr/bin/env python3
"""
Quick verification script to test the newly created database tables.
This verifies that the bot can interact with the unified tables without errors.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import sqlite3
from pathlib import Path

def verify_tables_sync():
    """Verify the database tables and their structure."""
    
    db_path = 'telegram_bot.db'
    if not Path(db_path).exists():
        print(f"❌ Database file {db_path} not found")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Verifying database tables structure...")
        
        # Check the unified tables
        unified_tables = [
            'user_mission_progress_unified',
            'user_archetypes_unified',
            'user_narrative_states_unified',
            'narrative_fragments_unified'
        ]
        
        for table in unified_tables:
            # Check if table exists and get column info
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            if columns:
                print(f"✅ Table {table}:")
                print(f"   - {len(columns)} columns")
                
                # Show key columns
                key_columns = [col[1] for col in columns[:5]]  # First 5 columns
                print(f"   - Key columns: {', '.join(key_columns)}...")
                
                # Check if we can perform basic operations
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   - Current records: {count}")
                    
                    # Test insert and delete (without committing)
                    if table == 'user_mission_progress_unified':
                        cursor.execute(f"""
                            INSERT INTO {table} (user_id, current_level, current_tier) 
                            VALUES (999999, 1, 'los_kinkys')
                        """)
                        cursor.execute(f"DELETE FROM {table} WHERE user_id = 999999")
                        print(f"   - ✅ Insert/Delete operations work")
                        
                    elif table == 'user_archetypes_unified':
                        cursor.execute(f"""
                            INSERT INTO {table} (user_id, explorer_score, dominant_archetype) 
                            VALUES (999999, 50, 'explorer')
                        """)
                        cursor.execute(f"DELETE FROM {table} WHERE user_id = 999999")
                        print(f"   - ✅ Insert/Delete operations work")
                        
                except Exception as e:
                    print(f"   - ⚠️ Operation test failed: {e}")
                    
            else:
                print(f"❌ Table {table} not found or has no columns")
        
        # Test some common queries that the bot might use
        print("\n🧪 Testing common bot queries...")
        
        # Test query patterns from the error logs
        test_queries = [
            ("SELECT current_level FROM user_mission_progress_unified WHERE user_id = 123", "Mission progress query"),
            ("SELECT dominant_archetype FROM user_archetypes_unified WHERE user_id = 123", "Archetype query"),
            ("SELECT current_fragment_id FROM user_narrative_states_unified WHERE user_id = 123", "Narrative state query"),
            ("SELECT COUNT(*) FROM narrative_fragments_unified WHERE is_active = 1", "Active fragments count")
        ]
        
        for query, description in test_queries:
            try:
                cursor.execute(query)
                result = cursor.fetchall()
                print(f"✅ {description}: Query executed successfully (found {len(result)} results)")
            except Exception as e:
                print(f"❌ {description}: Query failed - {e}")
        
        # Check indexes
        print("\n📊 Checking indexes...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE '%unified%'")
        indexes = cursor.fetchall()
        print(f"✅ Found {len(indexes)} unified table indexes")
        for idx in indexes:
            print(f"   - {idx[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

async def verify_sqlalchemy_integration():
    """Test SQLAlchemy integration with the new tables."""
    print("\n🔧 Testing SQLAlchemy integration...")
    
    try:
        # Import the models to see if they can be loaded
        from database.narrative_unified import (
            UserMissionProgress, 
            UserArchetype, 
            UserNarrativeState, 
            NarrativeFragment
        )
        print("✅ SQLAlchemy models imported successfully")
        
        # Try to create engine and connect
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        
        engine = create_async_engine('sqlite+aiosqlite:///./telegram_bot.db')
        session_factory = async_sessionmaker(engine, class_=AsyncSession)
        
        async with session_factory() as session:
            # Test basic queries
            from sqlalchemy import select, text
            
            # Test table access through SQLAlchemy
            result = await session.execute(text("SELECT COUNT(*) FROM user_mission_progress_unified"))
            count = result.scalar()
            print(f"✅ SQLAlchemy query successful: user_mission_progress_unified has {count} records")
            
            result = await session.execute(text("SELECT COUNT(*) FROM user_archetypes_unified"))
            count = result.scalar()
            print(f"✅ SQLAlchemy query successful: user_archetypes_unified has {count} records")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ SQLAlchemy integration test failed: {e}")
        return False

async def main():
    """Main verification function."""
    print("🚀 Database Tables Verification")
    print("=" * 50)
    
    # Sync verification
    sync_success = verify_tables_sync()
    
    # Async verification
    async_success = await verify_sqlalchemy_integration()
    
    print("\n" + "=" * 50)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 50)
    print(f"Database Structure: {'✅ PASS' if sync_success else '❌ FAIL'}")
    print(f"SQLAlchemy Integration: {'✅ PASS' if async_success else '❌ FAIL'}")
    
    overall_success = sync_success and async_success
    print(f"\nOverall Status: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 The database is ready for the unified narrative system!")
    else:
        print("\n⚠️ Some issues were found. Check the output above for details.")
    
    return overall_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)