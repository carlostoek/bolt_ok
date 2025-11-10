"""
Handler para el nuevo botón de historia completamente independiente.
Evita conflictos con el sistema existente.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "narrative_continue_new")
async def handle_new_narrative_button(callback: CallbackQuery, session: AsyncSession):
    """
    Handler completamente nuevo para el botón de historia.
    Simple y directo, sin dependencias complejas.
    """
    user_id = callback.from_user.id
    
    try:
        logger.info(f"[NEW_BUTTON_DEBUG] Nuevo botón presionado por usuario {user_id}")
        
        # Respuesta inmediata
        await callback.answer("📖 Cargando tu historia...")
        
        # Lógica simple y directa
        from services.narrative_service import NarrativeService
        service = NarrativeService(session, callback.bot)
        
        # Obtener fragmento actual del usuario
        current_fragment = await service.get_user_current_fragment(user_id)
        
        if current_fragment:
            logger.info(f"[NEW_BUTTON_DEBUG] Usuario {user_id} continúa desde: {current_fragment.key}")
            
            # Mostrar fragmento usando función simple
            await _display_simple_fragment(callback, current_fragment, session)
        else:
            # Usuario nuevo - iniciar desde welcome
            logger.info(f"[NEW_BUTTON_DEBUG] Usuario {user_id} es nuevo, iniciando desde welcome")
            welcome_fragment = await service._get_fragment_by_key("welcome")
            if welcome_fragment:
                await _display_simple_fragment(callback, welcome_fragment, session)
            else:
                await callback.message.edit_text(
                    "❌ No se pudo iniciar la historia. Intenta más tarde."
                )
        
    except Exception as e:
        logger.error(f"Error en nuevo botón de historia para usuario {user_id}: {e}", exc_info=True)
        await callback.answer("❌ Error al cargar la historia", show_alert=True)

async def _display_simple_fragment(callback: CallbackQuery, fragment, session: AsyncSession):
    """
    Función simple para mostrar fragmentos sin complejidades.
    """
    try:
        from keyboards.narrative_kb import get_narrative_keyboard
        
        # Texto simple del fragmento
        character_emoji = "🎩" if fragment.character == "Lucien" else "🌸"
        fragment_text = f"{character_emoji} **{fragment.character}**:\n\n{fragment.text}"
        
        # Teclado simple
        keyboard = await get_narrative_keyboard(fragment, session, user_id=callback.from_user.id)
        
        # Mostrar fragmento
        await callback.message.edit_text(
            fragment_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error mostrando fragmento simple: {e}")
        await callback.message.edit_text(
            "❌ Error al mostrar el fragmento. Intenta nuevamente."
        )