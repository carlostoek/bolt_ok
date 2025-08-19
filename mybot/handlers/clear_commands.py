"""
Comandos para limpieza de chat y gestión de mensajes del sistema.
Permite a los usuarios y administradores limpiar sus chats manualmente.
"""
import logging
from typing import Optional, List, Dict, Any, Union

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from services.message_manager_service import get_message_manager, MessageCategory
from services.ephemeral_message_service import get_ephemeral_service
from services.admin_notification_service import get_admin_notification_service, AdminNotificationType
from utils.sexy_logger import log

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("clear"))
async def cmd_clear_chat(message: Message):
    """
    Comando para limpiar el chat del usuario.
    Elimina mensajes del sistema, notificaciones y otros mensajes temporales.
    
    Opciones:
    /clear - Limpieza básica manteniendo mensajes importantes
    /clear all - Limpieza completa incluyendo mensajes de contenido
    /clear system - Solo mensajes del sistema
    /clear notifications - Solo notificaciones
    """
    user_id = message.from_user.id
    
    # Obtener servicio de mensajes
    message_manager = get_message_manager()
    if not message_manager:
        await message.answer("El servicio de mensajes no está disponible.")
        return
        
    # Analizar argumentos
    args = message.text.split()[1:] if message.text and len(message.text.split()) > 1 else []
    
    # Determinar categorías a limpiar
    categories = None
    keep_pinned = True
    force_all = False
    
    if args:
        if "all" in args:
            # Limpiar todo excepto anclados
            categories = None  # Todas
            force_all = True
        elif "system" in args:
            # Solo mensajes del sistema
            categories = [MessageCategory.SYSTEM]
        elif "notifications" in args or "notif" in args:
            # Solo notificaciones
            categories = [MessageCategory.NOTIFICATION]
        elif "errors" in args or "error" in args:
            # Solo mensajes de error
            categories = [MessageCategory.ERROR]
    
    # Si no se especifica, usar configuración por defecto
    if categories is None and not force_all:
        # Categorías por defecto para limpieza básica
        categories = [
            MessageCategory.SYSTEM,
            MessageCategory.NOTIFICATION,
            MessageCategory.ERROR
        ]
    
    # Ejecutar limpieza
    count = await message_manager.clean_user_messages(
        user_id=user_id,
        categories=categories,
        keep_pinned=keep_pinned
    )
    
    # Enviar confirmación
    ephemeral_service = get_ephemeral_service()
    if ephemeral_service:
        await ephemeral_service.send_success(
            user_id=user_id,
            text=f"Se han eliminado {count} mensajes de tu chat.",
            auto_delete_seconds=5
        )
    else:
        # Fallback si no está disponible el servicio efímero
        await message.answer(f"Se han eliminado {count} mensajes de tu chat.")
    
    # Registrar en logs
    log.user_action(
        f"Usuario limpió su chat: {count} mensajes eliminados",
        user_id=user_id,
        action="clean_chat"
    )


@router.message(Command("clearthis"))
async def cmd_clear_this(message: Message):
    """
    Elimina el mensaje al que se responde.
    Si no hay respuesta, elimina solo el comando.
    """
    user_id = message.from_user.id
    
    # Obtener servicios
    message_manager = get_message_manager()
    ephemeral_service = get_ephemeral_service()
    
    if not message_manager:
        await message.answer("El servicio de mensajes no está disponible.")
        return
    
    # Intentar eliminar mensaje de comando
    try:
        await message.delete()
    except Exception as e:
        logger.debug(f"No se pudo eliminar mensaje de comando: {e}")
    
    # Si es respuesta a otro mensaje, eliminar ese también
    if message.reply_to_message:
        try:
            reply_msg = message.reply_to_message
            await message_manager.delete_message(user_id, reply_msg.message_id)
            
            # Notificar éxito
            if ephemeral_service:
                await ephemeral_service.send_success(
                    user_id=user_id,
                    text="Mensaje eliminado correctamente.",
                    auto_delete_seconds=3
                )
        except Exception as e:
            logger.error(f"Error eliminando mensaje respondido: {e}")
            
            if ephemeral_service:
                await ephemeral_service.send_error(
                    user_id=user_id,
                    text="No se pudo eliminar el mensaje.",
                    auto_delete_seconds=5
                )


