"""
Diana Emotional System Handlers

This module provides handler functions for Diana's emotional memory system.
It demonstrates how to use the DianaEmotionalService to store and retrieve emotional memories.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Any, Optional

from services.diana_emotional_service import DianaEmotionalService
from database.diana_models import (
    EmotionalInteractionType,
    EmotionCategory,
    EmotionalIntensity,
    RelationshipStatus
)
from utils.safe_message import safe_answer

router = Router()

# --- Interaction Handling Examples ---


@router.message(Command("relationship_status"))
async def handle_relationship_status(message: Message, session: AsyncSession):
    """Handler for viewing current relationship status with Diana."""
    try:
        user_id = message.from_user.id
        
        # Create service instance
        diana_service = DianaEmotionalService(session)
        
        # Get relationship state
        result = await diana_service.get_relationship_state(user_id)
        
        if result["success"]:
            relationship = result["relationship"]
            
            # Format relationship info for display
            status = relationship["status"]
            trust_level = f"{relationship['trust_level'] * 100:.1f}%"
            rapport = f"{relationship['rapport'] * 100:.1f}%"
            interactions = relationship["interaction_count"]
            
            # Create a relationship summary based on status
            status_descriptions = {
                "initial": "Nos estamos conociendo",
                "acquaintance": "Somos conocidos",
                "friendly": "Somos amigos",
                "close": "Somos buenos amigos",
                "intimate": "Tenemos una relación cercana",
                "strained": "Nuestra relación está un poco tensa",
                "repaired": "Hemos resuelto nuestras diferencias",
                "distant": "No hemos hablado mucho últimamente",
                "complex": "Nuestra relación es complicada"
            }
            
            status_description = status_descriptions.get(status, "Relación en desarrollo")
            
            # Build a personalized message based on relationship metrics
            message_text = (
                f"💖 *Mi relación contigo* 💖\n\n"
                f"*Estado:* {status_description}\n"
                f"*Confianza:* {trust_level}\n"
                f"*Conexión:* {rapport}\n"
                f"*Interacciones:* {interactions}\n\n"
            )
            
            # Add emotional insight if available
            if relationship["dominant_emotion"]:
                emotion_names = {
                    "joy": "alegría",
                    "sadness": "tristeza",
                    "anger": "enojo",
                    "fear": "miedo",
                    "surprise": "sorpresa",
                    "disgust": "disgusto",
                    "trust": "confianza",
                    "anticipation": "anticipación",
                    "neutral": "neutralidad"
                }
                
                emotion_name = emotion_names.get(
                    relationship["dominant_emotion"], 
                    relationship["dominant_emotion"]
                )
                
                message_text += f"Nuestra relación se caracteriza por la *{emotion_name}*.\n\n"
            
            # Add relationship history if milestones exist
            if relationship.get("milestone_count", 0) > 0:
                milestones = relationship.get("milestone_data", {}).get("status_changes", [])
                if milestones and len(milestones) > 1:  # Skip the initial milestone
                    message_text += "*Momentos importantes:*\n"
                    # Show the last 3 significant milestones (skip the first one which is initialization)
                    for milestone in milestones[1:4]:
                        new_status = status_descriptions.get(milestone["new_status"], milestone["new_status"])
                        message_text += f"• {new_status}\n"
            
            await safe_answer(message, message_text)
            
            # Record this interaction for future reference
            await diana_service.record_interaction(
                user_id=user_id, 
                interaction_length=len(message.text or "")
            )
            
            # Store this as an emotional memory
            await diana_service.store_emotional_memory(
                user_id=user_id,
                interaction_type=EmotionalInteractionType.HELP_REQUEST,
                summary="El usuario solicitó información sobre nuestra relación",
                content=f"El usuario utilizó el comando /relationship_status para ver el estado de nuestra relación",
                primary_emotion=EmotionCategory.TRUST,
                intensity=EmotionalIntensity.MODERATE,
                tags=["relationship", "status_check"]
            )
        else:
            await safe_answer(
                message, 
                "Lo siento, no pude obtener información sobre nuestra relación en este momento."
            )
    
    except Exception as e:
        await safe_answer(
            message, 
            "Ocurrió un error al procesar tu solicitud. Por favor, intenta nuevamente más tarde."
        )


@router.message(Command("recent_memories"))
async def handle_recent_memories(message: Message, session: AsyncSession):
    """Handler for viewing recent emotional memories with Diana."""
    try:
        user_id = message.from_user.id
        
        # Create service instance
        diana_service = DianaEmotionalService(session)
        
        # Get recent memories
        result = await diana_service.get_recent_memories(user_id, limit=5)
        
        if result["success"] and result["memories"]:
            memories = result["memories"]
            
            # Format memories for display
            message_text = "💭 *Recuerdos recientes* 💭\n\n"
            
            for memory in memories:
                # Get human-readable date
                date_str = memory["timestamp"].split("T")[0]
                
                # Get emotion in Spanish
                emotion_names = {
                    "joy": "alegría",
                    "sadness": "tristeza",
                    "anger": "enojo",
                    "fear": "miedo",
                    "surprise": "sorpresa",
                    "disgust": "disgusto",
                    "trust": "confianza",
                    "anticipation": "anticipación",
                    "neutral": "neutralidad"
                }
                
                emotion = emotion_names.get(memory["primary_emotion"], memory["primary_emotion"])
                
                # Add memory to message
                message_text += f"📅 *{date_str}*\n"
                message_text += f"_{memory['summary']}_\n"
                message_text += f"Sentí: {emotion}\n\n"
            
            await safe_answer(message, message_text)
            
            # Record this interaction
            await diana_service.record_interaction(
                user_id=user_id, 
                interaction_length=len(message.text or "")
            )
            
            # Store this as an emotional memory
            await diana_service.store_emotional_memory(
                user_id=user_id,
                interaction_type=EmotionalInteractionType.STORYTELLING,
                summary="El usuario solicitó ver recuerdos recientes",
                content=f"El usuario utilizó el comando /recent_memories para ver recuerdos recientes compartidos",
                primary_emotion=EmotionCategory.JOY,
                intensity=EmotionalIntensity.MODERATE,
                tags=["memories", "recall", "history"]
            )
        else:
            await safe_answer(
                message, 
                "Aún no tenemos recuerdos significativos juntos. ¡Hagamos más momentos memorables!"
            )
    
    except Exception as e:
        await safe_answer(
            message, 
            "Ocurrió un error al procesar tu solicitud. Por favor, intenta nuevamente más tarde."
        )


@router.message(Command("personality_preferences"))
async def handle_personality_preferences(message: Message, session: AsyncSession):
    """Handler for viewing and updating Diana's personality preferences."""
    try:
        user_id = message.from_user.id
        
        # Create service instance
        diana_service = DianaEmotionalService(session)
        
        # Get personality adaptation
        result = await diana_service.get_personality_adaptation(user_id)
        
        if result["success"]:
            adaptation = result["adaptation"]
            
            # Format personality info for display
            warmth = f"{adaptation['warmth'] * 100:.0f}%"
            formality = f"{adaptation['formality'] * 100:.0f}%"
            humor = f"{adaptation['humor'] * 100:.0f}%"
            expressiveness = f"{adaptation['emotional_expressiveness'] * 100:.0f}%"
            emoji_usage = f"{adaptation['emoji_usage'] * 100:.0f}%"
            
            message_text = (
                f"✨ *Cómo me adapto a ti* ✨\n\n"
                f"*Calidez:* {warmth}\n"
                f"*Formalidad:* {formality}\n"
                f"*Humor:* {humor}\n"
                f"*Expresividad:* {expressiveness}\n"
                f"*Uso de emojis:* {emoji_usage}\n\n"
                f"Mi comunicación se ajusta continuamente para brindarte la mejor experiencia."
            )
            
            await safe_answer(message, message_text)
            
            # Record this interaction
            await diana_service.record_interaction(
                user_id=user_id, 
                interaction_length=len(message.text or "")
            )
            
            # Store this as an emotional memory
            await diana_service.store_emotional_memory(
                user_id=user_id,
                interaction_type=EmotionalInteractionType.HELP_REQUEST,
                summary="El usuario solicitó ver preferencias de personalidad",
                content=f"El usuario utilizó el comando /personality_preferences para ver cómo me adapto a su estilo de comunicación",
                primary_emotion=EmotionCategory.TRUST,
                intensity=EmotionalIntensity.MODERATE,
                tags=["personality", "preferences", "adaptation"]
            )
        else:
            await safe_answer(
                message, 
                "Lo siento, no pude obtener información sobre mis adaptaciones a tu personalidad en este momento."
            )
    
    except Exception as e:
        await safe_answer(
            message, 
            "Ocurrió un error al procesar tu solicitud. Por favor, intenta nuevamente más tarde."
        )


