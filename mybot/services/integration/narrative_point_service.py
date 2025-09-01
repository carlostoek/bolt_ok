"""
Integration service to connect narrative system with gamification (points) system.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from services.narrative_service import NarrativeService
from services.point_service import PointService
# NarrativeDecision not needed - using unified choice system in fragments

logger = logging.getLogger(__name__)

class NarrativePointService:
    """
    Service to handle integration between narrative decisions and the point system.
    Allows for point-gated narrative choices and awarding points for narrative progression.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.narrative_service = NarrativeService(session)
        
        # Initialize PointService with proper dependency injection
        from services.level_service import LevelService
        from services.achievement_service import AchievementService
        
        level_service = LevelService(session)
        achievement_service = AchievementService(session)
        self.point_service = PointService(session, level_service, achievement_service)
    
    # TODO: Update for unified narrative system - decisions are now stored in fragment choices JSON
    # async def can_make_decision(self, user_id: int, decision_id: int) -> bool:
    #     """DEPRECATED - needs refactoring for unified system"""
    #     pass
    
    # TODO: Update for unified narrative system - decisions are now stored in fragment choices JSON
    # async def process_decision_with_points(self, user_id: int, decision_id: int, bot=None):
    #     """DEPRECATED - needs refactoring for unified system"""
    #     pass
