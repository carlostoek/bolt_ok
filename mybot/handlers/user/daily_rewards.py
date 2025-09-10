"""
Daily Rewards Handler - Diana Bot
Handles /regalo command and daily reward management for users.
Maintains Diana's seductive personality and character consistency.
"""

import logging
from datetime import datetime, timedelta
from typing import Union, Dict, Any
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from services.daily_reward_service import DailyRewardService
from services.point_service import PointService
from services.level_service import LevelService
from services.mvp_achievement_service import MVPAchievementService
from services.notification_service import NotificationService
from services.event_bus import get_event_bus, EventType
from utils.message_safety import safe_answer, safe_edit
from utils.handler_decorators import safe_handler
from database.models import User, UserStats

logger = logging.getLogger(__name__)
router = Router()

# ==================== MAIN DAILY REWARD COMMAND ====================

@router.message(Command("regalo"))
@router.callback_query(F.data == "daily_reward_claim")
@safe_handler
async def handle_daily_reward_claim(update: Union[Message, CallbackQuery], session: AsyncSession):
    """
    Handle daily reward claim with Diana's seductive personality.
    Supports both command and callback query triggers.
    """
    user_id = update.from_user.id
    is_callback = isinstance(update, CallbackQuery)
    
    try:
        # Initialize services
        point_service = PointService(session, None, None)
        level_service = LevelService(session)
        achievement_service = MVPAchievementService(session, point_service)
        notification_service = NotificationService(session, None)  # Bot will be injected
        event_bus = get_event_bus()
        
        daily_reward_service = DailyRewardService(
            session=session,
            point_service=point_service,
            notification_service=notification_service,
            event_bus=event_bus
        )
        
        # Attempt to claim the daily reward
        result = await daily_reward_service.claim_daily_reward(user_id, update.bot)
        
        if result['success']:
            # Successful claim - Diana's celebration
            besitos = result['besitos']
            total_besitos = result['total_besitos']
            streak = result['streak_days']
            is_first_claim = result['is_first_claim']
            streak_bonus = result.get('streak_bonus', 0)
            
            # Create Diana's celebratory message
            if is_first_claim:
                title = "🎁 **¡TU PRIMER REGALO DIARIO CON DIANA!**"
                diana_intro = "*Diana sonríe con ternura mientras te entrega tu primer regalo...*"
            else:
                title = "🎁 **¡REGALO DIARIO RECLAMADO!**"
                diana_intro = "*Diana te susurra seductoramente mientras cuenta tus besitos...*"
            
            message_text = f"""
{title}
{diana_intro}

💋 **Recompensa de Diana**
━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Besitos recibidos: **+{besitos}** 💰
• Total acumulado: **{total_besitos:,}** besitos
• Racha actual: **{streak} días** {"🔥" if streak > 1 else "✨"}
"""

            if streak_bonus > 0:
                message_text += f"• Bonificación por racha: **+{streak_bonus}** besitos 🎯\n"
            
            message_text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌹 **Mensaje Personal de Diana:**
*"{result['message']}"*

⏰ **Próximo Regalo:** Disponible en **24 horas**
*Vuelve mañana para continuar nuestra rutina íntima...*

💫 **¿Sabías que...?**
• Los usuarios VIP reciben **50% más besitos** en sus regalos diarios
• Las rachas largas desbloquean bonificaciones especiales
• Diana prepara sorpresas especiales para usuarios dedicados
"""

            # Create keyboard for post-claim actions
            keyboard = _create_post_claim_keyboard(total_besitos, streak)
            
            if is_callback:
                await safe_edit(update.message, message_text, reply_markup=keyboard)
                await update.answer(f"🎁 ¡+{besitos} besitos recibidos!")
            else:
                await safe_answer(update, message_text, reply_markup=keyboard)
            
            # Log successful claim
            logger.info(f"User {user_id} claimed daily reward: {besitos} besitos (streak: {streak})")
            
        else:
            # Already claimed or on cooldown - Diana's gentle reminder
            cooldown_remaining = result.get('cooldown_remaining')
            hours = result.get('hours_remaining', 0)
            minutes = result.get('minutes_remaining', 0)
            
            message_text = f"""
🎁 **Diana te acaricia suavemente:**
*"{result['message']}"*

