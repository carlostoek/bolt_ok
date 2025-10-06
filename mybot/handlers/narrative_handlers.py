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
    """Inicia la historia para el usuario"""
    from modules.narrative.story_engine import NarrativeEngine
    engine = NarrativeEngine(session)
    fragment = await engine.start_story(message.from_user.id)
    
    await message.answer(
        fragment.content,
        reply_markup=get_decision_keyboard(fragment)
    )

@router.callback_query(F.data.startswith("narrative_choice:"))
async def handle_narrative_choice(callback: CallbackQuery, session: AsyncSession):
    """
    Maneja una elección narrativa del usuario con integración completa.
    Verifica requisitos de puntos y procesa la decisión.
    """
    user_id = callback.from_user.id
    _, fragment_id, choice_index = callback.data.split(":")
    choice_index = int(choice_index)
    
    # Obtener el ID de decisión basado en el fragmento y la elección
    from modules.narrative.story_engine import NarrativeEngine
    engine = NarrativeEngine(session)
    fragment = await engine.get_fragment(fragment_id)
    if not fragment or choice_index >= len(fragment.decisions):
        await callback.answer("Opción no válida", show_alert=True)
        return
    
    decision_id = fragment.decisions[choice_index].id
    
    # Usar el coordinador central para el flujo completo
    coordinador = CoordinadorCentral(session)
    result = await coordinador.ejecutar_flujo(
        user_id,
        AccionUsuario.TOMAR_DECISION,
        decision_id=decision_id,
        bot=callback.bot
    )
    
    if result["success"]:
        # Decisión exitosa, mostrar nuevo fragmento
        next_fragment = result["fragment"]
        await callback.message.edit_text(
            next_fragment.content,
            reply_markup=get_decision_keyboard(next_fragment)
        )
        await callback.answer()
    else:
        # Error o requisito no cumplido
        await callback.answer(result["message"], show_alert=True)
        
        # Si es un error de puntos, ofrecer opciones para conseguir más
        if result.get("action") == "points_required":
            await callback.bot.send_message(
                user_id,
                "Para conseguir más besitos, puedes:\n"
                "• Participar en los canales oficiales\n"
                "• Reaccionar a publicaciones\n"
                "• Completar misiones diarias con /misiones"
            )

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
