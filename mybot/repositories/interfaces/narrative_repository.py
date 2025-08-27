"""Narrative aggregate repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from database.narrative_unified import NarrativeFragment, UserNarrativeState
from database.models import LorePiece, UserLorePiece


class INarrativeRepository(ABC):
    """Repository interface for Narrative aggregate operations."""
    
    # Narrative Fragment operations
    @abstractmethod
    async def get_fragment_by_id(self, fragment_id: str) -> Optional[NarrativeFragment]:
        """Get narrative fragment by ID."""
        pass
    
    @abstractmethod
    async def get_active_fragments(self) -> List[NarrativeFragment]:
        """Get all active narrative fragments."""
        pass
    
    @abstractmethod
    async def get_fragments_by_type(self, fragment_type: str) -> List[NarrativeFragment]:
        """Get fragments by type (STORY, DECISION, INFO)."""
        pass
    
    @abstractmethod
    async def create_fragment(self, fragment_data: Dict[str, Any]) -> NarrativeFragment:
        """Create a new narrative fragment."""
        pass
    
    @abstractmethod
    async def update_fragment(self, fragment: NarrativeFragment) -> NarrativeFragment:
        """Update existing narrative fragment."""
        pass
    
    @abstractmethod
    async def delete_fragment(self, fragment_id: str) -> bool:
        """Delete narrative fragment."""
        pass
    
    @abstractmethod
    async def search_fragments_by_content(self, query: str, limit: int = 50) -> List[NarrativeFragment]:
        """Search fragments by content."""
        pass
    
    # User Narrative State operations
    @abstractmethod
    async def get_user_narrative_state(self, user_id: int) -> Optional[UserNarrativeState]:
        """Get user's narrative state."""
        pass
    
    @abstractmethod
    async def create_user_narrative_state(self, user_id: int) -> UserNarrativeState:
        """Create user narrative state."""
        pass
    
    @abstractmethod
    async def update_user_narrative_state(self, user_state: UserNarrativeState) -> UserNarrativeState:
        """Update user narrative state."""
        pass
    
    @abstractmethod
    async def get_user_visited_fragments(self, user_id: int) -> List[str]:
        """Get list of fragment IDs visited by user."""
        pass
    
    @abstractmethod
    async def get_user_completed_fragments(self, user_id: int) -> List[str]:
        """Get list of fragment IDs completed by user."""
        pass
    
    @abstractmethod
    async def add_visited_fragment(self, user_id: int, fragment_id: str) -> bool:
        """Add fragment to user's visited list."""
        pass
    
    @abstractmethod
    async def add_completed_fragment(self, user_id: int, fragment_id: str) -> bool:
        """Add fragment to user's completed list."""
        pass
    
    # Lore Piece operations
    @abstractmethod
    async def get_lore_piece_by_code(self, code_name: str) -> Optional[LorePiece]:
        """Get lore piece by code name."""
        pass
    
    @abstractmethod
    async def get_active_lore_pieces(self) -> List[LorePiece]:
        """Get all active lore pieces."""
        pass
    
    @abstractmethod
    async def get_lore_pieces_by_category(self, category: str) -> List[LorePiece]:
        """Get lore pieces by category."""
        pass
    
    @abstractmethod
    async def create_lore_piece(self, lore_data: Dict[str, Any]) -> LorePiece:
        """Create a new lore piece."""
        pass
    
    @abstractmethod
    async def update_lore_piece(self, lore_piece: LorePiece) -> LorePiece:
        """Update existing lore piece."""
        pass
    
    @abstractmethod
    async def get_user_unlocked_lore(self, user_id: int) -> List[LorePiece]:
        """Get all lore pieces unlocked by user."""
        pass
    
    @abstractmethod
    async def unlock_lore_for_user(self, user_id: int, lore_piece_id: int) -> UserLorePiece:
        """Unlock lore piece for user."""
        pass
    
    @abstractmethod
    async def has_user_unlocked_lore(self, user_id: int, lore_piece_id: int) -> bool:
        """Check if user has unlocked specific lore piece."""
        pass
    
    # Progress tracking
    @abstractmethod
    async def get_user_progress_percentage(self, user_id: int) -> float:
        """Get user's narrative progress percentage."""
        pass
    
    @abstractmethod
    async def get_narrative_statistics(self) -> Dict[str, Any]:
        """Get overall narrative system statistics."""
        pass
    
    @abstractmethod
    async def get_fragment_access_requirements(self, fragment_id: str) -> List[str]:
        """Get required clues for accessing a fragment."""
        pass
    
    @abstractmethod
    async def can_user_access_fragment(self, user_id: int, fragment_id: str) -> bool:
        """Check if user can access specific fragment."""
        pass