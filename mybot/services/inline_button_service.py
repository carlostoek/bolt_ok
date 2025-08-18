"""
Servicio para gestionar actualizaciones de botones inline con manejo avanzado de errores.
Implementa sistema de reintentos y monitoreo para botones interactivos.
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
import random

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from utils.sexy_logger import log

logger = logging.getLogger(__name__)


class InlineButtonService:
    """
    Servicio especializado en la gestión de botones inline con contadores, 
    optimizado para actualizaciones frecuentes y manejo robusto de errores.
    
    Features principales:
    - Actualización de contadores en botones inline con cache inteligente
    - Sistema de reintentos con backoff exponencial para operaciones fallidas
    - Manejo de rate limiting de Telegram con espera inteligente
    - Caché de actualizaciones para evitar llamadas innecesarias a la API
    - Monitoreo detallado de operaciones para identificar problemas
    - Compatibilidad con diferentes tipos de markup y estructuras de botones
    """
    
    def __init__(self, bot: Bot, session: Optional[AsyncSession] = None):
        self.bot = bot
        self.session = session
        
        # Caché de estados de botones para evitar actualizaciones innecesarias
        self.button_states: Dict[Tuple[int, int], Dict[str, Any]] = {}
        
        # Registro de reintentos para implementar backoff exponencial
        self.retry_counts: Dict[Tuple[int, int], int] = {}
        
        # Caché de markup para reconstrucción eficiente
        self.markup_cache: Dict[Tuple[int, int], Dict[str, Any]] = {}
        
        # Rate limiting y cooldowns
        self.update_cooldowns: Dict[Tuple[int, int], float] = {}
        self.min_update_interval = 1.0  # segundos entre actualizaciones del mismo mensaje
        
        # Métricas
        self.metrics = {
            "updates_requested": 0,
            "updates_skipped": 0,
            "updates_succeeded": 0,
            "updates_failed": 0,
            "retries_performed": 0,
            "rate_limited": 0
        }
        
        log.startup("InlineButtonService inicializado con caché y sistema de reintentos")
    
    async def update_counter_buttons(
        self,
        chat_id: Union[int, str],
        message_id: int,
        counters: Dict[str, int],
        button_prefix: str = "",
        markup_generator: Optional[Callable] = None,
        force_update: bool = False,
        max_retries: int = 2
    ) -> bool:
        """
        Actualiza los contadores en botones inline de forma robusta y eficiente.
        
        Args:
            chat_id: ID del chat donde está el mensaje
            message_id: ID del mensaje a actualizar
            counters: Diccionario de contadores {key: count}
            button_prefix: Prefijo para identificar botones de contador
            markup_generator: Función opcional para generar markup personalizado
            force_update: Forzar actualización aunque no haya cambios
            max_retries: Número máximo de reintentos en caso de error
            
        Returns:
            True si la actualización fue exitosa o no necesaria, False si falló
        """
        try:
            # Convertir chat_id a entero para consistencia
            if isinstance(chat_id, str):
                chat_id = int(chat_id)
            
            # Clave única para este mensaje
            message_key = (chat_id, message_id)
            self.metrics["updates_requested"] += 1
            
            # Verificar cooldown para evitar rate limiting
            if not force_update and message_key in self.update_cooldowns:
                time_since_last = time.time() - self.update_cooldowns[message_key]
                if time_since_last < self.min_update_interval:
                    wait_time = self.min_update_interval - time_since_last
                    # Si estamos en cooldown, esperar antes de continuar
                    self.metrics["rate_limited"] += 1
                    await asyncio.sleep(wait_time)
                    log.debug(f"Esperando {wait_time:.2f}s por cooldown para mensaje {message_id}")
            
            # Actualizar timestamp de última actualización
            self.update_cooldowns[message_key] = time.time()
            
            # Verificar si hay cambios reales en los contadores
            current_state = self.button_states.get(message_key, {})
            has_changes = current_state != counters
            
            # Si no hay cambios y no se fuerza actualización, omitir
            if not has_changes and not force_update and current_state:
                self.metrics["updates_skipped"] += 1
                log.debug(f"No hay cambios en contadores para mensaje {message_id}, omitiendo actualización")
                return True
            
            # Determinar función de generación de markup
            markup_func = markup_generator or self._generate_default_markup
            
            # Generar markup con los nuevos contadores
            try:
                new_markup = await markup_func(counters, button_prefix)
            except Exception as e:
                log.error(f"Error generando markup para mensaje {message_id}: {e}", error=e)
                return False
            
            # Intentar actualizar el markup con reintentos
            success = await self._update_markup_with_retry(
                chat_id=chat_id,
                message_id=message_id,
                new_markup=new_markup,
                max_retries=max_retries
            )
            
            if success:
                # Actualizar caché solo si la operación fue exitosa
                self.button_states[message_key] = counters.copy()
                # Guardar copia del markup para posible reconstrucción
                self.markup_cache[message_key] = {
                    "markup": new_markup,
                    "updated_at": time.time()
                }
                self.metrics["updates_succeeded"] += 1
                # Reset contador de reintentos tras éxito
                if message_key in self.retry_counts:
                    del self.retry_counts[message_key]
                return True
            else:
                self.metrics["updates_failed"] += 1
                return False
                
        except Exception as e:
            log.error(f"Error inesperado actualizando botones para mensaje {message_id}: {e}", error=e)
            self.metrics["updates_failed"] += 1
            return False
    
    async def increment_counter(
        self,
        chat_id: Union[int, str],
        message_id: int,
        counter_key: str,
        increment: int = 1,
        button_prefix: str = "",
        markup_generator: Optional[Callable] = None
    ) -> bool:
        """
        Incrementa un contador específico en un botón inline.
        
        Args:
            chat_id: ID del chat
            message_id: ID del mensaje
            counter_key: Clave del contador a incrementar
            increment: Valor a sumar (puede ser negativo)
            button_prefix: Prefijo para identificar botones
            markup_generator: Función para generar markup personalizado
            
        Returns:
            True si la actualización fue exitosa, False si falló
        """
        # Convertir chat_id a entero
        if isinstance(chat_id, str):
            chat_id = int(chat_id)
            
        message_key = (chat_id, message_id)
        
        # Obtener estado actual o inicializar vacío
        current_state = self.button_states.get(message_key, {})
        
        # Inicializar contador si no existe
        if counter_key not in current_state:
            current_state[counter_key] = 0
            
        # Incrementar contador
        current_state[counter_key] += increment
        
        # Asegurar que no sea negativo
        if current_state[counter_key] < 0:
            current_state[counter_key] = 0
            
        # Actualizar botones con el nuevo contador
        return await self.update_counter_buttons(
            chat_id=chat_id,
            message_id=message_id,
            counters=current_state,
            button_prefix=button_prefix,
            markup_generator=markup_generator,
            force_update=True  # Forzar actualización aunque el incremento sea 0
        )
    
    async def replace_button_text(
        self,
        chat_id: Union[int, str],
        message_id: int,
        button_callback_data: str,
        new_text: str,
        preserve_counter: bool = True
    ) -> bool:
        """
        Reemplaza el texto de un botón específico manteniendo su callback_data.
        
        Args:
            chat_id: ID del chat
            message_id: ID del mensaje
            button_callback_data: callback_data para identificar el botón
            new_text: Nuevo texto para el botón
            preserve_counter: Si True, preserva contador en el texto
            
        Returns:
            True si la actualización fue exitosa, False si falló
        """
        try:
            # Obtener markup actual
            message = await self.bot.get_message(
                chat_id=chat_id,
                message_id=message_id
            )
            
            if not message or not message.reply_markup:
                log.warning(f"No se encontró markup para mensaje {message_id}")
                return False
                
            # Clonar estructura de teclado
            keyboard = []
            button_found = False
            
            # Recorrer filas y botones
            for row in message.reply_markup.inline_keyboard:
                new_row = []
                for button in row:
                    if button.callback_data == button_callback_data:
                        # Encontramos el botón a modificar
                        modified_text = new_text
                        # Si hay contador y se debe preservar, extraerlo y reintegrarlo
                        if preserve_counter and "(" in button.text and ")" in button.text:
                            counter_part = button.text[button.text.rfind("("):]
                            modified_text = f"{new_text} {counter_part}"
                            
                        new_button = InlineKeyboardButton(
                            text=modified_text,
                            callback_data=button.callback_data
                        )
                        new_row.append(new_button)
                        button_found = True
                    else:
                        # Mantener botón sin cambios
                        new_row.append(button)
                keyboard.append(new_row)
            
            if not button_found:
                log.warning(f"No se encontró botón con callback_data {button_callback_data}")
                return False
                
            # Crear nuevo markup
            new_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            
            # Actualizar mensaje
            return await self._update_markup_with_retry(
                chat_id=chat_id,
                message_id=message_id,
                new_markup=new_markup
            )
            
        except Exception as e:
            log.error(f"Error reemplazando texto de botón: {e}", error=e)
            return False
    
    async def add_or_update_button(
        self,
        chat_id: Union[int, str],
        message_id: int,
        button_data: Dict[str, Any],
        row_index: int = -1  # -1 para añadir en nueva fila al final
    ) -> bool:
        """
        Añade o actualiza un botón en un mensaje existente.
        
        Args:
            chat_id: ID del chat
            message_id: ID del mensaje
            button_data: Datos del botón {text, callback_data}
            row_index: Índice de fila (-1 para nueva fila al final)
            
        Returns:
            True si la operación fue exitosa, False si falló
        """
        try:
            # Obtener markup actual
            message = await self.bot.get_message(
                chat_id=chat_id,
                message_id=message_id
            )
            
            if not message:
                log.warning(f"No se encontró mensaje {message_id}")
                return False
                
            # Inicializar nuevo teclado
            keyboard = []
            button_updated = False
            
            # Crear nuevo botón
            new_button = InlineKeyboardButton(
                text=button_data["text"],
                callback_data=button_data["callback_data"]
            )
            
            # Si no hay markup previo, crear uno nuevo con el botón
            if not message.reply_markup:
                keyboard = [[new_button]]
                button_updated = True
            else:
                # Copiar teclado existente
                keyboard = list(message.reply_markup.inline_keyboard)
                
                # Buscar botón existente con mismo callback_data para actualizar
                for i, row in enumerate(keyboard):
                    for j, btn in enumerate(row):
                        if btn.callback_data == button_data["callback_data"]:
                            # Actualizar botón existente
                            keyboard[i][j] = new_button
                            button_updated = True
                            break
                    if button_updated:
                        break
                
                # Si no se actualizó ningún botón existente, añadir nuevo
                if not button_updated:
                    if row_index == -1:
                        # Añadir en nueva fila al final
                        keyboard.append([new_button])
                    elif 0 <= row_index < len(keyboard):
                        # Añadir en fila existente
                        keyboard[row_index].append(new_button)
                    else:
                        # Crear filas intermedias si es necesario
                        while len(keyboard) <= row_index:
                            keyboard.append([])
                        keyboard[row_index].append(new_button)
            
            # Crear nuevo markup
            new_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            
            # Actualizar mensaje
            return await self._update_markup_with_retry(
                chat_id=chat_id,
                message_id=message_id,
                new_markup=new_markup
            )
            
        except Exception as e:
            log.error(f"Error añadiendo/actualizando botón: {e}", error=e)
            return False
    
    def get_button_states(self, chat_id: Union[int, str], message_id: int) -> Dict[str, int]:
        """
        Obtiene el estado actual de los contadores de botones desde la caché.
        
        Args:
            chat_id: ID del chat
            message_id: ID del mensaje
            
        Returns:
            Diccionario con los contadores actuales
        """
        if isinstance(chat_id, str):
            chat_id = int(chat_id)
            
        message_key = (chat_id, message_id)
        return self.button_states.get(message_key, {}).copy()
    
    def clear_cache(self, chat_id: Optional[Union[int, str]] = None, message_id: Optional[int] = None) -> None:
        """
        Limpia la caché de estados de botones.
        
        Args:
            chat_id: ID del chat (opcional, para limpiar solo un chat)
            message_id: ID del mensaje (opcional, requiere chat_id)
        """
        if chat_id is not None:
            if isinstance(chat_id, str):
                chat_id = int(chat_id)
                
            if message_id is not None:
                # Limpiar caché para un mensaje específico
                message_key = (chat_id, message_id)
                if message_key in self.button_states:
                    del self.button_states[message_key]
                if message_key in self.markup_cache:
                    del self.markup_cache[message_key]
                if message_key in self.retry_counts:
                    del self.retry_counts[message_key]
                if message_key in self.update_cooldowns:
                    del self.update_cooldowns[message_key]
            else:
                # Limpiar caché para todo un chat
                keys_to_remove = []
                for key in self.button_states.keys():
                    if key[0] == chat_id:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    if key in self.button_states:
                        del self.button_states[key]
                    if key in self.markup_cache:
                        del self.markup_cache[key]
                    if key in self.retry_counts:
                        del self.retry_counts[key]
                    if key in self.update_cooldowns:
                        del self.update_cooldowns[key]
        else:
            # Limpiar toda la caché
            self.button_states.clear()
            self.markup_cache.clear()
            self.retry_counts.clear()
            self.update_cooldowns.clear()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Retorna métricas del servicio de botones.
        
        Returns:
            Diccionario con métricas de operación
        """
        return {
            **self.metrics,
            "cached_messages": len(self.button_states),
            "retry_pending": len(self.retry_counts),
            "cooldown_active": len(self.update_cooldowns)
        }
    
    # Métodos privados auxiliares
    
    async def _update_markup_with_retry(
        self,
        chat_id: int,
        message_id: int,
        new_markup: InlineKeyboardMarkup,
        max_retries: int = 2
    ) -> bool:
        """
        Actualiza el markup de un mensaje con reintentos automáticos.
        
        Args:
            chat_id: ID del chat
            message_id: ID del mensaje
            new_markup: Nuevo markup a aplicar
            max_retries: Número máximo de reintentos
            
        Returns:
            True si la actualización fue exitosa, False si falló
        """
        message_key = (chat_id, message_id)
        retry_count = self.retry_counts.get(message_key, 0)
        
        # Intentar la operación
        for attempt in range(retry_count + 1, retry_count + max_retries + 2):
            try:
                await self.bot.edit_message_reply_markup(
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=new_markup
                )
                return True
                
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    # No es un error real si el markup es idéntico
                    return True
                elif "message to edit not found" in str(e):
                    # El mensaje ya no existe, limpiar cache
                    self.clear_cache(chat_id, message_id)
                    log.warning(f"Mensaje {message_id} no encontrado para editar")
                    return False
                elif attempt <= retry_count + max_retries:
                    # Reintentar después de un retraso
                    self.metrics["retries_performed"] += 1
                    # Backoff exponencial: 1s, 2s, 4s, etc.
                    delay = min(2 ** (attempt - 1), 8)  # Cap at 8 seconds
                    # Añadir variación aleatoria (jitter)
                    delay = delay * (0.75 + random.random() * 0.5)  # 75-125% of base delay
                    log.warning(f"Reintento {attempt-retry_count}/{max_retries} para mensaje {message_id} en {delay:.2f}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    # Agotados los reintentos
                    log.error(f"Error actualizando markup después de {max_retries} intentos: {e}")
                    # Actualizar contador de reintentos para futuras operaciones
                    self.retry_counts[message_key] = attempt
                    return False
                    
            except (TelegramForbiddenError, TelegramAPIError) as e:
                log.error(f"Error de Telegram actualizando markup: {e}")
                return False
                
            except Exception as e:
                log.error(f"Error inesperado actualizando markup: {e}", error=e)
                return False
        
        return False
    
    async def _generate_default_markup(self, counters: Dict[str, int], button_prefix: str = "") -> InlineKeyboardMarkup:
        """
        Genera un markup por defecto para contadores.
        
        Args:
            counters: Diccionario de contadores
            button_prefix: Prefijo para los callback_data
            
        Returns:
            Markup generado
        """
        keyboard = []
        row = []
        
        for key, count in counters.items():
            # Crear botón con contador
            callback_data = f"{button_prefix}:{key}" if button_prefix else key
            button = InlineKeyboardButton(
                text=f"{key} ({count})",
                callback_data=callback_data
            )
            
            # Añadir a la fila actual, máximo 2 por fila
            row.append(button)
            if len(row) == 2:
                keyboard.append(row)
                row = []
        
        # Añadir última fila si quedaron botones
        if row:
            keyboard.append(row)
            
        return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Singleton para acceso global
_inline_button_service = None

def get_inline_button_service(bot: Bot = None, session: AsyncSession = None) -> Optional[InlineButtonService]:
    """
    Obtiene la instancia global del servicio de botones inline.
    
    Args:
        bot: Instancia del bot (requerida para inicialización)
        session: Sesión de base de datos (opcional)
        
    Returns:
        Instancia del servicio o None si no está inicializado
    """
    global _inline_button_service
    
    if _inline_button_service is None and bot is not None:
        _inline_button_service = InlineButtonService(bot, session)
        log.startup("InlineButtonService inicializado como singleton")
        
    return _inline_button_service