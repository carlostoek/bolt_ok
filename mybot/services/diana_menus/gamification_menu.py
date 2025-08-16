"""
Diana Gamification Menu Module - Engaging Game Systems Interface
Provides immersive gamification experience with missions, achievements, and rewards.
"""

import logging
from typing import Dict, Any, Optional, List
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from ..coordinador_central import CoordinadorCentral, AccionUsuario
from ..point_service import PointService
from ..mission_service import MissionService
from ..achievement_service import AchievementService
from ..level_service import LevelService
from utils.message_safety import safe_edit
from utils.user_roles import get_user_role

logger = logging.getLogger(__name__)

class DianaGamificationMenu:
    """
    Diana-themed gamification menu system providing engaging game mechanics.
    Integrates points, missions, achievements, and level progression.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.coordinador = CoordinadorCentral(session)
        self.point_service = PointService(session)
        self.mission_service = MissionService(session)
        self.achievement_service = AchievementService(session)
        self.level_service = LevelService(session)
        
        # Diana-themed gamification elements
        self.gamification_themes = {
            "points": {"name": "Besitos", "icon": "💋", "description": "La moneda del amor"},
            "missions": {"name": "Desafíos", "icon": "🎯", "description": "Aventuras que Diana te propone"},
            "achievements": {"name": "Logros", "icon": "🏆", "description": "Momentos especiales conquistados"},
            "levels": {"name": "Conexión", "icon": "⭐", "description": "Tu cercanía con Diana"}
        }
    
    async def show_gamification_hub(self, callback: CallbackQuery) -> None:
        """
        Central gamification hub with comprehensive game mechanics overview.
        """
        user_id = callback.from_user.id
        bot = callback.bot
        
        try:
            # Get comprehensive gamification data
            gamif_data = await self._get_gamification_data(user_id)
            user_role = await get_user_role(bot, user_id, self.session)
            
            text = f"""
🎮 **CENTRO DE GAMIFICACIÓN - DIANA**
*Tu viaje de conquista y recompensas*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💋 **Tu Estado de Juego**
• Besitos: {gamif_data.get('points', 0)} 💋
• Nivel de Conexión: {gamif_data.get('level', 1)} ⭐
• Experiencia: {gamif_data.get('current_xp', 0)}/{gamif_data.get('xp_needed', 100)}
• Ranking: Top {gamif_data.get('ranking', 'N/A')}%

🎯 **Desafíos Activos**
• Misiones disponibles: {gamif_data.get('available_missions', 0)}
• Completadas hoy: {gamif_data.get('completed_today', 0)}
• Progreso semanal: {gamif_data.get('weekly_progress', 0)}%
• Racha de días: {gamif_data.get('streak', 0)} días

