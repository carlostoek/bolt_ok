"""
Enhanced admin menu with improved navigation and multi-tenant support.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.admin_main_kb import get_admin_main_kb
from utils.user_roles import is_admin
from utils.menu_manager import menu_manager
from utils.menu_factory import menu_factory
from services.tenant_service import TenantService
from services import get_admin_statistics
from database.models import Tariff, Token
from uuid import uuid4
from sqlalchemy import select
from utils.messages import BOT_MESSAGES
from utils.keyboard_utils import get_admin_manage_content_keyboard # Importar la función del teclado
from backpack import desbloquear_pista_narrativa

import logging

logger = logging.getLogger(__name__)
router = Router()

# Include all sub-routers
from .vip_menu import router as vip_router
from .free_menu import router as free_router
from .config_menu import router as config_router
from .channel_admin import router as channel_admin_router
from .subscription_plans import router as subscription_plans_router
from .game_admin import router as game_admin_router
from .event_admin import router as event_admin_router
from .admin_config import router as admin_config_router
from .shop_admin import router as shop_admin_router
from .analytics_handlers import router as analytics_router
from .lore_admin_handlers import router as lore_admin_router

# Include narrative admin handlers from root handlers directory
from ..admin_narrative_handlers import router as narrative_handlers_router

router.include_router(vip_router)
router.include_router(free_router)
router.include_router(config_router)
router.include_router(channel_admin_router)
router.include_router(subscription_plans_router)
router.include_router(game_admin_router)
router.include_router(event_admin_router)
router.include_router(admin_config_router)
router.include_router(shop_admin_router)
router.include_router(analytics_router)
router.include_router(lore_admin_router)
router.include_router(narrative_handlers_router)

@router.message(Command("admin"))
async def admin_start(message: Message, session: AsyncSession):
    """Handler de inicio de administración"""
    if not await is_admin(message.from_user.id, session):
        return await message.answer("Acceso denegado")
    
    await message.answer(
        "Panel de Administración",
        reply_markup=get_admin_kb()
    )

@router.message(Command("admin_menu"))
async def admin_menu(message: Message, session: AsyncSession, user_id: int | None = None):
    """Enhanced admin menu command."""
    uid = user_id if user_id is not None else message.from_user.id
    if not is_admin(uid):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nNo tienes permisos de administrador.",
            auto_delete_seconds=5
        )
        return
    
    try:
        text, keyboard = await menu_factory.create_menu("admin_main", uid, session, message.bot)
        await menu_manager.show_menu(message, text, keyboard, session, "admin_main")
    except Exception as e:
        logger.error(f"Error showing admin menu for user {uid}: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo cargar el panel de administración.",
            auto_delete_seconds=5
        )

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery, session: AsyncSession):
    """Enhanced admin statistics with better formatting."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        stats = await get_admin_statistics(session)
        
        # Get additional tenant-specific stats
        tenant_service = TenantService(session)
        tenant_summary = await tenant_service.get_tenant_summary(callback.from_user.id)
        
        text_lines = [
            "📊 **Estadísticas del Sistema**",
            "",
            "👥 **Usuarios**",
            f"• Total: {stats['users_total']}",
            f"• Suscripciones totales: {stats['subscriptions_total']}",
            f"• Activas: {stats['subscriptions_active']}",
            f"• Expiradas: {stats['subscriptions_expired']}",
            "",
            "💰 **Ingresos**",
            f"• Total recaudado: ${stats.get('revenue_total', 0)}",
            "",
            "⚙️ **Configuración**"
        ]
        
        if "error" not in tenant_summary:
            channels = tenant_summary.get("channels", {})
            text_lines.extend([
                f"• Canal VIP: {'✅' if channels.get('vip_channel_id') else '❌'}",
                f"• Canal Gratuito: {'✅' if channels.get('free_channel_id') else '❌'}",
                f"• Tarifas configuradas: {tenant_summary.get('tariff_count', 0)}"
            ])
        
        from keyboards.common import get_back_kb
        await menu_manager.update_menu(
            callback,
            "\n".join(text_lines),
            get_back_kb("admin_main_menu"),
            session,
            "admin_stats",
        )
    except Exception as e:
        logger.error(f"Error showing admin stats: {e}")
        await callback.answer("Error al cargar estadísticas", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery, session: AsyncSession):
    """Enhanced back navigation for admin."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        # Use menu manager's back functionality
        success = await menu_manager.go_back(callback, session, "admin_main")
        if not success:
            # Fallback to main admin menu
            text, keyboard = await menu_factory.create_menu("admin_main", callback.from_user.id, session, callback.bot)
            await menu_manager.update_menu(callback, text, keyboard, session, "admin_main")
    except Exception as e:
        logger.error(f"Error in admin back navigation: {e}")
        await callback.answer("Error en la navegación", show_alert=True)
    
    await callback.answer()

@router.callback_query(F.data == "admin_main_menu")
async def back_to_admin_main(callback: CallbackQuery, session: AsyncSession):
    """Return to main admin menu."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        text, keyboard = await menu_factory.create_menu("admin_main", callback.from_user.id, session, callback.bot)
        await menu_manager.update_menu(callback, text, keyboard, session, "admin_main")
    except Exception as e:
        logger.error(f"Error returning to admin main: {e}")
        await callback.answer("Error al cargar el menú principal", show_alert=True)
    
    await callback.answer()

