"""
Diana Test Handler - Simple handler to demonstrate Diana's emotional capabilities.

This handler provides a command to test Diana's emotional intelligence integration
without affecting the existing functionality.
"""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from services.coordinador_central import CoordinadorCentral, AccionUsuario
from utils.message_safety import safe_answer

logger = logging.getLogger(__name__)

# Initialize router
router = Router()

@router.message(Command("diana_test"))
async def diana_test_command(message: Message, session: AsyncSession):
    """
    Test command to demonstrate Diana's emotional intelligence capabilities.
    Simulates a reaction to a publication to show personalization.
    
    Usage: /diana_test
    """
    try:
        user_id = message.from_user.id
        
        # Create mock data for a simulated reaction
        mock_message_id = 12345
        mock_channel_id = -1001234567890
        mock_reaction = "❤️"
        
        # Create coordinator and execute flow
        coordinator = CoordinadorCentral(session)
        result = await coordinator.ejecutar_flujo(
            user_id, 
            AccionUsuario.REACCIONAR_PUBLICACION,
            message_id=mock_message_id,
            channel_id=mock_channel_id,
            reaction_type=mock_reaction
        )
        
        # Add a description to help the user understand what happened
        response_message = (
            f"{result.get('message', 'No message returned')}\n\n"
            f"_Prueba de Diana: {result.get('diana_active', False) or result.get('diana_observing', False)}_\n"
            f"_Besitos otorgados: {result.get('points_awarded', 0)}_"
        )
        
        # If there was an emotional moment, display it
        if result.get("emotional_moment"):
            response_message += f"\n\n*Momento emocional especial:*\n_{result['emotional_moment']['message']}_"
        
        await safe_answer(message, response_message)
        
    except Exception as e:
        logger.error(f"Error in diana_test_command: {e}")
        await safe_answer(message, "No pude completar la prueba de Diana. Por favor, inténtalo de nuevo más tarde.")

@router.message(Command("diana_daily"))
async def diana_daily_test(message: Message, session: AsyncSession):
    """
    Test command to simulate a daily check-in with Diana's personalization.
    
    Usage: /diana_daily
    """
    try:
        user_id = message.from_user.id
        
        # Create coordinator and execute flow
        coordinator = CoordinadorCentral(session)
        result = await coordinator.ejecutar_flujo(
            user_id, 
            AccionUsuario.VERIFICAR_ENGAGEMENT
        )
        
        # Add a description to help the user understand what happened
        response_message = (
            f"{result.get('message', 'No message returned')}\n\n"
            f"_Prueba de Diana: {result.get('diana_active', False) or result.get('diana_observing', False)}_\n"
            f"_Racha actual: {result.get('streak', 0)} días_"
        )
        
        # If there was an emotional moment, display it
        if result.get("emotional_moment"):
            response_message += f"\n\n*Momento emocional especial:*\n_{result['emotional_moment']['message']}_"
        
        await safe_answer(message, response_message)
        
    except Exception as e:
        logger.error(f"Error in diana_daily_test: {e}")
        await safe_answer(message, "No pude completar la prueba de Diana. Por favor, inténtalo de nuevo más tarde.")

@router.message(F.text.contains("Diana") | F.text.contains("diana"))
async def diana_message_handler(message: Message, session: AsyncSession):
    """
    Simple handler that responds to messages mentioning Diana.
    In Phase 2, this will be expanded to handle free-text emotional conversations.
    
    This is a placeholder for now, showing how Diana will eventually analyze
    and respond to emotional content directly.
    """
    try:
        # For Phase 1, just acknowledge the message
        await safe_answer(
            message, 
            "Diana nota que has mencionado su nombre. En futuras actualizaciones, "
            "ella podrá responder directamente a tus mensajes emocionales y formar "
            "una relación más profunda contigo."
        )
        
    except Exception as e:
        logger.error(f"Error in diana_message_handler: {e}")
        await safe_answer(message, "Diana no pudo procesar tu mensaje. Por favor, inténtalo de nuevo más tarde.")