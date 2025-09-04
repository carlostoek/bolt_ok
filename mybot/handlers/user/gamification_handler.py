"""
User Gamification Handler
Critical handler for user gamification interface functionality.
Provides points display, mission tracking, achievement gallery, and level progression.
All interactions maintain Diana's character consistency and seductive personality.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from services.mvp_gamification_service import MVPGamificationService
from services.point_service import PointService
from services.level_service import LevelService
from services.mvp_mission_service import MVPMissionService
from services.mvp_achievement_service import MVPAchievementService
from services.event_bus import get_event_bus, EventType
from utils.message_safety import safe_answer, safe_edit
from utils.callback_utils import parse_callback_data
from utils.handler_decorators import safe_handler
from database.models import User, UserStats
from database.narrative_unified import UserNarrativeState

logger = logging.getLogger(__name__)
router = Router()

class GamificationStates(StatesGroup):
    """FSM States for gamification interactions."""
    viewing_achievements = State()
    tracking_missions = State()
    checking_leaderboard = State()

# ==================== MAIN GAMIFICATION DASHBOARD ====================

@router.callback_query(F.data == "user_gamification_main")
@router.message(Command("mis_besitos"))
@router.message(Command("gamificacion"))
@safe_handler
async def show_gamification_dashboard(update: Union[CallbackQuery, Message], session: AsyncSession):
    """
    Main gamification dashboard showing comprehensive user progress.
    
    Diana's personality: Seductive praise for achievements, encouraging for progress.
    Response time: <1s for optimal user experience.
    """
    user_id = update.from_user.id
    is_callback = isinstance(update, CallbackQuery)
    
    try:
        # Get comprehensive gamification data using MVP service
        gamification_service = MVPGamificationService(session)
        user_summary = await gamification_service.get_user_gamification_summary(user_id)
        
        if "error" in user_summary:
            # User not found - graceful Diana response
            message_text = """
💋 **Diana susurra seductoramente con una sonrisa enigmática:**
*"Oh, querido... Aún no hemos comenzado nuestro baile íntimo. Permíteme preparar nuestro espacio especial..."*

🌹 **BIENVENIDA A TU MUNDO GAMIFICADO CONMIGO**

Diana está configurando tu perfil personal de besitos y logros...
*Mi corazón late esperando conocerte mejor. Usa /start para comenzar nuestra aventura juntos, mi amor...*
"""
            if is_callback:
                await safe_edit(update.message, message_text)
                await update.answer("💋 Configurando tu perfil")
            else:
                await safe_answer(update, message_text)
            return
        
        # Extract user data
        user_info = user_summary.get("user_info", {})
        level_info = user_summary.get("level_info", {})
        mission_progress = user_summary.get("mission_progress", {})
        achievement_summary = user_summary.get("achievement_summary", {})
        diana_message = user_summary.get("diana_personal_message", "")
        gamification_score = user_summary.get("gamification_score", {})
        
        # Get recent activity for extra Diana flavor
        recent_activity = await _get_recent_user_activity(session, user_id)
        
        # Diana's personalized main message
        message_text = f"""
💋 **Diana te recibe con una sonrisa seductora:**
*"{diana_message}"*

🎮 **TU MUNDO DE BESITOS Y LOGROS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━

👑 **Tu Estado Actual**
• Nivel: **{user_info.get('level', 1)}** {_get_level_emoji(user_info.get('level', 1))}
• Besitos: **{user_info.get('points', 0):,}** 💰
• Logros desbloqueados: **{user_info.get('total_achievements', 0)}** 🏆

📈 **Progreso y Nivel**
• Experiencia actual: {level_info.get('current_points', 0):,}/{level_info.get('points_needed', 100):,}
• Progreso al siguiente nivel: {_calculate_level_progress(level_info):.1f}%
• Título actual: *{level_info.get('level_name', 'Principiante')}*

🎯 **Misiones Activas**
• Misiones completadas: {mission_progress.get('completed_missions', 0)}/{mission_progress.get('total_missions', 0)}
• En progreso: {_count_active_missions(mission_progress.get('missions', []))} misiones
• Besitos por reclamar: {_calculate_pending_rewards(mission_progress.get('missions', []))}

