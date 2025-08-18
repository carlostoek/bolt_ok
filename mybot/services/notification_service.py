"""
Servicio centralizado de notificaciones para consolidar mensajes y evitar duplicaciones.
Implementa un sistema de agregación con cola temporal para agrupar notificaciones relacionadas.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot

from utils.message_safety import safe_send_message

logger = logging.getLogger(__name__)


class NotificationData:
    """Representa una notificación pendiente de envío."""
    
    def __init__(self, notification_type: str, data: Dict[str, Any], timestamp: datetime = None):
        self.type = notification_type
        self.data = data
        self.timestamp = timestamp or datetime.now()


class NotificationService:
    """
    Servicio centralizado para manejo de notificaciones con agregación temporal.
    Consolida notificaciones relacionadas en un solo mensaje para mejorar la experiencia de usuario.
    """
    
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
        self.pending_notifications: Dict[int, List[NotificationData]] = {}
        self.scheduled_tasks: Dict[int, asyncio.Task] = {}
        self.aggregation_delay = 0.8  # Segundos para esperar y agrupar notificaciones
        
    async def add_notification(self, user_id: int, notification_type: str, data: Dict[str, Any]) -> None:
        """
        Añade una notificación a la cola para posible agrupación.
        
        Args:
            user_id: ID del usuario de Telegram
            notification_type: Tipo de notificación (points, mission, achievement, etc.)
            data: Datos específicos de la notificación
        """
        try:
            notification = NotificationData(notification_type, data)
            
            # Inicializar lista de notificaciones si no existe
            if user_id not in self.pending_notifications:
                self.pending_notifications[user_id] = []
            
            self.pending_notifications[user_id].append(notification)
            
            # Cancelar tarea anterior si existe y programar nueva
            if user_id in self.scheduled_tasks:
                self.scheduled_tasks[user_id].cancel()
            
            # Programar envío después del delay de agregación
            self.scheduled_tasks[user_id] = asyncio.create_task(
                self._schedule_send(user_id)
            )
            
            logger.debug(f"Added {notification_type} notification for user {user_id}")
            
        except Exception as e:
            logger.exception(f"Error adding notification for user {user_id}: {e}")
    
    async def _schedule_send(self, user_id: int) -> None:
        """
        Envía notificaciones pendientes después del delay de agregación.
        
        Args:
            user_id: ID del usuario de Telegram
        """
        try:
            await asyncio.sleep(self.aggregation_delay)
            
            if user_id in self.pending_notifications and self.pending_notifications[user_id]:
                notifications = self.pending_notifications.pop(user_id, [])
                
                # Limpiar tarea completada
                if user_id in self.scheduled_tasks:
                    del self.scheduled_tasks[user_id]
                
                # Agrupar notificaciones por tipo
                grouped = self._group_notifications_by_type(notifications)
                
                # Construir mensaje unificado
                message = await self._build_unified_message(grouped)
                
                if message:
                    # Enviar mensaje usando safe_send_message
                    await safe_send_message(self.bot, user_id, message)
                    logger.info(f"Sent unified notification to user {user_id}: {len(notifications)} notifications")
                
        except asyncio.CancelledError:
            # Tarea cancelada, no hacer nada
            pass
        except Exception as e:
            logger.exception(f"Error sending scheduled notifications for user {user_id}: {e}")
    
    def _group_notifications_by_type(self, notifications: List[NotificationData]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Agrupa notificaciones por tipo para consolidación.
        
        Args:
            notifications: Lista de notificaciones a agrupar
            
        Returns:
            Dict con notificaciones agrupadas por tipo
        """
        grouped = {}
        for notification in notifications:
            if notification.type not in grouped:
                grouped[notification.type] = []
            grouped[notification.type].append(notification.data)
        
        return grouped
    
    async def _build_unified_message(self, grouped_notifications: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Construye un mensaje unificado a partir de notificaciones agrupadas.
        
        Args:
            grouped_notifications: Notificaciones agrupadas por tipo
            
        Returns:
            Mensaje unificado formateado
        """
        try:
            message_parts = []
            
            # Procesar puntos
            if "points" in grouped_notifications:
                total_points = sum(notif.get("points", 0) for notif in grouped_notifications["points"])
                if total_points > 0:
                    latest_total = grouped_notifications["points"][-1].get("total", 0)
                    message_parts.append(f"💋 *+{total_points} besitos* añadidos")
                    message_parts.append(f"Total actual: {latest_total} besitos")
            
            # Procesar misiones completadas
            if "mission" in grouped_notifications:
                missions = grouped_notifications["mission"]
                if len(missions) == 1:
                    mission = missions[0]
                    message_parts.append(f"🎉 ¡Misión '{mission.get('name', 'Desconocida')}' completada!")
                    if mission.get("points"):
                        message_parts.append(f"Recompensa: {mission.get('points')} besitos")
                else:
                    total_mission_points = sum(m.get("points", 0) for m in missions)
                    message_parts.append(f"🎉 ¡{len(missions)} misiones completadas!")
                    if total_mission_points > 0:
                        message_parts.append(f"Recompensa total: {total_mission_points} besitos")
            
            # Procesar logros
            if "achievement" in grouped_notifications:
                achievements = grouped_notifications["achievement"]
                if len(achievements) == 1:
                    achievement = achievements[0]
                    message_parts.append(f"🏆 ¡Logro desbloqueado: {achievement.get('name', 'Desconocido')}!")
                else:
                    message_parts.append(f"🏆 ¡{len(achievements)} logros desbloqueados!")
            
            # Procesar insignias
            if "badge" in grouped_notifications:
                badges = grouped_notifications["badge"]
                if len(badges) == 1:
                    badge = badges[0]
                    icon = badge.get("icon", "🏅")
                    message_parts.append(f"{icon} ¡Nueva insignia: {badge.get('name', 'Desconocida')}!")
                else:
                    message_parts.append(f"🏅 ¡{len(badges)} nuevas insignias obtenidas!")
            
            # Procesar subidas de nivel
            if "level" in grouped_notifications:
                levels = grouped_notifications["level"]
                latest_level = levels[-1]
                message_parts.append(f"📈 ¡Has alcanzado el nivel {latest_level.get('level', 'N/A')}!")
                if latest_level.get("reward"):
                    message_parts.append(f"Recompensa: {latest_level.get('reward')}")
            
            # Procesar pistas narrativas
            if "hint" in grouped_notifications:
                hints = grouped_notifications["hint"]
                latest_hint = hints[-1]
                message_parts.append("✨ *Nueva pista desbloqueada:*")
                message_parts.append(f"_{latest_hint.get('text', 'Pista misteriosa...')}_")
            
            # Procesar reacciones
            if "reaction" in grouped_notifications:
                reactions = grouped_notifications["reaction"]
                # Separar reacciones nativas e inline
                native_reactions = [r for r in reactions if r.get('is_native', False)]
                inline_reactions = [r for r in reactions if not r.get('is_native', False)]
                
                # Construir mensaje según tipos de reacciones
                if native_reactions and inline_reactions:
                    message_parts.append(f"Diana sonríe al notar tus {len(reactions)} reacciones diferentes...")
                elif native_reactions:
                    if len(native_reactions) == 1:
                        message_parts.append("💫 Diana se sonroja por tu reacción nativa...")
                    else:
                        message_parts.append(f"💫 Diana se emociona por tus {len(native_reactions)} reacciones nativas...")
                elif inline_reactions:
                    if len(inline_reactions) == 1:
                        message_parts.append("👆 Diana sonríe al notar tu reacción...")
                    else:
                        message_parts.append(f"👆 Diana observa con cariño tus {len(inline_reactions)} reacciones...")
                        
                # Añadir conteo de puntos para reacciones nativas si hay
                total_native_points = sum(r.get('points', 0) for r in native_reactions if r.get('points'))
                if total_native_points > 0:
                    message_parts.append(f"✨ +{total_native_points} besitos por reacciones nativas")
            
            # Construir mensaje final
            if message_parts:
                # Añadir saludo personalizado de Diana
                greeting = "Diana te mira con una sonrisa cálida...\n\n"
                body = "\n".join(message_parts)
                
                # Añadir mensaje de cierre si hay múltiples tipos de notificaciones
                if len(grouped_notifications) > 1:
                    closing = "\n\n*\"Cada paso que das me acerca más a ti, mi amor...\"*"
                    return greeting + body + closing
                else:
                    return greeting + body
            
            return ""
            
        except Exception as e:
            logger.exception(f"Error building unified message: {e}")
            return "Diana te envía una sonrisa misteriosa... 💋"
    
    async def send_immediate_notification(self, user_id: int, message: str) -> None:
        """
        Envía una notificación inmediata sin agregación.
        Útil para notificaciones críticas o de error.
        
        Args:
            user_id: ID del usuario de Telegram
            message: Mensaje a enviar
        """
        try:
            await safe_send_message(self.bot, user_id, message)
            logger.info(f"Sent immediate notification to user {user_id}")
        except Exception as e:
            logger.exception(f"Error sending immediate notification to user {user_id}: {e}")
    
    async def flush_pending_notifications(self, user_id: int) -> None:
        """
        Fuerza el envío inmediato de todas las notificaciones pendientes para un usuario.
        
        Args:
            user_id: ID del usuario de Telegram
        """
        try:
            if user_id in self.scheduled_tasks:
                self.scheduled_tasks[user_id].cancel()
                del self.scheduled_tasks[user_id]
            
            if user_id in self.pending_notifications and self.pending_notifications[user_id]:
                notifications = self.pending_notifications.pop(user_id, [])
                grouped = self._group_notifications_by_type(notifications)
                message = await self._build_unified_message(grouped)
                
                if message:
                    await safe_send_message(self.bot, user_id, message)
                    logger.info(f"Flushed {len(notifications)} notifications for user {user_id}")
                    
        except Exception as e:
            logger.exception(f"Error flushing notifications for user {user_id}: {e}")
    
    def get_pending_count(self, user_id: int) -> int:
        """
        Obtiene el número de notificaciones pendientes para un usuario.
        
        Args:
            user_id: ID del usuario de Telegram
            
        Returns:
            Número de notificaciones pendientes
        """
        return len(self.pending_notifications.get(user_id, []))
    
    def set_aggregation_delay(self, delay_seconds: float) -> None:
        """
        Configura el delay de agregación de notificaciones.
        
        Args:
            delay_seconds: Delay en segundos (mínimo 0.1, máximo 5.0)
        """
        if 0.1 <= delay_seconds <= 5.0:
            self.aggregation_delay = delay_seconds
            logger.info(f"Aggregation delay actualizado a {delay_seconds} segundos")
        else:
            logger.warning(f"Delay inválido {delay_seconds}, manteniendo {self.aggregation_delay}")
    
    def get_aggregation_delay(self) -> float:
        """
        Obtiene el delay actual de agregación.
        
        Returns:
            Delay en segundos
        """
        return self.aggregation_delay
        
    async def send_unified_notification(self, user_id: int, data: Dict[str, Any], bot: Bot) -> None:
        """
        Envía notificación unificada de reacción con formato personalizado según el tipo.
        
        Args:
            user_id: ID del usuario de Telegram
            data: Diccionario con datos de la notificación
            bot: Instancia del bot para enviar mensajes
        """
        try:
            message_parts = []
            
            # Determinar el tipo de reacción y personalizar el mensaje inicial
            reaction_type = data.get('reaction_type', '')
            is_native = data.get('is_native', False)
            
            # Mensaje introductorio según el tipo de reacción
            if is_native:
                intro = "💫 *Reacción nativa registrada*"
            else:
                intro = "👆 *Reacción registrada*"
                
            message_parts.append(intro)
            
            # Reacción registrada con puntos (solo para nativas)
            reaction_points = data.get('points_awarded', 0)
            if reaction_points > 0:
                message_parts.append(f"✨ +{reaction_points} besitos")
                
                # Total de puntos si está disponible
                total_points = data.get('total_points')
                if total_points is not None:
                    message_parts.append(f"Total actual: {total_points} besitos")
            
            # Misiones completadas
            missions_completed = data.get('missions_completed', [])
            if missions_completed:
                if len(missions_completed) == 1:
                    mission = missions_completed[0]
                    message_parts.append(f"🎉 ¡Misión '{mission.get('name', 'Desconocida')}' completada!")
                    if mission.get("points"):
                        message_parts.append(f"Recompensa: {mission.get('points')} besitos")
                else:
                    total_mission_points = data.get('mission_points_awarded', 0)
                    message_parts.append(f"🎉 ¡{len(missions_completed)} misiones completadas!")
                    if total_mission_points > 0:
                        message_parts.append(f"Recompensa total: {total_mission_points} besitos")
            
            # Pistas narrativas
            narrative_hint = data.get('narrative_hint')
            if narrative_hint:
                message_parts.append("✨ *Nueva pista desbloqueada:*")
                message_parts.append(f"_{narrative_hint}_")
            
            # Construir mensaje final
            if message_parts:
                # Añadir saludo personalizado de Diana
                greeting = "Diana te mira con una sonrisa cálida...\n\n"
                body = "\n".join(message_parts)
                
                # Añadir mensaje de cierre para reacciones
                if is_native:
                    closing = "\n\n*\"Qué bonito es sentir tu reacción espontánea, mi amor...\"*"
                else:
                    closing = "\n\n*\"Me encanta cuando interactúas conmigo, cariño...\"*"
                
                message = greeting + body + closing
                await safe_send_message(bot, user_id, message)
                logger.info(f"Sent unified reaction notification to user {user_id}")
                
        except Exception as e:
            logger.exception(f"Error sending unified notification to user {user_id}: {e}")
    
    async def cleanup_expired_notifications(self, max_age_minutes: int = 5) -> None:
        """
        Limpia notificaciones muy antiguas que no se han enviado.
        
        Args:
            max_age_minutes: Edad máxima en minutos antes de limpiar
        """
        try:
            cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
            users_to_cleanup = []
            
            for user_id, notifications in self.pending_notifications.items():
                # Filtrar notificaciones expiradas
                valid_notifications = [
                    n for n in notifications 
                    if n.timestamp > cutoff_time
                ]
                
                if len(valid_notifications) != len(notifications):
                    if valid_notifications:
                        self.pending_notifications[user_id] = valid_notifications
                    else:
                        users_to_cleanup.append(user_id)
                    
                    logger.info(f"Cleaned {len(notifications) - len(valid_notifications)} expired notifications for user {user_id}")
            
            # Limpiar usuarios sin notificaciones
            for user_id in users_to_cleanup:
                del self.pending_notifications[user_id]
                if user_id in self.scheduled_tasks:
                    self.scheduled_tasks[user_id].cancel()
                    del self.scheduled_tasks[user_id]
                    
        except Exception as e:
            logger.exception(f"Error cleaning up expired notifications: {e}")