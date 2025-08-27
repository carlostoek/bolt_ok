"""
Diana Admin Menu Module - Integrated Administration Interface
Connects with existing admin handlers while providing unified Diana experience.
"""

import logging
from typing import Dict, Any, Optional
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from ..coordinador_central import CoordinadorCentral
from ..admin_service import AdminService
from ..user_service import UserService
from utils.message_safety import safe_edit
from utils.user_roles import is_admin

logger = logging.getLogger(__name__)

class DianaAdminMenu:
    """
    Diana-themed admin menu system that integrates with existing admin handlers.
    Provides unified navigation while maintaining compatibility with current admin system.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.coordinador = CoordinadorCentral(session)
        self.admin_service = AdminService(session)
        self.user_service = UserService(session)
    
    async def show_main_admin_panel(self, callback: CallbackQuery) -> None:
        """
        Main admin panel with Diana branding and integrated system overview.
        """
        if not await is_admin(callback.from_user.id, self.session):
            await callback.answer("❌ Acceso denegado", show_alert=True)
            return
        
        try:
            # Get system overview statistics
            admin_stats = await self._get_admin_overview()
            
            text = f"""
🎭 **DIANA - CENTRO DE CONTROL ADMINISTRATIVO**
*Administración integral del sistema*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Resumen del Sistema**
👥 Usuarios totales: {admin_stats.get('total_users', 0)}
👑 VIP activos: {admin_stats.get('vip_users', 0)}
🆓 Usuarios gratuitos: {admin_stats.get('free_users', 0)}
💰 Puntos en circulación: {admin_stats.get('total_points', 0)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️ **Gestión Principal**
Controla todos los aspectos del sistema desde aquí

🎮 **Sistema de Gamificación**  
Misiones, puntos, logros y recompensas

📖 **Contenido Narrativo**
Historia, fragmentos y experiencias VIP

━━━━━━━━━━━━━━━━━━━━━━━━━━━
*Diana supervisa cada detalle con elegancia*
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("👥 Gestión de Usuarios", callback_data="admin_users_manage"),
                    InlineKeyboardButton("📺 Canales", callback_data="admin_channels_manage")
                ],
                [
                    InlineKeyboardButton("🎮 Gamificación", callback_data="admin_gamification_hub"),
                    InlineKeyboardButton("📖 Narrativa", callback_data="admin_narrative_hub")
                ],
                [
                    InlineKeyboardButton("👑 Sistema VIP", callback_data="admin_vip_system"),
                    InlineKeyboardButton("💳 Suscripciones", callback_data="admin_subscriptions")
                ],
                [
                    InlineKeyboardButton("📊 Estadísticas", callback_data="admin_detailed_stats"),
                    InlineKeyboardButton("⚙️ Configuración", callback_data="admin_system_config")
                ],
                [
                    InlineKeyboardButton("🔄 Actualizar", callback_data="admin_refresh"),
                    InlineKeyboardButton("❌ Cerrar", callback_data="close_menu")
                ]
            ]
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer("🎭 Panel administrativo cargado")
            
        except Exception as e:
            logger.error(f"Error showing admin panel: {e}")
            await callback.answer("❌ Error cargando panel administrativo", show_alert=True)
    
    async def show_user_management(self, callback: CallbackQuery) -> None:
        """
        User management panel with comprehensive user control.
        """
        if not await is_admin(callback.from_user.id, self.session):
            await callback.answer("❌ Acceso denegado", show_alert=True)
            return
        
        try:
            # Get user statistics
            user_stats = await self._get_user_management_stats()
            
            text = f"""
👥 **GESTIÓN DE USUARIOS - DIANA**
*Control completo sobre la comunidad*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Estadísticas de Usuarios**
• Total de usuarios: {user_stats.get('total', 0)}
• Usuarios activos (7 días): {user_stats.get('active_7d', 0)}
• Nuevos registros (24h): {user_stats.get('new_24h', 0)}

👑 **Usuarios VIP**
• VIP activos: {user_stats.get('vip_active', 0)}
• VIP expirados: {user_stats.get('vip_expired', 0)}
• Ingresos VIP del mes: ${user_stats.get('vip_revenue', 0)}

🆓 **Usuarios Gratuitos**
• Usuarios free: {user_stats.get('free_users', 0)}
• Conversión a VIP: {user_stats.get('conversion_rate', 0)}%

━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ **Acciones Administrativas**
Gestiona roles, permisos y comportamiento
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("🔍 Buscar Usuario", callback_data="admin_search_user"),
                    InlineKeyboardButton("📋 Lista Usuarios", callback_data="admin_list_users")
                ],
                [
                    InlineKeyboardButton("👑 Gestión VIP", callback_data="admin_vip_users"),
                    InlineKeyboardButton("🆓 Usuarios Free", callback_data="admin_free_users")
                ],
                [
                    InlineKeyboardButton("🚫 Moderación", callback_data="admin_moderation"),
                    InlineKeyboardButton("💰 Gestión Puntos", callback_data="admin_points_manage")
                ],
                [
                    InlineKeyboardButton("📊 Reportes", callback_data="admin_user_reports"),
                    InlineKeyboardButton("🔧 Herramientas", callback_data="admin_user_tools")
                ],
                [
                    InlineKeyboardButton("◀️ Volver", callback_data="admin_menu"),
                    InlineKeyboardButton("❌ Cerrar", callback_data="close_menu")
                ]
            ]
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer("👥 Gestión de usuarios cargada")
            
        except Exception as e:
            logger.error(f"Error showing user management: {e}")
            await callback.answer("❌ Error cargando gestión de usuarios", show_alert=True)
    
    async def show_gamification_admin(self, callback: CallbackQuery) -> None:
        """
        Comprehensive gamification administration panel.
        """
        if not await is_admin(callback.from_user.id, self.session):
            await callback.answer("❌ Acceso denegado", show_alert=True)
            return
        
        try:
            # Get gamification statistics
            gamif_stats = await self._get_gamification_stats()
            
            text = f"""
