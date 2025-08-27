"""SQLAlchemy implementation of Narrative repository."""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, text
from sqlalchemy.orm import selectinload

from database.narrative_unified import NarrativeFragment, UserNarrativeState
from database.models import LorePiece, UserLorePiece
from ..interfaces.narrative_repository import INarrativeRepository
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SqlNarrativeRepository(BaseRepository[NarrativeFragment], INarrativeRepository):
    """SQLAlchemy implementation of Narrative repository with query optimization."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, NarrativeFragment)
    
    # Narrative Fragment operations with optimized queries
    async def get_fragment_by_id(self, fragment_id: str) -> Optional[NarrativeFragment]:
        """Get narrative fragment by ID with efficient lookup."""
        return await self.session.get(NarrativeFragment, fragment_id)
    
    async def get_active_fragments(self) -> List[NarrativeFragment]:
        """Get all active narrative fragments with caching."""
        stmt = (
            select(NarrativeFragment)
            .where(NarrativeFragment.is_active == True)
            .order_by(NarrativeFragment.created_at)
        )
        return await self._execute_query(stmt, use_cache=True)
    
    async def get_fragments_by_type(self, fragment_type: str) -> List[NarrativeFragment]:
        """Get fragments by type with efficient filtering."""
        stmt = (
            select(NarrativeFragment)
            .where(
                and_(
                    NarrativeFragment.fragment_type == fragment_type,
                    NarrativeFragment.is_active == True
                )
            )
            .order_by(NarrativeFragment.created_at)
        )
        return await self._execute_query(stmt, use_cache=True)
    
    async def create_fragment(self, fragment_data: Dict[str, Any]) -> NarrativeFragment:
        """Create a new narrative fragment."""
        fragment = NarrativeFragment(**fragment_data)
        return await super().create(fragment)
    
    async def update_fragment(self, fragment: NarrativeFragment) -> NarrativeFragment:
        """Update existing narrative fragment."""
        self._clear_cache()  # Clear cache since fragment data changed
        return await super().update(fragment)
    
    async def delete_fragment(self, fragment_id: str) -> bool:
        """Delete narrative fragment (soft delete by marking inactive)."""
        fragment = await self.get_fragment_by_id(fragment_id)
        if fragment:
            fragment.is_active = False
            await self.update_fragment(fragment)
            return True
        return False
    
    async def search_fragments_by_content(self, query: str, limit: int = 50) -> List[NarrativeFragment]:
        """Search fragments by content with full-text search."""
        return await self.search(
            query=query,
            search_fields=['title', 'content'],
            limit=limit
        )
    
    # User Narrative State operations with optimized queries
    async def get_user_narrative_state(self, user_id: int) -> Optional[UserNarrativeState]:
        """Get user's narrative state with efficient lookup."""
        return await self.session.get(UserNarrativeState, user_id)
    
    async def create_user_narrative_state(self, user_id: int) -> UserNarrativeState:
        """Create user narrative state."""
        user_state = UserNarrativeState(
            user_id=user_id,
            visited_fragments=[],
            completed_fragments=[],
            unlocked_clues=[]
        )
        self.session.add(user_state)
        await self.session.commit()
        await self.session.refresh(user_state)
        return user_state
    
    async def update_user_narrative_state(self, user_state: UserNarrativeState) -> UserNarrativeState:
        """Update user narrative state."""
        await self.session.commit()
        await self.session.refresh(user_state)
        return user_state
    
    async def get_user_visited_fragments(self, user_id: int) -> List[str]:
        """Get list of fragment IDs visited by user."""
        user_state = await self.get_user_narrative_state(user_id)
        return user_state.visited_fragments if user_state else []
    
    async def get_user_completed_fragments(self, user_id: int) -> List[str]:
        """Get list of fragment IDs completed by user."""
        user_state = await self.get_user_narrative_state(user_id)
        return user_state.completed_fragments if user_state else []
    
    async def add_visited_fragment(self, user_id: int, fragment_id: str) -> bool:
        """Add fragment to user's visited list."""
        user_state = await self.get_user_narrative_state(user_id)
        if not user_state:
            user_state = await self.create_user_narrative_state(user_id)
        
        if fragment_id not in user_state.visited_fragments:
            user_state.visited_fragments.append(fragment_id)
            await self.update_user_narrative_state(user_state)
            return True
        return False
    
    async def add_completed_fragment(self, user_id: int, fragment_id: str) -> bool:
        """Add fragment to user's completed list."""
        user_state = await self.get_user_narrative_state(user_id)
        if not user_state:
            user_state = await self.create_user_narrative_state(user_id)
        
        if fragment_id not in user_state.completed_fragments:
            user_state.completed_fragments.append(fragment_id)
            # Also add to visited if not already there
            if fragment_id not in user_state.visited_fragments:
                user_state.visited_fragments.append(fragment_id)
            await self.update_user_narrative_state(user_state)
            return True
        return False
    
    # Lore Piece operations with optimized queries
    async def get_lore_piece_by_code(self, code_name: str) -> Optional[LorePiece]:
        """Get lore piece by code name with efficient lookup."""
        stmt = select(LorePiece).where(LorePiece.code_name == code_name)
        return await self._execute_query(stmt, single=True)
    
    async def get_active_lore_pieces(self) -> List[LorePiece]:
        """Get all active lore pieces with caching."""
        stmt = (
            select(LorePiece)
            .where(LorePiece.is_active == True)
            .order_by(LorePiece.created_at)
        )
        return await self._execute_query(stmt, use_cache=True)
    
    async def get_lore_pieces_by_category(self, category: str) -> List[LorePiece]:
        """Get lore pieces by category."""
        stmt = (
            select(LorePiece)
            .where(
                and_(
                    LorePiece.category == category,
                    LorePiece.is_active == True
                )
            )
            .order_by(LorePiece.created_at)
        )
        return await self._execute_query(stmt)
    
    async def create_lore_piece(self, lore_data: Dict[str, Any]) -> LorePiece:
        """Create a new lore piece."""
        lore_piece = LorePiece(**lore_data)
        self.session.add(lore_piece)
        await self.session.commit()
        await self.session.refresh(lore_piece)
        self._clear_cache()
        return lore_piece
    
    async def update_lore_piece(self, lore_piece: LorePiece) -> LorePiece:
        """Update existing lore piece."""
        await self.session.commit()
        await self.session.refresh(lore_piece)
        self._clear_cache()
        return lore_piece
    
    async def get_user_unlocked_lore(self, user_id: int) -> List[LorePiece]:
        """Get all lore pieces unlocked by user with optimized join."""
        stmt = (
            select(LorePiece)
            .join(UserLorePiece)
            .where(UserLorePiece.user_id == user_id)
            .order_by(UserLorePiece.unlocked_at.desc())
        )
        return await self._execute_query(stmt)
    
    async def unlock_lore_for_user(self, user_id: int, lore_piece_id: int) -> UserLorePiece:
        """Unlock lore piece for user with duplicate prevention."""
        # Check if already unlocked
        existing = await self.session.get(UserLorePiece, (user_id, lore_piece_id))
        if existing:
            return existing
        
        user_lore = UserLorePiece(user_id=user_id, lore_piece_id=lore_piece_id)
        self.session.add(user_lore)
        await self.session.commit()
        await self.session.refresh(user_lore)
        return user_lore
    
    async def has_user_unlocked_lore(self, user_id: int, lore_piece_id: int) -> bool:
        """Check if user has unlocked specific lore piece."""
        return await self.session.get(UserLorePiece, (user_id, lore_piece_id)) is not None
    
    # Progress tracking with advanced analytics
    async def get_user_progress_percentage(self, user_id: int) -> float:
        """Get user's narrative progress percentage."""
        user_state = await self.get_user_narrative_state(user_id)
        if not user_state:
            return 0.0
        
        total_fragments = await self.count_with_conditions(is_active=True)
        if total_fragments == 0:
            return 0.0
        
        completed_count = len(user_state.completed_fragments)
        return (completed_count / total_fragments) * 100
    
    async def get_narrative_statistics(self) -> Dict[str, Any]:
        """Get overall narrative system statistics."""
        # Use optimized queries for statistics
        total_fragments = await self.count_with_conditions(is_active=True)
        
        fragment_types_query = text("""
            SELECT fragment_type, COUNT(*) 
            FROM narrative_fragments_unified 
            WHERE is_active = true 
            GROUP BY fragment_type
        """)
        fragment_types_result = await self.session.execute(fragment_types_query)
        fragment_types = dict(fragment_types_result.fetchall())
        
        user_progress_query = text("""
            SELECT 
                COUNT(DISTINCT user_id) as total_users,
                AVG(CAST(json_array_length(CAST(completed_fragments AS TEXT)) AS FLOAT)) as avg_completed
            FROM user_narrative_states_unified
        """)
        user_progress_result = await self.session.execute(user_progress_query)
        user_progress = user_progress_result.fetchone()
        
        lore_stats_query = text("""
            SELECT 
                COUNT(*) as total_lore,
                COUNT(DISTINCT category) as categories
            FROM lore_pieces 
            WHERE is_active = true
        """)
        lore_stats_result = await self.session.execute(lore_stats_query)
        lore_stats = lore_stats_result.fetchone()
        
        return {
            "total_fragments": total_fragments,
            "fragment_types": fragment_types,
            "total_users_with_progress": user_progress[0] if user_progress else 0,
            "average_completed_fragments": float(user_progress[1]) if user_progress and user_progress[1] else 0.0,
            "total_lore_pieces": lore_stats[0] if lore_stats else 0,
            "lore_categories": lore_stats[1] if lore_stats else 0
        }
    
    async def get_fragment_access_requirements(self, fragment_id: str) -> List[str]:
        """Get required clues for accessing a fragment."""
        fragment = await self.get_fragment_by_id(fragment_id)
        return fragment.required_clues if fragment else []
    
    async def can_user_access_fragment(self, user_id: int, fragment_id: str) -> bool:
        """Check if user can access specific fragment."""
        fragment = await self.get_fragment_by_id(fragment_id)
        if not fragment or not fragment.is_active:
            return False
        
        # Check if fragment has clue requirements
        if not fragment.required_clues:
            return True  # No requirements, access granted
        
        # Get user's unlocked clues
        user_state = await self.get_user_narrative_state(user_id)
        if not user_state:
            return False
        
        user_clues = set(user_state.unlocked_clues)
        required_clues = set(fragment.required_clues)
        
        # Check if user has all required clues
        return required_clues.issubset(user_clues)
    
    # Advanced narrative analytics
    async def get_fragment_popularity_stats(self) -> List[Dict[str, Any]]:
        """Get fragment popularity statistics."""
        query = text("""
            WITH fragment_visits AS (
                SELECT 
                    fragment_id,
                    COUNT(*) as visit_count
                FROM (
                    SELECT user_id, json_array_elements_text(CAST(visited_fragments AS JSON)) as fragment_id
                    FROM user_narrative_states_unified
                ) as visits
                GROUP BY fragment_id
            )
            SELECT 
                nf.id,
                nf.title,
                nf.fragment_type,
                COALESCE(fv.visit_count, 0) as visit_count
            FROM narrative_fragments_unified nf
            LEFT JOIN fragment_visits fv ON nf.id = fv.fragment_id
            WHERE nf.is_active = true
            ORDER BY visit_count DESC
            LIMIT 50
        """)
        
        result = await self.session.execute(query)
        return [
            {
                "fragment_id": row[0],
                "title": row[1],
                "fragment_type": row[2],
                "visit_count": row[3]
            }
            for row in result.fetchall()
        ]
    
    async def get_user_narrative_journey(self, user_id: int) -> Dict[str, Any]:
        """Get user's complete narrative journey with analytics."""
        user_state = await self.get_user_narrative_state(user_id)
        if not user_state:
            return {"user_id": user_id, "journey": [], "stats": {}}
        
        # Get fragment details for visited fragments
        if user_state.visited_fragments:
            stmt = (
                select(NarrativeFragment)
                .where(NarrativeFragment.id.in_(user_state.visited_fragments))
            )
            visited_fragments = await self._execute_query(stmt)
            fragment_map = {f.id: f for f in visited_fragments}
        else:
            fragment_map = {}
        
        # Build journey timeline
        journey = []
        for fragment_id in user_state.visited_fragments:
            fragment = fragment_map.get(fragment_id)
            if fragment:
                journey.append({
                    "fragment_id": fragment_id,
                    "title": fragment.title,
                    "fragment_type": fragment.fragment_type,
                    "completed": fragment_id in user_state.completed_fragments
                })
        
        # Calculate stats
        progress_percentage = await self.get_user_progress_percentage(user_id)
        unlocked_lore = await self.get_user_unlocked_lore(user_id)
        
        return {
            "user_id": user_id,
            "current_fragment": user_state.current_fragment_id,
            "journey": journey,
            "stats": {
                "fragments_visited": len(user_state.visited_fragments),
                "fragments_completed": len(user_state.completed_fragments),
                "progress_percentage": progress_percentage,
                "unlocked_clues": len(user_state.unlocked_clues),
                "unlocked_lore_count": len(unlocked_lore)
            }
        }