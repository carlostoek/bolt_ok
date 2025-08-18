"""
Servicio centralizado de notificaciones para consolidar mensajes y evitar duplicaciones.
Implementa un sistema de agregación con cola temporal para agrupar notificaciones relacionadas.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from contextlib import asynccontextmanager
import time

from utils.message_safety import safe_send_message
from utils.sexy_logger import log, logger


class NotificationData:
    """Representa una notificación pendiente de envío con metadatos adicionales."""
    
    def __init__(self, notification_type: str, data: Dict[str, Any], timestamp: datetime = None, priority: int = 1):
        self.type = notification_type
        self.data = data
        self.timestamp = timestamp or datetime.now()
        self.priority = priority  # 1=normal, 2=alta, 3=crítica
        self.retry_count = 0
        self.source_module = data.get('source_module', 'unknown')


class NotificationService:
    """
    Servicio centralizado para manejo de notificaciones con agregación temporal mejorada.
    Implementa un sistema de interceptores y consolidación inteligente de notificaciones.
    
    Features:
    - Agregación temporal inteligente
    - Sistema de interceptores para procesamiento personalizado
    - Priorización de notificaciones
    - Retry automático con backoff exponencial
    - Métricas y monitoreo detallado
    - Rate limiting por usuario
    """
    
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
        self.pending_notifications: Dict[int, List[NotificationData]] = {}
        self.scheduled_tasks: Dict[int, asyncio.Task] = {}
        self.aggregation_delay = 0.8  # Segundos para esperar y agrupar notificaciones
        self.max_aggregation_delay = 5.0  # Delay máximo permitido
        
        # Sistema de interceptores
        self.interceptors: List[Callable] = []
        self.pre_send_interceptors: List[Callable] = []
        self.post_send_interceptors: List[Callable] = []
        
        # Rate limiting
        self.user_rate_limits: Dict[int, datetime] = {}
        self.min_interval_between_notifications = 1.0  # Segundos
        
        # Métricas detalladas
        self.metrics = {
            'notifications_sent': 0,
            'notifications_aggregated': 0,
            'notifications_failed': 0,
            'average_aggregation_count': 0,
            'total_users_notified': set(),
            'notifications_by_type': {},
            'interceptor_executions': 0
        }
        
        log.startup("NotificationService inicializado con interceptores y métricas avanzadas")
        
    async def add_notification(self, user_id: int, notification_type: str, data: Dict[str, Any], priority: int = 1, force_immediate: bool = False) -> None:
        """
        Añade una notificación a la cola para posible agrupación con sistema de interceptores.
        
        Args:
            user_id: ID del usuario de Telegram
            notification_type: Tipo de notificación (points, mission, achievement, etc.)
            data: Datos específicos de la notificación
            priority: Prioridad (1=normal, 2=alta, 3=crítica)
            force_immediate: Si True, envía inmediatamente sin agregación
        """
        start_time = time.time()
        
        try:
            # Verificar rate limiting
            if not self._check_rate_limit(user_id):
                log.warning(f"Rate limit excedido para usuario {user_id}, descartando notificación {notification_type}")
                return
            
            notification = NotificationData(notification_type, data, priority=priority)
            
            # Ejecutar interceptores de pre-procesamiento
            await self._execute_interceptors(self.interceptors, user_id, notification)
            
            # Registrar métrica por tipo
            if notification_type not in self.metrics['notifications_by_type']:
                self.metrics['notifications_by_type'][notification_type] = 0
            self.metrics['notifications_by_type'][notification_type] += 1
            
            # Envío inmediato para notificaciones críticas o forzadas
            if force_immediate or priority >= 3:
                await self._send_immediate_notification(user_id, notification)
                return
            
            # Inicializar lista de notificaciones si no existe
            if user_id not in self.pending_notifications:
                self.pending_notifications[user_id] = []
            
            self.pending_notifications[user_id].append(notification)
            
            # Cancelar tarea anterior si existe y programar nueva
            if user_id in self.scheduled_tasks:
                self.scheduled_tasks[user_id].cancel()
            
            # Determinar delay basado en prioridad
            delay = self._calculate_dynamic_delay(user_id, priority)
            
            # Programar envío después del delay de agregación
            self.scheduled_tasks[user_id] = asyncio.create_task(
                self._schedule_send_with_delay(user_id, delay)
            )
            
            duration = time.time() - start_time
            log.performance(f"Notificación {notification_type} agregada para usuario {user_id}", 
                          duration=duration, user_id=user_id, priority=priority)
            
        except Exception as e:
            log.error(f"Error adding notification for user {user_id}: {str(e)}", error=e)
    
    async def _schedule_send_with_delay(self, user_id: int, delay: float) -> None:
        """
        Envía notificaciones pendientes después del delay de agregación calculado dinámicamente.
        
        Args:
            user_id: ID del usuario de Telegram
            delay: Tiempo de espera en segundos
        """
        try:
            await asyncio.sleep(delay)
            await self._process_and_send_notifications(user_id)
                
        except asyncio.CancelledError:
            # Tarea cancelada, no hacer nada
            log.debug(f"Tarea de notificación cancelada para usuario {user_id}")
            pass
        except Exception as e:
            log.error(f"Error sending scheduled notifications for user {user_id}: {str(e)}", error=e)
    
    async def _process_and_send_notifications(self, user_id: int) -> None:
        """
        Procesa y envía las notificaciones pendientes con interceptores y métricas.
        
        Args:
            user_id: ID del usuario de Telegram
        """
        start_time = time.time()
        
        try:
            if user_id not in self.pending_notifications or not self.pending_notifications[user_id]:
                return
            
            notifications = self.pending_notifications.pop(user_id, [])
            
            # Limpiar tarea completada
            if user_id in self.scheduled_tasks:
                del self.scheduled_tasks[user_id]
            
            if not notifications:
                return
            
            # Ordenar por prioridad (mayor prioridad primero)
            notifications.sort(key=lambda n: n.priority, reverse=True)
            
            # Ejecutar interceptores pre-envío
            for notification in notifications:
                await self._execute_interceptors(self.pre_send_interceptors, user_id, notification)
            
            # Agrupar notificaciones por tipo
            grouped = self._group_notifications_by_type(notifications)
            
            # Construir mensaje unificado
            message = await self._build_unified_message(grouped, user_id)
            
            if message:
                # Enviar mensaje usando safe_send_message
                success = await self._send_message_with_retry(user_id, message)
                
                if success:
                    # Actualizar métricas
                    self._update_send_metrics(user_id, notifications)
                    
                    # Ejecutar interceptores post-envío
                    for notification in notifications:
                        await self._execute_interceptors(self.post_send_interceptors, user_id, notification)
                    
                    duration = time.time() - start_time
                    log.success(f"Notificación unificada enviada a usuario {user_id}: {len(notifications)} notificaciones agregadas", 
                              duration=duration, user_id=user_id, count=len(notifications))
                else:
                    self.metrics['notifications_failed'] += 1
                    log.error(f"Fallar envío de notificación unificada a usuario {user_id}")
            
        except Exception as e:
            self.metrics['notifications_failed'] += 1
            log.error(f"Error processing notifications for user {user_id}: {str(e)}", error=e)
    
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
    
    async def _build_unified_message(self, grouped_notifications: Dict[str, List[Dict[str, Any]]], user_id: int = None) -> str:
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
                    
                    expired_count = len(notifications) - len(valid_notifications)
                    log.warning(f"Limpiadas {expired_count} notificaciones expiradas para usuario {user_id}")
            
            # Limpiar usuarios sin notificaciones
            for user_id in users_to_cleanup:
                del self.pending_notifications[user_id]
                if user_id in self.scheduled_tasks:
                    self.scheduled_tasks[user_id].cancel()
                    del self.scheduled_tasks[user_id]
                    
        except Exception as e:
            log.error(f"Error cleaning up expired notifications: {str(e)}", error=e)
    
    # ============================================
    # SISTEMA DE INTERCEPTORES
    # ============================================
    
    def add_interceptor(self, interceptor: Callable, stage: str = "processing") -> None:
        """
        Añade un interceptor al sistema de notificaciones.
        
        Args:
            interceptor: Función async que recibe (user_id, notification_data)
            stage: 'processing', 'pre_send' o 'post_send'
        """
        try:
            if stage == "processing":
                self.interceptors.append(interceptor)
            elif stage == "pre_send":
                self.pre_send_interceptors.append(interceptor)
            elif stage == "post_send":
                self.post_send_interceptors.append(interceptor)
            else:
                raise ValueError(f"Stage '{stage}' no válido. Use: processing, pre_send, post_send")
            
            log.info(f"Interceptor añadido al stage '{stage}': {interceptor.__name__}")
            
        except Exception as e:
            log.error(f"Error añadiendo interceptor: {str(e)}", error=e)
    
    async def _execute_interceptors(self, interceptors: List[Callable], user_id: int, notification: NotificationData) -> None:
        """
        Ejecuta una lista de interceptores sobre una notificación.
        
        Args:
            interceptors: Lista de funciones interceptoras
            user_id: ID del usuario
            notification: Datos de la notificación
        """
        for interceptor in interceptors:
            try:
                await interceptor(user_id, notification)
                self.metrics['interceptor_executions'] += 1
            except Exception as e:
                log.error(f"Error ejecutando interceptor {interceptor.__name__}: {str(e)}", error=e)
    
    # ============================================
    # RATE LIMITING Y OPTIMIZACIONES
    # ============================================
    
    def _check_rate_limit(self, user_id: int) -> bool:
        """
        Verifica si el usuario puede recibir una nueva notificación.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            True si puede recibir la notificación, False si está rate limited
        """
        now = datetime.now()
        
        if user_id in self.user_rate_limits:
            time_since_last = (now - self.user_rate_limits[user_id]).total_seconds()
            if time_since_last < self.min_interval_between_notifications:
                return False
        
        self.user_rate_limits[user_id] = now
        return True
    
    def _calculate_dynamic_delay(self, user_id: int, priority: int) -> float:
        """
        Calcula el delay de agregación basado en la prioridad y actividad del usuario.
        
        Args:
            user_id: ID del usuario
            priority: Prioridad de la notificación (1-3)
            
        Returns:
            Delay en segundos
        """
        base_delay = self.aggregation_delay
        
        # Reducir delay para alta prioridad
        if priority >= 2:
            base_delay *= 0.5
        
        # Aumentar delay si hay muchas notificaciones pendientes
        pending_count = len(self.pending_notifications.get(user_id, []))
        if pending_count > 3:
            base_delay *= 1.5
        
        return min(base_delay, self.max_aggregation_delay)
    
    async def _send_immediate_notification(self, user_id: int, notification: NotificationData) -> None:
        """
        Envía una notificación inmediatamente sin agregación.
        
        Args:
            user_id: ID del usuario
            notification: Datos de la notificación
        """
        try:
            # Ejecutar interceptores pre-envío
            await self._execute_interceptors(self.pre_send_interceptors, user_id, notification)
            
            # Crear mensaje para notificación única
            grouped = {notification.type: [notification.data]}
            message = await self._build_unified_message(grouped, user_id)
            
            if message:
                success = await self._send_message_with_retry(user_id, message)
                
                if success:
                    self._update_send_metrics(user_id, [notification])
                    await self._execute_interceptors(self.post_send_interceptors, user_id, notification)
                    log.success(f"Notificación inmediata enviada a usuario {user_id}: {notification.type}")
                else:
                    self.metrics['notifications_failed'] += 1
                    log.error(f"Falló envío inmediato a usuario {user_id}")
            
        except Exception as e:
            log.error(f"Error enviando notificación inmediata a usuario {user_id}: {str(e)}", error=e)
    
    async def _send_message_with_retry(self, user_id: int, message: str, max_retries: int = 3) -> bool:
        """
        Envía un mensaje con retry automático y backoff exponencial.
        
        Args:
            user_id: ID del usuario
            message: Mensaje a enviar
            max_retries: Número máximo de reintentos
            
        Returns:
            True si se envió correctamente, False si falló
        """
        for attempt in range(max_retries + 1):
            try:
                await safe_send_message(self.bot, user_id, message)
                return True
                
            except Exception as e:
                if attempt < max_retries:
                    # Backoff exponencial: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    log.warning(f"Reintentando envío a usuario {user_id} en {wait_time}s (intento {attempt + 1}/{max_retries + 1})")
                    await asyncio.sleep(wait_time)
                else:
                    log.error(f"Falló envío definitivo a usuario {user_id} después de {max_retries + 1} intentos: {str(e)}", error=e)
                    return False
        
        return False
    
    def _update_send_metrics(self, user_id: int, notifications: List[NotificationData]) -> None:
        """
        Actualiza las métricas después de un envío exitoso.
        
        Args:
            user_id: ID del usuario
            notifications: Lista de notificaciones enviadas
        """
        self.metrics['notifications_sent'] += 1
        self.metrics['notifications_aggregated'] += len(notifications)
        self.metrics['total_users_notified'].add(user_id)
        
        # Actualizar promedio de agregación
        if self.metrics['notifications_sent'] > 0:
            self.metrics['average_aggregation_count'] = (
                self.metrics['notifications_aggregated'] / self.metrics['notifications_sent']
            )
    
    # ============================================
    # MÉTODOS DE MONITOREO Y MÉTRICAS
    # ============================================
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Obtiene un reporte detallado de métricas del servicio.
        
        Returns:
            Diccionario con métricas detalladas
        """
        return {
            **self.metrics,
            'total_users_notified': len(self.metrics['total_users_notified']),
            'pending_notifications_count': sum(len(notifications) for notifications in self.pending_notifications.values()),
            'active_scheduled_tasks': len(self.scheduled_tasks),
            'aggregation_delay': self.aggregation_delay,
            'rate_limited_users': len(self.user_rate_limits)
        }
    
    def log_metrics_summary(self) -> None:
        """
        Registra un resumen de métricas en los logs.
        """
        metrics = self.get_metrics()
        
        with log.section("MÉTRICAS DEL SERVICIO DE NOTIFICACIONES", "📊"):
            log.success(f"Notificaciones enviadas: {metrics['notifications_sent']}")
            log.success(f"Notificaciones agregadas: {metrics['notifications_aggregated']}")
            log.success(f"Promedio de agregación: {metrics['average_aggregation_count']:.2f}")
            log.success(f"Usuarios únicos notificados: {metrics['total_users_notified']}")
            log.success(f"Interceptores ejecutados: {metrics['interceptor_executions']}")
            
            if metrics['notifications_failed'] > 0:
                log.warning(f"Notificaciones fallidas: {metrics['notifications_failed']}")
            
            if metrics['pending_notifications_count'] > 0:
                log.info(f"Notificaciones pendientes: {metrics['pending_notifications_count']}")
            
            # Reporte por tipo
            if metrics['notifications_by_type']:
                log.info("Notificaciones por tipo:")
                for notif_type, count in metrics['notifications_by_type'].items():
                    log.info(f"  • {notif_type}: {count}")
    
    @asynccontextmanager
    async def notification_batch_context(self, user_id: int):
        """
        Context manager para agrupar múltiples notificaciones en un batch.
        
        Args:
            user_id: ID del usuario
        """
        # Cancelar cualquier tarea programada para evitar envío prematuro
        if user_id in self.scheduled_tasks:
            self.scheduled_tasks[user_id].cancel()
            del self.scheduled_tasks[user_id]
        
        try:
            yield
        finally:
            # Al salir del contexto, forzar el envío de notificaciones pendientes
            if user_id in self.pending_notifications and self.pending_notifications[user_id]:
                await self._process_and_send_notifications(user_id)


