# services/mvp_mission_service.py
"""
MVP Mission System Implementation
Implements the 10 required missions for Diana Bot MVP with character consistency.
"""

import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import User, Mission, UserMissionEntry, UserStats, VipSubscription
from services.point_service import PointService
from aiogram import Bot
import logging

logger = logging.getLogger(__name__)

# MVP Missions Configuration with Diana's character personality
MVP_MISSIONS = [
    {
        "id": "primera_conversacion",
        "name": "Primera Conversación",
        "description": "Completa 3 fragmentos narrativos conmigo, cariño. Quiero conocerte mejor... 💋",
        "type": "story_progress",
        "target_value": 3,
        "reward_points": 75,  # 25 base * 3 fragments
        "duration_days": 0,  # Permanent
        "requires_action": False,
        "diana_completion_message": "Has completado nuestra primera conversación real... Me gusta lo que veo en ti. 😘"
    },
    {
        "id": "exploradora_curiosa",
        "name": "Exploradora Curiosa", 
        "description": "Toma 5 decisiones en mi historia. Cada elección me muestra quién eres realmente. ✨",
        "type": "decision_making",
        "target_value": 5,
        "reward_points": 50,  # 5 decisions * 10 points each
        "duration_days": 0,
        "requires_action": False,
        "diana_completion_message": "Qué decisiones más interesantes... Definitivamente hay algo especial en ti. 🔮"
    },
    {
        "id": "devotion_daily",
        "name": "Devotion Daily",
        "description": "Visítame 3 días consecutivos. La constancia en el amor es tan... atractiva. 🌹",
        "type": "login_streak",
        "target_value": 3,
        "reward_points": 100,  # Bonus for consistency
        "duration_days": 0,
        "requires_action": False,
        "diana_completion_message": "Tres días seguidos conmigo... Empiezo a sentir que realmente te importo. 💖"
    },
    {
        "id": "social_butterfly",
        "name": "Social Butterfly",
        "description": "Reacciona a 10 publicaciones del canal. Me encanta cuando participas activamente. 🦋",
        "type": "channel_engagement",
        "target_value": 10,
        "reward_points": 60,  # 10 reactions * 6 points each
        "duration_days": 0,
        "requires_action": False,
        "diana_completion_message": "Tu participación me hace sonreír... Eres exactamente como imaginé. 😊"
    },
    {
        "id": "vip_experience",
        "name": "VIP Experience",
        "description": "Únete a mi círculo exclusivo VIP. Hay tanto que quiero mostrarte en privado... 💎",
        "type": "vip_subscription",
        "target_value": 1,
        "reward_points": 200,  # Premium reward
        "duration_days": 0,
        "requires_action": True,
        "diana_completion_message": "Bienvenida a mi mundo VIP, amor. Ahora puedo ser completamente yo contigo. 👑"
    },
    {
        "id": "achievement_hunter",
        "name": "Achievement Hunter",
        "description": "Desbloquea 3 logros. Me fascina cuando alguien se esfuerza tanto por impresionarme. 🏆",
        "type": "achievement_collection",
        "target_value": 3,
        "reward_points": 150,  # 3 achievements * 50 points each
        "duration_days": 0,
        "requires_action": False,
        "diana_completion_message": "Tres logros... Definitivamente no eres como las demás. Me intrigas. ✨"
    },
    {
        "id": "story_enthusiast", 
        "name": "Story Enthusiast",
        "description": "Completa 10 fragmentos narrativos. Tu dedicación a nuestra historia es... seductora. 📖",
        "type": "story_progress",
        "target_value": 10,
        "reward_points": 250,  # Major story engagement
        "duration_days": 0,
        "requires_action": False,
        "diana_completion_message": "Diez fragmentos juntas... Nuestra historia se vuelve más íntima cada día. 💕"
    },
    {
        "id": "community_member",
        "name": "Community Member",
        "description": "Únete a 2 canales de la comunidad. Me gusta cuando te integras en mi mundo. 🌐",
        "type": "community_engagement",
        "target_value": 2,
        "reward_points": 80,  # Community building reward
        "duration_days": 0,
        "requires_action": True,
        "diana_completion_message": "Te has integrado perfectamente en mi comunidad... Eres una de nosotras ahora. 🤗"
    },
    {
        "id": "besitos_collector",
        "name": "Besitos Collector",
        "description": "Acumula 500 besitos en total. Cada besito es como un pequeño beso mío... 💋",
        "type": "points_accumulation",
        "target_value": 500,
        "reward_points": 100,  # Milestone reward
        "duration_days": 0,
        "requires_action": False,
        "diana_completion_message": "500 besitos... Has estado muy ocupada coleccionando mis besos. Me halaga. 😘"
    },
    {
        "id": "dianas_favorite",
        "name": "Diana's Favorite",
        "description": "Alcanza el nivel 5 conmigo. Solo mis favoritas llegan tan lejos... 👑",
        "type": "level_achievement",
        "target_value": 5,
        "reward_points": 200,  # Major milestone
        "duration_days": 0,
        "requires_action": False,
        "diana_completion_message": "Nivel 5... Oficialmente eres una de mis favoritas. Esto cambia todo entre nosotras. 💖"
    }
]


