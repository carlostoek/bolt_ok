"""
Handlers para el sistema de narrativa inmersiva.
Maneja comandos de historia, decisiones y progreso narrativo.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.narrative_engine import NarrativeEngine
from keyboards.narrative_kb import get_narrative_keyboard, get_narrative_stats_keyboard
from utils.message_safety import safe_answer, safe_edit
from utils.user_roles import get_user_role
from utils.handler_decorators import safe_handler, track_usage, transaction
import logging

logger = logging.getLogger(__name__)
router = Router(name="narrative_handler")

@router.message(Command("historia"))
@safe_handler("Error al cargar la historia. Inténtalo de nuevo.")
@track_usage("start_narrative")
@transaction()
async def start_narrative_command(message: Message, session: AsyncSession):
    """Inicia o continúa la narrativa para el usuario."""
    user_id = message.from_user.id
    
    engine = NarrativeEngine(session, message.bot)
    
    # Obtener fragmento actual o iniciar narrativa
    current_fragment = await engine.get_user_current_fragment(user_id)
    
    if not current_fragment:
        # Intentar iniciar narrativa
        current_fragment = await engine.start_narrative(user_id)
        
        if not current_fragment:
            await safe_answer(
                message,
                "❌ **Historia No Disponible**\n\n"
                "No se pudo cargar la narrativa. Puede que necesites completar "
                "algunas misiones primero o que el sistema esté en mantenimiento."
            )
            return
    
    # Mostrar fragmento actual
    await _display_narrative_fragment(message, current_fragment, session)

@router.callback_query(F.data.startswith("narrative_choice:"))
@safe_handler("Error al procesar tu decisión narrativa.")
@track_usage("narrative_choice")
@transaction()
async def handle_narrative_choice(callback: CallbackQuery, session: AsyncSession):
    """Maneja las decisiones narrativas del usuario."""
    user_id = callback.from_user.id
    
    # Extraer índice de la decisión
    choice_data = callback.data.split(":")
    if len(choice_data) < 2:
        await callback.answer("❌ Decisión inválida", show_alert=True)
        return
    
    try:
        choice_index = int(choice_data[1])
    except ValueError:
        await callback.answer("❌ Decisión inválida", show_alert=True)
        return
    
    engine = NarrativeEngine(session, callback.bot)
    
    # Procesar la decisión
    next_fragment = await engine.process_user_decision(user_id, choice_index)
    
    if not next_fragment:
        await callback.answer(
            "❌ No puedes tomar esta decisión ahora. "
            "Puede que necesites más besitos o cumplir otros requisitos.",
            show_alert=True
        )
        return
    
    # Mostrar siguiente fragmento
    await _display_narrative_fragment(callback.message, next_fragment, session, is_callback=True)
    await callback.answer()

@router.callback_query(F.data == "narrative_auto_continue")
@safe_handler("Error en la continuación automática.")
@track_usage("narrative_auto_continue")
@transaction()
async def handle_auto_continue(callback: CallbackQuery, session: AsyncSession):
    """Maneja la continuación automática de fragmentos sin decisiones."""
    user_id = callback.from_user.id
    
    engine = NarrativeEngine(session, callback.bot)
    current_fragment = await engine.get_user_current_fragment(user_id)
    
    if current_fragment and current_fragment.auto_next_fragment_key:
        # Simular una decisión automática
        next_fragment = await engine._get_fragment_by_key(current_fragment.auto_next_fragment_key)
        if next_fragment:
            # Actualizar estado del usuario
            user_state = await engine._get_or_create_user_state(user_id)
            user_state.current_fragment_key = next_fragment.key
            user_state.fragments_visited += 1
            await engine._process_fragment_rewards(user_id, next_fragment)
            
            await _display_narrative_fragment(callback.message, next_fragment, session, is_callback=True)
        else:
            await callback.answer("❌ Error en la continuación automática", show_alert=True)
            return
    else:
        await callback.answer("❌ No hay continuación automática disponible", show_alert=True)
        return
    
    await callback.answer()

@router.message(Command("mi_historia"))
@safe_handler("Error al cargar tus estadísticas narrativas.")
@track_usage("narrative_stats")
@transaction()
async def show_narrative_stats(message: Message, session: AsyncSession):
    """Muestra estadísticas y progreso narrativo del usuario."""
    user_id = message.from_user.id
    
    engine = NarrativeEngine(session, message.bot)
    stats = await engine.get_user_narrative_stats(user_id)
    
    # Crear mensaje de estadísticas
    if stats["current_fragment"]:
        stats_text = f"""📖 **Tu Historia Personal**

