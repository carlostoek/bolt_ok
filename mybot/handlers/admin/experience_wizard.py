"""
Experience creation wizard handlers.
Provides a guided, step-by-step process for creating unified experiences.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.admin_experiences_kb import (
    get_admin_experience_wizard_start_kb,
    get_admin_experience_wizard_step_kb,
    get_admin_experience_wizard_confirm_kb,
    get_admin_experience_wizard_cancel_kb
)
from states.experience_wizard_states import ExperienceWizardStates
from utils.user_roles import is_admin
from utils.menu_manager import menu_manager
from services.experience_service import ExperienceService
from services.experience_propagator import ExperiencePropagator

import logging
import uuid

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "admin_experience_wizard_start")
async def admin_experience_wizard_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Start the experience creation wizard."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        # Reset state and start wizard
        await state.clear()
        await state.set_state(ExperienceWizardStates.waiting_for_name)
        
        text = (
            "✨ **Asistente de Creación de Experiencias**\n\n"
            "Te guiaré paso a paso para crear una experiencia unificada que incluye:\n\n"
            "📖 **Narrativa** - Fragmentos de historia\n"
            "🛒 **Tienda** - Items para comprar\n"
            "🎯 **Misiones** - Tareas para completar\n\n"
            "**Paso 1: Información Básica**\n"
            "Por favor, ingresa el **nombre** de la experiencia:\n\n"
            "💡 **Ejemplo:** \"La Mansión de Diana\" o \"El Secreto de Lucien\""
        )
        
        await menu_manager.update_menu(
            callback,
            text,
            get_admin_experience_wizard_cancel_kb(),
            session,
            "admin_experience_wizard_start"
        )
        
    except Exception as e:
        logger.error(f"Error starting experience wizard: {e}")
        await callback.answer("Error al iniciar el asistente", show_alert=True)
    
    await callback.answer()


@router.message(ExperienceWizardStates.waiting_for_name)
async def process_experience_name(message: Message, state: FSMContext, session: AsyncSession):
    """Process experience name and ask for description."""
    if not await is_admin(message.from_user.id, session):
        return
    
    try:
        name = message.text.strip()
        
        if len(name) < 3:
            await message.answer(
                "❌ **Nombre demasiado corto**\n\n"
                "El nombre debe tener al menos 3 caracteres.\n"
                "Por favor, ingresa un nombre más descriptivo:",
                reply_markup=get_admin_experience_wizard_cancel_kb()
            )
            return
        
        if len(name) > 100:
            await message.answer(
                "❌ **Nombre demasiado largo**\n\n"
                "El nombre debe tener máximo 100 caracteres.\n"
                "Por favor, ingresa un nombre más corto:",
                reply_markup=get_admin_experience_wizard_cancel_kb()
            )
            return
        
        # Save name and move to next state
        await state.update_data(name=name)
        await state.set_state(ExperienceWizardStates.waiting_for_description)
        
        text = (
            f"✅ **Nombre guardado:** {name}\n\n"
            "**Paso 2: Descripción**\n"
            "Ahora ingresa una **descripción** para la experiencia:\n\n"
            "💡 **Sugerencias:**\n"
            "• Describe qué experimentará el usuario\n"
            "• Menciona los elementos principales\n"
            "• Hazlo atractivo y misterioso\n\n"
            "**Ejemplo:** \"Una noche en la mansión donde Diana revela sus secretos más íntimos\""
        )
        
        await menu_manager.show_menu(
            message,
            text,
            get_admin_experience_wizard_step_kb("Siguiente: Requisitos", "admin_experience_wizard_requirements"),
            session,
            "admin_experience_wizard_description"
        )
        
    except Exception as e:
        logger.error(f"Error processing experience name: {e}")
        await message.answer(
            "❌ Error al procesar el nombre. Intenta nuevamente:",
            reply_markup=get_admin_experience_wizard_cancel_kb()
        )


@router.message(ExperienceWizardStates.waiting_for_description)
async def process_experience_description(message: Message, state: FSMContext, session: AsyncSession):
    """Process experience description and ask for requirements."""
    if not await is_admin(message.from_user.id, session):
        return
    
    try:
        description = message.text.strip()
        
        if len(description) < 10:
            await message.answer(
                "❌ **Descripción demasiado corta**\n\n"
                "La descripción debe tener al menos 10 caracteres.\n"
                "Por favor, ingresa una descripción más detallada:",
                reply_markup=get_admin_experience_wizard_cancel_kb()
            )
            return
        
        if len(description) > 500:
            await message.answer(
                "❌ **Descripción demasiado larga**\n\n"
                "La descripción debe tener máximo 500 caracteres.\n"
                "Por favor, ingresa una descripción más concisa:",
                reply_markup=get_admin_experience_wizard_cancel_kb()
            )
            return
        
        # Save description and move to requirements
        await state.update_data(description=description)
        
        text = (
            f"✅ **Descripción guardada**\n\n"
            "**Paso 3: Requisitos de Acceso**\n\n"
            "Configura los requisitos para acceder a esta experiencia:\n\n"
            "📊 **Nivel Mínimo:** ¿Qué nivel debe tener el usuario?\n"
            "💎 **Requiere VIP:** ¿Es solo para usuarios premium?\n\n"
            "💡 **Recomendación:**\n"
            "• Experiencias básicas: Sin requisitos\n"
            "• Experiencias avanzadas: Nivel 5+ y VIP\n"
            "• Experiencias exclusivas: Solo VIP"
        )
        
        await menu_manager.show_menu(
            message,
            text,
            get_admin_experience_wizard_step_kb("Configurar Requisitos", "admin_experience_wizard_requirements"),
            session,
            "admin_experience_wizard_requirements"
        )
        
    except Exception as e:
        logger.error(f"Error processing experience description: {e}")
        await message.answer(
            "❌ Error al procesar la descripción. Intenta nuevamente:",
            reply_markup=get_admin_experience_wizard_cancel_kb()
        )


@router.callback_query(F.data == "admin_experience_wizard_requirements")
async def admin_experience_wizard_requirements(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show requirements configuration options."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        data = await state.get_data()
        
        # Get current requirements
        current_level = data.get('required_level', 0)
        current_vip = data.get('requires_vip', False)
        
        text = (
            "⚙️ **Configuración de Requisitos**\n\n"
            "Establece los requisitos para acceder a esta experiencia:\n\n"
            "📊 **Nivel Mínimo:**\n"
            f"• Actual: Nivel {current_level}\n\n"
            "💎 **Acceso VIP:**\n"
            f"• Actual: {'✅ Requerido' if current_vip else '❌ No requerido'}\n\n"
            "💡 **Configuración actual:**\n"
            f"• Nombre: {data.get('name', 'No definido')}\n"
            f"• Descripción: {data.get('description', 'No definida')[:50]}..."
        )
        
        from keyboards.admin_experiences_kb import get_admin_experience_wizard_requirements_kb
        
        await menu_manager.update_menu(
            callback,
            text,
            get_admin_experience_wizard_requirements_kb(),
            session,
            "admin_experience_wizard_requirements"
        )
        
    except Exception as e:
        logger.error(f"Error showing requirements configuration: {e}")
        await callback.answer("Error al cargar la configuración", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "admin_experience_wizard_elements")
async def admin_experience_wizard_elements(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show elements configuration options."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        data = await state.get_data()
        
        # Get current elements configuration
        include_narrative = data.get('include_narrative', True)
        include_shop = data.get('include_shop', True)
        include_missions = data.get('include_missions', True)
        
        text = (
            "🎭 **Configuración de Elementos**\n\n"
            "Selecciona qué elementos incluir en esta experiencia:\n\n"
            "📖 **Fragmentos Narrativos:**\n"
            f"• Actual: {'✅ Incluir' if include_narrative else '❌ No incluir'}\n\n"
            "🛒 **Items de Tienda:**\n"
            f"• Actual: {'✅ Incluir' if include_shop else '❌ No incluir'}\n\n"
            "🎯 **Misiones:**\n"
            f"• Actual: {'✅ Incluir' if include_missions else '❌ No incluir'}\n\n"
            "💡 **Nota:** Puedes agregar estos elementos después de crear la experiencia."
        )
        
        from keyboards.admin_experiences_kb import get_admin_experience_wizard_elements_kb
        
        await menu_manager.update_menu(
            callback,
            text,
            get_admin_experience_wizard_elements_kb(),
            session,
            "admin_experience_wizard_elements"
        )
        
    except Exception as e:
        logger.error(f"Error showing elements configuration: {e}")
        await callback.answer("Error al cargar los elementos", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "admin_experience_wizard_rewards")
async def admin_experience_wizard_rewards(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show rewards configuration options."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        data = await state.get_data()
        
        # Get current rewards configuration
        reward_points = data.get('reward_points', 0)
        reward_vip_days = data.get('reward_vip_days', 0)
        
        text = (
            "🎁 **Configuración de Recompensas**\n\n"
            "Establece las recompensas por completar esta experiencia:\n\n"
            "💰 **Puntos:**\n"
            f"• Actual: {reward_points} puntos\n\n"
            "💎 **Días VIP:**\n"
            f"• Actual: {reward_vip_days} días\n\n"
            "🏅 **Logros:**\n"
            "• Puedes agregar logros después de crear la experiencia\n\n"
            "💡 **Recomendación:**\n"
            "• Experiencias básicas: 50-100 puntos\n"
            "• Experiencias avanzadas: 200-500 puntos + logros\n"
            "• Experiencias exclusivas: 500+ puntos + días VIP"
        )
        
        from keyboards.admin_experiences_kb import get_admin_experience_wizard_rewards_kb
        
        await menu_manager.update_menu(
            callback,
            text,
            get_admin_experience_wizard_rewards_kb(),
            session,
            "admin_experience_wizard_rewards"
        )
        
    except Exception as e:
        logger.error(f"Error showing rewards configuration: {e}")
        await callback.answer("Error al cargar las recompensas", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "admin_experience_wizard_review")
async def admin_experience_wizard_review(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Show final review before creating the experience."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        data = await state.get_data()
        
        # Get all configured values
        name = data.get('name', 'No definido')
        description = data.get('description', 'No definida')
        required_level = data.get('required_level', 0)
        requires_vip = data.get('requires_vip', False)
        include_narrative = data.get('include_narrative', True)
        include_shop = data.get('include_shop', True)
        include_missions = data.get('include_missions', True)
        reward_points = data.get('reward_points', 0)
        reward_vip_days = data.get('reward_vip_days', 0)
        
        text = (
            "📋 **Resumen de la Experiencia**\n\n"
            f"🎭 **Nombre:** {name}\n"
            f"📝 **Descripción:** {description}\n\n"
            "⚙️ **Configuración:**\n"
            f"• Nivel requerido: {required_level}\n"
            f"• Requiere VIP: {'✅ Sí' if requires_vip else '❌ No'}\n"
            f"• Narrativa: {'✅ Incluida' if include_narrative else '❌ No incluida'}\n"
            f"• Tienda: {'✅ Incluida' if include_shop else '❌ No incluida'}\n"
            f"• Misiones: {'✅ Incluidas' if include_missions else '❌ No incluidas'}\n"
            f"• Puntos de recompensa: {reward_points}\n"
            f"• Días VIP de recompensa: {reward_vip_days}\n\n"
            "💡 **Nota:** Puedes agregar logros y configurar elementos específicos después de crear la experiencia.\n\n"
            "¿Estás listo para crear esta experiencia?"
        )
        
        await menu_manager.update_menu(
            callback,
            text,
            get_admin_experience_wizard_confirm_kb(),
            session,
            "admin_experience_wizard_review"
        )
        
    except Exception as e:
        logger.error(f"Error showing review: {e}")
        await callback.answer("Error al cargar el resumen", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "admin_experience_wizard_confirm")
async def admin_experience_wizard_confirm(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Confirm and create the experience."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        data = await state.get_data()
        
        # Prepare requirements based on configured values
        requirements = {
            "level": data.get('required_level', 0),
            "vip": data.get('requires_vip', False)
        }
        
        # Prepare rewards based on configured values
        rewards = {
            "points": data.get('reward_points', 0),
            "vip_days": data.get('reward_vip_days', 0),
            "achievements": []
        }
        
        # Prepare narrative flow based on configured elements
        narrative_flow = {
            "include_narrative": data.get('include_narrative', True),
            "include_shop": data.get('include_shop', True),
            "include_missions": data.get('include_missions', True)
        }
        
        # Create the experience with correct parameters
        experience_service = ExperienceService(session)
        experience = await experience_service.create_experience(
            experience_id=str(uuid.uuid4()),
            name=data['name'],
            description=data['description'],
            requirements=requirements,
            triggers={},
            rewards=rewards,
            narrative_flow=narrative_flow
        )
        
        # Clear state
        await state.clear()
        
        text = (
            f"✅ **¡Experiencia Creada Exitosamente!**\n\n"
            f"🎭 **{experience.name}**\n"
            f"📝 {experience.description}\n\n"
            f"🆔 **ID:** {experience.id}\n"
            f"📊 **Estado:** {'✅ Activa' if experience.is_active else '❌ Inactiva'}\n\n"
            "**Próximos pasos:**\n"
            "• Agregar fragmentos narrativos\n"
            "• Configurar items de tienda\n"
            "• Crear misiones relacionadas\n"
            "• Establecer recompensas\n\n"
            "💡 Puedes gestionar estos elementos desde el panel de experiencias."
        )
        
        await menu_manager.update_menu(
            callback,
            text,
            get_admin_experience_wizard_step_kb("Volver al Panel", "admin_experiences_main"),
            session,
            "admin_experience_wizard_complete"
        )
        
        logger.info(f"Admin {callback.from_user.id} created experience: {experience.name} (ID: {experience.id})")
        
    except Exception as e:
        logger.error(f"Error creating experience: {e}")
        await callback.answer("Error al crear la experiencia", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "admin_experience_wizard_cancel")
async def admin_experience_wizard_cancel(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Cancel the wizard and return to experiences main."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        # Clear state
        await state.clear()
        
        text = "❌ **Asistente Cancelado**\n\nLa creación de la experiencia ha sido cancelada."
        
        await menu_manager.update_menu(
            callback,
            text,
            get_admin_experience_wizard_step_kb("Volver al Panel", "admin_experiences_main"),
            session,
            "admin_experience_wizard_cancelled"
        )
        
    except Exception as e:
        logger.error(f"Error cancelling wizard: {e}")
        await callback.answer("Error al cancelar", show_alert=True)
    
    await callback.answer()


# Requirements configuration handlers
@router.callback_query(F.data.startswith("admin_experience_wizard_level_"))
async def admin_experience_wizard_set_level(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Set required level for the experience."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        level = int(callback.data.split("_")[-1])
        await state.update_data(required_level=level)
        
        await callback.answer(f"✅ Nivel requerido establecido: {level}", show_alert=False)
        
        # Refresh the requirements menu
        await admin_experience_wizard_requirements(callback, state, session)
        
    except Exception as e:
        logger.error(f"Error setting level: {e}")
        await callback.answer("Error al establecer el nivel", show_alert=True)


@router.callback_query(F.data.startswith("admin_experience_wizard_vip_"))
async def admin_experience_wizard_set_vip(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Set VIP requirement for the experience."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        vip_required = callback.data.endswith("_true")
        await state.update_data(requires_vip=vip_required)
        
        status = "requerido" if vip_required else "no requerido"
        await callback.answer(f"✅ Acceso VIP {status}", show_alert=False)
        
        # Refresh the requirements menu
        await admin_experience_wizard_requirements(callback, state, session)
        
    except Exception as e:
        logger.error(f"Error setting VIP requirement: {e}")
        await callback.answer("Error al establecer el requisito VIP", show_alert=True)


# Elements configuration handlers
@router.callback_query(F.data.startswith("admin_experience_wizard_narrative_"))
async def admin_experience_wizard_set_narrative(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Set narrative inclusion for the experience."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        include_narrative = callback.data.endswith("_true")
        await state.update_data(include_narrative=include_narrative)
        
        status = "incluida" if include_narrative else "no incluida"
        await callback.answer(f"✅ Narrativa {status}", show_alert=False)
        
        # Refresh the elements menu
        await admin_experience_wizard_elements(callback, state, session)
        
    except Exception as e:
        logger.error(f"Error setting narrative inclusion: {e}")
        await callback.answer("Error al establecer la narrativa", show_alert=True)


@router.callback_query(F.data.startswith("admin_experience_wizard_shop_"))
async def admin_experience_wizard_set_shop(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Set shop inclusion for the experience."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        include_shop = callback.data.endswith("_true")
        await state.update_data(include_shop=include_shop)
        
        status = "incluida" if include_shop else "no incluida"
        await callback.answer(f"✅ Tienda {status}", show_alert=False)
        
        # Refresh the elements menu
        await admin_experience_wizard_elements(callback, state, session)
        
    except Exception as e:
        logger.error(f"Error setting shop inclusion: {e}")
        await callback.answer("Error al establecer la tienda", show_alert=True)


@router.callback_query(F.data.startswith("admin_experience_wizard_missions_"))
async def admin_experience_wizard_set_missions(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Set missions inclusion for the experience."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        include_missions = callback.data.endswith("_true")
        await state.update_data(include_missions=include_missions)
        
        status = "incluidas" if include_missions else "no incluidas"
        await callback.answer(f"✅ Misiones {status}", show_alert=False)
        
        # Refresh the elements menu
        await admin_experience_wizard_elements(callback, state, session)
        
    except Exception as e:
        logger.error(f"Error setting missions inclusion: {e}")
        await callback.answer("Error al establecer las misiones", show_alert=True)


# Rewards configuration handlers
@router.callback_query(F.data.startswith("admin_experience_wizard_points_"))
async def admin_experience_wizard_set_points(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Set reward points for the experience."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        points = int(callback.data.split("_")[-1])
        await state.update_data(reward_points=points)
        
        await callback.answer(f"✅ Puntos establecidos: {points}", show_alert=False)
        
        # Refresh the rewards menu
        await admin_experience_wizard_rewards(callback, state, session)
        
    except Exception as e:
        logger.error(f"Error setting reward points: {e}")
        await callback.answer("Error al establecer los puntos", show_alert=True)


@router.callback_query(F.data.startswith("admin_experience_wizard_vip_days_"))
async def admin_experience_wizard_set_vip_days(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Set VIP days reward for the experience."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        vip_days = int(callback.data.split("_")[-1])
        await state.update_data(reward_vip_days=vip_days)
        
        await callback.answer(f"✅ Días VIP establecidos: {vip_days}", show_alert=False)
        
        # Refresh the rewards menu
        await admin_experience_wizard_rewards(callback, state, session)
        
    except Exception as e:
        logger.error(f"Error setting VIP days: {e}")
        await callback.answer("Error al establecer los días VIP", show_alert=True)