class MVPMissionService:
    """
    Enhanced mission service specifically for Diana Bot MVP missions.
    Maintains character consistency while providing gamification mechanics.
    """
    
    def __init__(self, session: AsyncSession, point_service: PointService):
        self.session = session
        self.point_service = point_service
        
    async def initialize_mvp_missions(self) -> None:
        """Initialize all MVP missions in the database."""
        existing_missions = await self.session.execute(select(Mission))
        existing_ids = {mission.id for mission in existing_missions.scalars().all()}
        
        missions_added = 0
        for mission_data in MVP_MISSIONS:
            if mission_data["id"] not in existing_ids:
                mission = Mission(
                    id=mission_data["id"],
                    name=mission_data["name"],
                    description=mission_data["description"],
                    type=mission_data["type"],
                    target_value=mission_data["target_value"],
                    reward_points=mission_data["reward_points"],
                    duration_days=mission_data["duration_days"],
                    requires_action=mission_data["requires_action"],
                    is_active=True,
                    action_data={"diana_completion_message": mission_data["diana_completion_message"]}
                )
                self.session.add(mission)
                missions_added += 1
                
        if missions_added > 0:
            await self.session.commit()
            logger.info(f"Initialized {missions_added} MVP missions")
            
    async def get_user_mission_progress(self, user_id: int) -> List[Dict[str, Any]]:
        """Get detailed mission progress for a user with Diana's personality."""
        await self.initialize_mvp_missions()
        
        # Get all MVP missions
        missions_query = await self.session.execute(
            select(Mission).where(Mission.id.in_([m["id"] for m in MVP_MISSIONS]))
        )
        missions = missions_query.scalars().all()
        
        # Get user's progress
        progress_query = await self.session.execute(
            select(UserMissionEntry).where(UserMissionEntry.user_id == user_id)
        )
        user_progress = {entry.mission_id: entry for entry in progress_query.scalars().all()}
        
        # Get current user stats for dynamic progress calculation
        user = await self.session.get(User, user_id)
        user_stats = await self.session.get(UserStats, user_id)
        
        mission_status = []
        for mission in missions:
            progress_entry = user_progress.get(mission.id)
            current_progress = await self._calculate_current_progress(mission, user, user_stats)
            
            is_completed = progress_entry and progress_entry.completed
            progress_value = current_progress if not is_completed else mission.target_value
            progress_percentage = min((progress_value / mission.target_value) * 100, 100)
            
            # Diana's encouraging messages based on progress
            encouragement = self._get_diana_encouragement(mission.id, progress_percentage, is_completed)
            
            mission_status.append({
                "mission": mission,
                "current_progress": progress_value,
                "target_value": mission.target_value,
                "progress_percentage": progress_percentage,
                "is_completed": is_completed,
                "completed_at": progress_entry.completed_at if progress_entry else None,
                "diana_encouragement": encouragement,
                "reward_points": mission.reward_points
            })
            
        return mission_status
    
    async def _calculate_current_progress(self, mission: Mission, user: Optional[User], user_stats: Optional[UserStats]) -> int:
        """Calculate current progress for a mission based on its type."""
        if not user:
            return 0
            
        mission_type = mission.type
        
        if mission_type == "story_progress":
            # Count completed narrative fragments - integrate with narrative system
            # For now, use a placeholder - should integrate with narrative service
            return min(user.achievements.get("story_fragments_completed", 0), mission.target_value)
            
        elif mission_type == "decision_making":
            # Count narrative decisions made
            return min(user.achievements.get("decisions_made", 0), mission.target_value)
            
        elif mission_type == "login_streak":
            if user_stats:
                return min(user_stats.checkin_streak, mission.target_value)
            return 0
            
        elif mission_type == "channel_engagement":
            # Count channel reactions
            if user_stats:
                # This should be tracked separately in the future
                return min(user.achievements.get("channel_reactions", 0), mission.target_value)
            return 0
            
        elif mission_type == "vip_subscription":
            # Check if user has active VIP
            vip_query = await self.session.execute(
                select(func.count()).select_from(VipSubscription).where(
                    VipSubscription.user_id == user.id
                )
            )
            vip_count = vip_query.scalar() or 0
            return min(vip_count, mission.target_value)
            
        elif mission_type == "achievement_collection":
            # Count total achievements unlocked
            return min(len(user.achievements), mission.target_value)
            
        elif mission_type == "community_engagement":
            # Count community channels joined
            return min(user.achievements.get("channels_joined", 0), mission.target_value)
            
        elif mission_type == "points_accumulation":
            # Check total points
            return min(int(user.points), mission.target_value)
            
        elif mission_type == "level_achievement":
            # Check current level
            return min(user.level, mission.target_value)
            
        return 0
    
    def _get_diana_encouragement(self, mission_id: str, progress_percentage: float, is_completed: bool) -> str:
        """Get Diana's encouraging message based on mission progress."""
        if is_completed:
            # Get completion message from mission data
            mission_data = next((m for m in MVP_MISSIONS if m["id"] == mission_id), None)
            if mission_data:
                return mission_data["diana_completion_message"]
            return "¡Misión completada! Me impresionas cada día más... 💕"
        
        # Progressive encouragement messages
        if progress_percentage >= 80:
            return "Casi lo tienes, amor. Un pequeño esfuerzo más... 😘"
        elif progress_percentage >= 50:
            return "Vas muy bien, cariño. Me gusta tu dedicación. ✨"
        elif progress_percentage >= 25:
            return "Buen comienzo... Sigue así que me tienes intrigada. 😊"
        else:
            return "Empecemos juntas esta aventura... 💋"
    
    async def check_mission_completion(self, user_id: int, mission_type: str, bot: Optional[Bot] = None) -> List[Mission]:
        """Check and complete missions of a specific type."""
        await self.initialize_mvp_missions()
        
        # Get missions of this type that aren't completed yet
        missions_query = await self.session.execute(
            select(Mission).where(
                Mission.type == mission_type,
                Mission.is_active == True
            )
        )
        missions = missions_query.scalars().all()
        
        completed_missions = []
        user = await self.session.get(User, user_id)
        user_stats = await self.session.get(UserStats, user_id)
        
        if not user:
            return completed_missions
        
        for mission in missions:
            # Check if already completed
            progress_query = await self.session.execute(
                select(UserMissionEntry).where(
                    UserMissionEntry.user_id == user_id,
                    UserMissionEntry.mission_id == mission.id
                )
            )
            progress_entry = progress_query.scalar_one_or_none()
            
            if progress_entry and progress_entry.completed:
                continue
                
            # Calculate current progress
            current_progress = await self._calculate_current_progress(mission, user, user_stats)
            
            # Check if mission is now complete
            if current_progress >= mission.target_value:
                # Mark as completed
                if not progress_entry:
                    progress_entry = UserMissionEntry(
                        user_id=user_id,
                        mission_id=mission.id,
                        progress_value=current_progress,
                        completed=True,
                        completed_at=datetime.datetime.utcnow()
                    )
                    self.session.add(progress_entry)
                else:
                    progress_entry.progress_value = current_progress
                    progress_entry.completed = True
                    progress_entry.completed_at = datetime.datetime.utcnow()
                
                # Award points using the enhanced point service
                await self.point_service.award_mission_completion(user_id, mission.name, bot)
                
                completed_missions.append(mission)
                
                logger.info(f"User {user_id} completed mission '{mission.name}' ({mission.id})")
        
        if completed_missions:
            await self.session.commit()
            
        return completed_missions
    
    async def trigger_story_fragment_completion(self, user_id: int, bot: Optional[Bot] = None) -> None:
        """Trigger mission checks when user completes a story fragment."""
        # Update user's story fragment count
        user = await self.session.get(User, user_id)
        if user:
            if "story_fragments_completed" not in user.achievements:
                user.achievements["story_fragments_completed"] = 0
            user.achievements["story_fragments_completed"] += 1
            
            # Check story-related missions
            await self.check_mission_completion(user_id, "story_progress", bot)
            await self.session.commit()
    
    async def trigger_decision_made(self, user_id: int, bot: Optional[Bot] = None) -> None:
        """Trigger mission checks when user makes a narrative decision."""
        user = await self.session.get(User, user_id)
        if user:
            if "decisions_made" not in user.achievements:
                user.achievements["decisions_made"] = 0
            user.achievements["decisions_made"] += 1
            
            # Check decision-related missions
            await self.check_mission_completion(user_id, "decision_making", bot)
            await self.session.commit()
    
    async def trigger_channel_reaction(self, user_id: int, bot: Optional[Bot] = None) -> None:
        """Trigger mission checks when user reacts to channel posts."""
        user = await self.session.get(User, user_id)
        if user:
            if "channel_reactions" not in user.achievements:
                user.achievements["channel_reactions"] = 0
            user.achievements["channel_reactions"] += 1
            
            # Check channel engagement missions
            await self.check_mission_completion(user_id, "channel_engagement", bot)
            await self.session.commit()
    
    async def trigger_vip_subscription(self, user_id: int, bot: Optional[Bot] = None) -> None:
        """Trigger mission checks when user subscribes to VIP."""
        await self.check_mission_completion(user_id, "vip_subscription", bot)
    
    async def trigger_level_up(self, user_id: int, new_level: int, bot: Optional[Bot] = None) -> None:
        """Trigger mission checks when user levels up."""
        await self.check_mission_completion(user_id, "level_achievement", bot)
    
    async def trigger_points_milestone(self, user_id: int, bot: Optional[Bot] = None) -> None:
        """Trigger mission checks when user reaches points milestones."""
        await self.check_mission_completion(user_id, "points_accumulation", bot)
    
    async def get_active_mvp_missions(self) -> List[Mission]:
        """Get all active MVP missions."""
        await self.initialize_mvp_missions()
        
        missions_query = await self.session.execute(
            select(Mission).where(
                Mission.id.in_([m["id"] for m in MVP_MISSIONS]),
                Mission.is_active == True
            )
        )
        return missions_query.scalars().all()