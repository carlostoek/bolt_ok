"""
Integration service to connect narrative system with gamification (points) system.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
try:
    from ..narrative_service import NarrativeService
    from ..point_service import PointService
    from ..database.narrative_models import NarrativeChoice
except ImportError:
    # Fallback to absolute imports for standalone usage
    from services.narrative_service import NarrativeService
    from services.point_service import PointService
    from database.narrative_models import NarrativeChoice

# Alias for compatibility
NarrativeDecision = NarrativeChoice

logger = logging.getLogger(__name__)

class NarrativePointService:
    """
    Service to handle integration between narrative decisions and the point system.
    Allows for point-gated narrative choices and awarding points for narrative progression.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.narrative_service = NarrativeService(session)
        self.point_service = PointService(session)
    
    async def can_make_decision(self, user_id: int, decision_id: int) -> bool:
        """
        Checks if a user has enough points to make a specific narrative decision.
        Some premium decisions require a minimum number of points.
        
        Args:
            user_id: The Telegram user ID
            decision_id: The ID of the narrative decision
            
        Returns:
            bool: True if the user can make the decision, False otherwise
        """
        # Get the decision from the database
        decision = await self.session.execute(
            select(NarrativeDecision).where(NarrativeDecision.id == decision_id)
        )
        decision = decision.scalar_one_or_none()
        
        if not decision:
            logger.warning(f"Decision {decision_id} not found")
            return False
        
        # Check if decision requires points (using required_besitos field)
        required_points = getattr(decision, 'required_besitos', 0) or 0
        if required_points > 0:
            user_points = await self.point_service.get_user_points(user_id)
            if user_points < required_points:
                logger.info(f"User {user_id} attempted to make decision {decision_id} but has insufficient points ({user_points}/{required_points})")
                return False
            logger.info(f"User {user_id} has sufficient points for decision {decision_id} ({user_points}/{required_points})")
        
        return True
    
    async def process_decision_with_points(self, user_id: int, decision_id: int, bot=None):
        """
        Processes a narrative decision with point verification and rewards.
        If the decision requires points, verifies the user has enough.
        If the decision awards points, adds them to the user's account.
        
        Args:
            user_id: The Telegram user ID
            decision_id: The ID of the narrative decision
            bot: Optional bot instance for sending notifications
            
        Returns:
            dict: Result of the decision processing, including new fragment or error message
        """
        # Check if user can make the decision
        can_make = await self.can_make_decision(user_id, decision_id)
        if not can_make:
            return {
                "type": "points_required",
                "message": "No tienes suficientes puntos para esta decisión.",
                "decision_id": decision_id
            }
        
        # Get the decision
        decision = await self.session.execute(
            select(NarrativeDecision).where(NarrativeDecision.id == decision_id)
        )
        decision = decision.scalar_one_or_none()
        
        if not decision:
            return {
                "type": "error",
                "message": "Decisión no encontrada."
            }
        
        # Deduct points if required (using required_besitos field)
        required_points = getattr(decision, 'required_besitos', 0) or 0
        if required_points > 0:
            await self.point_service.deduct_points(user_id, required_points)
            logger.info(f"Deducted {required_points} points from user {user_id} for decision {decision_id}")
        
        # Note: The current NarrativeChoice model doesn't have a points_awarded field
        # This would need to be added to the database model if point rewards for decisions are needed
        
        # Process the decision in the narrative system using the actual decision ID
        new_fragment = await self.narrative_service.process_user_decision_by_id(user_id, decision_id)
        
        if not new_fragment:
            return {
                "type": "error",
                "message": "Error al procesar la decisión."
            }
        
        return {
            "type": "success",
            "fragment": new_fragment
        }
