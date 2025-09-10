#!/usr/bin/env python3
"""
Test Collaborative Character System
Tests the 70% Lucien, 30% Diana collaborative presentation model
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from services.mvp_narrative_fragment_service import MVPNarrativeFragmentService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_collaborative_characters():
    """Test collaborative character validation and presentation."""
    
    # Create in-memory SQLite for testing
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    # Create session factory
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session_factory() as session:
        try:
            # Initialize narrative service
            narrative_service = MVPNarrativeFragmentService(session)
            
            print("🎭 Testing Collaborative Character System")
            print("=" * 50)
            
            # Test fragment initialization with collaborative validation
            print("\n1. Testing Fragment Initialization...")
            result = await narrative_service.initialize_mvp_fragments()
            
            print(f"✅ Fragments processed: {result['fragments_processed']}")
            print(f"✅ Fragments created: {result['fragments_created']}")
            print(f"✅ Fragments updated: {result['fragments_updated']}")
            
            # Test validation results
            print("\n2. Testing Character Validation Results...")
            for validation in result['validation_results']:
                fragment_id = validation['fragment_id']
                score = validation['character_score']
                meets_req = validation['meets_requirement']
                
                status = "✅ PASS" if meets_req else "❌ FAIL"
                print(f"{status} {fragment_id}: {score:.1f}")
            
            # Test collaborative dialogue extraction
            print("\n3. Testing Dialogue Extraction...")
            test_content = '''🎭 **Lucien aparece con elegante compostura...**

*Permíteme presentarme. Soy Lucien, y antes de que pueda comprender lo que busca aquí, necesito evaluarlo apropiadamente.*

Diana encuentra particular interés en quienes demuestran capacidad para la autenticidad verdadera.

💫 **Holis hermoso... Lucien me dijo algo interesante sobre ti...**

*Me acomodo junto a Lucien, con una sonrisa auténtica* 

Dice que tienes algo diferente. ¿Es cierto?

*Intercambio una mirada cómplice con Lucien*

**¿Verdad, Lucien? Este parece tener... potencial.**'''
            
            diana_dialogue = narrative_service._extract_diana_dialogue(test_content)
            lucien_dialogue = narrative_service._extract_lucien_dialogue(test_content)
            
            print(f"✅ Diana dialogue extracted: {len(diana_dialogue)} characters")
            print(f"✅ Lucien dialogue extracted: {len(lucien_dialogue)} characters")
            
            print("\nDiana Dialogue:")
            print(diana_dialogue[:100] + "..." if len(diana_dialogue) > 100 else diana_dialogue)
            
            print("\nLucien Dialogue:")
            print(lucien_dialogue[:100] + "..." if len(lucien_dialogue) > 100 else lucien_dialogue)
            
            # Test collaboration authenticity validation
            print("\n4. Testing Collaboration Authenticity...")
            
            character_presentation = {
                'lucien_percentage': 70,
                'diana_percentage': 30,
                'collaboration_type': 'evaluation_and_curiosity'
            }
            
            collab_result = await narrative_service._validate_collaborative_characters(
                test_content, 
                character_presentation, 
                "test_fragment"
            )
            
            print(f"✅ Overall Score: {collab_result['overall_score']:.1f}")
            print(f"✅ Diana Score: {collab_result['diana_score']:.1f}")
            print(f"✅ Lucien Score: {collab_result['lucien_score']:.1f}")
            print(f"✅ Collaboration Score: {collab_result['collaboration_score']:.1f}")
            print(f"✅ Meets Requirement: {collab_result['meets_requirement']}")
            
            # Test character progression tracking
            print("\n5. Testing Character Progression...")
            fragments = narrative_service._get_mvp_fragment_definitions()
            
            level_1_fragments = [f for f in fragments if f['storyline_level'] == 1]
            
            for fragment in level_1_fragments:
                presentation = fragment.get('character_presentation', {})
                if presentation:
                    lucien_pct = presentation.get('lucien_percentage', 0)
                    diana_pct = presentation.get('diana_percentage', 0)
                    collab_type = presentation.get('collaboration_type', 'unknown')
                    
                    print(f"Fragment {fragment['id']}:")
                    print(f"  - Lucien: {lucien_pct}%, Diana: {diana_pct}%")
                    print(f"  - Type: {collab_type}")
            
            print("\n🎉 Collaborative Character System Test Complete!")
            print("=" * 50)
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(test_collaborative_characters())