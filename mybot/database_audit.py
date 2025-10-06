#!/usr/bin/env python3
"""
Database Audit Script - Test database setup and model consistency
"""

import asyncio
import logging
import sys
import os
from typing import List, Dict, Any
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_database_initialization():
    """Test database initialization and table creation"""
    try:
        logger.info("🔍 Testing database initialization...")
        
        # Set dummy environment variable to bypass config validation
        os.environ['BOT_TOKEN'] = 'dummy_token_for_testing'
        
        from database.setup import init_db, get_session
        from database.models import User, UserStats
        from database.narrative_models import UserNarrativeState, StoryFragment, NarrativeChoice
        
        # Initialize database
        engine = await init_db()
        logger.info("✅ Database engine initialized successfully")
        
        # Get session to test connectivity
        async with await get_session() as session:
            # Test basic connection
            result = await session.execute(text("SELECT 1"))
            test_value = result.scalar()
            if test_value == 1:
                logger.info("✅ Database connection working")
            else:
                logger.error("❌ Database connection test failed")
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

async def test_table_creation():
    """Test if all tables were created correctly"""
    try:
        logger.info("🔍 Testing table creation...")
        
        from database.setup import get_session
        
        async with await get_session() as session:
            # Get table names from database using sync connection
            def get_table_names(sync_conn):
                inspector = inspect(sync_conn)
                return inspector.get_table_names()
            
            connection = await session.connection()
            tables = await connection.run_sync(get_table_names)
            
            # Expected tables based on models
            expected_tables = [
                'users', 'achievements', 'story_fragments', 'narrative_choices',
                'user_narrative_states', 'rewards', 'lore_pieces', 'missions',
                'user_rewards', 'user_achievements', 'user_mission_entries',
                'user_stats', 'trivias', 'trivia_questions', 'trivia_attempts',
                'trivia_user_answers', 'auctions', 'bids', 'auction_participants'
            ]
            
            missing_tables = [t for t in expected_tables if t not in tables]
            extra_tables = [t for t in tables if t not in expected_tables and not t.startswith('sqlite_')]
            
            logger.info(f"📊 Found {len(tables)} tables in database")
            
            if missing_tables:
                logger.warning(f"⚠️ Missing expected tables: {missing_tables}")
            else:
                logger.info("✅ All expected core tables present")
                
            if extra_tables:
                logger.info(f"📋 Additional tables found: {extra_tables}")
                
            return len(missing_tables) == 0
            
    except Exception as e:
        logger.error(f"❌ Table creation test failed: {e}")
        return False

async def test_model_relationships():
    """Test key model relationships"""
    try:
        logger.info("🔍 Testing model relationships...")
        
        from database.setup import get_session
        from database.models import User, UserStats
        from database.narrative_models import UserNarrativeState
        
        async with await get_session() as session:
            # Test User creation
            test_user = User(
                id=999999,
                username="test_user",
                first_name="Test",
                last_name="User"
            )
            session.add(test_user)
            await session.commit()
            logger.info("✅ User creation successful")
            
            # Test UserStats relationship
            user_stats = UserStats(user_id=999999)
            session.add(user_stats)
            await session.commit()
            logger.info("✅ UserStats relationship working")
            
            # Test UserNarrativeState relationship  
            narrative_state = UserNarrativeState(
                user_id=999999,
                current_fragment_key="start",
                choices_made=[]
            )
            session.add(narrative_state)
            await session.commit()
            logger.info("✅ UserNarrativeState relationship working")
            
            # Test relationship loading
            from sqlalchemy.future import select
            result = await session.execute(
                select(User).where(User.id == 999999)
            )
            user_with_relationships = result.scalar_one_or_none()
            
            if user_with_relationships:
                # Test narrative_state relationship access
                narrative = user_with_relationships.narrative_state
                logger.info("✅ User->NarrativeState relationship accessible")
            
            # Cleanup test data
            await session.execute(text("DELETE FROM user_narrative_states WHERE user_id = 999999"))
            await session.execute(text("DELETE FROM user_stats WHERE user_id = 999999"))
            await session.execute(text("DELETE FROM users WHERE id = 999999"))
            await session.commit()
            logger.info("✅ Test data cleaned up")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Model relationship test failed: {e}")
        return False

