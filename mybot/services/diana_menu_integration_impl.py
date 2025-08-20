"""
Diana Menu System - Módulo de Integración Mejorado
Implementa la integración del Diana Menu System con el bot actual siguiendo las mejores prácticas
y respetando la arquitectura existente.
"""

import logging
from typing import Dict, Any, Optional, List, Callable, Union
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from .diana_menu_system import get_diana_menu_system, initialize_diana_system
from .event_bus import get_event_bus, EventType, Event
from .coordinador_central import CoordinadorCentral
from utils.handler_decorators import safe_handler, require_role
from utils.user_roles import is_admin, get_user_role
from utils.message_safety import safe_answer, safe_edit, safe_edit_message_text

logger = logging.getLogger(__name__)

# Router específico para Diana Menu System
diana_router = Router(name="diana_menu")

# ==================== COMMAND HANDLERS ====================

@diana_router.message(Command("diana"))
@safe_handler("❌ Error accediendo al sistema Diana.")
async def cmd_diana(message: Message, session: AsyncSession):
    """
    Comando principal para acceder al Diana Menu System.
    Dirige a los usuarios al menú apropiado según su rol.
    """
    user_id = message.from_user.id
    bot = message.bot
    
    try:
        # Obtener instancia del Diana Menu System
        diana_system = get_diana_menu_system(session)
        
        # Mostrar menú principal apropiado
        await diana_system.show_main_menu(message)
        
        logger.info(f"Diana menu accedido por usuario {user_id}")
        
    except Exception as e:
        logger.error(f"Error en comando diana para usuario {user_id}: {e}")
        await safe_answer(message, 
            "❌ Error accediendo al sistema Diana. Inténtalo de nuevo más tarde.")

@diana_router.message(Command("diana_admin"))
@require_role("admin")
@safe_handler("❌ Error accediendo al panel administrativo Diana.")
async def cmd_diana_admin(message: Message, session: AsyncSession):
    """
    Acceso directo al panel administrativo de Diana.
    Solo disponible para administradores.
    """
    user_id = message.from_user.id
    
    try:
        # Obtener instancia del Diana Menu System
        diana_system = get_diana_menu_system(session)
        
        # Mostrar menú de administración directamente
        await diana_system.admin_menu(message)
        
        logger.info(f"Panel de administración Diana accedido por usuario {user_id}")
        
    except Exception as e:
        logger.error(f"Error en comando diana_admin para usuario {user_id}: {e}")
        await safe_answer(message, 
            "❌ Error accediendo al panel administrativo Diana.")

# ==================== CALLBACK HANDLERS ====================

@diana_router.callback_query(F.data.startswith("diana_"))
@safe_handler("❌ Error procesando acción Diana.")
async def handle_diana_callback(callback: CallbackQuery, session: AsyncSession):
    """
    Maneja todas las callback queries relacionadas con Diana.
    Redirige callbacks a los manejadores apropiados en el Diana Menu System.
    """
    user_id = callback.from_user.id
    data = callback.data
    
    try:
        # Obtener instancia del Diana Menu System
        diana_system = get_diana_menu_system(session)
        
        # Eliminar prefijo "diana_" y delegar al manejador principal de callbacks
        clean_data = data.replace("diana_", "", 1)
        callback.data = clean_data
        
        # Delegar al manejador de callbacks del Diana Menu System
        await diana_system.handle_callback(callback)
        
        logger.debug(f"Diana callback {data} manejado para usuario {user_id}")
        
    except Exception as e:
        logger.error(f"Error manejando Diana callback {data} para usuario {user_id}: {e}")
        await callback.answer("❌ Error procesando acción Diana", show_alert=True)

@diana_router.callback_query(F.data.in_([
    "admin_menu", "user_menu", "admin_refresh", "user_refresh",
    "user_narrative", "user_games", "user_profile", "close_menu"
]))
@safe_handler("❌ Error procesando navegación Diana.")
async def handle_diana_navigation(callback: CallbackQuery, session: AsyncSession):
    """
    Maneja callbacks principales de navegación de Diana.
    Se integra con los patrones de menú existentes.
    """
    user_id = callback.from_user.id
    data = callback.data
    
    try:
        # Obtener instancia del Diana Menu System
        diana_system = get_diana_menu_system(session)
        
        # Delegar al manejador de callbacks del Diana Menu System
        await diana_system.handle_callback(callback)
        
        logger.debug(f"Navegación Diana {data} manejada para usuario {user_id}")
        
    except Exception as e:
        logger.error(f"Error manejando navegación Diana {data} para usuario {user_id}: {e}")
        await callback.answer("❌ Error en navegación Diana", show_alert=True)

