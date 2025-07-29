"""
Enhanced narrative handlers that integrate emotional system.
Provides emotionally aware narrative interactions.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.integration.narrative_emotional_service import NarrativeEmotionalService
from services.emotional_service import EmotionalService
from services.narrative_service import NarrativeService
from keyboards.emotional_kb import get_enhanced_narrative_keyboard
from keyboards.narrative_kb import get_narrative_stats_keyboard
from utils.message_safety import safe_answer, safe_edit
import logging

logger = logging.getLogger(__name__)
router = Router(name="emotional_narrative_handler")

@router.message(Command("historia_emocional"))
async def start_emotional_narrative(message: Message, session: AsyncSession):
    """Start or continue emotional narrative for the user."""
    user_id = message.from_user.id
    
    try:
        # Initialize services
        narrative_emotional_service = NarrativeEmotionalService(session, message.bot)
        
        # Get current fragment with emotional context
        result = await narrative_emotional_service.get_emotionally_enhanced_fragment(user_id)
        
        if "error" in result:
            await safe_answer(
                message,
                "❌ **Historia No Disponible**\n\n"
                "No se pudo cargar la narrativa emocional. Puede que necesites completar "
                "algunas misiones primero o que el sistema esté en mantenimiento."
            )
            return
        
        # Display the enhanced fragment
        await _display_emotional_narrative_fragment(message, result, session)
        
    except Exception as e:
        logger.error(f"Error en comando historia_emocional para usuario {user_id}: {e}")
        await safe_answer(
            message,
            "❌ **Error Temporal**\n\n"
            "Hubo un problema al cargar tu historia emocional. Intenta nuevamente en unos momentos."
        )

@router.callback_query(F.data.startswith("emotional_narrative_choice:"))
async def handle_emotional_narrative_choice(callback: CallbackQuery, session: AsyncSession):
    """Handle narrative choices with emotional impact."""
    user_id = callback.from_user.id
    
    try:
        # Extract choice ID
        choice_data = callback.data.split(":")
        if len(choice_data) < 2:
            await callback.answer("❌ Decisión inválida", show_alert=True)
            return
        
        choice_id = int(choice_data[1])
        
        # Process the choice with emotional impact
        narrative_emotional_service = NarrativeEmotionalService(session, callback.bot)
        result = await narrative_emotional_service.process_narrative_choice_with_emotions(
            user_id, 
            choice_id
        )
        
        if "error" in result:
            await callback.answer(
                "❌ No puedes tomar esta decisión ahora. "
                "Puede que necesites más besitos o cumplir otros requisitos.",
                show_alert=True
            )
            return
        
        # Show emotional change indicator if applicable
        emotional_changes = result.get("emotional_changes", {})
        if emotional_changes and emotional_changes.get("changes"):
            # Format a brief notification about emotional changes
            prev_emotion = emotional_changes.get("previous_dominant", "neutral")
            new_emotion = emotional_changes.get("new_dominant", "neutral")
            
            emotion_icons = {
                "joy": "😊",
                "trust": "🤝",
                "fear": "😨",
                "sadness": "😢",
                "anger": "😠",
                "surprise": "😲",
                "anticipation": "🔮",
                "disgust": "🤢",
                "neutral": "😐"
            }
            
            if prev_emotion != new_emotion:
                change_message = f"{emotion_icons.get(prev_emotion, '🔍')} → {emotion_icons.get(new_emotion, '🔍')}"
                await callback.answer(f"Cambio emocional: {change_message}", show_alert=False)
            else:
                # Show first significant change
                for change in emotional_changes.get("changes", [])[:1]:
                    emotion = change.get("emotion", "")
                    change_value = change.get("change", 0)
                    
                    if abs(change_value) >= 3:
                        direction = "+" if change_value > 0 else ""
                        await callback.answer(
                            f"{emotion_icons.get(emotion, '🔍')} {emotion.capitalize()}: {direction}{change_value:.0f}",
                            show_alert=False
                        )
                        break
        
        # Display the next fragment
        await _display_emotional_narrative_fragment(callback.message, result, session, is_callback=True)
        
    except ValueError:
        await callback.answer("❌ Decisión inválida", show_alert=True)
    except Exception as e:
        logger.error(f"Error procesando decisión narrativa emocional para usuario {user_id}: {e}")
        await callback.answer("❌ Error procesando tu decisión", show_alert=True)

@router.callback_query(F.data == "emotional_narrative_auto_continue")
async def handle_emotional_auto_continue(callback: CallbackQuery, session: AsyncSession):
    """Handle auto-continue for emotional narrative fragments."""
    user_id = callback.from_user.id
    
    try:
        # Get current fragment
        narrative_service = NarrativeService(session)
        current_fragment = await narrative_service.get_user_current_fragment(user_id)
        
        if not current_fragment or not current_fragment.auto_next_fragment_key:
            await callback.answer("❌ No hay continuación automática disponible", show_alert=True)
            return
        
        # Get the next fragment with emotional context
        narrative_emotional_service = NarrativeEmotionalService(session, callback.bot)
        
        # Update user state to next fragment
        user_state = await narrative_service._get_or_create_user_state(user_id)
        user_state.current_fragment_key = current_fragment.auto_next_fragment_key
        user_state.fragments_visited += 1
        await session.commit()
        
        # Get the enhanced fragment
        result = await narrative_emotional_service.get_emotionally_enhanced_fragment(
            user_id,
            current_fragment.auto_next_fragment_key
        )
        
        if "error" in result:
            await callback.answer("❌ Error en la continuación automática", show_alert=True)
            return
        
        # Display the next fragment
        await _display_emotional_narrative_fragment(callback.message, result, session, is_callback=True)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error en continuación automática emocional para usuario {user_id}: {e}")
        await callback.answer("❌ Error en la continuación", show_alert=True)

@router.callback_query(F.data.startswith("emotional_status:"))
async def show_emotional_status_from_narrative(callback: CallbackQuery, session: AsyncSession):
    """Show emotional status from narrative context."""
    user_id = callback.from_user.id
    
    try:
        # Extract character name
        character_name = callback.data.split(":")[1]
        
        # Get emotional state
        emotional_service = EmotionalService(session)
        emotional_state = await emotional_service.get_character_emotional_state(user_id, character_name)
        
        # Format message (similar to emotional_handler.show_character_emotions)
        dominant_emotion = emotional_state.get("dominant_emotion", "neutral")
        dominant_emotion_icon = {
            "joy": "😊",
            "trust": "🤝",
            "fear": "😨",
            "sadness": "😢",
            "anger": "😠",
            "surprise": "😲",
            "anticipation": "🔮",
            "disgust": "🤢",
            "neutral": "😐"
        }.get(dominant_emotion, "🔍")
        
        message_text = f"**Estado Emocional de {character_name}** {dominant_emotion_icon}\n\n"
        
        # Add dominant emotion description
        emotion_descriptions = {
            "joy": "se siente **feliz** y contenta",
            "trust": "siente **confianza** y seguridad",
            "fear": "siente **miedo** e inseguridad",
            "sadness": "se siente **triste** y melancólica",
            "anger": "está **molesta** o irritada",
            "surprise": "está **sorprendida** o asombrada",
            "anticipation": "siente **anticipación** y expectativa",
            "disgust": "siente **disgusto** o rechazo",
            "neutral": "se siente **neutral**"
        }
        
        message_text += f"{character_name} {emotion_descriptions.get(dominant_emotion, 'tiene emociones mixtas')} en este momento.\n\n"
        
        # Add emotional state bars
        message_text += "**Estado Emocional Detallado:**\n"
        for emotion in ["joy", "trust", "fear", "sadness", "anger", "surprise", "anticipation", "disgust"]:
            if emotion in emotional_state:
                value = emotional_state[emotion]
                icon = {
                    "joy": "😊",
                    "trust": "🤝",
                    "fear": "😨",
                    "sadness": "😢",
                    "anger": "😠",
                    "surprise": "😲",
                    "anticipation": "🔮", 
                    "disgust": "🤢"
                }.get(emotion, "🔍")
                
                # Create a visual bar
                bar_length = int(value / 10)  # 0-10 characters
                bar = "█" * bar_length + "▒" * (10 - bar_length)
                
                # Format with value
                message_text += f"{icon} {emotion.capitalize()}: {bar} {value:.0f}%\n"
        
        # Add button to return to narrative
        keyboard = [
            [InlineKeyboardButton(text="Volver a Historia", callback_data="emotional_return_to_narrative")]
        ]
        
        await callback.message.edit_text(
            message_text, 
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing emotional status from narrative for user {user_id}: {e}")
        await callback.answer("Error mostrando estado emocional", show_alert=True)

@router.callback_query(F.data == "emotional_return_to_narrative")
async def return_to_narrative(callback: CallbackQuery, session: AsyncSession):
    """Return to the narrative from emotional status view."""
    user_id = callback.from_user.id
    
    try:
        # Get current fragment with emotional context
        narrative_emotional_service = NarrativeEmotionalService(session, callback.bot)
        result = await narrative_emotional_service.get_emotionally_enhanced_fragment(user_id)
        
        if "error" in result:
            await callback.answer("❌ Error volviendo a la narrativa", show_alert=True)
            return
        
        # Display the fragment
        await _display_emotional_narrative_fragment(callback.message, result, session, is_callback=True)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error returning to narrative for user {user_id}: {e}")
        await callback.answer("❌ Error volviendo a la historia", show_alert=True)

@router.callback_query(F.data.startswith("emotional_switch:"))
async def switch_character_emotional_view(callback: CallbackQuery, session: AsyncSession):
    """Switch to viewing a different character's emotional state."""
    user_id = callback.from_user.id
    
    try:
        # Extract new character name
        new_character = callback.data.split(":")[1]
        
        # Get emotional state for new character
        emotional_service = EmotionalService(session)
        emotional_state = await emotional_service.get_character_emotional_state(user_id, new_character)
        
        # Format message (similar to show_character_emotions)
        dominant_emotion = emotional_state.get("dominant_emotion", "neutral")
        dominant_emotion_icon = {
            "joy": "😊",
            "trust": "🤝",
            "fear": "😨",
            "sadness": "😢",
            "anger": "😠",
            "surprise": "😲",
            "anticipation": "🔮",
            "disgust": "🤢",
            "neutral": "😐"
        }.get(dominant_emotion, "🔍")
        
        message_text = f"**Estado Emocional de {new_character}** {dominant_emotion_icon}\n\n"
        
        # Add dominant emotion description
        emotion_descriptions = {
            "joy": "se siente **feliz** y contenta",
            "trust": "siente **confianza** y seguridad",
            "fear": "siente **miedo** e inseguridad",
            "sadness": "se siente **triste** y melancólica",
            "anger": "está **molesta** o irritada",
            "surprise": "está **sorprendida** o asombrada",
            "anticipation": "siente **anticipación** y expectativa",
            "disgust": "siente **disgusto** o rechazo",
            "neutral": "se siente **neutral**"
        }
        
        message_text += f"{new_character} {emotion_descriptions.get(dominant_emotion, 'tiene emociones mixtas')} en este momento.\n\n"
        
        # Add emotional state bars
        message_text += "**Estado Emocional Detallado:**\n"
        for emotion in ["joy", "trust", "fear", "sadness", "anger", "surprise", "anticipation", "disgust"]:
            if emotion in emotional_state:
                value = emotional_state[emotion]
                icon = {
                    "joy": "😊",
                    "trust": "🤝",
                    "fear": "😨",
                    "sadness": "😢",
                    "anger": "😠",
                    "surprise": "😲",
                    "anticipation": "🔮", 
                    "disgust": "🤢"
                }.get(emotion, "🔍")
                
                # Create a visual bar
                bar_length = int(value / 10)  # 0-10 characters
                bar = "█" * bar_length + "▒" * (10 - bar_length)
                
                # Format with value
                message_text += f"{icon} {emotion.capitalize()}: {bar} {value:.0f}%\n"
        
        # Create keyboard for new character
        from keyboards.emotional_kb import get_emotional_status_keyboard
        keyboard = get_emotional_status_keyboard(new_character)
        
        await callback.message.edit_text(message_text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error switching character emotional view for user {user_id}: {e}")
        await callback.answer("Error cambiando de personaje", show_alert=True)

async def _display_emotional_narrative_fragment(
    message: Message, 
    enhanced_fragment: dict, 
    session: AsyncSession, 
    is_callback: bool = False
):
    """
    Display an emotionally enhanced narrative fragment.
    
    Args:
        message: The message to reply to or edit
        enhanced_fragment: The enhanced fragment data from NarrativeEmotionalService
        session: Database session
        is_callback: Whether this is a callback response (edit) or new message
    """
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    try:
        # Extract data from enhanced fragment
        fragment = enhanced_fragment.get("fragment", {})
        emotional_context = enhanced_fragment.get("emotional_context", {})
        choices = enhanced_fragment.get("choices", [])
        
        # Get character and emotional state
        character_name = fragment.get("character", "Diana")
        dominant_emotion = emotional_context.get("dominant_emotion", "neutral")
        
        # Get emotional modifiers
        modifiers = emotional_context.get("response_modifiers", {})
        
        # Format the fragment text with emotional modifiers
        text_prefix = modifiers.get("text_prefixes", [""])[0] if modifiers.get("text_prefixes") else ""
        text_suffix = modifiers.get("text_suffixes", [""])[0] if modifiers.get("text_suffixes") else ""
        
        # Get emotion icon
        emotion_icon = {
            "joy": "😊",
            "trust": "🤝",
            "fear": "😨",
            "sadness": "😢",
            "anger": "😠",
            "surprise": "😲",
            "anticipation": "🔮",
            "disgust": "🤢",
            "neutral": "😐"
        }.get(dominant_emotion, "🎭")
        
        # Format message text
        character_prefix = f"{emotion_icon} **{character_name}:**\n\n"
        fragment_text = f"{text_prefix}*{fragment.get('text', '')}*{text_suffix}"
        
        message_text = character_prefix + fragment_text
        
        # Add information about rewards if present
        if fragment.get("reward_besitos", 0) > 0:
            message_text += f"\n\n✨ *Has ganado {fragment.get('reward_besitos')} besitos*"
        
        # Create keyboard with choices
        keyboard = []
        
        for choice in choices:
            # Enhance choice text with emotional indicators if significant impact
            choice_text = choice.get("text", "")
            impact = choice.get("emotional_impact", {})
            
            # Add indicators for significant emotional impacts
            primary_changes = impact.get("primary_changes", [])
            if primary_changes:
                # Get the most significant change
                top_change = primary_changes[0]
                emotion = top_change.get("emotion", "")
                change = top_change.get("change", 0)
                
                if abs(change) >= 3:
                    emotion_icon = {
                        "joy": "😊",
                        "trust": "🤝",
                        "fear": "😨",
                        "sadness": "😢",
                        "anger": "😠",
                        "surprise": "😲",
                        "anticipation": "🔮",
                        "disgust": "🤢"
                    }.get(emotion, "")
                    
                    if emotion_icon:
                        choice_text = f"{choice_text} {emotion_icon}"
            
            keyboard.append([
                InlineKeyboardButton(
                    text=choice_text,
                    callback_data=f"emotional_narrative_choice:{choice.get('id')}"
                )
            ])
        
        # Add auto-continue button if applicable
        if fragment.get("auto_next_fragment_key"):
            keyboard.append([
                InlineKeyboardButton(
                    text="Continuar...",
                    callback_data="emotional_narrative_auto_continue"
                )
            ])
        
        # Add emotional status button
        keyboard.append([
            InlineKeyboardButton(
                text=f"Estado Emocional de {character_name}",
                callback_data=f"emotional_status:{character_name}"
            )
        ])
        
        # Send or edit message
        if is_callback:
            await safe_edit(
                message, 
                message_text, 
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
        else:
            await safe_answer(
                message, 
                message_text, 
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            
    except Exception as e:
        logger.error(f"Error displaying emotional narrative fragment: {e}")
        
        # Send a fallback message
        error_text = "❌ **Error al mostrar fragmento narrativo**\n\nHubo un problema al cargar el contenido emocional."
        
        if is_callback:
            await safe_edit(message, error_text)
        else:
            await safe_answer(message, error_text)