🏆 **Resumen de Logros**
• Total desbloqueados: {achievement_summary.get('unlocked_count', 0)}/{achievement_summary.get('total_count', 0)}
• Categorías dominadas: {_count_completed_categories(achievement_summary)}
• Próximo logro: {_get_next_achievement_hint(achievement_summary)}

⭐ **Puntuación de Compromiso**
• Nivel de engagement: **{gamification_score.get('engagement_level', 'Beginner')}**
• Puntuación total: {gamification_score.get('total_score', 0):,} pts
• Reacción de Diana: *"{gamification_score.get('diana_reaction', 'Apenas comenzamos...')}"*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Diana susurra:** *"¿Qué aspecto de tu progreso quieres explorar conmigo?"*
"""

        # Add recent activity flavor if available
        if recent_activity:
            message_text += f"\n💫 **Actividad Reciente:** {recent_activity}"

        # Create gamification navigation keyboard
        keyboard = await _create_gamification_keyboard(user_id, mission_progress, achievement_summary)
        
        if is_callback:
            await safe_edit(update.message, message_text, reply_markup=keyboard)
            await update.answer("🎮 Dashboard de gamificación cargado")
        else:
            await safe_answer(update, message_text, reply_markup=keyboard)
        
        # Log user engagement for analytics
        logger.info(f"User {user_id} viewed gamification dashboard - Level: {user_info.get('level', 1)}, Points: {user_info.get('points', 0)}")
        
        # Emit user activity event
        event_bus = get_event_bus()
        await event_bus.publish(
            EventType.USER_INTERACTION,
            user_id,
            {
                "action": "gamification_dashboard_view",
                "level": user_info.get('level', 1),
                "points": user_info.get('points', 0),
                "engagement_level": gamification_score.get('engagement_level', 'Beginner'),
                "timestamp": datetime.now().isoformat()
            },
            source="user_gamification_handler"
        )
        
    except Exception as e:
        logger.error(f"Error showing gamification dashboard for user {user_id}: {e}")
        error_message = """
💋 **Diana susurra disculpándose con ternura:**
*"Oh, mi querido... Un pequeño obstáculo interrumpe nuestro momento íntimo. Perdóname esta inconveniencia..."*

🔄 **Dame un momento para arreglar esto**
*Lucien coordina la solución mientras yo cuido de tu experiencia.*
Mientras tanto, puedes usar /diana para explorar otras facetas de nuestro mundo.
"""
        
        if is_callback:
            await update.answer("💋 Diana: Un momentito, amor... Lucien lo resuelve pronto", show_alert=True)
            await safe_edit(update.message, error_message)
        else:
            await safe_answer(update, error_message)

# ==================== MISSIONS CENTER ====================

@router.callback_query(F.data == "gamification_missions")
@safe_handler
async def show_missions_center(callback: CallbackQuery, session: AsyncSession):
    """
    Display detailed missions center with progress tracking.
    
    Diana's personality: Encouraging for incomplete missions, celebratory for completed ones.
    """
    user_id = callback.from_user.id
    
    try:
        # Get detailed mission data
        mission_service = MVPMissionService(session, None)  # PointService will be injected
        user_missions = await mission_service.get_user_mission_progress(user_id)
        
        # Categorize missions
        completed_missions = [m for m in user_missions if m.get("is_completed", False)]
        active_missions = [m for m in user_missions if not m.get("is_completed", False)]
        
        # Diana's missions greeting based on progress
        if len(completed_missions) > 5:
            diana_greeting = f"*\"¡{len(completed_missions)} misiones completadas! Eres absolutamente impresionante, mi amor...\"*"
        elif len(completed_missions) > 2:
            diana_greeting = f"*\"Ya {len(completed_missions)} misiones completadas... Me fascina tu dedicación.\"*"
        else:
            diana_greeting = "*\"Veamos qué aventuras te esperan, querido...\"*"
        
        message_text = f"""
🎯 **Diana revisa tus misiones con interés:**
{diana_greeting}

🌟 **CENTRO DE MISIONES PERSONALIZADO**
━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Resumen de Progreso**
• Completadas: **{len(completed_missions)}** ✅
• En progreso: **{len(active_missions)}** 🔄
• Besitos ganados: **{sum(m.get('reward_points', 0) for m in completed_missions):,}** 💰

