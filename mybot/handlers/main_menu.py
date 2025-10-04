from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from handlers.lore_handlers import show_lore_backpack
from handlers.missions_handler import show_available_missions
from handlers.narrative_handler import start_narrative_command
from keyboards.main_menu_kb import get_main_menu_keyboard
from utils.localization import get_text
import logging

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text == "🏠 Inicio")
async def handle_home_button(message: Message, session: AsyncSession):
    """Abre el menú principal inline."""
    from utils.user_roles import get_user_role
    from utils.menu_manager import menu_manager
    from utils.menu_factory import menu_factory

    user_id = message.from_user.id
    role = await get_user_role(message.bot, user_id, session=session)

    try:
        # Crear el menú principal según el rol
        text, keyboard = await menu_factory.create_menu("main", user_id, session, message.bot)

        # Enviar el menú inline
        await menu_manager.send_menu(
            message,
            text,
            keyboard,
            session,
            "main"
        )
    except Exception as e:
        logger.error(f"Error showing main menu for user {user_id}: {e}", exc_info=True)
        await message.answer("❌ Error al cargar el menú principal. Intenta /start")

@router.message(F.text == "🎒 Mochila")
async def handle_backpack_button(message: Message, session: AsyncSession):
    # Directly call the lore handler function
    await show_lore_backpack(message, session)

@router.message(F.text == "💰 Billetera")
async def handle_wallet_button(message: Message, session: AsyncSession):
    await message.answer(get_text("main_menu_handler.wallet_in_development"))

@router.message(F.text == "🎯 Misiones")
async def handle_missions_button(message: Message, session: AsyncSession):
    # Create a mock callback to reuse the existing handler
    class MockCallback:
        def __init__(self, message):
            self.from_user = message.from_user
            self.data = "misiones_disponibles"
            self.message = message
            
        async def answer(self, *args, **kwargs):
            pass
    
    mock_callback = MockCallback(message)
    await show_available_missions(mock_callback, session)

@router.message(F.text == "⚙️ Configuración")
async def handle_config_button(message: Message, session: AsyncSession):
    await message.answer(get_text("main_menu_handler.config_in_development"))

@router.message(F.text == "❓ Ayuda")
async def handle_help_button(message: Message, session: AsyncSession):
    await message.answer(get_text("main_menu_handler.help_in_development"))

@router.message(F.text == "📖 Historia")
async def handle_narrative_button(message: Message, session: AsyncSession):
    """Continúa la narrativa desde donde se quedó el usuario o inicia si es nuevo."""
    from services.narrative_service import NarrativeService
    from services.coordinador_central import CoordinadorCentral, AccionUsuario
    from handlers.narrative_handler import _display_narrative_fragment
    import logging

    logger = logging.getLogger(__name__)
    user_id = message.from_user.id

    try:
        service = NarrativeService(session, message.bot)

        # Check if user has a shop redirect fragment to return to
        user_state = await service._get_or_create_user_state(user_id)
        logger.info(f"[HISTORIA_BUTTON_DEBUG] User {user_id} state: shop_redirect={user_state.shop_redirect_fragment_key}, pending_decision={user_state.pending_decision_id}, current_fragment={user_state.current_fragment_key}")

        # First, check if there's a pending decision to process (e.g., after shop purchase)
        if user_state.shop_redirect_fragment_key and user_state.pending_decision_id:
            logger.info(f"[HISTORIA_BUTTON_DEBUG] Processing pending decision {user_state.pending_decision_id}")
            coordinador = CoordinadorCentral(session)

            result = await coordinador.ejecutar_flujo(
                user_id,
                AccionUsuario.TOMAR_DECISION,
                decision_id=user_state.pending_decision_id
            )

            if result["success"] and result.get("fragment"):
                # Clear flags and show the unlocked fragment
                user_state.shop_redirect_fragment_key = None
                user_state.pending_decision_id = None
                await session.commit()
                logger.info(f"[HISTORIA_BUTTON_DEBUG] Showing unlocked fragment: {result['fragment'].key}")
                await _display_narrative_fragment(message, result["fragment"], session)
                return

        # Try to get current fragment (where user left off)
        current_fragment = await service.get_user_current_fragment(user_id)

        # Check if user can go back (has history)
        can_go_back = await service.can_go_back(user_id)
        logger.info(f"[HISTORIA_BUTTON_DEBUG] User {user_id} can_go_back: {can_go_back}, choices_made: {len(user_state.choices_made or [])}")

        if current_fragment:
            logger.info(f"[HISTORIA_BUTTON_DEBUG] Continuing from fragment: {current_fragment.key}")
            await _display_narrative_fragment(message, current_fragment, session)
        else:
            # New user - start narrative from beginning
            logger.info(f"[HISTORIA_BUTTON_DEBUG] Starting new narrative for user {user_id}")
            await start_narrative_command(message, session)

    except Exception as e:
        logger.error(f"Error in historia button for user {user_id}: {e}", exc_info=True)
        await message.answer(get_text("main_menu_handler.story_load_error"))

