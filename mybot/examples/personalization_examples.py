#!/usr/bin/env python
"""
Personalization Examples - Diana Emotional Response System
---------------------------------------------------------

This script demonstrates the personalization capabilities of Diana's response system
by simulating different user interactions and showing how responses are customized
based on relationship status, emotional history, and user preferences.

Examples include:
1. New user interactions with standard responses
2. Developing relationship with increasing intimacy
3. Different relationship types and emotional contexts
4. Response customization based on reaction types
5. Memory-based personalization for long-term relationships

Usage:
    python personalization_examples.py
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

# Import necessary modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.diana_models import (
    EmotionalInteractionType,
    EmotionCategory,
    EmotionalIntensity,
    RelationshipStatus
)
from services.diana_emotional_service import DianaEmotionalService
from services.coordinador_central import CoordinadorCentral, AccionUsuario


# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Example database URL (in-memory SQLite for demonstration)
DATABASE_URL = "sqlite+aiosqlite:///:memory:"


async def setup_database():
    """Create tables and setup database for examples."""
    from database.base import Base
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    return async_session


async def create_example_users(session_factory):
    """Create example users with different relationship states."""
    diana_service = DianaEmotionalService(await session_factory())
    
    # Create users with different relationship stages
    users = {
        # New user - just starting interactions
        "new_user": {
            "id": 10001,
            "relationship": {
                "status": RelationshipStatus.INITIAL,
                "trust_level": 0.1,
                "rapport": 0.1,
                "familiarity": 0.0,
            },
            "adaptation": {
                "warmth": 0.5,
                "humor": 0.3,
                "formality": 0.7,
                "emoji_usage": 0.3,
            }
        },
        
        # Developing relationship - acquaintance stage
        "acquaintance_user": {
            "id": 10002,
            "relationship": {
                "status": RelationshipStatus.ACQUAINTANCE,
                "trust_level": 0.3,
                "rapport": 0.4,
                "familiarity": 0.3,
                "interaction_count": 12,
            },
            "adaptation": {
                "warmth": 0.6,
                "humor": 0.5,
                "formality": 0.5,
                "emoji_usage": 0.5,
            },
            "memories": [
                {
                    "interaction_type": EmotionalInteractionType.FEEDBACK,
                    "summary": "Primera reacción positiva",
                    "content": "El usuario reaccionó positivamente a una publicación",
                    "primary_emotion": EmotionCategory.JOY,
                    "intensity": EmotionalIntensity.MODERATE,
                    "importance_score": 1.2,
                }
            ]
        },
        
        # Close relationship - friendly stage with frequent interactions
        "friendly_user": {
            "id": 10003,
            "relationship": {
                "status": RelationshipStatus.FRIENDLY,
                "trust_level": 0.6,
                "rapport": 0.7,
                "familiarity": 0.6,
                "interaction_count": 35,
                "positive_interactions": 28,
                "negative_interactions": 2,
            },
            "adaptation": {
                "warmth": 0.8,
                "humor": 0.7,
                "formality": 0.3,
                "emoji_usage": 0.8,
                "emotional_expressiveness": 0.7,
            },
            "memories": [
                {
                    "interaction_type": EmotionalInteractionType.FEEDBACK,
                    "summary": "Reacción romántica repetida",
                    "content": "El usuario envía frecuentemente reacciones de corazón",
                    "primary_emotion": EmotionCategory.TRUST,
                    "intensity": EmotionalIntensity.HIGH,
                    "importance_score": 1.8,
                },
                {
                    "interaction_type": EmotionalInteractionType.PERSONAL_SHARE,
                    "summary": "Decisión narrativa íntima",
                    "content": "El usuario eligió una opción romántica en la narrativa",
                    "primary_emotion": EmotionCategory.ANTICIPATION,
                    "intensity": EmotionalIntensity.HIGH,
                    "importance_score": 2.0,
                }
            ]
        },
        
        # Intimate relationship - close/intimate with rich history
        "intimate_user": {
            "id": 10004,
            "relationship": {
                "status": RelationshipStatus.INTIMATE,
                "trust_level": 0.9,
                "rapport": 0.9,
                "familiarity": 0.8,
                "interaction_count": 120,
                "positive_interactions": 95,
                "negative_interactions": 5,
                "dominant_emotion": EmotionCategory.TRUST,
            },
            "adaptation": {
                "warmth": 0.9,
                "humor": 0.8,
                "formality": 0.2,
                "emoji_usage": 0.9,
                "emotional_expressiveness": 0.9,
                "directness": 0.8,
            },
            "memories": [
                {
                    "interaction_type": EmotionalInteractionType.CONFESSION,
                    "summary": "Confesión personal",
                    "content": "El usuario compartió detalles íntimos de su vida",
                    "primary_emotion": EmotionCategory.TRUST,
                    "intensity": EmotionalIntensity.VERY_HIGH,
                    "importance_score": 2.5,
                },
                {
                    "interaction_type": EmotionalInteractionType.FEEDBACK,
                    "summary": "Reacción apasionada",
                    "content": "El usuario reaccionó intensamente a contenido romántico",
                    "primary_emotion": EmotionCategory.JOY,
                    "secondary_emotion": EmotionCategory.ANTICIPATION,
                    "intensity": EmotionalIntensity.VERY_HIGH,
                    "importance_score": 2.2,
                },
                {
                    "interaction_type": EmotionalInteractionType.MILESTONE,
                    "summary": "Aniversario de interacción",
                    "content": "El usuario ha interactuado por 3 meses consecutivos",
                    "primary_emotion": EmotionCategory.JOY,
                    "intensity": EmotionalIntensity.HIGH,
                    "importance_score": 2.0,
                }
            ]
        }
    }
    
    # Create user states in the database
    for user_type, user_data in users.items():
        user_id = user_data["id"]
        
        # Create relationship state
        rel_data = user_data["relationship"]
        relationship = await diana_service._get_or_create_relationship_state(user_id)
        
        # Update relationship fields
        for key, value in rel_data.items():
            if hasattr(relationship, key):
                setattr(relationship, key, value)
        
        # Create personality adaptation
        adapt_data = user_data["adaptation"]
        adaptation = await diana_service._get_or_create_personality_adaptation(user_id)
        
        # Update adaptation fields
        for key, value in adapt_data.items():
            if hasattr(adaptation, key):
                setattr(adaptation, key, value)
        
        # Create memories if any
        if "memories" in user_data:
            for mem_data in user_data["memories"]:
                await diana_service.store_emotional_memory(
                    user_id=user_id,
                    interaction_type=mem_data["interaction_type"],
                    summary=mem_data["summary"],
                    content=mem_data["content"],
                    primary_emotion=mem_data["primary_emotion"],
                    secondary_emotion=mem_data.get("secondary_emotion"),
                    intensity=mem_data.get("intensity", EmotionalIntensity.MODERATE),
                    importance_score=mem_data.get("importance_score", 1.0),
                    context_data=mem_data.get("context_data", {})
                )
    
    return users


async def simulate_reactions(session_factory, users):
    """Simulate different reaction scenarios and show personalized responses."""
    
    reaction_types = ["👍", "❤️", "😂", "😮", "like", "love"]
    
    print("\n" + "="*80)
    print("DIANA PERSONALIZATION EXAMPLES: REACTIONS")
    print("="*80)
    
    async with session_factory() as session:
        coordinador = CoordinadorCentral(session)
        
        for user_type, user_data in users.items():
            user_id = user_data["id"]
            
            print(f"\n--- User Type: {user_type.upper()} (ID: {user_id}) ---")
            
            for reaction_type in reaction_types[:3]:  # Use first 3 reactions for brevity
                # Create a basic result that would come from a reaction
                base_result = {
                    "success": True,
                    "message": f"Diana sonríe al notar tu reacción... *+10 besitos* 💋 han sido añadidos a tu cuenta.",
                    "points_awarded": 10,
                    "total_points": 100,
                    "action": "reaction_success"
                }
                
                # Add a hint to every third message to test hint handling
                if reaction_types.index(reaction_type) % 3 == 0:
                    hint = "El jardín de los secretos esconde más de lo que revela a simple vista..."
                    base_result["message"] = f"{base_result['message']}\n\n*Nueva pista desbloqueada:* _{hint}_"
                    base_result["hint_unlocked"] = hint
                
                # Enhance the message using Diana's system
                enhanced_result = await coordinador.enhance_with_diana(
                    user_id, 
                    base_result, 
                    reaction_type=reaction_type
                )
                
                # Display the personalized result
                print(f"\nReaction: {reaction_type}")
                print(f"Standard message: {base_result['message']}")
                print(f"Personalized: {enhanced_result['message']}")
                print("-" * 50)


async def main():
    """Run the example demonstrations."""
    try:
        # Setup the database and create session factory
        session_factory = await setup_database()
        
        # Create example users with different relationship states
        users = await create_example_users(session_factory)
        
        # Simulate reaction scenarios
        await simulate_reactions(session_factory, users)
        
        print("\nAll examples completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in example: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())