"""
Manejadores para administración de misiones unificadas.
Permite a los administradores crear, editar, activar/desactivar y eliminar misiones en el sistema unificado.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import datetime

from services.unified_mission_service import UnifiedMissionService
from utils.user_roles import is_admin
from utils.menu_manager import menu_manager
from utils.handler_decorators import safe_handler, track_usage, transaction

# Estados para FSM
class MissionCreateForm(StatesGroup):
    title = State()
    description = State()
    mission_type = State()
    objectives = State()
    requirements = State()
    rewards = State()
    duration = State()
    is_repeatable = State()
    confirm = State()

# Configuración de logging
logger = logging.getLogger(__name__)

# Creación del router
router = Router(name="unified_mission_admin")

@router.callback_query(F.data == "admin_content_missions")
@safe_handler("Error al cargar panel de misiones")
@track_usage("admin_missions_panel")
@transaction()
async def show_admin_missions_panel(callback: CallbackQuery, session: AsyncSession):
    """Muestra el panel de administración de misiones unificadas."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        # Inicializar servicio
        mission_service = UnifiedMissionService(session, callback.bot)
        
        # Obtener estadísticas de misiones
        all_missions = await mission_service.get_all_missions(active_only=False)
        active_missions = [m for m in all_missions if m.is_active]
        inactive_missions = [m for m in all_missions if not m.is_active]
        
        mission_types_count = {}
        for mission in all_missions:
            mission_types_count[mission.mission_type] = mission_types_count.get(mission.mission_type, 0) + 1
        
        # Crear texto informativo
        text = "🎯 **ADMINISTRACIÓN DE MISIONES UNIFICADAS**\n\n"
        
        # Resumen de misiones
        text += f"**Total de misiones:** {len(all_missions)}\n"
        text += f"**Misiones activas:** {len(active_missions)}\n"
        text += f"**Misiones inactivas:** {len(inactive_missions)}\n\n"
        
        # Desglose por tipo
        text += "**Desglose por tipo:**\n"
        for mission_type, count in mission_types_count.items():
            type_label = {
                "MAIN": "Principales",
                "SIDE": "Secundarias",
                "DAILY": "Diarias",
                "WEEKLY": "Semanales",
                "EVENT": "Eventos"
            }.get(mission_type, mission_type)
            text += f"• {type_label}: {count}\n"
        
        # Crear teclado
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Crear Misión", callback_data="admin_create_mission"),
                InlineKeyboardButton(text="📋 Ver Misiones", callback_data="admin_list_missions")
            ],
            [
                InlineKeyboardButton(text="🔄 Actualizar Estado", callback_data="admin_toggle_mission"),
                InlineKeyboardButton(text="📝 Editar Misión", callback_data="admin_edit_mission")
            ],
            [
                InlineKeyboardButton(text="🗑️ Eliminar Misión", callback_data="admin_delete_mission")
            ],
            [
                InlineKeyboardButton(text="🔄 Actualizar", callback_data="admin_content_missions"),
                InlineKeyboardButton(text="↩️ Volver", callback_data="admin_manage_content")
            ],
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.exception(f"Error en panel de misiones: {e}")
        await callback.answer("Error al cargar el panel de misiones", show_alert=True)