@router.message(F.text == "🔓 Nivel de Muestra")
async def handle_sample_level_button(message: Message, session: AsyncSession):
    """Handle access to the sample level that requires 'Diario de Diana'"""
    # Use CoordinadorCentral to check access
    from services.coordinador_central import CoordinadorCentral, AccionUsuario
    coordinador = CoordinadorCentral(session)
    result = await coordinador.ejecutar_flujo(
        message.from_user.id,
        AccionUsuario.VERIFICAR_ACCESO_NIVEL,
        level_name="nivel_muestra"
    )
    
    if result.get("access_granted"):
        await message.answer(get_text("main_menu_handler.sample_level_granted"))
        # Here you would start the actual narrative level
    else:
        reason = result.get('message', get_text("main_menu_handler.default_access_denied"))
        await message.answer(get_text("main_menu_handler.access_restricted", reason=reason))

@router.message(F.text == "📓 Diario Íntimo")
async def handle_diario_intimo_button(message: Message, session: AsyncSession):
    """Handle access to the 'Diario Íntimo' level that requires 'Diario de Diana'"""
    # Use CoordinadorCentral to check access
    from services.coordinador_central import CoordinadorCentral, AccionUsuario
    coordinador = CoordinadorCentral(session)
    result = await coordinador.ejecutar_flujo(
        message.from_user.id,
        AccionUsuario.VERIFICAR_ACCESO_NIVEL,
        level_name="diario_intimo"
    )

    if result.get("access_granted"):
        await message.answer(get_text("main_menu_handler.diary_level_granted"))
        # Here you would start the actual narrative level
    else:
        reason = result.get('message', get_text("main_menu_handler.default_access_denied"))
        await message.answer(get_text("main_menu_handler.access_restricted", reason=reason))

@router.callback_query(F.data == "narrative_main_menu")
async def return_to_main_menu(callback: CallbackQuery, session: AsyncSession):
    """Regresa al menú principal desde la narrativa o tienda, según el rol del usuario"""
    user_id = callback.from_user.id

    try:
        # Use menu factory to create appropriate menu based on user role
        from utils.menu_factory import MenuFactory

        menu_factory = MenuFactory()
        text, keyboard = await menu_factory.create_menu("main", user_id, session, callback.bot)

        # Edit the message directly since this is a callback
        await callback.message.edit_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error returning to main menu for user {user_id}: {e}", exc_info=True)
        # Fallback to simple menu
        await callback.message.edit_text(
            f"{get_text('main_menu_handler.main_menu_fallback_title')}\n\n{get_text('main_menu_handler.main_menu_fallback_prompt')}",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()

@router.callback_query(F.data == "menu_principal")
async def return_to_main_menu_alt(callback: CallbackQuery, session: AsyncSession):
    """Handler alternativo para 'menu_principal' (usado en algunos lugares)"""
    await return_to_main_menu(callback, session)
