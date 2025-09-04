"""
Manejadores para el sistema narrativo con integración completa.
"""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.coordinador_central import CoordinadorCentral, AccionUsuario
from keyboards.narrative_kb import get_decision_keyboard

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("start_story"))
async def start_story_command(message: Message, session: AsyncSession):
    """Inicia la historia para el usuario usando MVP narrative system"""
    try:
        from services.mvp_narrative_fragment_service import MVPNarrativeFragmentService
        
        user_id = message.from_user.id
        fragment_service = MVPNarrativeFragmentService(session)
        
        # Initialize fragments if needed
        await fragment_service.initialize_mvp_fragments()
        
        # Get starting fragment
        fragment = await fragment_service.get_user_current_fragment(user_id)
        
        if fragment:
            await message.answer(
                f"✨ **{fragment.title}**\n\n{fragment.content}",
                reply_markup=get_decision_keyboard(fragment),
                parse_mode="Markdown"
            )
        else:
            await message.answer("😔 Los hilos del destino se han enredado... Inténtalo de nuevo, querido.")
    except Exception as e:
        logger.error(f"Error starting story for user {message.from_user.id}: {e}")
        await message.answer("😔 Algo interrumpe nuestra conexión... Inténtalo de nuevo en un momento, querido.")

@router.callback_query(F.data.startswith("narrative_choice:"))
async def handle_narrative_choice(callback: CallbackQuery, session: AsyncSession):
    """
    Maneja una elección narrativa del usuario usando MVP decision tree service.
    """
    try:
        user_id = callback.from_user.id
        _, fragment_id, choice_index = callback.data.split(":")
        choice_index = int(choice_index)
        
        from services.mvp_decision_tree_service import MVPDecisionTreeService
        from services.narrative_gamification_integration import NarrativeGamificationIntegration
        
        decision_service = MVPDecisionTreeService(session)
        integration_service = NarrativeGamificationIntegration(session)
        
        # Process decision with full consequences
        result = await decision_service.process_decision_with_consequences(
            user_id=user_id,
            fragment_id=fragment_id,
            choice_index=choice_index
        )
        
        if result['success']:
            next_fragment = result['next_fragment']
            
            if next_fragment:
                # Process gamification integration
                gamification_result = await integration_service.process_narrative_fragment_completion(
                    user_id=user_id,
                    fragment_id=next_fragment.id,
                    bot=callback.bot
                )
                
                # Show next fragment with Diana's response
                response_text = f"✨ **{next_fragment.title}**\n\n{next_fragment.content}"
                if gamification_result.get('diana_response'):
                    response_text += f"\n\n{gamification_result['diana_response']}"
                
                await callback.message.edit_text(
                    response_text,
                    reply_markup=get_decision_keyboard(next_fragment),
                    parse_mode="Markdown"
                )
                await callback.answer()
            else:
                await callback.message.edit_text(
                    "🌟 Has completado este capítulo de nuestra historia... Más secretos te esperan, querido.",
                    parse_mode="Markdown"
                )
                await callback.answer()
        else:
            # Error or requirement not met
            error_message = result.get('diana_response', result.get('error', 'Error desconocido'))
            await callback.answer(error_message, show_alert=True)
            
    except Exception as e:
        logger.error(f"Error handling narrative choice for user {callback.from_user.id}: {e}")
        await callback.answer("😔 Los hilos del destino se han enredado... Inténtalo de nuevo, querido.", show_alert=True)

@router.message(Command("vip_content"))
async def access_vip_content(message: Message, session: AsyncSession):
    """
    Intenta acceder a contenido VIP de la narrativa.
    Verifica suscripción antes de permitir acceso.
    """
    user_id = message.from_user.id
    fragment_key = "level4_secreto"  # Ejemplo de fragmento VIP
    
    # Usar el coordinador central para el flujo completo
    coordinador = CoordinadorCentral(session)
    result = await coordinador.ejecutar_flujo(
        user_id,
        AccionUsuario.ACCEDER_NARRATIVA_VIP,
        fragment_key=fragment_key,
        bot=message.bot
    )
    
    if result["success"]:
        # Acceso permitido, mostrar fragmento
        fragment = result["fragment"]
        await message.answer(
            f"{result['message']}\n\n{fragment.content}",
            reply_markup=get_decision_keyboard(fragment)
        )
    else:
        # Acceso denegado, mostrar mensaje y opciones de suscripción
        await message.answer(
            result["message"],
            reply_markup=get_subscription_keyboard()  # Función que debe implementarse
        )

def get_subscription_keyboard():
    """
    Crea un teclado con opciones de suscripción VIP.
    """
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Suscripción Mensual (9.99€)", callback_data="subscribe:monthly")],
        [InlineKeyboardButton(text="💎💎 Suscripción Anual (89.99€)", callback_data="subscribe:yearly")],
        [InlineKeyboardButton(text="❓ Beneficios VIP", callback_data="vip_benefits")]
    ])
    
    return keyboard

@router.callback_query(F.data == "narrative_progress")
async def show_narrative_progress(callback: CallbackQuery, session: AsyncSession):
    """Show user's narrative progress."""
    try:
        from services.mvp_narrative_fragment_service import MVPNarrativeFragmentService
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        user_id = callback.from_user.id
        fragment_service = MVPNarrativeFragmentService(session)
        
        progress = await fragment_service.get_user_progress_summary(user_id)
        
        progress_text = f"""📊 **Tu Progreso en la Historia de Diana**

🌟 **Nivel Actual:** {progress['current_level']} 
👑 **Tier:** {progress['current_tier_name']}
📈 **Progreso:** {progress['progress_percentage']:.1f}%

📚 **Fragmentos Completados:** {progress['fragments_completed']}/{progress['total_mvp_fragments']}

🔮 **Pistas Desbloqueadas:** {len(progress.get('unlocked_clues', []))}

✨ *Cada paso te acerca más a los misterios más profundos...*"""

        await callback.message.edit_text(
            progress_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📖 Continuar Historia", callback_data="narrative_continue")],
                [InlineKeyboardButton(text="🔙 Atrás", callback_data="narrative_back")]
            ])
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing narrative progress for user {callback.from_user.id}: {e}")
        await callback.answer("😔 No puedo mostrar tu progreso ahora... Inténtalo más tarde, querido.", show_alert=True)

@router.callback_query(F.data == "narrative_continue")
async def continue_narrative(callback: CallbackQuery, session: AsyncSession):
    """Continue from current narrative fragment."""
    try:
        from services.mvp_narrative_fragment_service import MVPNarrativeFragmentService
        
        user_id = callback.from_user.id
        fragment_service = MVPNarrativeFragmentService(session)
        
        current_fragment = await fragment_service.get_user_current_fragment(user_id)
        
        if current_fragment:
            await callback.message.edit_text(
                f"✨ **{current_fragment.title}**\n\n{current_fragment.content}",
                reply_markup=get_decision_keyboard(current_fragment),
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(
                "🌟 Tu historia está esperando comenzar... Usa /start_story para comenzar tu viaje conmigo.",
                parse_mode="Markdown"
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error continuing narrative for user {callback.from_user.id}: {e}")
        await callback.answer("😔 Los hilos del destino se han enredado... Inténtalo de nuevo.", show_alert=True)