🎮 **ADMINISTRACIÓN DE GAMIFICACIÓN**
*Control del sistema de recompensas y engagement*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Estado del Sistema**
• Misiones activas: {gamif_stats.get('active_missions', 0)}
• Logros disponibles: {gamif_stats.get('total_achievements', 0)}
• Puntos en circulación: {gamif_stats.get('total_points', 0)}
• Usuarios con misiones: {gamif_stats.get('users_with_missions', 0)}

🎯 **Misiones**
• Completadas hoy: {gamif_stats.get('missions_completed_today', 0)}
• Tasa de finalización: {gamif_stats.get('completion_rate', 0)}%
• Recompensas otorgadas: {gamif_stats.get('rewards_given', 0)}

🏆 **Logros**
• Logros desbloqueados: {gamif_stats.get('achievements_unlocked', 0)}
• Usuarios con logros: {gamif_stats.get('users_with_achievements', 0)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️ **Herramientas de Gestión**
Configura el ecosistema de gamificación
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("🎯 Gestionar Misiones", callback_data="admin_missions_manage"),
                    InlineKeyboardButton("🏆 Gestionar Logros", callback_data="admin_achievements_manage")
                ],
                [
                    InlineKeyboardButton("💰 Sistema de Puntos", callback_data="admin_points_system"),
                    InlineKeyboardButton("🎁 Recompensas", callback_data="admin_rewards_manage")
                ],
                [
                    InlineKeyboardButton("📈 Niveles", callback_data="admin_levels_manage"),
                    InlineKeyboardButton("🎲 Minijuegos", callback_data="admin_games_manage")
                ],
                [
                    InlineKeyboardButton("📊 Analytics", callback_data="admin_gamif_analytics"),
                    InlineKeyboardButton("⚙️ Configuración", callback_data="admin_gamif_config")
                ],
                [
                    InlineKeyboardButton("◀️ Volver", callback_data="admin_menu"),
                    InlineKeyboardButton("❌ Cerrar", callback_data="close_menu")
                ]
            ]
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer("🎮 Administración de gamificación cargada")
            
        except Exception as e:
            logger.error(f"Error showing gamification admin: {e}")
            await callback.answer("❌ Error cargando administración de gamificación", show_alert=True)
    
    async def show_narrative_admin(self, callback: CallbackQuery) -> None:
        """
        Narrative content administration panel.
        """
        if not await is_admin(callback.from_user.id, self.session):
            await callback.answer("❌ Acceso denegado", show_alert=True)
            return
        
        try:
            # Get narrative statistics
            narrative_stats = await self._get_narrative_stats()
            
            text = f"""
📖 **ADMINISTRACIÓN NARRATIVA**
*Control del contenido y experiencias interactivas*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 **Estado del Contenido**
• Fragmentos totales: {narrative_stats.get('total_fragments', 0)}
• Fragmentos VIP: {narrative_stats.get('vip_fragments', 0)}
• Usuarios en historia: {narrative_stats.get('users_in_story', 0)}
• Decisiones disponibles: {narrative_stats.get('total_decisions', 0)}

🎭 **Personajes**
• Diana - Fragmentos: {narrative_stats.get('diana_fragments', 0)}
• Lucien - Fragmentos: {narrative_stats.get('lucien_fragments', 0)}
• Interacciones activas: {narrative_stats.get('active_interactions', 0)}

🔓 **Contenido VIP**
• Accesos VIP hoy: {narrative_stats.get('vip_access_today', 0)}
• Fragmentos premium: {narrative_stats.get('premium_content', 0)}
• Conversiones a VIP: {narrative_stats.get('vip_conversions', 0)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

✍️ **Herramientas de Creación**
Gestiona la experiencia narrativa completa
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("📝 Gestionar Fragmentos", callback_data="admin_fragments_manage"),
                    InlineKeyboardButton("🔮 Decisiones", callback_data="admin_decisions_manage")
                ],
                [
                    InlineKeyboardButton("🎭 Personajes", callback_data="admin_characters_manage"),
                    InlineKeyboardButton("👑 Contenido VIP", callback_data="admin_vip_content")
                ],
                [
                    InlineKeyboardButton("🗝️ Pistas", callback_data="admin_hints_manage"),
                    InlineKeyboardButton("📊 Progreso Usuarios", callback_data="admin_narrative_progress")
                ],
                [
                    InlineKeyboardButton("🎨 Personalización", callback_data="admin_narrative_themes"),
                    InlineKeyboardButton("⚙️ Configuración", callback_data="admin_narrative_config")
                ],
                [
                    InlineKeyboardButton("◀️ Volver", callback_data="admin_menu"),
                    InlineKeyboardButton("❌ Cerrar", callback_data="close_menu")
                ]
            ]
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer("📖 Administración narrativa cargada")
            
        except Exception as e:
            logger.error(f"Error showing narrative admin: {e}")
            await callback.answer("❌ Error cargando administración narrativa", show_alert=True)
    
    async def show_vip_administration(self, callback: CallbackQuery) -> None:
        """
        Comprehensive VIP system administration.
        """
        if not await is_admin(callback.from_user.id, self.session):
            await callback.answer("❌ Acceso denegado", show_alert=True)
            return
        
        try:
            # Get VIP system statistics
            vip_stats = await self._get_vip_stats()
            
            text = f"""