@router.callback_query(F.data == "admin_list_missions")
@safe_handler("Error al listar misiones")
@track_usage("admin_list_missions")
@transaction()
async def list_missions(callback: CallbackQuery, session: AsyncSession):
    """Lista todas las misiones disponibles en el sistema unificado."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        # Inicializar servicio
        mission_service = UnifiedMissionService(session, callback.bot)
        
        # Obtener todas las misiones
        missions = await mission_service.get_all_missions(active_only=False)
        
        if not missions:
            text = "🎯 **LISTA DE MISIONES**\n\nNo hay misiones configuradas en el sistema."
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Crear Misión", callback_data="admin_create_mission")],
                [InlineKeyboardButton(text="↩️ Volver", callback_data="admin_content_missions")]
            ])
            await callback.message.edit_text(text, reply_markup=keyboard)
            await callback.answer()
            return
        
        # Ordenar misiones por tipo y estado
        missions.sort(key=lambda m: (
            0 if m.mission_type == "MAIN" else
            1 if m.mission_type == "SIDE" else
            2 if m.mission_type == "DAILY" else
            3 if m.mission_type == "WEEKLY" else
            4 if m.mission_type == "EVENT" else 5,
            not m.is_active
        ))
        
        # Crear texto informativo
        text = "🎯 **LISTA DE MISIONES**\n\n"
        
        # Mostrar misiones
        for i, mission in enumerate(missions[:15]):  # Mostrar máximo 15 misiones para evitar mensaje demasiado largo
            status = "✅" if mission.is_active else "❌"
            type_label = {
                "MAIN": "Principal",
                "SIDE": "Secundaria",
                "DAILY": "Diaria",
                "WEEKLY": "Semanal",
                "EVENT": "Evento"
            }.get(mission.mission_type, mission.mission_type)
            
            text += f"{i+1}. {status} **{mission.title}** ({type_label})\n"
            # Mostrar detalles mínimos
            if mission.rewards and "points" in mission.rewards:
                text += f"   → Recompensa: {mission.rewards['points']} puntos\n"
            
        if len(missions) > 15:
            text += f"\n... y {len(missions) - 15} misiones más."
        
        # Crear teclado con paginación si es necesario
        keyboard = InlineKeyboardBuilder()
        
        # Botones para filtrar por tipo
        keyboard.row(
            InlineKeyboardButton(text="🔍 Principales", callback_data="admin_list_missions_main"),
            InlineKeyboardButton(text="🔍 Secundarias", callback_data="admin_list_missions_side"),
            width=2
        )
        keyboard.row(
            InlineKeyboardButton(text="🔍 Diarias", callback_data="admin_list_missions_daily"),
            InlineKeyboardButton(text="🔍 Semanales", callback_data="admin_list_missions_weekly"),
            width=2
        )
        
        # Botones de acción
        keyboard.row(
            InlineKeyboardButton(text="➕ Crear", callback_data="admin_create_mission"),
            InlineKeyboardButton(text="🔄 Actualizar", callback_data="admin_list_missions"),
            width=2
        )
        keyboard.row(
            InlineKeyboardButton(text="↩️ Volver", callback_data="admin_content_missions")
        )
        
        await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
        await callback.answer()
        
    except Exception as e:
        logger.exception(f"Error al listar misiones: {e}")
        await callback.answer("Error al cargar la lista de misiones", show_alert=True)

@router.callback_query(F.data.startswith("admin_list_missions_"))
@safe_handler("Error al filtrar misiones")
@track_usage("admin_filter_missions")
@transaction()
async def filter_missions(callback: CallbackQuery, session: AsyncSession):
    """Filtra las misiones por tipo."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    # Extraer tipo de misión del callback
    mission_type = callback.data.split("_")[-1].upper()
    
    try:
        # Inicializar servicio
        mission_service = UnifiedMissionService(session, callback.bot)
        
        # Obtener misiones filtradas
        all_missions = await mission_service.get_all_missions(active_only=False)
        missions = [m for m in all_missions if m.mission_type == mission_type]
        
        if not missions:
            text = f"🎯 **MISIONES TIPO: {mission_type}**\n\nNo hay misiones de este tipo configuradas."
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Crear Misión", callback_data="admin_create_mission")],
                [InlineKeyboardButton(text="↩️ Volver a Misiones", callback_data="admin_list_missions")]
            ])
            await callback.message.edit_text(text, reply_markup=keyboard)
            await callback.answer()
            return
        
        # Ordenar misiones por estado (activas primero)
        missions.sort(key=lambda m: (not m.is_active, m.order))
        
        # Crear texto informativo
        type_label = {
            "MAIN": "PRINCIPALES",
            "SIDE": "SECUNDARIAS",
            "DAILY": "DIARIAS",
            "WEEKLY": "SEMANALES",
            "EVENT": "DE EVENTO"
        }.get(mission_type, mission_type)
        
        text = f"🎯 **MISIONES {type_label}**\n\n"
        
        # Mostrar misiones
        for i, mission in enumerate(missions):
            status = "✅" if mission.is_active else "❌"
            
            text += f"{i+1}. {status} **{mission.title}**\n"
            # Mostrar más detalles ya que hay menos misiones
            text += f"   ID: `{mission.id}`\n"
            if mission.rewards and "points" in mission.rewards:
                text += f"   → Recompensa: {mission.rewards['points']} puntos\n"
            
            # Agregar espaciado entre misiones
            text += "\n"
        
        # Crear teclado
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Crear", callback_data="admin_create_mission"),
                InlineKeyboardButton(text="📋 Ver Todas", callback_data="admin_list_missions")
            ],
            [InlineKeyboardButton(text="↩️ Volver", callback_data="admin_content_missions")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.exception(f"Error al filtrar misiones: {e}")
        await callback.answer("Error al filtrar misiones", show_alert=True)

@router.callback_query(F.data == "admin_toggle_mission")
@safe_handler("Error al acceder a cambio de estado")
@transaction()
async def choose_mission_to_toggle(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Permite al administrador elegir una misión para activar/desactivar."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        # Inicializar servicio
        mission_service = UnifiedMissionService(session, callback.bot)
        
        # Obtener todas las misiones
        missions = await mission_service.get_all_missions(active_only=False)
        
        if not missions:
            await callback.answer("No hay misiones configuradas", show_alert=True)
            return
        
        # Ordenar misiones por tipo y estado
        missions.sort(key=lambda m: (
            0 if m.mission_type == "MAIN" else
            1 if m.mission_type == "SIDE" else
            2 if m.mission_type == "DAILY" else
            3 if m.mission_type == "WEEKLY" else
            4 if m.mission_type == "EVENT" else 5,
            not m.is_active
        ))
        
        # Guardar lista de IDs en el estado
        await state.update_data(mission_ids=[m.id for m in missions])
        
        # Crear texto informativo
        text = "🔄 **CAMBIAR ESTADO DE MISIÓN**\n\n"
        text += "Selecciona la misión que deseas activar/desactivar:\n\n"
        
        # Crear teclado con botones para cada misión
        keyboard = InlineKeyboardBuilder()
        
        for i, mission in enumerate(missions[:15]):  # Limitar a 15 botones
            status = "✅" if mission.is_active else "❌"
            btn_text = f"{status} {mission.title[:20]}..." if len(mission.title) > 20 else f"{status} {mission.title}"
            keyboard.button(
                text=btn_text,
                callback_data=f"admin_toggle_mission_{i}"
            )
        
        # Añadir botones de navegación
        keyboard.row(
            InlineKeyboardButton(text="↩️ Volver", callback_data="admin_content_missions")
        )
        
        # Ajustar layout a una columna
        keyboard.adjust(1)
        
        await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
        await callback.answer()
        
    except Exception as e:
        logger.exception(f"Error al elegir misión para toggle: {e}")
        await callback.answer("Error al cargar misiones", show_alert=True)

@router.callback_query(F.data.startswith("admin_toggle_mission_"))
@safe_handler("Error al cambiar estado de misión")
@transaction()
async def toggle_mission_status(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Cambia el estado (activo/inactivo) de una misión seleccionada."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        # Obtener índice de la misión seleccionada
        mission_index = int(callback.data.split("_")[-1])
        
        # Recuperar datos del estado
        state_data = await state.get_data()
        mission_ids = state_data.get("mission_ids", [])
        
        if mission_index >= len(mission_ids):
            await callback.answer("Misión no válida", show_alert=True)
            return
        
        mission_id = mission_ids[mission_index]
        
        # Inicializar servicio
        mission_service = UnifiedMissionService(session, callback.bot)
        
        # Obtener la misión
        mission = await mission_service.get_mission_by_id(mission_id)
        if not mission:
            await callback.answer("Misión no encontrada", show_alert=True)
            return
        
        # Cambiar estado
        new_status = not mission.is_active
        success = await mission_service.update_mission_status(mission_id, new_status)
        
        if success:
            status_text = "activada" if new_status else "desactivada"
            await callback.answer(f"Misión {status_text} correctamente", show_alert=True)
            
            # Volver a la lista de misiones
            await choose_mission_to_toggle(callback, session, state)
        else:
            await callback.answer("Error al cambiar el estado de la misión", show_alert=True)
        
    except Exception as e:
        logger.exception(f"Error al cambiar estado de misión: {e}")
        await callback.answer("Error al procesar la solicitud", show_alert=True)

@router.callback_query(F.data == "admin_create_mission")
@safe_handler("Error al iniciar creación de misión")
@transaction()
async def start_create_mission(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Inicia el proceso de creación de una nueva misión."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    # Limpiar estado anterior
    await state.clear()
    
    # Establecer estado inicial
    await state.set_state(MissionCreateForm.title)
    
    # Mostrar instrucciones
    text = "🎯 **CREAR NUEVA MISIÓN**\n\n"
    text += "Por favor, introduce el título de la misión:"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_cancel_mission_create")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.message(MissionCreateForm.title)
@safe_handler("Error al procesar título")
async def process_mission_title(message: Message, state: FSMContext):
    """Procesa el título de la misión y solicita la descripción."""
    if not await is_admin(message.from_user.id, session):
        return
    
    # Guardar título
    await state.update_data(title=message.text)
    
    # Avanzar al siguiente estado
    await state.set_state(MissionCreateForm.description)
    
    # Solicitar descripción
    text = "🎯 **CREAR NUEVA MISIÓN**\n\n"
    text += f"Título: **{message.text}**\n\n"
    text += "Por favor, introduce la descripción de la misión:"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_cancel_mission_create")]
    ])
    
    await message.answer(text, reply_markup=keyboard)

@router.message(MissionCreateForm.description)
@safe_handler("Error al procesar descripción")
async def process_mission_description(message: Message, state: FSMContext):
    """Procesa la descripción de la misión y solicita el tipo."""
    if not await is_admin(message.from_user.id, session):
        return
    
    # Guardar descripción
    await state.update_data(description=message.text)
    
    # Obtener datos guardados
    data = await state.get_data()
    
    # Avanzar al siguiente estado
    await state.set_state(MissionCreateForm.mission_type)
    
    # Solicitar tipo de misión
    text = "🎯 **CREAR NUEVA MISIÓN**\n\n"
    text += f"Título: **{data['title']}**\n"
    text += f"Descripción: *{message.text[:50]}...*\n\n"
    text += "Por favor, selecciona el tipo de misión:"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📜 Principal", callback_data="mission_type_MAIN"),
            InlineKeyboardButton(text="📌 Secundaria", callback_data="mission_type_SIDE")
        ],
        [
            InlineKeyboardButton(text="🔄 Diaria", callback_data="mission_type_DAILY"),
            InlineKeyboardButton(text="📅 Semanal", callback_data="mission_type_WEEKLY")
        ],
        [
            InlineKeyboardButton(text="🎉 Evento", callback_data="mission_type_EVENT")
        ],
        [
            InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_cancel_mission_create")
        ]
    ])
    
    await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("mission_type_"))
