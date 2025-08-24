"""
Handlers para el sistema de narrativa unificada.
Maneja comandos de historia, decisiones y progreso narrativo con el nuevo sistema unificado.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.unified_narrative_service import UnifiedNarrativeService
from services.unified_mission_service import UnifiedMissionService
from services.narrative_fragment_service import NarrativeFragmentService
from keyboards.narrative_kb import get_narrative_keyboard, get_narrative_stats_keyboard
from utils.message_safety import safe_answer, safe_edit
from utils.user_roles import get_user_role
from utils.handler_decorators import safe_handler, track_usage, transaction
import json
import logging

logger = logging.getLogger(__name__)
router = Router(name="unified_narrative_handler")

@router.message(Command("historia_unificada"))
@safe_handler("Error al cargar la historia unificada. Inténtalo de nuevo.")
@track_usage("start_unified_narrative")
@transaction()
async def start_unified_narrative_command(message: Message, session: AsyncSession):
    """Inicia o continúa la narrativa unificada para el usuario."""
    user_id = message.from_user.id
    
    engine = UnifiedNarrativeService(session, message.bot)
    
    # Obtener fragmento actual o iniciar narrativa
    current_fragment = await engine.get_user_current_fragment(user_id)
    
    if not current_fragment:
        # Intentar iniciar narrativa
        current_fragment = await engine.start_narrative(user_id)
        
        if not current_fragment:
            await safe_answer(
                message,
                "❌ **Historia No Disponible**\n\n"
                "No se pudo cargar la narrativa unificada. Puede que necesites completar "
                "algunas misiones primero o que el sistema esté en mantenimiento."
            )
            return
    
    # Mostrar fragmento actual
    await _display_unified_narrative_fragment(message, current_fragment, session)

@router.callback_query(F.data.startswith("unified_narrative_choice:"))
@safe_handler("Error al procesar tu decisión narrativa unificada.")
@track_usage("unified_narrative_choice")
@transaction()
async def handle_unified_narrative_choice(callback: CallbackQuery, session: AsyncSession):
    """Maneja las decisiones narrativas del usuario en el sistema unificado."""
    user_id = callback.from_user.id
    
    # Extraer datos de la decisión
    choice_data = callback.data.split(":", 1)
    if len(choice_data) < 2:
        await callback.answer("❌ Decisión inválida", show_alert=True)
        return
    
    try:
        # Parsear los datos JSON de la decisión
        choice_info = json.loads(choice_data[1])
        choice_index = choice_info.get("index")
    except (json.JSONDecodeError, ValueError, KeyError):
        await callback.answer("❌ Decisión inválida", show_alert=True)
        return
    
    engine = UnifiedNarrativeService(session, callback.bot)
    
    # Procesar la decisión
    next_fragment = await engine.process_user_decision(user_id, choice_info)
    
    if not next_fragment:
        await callback.answer(
            "❌ No puedes tomar esta decisión ahora. "
            "Puede que necesites más puntos o cumplir otros requisitos.",
            show_alert=True
        )
        return
    
    # Mostrar siguiente fragmento
    await _display_unified_narrative_fragment(callback.message, next_fragment, session, is_callback=True)
    await callback.answer()

@router.message(Command("mi_historia_unificada"))
@safe_handler("Error al cargar tus estadísticas narrativas unificadas.")
@track_usage("unified_narrative_stats")
@transaction()
async def show_unified_narrative_stats(message: Message, session: AsyncSession):
    """Muestra estadísticas y progreso narrativo del usuario en el sistema unificado."""
    user_id = message.from_user.id
    
    engine = UnifiedNarrativeService(session, message.bot)
    stats = await engine.get_user_narrative_stats(user_id)
    
    # Crear mensaje de estadísticas
    if stats["current_fragment"]:
        stats_text = f"""📖 **Tu Historia Unificada**