👑 **ADMINISTRACIÓN SISTEMA VIP**
*Control completo de suscripciones premium*

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 **Estadísticas VIP**
• Suscriptores activos: {vip_stats.get('active_subscribers', 0)}
• Ingresos del mes: ${vip_stats.get('monthly_revenue', 0)}
• Tokens generados: {vip_stats.get('tokens_generated', 0)}
• Tokens usados: {vip_stats.get('tokens_used', 0)}

📊 **Conversiones**
• Tasa de conversión: {vip_stats.get('conversion_rate', 0)}%
• Nuevos VIP (7 días): {vip_stats.get('new_vip_7d', 0)}
• Renovaciones: {vip_stats.get('renewals', 0)}
• Cancelaciones: {vip_stats.get('cancellations', 0)}

⏰ **Vencimientos**
• Vencen en 7 días: {vip_stats.get('expiring_7d', 0)}
• Vencen en 30 días: {vip_stats.get('expiring_30d', 0)}
• Expirados sin renovar: {vip_stats.get('expired_no_renewal', 0)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️ **Gestión VIP**
Controla el ecosistema premium completo
            """
            
            keyboard = [
                [
                    InlineKeyboardButton("💳 Generar Tokens", callback_data="admin_generate_tokens"),
                    InlineKeyboardButton("📋 Gestionar Tarifas", callback_data="admin_manage_tariffs")
                ],
                [
                    InlineKeyboardButton("👑 Usuarios VIP", callback_data="admin_vip_users_list"),
                    InlineKeyboardButton("⏰ Vencimientos", callback_data="admin_vip_expirations")
                ],
                [
                    InlineKeyboardButton("📊 Reportes VIP", callback_data="admin_vip_reports"),
                    InlineKeyboardButton("🎁 Promociones", callback_data="admin_vip_promotions")
                ],
                [
                    InlineKeyboardButton("⚙️ Configuración", callback_data="admin_vip_config"),
                    InlineKeyboardButton("📧 Notificaciones", callback_data="admin_vip_notifications")
                ],
                [
                    InlineKeyboardButton("◀️ Volver", callback_data="admin_menu"),
                    InlineKeyboardButton("❌ Cerrar", callback_data="close_menu")
                ]
            ]
            
            await safe_edit(
                callback.message,
                text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer("👑 Sistema VIP cargado")
            
        except Exception as e:
            logger.error(f"Error showing VIP administration: {e}")
            await callback.answer("❌ Error cargando sistema VIP", show_alert=True)
    
    # ==================== HELPER METHODS ====================
    
    async def _get_admin_overview(self) -> Dict[str, Any]:
        """Get comprehensive admin overview statistics."""
        try:
            # This would integrate with existing admin statistics
            from services import get_admin_statistics
            stats = await get_admin_statistics(self.session)
            
            return {
                "total_users": stats.get("users_total", 0),
                "vip_users": stats.get("subscriptions_active", 0),
                "free_users": stats.get("users_total", 0) - stats.get("subscriptions_active", 0),
                "total_points": stats.get("total_points", 0)
            }
        except Exception as e:
            logger.error(f"Error getting admin overview: {e}")
            return {}
    
    async def _get_user_management_stats(self) -> Dict[str, Any]:
        """Get user management specific statistics."""
        try:
            # Placeholder implementation - would integrate with UserService
            return {
                "total": 150,
                "active_7d": 120,
                "new_24h": 5,
                "vip_active": 45,
                "vip_expired": 8,
                "vip_revenue": 2250,
                "free_users": 105,
                "conversion_rate": 12
            }
        except Exception as e:
            logger.error(f"Error getting user management stats: {e}")
            return {}
    
    async def _get_gamification_stats(self) -> Dict[str, Any]:
        """Get gamification system statistics."""
        try:
            # Placeholder implementation - would integrate with MissionService, AchievementService
            return {
                "active_missions": 12,
                "total_achievements": 25,
                "total_points": 15000,
                "users_with_missions": 89,
                "missions_completed_today": 23,
                "completion_rate": 78,
                "rewards_given": 156,
                "achievements_unlocked": 234,
                "users_with_achievements": 67
            }
        except Exception as e:
            logger.error(f"Error getting gamification stats: {e}")
            return {}
    
    async def _get_narrative_stats(self) -> Dict[str, Any]:
        """Get narrative system statistics."""
        try:
            # Placeholder implementation - would integrate with NarrativeService
            return {
                "total_fragments": 45,
                "vip_fragments": 18,
                "users_in_story": 123,
                "total_decisions": 67,
                "diana_fragments": 25,
                "lucien_fragments": 20,
                "active_interactions": 34,
                "vip_access_today": 12,
                "premium_content": 18,
                "vip_conversions": 3
            }
        except Exception as e:
            logger.error(f"Error getting narrative stats: {e}")
            return {}
    
    async def _get_vip_stats(self) -> Dict[str, Any]:
        """Get VIP system statistics."""
        try:
            # Placeholder implementation - would integrate with SubscriptionService
            return {
                "active_subscribers": 45,
                "monthly_revenue": 2250,
                "tokens_generated": 23,
                "tokens_used": 18,
                "conversion_rate": 12,
                "new_vip_7d": 4,
                "renewals": 8,
                "cancellations": 2,
                "expiring_7d": 6,
                "expiring_30d": 15,
                "expired_no_renewal": 3
            }
        except Exception as e:
            logger.error(f"Error getting VIP stats: {e}")
            return {}