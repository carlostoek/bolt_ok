#!/usr/bin/env python3
"""
Migration script to add shop_context column to user_narrative_states table
"""
import asyncio
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.setup import init_db
from sqlalchemy import text

async def add_shop_context_column():
    """Add shop_context column to user_narrative_states table"""
    session = await init_db()
    try:
        # Check if column already exists
        result = await session.execute(
            text("PRAGMA table_info(user_narrative_states)")
        )
        columns = [row[1] for row in result.fetchall()]
        
        if 'shop_context' not in columns:
            print("Adding shop_context column to user_narrative_states table...")
            await session.execute(
                text("ALTER TABLE user_narrative_states ADD COLUMN shop_context BOOLEAN DEFAULT FALSE")
            )
            await session.commit()
            print("✓ shop_context column added successfully")
        else:
            print("✓ shop_context column already exists")
            
    except Exception as e:
        print(f"✗ Error adding shop_context column: {e}")
        await session.rollback()
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(add_shop_context_column())