# ============================================
# INTERCEPTORES DE EJEMPLO PREDEFINIDOS
# ============================================

async def log_notification_interceptor(user_id: int, notification: NotificationData) -> None:
    """
    Interceptor de ejemplo que registra todas las notificaciones.
    """
    log.user_action(
        f"Notificación procesada: {notification.type}", 
        user_id=user_id, 
        action=f"notification_{notification.type}"
    )

async def gamification_metrics_interceptor(user_id: int, notification: NotificationData) -> None:
    """
    Interceptor que registra métricas específicas de gamificación.
    """
    if notification.type in ['points', 'mission', 'achievement', 'level']:
        points = notification.data.get('points', 0)
        if points > 0:
            log.gamification(
                f"Puntos otorgados via notificación: {points}",
                user_id=user_id,
                points=points
            )

async def narrative_tracking_interceptor(user_id: int, notification: NotificationData) -> None:
    """
    Interceptor para trackear eventos narrativos.
    """
    if notification.type == 'hint' or notification.data.get('narrative_hint'):
        fragment = notification.data.get('fragment', 'unknown')
        log.narrative(
            f"Pista narrativa desbloqueada",
            user_id=user_id,
            fragment=fragment
        )

async def reaction_analytics_interceptor(user_id: int, notification: NotificationData) -> None:
    """
    Interceptor para analytics de reacciones.
    """
    if notification.type == 'reaction':
        is_native = notification.data.get('is_native', False)
        reaction_type = "nativa" if is_native else "inline"
        
        log.user_action(
            f"Reacción {reaction_type} registrada",
            user_id=user_id,
            action=f"reaction_{reaction_type}"
        )


