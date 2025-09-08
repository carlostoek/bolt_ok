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

@router.message(Command("narrative"))
@safe_handler("😔 Las corrientes del destino se han enredado... Inténtalo de nuevo, querido.")
@track_usage("start_narrative")
@transaction()
async def start_narrative_command(message: Message, session: AsyncSession):
    """Inicia o continúa la narrativa usando el sistema MVP con Cinema Architecture."""
    user_id = message.from_user.id
    
    try:
        from services.mvp_narrative_progression_service import MVPNarrativeProgressionService
        
        # Use MVP narrative system for consistent experience
        narrative_service = MVPNarrativeProgressionService(session)
        
        # Get or start user's narrative journey
        current_fragment = await narrative_service.fragment_service.get_user_current_fragment(user_id)
        
        if not current_fragment:
            # Start new narrative journey
            start_result = await narrative_service.start_user_narrative(user_id)
            if start_result['success']:
                current_fragment = start_result['fragment']
            else:
                await safe_answer(
                    message,
                    "🌙 **Los Hilos del Destino**\n\n"
                    "Algo interrumpe nuestra conexión... Los misterios esperan un momento más propicio. "
                    "Inténtalo de nuevo en unos momentos, querido."
                )
                return
        
        # Display current fragment with Cinema Architecture enhancement
        await _display_mvp_narrative_fragment(message, current_fragment, session)
        
    except Exception as e:
        logger.error(f"Error starting MVP narrative for user {user_id}: {e}")
        await safe_answer(
            message,
            "🌙 **Las Corrientes Místicas Fluctúan**\n\n"
            "Los velos entre realidades tiemblan... Algo interrumpe nuestra conexión momentáneamente. "
            "Los secretos estarán aquí cuando regreses, querido."
        )

@router.message(Command("historia"))
@safe_handler("Error al cargar la historia. Inténtalo de nuevo.")
@track_usage("start_narrative")
@transaction()
async def start_legacy_narrative_command(message: Message, session: AsyncSession):
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

@router.callback_query(F.data.startswith("narrative_choice_"))
@safe_handler("🌙 Los vientos del destino encuentran resistencia... Inténtalo de nuevo, querido.")
@track_usage("mvp_narrative_choice")
@transaction()
async def handle_mvp_narrative_choice(callback: CallbackQuery, session: AsyncSession):
    """Handles MVP narrative choice selections with character consistency."""
    user_id = callback.from_user.id
    
    try:
        from services.mvp_narrative_progression_service import MVPNarrativeProgressionService
        
        # Parse choice data: narrative_choice_{fragment_id}_{choice_index}
        callback_parts = callback.data.split("_")
        if len(callback_parts) < 4:
            await callback.answer("❌ Elección inválida", show_alert=True)
            return
        
        fragment_id = callback_parts[2]
        choice_index = int(callback_parts[3])
        
        narrative_service = MVPNarrativeProgressionService(session)
        
        # Process the choice
        choice_result = await narrative_service.make_user_choice(user_id, fragment_id, choice_index)
        
        if not choice_result['success']:
            await callback.answer(
                "🌙 Esta senda está cerrada por ahora... Los secretos requieren preparación.",
                show_alert=True
            )
            return
        
        # Get the next fragment
        next_fragment = choice_result.get('current_fragment')
        if not next_fragment:
            await callback.answer(
                "🌙 Los misterios se profundizan... Tu elección resuena en las corrientes del destino.",
                show_alert=True
            )
            return
        
        # Display the next fragment
        await _display_mvp_narrative_fragment(callback.message, next_fragment, session, is_callback=True)
        await callback.answer("✨ Tu elección resuena en los misterios...")
        
    except Exception as e:
        logger.error(f"Error handling MVP narrative choice for user {user_id}: {e}")
        await callback.answer(
            "🌙 Las corrientes del destino fluctúan... Inténtalo de nuevo, querido.",
            show_alert=True
        )

