from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from services.user_narrative_service import UserNarrativeService
from database.narrative_unified import NarrativeFragment
import json
import logging

logger = logging.getLogger(__name__)
router = Router()

# FSM States for user narrative progression
class UserNarrativeStates(StatesGroup):
    waiting_for_fragment_id = State()
    waiting_for_clue_code = State()


@router.message(F.text == "/start_narrative")
async def start_narrative(message: Message, session: AsyncSession):
    \"\"\"Inicia la experiencia narrativa para el usuario.\"\"\"
    user_id = message.from_user.id
    
    try:
        narrative_service = UserNarrativeService(session)
        
        # Obtener el primer fragmento de historia (por simplicidad, el primero que encontremos)
        stmt = select(NarrativeFragment).where(
            NarrativeFragment.fragment_type == 'STORY',
            NarrativeFragment.is_active == True
        ).order_by(NarrativeFragment.created_at)
        result = await session.execute(stmt)
        first_fragment = result.scalar_one_or_none()
        
        if not first_fragment:
            await message.answer("❌ No se encontraron fragmentos de historia disponibles.")
            return
        
        # Actualizar el estado del usuario
        await narrative_service.update_current_fragment(user_id, first_fragment.id)
        
        # Enviar el contenido del fragmento
        response = f"📖 {first_fragment.title}\\n\\n{first_fragment.content}"
        
        # Si es un punto de decisión, mostrar las opciones
        if first_fragment.is_decision and first_fragment.choices:
            response += "\\n\\n❓ Opciones:"
            for i, choice in enumerate(first_fragment.choices, 1):
                response += f"\\n{i}. {choice['text']}"
        
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Error starting narrative for user {user_id}: {e}")
        await message.answer("❌ Ocurrió un error al iniciar la narrativa.")


@router.message(F.text == "/narrative_progress")
async def show_progress(message: Message, session: AsyncSession):
    \"\"\"Muestra el progreso del usuario en la narrativa.\"\"\"
    user_id = message.from_user.id
    
    try:
        narrative_service = UserNarrativeService(session)
        progress = await narrative_service.get_user_progress_percentage(user_id)
        
        response = f"📊 Tu progreso en la narrativa: {progress:.1f}%"
        await message.answer(response)
        
    except Exception as e:
        logger.error(f"Error showing progress for user {user_id}: {e}")
        await message.answer("❌ Ocurrió un error al obtener tu progreso.")


@router.message(F.text == "/unlock_clue")
async def start_unlock_clue(message: Message, state: FSMContext):
    \"\"\"Inicia el proceso de desbloqueo de una pista.\"\"\"
    await message.answer("🗝️ Por favor, envíame el código de la pista que deseas desbloquear:")
    await state.set_state(UserNarrativeStates.waiting_for_clue_code)


@router.message(UserNarrativeStates.waiting_for_clue_code)
async def process_clue_code(message: Message, state: FSMContext, session: AsyncSession):
    \"\"\"Procesa el código de la pista y la desbloquea para el usuario.\"\"\"
    user_id = message.from_user.id
    clue_code = message.text.strip()
    
    try:
        narrative_service = UserNarrativeService(session)
        updated_state = await narrative_service.unlock_clue(user_id, clue_code)
        
        await message.answer(f"✅ Pista '{clue_code}' desbloqueada exitosamente!")
        await state.clear()
        
    except ValueError as e:
        await message.answer(f"❌ {str(e)}")
        await state.clear()
    except Exception as e:
        logger.error(f"Error unlocking clue {clue_code} for user {user_id}: {e}")
        await message.answer("❌ Ocurrió un error al desbloquear la pista.")
        await state.clear()


# Register the router
def register_user_narrative_handlers(dp):
    \"\"\"Register user narrative handlers with the dispatcher.\"\"\"
    dp.include_router(router)