"""
Diana Menu System Integration Module
Provides integration handlers and connection points with existing bot handlers.
"""

import logging
from typing import Dict, Any, Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from .diana_menu_system import get_diana_menu_system
from utils.handler_decorators import safe_handler, require_role
from utils.user_roles import is_admin, get_user_role
from utils.message_safety import safe_answer

logger = logging.getLogger(__name__)

# Create router for Diana menu integration
diana_router = Router()

@diana_router.message(Command("diana"))
@safe_handler("❌ Error accediendo al sistema Diana.")
async def diana_main_command(message: Message, session: AsyncSession):
    """
    Main command to access Diana Menu System.
    Routes users to appropriate menu based on their role.
    """
    user_id = message.from_user.id
    bot = message.bot
    
    try:
        # Get Diana menu system instance
        diana_system = get_diana_menu_system(session)
        
        # Show appropriate main menu
        await diana_system.show_main_menu(message)
        
        logger.info(f"Diana menu accessed by user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in diana main command for user {user_id}: {e}")
        await safe_answer(message, 
            "❌ Error accediendo al sistema Diana. Inténtalo de nuevo más tarde.")

@diana_router.message(Command("diana_admin"))
@require_role("admin")
@safe_handler("❌ Error accediendo al panel administrativo Diana.")
async def diana_admin_command(message: Message, session: AsyncSession):
    """
    Direct access to Diana admin panel.
    Only available to administrators.
    """
    user_id = message.from_user.id
    
    try:
        # Get Diana menu system instance
        diana_system = get_diana_menu_system(session)
        
        # Show admin menu directly
        await diana_system.admin_menu(message)
        
        logger.info(f"Diana admin panel accessed by user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in diana admin command for user {user_id}: {e}")
        await safe_answer(message, 
            "❌ Error accediendo al panel administrativo Diana.")

@diana_router.callback_query(F.data.startswith("diana_"))
@safe_handler("❌ Error procesando acción Diana.")
async def diana_callback_handler(callback: CallbackQuery, session: AsyncSession):
    """
    Handles all Diana-related callback queries.
    Routes callbacks to appropriate Diana menu handlers.
    """
    user_id = callback.from_user.id
    data = callback.data
    
    try:
        # Get Diana menu system instance
        diana_system = get_diana_menu_system(session)
        
        # Remove "diana_" prefix and delegate to main callback handler
        clean_data = data.replace("diana_", "", 1)
        callback.data = clean_data
        
        # Delegate to Diana system callback handler
        await diana_system.handle_callback(callback)
        
        logger.debug(f"Diana callback {data} handled for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling Diana callback {data} for user {user_id}: {e}")
        await callback.answer("❌ Error procesando acción Diana", show_alert=True)

@diana_router.callback_query(F.data.in_([
    "admin_menu", "user_menu", "admin_refresh", "user_refresh",
    "user_narrative", "user_games", "user_profile", "close_menu"
]))
@safe_handler("❌ Error procesando navegación Diana.")
async def diana_navigation_handler(callback: CallbackQuery, session: AsyncSession):
    """
    Handles main Diana navigation callbacks.
    Integrates with existing menu patterns.
    """
    user_id = callback.from_user.id
    data = callback.data
    
    try:
        # Get Diana menu system instance
        diana_system = get_diana_menu_system(session)
        
        # Delegate to Diana system callback handler
        await diana_system.handle_callback(callback)
        
        logger.debug(f"Diana navigation {data} handled for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling Diana navigation {data} for user {user_id}: {e}")
        await callback.answer("❌ Error en navegación Diana", show_alert=True)

# ==================== INTEGRATION HELPERS ====================