@router.message(Command("purge"))
async def cmd_purge_messages(message: Message):
    """
    Comando administrativo para eliminar los últimos N mensajes.
    Uso: /purge [número] - Elimina los últimos N mensajes (default 5)
    """
    user_id = message.from_user.id
    
    # Verificar si es admin
    admin_service = get_admin_notification_service()
    is_admin = admin_service and user_id in admin_service.admin_ids
    
    if not is_admin:
        # Silenciosamente ignorar si no es admin
        try:
            await message.delete()
        except:
            pass
        return
    
    # Obtener número de mensajes a eliminar
    args = message.text.split()[1:] if message.text and len(message.text.split()) > 1 else []
    count = 5  # Valor por defecto
    
    if args and args[0].isdigit():
        count = min(int(args[0]), 50)  # Limitar a 50 como máximo
    
    # Intentar eliminar mensaje de comando
    try:
        await message.delete()
    except Exception as e:
        logger.debug(f"No se pudo eliminar mensaje de comando purge: {e}")
    
    # Eliminar mensajes recientes
    deleted = 0
    message_manager = get_message_manager()
    
    if message_manager:
        # Usar función especializada del gestor de mensajes
        deleted = await message_manager.clean_user_messages(
            user_id=user_id,
            categories=None,  # Todas las categorías
            keep_pinned=True,
            max_age_minutes=60  # Limitar a mensajes de la última hora
        )
    
    # Notificar resultado
    ephemeral_service = get_ephemeral_service()
    if ephemeral_service:
        await ephemeral_service.send_success(
            user_id=user_id,
            text=f"Purga completada: {deleted} mensajes eliminados.",
            auto_delete_seconds=5
        )
    
    # Registrar acción administrativa
    if admin_service:
        await admin_service.notify_admins(
            text=f"Admin {user_id} ejecutó purga de {deleted} mensajes en su chat.",
            notification_type=AdminNotificationType.AUDIT,
            exclude_ids=[user_id]  # No notificar al ejecutor
        )


# Registrar callbacks para botones de cierre/limpieza

@router.callback_query(F.data.startswith("close_notification"))
async def handle_close_notification(callback: CallbackQuery):
    """
    Maneja el botón de cerrar notificaciones.
    Elimina el mensaje asociado al botón.
    """
    try:
        # Eliminar mensaje
        await callback.message.delete()
        
        # Confirmar acción (sin alerta)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error cerrando notificación: {e}")
        await callback.answer("No se pudo cerrar el mensaje", show_alert=True)


@router.callback_query(F.data == "clear_chat")
async def handle_clear_chat_button(callback: CallbackQuery):
    """
    Maneja el botón para limpiar chat.
    Ejecuta una limpieza básica de mensajes del sistema.
    """
    user_id = callback.from_user.id
    
    # Obtener servicio
    message_manager = get_message_manager()
    
    if not message_manager:
        await callback.answer("Servicio no disponible", show_alert=True)
        return
    
    # Categorías para limpieza rápida
    categories = [
        MessageCategory.SYSTEM,
        MessageCategory.NOTIFICATION,
        MessageCategory.ERROR
    ]
    
    # Ejecutar limpieza
    count = await message_manager.clean_user_messages(
        user_id=user_id,
        categories=categories,
        keep_pinned=True
    )
    
    # Notificar resultado
    await callback.answer(f"Chat limpiado: {count} mensajes eliminados", show_alert=True)
    
    # Registrar acción
    log.user_action(
        f"Usuario limpió chat vía botón: {count} mensajes",
        user_id=user_id,
        action="clean_chat_button"
    )


def register_commands(dp):
    """
    Registra los comandos de limpieza en el dispatcher.
    
    Args:
        dp: Dispatcher de aiogram
    """
    # Registrar comandos específicos en message_manager
    message_manager = get_message_manager()
    if message_manager:
        message_manager.register_command_handler(dp, "clear")
    
    # Registrar comandos del módulo
    dp.include_router(router)
    
    # Registrar handlers para notificaciones efímeras
    ephemeral_service = get_ephemeral_service()
    if ephemeral_service:
        from services.ephemeral_message_service import register_close_notification_handler
        register_close_notification_handler(dp, dp.bot)
    
    log.startup("Comandos de limpieza registrados")