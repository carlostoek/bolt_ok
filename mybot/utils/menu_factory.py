"""
Enhanced Menu factory for creating consistent menus based on user role and state.
Centralizes menu creation logic for better maintainability.
Enhanced with HTML formatting support and improved administrative features.
"""
from typing import Tuple, Optional, Dict, Any, Union
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession
from utils.user_roles import get_user_role
from keyboards.admin_main_kb import get_admin_main_kb
from keyboards.vip_main_kb import get_vip_main_kb
from keyboards.subscription_kb import get_free_main_menu_kb
from keyboards.setup_kb import (
    get_setup_main_kb, 
    get_setup_channels_kb, 
    get_setup_complete_kb,
    get_setup_gamification_kb,
    get_setup_tariffs_kb,
    get_setup_confirmation_kb,
)
from database.models import User
import logging
import asyncio
from datetime import datetime

from aiogram.utils.keyboard import InlineKeyboardBuilder # Importar InlineKeyboardBuilder

# Importar creadores de menú específicos (asegúrate de que estos archivos existen)
from utils.menu_creators import (
    create_profile_menu,
    create_missions_menu,
    create_rewards_menu,
    create_auction_menu,
    create_ranking_menu
)
from utils.text_utils import sanitize_text # Asegúrate de que esta importación exista y sea correcta

# Import HTML formatter for enhanced admin menus
try:
    from utils.html_formatter import HTMLMessageFormatter
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False
    logging.warning("HTMLMessageFormatter not available - HTML features will be limited")

logger = logging.getLogger(__name__)