⏰ **Tiempo Restante para el Próximo Regalo**
━━━━━━━━━━━━━━━━━━━━━━━━━━━
🕐 **{hours}h {minutes}m** hasta tu próximo regalo

💭 **Mientras Esperas...**
• Explora la narrativa para ganar más besitos
• Completa misiones para obtener recompensas inmediatas  
• Reacciona en los canales para besitos adicionales
• Visita el menú de gamificación para ver tu progreso

🌹 **Diana susurra:**
*"La anticipación hace que el regalo sea aún más dulce, mi querido..."*

💡 **Consejo:** Los usuarios VIP obtienen bonificaciones especiales en todos los regalos diarios.
"""

            # Create keyboard for alternative actions
            keyboard = _create_cooldown_keyboard()
            
            if is_callback:
                await safe_edit(update.message, message_text, reply_markup=keyboard)
                await update.answer(f"⏰ Próximo regalo en {hours}h {minutes}m", show_alert=True)
            else:
                await safe_answer(update, message_text, reply_markup=keyboard)
            
            # Log cooldown attempt
            logger.info(f"User {user_id} attempted daily reward on cooldown: {hours}h {minutes}m remaining")
        
        # Emit interaction event
        await event_bus.publish(
            EventType.USER_INTERACTION,
            user_id,
            {
                "action": "daily_reward_attempt",
                "success": result['success'],
                "besitos_claimed": result.get('besitos', 0),
                "timestamp": datetime.now().isoformat()
            },
            source="daily_rewards_handler"
        )
        
    except Exception as e:
        logger.error(f"Error handling daily reward for user {user_id}: {e}")
        error_message = """
💋 **Diana suspira con disculpa:**
*"Oh, mi querido... Algo interrumpe nuestro momento especial. Dame un instante para solucionarlo..."*

🔄 **Error Temporal**
Lucien está resolviendo este pequeño inconveniente.
Intenta nuevamente en unos momentos con /regalo

💌 **Mientras tanto:** Puedes explorar otras funciones con /diana
"""
        
        if is_callback:
            await update.answer("💋 Diana: Un momentito, amor... Resolviendo el inconveniente", show_alert=True)
            await safe_edit(update.message, error_message)
        else:
            await safe_answer(update, error_message)

# ==================== REWARD STATUS COMMAND ====================

@router.message(Command("estado_regalo"))
@router.callback_query(F.data == "daily_reward_status")
@safe_handler
async def handle_daily_reward_status(update: Union[Message, CallbackQuery], session: AsyncSession):
    """
    Show current daily reward status and information.
    """
    user_id = update.from_user.id
    is_callback = isinstance(update, CallbackQuery)
    
    try:
        # Initialize services
        point_service = PointService(session, None, None)
        daily_reward_service = DailyRewardService(session, point_service)
        
        # Get current reward status
        status = await daily_reward_service.get_reward_status(user_id)
        
        can_claim = status['can_claim']
        next_reward = status['next_reward_besitos']
        current_streak = status['current_streak']
        total_besitos = status['total_besitos']
        hours_remaining = status['hours_remaining']
        minutes_remaining = status['minutes_remaining']
        
        if can_claim:
            # Reward is available
            message_text = f"""
🎁 **¡TU REGALO DIARIO ESTÁ LISTO!**
*Diana te espera con una sonrisa seductora...*

✨ **Regalo Disponible**
━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Besitos disponibles: **{next_reward}** 💰
• Tu racha actual: **{current_streak} días** {"🔥" if current_streak > 1 else "✨"}
• Tus besitos actuales: **{total_besitos:,}** 💎

💋 **Diana susurra:**
*"Tu regalo me espera aquí, querido... Solo di la palabra y será tuyo."*

🎯 **¿Sabías que...?**
• Mantener una racha te da bonificaciones especiales
• Los usuarios VIP reciben 50% más besitos
• Cada regalo fortalece tu conexión con Diana
"""
            keyboard = _create_available_reward_keyboard()
            
        else:
            # On cooldown
            message_text = f"""
⏰ **ESTADO DE TU REGALO DIARIO**
*Diana acaricia suavemente tu mejilla mientras esperas...*

🕐 **Próximo Regalo**
━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Tiempo restante: **{hours_remaining}h {minutes_remaining}m**
• Besitos que recibirás: **{next_reward}** 💰
• Tu racha actual: **{current_streak} días** {"🔥" if current_streak > 1 else "✨"}
• Tus besitos actuales: **{total_besitos:,}** 💎

