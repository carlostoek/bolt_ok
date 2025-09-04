#!/usr/bin/env python3
"""
Initialize MVP Narrative Fragments Script
Simple script to initialize all Level 1-3 fragments in the database.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.base import create_async_session
from services.mvp_narrative_fragment_service import MVPNarrativeFragmentService

async def main():
    """Initialize MVP fragments."""
    print("🚀 Initializing MVP Narrative Fragments...")
    
    try:
        async with create_async_session() as session:
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
                print("🎉 All fragments meet character consistency requirements!")
                return True
            else:
                print("⚠️ Some fragments need character improvement")
                return False
                
    except Exception as e:
        print(f"❌ Error initializing fragments: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)