"""
Narrative Loader Compatibility Wrapper
Provides a temporary wrapper to ensure system startup while migration is ongoing.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class NarrativeLoader:
    """
    Compatibility wrapper for narrative loader during migration.
    
    This allows the system to start while we complete the migration to unified models.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        logger.info("NarrativeLoader compatibility wrapper initialized")
    
    async def load_fragments_from_directory(self, directory_path: str = "mybot/narrative_fragments"):
        """Compatibility method - temporarily disabled during migration."""
        logger.warning(f"Narrative loading temporarily disabled during migration. Directory: {directory_path}")
        return 0
    
    async def load_fragment_from_file(self, filepath: str):
        """Compatibility method - temporarily disabled during migration."""
        logger.warning(f"Fragment loading temporarily disabled during migration. File: {filepath}")
        return None
    
    async def fragment_exists(self, fragment_key: str) -> bool:
        """Check if fragment exists - compatibility implementation."""
        from database.narrative_unified import NarrativeFragment
        from sqlalchemy import select
        
        try:
            stmt = select(NarrativeFragment).where(NarrativeFragment.title == fragment_key)
            result = await self.session.execute(stmt)
            fragment = result.scalar_one_or_none()
            return fragment is not None
        except Exception as e:
            logger.error(f"Error checking fragment existence: {e}")
            return False
    
    async def get_fragment_count(self) -> int:
        """Get total fragment count - compatibility implementation."""
        from database.narrative_unified import NarrativeFragment
        from sqlalchemy import select, func
        
        try:
            stmt = select(func.count(NarrativeFragment.id))
            result = await self.session.execute(stmt)
            count = result.scalar()
            return count or 0
        except Exception as e:
            logger.error(f"Error getting fragment count: {e}")
            return 0