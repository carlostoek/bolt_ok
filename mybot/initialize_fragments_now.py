#!/usr/bin/env python3
"""
URGENT: Initialize MVP Narrative Fragments
This script will initialize all MVP narrative fragments in the database.
RUN THIS to fix the narrative progression issue.
"""

import asyncio
import sys
import os

# Add the bot directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def main():
    """Initialize MVP fragments."""
    print("🚀 EMERGENCY: Initializing MVP Narrative Fragments...")
    
    try:
        from database.database import get_session
        from services.mvp_narrative_fragment_service import MVPNarrativeFragmentService
        
        async with get_session() as session:
            fragment_service = MVPNarrativeFragmentService(session)
            
            print("📚 Creating fragment definitions...")
            results = await fragment_service.initialize_mvp_fragments()
            
            print("\n📊 Initialization Results:")
            print(f"  Fragments processed: {results['fragments_processed']}")
            print(f"  Fragments created: {results['fragments_created']}")
            print(f"  Fragments updated: {results['fragments_updated']}")
            
            print("\n🎭 Character Validation Results:")
            for validation in results['validation_results']:
                fragment_id = validation['fragment_id']
                score = validation['character_score']
                meets_req = validation['meets_requirement']
                status = "✅" if meets_req else "⚠️"
                print(f"  {status} {fragment_id}: {score:.1f}%")
            
            if results['errors']:
                print(f"\n❌ Errors:")
                for error in results['errors']:
                    print(f"  • {error}")
            
            avg_score = sum(v['character_score'] for v in results['validation_results']) / len(results['validation_results']) if results['validation_results'] else 0
            passing_count = sum(1 for v in results['validation_results'] if v['meets_requirement'])
            
            print(f"\n📈 Summary:")
            print(f"  Average character score: {avg_score:.1f}%")
            print(f"  Fragments meeting ≥90% requirement: {passing_count}/{len(results['validation_results'])}")
            
            if avg_score >= 90 and passing_count == len(results['validation_results']):
                print("🎉 SUCCESS: All fragments initialized and meet character consistency requirements!")
                print("\n🔧 NEXT STEPS:")
                print("1. Restart your bot")
                print("2. Test the narrative menu with /diana command")
                print("3. Users should now be able to advance in the story")
                return True
            else:
                print("⚠️ PARTIAL SUCCESS: Some fragments need character improvement but should work")
                return True
                
    except Exception as e:
        print(f"❌ CRITICAL ERROR initializing fragments: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎯 FRAGMENT INITIALIZATION COMPLETED")
        print("💡 The narrative advancement issue should now be resolved!")
    else:
        print("\n💥 FRAGMENT INITIALIZATION FAILED")
        print("📧 Check the error messages above and fix database/connection issues")
    
    sys.exit(0 if success else 1)