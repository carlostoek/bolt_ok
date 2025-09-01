"""
Diana Menu System - Handler principal para integración con aiogram
Este módulo implementa los handlers para el Diana Menu System y permite
una integración gradual con el sistema de menús existente.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from services.diana_menu_integration_impl import (
    get_compatibility_bridge,
    get_integration_manager
)
from services.enhanced_diana_menu_system import (
    EnhancedDianaMenuSystem,
    show_diana_main_menu,
    handle_diana_callback
)
from services.enhanced_user_service import EnhancedUserService
from utils.handler_decorators import safe_handler, require_role

logger = logging.getLogger(__name__)

# Router para Diana Menu System
router = Router(name="diana_handler")

@router.message(Command("diana"))
@safe_handler("😔 Los hilos del destino se han enredado... Inténtalo de nuevo, querido.")
async def cmd_diana(message: Message, session: AsyncSession):
    """
    Comando de acceso al Enhanced Diana Menu System con consistencia de personaje.
    Optimizado para respuesta <1s y >95% consistencia de personaje.
    """
    user_id = message.from_user.id
    
    logger.info(f"Usuario {user_id} accediendo a Enhanced Diana Menu System")
    
    try:
        # Usar el sistema mejorado de Diana
        menu_result = await show_diana_main_menu(session, message)
        
        if not menu_result.success:
            logger.warning(f"Menu system failed for user {user_id}: {menu_result.errors}")
            
        # Log performance metrics
        if menu_result.response_time > 1.0:
            logger.warning(f"Menu response time exceeded 1s: {menu_result.response_time:.2f}s")
            
        if menu_result.character_score < 95.0:
            logger.warning(f"Character consistency below 95%: {menu_result.character_score:.1f}%")
        
    except Exception as e:
        logger.error(f"Error accediendo a Enhanced Diana Menu System: {e}")
        # Character-consistent error message
        error_message = "😔 Las corrientes místicas fluctúan... Algo interrumpe nuestra conexión momentáneamente. Los secretos estarán aquí cuando regreses, querido..."
        await message.answer(error_message)

@router.message(Command("diana_admin"))
@require_role("admin")
@safe_handler("❌ Error accediendo al panel administrativo Diana.")
async def cmd_diana_admin(message: Message, session: AsyncSession):
    """
    Comando de acceso directo al panel administrativo Diana.
    Solo disponible para administradores.
    """
    user_id = message.from_user.id
    
    logger.info(f"Administrador {user_id} accediendo al panel administrativo Diana")
    
    try:
        # Obtener bridge de compatibilidad
        diana_bridge = get_compatibility_bridge(session)
        
        # Intentar mostrar menú administrativo Diana
        success = await diana_bridge.bridge_admin_menu(message)
        
        if not success:
            await message.answer("ℹ️ El panel administrativo Diana no está disponible en este momento. Accediendo al panel administrativo clásico...")
            # Aquí podríamos redirigir al panel administrativo clásico
        
    except Exception as e:
        logger.error(f"Error accediendo al panel administrativo Diana: {e}")
        await message.answer("❌ Error accediendo al panel administrativo Diana. Inténtalo de nuevo más tarde.")

@router.callback_query(F.data.startswith("diana_"))
@safe_handler("😔 Los vientos del misterio encuentran resistencia...")
async def handle_diana_callback_enhanced(callback: CallbackQuery, session: AsyncSession):
    """
    Handler mejorado para callbacks de Diana Menu System con consistencia de personaje.
    Optimizado para respuesta <1s y >95% consistencia de personaje.
    """
    user_id = callback.from_user.id
    data = callback.data
    
    logger.debug(f"Enhanced Diana callback {data} recibido de usuario {user_id}")
    
    try:
        # Usar el sistema mejorado de callbacks
        callback_result = await handle_diana_callback(session, callback)
        
        # Log performance and character metrics
        if callback_result.response_time > 1.0:
            logger.warning(f"Callback response time exceeded 1s: {callback_result.response_time:.2f}s")
            
        if callback_result.character_score < 95.0:
            logger.warning(f"Callback character consistency below 95%: {callback_result.character_score:.1f}%")
        
        if not callback_result.success:
            logger.warning(f"Callback failed for user {user_id}: {callback_result.errors}")
            
    except Exception as e:
        logger.error(f"Error procesando Enhanced Diana callback {data}: {e}")
        # Character-consistent error message
        error_message = "🌙 Los hilos del destino se han enredado momentáneamente... Inténtalo de nuevo en un instante, querido."
        await callback.answer(error_message, show_alert=True)

# Este router intercepta callbacks que podrían ser manejados por Diana o por el sistema clásico
@router.callback_query(F.data.in_([
    "admin_menu", "user_menu", "admin_refresh", "user_refresh",
    "user_narrative", "user_games", "user_profile", "close_menu"
]))
@safe_handler("❌ Error procesando navegación Diana.")
async def handle_shared_callback(callback: CallbackQuery, session: AsyncSession):
    """
    Handler para callbacks que podrían ser manejados por Diana o el sistema clásico.
    Implementa una estrategia de fallback: intenta primero con Diana, si falla, deja
    que el callback sea manejado por el sistema clásico.
    """
    user_id = callback.from_user.id
    data = callback.data
    
    logger.debug(f"Callback compartido {data} recibido de usuario {user_id}")
    
    try:
        # Obtener bridge de compatibilidad
        diana_bridge = get_compatibility_bridge(session)
        
        # Intentar manejar con Diana
        handled = await diana_bridge.handle_callback(callback)
        
        if handled:
            # Si Diana lo manejó, evitar que llegue a los handlers clásicos
            return
            
        # Si no fue manejado por Diana, el callback seguirá propagándose
        # a los handlers clásicos
        
    except Exception as e:
        logger.error(f"Error intentando manejar callback compartido {data} con Diana: {e}")
        # No hacemos answer aquí para permitir que los handlers clásicos lo manejen

async def report_system_status(bot, session: AsyncSession):
    """
    Función utilitaria para reportar el estado del sistema Diana.
    Útil para diagnosticar problemas de integración.
    """
    try:
        integration_manager = get_integration_manager(session, bot)
        health_report = await integration_manager.health_check()
        
        status_summary = {
            "diana_active": health_report.get("status") == "healthy",
            "diana_modules": {k: v.get("status", "unknown") 
                             for k, v in health_report.get("modules", {}).items()},
            "event_system": health_report.get("event_system", {}).get("subscriptions_active", False)
        }
        
        return status_summary
    except Exception as e:
        logger.error(f"Error obteniendo estado del sistema Diana: {e}")
        return {"error": str(e), "diana_active": False}