# ==================== INTEGRATION HELPERS ====================

class DianaIntegrationManager:
    """
    Gestor de integración de Diana que proporciona métodos para inicializar,
    configurar y monitorear el sistema Diana.
    """
    
    def __init__(self, session: AsyncSession, bot: Bot = None):
        """Inicializa el gestor de integración con la sesión y opcionalmente el bot."""
        self.session = session
        self.bot = bot
        self.event_bus = get_event_bus()
        self.diana_system = get_diana_menu_system(session)
        self.is_initialized = False
        
    async def initialize(self) -> Dict[str, Any]:
        """
        Inicializa el Diana Menu System con sistemas de coordinación.
        Debe llamarse durante la inicialización del bot.
        """
        try:
            # Inicializar Diana Menu System
            init_result = await initialize_diana_system(self.session)
            
            if init_result.get("success", False):
                self.is_initialized = True
                
                # Configurar suscripciones de eventos para integración entre módulos
                await self._setup_event_subscriptions()
                
                logger.info("Diana Menu System inicializado correctamente")
                return {
                    "success": True,
                    "coordination_active": init_result.get("coordination_active", False),
                    "message": "Sistema Diana iniciado correctamente"
                }
            else:
                logger.warning("Falló la inicialización de los sistemas de coordinación de Diana")
                return {
                    "success": False,
                    "message": init_result.get("message", "Error inicializando Diana"),
                    "error": init_result.get("error")
                }
                
        except Exception as e:
            logger.error(f"Error inicializando Diana Menu System: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error crítico inicializando sistema Diana"
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Realiza una verificación de salud del Diana Menu System.
        Útil para monitoreo y diagnóstico.
        """
        try:
            if not self.is_initialized:
                return {
                    "status": "not_initialized",
                    "message": "Diana Menu System no está inicializado"
                }
                
            # Realizar verificación de salud a través del coordinador
            health_report = await self.diana_system.coordinador.perform_system_health_check()
            
            # Emitir evento de verificación de salud
            await self.event_bus.publish(
                EventType.CONSISTENCY_CHECK,
                0,  # Evento a nivel de sistema
                {
                    "type": "diana_health_check",
                    "result": health_report
                },
                source="diana_integration"
            )
            
            return health_report
            
        except Exception as e:
            logger.error(f"Error en verificación de salud de Diana: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Error verificando salud del sistema Diana"
            }
    
    async def _setup_event_subscriptions(self) -> None:
        """Configura suscripciones de eventos para integración entre módulos."""
        event_bus = self.event_bus
        
        # Suscribirse a eventos de menú del sistema actual
        event_bus.subscribe(EventType.WORKFLOW_COMPLETED, self._handle_workflow_completed)
        event_bus.subscribe(EventType.USER_REACTION, self._handle_user_reaction)
        event_bus.subscribe(EventType.NARRATIVE_PROGRESS, self._handle_narrative_progress)
        
        logger.info("Suscripciones de eventos de Diana configuradas")
    
    async def _handle_workflow_completed(self, event: Event) -> None:
        """Maneja eventos de flujo de trabajo completado."""
        # Este método reaccionaría a flujos de trabajo completados en el sistema existente
        pass
    
    async def _handle_user_reaction(self, event: Event) -> None:
        """Maneja eventos de reacción de usuario."""
        # Este método reaccionaría a reacciones de usuario en el sistema existente
        pass
    
    async def _handle_narrative_progress(self, event: Event) -> None:
        """Maneja eventos de progreso narrativo."""
        # Este método reaccionaría a progreso narrativo en el sistema existente
        pass

# ==================== COMPATIBILITY BRIDGE ====================

class DianaCompatibilityBridge:
    """
    Puente de compatibilidad para integrar los menús Diana con los handlers existentes.
    Proporciona una transición sin problemas entre los sistemas de menú antiguos y nuevos.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.diana_system = get_diana_menu_system(session)
        self.logger = logging.getLogger(f"{__name__}.DianaCompatibilityBridge")
    
    async def bridge_main_menu(self, message: Message) -> bool:
        """
        Puente para el menú principal.
        Intenta mostrar el menú Diana primero, con fallback al menú existente.
        
        Returns:
            bool: True si el menú Diana fue mostrado, False si se debe usar el handler existente
        """
        try:
            # Intentar mostrar el menú Diana primero
            await self.diana_system.show_main_menu(message)
            return True
            
        except Exception as e:
            self.logger.error(f"Error en puente de menú principal: {e}")
            return False
    
    async def bridge_admin_menu(self, callback: CallbackQuery) -> bool:
        """
        Puente para el menú de administración.
        Intenta mostrar el menú admin Diana primero, con fallback al menú existente.
        
        Returns:
            bool: True si el menú Diana fue mostrado, False si se debe usar el handler existente
        """
        try:
            # Verificar si el usuario es administrador
            user_role = await get_user_role(callback.bot, callback.from_user.id, self.session)
            
            if user_role == "admin":
                # Redirigir al panel de administración Diana
                await self.diana_system.show_admin_menu(callback)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error en puente de menú admin: {e}")
            return False
    
    async def bridge_narrative_menu(self, callback: CallbackQuery) -> bool:
        """
        Puente para el menú narrativo.
        Intenta mostrar el menú narrativo Diana primero, con fallback al menú existente.
        
        Returns:
            bool: True si el menú Diana fue mostrado, False si se debe usar el handler existente
        """
        try:
            # Redirigir al hub narrativo Diana
            await self.diana_system.show_narrative_hub(callback)
            return True
            
        except Exception as e:
            self.logger.error(f"Error en puente de menú narrativo: {e}")
            return False
    
    async def bridge_gamification_menu(self, callback: CallbackQuery) -> bool:
        """
        Puente para el menú de gamificación.
        Intenta mostrar el menú de gamificación Diana primero, con fallback al menú existente.
        
        Returns:
            bool: True si el menú Diana fue mostrado, False si se debe usar el handler existente
        """
        try:
            # Redirigir al hub de gamificación Diana
            await self.diana_system.show_gamification_hub(callback)
            return True
            
        except Exception as e:
            self.logger.error(f"Error en puente de menú de gamificación: {e}")
            return False
    
    async def handle_callback(self, callback: CallbackQuery) -> bool:
        """
        Manejador universal de callbacks para la integración.
        Determina si un callback debe ser manejado por Diana o por el sistema existente.
        
        Returns:
            bool: True si el callback fue manejado por Diana, False si se debe usar el handler existente
        """
        data = callback.data
        
        try:
            # Si es un callback Diana específico, delegarlo a Diana
            if data.startswith("diana_"):
                clean_data = data.replace("diana_", "", 1)
                callback.data = clean_data
                await self.diana_system.handle_callback(callback)
                callback.data = data  # Restaurar datos originales
                return True
                
            # Determinar si este callback debería ser manejado por Diana basado en su patrón
            diana_patterns = [
                "admin_menu", "user_menu", "admin_refresh", "user_refresh",
                "user_narrative", "user_games", "user_profile", "close_menu"
            ]
            
            if data in diana_patterns:
                await self.diana_system.handle_callback(callback)
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Error en manejo de callback: {e}")
            return False

# ==================== SETUP FUNCTION ====================

def setup_diana_menu_routes(main_router: Router) -> None:
    """
    Configura las rutas del menú Diana en el router principal del bot.
    Llamar durante la inicialización del bot.
    """
    try:
        # Incluir el router Diana en el router principal
        main_router.include_router(diana_router)
        
        logger.info("Rutas del menú Diana configuradas correctamente")
        
    except Exception as e:
        logger.error(f"Error configurando rutas del menú Diana: {e}")
        raise

# ==================== GLOBAL INSTANCES ====================

# Instancia global del gestor de integración Diana
_integration_manager = None

def get_integration_manager(session: AsyncSession, bot: Bot = None) -> DianaIntegrationManager:
    """Obtiene o crea la instancia del gestor de integración Diana."""
    global _integration_manager
    if _integration_manager is None or _integration_manager.session != session:
        _integration_manager = DianaIntegrationManager(session, bot)
    return _integration_manager

# Instancia global del puente de compatibilidad
_compatibility_bridge = None

def get_compatibility_bridge(session: AsyncSession) -> DianaCompatibilityBridge:
    """Obtiene o crea la instancia del puente de compatibilidad Diana."""
    global _compatibility_bridge
    if _compatibility_bridge is None or _compatibility_bridge.session != session:
        _compatibility_bridge = DianaCompatibilityBridge(session)
    return _compatibility_bridge