🎭 **Fragmento Actual**: {stats['current_fragment']}
📊 **Progreso**: {stats['progress_percentage']:.1f}%
🗺️ **Fragmentos Visitados**: {stats['fragments_visited']}
🎯 **Total Accesible**: {stats['total_accessible']}

🎪 **Decisiones Tomadas**: {len(stats['choices_made'])}"""

        if stats['choices_made']:
            stats_text += "\n\n🔍 **Últimas Decisiones**:"
            for choice in stats['choices_made'][-3:]:  # Últimas 3 decisiones
                stats_text += f"\n• {choice.get('choice_text', 'Decisión desconocida')}"
    else:
        stats_text = """📖 **Tu Historia Personal**

🌟 **Estado**: Historia no iniciada
🎭 **Sugerencia**: Usa `/historia` para comenzar tu aventura

*Lucien te está esperando...*"""
    
    await safe_answer(
        message,
        stats_text,
        reply_markup=get_narrative_stats_keyboard()
    )

@router.callback_query(F.data == "continue_narrative")
@safe_handler("Error al continuar la narrativa.")
@track_usage("continue_narrative")
@transaction()
async def continue_narrative(callback: CallbackQuery, session: AsyncSession):
    """Continúa la narrativa desde donde se quedó el usuario."""
    user_id = callback.from_user.id
    
    engine = NarrativeEngine(session, callback.bot)
    current_fragment = await engine.get_user_current_fragment(user_id)
    
    if current_fragment:
        await _display_narrative_fragment(callback.message, current_fragment, session, is_callback=True)
    else:
        await callback.message.edit_text(
            "❌ **Historia No Encontrada**\n\n"
            "No se pudo cargar tu historia. Usa `/historia` para comenzar.",
            reply_markup=get_narrative_stats_keyboard()
        )
    
    await callback.answer()

@router.callback_query(F.data == "narrative_help")
@safe_handler("Error al mostrar la ayuda narrativa.")
@track_usage("narrative_help")
async def show_narrative_help(callback: CallbackQuery, session: AsyncSession):
    """Muestra ayuda sobre el sistema narrativo."""
    help_text = """📚 **Guía del Sistema Narrativo**

🎭 **¿Cómo funciona?**
• Cada decisión que tomes afecta tu historia
• Gana besitos para desbloquear nuevos fragmentos
• Algunos caminos requieren suscripción VIP

🎪 **Personajes**:
• **Lucien**: Tu guía y mayordomo
• **Diana**: La misteriosa creadora

🎯 **Comandos Útiles**:
• `/historia` - Continuar tu aventura
• `/mi_historia` - Ver tu progreso

💡 **Consejo**: Presta atención a cada detalle, algunas pistas están ocultas en las reacciones y misiones."""
    
    await callback.message.edit_text(
        help_text,
        reply_markup=get_narrative_stats_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "narrative_stats")
@safe_handler("Error al cargar las estadísticas.")
@track_usage("narrative_stats_callback")
@transaction()
async def show_narrative_stats_callback(callback: CallbackQuery, session: AsyncSession):
    """Muestra estadísticas desde callback."""
    user_id = callback.from_user.id
    
    engine = NarrativeEngine(session, callback.bot)
    stats = await engine.get_user_narrative_stats(user_id)
    
    if stats["current_fragment"]:
        stats_text = f"""📖 **Tu Historia Personal**

🎭 **Fragmento Actual**: {stats['current_fragment']}
📊 **Progreso**: {stats['progress_percentage']:.1f}%
🗺️ **Fragmentos Visitados**: {stats['fragments_visited']}
🎯 **Total Accesible**: {stats['total_accessible']}"""
    else:
        stats_text = """📖 **Tu Historia Personal**

🌟 **Estado**: Historia no iniciada
🎭 **Sugerencia**: Usa "Continuar Historia" para comenzar"""
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=get_narrative_stats_keyboard()
    )
    await callback.answer()

async def _display_narrative_fragment(
    message: Message, 
    fragment, 
    session: AsyncSession, 
    is_callback: bool = False
):
    """Muestra un fragmento narrativo con sus opciones."""
    # Formatear el texto del fragmento
    character_emoji = "🎩" if fragment.character == "Lucien" else "🌸"
    
    fragment_text = f"{character_emoji} **{fragment.character}:**\n\n*{fragment.text}*"
    
    # Agregar información de recompensas si las hay
    if fragment.reward_besitos > 0:
        fragment_text += f"\n\n✨ *Has ganado {fragment.reward_besitos} besitos*"
    
    # Crear teclado con opciones
    keyboard = await get_narrative_keyboard(fragment, session)
    
    # Mostrar el fragmento
    if is_callback:
        await safe_edit(message, fragment_text, reply_markup=keyboard)
    else:
        await safe_answer(message, fragment_text, reply_markup=keyboard)
