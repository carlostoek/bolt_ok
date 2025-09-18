"""
Advanced menu management system for seamless user experience.
Handles message lifecycle, navigation state, and prevents chat clutter.
Extended with HTML formatting support for enhanced administrative interfaces.
"""
import asyncio
import logging
import time
from typing import Dict, Optional, Tuple, Any, Union
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from utils.message_safety import (
    safe_answer,
    safe_edit,
    safe_send_message,
    safe_edit_message_text,
)
from aiogram.exceptions import TelegramBadRequest, TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, set_user_menu_state

# Import HTML formatter for enhanced menu display
try:
    from utils.html_formatter import HTMLMessageFormatter
except ImportError:
    HTMLMessageFormatter = None
    logging.warning("HTMLMessageFormatter not available - HTML features will be limited")

logger = logging.getLogger(__name__)

class MenuManager:
    """
    Centralized menu management system that ensures clean chat experience.
    - Only one active menu message per user
    - Automatic cleanup of temporary messages
    - Smooth navigation without message proliferation
    """
    
    def __init__(self):
        # Store the current menu message for each user
        self._active_menus: Dict[int, Tuple[int, int]] = {}  # user_id -> (chat_id, message_id)
        # Store temporary messages that should be auto-deleted
        self._temp_messages: Dict[int, Tuple[int, int, float]] = {}  # user_id -> (chat_id, message_id, expire_time)
        # Navigation history for back button functionality
        self._nav_history: Dict[int, list] = {}  # user_id -> [menu_states]
    
    async def show_menu(
        self, 
        message: Message, 
        text: str, 
        keyboard: InlineKeyboardMarkup,
        session: AsyncSession,
        menu_state: str,
        parse_mode: str = "Markdown",
        # NUEVO PARÁMETRO: Indicar si se debe eliminar el mensaje original (ej. el comando /start)
        delete_origin_message: bool = False 
    ) -> Message:
        """
        Display a menu, replacing any existing menu for this user.
        This ensures only one menu message exists per user.
        If delete_origin_message is True, attempts to delete the message
        that triggered this menu display (e.g., a command).
        """
        user_id = message.from_user.id
        bot = message.bot
        
        # Clean up any temporary messages first
        await self._cleanup_temp_messages(bot, user_id)
        
        # Try to update existing menu if it exists
        existing = self._active_menus.get(user_id)
        if existing:
            chat_id, msg_id = existing
            try:
                # Intenta editar el mensaje del menú *anterior*
                await safe_edit_message_text(
                    bot,
                    chat_id,
                    msg_id,
                    text,
                    reply_markup=keyboard,
                    parse_mode=parse_mode,
                )
                await set_user_menu_state(session, user_id, menu_state)
                
                # Si el origen es un comando y se debe eliminar, lo hacemos aquí.
                if delete_origin_message and message.message_id:
                    try:
                        await bot.delete_message(message.chat.id, message.message_id)
                    except TelegramAPIError as e:
                        logger.warning(f"Could not delete origin message {message.message_id} for user {user_id}: {e}")
                return None  # Message was updated, no new message sent
            except TelegramBadRequest as e:
                if "message is not modified" in str(e).lower():
                    # Si el mensaje no ha cambiado, no hay necesidad de hacer nada.
                    if delete_origin_message and message.message_id:
                        try:
                            await bot.delete_message(message.chat.id, message.message_id)
                        except TelegramAPIError as e:
                            logger.warning(f"Could not delete origin message {message.message_id} for user {user_id}: {e}")
                    return None
                # El mensaje no se pudo editar (ej. fue borrado por el usuario), así que necesitamos enviar uno nuevo.
                logger.debug(f"Could not update menu for user {user_id} (will create new): {e}")
            except Exception as e:
                logger.error(f"Error updating menu for user {user_id}, falling back to create new: {e}")
        
        # Sanitize text to prevent Markdown parsing errors
        if parse_mode == "Markdown":
            from utils.text_utils import escape_markdown
            sanitized_text = escape_markdown(text)
        else:
            sanitized_text = text
        
        # Create new menu message (either because no existing, or update failed)
        try:
            sent_message = await safe_answer(
                message,
                sanitized_text,
                reply_markup=keyboard,
                parse_mode=parse_mode,
            )
            self._active_menus[user_id] = (sent_message.chat.id, sent_message.message_id)
            await set_user_menu_state(session, user_id, menu_state)
            
            # Update navigation history
            self._update_nav_history(user_id, menu_state, parse_mode)
            
            # Delete the original command message if requested
            if delete_origin_message and message.message_id:
                try:
                    await bot.delete_message(message.chat.id, message.message_id)
                except TelegramAPIError as e:
                    logger.warning(f"Could not delete origin message {message.message_id} for user {user_id}: {e}")
            
            return sent_message
        except Exception as e:
            logger.error(f"Error creating menu for user {user_id}: {e}")
            raise
    
    async def update_menu(
        self,
        callback: CallbackQuery,
        text: str,
        keyboard: InlineKeyboardMarkup,
        session: AsyncSession,
        menu_state: str,
        parse_mode: str = "Markdown"
    ) -> bool:
        """
        Update the current menu via callback query.
        Returns True if successful, False otherwise.
        """
        user_id = callback.from_user.id
        bot = callback.bot
        message = callback.message # This is the message that contains the inline keyboard
        
        # Clean up any temporary messages
        await self._cleanup_temp_messages(bot, user_id)
        
        try:
            # Sanitize text to prevent Markdown parsing errors
            if parse_mode == "Markdown":
                from utils.text_utils import escape_markdown
                sanitized_text = escape_markdown(text)
            else:
                sanitized_text = text
            
            await safe_edit(
                message,
                sanitized_text,
                reply_markup=keyboard,
                parse_mode=parse_mode,
            )
            
            # Update stored menu reference - this is crucial to ensure _active_menus points to the correct message
            self._active_menus[user_id] = (message.chat.id, message.message_id) # Corregido de message.message.id a message.message_id
            await set_user_menu_state(session, user_id, menu_state)
            
            # Update navigation history
            self._update_nav_history(user_id, menu_state, parse_mode)
            
            return True
        except TelegramBadRequest as e:
            if "message is not modified" in str(e).lower():
                return True  # No change needed
            logger.error(f"Error updating menu for user {user_id}: {e}")
            return await self._recover_to_main_admin_menu(callback, session)
        except Exception as e:
            logger.error(f"Error updating menu for user {user_id}: {e}")
            return await self._recover_to_main_admin_menu(callback, session)
    
    async def send_temporary_message(
        self,
        message: Message,
        text: str,
        keyboard: Optional[InlineKeyboardMarkup] = None,
        auto_delete_seconds: int = 5,
        parse_mode: str = "Markdown"
    ) -> Message:
        """
        Send a temporary message that will be automatically deleted.
        Useful for error messages, confirmations, etc.
        """
        user_id = message.from_user.id
        bot = message.bot
        
        # Clean up previous temporary message
        await self._cleanup_temp_messages(bot, user_id)
        
        try:
            sent_message = await safe_answer(
                message,
                text,
                reply_markup=keyboard,
                parse_mode=parse_mode,
            )
            
            # Schedule for deletion
            import time
            expire_time = time.time() + auto_delete_seconds
            self._temp_messages[user_id] = (sent_message.chat.id, sent_message.message_id, expire_time)
            
            # Schedule actual deletion
            asyncio.create_task(self._auto_delete_message(bot, user_id, auto_delete_seconds))
            
            return sent_message
        except Exception as e:
            logger.error(f"Error sending temporary message for user {user_id}: {e}")
            raise
    
    async def _recover_to_main_admin_menu(self, query: CallbackQuery, session: AsyncSession) -> bool:
        """
        Recovers user to the main admin menu after a failure.
        Sends a temporary message and updates the menu.
        """
        user_id = query.from_user.id
        try:
            from utils.menu_factory import menu_factory
            
            await self.send_temporary_message(
                query.message,
                "⚠️ Hubo un error al cargar el menú. Volviendo al menú principal.",
                auto_delete_seconds=7
            )

            main_menu_state = "admin_main_menu"
            text, keyboard = await menu_factory.create_menu(main_menu_state, user_id, session, query.bot)

            # We are recovering, so we directly edit the message to avoid recursion
            await safe_edit(
                query.message,
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            # And manually update the state
            self._active_menus[user_id] = (query.message.chat.id, query.message.message_id)
            await set_user_menu_state(session, user_id, main_menu_state)
            self._update_nav_history(user_id, main_menu_state, parse_mode="HTML")
            
            return True
        except Exception as fallback_e:
            logger.critical(f"CRITICAL: Fallback recovery to main admin menu failed for user {user_id}: {fallback_e}")
            return False

    async def go_back(
        self,
        callback: CallbackQuery,
        session: AsyncSession,
        default_menu_state: str = "main",
        default_parse_mode: str = "Markdown"
    ) -> bool:
        """
        Navigate back to the previous menu in the history.
        """
        user_id = callback.from_user.id
        history = self._nav_history.get(user_id, [])
        
        previous_state = default_menu_state
        previous_parse_mode = default_parse_mode

        # Ensure we always have at least one state (the current one) if history is not empty
        if len(history) > 1:
            # Remove current state
            history.pop() 
            previous_state, previous_parse_mode = history[-1]
        elif len(history) == 1:
            # If only one item, it means we are at the "root" of the history for this session.
            # We should try to go back to it, but not pop it.
            previous_state, previous_parse_mode = history[0] # Stay at the current state
            logger.debug(f"User {user_id} is at the start of navigation history. Staying at '{(previous_state, previous_parse_mode)}'.")
        else:
            previous_state = default_menu_state
            logger.debug(f"User {user_id} has no navigation history. Falling back to default: '{(default_menu_state, default_parse_mode)}'.")
        
        # Import here to avoid circular imports
        from utils.menu_factory import menu_factory # Usa la instancia global si existe
        
        try:
            # create_menu necesita 'bot' para ciertas lógicas de texto/teclado.
            # Pasamos callback.bot
            text, keyboard = await menu_factory.create_menu(previous_state, callback.from_user.id, session, callback.bot)
            return await self.update_menu(
                callback, text, keyboard, session, previous_state, parse_mode=previous_parse_mode
            )
        except Exception as e:
            logger.error(f"Error going back for user {user_id}: {e}")
            return await self._recover_to_main_admin_menu(callback, session)
    
    async def clear_user_data(self, user_id: int, bot) -> None:
        """
        Clear all stored data for a user (menus, temp messages, history).
        Useful when user logs out or resets.
        """
        # Clean up temporary messages
        await self._cleanup_temp_messages(bot, user_id)

        # Remove active menu reference
        self._active_menus.pop(user_id, None)

        # Clear navigation history
        self._nav_history.pop(user_id, None)

    async def create_html_menu(
        self,
        user_id: int,
        menu_data: Dict[str, Any],
        format_type: str = "html",
        user_context: Optional[Dict] = None
    ) -> str:
        """
        Create HTML-formatted menu text using HTMLMessageFormatter.

        Args:
            user_id: User ID for context
            menu_data: Menu data dictionary containing title, sections, etc.
            format_type: Format type ("html" or "markdown")
            user_context: Optional user context for personalization

        Returns:
            Formatted menu text string
        """
        try:
            if format_type == "html" and HTMLMessageFormatter:
                return HTMLMessageFormatter.format_admin_menu(menu_data, user_context)
            else:
                # Fallback to basic formatting
                lines = []
                if 'title' in menu_data:
                    lines.append(f"**{menu_data['title']}**\n")

                if 'description' in menu_data:
                    lines.append(f"{menu_data['description']}\n")

                if 'sections' in menu_data:
                    for section in menu_data['sections']:
                        if 'title' in section:
                            lines.append(f"\n**{section['title']}**")
                        if 'options' in section:
                            for option in section['options']:
                                if isinstance(option, dict):
                                    lines.append(f"• {option.get('icon', '')} {option.get('text', '')}")
                                else:
                                    lines.append(f"• {option}")

                return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error creating HTML menu for user {user_id}: {e}")
            return "**Menú Administrativo**\n\nError al cargar el menú."

    async def cleanup_with_retry(
        self,
        user_id: int,
        bot,
        max_retries: int = 3,
        backoff_factor: float = 1.0
    ) -> bool:
        """
        Enhanced cleanup with retry mechanism and graceful error handling.

        Args:
            user_id: User ID for cleanup
            bot: Bot instance for message operations
            max_retries: Maximum number of retry attempts
            backoff_factor: Exponential backoff multiplier

        Returns:
            True if cleanup successful, False otherwise
        """
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                # Clean up temporary messages first
                await self._cleanup_temp_messages(bot, user_id)

                # Clean up active menu if exists
                active_menu = self._active_menus.get(user_id)
                if active_menu:
                    chat_id, message_id = active_menu
                    try:
                        await bot.delete_message(chat_id, message_id)
                        self._active_menus.pop(user_id, None)
                        logger.debug(f"Successfully cleaned up menu for user {user_id}")
                    except TelegramBadRequest as e:
                        if "message to delete not found" in str(e).lower():
                            # Message already deleted, just clean up reference
                            self._active_menus.pop(user_id, None)
                            logger.debug(f"Menu message already deleted for user {user_id}")
                        else:
                            raise

                return True

            except Exception as e:
                retry_count += 1
                last_error = e

                if retry_count >= max_retries:
                    logger.error(f"Failed to cleanup for user {user_id} after {max_retries} retries: {e}")
                    break

                # Exponential backoff
                delay = backoff_factor * (2 ** (retry_count - 1))
                logger.warning(f"Cleanup retry {retry_count}/{max_retries} for user {user_id}, waiting {delay}s: {e}")
                await asyncio.sleep(delay)

        # Graceful degradation - clean up what we can
        try:
            self._active_menus.pop(user_id, None)
            self._temp_messages.pop(user_id, None)
            logger.warning(f"Performed graceful cleanup degradation for user {user_id}")
        except Exception as degradation_error:
            logger.error(f"Even graceful degradation failed for user {user_id}: {degradation_error}")

        return False

    async def schedule_cleanup(
        self,
        user_id: int,
        bot,
        delay_seconds: int = 7
    ) -> None:
        """
        Schedule automatic cleanup of user's temporary messages after delay.

        Args:
            user_id: User ID for cleanup
            bot: Bot instance
            delay_seconds: Delay before cleanup in seconds
        """
        try:
            logger.debug(f"Scheduling cleanup for user {user_id} in {delay_seconds} seconds")

            # Schedule the cleanup task
            asyncio.create_task(self._execute_scheduled_cleanup(user_id, bot, delay_seconds))

        except Exception as e:
            logger.error(f"Error scheduling cleanup for user {user_id}: {e}")

    async def _execute_scheduled_cleanup(
        self,
        user_id: int,
        bot,
        delay_seconds: int
    ) -> None:
        """
        Execute scheduled cleanup after delay.

        Args:
            user_id: User ID for cleanup
            bot: Bot instance
            delay_seconds: Delay before cleanup
        """
        try:
            await asyncio.sleep(delay_seconds)

            # Check if user still has temporary messages to clean up
            temp_msg = self._temp_messages.get(user_id)
            if temp_msg:
                chat_id, message_id, expire_time = temp_msg
                current_time = time.time()

                # Only clean up if message hasn't been manually cleaned up and is expired
                if current_time >= expire_time:
                    try:
                        await bot.delete_message(chat_id, message_id)
                        logger.debug(f"Scheduled cleanup executed for user {user_id}, message {message_id}")
                    except TelegramBadRequest as e:
                        if "message to delete not found" in str(e).lower():
                            logger.debug(f"Scheduled message already deleted for user {user_id}")
                        else:
                            logger.warning(f"Scheduled cleanup failed for user {user_id}: {e}")
                    except Exception as e:
                        logger.error(f"Unexpected error in scheduled cleanup for user {user_id}: {e}")
                    finally:
                        self._temp_messages.pop(user_id, None)

        except Exception as e:
            logger.error(f"Error in scheduled cleanup execution for user {user_id}: {e}")

    async def show_html_menu(
        self,
        message: Message,
        menu_data: Dict[str, Any],
        keyboard: InlineKeyboardMarkup,
        session: AsyncSession,
        menu_state: str,
        user_context: Optional[Dict] = None,
        delete_origin_message: bool = False
    ) -> Message:
        """
        Display an HTML-formatted menu using the enhanced MenuManager capabilities.
        This is the main method for showing admin menus with HTML formatting.

        Args:
            message: Telegram message object
            menu_data: Menu data dictionary for HTML formatting
            keyboard: Inline keyboard for menu navigation
            session: Database session
            menu_state: Current menu state for navigation
            user_context: Optional user context for personalization
            delete_origin_message: Whether to delete the original message

        Returns:
            Sent message object
        """
        try:
            # Create HTML-formatted menu text
            text = await self.create_html_menu(
                message.from_user.id,
                menu_data,
                format_type="html",
                user_context=user_context
            )

            # Display menu using existing show_menu method with HTML parse mode
            return await self.show_menu(
                message=message,
                text=text,
                keyboard=keyboard,
                session=session,
                menu_state=menu_state,
                parse_mode="HTML",  # Use HTML parse mode
                delete_origin_message=delete_origin_message
            )

        except Exception as e:
            logger.error(f"Error showing HTML menu for user {message.from_user.id}: {e}")
            # Fallback to basic menu
            fallback_text = "**Menú Administrativo**\n\nError al cargar el menú."
            return await self.show_menu(
                message=message,
                text=fallback_text,
                keyboard=keyboard,
                session=session,
                menu_state=menu_state,
                parse_mode="Markdown",
                delete_origin_message=delete_origin_message
            )

    async def update_html_menu(
        self,
        callback: CallbackQuery,
        menu_data: Dict[str, Any],
        keyboard: InlineKeyboardMarkup,
        session: AsyncSession,
        menu_state: str,
        user_context: Optional[Dict] = None
    ) -> bool:
        """
        Update current menu with HTML-formatted content.

        Args:
            callback: Callback query from user interaction
            menu_data: Menu data dictionary for HTML formatting
            keyboard: Updated inline keyboard
            session: Database session
            menu_state: New menu state
            user_context: Optional user context for personalization

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create HTML-formatted menu text
            text = await self.create_html_menu(
                callback.from_user.id,
                menu_data,
                format_type="html",
                user_context=user_context
            )

            # Update menu using existing method with HTML parse mode
            return await self.update_menu(
                callback=callback,
                text=text,
                keyboard=keyboard,
                session=session,
                menu_state=menu_state,
                parse_mode="HTML"
            )

        except Exception as e:
            logger.error(f"Error updating HTML menu for user {callback.from_user.id}: {e}")
            return False

    async def send_html_temporary_message(
        self,
        message: Message,
        action: str,
        result: Any,
        auto_delete_seconds: int = 7,
        details: Optional[Dict] = None,
        keyboard: Optional[InlineKeyboardMarkup] = None
    ) -> Message:
        """
        Send a temporary HTML-formatted message (usually for confirmations or errors).

        Args:
            message: Original message object
            action: Action that was performed
            result: Result of the action
            auto_delete_seconds: Seconds before auto-deletion
            details: Optional additional details
            keyboard: Optional inline keyboard

        Returns:
            Sent temporary message
        """
        try:
            if HTMLMessageFormatter:
                text = HTMLMessageFormatter.format_confirmation_message(
                    action=action,
                    result=result,
                    auto_delete=True,
                    details=details
                )
                parse_mode = "HTML"
            else:
                # Fallback formatting
                if isinstance(result, bool):
                    status = "✅ Exitoso" if result else "❌ Fallido"
                else:
                    status = "📋 Completado"
                text = f"**{status}**\n{action}"
                if auto_delete_seconds > 0:
                    text += f"\n\n_Se eliminará en {auto_delete_seconds}s_"
                parse_mode = "Markdown"

            # Send temporary message with enhanced cleanup
            sent_message = await self.send_temporary_message(
                message=message,
                text=text,
                keyboard=keyboard,
                auto_delete_seconds=auto_delete_seconds,
                parse_mode=parse_mode
            )

            # Schedule additional cleanup using new method
            if auto_delete_seconds > 0:
                await self.schedule_cleanup(
                    user_id=message.from_user.id,
                    bot=message.bot,
                    delay_seconds=auto_delete_seconds
                )

            return sent_message

        except Exception as e:
            logger.error(f"Error sending HTML temporary message for user {message.from_user.id}: {e}")
            # Fallback to basic temporary message
            return await self.send_temporary_message(
                message=message,
                text=f"Action: {action}",
                keyboard=keyboard,
                auto_delete_seconds=auto_delete_seconds
            )

    def _update_nav_history(self, user_id: int, menu_state: str, parse_mode: str = "Markdown") -> None:
        """Update navigation history for back button functionality."""
        if user_id not in self._nav_history:
            self._nav_history[user_id] = []
        
        history = self._nav_history[user_id]
        
        nav_entry = (menu_state, parse_mode)
        
        # Don't add duplicate consecutive states
        if not history or history[-1] != nav_entry:
            history.append(nav_entry)
            
            # Limit history size to prevent memory issues
            if len(history) > 10: # Keep a reasonable history length
                history.pop(0)
    
    async def _cleanup_temp_messages(self, bot, user_id: int) -> None:
        """Clean up expired temporary messages for a user."""
        temp_msg = self._temp_messages.get(user_id)
        if temp_msg:
            chat_id, msg_id, expire_time = temp_msg
            import time
            if time.time() >= expire_time:
                try:
                    await bot.delete_message(chat_id, msg_id)
                except Exception:
                    pass  # Message might already be deleted or not found
                finally:
                    self._temp_messages.pop(user_id, None)
    
    async def _auto_delete_message(self, bot, user_id: int, delay: int) -> None:
        """Auto-delete a temporary message after delay."""
        await asyncio.sleep(delay)
        await self._cleanup_temp_messages(bot, user_id)

# Global menu manager instance
menu_manager = MenuManager()
