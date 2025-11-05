"""
Menu factory for creating consistent menus based on user role and state.
Centralizes menu creation logic for better maintainability.
"""
from typing import Tuple, Optional
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession
from utils.user_roles import get_user_role
from keyboards.admin_main_kb import get_admin_main_kb
from keyboards.vip_main_kb import get_vip_main_kb
from keyboards.subscription_kb import get_free_main_menu_kb
from keyboards.admin_vip_channel_kb import get_admin_vip_channel_kb
from keyboards.free_channel_admin_kb import get_free_channel_admin_kb
from keyboards.admin_experiences_kb import (
    get_admin_experiences_main_kb,
    get_admin_experiences_list_kb,
    get_admin_experience_view_kb,
    get_admin_experience_elements_kb,
    get_admin_experience_back_kb
)
from services import ConfigService
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

logger = logging.getLogger(__name__)

class MenuFactory:
    """
    Factory class for creating menus based on user state and role.
    Centralizes menu logic and ensures consistency.
    All admin menus are designed to use message editing for clean navigation.
    """

    async def create_menu(
        self,
        menu_state: str,
        user_id: int,
        session: AsyncSession,
        bot=None # Asegúrate de que el objeto bot siempre se pase desde los handlers
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Create a menu based on the current state and user role.

        For admin users, menus are designed to be edited in place rather than
        sending new messages, keeping the chat clean.

        Returns:
            Tuple[str, InlineKeyboardMarkup]: (text, keyboard)
        """
        try:
            role = await get_user_role(bot, user_id, session=session)

            # Handle setup flow for new installations
            if menu_state.startswith("setup_") or menu_state == "admin_setup_choice": # Añadido admin_setup_choice aquí
                return await self._create_setup_menu(menu_state, user_id, session)

            # Handle role-based main menus
            if menu_state in ["main", "admin_main", "vip_main", "free_main"]:
                return self._create_main_menu(role)

            # Handle specific menu states
            return await self._create_specific_menu(menu_state, user_id, session, role)

        except Exception as e:
            logger.error(f"Error creating menu for state {menu_state}, user {user_id}: {e}")
            return self._create_fallback_menu(role) 
    
    def _create_main_menu(self, role: str) -> Tuple[str, InlineKeyboardMarkup]:
        """Create the main menu based on user role."""
        if role == "admin":
            text = (
                "🛠️ **Panel de Administración**\n\n"
                "Bienvenido al centro de control del bot. Desde aquí puedes gestionar "
                "todos los aspectos del sistema."
            )
            keyboard = get_admin_main_kb()
        elif role == "vip":
            text = (
                "✨ **Bienvenido al Diván de Diana**\n\n"
                "Tu suscripción VIP te da acceso completo a todas las funciones. "
                "¡Disfruta de la experiencia premium!"
            )
            keyboard = get_vip_main_kb()
        else: # Covers "free" and any other unrecognized roles
            text = (
                "✨ **Bienvenido, mi amor**\n\n"
                "Soy Diana, y me encanta que estés aquí. Este es tu espacio para "
                "descubrir lo que tengo para ti...\n\n"
                "💫 Explora, juega, y descubre. Algunas cosas son para todos, "
                "pero las más íntimas... solo para quienes se atreven a estar más cerca.\n\n"
                "¿Qué te gustaría ver primero?"
            )
            keyboard = get_free_main_menu_kb()
        
        # Add home button to refresh the main menu
        if hasattr(keyboard, 'inline_keyboard'):
            builder = InlineKeyboardBuilder()
            # Add existing buttons
            for row in keyboard.inline_keyboard:
                builder.row(*row)
            # Add home button (refresh)
            builder.button(text="🔄 Actualizar", callback_data="main")
            return text, builder.as_markup()
        return text, keyboard
    
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
            text, keyboard = await create_profile_menu(user_id, session)
        elif menu_state == "missions":
            text, keyboard = await create_missions_menu(user_id, session)
        elif menu_state == "rewards":
            text, keyboard = await create_rewards_menu(user_id, session)
        elif menu_state == "auctions":
            text, keyboard = await create_auction_menu(user_id, session)
        elif menu_state == "ranking":
            text, keyboard = await create_ranking_menu(user_id, session)
        elif menu_state == "narrative":
            text, keyboard = await self._create_narrative_menu(user_id, session)
        elif menu_state == "admin_gamification_main":
            text, keyboard = self._create_main_menu("admin")
        elif menu_state == "admin_vip":
            text, keyboard = self._create_admin_vip_menu()
        elif menu_state == "admin_free":
            text, keyboard = await self._create_admin_free_menu(session)
        elif menu_state.startswith("admin_experiences"):
            text, keyboard = await self._create_experiences_menu(menu_state, user_id, session)
        else:
            logger.warning(f"Unknown specific menu state: {menu_state}. Falling back to main menu for role: {role}")
            text, keyboard = self._create_main_menu(role)
        
        # Add home button to all specific menus
        # Los keyboards ya tienen el botón de menú principal
        # No agregar botón duplicado
        return text, keyboard
    
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
        
        keyboard = get_narrative_stats_keyboard()
        # Los keyboards ya tienen el botón de menú principal
        # No agregar botón duplicado
        return text, keyboard

    async def _create_experiences_menu(
        self, 
        menu_state: str, 
        user_id: int, 
        session: AsyncSession
    ) -> Tuple[str, InlineKeyboardMarkup]:
        """Create experiences-related menus."""
        from services.experience_service import ExperienceService
        
        experience_service = ExperienceService(session)
        
        if menu_state == "admin_experiences_main":
            # Main experiences panel
            total_experiences = await experience_service.get_total_count()
            active_experiences = await experience_service.get_active_count()
            
            text = (
                "🎭 **Panel de Experiencias Unificadas**\n\n"
                "Desde aquí puedes gestionar experiencias que unifican narrativa, tienda y misiones.\n\n"
                f"📊 **Estadísticas:**\n"
                f"• Total de experiencias: {total_experiences}\n"
                f"• Experiencias activas: {active_experiences}\n\n"
                "**Funcionalidades:**\n"
                "• 📋 Ver lista de experiencias\n"
                "• ✨ Crear nueva experiencia\n"
                "• 🔍 Ver elementos propagados\n"
                "• ⚙️ Configurar experiencias\n"
            )
            keyboard = get_admin_experiences_main_kb()
            
        elif menu_state == "admin_experiences_list":
            # Experiences list
            experiences = await experience_service.get_all_experiences()
            
            if not experiences:
                text = (
                    "📋 **Lista de Experiencias**\n\n"
                    "No hay experiencias creadas aún.\n\n"
                    "💡 **Sugerencia:** Crea tu primera experiencia para unificar narrativa, tienda y misiones."
                )
                keyboard = get_admin_experience_back_kb()
            else:
                text = (
                    "📋 **Lista de Experiencias**\n\n"
                    f"Se encontraron {len(experiences)} experiencia(s):\n\n"
                    "💡 **Leyenda:** ✅ Activa | ❌ Inactiva\n"
                )
                keyboard = get_admin_experiences_list_kb(experiences)
                
        elif menu_state == "admin_experience_elements":
            # All propagated elements
            total_fragments = await experience_service.get_total_fragment_count()
            total_items = await experience_service.get_total_item_count()
            total_missions = await experience_service.get_total_mission_count()
            
            text = (
                "🔍 **Elementos Propagados**\n\n"
                "Vista general de todos los elementos creados por experiencias unificadas:\n\n"
                f"📖 **Fragmentos Narrativos:** {total_fragments}\n"
                f"🛒 **Items de Tienda:** {total_items}\n"
                f"🎯 **Misiones:** {total_missions}\n\n"
                "💡 **Nota:** Estos elementos fueron creados automáticamente por el sistema de experiencias unificadas."
            )
            keyboard = get_admin_experience_elements_kb()
            
        elif menu_state == "admin_experience_config":
            # Configuration panel
            text = (
                "⚙️ **Configuración de Experiencias**\n\n"
                "Opciones de configuración del sistema de experiencias unificadas:\n\n"
                "🔧 **Funcionalidades disponibles:**\n"
                "• Propagación automática de elementos\n"
                "• Validación de requisitos compuestos\n"
                "• Gestión de dependencias entre experiencias\n"
                "• Recompensas automáticas\n\n"
                "💡 **Próximamente:**\n"
                "• Asistente visual para creación\n"
                "• Plantillas predefinidas\n"
                "• Análisis de rendimiento\n"
            )
            keyboard = get_admin_experience_back_kb()
            
        else:
            # Fallback for unknown experience states
            text = "⚠️ **Estado de Experiencia Desconocido**\n\nNo se pudo cargar el menú solicitado."
            keyboard = get_admin_experience_back_kb()
            
        return text, keyboard

    def _create_admin_vip_menu(self) -> Tuple[str, InlineKeyboardMarkup]:
        """Creates the admin VIP channel management menu."""
        return (
            "🔐 Administración Canal VIP",
            get_admin_vip_channel_kb(),
        )

    async def _create_admin_free_menu(self, session: AsyncSession) -> Tuple[str, InlineKeyboardMarkup]:
        """Creates the admin free channel management menu."""
        config_service = ConfigService(session)
        channel_id = await config_service.get_value("FREE_CHANNEL_ID")
        channel_configured = channel_id is not None
        return (
            "Menú de Administración de Canal Gratuito",
            get_free_channel_admin_kb(channel_configured=channel_configured),
        )
    
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

# Global factory instance
menu_factory = MenuFactory()