🌹 **Diana susurra:**
*"Cada hora que pasa me hace desearte más... La espera intensifica el regalo."*

💫 **Mientras Esperas:**
• Continúa la narrativa para más besitos
• Completa misiones diarias
• Reacciona en los canales
• Explora el mundo de Diana
"""
            keyboard = _create_status_keyboard()
        
        message_text += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **Consejo de Diana:** *"La constancia es la clave de todos mis secretos..."*
"""
        
        if is_callback:
            await safe_edit(update.message, message_text, reply_markup=keyboard)
            await update.answer("📊 Estado de regalo actualizado")
        else:
            await safe_answer(update, message_text, reply_markup=keyboard)
        
        # Log status check
        logger.info(f"User {user_id} checked daily reward status - Can claim: {can_claim}, Streak: {current_streak}")
        
    except Exception as e:
        logger.error(f"Error checking daily reward status for user {user_id}: {e}")
        error_message = """
💋 **Diana frunce ligeramente el ceño:**
*"Algo oculta el estado de tu regalo, mi amor... Dame un momento para revelarlo."*

🔍 **Verificando...**
Lucien está revisando tu estado de recompensas.
Intenta nuevamente con /estado_regalo

💌 **Alternativa:** Usa /regalo para intentar reclamar directamente.
"""
        
        if is_callback:
            await update.answer("💋 Verificando estado...", show_alert=True)
            await safe_edit(update.message, error_message)
        else:
            await safe_answer(update, error_message)

# ==================== CALLBACK HANDLERS ====================

@router.callback_query(F.data == "daily_reward_info")
@safe_handler
async def show_daily_reward_info(callback: CallbackQuery, session: AsyncSession):
    """
    Show detailed information about the daily reward system.
    """
    try:
        message_text = """
🎁 **SISTEMA DE REGALOS DIARIOS DE DIANA**
*Todo lo que necesitas saber sobre nuestros momentos íntimos...*

💋 **¿Cómo Funciona?**
━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Cada 24 horas puedes reclamar un regalo especial
• Usa /regalo para reclamar tu recompensa diaria
• Mantén una racha para bonificaciones adicionales
• Los regalos se reinician exactamente 24h después del último reclamo

💰 **Recompensas Base**
• Usuarios normales: **50 besitos** diarios
• Usuarios VIP: **75 besitos** diarios (50% bonus)
• Bonificación por racha: **+10 besitos** por día consecutivo
• Máximo bonus por racha: **+100 besitos**

🔥 **Sistema de Rachas**
• Día 1: Sin bonus
• Día 2-7: +10 besitos por día de racha
• Día 8+: +10 besitos + bonificaciones especiales
• La racha se rompe si no reclamas por más de 48 horas

👑 **Beneficios VIP**
• 50% más besitos en cada regalo
• Notificaciones exclusivas de Diana
• Acceso a regalos especiales en eventos
• Mensajes personalizados únicos

🌟 **Consejos de Diana**
• Reclama a la misma hora cada día para crear rutina
• Las rachas largas desbloquean sorpresas especiales
• Combina con otras actividades para maximizar besitos
• Los regalos son solo el comienzo de nuestra conexión...

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💫 **Diana susurra:** *"Cada regalo es una promesa de que nuestro vínculo crece cada día..."*
"""
        
        keyboard = _create_info_keyboard()
        await safe_edit(callback.message, message_text, reply_markup=keyboard)
        await callback.answer("📖 Información cargada")
        
    except Exception as e:
        logger.error(f"Error showing daily reward info: {e}")
        await callback.answer("💋 Diana: La información se esconde de nosotros... Intenta de nuevo", show_alert=True)

