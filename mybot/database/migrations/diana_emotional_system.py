"""
Diana Emotional System Migration Script

This script creates the necessary tables for Diana's emotional memory system:
1. diana_emotional_memories - Stores individual emotional interactions
2. diana_relationship_states - Tracks the current state of each user-Diana relationship
3. diana_contradictions - Records and resolves contradictory information
4. diana_personality_adaptations - Stores personalization data for Diana's interactions

The migration ensures all tables have proper indices for fast emotional queries
and integrates seamlessly with the existing user and narrative structures.
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select
from sqlalchemy.schema import CreateTable, CreateIndex

# Import the database configuration
from database.config import DATABASE_URL
from database.base import Base
from database.diana_models import (
    DianaEmotionalMemory, 
    DianaRelationshipState,
    DianaContradiction,
    DianaPersonalityAdaptation
)

logger = logging.getLogger(__name__)


async def create_diana_tables(engine):
    """Create Diana's emotional system tables if they don't exist."""
    
    async with engine.begin() as conn:
        # Check if diana_emotional_memories table exists
        result = await conn.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='diana_emotional_memories')"
        )
        diana_emotional_memories_exists = result.scalar()
        
        # Check if diana_relationship_states table exists
        result = await conn.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='diana_relationship_states')"
        )
        diana_relationship_states_exists = result.scalar()
        
        # Check if diana_contradictions table exists
        result = await conn.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='diana_contradictions')"
        )
        diana_contradictions_exists = result.scalar()
        
        # Check if diana_personality_adaptations table exists
        result = await conn.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='diana_personality_adaptations')"
        )
        diana_personality_adaptations_exists = result.scalar()
        
        # Create tables if they don't exist
        if not diana_emotional_memories_exists:
            logger.info("Creating diana_emotional_memories table...")
            await conn.execute(CreateTable(DianaEmotionalMemory.__table__))
            
            # Create indices for diana_emotional_memories
            for index in DianaEmotionalMemory.__table__.indexes:
                await conn.execute(CreateIndex(index))
                
            logger.info("diana_emotional_memories table created successfully.")
        else:
            logger.info("diana_emotional_memories table already exists.")
        
        if not diana_relationship_states_exists:
            logger.info("Creating diana_relationship_states table...")
            await conn.execute(CreateTable(DianaRelationshipState.__table__))
            logger.info("diana_relationship_states table created successfully.")
        else:
            logger.info("diana_relationship_states table already exists.")
            
        if not diana_contradictions_exists:
            logger.info("Creating diana_contradictions table...")
            await conn.execute(CreateTable(DianaContradiction.__table__))
            
            # Create indices for diana_contradictions
            for index in DianaContradiction.__table__.indexes:
                await conn.execute(CreateIndex(index))
                
            logger.info("diana_contradictions table created successfully.")
        else:
            logger.info("diana_contradictions table already exists.")
            
        if not diana_personality_adaptations_exists:
            logger.info("Creating diana_personality_adaptations table...")
            await conn.execute(CreateTable(DianaPersonalityAdaptation.__table__))
            
            # Create indices for diana_personality_adaptations
            for index in DianaPersonalityAdaptation.__table__.indexes:
                await conn.execute(CreateIndex(index))
                
            logger.info("diana_personality_adaptations table created successfully.")
        else:
            logger.info("diana_personality_adaptations table already exists.")


async def run_migration():
    """Run the migration script for Diana's emotional system tables."""
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    try:
        logger.info("Starting Diana emotional system migration...")
        await create_diana_tables(engine)
        logger.info("Diana emotional system migration completed successfully.")
    except Exception as e:
        logger.error(f"Error during Diana emotional system migration: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_migration())