"""
Diana User Menu Module - Unified User Experience
Provides seamless navigation across narrative, gamification, and VIP features.
"""

import logging
from typing import Dict, Any, Optional
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from ..coordinador_central import CoordinadorCentral, AccionUsuario
from ..point_service import PointService
from ..narrative_service import NarrativeService
from ..mission_service import MissionService
from ..achievement_service import AchievementService
from ..user_service import UserService
from utils.message_safety import safe_edit
from utils.user_roles import get_user_role

logger = logging.getLogger(__name__)

class DianaUserMenu:
    """
    Diana-themed user menu system providing integrated experience across all modules.
    Focuses on user engagement and seamless navigation between features.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.coordinador = CoordinadorCentral(session)
        self.point_service = PointService(session)
        self.narrative_service = NarrativeService(session)
        self.mission_service = MissionService(session)
        self.achievement_service = AchievementService(session)
        self.user_service = UserService(session)
    
    async def show_main_user_menu(self, callback: CallbackQuery) -> None:
        """
        Main user menu with personalized Diana experience.
        """
        user_id = callback.from_user.id
        bot = callback.bot
        
        try:
            # Get comprehensive user data
            user_data = await self._get_integrated_user_data(user_id)
            user_role = await get_user_role(bot, user_id, self.session)
            character = await self._get_active_character(user_id)
            
            # Dynamic greeting based on user progress and time
            greeting = await self._get_personalized_greeting(user_id, character)
            
            text = f"""
💋 **{character.upper()} - {greeting}**
*Tu mundo de secretos y pasión te espera*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 **Tu Estado Actual**
• Nivel: {user_data.get('level', 1)} ⭐
• Besitos: {user_data.get('points', 0)} 💋
• Estado: {self._get_status_emoji(user_role)} {user_role.upper()}

📖 **Tu Historia Personal**
• Progreso: {user_data.get('narrative_progress', 0)}% completado
• Capítulo: {user_data.get('current_chapter', 'Prólogo')}
• Pistas encontradas: {user_data.get('hints_unlocked', 0)}

🎮 **Tus Logros**
• Misiones completadas: {user_data.get('completed_missions', 0)}
• Logros desbloqueados: {user_data.get('achievements', 0)}
• Racha de días: {user_data.get('streak_days', 0)} días

━━━━━━━━━━━━━━━━━━━━━━━━━━━