async def test_basic_crud_operations():
    """Test basic CRUD operations"""
    try:
        logger.info("🔍 Testing basic CRUD operations...")
        
        from database.setup import get_session
        from database.models import User, Achievement
        from database.narrative_models import StoryFragment, NarrativeChoice
        from sqlalchemy.future import select
        
        async with await get_session() as session:
            # CREATE - Test creating records
            test_user = User(
                id=888888,
                username="crud_test_user",
                points=100.0,
                level=1
            )
            session.add(test_user)
            
            test_achievement = Achievement(
                id="test_achievement",
                name="Test Achievement",
                condition_type="points",
                condition_value=50,
                reward_text="Test reward"
            )
            session.add(test_achievement)
            
            test_fragment = StoryFragment(
                key="test_fragment",
                text="This is a test fragment",
                character="Lucien",
                level=1
            )
            session.add(test_fragment)
            
            await session.commit()
            logger.info("✅ CREATE operations successful")
            
            # READ - Test reading records
            user_result = await session.execute(select(User).where(User.id == 888888))
            read_user = user_result.scalar_one_or_none()
            
            achievement_result = await session.execute(select(Achievement).where(Achievement.id == "test_achievement"))
            read_achievement = achievement_result.scalar_one_or_none()
            
            fragment_result = await session.execute(select(StoryFragment).where(StoryFragment.key == "test_fragment"))
            read_fragment = fragment_result.scalar_one_or_none()
            
            if read_user and read_achievement and read_fragment:
                logger.info("✅ READ operations successful")
            else:
                logger.error("❌ READ operations failed")
                return False
            
            # UPDATE - Test updating records
            read_user.points = 150.0
            read_achievement.reward_text = "Updated reward text"
            read_fragment.text = "Updated fragment text"
            
            await session.commit()
            logger.info("✅ UPDATE operations successful")
            
            # Verify updates
            updated_user_result = await session.execute(select(User).where(User.id == 888888))
            updated_user = updated_user_result.scalar_one()
            
            if updated_user.points == 150.0:
                logger.info("✅ UPDATE verification successful")
            else:
                logger.error("❌ UPDATE verification failed")
                return False
            
            # DELETE - Test deleting records
            await session.delete(read_user)
            await session.delete(read_achievement)
            await session.delete(read_fragment)
            await session.commit()
            logger.info("✅ DELETE operations successful")
            
            # Verify deletions
            deleted_user_result = await session.execute(select(User).where(User.id == 888888))
            deleted_user = deleted_user_result.scalar_one_or_none()
            
            if deleted_user is None:
                logger.info("✅ DELETE verification successful")
            else:
                logger.error("❌ DELETE verification failed")
                return False
            
            return True
            
    except Exception as e:
        logger.error(f"❌ CRUD operations test failed: {e}")
        return False

async def check_schema_consistency():
    """Check for schema consistency issues"""
    try:
        logger.info("🔍 Checking schema consistency...")
        
        from database.setup import get_session
        
        async with await get_session() as session:
            # Check for foreign key constraints using sync connection
            def get_schema_info(sync_conn):
                inspector = inspect(sync_conn)
                table_names = inspector.get_table_names()
                
                schema_info = {'tables': table_names, 'foreign_keys': {}}
                
                # Get foreign keys for key tables
                for table in ['user_narrative_states', 'narrative_choices']:
                    if table in table_names:
                        schema_info['foreign_keys'][table] = inspector.get_foreign_keys(table)
                
                return schema_info
            
            connection = await session.connection()
            schema_info = await connection.run_sync(get_schema_info)
            
            issues = []
            
            # Check user_narrative_states foreign key to users
            tables = schema_info['tables']
            if 'user_narrative_states' in tables and 'users' in tables:
                fks = schema_info['foreign_keys'].get('user_narrative_states', [])
                user_fk_found = any(fk['referred_table'] == 'users' for fk in fks)
                if not user_fk_found:
                    issues.append("Missing foreign key: user_narrative_states -> users")
            
            # Check for any circular dependencies in narrative models
            if 'story_fragments' in tables and 'narrative_choices' in tables:
                fragment_fks = schema_info['foreign_keys'].get('narrative_choices', [])
                fragment_fk_found = any(fk['referred_table'] == 'story_fragments' for fk in fragment_fks)
                if not fragment_fk_found:
                    issues.append("Missing foreign key: narrative_choices -> story_fragments")
            
            if issues:
                for issue in issues:
                    logger.warning(f"⚠️ Schema issue: {issue}")
                return False
            else:
                logger.info("✅ Schema consistency check passed")
                return True
                
    except Exception as e:
        logger.error(f"❌ Schema consistency check failed: {e}")
        return False