@safe_handler("Error al procesar tipo de misión")
async def process_mission_type(callback: CallbackQuery, state: FSMContext):
    """Procesa el tipo de misión y solicita los objetivos."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    # Extraer tipo de misión
    mission_type = callback.data.split("_")[-1]
    
    # Guardar tipo
    await state.update_data(mission_type=mission_type)
    
    # Obtener datos guardados
    data = await state.get_data()
    
    # Avanzar al siguiente estado
    await state.set_state(MissionCreateForm.objectives)
    
    # Solicitar objetivos
    text = "🎯 **CREAR NUEVA MISIÓN**\n\n"
    text += f"Título: **{data['title']}**\n"
    text += f"Tipo: **{mission_type}**\n\n"
    text += "Por favor, introduce los objetivos de la misión.\n"
    text += "Formato: Un objetivo por línea.\n"
    text += "Ejemplo:\n"
    text += "Descubre el fragmento X\n"
    text += "Encuentra la pista Y\n"
    text += "Realiza 5 reacciones"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_cancel_mission_create")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.message(MissionCreateForm.objectives)
@safe_handler("Error al procesar objetivos")
async def process_mission_objectives(message: Message, state: FSMContext):
    """Procesa los objetivos de la misión y solicita los requisitos."""
    if not await is_admin(message.from_user.id, session):
        return
    
    # Procesar objetivos (un objetivo por línea)
    objectives = []
    for line in message.text.strip().split('\n'):
        if line.strip():
            objectives.append({"description": line.strip()})
    
    # Guardar objetivos
    await state.update_data(objectives=objectives)
    
    # Obtener datos guardados
    data = await state.get_data()
    
    # Avanzar al siguiente estado
    await state.set_state(MissionCreateForm.requirements)
    
    # Solicitar requisitos
    text = "🎯 **CREAR NUEVA MISIÓN**\n\n"
    text += f"Título: **{data['title']}**\n"
    text += f"Objetivos: **{len(objectives)}** definidos\n\n"
    text += "Ahora, introduce los requisitos de la misión en formato JSON simplificado.\n"
    text += "Ejemplo:\n"
    text += "```\n"
    text += "{\n"
    text += "  \"narrative_fragments\": [\"fragment_id1\", \"fragment_id2\"],\n"
    text += "  \"lore_pieces\": [\"piece_code1\", \"piece_code2\"],\n"
    text += "  \"actions\": [{\"type\": \"reaction\", \"count\": 5}]\n"
    text += "}\n"
    text += "```"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_cancel_mission_create")]
    ])
    
    await message.answer(text, reply_markup=keyboard)

@router.message(MissionCreateForm.requirements)
@safe_handler("Error al procesar requisitos")
async def process_mission_requirements(message: Message, state: FSMContext):
    """Procesa los requisitos de la misión y solicita las recompensas."""
    if not await is_admin(message.from_user.id, session):
        return
    
    try:
        # Intentar parsear JSON
        requirements = json.loads(message.text)
        
        # Guardar requisitos
        await state.update_data(requirements=requirements)
        
        # Obtener datos guardados
        data = await state.get_data()
        
        # Avanzar al siguiente estado
        await state.set_state(MissionCreateForm.rewards)
        
        # Solicitar recompensas
        text = "🎯 **CREAR NUEVA MISIÓN**\n\n"
        text += f"Título: **{data['title']}**\n"
        text += f"Requisitos: **Definidos correctamente**\n\n"
        text += "Ahora, introduce las recompensas de la misión en formato JSON simplificado.\n"
        text += "Ejemplo:\n"
        text += "```\n"
        text += "{\n"
        text += "  \"points\": 100,\n"
        text += "  \"badges\": [\"badge_id1\"],\n"
        text += "  \"lore_pieces\": [\"piece_code1\"]\n"
        text += "}\n"
        text += "```"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_cancel_mission_create")]
        ])
        
        await message.answer(text, reply_markup=keyboard)
        
    except json.JSONDecodeError:
        # Error al parsear JSON
        await message.answer(
            "❌ Error: El formato JSON no es válido. Por favor, introduce los requisitos en formato JSON válido.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_cancel_mission_create")]
            ])
        )

@router.message(MissionCreateForm.rewards)
@safe_handler("Error al procesar recompensas")
async def process_mission_rewards(message: Message, state: FSMContext):
    """Procesa las recompensas de la misión y solicita la duración."""
    if not await is_admin(message.from_user.id, session):
        return
    
    try:
        # Intentar parsear JSON
        rewards = json.loads(message.text)
        
        # Guardar recompensas
        await state.update_data(rewards=rewards)
        
        # Obtener datos guardados
        data = await state.get_data()
        
        # Avanzar al siguiente estado
        await state.set_state(MissionCreateForm.duration)
        
        # Solicitar duración
        text = "🎯 **CREAR NUEVA MISIÓN**\n\n"
        text += f"Título: **{data['title']}**\n"
        text += f"Recompensas: **Definidas correctamente**\n\n"
        
        if data['mission_type'] in ['DAILY', 'WEEKLY', 'EVENT']:
            text += "Por favor, introduce la duración de la misión en días (0 = sin límite):"
        else:
            text += "Las misiones principales y secundarias no tienen duración. Simplemente envía '0':"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_cancel_mission_create")]
        ])
        
        await message.answer(text, reply_markup=keyboard)
        
    except json.JSONDecodeError:
        # Error al parsear JSON
        await message.answer(
            "❌ Error: El formato JSON no es válido. Por favor, introduce las recompensas en formato JSON válido.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_cancel_mission_create")]
            ])
        )

@router.message(MissionCreateForm.duration)
@safe_handler("Error al procesar duración")
async def process_mission_duration(message: Message, state: FSMContext):
    """Procesa la duración de la misión y solicita si es repetible."""
    if not await is_admin(message.from_user.id, session):
        return
    
    try:
        # Intentar parsear entero
        duration = int(message.text)
        
        # Guardar duración
        await state.update_data(duration_days=duration)
        
        # Obtener datos guardados
        data = await state.get_data()
        
        # Avanzar al siguiente estado
        await state.set_state(MissionCreateForm.is_repeatable)
        
        # Solicitar si es repetible
        text = "🎯 **CREAR NUEVA MISIÓN**\n\n"
        text += f"Título: **{data['title']}**\n"
        text += f"Duración: **{duration} días**\n\n"
        text += "¿Es esta misión repetible?"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Sí", callback_data="mission_repeatable_yes"),
                InlineKeyboardButton(text="❌ No", callback_data="mission_repeatable_no")
            ],
            [
                InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_cancel_mission_create")
            ]
        ])
        
        await message.answer(text, reply_markup=keyboard)
        
    except ValueError:
        # Error al parsear entero
        await message.answer(
            "❌ Error: La duración debe ser un número entero. Por favor, introduce un valor numérico.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_cancel_mission_create")]
            ])
        )

@router.callback_query(F.data.startswith("mission_repeatable_"))
@safe_handler("Error al procesar repetibilidad")
async def process_mission_repeatable(callback: CallbackQuery, state: FSMContext):
    """Procesa si la misión es repetible y muestra resumen para confirmar."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    # Extraer valor
    is_repeatable = callback.data == "mission_repeatable_yes"
    
    # Guardar valor
    await state.update_data(is_repeatable=is_repeatable)
    
    if is_repeatable:
        # Solicitar tiempo de cooldown
        text = "🎯 **CREAR NUEVA MISIÓN**\n\n"
        text += "La misión será repetible.\n\n"
        text += "Por favor, introduce el tiempo de espera (cooldown) en horas antes de que la misión pueda repetirse:"
        
        await state.update_data(cooldown_asking=True)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_cancel_mission_create")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        return
    else:
        # Establecer cooldown a 0 para misiones no repetibles
        await state.update_data(cooldown_hours=0)
    
    # Avanzar al estado de confirmación
    await state.set_state(MissionCreateForm.confirm)
    
    # Obtener todos los datos
    data = await state.get_data()
    
    # Mostrar resumen para confirmar
    text = "🎯 **RESUMEN DE MISIÓN**\n\n"
    text += f"**Título:** {data['title']}\n"
    text += f"**Descripción:** {data['description'][:100]}...\n"
    text += f"**Tipo:** {data['mission_type']}\n"
    text += f"**Objetivos:** {len(data['objectives'])}\n"
    text += f"**Duración:** {data['duration_days']} días\n"
    text += f"**Repetible:** {'Sí' if is_repeatable else 'No'}\n"
    
    if 'points' in data.get('rewards', {}):
        text += f"**Recompensa puntos:** {data['rewards']['points']}\n"
    
    text += "\n¿Confirmas la creación de esta misión?"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirmar", callback_data="admin_confirm_mission_create"),
            InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_cancel_mission_create")
        ]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.message(MissionCreateForm.is_repeatable)
