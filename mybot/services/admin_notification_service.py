"""
Servicio especializado para la gestión de notificaciones de administradores.
Implementa un sistema de mensajes y notificaciones específico para roles administrativos.
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union, Set
from datetime import datetime, timedelta
from enum import Enum

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from utils.sexy_logger import log
from services.message_manager_service import get_message_manager, MessageCategory

logger = logging.getLogger(__name__)


class AdminNotificationType(Enum):
    """Tipos de notificaciones administrativas con comportamientos específicos."""
    INFO = "info"               # Información general
    WARNING = "warning"         # Advertencias
    ERROR = "error"             # Errores críticos
    STATS = "stats"             # Estadísticas del sistema
    AUDIT = "audit"             # Eventos de auditoría de seguridad
    ACTION_REQUIRED = "action"  # Acciones que requieren intervención


class AdminNotificationService:
    """
    Servicio especializado en la gestión de notificaciones para administradores.
    
    Features principales:
    - Panel de notificaciones anclado y actualizable
    - Histórico de notificaciones por tipo
    - Alertas prioritarias con confirmación de lectura
    - Soporte para notificaciones estadísticas con gráficos
    - Gestión de tareas pendientes para administradores
    - Sistema de auditoría de acciones críticas
    """
    
    def __init__(self, bot: Bot, session: Optional[AsyncSession] = None):
        self.bot = bot
        self.session = session
        self.message_manager = get_message_manager(bot, session)
        
        # Lista de administradores (IDs de Telegram)
        self.admin_ids: Set[int] = set()
        
        # Notificaciones activas por usuario y tipo
        self.active_notifications: Dict[int, Dict[AdminNotificationType, List[Dict[str, Any]]]] = {}
        
        # Notificaciones pendientes de acción por usuario
        self.pending_actions: Dict[int, List[Dict[str, Any]]] = {}
        
        # Estadísticas de notificaciones
        self.notification_stats: Dict[AdminNotificationType, int] = {
            ntype: 0 for ntype in AdminNotificationType
        }
        
        # Paneles anclados de administrador
        self.admin_panels: Dict[int, int] = {}  # user_id -> message_id
        
        # Configuración por tipo de notificación
        self.notification_config: Dict[AdminNotificationType, Dict[str, Any]] = {
            AdminNotificationType.INFO: {
                "emoji": "ℹ️", 
                "color": "blue",
                "auto_delete": 30,  # segundos
                "max_history": 10
            },
            AdminNotificationType.WARNING: {
                "emoji": "⚠️", 
                "color": "yellow",
                "auto_delete": 60,
                "max_history": 20
            },
            AdminNotificationType.ERROR: {
                "emoji": "🔴", 
                "color": "red",
                "auto_delete": 0,  # No auto-eliminar
                "max_history": 50
            },
            AdminNotificationType.STATS: {
                "emoji": "📊", 
                "color": "purple",
                "auto_delete": 120,
                "max_history": 5
            },
            AdminNotificationType.AUDIT: {
                "emoji": "🔒", 
                "color": "gray",
                "auto_delete": 300,
                "max_history": 100
            },
            AdminNotificationType.ACTION_REQUIRED: {
                "emoji": "⚡", 
                "color": "orange",
                "auto_delete": 0,  # No auto-eliminar
                "max_history": 20
            }
        }
        
        # Configuración global
        self.clear_read_notifications_after = 24  # horas
        
        log.startup("AdminNotificationService inicializado")
    
    def add_admin(self, user_id: int) -> None:
        """
        Registra un usuario como administrador para recibir notificaciones.
        
        Args:
            user_id: ID de Telegram del administrador
        """
        self.admin_ids.add(user_id)
        
        # Inicializar estructura de datos para este admin
        if user_id not in self.active_notifications:
            self.active_notifications[user_id] = {
                ntype: [] for ntype in AdminNotificationType
            }
        
        if user_id not in self.pending_actions:
            self.pending_actions[user_id] = []
            
        log.info(f"Usuario {user_id} registrado como administrador")
    
    def remove_admin(self, user_id: int) -> None:
        """
        Elimina un usuario de la lista de administradores.
        
        Args:
            user_id: ID de Telegram del administrador
        """
        if user_id in self.admin_ids:
            self.admin_ids.remove(user_id)
            
        # Limpiar estructuras asociadas
        if user_id in self.active_notifications:
            del self.active_notifications[user_id]
        
        if user_id in self.pending_actions:
            del self.pending_actions[user_id]
            
        if user_id in self.admin_panels:
            del self.admin_panels[user_id]
            
        log.info(f"Usuario {user_id} eliminado de administradores")
    
    async def notify_admins(
        self,
        text: str,
        notification_type: AdminNotificationType = AdminNotificationType.INFO,
        buttons: Optional[List[Dict[str, str]]] = None,
        exclude_ids: Optional[List[int]] = None,
        require_confirmation: bool = False,
        related_entity: Optional[Dict[str, Any]] = None
    ) -> List[int]:
        """
        Envía una notificación a todos los administradores registrados.
        
        Args:
            text: Texto de la notificación
            notification_type: Tipo de notificación
            buttons: Botones adicionales para la notificación
            exclude_ids: IDs de administradores a excluir
            require_confirmation: Si requiere confirmación de lectura
            related_entity: Datos relacionados con la notificación
            
        Returns:
            Lista de IDs de administradores notificados
        """
        if not self.admin_ids:
            log.warning("No hay administradores registrados para notificar")
            return []
            
        # Filtrar administradores excluidos
        target_admins = self.admin_ids
        if exclude_ids:
            target_admins = [admin_id for admin_id in self.admin_ids if admin_id not in exclude_ids]
            
        if not target_admins:
            return []
            
        # Incrementar estadísticas
        self.notification_stats[notification_type] += 1
        
        # Preparar notificación
        config = self.notification_config[notification_type]
        emoji = config["emoji"]
        
        # Formatear mensaje
        formatted_text = f"{emoji} <b>{notification_type.value.upper()}</b>\n\n{text}"
        
        # Preparar botones
        markup = None
        if buttons or require_confirmation:
            keyboard = []
            
            # Añadir botones personalizados
            if buttons:
                row = []
                for btn in buttons:
                    callback_data = btn.get("callback_data", f"admin_action:{len(self.pending_actions)}")
                    row.append(InlineKeyboardButton(
                        text=btn["text"],
                        callback_data=callback_data
                    ))
                    
                    # Filas de máximo 2 botones
                    if len(row) == 2:
                        keyboard.append(row)
                        row = []
                
                # Añadir última fila si quedaron botones
                if row:
                    keyboard.append(row)
            
            # Añadir botón de confirmación si se requiere
            if require_confirmation:
                confirm_button = InlineKeyboardButton(
                    text="✅ Confirmar recepción",
                    callback_data=f"admin_confirm:{int(time.time())}"
                )
                keyboard.append([confirm_button])
                
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        # Datos de la notificación para el registro
        notification_data = {
            "text": text,
            "type": notification_type,
            "timestamp": datetime.now(),
            "confirmed": False,
            "related_entity": related_entity
        }
        
        # Enviar a cada administrador
        notified_ids = []
        for admin_id in target_admins:
            try:
                # Enviar notificación
                message = await self.message_manager.send_message(
                    user_id=admin_id,
                    text=formatted_text,
                    category=MessageCategory.ADMIN,
                    reply_markup=markup,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                
                if message:
                    # Registrar notificación
                    notification_data["message_id"] = message.message_id
                    
                    # Añadir al historial del administrador
                    self.active_notifications[admin_id][notification_type].append(notification_data.copy())
                    
                    # Limitar historial si es necesario
                    max_history = config.get("max_history", 10)
                    if len(self.active_notifications[admin_id][notification_type]) > max_history:
                        # Eliminar más antiguas, preservando no confirmadas
                        self._trim_notifications(admin_id, notification_type, max_history)
                    
                    # Programar auto-eliminación si está configurado
                    auto_delete = config.get("auto_delete", 0)
                    if auto_delete > 0:
                        asyncio.create_task(self._schedule_notification_deletion(
                            admin_id, message.message_id, auto_delete
                        ))
                    
                    notified_ids.append(admin_id)
                    
                    # Actualizar panel de admin si existe
                    asyncio.create_task(self._update_admin_panel(admin_id))
            
            except Exception as e:
                log.error(f"Error enviando notificación a administrador {admin_id}: {e}", error=e)
        
        log.info(f"Notificación administrativa enviada a {len(notified_ids)} administradores: {notification_type.value}")
        return notified_ids
    
    async def send_action_required(
        self,
        text: str,
        actions: List[Dict[str, Any]],
        title: str = "Acción requerida",
        admin_id: Optional[int] = None
    ) -> List[int]:
        """
        Envía una notificación que requiere acción por parte de los administradores.
        
        Args:
            text: Descripción de la acción requerida
            actions: Lista de acciones posibles [{"text": str, "callback_data": str, "action": callable}]
            title: Título de la notificación
            admin_id: ID específico de admin o None para todos
            
        Returns:
            Lista de IDs notificados
        """
        # Preparar botones para las acciones
        buttons = []
        for i, action in enumerate(actions):
            callback_data = action.get("callback_data", f"admin_action:{int(time.time())}_{i}")
            buttons.append({
                "text": action["text"],
                "callback_data": callback_data
            })
            
            # Registrar acción para ejecutar cuando se presione el botón
            action_data = {
                "callback_data": callback_data,
                "action": action.get("action"),
                "description": action.get("text", "Acción sin descripción"),
                "created_at": datetime.now()
            }
            
            # Si es para un admin específico
            if admin_id:
                if admin_id in self.pending_actions:
                    self.pending_actions[admin_id].append(action_data)
            else:
                # Registrar para todos los admins
                for aid in self.admin_ids:
                    if aid in self.pending_actions:
                        self.pending_actions[aid].append(action_data)
        
        # Construir mensaje completo
        full_text = f"{title}\n\n{text}"
        
        # Enviar notificación
        if admin_id:
            target_admins = [admin_id] if admin_id in self.admin_ids else []
        else:
            target_admins = list(self.admin_ids)
            
        return await self.notify_admins(
            text=full_text,
            notification_type=AdminNotificationType.ACTION_REQUIRED,
            buttons=buttons,
            exclude_ids=None if admin_id else [],
            require_confirmation=True
        )
    
    async def send_stats_notification(
        self,
        title: str,
        stats_data: Dict[str, Any],
        description: Optional[str] = None
    ) -> List[int]:
        """
        Envía una notificación con estadísticas formateadas.
        
        Args:
            title: Título de las estadísticas
            stats_data: Datos estadísticos {etiqueta: valor}
            description: Descripción opcional
            
        Returns:
            Lista de IDs notificados
        """
        # Formatear estadísticas
        stats_text = []
        
        for label, value in stats_data.items():
            # Formatear valor según tipo
            if isinstance(value, (int, float)):
                if value > 1000:
                    formatted_value = f"{value:,}".replace(",", " ")
                else:
                    formatted_value = str(value)
            elif isinstance(value, datetime):
                formatted_value = value.strftime("%d/%m/%Y %H:%M")
            else:
                formatted_value = str(value)
                
            stats_text.append(f"• <b>{label}:</b> {formatted_value}")
        
        # Construir mensaje completo
        full_text = f"<b>{title}</b>\n\n"
        
        if description:
            full_text += f"{description}\n\n"
            
        full_text += "\n".join(stats_text)
        
        # Añadir timestamp
        full_text += f"\n\n<i>Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>"
        
        # Enviar como notificación de estadísticas
        return await self.notify_admins(
            text=full_text,
            notification_type=AdminNotificationType.STATS,
            require_confirmation=False
        )
    
    async def create_admin_panel(
        self,
        admin_id: int,
        title: str = "Panel de Administración",
        show_pending_actions: bool = True,
        show_notifications: bool = True,
        show_stats: bool = True
    ) -> Optional[Message]:
        """
        Crea o actualiza un panel de administración anclado.
        
        Args:
            admin_id: ID del administrador
            title: Título del panel
            show_pending_actions: Mostrar acciones pendientes
            show_notifications: Mostrar notificaciones recientes
            show_stats: Mostrar estadísticas básicas
            
        Returns:
            Mensaje del panel o None si falló
        """
        if admin_id not in self.admin_ids:
            log.warning(f"Intento de crear panel para usuario no administrador: {admin_id}")
            return None
            
        # Construir secciones del panel
        sections = []
        
        # 1. Acciones pendientes
        if show_pending_actions and admin_id in self.pending_actions and self.pending_actions[admin_id]:
            pending = self.pending_actions[admin_id]
            sections.append("<b>🔔 Acciones Pendientes</b>")
            
            for i, action in enumerate(pending[-5:]):  # Mostrar las 5 más recientes
                created = action.get("created_at", datetime.now())
                time_ago = self._format_time_ago(created)
                sections.append(f"• {action.get('description')} <i>({time_ago})</i>")
                
            if len(pending) > 5:
                sections.append(f"<i>...y {len(pending) - 5} más</i>")
                
            sections.append("")  # Línea en blanco
        
        # 2. Notificaciones recientes
        if show_notifications and admin_id in self.active_notifications:
            recent_notifications = []
            
            # Recopilar notificaciones recientes de todos los tipos
            for ntype, notifications in self.active_notifications[admin_id].items():
                for notif in notifications:
                    if notif.get("timestamp"):
                        recent_notifications.append({
                            "type": ntype,
                            "text": notif.get("text", ""),
                            "timestamp": notif.get("timestamp"),
                            "confirmed": notif.get("confirmed", False)
                        })
            
            # Ordenar por más recientes primero
            recent_notifications.sort(key=lambda x: x["timestamp"], reverse=True)
            
            if recent_notifications:
                sections.append("<b>📬 Notificaciones Recientes</b>")
                
                for i, notif in enumerate(recent_notifications[:5]):  # Mostrar las 5 más recientes
                    ntype = notif["type"]
                    config = self.notification_config[ntype]
                    emoji = config["emoji"]
                    
                    # Extracto corto del texto
                    text_preview = notif["text"]
                    if len(text_preview) > 30:
                        text_preview = text_preview[:27] + "..."
                        
                    time_ago = self._format_time_ago(notif["timestamp"])
                    confirmed = "✓" if notif["confirmed"] else ""
                    
                    sections.append(f"• {emoji} {text_preview} <i>({time_ago})</i> {confirmed}")
                    
                if len(recent_notifications) > 5:
                    sections.append(f"<i>...y {len(recent_notifications) - 5} más</i>")
                    
                sections.append("")  # Línea en blanco
        
        # 3. Estadísticas básicas
        if show_stats:
            sections.append("<b>📊 Estadísticas del Sistema</b>")
            
            # Contar notificaciones por tipo
            sections.append("Notificaciones enviadas:")
            for ntype, count in self.notification_stats.items():
                if count > 0:
                    config = self.notification_config[ntype]
                    emoji = config["emoji"]
                    sections.append(f"• {emoji} {ntype.value}: {count}")
            
            # Otras estadísticas que se quieran mostrar
            # ...
            
            sections.append("")  # Línea en blanco
        
        # 4. Comandos rápidos
        sections.append("<b>⚡ Comandos Rápidos</b>")
        sections.append("Usa los botones a continuación:")
        
        # Construir texto completo
        full_text = f"<b>{title}</b>\n\n" + "\n".join(sections)
        
        # Preparar botones para comandos rápidos
        buttons = [
            {"text": "🔄 Actualizar", "callback_data": "admin_panel:refresh"},
            {"text": "🧹 Limpiar Chat", "callback_data": "admin_panel:clear_chat"},
            {"text": "📊 Estadísticas", "callback_data": "admin_panel:show_stats"},
            {"text": "🔔 Ver Pendientes", "callback_data": "admin_panel:show_pending"}
        ]
        
        # Enviar o actualizar el panel
        message = await self.message_manager.send_message(
            user_id=admin_id,
            text=full_text,
            category=MessageCategory.ADMIN,
            reply_markup=self._create_markup_from_buttons(buttons),
            parse_mode="HTML",
            update_key="admin_panel",
            disable_web_page_preview=True,
            pin=True  # Anclado
        )
        
        if message:
            # Registrar panel
            self.admin_panels[admin_id] = message.message_id
            
        return message
    
    async def update_all_admin_panels(self) -> int:
        """
        Actualiza los paneles de todos los administradores.
        
        Returns:
            Número de paneles actualizados
        """
        updated = 0
        
        for admin_id in self.admin_ids:
            if admin_id in self.admin_panels:
                try:
                    await self.create_admin_panel(admin_id)
                    updated += 1
                except Exception as e:
                    log.error(f"Error actualizando panel de admin {admin_id}: {e}", error=e)
        
        return updated
    
    async def mark_notification_as_read(
        self,
        admin_id: int,
        message_id: int
    ) -> bool:
        """
        Marca una notificación como leída/confirmada.
        
        Args:
            admin_id: ID del administrador
            message_id: ID del mensaje de la notificación
            
        Returns:
            True si se marcó correctamente, False si no se encontró
        """
        if admin_id not in self.admin_ids or admin_id not in self.active_notifications:
            return False
            
        # Buscar notificación por message_id
        found = False
        for ntype in self.active_notifications[admin_id]:
            for notif in self.active_notifications[admin_id][ntype]:
                if notif.get("message_id") == message_id:
                    notif["confirmed"] = True
                    found = True
                    break
            if found:
                break
                
        if found:
            # Actualizar panel de admin
            await self._update_admin_panel(admin_id)
            return True
        
        return False
    
    async def clear_read_notifications(self, admin_id: int) -> int:
        """
        Elimina notificaciones ya leídas/confirmadas.
        
        Args:
            admin_id: ID del administrador
            
        Returns:
            Número de notificaciones eliminadas
        """
        if admin_id not in self.admin_ids or admin_id not in self.active_notifications:
            return 0
            
        deleted_count = 0
        
        for ntype in self.active_notifications[admin_id]:
            # Filtrar las que están confirmadas y son antiguas
            cutoff_time = datetime.now() - timedelta(hours=self.clear_read_notifications_after)
            
            to_delete = []
            for i, notif in enumerate(self.active_notifications[admin_id][ntype]):
                if notif.get("confirmed", False) and notif.get("timestamp", datetime.now()) < cutoff_time:
                    to_delete.append(i)
            
            # Eliminar desde el final para no afectar índices
            for i in sorted(to_delete, reverse=True):
                try:
                    # Intentar eliminar mensaje físicamente
                    msg_id = self.active_notifications[admin_id][ntype][i].get("message_id")
                    if msg_id:
                        try:
                            await self.bot.delete_message(admin_id, msg_id)
                        except:
                            pass  # Ignorar errores de eliminación física
                    
                    # Eliminar del registro
                    self.active_notifications[admin_id][ntype].pop(i)
                    deleted_count += 1
                except Exception as e:
                    logger.debug(f"Error eliminando notificación confirmada: {e}")
        
        # Actualizar panel de admin
        if deleted_count > 0:
            await self._update_admin_panel(admin_id)
            
        return deleted_count
    
    async def process_callback(self, callback_query) -> bool:
        """
        Procesa callbacks de botones de notificaciones administrativas.
        
        Args:
            callback_query: Objeto CallbackQuery de aiogram
            
        Returns:
            True si fue procesado, False si no correspondía a este servicio
        """
        if not callback_query or not callback_query.data or not callback_query.from_user:
            return False
            
        admin_id = callback_query.from_user.id
        data = callback_query.data
        
        # Verificar si es un callback de admin
        if not data.startswith(("admin_", "panel_")):
            return False
            
        # Verificar si el usuario es admin
        if admin_id not in self.admin_ids:
            await callback_query.answer("No tienes permisos de administrador", show_alert=True)
            return True
            
        try:
            # Manejar diferentes tipos de callbacks
            if data.startswith("admin_confirm:"):
                # Confirmación de lectura
                await self.mark_notification_as_read(admin_id, callback_query.message.message_id)
                await callback_query.answer("Notificación confirmada", show_alert=False)
                return True
                
            elif data.startswith("admin_action:"):
                # Acción personalizada
                action_id = data.split(":", 1)[1] if ":" in data else ""
                
                # Buscar la acción registrada
                if admin_id in self.pending_actions:
                    for i, action in enumerate(self.pending_actions[admin_id]):
                        if action.get("callback_data") == data:
                            # Ejecutar acción si es callable
                            if callable(action.get("action")):
                                try:
                                    # Llamar con el callback como parámetro
                                    await action["action"](callback_query)
                                    # Eliminar acción después de ejecutarla
                                    self.pending_actions[admin_id].pop(i)
                                    # Actualizar panel
                                    await self._update_admin_panel(admin_id)
                                    return True
                                except Exception as e:
                                    log.error(f"Error ejecutando acción admin: {e}", error=e)
                                    await callback_query.answer("Error al ejecutar acción", show_alert=True)
                                    return True
                
                await callback_query.answer("Acción no encontrada o ya ejecutada", show_alert=True)
                return True
                
            elif data == "admin_panel:refresh":
                # Actualizar panel
                await self.create_admin_panel(admin_id)
                await callback_query.answer("Panel actualizado", show_alert=False)
                return True
                
            elif data == "admin_panel:clear_chat":
                # Limpiar chat
                count = await self.message_manager.clean_user_messages(
                    user_id=admin_id,
                    categories=None,  # Todas
                    keep_pinned=True
                )
                await callback_query.answer(f"Chat limpiado: {count} mensajes eliminados", show_alert=True)
                return True
                
            elif data == "admin_panel:show_stats":
                # Mostrar estadísticas detalladas
                stats_data = {
                    "Notificaciones INFO": self.notification_stats[AdminNotificationType.INFO],
                    "Notificaciones WARNING": self.notification_stats[AdminNotificationType.WARNING],
                    "Notificaciones ERROR": self.notification_stats[AdminNotificationType.ERROR],
                    "Notificaciones STATS": self.notification_stats[AdminNotificationType.STATS],
                    "Notificaciones AUDIT": self.notification_stats[AdminNotificationType.AUDIT],
                    "Notificaciones ACTION": self.notification_stats[AdminNotificationType.ACTION_REQUIRED]
                }
                
                await self.send_stats_notification(
                    title="Estadísticas de Notificaciones",
                    stats_data=stats_data,
                    description="Resumen de notificaciones enviadas por tipo"
                )
                
                await callback_query.answer("Estadísticas enviadas", show_alert=False)
                return True
                
            elif data == "admin_panel:show_pending":
                # Mostrar acciones pendientes
                if admin_id in self.pending_actions and self.pending_actions[admin_id]:
                    pending_count = len(self.pending_actions[admin_id])
                    text = f"Tienes {pending_count} acciones pendientes."
                    
                    # Crear botones para cada acción pendiente
                    buttons = []
                    for action in self.pending_actions[admin_id]:
                        buttons.append({
                            "text": action.get("description", "Acción sin descripción"),
                            "callback_data": action.get("callback_data", "admin_action:unknown")
                        })
                    
                    await self.notify_admins(
                        text=text,
                        notification_type=AdminNotificationType.INFO,
                        buttons=buttons,
                        exclude_ids=[uid for uid in self.admin_ids if uid != admin_id]
                    )
                    
                    await callback_query.answer("Acciones pendientes enviadas", show_alert=False)
                else:
                    await callback_query.answer("No tienes acciones pendientes", show_alert=True)
                    
                return True
                
        except Exception as e:
            log.error(f"Error procesando callback admin: {e}", error=e)
            await callback_query.answer("Error procesando acción", show_alert=True)
            
        return False
    
    def register_handlers(self, dp) -> None:
        """
        Registra handlers para comandos administrativos.
        
        Args:
            dp: Dispatcher de aiogram
        """
        from aiogram import Router, F
        from aiogram.filters import Command
        from aiogram.types import Message as AiogramMessage, CallbackQuery
        
        router = Router()
        
        # Comando para crear/actualizar panel
        @router.message(Command("admin_panel"))
        async def cmd_admin_panel(message: AiogramMessage):
            user_id = message.from_user.id
            
            if user_id not in self.admin_ids:
                await message.answer("No tienes permisos de administrador")
                return
                
            await self.create_admin_panel(user_id)
        
        # Comando para limpiar notificaciones leídas
        @router.message(Command("admin_clear"))
        async def cmd_admin_clear(message: AiogramMessage):
            user_id = message.from_user.id
            
            if user_id not in self.admin_ids:
                await message.answer("No tienes permisos de administrador")
                return
                
            count = await self.clear_read_notifications(user_id)
            await message.answer(f"Se han eliminado {count} notificaciones leídas")
        
        # Handler para callbacks
        @router.callback_query(F.data.startswith(("admin_", "panel_")))
        async def handle_admin_callback(callback: CallbackQuery):
            await self.process_callback(callback)
        
        # Incluir el router en el dispatcher
        dp.include_router(router)
        log.info("Handlers de AdminNotificationService registrados")
    
    # Métodos privados auxiliares
    
    def _create_markup_from_buttons(self, buttons: List[Dict[str, str]]) -> InlineKeyboardMarkup:
        """Crea un markup de teclado a partir de lista de botones."""
        keyboard = []
        row = []
        
        for btn in buttons:
            row.append(InlineKeyboardButton(
                text=btn["text"],
                callback_data=btn["callback_data"]
            ))
            
            # Filas de máximo 2 botones
            if len(row) == 2:
                keyboard.append(row)
                row = []
        
        # Añadir última fila si quedaron botones
        if row:
            keyboard.append(row)
            
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    def _trim_notifications(self, admin_id: int, notification_type: AdminNotificationType, max_count: int) -> None:
        """Limita el número de notificaciones almacenadas preservando las importantes."""
        if admin_id not in self.active_notifications:
            return
            
        notifications = self.active_notifications[admin_id].get(notification_type, [])
        if len(notifications) <= max_count:
            return
            
        # Separar confirmadas y no confirmadas
        confirmed = [n for n in notifications if n.get("confirmed", False)]
        unconfirmed = [n for n in notifications if not n.get("confirmed", False)]
        
        # Si hay demasiadas no confirmadas, mantener las más recientes
        if len(unconfirmed) > max_count:
            # Ordenar por fecha, más recientes primero
            unconfirmed.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
            # Mantener solo las más recientes
            unconfirmed = unconfirmed[:max_count]
        
        # Si aún hay espacio, mantener algunas confirmadas (las más recientes)
        remaining_slots = max_count - len(unconfirmed)
        if remaining_slots > 0 and confirmed:
            # Ordenar por fecha, más recientes primero
            confirmed.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
            # Mantener solo las que quepan
            confirmed = confirmed[:remaining_slots]
        else:
            confirmed = []
        
        # Combinar y guardar
        self.active_notifications[admin_id][notification_type] = unconfirmed + confirmed
    
    def _format_time_ago(self, timestamp: datetime) -> str:
        """Formatea un timestamp como tiempo relativo ('hace X minutos')."""
        if not timestamp:
            return "tiempo desconocido"
            
        now = datetime.now()
        diff = now - timestamp
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "ahora mismo"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"hace {minutes} min"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"hace {hours} h"
        else:
            days = int(seconds // 86400)
            return f"hace {days} días"
    
    async def _schedule_notification_deletion(self, admin_id: int, message_id: int, delay_seconds: int) -> None:
        """Programa la eliminación de una notificación tras un retraso."""
        try:
            await asyncio.sleep(delay_seconds)
            
            # Verificar si el admin sigue registrado
            if admin_id not in self.admin_ids:
                return
                
            # Buscar la notificación para ver si aún existe y si está confirmada
            found = False
            is_confirmed = False
            
            for ntype in self.active_notifications.get(admin_id, {}):
                for notif in self.active_notifications[admin_id][ntype]:
                    if notif.get("message_id") == message_id:
                        found = True
                        is_confirmed = notif.get("confirmed", False)
                        break
                if found:
                    break
            
            # No eliminar si no está confirmada (para dar tiempo a leerla)
            if found and not is_confirmed:
                return
                
            # Intentar eliminar el mensaje
            try:
                await self.bot.delete_message(admin_id, message_id)
                
                # Quitar del registro
                if found:
                    for ntype in self.active_notifications.get(admin_id, {}):
                        self.active_notifications[admin_id][ntype] = [
                            n for n in self.active_notifications[admin_id][ntype]
                            if n.get("message_id") != message_id
                        ]
            except Exception as e:
                logger.debug(f"Error eliminando notificación programada {message_id}: {e}")
                
        except asyncio.CancelledError:
            # Tarea cancelada, ignorar
            pass
        except Exception as e:
            logger.error(f"Error en eliminación programada: {e}")
    
    async def _update_admin_panel(self, admin_id: int) -> None:
        """Actualiza el panel de administración si existe."""
        if admin_id not in self.admin_ids or admin_id not in self.admin_panels:
            return
            
        try:
            await self.create_admin_panel(admin_id)
        except Exception as e:
            logger.error(f"Error actualizando panel de admin {admin_id}: {e}")


# Singleton para acceso global
_admin_notification_service = None

def get_admin_notification_service(bot: Bot = None, session: AsyncSession = None) -> Optional[AdminNotificationService]:
    """
    Obtiene la instancia global del servicio de notificaciones para administradores.
    
    Args:
        bot: Instancia del bot (requerida para inicialización)
        session: Sesión de base de datos (opcional)
        
    Returns:
        Instancia del servicio o None si no está inicializado
    """
    global _admin_notification_service
    
    if _admin_notification_service is None and bot is not None:
        _admin_notification_service = AdminNotificationService(bot, session)
        log.startup("AdminNotificationService inicializado como singleton")
        
    return _admin_notification_service