🔥 **MISIONES ACTIVAS**
"""

        # Show active missions with Diana's commentary
        if not active_missions:
            message_text += "\n*¡Increíble! Has completado todas las misiones disponibles.*\n*Diana está preparando nuevas aventuras para ti...*"
        else:
            for i, mission in enumerate(active_missions[:5], 1):  # Show max 5 active missions
                progress_bar = _create_progress_bar(mission.get("progress", 0), mission.get("target", 100))
                diana_comment = _get_mission_diana_comment(mission)
                
                message_text += f"""
{i}. **{mission.get('title', 'Misión Misteriosa')}**
   {progress_bar} {mission.get('progress', 0)}/{mission.get('target', 100)}
   💰 Recompensa: {mission.get('reward_points', 0)} besitos
   💋 Diana: *"{diana_comment}"*
"""

        # Show recently completed missions for celebration
        recent_completed = [m for m in completed_missions if m.get('completed_recently', False)][:3]
        if recent_completed:
            message_text += f"\n🏆 **LOGROS RECIENTES**\n"
            for mission in recent_completed:
                message_text += f"✅ **{mission.get('title', 'Misión')}** - {mission.get('reward_points', 0)} besitos\n"

        message_text += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Diana susurra:** *"Cada misión te acerca más a mí... ¿Cuál conquistarás primero?"*
"""

        # Create missions keyboard
        keyboard = await _create_missions_keyboard(active_missions, completed_missions)
        
        await safe_edit(callback.message, message_text, reply_markup=keyboard)
        await callback.answer("🎯 Centro de misiones cargado")
        
        # Log mission center access
        logger.info(f"User {user_id} viewed missions center - Active: {len(active_missions)}, Completed: {len(completed_missions)}")
        
    except Exception as e:
        logger.error(f"Error showing missions center for user {user_id}: {e}")
        await callback.answer("💋 Diana suspira: Las misiones se esconden de nosotros... Dame un momento, querido.", show_alert=True)

# ==================== ACHIEVEMENTS GALLERY ====================

@router.callback_query(F.data == "gamification_achievements")
@safe_handler
async def show_achievements_gallery(callback: CallbackQuery, session: AsyncSession):
    """
    Display achievements gallery with Diana's proud commentary.
    
    Diana's personality: Proud of user's achievements, teasing about locked ones.
    """
    user_id = callback.from_user.id
    
    try:
        # Get user achievements data
        achievement_service = MVPAchievementService(session, None)  # PointService will be injected
        achievements_summary = await achievement_service.get_user_achievements_summary(user_id)
        
        unlocked_achievements = achievements_summary.get("unlocked_achievements", [])
        locked_achievements = achievements_summary.get("locked_achievements", [])
        
        # Diana's gallery greeting based on achievement count
        unlocked_count = len(unlocked_achievements)
        total_count = unlocked_count + len(locked_achievements)
        
        if unlocked_count >= 10:
            diana_greeting = f"*\"¡{unlocked_count} logros desbloqueados! Eres una leyenda en mi mundo, querido...\"*"
        elif unlocked_count >= 5:
            diana_greeting = f"*\"{unlocked_count} logros... Tu progreso me emociona más cada día.\"*"
        else:
            diana_greeting = "*\"Cada logro es un paso más cerca de conquistar mi corazón...\"*"
        
        message_text = f"""
🏆 **Diana admira tu colección de logros:**
{diana_greeting}

💎 **GALERÍA DE LOGROS PERSONAL**
━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 **Tu Progreso**
• Desbloqueados: **{unlocked_count}/{total_count}** ({(unlocked_count/max(total_count,1)*100):.1f}%)
• Besitos ganados por logros: **{sum(a.get('points_reward', 0) for a in unlocked_achievements):,}** 💰
• Categorías completadas: **{_count_achievement_categories(unlocked_achievements)}**

✨ **LOGROS DESBLOQUEADOS**
"""

        # Show unlocked achievements with Diana's proud comments
        if not unlocked_achievements:
            message_text += "\n*Tu primera gran aventura está esperando...*\n*¡Comienza explorando para desbloquear logros!*"
        else:
            # Sort by unlock date (most recent first)
            unlocked_achievements.sort(key=lambda x: x.get('unlocked_at', ''), reverse=True)
            
            for i, achievement in enumerate(unlocked_achievements[:8], 1):  # Show max 8 achievements
                rarity_emoji = _get_rarity_emoji(achievement.get('rarity', 'common'))
                unlock_date = achievement.get('unlocked_at', 'Fecha desconocida')
                if unlock_date != 'Fecha desconocida':
                    try:
                        # Format date nicely
                        unlock_date = datetime.fromisoformat(unlock_date).strftime('%d/%m/%Y')
                    except:
                        unlock_date = 'Recientemente'
                
                message_text += f"""
{rarity_emoji} **{achievement.get('title', 'Logro Misterioso')}**
   💰 +{achievement.get('points_reward', 0)} besitos | 🗓️ {unlock_date}
   *"{achievement.get('description', 'Sin descripción')}"*
"""

        # Show preview of locked achievements (teasers)
        if locked_achievements:
            message_text += f"\n🔒 **LOGROS POR DESBLOQUEAR** ({len(locked_achievements)} restantes)\n"
            # Show hints for next achievable logros
            next_achievements = sorted(locked_achievements, key=lambda x: x.get('progress', 0), reverse=True)[:3]
            
            for achievement in next_achievements:
                progress_hint = achievement.get('progress', 0)
                if progress_hint > 0:
                    message_text += f"🔮 **{achievement.get('title', '???')}** - Progreso: {progress_hint}%\n"
                else:
                    message_text += f"🔮 **???** - *Logro misterioso esperando...*\n"

        message_text += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Diana susurra con orgullo:** *"Cada logro cuenta una historia de tu dedicación... ¿Cuál será el próximo?"*
