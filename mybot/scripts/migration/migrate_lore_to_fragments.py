"""
Migration script to move all LorePiece data to StoryFragment system.
"""
import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import sessionmaker

# Import models
from database.models import LorePiece, UserLorePiece
from database.narrative_models import StoryFragment, UserNarrativeState
from database.setup import get_session_factory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_lore_to_fragments():
    """Main migration function."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            # Get all lore pieces
            lore_stmt = select(LorePiece)
            result = await session.execute(lore_stmt)
            lore_pieces = result.scalars().all()
            
            logger.info(f"Found {len(lore_pieces)} lore pieces to migrate")
            
            # Migrate each lore piece to story fragment
            for lore_piece in lore_pieces:
                # Check if fragment already exists
                existing_fragment_stmt = select(StoryFragment).where(
                    StoryFragment.key == f"lore_{lore_piece.code_name}"
                )
                existing_result = await session.execute(existing_fragment_stmt)
                existing_fragment = existing_result.scalar_one_or_none()
                
                if existing_fragment:
                    logger.info(f"Fragment for lore piece {lore_piece.code_name} already exists, updating")
                    # Update existing fragment
                    existing_fragment.text = lore_piece.content if lore_piece.content_type == "text" else f"🎁 {lore_piece.title}"
                    existing_fragment.image_url = lore_piece.content if lore_piece.content_type == "image" else None
                    # Add metadata about the original lore piece
                    if not existing_fragment.metadata:
                        existing_fragment.metadata = {}
                    existing_fragment.metadata.update({
                        "migrated_from_lore": True,
                        "original_lore_id": lore_piece.id,
                        "original_content_type": lore_piece.content_type,
                        "original_category": lore_piece.category
                    })
                else:
                    # Create new story fragment
                    fragment = StoryFragment(
                        key=f"lore_{lore_piece.code_name}",
                        text=lore_piece.content if lore_piece.content_type == "text" else f"🎁 {lore_piece.title}",
                        image_url=lore_piece.content if lore_piece.content_type == "image" else None,
                        character="Lucien",  # Default character for lore pieces
                        level=1,  # Default level
                        metadata={
                            "migrated_from_lore": True,
                            "original_lore_id": lore_piece.id,
                            "original_content_type": lore_piece.content_type,
                            "original_category": lore_piece.category,
                            "is_lore_piece": True,
                            "lore_title": lore_piece.title,
                            "lore_description": lore_piece.description
                        }
                    )
                    session.add(fragment)
                    logger.info(f"Created story fragment for lore piece: {lore_piece.code_name}")
            
            await session.commit()
            logger.info("Successfully migrated lore pieces to story fragments")
            
            # Migrate user lore pieces to user narrative state
            logger.info("Migrating user lore piece unlocks...")
            user_lore_stmt = select(UserLorePiece)
            user_lore_result = await session.execute(user_lore_stmt)
            user_lore_pieces = user_lore_result.scalars().all()
            
            migrated_count = 0
            for user_lore in user_lore_pieces:
                # Get or create user narrative state
                user_state_stmt = select(UserNarrativeState).where(
                    UserNarrativeState.user_id == user_lore.user_id
                )
                user_state_result = await session.execute(user_state_stmt)
                user_state = user_state_result.scalar_one_or_none()
                
                if not user_state:
                    user_state = UserNarrativeState(user_id=user_lore.user_id)
                    session.add(user_state)
                    await session.flush()
                
                # Add to unlocked fragments
                if not user_state.unlocked_fragments:
                    user_state.unlocked_fragments = []
                
                fragment_key = f"lore_{user_lore.lore_piece.code_name}"
                if fragment_key not in user_state.unlocked_fragments:
                    user_state.unlocked_fragments.append(fragment_key)
                    migrated_count += 1
            
            await session.commit()
            logger.info(f"Migrated {migrated_count} user lore piece unlocks")
            
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Migration failed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(migrate_lore_to_fragments())
