"""
Integration service to connect narrative system with gamification (points) system.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..narrative_service import NarrativeService
from ..point_service import PointService
from ..database.narrative_models import NarrativeDecision

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
        
        # Check if decision requires points
        if decision.points_required and decision.points_required > 0:
            user_points = await self.point_service.get_user_points(user_id)
            if user_points < decision.points_required:
                logger.info(f"User {user_id} attempted to make decision {decision_id} but has insufficient points ({user_points}/{decision.points_required})")
                return False
            logger.info(f"User {user_id} has sufficient points for decision {decision_id} ({user_points}/{decision.points_required})")
        
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
        
        # Deduct points if required
        if decision.points_required and decision.points_required > 0:
            await self.point_service.deduct_points(user_id, decision.points_required)
            logger.info(f"Deducted {decision.points_required} points from user {user_id} for decision {decision_id}")
        
        # Award points if this decision gives points
        if decision.points_awarded and decision.points_awarded > 0:
            await self.point_service.add_points(user_id, decision.points_awarded, bot=bot)
            logger.info(f"Awarded {decision.points_awarded} points to user {user_id} for decision {decision_id}")
        
        # Process the decision in the narrative system
        new_fragment = await self.narrative_service.process_user_decision(user_id, decision_id)
        
        if not new_fragment:
            return {
                "type": "error",
                "message": "Error al procesar la decisión."
            }
        
        return {
            "type": "success",
            "fragment": new_fragment
        }