@safe_handler("Error al procesar cooldown")
async def process_mission_cooldown(message: Message, state: FSMContext):
    """Procesa el tiempo de cooldown para misiones repetibles."""
    if not await is_admin(message.from_user.id, session):
        return
    
    data = await state.get_data()
    if not data.get('cooldown_asking'):
        # Ignorar mensajes que no son para cooldown
        return
    
    try:
        # Intentar parsear entero
        cooldown = int(message.text)
        
        # Guardar cooldown
        await state.update_data(cooldown_hours=cooldown)
        
        # Avanzar al estado de confirmación
        await state.set_state(MissionCreateForm.confirm)
        
        # Obtener todos los datos
        data = await state.get_data()
        
        # Mostrar resumen para confirmar
        text = "🎯 **RESUMEN DE MISIÓN**\n\n"
        text += f"**Título:** {data['title']}\n"
        text += f"**Descripción:** {data['description'][:100]}...\n"
        text += f"**Tipo:** {data['mission_type']}\n"
        text += f"**Objetivos:** {len(data['objectives'])}\n"
        text += f"**Duración:** {data['duration_days']} días\n"
        text += f"**Repetible:** Sí (Cooldown: {cooldown} horas)\n"
        
        if 'points' in data.get('rewards', {}):
            text += f"**Recompensa puntos:** {data['rewards']['points']}\n"
        
        text += "\n¿Confirmas la creación de esta misión?"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Confirmar", callback_data="admin_confirm_mission_create"),
                InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_cancel_mission_create")
            ]
        ])
        
        await message.answer(text, reply_markup=keyboard)
        
    except ValueError:
        # Error al parsear entero
        await message.answer(
            "❌ Error: El cooldown debe ser un número entero de horas. Por favor, introduce un valor numérico.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Cancelar", callback_data="admin_cancel_mission_create")]
            ])
        )