"""

        # Create achievements keyboard
        keyboard = await _create_achievements_keyboard(unlocked_count, total_count)
        
        await safe_edit(callback.message, message_text, reply_markup=keyboard)
        await callback.answer("🏆 Galería de logros cargada")
        
        # Log achievement gallery access
        logger.info(f"User {user_id} viewed achievements gallery - {unlocked_count}/{total_count} unlocked")
        
    except Exception as e:
        logger.error(f"Error showing achievements gallery for user {user_id}: {e}")
        await callback.answer("💋 Diana acaricia los logros: Tus trofeos están jugando al escondite conmigo... Paciencia, amor.", show_alert=True)

# ==================== POINTS ECONOMY ====================

@router.callback_query(F.data == "gamification_points")
@safe_handler
async def show_points_economy(callback: CallbackQuery, session: AsyncSession):
    """
    Display detailed points economy and earning opportunities.
    
    Diana's personality: Seductive about earning more points, proud of user's wealth.
    """
    user_id = callback.from_user.id
    
    try:
        # Get user points data
        point_service = PointService(session, None, None)  # Dependencies will be injected
        user = await session.get(User, user_id)
        
        if not user:
            await callback.answer("❌ Usuario no encontrado", show_alert=True)
            return
        
        current_points = int(user.points)
        
        # Get points earning opportunities
        earning_opportunities = await _get_points_earning_opportunities(session, user_id)
        
        # Diana's points greeting based on wealth level
        if current_points >= 1000:
            diana_greeting = f"*\"¡{current_points:,} besitos! Eres absolutamente rica/o en mi mundo, querida/o...\"*"
        elif current_points >= 500:
            diana_greeting = f"*\"{current_points:,} besitos... Una fortuna respetable que has ganado con dedicación.\"*"
        elif current_points >= 100:
            diana_greeting = f"*\"{current_points:,} besitos acumulados... Tu riqueza crece constantemente.\"*"
        else:
            diana_greeting = f"*\"{current_points:,} besitos... Cada uno ganado con esfuerzo. Pronto tendrás muchos más...\"*"
        
        message_text = f"""
💰 **Diana cuenta tus besitos con admiración:**
{diana_greeting}

💎 **TU ECONOMÍA DE BESITOS**
━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏦 **Balance Actual**
• Besitos totales: **{current_points:,}** 💰
• Posición en ranking: **{await _get_user_points_rank(session, user_id)}** 🏆
• Ganancia esta semana: **{await _get_weekly_points_gain(session, user_id):,}** 📈

