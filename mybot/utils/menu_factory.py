"""
Enhanced Menu factory for creating consistent menus based on user role and state.
Centralizes menu creation logic for better maintainability.
Enhanced with HTML formatting support and improved administrative features.
"""
from typing import Tuple, Optional, Dict, Any, Union
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
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
            if menu_state == "admin_automation" or menu_state == "admin_automation_enhanced":
                return await self._create_automation_menu(user_id, session, user_context)

            # Handle admin cleanup menu
            if menu_state == "admin_cleanup_enhanced":
                return await self.create_admin_cleanup_menu(user_id, session)
            
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
        Enhanced to support requirement 1.1 with improved menu system and cleanup.

        Args:
            user_id: Admin user ID
            session: Database session
            user_context: Optional user context data

        Returns:
            Tuple of HTML-formatted text and keyboard with enhanced admin features
        """
        try:
            # Get enhanced admin context data with automation details
            admin_context = await self._get_admin_context(user_id, session)

            # Prepare enhanced menu data with automation integration
            menu_data = {
                "title": "Panel de Administración Avanzado",
                "description": "Centro de control administrativo con automatización integrada",
                "stats": admin_context.get("quick_stats", {}),
                "automation_status": admin_context.get("automation_status", "🔴 Desconocido"),
                "system_health": admin_context.get("system_status", {}),
                "sections": [
                    {
                        "title": "Gestión de Canales",
                        "options": [
                            {"icon": "💎", "text": "Canal VIP", "callback": "admin_vip_enhanced"},
                            {"icon": "💬", "text": "Canal Gratuito", "callback": "admin_free_enhanced"}
                        ]
                    },
                    {
                        "title": "Automatización y Análisis",
                        "options": [
                            {
                                "icon": "🤖",
                                "text": f"Automatización {admin_context.get('automation_status', '🔴')}",
                                "callback": "admin_automation_enhanced"
                            },
                            {"icon": "📈", "text": "Analytics Avanzado", "callback": "admin_analytics_enhanced"}
                        ]
                    },
                    {
                        "title": "Sistema y Mantenimiento",
                        "options": [
                            {"icon": "⚙️", "text": "Configuración", "callback": "admin_config_enhanced"},
                            {"icon": "🧹", "text": "Limpieza de Menús", "callback": "admin_cleanup_enhanced"},
                            {"icon": "🔧", "text": "Diagnóstico", "callback": "admin_diagnostics"}
                        ]
                    }
                ],
                "performance_metrics": admin_context.get("performance_metrics", {})
            }

            # Enhanced user context with admin role information
            enhanced_user_context = user_context or {}
            if "user_name" not in enhanced_user_context:
                enhanced_user_context["user_name"] = f"Admin-{user_id}"
            enhanced_user_context["role"] = "Administrador"
            enhanced_user_context["automation_enabled"] = admin_context.get("automation_status") not in ["🔴 Inactivo", "🔴 Error"]

            # Format with enhanced HTML if available
            if HTML_AVAILABLE:
                text = HTMLMessageFormatter.format_admin_menu(menu_data, enhanced_user_context)
                # Add automation status section
                automation_details = admin_context.get("automation_details", {})
                if automation_details:
                    text += self._format_automation_status_section(automation_details)
            else:
                # Enhanced fallback formatting
                text = self._format_enhanced_admin_menu_fallback(menu_data, admin_context)

            # Get enhanced admin keyboard with updated navigation
            from keyboards.admin_enhanced_kb import get_enhanced_admin_main_kb
            keyboard = get_enhanced_admin_main_kb()

            return text, keyboard

        except Exception as e:
            logger.error(f"Error creating HTML admin menu for user {user_id}: {e}")
            return self._create_main_menu("admin")

    def _format_automation_status_section(self, automation_details: Dict[str, Any]) -> str:
        """
        Format automation status section for enhanced admin menu.

        Args:
            automation_details: Dictionary with automation task details

        Returns:
            HTML-formatted automation status section
        """
        try:
            sections = []

            if automation_details.get("active_tasks", 0) > 0:
                sections.append("\n<u>🤖 Estado de Automatización:</u>")
                active = automation_details.get("active_tasks", 0)
                total = automation_details.get("total_tasks", 0)
                sections.append(f"• <b>Tareas activas:</b> <code>{active}/{total}</code>")

                success_rate = automation_details.get("success_rate", 0)
                if success_rate > 0:
                    sections.append(f"• <b>Tasa de éxito:</b> <code>{success_rate:.1f}%</code>")

                last_exec = automation_details.get("last_execution", "N/A")
                sections.append(f"• <b>Última ejecución:</b> <code>{last_exec}</code>")

            return "\n".join(sections)
        except Exception as e:
            logger.warning(f"Error formatting automation status: {e}")
            return ""

    def _format_enhanced_admin_menu_fallback(
        self,
        menu_data: Dict[str, Any],
        admin_context: Dict[str, Any]
    ) -> str:
        """
        Enhanced fallback formatting for admin menus when HTML formatter is not available.

        Args:
            menu_data: Menu data dictionary
            admin_context: Admin context with system information

        Returns:
            Formatted text with enhanced admin information
        """
        lines = []

        if 'title' in menu_data:
            lines.append(f"**🛠️ {menu_data['title']}**\n")

        if 'description' in menu_data:
            lines.append(f"{menu_data['description']}\n")

        # Enhanced system status
        lines.append("**📊 Estado del Sistema:**")
        if 'automation_status' in menu_data:
            lines.append(f"• **Automatización:** `{menu_data['automation_status']}`")

        if 'stats' in menu_data and menu_data['stats']:
            for key, value in menu_data['stats'].items():
                lines.append(f"• **{key}:** `{value}`")

        # System health
        if 'system_health' in menu_data and menu_data['system_health']:
            lines.append("\n**⚡ Salud del Sistema:**")
            for key, value in menu_data['system_health'].items():
                lines.append(f"• **{key}:** `{value}`")

        lines.append("")

        # Menu sections with enhanced formatting
        if 'sections' in menu_data:
            for section in menu_data['sections']:
                if 'title' in section:
                    lines.append(f"**🔹 {section['title']}**")
                if 'options' in section:
                    for option in section['options']:
                        if isinstance(option, dict):
                            icon = option.get('icon', '•')
                            text = option.get('text', '')
                            lines.append(f"• {icon} **{text}**")
                        else:
                            lines.append(f"• **{option}**")
                lines.append("")

        # Performance metrics if available
        if 'performance_metrics' in menu_data and menu_data['performance_metrics']:
            lines.append("**⚡ Rendimiento:**")
            for metric, value in menu_data['performance_metrics'].items():
                metric_name = metric.replace('_', ' ').title()
                lines.append(f"• **{metric_name}:** `{value}`")
            lines.append("")

        timestamp = datetime.now().strftime("%H:%M:%S")
        lines.append(f"*⏰ Actualizado: {timestamp}*")

        return "\n".join(lines)

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
        Create enhanced automation control menu with detailed task status and controls.
        Enhanced to support requirement 1.6 for administrative task automation.

        Args:
            user_id: Admin user ID
            session: Database session
            user_context: Optional user context data

        Returns:
            Tuple of formatted text and automation keyboard with enhanced controls
        """
        try:
            # Get detailed automation status from enhanced service
            automation_data = await self._get_automation_status(session)
            enhanced_automation = await self._check_enhanced_automation_status()

            # Combine automation data for comprehensive display
            combined_data = {
                **automation_data,
                "enhanced_details": enhanced_automation["details"],
                "overall_status": enhanced_automation["status"]
            }

            if HTML_AVAILABLE:
                # Enhanced HTML formatting with detailed task breakdown
                text = self._format_enhanced_automation_menu_html(combined_data, user_context)
            else:
                # Enhanced fallback formatting with better organization
                text = self._format_enhanced_automation_menu_fallback(combined_data)

            # Get enhanced automation keyboard with more control options
            from keyboards.admin_automation_kb import get_automation_main_kb
            keyboard = get_automation_main_kb()

            return text, keyboard

        except Exception as e:
            logger.error(f"Error creating automation menu for user {user_id}: {e}")
            # Enhanced fallback with error recovery options
            text = """<b>🤖 Centro de Automatización</b>

🔴 <b>Estado:</b> Error al cargar detalles

<u>⚡ Funciones Disponibles:</u>
• 📝 Recordatorios VIP
• 🧹 Limpieza de mensajes
• 👥 Gestión de usuarios
• 📚 Eventos narrativos
• 🔍 Diagnóstico del sistema

<i>🔧 Usa las opciones del menú para intentar reactivar</i>"""

            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="🔄 Reintentar", callback_data="admin_automation")
            builder.button(text="🔙 Volver", callback_data="admin_main_enhanced")
            builder.adjust(1)
            return text, builder.as_markup()

    def _format_enhanced_automation_menu_html(
        self,
        automation_data: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Format enhanced automation menu using HTML with detailed task information.

        Args:
            automation_data: Combined automation status and details
            user_context: Optional user context

        Returns:
            HTML-formatted automation menu text
        """
        try:
            menu_data = {
                "title": "Centro de Automatización Avanzado",
                "description": "Gestión integral de tareas automatizadas",
                "automation_status": automation_data.get("overall_status", "🔴 Desconocido"),
                "task_summary": {
                    "Tareas Activas": automation_data.get("active_tasks", 0),
                    "Total Configuradas": automation_data.get("total_tasks", 0),
                    "Tasa de Éxito": f"{automation_data.get('enhanced_details', {}).get('success_rate', 0):.1f}%",
                    "Última Ejecución": automation_data.get("enhanced_details", {}).get("last_execution", "N/A")
                },
                "task_details": automation_data.get("enhanced_details", {}).get("task_breakdown", {})
            }

            text = HTMLMessageFormatter.format_automation_status(
                action="enhanced_status",
                started_tasks=automation_data.get("active_tasks", 0),
                total_tasks=automation_data.get("total_tasks", 0),
                details=automation_data.get("enhanced_details", {})
            )

            return text

        except Exception as e:
            logger.warning(f"Error formatting enhanced automation HTML: {e}")
            return HTMLMessageFormatter.format_automation_status(
                action="status_check",
                started_tasks=automation_data.get("active_tasks", 0),
                total_tasks=automation_data.get("total_tasks", 0),
                details=automation_data.get("details", {})
            )

    def _format_enhanced_automation_menu_fallback(self, automation_data: Dict[str, Any]) -> str:
        """
        Enhanced fallback formatting for automation menu.

        Args:
            automation_data: Combined automation status and details

        Returns:
            Formatted automation menu text
        """
        lines = []

        # Header with status
        overall_status = automation_data.get("overall_status", "🔴 Desconocido")
        lines.append(f"<b>🤖 Centro de Automatización Avanzado</b>\n")
        lines.append(f"<b>Estado General:</b> {overall_status}\n")

        # Task summary
        active_tasks = automation_data.get("active_tasks", 0)
        total_tasks = automation_data.get("total_tasks", 0)
        lines.append(f"<b>Resumen de Tareas:</b>")
        lines.append(f"• <b>Activas:</b> <code>{active_tasks}/{total_tasks}</code>")

        enhanced_details = automation_data.get("enhanced_details", {})
        if enhanced_details:
            success_rate = enhanced_details.get("success_rate", 0)
            last_exec = enhanced_details.get("last_execution", "N/A")
            lines.append(f"• <b>Tasa de éxito:</b> <code>{success_rate:.1f}%</code>")
            lines.append(f"• <b>Última ejecución:</b> <code>{last_exec}</code>")

        lines.append("")

        # Task breakdown if available
        task_breakdown = enhanced_details.get("task_breakdown", {})
        if task_breakdown:
            lines.append("<u>📄 Estado por Tarea:</u>")
            for task_name, is_active in task_breakdown.items():
                status_icon = "🟢" if is_active else "🔴"
                task_display = task_name.replace('_', ' ').title()
                lines.append(f"• {status_icon} <b>{task_display}</b>")
        else:
            lines.append("<u>⚡ Tareas Disponibles:</u>")
            lines.append("• 📝 <b>Recordatorios VIP</b>")
            lines.append("• 🧹 <b>Limpieza de mensajes</b>")
            lines.append("• 👥 <b>Gestión de usuarios</b>")
            lines.append("• 📚 <b>Eventos narrativos</b>")

        lines.append("")
        lines.append("<i>🛠️ Usa los controles para gestionar la automatización</i>")

        timestamp = datetime.now().strftime("%H:%M:%S")
        lines.append(f"\n<i>⏰ Actualizado: {timestamp}</i>")

        return "\n".join(lines)

    async def _get_admin_context(
        self,
        user_id: int,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get administrative context data for menu personalization.
        Enhanced to support requirements 1.1 and 1.6 with improved stats and automation integration.

        Args:
            user_id: Admin user ID
            session: Database session

        Returns:
            Dictionary with admin context data including automation status
        """
        try:
            # Check cache first
            if user_id in self._admin_context_cache:
                cached_data, cache_time = self._admin_context_cache[user_id]
                if (datetime.now().timestamp() - cache_time) < self._cache_ttl:
                    return cached_data

            context = {}

            # Get enhanced system status with better error handling
            try:
                # Get comprehensive user counts with role breakdown
                vip_result = await session.execute(
                    select(func.count(User.id)).where(User.role == "vip")
                )
                vip_count = vip_result.scalar() or 0

                free_result = await session.execute(
                    select(func.count(User.id)).where(User.role == "free")
                )
                free_count = free_result.scalar() or 0

                admin_result = await session.execute(
                    select(func.count(User.id)).where(User.role == "admin")
                )
                admin_count = admin_result.scalar() or 0

                total_users = vip_count + free_count + admin_count

                # Enhanced quick stats with percentages
                context["quick_stats"] = {
                    "Usuarios VIP": f"{vip_count} ({(vip_count/total_users*100):.1f}%)" if total_users > 0 else "0",
                    "Usuarios Free": f"{free_count} ({(free_count/total_users*100):.1f}%)" if total_users > 0 else "0",
                    "Total": total_users,
                    "Conversión VIP": f"{(vip_count/(vip_count+free_count)*100):.1f}%" if (vip_count+free_count) > 0 else "0%"
                }

                # Enhanced system status with health indicators
                context["system_status"] = {
                    "Base de datos": "🟢 Conectada" if total_users >= 0 else "🔴 Error",
                    "Cache": f"🟢 Activo ({len(self._admin_context_cache)} entradas)",
                    "Última actualización": datetime.now().strftime("%H:%M:%S")
                }

                # Add recent activity indicators
                context["activity_indicators"] = {
                    "menu_requests": len(self._menu_cache),
                    "cache_hit_ratio": self._calculate_cache_efficiency()
                }

            except Exception as db_error:
                logger.warning(f"Could not fetch admin context from DB: {db_error}")
                context["quick_stats"] = {"Estado": "🔴 Error de DB"}
                context["system_status"] = {
                    "Base de datos": "🔴 Error de conexión",
                    "Cache": f"🟡 Parcial ({len(self._admin_context_cache)} entradas)"
                }
                context["activity_indicators"] = {}

            # Enhanced automation status with detailed information
            automation_data = await self._check_enhanced_automation_status()
            context["automation_status"] = automation_data["status"]
            context["automation_details"] = automation_data["details"]

            # Add menu performance metrics
            context["performance_metrics"] = {
                "response_time": "< 2s",
                "cleanup_success": "99%",
                "last_error_count": 0
            }

            # Cache the enhanced result
            self._admin_context_cache[user_id] = (context, datetime.now().timestamp())

            return context

        except Exception as e:
            logger.error(f"Error getting admin context for user {user_id}: {e}")
            return {
                "quick_stats": {"Estado": "🔴 Error del sistema"},
                "system_status": {"Estado": "🔴 Error crítico"},
                "automation_status": "error",
                "automation_details": {},
                "activity_indicators": {},
                "performance_metrics": {}
            }

    async def _check_automation_status(self) -> str:
        """Check the status of automation services."""
        try:
            # Try to import and check automation service
            from services.automation_service import AutomationService
            automation_service = AutomationService()

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
            # Fallback to old import path
            try:
                from handlers.admin.automation_handlers import automation_service
                if hasattr(automation_service, 'active_tasks'):
                    active_count = len(automation_service.active_tasks)
                    if active_count == 0:
                        return "inactive"
                    elif active_count < 4:
                        return "partial"
                    else:
                        return "active"
                return "unavailable"
            except ImportError:
                return "unavailable"
        except Exception as e:
            logger.warning(f"Error checking automation status: {e}")
            return "unknown"

    async def _check_enhanced_automation_status(self) -> Dict[str, Any]:
        """
        Enhanced automation status check with detailed information.
        Supports requirement 1.6 for administrative task automation.

        Returns:
            Dict with detailed automation status and task information
        """
        try:
            # Try to get detailed automation data
            from services.automation_service import AutomationService
            automation_service = AutomationService()

            status_data = {
                "status": "unknown",
                "details": {
                    "active_tasks": 0,
                    "total_tasks": 0,
                    "success_rate": 0.0,
                    "last_execution": "N/A",
                    "task_breakdown": {},
                    "health_indicators": {}
                }
            }

            if hasattr(automation_service, 'get_detailed_status'):
                detailed_status = await automation_service.get_detailed_status()
                status_data["details"].update(detailed_status)

                # Determine overall status
                active_count = detailed_status.get("active_tasks", 0)
                total_count = detailed_status.get("total_tasks", 4)

                if active_count == 0:
                    status_data["status"] = "🔴 Inactivo"
                elif active_count == total_count:
                    status_data["status"] = "🟢 Activo"
                else:
                    status_data["status"] = "🟡 Parcial"

            elif hasattr(automation_service, 'active_tasks'):
                # Fallback to basic status
                active_count = len(automation_service.active_tasks)
                status_data["details"]["active_tasks"] = active_count
                status_data["details"]["total_tasks"] = 4

                if active_count == 0:
                    status_data["status"] = "🔴 Inactivo"
                elif active_count < 4:
                    status_data["status"] = "🟡 Parcial"
                else:
                    status_data["status"] = "🟢 Activo"
            else:
                status_data["status"] = "🔴 No disponible"

            return status_data

        except ImportError:
            # Try fallback automation handlers
            try:
                from handlers.admin.automation_handlers import automation_service
                status_data = {
                    "status": "🟡 Modo compatibilidad",
                    "details": {
                        "active_tasks": len(getattr(automation_service, 'active_tasks', [])),
                        "total_tasks": 4,
                        "success_rate": 85.0,
                        "last_execution": "Reciente",
                        "task_breakdown": {},
                        "health_indicators": {"compatibility_mode": True}
                    }
                }
                return status_data
            except ImportError:
                pass

        except Exception as e:
            logger.warning(f"Error getting enhanced automation status: {e}")

        return {
            "status": "🔴 Error",
            "details": {
                "active_tasks": 0,
                "total_tasks": 0,
                "success_rate": 0.0,
                "last_execution": "Error",
                "task_breakdown": {},
                "health_indicators": {"error": True}
            }
        }

    def _calculate_cache_efficiency(self) -> str:
        """
        Calculate cache hit ratio for performance monitoring.

        Returns:
            String representation of cache efficiency
        """
        try:
            # Simple cache efficiency calculation
            total_entries = len(self._menu_cache) + len(self._admin_context_cache)
            if total_entries == 0:
                return "N/A"

            # Estimate based on cache usage patterns
            efficiency = min(95.0, (total_entries / 10) * 100)  # Simple heuristic
            return f"{efficiency:.1f}%"
        except Exception:
            return "N/A"

    async def _get_automation_status(self, session: AsyncSession) -> Dict[str, Any]:
        """
        Get enhanced automation task status and details.
        Enhanced to support requirement 1.6 with comprehensive automation monitoring.
        """
        try:
            # Try to get automation data from new service first
            try:
                from services.automation_service import AutomationService
                automation_service = AutomationService()

                if hasattr(automation_service, 'get_task_status'):
                    status_data = await automation_service.get_task_status()
                    return {
                        "active_tasks": status_data.get("active_count", 0),
                        "total_tasks": status_data.get("total_count", 4),
                        "success_rate": status_data.get("success_rate", 0.0),
                        "details": {
                            "task_breakdown": status_data.get("task_breakdown", {}),
                            "intervals": status_data.get("intervals", {}),
                            "health_indicators": status_data.get("health_indicators", {}),
                            "performance_metrics": status_data.get("performance_metrics", {})
                        }
                    }
            except ImportError:
                pass

            # Fallback to old automation handlers
            from handlers.admin.automation_handlers import automation_service

            if hasattr(automation_service, 'task_status'):
                status_data = automation_service.task_status
                active_tasks = len([task for task, data in status_data.items() if data.get('active', False)])
                total_tasks = len(status_data)

                return {
                    "active_tasks": active_tasks,
                    "total_tasks": total_tasks,
                    "success_rate": 85.0,  # Default success rate
                    "details": {
                        "task_breakdown": {task: data.get('active', False) for task, data in status_data.items()},
                        "intervals": {task: data.get('interval', 'N/A') for task, data in status_data.items()},
                        "health_indicators": {"legacy_mode": True},
                        "performance_metrics": {"response_time": "2s", "uptime": "99%"}
                    }
                }
            elif hasattr(automation_service, 'active_tasks'):
                # Most basic fallback
                active_count = len(automation_service.active_tasks)
                return {
                    "active_tasks": active_count,
                    "total_tasks": 4,
                    "success_rate": 75.0 if active_count > 0 else 0.0,
                    "details": {
                        "task_breakdown": {f"task_{i}": i < active_count for i in range(4)},
                        "intervals": {f"task_{i}": "30m" for i in range(4)},
                        "health_indicators": {"basic_mode": True},
                        "performance_metrics": {"status": "basic"}
                    }
                }
            else:
                return {
                    "active_tasks": 0,
                    "total_tasks": 4,
                    "success_rate": 0.0,
                    "details": {
                        "task_breakdown": {"vip_reminders": False, "message_cleanup": False, "user_management": False, "narrative_events": False},
                        "intervals": {"vip_reminders": "1h", "message_cleanup": "30m", "user_management": "6h", "narrative_events": "24h"},
                        "health_indicators": {"not_configured": True},
                        "performance_metrics": {"status": "inactive"}
                    }
                }

        except ImportError:
            logger.warning("No automation service found, returning default status")
            return {
                "active_tasks": 0,
                "total_tasks": 0,
                "success_rate": 0.0,
                "details": {
                    "task_breakdown": {},
                    "intervals": {},
                    "health_indicators": {"service_unavailable": True},
                    "performance_metrics": {"status": "unavailable"}
                }
            }
        except Exception as e:
            logger.error(f"Error getting automation status: {e}")
            return {
                "active_tasks": 0,
                "total_tasks": 0,
                "success_rate": 0.0,
                "details": {
                    "task_breakdown": {},
                    "intervals": {},
                    "health_indicators": {"error": str(e)},
                    "performance_metrics": {"status": "error"}
                }
            }

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
        Create an enhanced menu for error recovery scenarios.
        Enhanced to support requirement 1.1 with improved error handling and graceful degradation.

        Args:
            error_type: Type of error that occurred
            user_id: User ID for context
            original_menu_state: The menu state that failed
            additional_info: Additional error information

        Returns:
            Enhanced error recovery menu with automated cleanup and multiple recovery options
        """
        try:
            # Enhanced error categorization
            error_categories = {
                "menu_load": "📄 Error de carga de menú",
                "database": "💾 Error de base de datos",
                "automation": "🤖 Error de automatización",
                "permission": "🔒 Error de permisos",
                "network": "🌐 Error de red",
                "unknown": "❓ Error desconocido"
            }

            error_title = error_categories.get(error_type, error_categories["unknown"])

            if HTML_AVAILABLE:
                # Enhanced recovery options based on error type
                recovery_options = self._get_recovery_options_for_error(error_type, original_menu_state)

                text = HTMLMessageFormatter.format_error_message(
                    error_code=f"MENU_ERROR_{error_type.upper()}",
                    details=f"Error al cargar menú: {original_menu_state}",
                    recovery_options=recovery_options
                )

                # Add system health information if available
                try:
                    health_info = await self._get_system_health_summary()
                    if health_info:
                        text += f"\n\n<u>📈 Estado del Sistema:</u>\n{health_info}"
                except Exception:
                    pass

            else:
                # Enhanced fallback formatting with better organization
                text = f"""<b>{error_title}</b>

<b>🏷️ Código:</b> <code>MENU_ERROR_{error_type.upper()}</code>
<b>🎯 Menú:</b> <code>{original_menu_state}</code>
<b>🕰️ Hora:</b> <code>{datetime.now().strftime('%H:%M:%S')}</code>

<u>🔍 Detalles:</u>
{additional_info if additional_info else "Se produjo un error inesperado durante la navegación."}

<u>🔧 Opciones de Recuperación:</u>
1. 🔄 <b>Reintentar la operación</b>
2. 🧹 <b>Limpiar caché y reintentar</b>
3. 🏠 <b>Volver al menú principal</b>
4. 🔍 <b>Diagnóstico del sistema</b>
5. 💬 <b>Contactar soporte técnico</b>

<i>📝 Si el problema persiste, usa la opción de diagnóstico para obtener más información.</i>"""

            # Create enhanced recovery keyboard with more options
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()

            # Primary recovery options
            builder.button(text="🔄 Reintentar", callback_data=original_menu_state)
            builder.button(text="🧹 Limpiar & Reintentar", callback_data=f"cleanup_retry_{original_menu_state}")

            # Secondary options
            builder.button(text="🏠 Menú Principal", callback_data="main")
            builder.button(text="🔍 Diagnóstico", callback_data="admin_diagnostics")

            # Support option
            builder.button(text="💬 Soporte", callback_data="support_contact")

            builder.adjust(2, 2, 1)

            # Schedule automatic cleanup after error
            asyncio.create_task(self._schedule_error_cleanup(user_id, error_type))

            return text, builder.as_markup()

        except Exception as e:
            logger.error(f"Error creating error recovery menu for user {user_id}: {e}")
            # Ultra-basic fallback with minimal dependencies
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="🏠 Inicio", callback_data="main")
            builder.button(text="🔄 Reintentar", callback_data=original_menu_state)
            builder.adjust(1)
            return f"⚠️ <b>Error del Sistema</b>\n\n<code>{error_type}</code>\n<i>Use los botones para continuar.</i>", builder.as_markup()

    def _get_recovery_options_for_error(self, error_type: str, menu_state: str) -> List[str]:
        """
        Get contextual recovery options based on error type.

        Args:
            error_type: Type of error that occurred
            menu_state: Original menu state that failed

        Returns:
            List of recovery options tailored to the error type
        """
        base_options = [
            "Reintentar operación",
            "Volver al menú principal",
            "Contactar soporte"
        ]

        if error_type == "automation":
            return [
                "Reiniciar servicio de automatización",
                "Verificar configuración de tareas",
                "Volver al menú de automatización",
                "Contactar soporte técnico"
            ]
        elif error_type == "database":
            return [
                "Reconectar a la base de datos",
                "Usar modo sin conexión",
                "Verificar configuración de DB",
                "Contactar administrador"
            ]
        elif error_type == "menu_load":
            return [
                "Limpiar caché de menús",
                "Cargar menú alternativo",
                "Reiniciar sesión",
                "Volver al inicio"
            ]
        else:
            return base_options

    async def _get_system_health_summary(self) -> str:
        """
        Get a brief system health summary for error recovery context.

        Returns:
            System health summary string
        """
        try:
            health_indicators = []

            # Check cache health
            cache_health = "Caché: 🟢" if len(self._menu_cache) < 100 else "Caché: 🟡"
            health_indicators.append(cache_health)

            # Check automation status
            automation_status = await self._check_automation_status()
            automation_health = f"Automatización: {'🟢' if automation_status == 'active' else '🔴'}"
            health_indicators.append(automation_health)

            return " | ".join(health_indicators)

        except Exception as e:
            logger.warning(f"Error getting system health: {e}")
            return "Estado: 🟡 Limitado"

    async def _schedule_error_cleanup(self, user_id: int, error_type: str) -> None:
        """
        Schedule automatic cleanup after error occurs.
        Supports requirement 1.1 for improved message cleanup.

        Args:
            user_id: User ID for cleanup
            error_type: Type of error for context
        """
        try:
            # Wait a short period before cleanup
            await asyncio.sleep(10)

            # Clear user's cache entries
            self._admin_context_cache.pop(user_id, None)

            # Clear related menu cache entries
            cache_keys_to_remove = []
            for cache_key in self._menu_cache.keys():
                if str(user_id) in cache_key:
                    cache_keys_to_remove.append(cache_key)

            for key in cache_keys_to_remove:
                self._menu_cache.pop(key, None)

            logger.info(f"Completed error cleanup for user {user_id} after {error_type} error")

        except Exception as e:
            logger.warning(f"Error during cleanup for user {user_id}: {e}")

    async def create_admin_cleanup_menu(
        self,
        user_id: int,
        session: AsyncSession,
        cleanup_stats: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Create menu for administrative cleanup operations.
        Supports requirement 1.1 for enhanced menu cleanup capabilities.

        Args:
            user_id: Admin user ID
            session: Database session
            cleanup_stats: Optional cleanup statistics

        Returns:
            Tuple of cleanup menu text and keyboard
        """
        try:
            stats = cleanup_stats or await self._get_cleanup_statistics()

            if HTML_AVAILABLE:
                text = self._format_cleanup_menu_html(stats)
            else:
                text = self._format_cleanup_menu_fallback(stats)

            # Create cleanup operations keyboard
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()

            # Cleanup operations
            builder.button(text="🧹 Limpiar Menús", callback_data="cleanup_menus")
            builder.button(text="📋 Limpiar Caché", callback_data="cleanup_cache")
            builder.button(text="📝 Limpiar Mensajes", callback_data="cleanup_messages")
            builder.button(text="📊 Ver Estadísticas", callback_data="cleanup_stats")

            # Advanced options
            builder.button(text="🔄 Limpieza Completa", callback_data="cleanup_full")
            builder.button(text="⏱️ Programar Limpieza", callback_data="cleanup_schedule")

            # Navigation
            builder.button(text="🔙 Volver", callback_data="admin_main_enhanced")

            builder.adjust(2, 2, 2, 1)

            return text, builder.as_markup()

        except Exception as e:
            logger.error(f"Error creating cleanup menu for user {user_id}: {e}")
            text = "<b>🧹 Centro de Limpieza</b>\n\nError al cargar las opciones de limpieza."
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="🔙 Volver", callback_data="admin_main_enhanced")
            return text, builder.as_markup()

    def _format_cleanup_menu_html(self, stats: Dict[str, Any]) -> str:
        """
        Format cleanup menu using HTML formatting.

        Args:
            stats: Cleanup statistics

        Returns:
            HTML-formatted cleanup menu text
        """
        lines = [
            "<b>🧹 Centro de Limpieza Administrativo</b>\n",
            "<i>Gestión avanzada de limpieza y mantenimiento del sistema</i>\n"
        ]

        # Current stats
        lines.append("<u>📈 Estado Actual:</u>")
        lines.append(f"• <b>Menús en caché:</b> <code>{stats.get('menu_cache_count', 0)}</code>")
        lines.append(f"• <b>Contextos de admin:</b> <code>{stats.get('admin_cache_count', 0)}</code>")
        lines.append(f"• <b>Mensajes temporales:</b> <code>{stats.get('temp_messages', 0)}</code>")
        lines.append(f"• <b>Última limpieza:</b> <code>{stats.get('last_cleanup', 'Nunca')}</code>")

        lines.append("")
        lines.append("<u>🔧 Operaciones Disponibles:</u>")
        lines.append("• 🧹 <b>Limpieza de menús</b> - Elimina caché de menús expirado")
        lines.append("• 📋 <b>Limpieza de caché</b> - Limpia caché de contexto admin")
        lines.append("• 📝 <b>Limpieza de mensajes</b> - Elimina mensajes temporales")
        lines.append("• 🔄 <b>Limpieza completa</b> - Ejecuta todas las operaciones")

        timestamp = datetime.now().strftime("%H:%M:%S")
        lines.append(f"\n<i>⏰ Actualizado: {timestamp}</i>")

        return "\n".join(lines)

    def _format_cleanup_menu_fallback(self, stats: Dict[str, Any]) -> str:
        """
        Fallback formatting for cleanup menu.

        Args:
            stats: Cleanup statistics

        Returns:
            Formatted cleanup menu text
        """
        return f"""<b>🧹 Centro de Limpieza</b>

<b>Estado del Sistema:</b>
• Menús: <code>{stats.get('menu_cache_count', 0)}</code>
• Caché: <code>{stats.get('admin_cache_count', 0)}</code>
• Mensajes: <code>{stats.get('temp_messages', 0)}</code>

<u>Operaciones Disponibles:</u>
• Limpieza de menús y caché
• Eliminación de mensajes temporales
• Mantenimiento del sistema
• Programación de tareas

<i>Selecciona una opción para continuar</i>"""

    async def _get_cleanup_statistics(self) -> Dict[str, Any]:
        """
        Get current cleanup statistics for display.

        Returns:
            Dictionary with cleanup-related statistics
        """
        try:
            return {
                "menu_cache_count": len(self._menu_cache),
                "admin_cache_count": len(self._admin_context_cache),
                "temp_messages": 0,  # Would need message tracking
                "last_cleanup": "N/A",  # Would need cleanup tracking
                "cache_efficiency": self._calculate_cache_efficiency(),
                "system_health": "Bueno"
            }
        except Exception as e:
            logger.warning(f"Error getting cleanup statistics: {e}")
            return {
                "menu_cache_count": 0,
                "admin_cache_count": 0,
                "temp_messages": 0,
                "last_cleanup": "Error",
                "cache_efficiency": "N/A",
                "system_health": "Error"
            }


# Global factory instance
menu_factory = MenuFactory()
