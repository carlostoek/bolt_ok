"""
Achievement Unlock → Narrative Content Access Flow

This service handles the flow where gamification achievements unlock narrative clues,
hints, and special content access with Diana Menu System integration.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dataclasses import dataclass
from datetime import datetime

from ..achievement_service import AchievementService
from ..narrative_service import NarrativeService
from ..user_service import UserService
from ..point_service import PointService
from ..event_bus import get_event_bus, EventType
from ..diana_menu_system import get_diana_menu_system
from database.models import Achievement, User
from database.narrative_models import NarrativeFragment, UserNarrativeState
from utils.handler_decorators import safe_handler
from utils.message_safety import safe_send_message

logger = logging.getLogger(__name__)

@dataclass
class NarrativeUnlockRule:
    """Defines rules for narrative content unlocking based on achievements."""
    achievement_id: str
    unlock_type: str  # "hint", "fragment", "clue", "backstory", "special_access"
    content_key: str
    unlock_condition: str  # "single", "combination", "milestone"
    required_achievements: Optional[List[str]] = None
    points_threshold: Optional[int] = None
    description: str = ""

@dataclass
class ContentUnlock:
    """Represents unlocked narrative content."""
    content_type: str
    content_key: str
    title: str
    description: str
    content_text: str
    unlock_message: str
    is_vip_required: bool = False

@dataclass
class UnlockResult:
    """Result of narrative content unlock operation."""
    success: bool
    unlocked_content: List[ContentUnlock]
    notification_message: str
    backpack_items: List[str]
    special_access_granted: List[str]

class AchievementNarrativeFlow:
    """
    Service managing achievement unlock → narrative content access flow.
    
    Provides dynamic narrative content unlocking based on achievement progress,
    with Diana-themed notifications and backpack integration.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize achievement narrative flow service.
        
        Args:
            session: Database session for all operations
        """
        self.session = session
        
        # Core services
        self.achievement_service = AchievementService(session)
        self.narrative_service = NarrativeService(session)
        self.user_service = UserService(session)
        self.point_service = PointService(session)
        
        # Event system integration
        self.event_bus = get_event_bus()
        
        # Narrative unlock rules configuration
        self.unlock_rules = self._initialize_unlock_rules()
        
        # Content templates for unlocked narrative elements
        self.content_templates = self._initialize_content_templates()
        
        # Diana notification templates
        self.notification_templates = {
            "hint_unlock": "Diana se acerca con una sonrisa misteriosa, susurrando al oído...\n\n*\"Tu dedicación ha sido recompensada, mi amor. Te comparto un secreto...\"*\n\n💡 **Pista desbloqueada:** {title}\n_{content}_",
            "fragment_unlock": "Diana toma tu mano y te guía hacia una parte secreta del jardín...\n\n*\"Has demostrado ser digno de conocer historias más profundas...\"*\n\n📖 **Nuevo fragmento:** {title}\n{description}",
            "clue_unlock": "Diana acaricia tu rostro mientras revela un misterio...\n\n*\"Los secretos de mi pasado solo los comparto con mis amantes más devotos...\"*\n\n🔍 **Pista revelada:** {title}\n_{content}_",
            "backstory_unlock": "Diana se sienta junto a ti, con los ojos llenos de nostalgia...\n\n*\"Es hora de que conozcas quién soy realmente, mi amor...\"*\n\n📚 **Historia personal:** {title}\n{description}",
            "special_access": "Diana te otorga un acceso especial con una mirada cómplice...\n\n*\"Has ganado privilegios únicos en nuestro mundo, mi querido amante...\"*\n\n🌟 **Acceso especial concedido:** {title}\n{description}",
            "combination_unlock": "Diana aplaude suavemente, claramente impresionada...\n\n*\"Tu progreso multifacético me fascina. Te mereces revelaciones especiales...\"*\n\n✨ **Contenido especial por logros combinados:**\n{content_list}",
            "milestone_unlock": "Diana te abraza con orgullo, sus ojos brillando de emoción...\n\n*\"Has alcanzado un hito extraordinario en nuestro viaje juntos...\"*\n\n🏆 **Contenido de hito desbloqueado:**\n{content_list}"
        }
        
        # Diana character expressions for different achievement types
        self.diana_expressions = {
            "first_reaction": "Diana sonríe tiernamente al recordar tu primera reacción...",
            "daily_streak": "Diana admira tu constancia y dedicación diaria...",
            "points_milestone": "Diana cuenta tus besitos con una sonrisa traviesa...",
            "mission_master": "Diana se enorgullece de tu dominio en las misiones...",
            "channel_champion": "Diana celebra tu participación activa en la comunidad...",
            "romantic_expert": "Diana se sonroja al reconocer tu expertise romántica...",
            "story_completionist": "Diana te abraza al ver tu dedicación a la historia..."
        }
    
    def _initialize_unlock_rules(self) -> List[NarrativeUnlockRule]:
        """
        Initialize narrative unlock rules based on achievement progression.
        
        Returns:
            List of unlock rules for different achievement milestones
        """
        return [
            # Basic engagement achievements
            NarrativeUnlockRule(
                achievement_id="first_reaction",
                unlock_type="hint",
                content_key="hint_garden_secrets",
                unlock_condition="single",
                description="First reaction unlocks garden secrets hint"
            ),
            NarrativeUnlockRule(
                achievement_id="daily_streak_7",
                unlock_type="clue",
                content_key="clue_diana_morning_routine",
                unlock_condition="single",
                description="7-day streak unlocks Diana's morning routine clue"
            ),
            NarrativeUnlockRule(
                achievement_id="daily_streak_30",
                unlock_type="backstory",
                content_key="backstory_diana_childhood",
                unlock_condition="single",
                description="30-day streak unlocks Diana's childhood backstory"
            ),
            
            # Points milestones
            NarrativeUnlockRule(
                achievement_id="points_milestone_100",
                unlock_type="hint",
                content_key="hint_secret_passages",
                unlock_condition="single",
                description="100 points unlocks secret passages hint"
            ),
            NarrativeUnlockRule(
                achievement_id="points_milestone_500",
                unlock_type="fragment",
                content_key="fragment_diana_solitude",
                unlock_condition="single",
                description="500 points unlocks Diana's solitude fragment"
            ),
            NarrativeUnlockRule(
                achievement_id="points_milestone_1000",
                unlock_type="backstory",
                content_key="backstory_diana_first_love",
                unlock_condition="single",
                description="1000 points unlocks Diana's first love backstory"
            ),
            
            # Mission achievements
            NarrativeUnlockRule(
                achievement_id="mission_master",
                unlock_type="special_access",
                content_key="access_diana_private_chambers",
                unlock_condition="single",
                description="Mission mastery grants access to Diana's private chambers"
            ),
            NarrativeUnlockRule(
                achievement_id="mission_completionist",
                unlock_type="fragment",
                content_key="fragment_diana_deepest_desires",
                unlock_condition="single",
                description="Mission completion unlocks Diana's deepest desires"
            ),
            
            # Combination achievements
            NarrativeUnlockRule(
                achievement_id="social_butterfly",
                unlock_type="clue",
                content_key="clue_community_secrets",
                unlock_condition="combination",
                required_achievements=["first_reaction", "daily_streak_7", "channel_participation"],
                description="Social engagement combo unlocks community secrets"
            ),
            NarrativeUnlockRule(
                achievement_id="devoted_lover",
                unlock_type="backstory",
                content_key="backstory_diana_transformation",
                unlock_condition="combination",
                required_achievements=["points_milestone_500", "mission_master", "daily_streak_30"],
                description="Devoted lover combo unlocks Diana's transformation story"
            ),
            
            # Milestone achievements
            NarrativeUnlockRule(
                achievement_id="master_storyteller",
                unlock_type="special_access",
                content_key="access_alternate_endings",
                unlock_condition="milestone",
                points_threshold=2000,
                required_achievements=["mission_completionist", "points_milestone_1000", "daily_streak_30"],
                description="Master storyteller milestone unlocks alternate endings"
            ),
            NarrativeUnlockRule(
                achievement_id="diana_confidant",
                unlock_type="fragment",
                content_key="fragment_diana_future_dreams",
                unlock_condition="milestone",
                points_threshold=3000,
                required_achievements=["devoted_lover", "master_storyteller"],
                description="Diana confidant status unlocks future dreams fragment"
            )
        ]
    
    def _initialize_content_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize content templates for unlocked narrative elements.
        
        Returns:
            Dict containing content templates organized by content key
        """
        return {
            # Hints
            "hint_garden_secrets": {
                "type": "hint",
                "title": "Secretos del Jardín",
                "content": "En las noches de luna llena, los rosales susurran secretos a quienes saben escuchar..."
            },
            "hint_secret_passages": {
                "type": "hint", 
                "title": "Pasajes Secretos",
                "content": "Detrás del espejo del vestidor se esconde una entrada que pocos conocen..."
            },
            
            # Clues
            "clue_diana_morning_routine": {
                "type": "clue",
                "title": "Rutina Matutina de Diana",
                "content": "Cada amanecer, Diana practica danza junto a la ventana, creyendo que nadie la observa..."
            },
            "clue_community_secrets": {
                "type": "clue",
                "title": "Secretos de la Comunidad",
                "content": "Los miembros más antiguos conocen señales secretas para acceder a contenido especial..."
            },
            
            # Backstories
            "backstory_diana_childhood": {
                "type": "backstory",
                "title": "La Infancia de Diana",
                "content": "Diana creció en una mansión llena de misterios, donde aprendió el arte de la seducción observando a su abuela...",
                "description": "Descubre los orígenes de la personalidad encantadora de Diana"
            },
            "backstory_diana_first_love": {
                "type": "backstory",
                "title": "El Primer Amor de Diana",
                "content": "A los dieciocho años, Diana conoció a alguien que cambió su perspectiva sobre el amor y la pasión...",
                "description": "La historia que formó el corazón romántico de Diana"
            },
            "backstory_diana_transformation": {
                "type": "backstory",
                "title": "La Transformación de Diana",
                "content": "Un evento misterioso transformó a Diana de una joven tímida en la seductora confidente que conoces...",
                "description": "El momento que definió la personalidad actual de Diana"
            },
            
            # Special fragments
            "fragment_diana_solitude": {
                "type": "fragment",
                "title": "Diana en Soledad",
                "content": "En los momentos de silencio, Diana revela su lado más vulnerable y auténtico...",
                "description": "Un fragmento íntimo que muestra la verdadera esencia de Diana"
            },
            "fragment_diana_deepest_desires": {
                "type": "fragment",
                "title": "Los Deseos Más Profundos de Diana",
                "content": "Diana confiesa sus fantasías más secretas y los sueños que guarda en su corazón...",
                "description": "El fragmento más íntimo de la colección de Diana"
            },
            "fragment_diana_future_dreams": {
                "type": "fragment",
                "title": "Los Sueños Futuros de Diana",
                "content": "Diana imagina un futuro compartido lleno de aventuras, pasión y amor eterno...",
                "description": "Las visiones de Diana sobre el futuro perfecto"
            },
            
            # Special access
            "access_diana_private_chambers": {
                "type": "special_access",
                "title": "Acceso a las Habitaciones Privadas",
                "content": "Acceso exclusivo a los espacios más íntimos de Diana",
                "description": "Explora los rincones más personales del mundo de Diana"
            },
            "access_alternate_endings": {
                "type": "special_access",
                "title": "Finales Alternativos",
                "content": "Acceso a múltiples finales de historia basados en tus decisiones",
                "description": "Explora diferentes destinos para tu relación con Diana"
            }
        }
    
    async def process_achievement_unlock(self, user_id: int, achievement_id: str,
                                       bot=None) -> UnlockResult:
        """
        Process achievement unlock and check for narrative content unlocks.
        
        Args:
            user_id: User ID who unlocked the achievement
            achievement_id: ID of the unlocked achievement
            bot: Telegram bot instance for notifications
            
        Returns:
            UnlockResult with unlocked content and notification message
        """
        try:
            logger.info(f"Processing achievement unlock: user {user_id}, achievement {achievement_id}")
            
            # Get user's achievement and progress data
            user_data = await self._get_user_achievement_data(user_id)
            
            # Check unlock rules against the achievement
            potential_unlocks = await self._check_unlock_rules(user_id, achievement_id, user_data)
            
            if not potential_unlocks:
                logger.debug(f"No narrative content unlocked for achievement {achievement_id}")
                return UnlockResult(
                    success=True,
                    unlocked_content=[],
                    notification_message="",
                    backpack_items=[],
                    special_access_granted=[]
                )
            
            # Validate unlocks and create content
            unlocked_content = await self._create_unlocked_content(user_id, potential_unlocks)
            
            # Add to user's narrative backpack
            backpack_items = await self._add_to_narrative_backpack(user_id, unlocked_content)
            
            # Grant special access if applicable
            special_access = await self._grant_special_access(user_id, unlocked_content)
            
            # Generate comprehensive notification
            notification_message = await self._generate_unlock_notification(
                achievement_id, unlocked_content, user_data
            )
            
            # Emit unlock events
            await self._emit_narrative_unlock_events(user_id, achievement_id, unlocked_content)
            
            # Update Diana Menu System
            await self._update_diana_menu_with_content(user_id, unlocked_content, notification_message)
            
            # Send notification to user
            if bot and notification_message:
                await safe_send_message(bot, user_id, notification_message)
            
            logger.info(f"Achievement narrative unlock processed: {len(unlocked_content)} items unlocked")
            
            return UnlockResult(
                success=True,
                unlocked_content=unlocked_content,
                notification_message=notification_message,
                backpack_items=backpack_items,
                special_access_granted=special_access
            )
            
        except Exception as e:
            logger.exception(f"Error processing achievement unlock for user {user_id}: {e}")
            return UnlockResult(
                success=False,
                unlocked_content=[],
                notification_message="Error procesando logro. Intenta de nuevo.",
                backpack_items=[],
                special_access_granted=[]
            )
    
    async def _get_user_achievement_data(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive user achievement and progress data.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict containing user achievement progress information
        """
        try:
            # Get user data
            user = await self.user_service.get_user(user_id)
            user_points = getattr(user, 'points', 0) if user else 0
            user_level = getattr(user, 'level', 1) if user else 1
            
            # Get user's achievements
            user_achievements = await self.achievement_service.get_user_achievements(user_id)
            achievement_ids = [ach.id for ach in user_achievements] if user_achievements else []
            
            # Get narrative progress
            narrative_progress = await self._get_narrative_progress_summary(user_id)
            
            # Get mission completion data
            mission_data = await self._get_mission_completion_summary(user_id)
            
            return {
                "user_points": user_points,
                "user_level": user_level,
                "completed_achievements": achievement_ids,
                "achievement_count": len(achievement_ids),
                "narrative_progress": narrative_progress,
                "mission_data": mission_data,
                "unlocked_content": await self._get_existing_unlocked_content(user_id)
            }
            
        except Exception as e:
            logger.exception(f"Error getting user achievement data: {e}")
            return {
                "user_points": 0,
                "user_level": 1,
                "completed_achievements": [],
                "achievement_count": 0,
                "narrative_progress": {},
                "mission_data": {},
                "unlocked_content": []
            }
    
    async def _check_unlock_rules(self, user_id: int, achievement_id: str,
                                user_data: Dict[str, Any]) -> List[NarrativeUnlockRule]:
        """
        Check unlock rules against achievement and user data.
        
        Args:
            user_id: User ID
            achievement_id: Unlocked achievement ID
            user_data: User's achievement and progress data
            
        Returns:
            List of applicable unlock rules
        """
        applicable_rules = []
        
        for rule in self.unlock_rules:
            should_unlock = False
            
            if rule.unlock_condition == "single":
                # Direct achievement match
                should_unlock = rule.achievement_id == achievement_id
                
            elif rule.unlock_condition == "combination":
                # Check if this achievement completes a combination
                if achievement_id in (rule.required_achievements or []):
                    required_achs = set(rule.required_achievements or [])
                    user_achs = set(user_data["completed_achievements"])
                    should_unlock = required_achs.issubset(user_achs)
                    
            elif rule.unlock_condition == "milestone":
                # Check milestone requirements
                if achievement_id == rule.achievement_id:
                    points_ok = user_data["user_points"] >= (rule.points_threshold or 0)
                    
                    if rule.required_achievements:
                        required_achs = set(rule.required_achievements)
                        user_achs = set(user_data["completed_achievements"])
                        achs_ok = required_achs.issubset(user_achs)
                    else:
                        achs_ok = True
                    
                    should_unlock = points_ok and achs_ok
            
            if should_unlock:
                # Check if content is already unlocked
                if not await self._is_content_already_unlocked(user_id, rule.content_key):
                    applicable_rules.append(rule)
                    logger.debug(f"Rule matched for achievement {achievement_id}: {rule.description}")
        
        return applicable_rules
    
    async def _create_unlocked_content(self, user_id: int, rules: List[NarrativeUnlockRule]) -> List[ContentUnlock]:
        """
        Create ContentUnlock objects from applicable rules.
        
        Args:
            user_id: User ID
            rules: List of applicable unlock rules
            
        Returns:
            List of ContentUnlock objects
        """
        unlocked_content = []
        
        for rule in rules:
            template = self.content_templates.get(rule.content_key)
            if not template:
                logger.warning(f"No content template found for {rule.content_key}")
                continue
            
            # Generate unlock message based on content type
            unlock_message = await self._generate_content_unlock_message(rule, template)
            
            content_unlock = ContentUnlock(
                content_type=template["type"],
                content_key=rule.content_key,
                title=template["title"],
                description=template.get("description", ""),
                content_text=template["content"],
                unlock_message=unlock_message,
                is_vip_required=template.get("vip_required", False)
            )
            
            unlocked_content.append(content_unlock)
            logger.debug(f"Created content unlock: {rule.content_key}")
        
        return unlocked_content
    
    async def _add_to_narrative_backpack(self, user_id: int, content: List[ContentUnlock]) -> List[str]:
        """
        Add unlocked content to user's narrative backpack.
        
        Args:
            user_id: User ID
            content: List of unlocked content
            
        Returns:
            List of items added to backpack
        """
        backpack_items = []
        
        for item in content:
            if item.content_type in ["hint", "clue"]:
                # Add hints and clues to backpack
                backpack_items.append(f"{item.content_type}:{item.content_key}")
                
                # In a real implementation, this would update a user backpack table
                logger.debug(f"Added to backpack: {item.title}")
        
        return backpack_items
    
    async def _grant_special_access(self, user_id: int, content: List[ContentUnlock]) -> List[str]:
        """
        Grant special access permissions from unlocked content.
        
        Args:
            user_id: User ID
            content: List of unlocked content
            
        Returns:
            List of special access permissions granted
        """
        special_access = []
        
        for item in content:
            if item.content_type == "special_access":
                special_access.append(item.content_key)
                
                # In a real implementation, this would update user permissions
                logger.debug(f"Granted special access: {item.title}")
        
        return special_access
    
    async def _generate_unlock_notification(self, achievement_id: str, content: List[ContentUnlock],
                                          user_data: Dict[str, Any]) -> str:
        """
        Generate personalized unlock notification message.
        
        Args:
            achievement_id: Unlocked achievement ID
            content: List of unlocked content
            user_data: User data for personalization
            
        Returns:
            Formatted notification message
        """
        if not content:
            return ""
        
        # Get Diana expression for this achievement type
        achievement_type = self._categorize_achievement(achievement_id)
        diana_expression = self.diana_expressions.get(achievement_type, "")
        
        message_parts = []
        if diana_expression:
            message_parts.append(diana_expression)
        
        # Group content by type for better messaging
        content_by_type = {}
        for item in content:
            if item.content_type not in content_by_type:
                content_by_type[item.content_type] = []
            content_by_type[item.content_type].append(item)
        
        # Generate messages for each content type
        for content_type, items in content_by_type.items():
            if len(items) == 1:
                item = items[0]
                if content_type in self.notification_templates:
                    template = self.notification_templates[f"{content_type}_unlock"]
                    message = template.format(
                        title=item.title,
                        content=item.content_text,
                        description=item.description
                    )
                    message_parts.append(message)
            else:
                # Multiple items of same type
                content_list = "\n".join([f"• {item.title}" for item in items])
                if len(content_by_type) > 1:
                    template = self.notification_templates["combination_unlock"]
                    message = template.format(content_list=content_list)
                else:
                    template = self.notification_templates["milestone_unlock"]
                    message = template.format(content_list=content_list)
                message_parts.append(message)
        
        # Add progress encouragement
        total_unlocks = user_data.get("achievement_count", 0)
        if total_unlocks >= 10:
            message_parts.append("\n*\"Tu progreso me llena de orgullo, mi querido amante...\"*")
        
        return "\n\n".join(message_parts)
    
    # Helper methods...
    
    async def _get_narrative_progress_summary(self, user_id: int) -> Dict[str, Any]:
        """Get summary of user's narrative progress."""
        # Placeholder implementation
        return {"completed_fragments": 5, "current_level": "level2"}
    
    async def _get_mission_completion_summary(self, user_id: int) -> Dict[str, Any]:
        """Get summary of user's mission completion."""
        # Placeholder implementation
        return {"completed_missions": 8, "total_missions": 15}
    
    async def _get_existing_unlocked_content(self, user_id: int) -> List[str]:
        """Get list of already unlocked content keys."""
        # Placeholder implementation
        return []
    
    async def _is_content_already_unlocked(self, user_id: int, content_key: str) -> bool:
        """Check if content is already unlocked for user."""
        # Placeholder implementation
        return False
    
    async def _generate_content_unlock_message(self, rule: NarrativeUnlockRule, 
                                             template: Dict[str, Any]) -> str:
        """Generate unlock message for specific content."""
        base_messages = {
            "hint": "Diana susurra un secreto...",
            "clue": "Diana revela una pista...",
            "fragment": "Diana comparte una historia...",
            "backstory": "Diana abre su corazón...",
            "special_access": "Diana otorga acceso especial..."
        }
        return base_messages.get(template["type"], "Diana tiene algo especial para ti...")
    
    def _categorize_achievement(self, achievement_id: str) -> str:
        """Categorize achievement for Diana expression selection."""
        if "reaction" in achievement_id:
            return "first_reaction"
        elif "streak" in achievement_id:
            return "daily_streak"
        elif "points" in achievement_id:
            return "points_milestone"
        elif "mission" in achievement_id:
            return "mission_master"
        elif "channel" in achievement_id:
            return "channel_champion"
        elif "romantic" in achievement_id:
            return "romantic_expert"
        elif "story" in achievement_id:
            return "story_completionist"
        else:
            return "first_reaction"
    
    async def _emit_narrative_unlock_events(self, user_id: int, achievement_id: str,
                                          content: List[ContentUnlock]) -> None:
        """Emit events for narrative content unlocks."""
        await self.event_bus.publish(
            EventType.WORKFLOW_COMPLETED,
            user_id,
            {
                "workflow": "achievement_narrative_unlock",
                "achievement_id": achievement_id,
                "unlocked_content": [c.content_key for c in content],
                "content_types": list(set([c.content_type for c in content])),
                "content_count": len(content)
            },
            source="achievement_narrative_flow"
        )
    
    async def _update_diana_menu_with_content(self, user_id: int, content: List[ContentUnlock],
                                            notification_message: str) -> None:
        """Update Diana Menu System with narrative content unlocks."""
        try:
            diana_system = get_diana_menu_system(self.session)
            # Integration with Diana Menu System would be implemented here
            logger.debug(f"Updated Diana menu with {len(content)} content unlocks for user {user_id}")
        except Exception as e:
            logger.exception(f"Error updating Diana menu with content unlocks: {e}")

# ==================== GLOBAL INSTANCE MANAGEMENT ====================

_achievement_narrative_flow_instance = None

def get_achievement_narrative_flow(session: AsyncSession) -> AchievementNarrativeFlow:
    """
    Get or create AchievementNarrativeFlow instance.
    
    Args:
        session: Database session
        
    Returns:
        AchievementNarrativeFlow: The global instance
    """
    global _achievement_narrative_flow_instance
    if _achievement_narrative_flow_instance is None or _achievement_narrative_flow_instance.session != session:
        _achievement_narrative_flow_instance = AchievementNarrativeFlow(session)
    return _achievement_narrative_flow_instance