async def integrate_with_existing_handlers(diana_system, session: AsyncSession) -> Dict[str, Any]:
    """
    Helper function to integrate Diana system with existing bot handlers.
    This would be called during bot initialization.
    """
    try:
        # Initialize Diana coordination systems
        init_result = await diana_system.coordinador.initialize_coordination_systems()
        
        # Set up event subscriptions for cross-module integration
        if init_result.get("success"):
            logger.info("Diana Menu System integrated successfully with existing handlers")
            return {
                "success": True,
                "diana_active": True,
                "coordination_active": init_result.get("coordination_active", False),
                "message": "Sistema Diana integrado correctamente"
            }
        else:
            logger.warning("Diana coordination systems failed to initialize")
            return {
                "success": False,
                "diana_active": False,
                "coordination_active": False,
                "message": "Error inicializando coordinación Diana"
            }
            
    except Exception as e:
        logger.error(f"Error integrating Diana system: {e}")
        return {
            "success": False,
            "error": str(e),
            "diana_active": False,
            "message": "Error integrando sistema Diana"
        }

def setup_diana_menu_routes(main_router: Router) -> None:
    """
    Setup Diana menu routes in the main bot router.
    Call this during bot initialization.
    """
    try:
        # Include Diana router in main router
        main_router.include_router(diana_router)
        
        logger.info("Diana menu routes configured successfully")
        
    except Exception as e:
        logger.error(f"Error setting up Diana menu routes: {e}")
        raise

# ==================== COMPATIBILITY BRIDGES ====================

class DianaCompatibilityBridge:
    """
    Compatibility bridge for integrating Diana menus with existing handlers.
    Provides seamless transition between old and new menu systems.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.diana_system = get_diana_menu_system(session)
    
    async def bridge_admin_menu(self, callback: CallbackQuery) -> bool:
        """
        Bridge existing admin menu calls to Diana admin system.
        Returns True if handled by Diana, False if should use existing handler.
        """
        try:
            # Check if user wants Diana interface
            user_role = await get_user_role(callback.bot, callback.from_user.id, self.session)
            
            if user_role == "admin":
                # Route to Diana admin panel
                await self.diana_system.admin_menu.show_main_admin_panel(callback)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error in admin menu bridge: {e}")
            return False
    
    async def bridge_user_menu(self, callback: CallbackQuery) -> bool:
        """
        Bridge existing user menu calls to Diana user system.
        Returns True if handled by Diana, False if should use existing handler.
        """
        try:
            # Route to Diana user menu
            await self.diana_system.user_menu.show_main_user_menu(callback)
            return True
            
        except Exception as e:
            logger.error(f"Error in user menu bridge: {e}")
            return False
    
    async def bridge_narrative_content(self, callback: CallbackQuery, fragment_key: str = None) -> bool:
        """
        Bridge narrative content access to Diana narrative system.
        """
        try:
            if fragment_key:
                # Handle specific fragment access
                await self.diana_system.narrative_menu.show_story_continuation(callback)
            else:
                # Show narrative hub
                await self.diana_system.narrative_menu.show_narrative_hub(callback)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in narrative bridge: {e}")
            return False
    
    async def bridge_gamification_features(self, callback: CallbackQuery, feature_type: str = None) -> bool:
        """
        Bridge gamification features to Diana gamification system.
        """
        try:
            if feature_type == "missions":
                await self.diana_system.gamification_menu.show_missions_center(callback)
            elif feature_type == "achievements":
                await self.diana_system.gamification_menu.show_achievements_gallery(callback)
            elif feature_type == "points":
                await self.diana_system.gamification_menu.show_points_economy(callback)
            else:
                # Show gamification hub
                await self.diana_system.gamification_menu.show_gamification_hub(callback)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in gamification bridge: {e}")
            return False

# ==================== GLOBAL COMPATIBILITY INSTANCE ====================

diana_bridge = None

def get_diana_bridge(session: AsyncSession) -> DianaCompatibilityBridge:
    """Get or create Diana compatibility bridge instance."""
    global diana_bridge
    if diana_bridge is None or diana_bridge.session != session:
        diana_bridge = DianaCompatibilityBridge(session)
    return diana_bridge