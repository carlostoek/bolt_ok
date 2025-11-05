"""
Admin handlers for unified experiences management.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.admin_experiences_kb import (
    get_admin_experiences_main_kb,
    get_admin_experiences_list_kb,
    get_admin_experience_view_kb,
    get_admin_experience_elements_kb,
    get_admin_experience_back_kb
)
from utils.user_roles import is_admin
from utils.menu_manager import menu_manager
from services.experience_service import ExperienceService
from services.experience_propagator import ExperiencePropagator
from database.experience_models import UnifiedExperience

import logging

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "admin_experiences_main")
async def admin_experiences_main(callback: CallbackQuery, session: AsyncSession):
    """Main unified experiences management panel."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        experience_service = ExperienceService(session)
        
        # Get basic statistics
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
        
        await menu_manager.update_menu(
            callback,
            text,
            get_admin_experiences_main_kb(),
            session,
            "admin_experiences_main"
        )
    except Exception as e:
        logger.error(f"Error showing experiences main panel: {e}")
        await callback.answer("Error al cargar el panel de experiencias", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "admin_experiences_list")
async def admin_experiences_list(callback: CallbackQuery, session: AsyncSession):
    """Show list of all experiences."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        experience_service = ExperienceService(session)
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
        
        await menu_manager.update_menu(
            callback,
            text,
            keyboard,
            session,
            "admin_experiences_list"
        )
    except Exception as e:
        logger.error(f"Error showing experiences list: {e}")
        await callback.answer("Error al cargar la lista de experiencias", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_experiences_list_"))
async def admin_experiences_list_pagination(callback: CallbackQuery, session: AsyncSession):
    """Handle pagination for experiences list."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        page = int(callback.data.split("_")[-1])
        experience_service = ExperienceService(session)
        experiences = await experience_service.get_all_experiences()
        
        text = (
            "📋 **Lista de Experiencias**\n\n"
            f"Se encontraron {len(experiences)} experiencia(s):\n\n"
            "💡 **Leyenda:** ✅ Activa | ❌ Inactiva\n"
        )
        keyboard = get_admin_experiences_list_kb(experiences, page=page)
        
        await menu_manager.update_menu(
            callback,
            text,
            keyboard,
            session,
            f"admin_experiences_list_{page}"
        )
    except Exception as e:
        logger.error(f"Error in experiences list pagination: {e}")
        await callback.answer("Error en la paginación", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_experience_view_"))
async def admin_experience_view(callback: CallbackQuery, session: AsyncSession):
    """View details of a specific experience."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        experience_id = int(callback.data.split("_")[-1])
        experience_service = ExperienceService(session)
        experience = await experience_service.get_experience_by_id(experience_id)
        
        if not experience:
            await callback.answer("Experiencia no encontrada", show_alert=True)
            return
        
        # Get element counts
        fragment_count = await experience_service.get_fragment_count(experience_id)
        item_count = await experience_service.get_item_count(experience_id)
        mission_count = await experience_service.get_mission_count(experience_id)
        
        text = (
            f"🎭 **Experiencia: {experience.name}**\n\n"
            f"📝 **Descripción:** {experience.description or 'Sin descripción'}\n"
            f"📊 **Estado:** {'✅ Activa' if experience.is_active else '❌ Inactiva'}\n"
            f"🎯 **Nivel requerido:** {experience.required_level or 'Ninguno'}\n"
            f"💎 **Requiere VIP:** {'✅ Sí' if experience.requires_vip else '❌ No'}\n\n"
            f"📊 **Elementos Propagados:**\n"
            f"• 📖 Fragmentos narrativos: {fragment_count}\n"
            f"• 🛒 Items de tienda: {item_count}\n"
            f"• 🎯 Misiones: {mission_count}\n\n"
            f"🎁 **Recompensas:**\n"
            f"• Puntos: {experience.reward_points or 0}\n"
            f"• Días VIP: {experience.reward_vip_days or 0}\n"
            f"• Logros: {len(experience.reward_achievements or [])}\n"
        )
        
        if experience.dependencies:
            text += f"\n🔗 **Dependencias:** {len(experience.dependencies)} experiencia(s)"
        
        await menu_manager.update_menu(
            callback,
            text,
            get_admin_experience_view_kb(experience_id),
            session,
            f"admin_experience_view_{experience_id}"
        )
    except Exception as e:
        logger.error(f"Error viewing experience {callback.data}: {e}")
        await callback.answer("Error al cargar la experiencia", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "admin_experience_create")
async def admin_experience_create(callback: CallbackQuery, session: AsyncSession):
    """Start experience creation wizard."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        text = (
            "✨ **Crear Nueva Experiencia**\n\n"
            "Te guiaré paso a paso para crear una experiencia unificada que incluye:\n\n"
            "📖 **Narrativa** - Fragmentos de historia\n"
            "🛒 **Tienda** - Items para comprar\n"
            "🎯 **Misiones** - Tareas para completar\n\n"
            "💡 **Características:**\n"
            "• Configuración centralizada\n"
            "• Propagación automática\n"
            "• Validación de requisitos\n"
            "• Gestión de dependencias\n\n"
            "¿Estás listo para comenzar?"
        )
        
        from keyboards.admin_experiences_kb import get_admin_experience_wizard_start_kb
        
        await menu_manager.update_menu(
            callback,
            text,
            get_admin_experience_wizard_start_kb(),
            session,
            "admin_experience_create"
        )
    except Exception as e:
        logger.error(f"Error showing experience creation: {e}")
        await callback.answer("Error al mostrar la creación de experiencia", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "admin_experience_elements")
async def admin_experience_elements(callback: CallbackQuery, session: AsyncSession):
    """Show all propagated elements across experiences."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        experience_service = ExperienceService(session)
        
        # Get total element counts
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
        
        await menu_manager.update_menu(
            callback,
            text,
            get_admin_experience_elements_kb(),
            session,
            "admin_experience_elements"
        )
    except Exception as e:
        logger.error(f"Error showing experience elements: {e}")
        await callback.answer("Error al cargar los elementos", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "admin_experience_config")
async def admin_experience_config(callback: CallbackQuery, session: AsyncSession):
    """Show experience configuration options."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
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
        
        await menu_manager.update_menu(
            callback,
            text,
            get_admin_experience_back_kb(),
            session,
            "admin_experience_config"
        )
    except Exception as e:
        logger.error(f"Error showing experience config: {e}")
        await callback.answer("Error al cargar la configuración", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_experience_toggle_"))
async def admin_experience_toggle(callback: CallbackQuery, session: AsyncSession):
    """Toggle experience active status."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        experience_id = int(callback.data.split("_")[-1])
        experience_service = ExperienceService(session)
        
        experience = await experience_service.get_experience_by_id(experience_id)
        if not experience:
            await callback.answer("Experiencia no encontrada", show_alert=True)
            return
        
        # Toggle status
        new_status = not experience.is_active
        await experience_service.update_experience_status(experience_id, new_status)
        
        status_text = "activada" if new_status else "desactivada"
        await callback.answer(f"Experiencia {status_text}", show_alert=False)
        
        # Refresh the view
        await admin_experience_view(callback, session)
        
    except Exception as e:
        logger.error(f"Error toggling experience {callback.data}: {e}")
        await callback.answer("Error al cambiar el estado", show_alert=True)


# Add to the main admin menu
@router.callback_query(F.data == "admin_experiences")
async def admin_experiences_redirect(callback: CallbackQuery, session: AsyncSession):
    """Redirect to experiences main panel."""
    await admin_experiences_main(callback, session)