@router.callback_query(F.data == "admin_confirm_mission_create")
@safe_handler("Error al crear misión")
@transaction()
async def confirm_create_mission(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Crea la misión con los datos recopilados."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        # Obtener todos los datos
        data = await state.get_data()
        
        # Inicializar servicio
        mission_service = UnifiedMissionService(session, callback.bot)
        
        # Crear misión
        mission = await mission_service.create_mission(
            title=data['title'],
            description=data['description'],
            mission_type=data['mission_type'],
            objectives=data['objectives'],
            requirements=data['requirements'],
            rewards=data['rewards'],
            is_active=True,
            is_repeatable=data.get('is_repeatable', False),
            duration_days=data.get('duration_days', 0),
            cooldown_hours=data.get('cooldown_hours', 0),
            order=0  # Orden predeterminado
        )
        
        await callback.answer("Misión creada con éxito", show_alert=True)
        
        # Limpiar estado
        await state.clear()
        
        # Volver al panel de misiones
        await show_admin_missions_panel(callback, session)
        
    except Exception as e:
        logger.exception(f"Error al crear misión: {e}")
        await callback.answer(f"Error al crear misión: {str(e)[:200]}", show_alert=True)

@router.callback_query(F.data == "admin_cancel_mission_create")
@safe_handler("Error al cancelar creación")
async def cancel_create_mission(callback: CallbackQuery, state: FSMContext):
    """Cancela el proceso de creación de misión."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    # Limpiar estado
    await state.clear()
    
    await callback.answer("Creación de misión cancelada", show_alert=True)
    
    # Volver al panel de misiones
    await show_admin_missions_panel(callback, session)

@router.callback_query(F.data == "admin_delete_mission")
@safe_handler("Error al acceder a eliminación")
@transaction()
async def choose_mission_to_delete(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Permite al administrador elegir una misión para eliminar."""
    if not await is_admin(callback.from_user.id, session):
        return await callback.answer("Acceso denegado", show_alert=True)
    
    try:
        # Inicializar servicio
        mission_service = UnifiedMissionService(session, callback.bot)
        
        # Obtener todas las misiones
        missions = await mission_service.get_all_missions(active_only=False)
        
        if not missions:
            await callback.answer("No hay misiones configuradas", show_alert=True)
            return
        
        # Ordenar misiones por tipo y estado
        missions.sort(key=lambda m: (
            0 if m.mission_type == "MAIN" else
            1 if m.mission_type == "SIDE" else
            2 if m.mission_type == "DAILY" else
            3 if m.mission_type == "WEEKLY" else
            4 if m.mission_type == "EVENT" else 5,
            not m.is_active
        ))
        
        # Guardar lista de IDs en el estado
        await state.update_data(mission_ids_delete=[m.id for m in missions])
        
        # Crear texto informativo
        text = "🗑️ **ELIMINAR MISIÓN**\n\n"
        text += "⚠️ **ADVERTENCIA**: Esta acción no se puede deshacer.\n\n"
        text += "Selecciona la misión que deseas eliminar:\n\n"
        
        # Crear teclado con botones para cada misión
        keyboard = InlineKeyboardBuilder()
        
        for i, mission in enumerate(missions[:15]):  # Limitar a 15 botones
            status = "✅" if mission.is_active else "❌"
            btn_text = f"{status} {mission.title[:20]}..." if len(mission.title) > 20 else f"{status} {mission.title}"
            keyboard.button(
                text=btn_text,
                callback_data=f"admin_delete_mission_{i}"
            )
        
        # Añadir botones de navegación
        keyboard.row(
            InlineKeyboardButton(text="↩️ Volver", callback_data="admin_content_missions")
        )
        
        # Ajustar layout a una columna
        keyboard.adjust(1)
        
        await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
        await callback.answer()
        
    except Exception as e:
        logger.exception(f"Error al elegir misión para eliminar: {e}")
        await callback.answer("Error al cargar misiones", show_alert=True)

# Aquí añadiremos más handlers para completar todas las funcionalidades administrativas
# como edición de misiones, eliminación, etc.