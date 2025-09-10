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
    
    async def process_decision_with_points(self, user_id: int, decision_id: int, bot=None):
        """
        Process narrative decision with integrated points system for unified narrative model.
        
        Args:
            user_id: ID del usuario de Telegram
            decision_id: Índice de la decisión tomada (0, 1, 2...)
            bot: Instancia del bot para enviar mensajes
            
        Returns:
            Dict con resultado de la decisión y información de puntos
        """
        try:
            # Use MVPNarrativeFragmentService for unified system
            from services.mvp_narrative_fragment_service import MVPNarrativeFragmentService
            mvp_narrative = MVPNarrativeFragmentService(self.session)
            
            # Process the choice using the unified system
            choice_result = await mvp_narrative.process_user_choice(
                user_id, 
                decision_id,
                additional_data={'source': 'coordinator_central'}
            )
            
            if choice_result['success']:
                # Award points for making a decision (cross-module integration)
                points_awarded = choice_result.get('points_awarded', 0)
                if points_awarded > 0:
                    await self.point_service.add_points(
                        user_id, 
                        points_awarded
                    )
                
                return {
                    'type': 'success',
                    'fragment': choice_result.get('current_fragment'),
                    'points_awarded': points_awarded,
                    'level_progression': choice_result.get('level_progression', {}),
                    'message': 'Decisión procesada exitosamente con recompensas integradas'
                }
            else:
                return {
                    'type': 'error',
                    'message': choice_result.get('error', 'Error procesando la decisión narrativa')
                }
                
        except Exception as e:
            logger.error(f"Error processing decision with points: {e}")
            return {
                'type': 'error',
                'message': f'Error interno procesando la decisión: {str(e)}'
            }
