"""
Enhanced Diana Menu System - Unified Interface for Admin, Gamification, and Narrative Modules
Integrates seamlessly with the existing service architecture and CoordinadorCentral.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from aiogram import Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.exceptions import TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from .coordinador_central import CoordinadorCentral, AccionUsuario
from .user_service import UserService
from .point_service import PointService
from .narrative_service import NarrativeService
from .narrative_compatibility_layer import get_narrative_compatibility
from .mission_service import MissionService
from .achievement_service import AchievementService
from .content_delivery_service import ContentDeliveryService, ContentPackage, ContentType
from .tenant_service import TenantService
from .event_bus import get_event_bus, EventType
from .diana_menus.admin_menu import DianaAdminMenu
from .diana_menus.user_menu import DianaUserMenu
from .diana_menus.narrative_menu import DianaNarrativeMenu
from .diana_menus.gamification_menu import DianaGamificationMenu
from utils.handler_decorators import safe_handler
from utils.message_safety import safe_edit, safe_answer
from utils.user_roles import get_user_role
from database.models import User

logger = logging.getLogger(__name__)

class DianaMenuSystem:
    """
    Enhanced Diana Menu System that provides unified interface across all three modules:
    - Admin: Complete system administration and configuration
    - Gamification: Points, missions, achievements, levels
    - Narrative: Interactive storytelling and VIP content
    
    Integrates with CoordinadorCentral for complex cross-module workflows.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize Diana Menu System with comprehensive service integration.
        
        Args:
            session: Database session for all service operations
        """
        self.session = session
        
        # Core coordination and services
        self.coordinador = CoordinadorCentral(session)
        self.user_service = UserService(session)
        self.point_service = PointService(session)
        self.narrative_service = NarrativeService(session)
        self.narrative_compatibility = get_narrative_compatibility(session)
        self.mission_service = MissionService(session)
        self.achievement_service = AchievementService(session)
        self.tenant_service = TenantService(session)
        self.content_delivery_service = ContentDeliveryService()
        
        # Specialized menu modules
        self.admin_menu = DianaAdminMenu(session)
        self.user_menu = DianaUserMenu(session, self)
        self.narrative_menu = DianaNarrativeMenu(session)
        self.gamification_menu = DianaGamificationMenu(session)
        
        # Event system integration
        self.event_bus = get_event_bus()
        
        # Menu state tracking
        self.temp_messages: Dict[int, tuple] = {}
        
        # Visual elements for consistent Diana character
        self.diana_icons = {
            "admin": "🎭",
            "user": "💋",
            "narrative": "📖", 
            "gamification": "🎮",
            "profile": "👤",
            "vip": "👑",
            "points": "💰",
            "missions": "🎯",
            "achievements": "🏆"
        }
    
    # ==================== MAIN MENU CONTROLLERS ====================
    
    async def show_main_menu(self, message: Message) -> None:
        """
        Display appropriate main menu based on user role.
        Entry point for the Diana Menu System.
        """
        user_id = message.from_user.id
        bot = message.bot
        
        try:
            # Get user role to determine menu type
            user_role = await get_user_role(bot, user_id, self.session)
            
            if user_role == "admin":
                await self.admin_menu(message)
            else:
                await self.user_menu(message)
                
        except Exception as e:
            logger.error(f"Error showing main menu for user {user_id}: {e}")
            await safe_answer(message, 
                "❌ Error cargando el menú principal. Inténtalo de nuevo.")
    
    async def admin_menu(self, update, context=None) -> None:
        """
        Enhanced admin menu with integrated system management.
        Delegates to specialized admin menu module.
        """
        # Handle both Message and CallbackQuery
        if hasattr(update, 'callback_query') and update.callback_query:
            callback = update.callback_query
            await self.admin_menu.show_main_admin_panel(callback)
        else:
            # Convert Message to CallbackQuery-like interface for compatibility
            message = update if hasattr(update, 'from_user') else update.message
            # For now, we'll handle direct message calls differently
            # In a real implementation, this would integrate with the existing admin handlers
            await safe_answer(message, 
                "🎭 **Panel de Administración Diana**\n\n"
                "Usa los comandos administrativos existentes o accede através de los menús inline.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton("🎭 Abrir Panel Admin", callback_data="admin_menu")]
                ]))
    
    async def user_menu(self, update, context=None) -> None:
        """
        Enhanced user menu with integrated experience across all modules.
        Delegates to specialized user menu module.
        """
        # Handle both Message and CallbackQuery
        if hasattr(update, 'callback_query') and update.callback_query:
            callback = update.callback_query
            await self.user_menu.show_main_user_menu(callback)
        else:
            # Convert Message to CallbackQuery-like interface for compatibility
            message = update if hasattr(update, 'from_user') else update.message
            await safe_answer(message, 
                "💋 **Menú Principal Diana**\n\n"
                "Bienvenido a tu experiencia personalizada con Diana.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton("💋 Abrir Menú Principal", callback_data="user_menu")]
                ]))
    
    # ==================== SPECIALIZED HUB CONTROLLERS ====================
    
    async def show_narrative_hub(self, callback: CallbackQuery) -> None:
        """
        Central hub for narrative content and interactive storytelling.
        Delegates to specialized narrative menu module.
        """
        await self.narrative_menu.show_narrative_hub(callback)
    
    async def show_gamification_hub(self, callback: CallbackQuery) -> None:
        """
        Central hub for gamification features: points, missions, achievements.
        Delegates to specialized gamification menu module.
        """
        await self.gamification_menu.show_gamification_hub(callback)
    
    async def show_profile_integration(self, callback: CallbackQuery) -> None:
        """
        Integrated profile showing progress and data from all three modules.
        Delegates to specialized user menu module.
        """
        await self.user_menu.show_user_profile(callback)
    
    # ==================== CALLBACK HANDLER ====================
    
    @safe_handler("❌ Error procesando la acción. Inténtalo de nuevo.")
    async def handle_callback(self, callback: CallbackQuery) -> None:
        """
        Enhanced callback handler that routes to appropriate menu functions.
        Integrates with existing handler patterns and EventBus.
        """
        user_id = callback.from_user.id
        data = callback.data
        
        logger.debug(f"Diana menu callback: {data} from user {user_id}")
        
        try:
            # Emit navigation event for analytics
            await self.event_bus.publish(
                EventType.USER_INTERACTION,
                user_id,
                {
                    "action": "menu_navigation",
                    "menu_item": data,
                    "source": "diana_menu_system"
                },
                source="diana_menu_system"
            )
            
            # Main menu navigation
            if data == "admin_menu":
                await self.admin_menu.show_main_admin_panel(callback)
            elif data == "user_menu":
                await self.user_menu.show_main_user_menu(callback)
            elif data in ["admin_refresh", "user_refresh"]:
                await self._handle_refresh(callback, data)
            elif data == "close_menu":
                await self._handle_close_menu(callback)
            
            # Specialized hubs
            elif data == "user_narrative":
                await self.narrative_menu.show_narrative_hub(callback)
            elif data == "admin_gamification" or data == "user_games":
                await self.gamification_menu.show_gamification_hub(callback)
            elif data == "user_profile":
                await self.user_menu.show_user_profile(callback)
            
            # Delegate to specialized handlers
            elif data.startswith("admin_"):
                await self._handle_admin_actions(callback, data)
            elif data.startswith("narrative_"):
                await self._handle_narrative_actions(callback, data)
            elif data.startswith("gamification_"):
                await self._handle_gamification_actions(callback, data)
            elif data.startswith("user_"):
                await self._handle_user_actions(callback, data)
            
            else:
                await callback.answer(f"🔧 Función '{data}' en desarrollo", show_alert=True)
                logger.warning(f"Unhandled callback: {data}")
                
        except Exception as e:
            logger.error(f"Error handling callback {data}: {e}")
            await callback.answer("❌ Error procesando la acción", show_alert=True)
    
    # ==================== HELPER METHODS ====================
    
    async def _get_integrated_user_data(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user data from all modules."""
        try:
            # Get base user data
            user = await self.user_service.get_user(user_id)
            points = await self.point_service.get_user_points(user_id)
            
            # Get narrative progress using compatibility layer
            narrative_data = await self.narrative_compatibility.get_user_narrative_data(user_id)
            
            # Get gamification data
            missions = await self.mission_service.get_user_missions_summary(user_id)
            achievements = await self.achievement_service.get_user_achievements(user_id)
            
            return {
                "level": getattr(user, 'level', 1) if user else 1,
                "points": points,
                "current_points": points,
                "narrative_progress": narrative_data.get("completion_percentage", 0),
                "current_chapter": narrative_data.get("fragment_title", "Prólogo"),
                "hints_unlocked": narrative_data.get("hints_unlocked", 0),
                "decisions_made": len(narrative_data.get("decisions", [])),
                "completed_missions": missions.get("completed", 0) if missions else 0,
                "total_missions": missions.get("total", 0) if missions else 0,
                "achievements": len(achievements) if achievements else 0,
                "streak_days": getattr(user, 'streak_days', 0) if user else 0,
                "last_activity": "Hoy"  # Would need activity tracking
            }
            
        except Exception as e:
            logger.error(f"Error getting integrated user data: {e}")
            # Return fallback data to prevent failures
            return {
                "level": 1,
                "points": 0,
                "current_points": 0,
                "narrative_progress": 0,
                "current_chapter": "Prólogo",
                "hints_unlocked": 0,
                "decisions_made": 0,
                "completed_missions": 0,
                "total_missions": 0,
                "achievements": 0,
                "streak_days": 0,
                "last_activity": "Hoy"
            }
    
    async def _get_admin_statistics(self) -> Dict[str, Any]:
        """Get system-wide statistics for admin overview."""
        try:
            # This would integrate with existing admin statistics
            from services import get_admin_statistics
            return await get_admin_statistics(self.session)
        except Exception as e:
            logger.error(f"Error getting admin statistics: {e}")
            return {"total_users": 0, "vip_users": 0, "total_points": 0}
    
    async def _get_active_character(self, user_id: int) -> str:
        """Determine active character (Diana/Lucien) based on narrative progress."""
        try:
            # Use compatibility layer for consistent access to narrative data
            narrative_data = await self.narrative_compatibility.get_user_narrative_data(user_id)
            
            # Logic to determine character based on fragment key or progress
            current_fragment = narrative_data.get("current_fragment")
            
            # Advanced logic could be implemented here based on fragment key patterns
            # For example: if "lucien" in current_fragment: return "lucien"
            
            # For now, default to Diana
            return "diana"
        except Exception as e:
            logger.error(f"Error determining active character for user {user_id}: {e}")
            return "diana"
    
    async def _calculate_narrative_progress(self, user_id: int) -> int:
        """Calculate narrative completion percentage using compatibility layer."""
        try:
            # Use compatibility layer to get normalized narrative data
            narrative_data = await self.narrative_compatibility.get_user_narrative_data(user_id)
            
            # Return progress percentage directly from normalized data
            return narrative_data.get("progress_percentage", 0)
            
        except Exception as e:
            logger.error(f"Error calculating narrative progress for user {user_id}: {e}")
            return 0
    
    async def _calculate_engagement_score(self, user_id: int) -> int:
        """Calculate overall engagement score across all modules."""
        try:
            data = await self._get_integrated_user_data(user_id)
            
            # Weighted score calculation
            narrative_score = data.get("narrative_progress", 0) * 0.4
            mission_score = min((data.get("completed_missions", 0) * 10), 100) * 0.3
            achievement_score = min((data.get("achievements", 0) * 5), 100) * 0.2
            activity_score = min((data.get("streak_days", 0) * 2), 100) * 0.1
            
            return int(narrative_score + mission_score + achievement_score + activity_score)
        except Exception:
            return 0
    
    async def _handle_refresh(self, callback: CallbackQuery, data: str) -> None:
        """Handle menu refresh actions."""
        if data == "admin_refresh":
            await self.admin_menu.show_main_admin_panel(callback)
            await callback.answer("🔄 Panel administrativo actualizado")
        elif data == "user_refresh":
            await self.user_menu.show_main_user_menu(callback)
            await callback.answer("🔄 Menú principal actualizado")
    
    async def _handle_close_menu(self, callback: CallbackQuery) -> None:
        """Handle menu close action."""
        try:
            await callback.message.delete()
            await callback.answer("❌ Menú cerrado")
        except TelegramAPIError:
            await callback.answer("❌ Menú cerrado")
    
    async def _handle_admin_actions(self, callback: CallbackQuery, data: str) -> None:
        """Delegate admin actions to specialized admin menu handlers."""
        try:
            if data == "admin_users_manage":
                await self.admin_menu.show_user_management(callback)
            elif data == "admin_gamification_hub":
                await self.admin_menu.show_gamification_admin(callback)
            elif data == "admin_narrative_hub":
                await self.admin_menu.show_narrative_admin(callback)
            elif data == "admin_vip_system":
                await self.admin_menu.show_vip_administration(callback)
            else:
                # For other admin actions, we'd integrate with existing handlers
                await callback.answer(f"🔧 Función admin '{data}' conectando con handlers existentes...")
        except Exception as e:
            logger.error(f"Error handling admin action {data}: {e}")
            await callback.answer("❌ Error en función administrativa", show_alert=True)
    
    async def _handle_narrative_actions(self, callback: CallbackQuery, data: str) -> None:
        """Delegate narrative actions to specialized narrative menu handlers."""
        try:
            if data == "narrative_continue":
                await self.narrative_menu.show_story_continuation(callback)
            elif data == "narrative_inventory":
                await self.narrative_menu.show_hints_inventory(callback)
            elif data == "narrative_decisions":
                await self.narrative_menu.show_decision_center(callback)
            elif data == "narrative_character":
                await self.narrative_menu.show_character_selection(callback)
            else:
                # For other narrative actions, we'd integrate with existing handlers
                await callback.answer(f"📖 Función narrativa '{data}' conectando con handlers existentes...")
        except Exception as e:
            logger.error(f"Error handling narrative action {data}: {e}")
            await callback.answer("❌ Error en función narrativa", show_alert=True)
    
    async def _handle_gamification_actions(self, callback: CallbackQuery, data: str) -> None:
        """Delegate gamification actions to specialized gamification menu handlers."""
        try:
            if data == "gamification_missions":
                await self.gamification_menu.show_missions_center(callback)
            elif data == "gamification_achievements":
                await self.gamification_menu.show_achievements_gallery(callback)
            elif data == "gamification_economy":
                await self.gamification_menu.show_points_economy(callback)
            elif data == "gamification_levels":
                await self.gamification_menu.show_level_progression(callback)
            else:
                # For other gamification actions, we'd integrate with existing handlers
                await callback.answer(f"🎮 Función gamificación '{data}' conectando con handlers existentes...")
        except Exception as e:
            logger.error(f"Error handling gamification action {data}: {e}")
            await callback.answer("❌ Error en función de gamificación", show_alert=True)
    
    async def _handle_user_actions(self, callback: CallbackQuery, data: str) -> None:
        """Delegate user actions to specialized user menu handlers."""
        try:
            if data == "user_daily_activities":
                await self.user_menu.show_daily_activities(callback)
            elif data == "user_achievements":
                await self.user_menu.show_achievements_gallery(callback)
            else:
                # For other user actions, we'd integrate with existing handlers
                await callback.answer(f"👤 Función usuario '{data}' conectando con handlers existentes...")
        except Exception as e:
            logger.error(f"Error handling user action {data}: {e}")
            await callback.answer("❌ Error en función de usuario", show_alert=True)

    async def deliver_content(self, content_id: str, context: Dict[str, Any], callback: CallbackQuery) -> bool:
        """
        Prepara y entrega contenido utilizando el ContentDeliveryService.

        Args:
            content_id: El ID del contenido a entregar.
            context: El contexto para la entrega (incluye user_id, chat_id, etc.).
            callback: El objeto CallbackQuery que originó la acción.

        Returns:
            True si la entrega fue exitosa, False en caso contrario.
        """
        try:
            # Añadir bot y message al contexto
            context["bot"] = callback.bot
            context["message"] = callback.message

            package = await self.content_delivery_service.prepare_content(content_id, context)
            
            # Personalización adicional si es necesario
            if package.content_type == ContentType.TEXT:
                package.payload = await self.content_delivery_service.personalize_content(package.payload, context)

            # Validar restricciones
            is_valid, reasons = await self.content_delivery_service.validate_delivery_constraints(package, context)
            if not is_valid:
                logger.warning(f"No se pueden cumplir las restricciones de entrega para {content_id}: {reasons}")
                # Opcional: enviar un mensaje al usuario sobre por qué no se puede entregar el contenido
                return False

            return await self.content_delivery_service.deliver_content(package, context)
        except Exception as e:
            logger.error(f"Error al entregar contenido {content_id}: {e}")
            return False

# ==================== GLOBAL INSTANCE AND INTEGRATION ====================

# Global Diana Menu System instance will be created in main application
diana_menu_system = None

def get_diana_menu_system(session: AsyncSession) -> DianaMenuSystem:
    """Get or create Diana Menu System instance."""
    global diana_menu_system
    if diana_menu_system is None or diana_menu_system.session != session:
        diana_menu_system = DianaMenuSystem(session)
    return diana_menu_system

async def initialize_diana_system(session: AsyncSession) -> Dict[str, Any]:
    """Initialize Diana Menu System with coordination systems."""
    try:
        diana_system = get_diana_menu_system(session)
        
        # Initialize coordination systems
        coordination_result = await diana_system.coordinador.initialize_coordination_systems()
        
        logger.info("Diana Menu System initialized successfully")
        return {
            "success": True,
            "coordination_active": coordination_result.get("coordination_active", False),
            "message": "Diana Menu System operativo"
        }
    except Exception as e:
        logger.error(f"Error initializing Diana system: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error inicializando sistema Diana"
        }