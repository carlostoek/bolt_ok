"""
Servicio centralizado para la gestión de todos los mensajes del sistema.
Implementa patrones de actualización, políticas de auto-eliminación y optimización de recursos.
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
import json

from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from utils.sexy_logger import log
from services.ephemeral_message_service import get_ephemeral_service
from services.inline_button_service import get_inline_button_service

logger = logging.getLogger(__name__)


class MessageCategory(Enum):
    """Categorías de mensajes para aplicar políticas específicas."""
    SYSTEM = "system"               # Mensajes del sistema (comandos, acciones)
    NOTIFICATION = "notification"   # Notificaciones temporales
    ADMIN = "admin"                 # Mensajes de administración
    INTERACTIVE = "interactive"     # Mensajes con botones interactivos
    CONTENT = "content"             # Contenido permanente (respuestas a preguntas)
    ERROR = "error"                 # Mensajes de error
    TUTORIAL = "tutorial"           # Mensajes de tutorial/guía


class MessageManagerService:
    """
    Servicio centralizado para la gestión unificada de mensajes con políticas por categoría.
    
    Features principales:
    - Gestión centralizada de todos los mensajes del sistema
    - Políticas de auto-eliminación configurables por categoría
    - Actualización inteligente de mensajes existentes vs crear nuevos
    - Persistencia selectiva de mensajes importantes
    - Limpieza automática basada en políticas y recursos
    - Historial de mensajes para recuperación y análisis
    """
    
    def __init__(self, bot: Bot, session: Optional[AsyncSession] = None):
        self.bot = bot
        self.session = session
        
        # Servicios dependientes
        self.ephemeral_service = get_ephemeral_service(bot)
        self.button_service = get_inline_button_service(bot, session)
        
        # Registro de mensajes por usuario y categoría
        self.user_messages: Dict[int, Dict[MessageCategory, List[Dict[str, Any]]]] = {}
        
        # Políticas de auto-eliminación por categoría (segundos, 0 = no eliminar)
        self.deletion_policies: Dict[MessageCategory, int] = {
            MessageCategory.SYSTEM: 15,        # 15 segundos
            MessageCategory.NOTIFICATION: 10,  # 10 segundos
            MessageCategory.ADMIN: 0,          # No eliminar
            MessageCategory.INTERACTIVE: 0,    # No eliminar
            MessageCategory.CONTENT: 0,        # No eliminar
            MessageCategory.ERROR: 20,         # 20 segundos
            MessageCategory.TUTORIAL: 60       # 1 minuto
        }
        
        # Límites de mensajes por categoría (0 = sin límite)
        self.message_limits: Dict[MessageCategory, int] = {
            MessageCategory.SYSTEM: 10,        # Máximo 10 mensajes de sistema
            MessageCategory.NOTIFICATION: 5,   # Máximo 5 notificaciones
            MessageCategory.ADMIN: 3,          # Máximo 3 mensajes de admin
            MessageCategory.INTERACTIVE: 15,   # Máximo 15 mensajes interactivos
            MessageCategory.CONTENT: 50,       # Máximo 50 mensajes de contenido
            MessageCategory.ERROR: 3,          # Máximo 3 mensajes de error
            MessageCategory.TUTORIAL: 10       # Máximo 10 tutoriales
        }
        
        # Mensajes anclados por usuario (1 por categoría)
        self.pinned_messages: Dict[int, Dict[MessageCategory, int]] = {}
        
        # Registro de mensajes para actualizar vs crear nuevos
        self.updateable_messages: Dict[int, Dict[str, int]] = {}
        
        # Última limpieza por usuario
        self.last_cleanup: Dict[int, datetime] = {}
        
        # Configuración global
        self.auto_cleanup_interval = 600  # 10 minutos entre limpiezas automáticas
        self.max_messages_per_user = 100  # Límite global por usuario
        
        # Iniciar tarea de mantenimiento
        self._cleanup_task = asyncio.create_task(self._scheduled_maintenance())
        
        log.startup("MessageManagerService inicializado con políticas por categoría")
    
    async def send_message(
        self,
        user_id: int,
        text: str,
        category: MessageCategory,
        parse_mode: str = "HTML",
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        update_key: Optional[str] = None,
        disable_web_page_preview: bool = True,
        disable_notification: bool = False,
        title: Optional[str] = None,
        pin: bool = False
    ) -> Optional[Message]:
        """
        Envía un mensaje aplicando políticas según su categoría.
        
        Args:
            user_id: ID del usuario destinatario
            text: Texto del mensaje
            category: Categoría del mensaje
            parse_mode: Modo de parseo HTML/Markdown
            reply_markup: Markup de teclado inline
            update_key: Clave para actualizar mensaje existente en vez de crear nuevo
            disable_web_page_preview: Desactivar vista previa de enlaces
            disable_notification: Enviar silenciosamente
            title: Título opcional para el mensaje
            pin: Si debe anclarse (1 por categoría)
            
        Returns:
            Mensaje enviado o None si falló
        """
        try:
            # Verificar si debemos actualizar un mensaje existente
            existing_message_id = None
            if update_key and user_id in self.updateable_messages:
                existing_message_id = self.updateable_messages[user_id].get(update_key)
            
            # Si hay mensaje existente, intentar actualizarlo
            if existing_message_id:
                try:
                    await self.bot.edit_message_text(
                        text=text,
                        chat_id=user_id,
                        message_id=existing_message_id,
                        parse_mode=parse_mode,
                        reply_markup=reply_markup,
                        disable_web_page_preview=disable_web_page_preview
                    )
                    
                    # Actualizar registro de mensajes si es necesario
                    self._update_message_in_registry(
                        user_id=user_id,
                        message_id=existing_message_id,
                        category=category,
                        update_key=update_key
                    )
                    
                    log.debug(f"Mensaje actualizado: user_id={user_id}, category={category.value}, key={update_key}")
                    
                    # Obtener mensaje para retornar objeto Message completo
                    try:
                        return await self.bot.get_message(
                            chat_id=user_id,
                            message_id=existing_message_id
                        )
                    except:
                        # Si no podemos obtener el mensaje, al menos retornamos un proxy
                        return self._create_message_proxy(user_id, existing_message_id, text)
                        
                except TelegramBadRequest as e:
                    if "message is not modified" in str(e):
                        # No es un error real, el contenido es idéntico
                        log.debug(f"Mensaje idéntico, no modificado: {existing_message_id}")
                        return self._create_message_proxy(user_id, existing_message_id, text)
                    elif "message to edit not found" in str(e):
                        # Mensaje no encontrado, eliminarlo del registro y continuar para crear uno nuevo
                        self._remove_message_from_registry(user_id, existing_message_id)
                        if user_id in self.updateable_messages and update_key in self.updateable_messages[user_id]:
                            del self.updateable_messages[user_id][update_key]
                    else:
                        log.warning(f"Error editando mensaje {existing_message_id}: {e}")
                except Exception as e:
                    log.warning(f"Error actualizando mensaje existente: {e}")
            
            # Formatear mensaje con título si existe
            formatted_text = text
            if title:
                formatted_text = f"<b>{title}</b>\n\n{text}"
            
            # Para mensajes efímeros, usar servicio especializado
            if category in [MessageCategory.NOTIFICATION, MessageCategory.ERROR, MessageCategory.SYSTEM]:
                auto_delete_seconds = self.deletion_policies[category]
                message = await self.ephemeral_service.send_notification(
                    user_id=user_id,
                    text=formatted_text,
                    parse_mode=parse_mode,
                    auto_delete_seconds=auto_delete_seconds,
                    add_close_button=True,
                    message_type=category.value,
                    buttons=[{"text": btn.text, "callback_data": btn.callback_data} 
                             for row in (reply_markup.inline_keyboard if reply_markup else [])
                             for btn in row],
                    title=None  # Ya formateado arriba
                )
            else:
                # Enviar mensaje normal para categorías persistentes
                message = await self.bot.send_message(
                    chat_id=user_id,
                    text=formatted_text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                    disable_web_page_preview=disable_web_page_preview,
                    disable_notification=disable_notification
                )
            
            if not message:
                return None
                
            # Registrar mensaje enviado
            self._register_new_message(
                user_id=user_id,
                message_id=message.message_id,
                category=category,
                update_key=update_key,
                creation_time=datetime.now()
            )
            
            # Si se especifica una clave de actualización, registrarla
            if update_key:
                if user_id not in self.updateable_messages:
                    self.updateable_messages[user_id] = {}
                self.updateable_messages[user_id][update_key] = message.message_id
            
            # Si debe ser anclado, registrarlo como tal
            if pin:
                self._pin_message(user_id, category, message.message_id)
                
            # Verificar límites y limpiar si es necesario
            await self._check_and_enforce_limits(user_id, category)
            
            return message
            
        except Exception as e:
            log.error(f"Error enviando mensaje a usuario {user_id}: {e}", error=e)
            return None
    
    async def send_or_update(
        self,
        user_id: int,
        text: str,
        update_key: str,
        category: MessageCategory = MessageCategory.CONTENT,
        **kwargs
    ) -> Optional[Message]:
        """
        Envía un mensaje nuevo o actualiza uno existente con la misma clave.
        
        Args:
            user_id: ID del usuario
            text: Texto del mensaje
            update_key: Clave única para identificar el mensaje
            category: Categoría del mensaje
            **kwargs: Argumentos adicionales para send_message
            
        Returns:
            Mensaje enviado/actualizado o None
        """
        return await self.send_message(
            user_id=user_id,
            text=text,
            category=category,
            update_key=update_key,
            **kwargs
        )
    
    async def update_message_text(
        self,
        user_id: int,
        message_id: int,
        new_text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[InlineKeyboardMarkup] = None
    ) -> bool:
        """
        Actualiza el texto de un mensaje específico.
        
        Args:
            user_id: ID del usuario
            message_id: ID del mensaje
            new_text: Nuevo texto
            parse_mode: Modo de parseo
            reply_markup: Nuevo markup o None para mantener
            
        Returns:
            True si se actualizó correctamente, False si falló
        """
        try:
            await self.bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=new_text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
            return True
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                # No es un error real si el contenido es idéntico
                return True
            log.warning(f"Error actualizando texto de mensaje {message_id}: {e}")
            return False
        except Exception as e:
            log.error(f"Error actualizando texto de mensaje {message_id}: {e}", error=e)
            return False
    
    async def delete_message(self, user_id: int, message_id: int) -> bool:
        """
        Elimina un mensaje específico y lo quita de los registros.
        
        Args:
            user_id: ID del usuario
            message_id: ID del mensaje
            
        Returns:
            True si se eliminó correctamente, False si falló
        """
        try:
            await self.bot.delete_message(user_id, message_id)
            # Quitar de todos los registros
            self._remove_message_from_registry(user_id, message_id)
            return True
        except Exception as e:
            log.warning(f"Error eliminando mensaje {message_id}: {e}")
            return False
    
    async def clean_user_messages(
        self,
        user_id: int,
        categories: Optional[List[MessageCategory]] = None,
        keep_pinned: bool = True,
        max_age_minutes: Optional[int] = None
    ) -> int:
        """
        Limpia mensajes de un usuario con filtros específicos.
        
        Args:
            user_id: ID del usuario
            categories: Lista de categorías a limpiar (None = todas)
            keep_pinned: Conservar mensajes anclados
            max_age_minutes: Edad máxima en minutos (None = cualquier edad)
            
        Returns:
            Número de mensajes eliminados
        """
        if user_id not in self.user_messages:
            return 0
        
        deleted_count = 0
        
        # Determinar categorías a limpiar
        cats_to_clean = categories or list(MessageCategory)
        
        # Obtener IDs de mensajes anclados si es necesario
        pinned_ids = set()
        if keep_pinned and user_id in self.pinned_messages:
            pinned_ids = set(self.pinned_messages[user_id].values())
        
        # Obtener tiempo límite si se especifica
        cutoff_time = None
        if max_age_minutes:
            cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        
        # Procesar cada categoría
        for category in cats_to_clean:
            if category not in self.user_messages[user_id]:
                continue
                
            # Filtrar mensajes a eliminar
            messages_to_delete = []
            for msg in self.user_messages[user_id][category]:
                # Filtrar por tiempo si aplica
                if cutoff_time and msg.get("creation_time") and msg["creation_time"] > cutoff_time:
                    continue
                    
                # Filtrar anclados si es necesario
                if keep_pinned and msg["message_id"] in pinned_ids:
                    continue
                    
                messages_to_delete.append(msg)
            
            # Eliminar mensajes filtrados
            for msg in messages_to_delete:
                try:
                    await self.bot.delete_message(user_id, msg["message_id"])
                    deleted_count += 1
                    # Quitar del registro
                    self._remove_message_from_registry(user_id, msg["message_id"])
                except Exception as e:
                    # Solo log, continuar con el siguiente
                    logger.debug(f"Error eliminando mensaje {msg['message_id']}: {e}")
        
        # Actualizar timestamp de limpieza
        self.last_cleanup[user_id] = datetime.now()
        
        log.info(f"Limpiados {deleted_count} mensajes para usuario {user_id}")
        return deleted_count
    
    async def send_admin_panel(
        self,
        user_id: int,
        text: str,
        buttons: List[Dict[str, str]] = None,
        title: str = "Panel de Administración",
        update_key: str = "admin_panel"
    ) -> Optional[Message]:
        """
        Envía o actualiza un panel de administración con botones.
        
        Args:
            user_id: ID del administrador
            text: Texto del panel
            buttons: Lista de botones [{"text": str, "callback_data": str}]
            title: Título del panel
            update_key: Clave para actualización
            
        Returns:
            Mensaje enviado/actualizado o None
        """
        # Construir markup de botones
        markup = None
        if buttons:
            keyboard = []
            row = []
            
            for btn in buttons:
                row.append(InlineKeyboardButton(
                    text=btn["text"],
                    callback_data=btn["callback_data"]
                ))
                
                # Crear filas de máximo 2 botones
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            
            # Añadir última fila si quedaron botones
            if row:
                keyboard.append(row)
                
            # Añadir botón de recargar al final
            refresh_button = InlineKeyboardButton(
                text="🔄 Actualizar",
                callback_data=f"refresh_admin_panel:{update_key}"
            )
            keyboard.append([refresh_button])
            
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        # Enviar como mensaje anclado de categoría ADMIN
        return await self.send_message(
            user_id=user_id,
            text=text,
            category=MessageCategory.ADMIN,
            reply_markup=markup,
            update_key=update_key,
            title=title,
            pin=True  # Anclado
        )
    
    def register_command_handler(self, dp, command_name: str = "clear"):
        """
        Registra el handler para el comando de limpieza manual.
        
        Args:
            dp: Dispatcher de aiogram
            command_name: Nombre del comando (por defecto 'clear')
        """
        from aiogram import Router
        from aiogram.filters import Command
        from aiogram.types import Message as AiogramMessage
        
        router = Router()
        
        @router.message(Command(command_name))
        async def handle_clear_command(message: AiogramMessage):
            user_id = message.from_user.id
            
            # Obtener argumentos opcionales
            args = message.text.split()[1:] if message.text and len(message.text.split()) > 1 else []
            
            # Determinar categorías a limpiar
            categories = None
            keep_pinned = True
            
            if args:
                if "all" in args:
                    # Limpiar todo incluyendo anclados
                    keep_pinned = False
                else:
                    # Limpiar categorías específicas
                    categories = []
                    for arg in args:
                        try:
                            # Intentar convertir argumento a categoría
                            cat = MessageCategory(arg.lower())
                            categories.append(cat)
                        except ValueError:
                            pass
            
            # Ejecutar limpieza
            count = await self.clean_user_messages(
                user_id=user_id,
                categories=categories,
                keep_pinned=keep_pinned
            )
            
            # Enviar confirmación
            await self.ephemeral_service.send_success(
                user_id=user_id,
                text=f"Se han eliminado {count} mensajes de tu chat.",
                auto_delete_seconds=5
            )
        
        # Incluir el router en el dispatcher
        dp.include_router(router)
        log.info(f"Registrado handler para comando /{command_name}")
    
    def get_message_counts(self, user_id: int) -> Dict[str, int]:
        """
        Obtiene conteo de mensajes por categoría para un usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Diccionario {categoría: conteo}
        """
        if user_id not in self.user_messages:
            return {}
            
        return {
            cat.value: len(msgs) 
            for cat, msgs in self.user_messages[user_id].items()
        }
    
    def set_deletion_policy(self, category: MessageCategory, seconds: int) -> None:
        """
        Configura la política de auto-eliminación para una categoría.
        
        Args:
            category: Categoría de mensaje
            seconds: Segundos hasta eliminación (0 = no eliminar)
        """
        self.deletion_policies[category] = max(0, seconds)
    
    def set_message_limit(self, category: MessageCategory, limit: int) -> None:
        """
        Configura el límite de mensajes para una categoría.
        
        Args:
            category: Categoría de mensaje
            limit: Número máximo (0 = sin límite)
        """
        self.message_limits[category] = max(0, limit)
    
    # Métodos privados auxiliares
    
    def _register_new_message(
        self,
        user_id: int,
        message_id: int,
        category: MessageCategory,
        update_key: Optional[str] = None,
        creation_time: Optional[datetime] = None
    ) -> None:
        """Registra un nuevo mensaje en el sistema de seguimiento."""
        # Inicializar estructura si no existe
        if user_id not in self.user_messages:
            self.user_messages[user_id] = {}
        
        if category not in self.user_messages[user_id]:
            self.user_messages[user_id][category] = []
        
        # Crear registro de mensaje
        message_data = {
            "message_id": message_id,
            "category": category,
            "update_key": update_key,
            "creation_time": creation_time or datetime.now()
        }
        
        # Añadir a la lista de mensajes
        self.user_messages[user_id][category].append(message_data)
    
    def _update_message_in_registry(
        self,
        user_id: int,
        message_id: int,
        category: MessageCategory,
        update_key: Optional[str] = None
    ) -> None:
        """Actualiza un mensaje existente en el registro."""
        if user_id not in self.user_messages:
            return
            
        # Buscar el mensaje en todas las categorías
        found = False
        for cat, messages in self.user_messages[user_id].items():
            for i, msg in enumerate(messages):
                if msg["message_id"] == message_id:
                    # Actualizar datos si es necesario
                    if cat != category:
                        # Mover a categoría correcta
                        self.user_messages[user_id][cat].pop(i)
                        if category not in self.user_messages[user_id]:
                            self.user_messages[user_id][category] = []
                        self.user_messages[user_id][category].append(msg)
                        msg["category"] = category
                    
                    # Actualizar clave si es necesario
                    if update_key:
                        msg["update_key"] = update_key
                    
                    found = True
                    break
            if found:
                break
        
        # Si no se encontró, registrarlo como nuevo
        if not found:
            self._register_new_message(user_id, message_id, category, update_key)
    
    def _remove_message_from_registry(self, user_id: int, message_id: int) -> None:
        """Elimina un mensaje de todos los registros."""
        if user_id not in self.user_messages:
            return
            
        # Buscar y eliminar de registros de mensajes
        for cat in list(self.user_messages[user_id].keys()):
            self.user_messages[user_id][cat] = [
                msg for msg in self.user_messages[user_id][cat] 
                if msg["message_id"] != message_id
            ]
        
        # Eliminar de registros de actualización
        if user_id in self.updateable_messages:
            keys_to_remove = []
            for key, mid in self.updateable_messages[user_id].items():
                if mid == message_id:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.updateable_messages[user_id][key]
        
        # Eliminar de mensajes anclados
        if user_id in self.pinned_messages:
            cats_to_remove = []
            for cat, mid in self.pinned_messages[user_id].items():
                if mid == message_id:
                    cats_to_remove.append(cat)
            
            for cat in cats_to_remove:
                del self.pinned_messages[user_id][cat]
    
    def _pin_message(self, user_id: int, category: MessageCategory, message_id: int) -> None:
        """Registra un mensaje como anclado para su categoría."""
        if user_id not in self.pinned_messages:
            self.pinned_messages[user_id] = {}
            
        # Si ya hay un mensaje anclado para esta categoría, borrarlo del registro
        if category in self.pinned_messages[user_id]:
            old_message_id = self.pinned_messages[user_id][category]
            if old_message_id != message_id:
                # No borrar físicamente, solo actualizar registro
                pass
        
        # Actualizar registro de anclaje
        self.pinned_messages[user_id][category] = message_id
    
    async def _check_and_enforce_limits(self, user_id: int, category: MessageCategory) -> None:
        """Verifica y aplica límites de mensajes por categoría."""
        if user_id not in self.user_messages or category not in self.user_messages[user_id]:
            return
            
        # Obtener límite para esta categoría
        limit = self.message_limits.get(category, 0)
        if limit <= 0:
            return  # Sin límite
            
        # Verificar si excedemos el límite
        messages = self.user_messages[user_id][category]
        if len(messages) <= limit:
            return  # Dentro del límite
            
        # Determinar cuántos eliminar
        to_delete = len(messages) - limit
        
        # Ordenar por antigüedad (más antiguos primero)
        messages.sort(key=lambda x: x.get("creation_time", datetime.min))
        
        # Obtener IDs de mensajes anclados para no eliminarlos
        pinned_ids = set()
        if user_id in self.pinned_messages:
            pinned_ids = set(self.pinned_messages[user_id].values())
        
        # Eliminar mensajes excedentes, respetando anclados
        deleted = 0
        for i, msg in enumerate(messages[:]):
            if deleted >= to_delete:
                break
                
            # No eliminar mensajes anclados
            if msg["message_id"] in pinned_ids:
                continue
                
            # Intentar eliminar
            try:
                await self.bot.delete_message(user_id, msg["message_id"])
                # Quitar del registro
                messages.remove(msg)
                deleted += 1
            except Exception as e:
                # Solo log, continuar con el siguiente
                logger.debug(f"Error al aplicar límite para mensaje {msg['message_id']}: {e}")
                # Quitar del registro aunque falle la eliminación física
                messages.remove(msg)
                deleted += 1
        
        if deleted > 0:
            log.debug(f"Límite aplicado: {deleted} mensajes eliminados para usuario {user_id}, categoría {category.value}")
    
    async def _scheduled_maintenance(self) -> None:
        """Tarea de mantenimiento periódico que se ejecuta automáticamente."""
        try:
            while True:
                await asyncio.sleep(120)  # Ejecutar cada 2 minutos
                await self._cleanup_old_messages()
                
        except asyncio.CancelledError:
            log.info("Tarea de mantenimiento de mensajes cancelada")
        except Exception as e:
            log.error(f"Error en tarea de mantenimiento de mensajes: {e}", error=e)
    
    async def _cleanup_old_messages(self) -> None:
        """Limpia mensajes antiguos según políticas configuradas."""
        now = datetime.now()
        
        for user_id in list(self.user_messages.keys()):
            # Verificar si corresponde limpieza automática
            if user_id in self.last_cleanup:
                time_since_cleanup = (now - self.last_cleanup[user_id]).total_seconds()
                if time_since_cleanup < self.auto_cleanup_interval:
                    continue  # Aún no es tiempo
            
            # Limpiar mensajes por categoría según políticas
            for category, seconds in self.deletion_policies.items():
                if seconds <= 0:
                    continue  # Sin auto-eliminación
                    
                if category not in self.user_messages.get(user_id, {}):
                    continue  # No hay mensajes de esta categoría
                
                # Calcular tiempo límite
                cutoff_time = now - timedelta(seconds=seconds)
                
                # Filtrar mensajes antiguos
                old_messages = [
                    msg for msg in self.user_messages[user_id][category]
                    if msg.get("creation_time") and msg["creation_time"] < cutoff_time
                ]
                
                # Obtener IDs de mensajes anclados
                pinned_ids = set()
                if user_id in self.pinned_messages:
                    pinned_ids = set(self.pinned_messages[user_id].values())
                
                # Eliminar mensajes antiguos, respetando anclados
                for msg in old_messages:
                    if msg["message_id"] in pinned_ids:
                        continue  # No eliminar anclados
                        
                    try:
                        await self.bot.delete_message(user_id, msg["message_id"])
                        # Quitar del registro
                        self._remove_message_from_registry(user_id, msg["message_id"])
                    except Exception as e:
                        # Solo log, continuar con el siguiente
                        logger.debug(f"Error en limpieza automática mensaje {msg['message_id']}: {e}")
                        # Quitar del registro aunque falle la eliminación física
                        self._remove_message_from_registry(user_id, msg["message_id"])
            
            # Actualizar timestamp de limpieza
            self.last_cleanup[user_id] = now
    
    def _create_message_proxy(self, chat_id: int, message_id: int, text: str) -> Message:
        """Crea un objeto Message simplificado para cuando no podemos obtener el original."""
        class MessageProxy:
            def __init__(self, chat_id, message_id, text):
                self.chat = type('obj', (object,), {'id': chat_id})
                self.message_id = message_id
                self.text = text
                
        return MessageProxy(chat_id, message_id, text)


# Singleton para acceso global
_message_manager = None

def get_message_manager(bot: Bot = None, session: AsyncSession = None) -> Optional[MessageManagerService]:
    """
    Obtiene la instancia global del gestor centralizado de mensajes.
    
    Args:
        bot: Instancia del bot (requerida para inicialización)
        session: Sesión de base de datos (opcional)
        
    Returns:
        Instancia del servicio o None si no está inicializado
    """
    global _message_manager
    
    if _message_manager is None and bot is not None:
        _message_manager = MessageManagerService(bot, session)
        log.startup("MessageManagerService inicializado como singleton")
        
    return _message_manager