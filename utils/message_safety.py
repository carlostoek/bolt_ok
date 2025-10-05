from aiogram.types import Message
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from functools import wraps

DEFAULT_SAFE_MESSAGE = "\ud83d\udcec No hay contenido disponible en este momento."

async def safe_answer(message: Message, text: str, **kwargs):
    text = text.strip() if isinstance(text, str) else ""
    if not text:
        text = DEFAULT_SAFE_MESSAGE
    return await message.answer(text, **kwargs)

async def safe_edit(message: Message, text: str, **kwargs):
    """
    Edita un mensaje de forma segura, manejando el caso de mensajes con foto.
    Si el mensaje tiene foto, lo elimina y envía uno nuevo.
    """
    text = text.strip() if isinstance(text, str) else ""
    if not text:
        text = DEFAULT_SAFE_MESSAGE

    # Si el mensaje tiene foto, no podemos usar edit_text
    # Debemos eliminar y enviar nuevo mensaje
    if message.photo:
        try:
            await message.delete()
            return await message.answer(text, **kwargs)
        except Exception:
            # Si falla eliminar, intentar enviar mensaje nuevo sin eliminar
            return await message.answer(text, **kwargs)

    return await message.edit_text(text, **kwargs)

async def safe_send_message(bot, chat_id: int, text: str, **kwargs):
    text = text.strip() if isinstance(text, str) else ""
    if not text:
        text = DEFAULT_SAFE_MESSAGE
    return await bot.send_message(chat_id, text, **kwargs)

async def safe_edit_message_text(bot, chat_id: int, message_id: int, text: str, **kwargs):
    text = text.strip() if isinstance(text, str) else ""
    if not text:
        text = DEFAULT_SAFE_MESSAGE
    return await bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id, **kwargs)


def patch_message_methods():
    """Globally patch aiogram Message methods to enforce safe text."""

    original_answer = Message.answer
    original_edit_text = Message.edit_text

    async def _patched_answer(self: Message, text: str, **kwargs):
        text = text.strip() if isinstance(text, str) else ""
        if not text:
            text = DEFAULT_SAFE_MESSAGE
        return await original_answer(self, text, **kwargs)

    async def _patched_edit_text(self: Message, text: str, **kwargs):
        text = text.strip() if isinstance(text, str) else ""
        if not text:
            text = DEFAULT_SAFE_MESSAGE

        # Si el mensaje tiene foto, no podemos usar edit_text
        # Debemos eliminar y enviar nuevo mensaje
        if self.photo:
            try:
                await self.delete()
                return await original_answer(self, text, **kwargs)
            except Exception:
                # Si falla eliminar, enviar mensaje nuevo sin eliminar
                return await original_answer(self, text, **kwargs)

        return await original_edit_text(self, text, **kwargs)

    Message.answer = _patched_answer
    Message.edit_text = _patched_edit_text