@router.callback_query(F.data.startswith("narrative_continue_"))
@safe_handler("🌙 Los velos del tiempo oscilan... Inténtalo de nuevo.")
@track_usage("mvp_narrative_continue")
@transaction()
async def handle_mvp_narrative_continue(callback: CallbackQuery, session: AsyncSession):
    """Handles continuation of MVP narrative story fragments."""
    user_id = callback.from_user.id
    
    try:
        from services.mvp_narrative_progression_service import MVPNarrativeProgressionService
        
        # Parse fragment ID from callback data
        callback_parts = callback.data.split("_")
        if len(callback_parts) < 3:
            await callback.answer("❌ Error en la continuación", show_alert=True)
            return
        
        fragment_id = callback_parts[2]
        
        narrative_service = MVPNarrativeProgressionService(session)
        
        # Get next fragment in sequence
        next_result = await narrative_service.continue_story(user_id, fragment_id)
        
        if not next_result['success']:
            # End of storyline or no continuation
            completion_text = "🌟 **Capítulo Completado**\n\n"
            completion_text += "*Los ecos de esta parte de tu viaje se desvanecen, "
            completion_text += "dejando solo el susurro de promesas por cumplir...*\n\n"
            completion_text += "💋 Regresa a Diana para continuar explorando los misterios."
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💋 Regresar a Diana", callback_data="diana_main")],
                [InlineKeyboardButton(text="📊 Mi Progreso", callback_data="narrative_progress")]
            ])
            
            await callback.message.edit_text(completion_text, reply_markup=keyboard)
            await callback.answer("✨ Capítulo completado...")
            return
        
        # Continue with next fragment
        next_fragment = next_result.get('current_fragment')
        if next_fragment:
            await _display_mvp_narrative_fragment(callback.message, next_fragment, session, is_callback=True)
            await callback.answer("🌟 La historia continúa...")
        
    except Exception as e:
        logger.error(f"Error continuing MVP narrative for user {user_id}: {e}")
        await callback.answer(
            "🌙 Los hilos narrativos se han enredado... Inténtalo de nuevo.",
            show_alert=True
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

async def _display_mvp_narrative_fragment(
    message: Message, 
    fragment, 
    session: AsyncSession, 
    is_callback: bool = False
):
    """
    Displays an MVP narrative fragment with Diana's character-consistent styling.
    Integrates with Cinema Architecture for enhanced storytelling.
    """
    try:
        # Character-consistent presentation based on fragment context
        if hasattr(fragment, 'character') and fragment.character:
            if fragment.character.lower() == 'lucien':
                character_emoji = "🎩"
                character_name = "**Lucien**"
            else:
                character_emoji = "🌙"
                character_name = "**Diana**"
        else:
            # Default Diana presentation for MVP fragments
            character_emoji = "🌙"
            character_name = "**Diana**"
        
        # Build fragment text with character consistency
        fragment_text = f"{character_emoji} {character_name}\n\n"
        
        # Add title if available
        if hasattr(fragment, 'title') and fragment.title:
            fragment_text += f"*{fragment.title}*\n\n"
        
        # Main content with mysterious styling
        if hasattr(fragment, 'content') and fragment.content:
            fragment_text += f"*{fragment.content}*"
        elif hasattr(fragment, 'text') and fragment.text:
            fragment_text += f"*{fragment.text}*"
        else:
            fragment_text += "*Los misterios se despliegan ante ti...*"
        
        # Add reward information with character consistency
        if hasattr(fragment, 'triggers') and fragment.triggers:
            reward_points = fragment.triggers.get('reward_points', 0)
            if reward_points > 0:
                fragment_text += f"\n\n✨ *{reward_points} besitos danzan hacia ti como susurros de aprobación*"
            
            unlock_lore = fragment.triggers.get('unlock_lore')
            if unlock_lore:
                fragment_text += f"\n\n🗝️ *Un secreto más se revela... Los velos se vuelven más tenues*"
        
        # Create keyboard for MVP fragments
        keyboard = await _get_mvp_narrative_keyboard(fragment, session)
        
        # Display the fragment
        if is_callback:
            await safe_edit(message, fragment_text, reply_markup=keyboard)
        else:
            await safe_answer(message, fragment_text, reply_markup=keyboard)
            
    except Exception as e:
        logger.error(f"Error displaying MVP narrative fragment: {e}")
        fallback_text = f"🌙 **Diana**\n\n*Los hilos del destino se entrelazan de maneras misteriosas... "
        fallback_text += "Algo interrumpe nuestra conexión momentáneamente.*"
        
        if is_callback:
            await safe_edit(message, fallback_text)
        else:
            await safe_answer(message, fallback_text)

async def _get_mvp_narrative_keyboard(fragment, session: AsyncSession):
    """Creates a keyboard for MVP narrative fragments with character-consistent options."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    import json
    
    builder = InlineKeyboardBuilder()
    
    try:
        # If it's a decision fragment, add the choice options
        if hasattr(fragment, 'is_decision') and fragment.is_decision:
            if hasattr(fragment, 'choices') and fragment.choices:
                for i, choice in enumerate(fragment.choices):
                    choice_text = choice.get('text', f"Elección {i+1}")
                    choice_data = f"narrative_choice_{fragment.id}_{i}"
                    builder.button(
                        text=f"🔮 {choice_text}",
                        callback_data=choice_data
                    )
        else:
            # For story fragments, add continue option
            builder.button(
                text="🌟 Continuar el Viaje",
                callback_data=f"narrative_continue_{fragment.id}"
            )
        
        # Add navigation options with character-consistent language
        builder.button(text="📊 Mi Progreso Místico", callback_data="narrative_progress")
        builder.button(text="🎭 Mi Perfil Narrativo", callback_data="narrative_profile")
        builder.button(text="💋 Regresar a Diana", callback_data="diana_main")
        builder.button(text="❓ Guía de Misterios", callback_data="narrative_help")
        
        builder.adjust(1)  # One column layout
        return builder.as_markup()
        
    except Exception as e:
        logger.error(f"Error creating MVP narrative keyboard: {e}")
        # Fallback simple keyboard
        builder.button(text="💋 Regresar a Diana", callback_data="diana_main")
        return builder.as_markup()

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