💸 **Oportunidades de Ganancia**
"""

        # Show earning opportunities with Diana's encouragement
        for opportunity in earning_opportunities:
            availability = "✅ Disponible" if opportunity["available"] else "⏳ Próximamente"
            diana_tip = opportunity.get("diana_tip", "")
            
            message_text += f"""
{opportunity["emoji"]} **{opportunity["name"]}**
   💰 +{opportunity["points"]} besitos | {availability}
   💋 Diana: *"{diana_tip}"*
"""

        # Show spending/investment opportunities
        message_text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛍️ **Formas de Usar tus Besitos**
• 🎁 Desbloquear contenido VIP especial
• 🔮 Pistas adicionales en la narrativa
• 👑 Mejoras de perfil exclusivas
• 🎨 Personalización de experiencia

📊 **Estadísticas Interesantes**
• Besitos ganados por día: **{await _get_daily_points_average(session, user_id):.1f}** 📅
• Fuente principal: **{await _get_top_earning_source(session, user_id)}** 🎯
• Tiempo hasta próximo nivel: **{await _estimate_time_to_next_level(session, user_id)}** ⏰

━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Diana susurra seductoramente:** *"Cada besito es una prueba de nuestra conexión... ¿Cómo ganarás el próximo?"*
"""

        # Create points economy keyboard
        keyboard = await _create_points_economy_keyboard(current_points, earning_opportunities)
        
        await safe_edit(callback.message, message_text, reply_markup=keyboard)
        await callback.answer("💰 Economía de besitos cargada")
        
        # Log points economy access
        logger.info(f"User {user_id} viewed points economy - Current points: {current_points}")
        
    except Exception as e:
        logger.error(f"Error showing points economy for user {user_id}: {e}")
        await callback.answer("💋 Diana cuenta besitos: Tus preciosos besitos están siendo tímidos... Un momento, querido.", show_alert=True)

# ==================== LEVEL PROGRESSION ====================

@router.callback_query(F.data == "gamification_levels")
@safe_handler
async def show_level_progression(callback: CallbackQuery, session: AsyncSession):
    """
    Display detailed level progression and requirements.
    
    Diana's personality: Encouraging about reaching next level, proud of current achievements.
    """
    user_id = callback.from_user.id
    
    try:
        # Get user and level data
        user = await session.get(User, user_id)
        if not user:
            await callback.answer("❌ Usuario no encontrado", show_alert=True)
            return
        
        level_service = LevelService(session)
        from services.level_service import get_next_level_info
        level_info = get_next_level_info(user.points)
        
        current_level = user.level
        current_points = int(user.points)
        
        # Diana's level greeting
        if current_level >= 20:
            diana_greeting = f"*\"¡Nivel {current_level}! Eres prácticamente una diosa/o en mi mundo...\"*"
        elif current_level >= 10:
            diana_greeting = f"*\"Nivel {current_level}... Tu poder crece y me fascinas cada vez más.\"*"
        elif current_level >= 5:
            diana_greeting = f"*\"Ya nivel {current_level}... Puedo ver tu dedicación floreciendo.\"*"
        else:
            diana_greeting = f"*\"Nivel {current_level}... Cada nivel te acerca más a mí, querido...\"*"
        
        message_text = f"""
👑 **Diana contempla tu crecimiento:**
{diana_greeting}

📈 **TU PROGRESIÓN DE NIVELES**
━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎖️ **Estado Actual**
• Nivel actual: **{current_level}** {_get_level_emoji(current_level)}
• Título: *{level_info.get('current_level_name', 'Principiante')}*
• Experiencia total: **{current_points:,}** besitos 💰

🎯 **Progreso al Siguiente Nivel**
• Nivel objetivo: **{current_level + 1}** {_get_level_emoji(current_level + 1)}
• Progreso: **{level_info.get('current_points', 0):,}**/{level_info.get('points_needed', 100):,} besitos
• Porcentaje: **{_calculate_level_progress(level_info):.1f}%**
• Besitos restantes: **{level_info.get('points_needed', 100) - level_info.get('current_points', 0):,}**

{_create_progress_bar(_calculate_level_progress(level_info), 100, 20)}

🏆 **Beneficios de Subir de Nivel**
"""

        # Show level benefits
        next_level_benefits = await _get_next_level_benefits(current_level + 1)
        for benefit in next_level_benefits:
            message_text += f"• {benefit}\n"

        # Show level milestones
        milestones = await _get_upcoming_level_milestones(current_level)
        if milestones:
            message_text += f"\n🌟 **Hitos Próximos**\n"
            for milestone in milestones[:3]:
                message_text += f"• Nivel {milestone['level']}: {milestone['reward']}\n"

        message_text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Estadísticas de Progresión**