🏆 **Tus Conquistas**
• Logros desbloqueados: {gamif_data.get('achievements_unlocked', 0)}/{gamif_data.get('total_achievements', 0)}
• Insignias especiales: {gamif_data.get('special_badges', 0)}
• Próximo logro: {gamif_data.get('next_achievement', 'Aventurero')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌟 **Actividades Destacadas**
{self._get_featured_activities(gamif_data, user_role)}

📈 **Progreso de Nivel**
{self._get_level_progress_bar(gamif_data.get('current_xp', 0), gamif_data.get('xp_needed', 100))}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
💋 *Diana sonríe: "Cada desafío completado nos acerca más, mi amor..."*
            """
            
            keyboard = await self._build_gamification_hub_keyboard(user_role, gamif_data)
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer("🎮 Centro de gamificación cargado")
            
        except Exception as e:
            logger.error(f"Error showing gamification hub: {e}")
            await callback.answer("❌ Error cargando centro de gamificación", show_alert=True)
    
    async def show_missions_center(self, callback: CallbackQuery) -> None:
        """
        Comprehensive missions center with available challenges.
        """
        user_id = callback.from_user.id
        
        try:
            # Get missions data
            missions_data = await self._get_missions_data(user_id)
            
            text = f"""
🎯 **CENTRO DE DESAFÍOS**
*Las aventuras que Diana ha preparado para ti*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ **Estado de Desafíos**
• Misiones activas: {missions_data.get('active_missions', 0)}
• Completadas hoy: {missions_data.get('completed_today', 0)}
• Total completadas: {missions_data.get('total_completed', 0)}
• Éxito general: {missions_data.get('success_rate', 0)}%

💰 **Recompensas Pendientes**
• Besitos por reclamar: {missions_data.get('pending_rewards', 0)} 💋
• XP disponible: {missions_data.get('pending_xp', 0)} ⭐
• Bonus especiales: {missions_data.get('special_bonuses', 0)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **Desafíos Disponibles**
{self._format_available_missions(missions_data.get('available', []))}

🔥 **Desafíos Especiales**
{self._format_special_missions(missions_data.get('special', []))}

⏰ **Desafíos Temporales**
{self._format_timed_missions(missions_data.get('timed', []))}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Tu Rendimiento**
• Racha actual: {missions_data.get('current_streak', 0)} días
• Mejor racha: {missions_data.get('best_streak', 0)} días
• Dificultad preferida: {missions_data.get('preferred_difficulty', 'Media')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
💋 *Diana te desafía: "¿Estás listo para demostrar tu dedicación?"*
            """
            
            keyboard = await self._build_missions_center_keyboard(missions_data, user_id)
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer("🎯 Centro de desafíos cargado")
            
        except Exception as e:
            logger.error(f"Error showing missions center: {e}")
            await callback.answer("❌ Error cargando centro de desafíos", show_alert=True)
    
    async def show_achievements_gallery(self, callback: CallbackQuery) -> None:
        """
        Comprehensive achievements gallery with progress tracking.
        """
        user_id = callback.from_user.id
        
        try:
            # Get achievements data
            achievements_data = await self._get_achievements_data(user_id)
            
            text = f"""
🏆 **GALERÍA DE LOGROS**
*Tus conquistas en el mundo de Diana*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌟 **Resumen de Logros**
• Desbloqueados: {achievements_data.get('unlocked', 0)}/{achievements_data.get('total', 0)}
• Progreso: {achievements_data.get('completion_percentage', 0)}%
• Puntos de logro: {achievements_data.get('achievement_points', 0)}
• Rareza promedio: {achievements_data.get('average_rarity', 'Común')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎭 **Categorías de Logros**
💋 Romance: {achievements_data.get('romance_achievements', 0)} logros
🎯 Desafíos: {achievements_data.get('challenge_achievements', 0)} logros
📖 Historia: {achievements_data.get('story_achievements', 0)} logros
💰 Economía: {achievements_data.get('economy_achievements', 0)} logros
👑 Exclusivos: {achievements_data.get('exclusive_achievements', 0)} logros

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 **Logros Recientes**
{self._format_recent_achievements(achievements_data.get('recent', []))}

🎯 **Próximos Objetivos**
{self._format_upcoming_achievements(achievements_data.get('upcoming', []))}

💎 **Logros Épicos**
{self._format_epic_achievements(achievements_data.get('epic', []))}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
💫 *Diana celebra: "Cada logro es una muestra de nuestra conexión especial..."*
            """
            
            keyboard = await self._build_achievements_gallery_keyboard(achievements_data, user_id)
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer("🏆 Galería de logros cargada")
            
        except Exception as e:
            logger.error(f"Error showing achievements gallery: {e}")
            await callback.answer("❌ Error cargando galería de logros", show_alert=True)
    
    async def show_points_economy(self, callback: CallbackQuery) -> None:
        """
        Comprehensive points economy with earning and spending options.
        """
        user_id = callback.from_user.id
        
        try:
            # Get points economy data
            economy_data = await self._get_economy_data(user_id)
            
            text = f"""
💋 **ECONOMÍA DE BESITOS**
*El sistema monetario del amor*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **Tu Cartera**
• Besitos actuales: {economy_data.get('current_points', 0)} 💋
• Total ganados: {economy_data.get('total_earned', 0)} 💋
• Total gastados: {economy_data.get('total_spent', 0)} 💋
• Balance histórico: {economy_data.get('net_balance', 0)} 💋

📈 **Estadísticas de Ingresos**
• Ganados hoy: {economy_data.get('earned_today', 0)} 💋
• Promedio diario: {economy_data.get('daily_average', 0)} 💋
• Mejor día: {economy_data.get('best_day', 0)} 💋
• Fuente principal: {economy_data.get('main_source', 'Misiones')}

💸 **Estadísticas de Gastos**
• Gastados hoy: {economy_data.get('spent_today', 0)} 💋
• Categoría principal: {economy_data.get('main_expense', 'Decisiones')}
• Eficiencia: {economy_data.get('efficiency_score', 0)}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💫 **Formas de Ganar Besitos**
🎯 Completar misiones: +5 a +50 💋
💬 Participar en canales: +2 a +10 💋
🎁 Regalo diario: +10 a +25 💋
🏆 Desbloquear logros: +20 a +100 💋
👑 Bonificaciones VIP: +50 a +200 💋

🛍️ **En Qué Gastar**
🔮 Decisiones narrativas: -5 a -25 💋
🎁 Regalos especiales: -10 a -50 💋
🎲 Minijuegos: -5 a -15 💋
💫 Contenido exclusivo: -20 a -100 💋

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Análisis Financiero**
• Crecimiento semanal: {economy_data.get('weekly_growth', 0)}%
• Tendencia: {economy_data.get('trend', 'Estable')}
• Predicción 7 días: +{economy_data.get('predicted_growth', 0)} 💋

━━━━━━━━━━━━━━━━━━━━━━━━━━━
💋 *Diana susurra: "Los besitos son solo el comienzo de nuestro intercambio..."*
            """
            
            keyboard = await self._build_economy_keyboard(economy_data, user_id)
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer("💋 Economía de besitos cargada")
            
        except Exception as e:
            logger.error(f"Error showing points economy: {e}")
            await callback.answer("❌ Error cargando economía de besitos", show_alert=True)
    
    async def show_level_progression(self, callback: CallbackQuery) -> None:
        """
        Show level progression system with rewards and requirements.
        """
        user_id = callback.from_user.id
        
        try:
            # Get level progression data
            level_data = await self._get_level_data(user_id)
            
            text = f"""
⭐ **SISTEMA DE CONEXIÓN**
*Tu cercanía y progreso con Diana*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌟 **Tu Nivel Actual: {level_data.get('current_level', 1)}**
Título: {level_data.get('level_title', 'Admirador Secreto')}
Experiencia: {level_data.get('current_xp', 0)}/{level_data.get('xp_needed', 100)}

{self._get_detailed_level_progress_bar(level_data.get('current_xp', 0), level_data.get('xp_needed', 100))}

Progreso: {level_data.get('level_progress', 0)}%
XP para siguiente nivel: {level_data.get('xp_remaining', 0)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 **Beneficios del Nivel Actual**
{self._format_current_level_benefits(level_data.get('current_benefits', []))}

✨ **Próximo Nivel: {level_data.get('next_level', 2)}**
Título: {level_data.get('next_title', 'Compañero Íntimo')}
Nuevos beneficios:
{self._format_next_level_benefits(level_data.get('next_benefits', []))}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 **Formas de Ganar Experiencia**
🎯 Completar misiones: +10 a +50 XP
📖 Progresar en historia: +20 a +100 XP
🏆 Desbloquear logros: +30 a +150 XP
💬 Participación activa: +5 a +25 XP
🎁 Check-in diario: +10 XP

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 **Historial de Progreso**
• XP total ganada: {level_data.get('total_xp', 0)}
• Tiempo en nivel actual: {level_data.get('time_in_level', '3 días')}
• Velocidad de progreso: {level_data.get('progression_speed', 'Normal')}
• Ranking de nivel: Top {level_data.get('level_ranking', 'N/A')}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ *Diana te anima: "Cada nivel representa lo especial que eres para mí..."*
            """
            
            keyboard = await self._build_level_progression_keyboard(level_data, user_id)
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer("⭐ Sistema de conexión cargado")
            
        except Exception as e:
            logger.error(f"Error showing level progression: {e}")
            await callback.answer("❌ Error cargando sistema de conexión", show_alert=True)
    
    # ==================== HELPER METHODS ====================
    
    async def _get_gamification_data(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive gamification data."""
        try:
            # Get data from various services
            points = await self.point_service.get_user_points(user_id)
            missions = await self.mission_service.get_user_missions_summary(user_id)
            achievements = await self.achievement_service.get_user_achievements(user_id)
            
            return {
                "points": points,
                "level": 5,  # Would get from level service
                "current_xp": 350,
                "xp_needed": 500,
                "ranking": 15,
                "available_missions": missions.get("available", 0) if missions else 3,
                "completed_today": missions.get("completed_today", 0) if missions else 1,
                "weekly_progress": 75,
                "streak": 7,
                "achievements_unlocked": len(achievements) if achievements else 8,
                "total_achievements": 25,
                "special_badges": 2,
                "next_achievement": "Aventurero Constante"
            }
        except Exception as e:
            logger.error(f"Error getting gamification data: {e}")
            return {}
    
    def _get_featured_activities(self, gamif_data: Dict, user_role: str) -> str:
        """Get featured activities based on user data and role."""
        activities = []
        
        if gamif_data.get("available_missions", 0) > 0:
            activities.append("🎯 Nuevas misiones disponibles")
        
        if gamif_data.get("xp_remaining", 100) < 50:
            activities.append("⭐ Próximo a subir de nivel")
        
        if user_role == "vip":
            activities.append("👑 Misiones VIP exclusivas")
        
        return "\n".join(f"• {activity}" for activity in activities[:3])
    
    def _get_level_progress_bar(self, current_xp: int, xp_needed: int) -> str:
        """Create a visual progress bar for level progression."""
        progress = min(current_xp / xp_needed, 1.0) if xp_needed > 0 else 0
        filled = int(progress * 10)
        empty = 10 - filled
        
        bar = "█" * filled + "░" * empty
        percentage = int(progress * 100)
        
        return f"[{bar}] {percentage}%"
    
    def _get_detailed_level_progress_bar(self, current_xp: int, xp_needed: int) -> str:
        """Create a detailed progress bar with XP numbers."""
        progress = min(current_xp / xp_needed, 1.0) if xp_needed > 0 else 0
        filled = int(progress * 15)
        empty = 15 - filled
        
        bar = "▰" * filled + "▱" * empty
        
        return f"{bar}\n{current_xp}/{xp_needed} XP"
    
    async def _build_gamification_hub_keyboard(self, user_role: str, gamif_data: Dict) -> List[List[InlineKeyboardButton]]:
        """Build gamification hub keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🎯 Centro de Desafíos", callback_data="gamification_missions"),
                InlineKeyboardButton("🏆 Galería de Logros", callback_data="gamification_achievements")
            ],
            [
                InlineKeyboardButton("💋 Economía Besitos", callback_data="gamification_economy"),
                InlineKeyboardButton("⭐ Sistema Conexión", callback_data="gamification_levels")
            ],
            [
                InlineKeyboardButton("🎲 Minijuegos", callback_data="gamification_minigames"),
                InlineKeyboardButton("🛍️ Tienda Recompensas", callback_data="gamification_shop")
            ]
        ]
        
        # Add VIP section if user has access
        if user_role in ["vip", "admin"]:
            keyboard.append([
                InlineKeyboardButton("👑 Gamificación VIP", callback_data="gamification_vip")
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton("📊 Estadísticas", callback_data="gamification_stats"),
                InlineKeyboardButton("🔄 Actualizar", callback_data="user_games")
            ],
            [
                InlineKeyboardButton("◀️ Volver", callback_data="user_menu"),
                InlineKeyboardButton("❌ Cerrar", callback_data="close_menu")
            ]
        ])
        
        return keyboard
    
    async def _get_missions_data(self, user_id: int) -> Dict[str, Any]:
        """Get missions data for the user."""
        # Placeholder implementation
        return {
            "active_missions": 3,
            "completed_today": 1,
            "total_completed": 47,
            "success_rate": 92,
            "pending_rewards": 35,
            "pending_xp": 45,
            "special_bonuses": 2,
            "current_streak": 7,
            "best_streak": 12,
            "preferred_difficulty": "Media",
            "available": [
                {"title": "Interacción Diaria", "reward": "10 besitos", "difficulty": "Fácil"},
                {"title": "Maestro Conversador", "reward": "25 besitos", "difficulty": "Media"},
                {"title": "Explorador Curioso", "reward": "50 besitos", "difficulty": "Difícil"}
            ],
            "special": [
                {"title": "Fin de Semana Especial", "reward": "100 besitos + logro", "time_left": "2 días"}
            ],
            "timed": [
                {"title": "Hora Dorada", "reward": "Doble XP", "time_left": "3 horas"}
            ]
        }
    
    def _format_available_missions(self, missions: List[Dict]) -> str:
        """Format available missions for display."""
        if not missions:
            return "• No hay misiones disponibles"
        
        formatted = []
        for mission in missions[:3]:
            difficulty_emoji = {"Fácil": "🟢", "Media": "🟡", "Difícil": "🔴"}.get(mission.get("difficulty", "Media"), "🟡")
            formatted.append(f"{difficulty_emoji} {mission.get('title', 'Misión misteriosa')}")
            formatted.append(f"   Recompensa: {mission.get('reward', 'Sorpresa')}")
        
        return "\n".join(formatted)
    
    def _format_special_missions(self, missions: List[Dict]) -> str:
        """Format special missions for display."""
        if not missions:
            return "• No hay misiones especiales disponibles"
        
        formatted = []
        for mission in missions[:2]:
            formatted.append(f"🌟 {mission.get('title', 'Evento especial')}")
            formatted.append(f"   {mission.get('reward', 'Recompensa especial')} - {mission.get('time_left', 'Tiempo limitado')}")
        
        return "\n".join(formatted)
    
    def _format_timed_missions(self, missions: List[Dict]) -> str:
        """Format timed missions for display."""
        if not missions:
            return "• No hay desafíos temporales activos"
        
        formatted = []
        for mission in missions[:2]:
            formatted.append(f"⏱️ {mission.get('title', 'Desafío temporal')}")
            formatted.append(f"   {mission.get('reward', 'Bonus especial')} - {mission.get('time_left', 'Expira pronto')}")
        
        return "\n".join(formatted)
    
    async def _build_missions_center_keyboard(self, missions_data: Dict, user_id: int) -> List[List[InlineKeyboardButton]]:
        """Build missions center keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("🎯 Misiones Disponibles", callback_data="missions_available"),
                InlineKeyboardButton("✅ Misiones Completadas", callback_data="missions_completed")
            ],
            [
                InlineKeyboardButton("🌟 Misiones Especiales", callback_data="missions_special"),
                InlineKeyboardButton("⏱️ Desafíos Temporales", callback_data="missions_timed")
            ],
            [
                InlineKeyboardButton("💰 Reclamar Recompensas", callback_data="missions_claim_rewards"),
                InlineKeyboardButton("📊 Mi Rendimiento", callback_data="missions_stats")
            ],
            [
                InlineKeyboardButton("🔄 Actualizar", callback_data="gamification_missions"),
                InlineKeyboardButton("◀️ Volver", callback_data="user_games")
            ]
        ]
        
        return keyboard
    
    async def _get_achievements_data(self, user_id: int) -> Dict[str, Any]:
        """Get achievements data."""
        # Placeholder implementation  
        return {
            "unlocked": 8,
            "total": 25,
            "completion_percentage": 32,
            "achievement_points": 320,
            "average_rarity": "Poco Común",
            "romance_achievements": 3,
            "challenge_achievements": 2,
            "story_achievements": 2,
            "economy_achievements": 1,
            "exclusive_achievements": 0,
            "recent": [
                {"title": "Primera Conexión", "description": "Estableciste tu primer vínculo con Diana"},
                {"title": "Coleccionista", "description": "Desbloqueaste 5 pistas narrativas"}
            ],
            "upcoming": [
                {"title": "Aventurero", "progress": "7/10 misiones"},
                {"title": "Dedicado", "progress": "5/7 días consecutivos"}
            ],
            "epic": [
                {"title": "Alma Gemela", "description": "Logro épico - 100% historia completada"}
            ]
        }
    
    def _format_recent_achievements(self, achievements: List[Dict]) -> str:
        """Format recent achievements."""
        if not achievements:
            return "• No hay logros recientes"
        
        formatted = []
        for achievement in achievements[:3]:
            formatted.append(f"🏆 {achievement.get('title', 'Logro misterioso')}")
            formatted.append(f"   {achievement.get('description', 'Una conquista especial')}")
        
        return "\n".join(formatted)
    
    def _format_upcoming_achievements(self, achievements: List[Dict]) -> str:
        """Format upcoming achievements."""
        if not achievements:
            return "• No hay objetivos próximos definidos"
        
        return "\n".join(f"🎯 {a.get('title', 'Objetivo')}: {a.get('progress', 'En progreso')}" for a in achievements[:3])
    
    def _format_epic_achievements(self, achievements: List[Dict]) -> str:
        """Format epic achievements."""
        if not achievements:
            return "• No hay logros épicos disponibles aún"
        
        return "\n".join(f"💎 {a.get('title', 'Logro épico')}: {a.get('description', 'Una hazaña legendaria')}" for a in achievements[:2])
    
    async def _build_achievements_gallery_keyboard(self, achievements_data: Dict, user_id: int) -> List[List[InlineKeyboardButton]]:
        """Build achievements gallery keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("💋 Logros Romance", callback_data="achievements_romance"),
                InlineKeyboardButton("🎯 Logros Desafíos", callback_data="achievements_challenges")
            ],
            [
                InlineKeyboardButton("📖 Logros Historia", callback_data="achievements_story"),
                InlineKeyboardButton("💰 Logros Economía", callback_data="achievements_economy")
            ],
            [
                InlineKeyboardButton("💎 Logros Épicos", callback_data="achievements_epic"),
                InlineKeyboardButton("🎯 Mis Objetivos", callback_data="achievements_goals")
            ],
            [
                InlineKeyboardButton("📊 Estadísticas", callback_data="achievements_detailed_stats"),
                InlineKeyboardButton("🔄 Actualizar", callback_data="gamification_achievements")
            ],
            [
                InlineKeyboardButton("◀️ Volver", callback_data="user_games"),
                InlineKeyboardButton("❌ Cerrar", callback_data="close_menu")
            ]
        ]
        
        return keyboard
    
    async def _get_economy_data(self, user_id: int) -> Dict[str, Any]:
        """Get economy data."""
        # Placeholder implementation
        points = await self.point_service.get_user_points(user_id)
        
        return {
            "current_points": points,
            "total_earned": points + 150,
            "total_spent": 150,
            "net_balance": points,
            "earned_today": 25,
            "daily_average": 20,
            "best_day": 75,
            "main_source": "Misiones Diarias",
            "spent_today": 10,
            "main_expense": "Decisiones Narrativas",
            "efficiency_score": 85,
            "weekly_growth": 15,
            "trend": "Creciente",
            "predicted_growth": 140
        }
    
    async def _build_economy_keyboard(self, economy_data: Dict, user_id: int) -> List[List[InlineKeyboardButton]]:
        """Build economy keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("💰 Ganar Besitos", callback_data="economy_earn_points"),
                InlineKeyboardButton("🛍️ Gastar Besitos", callback_data="economy_spend_points")
            ],
            [
                InlineKeyboardButton("📈 Historial Ingresos", callback_data="economy_income_history"),
                InlineKeyboardButton("📉 Historial Gastos", callback_data="economy_expense_history")
            ],
            [
                InlineKeyboardButton("📊 Análisis Financiero", callback_data="economy_analysis"),
                InlineKeyboardButton("🎯 Objetivos Económicos", callback_data="economy_goals")
            ],
            [
                InlineKeyboardButton("🔄 Actualizar", callback_data="gamification_economy"),
                InlineKeyboardButton("◀️ Volver", callback_data="user_games")
            ]
        ]
        
        return keyboard
    
    async def _get_level_data(self, user_id: int) -> Dict[str, Any]:
        """Get level progression data."""
        # Placeholder implementation
        return {
            "current_level": 5,
            "level_title": "Compañero Íntimo",
            "current_xp": 350,
            "xp_needed": 500,
            "level_progress": 70,
            "xp_remaining": 150,
            "next_level": 6,
            "next_title": "Amante Apasionado",
            "current_benefits": [
                "Acceso a misiones especiales",
                "Bonificación de besitos +10%",
                "Contenido narrativo expandido"
            ],
            "next_benefits": [
                "Misiones VIP exclusivas",
                "Bonificación de besitos +15%",
                "Decisiones narrativas premium"
            ],
            "total_xp": 1850,
            "time_in_level": "5 días",
            "progression_speed": "Rápida",
            "level_ranking": 12
        }
    
    def _format_current_level_benefits(self, benefits: List[str]) -> str:
        """Format current level benefits."""
        if not benefits:
            return "• No hay beneficios especiales en este nivel"
        
        return "\n".join(f"✅ {benefit}" for benefit in benefits[:4])
    
    def _format_next_level_benefits(self, benefits: List[str]) -> str:
        """Format next level benefits."""
        if not benefits:
            return "• Información no disponible"
        
        return "\n".join(f"🆕 {benefit}" for benefit in benefits[:4])
    
    async def _build_level_progression_keyboard(self, level_data: Dict, user_id: int) -> List[List[InlineKeyboardButton]]:
        """Build level progression keyboard."""
        keyboard = [
            [
                InlineKeyboardButton("📈 Ganar Experiencia", callback_data="levels_gain_xp"),
                InlineKeyboardButton("🎁 Beneficios Nivel", callback_data="levels_benefits")
            ],
            [
                InlineKeyboardButton("🏆 Historial Niveles", callback_data="levels_history"),
                InlineKeyboardButton("📊 Ranking Global", callback_data="levels_ranking")
            ],
            [
                InlineKeyboardButton("🎯 Acelerar Progreso", callback_data="levels_boost"),
                InlineKeyboardButton("📋 Requisitos Siguientes", callback_data="levels_requirements")
            ],
            [
                InlineKeyboardButton("🔄 Actualizar", callback_data="gamification_levels"),
                InlineKeyboardButton("◀️ Volver", callback_data="user_games")
            ]
        ]
        
        return keyboard