@router.callback_query(F.data == "daily_reward_leaderboard")
@safe_handler
async def show_daily_reward_leaderboard(callback: CallbackQuery, session: AsyncSession):
    """
    Show leaderboard of users with longest daily reward streaks.
    """
    try:
        # This would need implementation of streak tracking and leaderboard
        message_text = """
🏆 **TABLA DE RACHAS DIARIAS**
*Los más dedicados en el mundo de Diana...*

🔥 **Top Rachas Actuales**
━━━━━━━━━━━━━━━━━━━━━━━━━━━
1️⃣ Usuario Mítico: **127 días** 👑
2️⃣ Devoto Leal: **89 días** 💎
3️⃣ Admirador Constante: **76 días** ⭐
4️⃣ Seguidor Fiel: **45 días** 🌟
5️⃣ Usuario Dedicado: **32 días** ✨

🎯 **Tu Posición:** En desarrollo...

🌹 **Diana observa:**
*"Cada día de consistencia me impresiona más... ¿Hasta dónde llegará tu dedicación?"*

💫 **Premios Especiales por Rachas:**
• 30 días: Título especial de Diana
• 60 días: Acceso a contenido exclusivo
• 90 días: Reconocimiento personal de Diana
• 365 días: Estatus de leyenda eterna

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **Próximamente:** Sistema completo de rankings y competencias.
"""
        
        keyboard = _create_leaderboard_keyboard()
        await safe_edit(callback.message, message_text, reply_markup=keyboard)
        await callback.answer("🏆 Leaderboard cargado")
        
    except Exception as e:
        logger.error(f"Error showing daily reward leaderboard: {e}")
        await callback.answer("💋 Diana: El ranking se oculta... Dame un momento", show_alert=True)

# ==================== KEYBOARD FUNCTIONS ====================

def _create_post_claim_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard after successful reward claim."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📊 Ver Mi Estado", callback_data="daily_reward_status")
    builder.button(text="🏆 Ver Rachas", callback_data="daily_reward_leaderboard")
    builder.button(text="🎮 Gamificación", callback_data="user_gamification_main")
    builder.button(text="📖 Continuar Historia", callback_data="user_narrative_menu")
    builder.button(text="💫 Menú Diana", callback_data="user_menu")
    
    builder.adjust(2, 2, 1)
    return builder.as_markup()

def _create_cooldown_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard when reward is on cooldown."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="⏰ Ver Estado", callback_data="daily_reward_status")
    builder.button(text="💡 Información", callback_data="daily_reward_info")
    builder.button(text="🎮 Gamificación", callback_data="user_gamification_main")
    builder.button(text="📖 Narrativa", callback_data="user_narrative_menu")
    builder.button(text="💎 Upgrade VIP", callback_data="vip_subscription_menu")
    builder.button(text="🏠 Menú Diana", callback_data="user_menu")
    
    builder.adjust(2, 2, 2)
    return builder.as_markup()

def _create_available_reward_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard when reward is available."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🎁 ¡RECLAMAR REGALO!", callback_data="daily_reward_claim")
    builder.button(text="💡 Información", callback_data="daily_reward_info")
    builder.button(text="🏆 Ver Rachas", callback_data="daily_reward_leaderboard")
    builder.button(text="🏠 Menú Diana", callback_data="user_menu")
    
    builder.adjust(1, 2, 1)
    return builder.as_markup()

def _create_status_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for status display."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🔄 Actualizar", callback_data="daily_reward_status")
    builder.button(text="💡 Información", callback_data="daily_reward_info")
    builder.button(text="🎮 Gamificación", callback_data="user_gamification_main")
    builder.button(text="🏠 Menú Diana", callback_data="user_menu")
    
    builder.adjust(2, 2)
    return builder.as_markup()

def _create_info_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for info display."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🎁 Mi Regalo", callback_data="daily_reward_status")
    builder.button(text="🏆 Rachas", callback_data="daily_reward_leaderboard")
    builder.button(text="💎 Ser VIP", callback_data="vip_subscription_menu")
    builder.button(text="🔙 Volver", callback_data="daily_reward_status")
    
    builder.adjust(2, 2)
    return builder.as_markup()

def _create_leaderboard_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for leaderboard display."""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🎁 Mi Regalo", callback_data="daily_reward_status")
    builder.button(text="💡 Información", callback_data="daily_reward_info")
    builder.button(text="🔄 Actualizar", callback_data="daily_reward_leaderboard")
    builder.button(text="🔙 Volver", callback_data="daily_reward_status")
    
    builder.adjust(2, 2)
    return builder.as_markup()

# ==================== ROUTER SETUP ====================

def setup_daily_rewards_handlers(dp):
    """
    Configure daily rewards handlers in the dispatcher.
    
    Args:
        dp: Aiogram message dispatcher
    """
    dp.include_router(router)
    logger.info("Daily rewards handlers configured successfully")
    return router