# --- MODIFICACIÓN: RENOMBRADO Y REUTILIZADO PARA GESTIÓN DE GAMIFICACIÓN ---
@router.callback_query(F.data == "admin_manage_content") # Este sigue siendo el callback de los botones dentro de get_admin_manage_content_keyboard
async def handle_gamification_content_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Shows the comprehensive content and gamification management menu.
    This handler is now the central point for managing all gamification features.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        # El texto se personaliza para este menú principal de gamificación
        text = "🎮 **Panel de Gestión de Gamificación**\n\n" \
               "Desde aquí puedes administrar usuarios, misiones, recompensas, " \
               "niveles, minijuegos, subastas y eventos. Elige una opción para empezar:"
        
        # Reutilizamos el teclado que ya tienes con todas las opciones de gamificación
        keyboard = get_admin_manage_content_keyboard()
        
        await menu_manager.update_menu(
            callback,
            text,
            keyboard,
            session,
            "admin_gamification_main" # Nuevo estado para el historial más descriptivo
        )
    except Exception as e:
        logger.error(f"Error showing gamification content management: {e}")
        await callback.answer("Error al cargar el panel de gamificación", show_alert=True)
    
    await callback.answer()

# --- NUEVO HANDLER PARA EL BOTÓN "JUEGO KINKY" EN EL MENÚ PRINCIPAL DEL ADMIN ---
@router.callback_query(F.data == "admin_kinky_game") # ASUME QUE ESTE ES EL CALLBACK_DATA DE TU BOTÓN "JUEGO KINKY" EN admin_main_kb
async def handle_kinky_game_button_from_main(callback: CallbackQuery, session: AsyncSession):
    """
    Handles the 'Juego Kinky' button click from the main admin menu.
    Redirects to the main gamification management panel.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    # Simplemente llamamos al handler que ya muestra el menú completo de gamificación
    await handle_gamification_content_menu(callback, session)
    # No es necesario un callback.answer() aquí porque handle_gamification_content_menu ya lo hace.


@router.callback_query(F.data == "admin_bot_config")
async def admin_bot_config(callback: CallbackQuery, session: AsyncSession):
    """Enhanced bot configuration menu."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        from keyboards.common import get_back_kb
        
        # Get current configuration status
        tenant_service = TenantService(session)
        tenant_summary = await tenant_service.get_tenant_summary(callback.from_user.id)
        
        config_text = "⚙️ **Configuración del Bot**\n\n"
        
        if "error" not in tenant_summary:
            status = tenant_summary["configuration_status"]
            config_text += "**Estado actual:**\n"
            config_text += f"📢 Canales: {'✅ Configurados' if status['channels_configured'] else '❌ Pendiente'}\n"
            config_text += f"💳 Tarifas: {'✅ Configuradas' if status['tariffs_configured'] else '❌ Pendiente'}\n"
            config_text += f"🎮 Gamificación: {'✅ Configurada' if status['gamification_configured'] else '❌ Pendiente'}\n\n"
            
            if not status["basic_setup_complete"]:
                config_text += "⚠️ **Configuración incompleta**\nAlgunas funciones pueden no estar disponibles."
            else:
                config_text += "✅ **Bot completamente configurado**\nTodas las funciones están disponibles."
        else:
            config_text += "❌ Error al cargar el estado de configuración."
        
        await menu_manager.update_menu(
            callback,
            config_text,
            get_back_kb("admin_main_menu"),
            session,
            "admin_bot_config",
        )
    except Exception as e:
        logger.error(f"Error showing bot config: {e}")
        await callback.answer("Error al cargar la configuración", show_alert=True)
    
    await callback.answer()