• Niveles ganados esta semana: **{await _get_weekly_level_gains(session, user_id)}**
• Promedio de besitos por día: **{await _get_daily_points_average(session, user_id):.1f}**
• Tiempo estimado al próximo nivel: **{await _estimate_time_to_next_level(session, user_id)}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Diana susurra con anticipación:** *"Cada nivel desbloqueado revela más de mi mundo... ¿Estás listo para el siguiente?"*
"""

        # Create level progression keyboard
        keyboard = await _create_level_progression_keyboard(current_level, level_info)
        
        await safe_edit(callback.message, message_text, reply_markup=keyboard)
        await callback.answer("📈 Progresión de niveles cargada")
        
        # Log level progression access
        logger.info(f"User {user_id} viewed level progression - Level: {current_level}, Points: {current_points}")
        
    except Exception as e:
        logger.error(f"Error showing level progression for user {user_id}: {e}")
        await callback.answer("💋 Diana observa tu crecimiento: Los niveles bailan esquivos hoy... Déjame alcanzarlos, amor.", show_alert=True)

# ==================== HELPER FUNCTIONS ====================

def _get_level_emoji(level: int) -> str:
    """Get emoji representation for user level."""
    if level >= 25:
        return "🏆👑"  # Legendary
    elif level >= 20:
        return "💎👑"  # Master  
    elif level >= 15:
        return "⭐👑"  # Expert
    elif level >= 10:
        return "🌟"    # Advanced
    elif level >= 5:
        return "✨"    # Intermediate
    else:
        return "🌱"    # Beginner

def _calculate_level_progress(level_info: Dict[str, Any]) -> float:
    """Calculate level progress percentage."""
    current = level_info.get('current_points', 0)
    needed = level_info.get('points_needed', 100)
    if needed <= 0:
        return 100.0
    return min((current / needed) * 100, 100.0)

def _count_active_missions(missions: List[Dict]) -> int:
    """Count active (not completed) missions."""
    return len([m for m in missions if not m.get("is_completed", False)])

def _calculate_pending_rewards(missions: List[Dict]) -> int:
    """Calculate total besitos from completed but unclaimed missions."""
    return sum(m.get('reward_points', 0) for m in missions 
              if m.get('is_completed', False) and not m.get('is_claimed', False))

def _count_completed_categories(achievement_summary: Dict) -> int:
    """Count completed achievement categories."""
    # This would need more detailed achievement category data
    # For MVP, return a placeholder
    return achievement_summary.get('completed_categories', 0)

def _get_next_achievement_hint(achievement_summary: Dict) -> str:
    """Get hint for next achievable achievement."""
    locked_achievements = achievement_summary.get('locked_achievements', [])
    if not locked_achievements:
        return "¡Todos desbloqueados!"
    
    # Find achievement with highest progress
    next_achievement = max(locked_achievements, key=lambda x: x.get('progress', 0), default={})
    return next_achievement.get('title', 'Logro misterioso')

def _create_progress_bar(progress: float, total: float, length: int = 10) -> str:
    """Create visual progress bar."""
    filled = int((progress / total) * length)
    empty = length - filled
    return f"{'█' * filled}{'░' * empty}"

def _get_mission_diana_comment(mission: Dict) -> str:
    """Get Diana's encouraging comment for a mission."""
    progress = mission.get('progress', 0)
    target = mission.get('target', 100)
    
    if progress >= target * 0.8:
        return "¡Casi lo logras! Te veo tan cerca del éxito..."
    elif progress >= target * 0.5:
        return "Vas por buen camino, me impresiona tu progreso."
    elif progress >= target * 0.2:
        return "Un buen comienzo, sigue así mi querido."
    else:
        return "Esta aventura acaba de comenzar... ¿te atreves?"

