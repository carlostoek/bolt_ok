#!/usr/bin/env python3
"""
Simple test for narrative fragment unified system.
This script tests the basic functionality of the NarrativeFragment model and service
without depending on the full project structure.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool
from database.base import Base
from database.narrative_unified import NarrativeFragment

# Simple service implementation for testing
class SimpleNarrativeFragmentService:
    """Simple service for testing narrative fragments."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_fragment(self, title, content, fragment_type, choices=None, triggers=None, required_clues=None):
        """Create a new narrative fragment."""
        fragment = NarrativeFragment(
            title=title,
            content=content,
            fragment_type=fragment_type,
            choices=choices or [],
            triggers=triggers or {},
            required_clues=required_clues or []
        )
        
        self.session.add(fragment)
        await self.session.commit()
        await self.session.refresh(fragment)
        return fragment

    async def get_fragment(self, fragment_id):
        """Get a narrative fragment by ID."""
        from sqlalchemy import select
        stmt = select(NarrativeFragment).where(
            NarrativeFragment.id == fragment_id,
            NarrativeFragment.is_active == True
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

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
        service = SimpleNarrativeFragmentService(session)
        
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
        
        # Test 3: Retrieve a fragment
        print("\n3. Retrieving a fragment...")
        fragment = await service.get_fragment(story_fragment.id)
        print(f"   Retrieved: {fragment.title}")
        
    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    try:
        asyncio.run(test_narrative_fragment_system())
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)