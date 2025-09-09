#!/usr/bin/env python3
"""
Test script to verify narrative system fixes work.
This tests basic fragment retrieval and user progress tracking.
"""

import asyncio
import sys
import os

# Add the bot directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_narrative_fixes():
    """Test that narrative system basic functionality works."""
    print("🔧 TESTING NARRATIVE SYSTEM FIXES...")
    
    try:
        from database.setup import init_db, get_session
        from services.mvp_narrative_fragment_service import MVPNarrativeFragmentService
        
        # Initialize database
        await init_db()
        
        # Test 1: Fragment Service Creation
        print("\n1. Testing Fragment Service Creation...")
        session = await get_session()
        try:
            fragment_service = MVPNarrativeFragmentService(session)
            print("✅ Fragment service created successfully")
            
            # Test 2: Fragment Retrieval
            print("\n2. Testing Fragment Retrieval...")
            fragment = await fragment_service._get_fragment_cached('diana_l1_f1_umbral')
            if fragment:
                print(f"✅ Fragment retrieved: {fragment.title}")
                print(f"   Type: {fragment.fragment_type}")
                print(f"   Level: {fragment.storyline_level}")
            else:
                print("❌ Fragment not found")
                return False
            
            # Test 3: User Current Fragment
            print("\n3. Testing User Current Fragment...")
            test_user_id = 123456789
            current_fragment = await fragment_service.get_user_current_fragment(test_user_id)
            if current_fragment:
                print(f"✅ User current fragment: {current_fragment.title}")
            else:
                print("❌ No current fragment for user")
                return False
                
            # Test 4: User Progress Summary
            print("\n4. Testing User Progress Summary...")
            progress = await fragment_service.get_user_progress_summary(test_user_id)
            print(f"✅ Progress summary:")
            print(f"   Level: {progress['current_level']}")
            print(f"   Tier: {progress['current_tier']}")
            print(f"   Progress: {progress['progress_percentage']:.1f}%")
            
            # Test 5: User State Creation
            print("\n5. Testing Database Tables...")
            user_state = await fragment_service._get_or_create_user_state(test_user_id)
            mission_progress = await fragment_service._get_or_create_mission_progress(test_user_id)
            print(f"✅ User state created - Level {user_state.current_level}")
            print(f"✅ Mission progress created - Level {mission_progress.current_level}")
            
            return True
            
        finally:
            await session.close()
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_narrative_fixes())
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Database schema is fixed")
        print("✅ Fragment retrieval works")
        print("✅ User progress tracking works") 
        print("✅ Narrative system is ready for use")
        print("\n💡 You can now test /narrative command in your bot!")
    else:
        print("\n💥 SOME TESTS FAILED")
        print("📧 Check the error messages above")
    
    sys.exit(0 if success else 1)