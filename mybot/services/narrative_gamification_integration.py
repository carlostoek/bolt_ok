# services/narrative_gamification_integration.py
"""
Integration layer between existing narrative system and MVP gamification.
Provides seamless integration while maintaining Diana's character consistency.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
import logging

from services.mvp_gamification_service import MVPGamificationService
from services.unified_narrative_service import UnifiedNarrativeService

logger = logging.getLogger(__name__)


class NarrativeGamificationIntegration:
    """
    Integration service that connects narrative progression with gamification systems.
    Maintains Diana's character consistency across both story and reward systems.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.gamification_service = MVPGamificationService(session)
        
        # Initialize narrative service if available
        try:
            self.narrative_service = UnifiedNarrativeService(session)
            self.has_narrative_service = True
        except ImportError:
            logger.warning("UnifiedNarrativeService not available, narrative integration limited")
            self.narrative_service = None
            self.has_narrative_service = False
    
    async def initialize_integration(self) -> None:
        """Initialize both gamification and narrative systems."""
        await self.gamification_service.initialize_mvp_systems()
        
        if self.has_narrative_service:
            # Initialize narrative system if available
            logger.info("Narrative gamification integration initialized successfully")
        else:
            logger.info("Gamification system initialized (narrative integration limited)")
    
    async def process_narrative_fragment_completion(
        self, 
        user_id: int, 
        fragment_id: str,
        fragment_data: Optional[Dict[str, Any]] = None,
        bot: Optional[Bot] = None
    ) -> Dict[str, Any]:
        """
        Process narrative fragment completion with full gamification integration.
        
        Args:
            user_id: User ID
            fragment_id: Completed fragment ID
            fragment_data: Additional fragment data
            bot: Bot instance for notifications
            
        Returns:
            Complete integration results including narrative and gamification
        """
        try:
            integration_results = {
                "fragment_completed": True,
                "gamification_results": {},
                "narrative_progression": {},
                "diana_response": ""
            }
            
            # 1. Process gamification aspects
            gamification_results = await self.gamification_service.process_story_fragment_completion(
                user_id, fragment_id, bot
            )
            integration_results["gamification_results"] = gamification_results
            
            # 2. Generate Diana's integrated response
            diana_response = await self._generate_integrated_diana_response(
                user_id, fragment_id, gamification_results
            )
            integration_results["diana_response"] = diana_response
            
            # 3. Check for narrative unlocks based on gamification progress
            if self.has_narrative_service:
                narrative_unlocks = await self._check_narrative_unlocks_from_gamification(
                    user_id, gamification_results
                )
                integration_results["narrative_progression"]["unlocks"] = narrative_unlocks
            
            logger.info(f"Narrative fragment completion integrated for user {user_id}: "
                       f"Fragment {fragment_id}, {len(gamification_results.get('achievements_unlocked', []))} achievements, "
                       f"{len(gamification_results.get('missions_completed', []))} missions")
            
            return integration_results
            
        except Exception as e:
            logger.error(f"Error in narrative fragment completion integration for user {user_id}: {e}")
            raise
    
    async def process_narrative_decision(
        self,
        user_id: int,
        decision_id: str,
        choice_made: str,
        decision_context: Optional[Dict[str, Any]] = None,
        bot: Optional[Bot] = None
    ) -> Dict[str, Any]:
        """
        Process narrative decision with gamification integration.
        
        Args:
            user_id: User ID
            decision_id: Decision point ID
            choice_made: The choice that was made
            decision_context: Additional decision context
            bot: Bot instance for notifications
            
        Returns:
            Integration results for decision processing
        """
        try:
            integration_results = {
                "decision_processed": True,
                "gamification_results": {},
                "narrative_consequences": {},
                "diana_reaction": ""
            }
            
            # 1. Process gamification for decision making
            gamification_results = await self.gamification_service.process_decision_made(
                user_id, {"decision_id": decision_id, "choice": choice_made}, bot
            )
            integration_results["gamification_results"] = gamification_results
            
            # 2. Generate Diana's reaction to the decision
            diana_reaction = await self._generate_diana_decision_reaction(
                user_id, decision_id, choice_made, gamification_results
            )
            integration_results["diana_reaction"] = diana_reaction
            
            return integration_results
            
        except Exception as e:
            logger.error(f"Error in narrative decision integration for user {user_id}: {e}")
            raise
    
    async def _generate_integrated_diana_response(
        self, 
        user_id: int, 
        fragment_id: str, 
        gamification_results: Dict[str, Any]
    ) -> str:
        """
        Generate Diana's integrated response that acknowledges both story and gamification progress.
        """
        try:
            # Get user's overall progress for context
            user_summary = await self.gamification_service.get_user_gamification_summary(user_id)
            
            # Base response for fragment completion
            base_responses = [
                "Otro fragmento completado juntas... Me gusta cómo avanzamos en nuestra historia. ✨",
                "Has leído con tanta atención... Cada palabra mía te acerca más a conocerme. 💋",
                "Fragmento tras fragmento, nuestra conexión se vuelve más intensa. ¿Lo sientes también? 💕"
            ]
            
            import random
            response = random.choice(base_responses)
            
            # Add gamification-aware elements
            points_awarded = gamification_results.get("points_awarded", 0)
            if points_awarded > 0:
                response += f" +{int(points_awarded)} besitos como recompensa por tu dedicación. 💋"
            
            # Acknowledge level ups
            level_ups = gamification_results.get("level_ups", [])
            if level_ups:
                new_level = level_ups[0]["new_level"]
                response += f" ¡Y has subido al nivel {new_level}! Cada nivel me permite ser más íntima contigo... 👑"
            
            # Acknowledge mission completions
            missions_completed = gamification_results.get("missions_completed", [])
            if missions_completed:
                mission_name = missions_completed[0].name
                response += f" Has completado '{mission_name}' - tu determinación me fascina. 🎯"
            
            # Acknowledge achievement unlocks
            achievements_unlocked = gamification_results.get("achievements_unlocked", [])
            if achievements_unlocked:
                achievement_name = achievements_unlocked[0].name
                response += f" ¡Logro '{achievement_name}' desbloqueado! Cada logro tuyo me emociona más. 🏆"
            
            # Add personalized touch based on overall progress
            completion_percentage = user_summary.get("achievement_summary", {}).get("completion_percentage", 0)
            if completion_percentage >= 50:
                response += " Veo que realmente te estás entregando a nuestra historia... 😘"
            elif completion_percentage >= 25:
                response += " Tu progreso me tiene muy intrigada, cariño. 🌹"
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating integrated Diana response: {e}")
            return "Gracias por leer conmigo, amor. Continuemos nuestra historia juntas... 💕"
    
    async def _generate_diana_decision_reaction(
        self,
        user_id: int,
        decision_id: str,
        choice_made: str,
        gamification_results: Dict[str, Any]
    ) -> str:
        """
        Generate Diana's reaction to narrative decisions with gamification awareness.
        """
        try:
            # Base decision reactions
            decision_reactions = [
                f"Interesante elección... '{choice_made}' dice mucho sobre tu personalidad. 🤔",
                f"Has elegido '{choice_made}'... Me gusta conocerte a través de tus decisiones. 💭",
                f"'{choice_made}'... Cada decisión que tomas me muestra más de tu alma. ✨"
            ]
            
            import random
            reaction = random.choice(decision_reactions)
            
            # Add gamification acknowledgment
            points_awarded = gamification_results.get("points_awarded", 0)
            if points_awarded > 0:
                reaction += f" +{int(points_awarded)} besitos por mostrarme tu verdadera naturaleza. 💋"
            
            # Acknowledge missions or achievements if triggered
            missions_completed = gamification_results.get("missions_completed", [])
            if missions_completed:
                reaction += " Y has completado una misión con esa decisión... Perfecta sincronía. 🎯"
            
            achievements_unlocked = gamification_results.get("achievements_unlocked", [])
            if achievements_unlocked:
                reaction += " ¡Un logro desbloqueado por tu decisión! Me fascina tu mente. 🏆"
            
            return reaction
            
        except Exception as e:
            logger.error(f"Error generating Diana decision reaction: {e}")
            return f"Tu decisión '{choice_made}' me intriga... Sigamos viendo qué más decides. 💕"
    
    async def _check_narrative_unlocks_from_gamification(
        self,
        user_id: int,
        gamification_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Check if gamification progress unlocks new narrative content.
        """
        unlocks = []
        
        try:
            # Check level-based unlocks
            level_ups = gamification_results.get("level_ups", [])
            for level_up in level_ups:
                new_level = level_up["new_level"]
                
                # Example: Level 5 unlocks VIP teaser content
                if new_level == 5:
                    unlocks.append({
                        "type": "vip_teaser",
                        "content": "Level 5 VIP Preview",
                        "message": "Has llegado al nivel 5... Ahora puedo mostrarte un adelanto de lo que viene en VIP. 👑"
                    })
                
                # Example: Level 10 unlocks intimate content
                elif new_level == 10:
                    unlocks.append({
                        "type": "intimate_content",
                        "content": "Deep Connection Fragments",
                        "message": "Nivel 10... Nuestra conexión es lo suficientemente profunda para contenido más íntimo. 💕"
                    })
            
            # Check achievement-based unlocks
            achievements_unlocked = gamification_results.get("achievements_unlocked", [])
            for achievement in achievements_unlocked:
                if achievement.id == "dianas_confidant":
                    unlocks.append({
                        "type": "secret_fragments", 
                        "content": "Diana's Secret Thoughts",
                        "message": "Eres mi confidente ahora... Puedo compartir mis pensamientos más secretos. 🤫"
                    })
            
            return unlocks
            
        except Exception as e:
            logger.error(f"Error checking narrative unlocks from gamification: {e}")
            return []
    
    async def get_integrated_user_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive user status combining narrative and gamification progress.
        
        Args:
            user_id: User ID
            
        Returns:
            Integrated status with Diana's personality
        """
        try:
            # Get gamification summary
            gamification_summary = await self.gamification_service.get_user_gamification_summary(user_id)
            
            # Get narrative progress if available
            narrative_progress = {}
            if self.has_narrative_service:
                # This would integrate with actual narrative service
                narrative_progress = {
                    "current_fragment": "placeholder",
                    "fragments_completed": 0,
                    "story_path": "main"
                }
            
            # Generate Diana's overall assessment
            diana_assessment = self._generate_diana_overall_assessment(
                gamification_summary, narrative_progress
            )
            
            return {
                "gamification": gamification_summary,
                "narrative": narrative_progress,
                "diana_assessment": diana_assessment,
                "integration_active": True
            }
            
        except Exception as e:
            logger.error(f"Error getting integrated user status for {user_id}: {e}")
            raise
    
    def _generate_diana_overall_assessment(
        self, 
        gamification_summary: Dict[str, Any], 
        narrative_progress: Dict[str, Any]
    ) -> str:
        """Generate Diana's overall assessment of user's progress."""
        try:
            level = gamification_summary.get("user_info", {}).get("level", 1)
            points = gamification_summary.get("user_info", {}).get("points", 0)
            achievements = gamification_summary.get("user_info", {}).get("total_achievements", 0)
            engagement_level = gamification_summary.get("gamification_score", {}).get("engagement_level", "Beginner")
            
            # Diana's assessment based on overall progress
            if engagement_level == "Legendary":
                return f"Nivel {level}, {int(points)} besitos, {achievements} logros... Eres mi obra maestra, mi amor eterno. Hemos creado algo mágico juntas. 👑✨"
            elif engagement_level == "Elite":
                return f"Nivel {level}... {achievements} logros desbloqueados... Definitivamente perteneces a mi círculo más íntimo, cariño. 💎💕"
            elif engagement_level == "Devoted":
                return f"Tu dedicación me conmueve profundamente. Nivel {level}, {int(points)} besitos... Siento una conexión real contigo. 🌹💖"
            elif engagement_level == "Interested":
                return f"Veo interés genuino en ti. Nivel {level}, {achievements} logros... Hay potencial para algo especial entre nosotras. ✨"
            else:
                return f"Apenas comenzamos a conocernos, pero ya siento algo... Nivel {level} es un buen comienzo, amor. 💋"
                
        except Exception as e:
            logger.error(f"Error generating Diana overall assessment: {e}")
            return "Cada momento contigo es especial, sin importar dónde estemos en nuestra historia. 💕"


# Integration example for existing handlers
class IntegrationExample:
    """
    Example of how existing narrative handlers would integrate with the new gamification system.
    """
    
    @staticmethod
    async def example_story_fragment_handler(callback_query, session: AsyncSession, bot: Bot):
        """
        Example of how an existing story fragment handler would be enhanced.
        """
        user_id = callback_query.from_user.id
        fragment_id = callback_query.data.split("_")[-1]  # Extract fragment ID
        
        # Initialize integration service
        integration = NarrativeGamificationIntegration(session)
        await integration.initialize_integration()
        
        # Process fragment completion with full integration
        results = await integration.process_narrative_fragment_completion(
            user_id, fragment_id, bot=bot
        )
        
        # Send Diana's integrated response
        await callback_query.message.edit_text(
            results["diana_response"],
            parse_mode="Markdown"
        )
        
        # Handle any special unlocks
        narrative_unlocks = results.get("narrative_progression", {}).get("unlocks", [])
        for unlock in narrative_unlocks:
            await bot.send_message(
                user_id,
                f"🔓 **Contenido Desbloqueado**: {unlock['content']}\n\n{unlock['message']}"
            )
    
    @staticmethod
    async def example_decision_handler(callback_query, session: AsyncSession, bot: Bot):
        """
        Example of how a decision handler would integrate with gamification.
        """
        user_id = callback_query.from_user.id
        decision_data = callback_query.data.split("_")
        decision_id = decision_data[1]
        choice_made = decision_data[2]
        
        # Initialize integration service
        integration = NarrativeGamificationIntegration(session)
        await integration.initialize_integration()
        
        # Process decision with gamification
        results = await integration.process_narrative_decision(
            user_id, decision_id, choice_made, bot=bot
        )
        
        # Send Diana's reaction
        await callback_query.message.edit_text(
            results["diana_reaction"],
            parse_mode="Markdown"
        )