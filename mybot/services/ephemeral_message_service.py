"""
Servicio para gestionar mensajes efímeros y notificaciones temporales.
Implementa un sistema de mensajes con auto-eliminación, interactividad y monitoreo.
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from utils.sexy_logger import log

logger = logging.getLogger(__name__)


class EphemeralMessageService:
    """
    Servicio para gestionar mensajes que se auto-eliminan con interactividad mejorada.
    
    Features principales:
    - Envío de notificaciones con auto-eliminación configurable
    - Botones interactivos personalizables (cerrar, ver detalles, etc.)
    - Limpieza de mensajes por usuario o tipo
    - Gestión eficiente de recursos con eliminación automática
    - Soporte para persistencia (opcional) de mensajes importantes
    - Integración con sistema de notificaciones centralizado
    """
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.active_messages: Dict[int, List[Dict[str, Any]]] = {}  # user_id -> [message_data]
        self.message_types: Dict[str, Dict[str, Any]] = {
            "system": {"auto_delete_seconds": 15, "add_close_button": True},
            "notification": {"auto_delete_seconds": 10, "add_close_button": True},
            "error": {"auto_delete_seconds": 20, "add_close_button": True},
            "success": {"auto_delete_seconds": 8, "add_close_button": True},
            "admin": {"auto_delete_seconds": 0, "add_close_button": True},  # Sin auto-eliminación
        }
        self.pinned_admin_messages: Dict[int, int] = {}  # user_id -> message_id
        
        # Iniciar tareas de mantenimiento automático
        self._cleanup_task = asyncio.create_task(self._scheduled_cleanup())
        log.startup("EphemeralMessageService inicializado con limpieza automática")
        
    async def send_notification(
        self,
        user_id: int,
        text: str,
        parse_mode: str = "HTML",
        auto_delete_seconds: int = 10, 
        add_close_button: bool = True,
        message_type: str = "notification",
        buttons: Optional[List[Dict[str, Any]]] = None,
        title: Optional[str] = None
    ) -> Optional[Message]:
        """
        Envía una notificación que se auto-elimina con botones interactivos personalizados.
        
        Args:
            user_id: ID del usuario de Telegram
            text: Texto del mensaje
            parse_mode: Modo de parseo HTML/Markdown
            auto_delete_seconds: Segundos hasta auto-eliminación (0 = sin eliminar)
            add_close_button: Añadir botón de cerrar
            message_type: Tipo de mensaje (system, notification, error, success, admin)
            buttons: Lista de botones adicionales [{"text": str, "callback_data": str}]
            title: Título opcional para el mensaje (se añade en negrita al inicio)
            
        Returns:
            Objeto Message si se envió correctamente, None en caso contrario
        """
        try:
            # Aplicar configuración predeterminada según el tipo
            if message_type in self.message_types:
                type_config = self.message_types[message_type]
                # Solo sobreescribir si no se especifica explícitamente
                if auto_delete_seconds == 10:  # Valor por defecto
                    auto_delete_seconds = type_config["auto_delete_seconds"]
                if add_close_button == True:  # Valor por defecto
                    add_close_button = type_config["add_close_button"]
            
            # Formatear mensaje con título si existe
            formatted_text = text
            if title:
                formatted_text = f"<b>{title}</b>\n\n{text}"
            
            # Crear markup con botones personalizados y de cierre
            markup = None
            if buttons or add_close_button:
                keyboard_buttons = []
                
                # Añadir botones personalizados
                if buttons:
                    custom_row = []
                    for btn in buttons:
                        custom_row.append(InlineKeyboardButton(
                            text=btn["text"], 
                            callback_data=btn["callback_data"]
                        ))
                        # Crear filas de máximo 2 botones
                        if len(custom_row) == 2:
                            keyboard_buttons.append(custom_row)
                            custom_row = []
                    # Añadir última fila si quedaron botones
                    if custom_row:
                        keyboard_buttons.append(custom_row)
                
                # Añadir botón de cerrar
                if add_close_button:
                    close_button = InlineKeyboardButton(
                        text="❌ Cerrar", 
                        callback_data=f"close_notification:{message_type}"
                    )
                    keyboard_buttons.append([close_button])
                
                markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            
            # Enviar mensaje
            message = await self.bot.send_message(
                chat_id=user_id,
                text=formatted_text,
                parse_mode=parse_mode,
                reply_markup=markup
            )
            
            # Registrar mensaje para seguimiento
            self._register_message(
                user_id=user_id,
                message_id=message.message_id,
                delete_at=time.time() + auto_delete_seconds if auto_delete_seconds > 0 else None,
                message_type=message_type
            )
            
            # Si es mensaje de admin y está configurado para pinear, gestionar mensaje anclado
            if message_type == "admin" and self.message_types["admin"].get("pin_message", False):
                await self._manage_pinned_admin_message(user_id, message.message_id)
            
            # Programar eliminación si corresponde
            if auto_delete_seconds > 0:
                asyncio.create_task(self._schedule_deletion(
                    user_id, message.message_id, auto_delete_seconds
                ))
            
            log.debug(f"Mensaje efímero enviado al usuario {user_id}: tipo={message_type}, auto_delete={auto_delete_seconds}s")
            return message
            
        except Exception as e:
            log.error(f"Error enviando mensaje efímero a usuario {user_id}: {e}", error=e)
            return None
    
    async def send_error(
        self, 
        user_id: int, 
        text: str, 
        auto_delete_seconds: int = 20
    ) -> Optional[Message]:
        """
        Envía un mensaje de error formateado con estilo distintivo.
        
        Args:
            user_id: ID del usuario
            text: Texto del error
            auto_delete_seconds: Tiempo hasta auto-eliminación
            
        Returns:
            Mensaje enviado o None
        """
        formatted_text = f"⚠️ <b>Error</b>\n\n{text}"
        return await self.send_notification(
            user_id=user_id,
            text=formatted_text,
            auto_delete_seconds=auto_delete_seconds,
            message_type="error"
        )
    
    async def send_success(
        self, 
        user_id: int, 
        text: str, 
        auto_delete_seconds: int = 8
    ) -> Optional[Message]:
        """
        Envía un mensaje de éxito formateado con estilo distintivo.
        
        Args:
            user_id: ID del usuario
            text: Texto del mensaje de éxito
            auto_delete_seconds: Tiempo hasta auto-eliminación
            
        Returns:
            Mensaje enviado o None
        """
        formatted_text = f"✅ <b>Completado</b>\n\n{text}"
        return await self.send_notification(
            user_id=user_id,
            text=formatted_text,
            auto_delete_seconds=auto_delete_seconds,
            message_type="success"
        )
    
    async def send_admin_message(
        self, 
        user_id: int, 
        text: str, 
        buttons: Optional[List[Dict[str, Any]]] = None,
        title: str = "Panel de Administración",
        replace_existing: bool = True
    ) -> Optional[Message]:
        """
        Envía un mensaje administrativo anclado que reemplaza al anterior.
        
        Args:
            user_id: ID del usuario administrador
            text: Texto del panel de administración
            buttons: Botones de acción para el panel
            title: Título del panel
            replace_existing: Si True, elimina el panel anterior
            
        Returns:
            Mensaje enviado o None
        """
        # Si hay un mensaje de admin previo y se solicita reemplazar, eliminarlo
        if replace_existing and user_id in self.pinned_admin_messages:
            await self.delete_message(user_id, self.pinned_admin_messages[user_id])
        
        # Enviar nuevo mensaje de admin sin auto-eliminación
        message = await self.send_notification(
            user_id=user_id,
            text=text,
            title=title,
            auto_delete_seconds=0,  # Sin auto-eliminación
            message_type="admin",
            buttons=buttons
        )
        
        # Registrar como mensaje anclado
        if message:
            self.pinned_admin_messages[user_id] = message.message_id
            
        return message
    
    async def update_message(
        self,
        user_id: int,
        message_id: int,
        new_text: str,
        parse_mode: str = "HTML",
        new_markup: Optional[InlineKeyboardMarkup] = None
    ) -> bool:
        """
        Actualiza un mensaje existente en lugar de crear uno nuevo.
        
        Args:
            user_id: ID del usuario
            message_id: ID del mensaje a actualizar
            new_text: Nuevo texto del mensaje
            parse_mode: Modo de parseo
            new_markup: Nuevo markup de teclado o None para mantener
            
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        try:
            # Verificar si tenemos el mensaje registrado
            message_data = self._find_message(user_id, message_id)
            
            if not message_data:
                log.warning(f"Intento de actualizar mensaje no registrado: user_id={user_id}, message_id={message_id}")
            
            # Intentar actualizar el mensaje
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=new_text,
                parse_mode=parse_mode,
                reply_markup=new_markup
            )
            
            log.debug(f"Mensaje actualizado: user_id={user_id}, message_id={message_id}")
            return True
            
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                # No es un error real si el contenido es idéntico
                return True
            log.error(f"Error actualizando mensaje {message_id} para usuario {user_id}: {e}")
            return False
        except Exception as e:
            log.error(f"Error actualizando mensaje {message_id} para usuario {user_id}: {e}", error=e)
            return False
    
    async def clean_user_chat(
        self, 
        user_id: int, 
        keep_last_n: int = 0,
        message_types: Optional[List[str]] = None
    ) -> int:
        """
        Limpia mensajes del sistema para un usuario con filtrado por tipo.
        
        Args:
            user_id: ID del usuario
            keep_last_n: Número de mensajes recientes a conservar
            message_types: Lista de tipos de mensajes a eliminar, None para todos
            
        Returns:
            Número de mensajes eliminados
        """
        if user_id not in self.active_messages:
            return 0
        
        # Filtrar por tipo si se especifica
        messages_to_process = self.active_messages[user_id]
        if message_types:
            messages_to_process = [
                msg for msg in messages_to_process 
                if msg.get("message_type") in message_types
            ]
        
        # Determinar qué mensajes eliminar respetando keep_last_n
        messages_to_delete = messages_to_process[:-keep_last_n] if keep_last_n > 0 else messages_to_process
        
        deleted_count = 0
        # Eliminar mensajes
        for msg_data in messages_to_delete:
            try:
                await self.bot.delete_message(user_id, msg_data["message_id"])
                self._remove_message(user_id, msg_data["message_id"])
                deleted_count += 1
            except Exception as e:
                log.warning(f"Error al limpiar mensaje {msg_data['message_id']}: {e}")
        
        log.info(f"Limpiados {deleted_count} mensajes para usuario {user_id}")
        return deleted_count
    
    async def delete_message(self, user_id: int, message_id: int) -> bool:
        """
        Elimina un mensaje específico y lo quita del registro.
        
        Args:
            user_id: ID del usuario
            message_id: ID del mensaje a eliminar
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            await self.bot.delete_message(user_id, message_id)
            self._remove_message(user_id, message_id)
            
            # Si era un mensaje anclado de admin, actualizar registro
            if user_id in self.pinned_admin_messages and self.pinned_admin_messages[user_id] == message_id:
                del self.pinned_admin_messages[user_id]
                
            return True
        except Exception as e:
            log.warning(f"Error eliminando mensaje {message_id} para usuario {user_id}: {e}")
            return False
    
    async def clear_all_messages(self) -> int:
        """
        Limpia todos los mensajes registrados en el sistema.
        Útil para reinicios o mantenimiento.
        
        Returns:
            Número total de mensajes eliminados
        """
        total_deleted = 0
        
        for user_id in list(self.active_messages.keys()):
            deleted = await self.clean_user_chat(user_id)
            total_deleted += deleted
        
        log.info(f"Limpieza completa: {total_deleted} mensajes eliminados")
        return total_deleted
    
    # Métodos auxiliares privados
    
    def _register_message(
        self, 
        user_id: int, 
        message_id: int, 
        delete_at: Optional[float] = None,
        message_type: str = "notification"
    ) -> None:
        """Registra un mensaje en el sistema de seguimiento."""
        if user_id not in self.active_messages:
            self.active_messages[user_id] = []
        
        self.active_messages[user_id].append({
            "message_id": message_id,
            "delete_at": delete_at,
            "message_type": message_type,
            "created_at": time.time()
        })
    
    def _remove_message(self, user_id: int, message_id: int) -> None:
        """Elimina un mensaje del registro de seguimiento."""
        if user_id in self.active_messages:
            self.active_messages[user_id] = [
                msg for msg in self.active_messages[user_id] 
                if msg["message_id"] != message_id
            ]
    
    def _find_message(self, user_id: int, message_id: int) -> Optional[Dict[str, Any]]:
        """Busca y retorna los datos de un mensaje específico."""
        if user_id in self.active_messages:
            for msg in self.active_messages[user_id]:
                if msg["message_id"] == message_id:
                    return msg
        return None
    
    async def _schedule_deletion(self, user_id: int, message_id: int, delay_seconds: int) -> None:
        """Programa la eliminación de un mensaje después de un retraso."""
        try:
            await asyncio.sleep(delay_seconds)
            # Verificar si el mensaje aún existe en nuestro registro
            message_data = self._find_message(user_id, message_id)
            if not message_data:
                return  # El mensaje ya fue eliminado manualmente
                
            # Intentar eliminar el mensaje
            await self.delete_message(user_id, message_id)
            
        except asyncio.CancelledError:
            # Tarea cancelada, ignorar
            pass
        except Exception as e:
            log.warning(f"Error en eliminación programada para mensaje {message_id}: {e}")
    
    async def _scheduled_cleanup(self) -> None:
        """Tarea de limpieza automática que se ejecuta periódicamente."""
        try:
            while True:
                await asyncio.sleep(60)  # Ejecutar cada minuto
                await self._cleanup_expired_messages()
        except asyncio.CancelledError:
            # Tarea cancelada durante apagado
            log.info("Tarea de limpieza cancelada")
        except Exception as e:
            log.error(f"Error en tarea de limpieza programada: {e}", error=e)
    
    async def _cleanup_expired_messages(self) -> None:
        """Elimina mensajes que han alcanzado su tiempo de expiración."""
        now = time.time()
        total_cleaned = 0
        
        for user_id in list(self.active_messages.keys()):
            expired_messages = [
                msg for msg in self.active_messages[user_id]
                if msg.get("delete_at") and msg["delete_at"] <= now
            ]
            
            for msg in expired_messages:
                try:
                    await self.bot.delete_message(user_id, msg["message_id"])
                    self._remove_message(user_id, msg["message_id"])
                    total_cleaned += 1
                except Exception as e:
                    # Solo registrar y continuar con el siguiente
                    self._remove_message(user_id, msg["message_id"])
                    logger.debug(f"Error limpiando mensaje expirado {msg['message_id']}: {e}")
        
        if total_cleaned > 0:
            log.debug(f"Limpieza automática: {total_cleaned} mensajes expirados eliminados")
    
    async def _manage_pinned_admin_message(self, user_id: int, message_id: int) -> None:
        """Gestiona el mensaje anclado de administrador, eliminando el anterior si existe."""
        if user_id in self.pinned_admin_messages:
            old_message_id = self.pinned_admin_messages[user_id]
            if old_message_id != message_id:
                try:
                    await self.bot.delete_message(user_id, old_message_id)
                    self._remove_message(user_id, old_message_id)
                except Exception as e:
                    logger.debug(f"No se pudo eliminar mensaje admin anterior: {e}")
        
        # Actualizar referencia al mensaje anclado actual
        self.pinned_admin_messages[user_id] = message_id


# Handler para callback de botones de cierre
async def register_close_notification_handler(dp, bot):
    """
    Registra el handler para manejar botones de cierre de notificaciones.
    
    Args:
        dp: Dispatcher de aiogram
        bot: Instancia del bot
    """
    from aiogram import F, Router
    from aiogram.types import CallbackQuery
    
    router = Router()
    
    @router.callback_query(F.data.startswith("close_notification"))
    async def handle_close_button(callback: CallbackQuery):
        try:
            # Extraer tipo de mensaje si está presente
            message_type = "notification"
            if ":" in callback.data:
                _, message_type = callback.data.split(":", 1)
            
            # Eliminar el mensaje directamente
            await bot.delete_message(
                chat_id=callback.from_user.id,
                message_id=callback.message.message_id
            )
            
            # Responder al callback para evitar el indicador de carga
            await callback.answer(
                text="Mensaje cerrado",
                show_alert=False
            )
            
            logger.debug(f"Mensaje cerrado por usuario {callback.from_user.id}: tipo={message_type}")
            
        except Exception as e:
            logger.error(f"Error manejando botón de cierre: {e}")
            await callback.answer(
                text="No se pudo cerrar el mensaje",
                show_alert=True
            )
    
    # Incluir el router en el dispatcher
    dp.include_router(router)


# Singleton para acceso global
_ephemeral_service = None

def get_ephemeral_service(bot: Bot = None) -> Optional[EphemeralMessageService]:
    """
    Obtiene la instancia global del servicio de mensajes efímeros.
    
    Args:
        bot: Instancia del bot (requerida para inicialización)
        
    Returns:
        Instancia del servicio o None si no está inicializado
    """
    global _ephemeral_service
    
    if _ephemeral_service is None and bot is not None:
        _ephemeral_service = EphemeralMessageService(bot)
        log.startup("EphemeralMessageService inicializado como singleton")
        
    return _ephemeral_service