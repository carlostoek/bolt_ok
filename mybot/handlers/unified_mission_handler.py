"""
Handlers para el sistema de misiones unificadas.
Proporciona comandos y callbacks para gestionar misiones con integración narrativa.
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from services.unified_mission_service import UnifiedMissionService
from services.unified_narrative_service import UnifiedNarrativeService
from utils.callback_factories import MissionCallbackFactory
from utils.keyboard_utils import (
    get_missions_keyboard, 
    get_mission_details_keyboard,
    get_back_keyboard
)
from utils.handler_decorators import safe_handler, track_usage, transaction
from utils.message_safety import safe_answer, safe_edit

# Configuración de logging
logger = logging.getLogger(__name__)

# Creación del router
router = Router(name="unified_missions")

@router.message(Command("misiones", "missions"))
@safe_handler("Error al cargar misiones. Inténtalo de nuevo.")
@track_usage("list_unified_missions")
@transaction()
async def cmd_list_missions(message: Message, session: AsyncSession):
    """Comando para mostrar las misiones disponibles."""
    user_id = message.from_user.id
    
    # Inicializar servicio
    mission_service = UnifiedMissionService(session, message.bot)
    
    # Obtener misiones disponibles
    missions = await mission_service.get_user_available_missions(user_id)
    
    # Ordenar misiones: primero principales, luego secundarias, luego diarias/semanales
    missions.sort(key=lambda m: (
        0 if m["mission_type"] == "MAIN" else
        1 if m["mission_type"] == "SIDE" else
        2 if m["mission_type"] == "DAILY" else
        3 if m["mission_type"] == "WEEKLY" else 4,
        m["is_completed"]  # Las no completadas primero
    ))
    
    # Preparar texto de respuesta
    if not missions:
        text = "🎯 *No hay misiones disponibles actualmente.*\n\nVuelve más tarde para descubrir nuevas misiones."
        await safe_answer(message, text)
        return
    
    # Contar misiones por tipo
    main_missions = sum(1 for m in missions if m["mission_type"] == "MAIN")
    side_missions = sum(1 for m in missions if m["mission_type"] == "SIDE")
    daily_missions = sum(1 for m in missions if m["mission_type"] == "DAILY")
    weekly_missions = sum(1 for m in missions if m["mission_type"] == "WEEKLY")
    event_missions = sum(1 for m in missions if m["mission_type"] == "EVENT")
    
    # Construir texto
    text = "🎯 *Misiones Disponibles* 🎯\n\n"
    text += f"📜 Principales: {main_missions}\n"
    text += f"📌 Secundarias: {side_missions}\n"
    text += f"🔄 Diarias: {daily_missions}\n"
    text += f"📅 Semanales: {weekly_missions}\n"
    if event_missions > 0:
        text += f"🎉 Eventos: {event_missions}\n"
    text += "\nSelecciona una misión para ver más detalles:\n"
    
    # Crear teclado con las misiones
    keyboard = get_missions_keyboard(missions)
    
    await safe_answer(message, text, reply_markup=keyboard)
    
@router.callback_query(MissionCallbackFactory.filter(F.action == "list"))
@safe_handler("Error al cargar la lista de misiones.")
@track_usage("list_missions_callback")
@transaction()
async def show_missions_list(callback: CallbackQuery, callback_data: dict, session: AsyncSession):
    """Muestra la lista de misiones disponibles para el usuario."""
    user_id = callback.from_user.id
    mission_type = callback_data.mission_type if hasattr(callback_data, "mission_type") else None
    
    # Inicializar servicio de misiones
    mission_service = UnifiedMissionService(session, callback.bot)
    
    # Obtener misiones disponibles
    missions = await mission_service.get_user_available_missions(user_id)
    
    # Filtrar por tipo si es necesario
    if mission_type:
        if mission_type == "completed":
            missions = [m for m in missions if m["is_completed"]]
        else:
            missions = [m for m in missions if m["mission_type"] == mission_type]
    
    # Ordenar misiones: primero principales, luego secundarias, luego diarias/semanales
    missions.sort(key=lambda m: (
        0 if m["mission_type"] == "MAIN" else
        1 if m["mission_type"] == "SIDE" else
        2 if m["mission_type"] == "DAILY" else
        3 if m["mission_type"] == "WEEKLY" else 4,
        m["is_completed"]  # Las no completadas primero
    ))
    
    # Preparar texto de respuesta
    if not missions:
        text = "🎯 *No hay misiones disponibles actualmente.*\n\nVuelve más tarde para descubrir nuevas misiones."
        await safe_edit(callback.message, text, reply_markup=get_back_keyboard())
        await callback.answer()
        return
    
    # Contar misiones por tipo
    main_missions = sum(1 for m in missions if m["mission_type"] == "MAIN")
    side_missions = sum(1 for m in missions if m["mission_type"] == "SIDE")
    daily_missions = sum(1 for m in missions if m["mission_type"] == "DAILY")
    weekly_missions = sum(1 for m in missions if m["mission_type"] == "WEEKLY")
    event_missions = sum(1 for m in missions if m["mission_type"] == "EVENT")
    
    # Construir texto
    text = "🎯 *Misiones Disponibles* 🎯\n\n"
    
    if mission_type:
        if mission_type == "completed":
            text += f"Mostrando misiones completadas ({len(missions)})\n\n"
        else:
            text += f"Mostrando misiones de tipo: *{mission_type}*\n\n"
    else:
        text += f"📜 Principales: {main_missions}\n"
        text += f"📌 Secundarias: {side_missions}\n"
        text += f"🔄 Diarias: {daily_missions}\n"
        text += f"📅 Semanales: {weekly_missions}\n"
        if event_missions > 0:
            text += f"🎉 Eventos: {event_missions}\n"
        text += "\nSelecciona una misión para ver más detalles:\n"
    
    # Crear teclado con las misiones
    keyboard = get_missions_keyboard(missions)
    
    await safe_edit(callback.message, text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(MissionCallbackFactory.filter(F.action == "details"))
@safe_handler("Error al cargar detalles de la misión.")
@track_usage("mission_details")
@transaction()
async def show_mission_details(callback: CallbackQuery, callback_data: dict, session: AsyncSession):
    """Muestra los detalles de una misión específica."""
    user_id = callback.from_user.id
    mission_id = callback_data.mission_id
    
    # Inicializar servicio
    mission_service = UnifiedMissionService(session, callback.bot)
    
    # Obtener la misión
    mission = await mission_service.get_mission_by_id(mission_id)
    if not mission:
        await callback.answer("Misión no encontrada", show_alert=True)
        return
    
    # Obtener progreso del usuario
    progress = await mission_service.get_mission_progress(user_id, mission_id)
    
    # Formato para el tipo de misión
    mission_type_names = {
        "MAIN": "Principal",
        "SIDE": "Secundaria",
        "DAILY": "Diaria",
        "WEEKLY": "Semanal",
        "EVENT": "Evento"
    }
    mission_type_text = mission_type_names.get(mission.mission_type, mission.mission_type)
    
    # Construir texto
    text = f"📜 *{mission.title}* 📜\n\n"
    text += f"*Tipo:* {mission_type_text}\n"
    text += f"*Estado:* {'✅ Completada' if (progress and progress.is_completed) else '⏳ En progreso'}\n\n"
    text += f"{mission.description}\n\n"
    
    # Objetivos
    if mission.objectives:
        text += "*Objetivos:*\n"
        for i, obj in enumerate(mission.objectives):
            # Verificar si el objetivo está completado
            is_completed = False
            if progress and progress.progress_data:
                complete_key = obj.get("complete_key", "")
                if complete_key:
                    key_parts = complete_key.split(".", 1)
                    if len(key_parts) == 2:
                        obj_type, obj_value = key_parts
                        
                        if obj_type == "narrative_fragments":
                            is_completed = obj_value in progress.progress_data.get("narrative_fragments", [])
                        elif obj_type == "lore_pieces":
                            is_completed = obj_value in progress.progress_data.get("lore_pieces", [])
                        elif obj_type == "actions":
                            required_count = obj.get("count", 1)
                            current_count = progress.progress_data.get("actions", {}).get(obj_value, 0)
                            is_completed = current_count >= required_count
            
            check_mark = "✅" if is_completed else "⬜"
            text += f"{check_mark} {obj.get('description', 'Objetivo desconocido')}\n"
    
    # Recompensas
    if mission.rewards:
        text += "\n*Recompensas:*\n"
        if "points" in mission.rewards and mission.rewards["points"] > 0:
            text += f"💰 {mission.rewards['points']} besitos\n"
        if "lore_pieces" in mission.rewards and mission.rewards["lore_pieces"]:
            count = len(mission.rewards["lore_pieces"])
            text += f"📜 {count} pista{'s' if count > 1 else ''} de lore\n"
        if "badges" in mission.rewards and mission.rewards["badges"]:
            count = len(mission.rewards["badges"])
            text += f"🏅 {count} insignia{'s' if count > 1 else ''}\n"
    
    # Progreso general
    if progress:
        progress_percent = progress.get_completion_percentage()
        progress_bar = generate_progress_bar(progress_percent)
        text += f"\n*Progreso:* {progress_bar} {progress_percent:.0f}%\n"
    
    # Crear teclado
    keyboard = get_mission_details_keyboard(mission_id, progress and progress.is_completed)
    
    await safe_edit(callback.message, text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(MissionCallbackFactory.filter(F.action == "complete"))
@safe_handler("Error al completar la misión.")
@track_usage("complete_mission")
@transaction()
async def complete_mission(callback: CallbackQuery, callback_data: dict, session: AsyncSession):
    """Completa manualmente una misión si todos los requisitos se cumplen."""
    user_id = callback.from_user.id
    mission_id = callback_data.mission_id
    
    # Inicializar servicio
    mission_service = UnifiedMissionService(session, callback.bot)
    
    # Intentar completar la misión
    success, mission = await mission_service.complete_mission(user_id, mission_id)
    
    if success:
        await callback.answer("¡Misión completada con éxito!", show_alert=True)
        # Redirigir a la lista de misiones
        await show_missions_list(
            callback, 
            MissionCallbackFactory(action="list"), 
            session
        )
    else:
        await callback.answer(
            "No se pudo completar la misión. Verifica que cumplas todos los requisitos.", 
            show_alert=True
        )

@router.callback_query(MissionCallbackFactory.filter(F.action == "narrative_connect"))
@safe_handler("Error al conectar con la narrativa.")
@track_usage("mission_narrative_connect")
@transaction()
async def connect_with_narrative(callback: CallbackQuery, callback_data: dict, session: AsyncSession):
    """Conecta una misión con la narrativa del usuario."""
    user_id = callback.from_user.id
    mission_id = callback_data.mission_id
    
    # Inicializar servicios
    mission_service = UnifiedMissionService(session, callback.bot)
    narrative_service = UnifiedNarrativeService(session, callback.bot)
    
    # Obtener la misión
    mission = await mission_service.get_mission_by_id(mission_id)
    if not mission:
        await callback.answer("Misión no encontrada", show_alert=True)
        return
    
    # Verificar si hay fragmentos narrativos asociados a la misión
    narrative_fragments = mission.requirements.get("narrative_fragments", [])
    if not narrative_fragments:
        await callback.answer("Esta misión no está conectada con ningún fragmento narrativo", show_alert=True)
        return
    
    # Obtener el fragmento actual del usuario
    current_fragment = await narrative_service.get_user_current_fragment(user_id)
    
    # Verificar si el fragmento actual está relacionado con la misión
    is_related = current_fragment and current_fragment.id in narrative_fragments
    
    if is_related:
        text = f"*¡Conexión Narrativa!*\n\n"
        text += f"El fragmento narrativo actual está relacionado con la misión *{mission.title}*.\n\n"
        text += f"Continúa explorando la historia para avanzar en esta misión."
    else:
        text = f"*Conexión Narrativa*\n\n"
        text += f"La misión *{mission.title}* está relacionada con fragmentos específicos de la historia.\n\n"
        text += f"Explora la narrativa para encontrar estos fragmentos y avanzar en la misión."
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🔙 Volver a la misión", 
            callback_data=MissionCallbackFactory(
                action="details", 
                mission_id=mission_id
            ).pack()
        )]
    ])
    
    await safe_edit(callback.message, text, reply_markup=back_keyboard)
    await callback.answer()

# Función auxiliar para generar barra de progreso
def generate_progress_bar(percentage, length=10):
    """Genera una barra de progreso visual basada en porcentaje."""
    filled = int(percentage / 100 * length)
    empty = length - filled
    return "█" * filled + "░" * empty