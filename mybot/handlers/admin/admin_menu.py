"""
Enhanced admin menu with improved navigation and multi-tenant support.
"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.admin_main_kb import get_admin_main_kb
from keyboards.admin_kb import get_admin_kb
from utils.user_roles import is_admin
from utils.menu_manager import menu_manager
from utils.menu_factory import menu_factory
from services.admin_service import AdminService
from services import get_admin_statistics
from database.models import User
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
from .narrative_admin import router as narrative_admin_router
from .lucien_config import router as lucien_config_router

router.include_router(vip_router)
router.include_router(free_router)
router.include_router(config_router)
router.include_router(channel_admin_router)
router.include_router(subscription_plans_router)
router.include_router(game_admin_router)
router.include_router(event_admin_router)
router.include_router(admin_config_router)
router.include_router(narrative_admin_router)
router.include_router(lucien_config_router)

@router.message(Command("admin"))
async def admin_start(message: Message, session: AsyncSession):
    """Handler de inicio de administración - Complete admin menu"""
    if not await is_admin(message.from_user.id, session):
        return await message.answer("Acceso denegado")
    
    # Use the comprehensive admin main menu instead of the simple one
    await message.answer(
        "⚙️ **PANEL DE ADMINISTRACIÓN COMPLETO**\n\n"
        "Bienvenido al centro de control del bot. Desde aquí puedes gestionar "
        "todos los aspectos del sistema: usuarios, canales, gamificación, "
        "subastas, eventos y configuraciones avanzadas.",
        reply_markup=await get_admin_main_kb(session)
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
        
        # Get additional admin-specific stats
        admin_service = AdminService(session)
        dashboard_data = await admin_service.get_dashboard_data(callback.from_user.id)
        
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
        
        if "error" not in dashboard_data:
            channels = dashboard_data.get("channels", {})
            config_status = dashboard_data.get("configuration_status", {})
            text_lines.extend([
                f"• Canal VIP: {'✅' if channels.get('vip_channel_id') else '❌'}",
                f"• Canal Gratuito: {'✅' if channels.get('free_channel_id') else '❌'}",
                f"• Gamificación: {'✅' if config_status.get('gamification_configured') else '❌'}"
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
        # Si el keyboard es None, generamos uno personalizado con los nombres de los canales
        if keyboard is None:
            keyboard = await get_admin_main_kb(session)
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
        admin_service = AdminService(session)
        dashboard_data = await admin_service.get_dashboard_data(callback.from_user.id)
        
        config_text = "⚙️ **Configuración del Bot**\n\n"
        
        if "error" not in dashboard_data:
            status = dashboard_data["configuration_status"]
            config_text += "**Estado actual:**\n"
            config_text += f"📢 Canales: {'✅ Configurados' if status['channels_configured'] else '❌ Pendiente'}\n"
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
        # Inform the admin that the token system has been updated
        await menu_manager.send_temporary_message(
            message,
            "ℹ️ **Sistema de Tokens Actualizado**\n\n"
            "El sistema de generación de tokens VIP ha sido actualizado. "
            "Ahora utiliza el nuevo sistema de transacciones VIP. "
            "Por favor, use el panel de administración de VIP para gestionar accesos.",
            auto_delete_seconds=10
        )
    except Exception as e:
        logger.error(f"Error in token generation command: {e}")
        await menu_manager.send_temporary_message(
            message,
            "❌ **Error Temporal**\n\nNo se pudo procesar la solicitud.",
            auto_delete_seconds=5
        )

@router.callback_query(F.data.startswith("generate_token_"))
async def generate_token_callback(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Enhanced token generation with better feedback."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        await callback.answer(
            "ℹ️ Sistema actualizado\n\n"
            "El sistema de tokens ha sido actualizado. "
            "Use el panel de administración de VIP para gestionar accesos.",
            show_alert=True
        )
    except Exception as e:
        logger.error(f"Error in token generation callback: {e}")
        await callback.answer("Error al procesar la solicitud", show_alert=True)

# Callback para gestión del sistema narrativo
@router.callback_query(F.data == "admin_fragments_manage")
async def admin_fragments_redirect(callback: CallbackQuery, session: AsyncSession):
    """Redirigir a la gestión del sistema narrativo."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("❌ Acceso denegado", show_alert=True)
    
    # Importar y llamar al handler principal de administración narrativa
    from handlers.admin.narrative_admin import handle_admin_fragments_manage
    await handle_admin_fragments_manage(callback, session)
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


@router.message(F.text.startswith("/give_hint "))
async def cmd_give_hint(message: Message):
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
