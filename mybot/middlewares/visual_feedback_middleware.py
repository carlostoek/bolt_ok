"""
Middleware para feedback visual inmediato con personalidad
QUICK WIN: Mejora percepción de responsividad y construye personalidad
"""
import asyncio
import logging
from typing import Any, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatAction

logger = logging.getLogger(__name__)


class VisualFeedbackMiddleware(BaseMiddleware):
    """
    Middleware que proporciona feedback visual inmediato para todas las interacciones
    Transforma acciones silenciosas en experiencias con personalidad
    """
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Any],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        # Solo aplicar a mensajes y callback queries
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        bot = data.get("bot")
        if not bot:
            return await handler(event, data)

        user = data.get("user")
        chat_id = event.from_user.id if isinstance(event, CallbackQuery) else event.chat.id

        try:
            # FEEDBACK INMEDIATO (< 100ms) - Emoji de reacción
            if isinstance(event, Message) and event.text:
                # Reaccionar inmediatamente a mensajes de texto
                try:
                    # Check if set_message_reaction is available
                    if hasattr(bot, 'set_message_reaction'):
                        await bot.set_message_reaction(
                            chat_id=chat_id,
                            message_id=event.message_id,
                            reaction=[{"type": "emoji", "emoji": "👀"}]
                        )
                    else:
                        # Fallback: enviar acción de typing
                        await bot.send_chat_action(chat_id, ChatAction.TYPING)
                except Exception:
                    # Fallback: enviar acción de typing
                    await bot.send_chat_action(chat_id, ChatAction.TYPING)
            
            elif isinstance(event, CallbackQuery):
                # Para callbacks, mostrar acción de typing
                await bot.send_chat_action(chat_id, ChatAction.TYPING)

            # FEEDBACK DE PROCESAMIENTO (si tarda > 1s)
            processing_task = None
            if isinstance(event, Message):
                processing_task = asyncio.create_task(
                    self._show_processing_indicator(bot, chat_id, event.message_id)
                )

            # Ejecutar el handler original
            result = await handler(event, data)

            # LIMPIAR FEEDBACK si se completó rápidamente
            if processing_task and not processing_task.done():
                processing_task.cancel()
            
            # MOSTRAR ÉXITO si fue una callback query
            if isinstance(event, CallbackQuery) and not processing_task:
                try:
                    await bot.answer_callback_query(event.id, text="✓ Listo")
                except Exception:
                    pass

            return result

        except Exception as e:
            logger.error(f"Error en feedback visual: {e}")
            # Aún ejecutar el handler incluso si falla el feedback
            return await handler(event, data)

    async def _show_processing_indicator(self, bot, chat_id: int, message_id: int):
        """Muestra indicador de procesamiento si la operación tarda más de 1 segundo"""
        await asyncio.sleep(1.0)  # Esperar 1 segundo antes de mostrar processing
        
        try:
            # Cambiar reacción a "procesando"
            if hasattr(bot, 'set_message_reaction'):
                await bot.set_message_reaction(
                    chat_id=chat_id,
                    message_id=message_id,
                    reaction=[{"type": "emoji", "emoji": "⏳"}]
                )
            else:
                # Fallback: enviar mensaje de procesamiento
                await bot.send_message(chat_id, "⏳ Procesando...")
        except Exception as e:
            logger.debug(f"No se pudo actualizar reacción: {e}")
