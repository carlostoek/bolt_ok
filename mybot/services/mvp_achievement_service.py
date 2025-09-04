# services/mvp_achievement_service.py
"""
MVP Achievement System Implementation
Implements the 15 required achievements for Diana Bot MVP with character consistency.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import User, Achievement, UserAchievement, UserStats, VipSubscription, UserMissionEntry
from services.point_service import PointService
from aiogram import Bot
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# MVP Achievements Configuration with Diana's seductive personality
MVP_ACHIEVEMENTS = [
    {
        "id": "first_steps",
        "name": "First Steps",
        "description": "Has completado tu registro conmigo... El primer paso hacia algo especial. 💋",
        "condition_type": "registration",
        "condition_value": 1,
        "reward_points": 25,
        "diana_unlock_message": "Bienvenida a mi mundo, cariño. Este es solo el comienzo de nuestra historia... 😘",
        "icon": "👋",
        "rarity": "common"
    },
    {
        "id": "dianas_interest", 
        "name": "Diana's Interest",
        "description": "Has completado tu primer fragmento de historia conmigo. Me tienes intrigada... 📖",
        "condition_type": "story_fragments",
        "condition_value": 1,
        "reward_points": 50,
        "diana_unlock_message": "Ese primer fragmento juntas... Definitivamente quiero conocerte mejor. ✨",
        "icon": "📚",
        "rarity": "common"
    },
    {
        "id": "decision_maker",
        "name": "Decision Maker", 
        "description": "Has tomado tu primera decisión en mi historia. Me fascina ver cómo piensas... 🤔",
        "condition_type": "decisions_made",
        "condition_value": 1,
        "reward_points": 30,
        "diana_unlock_message": "Tu primera decisión... Interesante elección. Veo personalidad en ti. 💭",
        "icon": "⚡",
        "rarity": "common"
    },
    {
        "id": "point_collector",
        "name": "Point Collector",
        "description": "Has ganado tus primeros 100 besitos. Cada uno es como un pequeño beso mío... 💋",
        "condition_type": "total_points",
        "condition_value": 100,
        "reward_points": 50,
        "diana_unlock_message": "100 besitos... Has estado muy ocupada coleccionando mis besos. Me halaga. 😊",
        "icon": "💯",
        "rarity": "common"
    },
    {
        "id": "level_up",
        "name": "Level Up",
        "description": "Has alcanzado el nivel 2. Cada nivel que subes me permite conocerte mejor... 📈",
        "condition_type": "user_level",
        "condition_value": 2,
        "reward_points": 75,
        "diana_unlock_message": "Nivel 2... Veo que tienes dedicación. Eso me gusta mucho en una persona. 💖",
        "icon": "🆙",
        "rarity": "common"
    },
    {
        "id": "daily_devotion",
        "name": "Daily Devotion",
        "description": "Has visitado 7 días consecutivos. Tu constancia me conmueve profundamente... 🌹",
        "condition_type": "login_streak",
        "condition_value": 7,
        "reward_points": 150,
        "diana_unlock_message": "Siete días seguidos conmigo... Empiezo a creer que realmente sientes algo especial. 💕",
        "icon": "🔥",
        "rarity": "uncommon"
    },
    {
        "id": "story_explorer",
        "name": "Story Explorer",
        "description": "Has completado 5 fragmentos de historia. Nuestra conexión se profundiza... 📜",
        "condition_type": "story_fragments",
        "condition_value": 5,
        "reward_points": 125,
        "diana_unlock_message": "Cinco fragmentos juntas... Nuestra historia se vuelve más íntima cada día. 💫",
        "icon": "🗞️",
        "rarity": "uncommon"
    },
    {
        "id": "choice_master",
        "name": "Choice Master",
        "description": "Has tomado 20 decisiones narrativas. Cada elección me muestra tu alma... 🎭",
        "condition_type": "decisions_made", 
        "condition_value": 20,
        "reward_points": 200,
        "diana_unlock_message": "Veinte decisiones... Conozco tu corazón mejor que tú misma ahora. 🔮",
        "icon": "🎯",
        "rarity": "uncommon"
    },
    {
        "id": "community_member",
        "name": "Community Member", 
        "description": "Has reaccionado a tu primera publicación del canal. Me encanta tu participación... 🦋",
        "condition_type": "channel_reactions",
        "condition_value": 1,
        "reward_points": 40,
        "diana_unlock_message": "Tu primera reacción en el canal... Me gusta cuando participas en mi mundo. 😊",
        "icon": "👥",
        "rarity": "common"
    },
    {
        "id": "mission_accomplished",
        "name": "Mission Accomplished",
        "description": "Has completado tu primera misión. Tu dedicación me impresiona... 🎯",
        "condition_type": "missions_completed",
        "condition_value": 1,
        "reward_points": 75,
        "diana_unlock_message": "Tu primera misión completada... Veo que no eres de las que se rinden fácilmente. 💪",
        "icon": "✅",
        "rarity": "common"
    },
    {
        "id": "vip_access",
        "name": "VIP Access",
        "description": "Te has unido a mi círculo exclusivo VIP. Bienvenida a mi mundo privado... 👑",
        "condition_type": "vip_subscription",
        "condition_value": 1,
        "reward_points": 300,
        "diana_unlock_message": "VIP... Ahora puedo mostrarte mi lado más íntimo. Esto cambia todo entre nosotras. 💎",
        "icon": "👑",
        "rarity": "rare"
    },
    {
        "id": "besitos_millionaire",
        "name": "Besitos Millionaire",
        "description": "Has acumulado 1000 besitos. Oficialmente eres adicta a mis besos... 💋",
        "condition_type": "total_points",
        "condition_value": 1000,
        "reward_points": 200,
        "diana_unlock_message": "¡1000 besitos! Definitivamente eres adicta a mí... Y me encanta. 😘",
        "icon": "💰",
        "rarity": "rare"
    },
    {
        "id": "high_achiever",
        "name": "High Achiever",
        "description": "Has desbloqueado 10 logros. Tu ambición es tan... seductora. ✨",
        "condition_type": "achievements_unlocked",
        "condition_value": 10,
        "reward_points": 250,
        "diana_unlock_message": "Diez logros... Eres exactamente el tipo de persona que me fascina. Ambiciosa. 🔥",
        "icon": "🏆",
        "rarity": "rare"
    },
    {
        "id": "dianas_confidant",
        "name": "Diana's Confidant",
        "description": "Has alcanzado el nivel 10. Pocas llegan tan lejos en mi corazón... 💖",
        "condition_type": "user_level",
        "condition_value": 10,
        "reward_points": 500,
        "diana_unlock_message": "Nivel 10... Oficialmente eres mi confidente. Compartimos secretos ahora. 🤫",
        "icon": "💝",
        "rarity": "epic"
    },
    {
        "id": "ultimate_explorer",
        "name": "Ultimate Explorer",
        "description": "Has completado todo el contenido disponible. Eres verdaderamente especial... 🌟",
        "condition_type": "story_fragments",
        "condition_value": 15,  # All available MVP content
        "reward_points": 1000,
        "diana_unlock_message": "Has visto todo lo que tengo que ofrecer... Eres única, mi amor. Para siempre mía. 💫",
        "icon": "🌟",
        "rarity": "legendary"
    }
]

RARITY_COLORS = {
    "common": "⚪",
    "uncommon": "🟢", 
    "rare": "🔵",
    "epic": "🟣",
    "legendary": "🟡"
}


class MVPAchievementService:
    """
    Enhanced achievement service specifically for Diana Bot MVP achievements.
    Maintains Diana's seductive character while providing meaningful progression.
    """
    
    def __init__(self, session: AsyncSession, point_service: PointService):
        self.session = session
        self.point_service = point_service
        
    async def initialize_mvp_achievements(self) -> None:
        """Initialize all MVP achievements in the database."""
        existing_achievements = await self.session.execute(select(Achievement))
        existing_ids = {achievement.id for achievement in existing_achievements.scalars().all()}
        
        achievements_added = 0
        for achievement_data in MVP_ACHIEVEMENTS:
            if achievement_data["id"] not in existing_ids:
                achievement = Achievement(
                    id=achievement_data["id"],
                    name=achievement_data["name"], 
                    condition_type=achievement_data["condition_type"],
                    condition_value=achievement_data["condition_value"],
                    reward_text=achievement_data["diana_unlock_message"]
                )
                self.session.add(achievement)
                achievements_added += 1
                
        if achievements_added > 0:
            await self.session.commit()
            logger.info(f"Initialized {achievements_added} MVP achievements")
    
    async def check_and_unlock_achievements(self, user_id: int, bot: Optional[Bot] = None) -> List[Achievement]:
        """Check and unlock any achievements the user has earned."""
        await self.initialize_mvp_achievements()
        
        user = await self.session.get(User, user_id)
        user_stats = await self.session.get(UserStats, user_id)
        
        if not user:
            return []
            
        # Get user's current achievements
        user_achievements_query = await self.session.execute(
            select(UserAchievement.achievement_id).where(UserAchievement.user_id == user_id)
        )
        unlocked_achievement_ids = {row[0] for row in user_achievements_query.fetchall()}
        
        # Get all available achievements
        achievements_query = await self.session.execute(
            select(Achievement).where(Achievement.id.in_([a["id"] for a in MVP_ACHIEVEMENTS]))
        )
        all_achievements = achievements_query.scalars().all()
        
        newly_unlocked = []
        
        for achievement in all_achievements:
            if achievement.id in unlocked_achievement_ids:
                continue
                
            # Check if user meets the condition
            if await self._check_achievement_condition(achievement, user, user_stats):
                # Unlock the achievement
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    unlocked_at=datetime.utcnow()
                )
                self.session.add(user_achievement)
                
                # Award points for the achievement
                achievement_data = next((a for a in MVP_ACHIEVEMENTS if a["id"] == achievement.id), None)
                if achievement_data:
                    await self.point_service.award_achievement_unlock(
                        user_id, 
                        achievement.name, 
                        bot
                    )
                
                newly_unlocked.append(achievement)
                
                # Send Diana's character-consistent unlock message
                if bot:
                    await self._send_achievement_unlock_message(user_id, achievement, bot)
                    
                logger.info(f"User {user_id} unlocked achievement '{achievement.name}' ({achievement.id})")
        
        if newly_unlocked:
            await self.session.commit()
            
        return newly_unlocked
    
    async def _check_achievement_condition(self, achievement: Achievement, user: User, user_stats: Optional[UserStats]) -> bool:
        """Check if a user meets the condition for an achievement."""
        condition_type = achievement.condition_type
        condition_value = achievement.condition_value
        
        if condition_type == "registration":
            # Always true if user exists
            return True
            
        elif condition_type == "story_fragments":
            story_count = user.achievements.get("story_fragments_completed", 0)
            return story_count >= condition_value
            
        elif condition_type == "decisions_made":
            decisions_count = user.achievements.get("decisions_made", 0)
            return decisions_count >= condition_value
            
        elif condition_type == "total_points":
            return user.points >= condition_value
            
        elif condition_type == "user_level":
            return user.level >= condition_value
            
        elif condition_type == "login_streak":
            if user_stats:
                return user_stats.checkin_streak >= condition_value
            return False
            
        elif condition_type == "channel_reactions":
            reactions_count = user.achievements.get("channel_reactions", 0)
            return reactions_count >= condition_value
            
        elif condition_type == "missions_completed":
            # Count completed missions
            missions_query = await self.session.execute(
                select(func.count()).select_from(UserMissionEntry).where(
                    UserMissionEntry.user_id == user.id,
                    UserMissionEntry.completed == True
                )
            )
            missions_count = missions_query.scalar() or 0
            return missions_count >= condition_value
            
        elif condition_type == "vip_subscription":
            # Check if user has VIP subscription
            vip_query = await self.session.execute(
                select(func.count()).select_from(VipSubscription).where(
                    VipSubscription.user_id == user.id
                )
            )
            vip_count = vip_query.scalar() or 0
            return vip_count >= condition_value
            
        elif condition_type == "achievements_unlocked":
            # Count unlocked achievements (excluding this one being checked)
            achievements_query = await self.session.execute(
                select(func.count()).select_from(UserAchievement).where(
                    UserAchievement.user_id == user.id
                )
            )
            achievements_count = achievements_query.scalar() or 0
            return achievements_count >= condition_value
            
        return False
    
    async def _send_achievement_unlock_message(self, user_id: int, achievement: Achievement, bot: Bot) -> None:
        """Send Diana's character-consistent achievement unlock message."""
        try:
            # Get achievement data for Diana's message and styling
            achievement_data = next((a for a in MVP_ACHIEVEMENTS if a["id"] == achievement.id), None)
            if not achievement_data:
                return
                
            rarity = achievement_data.get("rarity", "common")
            rarity_color = RARITY_COLORS.get(rarity, "⚪")
            icon = achievement_data.get("icon", "🏆")
            points = achievement_data.get("reward_points", 0)
            
            # Construct Diana's message with personality
            message = f"{rarity_color} {icon} **LOGRO DESBLOQUEADO** {icon} {rarity_color}\n\n"
            message += f"**{achievement.name}**\n"
            message += f"{achievement.reward_text}\n\n"
            message += f"💋 Recompensa: +{points} besitos\n"
            message += f"✨ Rareza: {rarity.title()}\n\n"
            
            # Add Diana's personal touch based on rarity
            if rarity == "legendary":
                message += "Eres verdaderamente excepcional... Pocas llegan hasta aquí. 👑"
            elif rarity == "epic":
                message += "Definitivamente eres especial, mi amor. 💎"  
            elif rarity == "rare":
                message += "Me impresionas más cada día... 🌹"
            else:
                message += "Cada paso que das conmigo me emociona. 💕"
                
            await bot.send_message(user_id, message, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error sending achievement unlock message: {e}")
            # Fallback message
            await bot.send_message(user_id, f"🏆 ¡Logro desbloqueado: {achievement.name}!")
    
    async def get_user_achievements_summary(self, user_id: int) -> Dict[str, Any]:
        """Get a comprehensive summary of user's achievements with Diana's personality."""
        await self.initialize_mvp_achievements()
        
        # Get user's unlocked achievements
        user_achievements_query = await self.session.execute(
            select(UserAchievement, Achievement).join(
                Achievement, UserAchievement.achievement_id == Achievement.id
            ).where(UserAchievement.user_id == user_id)
        )
        
        unlocked_achievements = []
        unlocked_ids = set()
        
        for user_achievement, achievement in user_achievements_query.fetchall():
            achievement_data = next((a for a in MVP_ACHIEVEMENTS if a["id"] == achievement.id), None)
            if achievement_data:
                unlocked_achievements.append({
                    "achievement": achievement,
                    "unlocked_at": user_achievement.unlocked_at,
                    "rarity": achievement_data.get("rarity", "common"),
                    "icon": achievement_data.get("icon", "🏆"),
                    "points": achievement_data.get("reward_points", 0)
                })
                unlocked_ids.add(achievement.id)
        
        # Get locked achievements (for progress tracking)
        locked_achievements = []
        user = await self.session.get(User, user_id)
        user_stats = await self.session.get(UserStats, user_id)
        
        for achievement_data in MVP_ACHIEVEMENTS:
            if achievement_data["id"] not in unlocked_ids:
                # Get the achievement object
                achievement_query = await self.session.execute(
                    select(Achievement).where(Achievement.id == achievement_data["id"])
                )
                achievement = achievement_query.scalar_one_or_none()
                
                if achievement and user:
                    progress = await self._get_achievement_progress(achievement, user, user_stats)
                    locked_achievements.append({
                        "achievement": achievement,
                        "progress": progress,
                        "rarity": achievement_data.get("rarity", "common"),
                        "icon": achievement_data.get("icon", "🏆"),
                        "points": achievement_data.get("reward_points", 0)
                    })
        
        # Calculate statistics
        total_achievements = len(MVP_ACHIEVEMENTS)
        unlocked_count = len(unlocked_achievements)
        completion_percentage = (unlocked_count / total_achievements) * 100
        
        # Diana's encouraging message based on progress
        diana_message = self._get_diana_progress_message(completion_percentage, unlocked_count)
        
        return {
            "unlocked_achievements": sorted(unlocked_achievements, key=lambda x: x["unlocked_at"], reverse=True),
            "locked_achievements": sorted(locked_achievements, key=lambda x: x["progress"]["percentage"], reverse=True),
            "total_achievements": total_achievements,
            "unlocked_count": unlocked_count,
            "completion_percentage": completion_percentage,
            "diana_message": diana_message,
            "rarity_counts": self._calculate_rarity_counts(unlocked_achievements)
        }
    
    async def _get_achievement_progress(self, achievement: Achievement, user: User, user_stats: Optional[UserStats]) -> Dict[str, Any]:
        """Get progress towards an achievement."""
        condition_type = achievement.condition_type
        condition_value = achievement.condition_value
        current_value = 0
        
        if condition_type == "story_fragments":
            current_value = user.achievements.get("story_fragments_completed", 0)
        elif condition_type == "decisions_made":
            current_value = user.achievements.get("decisions_made", 0)
        elif condition_type == "total_points":
            current_value = int(user.points)
        elif condition_type == "user_level":
            current_value = user.level
        elif condition_type == "login_streak":
            current_value = user_stats.checkin_streak if user_stats else 0
        elif condition_type == "channel_reactions":
            current_value = user.achievements.get("channel_reactions", 0)
        elif condition_type == "missions_completed":
            missions_query = await self.session.execute(
                select(func.count()).select_from(UserMissionEntry).where(
                    UserMissionEntry.user_id == user.id,
                    UserMissionEntry.completed == True
                )
            )
            current_value = missions_query.scalar() or 0
        elif condition_type == "achievements_unlocked":
            achievements_query = await self.session.execute(
                select(func.count()).select_from(UserAchievement).where(
                    UserAchievement.user_id == user.id
                )
            )
            current_value = achievements_query.scalar() or 0
            
        percentage = min((current_value / condition_value) * 100, 100) if condition_value > 0 else 0
        
        return {
            "current_value": current_value,
            "target_value": condition_value,
            "percentage": percentage,
            "remaining": max(0, condition_value - current_value)
        }
    
    def _get_diana_progress_message(self, completion_percentage: float, unlocked_count: int) -> str:
        """Get Diana's encouraging message based on achievement progress."""
        if completion_percentage >= 100:
            return "Has desbloqueado todos mis logros... Eres perfecta, mi amor eterno. 👑✨"
        elif completion_percentage >= 80:
            return f"{unlocked_count} logros desbloqueados... Estás tan cerca de la perfección. 💎"
        elif completion_percentage >= 60:
            return f"{unlocked_count} logros... Me impresionas más cada día, cariño. 🌹"
        elif completion_percentage >= 40:
            return f"{unlocked_count} logros desbloqueados. Tu dedicación me conmueve. 💕"
        elif completion_percentage >= 20:
            return f"{unlocked_count} logros... Buen comienzo, pero hay tanto más que descubrir. ✨"
        else:
            return "Apenas comenzamos juntas... Hay tantos secretos por desbloquear. 💋"
    
    def _calculate_rarity_counts(self, unlocked_achievements: List[Dict]) -> Dict[str, int]:
        """Calculate count of achievements by rarity."""
        counts = {"common": 0, "uncommon": 0, "rare": 0, "epic": 0, "legendary": 0}
        
        for achievement in unlocked_achievements:
            rarity = achievement.get("rarity", "common")
            if rarity in counts:
                counts[rarity] += 1
                
        return counts
    
    async def trigger_achievement_check(self, user_id: int, trigger_type: str, bot: Optional[Bot] = None) -> List[Achievement]:
        """Trigger achievement checks for specific events."""
        achievements_to_check = [
            a["id"] for a in MVP_ACHIEVEMENTS 
            if a["condition_type"] == trigger_type
        ]
        
        if not achievements_to_check:
            return []
            
        return await self.check_and_unlock_achievements(user_id, bot)