# ============================================
# SINGLETON MEJORADO CON INTERCEPTORES
# ============================================

_notification_service = None

def get_notification_service(session: AsyncSession = None, bot: Bot = None, setup_interceptors: bool = True) -> Optional[NotificationService]:
    """
    Obtiene la instancia global del servicio de notificaciones mejorado.
    
    Args:
        session: Sesión de base de datos (requerida para inicialización)
        bot: Instancia del bot (requerida para inicialización)  
        setup_interceptors: Si True, configura interceptores predefinidos
        
    Returns:
        Instancia del servicio de notificaciones o None si no está inicializado
    """
    global _notification_service
    
    if _notification_service is None and session is not None and bot is not None:
        _notification_service = NotificationService(session, bot)
        
        if setup_interceptors:
            # Configurar interceptores predefinidos
            _notification_service.add_interceptor(log_notification_interceptor, "processing")
            _notification_service.add_interceptor(gamification_metrics_interceptor, "processing")
            _notification_service.add_interceptor(narrative_tracking_interceptor, "processing")
            _notification_service.add_interceptor(reaction_analytics_interceptor, "processing")
            
            log.startup("NotificationService inicializado con interceptores predefinidos")
        
    return _notification_service

def setup_notification_service(session: AsyncSession, bot: Bot, custom_interceptors: List[Callable] = None) -> NotificationService:
    """
    Configuración avanzada del servicio de notificaciones con interceptores personalizados.
    
    Args:
        session: Sesión de base de datos
        bot: Instancia del bot
        custom_interceptors: Lista de interceptores personalizados
        
    Returns:
        Instancia configurada del servicio
    """
    global _notification_service
    
    _notification_service = NotificationService(session, bot)
    
    # Interceptores básicos
    _notification_service.add_interceptor(log_notification_interceptor, "processing")
    _notification_service.add_interceptor(gamification_metrics_interceptor, "processing")
    _notification_service.add_interceptor(narrative_tracking_interceptor, "processing")
    _notification_service.add_interceptor(reaction_analytics_interceptor, "processing")
    
    # Interceptores personalizados
    if custom_interceptors:
        for interceptor in custom_interceptors:
            _notification_service.add_interceptor(interceptor, "processing")
    
    log.startup(f"NotificationService configurado con {len(_notification_service.interceptors)} interceptores")
    
    return _notification_service