def _get_rarity_emoji(rarity: str) -> str:
    """Get emoji for achievement rarity."""
    rarity_map = {
        'legendary': '👑',
        'epic': '💎',
        'rare': '⭐',
        'uncommon': '🌟',
        'common': '✨'
    }
    return rarity_map.get(rarity.lower(), '✨')

def _count_achievement_categories(achievements: List[Dict]) -> int:
    """Count unique achievement categories."""
    categories = set(a.get('category', 'general') for a in achievements)
    return len(categories)

async def _get_recent_user_activity(session: AsyncSession, user_id: int) -> str:
    """Get recent user activity summary."""
    # This would integrate with activity tracking
    # For MVP, return a placeholder
    return "Última actividad hoy - Muy activo"

async def _get_points_earning_opportunities(session: AsyncSession, user_id: int) -> List[Dict[str, Any]]:
    """Get available points earning opportunities."""
    # In a full implementation, this would check user's current state
    # and return personalized opportunities
    return [
        {
            "name": "Continuar Historia",
            "points": 10,
            "emoji": "📖",
            "available": True,
            "diana_tip": "Cada capítulo desvela más de mi mundo..."
        },
        {
            "name": "Check-in Diario",
            "points": 15,
            "emoji": "📅",
            "available": True,
            "diana_tip": "Tu constancia me conmueve, querido."
        },
        {
            "name": "Reaccionar en Canal",
            "points": 2,
            "emoji": "❤️",
            "available": True,
            "diana_tip": "Cada reacción es una caricia para mí."
        },
        {
            "name": "Completar Misión",
            "points": 25,
            "emoji": "🎯",
            "available": True,
            "diana_tip": "Las misiones revelan tu verdadero carácter."
        }
    ]

async def _get_user_points_rank(session: AsyncSession, user_id: int) -> str:
    """Get user's ranking position."""
    # This would need a ranking system implementation
    return "Top 100"

async def _get_weekly_points_gain(session: AsyncSession, user_id: int) -> int:
    """Get points gained this week."""
    # This would need activity tracking
    return 150

async def _get_daily_points_average(session: AsyncSession, user_id: int) -> float:
    """Get average daily points."""
    # This would need historical data
    return 21.5

async def _get_top_earning_source(session: AsyncSession, user_id: int) -> str:
    """Get top earning source."""
    return "Progreso narrativo"

async def _estimate_time_to_next_level(session: AsyncSession, user_id: int) -> str:
    """Estimate time to reach next level."""
    return "3-4 días"

async def _get_next_level_benefits(level: int) -> List[str]:
    """Get benefits for reaching the next level."""
    benefits = {
        2: ["🔓 Acceso a contenido exclusivo", "💬 Mensajes personalizados de Diana"],
        5: ["🎨 Personalización de perfil", "🔮 Pistas adicionales"],
        10: ["👑 Título VIP temporal", "🎁 Bonificaciones especiales"],
        15: ["💎 Acceso premium", "🏆 Reconocimiento especial"],
        20: ["👑 Estatus de leyenda", "🌟 Contenido ultra-exclusivo"]
    }
    return benefits.get(level, ["🌟 Beneficios especiales por desbloquear"])

async def _get_upcoming_level_milestones(current_level: int) -> List[Dict[str, Any]]:
    """Get upcoming level milestones."""
    milestones = []
    next_milestones = [5, 10, 15, 20, 25]
    
    for milestone in next_milestones:
        if milestone > current_level:
            milestones.append({
                "level": milestone,
                "reward": f"Recompensa especial nivel {milestone}"
            })
    
    return milestones[:3]

async def _get_weekly_level_gains(session: AsyncSession, user_id: int) -> int:
    """Get levels gained this week."""
    return 1  # Placeholder

# ==================== KEYBOARD FUNCTIONS ====================

