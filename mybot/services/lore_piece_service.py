from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import LorePiece

class LorePieceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Optional Cinema System Integration
        self.cinema_master = None
        try:
            from .cinema_master_integration import get_cinema_master_integration
            self.cinema_master = get_cinema_master_integration(session)
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Cinema Master Integration available for LorePieceService")
        except ImportError:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Cinema Master Integration not available for LorePieceService")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to initialize Cinema Master Integration: {e}")

    async def code_exists(self, code_name: str) -> bool:
        stmt = select(LorePiece).where(LorePiece.code_name == code_name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_lore_piece(
        self,
        code_name: str,
        title: str,
        content_type: str,
        content: str,
        *,
        description: str | None = None,
        category: str | None = None,
        is_main_story: bool = False,
    ) -> LorePiece:
        piece = LorePiece(
            code_name=code_name,
            title=title,
            description=description,
            content_type=content_type,
            content=content,
            category=category,
            is_main_story=is_main_story,
        )
        self.session.add(piece)
        await self.session.commit()
        await self.session.refresh(piece)
        return piece

    async def get_lore_piece_by_code(self, code_name: str) -> LorePiece | None:
        stmt = select(LorePiece).where(LorePiece.code_name == code_name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_lore_piece(
        self,
        code_name: str,
        *,
        title: str | None = None,
        description: str | None = None,
        category: str | None = None,
        is_main_story: bool | None = None,
        content_type: str | None = None,
        content: str | None = None,
    ) -> bool:
        piece = await self.get_lore_piece_by_code(code_name)
        if not piece:
            return False
        if title is not None:
            piece.title = title
        if description is not None:
            piece.description = description
        if category is not None:
            piece.category = category
        if is_main_story is not None:
            piece.is_main_story = is_main_story
        if content_type is not None:
            piece.content_type = content_type
        if content is not None:
            piece.content = content
        await self.session.commit()
        return True

    async def delete_lore_piece(self, code_name: str) -> bool:
        piece = await self.get_lore_piece_by_code(code_name)
        if not piece:
            return False
        await self.session.delete(piece)
        await self.session.commit()
        return True

    async def toggle_piece_status(self, code_name: str, status: bool) -> bool:
        piece = await self.get_lore_piece_by_code(code_name)
        if piece:
            piece.is_active = status
            await self.session.commit()
            return True
        return False

    # ==================== CINEMA ENHANCED METHODS ====================
    
    async def get_lore_piece_with_treasure_hunting(self, code_name: str, user_id: int, **kwargs) -> Dict[str, Any]:
        """
        Enhanced lore piece retrieval with treasure hunting cinema integration.
        Falls back to standard functionality if cinema systems unavailable.
        
        Args:
            code_name: Lore piece code name
            user_id: User ID for personalization
            **kwargs: Additional parameters for treasure hunting enhancement
            
        Returns:
            Enhanced lore piece data with treasure hunting experience if available
        """
        import logging
        from typing import Dict, Any
        logger = logging.getLogger(__name__)
        
        try:
            # Get standard lore piece
            standard_piece = await self.get_lore_piece_by_code(code_name)
            
            result = {
                "lore_piece": standard_piece,
                "enhanced": False,
                "treasure_hunting_applied": False
            }
            
            if not standard_piece:
                return result
            
            # Try treasure hunting enhancement
            if (self.cinema_master and 
                self.cinema_master.is_treasure_hunting_available()):
                
                try:
                    treasure_hunting = getattr(self.cinema_master, 'treasure_hunting', None)
                    if treasure_hunting and hasattr(treasure_hunting, 'enhance_lore_piece_discovery'):
                        treasure_enhancement = await treasure_hunting.enhance_lore_piece_discovery(
                            user_id, code_name, standard_piece, **kwargs
                        )
                        if treasure_enhancement:
                            result.update({
                                "treasure_enhancement": treasure_enhancement,
                                "treasure_hunting_applied": True,
                                "enhanced": True,
                                "enhancement_type": "treasure_hunting"
                            })
                except Exception as e:
                    logger.warning(f"Treasure hunting enhancement failed for lore piece {code_name}: {e}")
            
            return result
            
        except Exception as e:
            logger.exception(f"Error in get_lore_piece_with_treasure_hunting for {code_name}: {e}")
            # Fallback to standard lore piece
            standard_piece = await self.get_lore_piece_by_code(code_name)
            return {
                "lore_piece": standard_piece,
                "enhanced": False,
                "fallback_used": True,
                "error": str(e)
            }
    
    async def unlock_clue_with_cinema(self, user_id: int, piece_code: str, unlock_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Enhanced clue unlocking with cinema treasure hunting experience.
        
        Args:
            user_id: User ID
            piece_code: Lore piece code to unlock
            unlock_context: Context data for the unlock (choice made, points spent, etc.)
            
        Returns:
            Enhanced unlock experience result
        """
        import logging
        from typing import Dict, Any
        logger = logging.getLogger(__name__)
        
        try:
            # Get the lore piece being unlocked
            lore_piece = await self.get_lore_piece_by_code(piece_code)
            
            result = {
                "success": bool(lore_piece),
                "lore_piece": lore_piece,
                "enhanced": False,
                "treasure_experience": None
            }
            
            if not lore_piece:
                result["error"] = f"Lore piece {piece_code} not found"
                return result
            
            # Try cinema enhancement
            if self.cinema_master and self.cinema_master.cinema_active:
                try:
                    enhanced_result = await self.cinema_master.enhance_clue_experience(
                        user_id, piece_code, {
                            "lore_piece": lore_piece,
                            "unlock_context": unlock_context or {}
                        }
                    )
                    
                    if enhanced_result:
                        result.update(enhanced_result)
                        result["enhanced"] = True
                        
                except Exception as e:
                    logger.warning(f"Cinema enhancement failed for clue unlock: {e}")
            
            return result
            
        except Exception as e:
            logger.exception(f"Error in unlock_clue_with_cinema: {e}")
            return {
                "success": False,
                "error": str(e),
                "enhanced": False,
                "fallback_available": True
            }
    
    async def get_treasure_hunting_recommendations(self, user_id: int, context: str = None) -> List[Dict[str, Any]]:
        """
        Get personalized lore piece recommendations based on treasure hunting psychology.
        
        Args:
            user_id: User ID
            context: Context for recommendations (current fragment, last choice, etc.)
            
        Returns:
            List of recommended lore pieces with treasure hunting appeal
        """
        import logging
        from typing import Dict, Any, List
        from sqlalchemy import select
        logger = logging.getLogger(__name__)
        
        try:
            # Get all available lore pieces
            stmt = select(LorePiece).where(LorePiece.is_active == True)
            result = await self.session.execute(stmt)
            all_pieces = result.scalars().all()
            
            recommendations = []
            
            # If no cinema enhancement, return basic recommendations
            if not self.cinema_master or not self.cinema_master.is_treasure_hunting_available():
                return [{"lore_piece": p, "treasure_appeal": 0.5, "personalized": False} for p in all_pieces]
            
            # Apply treasure hunting personalization to recommendations
            treasure_hunting = getattr(self.cinema_master, 'treasure_hunting', None)
            if treasure_hunting and hasattr(treasure_hunting, 'get_treasure_recommendations'):
                try:
                    treasure_recommendations = await treasure_hunting.get_treasure_recommendations(
                        user_id, all_pieces, context
                    )
                    recommendations.extend(treasure_recommendations)
                except Exception as e:
                    logger.warning(f"Treasure recommendations failed for user {user_id}: {e}")
                    # Fallback to basic recommendations
                    recommendations = [{"lore_piece": p, "treasure_appeal": 0.5, "personalized": False} for p in all_pieces]
            else:
                recommendations = [{"lore_piece": p, "treasure_appeal": 0.5, "personalized": False} for p in all_pieces]
            
            return recommendations
            
        except Exception as e:
            logger.exception(f"Error in get_treasure_hunting_recommendations for user {user_id}: {e}")
            return []
    
    async def create_treasure_hunting_experience(self, user_id: int, discovery_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a complete treasure hunting experience for clue discovery.
        
        Args:
            user_id: User ID
            discovery_context: Context of the discovery (how clue was found, etc.)
            
        Returns:
            Complete treasure hunting experience data
        """
        import logging
        from typing import Dict, Any
        logger = logging.getLogger(__name__)
        
        try:
            result = {
                "treasure_experience_created": False,
                "experience_data": None,
                "enhanced": False
            }
            
            # Try treasure hunting experience creation
            if (self.cinema_master and 
                self.cinema_master.is_treasure_hunting_available()):
                
                try:
                    treasure_hunting = getattr(self.cinema_master, 'treasure_hunting', None)
                    if treasure_hunting and hasattr(treasure_hunting, 'create_discovery_experience'):
                        experience_data = await treasure_hunting.create_discovery_experience(
                            user_id, discovery_context
                        )
                        if experience_data:
                            result.update({
                                "treasure_experience_created": True,
                                "experience_data": experience_data,
                                "enhanced": True,
                                "enhancement_type": "treasure_hunting_experience"
                            })
                except Exception as e:
                    logger.warning(f"Treasure hunting experience creation failed for user {user_id}: {e}")
            
            return result
            
        except Exception as e:
            logger.exception(f"Error in create_treasure_hunting_experience: {e}")
            return {
                "treasure_experience_created": False,
                "enhanced": False,
                "error": str(e)
            }