# Enhanced token generation with better UX
@router.message(Command("admin_generate_token"))
async def admin_generate_token_cmd(message: Message, session: AsyncSession, bot: Bot):
    """Enhanced token generation command."""
    if not await is_admin(message.from_user.id, session):
        await menu_manager.send_temporary_message(
            message,
            "❌ **Acceso Denegado**\n\nNo tienes permisos de administrador.",
            auto_delete_seconds=5
        )
        return
    
    try:
        result = await session.execute(select(Tariff))
        tariffs = result.scalars().all()
        
        if not tariffs:
            await menu_manager.send_temporary_message(
                message,
                "❌ **Sin Tarifas Configuradas**\n\n"
                "Primero debes configurar las tarifas VIP desde el panel de administración.",
                auto_delete_seconds=8
            )
            return
        
        from keyboards.admin_vip_config_kb import get_tariff_select_kb
        
        await menu_manager.show_menu(
            message,
            "💳 **Generar Token VIP**\n\n"
            "Selecciona la tarifa para la cual quieres generar un token de activación:",
            get_tariff_select_kb(tariffs),
            session,
            "admin_generate_token"
        )
    except Exception as e:
        logger.error(f"Error in token generation command: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo cargar las tarifas.",
            auto_delete_seconds=5
        )

@router.callback_query(F.data.startswith("generate_token_"))
async def generate_token_callback(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Enhanced token generation with better feedback."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        tariff_id = int(callback.data.split("_")[-1])
        tariff = await session.get(Tariff, tariff_id)
        
        if not tariff:
            await callback.answer("Tarifa no encontrada", show_alert=True)
            return
        
        # Generate token
        token_string = str(uuid4())
        token = Token(token_string=token_string, tariff_id=tariff_id)
        session.add(token)
        await session.commit()
        
        # Create activation link
        bot_username = (await bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={token_string}"
        
        from keyboards.common import get_back_kb
        
        success_text = (
            f"✅ **Token VIP Generado**\n\n"
            f"📋 **Tarifa:** {tariff.name}\n"
            f"⏱️ **Duración:** {tariff.duration_days} días\n"
            f"💰 **Precio:** ${tariff.price}\n\n"
            f"🔗 **Enlace de activación:**\n"
            f"`{link}`\n\n"
            f"⚠️ **Importante:** Este enlace es de un solo uso. "
            f"Compártelo directamente con el cliente."
        )
        
        await menu_manager.update_menu(
            callback,
            success_text,
            get_back_kb("admin_vip"),
            session,
            "token_generated"
        )
        
        logger.info(f"Admin {callback.from_user.id} generated token for tariff {tariff.name}")
    except Exception as e:
        logger.error(f"Error generating token: {e}")
        await callback.answer("Error al generar el token", show_alert=True)
    
    await callback.answer()

# Nuevo callback para gestión del canal gratuito
@router.callback_query(F.data == "admin_free_channel")
async def admin_free_channel_redirect(callback: CallbackQuery, session: AsyncSession):
    """Redirigir a la gestión del canal gratuito."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    # Importar y llamar al handler del canal gratuito
    from handlers.free_channel_admin import free_channel_admin_menu
    await free_channel_admin_menu(callback, session)


# COMPREHENSIVE NARRATIVE MANAGEMENT

@router.callback_query(F.data == "admin_narrative_main")
async def show_narrative_admin_main(callback: CallbackQuery, session: AsyncSession):
    """
    Display the main narrative administration menu with comprehensive management options.

    This handler serves as the central entry point for all narrative management features,
    implementing requirements 1.1 (Enhanced Narrative Content Management System) and
    4.1 (Comprehensive Analytics and User Journey Tracking).
    """
    # Admin authentication check using existing patterns
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Get narrative system overview statistics
        from sqlalchemy import select, func
        from database.narrative_models import StoryFragment, UserNarrativeState
        from database.models import LorePiece, UserLorePiece

        # Count story fragments
        fragments_stmt = select(func.count()).select_from(StoryFragment)
        fragments_result = await session.execute(fragments_stmt)
        total_fragments = fragments_result.scalar() or 0

        # Count lore pieces
        lore_stmt = select(func.count()).select_from(LorePiece).where(LorePiece.is_active == True)
        lore_result = await session.execute(lore_stmt)
        total_lore = lore_result.scalar() or 0

        # Count active users in narrative system
        users_stmt = select(func.count()).select_from(UserNarrativeState)
        users_result = await session.execute(users_stmt)
        active_users = users_result.scalar() or 0

        # Build comprehensive narrative admin menu text
        menu_text = "📚 **Panel de Gestión Narrativa Integral**\n\n"
        menu_text += "Centro de administración para todo el contenido narrativo del sistema.\n\n"

        menu_text += "📊 **Estado del Sistema:**\n"
        menu_text += f"• Fragmentos narrativos: {total_fragments}\n"
        menu_text += f"• Piezas de lore: {total_lore}\n"
        menu_text += f"• Usuarios activos: {active_users}\n\n"

        menu_text += "**🎯 Funciones disponibles:**\n"
        menu_text += "• Gestión completa de fragmentos narrativos\n"
        menu_text += "• Administración de contenido de lore\n"
        menu_text += "• Analytics y seguimiento de usuarios\n"
        menu_text += "• Validación de consistencia narrativa\n"
        menu_text += "• Herramientas de monitoreo del sistema\n\n"

        menu_text += "**Selecciona una opción para continuar:**"

        # Get the narrative admin main keyboard
        from keyboards.admin_narrative_kb import get_narrative_admin_main_kb
        keyboard = get_narrative_admin_main_kb()

        # Update the menu using existing menu manager pattern
        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_narrative_main"
        )

        logger.info(f"Narrative admin main menu displayed for admin {callback.from_user.id}")

    except Exception as e:
        logger.error(f"Error showing narrative admin main menu for user {callback.from_user.id}: {e}")
        await callback.answer("❌ Error al cargar el panel de gestión narrativa", show_alert=True)

    await callback.answer()

@router.callback_query(F.data == "admin_narrative_fragments")
async def show_narrative_fragments_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Display the story fragments management menu.

    Implements requirement 1.1 - Story fragment management organized by level and progression path.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        from keyboards.admin_narrative_kb import get_fragment_management_kb

        menu_text = "📖 **Gestión de Fragmentos Narrativos**\n\n"
        menu_text += "Administra todos los fragmentos de la historia organizados por nivel y ruta de progresión.\n\n"

        menu_text += "**🔧 Herramientas disponibles:**\n"
        menu_text += "• Crear nuevos fragmentos con editor enriquecido\n"
        menu_text += "• Editar fragmentos existentes preservando la integridad\n"
        menu_text += "• Organizar por nivel y ruta de progresión\n"
        menu_text += "• Configurar condiciones de acceso complejas\n"
        menu_text += "• Validar consistencia narrativa automáticamente\n\n"

        menu_text += "**Selecciona una acción:**"

        keyboard = get_fragment_management_kb()

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_narrative_fragments"
        )

    except Exception as e:
        logger.error(f"Error showing fragments menu: {e}")
        await callback.answer("❌ Error al cargar gestión de fragmentos", show_alert=True)

    await callback.answer()

@router.callback_query(F.data == "admin_narrative_analytics")
async def show_narrative_analytics_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Display narrative-specific analytics menu with direct integration to analytics system.

    Implements requirement 4.1 - Analytics integration from narrative admin panel.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        # Redirect to the comprehensive analytics admin menu with narrative focus
        from .analytics_handlers import show_analytics_admin_menu
        await show_analytics_admin_menu(callback, session)

    except Exception as e:
        logger.error(f"Error showing narrative analytics: {e}")
        await callback.answer("❌ Error al cargar analytics narrativos", show_alert=True)

@router.callback_query(F.data == "admin_narrative_validate")
async def validate_narrative_system(callback: CallbackQuery, session: AsyncSession):
    """
    Perform comprehensive narrative system validation.

    Implements requirement 1.1 - Narrative consistency validation and system health monitoring.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        await callback.answer("🔍 Ejecutando validación completa del sistema narrativo...", show_alert=False)

        from services.narrative_admin_service import NarrativeAdminService
        admin_service = NarrativeAdminService(session)

        # Perform comprehensive validation
        report = await admin_service.validate_narrative_consistency()

        menu_text = "🔍 **Validación del Sistema Narrativo**\n\n"

        if report["status"] == "ok":
            menu_text += "✅ **Sistema Consistente**\n\n"
            menu_text += "La narrativa es consistente y no se encontraron problemas.\n\n"
            menu_text += f"📊 **Estadísticas:**\n"
            menu_text += f"• Fragmentos totales: {report['summary']['total_fragments']}\n"
            menu_text += f"• Fragmentos accesibles: {report['summary']['reachable_fragments']}\n"
            menu_text += f"• Integridad: 100%\n\n"
            menu_text += "🏥 **Estado del sistema:** Saludable"

        elif report["status"] == "empty":
            menu_text += "⚠️ **Sistema Vacío**\n\n"
            menu_text += "No hay fragmentos narrativos en la base de datos.\n"
            menu_text += "Considera cargar contenido narrativo inicial."

        elif report["status"] == "error":
            menu_text += "❌ **Errores Críticos Detectados**\n\n"
            error_msg = "\n".join(report["issues"])
            menu_text += f"{error_msg}\n\n"
            menu_text += "🚨 **Acción requerida:** Revisar y corregir errores críticos."

        else:  # issues_found
            menu_text += "⚠️ **Problemas Detectados**\n\n"

            summary = report['summary']
            menu_text += f"📊 **Resumen:**\n"
            menu_text += f"• Fragmentos totales: {summary['total_fragments']}\n"
            menu_text += f"• Fragmentos accesibles: {summary['reachable_fragments']}\n"
            menu_text += f"• Fragmentos huérfanos: {summary['orphaned_count']}\n"
            menu_text += f"• Enlaces rotos: {summary['broken_link_count']}\n\n"

            # Show specific issues
            if report.get("orphaned_fragments"):
                orphaned = ", ".join(report["orphaned_fragments"][:3])
                if len(report["orphaned_fragments"]) > 3:
                    orphaned += f" y {len(report['orphaned_fragments']) - 3} más"
                menu_text += f"🔗 **Fragmentos huérfanos:** {orphaned}\n"

            if report.get("broken_links"):
                broken_count = len(report["broken_links"])
                menu_text += f"❌ **Enlaces rotos:** {broken_count} detectados\n"

            menu_text += "\n💡 **Recomendación:** Revisar y corregir problemas detectados."

        from keyboards.common import get_back_kb
        keyboard = get_back_kb("admin_narrative_main")

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_narrative_validate"
        )

        logger.info(f"Narrative validation performed by admin {callback.from_user.id}: {report['status']}")

    except Exception as e:
        logger.error(f"Error in narrative validation: {e}")
        await callback.answer("❌ Error al validar el sistema narrativo", show_alert=True)

@router.callback_query(F.data == "admin_narrative_import")
async def show_narrative_import_menu(callback: CallbackQuery, session: AsyncSession):
    """
    Display bulk import options for narrative content.

    Implements requirement 1.1 - Bulk content management capabilities.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        menu_text = "📦 **Importación Masiva de Contenido**\n\n"
        menu_text += "Importa y gestiona contenido narrativo en lote desde archivos estructurados.\n\n"

        menu_text += "**📁 Formatos soportados:**\n"
        menu_text += "• JSON - Fragmentos narrativos estructurados\n"
        menu_text += "• CSV - Datos tabulares de lore\n"
        menu_text += "• Archivos de texto - Contenido narrativo\n\n"

        menu_text += "**🔧 Herramientas disponibles:**\n"
        menu_text += "• Validación automática de consistencia\n"
        menu_text += "• Importación por lotes con rollback\n"
        menu_text += "• Verificación de dependencias\n"
        menu_text += "• Mapeo automático de referencias\n\n"

        menu_text += "**🚀 Para importar contenido:**\n"
        menu_text += "Usa el comando `/upload_narrative` y sigue las instrucciones.\n\n"

        menu_text += "**📋 Comando de carga directa:**\n"
        menu_text += "Usa `/load_narrative` para cargar desde el directorio del sistema."

        from keyboards.common import get_back_kb
        keyboard = get_back_kb("admin_narrative_main")

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_narrative_import"
        )

    except Exception as e:
        logger.error(f"Error showing import menu: {e}")
        await callback.answer("❌ Error al cargar menú de importación", show_alert=True)

    await callback.answer()

@router.callback_query(F.data == "admin_narrative_user_tools")
async def show_narrative_user_tools(callback: CallbackQuery, session: AsyncSession):
    """
    Display user management tools for narrative system.

    Implements requirement 4.1 - User journey tracking and admin management tools.
    """
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)

    try:
        menu_text = "🎮 **Herramientas de Gestión de Usuarios**\n\n"
        menu_text += "Administra usuarios, progreso narrativo y seguimiento del sistema.\n\n"

        menu_text += "**🔧 Herramientas disponibles:**\n"
        menu_text += "• Resetear progreso narrativo de usuarios\n"
        menu_text += "• Otorgar pistas y fragmentos específicos\n"
        menu_text += "• Ver progreso detallado de usuarios\n"
        menu_text += "• Gestionar estados de progresión\n"
        menu_text += "• Herramientas de debugging narrativo\n\n"

        menu_text += "**📋 Comandos administrativos:**\n"
        menu_text += "• `/give_hint <user_id> <hint_code>` - Otorgar pista\n"
        menu_text += "• `/reset_narrative <user_id>` - Reiniciar progreso\n"
        menu_text += "• `/narrative_stats` - Ver estadísticas del sistema\n"
        menu_text += "• `/validate_narrative` - Validar consistencia\n\n"

        menu_text += "**⚡ Acceso rápido:**\n"
        menu_text += "Usa los comandos directamente o navega por las opciones del menú."

        from keyboards.common import get_back_kb
        keyboard = get_back_kb("admin_narrative_main")

        await menu_manager.update_menu(
            callback,
            menu_text,
            keyboard,
            session,
            "admin_narrative_user_tools"
        )

    except Exception as e:
        logger.error(f"Error showing user tools: {e}")
        await callback.answer("❌ Error al cargar herramientas de usuario", show_alert=True)

    await callback.answer()

@router.message(F.text.startswith("/give_hint "))
async def cmd_give_hint(message: Message, session: AsyncSession):
    """Comando de admin para dar una pista a un usuario."""
    if not await is_admin(message.from_user.id, session):
        await message.answer(
            "❌ **Acceso Denegado**\n\nNo tienes permisos para usar este comando.",
            parse_mode="HTML",
        )
        return

    parts = message.text.split()
    if len(parts) == 3:
        try:
            target_user_id = int(parts[1])
            hint_code_to_give = parts[2]

            success = await desbloquear_pista_narrativa(
                message.bot,
                target_user_id,
                hint_code_to_give,
                {"source": "admin_command", "admin_id": message.from_user.id},
            )

            if success:
                await message.answer(
                    f"✅ Pista '<b>{hint_code_to_give}</b>' desbloqueada para el usuario <b>{target_user_id}</b>.",
                    parse_mode="HTML",
                )
            else:
                await message.answer(
                    f"⚠️ La pista '<b>{hint_code_to_give}</b>' ya la tiene el usuario <b>{target_user_id}</b> o no existe.",
                    parse_mode="HTML",
                )
        except ValueError:
            await message.answer(
                "❌ Uso incorrecto. Formato: <code>/give_hint <user_id> <hint_code></code>",
                parse_mode="HTML",
            )
    else:
        await message.answer(
            "❌ Uso incorrecto. Formato: <code>/give_hint <user_id> <hint_code></code>",
            parse_mode="HTML",
        )
