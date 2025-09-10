"""
Daily Reward Service - Diana Bot
Manages daily besitos rewards for users with 24-hour cooldown
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.sql import func
from aiogram import Bot

from database.models import User, UserStats
from services.interfaces import IPointService, INotificationService
from services.event_bus import EventBus
import random

logger = logging.getLogger(__name__)

# Diana's daily reward configuration
DAILY_REWARD_CONFIG = {
    'base_besitos': 50,
    'vip_multiplier': 1.5,
    'cooldown_hours': 24,
    'streak_bonus_besitos': 10,  # Extra besitos for consecutive days
    'max_streak_bonus': 100  # Maximum streak bonus
}

# Diana's personality-consistent messages for daily rewards
DIANA_DAILY_MESSAGES = {
    'reward_claimed': [
        "¡Buenos días, mi amor! Aquí tienes {besitos} besitos frescos para empezar el día... ¿Los sientes ya? 💋",
        "Mmm... {besitos} besitos matutinos solo para ti, cariño. Cada día que vienes por ellos me hace sonreír... 😘",
        "¡Tu regalo diario está aquí! {besitos} besitos tiernos... ¿Sabes? Me gusta cuando vienes a buscarme cada día. 💫"
    ],
    'streak_bonus': [
        "¡Oh! Has venido {days} días seguidos... {bonus} besitos extra por tu dedicación constante, mi querido. 🔥",
        "Qué constancia... {days} días consecutivos conmigo. Te mereces {bonus} besitos adicionales por tu fidelidad. 💎",
        "¡{days} días sin faltar! Esto merece {bonus} besitos especiales... Me encanta tu perseverancia. ✨"
    ],
    'already_claimed': [
        "Ya reclamaste tus besitos hoy, mi amor... Vuelve en {hours}h {minutes}m para más. La espera los hace más dulces. 💋",
        "Paciencia, cariño... Tus próximos besitos estarán listos en {hours}h {minutes}m. Las mejores cosas requieren tiempo. 😌",
        "Mmm... ya tuviste tu ración diaria. Espera {hours}h {minutes}m más... la anticipación es parte del juego. 🌹"
    ],
    'first_claim': [
        "¡Bienvenido al ritual diario de besitos! {besitos} para comenzar... Ahora podrás reclamar estos regalos cada día. 💋✨",
        "Tu primer regalo diario: {besitos} besitos especiales. Vuelve mañana para más... así comenzamos nuestra rutina íntima. 😘",
        "¡Qué emocionante! Primer regalo: {besitos} besitos. Cada día tendrás una razón más para volver a mí... 💫"
    ]
}


class DailyRewardService:
    """
    Service for managing daily rewards with 24-hour cooldown.
    Integrates with Diana's personality and existing point system.
    """
    
    def __init__(self, 
                 session: AsyncSession,
                 point_service: IPointService,
                 notification_service: Optional[INotificationService] = None,
                 event_bus: Optional[EventBus] = None):
        """
        Initialize the daily reward service.
        
        Args:
            session: Database session
            point_service: Point service for awarding besitos
            notification_service: Optional notification service
            event_bus: Optional event bus for publishing events
        """
        self.session = session
        self.point_service = point_service
        self.notification_service = notification_service
        self.event_bus = event_bus
    
    async def claim_daily_reward(self, user_id: int, bot: Optional[Bot] = None) -> Dict:
        """
        Claim daily reward for a user.
        
        Args:
            user_id: User ID to claim reward for
            bot: Optional bot instance for notifications
            
        Returns:
            Dict with claim result containing:
            - success: bool
            - besitos: int (if successful)
            - total_besitos: int (if successful)
            - cooldown_remaining: timedelta (if on cooldown)
            - message: str
            - is_first_claim: bool
            - streak_days: int
            - streak_bonus: int
        """
        try:
            # Get or create user and stats
            user = await self._get_or_create_user(user_id)
            user_stats = await self._get_or_create_user_stats(user_id)
            
            # Check if user can claim reward
            can_claim, time_remaining = await self._can_claim_reward(user_stats)
            
            if not can_claim:
                hours = int(time_remaining.total_seconds() // 3600)
                minutes = int((time_remaining.total_seconds() % 3600) // 60)
                
                message = random.choice(DIANA_DAILY_MESSAGES['already_claimed']).format(
                    hours=hours, minutes=minutes
                )
                
                return {
                    'success': False,
                    'cooldown_remaining': time_remaining,
                    'message': message,
                    'hours_remaining': hours,
                    'minutes_remaining': minutes
                }
            
            # Determine if this is the first claim
            is_first_claim = user_stats.last_daily_gift_at is None
            
            # Calculate streak
            current_streak = await self._calculate_streak(user_stats)
            
            # Calculate reward amount
            base_besitos = DAILY_REWARD_CONFIG['base_besitos']
            
            # Apply VIP multiplier if applicable
            final_besitos = await self._apply_vip_multiplier(user, base_besitos)
            
            # Calculate streak bonus
            streak_bonus = min(
                current_streak * DAILY_REWARD_CONFIG['streak_bonus_besitos'],
                DAILY_REWARD_CONFIG['max_streak_bonus']
            )
            
            total_reward = final_besitos + streak_bonus
            
            # Award the points
            await self.point_service.add_points(
                user_id, 
                total_reward, 
                bot=bot, 
                skip_notification=True,  # We'll send our own Diana-style notification
                source="daily_reward"
            )
            
            # Update user stats and streak
            now = datetime.utcnow()
            user_stats.last_daily_gift_at = now
            
            # Update daily gift streak
            if current_streak == 0 or not hasattr(user_stats, 'daily_gift_streak'):
                user_stats.daily_gift_streak = 1
            else:
                user_stats.daily_gift_streak = current_streak + 1
                
            await self.session.commit()
            
            # Get updated total besitos
            total_besitos = await self.point_service.get_balance(user_id)
            
            # Send Diana-style notification
            await self._send_reward_notification(
                user_id, user, total_reward, total_besitos, 
                current_streak, streak_bonus, is_first_claim, bot
            )
            
            # Publish event if event bus is available
            if self.event_bus:
                await self.event_bus.publish('daily_reward_claimed', {
                    'user_id': user_id,
                    'besitos': total_reward,
                    'streak': current_streak,
                    'is_first_claim': is_first_claim
                })
            
            logger.info(f"User {user_id} claimed daily reward: {total_reward} besitos (streak: {current_streak})")
            
            return {
                'success': True,
                'besitos': int(total_reward),
                'total_besitos': int(total_besitos),
                'message': f"Has recibido {int(total_reward)} besitos diarios",
                'is_first_claim': is_first_claim,
                'streak_days': current_streak,
                'streak_bonus': streak_bonus
            }
            
        except Exception as e:
            logger.error(f"Error claiming daily reward for user {user_id}: {e}")
            return {
                'success': False,
                'message': "Hubo un error al reclamar tu regalo diario. Inténtalo más tarde."
            }
    
    async def get_reward_status(self, user_id: int) -> Dict:
        """
        Get the current reward status for a user.
        
        Args:
            user_id: User ID to check status for
            
        Returns:
            Dict with status information:
            - can_claim: bool
            - time_remaining: timedelta (if can't claim)
            - next_reward_besitos: int
            - current_streak: int
            - total_besitos: int
        """
        try:
            user = await self._get_or_create_user(user_id)
            user_stats = await self._get_or_create_user_stats(user_id)
            
            can_claim, time_remaining = await self._can_claim_reward(user_stats)
            current_streak = await self._calculate_streak(user_stats)
            
            # Calculate next reward amount
            base_besitos = DAILY_REWARD_CONFIG['base_besitos']
            next_reward = await self._apply_vip_multiplier(user, base_besitos)
            
            # Add potential streak bonus
            streak_bonus = min(
                (current_streak + 1) * DAILY_REWARD_CONFIG['streak_bonus_besitos'],
                DAILY_REWARD_CONFIG['max_streak_bonus']
            )
            
            total_besitos = await self.point_service.get_balance(user_id)
            
            return {
                'can_claim': can_claim,
                'time_remaining': time_remaining,
                'next_reward_besitos': int(next_reward + streak_bonus),
                'current_streak': current_streak,
                'total_besitos': int(total_besitos),
                'hours_remaining': int(time_remaining.total_seconds() // 3600) if time_remaining else 0,
                'minutes_remaining': int((time_remaining.total_seconds() % 3600) // 60) if time_remaining else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting reward status for user {user_id}: {e}")
            return {
                'can_claim': False,
                'time_remaining': timedelta(hours=24),
                'next_reward_besitos': DAILY_REWARD_CONFIG['base_besitos'],
                'current_streak': 0,
                'total_besitos': 0,
                'hours_remaining': 24,
                'minutes_remaining': 0
            }
    
    async def reset_daily_rewards(self) -> int:
        """
        Background task to reset daily rewards. 
        This could be called by a scheduler to clean up or handle edge cases.
        
        Returns:
            Number of users affected
        """
        try:
            # This is mainly for maintenance - the cooldown is handled per-user
            # Could be used to reset global daily limits or cleanup old data
            
            # For now, we'll just log that the reset was called
            logger.info("Daily rewards reset task executed")
            return 0
            
        except Exception as e:
            logger.error(f"Error in daily rewards reset: {e}")
            return 0
    
    async def _get_or_create_user(self, user_id: int) -> User:
        """Get or create a user record"""
        user = await self.session.get(User, user_id)
        if not user:
            user = User(id=user_id, points=0)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
        return user
    
    async def _get_or_create_user_stats(self, user_id: int) -> UserStats:
        """Get or create user stats record"""
        stats = await self.session.get(UserStats, user_id)
        if not stats:
            stats = UserStats(user_id=user_id)
            self.session.add(stats)
            await self.session.commit()
            await self.session.refresh(stats)
        return stats
    
    async def _can_claim_reward(self, user_stats: UserStats) -> Tuple[bool, Optional[timedelta]]:
        """Check if user can claim daily reward"""
        if not user_stats.last_daily_gift_at:
            return True, None
        
        now = datetime.utcnow()
        time_since_last = now - user_stats.last_daily_gift_at
        cooldown = timedelta(hours=DAILY_REWARD_CONFIG['cooldown_hours'])
        
        if time_since_last >= cooldown:
            return True, None
        else:
            time_remaining = cooldown - time_since_last
            return False, time_remaining
    
    async def _calculate_streak(self, user_stats: UserStats) -> int:
        """Calculate current daily claim streak"""
        if not user_stats.last_daily_gift_at:
            return 0
        
        now = datetime.utcnow()
        time_since_last = now - user_stats.last_daily_gift_at
        
        # If less than 48 hours (allowing some buffer), continue streak
        if time_since_last <= timedelta(hours=48):
            return getattr(user_stats, 'daily_gift_streak', 0)
        else:
            # Streak broken - reset it
            user_stats.daily_gift_streak = 0
            return 0
    
    async def _apply_vip_multiplier(self, user: User, base_besitos: float) -> float:
        """Apply VIP multiplier if user has VIP status"""
        if (user.role == "vip" and 
            user.vip_expires_at and 
            user.vip_expires_at > datetime.utcnow()):
            return base_besitos * DAILY_REWARD_CONFIG['vip_multiplier']
        return base_besitos
    
    async def _send_reward_notification(self, user_id: int, user: User, besitos: int, 
                                       total_besitos: int, streak: int, streak_bonus: int,
                                       is_first_claim: bool, bot: Optional[Bot]):
        """Send Diana-style reward notification"""
        try:
            if is_first_claim:
                message = random.choice(DIANA_DAILY_MESSAGES['first_claim']).format(
                    besitos=besitos
                )
            else:
                message = random.choice(DIANA_DAILY_MESSAGES['reward_claimed']).format(
                    besitos=besitos
                )
            
            # Add streak bonus message if applicable
            if streak > 1 and streak_bonus > 0:
                streak_message = random.choice(DIANA_DAILY_MESSAGES['streak_bonus']).format(
                    days=streak, bonus=streak_bonus
                )
                message += f"\n\n{streak_message}"
            
            # Send through notification service if available
            if self.notification_service:
                await self.notification_service.add_notification(
                    user_id,
                    "daily_reward",
                    {
                        "message": message,
                        "besitos": besitos,
                        "total_besitos": total_besitos,
                        "streak": streak,
                        "is_first_claim": is_first_claim
                    },
                    priority=2  # MEDIUM priority
                )
                logger.debug(f"Sent Diana daily reward notification to user {user_id}")
            elif bot:
                # Fallback to direct bot message
                await bot.send_message(user_id, message)
                
        except Exception as e:
            logger.error(f"Error sending daily reward notification to user {user_id}: {e}")
            # Don't raise - notification failure shouldn't break reward claiming