def reset_notification_service() -> None:
    """
    Resetea la instancia global del servicio (útil para testing).
    """
    global _notification_service
    _notification_service = None
    log.info("NotificationService reseteado")


# ============================================
# FUNCIONES DE CONVENIENCIA
# ============================================

async def send_unified_notification(user_id: int, data: Dict[str, Any], bot: Bot = None, delay_seconds: float = 1.0) -> None:
    """
    Función de conveniencia para enviar notificaciones unificadas (compatibilidad con código existente).
    
    Args:
        user_id: ID del usuario destinatario
        data: Datos para la notificación 
        bot: Instancia del bot (opcional si el servicio ya está inicializado)
        delay_seconds: Tiempo de espera para agrupar notificaciones
    """
    service = get_notification_service()
    if service is None:
        log.error("NotificationService no inicializado para send_unified_notification")
        return
    
    # Determinar tipo de notificación basado en los datos
    if 'reaction_registered' in data or 'reaction_points' in data:
        notification_type = 'reaction'
    elif 'missions_completed' in data:
        notification_type = 'mission'
    elif 'points_awarded' in data:
        notification_type = 'points'
    else:
        notification_type = 'general'
    
    # Usar el delay personalizado si es diferente al default
    if delay_seconds != service.aggregation_delay:
        old_delay = service.aggregation_delay
        service.set_aggregation_delay(delay_seconds)
        await service.add_notification(user_id, notification_type, data)
        service.set_aggregation_delay(old_delay)  # Restaurar delay original
    else:
        await service.add_notification(user_id, notification_type, data)