"""
Menu System Router - Router central para el sistema de menús
Este módulo implementa el router para el Sistema de Menús Diana y
conecta la funcionalidad de los módulos del sistema con aiogram.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
import logging

from services.diana_menu_integration_impl import get_compatibility_bridge

logger = logging.getLogger(__name__)

# Router para Menu System
menu_system_router = Router(name="menu_system_router")

@menu_system_router.callback_query(F.data.startswith("menu_"))
async def handle_menu_callback(callback: CallbackQuery, session):
    """
    Handler para callbacks del sistema de menús.
    Procesa todas las interacciones con los menús del sistema Diana.
    """
    user_id = callback.from_user.id
    data = callback.data
    
    logger.debug(f"Menu System callback {data} recibido de usuario {user_id}")
    
    try:
        # Obtener bridge de compatibilidad
        diana_bridge = get_compatibility_bridge(session)
        
        # Manejar callback a través del bridge
        handled = await diana_bridge.bridge_user_menu(callback)
        
        if not handled:
            await callback.answer("ℹ️ Acción no disponible en el sistema de menús")
            
    except Exception as e:
        logger.error(f"Error procesando menu callback {data}: {e}")
        await callback.answer("❌ Error procesando acción del menú", show_alert=True)