✨ **¿Qué deseas explorar hoy?**
{self._get_personalized_suggestions(user_data, user_role)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
💫 *{character.title()} susurra: "Cada momento contigo es una nueva aventura..."*
            """
            
            keyboard = await self._build_main_menu_keyboard(user_role, user_data)
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer(f"💋 Bienvenido de vuelta...")
            
        except Exception as e:
            logger.error(f"Error showing main user menu: {e}")
            await callback.answer("❌ Error cargando tu menú personal", show_alert=True)
    
    async def show_user_profile(self, callback: CallbackQuery) -> None:
        """
        Comprehensive user profile with integrated progress from all modules.
        """
        user_id = callback.from_user.id
        bot = callback.bot
        
        try:
            user_data = await self._get_integrated_user_data(user_id)
            user_role = await get_user_role(bot, user_id, self.session)
            engagement_score = await self._calculate_engagement_score(user_data)
            
            text = f"""
👤 **PERFIL DE {callback.from_user.first_name}**
*Tu viaje completo en el mundo de Diana*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎭 **Información Personal**
• ID: {user_id}
• Nombre: {callback.from_user.first_name}
• Estado: {self._get_status_emoji(user_role)} {user_role.upper()}
• Miembro desde: {user_data.get('member_since', 'Recientemente')}

📊 **Estadísticas de Engagement**
• Puntuación general: {engagement_score}/100 ⭐
• Nivel de actividad: {self._get_activity_level(engagement_score)}
• Ranking aproximado: Top {self._get_ranking_estimate(engagement_score)}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **Economía Personal**
• Besitos actuales: {user_data.get('points', 0)} 💋
• Total ganados: {user_data.get('total_earned_points', 0)} 💋
• Total gastados: {user_data.get('spent_points', 0)} 💋
• Eficiencia: {self._calculate_efficiency(user_data)}%

📖 **Progreso Narrativo**
• Historia completada: {user_data.get('narrative_progress', 0)}% 📚
• Capítulo actual: {user_data.get('current_chapter', 'Prólogo')}
• Pistas desbloqueadas: {user_data.get('hints_unlocked', 0)} 🗝️
• Decisiones importantes: {user_data.get('decisions_made', 0)} 🔮

🎮 **Logros en Gamificación**
• Nivel actual: {user_data.get('level', 1)} ⭐
• Misiones completadas: {user_data.get('completed_missions', 0)} 🎯
• Logros conseguidos: {user_data.get('achievements', 0)} 🏆
• Días consecutivos: {user_data.get('streak_days', 0)} 📅

━━━━━━━━━━━━━━━━━━━━━━━━━━━
💋 *Diana sonríe: "Cada paso que das me acerca más a ti..."*
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("📊 Estadísticas Detalladas", callback_data="profile_detailed_stats"),
                    InlineKeyboardButton("🏆 Mis Logros", callback_data="profile_my_achievements")
                ],
                [
                    InlineKeyboardButton("📖 Mi Historia", callback_data="profile_narrative_summary"),
                    InlineKeyboardButton("🎮 Progreso Juegos", callback_data="profile_gamification_summary")
                ],
                [
                    InlineKeyboardButton("💰 Historial Puntos", callback_data="profile_points_history"),
                    InlineKeyboardButton("📈 Mi Progreso", callback_data="profile_progress_chart")
                ],
                [
                    InlineKeyboardButton("⚙️ Configuración", callback_data="profile_settings"),
                    InlineKeyboardButton("🔄 Actualizar", callback_data="user_profile")
                ],
                [
                    InlineKeyboardButton("◀️ Volver", callback_data="user_menu"),
                    InlineKeyboardButton("❌ Cerrar", callback_data="close_menu")
                ]
            ]
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer("👤 Tu perfil completo")
            
        except Exception as e:
            logger.error(f"Error showing user profile: {e}")
            await callback.answer("❌ Error cargando perfil", show_alert=True)
    
    async def show_daily_activities(self, callback: CallbackQuery) -> None:
        """
        Daily activities hub with missions, gifts, and challenges.
        """
        user_id = callback.from_user.id
        
        try:
            # Get daily activity data
            daily_data = await self._get_daily_activity_data(user_id)
            
            text = f"""
🌅 **ACTIVIDADES DIARIAS - DIANA**
*Tu rutina diaria de seducción y aventura*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎁 **Regalo Diario**
Estado: {daily_data.get('daily_gift_status', '✅ Disponible')}
Racha: {daily_data.get('streak_days', 0)} días consecutivos
Próximo bonus: {daily_data.get('next_bonus', 'En 2 días')}

🎯 **Misiones de Hoy**
Disponibles: {daily_data.get('available_missions', 0)}
Completadas: {daily_data.get('completed_today', 0)}
Progreso: {daily_data.get('daily_progress', 0)}%

⚡ **Actividades Rápidas**
• Check-in diario: {daily_data.get('checkin_status', '⏳ Pendiente')}
• Interacción canales: {daily_data.get('channel_activity', '⏳ Pendiente')}
• Trivia diaria: {daily_data.get('trivia_status', '⏳ Disponible')}

🏆 **Bonificaciones Especiales**
• Bonus de fin de semana: {daily_data.get('weekend_bonus', 'No disponible')}
• Evento especial: {daily_data.get('special_event', 'No hay eventos')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💋 **Recompensas de Hoy**
Besitos ganados: {daily_data.get('points_earned_today', 0)} 💋
XP obtenida: {daily_data.get('xp_earned_today', 0)} ⭐

━━━━━━━━━━━━━━━━━━━━━━━━━━━
*Diana te anima: "Cada día es una oportunidad para crecer juntos..."*
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("🎁 Reclamar Regalo", callback_data="daily_claim_gift"),
                    InlineKeyboardButton("🎯 Ver Misiones", callback_data="daily_view_missions")
                ],
                [
                    InlineKeyboardButton("⚡ Check-in Rápido", callback_data="daily_quick_checkin"),
                    InlineKeyboardButton("🧩 Trivia Diaria", callback_data="daily_trivia")
                ],
                [
                    InlineKeyboardButton("📈 Mi Progreso", callback_data="daily_progress_view"),
                    InlineKeyboardButton("🏆 Ranking Diario", callback_data="daily_ranking")
                ],
                [
                    InlineKeyboardButton("◀️ Volver", callback_data="user_menu"),
                    InlineKeyboardButton("❌ Cerrar", callback_data="close_menu")
                ]
            ]
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer("🌅 Actividades diarias cargadas")
            
        except Exception as e:
            logger.error(f"Error showing daily activities: {e}")
            await callback.answer("❌ Error cargando actividades diarias", show_alert=True)
    
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

📊 **Resumen de Logros**
• Desbloqueados: {achievements_data.get('unlocked', 0)}/{achievements_data.get('total', 0)}
• Progreso total: {achievements_data.get('completion_percentage', 0)}%
• Puntos de logros: {achievements_data.get('achievement_points', 0)}

🎭 **Categorías**
📖 Narrativa: {achievements_data.get('narrative_achievements', 0)} logros
🎮 Gamificación: {achievements_data.get('gamification_achievements', 0)} logros
💰 Economía: {achievements_data.get('economy_achievements', 0)} logros
👑 VIP: {achievements_data.get('vip_achievements', 0)} logros
🔥 Especiales: {achievements_data.get('special_achievements', 0)} logros

━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌟 **Logros Recientes**
{self._format_recent_achievements(achievements_data.get('recent', []))}

🎯 **Próximos Objetivos**
{self._format_next_achievements(achievements_data.get('next_goals', []))}

━━━━━━━━━━━━━━━━━━━━━━━━━━━
💫 *Diana celebra: "Cada logro tuyo es una victoria compartida..."*
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("📖 Logros Narrativa", callback_data="achievements_narrative"),
                    InlineKeyboardButton("🎮 Logros Gamificación", callback_data="achievements_gamification")
                ],
                [
                    InlineKeyboardButton("💰 Logros Economía", callback_data="achievements_economy"),
                    InlineKeyboardButton("👑 Logros VIP", callback_data="achievements_vip")
                ],
                [
                    InlineKeyboardButton("🔥 Logros Especiales", callback_data="achievements_special"),
                    InlineKeyboardButton("📊 Estadísticas", callback_data="achievements_stats")
                ],
                [
                    InlineKeyboardButton("🎯 Objetivos", callback_data="achievements_goals"),
                    InlineKeyboardButton("🔄 Actualizar", callback_data="achievements_refresh")
                ],
                [
                    InlineKeyboardButton("◀️ Volver", callback_data="user_menu"),
                    InlineKeyboardButton("❌ Cerrar", callback_data="close_menu")
                ]
            ]
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer("🏆 Galería de logros cargada")
            
        except Exception as e:
            logger.error(f"Error showing achievements gallery: {e}")
            await callback.answer("❌ Error cargando galería de logros", show_alert=True)
    
    # ==================== HELPER METHODS ====================
    
    async def _get_integrated_user_data(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user data from all modules."""
        try:
            # Get base user data
            user = await self.user_service.get_user(user_id)
            points = await self.point_service.get_user_points(user_id)
            
            # Get narrative progress
            current_fragment = await self.narrative_service.get_user_current_fragment(user_id)
            narrative_progress = await self._calculate_narrative_progress(user_id)
            
            # Get gamification data
            missions = await self.mission_service.get_user_missions_summary(user_id)
            achievements = await self.achievement_service.get_user_achievements(user_id)
            
            return {
                "level": getattr(user, 'level', 1) if user else 1,
                "points": points,
                "narrative_progress": narrative_progress,
                "current_chapter": current_fragment.title if current_fragment else "Prólogo",
                "hints_unlocked": narrative_progress // 10,
                "decisions_made": narrative_progress // 5,
                "completed_missions": missions.get("completed", 0) if missions else 0,
                "achievements": len(achievements) if achievements else 0,
                "streak_days": getattr(user, 'streak_days', 0) if user else 0,
                "member_since": "Hace 2 semanas",  # Would calculate from user.created_at
                "total_earned_points": points + 200,  # Would get from point history
                "spent_points": 50  # Would get from spending history
            }
            
        except Exception as e:
            logger.error(f"Error getting integrated user data: {e}")
            return {}
    
    async def _get_active_character(self, user_id: int) -> str:
        """Determine active character based on narrative progress."""
        try:
            current_fragment = await self.narrative_service.get_user_current_fragment(user_id)
            # Logic to determine character - for now default to Diana
            return "diana"
        except Exception:
            return "diana"
    
    async def _get_personalized_greeting(self, user_id: int, character: str) -> str:
        """Get personalized greeting based on user activity and time."""
        import datetime
        hour = datetime.datetime.now().hour
        
        if character == "diana":
            if 6 <= hour < 12:
                return "Buenos días, mi amor"
            elif 12 <= hour < 18:
                return "Buenas tardes, cariño"
            elif 18 <= hour < 22:
                return "Buenas noches, mi seductor"
            else:
                return "Hora de secretos nocturnos"
        else:
            return "Lucien te da la bienvenida"
    
    def _get_status_emoji(self, user_role: str) -> str:
        """Get status emoji for user role."""
        return {"admin": "👑", "vip": "💎", "free": "🆓"}.get(user_role, "🆓")
    
    def _get_personalized_suggestions(self, user_data: Dict, user_role: str) -> str:
        """Get personalized activity suggestions."""
        suggestions = []
        
        if user_data.get("narrative_progress", 0) < 50:
            suggestions.append("📖 Continúa tu historia personal")
        
        if user_data.get("completed_missions", 0) < 5:
            suggestions.append("🎯 Completa misiones para ganar besitos")
        
        if user_role == "free":
            suggestions.append("👑 Descubre el contenido VIP exclusivo")
        
        return "\n".join(f"• {s}" for s in suggestions[:3])
    
    async def _build_main_menu_keyboard(self, user_role: str, user_data: Dict) -> list:
        """Build main menu keyboard based on user role and progress."""
        keyboard = [
            [
                InlineKeyboardButton("👤 Mi Perfil", callback_data="user_profile"),
                InlineKeyboardButton("📖 Mi Historia", callback_data="user_narrative")
            ],
            [
                InlineKeyboardButton("🎯 Misiones", callback_data="user_missions"),
                InlineKeyboardButton("🏆 Logros", callback_data="user_achievements")
            ],
            [
                InlineKeyboardButton("🌅 Actividades Diarias", callback_data="user_daily_activities"),
                InlineKeyboardButton("🛍️ Tienda", callback_data="user_shop")
            ]
        ]
        
        # Add VIP section if user has access
        if user_role in ["vip", "admin"]:
            keyboard.append([
                InlineKeyboardButton("👑 Contenido VIP", callback_data="user_vip_content")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton("💎 Hazte VIP", callback_data="user_upgrade_vip")
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton("🔄 Actualizar", callback_data="user_refresh"),
                InlineKeyboardButton("❌ Cerrar", callback_data="close_menu")
            ]
        ])
        
        return keyboard
    
    async def _calculate_engagement_score(self, user_data: Dict) -> int:
        """Calculate user engagement score."""
        narrative_score = user_data.get("narrative_progress", 0) * 0.4
        mission_score = min(user_data.get("completed_missions", 0) * 10, 100) * 0.3
        achievement_score = min(user_data.get("achievements", 0) * 5, 100) * 0.2
        activity_score = min(user_data.get("streak_days", 0) * 2, 100) * 0.1
        
        return int(narrative_score + mission_score + achievement_score + activity_score)
    
    def _get_activity_level(self, engagement_score: int) -> str:
        """Get activity level description."""
        if engagement_score >= 80:
            return "🔥 Muy Activo"
        elif engagement_score >= 60:
            return "⚡ Activo"
        elif engagement_score >= 40:
            return "🌟 Moderado"
        else:
            return "💤 Casual"
    
    def _get_ranking_estimate(self, engagement_score: int) -> int:
        """Estimate user ranking based on engagement."""
        if engagement_score >= 90:
            return 5
        elif engagement_score >= 80:
            return 10
        elif engagement_score >= 70:
            return 20
        elif engagement_score >= 60:
            return 30
        else:
            return 50
    
    def _calculate_efficiency(self, user_data: Dict) -> int:
        """Calculate point spending efficiency."""
        earned = user_data.get("total_earned_points", 1)
        spent = user_data.get("spent_points", 0)
        return int((spent / earned) * 100) if earned > 0 else 0
    
    async def _calculate_narrative_progress(self, user_id: int) -> int:
        """Calculate narrative completion percentage."""
        try:
            current_fragment = await self.narrative_service.get_user_current_fragment(user_id)
            if current_fragment:
                # Simple progress calculation based on fragment key
                if "level1" in current_fragment.key:
                    return 20
                elif "level2" in current_fragment.key:
                    return 40
                elif "level3" in current_fragment.key:
                    return 60
                elif "level4" in current_fragment.key:
                    return 80
                elif "level5" in current_fragment.key:
                    return 100
            return 0
        except Exception:
            return 0
    
    async def _get_daily_activity_data(self, user_id: int) -> Dict[str, Any]:
        """Get daily activity data for the user."""
        # Placeholder implementation
        return {
            "daily_gift_status": "✅ Disponible",
            "streak_days": 5,
            "next_bonus": "En 2 días",
            "available_missions": 3,
            "completed_today": 1,
            "daily_progress": 33,
            "checkin_status": "✅ Completado",
            "channel_activity": "⏳ Pendiente",
            "trivia_status": "⏳ Disponible",
            "weekend_bonus": "No disponible",
            "special_event": "No hay eventos",
            "points_earned_today": 25,
            "xp_earned_today": 15
        }
    
    async def _get_achievements_data(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive achievements data."""
        # Placeholder implementation
        return {
            "unlocked": 8,
            "total": 25,
            "completion_percentage": 32,
            "achievement_points": 120,
            "narrative_achievements": 3,
            "gamification_achievements": 3,
            "economy_achievements": 1,
            "vip_achievements": 0,
            "special_achievements": 1,
            "recent": [
                {"name": "Primera Historia", "description": "Completaste tu primer fragmento"},
                {"name": "Coleccionista", "description": "Desbloqueaste 5 pistas"}
            ],
            "next_goals": [
                {"name": "Aventurero", "description": "Completa 10 misiones", "progress": "7/10"},
                {"name": "Dedicado", "description": "7 días consecutivos", "progress": "5/7"}
            ]
        }
    
    def _format_recent_achievements(self, achievements: list) -> str:
        """Format recent achievements for display."""
        if not achievements:
            return "• No hay logros recientes"
        
        return "\n".join(f"🏆 {a['name']}: {a['description']}" for a in achievements[:3])
    
    def _format_next_achievements(self, goals: list) -> str:
        """Format next achievement goals for display."""
        if not goals:
            return "• No hay objetivos próximos"
        
        return "\n".join(f"🎯 {g['name']}: {g['progress']}" for g in goals[:3])