"""
Handlers para el sistema de narrativa inmersiva.
Maneja comandos de historia, decisiones y progreso narrativo.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.narrative_service import NarrativeService, RequirementsInfo
from services.narrative_loader import NarrativeLoader
from keyboards.narrative_kb import get_narrative_keyboard, get_narrative_stats_keyboard
from utils.message_safety import safe_answer, safe_edit
from utils.user_roles import get_user_role
from utils.localization import get_text
import logging
from aiogram import Bot

logger = logging.getLogger(__name__)
router = Router(name="narrative_handler")

@router.message(Command("historia"))
async def start_narrative_command(message: Message, session: AsyncSession):
    """Continúa la narrativa desde el último punto guardado del usuario."""
    user_id = message.from_user.id

    try:
        service = NarrativeService(session, message.bot)

        # Obtener fragmento actual del usuario (esto debería recordar el progreso)
        current_fragment = await service.get_user_current_fragment(user_id)
        
        if current_fragment:
            # El usuario ya tiene progreso - continuar desde ahí
            logger.info(f"Usuario {user_id} continúa narrativa desde fragmento: {current_fragment.key}")
            await _display_narrative_fragment(message, current_fragment, session)
        else:
            # Usuario nuevo - iniciar narrativa desde el principio
            logger.info(f"Usuario {user_id} inicia narrativa por primera vez")
            current_fragment = await service.start_narrative(user_id)
            
            if current_fragment:
                await _display_narrative_fragment(message, current_fragment, session)
            else:
                await safe_answer(
                    message,
                    "❌ No se pudo iniciar la narrativa. Por favor, intenta más tarde."
                )

    except Exception as e:
        logger.error(f"Error en comando historia para usuario {user_id}: {e}")
        await safe_answer(
            message,
            "❌ Error al cargar tu historia. Por favor, intenta nuevamente."
        )

@router.callback_query(F.data.startswith("narrative_choice:"))
async def handle_narrative_choice(callback: CallbackQuery, session: AsyncSession):
    """Maneja las decisiones narrativas del usuario."""
    user_id = callback.from_user.id

    try:
        # Immediate feedback to user with emotional response (UX improvement)
        await callback.answer("🌸 Diana siente tu elección...")
        
        # Show visual processing feedback with Diana's voice
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        processing_builder = InlineKeyboardBuilder()
        processing_builder.button(text="⏳ Pensando en tu decisión...", callback_data="noop")
        
        # Get current fragment to show character context
        service = NarrativeService(session, callback.bot)
        current_fragment = await service.get_user_current_fragment(user_id)
        
        character_emoji = "🎩" if current_fragment and current_fragment.character == "Lucien" else "🌸"
        processing_text = f"{character_emoji} *{current_fragment.character if current_fragment else 'Diana'}*:\n\n"
        processing_text += "Siento tu elección... déjame ver qué nos depara el destino..."
        
        # Update message with processing feedback
        try:
            await callback.message.edit_text(
                processing_text,
                reply_markup=processing_builder.as_markup(),
                parse_mode="MarkdownV2"
            )
        except Exception:
            # If message edit fails, continue with the flow
            pass

        # Extraer índice de la decisión
        choice_data = callback.data.split(":")
        if len(choice_data) < 2:
            await callback.answer(get_text("narrative.handler.invalid_decision"), show_alert=True)
            return

        choice_index = int(choice_data[1])

        # Get current fragment and choices to check for special decisions
        if current_fragment:
            choices = await service._get_fragment_choices(current_fragment.id)
            if 0 <= choice_index < len(choices):
                selected_choice = choices[choice_index]

                # Check if this is the "Go to shop" special action from teaser
                if "🛒" in selected_choice.text and ("tienda" in selected_choice.text.lower() or "shop" in selected_choice.text.lower()):
                    logger.info(f"User {user_id} selecting 'Go to Shop' from narrative teaser")
                    # Use State Machine for atomic shop transition
                    from services.narrative_state_machine import NarrativeStateMachine
                    state_machine = NarrativeStateMachine(session)
                    success = await state_machine.transition_to_shop(
                        user_id=user_id,
                        current_fragment_key=current_fragment.key
                    )
                    if success:
                        logger.info(f"[STATE_MACHINE] User {user_id} transitioned to SHOPPING from {current_fragment.key}")
                    else:
                        logger.warning(f"[STATE_MACHINE] Failed to transition user {user_id} to shop")
                    
                    # Show shop directly instead of going to next fragment
                    from handlers.shop_handlers import show_shop

                    # Create a mock callback for shop handler
                    class MockCallback:
                        def __init__(self, original_callback):
                            self.from_user = original_callback.from_user
                            self.message = original_callback.message
                            self.bot = original_callback.bot
                            self._callback = original_callback

                        async def answer(self, *args, **kwargs):
                            await self._callback.answer(*args, **kwargs)

                    mock_callback = MockCallback(callback)
                    await show_shop(mock_callback, session)
                    return

                # Check if this is a special decision that requires item verification
                if "diario íntimo" in selected_choice.text.lower():
                    # Use CoordinadorCentral for special item verification
                    from services.coordinador_central import CoordinadorCentral, AccionUsuario
                    coordinador = CoordinadorCentral(session)

                    # Log for debugging
                    logger.info(f"[DECISION_DEBUG] Processing diary decision for user {user_id}, choice ID: {selected_choice.id}, current_fragment: {current_fragment.key}")

                    result = await coordinador.ejecutar_flujo(
                        user_id,
                        AccionUsuario.TOMAR_DECISION,
                        decision_id=selected_choice.id
                    )

                    logger.info(f"[DECISION_DEBUG] Coordinator result: success={result['success']}, has_fragment={result.get('fragment') is not None}")
                    if result.get("fragment"):
                        logger.info(f"[DECISION_DEBUG] Fragment returned: key={result['fragment'].key}")

                    if result["success"]:
                        next_fragment = result.get("fragment")
                    else:
                        logger.warning(f"[DECISION_DEBUG] Decision failed: {result.get('message')}")
                        await callback.answer(result.get("message", get_text("narrative.handler.cannot_make_decision")), show_alert=True)
                        return
                else:
                    # Process normal decision using the actual decision ID, not the choice index
                    logger.info(f"[DECISION_DEBUG] Processing normal decision for user {user_id}, choice ID: {selected_choice.id}")
                    next_fragment = await service.process_user_decision_by_id(user_id, selected_choice.id)
                    if next_fragment:
                        logger.info(f"[DECISION_DEBUG] Normal decision returned fragment: {next_fragment.key}")
                    else:
                        logger.warning(f"[DECISION_DEBUG] Normal decision returned None")
            else:
                next_fragment = None
        else:
            next_fragment = None

        if not next_fragment:
            # Get detailed requirements info
            # We need to get selected_choice again for requirements check
            if current_fragment and 0 <= choice_index < len(choices):
                selected_choice = choices[choice_index]
                can_proceed, requirements_info = await service.check_decision_requirements_info(user_id, selected_choice.id)
                
                # Build detailed message with requirements
                await _show_requirements_message(callback, requirements_info, session)
            return

        # Mostrar siguiente fragmento con feedback emocional
        await callback.answer("✨ Tu decisión ha sido escuchada...")
        await _display_narrative_fragment(callback.message, next_fragment, session, is_callback=True)

        # ========================================
        # MEJORA #3: TRIGGER DE SESIÓN INDIVIDUAL
        # ========================================
        # Evaluar si es momento de ofrecer sesión individual después de fragmento emocional
        try:
            from services.session_trigger_service import SessionTriggerService
            trigger_service = SessionTriggerService(session)
            await trigger_service.trigger_on_narrative_completion(
                user_id=user_id,
                fragment_key=next_fragment.key,
                bot=callback.bot
            )
        except Exception as trigger_error:
            # No bloquear flujo principal si falla el trigger
            logger.error(f"Error in session trigger: {trigger_error}")

    except ValueError:
        await callback.answer(get_text("narrative.handler.invalid_decision"), show_alert=True)
    except Exception as e:
        logger.error(f"Error procesando decisión narrativa para usuario {user_id}: {e}")
        await callback.answer(get_text("narrative.handler.processing_decision_error"), show_alert=True)

@router.callback_query(F.data.startswith("enhanced_l1f1_choice:"))
async def handle_enhanced_l1f1_choice(callback: CallbackQuery, session: AsyncSession):
    """Maneja las decisiones del fragmento enhanced L1F1 con captura de timing."""
    user_id = callback.from_user.id

    try:
        # Immediate emotional feedback to user (UX improvement)
        await callback.answer("🌸 Diana siente tu elección...")
        
        # Show visual processing feedback with Diana's voice
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        processing_builder = InlineKeyboardBuilder()
        processing_builder.button(text="⏳ Analizando tu elección...", callback_data="noop")
        
        processing_text = f"🌸 **Diana**:\n\n"
        processing_text += "¡Qué interesante elección! Cada decisión me dice más de ti...\n\n"
        processing_text += "*Diana sonríe con curiosidad...*"
        
        # Update message with processing feedback
        try:
            await callback.message.edit_text(
                processing_text,
                reply_markup=processing_builder.as_markup(),
                parse_mode="MarkdownV2"
            )
        except Exception:
            # If message edit fails, continue with the flow
            pass

        # Extraer índice de la elección
        choice_data = callback.data.split(":")
        if len(choice_data) < 2:
            await callback.answer(get_text("narrative.handler.invalid_decision"), show_alert=True)
            return

        choice_index = int(choice_data[1])

        # Capturar tiempo de respuesta
        response_time = await _capture_response_timing(user_id, callback.message.date)

        # Cargar datos del enhanced L1F1 para obtener la elección
        enhanced_fragment = await _try_load_enhanced_l1f1(session)
        if not enhanced_fragment:
            await callback.answer(get_text("narrative.handler.processing_choice_error"), show_alert=True)
            return

        choices = enhanced_fragment.get('choices', [])
        if not (0 <= choice_index < len(choices)):
            await callback.answer(get_text("narrative.handler.invalid_choice"), show_alert=True)
            return

        selected_choice = choices[choice_index]

        # Almacenar elección con timing para análisis posterior
        await _store_enhanced_l1f1_choice(user_id, choice_index, selected_choice, response_time, session)

        # Verificar si necesitamos activar análisis de arquetipo
        choices_made = await _get_user_l1f1_choices(user_id, session)

        if len(choices_made) >= 3:  # Suficientes datos para análisis
            await _trigger_archetype_analysis(user_id, choices_made, session)

        # Continuar a siguiente fragmento según la elección
        await _process_enhanced_l1f1_followup(callback, choice_index, enhanced_fragment, session)

        await callback.answer("✨ Tu elección ha sido registrada... Diana sonríe")

    except ValueError:
        await callback.answer(get_text("narrative.handler.invalid_decision"), show_alert=True)
    except Exception as e:
        logger.error(f"Error procesando elección enhanced L1F1 para usuario {user_id}: {e}")
        await callback.answer(get_text("narrative.handler.processing_choice_error"), show_alert=True)

@router.callback_query(F.data == "narrative_auto_continue")
async def handle_auto_continue(callback: CallbackQuery, session: AsyncSession):
    """Maneja la continuación automática de fragmentos sin decisiones."""
    user_id = callback.from_user.id

    try:
        # Immediate feedback to user (UX improvement)
        await callback.answer("➡️ Continuando...")

        service = NarrativeService(session, callback.bot)
        current_fragment = await service.get_user_current_fragment(user_id)
        
        if current_fragment and current_fragment.auto_next_fragment_key:
            # Simular una decisión automática
            next_fragment = await service._get_fragment_by_key(current_fragment.auto_next_fragment_key)
            if next_fragment:
                # Actualizar estado del usuario
                user_state = await service._get_or_create_user_state(user_id)
                user_state.current_fragment_key = next_fragment.key
                user_state.fragments_visited += 1
                await service._process_fragment_rewards(user_id, next_fragment)
                await session.commit()
                
                await _display_narrative_fragment(callback.message, next_fragment, session, is_callback=True)
            else:
                await callback.answer(get_text("narrative.handler.auto_continue_error"), show_alert=True)
        else:
            await callback.answer(get_text("narrative.handler.no_auto_continue"), show_alert=True)
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error en continuación automática para usuario {user_id}: {e}")
        await callback.answer(get_text("narrative.handler.continue_error"), show_alert=True)

@router.message(Command("mi_historia"))
async def show_narrative_stats(message: Message, session: AsyncSession):
    """Muestra estadísticas y progreso narrativo del usuario."""
    user_id = message.from_user.id
    
    try:
        service = NarrativeService(session, message.bot)
        stats = await service.get_user_narrative_stats(user_id)
        
        # Crear mensaje de estadísticas
        if stats["current_fragment"]:
            stats_text = (
                f"{get_text('narrative.stats.title')}\n\n"
                f"{get_text('narrative.stats.current_fragment', fragment=stats['current_fragment'])}\n"
                f"{get_text('narrative.stats.progress', progress_percentage=stats['progress_percentage'])}\n"
                f"{get_text('narrative.stats.fragments_visited', visited=stats['fragments_visited'])}\n"
                f"{get_text('narrative.stats.total_accessible', total=stats['total_accessible'])}\n\n"
                f"{get_text('narrative.stats.choices_made', count=len(stats['choices_made']))}"
            )

            if stats['choices_made']:
                stats_text += get_text('narrative.stats.last_choices_header')
                for choice in stats['choices_made'][-3:]:  # Últimas 3 decisiones
                    stats_text += get_text(
                        'narrative.stats.last_choice_item',
                        choice_text=choice.get('choice_text', get_text('narrative.stats.unknown_decision'))
                    )
        else:
            stats_text = (
                f"{get_text('narrative.stats.title')}\n\n"
                f"{get_text('narrative.stats.not_started_status')}\n"
                f"{get_text('narrative.stats.not_started_suggestion')}\n\n"
                f"{get_text('narrative.stats.not_started_footer')}"
            )
        
        await safe_answer(
            message,
            stats_text,
            reply_markup=get_narrative_stats_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error mostrando estadísticas narrativas para usuario {user_id}: {e}")
        await safe_answer(
            message,
            get_text("narrative.handler.stats_load_error")
        )

@router.callback_query(F.data == "continue_narrative")
async def continue_narrative(callback: CallbackQuery, session: AsyncSession):
    """Continúa la narrativa desde donde se quedó el usuario."""
    user_id = callback.from_user.id

    try:
        # Immediate feedback to user (UX improvement)
        await callback.answer("📖 Cargando historia...")

        service = NarrativeService(session, callback.bot)
        current_fragment = await service.get_user_current_fragment(user_id)

        if current_fragment:
            await _display_narrative_fragment(callback.message, current_fragment, session, is_callback=True)
        else:
            await callback.message.edit_text(
                get_text("narrative.handler.story_not_found"),
                reply_markup=get_narrative_stats_keyboard()
            )

        await callback.answer()

    except Exception as e:
        logger.error(f"Error continuando narrativa para usuario {user_id}: {e}")
        await callback.answer(get_text("narrative.handler.load_story_error"), show_alert=True)

@router.callback_query(F.data == "return_from_shop")
async def return_from_shop(callback: CallbackQuery, session: AsyncSession):
    """Regresa de la tienda y procesa cualquier decisión pendiente."""
    user_id = callback.from_user.id

    try:
        from services.narrative_state_machine import NarrativeStateMachine
        service = NarrativeService(session, callback.bot)
        state_machine = NarrativeStateMachine(session)

        # Use State Machine to handle shop return
        return_result = await state_machine.return_from_shop(user_id)

        if return_result["success"]:
            return_fragment_key = return_result.get("return_fragment_key")
            pending_decision_id = return_result.get("pending_decision_id")

            logger.info(f"[STATE_MACHINE] User {user_id} returned from shop - fragment: {return_fragment_key}, pending_decision: {pending_decision_id}")

            # Check if there's a pending decision to process
            if pending_decision_id:
                logger.info(f"[SHOP_RETURN_DEBUG] Processing pending decision {pending_decision_id} for user {user_id} after shop return")
                # Process the pending decision
                from services.coordinador_central import CoordinadorCentral, AccionUsuario
                coordinador = CoordinadorCentral(session)

                try:
                    result = await coordinador.ejecutar_flujo(
                        user_id,
                        AccionUsuario.TOMAR_DECISION,
                        decision_id=pending_decision_id
                    )

                    logger.info(f"[SHOP_RETURN_DEBUG] Coordinator result: success={result['success']}, has_fragment={result.get('fragment') is not None}")
                    if result.get("fragment"):
                        logger.info(f"[SHOP_RETURN_DEBUG] Fragment returned: key={result['fragment'].key}")

                    if result["success"]:
                        # CRITICAL FIX: Clear shop context ONLY after successful decision processing
                        logger.info(f"[SHOP_RETURN_DEBUG] Decision processed successfully, clearing shop context")
                        await state_machine.clear_shop_context(user_id)

                        # Show the next fragment
                        next_fragment = result.get("fragment")
                        if next_fragment:
                            logger.info(f"[SHOP_RETURN_DEBUG] Showing next fragment {next_fragment.key} to user {user_id}")
                            await _display_narrative_fragment(callback.message, next_fragment, session, is_callback=True)
                            await callback.answer(get_text("narrative.handler.continuing_story"))
                            return
                        else:
                            logger.warning(f"[SHOP_RETURN_DEBUG] No fragment returned from pending decision processing for user {user_id}")
                    else:
                        # Decision failed - context preserved for retry
                        logger.warning(f"[SHOP_RETURN_DEBUG] Pending decision still failed for user {user_id}: {result.get('message')} - preserving shop context")
                except Exception as e:
                    # Error during decision processing - context preserved for retry
                    logger.error(f"[SHOP_RETURN_DEBUG] Error processing pending decision for user {user_id}: {e} - preserving shop context", exc_info=True)

            # Return to the fragment where user was redirected to shop
            if return_fragment_key:
                logger.info(f"[SHOP_RETURN_DEBUG] Returning to fragment {return_fragment_key} for user {user_id}")
                return_fragment = await service._get_fragment_by_key(return_fragment_key)
                if return_fragment:
                    logger.info(f"[SHOP_RETURN_DEBUG] Found return fragment: key={return_fragment.key}")
                    # Update current fragment
                    user_state = await service._get_or_create_user_state(user_id)
                    user_state.current_fragment_key = return_fragment_key
                    await session.commit()
                    logger.info(f"[SHOP_RETURN_DEBUG] Set current_fragment to {user_state.current_fragment_key} for user {user_id}")

                    await _display_narrative_fragment(callback.message, return_fragment, session, is_callback=True)
                    await callback.answer(get_text("narrative.handler.return_to_story"))
                    return
        else:
            logger.warning(f"[STATE_MACHINE] User {user_id} not in shop state: {return_result.get('error')}")

        # No shop redirect, just continue normally
        current_fragment = await service.get_user_current_fragment(user_id)
        if current_fragment:
            await _display_narrative_fragment(callback.message, current_fragment, session, is_callback=True)
            await callback.answer()
        else:
            await callback.message.edit_text(
                get_text("narrative.handler.story_not_found"),
                reply_markup=get_narrative_stats_keyboard()
            )
            await callback.answer()

    except Exception as e:
        logger.error(f"Error returning from shop for user {user_id}: {e}", exc_info=True)
        await callback.answer(get_text("narrative.handler.return_to_story_error"), show_alert=True)

@router.callback_query(F.data == "narrative_go_back")
async def go_back_narrative(callback: CallbackQuery, session: AsyncSession):
    """Navega al fragmento anterior en la historia."""
    user_id = callback.from_user.id

    try:
        service = NarrativeService(session, callback.bot)
        previous_fragment = await service.go_back_to_previous_fragment(user_id)

        if previous_fragment:
            await _display_narrative_fragment(callback.message, previous_fragment, session, is_callback=True)
            await callback.answer(get_text("narrative.handler.returned_to_previous_fragment"))
        else:
            await callback.answer(
                get_text("narrative.handler.cannot_go_back"),
                show_alert=True
            )

    except Exception as e:
        logger.error(f"Error retrocediendo en narrativa para usuario {user_id}: {e}")
        await callback.answer(get_text("narrative.handler.go_back_error"), show_alert=True)

@router.callback_query(F.data == "narrative_help")
async def show_narrative_help(callback: CallbackQuery, session: AsyncSession):
    """Muestra ayuda sobre el sistema narrativo."""
    help_text = (
        f"{get_text('narrative.help.title')}\n\n"
        f"{get_text('narrative.help.how_it_works_title')}\n"
        f"{get_text('narrative.help.line_1')}\n"
        f"{get_text('narrative.help.line_2')}\n"
        f"{get_text('narrative.help.line_3')}\n\n"
        f"{get_text('narrative.help.characters_title')}\n"
        f"{get_text('narrative.help.char_1')}\n"
        f"{get_text('narrative.help.char_2')}\n\n"
        f"{get_text('narrative.help.commands_title')}\n"
        f"{get_text('narrative.help.cmd_1')}\n"
        f"{get_text('narrative.help.cmd_2')}\n\n"
        f"{get_text('narrative.help.navigation_title')}\n"
        f"{get_text('narrative.help.nav_1')}\n"
        f"{get_text('narrative.help.nav_2')}\n\n"
        f"{get_text('narrative.help.tip_title')}"
    )

    await callback.message.edit_text(
        help_text,
        reply_markup=get_narrative_stats_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "narrative_stats")
async def show_narrative_stats_callback(callback: CallbackQuery, session: AsyncSession):
    """Muestra estadísticas desde callback."""
    user_id = callback.from_user.id
    
    try:
        service = NarrativeService(session, callback.bot)
        stats = await service.get_user_narrative_stats(user_id)
        
        if stats["current_fragment"]:
            stats_text = (
                f"{get_text('narrative.stats.title')}\n\n"
                f"{get_text('narrative.stats.current_fragment', fragment=stats['current_fragment'])}\n"
                f"{get_text('narrative.stats.progress', progress_percentage=stats['progress_percentage'])}\n"
                f"{get_text('narrative.stats.fragments_visited', visited=stats['fragments_visited'])}\n"
                f"{get_text('narrative.stats.total_accessible', total=stats['total_accessible'])}"
            )
        else:
            stats_text = (
                f"{get_text('narrative.stats.title')}\n\n"
                f"{get_text('narrative.stats.not_started_status')}\n"
                f"{get_text('narrative.stats.not_started_suggestion_callback')}"
            )
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=get_narrative_stats_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error mostrando estadísticas narrativas para usuario {user_id}: {e}")
        await callback.answer(get_text("narrative.handler.stats_callback_error"), show_alert=True)

async def _display_narrative_fragment(
    message: Message,
    fragment,
    session: AsyncSession,
    is_callback: bool = False
):
    """Muestra un fragmento narrativo con sus opciones."""
    # Obtener user_id
    user_id = message.from_user.id if hasattr(message, 'from_user') else (message.chat.id if hasattr(message, 'chat') else None)

    # Obtener estadísticas de progreso
    progress_info = ""
    if user_id:
        try:
            service = NarrativeService(session)
            stats = await service.get_user_narrative_stats(user_id)
            fragments_visited = stats.get('fragments_visited', 0)
            total_accessible = stats.get('total_accessible', 0)
            progress_pct = stats.get('progress_percentage', 0)

            # Crear indicador visual de progreso
            progress_info = get_text(
                "narrative.display.fragment_progress",
                visited=fragments_visited,
                total=total_accessible,
                level=fragment.level,
                progress_pct=progress_pct
            )
        except Exception as e:
            logger.warning(f"No se pudo obtener progreso para usuario {user_id}: {e}")

    # Formatear el texto del fragmento
    character_emoji = "🎩" if fragment.character == "Lucien" else "🌸"

    # HTML mode: No escaping needed, HTML tags are safe
    fragment_text = f"{progress_info}{character_emoji} <b>{fragment.character}:</b>\n\n{fragment.text}"

    # Agregar información de recompensas si las hay
    if fragment.reward_besitos > 0:
        fragment_text += get_text("narrative.display.reward_line", reward=fragment.reward_besitos)

    # Crear teclado con opciones (pasando user_id para navegación)
    keyboard = await get_narrative_keyboard(fragment, session, user_id=user_id)

    # Verificar si el fragmento tiene imagen
    has_image = hasattr(fragment, 'image_url') and fragment.image_url

    # Mostrar el fragmento
    if has_image:
        # Si tiene imagen, enviar como foto con caption
        try:
            if is_callback:
                # En callback, eliminar mensaje anterior y enviar nuevo con imagen
                try:
                    await message.delete()
                except Exception:
                    # El mensaje puede ya no existir, continuar de todos modos
                    pass
                await message.bot.send_photo(
                    chat_id=message.chat.id,
                    photo=fragment.image_url,
                    caption=fragment_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                # En mensaje normal, enviar directamente
                await message.answer_photo(
                    photo=fragment.image_url,
                    caption=fragment_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Error enviando fragmento con imagen: {e}")
            # Fallback a texto sin imagen
            if is_callback:
                # Si el mensaje anterior tenía foto, eliminar y enviar nuevo
                if message.photo:
                    try:
                        await message.delete()
                    except Exception:
                        pass
                    await message.answer(fragment_text, reply_markup=keyboard, parse_mode="HTML")
                else:
                    await safe_edit(message, fragment_text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await safe_answer(message, fragment_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        # Sin imagen, enviar solo texto como antes
        if is_callback:
            # Si el mensaje anterior tenía foto, debemos eliminar y enviar nuevo
            # El patch en message_safety.py manejará esto automáticamente
            await safe_edit(message, fragment_text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await safe_answer(message, fragment_text, reply_markup=keyboard, parse_mode="HTML")

@router.callback_query(F.data == "start_narrative")
async def start_narrative_callback(callback: CallbackQuery, session: AsyncSession):
    """Handles the 'start_narrative' button click by calling the command handler."""
    await callback.answer(get_text("narrative.handler.starting_story"))
    await start_narrative_command(callback.message, session)

# Enhanced L1F1 Helper Functions

async def _is_new_user(user_id: int, session: AsyncSession) -> bool:
    """
    Determina si es un usuario nuevo que debe recibir enhanced L1F1.

    Verifica si el usuario ya ha iniciado narrativa o tiene estado narrativo.
    Los usuarios sin estado narrativo previo son considerados nuevos.

    Args:
        user_id: ID del usuario a verificar
        session: Sesión de base de datos

    Returns:
        True si es usuario nuevo, False si ya tiene historial narrativo
    """
    try:
        from database.narrative_models import UserNarrativeState
        from sqlalchemy import select

        # Verificar si existe estado narrativo previo
        stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        result = await session.execute(stmt)
        user_state = result.scalar_one_or_none()

        # Usuario nuevo si no tiene estado o nunca inició narrativa
        if not user_state or not user_state.narrative_started_at:
            return True

        return False

    except Exception as e:
        logger.error(f"Error verificando si es usuario nuevo {user_id}: {e}")
        # En caso de error, asumir que no es nuevo para usar flujo estándar
        return False

async def _try_load_enhanced_l1f1(session: AsyncSession) -> dict:
    """
    Intenta cargar el fragmento enhanced L1F1 para detección de arquetipos.

    Utiliza NarrativeLoader para cargar el fragmento mejorado con pesos
    de arquetipo integrados. En caso de error, retorna None para usar fallback.

    Args:
        session: Sesión de base de datos

    Returns:
        Diccionario con datos del fragmento enhanced L1F1 o None si falla
    """
    try:
        loader = NarrativeLoader(session)
        enhanced_fragment = await loader.load_enhanced_l1f1()

        if enhanced_fragment and enhanced_fragment.get('archetype_tracking', {}).get('enabled', False):
            logger.info("Enhanced L1F1 cargado exitosamente para detección de arquetipos")
            return enhanced_fragment

        logger.warning("Enhanced L1F1 no tiene tracking de arquetipos habilitado")
        return None

    except Exception as e:
        logger.error(f"Error cargando enhanced L1F1: {e}")
        return None

async def _display_enhanced_l1f1_fragment(message: Message, fragment_data: dict, session: AsyncSession):
    """
    Muestra el fragmento enhanced L1F1 con opciones optimizadas para detección de arquetipos.

    Renderiza el fragmento L1F1 mejorado con sus opciones de elección que incluyen
    pesos psicológicos. Prepara el teclado para capturar tanto la elección como
    el timing de respuesta para análisis de arquetipo.

    Args:
        message: Mensaje de Telegram para responder
        fragment_data: Datos del fragmento enhanced L1F1
        session: Sesión de base de datos
    """
    try:
        # Extraer información del fragmento
        character = fragment_data.get('character', 'Diana')
        content = fragment_data.get('content', '')
        choices = fragment_data.get('choices', [])
        image_url = fragment_data.get('image_url')

        # Formatear texto del fragmento
        character_emoji = "🌸" if character == "Diana" else "🎩"

        # HTML mode: No escaping needed
        fragment_text = f"{character_emoji} <b>{character}:</b>\n\n{content}"

        # Agregar información de recompensas si las hay
        reward_besitos = fragment_data.get('reward_besitos', 0)
        if reward_besitos > 0:
            fragment_text += f"\n\n✨ <i>Has ganado {reward_besitos} besitos</i>"

        # Crear teclado con opciones de enhanced L1F1
        keyboard = await _get_enhanced_l1f1_keyboard(choices)

        # Enviar con imagen si está disponible
        if image_url:
            try:
                await message.answer_photo(
                    photo=image_url,
                    caption=fragment_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Error enviando enhanced L1F1 con imagen: {e}")
                # Fallback a texto sin imagen
                await safe_answer(message, fragment_text, reply_markup=keyboard)
        else:
            await safe_answer(message, fragment_text, reply_markup=keyboard)

        logger.info(f"Enhanced L1F1 mostrado a usuario {message.from_user.id}")

    except Exception as e:
        logger.error(f"Error mostrando enhanced L1F1: {e}")
        # Fallback a mensaje de error
        await safe_answer(
            message,
            get_text("narrative.handler.enhanced_l1f1_load_error")
        )

async def _get_enhanced_l1f1_keyboard(choices: list):
    """
    Crea teclado interactivo para enhanced L1F1 con callback data especial.

    Genera botones para cada opción del enhanced L1F1 que incluyen metadata
    especial para capturar timing y activar análisis de arquetipos.

    Args:
        choices: Lista de opciones de elección del enhanced L1F1

    Returns:
        Teclado inline de Telegram con botones para enhanced L1F1
    """
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    buttons = []

    for i, choice in enumerate(choices):
        choice_text = choice.get('text', f'Opción {i+1}')
        # Usar callback data especial para enhanced L1F1
        callback_data = f"enhanced_l1f1_choice:{i}"

        buttons.append([InlineKeyboardButton(
            text=choice_text,
            callback_data=callback_data
        )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def _mark_user_started_enhanced_l1f1(user_id: int, session: AsyncSession):
    """
    Marca que el usuario ha comenzado con enhanced L1F1 para análisis posterior.

    Crea o actualiza el estado narrativo del usuario indicando que comenzó
    con el fragmento enhanced L1F1, lo cual será útil para el análisis de
    arquetipos y para evitar mostrar enhanced L1F1 en futuras sesiones.

    Args:
        user_id: ID del usuario
        session: Sesión de base de datos
    """
    try:
        from database.narrative_models import UserNarrativeState
        from sqlalchemy import select
        from datetime import datetime

        # Buscar o crear estado del usuario
        stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == user_id)
        result = await session.execute(stmt)
        user_state = result.scalar_one_or_none()

        if not user_state:
            user_state = UserNarrativeState(
                user_id=user_id,
                current_fragment_key="diana_enhanced_l1f1",
                fragments_visited=1,
                narrative_started_at=datetime.utcnow(),
                choices_made=[]
            )
            session.add(user_state)
        else:
            # Actualizar estado existente
            user_state.current_fragment_key = "diana_enhanced_l1f1"
            user_state.narrative_started_at = datetime.utcnow()

        await session.commit()
        logger.info(f"Usuario {user_id} marcado como iniciado con enhanced L1F1")

    except Exception as e:
        logger.error(f"Error marcando usuario como iniciado con enhanced L1F1: {e}")
        # No es crítico, continúa el flujo

# Choice Tracking Enhancement Functions

async def _capture_response_timing(user_id: int, message_date) -> float:
    """
    Captura el tiempo de respuesta del usuario para análisis de arquetipo.

    Calcula el tiempo transcurrido desde que se mostró el mensaje hasta que
    el usuario hizo su elección. Este timing es crucial para el análisis
    psicológico de patrones de respuesta.

    Args:
        user_id: ID del usuario
        message_date: Fecha/hora del mensaje original

    Returns:
        Tiempo de respuesta en segundos como float
    """
    try:
        from datetime import datetime
        import asyncio

        # Obtener timestamp actual
        current_time = datetime.utcnow()

        # Calcular diferencia en segundos
        if hasattr(message_date, 'timestamp'):
            message_timestamp = datetime.fromtimestamp(message_date.timestamp())
        else:
            message_timestamp = message_date

        time_diff = (current_time - message_timestamp).total_seconds()

        # Limitar a valores razonables (máximo 10 minutos)
        response_time = min(time_diff, 600.0)

        logger.info(f"Usuario {user_id} respondió en {response_time:.2f} segundos")
        return response_time

    except Exception as e:
        logger.error(f"Error capturando timing de respuesta para usuario {user_id}: {e}")
        # Retornar valor por defecto si hay error
        return 15.0

async def _store_enhanced_l1f1_choice(
    user_id: int,
    choice_index: int,
    choice_data: dict,
    response_time: float,
    session: AsyncSession
):
    """
    Almacena la elección de enhanced L1F1 con datos de timing para análisis.

    Guarda la elección del usuario junto con sus pesos de arquetipo,
    tiempo de respuesta y metadata para el análisis psicológico posterior.

    Args:
        user_id: ID del usuario
        choice_index: Índice de la elección seleccionada
        choice_data: Datos de la elección con pesos de arquetipo
        response_time: Tiempo de respuesta en segundos
        session: Sesión de base de datos
    """
    try:
        # Usar modelo temporal para almacenamiento en sesión de usuario
        # En implementación completa, esto se almacenaría en base de datos

        # Por ahora, almacenar en caché temporal para el análisis
        cache_key = f"enhanced_l1f1_choices_{user_id}"

        from datetime import datetime

        # Crear estructura de datos para la elección
        choice_record = {
            'choice_index': choice_index,
            'text': choice_data.get('text', ''),
            'archetype_weights': choice_data.get('archetype_weights', {}),
            'sub_archetype_weights': choice_data.get('sub_archetype_weights', {}),
            'response_time': response_time,
            'timestamp': datetime.utcnow().isoformat()
        }

        # Almacenar en atributo temporal de sesión (simple cache)
        if not hasattr(session, '_enhanced_l1f1_cache'):
            session._enhanced_l1f1_cache = {}

        if cache_key not in session._enhanced_l1f1_cache:
            session._enhanced_l1f1_cache[cache_key] = []

        session._enhanced_l1f1_cache[cache_key].append(choice_record)

        logger.info(f"Elección enhanced L1F1 almacenada para usuario {user_id}: índice {choice_index}")

    except Exception as e:
        logger.error(f"Error almacenando elección enhanced L1F1 para usuario {user_id}: {e}")

async def _get_user_l1f1_choices(user_id: int, session: AsyncSession) -> list:
    """
    Recupera las elecciones de enhanced L1F1 del usuario para análisis.

    Obtiene todas las elecciones realizadas por el usuario en el fragmento
    enhanced L1F1, incluyendo timing y pesos de arquetipo.

    Args:
        user_id: ID del usuario
        session: Sesión de base de datos

    Returns:
        Lista de elecciones con datos completos para análisis
    """
    try:
        cache_key = f"enhanced_l1f1_choices_{user_id}"

        if hasattr(session, '_enhanced_l1f1_cache') and cache_key in session._enhanced_l1f1_cache:
            return session._enhanced_l1f1_cache[cache_key]

        return []

    except Exception as e:
        logger.error(f"Error recuperando elecciones L1F1 para usuario {user_id}: {e}")
        return []

async def _trigger_archetype_analysis(user_id: int, choices_made: list, session: AsyncSession):
    """
    Activa el análisis de arquetipo cuando hay suficientes datos de L1.

    Procesa las elecciones del usuario con el ArchetypeAnalyzer para generar
    clasificación psicológica. Se activa cuando el usuario ha hecho suficientes
    elecciones en el fragmento L1F1.

    Args:
        user_id: ID del usuario
        choices_made: Lista de elecciones con pesos y timing
        session: Sesión de base de datos
    """
    try:
        from services.archetype_analyzer import ArchetypeAnalyzer

        analyzer = ArchetypeAnalyzer(session)

        # Preparar datos para análisis
        choice_weights = []
        timings = []

        for choice in choices_made:
            choice_weights.append({
                'archetype_weights': choice.get('archetype_weights', {}),
                'sub_archetype_weights': choice.get('sub_archetype_weights', {})
            })
            timings.append(choice.get('response_time', 15.0))

        # Ejecutar análisis de arquetipos
        analysis_results = await analyzer.analyze_l1_choices(user_id, choice_weights, timings)

        # Almacenar resultados en base de datos
        classification = await analyzer.store_classification_results(user_id, analysis_results)

        logger.info(f"Análisis de arquetipo completado para usuario {user_id}: "
                   f"arquetipo primario {analysis_results.get('dominant_archetype')} "
                   f"con confianza {analysis_results.get('confidence_score', 0):.2f}")

        # Limpiar caché temporal después del análisis
        cache_key = f"enhanced_l1f1_choices_{user_id}"
        if hasattr(session, '_enhanced_l1f1_cache') and cache_key in session._enhanced_l1f1_cache:
            del session._enhanced_l1f1_cache[cache_key]

    except Exception as e:
        logger.error(f"Error en análisis de arquetipo para usuario {user_id}: {e}")

async def _process_enhanced_l1f1_followup(
    callback: CallbackQuery,
    choice_index: int,
    enhanced_fragment: dict,
    session: AsyncSession
):
    """
    Procesa el fragmento de seguimiento según la elección en enhanced L1F1.

    Navega al siguiente fragmento apropiado basado en la elección del usuario,
    mantiene la experiencia narrativa fluida después del enhanced L1F1.

    Args:
        callback: Callback query de Telegram
        choice_index: Índice de la elección seleccionada
        enhanced_fragment: Datos del fragmento enhanced L1F1
        session: Sesión de base de datos
    """
    try:
        choices = enhanced_fragment.get('choices', [])
        followup_fragments = enhanced_fragment.get('followup_fragments', {})

        if 0 <= choice_index < len(choices):
            selected_choice = choices[choice_index]
            destination_key = selected_choice.get('destination_key', '')

            # Buscar fragmento de seguimiento
            if destination_key and destination_key in followup_fragments:
                followup_fragment = followup_fragments[destination_key]

                # Mostrar fragmento de seguimiento
                await _display_enhanced_followup_fragment(callback, followup_fragment, session)

            else:
                # Fallback a narrativa estándar
                await _fallback_to_standard_narrative(callback, session)

        else:
            await callback.message.edit_text(
                get_text("narrative.handler.enhanced_l1f1_choice_error")
            )

    except Exception as e:
        logger.error(f"Error procesando followup de enhanced L1F1: {e}")
        await _fallback_to_standard_narrative(callback, session)

async def _display_enhanced_followup_fragment(
    callback: CallbackQuery,
    fragment_data: dict,
    session: AsyncSession
):
    """
    Muestra un fragmento de seguimiento del enhanced L1F1.

    Args:
        callback: Callback query de Telegram
        fragment_data: Datos del fragmento de seguimiento
        session: Sesión de base de datos
    """
    try:
        character = fragment_data.get('character', 'Diana')
        content = fragment_data.get('content', '')
        choices = fragment_data.get('choices', [])
        image_url = fragment_data.get('image_url')

        # Formatear texto del fragmento
        character_emoji = "🌸" if character == "Diana" else "🎩"

        # HTML mode: No escaping needed
        fragment_text = f"{character_emoji} <b>{character}:</b>\n\n{content}"

        # Agregar recompensas si las hay
        reward_besitos = fragment_data.get('reward_besitos', 0)
        if reward_besitos > 0:
            fragment_text += f"\n\n✨ <i>Has ganado {reward_besitos} besitos</i>"

        # Crear teclado para el seguimiento
        keyboard = await _get_enhanced_followup_keyboard(choices)

        # Enviar con imagen si está disponible
        if image_url:
            try:
                # Eliminar mensaje anterior y enviar nuevo con imagen
                try:
                    await callback.message.delete()
                except Exception:
                    # El mensaje puede ya no existir
                    pass
                await callback.bot.send_photo(
                    chat_id=callback.message.chat.id,
                    photo=image_url,
                    caption=fragment_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Error enviando followup con imagen: {e}")
                # Fallback a editar texto con safe_edit que manejará fotos
                from utils.message_safety import safe_edit
                await safe_edit(callback.message, fragment_text, reply_markup=keyboard)
        else:
            # Usar safe_edit que manejará si el mensaje anterior tenía foto
            from utils.message_safety import safe_edit
            await safe_edit(callback.message, fragment_text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Error mostrando fragmento de seguimiento: {e}")
        await _fallback_to_standard_narrative(callback, session)

async def _get_enhanced_followup_keyboard(choices: list):
    """
    Crea teclado para fragmentos de seguimiento de enhanced L1F1.

    Args:
        choices: Lista de opciones de elección

    Returns:
        Teclado inline de Telegram
    """
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    buttons = []

    for i, choice in enumerate(choices):
        choice_text = choice.get('text', f'Opción {i+1}')
        # Usar callback data para seguimiento de enhanced L1F1
        callback_data = f"enhanced_l1f1_followup:{i}"

        buttons.append([InlineKeyboardButton(
            text=choice_text,
            callback_data=callback_data
        )])

    # Agregar opción para continuar a narrativa estándar
    buttons.append([InlineKeyboardButton(
        text=get_text("narrative.handler.continue_to_standard_narrative_button"),
        callback_data="continue_to_standard_narrative"
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def _fallback_to_standard_narrative(callback: CallbackQuery, session: AsyncSession):
    """
    Hace fallback a la narrativa estándar desde enhanced L1F1.

    Args:
        callback: Callback query de Telegram
        session: Sesión de base de datos
    """
    try:
        await callback.message.edit_text(
            get_text("narrative.handler.fallback_to_standard")
        )

    except Exception as e:
        logger.error(f"Error en fallback a narrativa estándar: {e}")
        await callback.answer(get_text("narrative.handler.continue_error"), show_alert=True)


async def _show_requirements_message(callback: CallbackQuery, requirements_info: RequirementsInfo, session: AsyncSession):
    """
    Muestra un mensaje detallado de requisitos no cumplidos con opciones de conversión.

    Args:
        callback: CallbackQuery from user
        requirements_info: Type-safe dict with requirement details
        session: Database session
    """
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    # Build message parts
    message_parts = [get_text("narrative.requirements.blocked_title")]
    message_parts.append(get_text("narrative.requirements.subtitle"))
    message_parts.append(get_text("narrative.requirements.header"))

    has_requirements = False

    # Besitos requirement
    if requirements_info.get("required_besitos", 0) > 0:
        has_requirements = True
        missing = requirements_info.get("missing_besitos", 0)
        status_icon = "✅" if missing <= 0 else "❌"
        
        message_parts.append(get_text(
            "narrative.requirements.besitos_req",
            icon=status_icon,
            current=requirements_info.get("current_besitos", 0),
            required=requirements_info.get("required_besitos", 0)
        ))

        if missing > 0:
            message_parts.append(get_text("narrative.requirements.besitos_missing", missing=missing))
        else:
            message_parts.append("\n")


    # Role requirement
    if requirements_info.get("required_role"):
        has_requirements = True
        missing_role = requirements_info.get("missing_role")
        status_icon = "✅" if not missing_role else "❌"

        role_names = {
            "vip": get_text("narrative.requirements.role_vip"),
            "free": get_text("narrative.requirements.role_free"),
            "admin": get_text("narrative.requirements.role_admin")
        }
        current_role = requirements_info.get("current_role", "free")
        required_role = requirements_info.get("required_role")
        current_role_name = role_names.get(current_role, current_role)
        required_role_name = role_names.get(required_role, required_role)

        message_parts.append(get_text(
            "narrative.requirements.access_req",
            icon=status_icon,
            current_role=current_role_name
        ))

        if missing_role:
            message_parts.append(get_text("narrative.requirements.access_needed", required_role=required_role_name))

    if not has_requirements:
        message_parts.append(get_text("narrative.requirements.no_specific_req"))

    # Add conversion teaser
    message_parts.append(get_text("narrative.requirements.how_to_get_it"))

    # Build keyboard with actions
    builder = InlineKeyboardBuilder()

    # If missing besitos, offer ways to earn them
    if requirements_info.get("missing_besitos", 0) > 0:
        message_parts.append(get_text("narrative.requirements.earn_besitos_title"))
        message_parts.append(get_text("narrative.requirements.earn_besitos_1"))
        message_parts.append(get_text("narrative.requirements.earn_besitos_2"))
        message_parts.append(get_text("narrative.requirements.earn_besitos_3"))

        builder.button(text=get_text("narrative.requirements.visit_shop_button"), callback_data="shop_access")

    # If missing role (VIP), offer subscription
    if requirements_info.get("missing_role") == "vip":
        message_parts.append(get_text("narrative.requirements.get_vip_title"))
        message_parts.append(get_text("narrative.requirements.get_vip_1"))
        message_parts.append(get_text("narrative.requirements.get_vip_2"))
        message_parts.append(get_text("narrative.requirements.get_vip_3"))

        builder.button(text=get_text("narrative.requirements.vip_info_button"), callback_data="vip_info")

    # Add back button
    builder.button(text=get_text("narrative.requirements.back_button"), callback_data="continue_narrative")
    builder.adjust(1)

    message_text = "".join(message_parts)

    try:
        await callback.message.edit_text(
            message_text,
            reply_markup=builder.as_markup(),
            parse_mode="MarkdownV2"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error showing requirements message: {e}")
        await callback.answer(
            get_text("narrative.requirements.unmet_req_error"),
            show_alert=True
        )
