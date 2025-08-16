"""
Tests de protección para Message Safety - Critical Production Stability.
Estos tests protegen las funciones de seguridad de mensajes que previenen errores de Telegram API.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, User as TelegramUser, Chat
from aiogram.exceptions import TelegramBadRequest

from utils.message_safety import (
    safe_answer, 
    safe_edit, 
    safe_send_message, 
    safe_edit_message_text,
    patch_message_methods,
    DEFAULT_SAFE_MESSAGE
)


@pytest.mark.asyncio
class TestMessageSafetyProtection:
    """Tests críticos para las funciones de seguridad de mensajes."""

    async def test_safe_answer_texto_normal(self):
        """
        CRITICAL: Test que protege el comportamiento normal de safe_answer.
        Los mensajes normales deben enviarse sin modificación.
        """
        # Setup mock message
        message = MagicMock()
        message.answer = AsyncMock()
        
        # Test normal text
        await safe_answer(message, "Hola Diana, ¿cómo estás?")
        
        # Critical assertions - normal text must pass through unchanged
        message.answer.assert_called_once_with("Hola Diana, ¿cómo estás?")

    async def test_safe_answer_texto_vacio(self):
        """
        CRITICAL: Test que protege contra textos vacíos.
        Los textos vacíos DEBEN ser reemplazados por el mensaje seguro.
        """
        message = MagicMock()
        message.answer = AsyncMock()
        
        test_cases = ["", "   ", "\n\t  ", None]
        
        for empty_text in test_cases:
            message.answer.reset_mock()
            await safe_answer(message, empty_text)
            
            # Critical assertions - empty text must be replaced
            message.answer.assert_called_once_with(DEFAULT_SAFE_MESSAGE)

    async def test_safe_answer_caracteres_surrogates(self):
        """
        CRITICAL: Test que protege contra caracteres surrogates problemáticos.
        Los caracteres problemáticos deben ser limpiados sin fallar.
        """
        message = MagicMock()
        message.answer = AsyncMock()
        
        # Text with potential surrogate issues
        problematic_text = "Diana te sonríe \udcff\udcfe con cariño"
        
        await safe_answer(message, problematic_text)
        
        # Critical assertions - must not crash and must clean text
        message.answer.assert_called_once()
        called_text = message.answer.call_args[0][0]
        assert isinstance(called_text, str), "Result must be valid string"
        # Text should be cleaned but still contain main content
        assert "Diana te sonríe" in called_text, "Main content must be preserved"

    async def test_safe_answer_con_parametros_adicionales(self):
        """
        CRITICAL: Test que protege el paso de parámetros adicionales.
        Los parámetros como parse_mode, reply_markup deben conservarse.
        """
        message = MagicMock()
        message.answer = AsyncMock()
        
        # Mock keyboard
        mock_keyboard = MagicMock()
        
        await safe_answer(
            message, 
            "Diana te presenta opciones", 
            parse_mode="Markdown",
            reply_markup=mock_keyboard,
            disable_web_page_preview=True
        )
        
        # Critical assertions - all parameters must be preserved
        message.answer.assert_called_once_with(
            "Diana te presenta opciones",
            parse_mode="Markdown", 
            reply_markup=mock_keyboard,
            disable_web_page_preview=True
        )

    async def test_safe_edit_funcionalidad_basica(self):
        """
        CRITICAL: Test que protege la funcionalidad básica de safe_edit.
        Debe editar mensajes correctamente y manejar textos vacíos.
        """
        message = MagicMock()
        message.edit_text = AsyncMock()
        
        # Test normal edit
        await safe_edit(message, "Diana actualiza su mensaje")
        message.edit_text.assert_called_once_with("Diana actualiza su mensaje")
        
        # Test empty text edit
        message.edit_text.reset_mock()
        await safe_edit(message, "")
        message.edit_text.assert_called_once_with(DEFAULT_SAFE_MESSAGE)

    async def test_safe_send_message_funcionalidad_basica(self):
        """
        CRITICAL: Test que protege la funcionalidad básica de safe_send_message.
        Debe enviar mensajes correctamente a través del bot.
        """
        bot = MagicMock()
        bot.send_message = AsyncMock()
        
        chat_id = 123456789
        
        # Test normal send
        await safe_send_message(bot, chat_id, "Diana te envía un mensaje")
        bot.send_message.assert_called_once_with(chat_id, "Diana te envía un mensaje")
        
        # Test empty text send
        bot.send_message.reset_mock()
        await safe_send_message(bot, chat_id, "")
        bot.send_message.assert_called_once_with(chat_id, DEFAULT_SAFE_MESSAGE)

    async def test_safe_edit_message_text_funcionalidad_basica(self):
        """
        CRITICAL: Test que protege la funcionalidad básica de safe_edit_message_text.
        Debe editar mensajes específicos correctamente.
        """
        bot = MagicMock()
        bot.edit_message_text = AsyncMock()
        
        chat_id = 123456789
        message_id = 456
        
        # Test normal edit
        await safe_edit_message_text(bot, chat_id, message_id, "Diana edita su mensaje")
        bot.edit_message_text.assert_called_once_with(
            text="Diana edita su mensaje", 
            chat_id=chat_id, 
            message_id=message_id
        )
        
        # Test empty text edit
        bot.edit_message_text.reset_mock()
        await safe_edit_message_text(bot, chat_id, message_id, "")
        bot.edit_message_text.assert_called_once_with(
            text=DEFAULT_SAFE_MESSAGE, 
            chat_id=chat_id, 
            message_id=message_id
        )

    async def test_safe_functions_preservan_kwargs(self):
        """
        CRITICAL: Test que protege la preservación de argumentos nombrados.
        Todos los kwargs deben pasarse correctamente a las funciones subyacentes.
        """
        # Test safe_send_message with kwargs
        bot = MagicMock()
        bot.send_message = AsyncMock()
        
        await safe_send_message(
            bot, 
            123456, 
            "Diana te habla",
            parse_mode="HTML",
            disable_notification=True,
            reply_to_message_id=789
        )
        
        bot.send_message.assert_called_once_with(
            123456, 
            "Diana te habla",
            parse_mode="HTML",
            disable_notification=True,
            reply_to_message_id=789
        )

    def test_patch_message_methods_aplicacion(self):
        """
        CRITICAL: Test que protege la aplicación de parches a métodos de Message.
        Los métodos originales deben ser reemplazados por versiones seguras.
        """
        # Store original methods
        original_answer = Message.answer
        original_edit_text = Message.edit_text
        
        try:
            # Apply patches
            patch_message_methods()
            
            # Critical assertions - methods must be patched
            assert Message.answer != original_answer, "answer method must be patched"
            assert Message.edit_text != original_edit_text, "edit_text method must be patched"
            
        finally:
            # Restore original methods to avoid affecting other tests
            Message.answer = original_answer
            Message.edit_text = original_edit_text

    async def test_patched_methods_comportamiento_seguro(self):
        """
        CRITICAL: Test que protege el comportamiento seguro de métodos parcheados.
        Los métodos parcheados deben aplicar la misma lógica de seguridad.
        """
        # Store and patch methods
        original_answer = Message.answer
        original_edit_text = Message.edit_text
        
        try:
            patch_message_methods()
            
            # Create mock message
            message = MagicMock()
            message.answer = AsyncMock()
            message.edit_text = AsyncMock()
            
            # Test patched answer with empty text
            patched_answer = Message.answer.__func__
            await patched_answer(message, "")
            message.answer.assert_called_once_with(DEFAULT_SAFE_MESSAGE)
            
            # Test patched edit_text with empty text
            message.edit_text.reset_mock()
            patched_edit = Message.edit_text.__func__
            await patched_edit(message, "")
            message.edit_text.assert_called_once_with(DEFAULT_SAFE_MESSAGE)
            
        finally:
            # Restore original methods
            Message.answer = original_answer
            Message.edit_text = original_edit_text

    async def test_comportamiento_con_none_values(self):
        """
        CRITICAL: Test que protege el manejo de valores None.
        Los valores None deben ser tratados como texto vacío.
        """
        message = MagicMock()
        message.answer = AsyncMock()
        
        await safe_answer(message, None)
        
        # Critical assertions - None must be handled as empty
        message.answer.assert_called_once_with(DEFAULT_SAFE_MESSAGE)

    async def test_comportamiento_con_objetos_no_string(self):
        """
        CRITICAL: Test que protege el manejo de objetos no-string.
        Los objetos que no sean strings deben ser manejados gracefully.
        """
        message = MagicMock()
        message.answer = AsyncMock()
        
        # Test with various non-string objects
        test_objects = [123, [], {}, object()]
        
        for obj in test_objects:
            message.answer.reset_mock()
            await safe_answer(message, obj)
            
            # Critical assertions - non-strings must be handled
            message.answer.assert_called_once_with(DEFAULT_SAFE_MESSAGE)

    async def test_preservacion_texto_con_espacios_significativos(self):
        """
        CRITICAL: Test que protege la preservación de espacios significativos.
        Los espacios dentro del texto deben preservarse, solo se eliminan espacios de borde.
        """
        message = MagicMock()
        message.answer = AsyncMock()
        
        text_with_internal_spaces = "  Diana te dice:   'Hola mi amor'  "
        expected_cleaned = "Diana te dice:   'Hola mi amor'"
        
        await safe_answer(message, text_with_internal_spaces)
        
        # Critical assertions - internal spaces must be preserved
        message.answer.assert_called_once_with(expected_cleaned)

    async def test_manejo_texto_solo_espacios(self):
        """
        CRITICAL: Test que protege el manejo de texto que solo contiene espacios.
        El texto de solo espacios debe tratarse como vacío.
        """
        message = MagicMock()
        message.answer = AsyncMock()
        
        whitespace_only_texts = ["   ", "\n\n\n", "\t\t", " \n \t ", "\r\n"]
        
        for whitespace_text in whitespace_only_texts:
            message.answer.reset_mock()
            await safe_answer(message, whitespace_text)
            
            # Critical assertions - whitespace-only text must be treated as empty
            message.answer.assert_called_once_with(DEFAULT_SAFE_MESSAGE)

    async def test_integration_escenario_real_usuario(self):
        """
        CRITICAL: Test de integración que simula escenarios reales de usuario.
        Debe manejar correctamente una secuencia típica de interacciones.
        """
        # Simulate real user interaction sequence
        message = MagicMock()
        message.answer = AsyncMock()
        message.edit_text = AsyncMock()
        
        bot = MagicMock()
        bot.send_message = AsyncMock()
        
        user_id = 123456789
        
        # 1. User sends normal message
        await safe_answer(message, "Diana, quiero conocer más sobre ti")
        message.answer.assert_called_with("Diana, quiero conocer más sobre ti")
        
        # 2. Bot responds with narrative
        narrative_response = "Diana te mira con ojos misteriosos y sonríe suavemente..."
        await safe_send_message(bot, user_id, narrative_response)
        bot.send_message.assert_called_with(user_id, narrative_response)
        
        # 3. System tries to edit a message (possibly with empty content due to error)
        await safe_edit(message, "")
        message.edit_text.assert_called_with(DEFAULT_SAFE_MESSAGE)
        
        # 4. System sends follow-up message
        await safe_send_message(bot, user_id, "Diana espera tu respuesta...")
        
        # Critical assertions - all interactions must complete successfully
        assert message.answer.call_count == 1, "Answer must be called once"
        assert message.edit_text.call_count == 1, "Edit must be called once"
        assert bot.send_message.call_count == 2, "Send message must be called twice"

    async def test_default_safe_message_personalizado(self):
        """
        CRITICAL: Test que verifica que el mensaje seguro por defecto es apropiado.
        El mensaje por defecto debe ser informativo y mantener el tono del bot.
        """
        # Verify the default safe message is appropriate
        assert DEFAULT_SAFE_MESSAGE is not None, "Default safe message must be defined"
        assert len(DEFAULT_SAFE_MESSAGE) > 0, "Default safe message must not be empty"
        assert isinstance(DEFAULT_SAFE_MESSAGE, str), "Default safe message must be string"
        
        # The current default should be informative for users
        expected_default = "📬 No hay contenido disponible en este momento."
        assert DEFAULT_SAFE_MESSAGE == expected_default, f"Default message should be '{expected_default}'"