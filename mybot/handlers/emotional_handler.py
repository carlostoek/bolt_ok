"""
Handlers for emotional system integration with the bot.
Provides commands and callbacks for emotional state visualization and interaction.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.emotional_service import EmotionalService
from services.integration.narrative_emotional_service import NarrativeEmotionalService
from utils.message_safety import safe_answer, safe_edit
from keyboards.emotional_kb import get_emotional_status_keyboard, get_character_relationship_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router(name="emotional_handler")

@router.message(Command("emociones"))
async def show_character_emotions(message: Message, session: AsyncSession):
    """Show the current emotional state of a character toward the user."""
    user_id = message.from_user.id
    
    try:
        # Default to Diana if no character is specified
        parts = message.text.split(maxsplit=1)
        character_name = parts[1] if len(parts) > 1 else "Diana"
        
        # Format character name
        character_name = character_name.strip().capitalize()
        if character_name not in ["Diana", "Lucien"]:
            character_name = "Diana"  # Default to Diana for unknown characters
        
        # Get emotional state
        emotional_service = EmotionalService(session)
        emotional_state = await emotional_service.get_character_emotional_state(user_id, character_name)
        
        # Format message
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
        
        # Add relationship info button
        keyboard = get_emotional_status_keyboard(character_name)
        
        await safe_answer(message, message_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error showing emotions for user {user_id}: {e}")
        await safe_answer(
            message,
            "❌ **Error Temporal**\n\n"
            "No se pudo cargar el estado emocional. Intenta nuevamente en unos momentos."
        )

@router.callback_query(F.data.startswith("emotional_relationship:"))
async def show_character_relationship(callback: CallbackQuery, session: AsyncSession):
    """Show the relationship status between the user and a character."""
    user_id = callback.from_user.id
    
    try:
        # Extract character name
        character_name = callback.data.split(":")[1]
        if character_name not in ["Diana", "Lucien"]:
            await callback.answer("Personaje no válido", show_alert=True)
            return
        
        # Get relationship data
        narrative_emotional_service = NarrativeEmotionalService(session, callback.bot)
        relationship = await narrative_emotional_service.get_character_relationship_status(
            user_id, 
            character_name
        )
        
        if "error" in relationship:
            await callback.answer("Error obteniendo relación", show_alert=True)
            return
        
        # Format message
        status_icons = {
            "distante": "❄️",
            "cautelosa": "🔍",
            "neutral": "🤔",
            "amistosa": "👥",
            "íntima": "💫"
        }
        
        level_icons = ["", "⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"]
        status_icon = status_icons.get(relationship["relationship_status"], "🔍")
        level_indicator = level_icons[min(relationship["relationship_level"], 5)]
        
        message_text = f"**Relación con {character_name}** {status_icon}\n\n"
        message_text += f"**Nivel**: {level_indicator}\n"
        message_text += f"**Estado**: {relationship['relationship_status'].capitalize()}\n"
        message_text += f"**Descripción**: {relationship['description']}\n\n"
        
        # Add positive traits
        if relationship["positive_traits"]:
            message_text += "**Aspectos Positivos**:\n"
            for trait in relationship["positive_traits"]:
                message_text += f"• {trait.capitalize()}\n"
            message_text += "\n"
        
        # Add challenging traits
        if relationship["challenging_traits"]:
            message_text += "**Aspectos a Mejorar**:\n"
            for trait in relationship["challenging_traits"]:
                message_text += f"• {trait.capitalize()}\n"
            message_text += "\n"
        
        # Add narrative progress
        progress = relationship["narrative_progress"]
        message_text += f"**Progreso Narrativo**:\n"
        message_text += f"• Fragmentos visitados: {progress['fragments_visited']}\n"
        message_text += f"• Decisiones tomadas: {progress['choices_made']}\n"
        
        # Create keyboard
        keyboard = get_character_relationship_keyboard(character_name)
        
        await callback.message.edit_text(message_text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing relationship for user {user_id}: {e}")
        await callback.answer("Error mostrando relación", show_alert=True)

@router.callback_query(F.data == "emotional_back_to_status")
async def back_to_emotional_status(callback: CallbackQuery, session: AsyncSession):
    """Return to the emotional status view."""
    user_id = callback.from_user.id
    
    try:
        # Extract character name from current keyboard
        character_name = "Diana"  # Default
        if callback.message.reply_markup:
            for row in callback.message.reply_markup.inline_keyboard:
                for button in row:
                    if button.callback_data.startswith("emotional_relationship:"):
                        character_name = button.callback_data.split(":")[1]
                        break
        
        # Get emotional state
        emotional_service = EmotionalService(session)
        emotional_state = await emotional_service.get_character_emotional_state(user_id, character_name)
        
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
        
        # Add relationship info button
        keyboard = get_emotional_status_keyboard(character_name)
        
        await callback.message.edit_text(message_text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error returning to emotional status for user {user_id}: {e}")
        await callback.answer("Error volviendo al estado emocional", show_alert=True)

@router.callback_query(F.data.startswith("emotional_history:"))
async def show_emotional_history(callback: CallbackQuery, session: AsyncSession):
    """Show the emotional history/evolution for a character."""
    user_id = callback.from_user.id
    
    try:
        # Extract character name
        character_name = callback.data.split(":")[1]
        
        # This would require additional implementation to track historical
        # emotional states. For now, show a placeholder message.
        
        message_text = f"**Historial Emocional de {character_name}**\n\n"
        message_text += "El historial emocional detallado estará disponible próximamente.\n\n"
        message_text += "Esta función te permitirá ver cómo han evolucionado las emociones a lo largo de tu interacción con el personaje."
        
        # Create keyboard to go back
        keyboard = get_character_relationship_keyboard(character_name)
        
        await callback.message.edit_text(message_text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing emotional history for user {user_id}: {e}")
        await callback.answer("Error mostrando historial emocional", show_alert=True)