🎭 **Fragmento Actual**: {stats['current_fragment'][:20]}...
📊 **Progreso**: {stats['progress_percentage']:.1f}%
🗺️ **Fragmentos Visitados**: {stats['fragments_visited']}
🎯 **Total Accesible**: {stats['total_accessible']}

🎪 **Decisiones Tomadas**: {len(stats['choices_made'])}"""

        if stats['choices_made']:
            stats_text += "\n\n🔍 **Últimas Decisiones**:"
            for choice in stats['choices_made'][-3:]:  # Últimas 3 decisiones
                stats_text += f"\n• {choice.get('choice_text', 'Decisión desconocida')}"
    else:
        stats_text = """📖 **Tu Historia Unificada**

🌟 **Estado**: Historia no iniciada
🎭 **Sugerencia**: Usa `/historia_unificada` para comenzar tu aventura

*Lucien te está esperando...*"""
    
    await safe_answer(
        message,
        stats_text,
        reply_markup=get_narrative_stats_keyboard()
    )

@router.callback_query(F.data == "continue_unified_narrative")
@safe_handler("Error al continuar la narrativa unificada.")
@track_usage("continue_unified_narrative")
@transaction()
async def continue_unified_narrative(callback: CallbackQuery, session: AsyncSession):
    """Continúa la narrativa unificada desde donde se quedó el usuario."""
    user_id = callback.from_user.id
    
    engine = UnifiedNarrativeService(session, callback.bot)
    current_fragment = await engine.get_user_current_fragment(user_id)
    
    if current_fragment:
        await _display_unified_narrative_fragment(callback.message, current_fragment, session, is_callback=True)
    else:
        await callback.message.edit_text(
            "❌ **Historia No Encontrada**\n\n"
            "No se pudo cargar tu historia unificada. Usa `/historia_unificada` para comenzar.",
            reply_markup=get_narrative_stats_keyboard()
        )
    
    await callback.answer()


@router.callback_query(F.data == "mission:list")
@safe_handler("Error al cargar las misiones disponibles.")
@track_usage("list_missions")
@transaction()
async def show_missions_from_narrative(callback: CallbackQuery, session: AsyncSession):
    """Muestra las misiones disponibles desde la narrativa."""
    user_id = callback.from_user.id
    
    # Inicializar servicio de misiones
    mission_service = UnifiedMissionService(session, callback.bot)
    
    # Obtener misiones disponibles
    missions = await mission_service.get_user_available_missions(user_id)
    
    if not missions:
        await callback.message.edit_text(
            "🎯 **Misiones**\n\n"
            "No tienes misiones disponibles en este momento.",
            reply_markup=get_narrative_stats_keyboard()
        )
        await callback.answer()
        return
    
    # Contar misiones por tipo y estado
    main_active = sum(1 for m in missions if m["mission_type"] == "MAIN" and not m["is_completed"])
    side_active = sum(1 for m in missions if m["mission_type"] == "SIDE" and not m["is_completed"])
    daily_active = sum(1 for m in missions if m["mission_type"] == "DAILY" and not m["is_completed"])
    weekly_active = sum(1 for m in missions if m["mission_type"] == "WEEKLY" and not m["is_completed"])
    completed = sum(1 for m in missions if m["is_completed"])
    
    # Construir texto
    text = "🎯 **Misiones Disponibles**\n\n"
    
    if main_active > 0:
        text += f"📜 **Principales**: {main_active} activas\n"
    if side_active > 0:
        text += f"📌 **Secundarias**: {side_active} activas\n"
    if daily_active > 0:
        text += f"🔄 **Diarias**: {daily_active} activas\n"
    if weekly_active > 0:
        text += f"📅 **Semanales**: {weekly_active} activas\n"
    if completed > 0:
        text += f"✅ **Completadas**: {completed} misiones\n"
    
    # Mencionar misiones relacionadas con la narrativa
    narrative_service = UnifiedNarrativeService(session, callback.bot)
    current_fragment = await narrative_service.get_user_current_fragment(user_id)
    
    if current_fragment:
        narrative_missions = []
        for mission in missions:
            if not mission["is_completed"] and "narrative_fragments" in mission.get("requirements", {}):
                if current_fragment.id in mission["requirements"]["narrative_fragments"]:
                    narrative_missions.append(mission)
        
        if narrative_missions:
            text += "\n**Misiones relacionadas con tu narrativa actual:**\n"
            for mission in narrative_missions[:3]:  # Mostrar máximo 3
                progress = mission["progress_percentage"]
                text += f"• {mission['title']} ({progress:.0f}%)\n"
    
    text += "\nUsa el comando /misiones para gestionar tus misiones."
    
    # Mostrar resultados
    await callback.message.edit_text(
        text,
        reply_markup=get_narrative_stats_keyboard()
    )
    await callback.answer()


async def _update_mission_progress(user_id: int, fragment_id: str, session: AsyncSession, bot=None):
    """Actualiza el progreso de misiones relacionadas con un fragmento narrativo."""
    try:
        # Inicializar servicio de misiones
        mission_service = UnifiedMissionService(session, bot)
        
        # Actualizar progreso
        completed_missions = await mission_service.update_user_progress(
            user_id,
            "narrative_fragment",
            {"fragment_id": fragment_id}
        )
        
        logger.info(f"Usuario {user_id} progresó en misiones con fragmento {fragment_id}")
        if completed_missions:
            logger.info(f"Usuario {user_id} completó {len(completed_missions)} misiones")
            
        return completed_missions
    except Exception as e:
        logger.error(f"Error al actualizar progreso de misiones: {e}")
        return []

async def _display_unified_narrative_fragment(
    message: Message, 
    fragment, 
    session: AsyncSession, 
    is_callback: bool = False
):
    """Muestra un fragmento narrativo unificado con sus opciones."""
    # Actualizar progreso de misiones relacionadas con este fragmento
    user_id = message.from_user.id
    await _update_mission_progress(user_id, fragment.id, session, message.bot)
    
    # Formatear el texto del fragmento
    character_emoji = "📖"
    
    fragment_text = f"{character_emoji} **{fragment.title}**\n\n{fragment.content}"
    
    # Agregar información de recompensas si las hay en los triggers
    if fragment.triggers:
        reward_points = fragment.triggers.get("reward_points", 0)
        if reward_points > 0:
            fragment_text += f"\n\n✨ *Has ganado {reward_points} puntos*"
        
        # Mostrar información de pistas desbloqueadas
        unlock_lore = fragment.triggers.get("unlock_lore")
        if unlock_lore:
            fragment_text += f"\n\n🗝️ *Has desbloqueado una nueva pista*"
    
    # Crear teclado con opciones para fragmentos de decisión
    keyboard = await _get_unified_narrative_keyboard(fragment, session)
    
    # Mostrar el fragmento
    if is_callback:
        await safe_edit(message, fragment_text, reply_markup=keyboard)
    else:
        await safe_answer(message, fragment_text, reply_markup=keyboard)

async def _get_unified_narrative_keyboard(fragment, session: AsyncSession):
    """Crea un teclado para fragmentos narrativos unificados."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    builder = InlineKeyboardBuilder()
    
    # Si es un fragmento de decisión, agregar las opciones
    if fragment.is_decision and fragment.choices:
        for i, choice in enumerate(fragment.choices):
            choice_data = {
                "index": i,
                "fragment_id": fragment.id
            }
            builder.button(
                text=choice.get("text", f"Opción {i+1}"),
                callback_data=f"unified_narrative_choice:{json.dumps(choice_data)}"
            )
    
    # Agregar botones de navegación
    builder.button(text="📊 Mis Estadísticas", callback_data="narrative_stats")
    builder.button(text="🎯 Misiones", callback_data="mission:list")
    builder.button(text="❓ Ayuda", callback_data="narrative_help")
    builder.button(text="↩️ Volver", callback_data="continue_narrative")
    
    builder.adjust(1)  # Una columna
    return builder.as_markup()