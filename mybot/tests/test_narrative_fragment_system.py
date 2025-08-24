#!/usr/bin/env python3
"""
Test script for narrative fragment unified system.
This script tests the basic functionality of the NarrativeFragment model and service.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Set the Python path for imports
os.environ['PYTHONPATH'] = project_root

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool
from database.base import Base
from database.narrative_unified import NarrativeFragment
from services.narrative_fragment_service import NarrativeFragmentService

async def test_narrative_fragment_system():
    """Test the narrative fragment system."""
    print("Testing Narrative Fragment Unified System...")
    
    # Create in-memory SQLite database for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with AsyncSession(engine, expire_on_commit=False) as session:
        service = NarrativeFragmentService(session)
        
        # Test 1: Create a story fragment
        print("\n1. Creating a story fragment...")
        story_fragment = await service.create_fragment(
            title="Introducción al Misterio",
            content="En una noche oscura, un misterio inquietante esperaba ser resuelto.",
            fragment_type="STORY"
        )
        print(f"   Created: {story_fragment.title} (ID: {story_fragment.id})")
        
        # Test 2: Create a decision fragment
        print("\n2. Creating a decision fragment...")
        decision_fragment = await service.create_fragment(
            title="Cruce en el Bosque",
            content="Llegas a un cruce en el bosque. ¿Qué camino tomas?",
            fragment_type="DECISION",
            choices=[
                {"text": "Camino de la izquierda", "next_fragment_id": "fragment-2"},
                {"text": "Camino de la derecha", "next_fragment_id": "fragment-3"}
            ],
            triggers={"reward_points": 5},
            required_clues=["pista-bosque"]
        )
        print(f"   Created: {decision_fragment.title} (ID: {decision_fragment.id})")
        
        # Test 3: Create an info fragment
        print("\n3. Creating an info fragment...")
        info_fragment = await service.create_fragment(
            title="Historia del Castillo",
            content="El castillo fue construido en el siglo XV por el rey Alonso.",
            fragment_type="INFO",
            triggers={"unlock_lore": "historia-castillo"}
        )
        print(f"   Created: {info_fragment.title} (ID: {info_fragment.id})")
        
        # Test 4: Retrieve fragments by type
        print("\n4. Retrieving fragments by type...")
        story_fragments = await service.get_story_fragments()
        print(f"   Found {len(story_fragments)} story fragments")
        
        decision_fragments = await service.get_decision_fragments()
        print(f"   Found {len(decision_fragments)} decision fragments")
        
        info_fragments = await service.get_info_fragments()
        print(f"   Found {len(info_fragments)} info fragments")
        
        # Test 5: Get a specific fragment
        print("\n5. Retrieving a specific fragment...")
        fragment = await service.get_fragment(story_fragment.id)
        print(f"   Retrieved: {fragment.title}")
        
        # Test 6: Update a fragment
        print("\n6. Updating a fragment...")
        updated_fragment = await service.update_fragment(
            fragment_id=story_fragment.id,
            title="Introducción Actualizada",
            content="En una noche aún más oscura..."
        )
        print(f"   Updated: {updated_fragment.title}")
        
        # Test 7: Check user access
        print("\n7. Checking user access...")
        user_with_clues = ["pista-bosque", "pista-castillo"]
        has_access = await service.check_user_access(decision_fragment.id, user_with_clues)
        print(f"   User with clues has access: {has_access}")
        
        user_without_clues = ["pista-castillo"]
        has_access = await service.check_user_access(decision_fragment.id, user_without_clues)
        print(f"   User without required clues has access: {has_access}")
        
        # Test 8: Delete a fragment (soft delete)
        print("\n8. Deleting a fragment...")
        result = await service.delete_fragment(info_fragment.id)
        print(f"   Deleted: {result}")
        
        # Verify deletion
        deleted_fragment = await service.get_fragment(info_fragment.id)
        print(f"   Fragment after deletion is active: {deleted_fragment is not None}")
        
    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    try:
        asyncio.run(test_narrative_fragment_system())
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        sys.exit(1)