class MenuFactory:
    """
    Enhanced Factory class for creating menus based on user state and role.
    Centralizes menu logic and ensures consistency.
    Features:
    - HTML-formatted administrative menus
    - Enhanced navigation history management
    - Automation task coordination support
    - Improved error handling and graceful degradation
    """

    def __init__(self):
        """Initialize menu factory with enhanced capabilities."""
        self._menu_cache: Dict[str, Tuple[str, float]] = {}  # cache_key -> (content, timestamp)
        self._cache_ttl = 300  # 5 minutes cache TTL
        self._admin_context_cache: Dict[int, Dict[str, Any]] = {}  # user_id -> context data
    
    async def create_menu(
        self,
        menu_state: str,
        user_id: int,
        session: AsyncSession,
        bot=None,
        use_html: bool = False,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Create a menu based on the current state and user role.

        Args:
            menu_state: Current menu state identifier
            user_id: ID of the user requesting the menu
            session: Database session for data access
            bot: Bot instance for role checking
            use_html: Whether to use HTML formatting for admin menus
            user_context: Optional context data for menu personalization

        Returns:
            Tuple[str, InlineKeyboardMarkup]: (text, keyboard)
        """
        try:
            role = await get_user_role(bot, user_id, session=session)
            logger.info(f"Creating menu for user {user_id}, state {menu_state}, role {role}")
            
            # Handle setup flow for new installations
            if menu_state.startswith("setup_") or menu_state == "admin_setup_choice":
                return await self._create_setup_menu(menu_state, user_id, session)
            
            # Handle role-based main menus with HTML support
            if menu_state in ["main", "admin_main", "vip_main", "free_main"]:
                if role == "admin" and use_html:
                    return await self._create_html_admin_menu(user_id, session, user_context)
                else:
                    result = self._create_main_menu(role)
                    logger.info(f"Main menu created for role {role}: text length {len(result[0])}")
                    return result

            # Handle enhanced admin menus
            if menu_state == "admin_main_enhanced":
                return await self._create_enhanced_admin_menu(user_id, session, user_context)

            # Handle automation menu states
            if menu_state == "admin_automation":
                return await self._create_automation_menu(user_id, session, user_context)
            
            # Handle admin narrative main menu
            if menu_state == "admin_narrative_main":
                return await self._create_admin_narrative_menu()
            
            # Handle admin gamification main menu
            if menu_state == "admin_gamification_main":
                return await self._create_admin_gamification_menu()
            
            # Handle specific menu states
            return await self._create_specific_menu(menu_state, user_id, session, role)
            
        except Exception as e:
            logger.error(f"Error creating menu for state {menu_state}, user {user_id}: {e}", exc_info=True)
            # Make sure to pass role to _create_fallback_menu
            try:
                role = await get_user_role(bot, user_id, session=session)
            except:
                role = "free"
            return self._create_fallback_menu(role) 
    
    def _create_main_menu(self, role: str) -> Tuple[str, InlineKeyboardMarkup]:
        """Create the main menu based on user role."""
        if role == "admin":
            return (
                "👑 **¡Bienvenido, Administrador!**\n\n"
                "Bienvenido al centro de control del bot. Desde aquí puedes gestionar "
                "todos los aspectos del sistema.",
                get_admin_main_kb()
            )
        elif role == "vip":
            return (
                "✨ **Bienvenido al Diván de Diana**\n\n"
                "Tu suscripción VIP te da acceso completo a todas las funciones. "
                "¡Disfruta de la experiencia premium!",
                get_vip_main_kb()
            )
        else: # Covers "free" and any other unrecognized roles
            return (
                "🌟 **Bienvenido a los Kinkys**\n\n"
                "Explora nuestro contenido gratuito y descubre todo lo que tenemos para ti. "
                "¿Listo para una experiencia única?",
                get_free_main_menu_kb()
            )
    
    async def _create_setup_menu(
        self, 
        menu_state: str, 
        user_id: int, 
        session: AsyncSession
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """Create setup menus for initial bot configuration."""
        if menu_state == "setup_main":
            return (
                "🚀 **Bienvenido a la Configuración Inicial**\n\n"
                "¡Hola! Vamos a configurar tu bot paso a paso para que esté listo "
                "para tus usuarios. Este proceso es rápido y fácil.\n\n"
                "**¿Qué vamos a configurar?**\n"
                "• 📢 Canales (VIP y/o Gratuito)\n"
                "• 💳 Tarifas de suscripción\n"
                "• 🎮 Sistema de gamificación\n\n"
                "¡Empecemos!",
                get_setup_main_kb()
            )
        elif menu_state == "setup_channels":
            return (
                "📢 **Configuración de Canales**\n\n"
                "Los canales son el corazón de tu bot. Puedes configurar:\n\n"
                "🔐 **Canal VIP**: Para suscriptores premium\n"
                "🆓 **Canal Gratuito**: Para usuarios sin suscripción\n\n"
                "**Recomendación**: Configura al menos un canal para empezar. "
                "Puedes agregar más canales después desde el panel de administración.",
                get_setup_channels_kb()
            )
        elif menu_state == "setup_complete":
            return (
                "✅ **Configuración Completada**\n\n"
                "¡Perfecto! Tu bot está listo para usar. Puedes acceder al panel de "
                "administración en cualquier momento.",
                get_setup_complete_kb()
            )
        # --- NUEVO BLOQUE: admin_setup_choice ---
        elif menu_state == "admin_setup_choice":
            return self.create_setup_choice_menu() # Reutiliza el método para el menú de elección
        # --- FIN NUEVO BLOQUE ---
        elif menu_state == "setup_vip_channel_prompt":
            return (
                "🔐 **Configurar Canal VIP**\n\n"
                "Para configurar tu canal VIP, reenvía cualquier mensaje de tu canal aquí. "
                "El bot detectará automáticamente el ID del canal.\n\n"
                "**Importante**: Asegúrate de que el bot sea administrador del canal "
                "con permisos para invitar usuarios.",
                get_setup_confirmation_kb("cancel_channel_setup")
            )
        elif menu_state == "setup_free_channel_prompt":
            return (
                "🆓 **Configurar Canal Gratuito**\n\n"
                "Para configurar tu canal gratuito, reenvía cualquier mensaje de tu canal aquí. "
                "El bot detectará automáticamente el ID del canal.\n\n"
                "**Importante**: Asegúrate de que el bot sea administrador del canal "
                "con permisos para aprobar solicitudes de unión.",
                get_setup_confirmation_kb("cancel_channel_setup")
            )
        elif menu_state == "setup_manual_channel_id_prompt":
            return (
                "📝 **Ingresa el ID del Canal Manualmente**\n\n"
                "Por favor, ingresa el ID numérico de tu canal. Normalmente empieza con `-100`.",
                get_setup_confirmation_kb("cancel_channel_setup")
            )
        elif menu_state == "setup_gamification":
            return (
                "🎮 **Configuración de Gamificación**\n\n"
                "El sistema de gamificación mantiene a tus usuarios comprometidos con:\n\n"
                "🎯 **Misiones**: Tareas que los usuarios pueden completar\n"
                "🏅 **Insignias**: Reconocimientos por logros\n"
                "🎁 **Recompensas**: Premios por acumular puntos\n"
                "📊 **Niveles**: Sistema de progresión\n\n"
                "**Recomendación**: Usa la configuración por defecto para empezar rápido.",
                get_setup_gamification_kb()
            )
        elif menu_state == "setup_tariffs":
            return (
                "💳 **Configuración de Tarifas VIP**\n\n"
                "Las tarifas determinan los precios y duración de las suscripciones VIP.\n\n"
                "**Opciones disponibles**:\n"
                "💎 **Básica**: Tarifa estándar de 30 días\n"
                "👑 **Premium**: Tarifa de 90 días con descuento\n"
                "🎯 **Personalizada**: Crea tus propias tarifas\n\n"
                "**Recomendación**: Empieza con las tarifas básica y premium.",
                get_setup_tariffs_kb()
            )
        elif menu_state in ["setup_missions_info", "setup_badges_info", "setup_rewards_info", "setup_levels_info"]:
            feature_name = menu_state.replace('_info', '').replace('setup_', '').replace('_', ' ').capitalize()
            return (
                f"ℹ️ **Información sobre {feature_name}**\n\n"
                "Esta es una sección informativa. La implementación para crear/editar "
                "estos elementos estará disponible próximamente.",
                get_setup_gamification_kb()
            )
        elif menu_state in ["setup_premium_tariff_info", "setup_custom_tariffs_info"]:
            feature_name = menu_state.replace('_info', '').replace('setup_', '').replace('_', ' ').capitalize()
            return (
                f"ℹ️ **Información sobre {feature_name}**\n\n"
                "Esta es una sección informativa. La implementación para crear/editar "
                "tarifas premium o personalizadas estará disponible próximamente.",
                get_setup_tariffs_kb()
            )
        elif menu_state == "setup_guide_info":
            return (
                "📖 **Guía de Uso del Bot**\n\n"
                "Aquí encontrarás información detallada sobre cómo usar y configurar tu bot. "
                "Temas:\n"
                "• Gestión de usuarios\n"
                "• Creación de contenido\n"
                "• Marketing y monetización\n\n"
                "*(Contenido de la guía próximamente)*",
                get_setup_complete_kb()
            )
        elif menu_state == "setup_advanced_info":
            return (
                "🔧 **Configuración Avanzada (Próximamente)**\n\n"
                "Esta sección contendrá opciones avanzadas para la personalización del bot, "
                "integraciones y herramientas de depuración.\n\n"
                "*(Opciones avanzadas próximamente)*",
                get_setup_complete_kb()
            )
        else:
            logger.warning(f"Unknown setup menu state: {menu_state}. Falling back to main setup menu.")
            return (
                "⚠️ **Error de Configuración**\n\n"
                "No se pudo cargar el menú de configuración solicitado. Volviendo al inicio.",
                get_setup_main_kb()
            )
    
    async def _create_specific_menu(
        self, 
        menu_state: str, 
        user_id: int, 
        session: AsyncSession, 
        role: str
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """Create specific menus based on state."""
        
        if menu_state == "profile":
            return await create_profile_menu(user_id, session)
        elif menu_state == "missions":
            return await create_missions_menu(user_id, session)
        elif menu_state == "rewards":
            return await create_rewards_menu(user_id, session)
        elif menu_state == "auctions":
            return await create_auction_menu(user_id, session)
        elif menu_state == "ranking":
            return await create_ranking_menu(user_id, session)
        
        elif menu_state == "narrative":
            return await self._create_narrative_menu(user_id, session)
        
        elif menu_state == "admin_gamification_main": # Asegúrate de que este estado es reconocido si alguna otra parte lo invoca
            # Aunque el handler directo lo gestiona, si por alguna razón menu_factory
            # necesita crear este menú, podemos redirigirlo al panel admin principal
            return self._create_main_menu("admin") # O puedes definir un texto y teclado específico aquí
        else:
            logger.warning(f"Unknown specific menu state: {menu_state}. Falling back to main menu for role: {role}")
            return self._create_main_menu(role)
    
    async def _create_html_admin_menu(
        self,
        user_id: int,
        session: AsyncSession,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Create HTML-formatted admin main menu with enhanced features.

        Args:
            user_id: Admin user ID
            session: Database session
            user_context: Optional user context data

        Returns:
            Tuple of HTML-formatted text and keyboard
        """
        try:
            # Get admin context data
            admin_context = await self._get_admin_context(user_id, session)

            # Prepare menu data for HTML formatting
            menu_data = {
                "title": "Panel de Administración Avanzado",
                "description": "Centro de control administrativo con capacidades mejoradas",
                "stats": admin_context.get("quick_stats", {}),
                "sections": [
                    {
                        "title": "Gestión de Canales",
                        "options": [
                            {"icon": "💎", "text": "Canal VIP"},
                            {"icon": "💬", "text": "Canal Gratuito"}
                        ]
                    },
                    {
                        "title": "Automatización y Análisis",
                        "options": [
                            {"icon": "🤖", "text": "Sistema de Automatización"},
                            {"icon": "📈", "text": "Analytics Avanzado"}
                        ]
                    },
                    {
                        "title": "Sistema",
                        "options": [
                            {"icon": "⚙️", "text": "Configuración"},
                            {"icon": "🔧", "text": "Mantenimiento"}
                        ]
                    }
                ]
            }

            # Format with HTML if available
            if HTML_AVAILABLE:
                text = HTMLMessageFormatter.format_admin_menu(menu_data, user_context)
            else:
                # Fallback formatting
                text = self._format_admin_menu_fallback(menu_data)

            # Get enhanced admin keyboard
            from keyboards.admin_enhanced_kb import get_enhanced_admin_main_kb
            keyboard = get_enhanced_admin_main_kb()

            return text, keyboard

        except Exception as e:
            logger.error(f"Error creating HTML admin menu for user {user_id}: {e}")
            return self._create_main_menu("admin")

    async def _create_enhanced_admin_menu(
        self,
        user_id: int,
        session: AsyncSession,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Create enhanced admin menu with automation support and improved layout.

        Args:
            user_id: Admin user ID
            session: Database session
            user_context: Optional user context data

        Returns:
            Tuple of formatted text and enhanced keyboard
        """
        try:
            admin_context = await self._get_admin_context(user_id, session)

            # Check if automation is available
            automation_status = admin_context.get("automation_status", "unavailable")

            text_parts = [
                "<b>🛠️ Panel de Administración Mejorado</b>\n",
                f"<i>Bienvenido de vuelta, {user_context.get('user_name', 'Administrador')}</i>\n"
            ]

            # Add system status
            if admin_context.get("system_status"):
                text_parts.append("<u>📊 Estado del Sistema:</u>")
                for key, value in admin_context["system_status"].items():
                    text_parts.append(f"• <b>{key}:</b> <code>{value}</code>")
                text_parts.append("")

            # Add automation status
            if automation_status == "active":
                text_parts.append("🟢 <b>Automatización:</b> <i>Activa</i>")
            elif automation_status == "partial":
                text_parts.append("🟡 <b>Automatización:</b> <i>Parcial</i>")
            else:
                text_parts.append("🔴 <b>Automatización:</b> <i>Inactiva</i>")

            # Add quick stats
            if admin_context.get("quick_stats"):
                text_parts.append("\n<u>📈 Estadísticas Rápidas:</u>")
                for stat_name, stat_value in admin_context["quick_stats"].items():
                    text_parts.append(f"• <b>{stat_name}:</b> <code>{stat_value}</code>")

            # Footer with timestamp
            timestamp = datetime.now().strftime("%H:%M")
            text_parts.append(f"\n<i>⏰ Actualizado: {timestamp}</i>")

            text = "\n".join(text_parts)

            # Get enhanced keyboard
            from keyboards.admin_enhanced_kb import get_enhanced_admin_main_kb
            keyboard = get_enhanced_admin_main_kb()

            return text, keyboard

        except Exception as e:
            logger.error(f"Error creating enhanced admin menu for user {user_id}: {e}")
            return self._create_main_menu("admin")

    async def _create_automation_menu(
        self,
        user_id: int,
        session: AsyncSession,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Create automation control menu with task status and controls.

        Args:
            user_id: Admin user ID
            session: Database session
            user_context: Optional user context data

        Returns:
            Tuple of formatted text and automation keyboard
        """
        try:
            # Get automation status from service if available
            automation_data = await self._get_automation_status(session)

            if HTML_AVAILABLE:
                text = HTMLMessageFormatter.format_automation_status(
                    action="status_check",
                    started_tasks=automation_data.get("active_tasks", 0),
                    total_tasks=automation_data.get("total_tasks", 0),
                    details=automation_data.get("details", {})
                )
            else:
                # Fallback formatting
                active_tasks = automation_data.get("active_tasks", 0)
                total_tasks = automation_data.get("total_tasks", 0)
                text = f"""<b>🤖 Centro de Automatización</b>

<b>Estado:</b> {active_tasks}/{total_tasks} tareas activas

<u>⚡ Tareas Disponibles:</u>
• Recordatorios VIP
• Limpieza de mensajes
• Gestión de usuarios
• Eventos narrativos

<i>Selecciona una opción para continuar</i>"""

            # Get automation keyboard
            from keyboards.admin_automation_kb import get_automation_main_kb
            keyboard = get_automation_main_kb()

            return text, keyboard

        except Exception as e:
            logger.error(f"Error creating automation menu for user {user_id}: {e}")
            # Fallback to basic automation menu
            text = "<b>🤖 Automatización</b>\n\nSistema de automatización disponible."
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="🔙 Volver", callback_data="admin_main")
            return text, builder.as_markup()

    async def _get_admin_context(
        self,
        user_id: int,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get administrative context data for menu personalization.

        Args:
            user_id: Admin user ID
            session: Database session

        Returns:
            Dictionary with admin context data
        """
        try:
            # Check cache first
            if user_id in self._admin_context_cache:
                cached_data, cache_time = self._admin_context_cache[user_id]
                if (datetime.now().timestamp() - cache_time) < self._cache_ttl:
                    return cached_data

            context = {}

            # Get system status
            try:
                # Get user counts
                from sqlalchemy import func
                result = await session.execute(
                    select(func.count(User.id)).where(User.role == "vip")
                )
                vip_count = result.scalar() or 0

                result = await session.execute(
                    select(func.count(User.id)).where(User.role == "free")
                )
                free_count = result.scalar() or 0

                context["quick_stats"] = {
                    "Usuarios VIP": vip_count,
                    "Usuarios Free": free_count,
                    "Total": vip_count + free_count
                }

                context["system_status"] = {
                    "Base de datos": "Conectada",
                    "Última actualización": datetime.now().strftime("%H:%M")
                }

            except Exception as db_error:
                logger.warning(f"Could not fetch admin context from DB: {db_error}")
                context["quick_stats"] = {"Estado": "Error de DB"}
                context["system_status"] = {"Base de datos": "Error"}

            # Check automation status
            context["automation_status"] = await self._check_automation_status()

            # Cache the result
            self._admin_context_cache[user_id] = (context, datetime.now().timestamp())

            return context

        except Exception as e:
            logger.error(f"Error getting admin context for user {user_id}: {e}")
            return {"quick_stats": {}, "system_status": {}, "automation_status": "unknown"}

    async def _check_automation_status(self) -> str:
        """Check the status of automation services."""
        try:
            # Try to import and check automation service
            from handlers.admin.automation_handlers import automation_service
            if hasattr(automation_service, 'active_tasks'):
                active_count = len(automation_service.active_tasks)
                if active_count == 0:
                    return "inactive"
                elif active_count < 4:  # Assuming 4 main automation tasks
                    return "partial"
                else:
                    return "active"
            return "unavailable"
        except ImportError:
            return "unavailable"
        except Exception as e:
            logger.warning(f"Error checking automation status: {e}")
            return "unknown"

    async def _get_automation_status(self, session: AsyncSession) -> Dict[str, Any]:
        """Get automation task status and details."""
        try:
            # Try to get automation data
            from handlers.admin.automation_handlers import automation_service

            if hasattr(automation_service, 'task_status'):
                status_data = automation_service.task_status
                active_tasks = len([task for task, data in status_data.items() if data.get('active', False)])
                total_tasks = len(status_data)

                return {
                    "active_tasks": active_tasks,
                    "total_tasks": total_tasks,
                    "details": {
                        "task_breakdown": {task: data.get('active', False) for task, data in status_data.items()},
                        "intervals": {task: data.get('interval', 'N/A') for task, data in status_data.items()}
                    }
                }
            else:
                return {"active_tasks": 0, "total_tasks": 4, "details": {}}

        except ImportError:
            return {"active_tasks": 0, "total_tasks": 0, "details": {}}
        except Exception as e:
            logger.error(f"Error getting automation status: {e}")
            return {"active_tasks": 0, "total_tasks": 0, "details": {}}

    def _format_admin_menu_fallback(self, menu_data: Dict[str, Any]) -> str:
        """Fallback formatting for admin menus when HTML formatter is not available."""
        lines = []

        if 'title' in menu_data:
            lines.append(f"**{menu_data['title']}**\n")

        if 'description' in menu_data:
            lines.append(f"{menu_data['description']}\n")

        if 'stats' in menu_data and menu_data['stats']:
            lines.append("**📊 Estadísticas:**")
            for key, value in menu_data['stats'].items():
                lines.append(f"• **{key}:** `{value}`")
            lines.append("")

        if 'sections' in menu_data:
            for section in menu_data['sections']:
                if 'title' in section:
                    lines.append(f"**{section['title']}**")
                if 'options' in section:
                    for option in section['options']:
                        if isinstance(option, dict):
                            lines.append(f"• {option.get('icon', '')} {option.get('text', '')}")
                        else:
                            lines.append(f"• {option}")
                lines.append("")

        timestamp = datetime.now().strftime("%H:%M")
        lines.append(f"*⏰ Actualizado: {timestamp}*")

        return "\n".join(lines)

    async def _create_admin_narrative_menu(self) -> Tuple[str, InlineKeyboardMarkup]:
        """Create the admin narrative main menu."""
        try:
            from keyboards.admin_narrative_kb import get_admin_narrative_main_kb
            text = "📚 **Panel de Administración Narrativa**\n\n" \
                   "Gestiona todos los aspectos del sistema narrativo desde este panel central.\n\n" \
                   "**Funcionalidades disponibles:**\n" \
                   "• Crear y editar fragmentos de historia\n" \
                   "• Gestionar conexiones entre fragmentos\n" \
                   "• Analizar métricas de engagement\n" \
                   "• Validar consistencia narrativa\n" \
                   "• Configurar voces de personajes"
            
            return text, get_admin_narrative_main_kb()
        except ImportError:
            # Fallback if the keyboard doesn't exist
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="📝 Gestionar Fragmentos", callback_data="admin_narrative_fragments")
            builder.button(text="🔗 Conexiones", callback_data="admin_narrative_connections")
            builder.button(text="📊 Analytics", callback_data="admin_narrative_analytics")
            builder.button(text="✅ Validar", callback_data="admin_narrative_validate")
            builder.button(text="🔙 Volver", callback_data="admin_main")
            builder.adjust(2)
            
            text = "📚 **Panel de Administración Narrativa**\n\n" \
                   "Gestiona todos los aspectos del sistema narrativo."
            
            return text, builder.as_markup()

    async def _create_admin_gamification_menu(self) -> Tuple[str, InlineKeyboardMarkup]:
        """Create the admin gamification main menu."""
        try:
            from keyboards.admin_gamification_kb import get_admin_gamification_main_kb
            text = "🎮 **Panel de Gamificación**\n\n" \
                   "Gestiona misiones, logros y sistema de puntos.\n\n" \
                   "**Funcionalidades disponibles:**\n" \
                   "• Crear y editar misiones\n" \
                   "• Gestionar logros e insignias\n" \
                   "• Configurar sistema de puntos\n" \
                   "• Ver estadísticas de gamificación"
            
            return text, get_admin_gamification_main_kb()
        except ImportError:
            # Fallback if the keyboard doesn't exist
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="🎯 Misiones", callback_data="admin_missions")
            builder.button(text="🏆 Logros", callback_data="admin_achievements")
            builder.button(text="⭐ Puntos", callback_data="admin_points")
            builder.button(text="📊 Estadísticas", callback_data="admin_gamification_stats")
            builder.button(text="🔙 Volver", callback_data="admin_main")
            builder.adjust(2)
            
            text = "🎮 **Panel de Gamificación**\n\n" \
                   "Gestiona misiones, logros y sistema de puntos."
            
            return text, builder.as_markup()
    
    async def _create_narrative_menu(self, user_id: int, session: AsyncSession) -> Tuple[str, InlineKeyboardMarkup]:
        """Create the narrative menu for a user."""
        from services.narrative_engine import NarrativeEngine
        from keyboards.narrative_kb import get_narrative_stats_keyboard
        
        engine = NarrativeEngine(session)
        stats = await engine.get_user_narrative_stats(user_id)
        
        if stats["current_fragment"]:
            text = f"""📖 **Tu Historia con Diana**

🎭 **Fragmento Actual**: {stats['current_fragment']}
📊 **Progreso**: {stats['progress_percentage']:.1f}%
🗺️ **Fragmentos Visitados**: {stats['fragments_visited']}

*Lucien te está esperando para continuar...*"""
        else:
            text = """📖 **El Diván de Diana**

🌟 **Historia no iniciada**

*Una mansión misteriosa te espera. Lucien, el mayordomo, está listo para guiarte a través de los secretos de Diana.*

*¿Te atreves a comenzar esta aventura?*"""
        
        return text, get_narrative_stats_keyboard()
    
    def _create_fallback_menu(self, role: str = "free") -> Tuple[str, InlineKeyboardMarkup]:
        """
        Create a fallback menu when something goes wrong.
        Tries to provide a role-appropriate fallback.
        """
        text = "⚠️ **Error de Navegación**\n\n" \
               "Hubo un problema al cargar el menú. Por favor, intenta nuevamente."
        
        if role == "admin":
            return (text, get_admin_main_kb())
        elif role == "vip":
            return (text, get_vip_main_kb())
        else: # Default for 'free' or unknown
            return (text, get_free_main_menu_kb())

    def create_setup_choice_menu(self) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Crea el texto y el teclado para la elección inicial de configuración del admin.
        Este método está diseñado para ser llamado por handlers/start.py
        """
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🚀 Configurar Ahora", callback_data="start_setup")
        builder.button(text="⏭️ Ir al Panel", callback_data="skip_to_admin")
        builder.button(text="📖 Ver Guía", callback_data="show_setup_guide")
        builder.adjust(1)
        
        text = (
            "👋 **¡Hola, Administrador!**\n\n"
            "Parece que es la primera vez que usas este bot. "
            "Te guiaré a través de una configuración rápida para que "
            "esté listo para tus usuarios.\n\n"
            "**¿Quieres configurar el bot ahora?**\n"
            "• ✅ Configuración guiada (recomendado)\n"
            "• ⏭️ Ir directo al panel de administración\n\n"
            "La configuración solo toma unos minutos y puedes "
            "cambiar todo después."
        )
        return text, builder.as_markup()

    def _get_current_menu_state_from_text(self, text: str) -> str:
        """
        Intenta inferir el estado del menú a partir de su texto.
        Esto es un helper para la lógica de personalización en cmd_start.
        """
        text_lower = text.lower()
        if "panel de administración" in text_lower:
            return "admin_main"
        elif "bienvenido al diván de diana" in text_lower or "experiencia premium" in text_lower:
            return "vip_main"
        elif "bienvenido a los kinkys" in text_lower or "explora nuestro contenido gratuito" in text_lower:
            return "free_main"
        return "unknown" # O un estado por defecto

    async def cleanup_menu_cache(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up expired menu cache entries.

        Args:
            max_age_seconds: Maximum age for cache entries in seconds

        Returns:
            Number of entries cleaned up
        """
        try:
            current_time = datetime.now().timestamp()
            expired_keys = []

            for cache_key, (content, timestamp) in self._menu_cache.items():
                if (current_time - timestamp) > max_age_seconds:
                    expired_keys.append(cache_key)

            for key in expired_keys:
                self._menu_cache.pop(key, None)

            logger.debug(f"Cleaned up {len(expired_keys)} expired menu cache entries")
            return len(expired_keys)

        except Exception as e:
            logger.error(f"Error cleaning up menu cache: {e}")
            return 0

    async def cleanup_admin_context_cache(self, max_age_seconds: int = 1800) -> int:
        """
        Clean up expired admin context cache entries.

        Args:
            max_age_seconds: Maximum age for admin context cache in seconds

        Returns:
            Number of entries cleaned up
        """
        try:
            current_time = datetime.now().timestamp()
            expired_users = []

            for user_id, (context, cache_time) in self._admin_context_cache.items():
                if (current_time - cache_time) > max_age_seconds:
                    expired_users.append(user_id)

            for user_id in expired_users:
                self._admin_context_cache.pop(user_id, None)

            logger.debug(f"Cleaned up {len(expired_users)} expired admin context cache entries")
            return len(expired_users)

        except Exception as e:
            logger.error(f"Error cleaning up admin context cache: {e}")
            return 0

    async def refresh_admin_context(self, user_id: int, session: AsyncSession) -> Dict[str, Any]:
        """
        Force refresh of admin context cache for a specific user.

        Args:
            user_id: Admin user ID to refresh
            session: Database session

        Returns:
            Refreshed admin context data
        """
        try:
            # Remove from cache to force refresh
            self._admin_context_cache.pop(user_id, None)

            # Get fresh context
            return await self._get_admin_context(user_id, session)

        except Exception as e:
            logger.error(f"Error refreshing admin context for user {user_id}: {e}")
            return {"quick_stats": {}, "system_status": {}, "automation_status": "error"}

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about cache usage and performance.

        Returns:
            Dictionary with cache statistics
        """
        try:
            current_time = datetime.now().timestamp()

            # Menu cache stats
            menu_cache_size = len(self._menu_cache)
            menu_cache_expired = 0
            for _, (_, timestamp) in self._menu_cache.items():
                if (current_time - timestamp) > self._cache_ttl:
                    menu_cache_expired += 1

            # Admin context cache stats
            admin_cache_size = len(self._admin_context_cache)
            admin_cache_expired = 0
            for _, (_, cache_time) in self._admin_context_cache.items():
                if (current_time - cache_time) > self._cache_ttl:
                    admin_cache_expired += 1

            return {
                "menu_cache": {
                    "total_entries": menu_cache_size,
                    "expired_entries": menu_cache_expired,
                    "hit_ratio": "N/A"  # Would need hit/miss tracking
                },
                "admin_context_cache": {
                    "total_entries": admin_cache_size,
                    "expired_entries": admin_cache_expired
                },
                "cache_ttl_seconds": self._cache_ttl
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}

    async def create_menu_with_retry(
        self,
        menu_state: str,
        user_id: int,
        session: AsyncSession,
        bot=None,
        use_html: bool = False,
        user_context: Optional[Dict[str, Any]] = None,
        max_retries: int = 2,
        backoff_factor: float = 1.0
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Create menu with retry mechanism for improved reliability.

        Args:
            menu_state: Menu state to create
            user_id: User ID requesting the menu
            session: Database session
            bot: Bot instance
            use_html: Whether to use HTML formatting
            user_context: Optional user context
            max_retries: Maximum retry attempts
            backoff_factor: Exponential backoff factor

        Returns:
            Tuple of text and keyboard, with fallback on failure
        """
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                return await self.create_menu(
                    menu_state=menu_state,
                    user_id=user_id,
                    session=session,
                    bot=bot,
                    use_html=use_html,
                    user_context=user_context
                )

            except Exception as e:
                last_error = e

                if attempt < max_retries:
                    delay = backoff_factor * (2 ** attempt)
                    logger.warning(f"Menu creation attempt {attempt + 1} failed for user {user_id}, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Menu creation failed after {max_retries + 1} attempts for user {user_id}: {e}")

        # Final fallback
        try:
            role = await get_user_role(bot, user_id, session=session) if bot else "free"
            return self._create_fallback_menu(role)
        except Exception as fallback_error:
            logger.error(f"Even fallback menu creation failed for user {user_id}: {fallback_error}")
            # Ultimate fallback
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="🔄 Reintentar", callback_data="main")
            return (
                "⚠️ **Error del Sistema**\n\nNo se pudo cargar el menú. Intenta nuevamente.",
                builder.as_markup()
            )

    async def create_error_recovery_menu(
        self,
        error_type: str,
        user_id: int,
        original_menu_state: str = "main",
        additional_info: Optional[str] = None
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Create a menu for error recovery scenarios.

        Args:
            error_type: Type of error that occurred
            user_id: User ID for context
            original_menu_state: The menu state that failed
            additional_info: Additional error information

        Returns:
            Error recovery menu with appropriate options
        """
        try:
            if HTML_AVAILABLE:
                recovery_options = [
                    "Reintentar operación",
                    "Volver al menú principal",
                    "Contactar soporte"
                ]

                text = HTMLMessageFormatter.format_error_message(
                    error_code=f"MENU_ERROR_{error_type.upper()}",
                    details=f"Error al cargar menú: {original_menu_state}",
                    recovery_options=recovery_options
                )
                parse_mode = "HTML"
            else:
                text = f"""⚠️ **Error del Sistema**

**Tipo:** {error_type}
**Menú:** {original_menu_state}

{additional_info if additional_info else "Se produjo un error inesperado."}

**Opciones de recuperación:**
1. Reintentar la operación
2. Volver al menú principal
3. Contactar soporte técnico"""

            # Create recovery keyboard
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()

            builder.button(text="🔄 Reintentar", callback_data=original_menu_state)
            builder.button(text="🏠 Menú Principal", callback_data="main")
            builder.button(text="💬 Soporte", callback_data="support_contact")
            builder.adjust(1)

            return text, builder.as_markup()

        except Exception as e:
            logger.error(f"Error creating error recovery menu for user {user_id}: {e}")
            # Ultra-basic fallback
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="🏠 Inicio", callback_data="main")
            return "⚠️ Error del sistema. Use el botón para volver al inicio.", builder.as_markup()

# Global factory instance
menu_factory = MenuFactory()