async def test_service_database_connectivity():
    """Test that existing services can connect to database properly"""
    try:
        logger.info("🔍 Testing service database connectivity...")
        
        from database.setup import get_session
        from services.user_service import UserService
        from services.narrative_engine import NarrativeEngine
        from services.point_service import PointService
        
        async with await get_session() as session:
            # Test UserService
            user_service = UserService(session)
            test_user = await user_service.create_user(
                777777,
                first_name="Service Test",
                username="service_test"
            )
            logger.info("✅ UserService database connectivity working")
            
            # Test PointService
            point_service = PointService(session)
            initial_points = test_user.points
            await point_service.add_points(777777, 50.0)
            await session.refresh(test_user)
            if test_user.points == initial_points + 50.0:
                logger.info("✅ PointService database connectivity working")
            else:
                logger.error("❌ PointService points not updated correctly")
                return False
            
            # Test NarrativeEngine basic functionality
            narrative_engine = NarrativeEngine(session)
            user_state = await narrative_engine._get_or_create_user_state(777777)
            if user_state:
                logger.info("✅ NarrativeEngine database connectivity working")
            else:
                logger.error("❌ NarrativeEngine failed to create user state")
                return False
            
            # Cleanup test data
            await session.execute(text("DELETE FROM user_narrative_states WHERE user_id = 777777"))
            await session.execute(text("DELETE FROM users WHERE id = 777777"))
            await session.commit()
            logger.info("✅ Service test data cleaned up")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Service database connectivity test failed: {e}")
        return False

async def generate_health_report():
    """Generate comprehensive database health report"""
    logger.info("📋 Generating Database Health Report...")
    logger.info("=" * 60)
    
    # Test results tracking
    results = {}
    
    # Test database initialization
    results['initialization'] = await test_database_initialization()
    
    # Test table creation
    results['table_creation'] = await test_table_creation()
    
    # Test model relationships
    results['model_relationships'] = await test_model_relationships()
    
    # Test CRUD operations
    results['crud_operations'] = await test_basic_crud_operations()
    
    # Check schema consistency
    results['schema_consistency'] = await check_schema_consistency()
    
    # Test service connectivity
    results['service_connectivity'] = await test_service_database_connectivity()
    
    # Summary
    logger.info("📊 DATABASE HEALTH SUMMARY")
    logger.info("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
    
    logger.info(f"\nOverall Health: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 Database is healthy and ready for use!")
        return True
    else:
        logger.warning(f"⚠️ Database has {total_tests - passed_tests} issues that need attention")
        return False

async def main():
    """Main audit function"""
    try:
        # Set dummy environment variable to bypass config validation
        os.environ['BOT_TOKEN'] = 'dummy_token_for_testing'
        
        logger.info("🚀 Starting Database Audit...")
        logger.info("=" * 60)
        
        health_status = await generate_health_report()
        
        if health_status:
            logger.info("\n✅ Database audit completed successfully - no critical issues found")
            sys.exit(0)
        else:
            logger.error("\n❌ Database audit found critical issues that need to be fixed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 Audit failed with critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())