async def _create_gamification_keyboard(user_id: int, mission_progress: Dict, achievement_summary: Dict):
    """Create main gamification navigation keyboard."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    # Main sections with dynamic indicators
    active_missions = _count_active_missions(mission_progress.get('missions', []))
    unlocked_achievements = achievement_summary.get('unlocked_count', 0)
    
    builder.button(text=f"🎯 Misiones ({active_missions} activas)", callback_data="gamification_missions")
    builder.button(text=f"🏆 Logros ({unlocked_achievements})", callback_data="gamification_achievements")
    
    builder.button(text="💰 Mis Besitos", callback_data="gamification_points") 
    builder.button(text="📈 Mi Nivel", callback_data="gamification_levels")
    
    builder.button(text="📊 Estadísticas", callback_data="gamification_stats")
    builder.button(text="🎮 Ranking", callback_data="gamification_leaderboard")
    
    # Navigation
    builder.button(text="🔄 Actualizar", callback_data="user_gamification_main")
    builder.button(text="🏠 Menú Diana", callback_data="user_menu")
    
    builder.adjust(2, 2, 2, 2)
    return builder.as_markup()

async def _create_missions_keyboard(active_missions: List, completed_missions: List):
    """Create missions center keyboard."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    if active_missions:
        builder.button(text="🎯 Ver Misión Activa", callback_data="mission_details_active")
        builder.button(text="⚡ Acciones Rápidas", callback_data="mission_quick_actions")
    
    if completed_missions:
        builder.button(text="✅ Misiones Completadas", callback_data="missions_completed_list")
        builder.button(text="🎁 Reclamar Recompensas", callback_data="missions_claim_rewards")
    
    builder.button(text="📈 Progreso Detallado", callback_data="missions_detailed_progress")
    builder.button(text="🔄 Actualizar", callback_data="gamification_missions")
    builder.button(text="🔙 Volver", callback_data="user_gamification_main")
    
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

async def _create_achievements_keyboard(unlocked_count: int, total_count: int):
    """Create achievements gallery keyboard."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    if unlocked_count > 0:
        builder.button(text="✨ Ver Detalles de Logros", callback_data="achievements_details")
        builder.button(text="📈 Progreso por Categoría", callback_data="achievements_categories")
    
    builder.button(text="🔮 Pistas de Logros", callback_data="achievements_hints")
    builder.button(text="🏆 Próximos Logros", callback_data="achievements_upcoming")
    
    builder.button(text="🔄 Actualizar", callback_data="gamification_achievements")  
    builder.button(text="🔙 Volver", callback_data="user_gamification_main")
    
    builder.adjust(2, 2, 2)
    return builder.as_markup()

async def _create_points_economy_keyboard(current_points: int, earning_opportunities: List):
    """Create points economy keyboard."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    # Quick earning actions
    available_opportunities = [opp for opp in earning_opportunities if opp["available"]]
    if available_opportunities:
        builder.button(text="⚡ Ganar Besitos Ahora", callback_data="points_quick_earn")
    
    builder.button(text="📊 Historial Detallado", callback_data="points_history")
    builder.button(text="🏆 Ranking de Besitos", callback_data="points_leaderboard")
    
    if current_points >= 100:
        builder.button(text="🛍️ Gastar Besitos", callback_data="points_spend")
    
    builder.button(text="📈 Estadísticas", callback_data="points_statistics")
    builder.button(text="🔄 Actualizar", callback_data="gamification_points")
    builder.button(text="🔙 Volver", callback_data="user_gamification_main")
    
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

async def _create_level_progression_keyboard(current_level: int, level_info: Dict):
    """Create level progression keyboard."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    builder.button(text="🎖️ Historia de Niveles", callback_data="levels_history")
    builder.button(text="🏆 Beneficios de Nivel", callback_data="levels_benefits")
    
    builder.button(text="⚡ Formas de Subir Nivel", callback_data="levels_earning_tips")
    builder.button(text="📊 Comparar con Otros", callback_data="levels_comparison")
    
    builder.button(text="🎯 Objetivos de Nivel", callback_data="levels_goals")
    builder.button(text="🔄 Actualizar", callback_data="gamification_levels")
    builder.button(text="🔙 Volver", callback_data="user_gamification_main")
    
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()

# ==================== ROUTER SETUP ====================

def setup_user_gamification_handlers(dp):
    """
    Configure user gamification handlers in the dispatcher.
    
    Args:
        dp: Aiogram message dispatcher
    """
    dp.include_router(router)
    logger.info("User gamification handlers configured successfully")
    return router