@router.message()
async def handle_general_message(message: Message, session: AsyncSession):
    """Handler for processing general messages and updating emotional memory."""
    # This should be registered last as a catch-all handler
    
    # Only process text messages from users
    if not message.text or not message.from_user:
        return
    
    try:
        user_id = message.from_user.id
        text = message.text
        
        # Create service instance
        diana_service = DianaEmotionalService(session)
        
        # Record this interaction
        await diana_service.record_interaction(
            user_id=user_id, 
            interaction_length=len(text)
        )
        
        # Simple emotion detection - in a real implementation, this would use NLP
        # This is just a simple example using keyword matching
        emotion = EmotionCategory.NEUTRAL
        intensity = EmotionalIntensity.MODERATE
        
        # Very basic emotion detection based on keywords
        joy_words = ["feliz", "contento", "alegre", "genial", "excelente", "increíble", "gracias"]
        sad_words = ["triste", "deprimido", "mal", "horrible", "peor", "decepcionado"]
        angry_words = ["enojado", "molesto", "irritado", "frustrado", "odio", "detesto"]
        fear_words = ["miedo", "asustado", "preocupado", "ansioso", "nervioso", "terror"]
        trust_words = ["confío", "creo", "seguro", "fiable", "honesto", "verdad"]
        
        text_lower = text.lower()
        
        if any(word in text_lower for word in joy_words):
            emotion = EmotionCategory.JOY
        elif any(word in text_lower for word in sad_words):
            emotion = EmotionCategory.SADNESS
        elif any(word in text_lower for word in angry_words):
            emotion = EmotionCategory.ANGER
        elif any(word in text_lower for word in fear_words):
            emotion = EmotionCategory.FEAR
        elif any(word in text_lower for word in trust_words):
            emotion = EmotionCategory.TRUST
        
        # Determine intensity based on message length and punctuation
        if len(text) > 100:
            intensity = EmotionalIntensity.HIGH
        if text.count("!") > 2 or text.count("?") > 2:
            intensity = EmotionalIntensity.VERY_HIGH
        
        # Store as emotional memory if significant
        if emotion != EmotionCategory.NEUTRAL or len(text) > 50:
            # Determine interaction type based on message content
            interaction_type = EmotionalInteractionType.PERSONAL_SHARE
            
            if text.startswith(("¿", "?", "Cómo", "Qué", "Cuándo", "Dónde", "Por qué")):
                interaction_type = EmotionalInteractionType.HELP_REQUEST
            elif "gracias" in text_lower or "agradezco" in text_lower:
                interaction_type = EmotionalInteractionType.PRAISE
            
            # Create a summary (in a real implementation, use NLP for better summarization)
            summary = text[:50] + "..." if len(text) > 50 else text
            
            # Store the memory
            await diana_service.store_emotional_memory(
                user_id=user_id,
                interaction_type=interaction_type,
                summary=summary,
                content=text,
                primary_emotion=emotion,
                intensity=intensity,
                tags=["message", "conversation"]
            )
    
    except Exception as e:
        # Silent error handling for background processing
        pass
    
    # Continue to the next handler without responding here