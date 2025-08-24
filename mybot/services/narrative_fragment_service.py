from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from database.narrative_unified import NarrativeFragment
import logging

logger = logging.getLogger(__name__)


# Simple decorator to replace safe_handler
def safe_handler(func):
    """Simple decorator to handle exceptions."""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper


class NarrativeFragmentService:
    """Service for managing unified narrative fragments."""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_fragment(
        self,
        title: str,
        content: str,
        fragment_type: str,
        choices: List[Dict[str, Any]] = None,
        triggers: Dict[str, Any] = None,
        required_clues: List[str] = None
    ) -> NarrativeFragment:
        """Create a new narrative fragment.
        
        Args:
            title: Fragment title
            content: Fragment content
            fragment_type: Type of fragment (STORY, DECISION, INFO)
            choices: List of choice dictionaries for decision points
            triggers: Dictionary of triggers for rewards/effects
            required_clues: List of clue codes required to access this fragment
            
        Returns:
            Created NarrativeFragment instance
        """
        if fragment_type not in [t[0] for t in NarrativeFragment.FRAGMENT_TYPES]:
            raise ValueError(f"Invalid fragment type: {fragment_type}")
            
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
        
        logger.info(f"Created narrative fragment: {fragment.id} - {fragment.title}")
        return fragment

    async def get_fragment(self, fragment_id: str) -> Optional[NarrativeFragment]:
        """Get a narrative fragment by ID.
        
        Args:
            fragment_id: UUID of the fragment
            
        Returns:
            NarrativeFragment instance or None if not found
        """
        stmt = select(NarrativeFragment).where(
            NarrativeFragment.id == fragment_id,
            NarrativeFragment.is_active == True
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_fragments_by_type(self, fragment_type: str) -> List[NarrativeFragment]:
        """Get all active fragments of a specific type.
        
        Args:
            fragment_type: Type of fragments to retrieve
            
        Returns:
            List of NarrativeFragment instances
        """
        if fragment_type not in [t[0] for t in NarrativeFragment.FRAGMENT_TYPES]:
            raise ValueError(f"Invalid fragment type: {fragment_type}")
            
        stmt = select(NarrativeFragment).where(
            NarrativeFragment.fragment_type == fragment_type,
            NarrativeFragment.is_active == True
        ).order_by(NarrativeFragment.created_at)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_fragment(
        self,
        fragment_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        fragment_type: Optional[str] = None,
        choices: Optional[List[Dict[str, Any]]] = None,
        triggers: Optional[Dict[str, Any]] = None,
        required_clues: Optional[List[str]] = None,
        is_active: Optional[bool] = None
    ) -> Optional[NarrativeFragment]:
        """Update an existing narrative fragment.
        
        Args:
            fragment_id: UUID of the fragment to update
            title: New title (optional)
            content: New content (optional)
            fragment_type: New type (optional)
            choices: New choices (optional)
            triggers: New triggers (optional)
            required_clues: New required clues (optional)
            is_active: New active status (optional)
            
        Returns:
            Updated NarrativeFragment instance or None if not found
        """
        fragment = await self.get_fragment(fragment_id)
        if not fragment:
            return None
            
        if title is not None:
            fragment.title = title
        if content is not None:
            fragment.content = content
        if fragment_type is not None:
            if fragment_type not in [t[0] for t in NarrativeFragment.FRAGMENT_TYPES]:
                raise ValueError(f"Invalid fragment type: {fragment_type}")
            fragment.fragment_type = fragment_type
        if choices is not None:
            fragment.choices = choices
        if triggers is not None:
            fragment.triggers = triggers
        if required_clues is not None:
            fragment.required_clues = required_clues
        if is_active is not None:
            fragment.is_active = is_active
            
        await self.session.commit()
        await self.session.refresh(fragment)
        
        logger.info(f"Updated narrative fragment: {fragment.id}")
        return fragment

    async def delete_fragment(self, fragment_id: str) -> bool:
        """Delete a narrative fragment (soft delete by setting is_active=False).
        
        Args:
            fragment_id: UUID of the fragment to delete
            
        Returns:
            True if fragment was found and "deleted", False otherwise
        """
        stmt = update(NarrativeFragment).where(
            NarrativeFragment.id == fragment_id
        ).values(is_active=False)
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Deleted narrative fragment: {fragment_id}")
        return deleted

    async def get_story_fragments(self) -> List[NarrativeFragment]:
        """Get all active story fragments.
        
        Returns:
            List of story NarrativeFragment instances
        """
        return await self.get_fragments_by_type('STORY')

    async def get_decision_fragments(self) -> List[NarrativeFragment]:
        """Get all active decision fragments.
        
        Returns:
            List of decision NarrativeFragment instances
        """
        return await self.get_fragments_by_type('DECISION')

    async def get_info_fragments(self) -> List[NarrativeFragment]:
        """Get all active info fragments.
        
        Returns:
            List of info NarrativeFragment instances
        """
        return await self.get_fragments_by_type('INFO')

    async def check_user_access(self, fragment_id: str, user_clues: List[str]) -> bool:
        """Check if a user has access to a fragment based on their clues.
        
        Args:
            fragment_id: UUID of the fragment to check
            user_clues: List of clue codes the user has
            
        Returns:
            True if user has access, False otherwise
        """
        fragment = await self.get_fragment(fragment_id)
        if not fragment:
            return False
            
        # If no required clues, user has access
        if not fragment.required_clues:
            return True
            
        # Check if user has all required clues
        return all(clue in user_clues for clue in fragment.required_clues)