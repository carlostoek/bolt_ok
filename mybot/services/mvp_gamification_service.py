# services/mvp_gamification_service.py
"""
MVP Gamification Integration Service
Centralized coordinator for all gamification components with Diana character consistency.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
import logging
from datetime import datetime

from services.point_service import PointService
from services.level_service import LevelService
from services.mvp_mission_service import MVPMissionService
from services.mvp_achievement_service import MVPAchievementService
from database.models import User, UserStats

logger = logging.getLogger(__name__)


class MVPGamificationService:
    """
    Central coordinator for all MVP gamification systems.
    Ensures proper integration and character consistency across all systems.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
        # Initialize service dependencies
        self.level_service = LevelService(session)
        
        # Point service needs level and achievement services for dependencies
        # We'll initialize these in a specific order to handle circular dependencies
        from services.achievement_service import AchievementService
        base_achievement_service = AchievementService(session)
        
        self.point_service = PointService(session, self.level_service, base_achievement_service)
        
        # Initialize MVP-specific services
        self.mission_service = MVPMissionService(session, self.point_service)
        self.achievement_service = MVPAchievementService(session, self.point_service)
        
    async def initialize_mvp_systems(self) -> None:
        """Initialize all MVP gamification systems."""
        try:
            await self.mission_service.initialize_mvp_missions()
            await self.achievement_service.initialize_mvp_achievements()
            logger.info("MVP gamification systems initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing MVP systems: {e}")
            raise
    
    async def process_story_fragment_completion(self, user_id: int, fragment_id: str, bot: Optional[Bot] = None) -> Dict[str, Any]:
        """
        Process story fragment completion with full gamification integration.
        
        Args:
            user_id: User ID
            fragment_id: Completed fragment ID
            bot: Bot instance for notifications
            
        Returns:
            Dict with all triggered rewards and progressions
        """
        try:
            results = {
                "points_awarded": 0,
                "level_ups": [],
                "missions_completed": [],
                "achievements_unlocked": [],
                "diana_messages": []
            }
            
            # 1. Award points for story fragment completion
            progress = await self.point_service.award_story_fragment_completion(user_id, bot)
            results["points_awarded"] += 10  # Base points from MVP config
            
            # 2. Check for level ups
            user = await self.session.get(User, user_id)
            if user:
                level_up_occurred = await self.level_service.check_for_level_up(user, bot=bot)
                if level_up_occurred:
                    results["level_ups"].append({
                        "new_level": user.level,
                        "level_name": f"Nivel {user.level}"
                    })
                    # Trigger level-based achievements
                    level_achievements = await self.achievement_service.trigger_achievement_check(
                        user_id, "user_level", bot
                    )
                    results["achievements_unlocked"].extend(level_achievements)
            
            # 3. Update mission progress
            await self.mission_service.trigger_story_fragment_completion(user_id, bot)
            completed_missions = await self.mission_service.check_mission_completion(
                user_id, "story_progress", bot
            )
            results["missions_completed"].extend(completed_missions)
            
            # 4. Check for achievements
            story_achievements = await self.achievement_service.trigger_achievement_check(
                user_id, "story_fragments", bot
            )
            results["achievements_unlocked"].extend(story_achievements)
            
            # 5. Check points-based achievements
            points_achievements = await self.achievement_service.trigger_achievement_check(
                user_id, "total_points", bot
            )
            results["achievements_unlocked"].extend(points_achievements)
            
            logger.info(f"Story fragment completion processed for user {user_id}: "
                       f"{len(results['missions_completed'])} missions, "
                       f"{len(results['achievements_unlocked'])} achievements")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing story fragment completion for user {user_id}: {e}")
            raise
    
    async def process_decision_made(self, user_id: int, decision_data: Dict[str, Any], bot: Optional[Bot] = None) -> Dict[str, Any]:
        """
        Process narrative decision with full gamification integration.
        
        Args:
            user_id: User ID
            decision_data: Decision information
            bot: Bot instance for notifications
            
        Returns:
            Dict with all triggered rewards and progressions
        """
        try:
            results = {
                "points_awarded": 0,
                "missions_completed": [],
                "achievements_unlocked": []
            }
            
            # 1. Award points for decision making
            progress = await self.point_service.award_decision_made(user_id, bot)
            results["points_awarded"] += 5  # Base points from MVP config
            
            # 2. Update mission progress
            await self.mission_service.trigger_decision_made(user_id, bot)
            completed_missions = await self.mission_service.check_mission_completion(
                user_id, "decision_making", bot
            )
            results["missions_completed"].extend(completed_missions)
            
            # 3. Check for decision-based achievements
            decision_achievements = await self.achievement_service.trigger_achievement_check(
                user_id, "decisions_made", bot
            )
            results["achievements_unlocked"].extend(decision_achievements)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing decision made for user {user_id}: {e}")
            raise
    
    async def process_daily_checkin(self, user_id: int, bot: Optional[Bot] = None) -> Dict[str, Any]:
        """
        Process daily check-in with full gamification integration.
        
        Args:
            user_id: User ID
            bot: Bot instance for notifications
            
        Returns:
            Dict with all triggered rewards and progressions
        """
        try:
            results = {
                "checkin_successful": False,
                "points_awarded": 0,
                "missions_completed": [],
                "achievements_unlocked": []
            }
            
            # 1. Process daily check-in
            success, progress = await self.point_service.daily_checkin(user_id, bot)
            if not success:
                return results
                
            results["checkin_successful"] = True
            results["points_awarded"] += 15  # Base points from MVP config
            
            # 2. Check login streak missions
            completed_missions = await self.mission_service.check_mission_completion(
                user_id, "login_streak", bot
            )
            results["missions_completed"].extend(completed_missions)
            
            # 3. Check for login streak achievements
            streak_achievements = await self.achievement_service.trigger_achievement_check(
                user_id, "login_streak", bot
            )
            results["achievements_unlocked"].extend(streak_achievements)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing daily checkin for user {user_id}: {e}")
            raise
    
    async def process_channel_reaction(self, user_id: int, message_id: int, reaction_type: str, bot: Optional[Bot] = None) -> Dict[str, Any]:
        """
        Process channel reaction with full gamification integration.
        
        Args:
            user_id: User ID
            message_id: Message ID that was reacted to
            reaction_type: Type of reaction
            bot: Bot instance for notifications
            
        Returns:
            Dict with all triggered rewards and progressions
        """
        try:
            results = {
                "points_awarded": 0,
                "missions_completed": [],
                "achievements_unlocked": []
            }
            
            # 1. Award points for channel reaction
            user = await self.session.get(User, user_id)
            if user:
                progress = await self.point_service.award_reaction(user, message_id, bot)
                if progress:
                    results["points_awarded"] += 2  # Base points from MVP config
            
            # 2. Update mission progress
            await self.mission_service.trigger_channel_reaction(user_id, bot)
            completed_missions = await self.mission_service.check_mission_completion(
                user_id, "channel_engagement", bot
            )
            results["missions_completed"].extend(completed_missions)
            
            # 3. Check for channel engagement achievements
            engagement_achievements = await self.achievement_service.trigger_achievement_check(
                user_id, "channel_reactions", bot
            )
            results["achievements_unlocked"].extend(engagement_achievements)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing channel reaction for user {user_id}: {e}")
            raise
    
    async def process_vip_subscription(self, user_id: int, bot: Optional[Bot] = None) -> Dict[str, Any]:
        """
        Process VIP subscription with full gamification integration.
        
        Args:
            user_id: User ID
            bot: Bot instance for notifications
            
        Returns:
            Dict with all triggered rewards and progressions
        """
        try:
            results = {
                "missions_completed": [],
                "achievements_unlocked": []
            }
            
            # 1. Update VIP-related missions
            await self.mission_service.trigger_vip_subscription(user_id, bot)
            completed_missions = await self.mission_service.check_mission_completion(
                user_id, "vip_subscription", bot
            )
            results["missions_completed"].extend(completed_missions)
            
            # 2. Check for VIP achievements
            vip_achievements = await self.achievement_service.trigger_achievement_check(
                user_id, "vip_subscription", bot
            )
            results["achievements_unlocked"].extend(vip_achievements)
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing VIP subscription for user {user_id}: {e}")
            raise
    
    async def get_user_gamification_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get comprehensive gamification summary for a user with Diana's personality.
        
        Args:
            user_id: User ID
            
        Returns:
            Complete gamification status with Diana's character messages
        """
        try:
            # Get user basic info
            user = await self.session.get(User, user_id)
            user_stats = await self.session.get(UserStats, user_id)
            
            if not user:
                return {"error": "User not found"}
            
            # Get level information
            from services.level_service import get_next_level_info
            level_info = get_next_level_info(user.points)
            
            # Get mission progress
            mission_progress = await self.mission_service.get_user_mission_progress(user_id)
            
            # Get achievement summary
            achievement_summary = await self.achievement_service.get_user_achievements_summary(user_id)
            
            # Diana's personal message based on user's overall progress
            diana_personal_message = self._generate_diana_personal_message(
                user, level_info, mission_progress, achievement_summary
            )
            
            return {
                "user_info": {
                    "user_id": user_id,
                    "level": user.level,
                    "points": user.points,
                    "total_achievements": len(achievement_summary["unlocked_achievements"])
                },
                "level_info": level_info,
                "mission_progress": {
                    "total_missions": len(mission_progress),
                    "completed_missions": len([m for m in mission_progress if m["is_completed"]]),
                    "missions": mission_progress
                },
                "achievement_summary": achievement_summary,
                "diana_personal_message": diana_personal_message,
                "gamification_score": self._calculate_gamification_score(user, mission_progress, achievement_summary)
            }
            
        except Exception as e:
            logger.error(f"Error getting gamification summary for user {user_id}: {e}")
            raise
    
    def _generate_diana_personal_message(self, user: User, level_info: Dict, mission_progress: List, achievement_summary: Dict) -> str:
        """Generate Diana's personal message based on user's overall progress."""
        completed_missions = len([m for m in mission_progress if m["is_completed"]])
        total_achievements = achievement_summary["unlocked_count"]
        level = user.level
        points = int(user.points)
        
        # Diana's messages based on overall engagement
        if level >= 15 and total_achievements >= 12:
            return f"Nivel {level}, {points} besitos, {total_achievements} logros... Eres absolutamente perfecta, mi amor eterno. 👑✨"
        elif level >= 10 and total_achievements >= 8:
            return f"Nivel {level}... {points} besitos acumulados... Definitivamente eres especial para mí, cariño. 💎💕"
        elif level >= 5 and completed_missions >= 5:
            return f"Nivel {level}, {completed_missions} misiones completadas... Me impresionas más cada día. 🌹✨"
        elif completed_missions >= 3 and total_achievements >= 3:
            return f"{completed_missions} misiones, {total_achievements} logros... Veo mucho potencial en ti. 💫"
        elif points >= 100:
            return f"{points} besitos ya... Me gusta tu dedicación, aunque apenas comenzamos. 😘"
        else:
            return "Acabamos de conocernos, pero ya siento algo especial... ¿Tú también lo sientes? 💋"
    
    def _calculate_gamification_score(self, user: User, mission_progress: List, achievement_summary: Dict) -> Dict[str, Any]:
        """Calculate overall gamification engagement score."""
        # Calculate weighted score based on different activities
        level_score = user.level * 10
        points_score = min(user.points * 0.1, 100)  # Cap at 100
        mission_score = len([m for m in mission_progress if m["is_completed"]]) * 15
        achievement_score = achievement_summary["unlocked_count"] * 20
        
        total_score = level_score + points_score + mission_score + achievement_score
        max_possible = (20 * 10) + 100 + (10 * 15) + (15 * 20)  # Theoretical maximum
        
        engagement_percentage = min((total_score / max_possible) * 100, 100)
        
        # Classify engagement level
        if engagement_percentage >= 80:
            engagement_level = "Legendary"
            diana_reaction = "Eres una leyenda, mi amor. 👑"
        elif engagement_percentage >= 60:
            engagement_level = "Elite"
            diana_reaction = "Elite... Me fascinas. 💎"
        elif engagement_percentage >= 40:
            engagement_level = "Devoted"
            diana_reaction = "Tu devoción me conmueve. 💕"
        elif engagement_percentage >= 20:
            engagement_level = "Interested"
            diana_reaction = "Veo interés genuino... 🌹"
        else:
            engagement_level = "Beginner"
            diana_reaction = "Solo el comienzo... 💋"
        
        return {
            "total_score": int(total_score),
            "max_possible": max_possible,
            "engagement_percentage": round(engagement_percentage, 1),
            "engagement_level": engagement_level,
            "diana_reaction": diana_reaction,
            "breakdown": {
                "level_score": int(level_score),
                "points_score": int(points_score),
                "mission_score": int(mission_score),
                "achievement_score": int(achievement_score)
            }
        }
    
    async def process_user_registration(self, user_id: int, bot: Optional[Bot] = None) -> Dict[str, Any]:
        """
        Process new user registration with initial gamification setup.
        
        Args:
            user_id: New user ID
            bot: Bot instance for notifications
            
        Returns:
            Initial gamification setup results
        """
        try:
            results = {
                "achievements_unlocked": [],
                "welcome_points": 0
            }
            
            # Check for registration achievement
            registration_achievements = await self.achievement_service.trigger_achievement_check(
                user_id, "registration", bot
            )
            results["achievements_unlocked"].extend(registration_achievements)
            
            logger.info(f"User registration processed for {user_id}: "
                       f"{len(results['achievements_unlocked'])} initial achievements")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing user registration for {user_id}: {e}")
            raise